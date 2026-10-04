"""A press simulator: replay presses, releases and time on a layout, along one path.

    sim = Simulator(layout)                      # on the action set, at 0 ms
    sim.press(("switch", "left_bumper"))
    sim.wait(300)
    sim.release(("switch", "left_bumper"))
    sim.stack                                    # layer titles, bottom to top
    sim.down()                                   # keys and mouse buttons held down now
    sim.typed()                                  # every key or wheel event, in order
    sim.log                                      # (ms, what, detail) for everything that happened

It answers the three questions a Deck check asks: which layer gets an input,
what is on the stack, and which keys are down. It does not know how far a stick
or trigger is (a control is held or not), and it does not simulate mode shifts
or gyro motion. The one exception to "held or not" is
`press_between`: an input that sits inside an inverted Soft Press's range and
past a normal one's threshold at once, such as a thumb on the ring where a
pad's centre and outer ranges overlap.

Every behaviour below is an assumption about Steam, by ID from
resources/Steam Behaviour Assumptions.md. An unverified one is modelled as
stated; the ones the layout must work either way under are switches.

    A1, A2   the topmost layer that defines an input answers it (flow_model.resolve)
    A3, A4   re-adding doesn't move a layer; an array runs bottom to top
    A5, A6   a layer that lands on a held input doesn't fire its immediate layer command
             there; a start delay still runs out, and a Hold to Repeat one fires at once: a
             repeating action always triggers (author, 2026-10-04)
    A7, A8   a Release fires in the layer that answers the input when it is released,
             also when that layer was added while the input was held
    A9       `exposed_fires`: a layer command exposed by a removal under a held input fires
             at once (True), or behaves like one that landed (False)
    A10, A11 a key or mouse output is a level: it is down while its activator is active,
             also when the layer landed on, or was exposed under, a held input
    A12      removing a delayed add's target restarts that delay; a completed one is rearmed
    A13      `any_removal_resets`: any removal restarts every pending start delay
    A14, A15 a layer that binds a button ends the delay running on it; when a removal
             exposes the binding again, the delay starts from the beginning
    A16      a delay's clock starts when its binding starts answering the input
    A17, A36 a chord is decided when its binding starts answering a held input; pressing
             the chord button later doesn't start it, releasing it doesn't end it
    A27      an active chord suppresses an interruptible Regular Press on the same input
    A31      a repeat keeps its schedule when another layer is removed
    A32      `reverse_ties`: activators due at the same moment run in file order, or reversed
    A35      `default_repeat_ms`: Hold to Repeat with no stated rate uses this interval
    A37      a key handed from one binding to another at the same moment stays down (`typed`)
    A38      a stick edge is inverted only where its own group says so
    A42      `hold_releases`: `hold_layer` puts a layer on, and takes it off when the activator
             that holds it ends, whoever added the layer first (False: it only puts it on)
    A43      an input with a Double Press or a Long Press beside its Regular Press (`_native`): a tap
             sends the interruptible Regular Press once, after the Double Press time; a hold sends
             only the Long Press; a second press inside the Double Press time sends only the Double
             Press, for as long as it is held
    A39      `soft_press_interrupts`: an active uninterruptible Soft Press suppresses an interruptible
             Soft Press on the same input (`press_between` puts an input in both of two ranges)
    A21      `desktop(data)`: the layout with every entry past the third dropped
    A25      `lose(control)`: a release the layout never saw

Plan: plans/2026-10-02-rule-registry.md, phase 12. The older `stacks.walk` replays
named activations without time; this replays physical presses.
"""
from collections import namedtuple
import copy
import re

from .flow_model import chord_condition, resolve
from .model import TARGET, Layout, actions, entries

ALWAYS_ON = "always_on_action"
LEVEL = re.compile(r"(key_press|mouse_button|xinput_button) ([^,\s]+)")
NATIVE = ("Long_Press", "Double_Press")
MOMENTARY = re.compile(r"(mouse_wheel) ([^,\s]+)")
COMMAND = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|\d+)(?: (\d+))?")
UNSUPPORTED = re.compile(r"mode_shift |CHANGE_PRESET")

def desktop(data, keep=3):
    """A copy of the layout as the desktop configuration runs it: every entry past the third dropped (A21)."""
    data = copy.deepcopy(data)
    for group in data["controller_mappings"]["group"]:
        for value in group.get("inputs", {}).values():
            kept, count = {}, 0
            for kind, found in (value.get("activators") or {}).items():
                found = found if isinstance(found, list) else [found]
                found = found[:max(0, keep - count)]
                count += len(found)
                if found:
                    kept[kind] = found if len(found) > 1 else found[0]
            if "activators" in value:
                value["activators"] = kept
    return data


def typed(log):
    """The outputs a log shows going down or ticking, in order.

    A key that one binding lets go of and another presses at the same moment, under an input that stays
    held, was handed over, not typed again (A37): W carries on when a window above the driver's layer times
    out. The log says "handover" for that kind of up; a physical release says "up".
    """
    found, released = [], {}
    for ms, what, detail in log:
        if what == "handover":
            released[detail] = ms
        elif what == "down" and released.get(detail) == ms:
            released.pop(detail)
        elif what in ("down", "tap"):
            found.append(detail)
    return found


Entry = namedtuple("Entry", "control layer kind index settings ops outputs taps beeps inverted condition unsupported")


def _threshold(entry):
    return int(entry.settings.get("activation_threshold") or 0)


class Act:
    """One activator that is live: its entry, when it next fires, and the outputs it holds down."""

    def __init__(self, entry, due, first, order):
        self.entry, self.due, self.first, self.order = entry, due, first, order
        self.down = []          # outputs this activator holds down
        self.holds = []         # layers this activator holds (`hold_layer`): they go when it ends
        self.fired = False      # its layer commands have run at least once
        self.allow_ops = True   # False for the first firing of a command that landed on a held input


class Simulator:
    def __init__(self, layout, start=None, *, exposed_fires=True, any_removal_resets=True, reverse_ties=False,
                 default_repeat_ms=100, soft_press_interrupts=True, hold_releases=True):
        self.layout = layout if isinstance(layout, Layout) else Layout(layout)
        self.base = self.layout.base
        self.stack = tuple(start or (self.base,))
        self.exposed_fires, self.any_removal_resets = exposed_fires, any_removal_resets
        self.reverse_ties, self.default_repeat_ms = reverse_ties, default_repeat_ms
        self.soft_press_interrupts, self.hold_releases = soft_press_interrupts, hold_releases
        self.now, self.held, self.log = 0, set(), []
        self.between = set()            # held controls that are also inside an inverted range (`press_between`)
        self.acts = {}                  # (control, phase, kind, index) -> Act
        self.pressed_at = {}            # control -> when its last first press was (for a Double Press, A43)
        self.bound = {}                 # (control, phase) -> the layer whose binding is established there
        self._cache, self._order = {}, 0
        self._inverted = self._inverted_controls()
        self._rebind()
        self._drain()

    # --- reading the layout ---------------------------------------------------------------

    def _inverted_controls(self):
        """Controls that some layer binds with an inverted activator: active while the input is not held."""
        found = set()
        for title in self.layout.presets:
            for source, group in self.layout.active(title).items():
                for name in group.get("inputs", {}):
                    if any(e.inverted for e in self._entries_of(title, source, name)):
                        found.add((source, name))
        return found

    def _entries_of(self, layer, source, name):
        key = (layer, source, name)
        if key not in self._cache:
            group = self.layout.active(layer)[source]
            group_inverted = name == "edge" and (group.get("settings") or {}).get("edge_binding_invert") == "1"
            found = []
            for index, (kind, raw) in enumerate(entries(group["inputs"][name].get("activators", {}))):
                settings = raw.get("settings") or {}
                ops, outputs, taps, beeps, unsupported = [], [], [], [], []
                for action in reversed(actions(raw)):                     # execution order (A4)
                    command = COMMAND.search(action)
                    if command:
                        title = self.layout.resolve(TARGET.search(action).group(2))
                        ops.append((command.group(1), title))
                        if command.group(3) == "1":
                            beeps.append(title)
                    elif LEVEL.search(action):
                        outputs.append(" ".join(LEVEL.search(action).groups()).replace("key_press ", ""))
                    elif MOMENTARY.search(action):
                        taps.append(" ".join(MOMENTARY.search(action).groups()))
                    elif UNSUPPORTED.search(action):
                        unsupported.append(action.split(",")[0])
                condition = chord_condition(settings) if kind == "chord" else None
                found.append(Entry((source, name), layer, kind, index, settings, tuple(ops), tuple(outputs),
                                   tuple(taps), tuple(beeps),
                                   group_inverted or settings.get("edge_binding_invert") == "1",
                                   condition, tuple(unsupported)))
            self._cache[key] = found
        return self._cache[key]

    def binding(self, control):
        """(layer, entries) of the layer that answers `control` on the stack now, or (None, [])."""
        kind, layer, _, _ = resolve(self.layout, self.stack, *control)
        if kind != "binding":
            return (layer if kind in ("mode", "disabled") else None), []
        return layer, self._entries_of(layer, *control)

    def gyro_disabled(self):
        """True if the topmost gyro group on the stack is a disabled one."""
        for title in reversed(self.stack):
            group = self.layout.active(title).get("gyro")
            if group is not None:
                return group["mode"] == "disabled"
        return False

    # --- the log --------------------------------------------------------------------------

    def _note(self, what, detail):
        self.log.append((self.now, what, detail))

    def down(self):
        """The keys and mouse buttons held down now, sorted."""
        return sorted({output for act in self.acts.values() for output in act.down})

    def typed(self, since=0):
        """Every output that went down or ticked, in order: keys, mouse buttons and wheel steps."""
        return typed([event for event in self.log if event[0] >= since])

    def events(self, *kinds, since=0):
        return [(ms, what, detail) for ms, what, detail in self.log if what in kinds and ms >= since]

    # --- physical events -------------------------------------------------------------------

    def press(self, control):
        control = tuple(control)
        if control in self.held:
            raise ValueError(f"{'/'.join(control)} is already held")
        self._note("press", "/".join(control))
        self._end(control, "up")
        self.held.add(control)
        self._establish(control, "down", "pressed")
        self._rebind()
        self._drain()
        return self

    def _native(self, control, phase, mode, found):
        """An input with a Double Press or a Long Press (A43). Returns the entries left to arm as usual."""
        doubles = [e for e in found if e.kind == "Double_Press"]
        longs = [e for e in found if e.kind == "Long_Press"]
        if not doubles and not longs:
            return found
        window = max((int(e.settings.get("double_tap_time") or 0) for e in doubles), default=0)
        first = self.pressed_at.get(control)
        self.acts.pop((control, "tap"), None)                 # a new press: the pending tap never fires
        if mode == "pressed" and doubles and first is not None and self.now - first <= window:
            self.pressed_at.pop(control)
            for entry in self._ordered(doubles):                 # the second press: only the Double Press
                self._arm(entry, phase, mode)
            return []
        if mode == "pressed":
            self.pressed_at[control] = self.now
        for entry in self._ordered(longs):                       # fires if the input is still held then
            self._arm(entry, phase, mode, delay=int(entry.settings.get("long_press_time") or 0))
        rest = []
        for entry in found:
            if entry.kind in NATIVE:
                continue
            if entry.kind == "Full_Press" and entry.settings.get("interruptable") != "0" and doubles:
                self._arm(entry, phase, mode, delay=window)      # waits to see whether a second press comes
            else:
                rest.append(entry)
        return rest

    def press_between(self, control):
        """Hold an input between a normal Soft Press's threshold and an inverted one's: both are active.
        A normal one whose threshold is at or past the inverted one's has no overlap with it and stays off."""
        control = tuple(control)
        if control in self.held:
            raise ValueError(f"{'/'.join(control)} is already held")
        self._note("press", "/".join(control) + " (between)")
        self.held.add(control)
        self.between.add(control)
        if (control, "up") not in self.bound:
            self._establish(control, "up", "pressed")
        self._establish(control, "down", "pressed")
        self._rebind()
        self._drain()
        return self

    def release(self, control):
        control = tuple(control)
        if control not in self.held:
            raise ValueError(f"{'/'.join(control)} is not held")
        self._note("release", "/".join(control))
        _, found = self.binding(control)                      # the layer that answers it now (A7, A8)
        waiting = [act for key, act in self.acts.items() if key[:2] == (control, "down") and act.first
                   and act.entry.kind == "Full_Press" and any(e.kind == "Double_Press" for e in found)]
        self._end(control, "down")
        for act in waiting:                                   # a tap: the Regular Press fires once, later (A43)
            self.acts[(control, "tap")] = Act(act.entry, act.due, True, act.order)
        self.held.discard(control)
        was_between = control in self.between
        self.between.discard(control)
        if control in self._inverted and not (was_between and (control, "up") in self.bound):
            self._establish(control, "up", "pressed")        # an inverted activator starts when the input lets go
        for entry in self._ordered(e for e in found if e.kind == "release" and not e.inverted):
            self._run(entry, tap=True)
        self._rebind()
        self._drain()
        return self

    def lose(self, control):
        """A missed release (A25): the button is up, but no Release fires and the layers stay."""
        control = tuple(control)
        if control not in self.held:
            raise ValueError(f"{'/'.join(control)} is not held")
        self._note("lose", "/".join(control))
        self._end(control, "down")
        self.held.discard(control)
        self.between.discard(control)
        self._rebind()
        self._drain()
        return self

    def wait(self, ms):
        end = self.now + ms
        while True:
            due = [act.due for act in self.acts.values() if act.due is not None]
            if not due or min(due) > end:
                break
            self.now = max(self.now, min(due))
            self._drain()
        self.now = end
        return self

    # --- activators --------------------------------------------------------------------------

    def _ordered(self, found):
        found = list(found)
        return list(reversed(found)) if self.reverse_ties else found

    def _live(self):
        """The (control, phase) pairs that can have live activators now."""
        pairs = {(control, "down") for control in self.held}
        pairs |= {(control, "up") for control in self._inverted if control not in self.held or control in self.between}
        for title in self.stack:
            for source, group in self.layout.active(title).items():
                if ALWAYS_ON in group.get("inputs", {}):
                    pairs.add(((source, ALWAYS_ON), "down"))
        return pairs

    def _end(self, control, phase, handover=False):
        """End the activators of one input. `handover`: the input is still held and another layer takes over."""
        released = []
        for key in [k for k in self.acts if k[0] == control and k[1] == phase]:
            act = self.acts.pop(key)
            for output in act.down:
                self._note("handover" if handover else "up", output)
            if not handover:                            # covered, not let go: the hold is left alone
                released += act.holds
        self.bound.pop((control, phase), None)
        if self.hold_releases:                          # A42: a hold lets go with the activator that made it
            gone = [title for title in dict.fromkeys(released) if title in self.stack and title != self.base]
            for title in gone:
                self.stack = tuple(t for t in self.stack if t != title)
                self._note("remove", title)
            if gone:
                self._reset(gone)

    def _establish(self, control, phase, mode):
        """The binding that answers `control` starts answering it: decide which of its activators are live."""
        layer, found = self.binding(control)
        self.bound[(control, phase)] = layer
        if control in self.between:                     # between two ranges: a normal Soft Press that starts at or
            inner = [_threshold(e) for e in found if e.kind == "Soft_Press" and e.inverted]      # past the inverted
            found = [e for e in found if not (inner and e.kind == "Soft_Press" and not e.inverted  # one's edge
                                              and _threshold(e) >= max(inner))]                    # isn't reached
        active = [e for e in found if e.kind == "Soft_Press" and (control in self.between or e.inverted == (phase == "up"))]
        found = [e for e in found if e.kind != "release" and e.inverted == (phase == "up")]
        if self.soft_press_interrupts and any(e.settings.get("interruptable") == "0" for e in active):   # A39
            found = [e for e in found if e.kind != "Soft_Press" or e.settings.get("interruptable") == "0"]
        for entry in found:
            if entry.condition is not None and not entry.condition.known:
                raise NotImplementedError(f"{layer} {'/'.join(control)}: unknown chord button ({entry.condition.label})")
        if phase == "down":
            found = self._native(control, phase, mode, found)                                      # A43
        chords = [e for e in found if e.kind == "chord" and e.condition.satisfied(self.held)]     # A17, A36
        others = [e for e in found if e.kind != "chord" and not (chords and e.settings.get("interruptable") != "0")]
        for entry in self._ordered(sorted(chords + others, key=lambda e: e.index)):                # A27
            self._arm(entry, phase, mode)

    def _arm(self, entry, phase, mode, delay=None):
        delay = int(entry.settings.get("delay_start") or 0) if delay is None else delay
        repeat = self._repeat(entry)
        edge = mode == "pressed" or (mode == "exposed" and self.exposed_fires)                   # A5, A9
        self._order += 1
        act = Act(entry, self.now + delay, True, self._order)                                      # A6, A16
        if not edge and not delay and not (repeat is not None and mode == "landed"):
            act.allow_ops = False              # the press came before this binding: outputs only (A5, A10).
                                               # A repeating one that landed runs its commands all the same (A6);
                                               # one that a removal exposed waits for its next repeat (A9)
        self.acts[(entry.control, phase, entry.kind, entry.index)] = act

    def _repeat(self, entry):
        if entry.settings.get("hold_repeats") != "1":
            return None
        return int(entry.settings.get("repeat_rate") or self.default_repeat_ms)                    # A35

    def _drain(self):
        """Fire everything that is due now, one activator at a time, until nothing is."""
        for _ in range(10000):
            due = [(key, act) for key, act in self.acts.items() if act.due is not None and act.due <= self.now]
            if not due:
                return
            key, act = min(due, key=lambda pair: (pair[1].due, pair[1].order))     # `_ordered` set the order (A32)
            self._fire(key, act)
        raise RuntimeError(f"activators keep firing at {self.now} ms without time passing")

    def _fire(self, key, act):
        if key[1] == "tap":                                   # a Regular Press that waited out the Double Press time
            del self.acts[key]
            self._run(act.entry, tap=True)
            return
        if act.entry.kind == "Long_Press" and act.first:      # it interrupts the Regular Press (A43)
            for other in [k for k, a in self.acts.items() if k[:2] == key[:2] and a.entry.kind == "Full_Press"
                          and a.entry.settings.get("interruptable") != "0"]:
                for output in self.acts.pop(other).down:
                    self._note("up", output)
        entry, repeat = act.entry, self._repeat(act.entry)
        act.due = self.now + repeat if repeat is not None else None                                # A31
        if act.first:
            act.first = False
            for output in entry.outputs:
                act.down.append(output)
                self._note("down", output)
        else:
            for output in entry.outputs:
                self._note("tap", output)                                                          # a repeat types it again
        self._run(entry, act=act, commands=act.allow_ops)
        act.allow_ops = True                    # a later repeat does run the commands (A6)

    def _run(self, entry, act=None, tap=False, commands=True):
        """Run an entry: wheel steps and haptics, then its layer commands in order.

        `commands=False` is a binding that landed on a held input: its outputs fire (A10), its layer
        commands don't (A5).
        """
        if not commands:
            for output in entry.taps:
                self._note("tap", output)
            return
        if entry.unsupported:
            raise NotImplementedError(f"{entry.layer} {'/'.join(entry.control)}: {entry.unsupported[0]} is not simulated")
        if tap:
            for output in entry.outputs:
                self._note("tap", output)
        for output in entry.taps:
            self._note("tap", output)
        if int(entry.settings.get("haptic_intensity") or 0) > 0:
            self._note("haptic", f"{entry.settings['haptic_intensity']} {entry.layer} {'/'.join(entry.control)}")
        if act is not None and entry.ops:
            act.fired = True
        removed, before = [], self.stack
        for op, title in entry.ops:
            if op == "remove_layer":
                removed.append(title)
                if title in self.stack and title != self.base:
                    self.stack = tuple(t for t in self.stack if t != title)
                    self._note("remove", title)
            else:
                if title not in self.stack:                                                        # A3
                    self.stack += (title,)
                    self._note("add", title)
                if op == "hold_layer" and act is not None and title not in act.holds:
                    act.holds.append(title)
            if title in entry.beeps:
                self._note("beep", title)
        if removed:
            self._reset(removed, skip=act)
        if entry.ops:
            self._rebind(before)

    def _reset(self, removed, skip=None):
        """A removal restarts start delays (A12, A13)."""
        for act in self.acts.values():
            delay = int(act.entry.settings.get("delay_start") or 0)
            if not delay or act is skip:
                continue
            adds = {title for op, title in act.entry.ops if op == "add_layer"}
            if act.first and (self.any_removal_resets or adds & set(removed)):
                act.due = self.now + delay
            elif not act.first and act.due is None and adds & set(removed):
                act.first, act.due = True, self.now + delay      # a completed add whose target was removed
                for output in act.down:
                    self._note("up", output)
                act.down = []

    def _rebind(self, before=None):
        """After the stack or the held set changed: end activators whose layer no longer answers, start the new ones.

        `before` is the stack before the commands that just ran. A layer that wasn't on it has landed on the
        held input (A5); one that was there, under a layer that left, has been exposed (A9).
        """
        before = self.stack if before is None else before
        for key in [k for k, act in self.acts.items() if k[1] == "tap" and self.binding(k[0])[0] != act.entry.layer]:
            del self.acts[key]                                # the layer that owed the tap no longer answers
        live = self._live()
        for control, phase in [pair for pair in self.bound if pair not in live]:
            self._end(control, phase)
        for control, phase in sorted(live):
            layer, _ = self.binding(control)
            if (control, phase) in self.bound and self.bound[(control, phase)] == layer:
                continue
            self._end(control, phase, handover=True)
            how = "pressed" if control[1] == ALWAYS_ON else ("exposed" if layer in before else "landed")
            self._establish(control, phase, how)
