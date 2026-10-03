"""Deprecated 2026-10-01: the family walk. The audits now use backward chains (chains.py, covers.py).

Kept for reference with its tests. It needs a `families` section in the rules, which
steam_layout/flow_config.json no longer has; the last version is tests/data/flow_families_90.9.json.
tests/test_covers.py and tests/test_chains.py compare it with the chains on the 90.9 layouts.
Record: findings/2026-10-01-backward-chain-stacks/README.md.

Follow a family's intended layer transitions from its starting contexts.

A state is (ordered stack, held controls). From each state, a control can be
pressed, held long enough for its delayed entries, or released; an Always On
window can expire. What fires is decided by the topmost layer defining that
input (a disabled source, or a group in a different source mode, stops the
lookup), using only followed transitions
(flow_model.FOLLOWED):

- press: undelayed press entries, chords only when their condition is held.
  A satisfied chord suppresses interruptible Regular Presses on that input.
- hold: delayed entries (the successful hold branch). An early release is
  simply a release without the hold event.
- release: Release entries. Controls nothing tracks are taps: press and
  release in one event.

One physical rule: a stick points one way, so at most one of its directions
is held at a time (diagonals are not modelled).
- expiry: the effective `always_on_action` entries.

Family scope: a restricted context layer (Base, Gyro) fires only on the
family's declared controls; layers added during the flow, and context layers
declared live (Steering after its commit), fire on any of their inputs. That keeps
unrelated families (pads, stick touch entry, other menus) out of the flow
without listing them. Excluded transitions are kept in the report.

Entries firing together run in serialized order; each step records them.
Visited states end cycles, so there is no depth cap. `max_states` is a
resource limit: hitting it marks the family as not covered.

Plan: plans/2026-10-01-intended-flow-inheritance.md, section 2.
"""
import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from .flow_model import ALWAYS_ON, DIRECTIONS, Inventory, chord_condition, resolve
from .model import entries, map_title
from .stacks import apply_ops

CONFIG = Path(__file__).with_name("flow_config.json")


def variant_of(layout):
    return "alternative" if "alternative" in layout.cm.get("title", "") else "default"


def load_config(path=None):
    return json.loads(Path(path or CONFIG).read_text(encoding="utf-8"))


def _per_variant(value, variant):
    return value.get(variant, value.get("default", [])) if isinstance(value, dict) else value


def _control(text):
    source, name = text.split("/", 1)
    return (source, name)


@dataclass
class Family:
    name: str
    contexts: list
    controls: set
    held_at_start: frozenset
    exclude: dict             # (layer, control) -> reason
    doc: str = ""
    restricted: frozenset = None  # context layers limited to the declared controls
    may_hold: frozenset = frozenset()  # pressable for chord conditions; context bindings don't fire

    def __post_init__(self):
        if self.restricted is None:
            self.restricted = frozenset(t for c in self.contexts for t in c)

    @classmethod
    def from_config(cls, name, spec, variant, mapping):
        controls = _per_variant(spec["controls"], variant)
        stacks, live = [], set()
        for ctx in spec["contexts"]:
            stack = ctx["stack"] if isinstance(ctx, dict) else ctx
            stacks.append(tuple(map_title(t, mapping) for t in stack))
            live |= {map_title(t, mapping) for t in (ctx.get("live", []) if isinstance(ctx, dict) else [])}
        return cls(
            name=name,
            contexts=stacks,
            restricted=frozenset(t for c in stacks for t in c) - live,
            controls={_control(c) for c in controls},
            held_at_start=frozenset(_control(c) for c in spec.get("held_at_start", [])),
            exclude={(map_title(e["layer"], mapping), _control(e["control"])): e["reason"]
                     for e in spec.get("exclude", [])},
            may_hold=frozenset(_control(c) for c in _per_variant(spec.get("may_hold", []), variant)),
            doc=spec.get("doc", ""))


def families(layout, config):
    variant = variant_of(layout)
    mapping = config.get("variants", {}).get(variant, {})
    return {name: Family.from_config(name, spec, variant, mapping)
            for name, spec in config["families"].items()}


@dataclass
class Step:
    event: str                # press, hold, release, tap, expiry
    control: tuple
    layer: str = None         # the layer whose binding fired (None: nothing fired)
    fired: tuple = ()         # Transitions applied, in order
    skipped: tuple = ()       # (Transition, reason) that matched but aren't followed

    def describe(self):
        what = f"{self.event} {self.control[0]}/{self.control[1]}"
        if not self.fired:
            return what + (f" ({self.layer}: nothing followed)" if self.layer else "")
        return what + f" -> {self.layer} " + "; ".join(t.activator + "#" + str(t.index) for t in self.fired)


@dataclass
class FlowResult:
    family: Family
    states: dict = field(default_factory=dict)   # state -> (parent state, Step) or None for a start
    complete: bool = True
    skipped: dict = field(default_factory=dict)  # (Transition) -> reason, seen but not followed

    def path(self, state):
        steps = []
        while self.states.get(state):
            parent, step = self.states[state]
            steps.append(step)
            state = parent
        return state, list(reversed(steps))

    def layers(self):
        """Every layer the flow reaches, contexts included; the action set (bottom) excluded."""
        bottoms = {c[0] for c in self.family.contexts}
        return sorted({t for stack, _ in self.states for t in stack} - bottoms)

    def lower_stacks(self, title):
        """{lower stack: first state where `title` sits on it}, in discovery order."""
        found = {}
        for state in self.states:
            stack = state[0]
            if title in stack:
                found.setdefault(stack[:stack.index(title)], state)
        return found


class FlowWalker:
    def __init__(self, layout, inventory=None):
        self.layout = layout
        self.inventory = inventory or Inventory.of(layout)
        self._by_key = {}
        for t in self.inventory.transitions:
            self._by_key.setdefault((t.layer, t.control), []).append(t)
        self._tracked = {}

    @staticmethod
    def can_fire(family, t):
        """Whether a transition can ever be followed in this family."""
        return t.followed and (t.layer, t.control) not in family.exclude and \
            (t.layer not in family.restricted or t.control in family.controls)

    def reachable(self, family):
        """Layers the family's followed transitions could add: a cheap add-graph closure."""
        fires = lambda t: self.can_fire(family, t)
        layers = {x for c in family.contexts for x in c}
        frontier = list(layers)
        while frontier:
            title = frontier.pop()
            for t in self.inventory.by_layer(title):
                if fires(t):
                    for op, target in t.ops:
                        if op == "add_layer" and target not in layers:
                            layers.add(target)
                            frontier.append(target)
        return layers

    def tracked(self, family):
        """Controls whose timing matters in this family (held across steps); the rest are taps."""
        if family.name not in self._tracked:
            layers = self.reachable(family)
            followed = [t for t in self.inventory.transitions if t.layer in layers and self.can_fire(family, t)]
            result = {t.control for t in followed if t.event in ("release", "hold")}
            result |= {c for t in followed if t.condition for c in t.condition.controls()}
            self._tracked[family.name] = result
        return self._tracked[family.name]

    def _chord_satisfied(self, title, control, held):
        group = self.layout.active(title).get(control[0])
        value = group["inputs"][control[1]]["activators"]
        for kind, e in entries(value):
            cond = chord_condition(e.get("settings", {})) if kind == "chord" else None
            if cond and cond.satisfied(held):
                return True
        return False

    def _select(self, family, stack, control, held, phase):
        kind, layer, _, _ = resolve(self.layout, stack, *control)
        if kind != "binding":
            return None, [], []
        if layer in family.restricted and control not in family.controls:
            return layer, [], []
        blocked = self._chord_satisfied(layer, control, held)
        chosen, skipped = [], []
        for t in self._by_key.get((layer, control), []):
            if t.event != phase:
                continue
            if t.condition and not t.condition.satisfied(held):
                continue
            if t.activator == "Full_Press" and t.interruptible and blocked:
                continue
            reason = family.exclude.get((layer, control))
            if reason:
                skipped.append((t, "excluded: " + reason))
            elif not t.followed:
                skipped.append((t, t.role + ": " + t.reason))
            else:
                chosen.append(t)
        return layer, chosen, skipped

    def _fire(self, family, stack, control, held, phase):
        layer, chosen, skipped = self._select(family, stack, control, held, phase)
        for t in chosen:
            stack = apply_ops(stack, t.ops, self.layout.base)
        return stack, Step(phase, control, layer, tuple(chosen), tuple(skipped))

    def candidates(self, family, state):
        stack, held = state
        result = set(family.controls) | set(family.held_at_start) | set(held) | set(family.may_hold)
        for title in stack:
            if title not in family.restricted:
                result |= {t.control for t in self.inventory.by_layer(title) if t.control != ALWAYS_ON}
        return sorted(result)

    def successors(self, family, state):
        stack, held = state
        for control in self.candidates(family, state):
            if control in held:
                new, step = self._fire(family, stack, control, held, "hold")
                if step.fired:
                    yield (new, held), step
                new, step = self._fire(family, stack, control, held, "release")
                yield (new, held - {control}), step
            elif control[1] in DIRECTIONS and any(h[0] == control[0] and h[1] in DIRECTIONS for h in held):
                continue  # the stick already points another way
            else:
                pressed = held | {control}
                new, step = self._fire(family, stack, control, pressed, "press")
                if control in self.tracked(family) or control in family.held_at_start or control in family.may_hold:
                    yield (new, pressed), step
                else:
                    new, release = self._fire(family, new, control, held, "release")
                    tap = Step("tap", control, step.layer, step.fired + release.fired, step.skipped + release.skipped)
                    yield (new, held), tap
        new, step = self._fire(family, stack, ALWAYS_ON, held, "expiry")
        if step.fired:
            yield (new, held), step

    def walk(self, family, max_states=200_000):
        result = FlowResult(family)
        queue = deque()
        for ctx in family.contexts:
            missing = [t for t in ctx if t not in self.layout.presets]
            if missing:
                raise ValueError(f"{family.name}: unknown context layers {missing}")
            start = (tuple(ctx), family.held_at_start)
            if start not in result.states:
                result.states[start] = None
                queue.append(start)
        while queue:
            state = queue.popleft()
            for nxt, step in self.successors(family, state):
                for t, reason in step.skipped:
                    result.skipped.setdefault(t, reason)
                if nxt == state or nxt in result.states:
                    continue
                if len(result.states) >= max_states:
                    result.complete = False
                    return result
                result.states[nxt] = (state, step)
                queue.append(nxt)
        return result
