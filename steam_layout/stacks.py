"""Stack helpers: applying layer commands and following one concrete sequence of inputs.

A stack is a tuple of layer titles, bottom (the action set) to top.

- `apply_ops`, `definer` and `effective_input`: what the backward chains (chains.py) and the
  audits build on. Only the topmost layer defining an input fires it, a disabled source stops
  the lookup, and re-adding an active layer doesn't move it.
- `fire` applies a single input to a stack and `walk` applies a list of them from the action
  set. Order matters: the result depends on which layer is topmost for each input and on the
  execution order inside the fired array.

    walk(layout, [("switch", "left_bumper", "chord", "hold L1"),
                  ("switch", "left_bumper", "release", "let go")])

The depth-limited search of every stack (`StackSpace`, deprecated 2026-10-01) is in
archived/depth-search-and-family-walk/.
"""
from .model import defined, entries


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
