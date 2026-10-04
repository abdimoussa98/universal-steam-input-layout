"""The press simulator (steam_layout/simulator.py), on tiny made-up layouts.

One behaviour per test, each named with the Steam assumption it models
(resources/Steam Behaviour Assumptions.md).
"""
import unittest

from steam_layout.model import Layout
from steam_layout.simulator import Simulator, desktop
from tests.test_audit_inheritance import EMPTY, add, build, remove
from tests.test_chains import SW, on, press, release

LB, RB = ("switch", "left_bumper"), ("switch", "right_bumper")
A, B, X = ("switch", "button_a"), ("switch", "button_b"), ("switch", "button_x")
EDGE = ("joystick", "edge")


def key(name, kind="Full_Press", **settings):
    return on(kind, f"key_press {name}, , ", **settings)


def sim(layers, **options):
    return Simulator(Layout(build(layers)), **options)


def hold():
    """Base's LB adds P; P ends on the LB Release."""
    return {"Base": {"switch": (SW, {"left_bumper": press(add("P")), "button_a": key("Q")})},
            "P": {"switch": (SW, {"left_bumper": release(remove("P")), "button_a": key("F")})}}


class StackTests(unittest.TestCase):
    def test_a_press_adds_and_the_release_in_the_top_layer_removes(self):       # A1, A7
        s = sim(hold())
        self.assertEqual(s.press(LB).stack, ("Base", "P"))
        self.assertEqual(s.release(LB).stack, ("Base",))

    def test_an_array_runs_bottom_to_top_and_a_re_add_does_not_move(self):      # A3, A4
        s = sim({"Base": {"switch": (SW, {"button_a": press(add("X")), "button_b": press(remove("X"), add("Y"), add("X"))})},
                 "X": {}, "Y": {}})
        s.press(A)
        self.assertEqual(s.stack, ("Base", "X"))
        s.press(B)                       # remove X, add Y, add X: X ends on top
        self.assertEqual(s.stack, ("Base", "Y", "X"))
        s.release(A).press(A)            # re-adding X leaves it where it is
        self.assertEqual(s.stack, ("Base", "Y", "X"))

    def test_the_topmost_layer_that_binds_the_input_answers_it(self):           # A1
        s = sim(hold())
        s.press(A)
        self.assertEqual(s.down(), ["Q"])
        s.release(A).press(LB).press(A)
        self.assertEqual(s.down(), ["F"])

    def test_a_release_that_a_layer_above_takes_never_reaches_the_lower_layer(self):   # the hidden exit, R136
        layers = hold()
        layers["Base"]["switch"][1]["button_b"] = press(add("C"))
        layers["C"] = {"switch": (SW, {"left_bumper": release(remove("C"))})}
        s = sim(layers)
        s.press(LB).press(B).release(LB)
        self.assertEqual(s.stack, ("Base", "P"))     # C took the Release; P is stranded


class OutputTests(unittest.TestCase):
    def test_a_key_is_down_while_its_button_is_held(self):
        s = sim(hold())
        s.press(A)
        self.assertEqual(s.down(), ["Q"])
        s.release(A)
        self.assertEqual((s.down(), s.typed()), ([], ["Q"]))

    def test_a_release_activator_types_its_key_once(self):
        s = sim({"Base": {"switch": (SW, {"button_a": key("TAB", "release")})}})
        s.press(A).release(A)
        self.assertEqual((s.typed(), s.down()), (["TAB"], []))

    def test_a_repeating_key_is_typed_again_each_interval(self):                # A35 when no rate is given
        s = sim({"Base": {"switch": (SW, {"button_a": key("Z", hold_repeats=1, repeat_rate=200),
                                          "button_b": key("Y", hold_repeats=1)})}}, default_repeat_ms=100)
        s.press(A).wait(450)
        self.assertEqual(s.typed(), ["Z", "Z", "Z"])           # at 0, 200 and 400 ms
        s.release(A).press(B).wait(250)
        self.assertEqual(s.typed(since=450), ["Y", "Y", "Y"])  # at 0, 100 and 200 ms after the press

    def test_a_key_handed_to_another_binding_at_the_same_moment_is_not_typed_again(self):   # A37
        s = sim({"Base": {"switch": (SW, {"button_a": key("W"), "button_b": press(add("P"))})},
                 "P": {"switch": (SW, {"button_a": key("W"), "button_b": release(remove("P"))})}})
        s.press(A).press(B)                           # P lands on held A and sends the same key
        self.assertEqual((s.down(), s.typed()), (["W"], ["W"]))
        s.release(B)                                  # P leaves: Base's W takes over
        self.assertEqual((s.down(), s.typed()), (["W"], ["W"]))
        s.release(A).press(A)                         # a real release and press at the same moment is typed again
        self.assertEqual(s.typed(), ["W", "W"])

    def test_haptics_and_beeps_are_logged(self):
        beep = "controller_action add_layer {{Base::P}} 1 0, , "
        s = sim({"Base": {"switch": (SW, {"button_a": on("Full_Press", beep, haptic_intensity=3)})}, "P": {}})
        s.press(A)
        self.assertEqual([what for _, what, _ in s.events("haptic", "beep")], ["haptic", "beep"])


class ChordTests(unittest.TestCase):
    def guarded(self):
        """A is F1 with LB held; with no LB it removes P (a cleanup function)."""
        return {"Base": {"switch": (SW, {"left_bumper": press(add("P"))})},
                "P": {"switch": (SW, {"left_bumper": release(remove("P")),
                                      "button_a": {**key("F1", "chord", chord_button=1),
                                                   **press(remove("P"), hold_repeats=1)}})}}

    def test_a_chord_fires_and_suppresses_an_interruptible_regular_press(self):  # A27
        s = sim(self.guarded())
        s.press(LB).press(A)
        self.assertEqual((s.down(), s.stack), (["F1"], ("Base", "P")))

    def test_without_the_chord_button_the_regular_press_fires(self):             # the cleanup function, A25
        s = sim(self.guarded())
        s.press(LB).lose(LB)             # a missed release: P stays
        self.assertEqual(s.stack, ("Base", "P"))
        s.press(A)
        self.assertEqual((s.stack, s.down()), (("Base",), []))

    def test_an_uninterruptible_regular_press_fires_beside_the_chord(self):
        layers = self.guarded()
        layers["P"]["switch"][1]["button_a"] = {**key("F1", "chord", chord_button=1),
                                               **press(remove("Other"), interruptable=0, hold_repeats=1)}
        s = sim(layers)
        s.press(LB).press(A)
        self.assertEqual(s.down(), ["F1"])
        self.assertIn("switch/button_a", {d for _, what, d in s.log if what == "press"})
        self.assertTrue(any(act.entry.kind == "Full_Press" for act in s.acts.values()))

    def test_any_and_all_masks(self):                                            # A30
        both = {"gyro_ratchet_button_mask": (1 << 2) | (1 << 3), "gyro_ratchet_button_requireany_or_all": 1}
        any_ = {"gyro_ratchet_button_mask": (1 << 2) | (1 << 3), "gyro_ratchet_button_requireany_or_all": 0}
        from steam_layout.flow_model import chord_condition
        controls = sorted(chord_condition({k: str(v) for k, v in both.items()}).controls())
        first, second = controls[0], controls[-1]
        for settings, expected in ((both, []), (any_, ["K"])):
            s = sim({"Base": {"switch": (SW, {"button_a": key("K", "chord", **settings)})}})
            s.press(first).press(A)                   # one of the two chord buttons is held
            self.assertEqual(s.down(), expected, settings)

    def test_a_chord_latches_when_the_chord_button_lets_go(self):                # A17
        s = sim(self.guarded())
        s.press(LB).press(A).lose(LB)
        self.assertEqual(s.down(), ["F1"])           # still in the chord until A is released
        self.assertEqual(s.stack, ("Base", "P"))     # and the cleanup stays suppressed

    def test_pressing_the_chord_button_afterwards_does_not_start_the_chord(self):    # A36
        s = sim({"Base": {"switch": (SW, {"button_a": {**key("F1", "chord", chord_button=1), **key("Q")}})}})
        s.press(A).press(LB)
        self.assertEqual(s.down(), ["Q"])


class TimeTests(unittest.TestCase):
    def delayed(self):
        """Base's A adds P after 200 ms, and resets it every 250 ms; P binds A, so the reset stops."""
        return {"Base": {"switch": (SW, {"button_a": {**on("chord", add("P"), chord_button=1, delay_start=200),
                                                      **press(remove("P"), hold_repeats=1, repeat_rate=250, interruptable=0),
                                                      **release(remove("P"))},
                                         "button_b": press(remove("Other"))})},
                "P": {"switch": (SW, {"button_a": release(remove("P"))})}}

    def test_a_delayed_add_lands_when_its_delay_ends(self):
        s = sim(self.delayed())
        s.press(LB).press(A).wait(199)
        self.assertEqual(s.stack, ("Base",))
        s.wait(1)
        self.assertEqual(s.stack, ("Base", "P"))
        s.wait(1000)                                  # P binds A: the reset can't remove it (R122)
        self.assertEqual(s.stack, ("Base", "P"))

    def test_letting_go_before_the_delay_cancels_it(self):
        s = sim(self.delayed())
        s.press(LB).press(A).wait(150).release(A).wait(500)
        self.assertEqual(s.stack, ("Base",))

    def test_a_removal_restarts_a_pending_delay(self):                            # A12, A13
        s = sim(self.delayed())
        s.press(LB).press(A).wait(150).press(B)       # B's removal at 150 ms restarts the 200 ms: due at 350
        s.wait(299)                                   # the reset at 250 ms restarts it again: due at 450
        self.assertEqual(s.stack, ("Base",))
        s.wait(1)                                     # it lands before the next reset at 500 ms (R121)
        self.assertEqual(s.stack, ("Base", "P"))

    def test_only_the_targets_own_removal_restarts_it_when_the_switch_is_off(self):   # A12 without A13
        s = sim(self.delayed(), any_removal_resets=False)
        s.press(LB).press(A).wait(150).press(B).wait(50)
        self.assertEqual(s.stack, ("Base", "P"))

    def test_an_always_on_window_removes_itself_after_its_delay(self):            # A16: the clock starts with the layer
        s = sim({"Base": {"switch": (SW, {"button_a": release(add("W"))})},
                 "W": {"switch": (SW, {"always_on_action": {"Full_Press": [
                     {"bindings": {"binding": remove("W")}, "settings": {"delay_start": "150"}},
                     {"bindings": {"binding": "key_press ESCAPE, , "}, "settings": {"delay_start": "50"}}]}})}})
        s.press(A).wait(500).release(A)
        self.assertEqual(s.stack, ("Base", "W"))
        s.wait(49)
        self.assertEqual(s.typed(), [])
        s.wait(1)
        self.assertEqual((s.typed(), s.down()), (["ESCAPE"], ["ESCAPE"]))
        s.wait(100)
        self.assertEqual((s.stack, s.down(), s.typed()), (("Base",), [], ["ESCAPE"]))

    def test_same_moment_activators_run_in_file_order_or_reversed(self):          # A32
        both = {"Full_Press": [{"bindings": {"binding": add("X")}}, {"bindings": {"binding": add("Y")}}]}
        layers = {"Base": {"switch": (SW, {"button_a": both})}, "X": {}, "Y": {}}
        self.assertEqual(sim(layers).press(A).stack, ("Base", "X", "Y"))
        self.assertEqual(sim(layers, reverse_ties=True).press(A).stack, ("Base", "Y", "X"))


class HeldInputTests(unittest.TestCase):
    def landing(self, binding):
        """LB adds L over a held A; L binds A with `binding`."""
        return {"Base": {"switch": (SW, {"left_bumper": press(add("L")), "button_a": key("Q")})},
                "L": {"switch": (SW, {"button_a": binding})}, "T": {}}

    def test_an_immediate_layer_command_does_not_fire_on_a_held_input(self):      # A5
        s = sim(self.landing(press(add("T"))))
        s.press(A).press(LB).wait(1000)
        self.assertEqual(s.stack, ("Base", "L"))
        s.release(A).press(A)                         # a fresh press does fire it
        self.assertEqual(s.stack, ("Base", "L", "T"))

    def test_a_delayed_command_fires_when_its_delay_ends(self):                   # A6, A16
        s = sim(self.landing(press(add("T"), delay_start=5)))
        s.press(A).wait(300).press(LB).wait(4)
        self.assertEqual(s.stack, ("Base", "L"))
        s.wait(1)
        self.assertEqual(s.stack, ("Base", "L", "T"))

    def test_a_repeating_command_fires_at_its_next_repeat(self):                  # A6
        s = sim(self.landing(press(add("T"), hold_repeats=1, repeat_rate=50)))
        s.press(A).press(LB)
        self.assertEqual(s.stack, ("Base", "L"))
        s.wait(50)
        self.assertEqual(s.stack, ("Base", "L", "T"))

    def test_a_key_does_go_down_on_a_held_input(self):                            # A10
        s = sim(self.landing(key("F")))
        s.press(A).press(LB)
        self.assertEqual((s.down(), s.typed()), (["F"], ["Q", "F"]))

    def test_a_wheel_step_fires_on_a_held_input_too(self):                        # A10: the second-press scroll
        s = sim(self.landing(on("Full_Press", "mouse_wheel SCROLL_DOWN, , ")))
        s.press(A).press(LB)
        self.assertEqual(s.typed(), ["Q", "mouse_wheel SCROLL_DOWN"])

    def test_a_layer_added_beside_a_removal_has_landed_not_been_exposed(self):    # A5
        s = sim({"Base": {"switch": (SW, {"button_a": press(add("Old")), "button_b": press(remove("Old"), add("New"))})},
                 "Old": {"switch": (SW, {"button_x": key("O")})},
                 "New": {"switch": (SW, {"button_x": press(add("T"))})}, "T": {}})
        s.press(A).press(X).press(B)                  # B swaps Old for New under a held X
        self.assertEqual(s.stack, ("Base", "New"))    # New's command on X doesn't fire: the press came first

    def exposing(self):
        """A is held in L, whose A removes L; Base's A then adds T and holds Q."""
        return {"Base": {"switch": (SW, {"left_bumper": press(add("L")),
                                         "button_a": {"Full_Press": [{"bindings": {"binding": add("T")}},
                                                                     {"bindings": {"binding": "key_press Q, , "}}]}})},
                "L": {"switch": (SW, {"button_a": press(remove("L"))})}, "T": {}}

    def test_a_removal_exposes_the_lower_command_one_way_or_the_other(self):      # A9: the layout works either way
        fires = sim(self.exposing(), exposed_fires=True)
        fires.press(LB).press(A)
        self.assertEqual(fires.stack, ("Base", "T"))
        waits = sim(self.exposing(), exposed_fires=False)
        waits.press(LB).press(A)
        self.assertEqual(waits.stack, ("Base",))

    def test_a_key_exposed_by_a_removal_goes_down(self):                          # A11
        for fires in (True, False):
            s = sim(self.exposing(), exposed_fires=fires)
            s.press(LB).press(A)
            self.assertEqual(s.down(), ["Q"], fires)

    def test_a_layer_that_binds_the_button_ends_the_delay_running_on_it(self):    # A15
        s = sim({"Base": {"switch": (SW, {"button_a": press(add("Fn"), delay_start=200), "button_b": press(add("G"))})},
                 "G": {"switch": (SW, {"button_a": key("TAB"), "button_b": release(remove("G"))})}, "Fn": {}})
        s.press(A).wait(100).press(B).wait(500)       # G lands on held A inside the 200 ms
        self.assertEqual(s.stack, ("Base", "G"))
        s.release(B).wait(199)                        # G leaves: the delay starts again from zero (A14)
        self.assertEqual(s.stack, ("Base",))
        s.wait(1)
        self.assertEqual(s.stack, ("Base", "Fn"))


class NativeActivatorTests(unittest.TestCase):
    """A Double Press and a Long Press beside an interruptible Regular Press (A43), as on Gamepad's Start."""

    def menu(self):
        start = {**key("START"), **key("START", "Double_Press", double_tap_time=200),
                 **on("Long_Press", EMPTY, long_press_time=200, haptic_intensity=1)}
        return {"Base": {"switch": (SW, {"button_a": start, "button_b": press(add("G"))})},
                "G": {"switch": (SW, {"button_a": key("TAB")})}}

    def test_a_tap_sends_the_regular_press_once_after_the_double_press_time(self):
        s = sim(self.menu())
        s.press(A).wait(30).release(A).wait(169)
        self.assertEqual(s.typed(), [])
        s.wait(1)
        self.assertEqual((s.typed(), s.down()), (["START"], []))

    def test_a_hold_sends_only_the_long_press(self):
        s = sim(self.menu())
        s.press(A).wait(600)
        self.assertEqual((s.typed(), s.down()), ([], []))
        self.assertEqual([detail for _, what, detail in s.log if what == "haptic"], ["1 Base switch/button_a"])
        s.release(A).wait(600)
        self.assertEqual(s.typed(), [])

    def test_a_second_press_sends_only_the_double_press_for_as_long_as_it_is_held(self):
        s = sim(self.menu())
        s.press(A).wait(30).release(A).wait(60).press(A).wait(600)
        self.assertEqual((s.typed(), s.down()), (["START"], ["START"]))
        s.release(A).wait(600)
        self.assertEqual((s.typed(), s.down()), (["START"], []))

    def test_two_slow_taps_are_two_taps(self):
        s = sim(self.menu())
        s.press(A).wait(30).release(A).wait(400).press(A).wait(30).release(A).wait(400)
        self.assertEqual(s.typed(), ["START", "START"])

    def test_a_layer_that_binds_the_button_ends_the_tap_that_was_waiting(self):   # A15
        s = sim(self.menu())
        s.press(A).wait(30).release(A).wait(50).press(B).wait(600)
        self.assertEqual((s.stack, s.typed()), (("Base", "G"), []))

    def test_without_a_double_press_the_regular_press_fires_at_once_and_the_long_press_ends_it(self):
        start = {**key("START"), **on("Long_Press", EMPTY, long_press_time=200)}
        s = sim({"Base": {"switch": (SW, {"button_a": start})}})
        s.press(A).wait(100)
        self.assertEqual(s.down(), ["START"])
        s.wait(100)
        self.assertEqual(s.down(), [])

    def test_a_gamepad_button_is_an_output(self):
        s = sim({"Base": {"switch": (SW, {"button_a": press("xinput_button A, , ")})}})
        s.press(A)
        self.assertEqual(s.down(), ["xinput_button A"])


class EdgeTests(unittest.TestCase):
    def test_an_inverted_edge_fires_when_the_stick_comes_back_in(self):
        ramp = {"Soft_Press": {"bindings": {"binding": remove("Ramp")},
                               "settings": {"edge_binding_invert": "1", "hold_repeats": "1"}}}
        s = sim({"Base": {"joystick": ("joystick_mouse", {"edge": press(add("Ramp"))})},
                 "Ramp": {"joystick": ("joystick_mouse", {"edge": ramp})}})
        s.press(EDGE).wait(500)
        self.assertEqual(s.stack, ("Base", "Ramp"))
        s.release(EDGE)
        self.assertEqual(s.stack, ("Base",))

    def test_an_exit_already_true_when_its_layer_lands_waits_for_its_repeat(self):   # A5, A6 on an inverted edge
        ramp = {"Soft_Press": {"bindings": {"binding": remove("Ramp")},
                               "settings": {"edge_binding_invert": "1", "hold_repeats": "1", "repeat_rate": "80"}}}
        s = sim({"Base": {"switch": (SW, {"button_a": press(add("Ramp"))})},
                 "Ramp": {"joystick": ("joystick_mouse", {"edge": ramp})}})
        s.press(A)                                    # the stick is already in when Ramp lands
        self.assertEqual(s.stack, ("Base", "Ramp"))
        s.wait(80)
        self.assertEqual(s.stack, ("Base",))

    def ring(self, **options):
        """A pad edge with two Soft Presses: an inverted one inside 3, not interruptible, and a normal one past 2."""
        def soft(name, **settings):
            return {"bindings": {"binding": f"key_press {name}, , "}, "settings": {k: str(v) for k, v in settings.items()}}
        edge = {"Soft_Press": [soft("IN", activation_threshold=3, edge_binding_invert=1, interruptable=0),
                               soft("OUT", activation_threshold=2)]}
        return sim({"Base": {"joystick": ("dpad", {"edge": edge})}}, **options)

    def test_an_input_is_inside_the_inverted_range_or_past_the_normal_one(self):
        s = self.ring()
        self.assertEqual(s.down(), ["IN"])                    # not held: inside
        self.assertEqual(s.press(EDGE).down(), ["OUT"])       # held: past the threshold
        self.assertEqual(s.release(EDGE).down(), ["IN"])

    def test_between_the_two_the_uninterruptible_soft_press_suppresses_the_other(self):   # A39
        s = self.ring()
        self.assertEqual(s.press_between(EDGE).down(), ["IN"])
        self.assertEqual(s.release(EDGE).down(), ["IN"])      # still inside: it never let go
        self.assertEqual(s.typed(), ["IN"])

    def test_between_the_two_both_fire_when_the_switch_is_off(self):                      # A39 false
        s = self.ring(soft_press_interrupts=False)
        self.assertEqual(s.press_between(EDGE).down(), ["IN", "OUT"])
        self.assertEqual(s.release(EDGE).down(), ["IN"])

    HOLD_P = "controller_action hold_layer {{Base::P}} 0 0, , "

    def test_a_hold_puts_the_layer_on_and_takes_it_off_with_the_press(self):      # A42
        s = sim({"Base": {"switch": (SW, {"button_a": press(self.HOLD_P)})}, "P": {}})
        self.assertEqual(s.press(A).stack, ("Base", "P"))
        self.assertEqual(s.release(A).stack, ("Base",))

    def test_a_hold_only_puts_the_layer_on_when_the_switch_is_off(self):          # A42 false
        s = sim({"Base": {"switch": (SW, {"button_a": press(self.HOLD_P)})}, "P": {}}, hold_releases=False)
        self.assertEqual(s.press(A).release(A).stack, ("Base", "P"))

    def test_a_layer_that_holds_itself_on_a_held_input_never_gets_its_hold(self):  # A5: the hold is a layer command
        own = {"switch": (SW, {"button_a": press(self.HOLD_P)})}
        s = sim({"Base": {"switch": (SW, {"button_a": press(add("P"))})}, "P": own})
        s.press(A)                                    # P lands on A, which is already down: its hold doesn't fire
        self.assertEqual(s.release(A).stack, ("Base", "P"))
        self.assertEqual(s.press(A).release(A).stack, ("Base",))    # a fresh press in P holds it, and the release ends it

    def test_a_hold_that_is_covered_is_left_alone(self):
        s = sim({"Base": {"switch": (SW, {"button_a": press(self.HOLD_P)})},
                 "P": {"switch": (SW, {"button_b": press(add("C"))})},
                 "C": {"switch": (SW, {"button_a": press(EMPTY)})}})
        s.press(A).press(B)                           # C takes A's binding while A is down
        self.assertEqual(s.stack, ("Base", "P", "C"))
        self.assertEqual(s.release(A).stack, ("Base", "P", "C"))    # the release went to C: nothing lets go of P

    def test_mode_shifts_are_refused(self):
        s = sim({"Base": {"switch": (SW, {"button_a": press("controller_action mode_shift joystick 7, , ")})}})
        with self.assertRaises(NotImplementedError):
            s.press(A)

    def test_the_desktop_configuration_keeps_three_entries(self):                # A21
        four = {"release": {"bindings": {"binding": remove("P")}},
                "chord": {"bindings": {"binding": add("C")}, "settings": {"chord_button": "1", "delay_start": "150"}},
                "Full_Press": [{"bindings": {"binding": "key_press Q, , "}},
                               {"bindings": {"binding": remove("C")}, "settings": {"hold_repeats": "1"}}]}
        data = build({"Base": {"switch": (SW, {"button_a": four})}, "P": {}, "C": {}})
        kept = desktop(data)["controller_mappings"]["group"][0]["inputs"]["button_a"]["activators"]
        self.assertEqual(list(kept), ["release", "chord", "Full_Press"])
        self.assertEqual(kept["Full_Press"], {"bindings": {"binding": "key_press Q, , "}})     # the reset, last, is the one dropped
        self.assertEqual(len(data["controller_mappings"]["group"][0]["inputs"]["button_a"]["activators"]["Full_Press"]), 2)

    def test_a_disabled_gyro_on_the_stack(self):
        s = sim({"Base": {"switch": (SW, {"button_a": press(add("Off"))}), "gyro": ("gyro_to_mouse", {})},
                 "Off": {"gyro": ("disabled", {})}})
        self.assertFalse(s.gyro_disabled())
        self.assertTrue(s.press(A).gyro_disabled())


class WalkCrossCheck(unittest.TestCase):
    """The simulator, given physical presses, reaches the stacks `stacks.walk` reaches when it is told
    which activator fires. Both working layouts, with Gyro off and on (the sequences of test_modifier_rocking)."""

    @classmethod
    def setUpClass(cls):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        cls.layouts = {v: Layout(json.loads((root / f"neptune/single-set-{v}_hold-gyro_latest.json").read_text()))
                       for v in ("default", "alternative")}

    def cases(self):
        from tests.test_modifier_rocking import VARIANTS, Names
        for variant, (L, R, entry, sides) in VARIANTS.items():
            for gyro in (False, True):
                yield f"{variant}{', Gyro' if gyro else ''}", self.layouts[variant], L, R, entry, Names(sides, gyro)

    def compare(self, layout, n, pairs, **options):
        """pairs: (the walk step this physical action stands for, or None; the action)."""
        from steam_layout.stacks import walk
        expected = iter(walk(layout, [step for step, _ in pairs if step], start=n.base))
        s = Simulator(layout, start=n.base, **options)
        for step, (what, value) in pairs:
            getattr(s, what)(value)
            if step:
                self.assertEqual(s.stack, next(expected)["stack"], step[-1])
        return s

    def test_rocking_in_both_directions(self):
        for label, layout, L, R, entry, n in self.cases():
            for first, second in ((L, R), (R, L)):
                with self.subTest(label, first=first):
                    s = self.compare(layout, n, [
                        ((*first, entry, "hold the first side"), ("press", first)),
                        ((*second, "chord", "hold the second side"), ("press", second)),
                        ((*second, "chord", "200 ms: the combined cover"), ("wait", 200)),
                        ((*first, "release", "let go of the first"), ("release", first)),
                        ((*first, "chord", "press it again"), ("press", first)),
                        ((*first, "chord", "200 ms: the combined cover"), ("wait", 200)),
                        ((*second, "release", "let go of the second"), ("release", second)),
                        ((*first, "release", "let go of the first"), ("release", first))])
                    self.assertEqual(s.stack, n.base)
                    self.assertEqual(s.typed(), [])                       # no scroll at any point

    def test_the_quick_tap_inside_200_ms(self):
        """Modifier 2's own release clears every modifier and toggles Gyro. `walk` stops there. The simulator
        knows the other side is still held: its modifier comes back in the new mode within 50 ms, on the
        repeating entry of Base or Gyro, whichever way a removal treats an exposed command (A9)."""
        from tests.test_modifier_rocking import Names
        for label, layout, L, R, entry, n in self.cases():
            other = Names((n.l, n.r), not n.g)
            for let_go, held in ((L, n.r), (R, n.l)):
                with self.subTest(label, let_go=let_go):
                    steps = [((*L, entry, "hold L"), ("press", L)), ((*R, "chord", "press R"), ("press", R)),
                             ((*let_go, "release", "let go inside 200 ms"), ("release", let_go))]
                    waits = self.compare(layout, n, steps, exposed_fires=False)
                    self.assertEqual(waits.wait(50).stack, other.base + (other.mod(held),))
                    fires = Simulator(layout, start=n.base, exposed_fires=True)
                    fires.press(L).press(R).release(let_go).wait(50)
                    self.assertEqual(fires.stack, other.base + (other.mod(held),))

    def test_a_double_tap_a_used_bumper_and_the_cursor(self):
        from tests.test_modifier_rocking import A
        for label, layout, L, R, entry, n in self.cases():
            with self.subTest(label):
                s = self.compare(layout, n, [((*L, entry, "press L"), ("press", L)),
                                             ((*L, "release", "let go"), ("release", L)),
                                             ((*L, "Full_Press", "press again inside 150 ms"), ("press", L))])
                self.assertEqual(len(s.typed()), 1)                       # the scroll
                self.compare(layout, n, [((*L, entry, "press L"), ("press", L)),
                                         ((*A, "chord", "press A with L held"), ("press", A)),
                                         (None, ("release", A)),
                                         ((*L, "release", "let go of L"), ("release", L)),
                                         ((*L, entry, "press L again at once"), ("press", L))])
                self.compare(layout, n, [((*L, entry, "press L"), ("press", L)),
                                         ((*L, "chord", "hold L 300 ms"), ("wait", 300)),
                                         ((*L, "release", "let go of L"), ("release", L))])


if __name__ == "__main__":
    unittest.main()
