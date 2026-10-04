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
- `landings()` lists one more adding binding on every visited stack, for the
  hidden-exit check: a layer that lands through a lower layer's binding is on
  top of the whole stack, though it is in nobody's chain there (2026-10-03).
- Chords are ignored (author, 2026-10-01): every adding binding is followed as
  if its chord could fire. That can add a stack that can't happen, never drop
  one that can.
- Recovery and reset bindings, hold_layer and mode shifts are not followed.
- The limits of one (arrival, bystander, landing) keep the walk small. walk.py
  has none of them: it builds every stack with at most N layers on at once.
- `workers` splits the walk over processes, one wave of chain states at a
  time. It only pays with more than one arrival; the result and every reason
  are the same as on one core. The default is one process.

Plan: plans/2026-10-01-backward-chain-audit.md. Record:
findings/2026-10-01-backward-chain-stacks/README.md.
"""
from collections import deque
from dataclasses import dataclass
import multiprocessing

from .flow_model import Inventory, resolve
from .stacks import apply_ops

NOT_FOLLOWED = ("recovery", "reset", "legacy-hold", "mode-shift")
# "center" is a repeating removal on an inverted stick edge; "release" covers the
# normal edge's Release that the stateful transitions plan moves those exits to.
SETTLE = ("center", "removal", "cancel", "release")
POOL_MIN = 256             # chain states in one wave before the work is split over processes
_SOLVING = None            # the Chains whose wave is being expanded; the forked workers inherit it


def _expand_states(task):
    """One task: the events of a list of (head, key, encoded reason), each distinct event once."""
    chains = _SOLVING
    events, seen = [], set()
    for head, key, steps in task:
        for event in chains._expand(head, key, chains._decode(steps)):
            mark = event[:-1]
            if mark not in seen:
                seen.add(mark)
                events.append(mark + (chains._encode(event[-1]),))
    return events


@dataclass(frozen=True)
class Why:
    """The reason a stack exists: the bindings that built it, in order."""
    steps: tuple = ()        # ((kind, Transition), ...); kind is "step", "settle" or "arrival"
    bystander: str = None

    def describe(self):
        return [("" if kind == "step" else kind + ": ") + t.describe() for kind, t in self.steps]


class Chains:
    def __init__(self, layout, inventory=None, arrivals=1, contexts=(), foreign_arrivals=True, workers=1):
        self.layout = layout
        self.arrivals = arrivals
        self.workers = workers
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
        self._landings = None
        self._stacks = {}        # every stack the walk visited -> Why
        self._added = {}         # layer -> {stack right after it was freshly added: Why}
        self._below = {}
        self._answers = {}       # (stack, source, input) -> the layer whose binding fires there
        self._number = {id(t): i for i, t in enumerate(inventory.transitions)}

    def _encode(self, why):
        """A reason as ((kind, binding number), ...), to pass between processes."""
        return tuple((kind, self._number[id(t)]) for kind, t in why.steps)

    def _decode(self, steps):
        return Why(tuple((kind, self.inventory.transitions[i]) for kind, i in steps))

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
        return found

    def _expand(self, head, key, why):
        """What one chain state leads to, as events in order:

            ("visit", stack, Why)                 a stack the walk met
            ("added", layer, stack, Why)          the stack right after the layer was freshly added
            ("state", layer, (stack, used), Why)  a chain state of the layer the step added
        """
        base = self.layout.base
        found = self._between(key, why)
        for (stack, _), reason in found.items():
            yield ("visit", stack, reason)
        for (before, used), reached in found.items():
            for t in self._adding.get(head, ()):
                if not self.fires(t, before):
                    continue
                new = (apply_ops(before, t.ops, base), used)
                reason = Why(reached.steps + (("step", t),))
                yield ("visit", new[0], reason)
                for op, target in t.ops:
                    if op != "add_layer" or target not in new[0]:
                        continue
                    if target not in before:
                        yield ("added", target, new[0], reason)
                    yield ("state", target, new, reason)

    def _solve(self):
        """{layer: {(full stack right after the layer was added, arrivals used): Why}}, to a fixed point.

        Breadth first, so the reason kept for a stack is a shortest chain. A wave is every state the
        wave before it found; with `workers` its states are expanded in other processes and the events
        are applied here, in the same order.
        """
        global _SOLVING
        base = self.layout.base
        states = {base: {}}
        for context in [(base,)] + self.contexts:
            unknown = [t for t in context if t not in self.layout.presets]
            if unknown or context[0] != base:
                raise ValueError(f"bad context {list(context)}: it must start at {base} and name existing layers")
            states[base][(context, 0)] = Why()
        wave = [(base, key) for key in states[base]]

        def apply(event, decode=False):
            kind, reason = event[0], (self._decode(event[-1]) if decode else event[-1])
            if kind == "visit":
                self._stacks.setdefault(event[1], reason)
            elif kind == "added":
                self._added.setdefault(event[1], {}).setdefault(event[2], reason)
            elif event[2] not in states.setdefault(event[1], {}):
                states[event[1]][event[2]] = reason
                found.append((event[1], event[2]))

        pool = None
        try:
            while wave:
                found = []
                if self.workers > 1 and len(wave) >= POOL_MIN:
                    if pool is None:
                        _SOLVING = self
                        pool = multiprocessing.get_context("fork").Pool(self.workers)
                    size = max(1, min(64, len(wave) // (self.workers * 4)))
                    tasks = [[(head, key, self._encode(states[head][key])) for head, key in wave[i:i + size]]
                             for i in range(0, len(wave), size)]
                    for events in pool.imap(_expand_states, tasks):
                        for event in events:
                            apply(event, decode=True)
                else:
                    for head, key in wave:
                        for event in self._expand(head, key, states[head][key]):
                            apply(event)
                wave = found
        finally:
            if pool is not None:
                _SOLVING = None
                pool.terminate()
                pool.join()
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

    def landings(self):
        """[(stack before, binding, stack after)]: every adding binding that answers on a stack the walk visited.

        This is "what can land on this stack next", one binding at a time, whichever layer of the stack the
        binding belongs to. `above` doesn't see these: it only knows a layer's own chain and one bystander, so a
        layer that a lower layer's binding adds on top of another layer's stack (an arrival) is missing there.
        The hidden-exit check reads them (cleanups.covered_exits).
        """
        if self._landings is None:
            self._landings = []
            for stack in list(self.stacks()):
                for t in (t for layer in stack for t in self._adding.get(layer, ())):
                    if self.fires(t, stack):
                        after = apply_ops(stack, t.ops, self.layout.base)
                        if after != stack:
                            self._landings.append((stack, t, after))
        return self._landings

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
