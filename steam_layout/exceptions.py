"""The exceptions register: every accepted finding, in one list.

An exception is one place where the layout breaks a rule and that is accepted,
or is a known gap that still has to end. They all live under `exceptions` in
steam_layout/flow_config.json:

    {"rule": "R139",                     the rule it is an exception to (resources/Layer Definition of Done.md)
     "scope": {...},                     what it covers; the shape depends on the rule, see below
     "status": "allow" or "todo",        accepted for good, or a gap that a to-do will close
     "why": "...",                       the reason
     "decided": "Author, 2026-10-02",    who decided it, and when
     "todo": "todos.md: ..." or null}    the to-do that ends it; required when the status is "todo"

Scope, by rule:

    R108         {"layers": [...], "inputs": [...]}                      where the Budget audit accepts a Long or Double Press
    R111         {"layers": [...], "source": "...", "activation": "...", "operations": [...], "settings": {...}}
                                                                          exact inverted-edge commands and per-variant activator settings;
                                                                          optional `command_flags` lists each command's name/beep flags in stored order
    R139, R145   {"layers": [...], "inputs": [...]}                      the Flow audit's inherited inputs
                 (`inputs` may be {"default": [...], "alternative": [...]})
                 `where` and `not_where`, optional: require or exclude a named layer in the audited layout
    R145         {"layers": [...], "dormant": true}                      retained layers with no reachable adding chain;
                                                                          reachable layers and explicit target audits are never waived
    R139         {"kind": "covers"}                                       cover layers' inherited inputs need no review
    R144         {"cover": "...", "checks": [...]}                        the cover check
    R132         {"layers": [...], "removes": [...]}                      a removal the Cleanup audit keeps: one that is never there (R132)
                                                                          or one outside the guard, such as a stateful layer (R127, R131)
                                                                          `where`, optional: only on a layout that has this layer. The frozen builders
                                                                          read this register too, so an entry for one build names a layer of that build.
                                                                          `not_where`, optional: exclude layouts that contain this layer
                                                                          `until`, optional: the last release it holds on ("90.56"), for a
                                                                          removal a later release took out with no layer to tell them apart
    R140         {"target": "...", "source": "...", "input": "..."}       a route the Window audit allows
    R130         {"layers": [...], "inputs": ["joystick/dpad_north", ...]}  an input on which the layer may hide the cleanup function below
    R136         {"kind": "touchpad"}                                     the hidden-exit pairs set aside
    R136         {"upper": "...", "lower": "..."}                         a covered side exit that was reviewed
    R169 to R171 {"layers": [...], "inputs": ["joystick/edge", ...]}      an input the layer may leave without a cleanup function
                                                                          `where` and `not_where`, optional, as for R132
    other rules  any object, for example {"note": "..."}: a record that no audit reads

The audits still read the sections they always read. `expand` fills
`decisions`, `covers.allow`, `cleanups.keep`, `cleanups.touchpad_exits`,
`cleanups.accepted_exits`, `cleanups.hidden`, `cleanups.required` and `review.covers` from the
register, and `window` adds the R140 entries to the Window audit's stacks
config, so one entry format serves all four. Titles use default-layout names, as everywhere in this file.
"""
import copy
import json
from pathlib import Path

from .rules import RULE_ID

REGISTER = Path(__file__).with_name("flow_config.json")
STATUSES = ("allow", "todo")
FIELDS = ("rule", "scope", "status", "why", "decided", "todo")
FLOW = ("R139", "R145")
REQUIRED = ("R169", "R170", "R171")                # the required-cleanup rules (steam_layout/required_cleanups.py)
SCOPES = {"R108": (("layers", "inputs"),),                                                # rule -> the shapes it takes
          "R111": (("layers", "source", "activation", "operations", "settings"),),
          "R139": (("layers", "inputs"), ("kind",)), "R145": (("layers", "inputs"), ("layers", "dormant")),
          "R144": (("cover", "checks"),), "R130": (("layers", "inputs"),), "R132": (("layers", "removes"),), "R140": (("target", "source", "input"),),
          "R136": (("kind",), ("upper", "lower")), **{rule: (("layers", "inputs"),) for rule in REQUIRED}}


def check(entries):
    """The entries, unchanged, once each has every field and a scope that fits its rule."""
    for entry in entries:
        missing = [field for field in FIELDS if field not in entry]
        if missing:
            raise ValueError(f"an exception needs {', '.join(missing)}: {entry}")
        if not RULE_ID.fullmatch(entry["rule"] or ""):
            raise ValueError(f"an exception needs a rule ID: {entry}")
        if entry["status"] not in STATUSES:
            raise ValueError(f"an exception's status is one of {STATUSES}: {entry}")
        if not entry["why"] or not entry["decided"]:
            raise ValueError(f"an exception needs a why and who decided it: {entry}")
        if entry["status"] == "todo" and not entry["todo"]:
            raise ValueError(f"an exception with status todo names the to-do that ends it: {entry}")
        scope, shapes = entry["scope"], SCOPES.get(entry["rule"])
        if not scope or (shapes and not any(all(key in scope for key in shape) for shape in shapes)):
            raise ValueError(f"{entry['rule']}: the scope needs one of {shapes or 'something'}: {entry}")
        if entry["rule"] == "R145" and "dormant" in scope:
            if scope["dormant"] is not True or not isinstance(scope.get("layers"), list) or not scope["layers"] \
                    or not all(isinstance(t, str) and t.strip() for t in scope["layers"]) or "inputs" in scope:
                raise ValueError(f"R145: a dormant scope needs exact layer titles, dormant true and no inputs: {entry}")
    return entries


def load(path=None, data=None):
    """The register's entries, checked; with a layout, as they apply to its controller (`for_layout`)."""
    entries = check(json.loads(Path(path or REGISTER).read_text(encoding="utf-8")).get("exceptions", []))
    return for_layout(entries, data) if data is not None else entries


# --- one controller's view of the register (R178 g) ---------------------------------------------

def _controller_view(data):
    """(controller, title renames, the layout's titles by default-layout names, variant mapping), or None for a
    Neptune layout (or one of no known controller): the register was written on Neptune's layouts."""
    from . import controllers
    from .convert import WHOLE_PAD_LAYERS
    from .model import map_title
    controller = controllers.of_layout(data)
    if controller is None or controller is controllers.NEPTUNE:
        return None
    cm = data["controller_mappings"]
    variant = "alternative" if "alternative" in cm.get("title", "") else "default"
    mapping = json.loads(REGISTER.read_text(encoding="utf-8")).get("variants", {}).get(variant, {})
    back = {new: old for old, new in mapping.items()}
    present = {map_title(v["title"], back) for section in ("actions", "action_layers") for v in cm[section].values()}
    renames = WHOLE_PAD_LAYERS if controller.whole_pad else {}
    return controller, renames, present, mapping


def _input(text, controller):
    """A register input, `source/input`, on the controller: moved (R181, R183) or None if absent (R178)."""
    from .convert import moved
    source, _, name = text.partition("/")
    now = moved(controller, (source, name))
    return f"{now[0]}/{now[1]}" if now else None


def _entry_view(entry, view):
    """One entry on a converted controller, or None where it names nothing the layout has."""
    from . import controllers
    controller, renames, present, _ = view
    if entry["rule"] == "R169" and any(controller.lacks(*touch) for touch in (("joystick", "touch"),
                                                                              ("right_joystick", "touch"))):
        return None                                      # R178 (g): no stick touch, no rule about it
    split = controllers.NEPTUNE.built_until
    if "until" in entry["scope"] and controllers.version_key(entry["scope"]["until"]) <= controllers.version_key(split):
        return None                                      # it ended on Neptune's line, before the base layout (R177)
    scope = copy.deepcopy(entry["scope"])

    def title(name):
        name = renames.get(name, name)
        return name if name in present else None

    for key in ("layers", "removes"):
        if key in scope:
            scope[key] = [t for t in map(title, scope[key]) if t]
            if not scope[key]:
                return None
    for key in ("target", "upper", "lower", "cover", "where"):
        if key in scope:
            scope[key] = title(scope[key])
            if scope[key] is None:
                return None
    if "not_where" in scope and title(scope["not_where"]) is None:
        del scope["not_where"]                           # the layer it excludes is not there: nothing to exclude
    elif "not_where" in scope:
        scope["not_where"] = title(scope["not_where"])
    if "operations" in scope:
        if any(title(t) is None for _, t in scope["operations"]):
            return None
        scope["operations"] = [[op, title(t)] for op, t in scope["operations"]]
    if entry["rule"] == "R140":
        now = _input(f"{scope['source']}/{scope['input']}", controller)
        if now is None:
            return None
        scope["source"], scope["input"] = now.split("/", 1)
    if "inputs" in scope:
        def inputs(listed):
            return [now for now in (_input(text, controller) for text in listed) if now]
        if isinstance(scope["inputs"], dict):
            scope["inputs"] = {variant: inputs(listed) for variant, listed in scope["inputs"].items()}
            if not any(scope["inputs"].values()):
                return None
        else:
            scope["inputs"] = inputs(scope["inputs"])
            if not scope["inputs"]:
                return None
    return {**entry, "scope": scope}


def for_layout(entries, data):
    """The entries as they apply to a layout's controller. Neptune: unchanged; the register was written on its
    layouts. Ibex and the conversions: an entry whose `until` release is on Neptune's line before the base layout is
    over (R177). A conversion such as the DualSense Edge's also has titles renamed as the conversion renames them
    (the left pad's layers to the whole pad's), inputs moved as it moves them (the grips, the left pad), and what the
    layout lacks left out: a layer it deleted, an absent input, and R169 where there is no stick touch (R178 g). An
    entry left naming nothing is dropped."""
    view = _controller_view(data)
    if view is None:
        return entries
    return [kept for kept in (_entry_view(entry, view) for entry in entries) if kept is not None]


def stacks_for_layout(stacks_config, data):
    """The Window audit's declared targets and stacks (steam_layout/traced_stacks.json) for a layout's controller,
    as `for_layout` does for the register: renamed, and without a target or stack the layout lacks."""
    view = _controller_view(data)
    if view is None:
        return stacks_config
    controller, renames, present, _ = view
    config = copy.deepcopy(stacks_config)
    targets = {}
    for target, spec in config.get("targets", {}).items():
        target = renames.get(target, target)
        if target not in present:
            continue
        rows = []
        for row in spec.get("stacks", []):
            layers = [renames.get(t, t) for t in row["layers"]]
            condition = row.get("when_inherited")
            if any(t not in present for t in layers) or (condition and controller.lacks(condition["source"],
                                                                                         condition["input"])):
                continue
            rows.append({**row, "layers": layers})
        targets[target] = {**spec, "stacks": rows}
    config["targets"] = targets
    return config


def of(entries, rule):
    """The entries for one rule."""
    return [entry for entry in entries if entry["rule"] == rule]


def expand(config, data=None):
    """A copy of `config` with the sections the audits read filled in from its `exceptions`, as they apply to the
    layout `data` when given (`for_layout`)."""
    config = copy.deepcopy(config)
    entries = check(config.get("exceptions", []))
    for entry in (for_layout(entries, data) if data is not None else entries):
        scope, rule = entry["scope"], entry["rule"]
        if rule == "R139" and scope.get("kind") == "covers":
            config.setdefault("review", {})["covers"] = entry["why"]
        elif rule == "R145" and scope.get("dormant"):
            config.setdefault("dormant_layers", []).append(
                {"layers": scope["layers"], "status": entry["status"], "why": entry["why"], "todo": entry["todo"]})
        elif rule in FLOW:
            config.setdefault("decisions", []).append(
                {"layers": scope["layers"], "inputs": scope["inputs"], "status": entry["status"], "why": entry["why"],
                 **{key: scope[key] for key in ("where", "not_where") if key in scope}})
        elif rule == "R144":
            config.setdefault("covers", {}).setdefault("allow", []).append(
                {"cover": scope["cover"], "checks": scope["checks"], "reason": entry["why"]})
        elif rule == "R132":
            config.setdefault("cleanups", {}).setdefault("keep", []).append(
                {"layers": scope["layers"], "removes": scope["removes"], "why": entry["why"],
                 **{key: scope[key] for key in ("where", "not_where", "until") if key in scope}})
        elif rule == "R130":
            config.setdefault("cleanups", {}).setdefault("hidden", []).append(
                {"layers": scope["layers"], "inputs": scope["inputs"], "why": entry["why"]})
        elif rule == "R136" and scope.get("kind") == "touchpad":
            config.setdefault("cleanups", {})["touchpad_exits"] = entry["why"]
        elif rule == "R136" and "upper" in scope:
            config.setdefault("cleanups", {}).setdefault("accepted_exits", []).append(
                {"upper": scope["upper"], "lower": scope["lower"], "why": entry["why"]})
        elif rule in REQUIRED:
            config.setdefault("cleanups", {}).setdefault("required", []).append(
                {"rule": rule, "layers": scope["layers"], "inputs": scope["inputs"], "why": entry["why"],
                 **{key: scope[key] for key in ("where", "not_where") if key in scope}})
    return config


def load_config(path=None, data=None):
    """The rules file with its exceptions expanded: what the Flow, cover and Cleanup audits read. With a layout,
    the exceptions as they apply to its controller (`for_layout`)."""
    return expand(json.loads(Path(path or REGISTER).read_text(encoding="utf-8")), data)


def window(stacks_config, entries):
    """A copy of the Window audit's stacks config with the register's R140 routes as its decisions."""
    config = copy.deepcopy(stacks_config)
    for entry in of(check(entries), "R140"):
        scope = entry["scope"]
        config.setdefault("targets", {}).setdefault(scope["target"], {}).setdefault("decisions", []).append(
            {"source": scope["source"], "input": scope["input"], "status": entry["status"], "why": entry["why"]})
    return config
