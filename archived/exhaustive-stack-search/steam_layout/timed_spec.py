"""Lossless activator specifications for the millisecond runtime model.

This parser deliberately does not reuse HeldModel's boolean delay/repeat
abstraction. Unknown timing and selector encodings fail with their entry path.
An omitted repeat interval needs an explicit caller-supplied default; it is not
silently assigned a guessed Steam default.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Optional, Tuple, Union

from .held_model import BITS, LEGACY
from .model import TOKEN, actions, entries

KINDS = frozenset(("Full_Press", "Start_Press", "Soft_Press", "chord", "release"))
CHORD_KEYS = ("chord_button", "gyro_ratchet_button_mask", "gyro_ratchet_button_requireany_or_all")
TIMING_KEYS = frozenset(("delay_start", "delay_end", "hold_repeats", "repeat_rate"))
LAYER_TARGET = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|[0-9]+)(?=\s|,|$)")
SHIFT_TARGET = re.compile(r"mode_shift (\S+) ([0-9]+)(?=\s|,|$)")

# Additional selector IDs/indices are recorded in resources/neptune_chord_ids
# and findings/2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md.
LEGACY_SELECTORS = dict(LEGACY, **{
    "18": [("left_trackpad", "click")], "19": [("right_trackpad", "click")],
})
CHORD_BITS = dict(BITS)
CHORD_BITS.update({
    4: [("button_diamond", "button_y")], 5: [("button_diamond", "button_b")],
    6: [("button_diamond", "button_x")], 7: [("button_diamond", "button_a")],
    8: [("dpad", "dpad_north")], 9: [("dpad", "dpad_east")],
    10: [("dpad", "dpad_west")], 11: [("dpad", "dpad_south")],
    15: [("switch", "button_back_left")], 16: [("switch", "button_back_right")],
    17: [("left_trackpad", "click")], 18: [("right_trackpad", "click")],
    41: [("switch", "button_back_left_upper")],
    42: [("switch", "button_back_right_upper")],
})

CONTROL_ALIASES = {
    ("switch", "left_trackpad_touch"): ("left_trackpad", "touch"),
    ("switch", "right_trackpad_touch"): ("right_trackpad", "touch"),
    ("switch", "left_stick_click"): ("joystick", "click"),
    ("switch", "right_stick_click"): ("right_joystick", "click"),
}


def canonical_control(control):
    """Map switch-bank aliases to the same physical pad/stick control."""
    control = tuple(control)
    return CONTROL_ALIASES.get(control, control)


def _freeze(value):
    if isinstance(value, dict):
        return tuple((k, _freeze(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _integer(value, path, positive=False):
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
        raise ValueError(f"{path}: expected a nonnegative integer, got {value!r}")
    number = int(value)
    if positive and number == 0:
        raise ValueError(f"{path}: repeat interval must be greater than zero")
    return number


def _flag(settings, key, path, default=False):
    if key not in settings:
        return default
    value = settings[key]
    if isinstance(value, bool) or str(value) not in ("0", "1"):
        raise ValueError(f"{path}.{key}: expected 0 or 1, got {value!r}")
    return str(value) == "1"


def chord_selectors(settings, path="chord"):
    """Return (require_all, selector specifications), rejecting unknown IDs.

    Each specification is either alternatives of physical controls or the
    strings ``pad:source`` / ``deflect:source`` used by the runtime model.
    """
    if "chord_button" in settings and "gyro_ratchet_button_mask" in settings:
        raise ValueError(f"{path}: ambiguous legacy and mask chord selectors")
    require_all = _flag(settings, "gyro_ratchet_button_requireany_or_all", path)
    if "chord_button" in settings:
        value = str(settings["chord_button"])
        if value not in LEGACY_SELECTORS:
            raise ValueError(f"{path}: unsupported chord_button {value!r}")
        return False, (LEGACY_SELECTORS[value],)
    if "gyro_ratchet_button_mask" in settings:
        mask = _integer(settings["gyro_ratchet_button_mask"], f"{path}.gyro_ratchet_button_mask")
        if not mask:
            raise ValueError(f"{path}: chord mask must select at least one button")
        bits = [bit for bit in range(mask.bit_length()) if mask & (1 << bit)]
        unsupported = [bit for bit in bits if bit not in CHORD_BITS]
        if unsupported:
            raise ValueError(f"{path}: unsupported chord mask bits {unsupported}")
        return require_all, tuple(CHORD_BITS[bit] for bit in bits)
    raise ValueError(f"{path}: chord activator has no button selector")


@dataclass(frozen=True)
class EntrySpec:
    id: str
    source: str
    input: str
    owner: Union[int, str]
    kind: str
    delay_start_ms: int
    delay_end_ms: int
    repeat_ms: Optional[int]
    interruptible: bool
    chord: Tuple[Tuple[str, object], ...]
    threshold: Optional[Decimal]
    invert: bool
    ops: Tuple[Tuple[str, int], ...]
    shifts: Tuple[Tuple[str, str], ...]
    fingerprint: str
    settings: Tuple[Tuple[str, object], ...]


class TimedSpec:
    """Parse active groups and every recursively referenced mode-shift group.

    ``bindings[(owner, (source, input))]`` holds complete EntrySpec tuples.
    Normal owners are zero-based layer IDs; shift owners are
    ``shift:<source>:<group ID>``. ``blocked[owner]`` contains disabled sources.
    ``shifts_by_group[(source, group ID)]`` maps controls to EntrySpec tuples.
    ``ignored_hold_commands`` contains ``(entry ID, raw command)`` pairs.
    """

    def __init__(self, layout, ignore_hold_bindings=False, default_repeat_ms=None):
        self.layout = layout
        self.ignore_hold_bindings = ignore_hold_bindings
        self.default_repeat_ms = (None if default_repeat_ms is None else
                                  _integer(default_repeat_ms, "default_repeat_ms", positive=True))
        if len(layout.cm["actions"]) != 1:
            raise ValueError("TimedSpec supports exactly one Base action set; action-set switching is excluded")
        self.layer_names = list(layout.presets)
        if not self.layer_names or self.layer_names[0] != layout.base:
            raise ValueError("the Base action set must be the first preset")
        self.index = {title: n for n, title in enumerate(self.layer_names)}
        self.bindings, self.blocked, self.entries, self.shifts_by_group = {}, {}, {}, {}
        self.ignored_hold_commands = []
        self._controls = set()
        pending = []
        for title in self.layer_names:
            owner = self.index[title]
            for source, group in layout.active(title).items():
                self._group(owner, source, group, pending)
        while pending:
            source, gid = pending.pop(0)
            if (source, gid) in self.shifts_by_group:
                continue
            owner = self.shift_owner(source, gid)
            self.shifts_by_group[(source, gid)] = {}
            self._group(owner, source, layout.groups[gid], pending)
            self.shifts_by_group[(source, gid)] = {
                control: value for (found, control), value in self.bindings.items() if found == owner
            }
        self.controls = tuple(sorted(self._controls))
        self.blocked = {owner: frozenset(sources) for owner, sources in self.blocked.items()}
        self.ignored_hold_commands = tuple(self.ignored_hold_commands)
        del self._controls

    @staticmethod
    def shift_owner(source, gid):
        return f"shift:{source}:{gid}"

    def _group(self, owner, source, group, pending):
        self._controls.update((source, name) for name in group.get("inputs", {}))
        if group.get("mode") == "disabled":
            self.blocked.setdefault(owner, set()).add(source)
            return
        for name, value in group.get("inputs", {}).items():
            activators = value.get("activators", {})
            if not activators:
                continue
            parsed = []
            counts = {}
            for kind, entry in entries(activators):
                ordinal = counts.get(kind, 0)
                counts[kind] = ordinal + 1
                entry_id = f"{owner}/{source}/{name}/{kind}/{ordinal}"
                spec = self._entry(entry_id, owner, source, name, kind, entry)
                parsed.append(spec)
                self.entries[entry_id] = spec
                pending.extend(spec.shifts)
            self.bindings[(owner, (source, name))] = tuple(parsed)

    def _target(self, ref, path):
        token = TOKEN.fullmatch(ref)
        if token:
            title = token.group(1)
        else:
            runtime_id = _integer(ref, path)
            if not 1 <= runtime_id <= len(self.layout.order):
                raise ValueError(f"{path}: dangling runtime layer ID {runtime_id}")
            title = self.layout.titles[self.layout.order[runtime_id - 1]]
        if title not in self.index:
            raise ValueError(f"{path}: dangling layer target {title!r}")
        return self.index[title]

    def _entry(self, path, owner, source, name, kind, entry):
        if kind not in KINDS:
            raise ValueError(f"{path}: unsupported activator kind {kind!r}")
        settings = entry.get("settings", {})
        for key in settings:
            if ("delay" in key.lower() or "repeat" in key.lower()) and key not in TIMING_KEYS:
                raise ValueError(f"{path}: unsupported timing setting {key!r}")
        delay_start = _integer(settings.get("delay_start", 0), f"{path}.delay_start")
        delay_end = _integer(settings.get("delay_end", 0), f"{path}.delay_end")
        repeats = _flag(settings, "hold_repeats", path)
        rate = (_integer(settings["repeat_rate"], f"{path}.repeat_rate", positive=repeats)
                if "repeat_rate" in settings else self.default_repeat_ms)
        if repeats and rate is None:
            raise ValueError(f"{path}: hold_repeats has no repeat_rate; supply default_repeat_ms explicitly")
        threshold = None
        if "activation_threshold" in settings:
            try:
                threshold = Decimal(str(settings["activation_threshold"]))
            except InvalidOperation:
                raise ValueError(f"{path}: invalid activation_threshold") from None
            if not threshold.is_finite() or threshold < 0:
                raise ValueError(f"{path}: activation_threshold must be finite and nonnegative")
        if kind == "chord":
            _, selectors = chord_selectors(settings, path)
            for selector in selectors:
                if isinstance(selector, str):
                    selector_kind, selector_source = selector.split(":", 1)
                    self._controls.add((selector_source, "touch" if selector_kind == "pad" else "edge"))
                else:
                    self._controls.update(selector)
        ops, shifts = [], []
        for command in reversed(actions(entry)):
            if not isinstance(command, str):
                raise ValueError(f"{path}: binding commands must be strings")
            if re.search(r"\bCHANGE_PRESET\b", command, re.IGNORECASE):
                raise ValueError(f"{path}: CHANGE_PRESET action-set switching is excluded")
            target = LAYER_TARGET.search(command)
            if target:
                operation, ref = target.groups()
                target_id = self._target(ref, path)
                if operation == "hold_layer":
                    if not self.ignore_hold_bindings:
                        raise ValueError(f"{path}: hold_layer is excluded; use ignore_hold_bindings=True to omit it explicitly")
                    self.ignored_hold_commands.append((path, command))
                else:
                    ops.append(("a" if operation == "add_layer" else "r", target_id))
            elif re.search(r"controller_action\s+(?:add_layer|remove_layer|hold_layer)\b", command):
                raise ValueError(f"{path}: malformed layer command {command!r}")
            shifted = SHIFT_TARGET.search(command)
            if shifted:
                shift_source, gid = shifted.groups()
                if gid not in self.layout.groups:
                    raise ValueError(f"{path}: dangling mode-shift group {gid!r}")
                shifts.append((shift_source, gid))
            elif re.search(r"\bmode_shift\b", command):
                raise ValueError(f"{path}: malformed mode-shift command {command!r}")
        payload = json.dumps({"source": source, "input": name, "kind": kind, "entry": entry},
                             sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return EntrySpec(path, source, name, owner, kind, delay_start, delay_end,
                         rate if repeats else None,
                         _flag(settings, "interruptable", path, default=True),
                         tuple((key, _freeze(settings[key])) for key in CHORD_KEYS if key in settings),
                         threshold, _flag(settings, "edge_binding_invert", path), tuple(ops), tuple(shifts),
                         hashlib.sha256(payload.encode("utf-8")).hexdigest(), _freeze(settings))
