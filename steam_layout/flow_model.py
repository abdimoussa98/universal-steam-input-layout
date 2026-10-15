"""Intended layer transitions, classified from the bindings themselves.

Every activator entry that changes layers becomes a `Transition`: its owner
layer, input, activator, settings, chord condition and ordered layer ops, with
the original JSON as evidence. Each one gets a role, and the role decides
whether the backward chains (chains.py) follow it:

    entry         Regular/Start/chord press that adds layers
    center        a repeating removal on an inverted stick edge: the stick
                  returning to center ends the layer's lifecycle
    second-press  a press in an Always On window that removes the window first
    hold          a delayed entry (Fire Start Delay): the successful hold branch
    release       a Release entry, including a release into a Double Tap window
    expiry        a window's delayed Always On self-removal
    removal       a press that only removes (not repeating)
    cancel        a repeating, non-interruptible removal with no guard chord
                  (for example a face button cancelling Temp Cursor Gyro)

These roles are not followed, and are listed with their reason:

    reset         a repeating removal of the same input's delayed-add target
    relay         a held driver's key carried up into a layer above its own, on a Regular
                  Press that also repeats the entry of the layer underneath (the other
                  driver's way into Modifier 2). The held driver never runs it (A5); a
                  fresh press gives the stack the layer underneath gives by itself
    recovery      an interruptible repeating removal (guarded or stale-state), or a
                  repeating removal on a chord with Invert Activation, which runs
                  while no chord button is held and so carries its own guard
    legacy-hold   a hold_layer command (migration work, not modelled)
    mode-shift    a mode shift whose shifted group changes layers (unsupported)

Plan: plans/2026-10-01-intended-flow-inheritance.md, section 1.
"""
from dataclasses import dataclass, field

from .model import EMPTY, LAYER_COMMAND, MODE_SHIFT, actions, always_on_layers, defined, entries

# What a chord's button stands for: legacy `chord_button` IDs and `gyro_ratchet_button_mask` bits.
# A list is the (source, input) controls that satisfy it; "pad:" means a thumb on that pad and
# "deflect:" means that stick is off centre. See resources/Neptune Chorded Button Ids.md.
LEGACY = {"1": [("switch", "left_bumper")], "2": [("switch", "right_bumper")],
          "5": [("left_trigger", "click")], "6": [("right_trigger", "click")],
          "7": [("left_trigger", "edge"), ("left_trigger", "click")],
          "8": [("right_trigger", "edge"), ("right_trigger", "click")],
          "9": [("joystick", "click")], "20": [("right_joystick", "click")],
          "14": [("switch", "button_escape")], "15": [("switch", "button_menu")],
          "16": "pad:left_trackpad", "17": "pad:right_trackpad",
          "23": [("joystick", "touch")], "24": [("right_joystick", "touch")]}
BITS = {3: [("switch", "left_bumper")], 2: [("switch", "right_bumper")],
        1: [("left_trigger", "click")], 0: [("right_trigger", "click")],
        25: [("left_trigger", "edge"), ("left_trigger", "click")],
        24: [("right_trigger", "edge"), ("right_trigger", "click")],
        22: [("joystick", "click")], 26: [("right_joystick", "click")],
        14: [("switch", "button_escape")], 12: [("switch", "button_menu")],
        19: "pad:left_trackpad", 20: "pad:right_trackpad",
        27: "pad:center_trackpad", 28: [("center_trackpad", "click")],          # the whole pad (resources/Controllers.md)
        46: [("joystick", "touch")], 47: [("right_joystick", "touch")],
        30: "deflect:joystick", 31: "deflect:right_joystick"}

FOLLOWED = ("entry", "second-press", "hold", "release", "expiry", "removal", "cancel", "center")
DIRECTIONS = ("dpad_north", "dpad_east", "dpad_south", "dpad_west")
ALWAYS_ON = ("switch", "always_on_action")
# The layers whose inverted chord is their own exit, registered as such (R111, R170): it stays a "cancel".
INVERTED_EXITS = frozenset({"Steering | LS: Entry Guard"})
# The one layer a cleanup function may add before it removes (90.67, author 2026-10-13): if the press runs past
# its guard chord (A69), this guard is what it leaves on top, not the stateful layer's own stick.
CLEANUP_GUARDS = frozenset({"Steering | LS: Entry Guard"})


@dataclass(frozen=True)
class Condition:
    """A chord condition: `mode` is "any" or "all" over `groups`; each group is
    satisfied by any one of its (source, input) controls being held."""
    mode: str
    groups: tuple
    label: str
    known: bool = True

    def satisfied(self, held):
        if not self.known:
            return False
        hits = [any(c in held for c in group) for group in self.groups]
        return all(hits) if self.mode == "all" else any(hits)

    def controls(self):
        return {c for group in self.groups for c in group}


def chord_condition(settings):
    """The Condition a chord entry's settings describe, or None if it has none."""
    if "chord_button" in settings:
        spec = LEGACY.get(settings["chord_button"])
        specs, mode, label = [spec], "any", f"chord_button {settings['chord_button']}"
    elif "gyro_ratchet_button_mask" in settings:
        mask = int(settings["gyro_ratchet_button_mask"])
        specs = [BITS.get(bit) for bit in range(64) if mask >> bit & 1]
        mode = "all" if settings.get("gyro_ratchet_button_requireany_or_all") == "1" else "any"
        label = f"mask {mask} ({mode})"
    else:
        return None
    groups = []
    for spec in specs:
        if spec is None:
            return Condition(mode, (), label + ": unknown button id", known=False)
        if isinstance(spec, str):
            kind, source = spec.split(":")
            # A pad chord means the thumb is on the pad. A deflection chord means the
            # stick is off center: any direction, or the edge (an over-approximation
            # where the edge is inverted and means center).
            groups.append(((source, "touch"),) if kind == "pad"
                          else tuple((source, d) for d in DIRECTIONS + ("edge",)))
        else:
            groups.append(tuple(spec))
    return Condition(mode, tuple(groups), label)


@dataclass(frozen=True)
class Transition:
    layer: str
    source: str
    input: str
    activator: str
    index: int            # entry position within the input, in serialized order
    event: str            # press, hold, release, expiry
    role: str
    reason: str
    ops: tuple            # ((op, title), ...) in execution order
    condition: Condition = None
    interruptible: bool = True
    settings: tuple = ()
    commands: tuple = ()  # binding strings in storage order (arrays run bottom to top)
    shift_group: str = None

    @property
    def followed(self):
        return self.role in FOLLOWED

    @property
    def control(self):
        return (self.source, self.input)

    def describe(self):
        ops = " ; ".join(("+" if op == "add_layer" else "-" if op == "remove_layer" else "hold ") + t
                         for op, t in self.ops)
        cond = f" [{self.condition.label}]" if self.condition else ""
        return f"{self.layer} {self.source}/{self.input} {self.activator}#{self.index}{cond}: {ops}"


def _delay(settings):
    return settings.get("delay_start", "0") not in ("", "0")


def _shift_changes_layers(layout, gid):
    group = layout.groups.get(gid, {})
    return any(LAYER_COMMAND.search(b) for value in group.get("inputs", {}).values()
               for _, e in entries(value.get("activators", {})) for b in actions(e))


def _relays(layout, title, source, name, listed):
    """True if this input carries a driver's key up from a layer underneath: its Regular Press sends the key
    that a layer this input's Release removes sends on the same input, and adds layers beside it."""
    press = [e for kind, e in listed if kind == "Full_Press"]
    if len(press) != 1 or not any(kind == "release" for kind, _ in listed):
        return False
    keys = [a for a in actions(press[0]) if a.startswith("key_press ")]
    if len(keys) != 1 or not any(op == "add_layer" for op, _ in layout.layer_ops(press[0])):
        return False
    below = {t for kind, e in listed if kind == "release" for op, t in layout.layer_ops(e)
             if op == "remove_layer" and t != title and t in layout.presets}
    for lower in below:
        found = layout.active(lower).get(source, {}).get("inputs", {}).get(name, {}).get("activators", {})
        if isinstance(found.get("Full_Press"), dict) and actions(found["Full_Press"]) == keys:
            return True
    return False


def layer_transitions(layout, title, windows=None):
    """Every layer-changing entry of `title`, classified."""
    windows = set(always_on_layers(layout)) if windows is None else windows
    result = []
    # A delayed add chorded on a stick's deflect may sit on another input, the held driver (a start delay
    # owned by a stick direction misfires, author 2026-10-10). Its reset stays on that stick's directions.
    # The same for a delayed add on the stick's own edge (90.54, and a Soft Press there since 90.55).
    deflected = {}
    for source, group in layout.active(title).items():
        for name, value in group.get("inputs", {}).items():
            for kind, e in entries(value.get("activators", {})):
                if name == "edge" and _delay(e.get("settings", {})):
                    deflected.setdefault(source, set()).update(
                        t for op, t in layout.layer_ops(e) if op == "add_layer")
                condition = chord_condition(e.get("settings", {})) if kind == "chord" and _delay(e.get("settings", {})) else None
                if condition and condition.known:
                    for stick in {c[0] for c in condition.controls() if c[1] in DIRECTIONS}:
                        deflected.setdefault(stick, set()).update(
                            t for op, t in layout.layer_ops(e) if op == "add_layer")
    for source, group in layout.active(title).items():
        if group["mode"] == "disabled":
            continue
        for name, value in group.get("inputs", {}).items():
            listed = list(entries(value.get("activators", {})))
            delayed_targets = {t for kind, e in listed if _delay(e.get("settings", {}))
                               for op, t in layout.layer_ops(e) if op == "add_layer"}
            if name in DIRECTIONS:
                delayed_targets |= deflected.get(source, set())
            has_chord = any(kind == "chord" for kind, _ in listed)
            for index, (kind, entry) in enumerate(listed):
                settings = entry.get("settings", {})
                ops = tuple(layout.layer_ops(entry))
                commands = tuple(actions(entry))
                shifts = [m.group(2) for c in commands if (m := MODE_SHIFT.search(c))]
                if not ops and not any(_shift_changes_layers(layout, gid) for gid in shifts):
                    continue
                centered = name == "edge" and group.get("settings", {}).get("edge_binding_invert") == "1"
                role, reason, event = _classify(title, source, name, kind, settings, ops, delayed_targets,
                                                has_chord, windows, centered)
                if kind == "Full_Press" and role == "entry" and _relays(layout, title, source, name, listed):
                    role, reason = "relay", "a held driver's key with the entry of the layer underneath (A5)"
                if not ops:
                    role, reason, event = "mode-shift", "mode-shift lookup is not modelled yet", "press"
                result.append(Transition(
                    layer=title, source=source, input=name, activator=kind, index=index, event=event,
                    role=role, reason=reason, ops=ops,
                    condition=chord_condition(settings) if kind == "chord" else None,
                    interruptible=settings.get("interruptable") != "0",
                    settings=tuple(sorted(settings.items())), commands=commands,
                    shift_group=shifts[0] if shifts else None))
    return result


def _classify(title, source, name, kind, settings, ops, delayed_targets, has_chord, windows, centered=False):
    if any(op == "hold_layer" for op, _ in ops):
        return "legacy-hold", "hold_layer is migration work and is not modelled", "press"
    repeat = settings.get("hold_repeats") == "1"
    removals = [t for op, t in ops if op == "remove_layer"]
    removal_only = ops and len(removals) == len(ops)
    if (source, name) == ALWAYS_ON:
        return "expiry", "window timeout", "expiry"
    if kind == "release":
        return "release", "release", "release"
    # A repeating, interruptible Regular Press of removes stays a cleanup function with a start delay on it
    # (90.65: 5 ms on the left edge of ten Steering layers, author 2026-10-13). No earlier build has one.
    late_cleanup = kind == "Full_Press" and repeat and removal_only and settings.get("interruptable") != "0"
    if _delay(settings) and not late_cleanup:
        return "hold", "successful hold (the delay completes)", "hold"
    added = {t for op, t in ops if op == "add_layer"}
    if kind == "Full_Press" and repeat and has_chord and removals and len(removals) + len(added) == len(ops) \
            and added and added <= CLEANUP_GUARDS and settings.get("interruptable") != "0":
        # Still a cleanup function, so the chains do not follow its add: the guard lands on what the same
        # list leaves, which is the stack the guard's own entry gives.
        return "recovery", "guarded recovery that adds its temporary guard first", "press"
    if repeat and removal_only:
        if set(removals) <= delayed_targets:
            return "reset", "interrupted-delay reset of this input's delayed add", "press"
        if centered and not has_chord:
            return "center", "stick returns to center (inverted edge)", "press"
        if kind == "chord" and settings.get("edge_binding_invert") == "1" and title not in INVERTED_EXITS:
            # Invert Activation on a chord: it runs while its input is released and no chord button
            # is held, so it is a cleanup function that carries its own guard (author, 2026-10-10).
            return "recovery", "inverted chord (runs while no chord button is held)", "press"
        if settings.get("interruptable") != "0":
            guard = "guarded recovery (a satisfied chord suppresses it)" if has_chord \
                else "stale-state recovery (repeating, interruptible)"
            return "recovery", guard, "press"
        return "cancel", "repeating non-interruptible removal", "press"
    if kind == "Full_Press" and removal_only and has_chord and settings.get("interruptable") != "0":
        # 90.69, a trial off the line (author, 2026-10-13: "Still interruptible, but no longer repeating"): beside
        # a chord, an interruptible press of removes is a cleanup function without Hold to Repeat too. Up to
        # 90.68 no press of removes without a repeat has a chord beside it.
        return "recovery", "guarded recovery without a repeat (a satisfied chord suppresses it)", "press"
    if title in windows and ops[0] == ("remove_layer", title) and any(op == "add_layer" for op, _ in ops):
        return "second-press", "second press: removes the window first", "press"
    if any(op == "add_layer" for op, _ in ops):
        return "entry", "press that adds layers", "press"
    return "removal", "press that only removes layers", "press"


@dataclass
class Inventory:
    """All classified transitions of a layout, indexed by layer and control."""
    layout: object
    transitions: list = field(default_factory=list)

    @classmethod
    def of(cls, layout):
        windows = set(always_on_layers(layout))
        inv = cls(layout)
        for title in layout.presets:
            inv.transitions += layer_transitions(layout, title, windows)
        return inv

    def by_layer(self, title):
        if not hasattr(self, "_by_layer"):
            self._by_layer = {}
            for t in self.transitions:
                self._by_layer.setdefault(t.layer, []).append(t)
        return self._by_layer.get(title, [])

    def on(self, title, control):
        return [t for t in self.transitions if t.layer == title and t.control == control]

    def adders(self, title):
        """Transitions that add `title`."""
        return [t for t in self.transitions if ("add_layer", title) in t.ops]

    def legacy_only(self, title):
        """True if only legacy hold_layer commands ever bring `title` in."""
        sources = [t for t in self.transitions if ("add_layer", title) in t.ops or ("hold_layer", title) in t.ops]
        return bool(sources) and all(t.role == "legacy-hold" for t in sources)


def resolve(layout, stack, source, name, mode=None, mode_from=None):
    """The nearest definition of an input, walking down `stack` from the top.

    Returns (kind, layer, activators, mode); kind is "binding", "disabled" (a
    disabled source stops the lookup), "mode" or "none". The first group for
    the source sets the mode, unless `mode` is given (the target's own group,
    named by `mode_from`). A group in a different mode blocks inheritance: the
    lower mode's inputs don't carry over (author rule, 2026-10-01). For a block,
    the layer returned is the one whose mode blocks.
    """
    for title in reversed(stack):
        group = layout.active(title).get(source)
        if group is None:
            continue
        if group["mode"] == "disabled":
            return "disabled", title, None, "disabled"
        if mode is None:
            mode, mode_from = group["mode"], title
        if group["mode"] != mode:
            return "mode", mode_from, None, mode
        if defined(group, name):
            return "binding", title, group["inputs"][name]["activators"], mode
    return "none", None, None, mode


def is_clear(activators):
    """True if every binding of the input is an empty binding."""
    commands = [c for _, e in entries(activators or {}) for c in actions(e)]
    return bool(commands) and all(c.startswith(EMPTY) for c in commands)
