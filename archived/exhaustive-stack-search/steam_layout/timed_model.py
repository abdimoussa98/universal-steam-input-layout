"""Millisecond replay of explicit layer commands.

This is a separate, versioned runtime contract, not the untimed HeldModel or
its proof engine. Physical events and clock advances are explicit; simultaneous
entries branch over their execution orders. See TIMED-MODEL.md for assumptions.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path

from .held_model import ALWAYS, DIRS, THUMBS
from .timed_spec import TimedSpec, canonical_control as canonical, chord_selectors


@dataclass(frozen=True, order=True)
class Activation:
    entry_id: str
    deadline_ms: object  # int or None when already fired/suppressed
    stage: str          # start, repeat, done
    fired: bool = False


@dataclass(frozen=True)
class Shift:
    control: tuple
    source: str
    group: str
    entry_id: str


@dataclass(frozen=True)
class TimedState:
    now_ms: int = 0
    stack: tuple = (0,)
    held: frozenset = frozenset()
    analog_values: tuple = ()
    activations: tuple = ()
    shifts: tuple = ()


class TimedModel:
    """Reference simulator; immutable states retain all timer-order branches.

    Removal resets pending start delays, even for an absent target. A completed
    delayed add is rearmed when its target is removed. Repeats keep their clocks.
    These choices are explicit contract assumptions, not hardware certification.
    """

    def __init__(self, layout, *, ignore_hold_bindings=False, default_repeat_ms=None):
        self.layout = layout
        self.spec = TimedSpec(layout, ignore_hold_bindings=ignore_hold_bindings,
                              default_repeat_ms=default_repeat_ms)
        self.controls = frozenset(canonical(c) for c in self.spec.controls if c != ALWAYS)
        self.raw_controls = tuple(c for c in self.spec.controls if c != ALWAYS)
        implementation = hashlib.sha256()
        for filename in ("timed_model.py", "timed_spec.py", "held_model.py", "model.py"):
            implementation.update(filename.encode("utf-8"))
            implementation.update(Path(__file__).with_name(filename).read_bytes())
        self.semantics = {
            "version": "timed-layer-replay-v1",
            "implementation_sha256": implementation.hexdigest(),
            "time_unit": "integer milliseconds",
            "default_repeat_ms": default_repeat_ms,
            "ignore_hold_bindings": ignore_hold_bindings,
            "ignored_hold_commands": list(self.spec.ignored_hold_commands),
            "removal_reset": "all pending start delays, including absent-target removals",
            "completed_add_reset": "rearm when that add's target is removed",
            "exposed_held_binding": "delays start; repeats wait one interval; immediate commands suppressed",
            "matching_activators": "identical source/input/kind/serialized entry preserve clocks",
            "threshold_boundary": "normal strictly above; inverted at or below",
            "analog_units": "Steam raw magnitude, 0 through 32767",
            "mode_shift_lifetime": "latched until physical release or chord condition ends",
            "same_deadline": "all entry orders; wait processes deadlines before the next physical event",
            "hardware_verified": False,
        }
        for entry in self.spec.entries.values():
            if entry.delay_end_ms:
                raise ValueError(f"{entry.id}: nonzero delay_end is not supported by timed layer replay")
            if entry.kind == "release" and (entry.delay_start_ms or entry.repeat_ms is not None):
                raise ValueError(f"{entry.id}: delayed/repeating release activators are not supported")
            if entry.ops or entry.shifts or entry.kind == "chord":
                supported = {"activation_threshold", "chord_button", "delay_start", "delay_end",
                             "edge_binding_invert", "gyro_ratchet_button_mask",
                             "gyro_ratchet_button_requireany_or_all", "haptic_intensity",
                             "hold_repeats", "interruptable", "repeat_rate"}
                for key, value in entry.settings:
                    if key not in supported:
                        raise ValueError(f"{entry.id}: unsupported behavioral setting {key}={value}")

    def names_of(self, stack):
        return tuple(self.spec.layer_names[n] for n in stack)

    def start(self):
        state = TimedState()
        return self._settle(self._refresh(state, state))

    def _control(self, control):
        control = canonical(control)
        if control not in self.controls:
            raise ValueError(f"unknown control: {'/'.join(control)}")
        return control

    def _valid(self, held):
        for thumb in "LR":
            locations = {c[0] if c not in THUMBS else "/".join(c) for c in held
                         if THUMBS.get(c, THUMBS.get(c[0])) == thumb}
            if len(locations) > 1:
                return False
        for source in {c[0] for c in held}:
            names = {c[1] for c in held if c[0] == source}
            if source.endswith(("joystick", "trackpad")):
                dirs = sorted(DIRS[n] for n in names if n in DIRS)
                if len(dirs) > 2 or (len(dirs) == 2 and dirs[1] - dirs[0] not in (1, 3)):
                    return False
                if names - {"touch"} and (source, "touch") in self.controls and "touch" not in names:
                    return False
            if source.endswith("trigger") and "click" in names:
                if (source, "edge") in self.controls and "edge" not in names:
                    return False
        return True

    def _binding(self, state, control):
        # Shift groups replace their whole source, including absent inputs.
        for shift in reversed(state.shifts):
            if shift.source == control[0]:
                return self.spec.shifts_by_group[(shift.source, shift.group)].get(control, ())
        for owner in reversed(state.stack):
            if control[0] in self.spec.blocked.get(owner, ()):
                return ()
            found = self.spec.bindings.get((owner, control))
            if found is not None:
                return found
        return ()

    def _condition(self, entry, state):
        settings = dict(entry.chord)
        if not settings:
            return True
        all_, specs = chord_selectors(settings, entry.id)
        hits = []
        for spec in specs:
            if spec is None:
                raise ValueError(f"{entry.id}: unsupported chord condition {settings}")
            if isinstance(spec, str):
                kind, source = spec.split(":")
                hit = ((source, "touch") in state.held if kind == "pad" else
                       any(c[0] == source and c[1] not in ("touch", "click") for c in state.held))
            else:
                hit = any(canonical(c) in state.held for c in spec)
            hits.append(hit)
        return all(hits) if all_ else any(hits)

    def _pressed(self, entry, state):
        control = canonical((entry.source, entry.input))
        if control == ALWAYS:
            return True
        if entry.kind == "Soft_Press":
            values = dict(state.analog_values)
            if control in values:
                threshold = entry.threshold if entry.threshold is not None else Decimal(0)
                outside = values[control] > threshold
                return not outside if entry.invert else outside
            # A digital trace provides a threshold crossing, not a fabricated
            # analog magnitude. Numeric thresholds require an explicit sample.
            if entry.threshold is not None:
                return False
            if entry.invert:
                return control not in state.held
        return control in state.held

    def _eligible(self, state):
        found = {}
        for control in (*self.raw_controls, ALWAYS):
            entries = self._binding(state, control)
            blocked = any(e.kind == "chord" and self._pressed(e, state) and self._condition(e, state)
                          for e in entries)
            for entry in entries:
                if entry.kind == "release" or not self._pressed(entry, state):
                    continue
                if entry.kind == "chord" and not self._condition(entry, state):
                    continue
                if entry.kind == "Full_Press" and entry.interruptible and blocked:
                    continue
                if entry.ops or entry.shifts:
                    found[entry.id] = entry
        return found

    def _refresh(self, state, previous, pressed=frozenset()):
        # A mode shift belongs to the physical press that activated it, even
        # when a layer replaces that button's binding while it remains held.
        shifts = tuple(s for s in state.shifts if s.control in state.held and
                       self._condition(self.spec.entries[s.entry_id], state))
        state = replace(state, shifts=shifts)
        desired = self._eligible(state)
        old = {a.entry_id: a for a in state.activations}
        # Reserve exact matches before allowing cross-owner state transfer.
        # Otherwise one newly exposed duplicate could steal another retained
        # entry's timer and duplicate its elapsed time.
        unmatched = [a for a in state.activations if a.entry_id not in desired]
        result = []
        for eid, entry in sorted(desired.items()):
            active = old.get(eid)
            if active is None:
                active = next((a for a in unmatched if
                               self.spec.entries[a.entry_id].fingerprint == entry.fingerprint), None)
            if active is not None:
                if active in unmatched:
                    unmatched.remove(active)
                result.append(replace(active, entry_id=eid))
                continue
            control = (entry.source, entry.input)
            was_bound = any(e.id == eid for e in self._binding(previous, control))
            immediate = control == ALWAYS or canonical(control) in pressed or was_bound
            if entry.delay_start_ms:
                active = Activation(eid, state.now_ms + entry.delay_start_ms, "start")
            elif immediate:
                active = Activation(eid, state.now_ms, "start")
            elif entry.repeat_ms is not None:
                active = Activation(eid, state.now_ms + entry.repeat_ms, "repeat")
            else:
                active = Activation(eid, None, "done")
            result.append(active)
        return replace(state, activations=tuple(result))

    def _execute(self, state, entries):
        stack = list(state.stack)
        removed = set()
        shifts = list(state.shifts)
        for entry in entries:
            for op, target in entry.ops:
                if op == "r":
                    removed.add(target)
                    if target in stack and target != 0:
                        stack.remove(target)
                elif target not in stack:
                    stack.append(target)
            for source, group in entry.shifts:
                shift = Shift(canonical((entry.source, entry.input)), source, group, entry.id)
                if shift not in shifts:
                    shifts.append(shift)
        active = []
        for a in state.activations:
            entry = self.spec.entries[a.entry_id]
            if removed and entry.delay_start_ms:
                pending = a.stage == "start" and a.deadline_ms is not None
                removed_target = any(op == "a" and target in removed for op, target in entry.ops)
                if pending or (removed_target and a.stage == "done"):
                    a = Activation(a.entry_id, state.now_ms + entry.delay_start_ms, "start")
            active.append(a)
        changed = replace(state, stack=tuple(stack), activations=tuple(active), shifts=tuple(shifts))
        return self._refresh(changed, state)

    @staticmethod
    def _orders(entries):
        """All distinct command orders, collapsing identical effects.

        Removal-only batches commute. For mixed batches retain multiplicity:
        add A, remove A, add A differs from two consecutive adds then removal.
        """
        entries = tuple(entries)
        if all(not e.shifts and all(op == "r" for op, _ in e.ops) for e in entries):
            yield entries
            return
        groups = {}
        for entry in entries:
            key = (entry.ops, entry.id if entry.shifts else None)
            if key not in groups:
                groups[key] = [entry, 0]
            groups[key][1] += 1
        groups = list(groups.values())

        def walk(prefix):
            if len(prefix) == len(entries):
                yield tuple(prefix)
                return
            for group in groups:
                if group[1]:
                    group[1] -= 1
                    yield from walk([*prefix, group[0]])
                    group[1] += 1

        yield from walk([])

    def _settle(self, state):
        """Drain same-instant commands without imposing an entry-order cap."""
        todo = [(state, frozenset())]
        seen, finished = set(), set()
        while todo:
            current, ancestors = todo.pop()
            if current in ancestors:
                raise ValueError("zero-time command cycle in timed replay")
            if current in seen:
                continue
            seen.add(current)
            due = [a for a in current.activations if a.deadline_ms is not None and
                   a.deadline_ms <= current.now_ms]
            if not due:
                finished.add(current)
                continue
            advanced = []
            for a in current.activations:
                if a not in due:
                    advanced.append(a)
                    continue
                entry = self.spec.entries[a.entry_id]
                advanced.append(Activation(a.entry_id,
                                           current.now_ms + entry.repeat_ms if entry.repeat_ms is not None else None,
                                           "repeat" if entry.repeat_ms is not None else "done", True))
            ready = replace(current, activations=tuple(advanced))
            successors = {self._execute(ready, order) for order in self._orders(
                [self.spec.entries[a.entry_id] for a in due])}
            todo.extend((successor, ancestors | {current}) for successor in successors)
        return frozenset(finished)

    def press(self, state, control):
        control = self._control(control)
        if control in state.held:
            raise ValueError(f"control already held: {'/'.join(control)}")
        held = state.held | {control}
        if not self._valid(held):
            raise ValueError(f"physically incompatible press: {'/'.join(control)}")
        values = dict(state.analog_values)
        values.pop(control, None)
        new = replace(state, held=held, analog_values=tuple(sorted(values.items())))
        return self._settle(self._refresh(new, state, frozenset({control})))

    def release(self, state, control):
        control = self._control(control)
        if control not in state.held:
            raise ValueError(f"control is not held: {'/'.join(control)}")
        held = state.held - {control}
        if not self._valid(held):
            raise ValueError("release dependent pad/stick/trigger controls before their touch/edge")
        values = dict(state.analog_values)
        values.pop(control, None)
        new = replace(state, held=held, analog_values=tuple(sorted(values.items())))
        return self._release(state, new, control)

    def _release(self, state, new, control):
        entries = {e.id: e for raw in self.raw_controls if canonical(raw) == control
                   for e in self._binding(state, raw) if e.kind == "release"}
        new = self._refresh(new, state)
        result = set()
        for order in self._orders(entries.values()):
            result.update(self._settle(self._execute(new, order)))
        return frozenset(result)

    def analog(self, state, control, value):
        control = self._control(control)
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("analog value must be a finite number between 0 and 32767") from None
        if not value.is_finite() or not 0 <= value <= 32767:
            raise ValueError("analog value must be a finite number between 0 and 32767")
        values = dict(state.analog_values)
        values[control] = value
        held = state.held | {control} if value > 0 else state.held - {control}
        if not self._valid(held):
            raise ValueError(f"physically incompatible analog sample: {'/'.join(control)}")
        new = replace(state, held=held, analog_values=tuple(sorted(values.items())))
        if control in state.held and value == 0:
            return self._release(state, new, control)
        pressed = frozenset({control}) if control not in state.held and value > 0 else frozenset()
        return self._settle(self._refresh(new, state, pressed))

    def wait(self, state, milliseconds):
        if isinstance(milliseconds, bool) or not isinstance(milliseconds, int) or milliseconds < 0:
            raise ValueError("wait duration must be a nonnegative integer number of milliseconds")
        end = state.now_ms + milliseconds
        todo = [state]
        finished = set()
        while todo:
            current = todo.pop()
            deadlines = [a.deadline_ms for a in current.activations if a.deadline_ms is not None]
            due = min(deadlines) if deadlines else None
            if due is None or due > end:
                finished.add(replace(current, now_ms=end))
            else:
                todo.extend(self._settle(replace(current, now_ms=due)))
        return frozenset(finished)

    def snapshot(self, state):
        return {"now_ms": state.now_ms, "stack": list(self.names_of(state.stack)),
                "held": [list(c) for c in sorted(state.held)],
                "analog": [{"control": list(c), "value": str(v)} for c, v in state.analog_values],
                "timers": [{"entry": a.entry_id, "deadline_ms": a.deadline_ms,
                            "stage": a.stage, "fired": a.fired} for a in state.activations],
                "mode_shifts": [{"control": list(s.control), "source": s.source,
                                 "group": s.group, "entry": s.entry_id} for s in state.shifts]}
