"""Scenarios for Ibex 1.1 (Neptune 90.77, DSE 1.1): the Fn layers take over from the Entry Points.

The record is findings/2026-10-16-fn-right-stick-owner/README.md; the plan is
plans/2026-10-16-fn-right-stick-owner.md, part 5. They run on the default scenario controller (Neptune's layouts,
the Deck's conversion of Ibex 1.1; `SCENARIO_CONTROLLER=ibex` runs them on Ibex's own), and the ones marked
`controller="dse"` on the Edge's.

- On the Deck the Fn layers' right stick typed nothing: a D-pad over the menu Entry Point's D-pad over Base's mouse
  stick. By the author's rule (A77) the Entry Point, the layer that changed the mode, answered the whole stick. Since
  Ibex 1.1 the Entry Points, the stick guards and the Tap Cover keep Base's mouse mode on the right stick, so Fn lands
  on a mouse stick and is its owner. In 1.1 every bind that adds an Fn layer also removed its Entry Point; on the Deck
  that broke the menu button's 200 ms delay after a stick guard ate it, so since Ibex 1.2 (Neptune 90.78, DSE 1.2) the
  Entry Point stays under Fn again (findings/2026-10-17-entry-point-stays-under-fn/).
- The stick clicks: an Entry Point's click adds its Fn layer at the press, silent and repeating, and also removes the
  guards and the Tap Cover; Fn's own click Release does the transition, command for command the Entry Point's.
- Each Fn stick key's click guard is one Any chord on both stick clicks, not interruptible: it holds the key's chord
  back (A78, verified by the author, 2026-10-17).
- Chords that differed only in their button are one Any chord (part 4).
"""
import unittest

from steam_layout.flow_model import chord_condition
from tests.scenario import DIRECTIONS, SOURCES, ScenarioCase, scenario

MENU = {"Menu Left": "Select", "Menu Right": "Start"}
OTHER = {"Select": "Start", "Start": "Select"}
COMBO = {"Menu Left": "Menu Left!Right: Entry Point", "Menu Right": "Menu Right!Left: Entry Point"}
MODES = {"Base": None, "Gyro": ("Base", "Gyro"), "Steering": "steering", "Cursor Gyro": ("Base", "Gyro", "Cursor Gyro")}
STATEFUL = ("Steering", "Cursor Gyro")
GUARDS = {"LS": "Menu Buttons: Left Stick Guard", "RS": "Menu Buttons: Right Stick Guard"}
TAP_COVER = "Menu Buttons: Tap Cover"
ENTRIES = ("Menu Left: Entry Point", "Menu Right: Entry Point", "Stateful | Menu Left: Entry Point",
           "Stateful | Menu Right: Entry Point")
COVERS = (*GUARDS.values(), TAP_COVER)        # what a click into Fn removes; since 1.2 the Entry Point stays
KEYS = {"LS": {"up": "BACKSLASH", "down": "FORWARD_SLASH", "right": "RIGHT_BRACKET", "left": "LEFT_BRACKET"},
        "RS": {"up": "SEMICOLON", "down": "SINGLE_QUOTE", "right": "PERIOD", "left": "COMMA"}}
MERGED_KEYS = {"A": "F3", "B": "F2", "X": "F4", "Y": "F1", "Up": "F5", "Down": "F7", "Right": "F6", "Left": "F8",
               "LT full": "F12", "RT full": "F11", "LB": "F10", "RB": "F9", "L5": "RIGHT_CONTROL", "R5": "RIGHT_ALT",
               "L4": "RIGHT_SHIFT", "R4": "LEFT_WINDOWS"}
TRANSITIONS = {("Menu Left", "LS"): ("Base", "Gamepad"), ("Menu Left", "RS"): ("Base", "Gyro", "Cursor Gyro"),
               ("Menu Right", "LS"): ("Base", "Steering"), ("Menu Right", "RS"): ("Base", "Gamepad")}
CLICKS = "71303168"                       # bits 22 and 26: either stick's click


def fn_of(side, mode="Base"):
    return f"{'Stateful | ' if mode in STATEFUL else ''}{side}: Fn Layer"


def entry_of(side, mode="Base"):
    return f"{'Stateful | ' if mode in STATEFUL else ''}{side}: Entry Point"


def other_stick(stick):
    return "RS" if stick == "LS" else "LS"


def bumps(pad):
    """Each haptic since the mark: intensity, layer and input."""
    return [detail for _, detail in pad.seen("haptic")]


def press_click(pad, stick):
    pad.touch(stick)
    pad.sim.press((SOURCES[stick], "click"))
    return pad


def let_go_click(pad, stick):
    pad.sim.release((SOURCES[stick], "click"))
    return pad


def right_stick_mode(pad):
    """The mode of the right-stick group that answers now: the topmost on the stack (A1, A2)."""
    for title in reversed(pad.stack):
        group = pad.layout.active(title).get("right_joystick")
        if group is not None:
            return group["mode"]
    return None


def live_click_guard(pad, stick, direction):
    """The click guard live on a stick direction now, with the held buttons meeting its chord, or None."""
    control = (SOURCES[stick], DIRECTIONS[direction])
    for act in pad.sim.acts.values():
        entry = act.entry
        if entry.control == control and entry.kind == "chord" and entry.settings.get("gyro_ratchet_button_mask") == CLICKS:
            return entry if chord_condition(entry.settings).satisfied(pad.sim.held) else None
    return None


class FnRightStick(ScenarioCase):
    @scenario("ibex 1.1 F1", rests=("A1", "A5", "A6", "A10", "A77"))
    def test_each_direction_types_its_key_with_a_low_bump_in_every_mode(self):
        for mode, start in MODES.items():
            for side, button in MENU.items():
                for resting in (False, True):
                    for pad in self.each(start=start):
                        fn = fn_of(side, mode)
                        if resting:
                            pad.touch("LS").touch("RS").wait(300)
                        pad.hold(button).wait(300)
                        self.assertEqual(pad.top, fn, (mode, side, resting))
                        self.assertTrue(pad.has(entry_of(side, mode)) and pad.lacks(*COVERS), "the Entry Point stays under Fn (1.2)")
                        for stick, keys in KEYS.items():
                            for where, key in keys.items():
                                pad.mark().push(stick, where).wait(80)
                                self.assertEqual(pad.typed(), [key], (mode, side, resting, stick, where))
                                self.assertEqual(bumps(pad), [f"1 {fn} {SOURCES[stick]}/{DIRECTIONS[where]}"])
                                pad.recentre(stick).wait(50)
                                if not resting:
                                    pad.lift(stick).wait(50)
                        self.assertEqual(pad.top, fn)
                        pad.let_go(button).lift("LS").lift("RS").wait(300)

    @scenario("ibex 1.1 F2", rules=("R123",), rests=("A3", "A4", "A5", "A6", "A7"))
    def test_every_adder_lands_fn_over_its_entry_point_with_no_guard_or_cover(self):
        gestures = {
            "the hold": lambda pad, button: pad.hold(button).wait(300),
            "the other menu button": lambda pad, button: pad.hold(button).wait(50).hold(OTHER[button]).wait(50),
            "the left stick touch's release": lambda pad, button: pad.touch("LS").wait(300).hold(button).wait(50).lift("LS").wait(50),
            "the right stick touch's release": lambda pad, button: pad.touch("RS").wait(300).hold(button).wait(50).lift("RS").wait(50),
            "the left stick click": lambda pad, button: press_click(pad.hold(button).wait(50), "LS").wait(30),
            "the right stick click": lambda pad, button: press_click(pad.hold(button).wait(50), "RS").wait(30),
        }
        for mode in ("Base", "Steering"):
            for side, button in MENU.items():
                for name, gesture in gestures.items():
                    for pad in self.each(start=MODES[mode]):
                        gesture(pad, button)
                        self.assertTrue(pad.has(fn_of(side, mode)), (mode, side, name))
                        self.assertTrue(pad.has(entry_of(side, mode)) and pad.lacks(*COVERS), (mode, side, name, pad.names()))
                        if name == "the other menu button" and mode == "Base":
                            self.assertEqual(pad.top, COMBO[side], "the chord also adds the combo Entry Point")

    @scenario("ibex 1.1 F3", rules=("R137",), rests=("A5", "A6", "A7", "A15"))
    def test_a_stick_click_reaches_its_transition_from_every_menu_layer(self):
        places = {"Fn": lambda pad, button, stick: pad.hold(button).wait(300),
                  "the Entry Point": lambda pad, button, stick: pad.hold(button).wait(100),
                  "its own stick's guard": lambda pad, button, stick: pad.hold(button).wait(50).push(stick, "up").wait(50),
                  "the other stick's guard": lambda pad, button, stick: pad.hold(button).wait(50).push(other_stick(stick), "up").wait(50),
                  "the Tap Cover": lambda pad, button, stick: pad.hold(button).wait(50).push(other_stick(stick), "up").wait(300)}
        under = {"Fn": None, "the Entry Point": None, "its own stick's guard": "own", "the other stick's guard": "other",
                 "the Tap Cover": TAP_COVER}
        for mode in ("Base", "Steering"):
            for side, button in MENU.items():
                for stick in ("LS", "RS"):
                    for place, setup in places.items():
                        for pad in self.each(start=MODES[mode]):
                            fn = fn_of(side, mode)
                            setup(pad, button, stick)
                            expected = {"own": GUARDS[stick], "other": GUARDS[other_stick(stick)]}.get(under[place], under[place])
                            if expected:
                                self.assertEqual(pad.top, expected, (mode, side, stick, place))
                            pad.mark()
                            press_click(pad, stick).wait(30)
                            self.assertEqual(pad.top, fn, f"{place}: Fn lands at the press")
                            self.assertTrue(pad.has(entry_of(side, mode)) and pad.lacks(*COVERS), (mode, side, stick, place, pad.names()))
                            self.assertEqual([b for b in bumps(pad) if b.endswith("/click")], [], "no bump at the press")
                            let_go_click(pad, stick).wait(30)
                            self.assertTrue(pad.lacks(fn))
                            pad.let_go(button).lift("LS").lift("RS").wait(400)
                            end = ("Base",) if mode in STATEFUL else TRANSITIONS[side, stick]
                            self.assertEqual(pad.names(), end, (mode, side, stick, place))

    @scenario("ibex 1.1 F4", rests=("A10", "A17", "A36", "A78"))
    def test_with_either_stick_clicked_neither_stick_types_an_fn_key(self):
        # The guard is not interruptible and the key's chord is, so the guard holds the key back (A78, the author,
        # 2026-10-17). New in 1.1: a click with the other stick out brings Fn in over that stick, and only the guard
        # keeps its key from typing until the click's Release.
        for side, button in MENU.items():
            for clicked in ("LS", "RS"):
                out = other_stick(clicked)
                for pad in self.each():
                    pad.hold(button).wait(50).push(out, "up").wait(50)
                    self.assertEqual(pad.top, GUARDS[out])
                    pad.mark()
                    press_click(pad, clicked).wait(30)
                    self.assertEqual(pad.top, fn_of(side), "Fn lands over the stick that is out")
                    self.assertIsNotNone(live_click_guard(pad, out, "up"), (side, clicked))
                    pad.roll(out, "right").wait(30)
                    self.assertIsNotNone(live_click_guard(pad, out, "right"), (side, clicked))
                    self.assertEqual((pad.typed(), pad.down()), ([], []), (side, clicked))
                    let_go_click(pad, clicked).let_go(button).lift("LS").lift("RS").wait(300)
                for pad in self.each():
                    pad.hold(button).wait(300).mark()
                    press_click(pad, clicked).wait(30)
                    for stick in ("LS", "RS"):
                        pad.push(stick, "left").wait(30)
                        self.assertIsNotNone(live_click_guard(pad, stick, "left"), (side, clicked, stick))
                        pad.recentre(stick).wait(30)
                    self.assertEqual(pad.typed(), [], (side, clicked))

    @scenario("ibex 1.1 F5", rules=("R170",), rests=("A17", "A25", "A27", "A36"))
    def test_a_stick_edge_cleans_up_fn_only_with_no_menu_button_held(self):
        for mode in ("Base", "Steering"):
            for side, button in MENU.items():
                for stick in ("LS", "RS"):
                    for pad in self.each(start=MODES[mode]):
                        fn = fn_of(side, mode)
                        pad.hold(button).wait(300)
                        for each in ("LS", "RS"):
                            pad.push(each, "up").wait(50).recentre(each).wait(50)
                        self.assertEqual(pad.top, fn, "the menu button is held: no cleanup")
                        pad.lift("LS").lift("RS").miss(button).wait(100)
                        self.assertEqual(pad.top, fn, "the release was missed")
                        pad.sim.press((SOURCES[stick], "edge"))
                        pad.wait(50)
                        self.assertTrue(pad.lacks(fn), (mode, side, stick))

    @scenario("ibex 1.1 F6", rests=("A17", "A36"))
    def test_each_merged_key_types_with_its_menu_button_and_with_both(self):
        for side, button in MENU.items():
            for pad in self.each():
                pad.hold(button).wait(300)
                for name, key in MERGED_KEYS.items():
                    pad.mark().tap(name).wait(30)
                    self.assertEqual(pad.typed(), [key], (side, name))
                self.assertEqual(pad.top, fn_of(side))
            for name in ("A", "B", "X", "Y", "Up", "Down", "Right", "Left"):     # the combo binds the others
                for pad in self.each():
                    pad.hold(button).wait(300).hold(OTHER[button]).wait(30)       # inside the combo's 200 ms
                    self.assertEqual(pad.names()[-2:], (fn_of(side), COMBO[side]))
                    pad.mark().tap(name).wait(30)
                    self.assertEqual(pad.typed(), [MERGED_KEYS[name]], (side, name, "both held"))

    @scenario("ibex 1.1 F7", rests=("A17", "A27", "A36"))
    def test_the_merged_edge_guards_hold_with_both_buttons(self):
        for first, second, layer in (("L1", "R1", "L1!R1: Modifier 2"), ("R1", "L1", "R1!L1: Modifier 2")):
            for pad in self.each():
                pad.hold(first).wait(50).hold(second).wait(50)
                self.assertTrue(pad.has(layer))
                for stick in ("LS", "RS"):
                    pad.push(stick, "up").wait(50).recentre(stick).wait(30)
                    self.assertTrue(pad.has(layer), (layer, stick))
        for side, button in MENU.items():
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.hold(button).wait(30).hold(OTHER[button]).wait(30)        # inside the combo's 200 ms
                    self.assertEqual(pad.top, COMBO[side])
                    pad.push(stick, "up").wait(40).recentre(stick).wait(20)
                    self.assertEqual(pad.top, COMBO[side], (side, stick))

    @scenario("ibex 1.1 F8", rests=("A1", "A2"))
    def test_the_right_stick_is_base_mouse_until_fn_lands(self):
        for side, button in MENU.items():
            for pad in self.each():
                pad.hold(button).wait(100)
                self.assertEqual((pad.top, right_stick_mode(pad)), (f"{side}: Entry Point", "joystick_mouse"))
                pad.push("LS", "up").wait(50)
                self.assertEqual((pad.top, right_stick_mode(pad)), (GUARDS["LS"], "joystick_mouse"))
                pad.push("RS", "up").wait(50)
                self.assertEqual((pad.top, right_stick_mode(pad)), (GUARDS["RS"], "joystick_mouse"))
                pad.wait(300)
                self.assertEqual((pad.top, right_stick_mode(pad)), (TAP_COVER, "joystick_mouse"))
                pad.let_go(button).lift("LS").lift("RS").wait(300)
                pad.hold(button).wait(300)
                self.assertEqual((pad.top, right_stick_mode(pad)), (fn_of(side), "dpad"))

    @scenario("ibex 1.1 F9", rests=("A6", "A15", "A16"))
    def test_a_stick_out_at_the_press_brings_its_guard_and_fn_follows_when_it_comes_back(self):
        for side, button in MENU.items():
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.push(stick, "right").wait(20).hold(button).wait(100)
                    self.assertEqual(pad.top, GUARDS[stick])
                    pad.recentre(stick).wait(20)
                    self.assertTrue(pad.lacks(GUARDS[stick]), "the guard leaves at the stick's edge Release")
                    self.assertEqual(pad.top, f"{side}: Entry Point")
                    pad.wait(150)
                    self.assertTrue(pad.lacks(fn_of(side)), "the 200 ms start again when the guard leaves (A15)")
                    pad.wait(100)
                    self.assertEqual(pad.top, fn_of(side))
                    self.assertTrue(pad.has(entry_of(side)) and pad.lacks(*COVERS))

    @scenario("ibex 1.1 F10", rules=("R169", "R170"), rests=("A25",))
    def test_a_release_missed_in_the_steam_menu_clears_at_the_next_stick_touch(self):
        for mode in ("Base", "Steering"):
            for side, button in MENU.items():
                for stick in ("LS", "RS"):
                    for pad in self.each(start=MODES[mode]):
                        pad.hold(button).wait(300).miss(button).wait(100)
                        self.assertEqual(pad.top, fn_of(side, mode))
                        pad.touch(stick).wait(50)
                        self.assertTrue(pad.lacks(fn_of(side, mode), *ENTRIES, *COVERS), (mode, side, stick))

    @scenario("ibex 1.1 F11", rules=("R170",), rests=("A25",), controller="dse")
    def test_on_the_edge_fn_takes_over_and_a_missed_release_clears_at_the_next_stick_push(self):
        for side, button in MENU.items():
            for stick in ("LS", "RS"):
                for pad in self.each(controller="dse"):
                    press_click(pad.hold(button).wait(50), stick).wait(30)
                    self.assertEqual(pad.top, fn_of(side))
                    self.assertTrue(pad.has(entry_of(side)) and pad.lacks(*COVERS))
                    let_go_click(pad, stick).let_go(button).wait(400)
                    self.assertEqual(pad.names(), TRANSITIONS[side, stick])
                for pad in self.each(controller="dse"):
                    pad.hold(button).wait(300)
                    self.assertEqual(pad.top, fn_of(side))
                    self.assertTrue(pad.has(entry_of(side)) and pad.lacks(*COVERS))
                    for where, key in KEYS[stick].items():
                        pad.mark().push(stick, where).wait(80)
                        self.assertEqual(pad.typed(), [key], (side, stick, where))
                        pad.recentre(stick).wait(50)
                    pad.miss(button).wait(100).push(stick, "up").wait(50)
                    self.assertTrue(pad.lacks(fn_of(side)), (side, stick))

    @scenario("ibex 1.1 F12", rests=("A6", "A15", "A16", "A17", "A36"), controller="dse")
    def test_on_the_edge_the_changed_menu_modifier_and_steering_layers_still_land(self):
        # The Edge's layouts changed in 38 layers (R165). With no stick touch these are their ways in.
        for pad in self.each(controller="dse"):
            pad.hold("Start").wait(50).push("LS", "up").wait(50)
            self.assertEqual(pad.top, GUARDS["LS"])
            pad.push("RS", "up").wait(50)
            self.assertEqual(pad.top, GUARDS["RS"])
            pad.wait(250)
            self.assertEqual(pad.top, TAP_COVER)
        for first, second, combo, key in (("Select", "Start", "Menu Left!Right", "Enter"),
                                          ("Start", "Select", "Menu Right!Left", "Backspace")):
            for pad in self.each(controller="dse"):
                pad.hold(first).wait(50).hold(second).wait(50)
                self.assertEqual(pad.top, f"{combo}: Entry Point")
                pad.let_go(second).wait(30)
                self.assertEqual(pad.top, f"{combo}: Double Tap")
                pad.hold(second).wait(30)
                self.assertEqual(pad.top, f"{combo}: {key}")
                pad.wait(250)
                self.assertEqual(pad.top, f"{combo}: Double Tap Cover")
        for start, prefix in ((None, ""), (("Base", "Gyro"), "Gyro | ")):
            for first, second in (("L1", "R1"), ("R1", "L1")):
                for pad in self.each(controller="dse", start=start):
                    pad.hold(first).wait(50).hold(second).wait(50)
                    self.assertTrue(pad.has(f"{prefix}{first}!{second}: Modifier 2"), (start, first))
        for driver, other, key in (("R1", "L1", "W Key"), ("L1", "R1", "S Key")):
            for pad in self.each(controller="dse", start="steering"):
                pad.hold(driver).wait(50)
                self.assertTrue(pad.has(f"Steering | {driver}: {key}"))
                pad.hold(other).wait(50)
                self.assertTrue(pad.has(f"Steering | {driver}!{other}: Modifier 2"))
            for direction, word, modifier in (("up", "Up", "Modifier 1"), ("down", "Down", "Modifier 0")):
                for pad in self.each(controller="dse", start="steering"):
                    pad.hold(driver).wait(50).push("LS", direction).wait(300)
                    self.assertTrue(pad.has(f"Steering | LS {word}: {modifier}", "Steering | LS: Tap Cover"))
                for pad in self.each(controller="dse", start="steering"):
                    pad.hold(driver).wait(50).flick("LS", direction).wait(10)
                    self.assertTrue(pad.has(f"Steering | LS {word}: Double Tap"), (driver, direction))
                    pad.wait(50).push("LS", direction).wait(20)
                    self.assertTrue(pad.has(f"Steering | LS {word}: Scroll {word}"), (driver, direction))
                    pad.wait(300)
                    self.assertTrue(pad.has("Steering | LS: Double Tap Cover"), (driver, direction))
        for side, button in MENU.items():
            for pad in self.each(controller="dse", start="steering"):
                pad.hold(button).wait(100)
                self.assertEqual(pad.top, f"Stateful | {side}: Entry Point")
                pad.wait(250)
                self.assertEqual(pad.top, fn_of(side, "Steering"))
                self.assertTrue(pad.has(entry_of(side, "Steering")) and pad.lacks(*COVERS))


if __name__ == "__main__":
    unittest.main()
