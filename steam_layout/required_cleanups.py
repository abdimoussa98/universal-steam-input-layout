"""The Cleanup audit's three "required cleanup" checks: where a layer must have a cleanup function.

The author's rules (2026-10-04). A layer has a cleanup function in three places:

    R169  both stick touches     every layer, covers included
    R170  the stick edges        an edge the layer binds or blocks; both edges when the layer
                                 binds or blocks a face button, a D-pad direction, Start, Select
                                 or a back button
    R171  the buttons            every button the layer retypes or blocks: those, the bumpers,
                                 and each trigger's pull and full pull

A cleanup function on an input is a guarded recovery there that removes the layer itself
(cleanups.py, flow_model role "recovery"; its shape is R133).

Left out of all three: an Always On window, a stateful layer and a ramp layer (one that no
button, thumb or stick keeps on: a cancellation or a return to centre ends it). The six stick-touch helpers are left
out of R169 only. R171 also leaves out the layer's own button (its Release removes the layer)
and a button that removes the layer by cancellation (R135), as in the Temp Cursor layers.

How a layer answers an input:

    open       no group for the source, or the input isn't defined: it comes from below
    cleanup    a cleanup function that removes the layer
    own        a Release that removes the layer
    cancel     a cancellation that removes the layer
    empty      only empty bindings: a block
    bound      anything else
    disabled   the layer's group for the source is disabled

A block is counted like a retype (author, 2026-10-04). The check also says when a blocked
button covers nothing: no layer the chains put under this one, and not the action set, binds
that input.

Not modelled: a group in another mode than the layer below also blocks the input (A2). That
depends on the stack, so the hidden-exit check reads it (R136), not these three.

Exceptions are register entries for R169, R170 or R171 with the scope
{"layers": [...], "inputs": ["joystick/edge", ...]} (steam_layout/exceptions.py fills
`cleanups.required` from them). An entry that matches no finding is reported as stale.

The six list checks and the two exit checks are in cleanups.py; tools/audit_cleanups.py prints
all eleven. Suggested fixes for 90.23: findings/2026-10-04-required-cleanups/.
"""
from collections import defaultdict

from .flow_model import DIRECTIONS, is_clear
from .model import defined, map_title

TOUCH, EDGE, BUTTON = "touch without cleanup", "edge without cleanup", "button without cleanup"
CHECKS = (TOUCH, EDGE, BUTTON)
ENFORCES = {TOUCH: ("R169",), EDGE: ("R170",), BUTTON: ("R171",)}             # check -> rules
RULE = {check: ids[0] for check, ids in ENFORCES.items()}

STICKS = ("joystick", "right_joystick")
TOUCHES = tuple((stick, "touch") for stick in STICKS)
EDGES = tuple((stick, "edge") for stick in STICKS)
FACE = tuple(("button_diamond", button) for button in ("button_a", "button_b", "button_x", "button_y"))
DPAD = tuple(("dpad", direction) for direction in DIRECTIONS)
MENU = (("switch", "button_escape"), ("switch", "button_menu"))
BACK = tuple(("switch", button) for button in ("button_back_left_upper", "button_back_left",
                                               "button_back_right_upper", "button_back_right"))
BUMPERS = (("switch", "left_bumper"), ("switch", "right_bumper"))
TRIGGERS = tuple((trigger, name) for trigger in ("left_trigger", "right_trigger") for name in ("edge", "click"))
EDGE_BUTTONS = FACE + DPAD + MENU + BACK        # binding or blocking one of these asks for both stick edges (R170)
BUTTONS = EDGE_BUTTONS + BUMPERS + TRIGGERS     # the buttons of R171

LABELS = dict(zip(TOUCHES + EDGES + BUTTONS, (
    "left-stick touch", "right-stick touch", "left-stick edge", "right-stick edge", "A", "B", "X", "Y",
    "D-pad up", "D-pad right", "D-pad down", "D-pad left", "Start", "Select", "L4", "L5", "R4", "R5", "LB", "RB",
    "LT pull", "LT full pull", "RT pull", "RT full pull")))
LEFT_OUT = {"timer": "window", "mode": "stateful", "other": "ramp", "thumb": "helper"}    # keeper kind -> layer type
EVERY_RULE = ("window", "stateful", "ramp")     # the types all three rules leave out; a helper only R169
PASSES = ("open", "cleanup", "own", "cancel")   # the states R171 accepts on a button
REASON = {
    TOUCH: {"open": "it leaves this touch to the layer below", "disabled": "its group for this stick is disabled",
            None: "it binds this touch without a cleanup function"},
    EDGE: {"open": "it binds or blocks a button and leaves this edge open",
           "empty": "it blocks this edge with an empty binding", "disabled": "its group for this stick is disabled",
           None: "it binds this edge without a cleanup function"},
    BUTTON: {"empty": "it blocks this button with an empty binding", "disabled": "its group for this button is disabled",
             None: "it retypes this button without a cleanup function"}}
NOTHING = "it blocks this button with an empty binding that covers nothing"


def label(control):
    return LABELS.get(tuple(control), "/".join(control))


def state(c, layer, control):
    """How `layer` answers one input: open, disabled, cleanup, own, cancel, empty or bound (see the module text)."""
    source, name = control
    group = c.layout.active(layer).get(source)
    if group is None:
        return "open"
    if group["mode"] == "disabled":
        return "disabled"
    if not defined(group, name):
        return "open"
    roles = {t.role for t in c.inv.by_layer(layer) if t.control == control and ("remove_layer", layer) in t.ops}
    for role, found in (("recovery", "cleanup"), ("cancel", "cancel"), ("release", "own")):
        if role in roles:
            return found
    return "empty" if is_clear(group["inputs"][name]["activators"]) else "bound"


def left_out(c, layer):
    """The type that leaves `layer` out: window, stateful, ramp or helper. None for every other layer.

    A ramp layer has no keeper and ends on a threshold: a cancellation or a return to centre removes it.
    A layer with no keeper and no such exit is not left out, so a layer nothing ends still fails."""
    kind = LEFT_OUT.get(c.keeper(layer)[0])
    if kind == "ramp" and not any(t.role in ("cancel", "center") and ("remove_layer", layer) in t.ops
                                  for t in c.inv.by_layer(layer)):
        return None
    return kind


def bound_below(c, layer, control):
    """The layers that can be under `layer`, and the action set, that bind this input with more than a block."""
    source, name = control
    found = []
    for lower in [c.base] + sorted(c.below(layer)):
        group = c.layout.active(lower).get(source)
        if group and group["mode"] != "disabled" and defined(group, name) \
                and not is_clear(group["inputs"][name]["activators"]):
            found.append(lower)
    return found


def missing(c, only=None):
    """[(check, layer, control, state, reason)]: every input that needs a cleanup function and has none."""
    rows = []
    for layer in c.layers:
        kind = left_out(c, layer)
        if kind in EVERY_RULE or not c.reached(layer) or (only and layer not in only):
            continue
        states = {control: state(c, layer, control) for control in TOUCHES + EDGES + BUTTONS}

        def add(check, control, reason=None):
            rows.append((check, layer, control, states[control],
                         reason or REASON[check].get(states[control], REASON[check][None])))

        if kind != "helper":
            for control in TOUCHES:
                if states[control] != "cleanup":
                    add(TOUCH, control)
        overrides = any(states[button] != "open" for button in EDGE_BUTTONS)
        for control in EDGES:
            if states[control] != "cleanup" and (overrides or states[control] != "open"):
                add(EDGE, control)
        for control in BUTTONS:
            if states[control] not in PASSES:
                nothing = states[control] == "empty" and not bound_below(c, layer, control)
                add(BUTTON, control, NOTHING if nothing else None)
    return rows


def excepted(config, variant):
    """{(rule, layer, "source/input"): why} from the config's `cleanups.required`, which the register fills."""
    mapping = config.get("variants", {}).get(variant, {})
    result = {}
    for decision in config.get("cleanups", {}).get("required", []):
        if not decision.get("why"):
            raise ValueError(f"an exception needs a why: {decision}")
        for layer in decision["layers"]:
            for name in decision["inputs"]:
                result[(decision["rule"], map_title(layer, mapping), name)] = decision["why"]
    return result


def audit(c, config=None, only=None):
    """The three checks' report for one layout. `c` is its Cleanups (cleanups.py), for the keepers and the chains.

    Findings are grouped: one for each (check, layer, reason), with the inputs it is on. The keys match the
    Cleanup audit's, so tools/audit_cleanups.py can print the two reports as one.
    """
    variant = "alternative" if "alternative" in c.layout.cm.get("title", "") else "default"
    decided = excepted(config or {}, variant)
    used, grouped, set_aside = set(), defaultdict(list), []
    for check, layer, control, found, reason in missing(c, only):
        key = (RULE[check], layer, "/".join(control))
        if key in decided:
            used.add(key)
            set_aside.append({"check": check, "layer": layer, "input": label(control), "control": key[2],
                              "why": decided[key]})
        else:
            grouped[(check, layer, reason)].append((control, found))
    findings = []
    for (check, layer, reason), rows in grouped.items():
        kind, keep = c.keeper(layer)
        findings.append({"check": check, "layer": layer, "target": None, "kind": "layer", "reason": reason,
                         "inputs": [label(control) for control, _ in rows],
                         "controls": ["/".join(control) for control, _ in rows],
                         "states": sorted({found for _, found in rows}), "bindings": len(rows), "guard": [],
                         "keeper": " ".join(filter(None, [kind, "+".join(sorted(keep))])),
                         "example": f"{layer} {'/'.join(rows[0][0])}"})
    order = {check: index for index, check in enumerate(CHECKS)}
    findings.sort(key=lambda f: (order[f["check"]], c.layers.index(f["layer"]), f["reason"]))
    types = defaultdict(list)
    for layer in c.layers:
        if left_out(c, layer):
            types[left_out(c, layer)].append(layer)
    return {"ok": not findings, "findings": findings,
            "counts": {check: {"findings": sum(1 for f in findings if f["check"] == check),
                               "bindings": sum(f["bindings"] for f in findings if f["check"] == check)}
                       for check in CHECKS},
            "excepted": set_aside, "left_out": dict(types),
            "stale_decisions": [] if only else [f"{rule}: {layer} on {name}" for rule, layer, name in sorted(set(decided) - used)]}
