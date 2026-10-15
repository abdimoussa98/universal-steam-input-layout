"""Conversions: Neptune's and the DualSense Edge's layouts made from an Ibex release (R177).

Ibex, the Steam Controller 2, is the base layout. Every other controller's layout is made from an Ibex release by
that controller's rules, one function each below, and never edited by hand (Layer Definition of Done section 12):

    R179  neptune  `header` and `gyro_style`: Neptune's Steam names and Yaw + Roll in every gyro-to-mouse group
    R180  dse      `header`: the Edge's Steam names; the gyro style stays Player Space
    R181  dse      `swap_grips`: L4 with L5, R4 with R5
    R183  dse      `whole_pad`: the left pad's role goes to the whole touchpad, with six CTP: layers
    R182  dse      `drop_absent`: no stick touch (R178 a to e), and no right pad (R183)
    R184  dse      `mute`: the mute button is the middle mouse button
    R185  dse      `gyro_always_on`: no gyro enable mask
    R178  all      `delete_unreachable`: (f) a layer the layout can no longer reach goes, with every command naming it

    data, report = convert.convert(ibex, "dse", "default", "1.0")          # a new dict; `ibex` is not changed
    text = convert.dumps(data)                                              # as written to dse/*_latest.json

`ibex` is a layout dict with numeric runtime IDs, as the snapshots are; the result is one too. The rules work on
layer titles, and the order is renumbered at the end (R104). As a build does, the conversion ends with the fix
pipeline (steam_layout.fixes), and the result is a fixed point of it (R152). The registry
(steam_layout/controllers.py) holds what the rules read: each controller's header values, absent inputs, swaps and
gyro style. `report` lists what a rule left for the author: a gyro enable mask or an inverted chord it would not
rewrite (R178 b, c, e), and what it deleted.

Plan: plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4.
"""
import copy
import json
import re

from . import controllers
from .model import MODE_SHIFT, actions, entries

# What a chord names, as (source, input): the legacy `chord_button` IDs and the mask bits
# (resources/Neptune Chorded Button Ids.md, resources/Controllers.md). Bits 30 and 31 are a stick's deflection,
# which every controller has.
CHORD_INPUTS = {"1": ("switch", "left_bumper"), "2": ("switch", "right_bumper"), "5": ("left_trigger", "click"),
                "6": ("right_trigger", "click"), "7": ("left_trigger", "edge"), "8": ("right_trigger", "edge"),
                "9": ("joystick", "click"), "14": ("switch", "button_escape"), "15": ("switch", "button_menu"),
                "16": ("left_trackpad", "touch"), "17": ("right_trackpad", "touch"),
                "20": ("right_joystick", "click"), "23": ("joystick", "touch"), "24": ("right_joystick", "touch")}
CHORD_IDS = {control: chord for chord, control in CHORD_INPUTS.items()}
BIT_INPUTS = {0: ("right_trigger", "click"), 1: ("left_trigger", "click"), 2: ("switch", "right_bumper"),
              3: ("switch", "left_bumper"), 4: ("button_diamond", "button_y"), 5: ("button_diamond", "button_b"),
              6: ("button_diamond", "button_x"), 7: ("button_diamond", "button_a"), 8: ("dpad", "dpad_north"),
              9: ("dpad", "dpad_east"), 10: ("dpad", "dpad_west"), 11: ("dpad", "dpad_south"),
              12: ("switch", "button_menu"), 14: ("switch", "button_escape"), 15: ("switch", "button_back_left"),
              16: ("switch", "button_back_right"), 17: ("left_trackpad", "click"), 18: ("right_trackpad", "click"),
              19: ("left_trackpad", "touch"), 20: ("right_trackpad", "touch"), 22: ("joystick", "click"),
              24: ("right_trigger", "edge"), 25: ("left_trigger", "edge"), 26: ("right_joystick", "click"),
              27: ("center_trackpad", "touch"), 28: ("center_trackpad", "click"), 29: ("switch", "button_capture"),
              41: ("switch", "button_back_left_upper"), 42: ("switch", "button_back_right_upper"),
              46: ("joystick", "touch"), 47: ("right_joystick", "touch")}
BITS = {control: bit for bit, control in BIT_INPUTS.items()}
DEFLECT = {30: "joystick", 31: "right_joystick"}
MASK, ANY_OR_ALL = "gyro_ratchet_button_mask", "gyro_ratchet_button_requireany_or_all"
INVERT = "edge_binding_invert"                        # on a chord's own settings: Invert Activation (A61)
EMPTY = "controller_action empty_binding, , "
COMMAND = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) \{\{(?:[^:}]+::)?(.+?)\}\}")

# R183: the left pad's six layers and the whole pad's, made from them (the layer keeps its place, R104).
WHOLE_PAD_LAYERS = {"LTP: Click Entry Point": "CTP: Click Entry Point", "LTP: Arrow Keys": "CTP: Arrow Keys",
                    "Escape": "CTP: Escape", "Enter": "CTP: Enter", "Tab": "CTP: Tab", "Backspace": "CTP: Backspace"}
CENTRE_PRESS_TARGET = "LTP: Middle Click"          # what the Click Entry Point's centre press adds; not on the Edge
SOFT_ONLY = ("activation_threshold", "soft_press_sytle", INVERT)      # Soft Press settings a Regular Press has not
MUTE = "mouse_button MIDDLE, , "


class Report(list):
    """What the conversion left for the author or deleted, one line each."""

    def add(self, rule, text):
        self.append(f"{rule}: {text}")


# --- the layout, by title ----------------------------------------------------------------------

def readable(data):
    """A copy with every layer command naming its layer by title, `{{Base::Title}}`."""
    from tools.convert_runtime_ids import generate_lookup, ids_to_titles
    text, _ = ids_to_titles(json.dumps(data), generate_lookup(data))
    return json.loads(text)


def dumps(data):
    """The layout as a working file holds it: numeric runtime IDs, tab-indented, as the builders write it."""
    from tools.convert_runtime_ids import generate_lookup, titles_to_ids
    text, _ = titles_to_ids(json.dumps(data, indent="\t") + "\n", generate_lookup(data))
    if "{{" in text:
        raise ValueError("a layer command names no layer of the layout")
    return text


def titles(data):
    """{Preset key: title} for the action set and every layer."""
    cm = data["controller_mappings"]
    return {key: value["title"] for section in ("actions", "action_layers") for key, value in cm[section].items()}


def sources(data):
    """{group id: source}, from the preset bindings. A group is bound to one source."""
    found = {}
    for preset in data["controller_mappings"]["preset"]:
        for gid, state in preset["group_source_bindings"].items():
            source = state.split(" ")[0]
            if found.setdefault(gid, source) != source:
                raise ValueError(f"group {gid} is bound to {found[gid]} and {source}")
    return found


def activators(group):
    """(input name, activation type, entry) for every activator of a group, in order."""
    for name, value in (group.get("inputs") or {}).items():
        for kind, entry in entries((value or {}).get("activators") or {}):
            yield name, kind, entry


def keep_activators(value, keep):
    """Keep the activators of one input for which `keep(kind, entry)` is true, in place; True if any is left."""
    kept = {}
    for kind, found in (value.get("activators") or {}).items():
        listed = found if isinstance(found, list) else [found]
        left = [entry for entry in listed if keep(kind, entry)]
        if left:
            kept[kind] = left if isinstance(found, list) and len(left) > 1 else left[0]
    value["activators"] = kept
    return bool(kept)


def rename_key(mapping, old, new):
    """`mapping` with key `old` called `new`, in the same place."""
    return {(new if key == old else key): value for key, value in mapping.items()}


# --- R179, R180: the header and the gyro style --------------------------------------------------

def header(data, controller, variant, version):
    """The controller's Steam names, Workshop link and description, and `version` at the end of the title."""
    cm = data["controller_mappings"]
    cm["title"] = cm["title"].rsplit(" :: ", 1)[0] + f" :: {version}"
    cm["description"] = controller.descriptions[variant]
    cm["controller_type"] = controller.controller_type
    cm["controller_caps"] = controller.controller_caps
    cm["url"] = controller.urls[variant]


def gyro_style(data, style):
    """`gyro_to_2d_conversion_style` in every gyro-to-mouse group; the number of groups."""
    groups = [group for group in data["controller_mappings"]["group"] if group["mode"] == "gyro_to_mouse"]
    for group in groups:
        group.setdefault("settings", {})["gyro_to_2d_conversion_style"] = str(style)
    return len(groups)


# --- what an input becomes on a controller --------------------------------------------------

def moved(controller, control):
    """Where an Ibex input is on `controller`: the same, swapped (R181), on the whole pad (R183), or None if absent."""
    source, name = control
    if controller.lacks(source, name):
        return None
    for one, other in controller.swaps:
        if control == one:
            return other
        if control == other:
            return one
    if controller.whole_pad and source == "left_trackpad":
        return "center_trackpad", name
    return control


def chord(settings, controller, report, where):
    """The settings of a chord, or of a gyro group's enable mask, on `controller`: (settings, keep).

    A chord button that moved is named where it is now, as a mask bit when it has no `chord_button` ID (R180).
    An absent one follows R178: (b) an any-of mask loses it; (c) an all-of mask, or a one-button chord, with one
    absent is dropped (keep False), or listed if it is a gyro mask (`where` says so) or (e) the chord is inverted;
    (d) a stick touch goes from an all-of mask that also needs that stick's deflection (A74)."""
    gyro = where.startswith("gyro")
    if "chord_button" in settings:
        control = CHORD_INPUTS.get(settings["chord_button"])
        if control is None:
            return settings, True
        now = moved(controller, control)
        if now == control:
            return settings, True
        if now is None:
            if settings.get(INVERT) == "1":
                report.add("R178 (e)", f"{where}: an inverted chord on {control[0]}/{control[1]}, not rewritten")
                return settings, True
            return settings, False
        if now in CHORD_IDS:
            return {**settings, "chord_button": CHORD_IDS[now]}, True
        changed = {}
        for key, value in settings.items():                  # the mask takes the chord button's place
            if key == "chord_button":
                changed[MASK], changed[ANY_OR_ALL] = str(1 << BITS[now]), "0"
            else:
                changed[key] = value
        return changed, True
    if MASK not in settings:
        return settings, True
    mask, every = int(settings[MASK]), settings.get(ANY_OR_ALL) == "1"
    kept, absent = 0, []
    for bit in range(64):
        if not mask >> bit & 1:
            continue
        if bit in DEFLECT or bit not in BIT_INPUTS:
            kept |= 1 << bit
            continue
        now = moved(controller, BIT_INPUTS[bit])
        if now is None:
            absent.append(bit)
        else:
            kept |= 1 << BITS[now]
    if not absent:
        return ({**settings, MASK: str(kept)} if kept != mask else settings), True
    if every:
        stuck = [bit for bit in absent
                 if not (BIT_INPUTS[bit][1] == "touch" and BIT_INPUTS[bit][0] in DEFLECT.values()
                         and kept >> next(d for d, stick in DEFLECT.items() if stick == BIT_INPUTS[bit][0]) & 1)]
        if not stuck:                                          # (d): each absent touch's stick deflection is needed
            return {**settings, MASK: str(kept)}, True
    elif kept:                                                 # (b)
        return {**settings, MASK: str(kept)}, True
    if gyro or settings.get(INVERT) == "1":                     # (c) for a gyro mask, (e)
        rule = "R178 (c)" if gyro else "R178 (e)"
        report.add(rule, f"{where}: a mask on absent inputs, not changed")
        return settings, True
    return settings, False


# --- R181: the grips -----------------------------------------------------------------------------

def swap_grips(data, controller):
    """Each pair of `controller.swaps` trades places in every group bound to their source, with everything bound to
    them. The input keeps its place in the group. Returns the number of groups changed."""
    of = sources(data)
    changed = 0
    for group in data["controller_mappings"]["group"]:
        inputs = group.get("inputs") or {}
        partner = {}
        for (source, one), (_, other) in controller.swaps:
            if of.get(group["id"]) == source:
                partner.update({one: other, other: one})
        if not partner.keys() & inputs.keys():
            continue
        swapped = {}
        for key, value in inputs.items():
            if key not in partner:
                swapped[key] = value
            elif partner[key] in inputs:
                swapped[key] = inputs[partner[key]]          # both bound: the binds trade places
            else:
                swapped[partner[key]] = value                # one bound: it moves to the other, in the same place
        group["inputs"] = swapped
        changed += 1
    return changed


# --- R183: the whole pad ------------------------------------------------------------------------

def whole_pad(data, report):
    """The left pad's binds go to the whole pad in every layer; the left pad's six layers become the CTP: layers,
    whose Click Entry Point has no centre press; every click on the whole pad is a Regular Press. Chords on the left
    pad's touch become the whole pad's mask bit in `drop_absent`, with the other chords."""
    cm = data["controller_mappings"]
    for preset in cm["preset"]:
        preset["group_source_bindings"] = {
            gid: ("center_trackpad" + state[len("left_trackpad"):] if state.split(" ")[0] == "left_trackpad" else state)
            for gid, state in preset["group_source_bindings"].items()}
    names = titles(data)
    for key, value in cm["action_layers"].items():
        if value["title"] in WHOLE_PAD_LAYERS:
            value["title"] = WHOLE_PAD_LAYERS[value["title"]]
    rename_commands(data, WHOLE_PAD_LAYERS)
    missing = set(WHOLE_PAD_LAYERS) - set(names.values())
    if missing:
        raise ValueError(f"the left pad's layers are not all there: {sorted(missing)}")
    groups = {group["id"]: group for group in cm["group"]}
    of = sources(data)
    entry = next(p for p in cm["preset"] if names[p["name"]] == "LTP: Click Entry Point")
    for gid, state in entry["group_source_bindings"].items():
        if state != "center_trackpad active":
            continue
        group = groups[gid]
        for name, value in (group.get("inputs") or {}).items():
            keep_activators(value, lambda kind, item: not any(
                op == "add_layer" and target == CENTRE_PRESS_TARGET for op, target in COMMAND.findall(" ".join(actions(item)))))
        ring = group["inputs"].get("edge", {}).get("activators", {}).get("Soft_Press")
        if isinstance(ring, dict) and "activation_threshold" in ring.get("settings", {}):
            # The ring press was a Soft Press past a threshold; as a Regular Press the ring is the group's outer ring.
            group.setdefault("settings", {})["edge_binding_radius"] = ring["settings"]["activation_threshold"]
            group["inputs"]["edge"]["activators"] = rename_key(group["inputs"]["edge"]["activators"], "Soft_Press",
                                                               "Full_Press")
            ring["settings"] = {k: v for k, v in ring["settings"].items() if k not in SOFT_ONLY}
            report.add("R183", "CTP: Click Entry Point: the ring press is a Regular Press, the ring at "
                               f"{group['settings']['edge_binding_radius']}; no centre press")
    for group in cm["group"]:
        if of.get(group["id"]) != "center_trackpad":
            continue
        value = (group.get("inputs") or {}).get("click")
        found = (value or {}).get("activators", {})
        if "Soft_Press" not in found:
            continue
        if "Full_Press" in found:
            raise ValueError(f"group {group['id']}: a click with a Regular Press and a Soft Press")
        for item in found["Soft_Press"] if isinstance(found["Soft_Press"], list) else [found["Soft_Press"]]:
            if "settings" in item:
                item["settings"] = {k: v for k, v in item["settings"].items() if k not in SOFT_ONLY}
        value["activators"] = rename_key(found, "Soft_Press", "Full_Press")


def rename_commands(data, renames):
    """Every layer command naming an old title names the new one."""
    for group in data["controller_mappings"]["group"]:
        for _, _, entry in activators(group):
            binding = entry.get("bindings", {}).get("binding")
            if binding is None:
                continue
            listed = binding if isinstance(binding, list) else [binding]
            new = [re.sub(r"\{\{([^:}]+::)?(.+?)\}\}",
                          lambda m: "{{" + (m.group(1) or "") + renames.get(m.group(2), m.group(2)) + "}}", b)
                   for b in listed]
            entry["bindings"]["binding"] = new if isinstance(binding, list) else new[0]


# --- R182 (R178 a to e): absent inputs ---------------------------------------------------------

def drop_absent(data, controller, report):
    """Binds on an absent source or input go (a); chords and gyro masks follow `chord` (b to e). Groups no layer
    binds any more go too. Returns the number of activators dropped."""
    cm = data["controller_mappings"]
    names = titles(data)
    of = sources(data)
    owner = {}
    for preset in cm["preset"]:
        for gid in preset["group_source_bindings"]:
            owner.setdefault(gid, names[preset["name"]])
        preset["group_source_bindings"] = {gid: state for gid, state in preset["group_source_bindings"].items()
                                           if state.split(" ")[0] not in controller.absent_sources}
    dropped = 0
    for group in cm["group"]:
        source = of.get(group["id"])
        where = f"{owner.get(group['id'], '?')} / {source}"
        if group["mode"] == "gyro_to_mouse" and MASK in group.get("settings", {}):
            group["settings"], _ = chord(group["settings"], controller, report, "gyro " + where)
        inputs = group.get("inputs") or {}
        for name in list(inputs):
            if source in controller.absent_sources or controller.lacks(source, name):
                dropped += sum(1 for _ in entries((inputs[name] or {}).get("activators") or {}))
                del inputs[name]
                continue

            def keep(kind, entry, name=name):
                nonlocal dropped
                if "settings" not in entry:
                    return True
                entry["settings"], kept = chord(entry["settings"], controller, report, f"{where} {name} {kind}")
                dropped += not kept
                return kept
            if not keep_activators(inputs[name], keep):
                del inputs[name]
    used = {gid for preset in cm["preset"] for gid in preset["group_source_bindings"]}
    cm["group"] = [group for group in cm["group"] if group["id"] in used]
    return dropped


# --- R184: the mute button ----------------------------------------------------------------------

def mute(data, controller):
    """Base binds the mute button to the middle mouse button with a Regular Press."""
    cm = data["controller_mappings"]
    base = cm["preset"][0]
    groups = {group["id"]: group for group in cm["group"]}
    (gid,) = [gid for gid, state in base["group_source_bindings"].items() if state == "switch active"]
    groups[gid].setdefault("inputs", {})[controller.mute] = {
        "activators": {"Full_Press": {"bindings": {"binding": MUTE}}}, "disabled_activators": {}}


# --- R185: gyro always on -----------------------------------------------------------------------

def gyro_always_on(data):
    """The enable mask comes off every gyro-to-mouse group; the layers whose groups lost one, by title."""
    names = titles(data)
    owners = {}
    for preset in data["controller_mappings"]["preset"]:
        for gid in preset["group_source_bindings"]:
            owners.setdefault(gid, []).append(names[preset["name"]])
    changed = []
    for group in data["controller_mappings"]["group"]:
        settings = group.get("settings") or {}
        if group["mode"] == "gyro_to_mouse" and MASK in settings:
            settings.pop(MASK)
            settings.pop(ANY_OR_ALL, None)
            changed.extend(owners.get(group["id"], []))
    return changed


# --- R178 (f): layers that can no longer be reached ---------------------------------------------

def reachable(data):
    """The titles a chain of add_layer or hold_layer binds reaches from the action set, over every active and
    mode-shift group, chords included."""
    cm = data["controller_mappings"]
    names = titles(data)
    groups = {group["id"]: group for group in cm["group"]}
    adds = {}
    for preset in cm["preset"]:
        found = adds.setdefault(names[preset["name"]], set())
        for gid, state in preset["group_source_bindings"].items():
            rest = state.partition(" ")[2]
            if rest != "active" and "modeshift" not in rest:
                continue
            for _, _, entry in activators(groups[gid]):
                for op, target in COMMAND.findall(" ".join(actions(entry))):
                    if op != "remove_layer":
                        found.add(target)
    base = names[cm["preset"][0]["name"]]
    seen, queue = {base}, [base]
    while queue:
        for target in adds.get(queue.pop(), ()):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def delete_unreachable(data, report):
    """Delete every layer no chain reaches, with every command that names it, keeping the order (R104). An activator
    left with no command blocks its input with an empty binding, as it blocked it before. Returns the titles."""
    cm = data["controller_mappings"]
    names = titles(data)
    reached = reachable(data)
    gone = [title for key, title in names.items() if key in cm["action_layers"] and title not in reached]
    if not gone:
        return []
    keys = {key for key, title in names.items() if title in gone}
    cm["action_layers"] = {key: value for key, value in cm["action_layers"].items() if key not in keys}
    cm["preset"] = [preset for preset in cm["preset"] if preset["name"] not in keys]
    for index, preset in enumerate(cm["preset"]):
        preset["id"] = str(index)
    used = {gid for preset in cm["preset"] for gid in preset["group_source_bindings"]}
    cm["group"] = [group for group in cm["group"] if group["id"] in used]
    for group in cm["group"]:
        for _, _, entry in activators(group):
            binding = entry.get("bindings", {}).get("binding")
            if binding is None:
                continue
            listed = binding if isinstance(binding, list) else [binding]
            left = [b for b in listed if not any(target in gone for _, target in COMMAND.findall(b))]
            if len(left) == len(listed):
                continue
            if not left:
                left = [EMPTY]
                report.add("R178 (f)", f"group {group['id']}: a bind that named only deleted layers is a block")
            entry["bindings"]["binding"] = left if len(left) > 1 else left[0]
    for title in gone:
        report.add("R178 (f)", f"deleted {title}")
    return gone


# --- the conversions ------------------------------------------------------------------------

def convert(ibex, name, variant, version):
    """The layout of controller `name` made from an Ibex layout by that controller's rules: (data, report)."""
    from .fixes import apply_all
    controller = controllers.get(name)
    if controller.base:
        raise ValueError("Ibex is the base layout: it is built, not converted (R177)")
    if controllers.of_layout(ibex) is not controllers.BASE:
        raise ValueError("the source is not an Ibex layout")
    data = readable(copy.deepcopy(ibex))
    report = Report()
    header(data, controller, variant, version)                                         # R179, R180
    if controller.swaps:
        report.add("R181", f"the grips trade places in {swap_grips(data, controller)} groups")
    if controller.whole_pad:
        whole_pad(data, report)                                                        # R183
    dropped = drop_absent(data, controller, report)                                    # R182, R178 (a) to (e)
    if controller.absent or controller.absent_sources:
        report.add("R182", f"{dropped} activators on absent inputs dropped")
    if controller.mute:
        mute(data, controller)                                                         # R184
    always = gyro_always_on(data) if controller.always_gyro else []                    # R185
    report.add("R179" if name == "neptune" else "R180",
               f"gyro style {controller.gyro_style} in {gyro_style(data, controller.gyro_style)} groups")
    gone = delete_unreachable(data, report)                                            # R178 (f)
    masks = "R178 (c): gyro "
    report[:] = [line for line in report                                               # not a deleted layer's mask
                 if not line.startswith(masks) or line[len(masks):].split(" / ")[0] not in gone]
    if controller.always_gyro:
        report.add("R185", "no enable mask in the gyro of " + ", ".join(t for t in always if t not in gone))
    before = copy.deepcopy(data)
    fixes = apply_all(data)
    if data != before:
        report.add("fix pipeline", f"changed the layout: {fixes}")
    groups = {group["id"] for group in data["controller_mappings"]["group"]}
    for group in data["controller_mappings"]["group"]:
        for _, _, entry in activators(group):
            for source, target in MODE_SHIFT.findall(" ".join(actions(entry))):
                if target not in groups:
                    raise ValueError(f"group {group['id']}: a mode shift to group {target} ({source}), which the "
                                     "conversion deleted")
    return json.loads(dumps(data)), report


def bootstrap(deck, variant, version):
    """Ibex's first layout, made once from a Neptune layout: Ibex's Steam names and Player Space in every
    gyro-to-mouse group, nothing else (R177). Every later change goes the other way."""
    if controllers.of_layout(deck) is not controllers.NEPTUNE:
        raise ValueError("the bootstrap reads a Neptune layout")
    data = copy.deepcopy(deck)
    header(data, controllers.BASE, variant, version)
    gyro_style(data, controllers.BASE.gyro_style)
    return data
