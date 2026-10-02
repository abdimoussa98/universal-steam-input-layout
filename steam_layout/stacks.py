"""Stack helpers: applying layer commands, following one sequence, and the deprecated StackSpace search.

Still in use: `apply_ops`, `definer` and `effective_input` (chains.py and the audits build on them),
and `fire` / `walk` for replaying one concrete sequence of inputs.

**Deprecated 2026-10-01: `StackSpace` and `explore`**, the depth-limited search of every stack. It
can't reach layers more than a few inputs from the action set (the Steering windows are seven away) and
took seconds where the backward chains take a fraction of one. The audits now use chains.py. The search
is kept for reference and as an opt-in comparison (`audit_inheritance.py --depth N`); nothing depends on
it. Record: findings/2026-10-01-backward-chain-stacks/README.md.

StackSpace: every layer stack reachable from the action set, and queries over it.

A stack is a tuple of layer titles, bottom (the action set) to top. Starting
from the action set, every effective binding's layer commands are applied, one
input event at a time, up to `depth` events. The search respects:

- bottom-to-top execution of binding arrays
- whole-input overrides: only the topmost layer defining an input fires it
- disabled sources, which stop the lookup
- re-adding an active layer, which doesn't move it
- mode-shift groups, whose entries can fire
- hold_layer targets, which can be released at any time

Chord conditions are ignored, so stacks left by missed releases are included.
The result is an over-approximation: it may contain stacks that can't happen,
but it won't miss one that can within the depth.

Typical queries:

    space = StackSpace.of(layout, depth=5)
    space.below("L1: Double Tap")                          # stacks under it when it's on top
    space.containing("L1: Tap Cover")                      # every stack it's part of
    space.when_effective("L1: Modifier 0", "switch", "left_bumper")  # where that binding fires
    space.co_active("L1: Modifier 0", "switch", "left_bumper")       # what a cleanup there could find

To follow one concrete sequence instead, `fire` applies a single input to a
stack and `walk` applies a list of them from the action set. Order matters:
the result depends on which layer is topmost for each input and on the
execution order inside the fired array.

    walk(layout, [("switch", "left_bumper", "chord", "hold L1"),
                  ("switch", "left_bumper", "release", "let go")])
"""
from collections import Counter

from .model import MODE_SHIFT, TARGET, actions, bindings, defined, entries


def definer(layout, stack, source, name):
    """(title, activators) of the topmost layer in `stack` defining this input, or None."""
    for title in reversed(stack):
        group = layout.active(title).get(source)
        if group is None:
            continue
        if group["mode"] == "disabled":
            return None
        if defined(group, name):
            return title, group["inputs"][name]["activators"]
    return None


def effective_input(layout, stack, source, name):
    """The activators the topmost layer in `stack` gives this input, or None."""
    found = definer(layout, stack, source, name)
    return found[1] if found else None


def apply_ops(stack, ops, base):
    """Apply layer ops (execution order) to a stack. Re-adding doesn't move a layer; the action set stays."""
    result = list(stack)
    for op, title in ops:
        if op == "remove_layer":
            if title in result and title != base:
                result.remove(title)
        elif title not in result:
            result.append(title)
    return tuple(result)


def fire(layout, stack, source, name, activation, index=0):
    """Fire one input on `stack`: the topmost definer's `index`-th `activation` entry that changes layers.

    Returns (new stack, the layer whose binding fired).
    """
    found = definer(layout, stack, source, name)
    candidates = [entry for kind, entry in entries(found[1]) if kind == activation and layout.layer_ops(entry)] if found else []
    if len(candidates) <= index:
        where = found[0] if found else "no layer"
        raise ValueError(f"{source}/{name}: {where} has no {activation} entry #{index} with layer commands in {stack}")
    return apply_ops(stack, layout.layer_ops(candidates[index]), layout.base), found[0]


def walk(layout, steps, start=None):
    """Apply (source, input, activation[, label]) steps in order from `start` (default: the action set).

    Returns one dict per step: label, the layer whose binding fired, and the stack after it.
    """
    stack = tuple(start or (layout.base,))
    result = []
    for source, name, activation, *label in steps:
        stack, layer = fire(layout, stack, source, name, activation)
        result.append({"label": label[0] if label else f"{source}/{name} {activation}",
                       "layer": layer, "stack": stack})
    return result


def operations(layout, activators):
    """Per activator entry: (layer ops in execution order, mode-shift group IDs)."""
    for _, entry in entries(activators):
        yield layout.layer_ops(entry), [m.group(2) for a in actions(entry) if (m := MODE_SHIFT.search(a))]


def inputs_of(layout, stack):
    """Every (source, input) any layer in the stack defines, in first-seen order."""
    return dict.fromkeys((source, name) for title in stack for source, group in layout.active(title).items()
                         for name in group.get("inputs", {}))


class StackSpace:
    def __init__(self, layout, depth=5, cap=2_000_000):
        self.layout = layout
        self.depth = depth
        self._events = self._explore(cap)

    @classmethod
    def of(cls, layout, depth=5):
        """The cached space for this layout object and depth."""
        cache = layout.__dict__.setdefault("_stack_spaces", {})
        if depth not in cache:
            cache[depth] = cls(layout, depth)
        return cache[depth]

    # -- search --------------------------------------------------------------
    def _apply(self, stack, ops):
        return apply_ops(stack, ops, self.layout.base)

    def _successors(self, stack, holds):
        layout = self.layout
        found = set()
        for source, name in inputs_of(layout, stack):
            for ops, shifts in operations(layout, effective_input(layout, stack, source, name) or {}):
                if ops:
                    found.add(self._apply(stack, ops))
                for gid in shifts:
                    for value in layout.groups.get(gid, {}).get("inputs", {}).values():
                        for shifted, _ in operations(layout, value.get("activators", {})):
                            if shifted:
                                found.add(self._apply(stack, shifted))
        found.update(tuple(t for t in stack if t != held) for held in holds if held in stack)
        return found

    def _explore(self, cap):
        layout = self.layout
        holds = {layout.resolve(m.group(2)) for g in layout.cm["group"] for v in g.get("inputs", {}).values()
                 for b in bindings(v.get("activators", {})) if (m := TARGET.search(b)) and m.group(1) == "hold_layer"}
        start = (layout.base,)
        seen = {start: 0}
        frontier = [start]
        for level in range(1, self.depth + 1):
            following = []
            for stack in frontier:
                for nxt in self._successors(stack, holds):
                    if nxt not in seen:
                        seen[nxt] = level
                        following.append(nxt)
            if len(seen) > cap:
                raise ValueError(f"stack search exceeded {cap} states at depth {level}; lower the depth")
            frontier = following
        return seen

    # -- queries -------------------------------------------------------------
    @property
    def stacks(self):
        """{stack: fewest input events to reach it}."""
        return self._events

    def events(self, stack):
        return self._events[tuple(stack)]

    def below(self, title):
        """{stack below: events} for every stack with `title` on top."""
        return {s[:-1]: n for s, n in self._events.items() if s[-1] == title}

    def containing(self, title):
        """{stack: events} for every stack that includes `title`."""
        return {s: n for s, n in self._events.items() if title in s}

    def effective(self, stack, source, name):
        """(title, activators) that actually fire this input in `stack`, or None."""
        return definer(self.layout, stack, source, name)

    def when_effective(self, title, source, name):
        """{stack: events} for every stack in which `title`'s binding on this input is the one that fires."""
        return {s: n for s, n in self.containing(title).items()
                if (found := definer(self.layout, s, source, name)) and found[0] == title}

    def co_active(self, title, source, name):
        """Counter of the layers present (action set excluded) in the stacks where that binding fires."""
        counts = Counter()
        for stack in self.when_effective(title, source, name):
            counts.update(t for t in stack if t != self.layout.base)
        return counts


def explore(layout, depth, cap=2_000_000):
    """Compatibility wrapper: {"below": {top: {stack below: events}}, "states", "depth"}."""
    space = StackSpace(layout, depth, cap)
    below = {}
    for stack, level in space.stacks.items():
        below.setdefault(stack[-1], {})[stack[:-1]] = level
    return {"below": below, "states": len(space.stacks), "depth": depth}
