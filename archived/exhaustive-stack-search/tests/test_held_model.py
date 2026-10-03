"""The realistic (held-button) stack model: steam_layout.held_model."""
import json
from pathlib import Path
import unittest

from steam_layout.held_model import LOST, PRESS, RELEASE, TAP, TAP_HELD_LOST, TAP_LOST, TIMER, HeldModel, explore
from steam_layout.model import Layout
from test_audit_inheritance import EMPTY, act, add, build, release, remove

ROOT = Path(__file__).resolve().parents[1]
LB, RB = ("switch", "left_bumper"), ("switch", "right_bumper")


def chord(binding, button="1", **settings):
    return {"bindings": {"binding": binding}, "settings": {"chord_button": button, **settings}}


def guarded_layout():
    """Base: LB (chord on itself) adds Mod. Mod: A is guarded recovery; LB release exits; RB chord delayed."""
    return build({
        "Base": {"switch": ("switches", {"left_bumper": {"chord": chord(add("Mod"))}}),
                 "joystick": ("joystick_mouse", {"touch": act("key_press T, , ")}),
                 "right_joystick": ("joystick_mouse", {"touch": act("key_press T, , ")})},
        "Mod": {"switch": ("switches", {
                    "left_bumper": release([remove("Mod")]),
                    "button_escape": {"chord": chord(add("Late"), delay_start="200"),
                                      "Full_Press": {"bindings": {"binding": remove("Late")},
                                                     "settings": {"hold_repeats": "1", "interruptable": "0"}}}}),
                "button_diamond": ("four_buttons", {"button_a": {
                    "chord": chord(EMPTY),
                    "Full_Press": {"bindings": {"binding": remove("Mod")}, "settings": {"hold_repeats": "1"}}}})},
        "Late": {},
        "Win": {"switch": ("switches", {"always_on_action": {"Full_Press": {
            "bindings": {"binding": remove("Win")}, "settings": {"delay_start": "150"}}}})}})


class HeldRuleTests(unittest.TestCase):
    def setUp(self):
        self.model = HeldModel(Layout(guarded_layout()), missed=True)
        self.c = self.model.cid

    def step(self, state, control, phase):
        found = {nxt for nxt, (c, p) in self.model.successors(state) if c == control and p == phase}
        self.assertTrue(found, (control, phase))
        return found

    def names(self, state):
        return self.model.names_of(state[0])

    def test_press_then_release_and_nothing_fires_without_a_press(self):
        s = self.model.start()
        (held,) = self.step(s, self.c[LB], PRESS)
        self.assertEqual(self.names(held), ("Base", "Mod"))
        (back,) = self.step(held, self.c[LB], RELEASE)
        self.assertEqual((self.names(back), back[1], back[2]), (("Base",), frozenset(), False))
        self.assertFalse({n for n, (c, p) in self.model.successors(s) if c == self.c[LB] and p == RELEASE})

    def test_missed_release_keeps_the_stack_and_sets_the_flag(self):
        (held,) = self.step(self.model.start(), self.c[LB], PRESS)
        (lost,) = self.step(held, self.c[LB], LOST)
        self.assertEqual((self.names(lost), lost[1], lost[2]), (("Base", "Mod"), frozenset(), True))

    def test_missed_releases_are_off_by_default(self):
        model = HeldModel(Layout(guarded_layout()))
        (held,) = {n for n, (c, p) in model.successors(model.start()) if c == self.c[LB] and p == PRESS}
        phases = {p for _, (_, p) in model.successors(held)}
        self.assertIn(RELEASE, phases)
        self.assertFalse(phases & {LOST, TAP_LOST, TAP_HELD_LOST})
        self.assertFalse(any(m for _, _, m in explore(model)))

    def test_chords_only_fire_while_their_buttons_are_held(self):
        # In Mod with LB held, pressing A hits the empty guard chord, which blocks the recovery.
        # (A is tracked: its recovery repeats while it is held.)
        a = self.c[("button_diamond", "button_a")]
        (held,) = self.step(self.model.start(), self.c[LB], PRESS)
        self.assertEqual({self.names(n) for n in self.step(held, a, PRESS)}, {("Base", "Mod")})
        # After a missed LB release the guard is off, so A's recovery removes Mod.
        (lost,) = self.step(held, self.c[LB], LOST)
        self.assertIn(("Base",), {self.names(n) for n in self.step(lost, a, PRESS)})

    def test_delayed_chord_fires_on_hold_not_on_press(self):
        # Start is tracked (its delayed chord and repeating reset change layers): pressing it
        # doesn't reach the 200 ms chord; holding it does (the repeating reset may also run).
        from steam_layout.held_model import LATER
        (held,) = self.step(self.model.start(), self.c[LB], PRESS)
        start = self.c[("switch", "button_escape")]
        (pressed,) = self.step(held, start, PRESS)
        self.assertEqual(self.names(pressed), ("Base", "Mod"))
        self.assertIn(("Base", "Mod", "Late"), {self.names(n) for n in self.step(pressed, start, LATER)})

    def test_one_thumb_one_place(self):
        m = self.model
        ls, rs = m.cid[("joystick", "touch")], m.cid[("right_joystick", "touch")]
        a = m.cid[("button_diamond", "button_a")]
        self.assertTrue(m.valid(frozenset({ls, a})))
        self.assertFalse(m.valid(frozenset({rs, a})))

    def test_always_on_timer_can_fire_any_time(self):
        state = ((0, self.model.index["Win"]), frozenset(), False)
        self.assertIn(("Base",), {self.names(n) for n, (c, p) in self.model.successors(state) if p == TIMER})


def pad_layout():
    """Base: pad touch release adds Win; Win: north adds Scroll, the center (edge) clears Win,
    click holds Clicked; Scroll: A's delayed add and B's repeating remove; Mod chords on pad touch."""
    hold = "controller_action hold_layer {{Base::Clicked}} 0 0, , "
    return build({
        "Base": {"right_trackpad": ("dpad", {"touch": release([add("Win")]),
                                             "click": {"Soft_Press": {"bindings": {"binding": hold}}}}),
                 "button_diamond": ("four_buttons", {
                     "button_a": {"Full_Press": {"bindings": {"binding": add("Mod")}, "settings": {"delay_start": "200"}}},
                     "button_b": {"Full_Press": {"bindings": {"binding": remove("Mod")}, "settings": {"hold_repeats": "1"}}},
                     "button_x": act(add("Mod")),
                     "button_y": act("key_press Y, , ")})},
        "Win": {"right_trackpad": ("dpad", {"dpad_north": act(add("Scroll")), "edge": act(remove("Win"))})},
        "Scroll": {},
        "Clicked": {},
        "Mod": {"switch": ("switches", {"left_bumper": {"chord": chord(add("Scroll"), button="17")}})}})


class TrackedInputTests(unittest.TestCase):
    """Only inputs whose timing matters stay held; the rest are press-and-release."""

    def setUp(self):
        self.model = HeldModel(Layout(pad_layout()))
        self.c = self.model.cid

    def tracked(self, source, name):
        return self.model.owner[self.c[(source, name)]]

    def test_pad_chords_track_touch_not_every_pad_input(self):
        self.assertTrue(self.tracked("right_trackpad", "touch"))
        for name in ("dpad_north", "edge"):
            self.assertFalse(self.tracked("right_trackpad", name), name)

    def test_release_hold_layer_delayed_and_repeating_layer_commands_are_tracked(self):
        self.assertTrue(self.tracked("right_trackpad", "click"))       # hold_layer
        self.assertTrue(self.tracked("button_diamond", "button_a"))    # delayed add
        self.assertTrue(self.tracked("button_diamond", "button_b"))    # repeating remove
        self.assertFalse(self.tracked("button_diamond", "button_x"))   # plain add: press-and-release
        self.assertFalse(self.tracked("button_diamond", "button_y"))   # no layer command

    def test_pad_direction_fires_only_with_the_thumb_on_the_pad(self):
        m, touch = self.model, self.c[("right_trackpad", "touch")]
        north = self.c[("right_trackpad", "dpad_north")]
        win = ((0, m.index["Win"]), frozenset(), False)
        self.assertFalse({n for n, (c, _) in m.successors(win) if c == north})
        on_pad = ((0, m.index["Win"]), frozenset({touch}), False)
        self.assertIn(("Base", "Win", "Scroll"), {m.names_of(n[0]) for n, (c, p) in m.successors(on_pad)
                                                  if c == north and p == TAP})

    def test_releasing_the_button_removes_its_hold_layer(self):
        m, click, touch = self.model, self.c[("right_trackpad", "click")], self.c[("right_trackpad", "touch")]
        on_pad = ((0,), frozenset({touch}), False)
        (pressed,) = {n for n, (c, p) in m.successors(on_pad) if c == click and p == PRESS}
        self.assertEqual(m.names_of(pressed[0]), ("Base", "Clicked"))
        (released,) = {n for n, (c, p) in m.successors(pressed) if c == click and p == RELEASE}
        self.assertEqual(m.names_of(released[0]), ("Base",))


class NeptuneHeldTests(unittest.TestCase):
    def test_rocking_is_reachable_with_real_button_presses(self):
        model = HeldModel(Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text())))
        lb, rb = model.cid[LB], model.cid[RB]
        from steam_layout.held_model import LATER

        def only(state, control, phase, want):
            found = [n for n, (c, p) in model.successors(state) if c == control and p == phase
                     and model.names_of(n[0]) == want]
            self.assertTrue(found, (control, phase, want))
            return found[0]

        s = only(model.start(), lb, PRESS, ("Base", "L1: Modifier 0"))
        s = only(s, rb, PRESS, ("Base", "L1: Modifier 0", "L1: Tap Cover", "R1: Modifier 1", "R1: Tap Cover",
                               "L1!R1: Modifier 2"))
        s = only(s, rb, LATER, ("Base", "L1: Modifier 0", "L1: Tap Cover", "R1: Modifier 1", "R1: Tap Cover",
                               "L1!R1: Modifier 2", "L1&R1: Tap Cover"))
        s = only(s, lb, RELEASE, ("Base", "R1: Modifier 1", "R1: Tap Cover"))
        self.assertEqual(s[1], frozenset({rb}))


if __name__ == "__main__":
    unittest.main()
