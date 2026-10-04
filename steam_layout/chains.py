"""Backward chains: the stacks that can be under a layer, without searching every stack.

Start at a layer and ask who adds it, then who adds that layer, back to the
action set. Each chain of adding bindings gives one stack, and the stack keeps
the bindings that built it as its reason.

    chains = Chains.of(layout)
    chains.below("L1: Double Tap")       # {lower stack: Why}: its own chains plus bystanders
    chains.above("L1: Modifier 0")       # {layer: (lower stack, Why)}: every layer that has it underneath
    chains.lineage("L1: Double Tap")     # the same from its own chains only
    chains.reached("LTP: Arrow Keys")    # True since 90.14; False for a layer only hold_layer adds

Rules:

- A step applies its whole binding (arrays run bottom to top), so a parent
  that removes itself is not under the layer it adds.
- A step only counts if its layer answers that input on the stack so far. A
  layer on top that binds the input, a disabled source or a group in another
  source mode intercepts it (flow_model.resolve).
- Between two steps the stack can shrink through a removal-only binding
  (settle): a cover lifting at stick centre, or on a release. Only removals
  are applied there; adds are only ever followed along the chain.
- Between two steps one other layer may arrive (arrival): any adding binding
  that fires on the stack at that point, such as an Entry Point's Tap Cover
  landing before the stick click that adds the Fn layer. At most `arrivals`
  per chain (default 1).
- A bystander is a layer that added nothing in the chain but is on the stack
  anyway (a ramp layer under a bumper window). The chain is replayed on top
  of each other layer's own stack; the layer stays underneath if no step is
  intercepted and no step removes it. One bystander stack at a time.
- Two views. The default sees overlaps between families: any layer may
  arrive or be a bystander (the Window audit, audit_layer.py). The family
  view (`contexts=...`, `foreign_arrivals=False`) keeps each chain to its own
  layers: it may start from a declared context such as Base with Gyro, and
  only layers the chain itself added may arrive, not Base's or a context
  layer's (the cover check).
- The Cleanup audit's hidden-exit check wants more than one arrival. A compiled
  engine does this same walk with up to six of them (native.py,
  engine/chain_engine.cpp), and tests keep the two in step.
- Chords are ignored (author, 2026-10-01): every adding binding is followed as
  if its chord could fire. That can add a stack that can't happen, never drop
  one that can.
- Recovery and reset bindings, hold_layer and mode shifts are not followed.

Plan: plans/2026-10-01-backward-chain-audit.md. Record:
findings/2026-10-01-backward-chain-stacks/README.md.
"""
from collections import deque
from dataclasses import dataclass

from .flow_model import Inventory, resolve
from .stacks import apply_ops

NOT_FOLLOWED = ("recovery", "reset", "legacy-hold", "mode-shift")
# "center" is a repeating removal on an inverted stick edge; "release" covers the
# normal edge's Release that the stateful transitions plan moves those exits to.
SETTLE = ("center", "removal", "cancel", "release")


@dataclass(frozen=True)
class Why:
    """The reason a stack exists: the bindings that built it, in order."""
    steps: tuple = ()        # ((kind, Transition), ...); kind is "step", "settle" or "arrival"
    bystander: str = None

    def describe(self):
        return [("" if kind == "step" else kind + ": ") + t.describe() for kind, t in self.steps]


class Chains:
    def __init__(self, layout, inventory=None, arrivals=1, contexts=(), foreign_arrivals=True):
        self.layout = layout
        self.arrivals = arrivals
        self.contexts = [tuple(c) for c in contexts]
        self.foreign_arrivals = foreign_arrivals
        self._context_layers = {layout.base} | {t for c in self.contexts for t in c}
        self.inventory = inventory = inventory or Inventory.of(layout)
        self._adding = {}
        for t in inventory.transitions:
            if t.role not in NOT_FOLLOWED and any(op == "add_layer" for op, _ in t.ops):
                self._adding.setdefault(t.layer, []).append(t)
        self._removing = {}
        for t in inventory.transitions:
            if t.role in SETTLE and t.ops and all(op == "remove_layer" for op, _ in t.ops):
                self._removing.setdefault(t.layer, []).append(t)
        self._states = None
        self._stacks = {}        # every stack the walk visited -> Why
        self._added = {}         # layer -> {stack right after it was freshly added: Why}
        self._below = {}
        self._answers = {}       # (stack, source, input) -> the layer whose binding fires there

    @classmethod
    def of(cls, layout):
        """The cached chains for this layout object."""
        if "_chains" not in layout.__dict__:
            layout.__dict__["_chains"] = cls(layout)
        return layout.__dict__["_chains"]

    def fires(self, t, stack):
        """True if `t`'s layer is the one that answers its input on `stack`."""
        if t.layer not in stack:
            return False
        key = (stack, t.source, t.input)
        if key not in self._answers:
            kind, layer, _, _ = resolve(self.layout, stack, t.source, t.input)
            self._answers[key] = layer if kind == "binding" else None
        return self._answers[key] == t.layer

    def _settle(self, found):
        """`found` ({(stack, arrivals used): Why}) plus every stack it can shrink to through removal-only bindings."""
        found = dict(found)
        todo = list(found)
        while todo:
            stack, used = key = todo.pop()
            for t in (t for layer in stack for t in self._removing.get(layer, ())):
                if self.fires(t, stack):
                    new = (apply_ops(stack, t.ops, self.layout.base), used)
                    if new not in found:
                        found[new] = Why(found[key].steps + (("settle", t),))
                        todo.append(new)
        return found

    def _arrive(self, found):
        """`found` plus each stack one more adding binding turns it into, within the arrival budget."""
        result = dict(found)
        for (stack, used), why in found.items():
            if used >= self.arrivals:
                continue
            for t in (t for layer in stack for t in self._adding.get(layer, ())):
                if not self.foreign_arrivals and t.layer in self._context_layers:
                    continue
                if self.fires(t, stack):
                    new = apply_ops(stack, t.ops, self.layout.base)
                    if new != stack:
                        result.setdefault((new, used + 1), Why(why.steps + (("arrival", t),)))
        return result

    def _between(self, key, why):
        """Every stack the chain's next step could meet: settled, with up to the budget of arrivals."""
        found = self._settle({key: why})
        for _ in range(self.arrivals):
            found = self._settle(self._arrive(found))
        for (stack, _), reason in found.items():
            self._stacks.setdefault(stack, reason)
        return found

    def _solve(self):
        """{layer: {(full stack right after the layer was added, arrivals used): Why}}, to a fixed point.

        Breadth first, so the reason kept for a stack is a shortest chain.
        """
        base = self.layout.base
        states = {base: {}}
        for context in [(base,)] + self.contexts:
            unknown = [t for t in context if t not in self.layout.presets]
            if unknown or context[0] != base:
                raise ValueError(f"bad context {list(context)}: it must start at {base} and name existing layers")
            states[base][(context, 0)] = Why()
        todo = deque((base, key) for key in states[base])
        while todo:
            head, key = todo.popleft()
            for (before, used), why in self._between(key, states[head][key]).items():
                for t in self._adding.get(head, ()):
                    if not self.fires(t, before):
                        continue
                    new = (apply_ops(before, t.ops, base), used)
                    reason = Why(why.steps + (("step", t),))
                    self._stacks.setdefault(new[0], reason)
                    for op, target in t.ops:
                        if op != "add_layer" or target not in new[0]:
                            continue
                        if target not in before:
                            self._added.setdefault(target, {}).setdefault(new[0], reason)
                        if new not in states.setdefault(target, {}):
                            states[target][new] = reason
                            todo.append((target, new))
        return states

    @property
    def states(self):
        if self._states is None:
            self._states = self._solve()
        return self._states

    def stacks(self):
        """{stack: Why} for every stack the walk visited: after each add, and settled or with an arrival."""
        self.states
        return self._stacks

    def added(self, title):
        """{stack: Why} right after `title` was added by a binding that didn't already have it on the stack."""
        self.states
        return self._added.get(title, {})

    def reached(self, title):
        """True if some chain of adding bindings leads from the action set to `title`."""
        return bool(self.states.get(title))

    def lineage(self, title):
        """{lower stack: Why} from the layer's own chains."""
        result = {}
        for (stack, _), why in self.states.get(title, {}).items():
            result.setdefault(stack[:stack.index(title)], why)
        return result

    def replay(self, why, stack):
        """`why`'s bindings applied on top of `stack`, or None if one of them no longer fires there."""
        for _, t in why.steps:
            if not self.fires(t, stack):
                return None
            stack = apply_ops(stack, t.ops, self.layout.base)
        return stack

    def below(self, title):
        """{lower stack: Why} for the layer: its own chains, plus one bystander stack underneath."""
        if title not in self._below:
            result = self.lineage(title)
            others = {}                      # each other layer's stacks, as places the chain could start from
            for layer, stacks in self.states.items():
                if layer not in (self.layout.base, title):
                    for stack, _ in stacks:
                        others.setdefault(stack, layer)
            for (own, _), why in self.states.get(title, {}).items():
                for start, layer in others.items():
                    if layer in own:
                        continue
                    done = self.replay(why, start)
                    if done and title in done and layer in done[:done.index(title)]:
                        result.setdefault(done[:done.index(title)], Why(why.steps, layer))
            self._below[title] = result
        return self._below[title]

    def above(self, title):
        """{layer: (one of its lower stacks that holds `title`, Why)}: the layers that can be on top of `title`.

        The inverse of `below`, so it works out `below` for every layer first.
        """
        result = {}
        for layer in self.layout.presets:
            if layer in (title, self.layout.base):
                continue
            for stack, why in self.below(layer).items():
                if title in stack:
                    result[layer] = (stack, why)
                    break
        return result
