"""The Cleanup audit: what a cleanup function and a release may remove.

Tiny layouts, one rule per test, then the frozen 90.10 snapshots. The rules are in
findings/2026-10-02-cleanup-boundaries/README.md; the plan is plans/2026-10-02-cleanup-audit.md.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.cleanups import *

class HiddenExitSnapshotTests(unittest.TestCase):
    """The frozen 90.13 snapshots: the prototype's result of 2026-10-02, plus two gaps the check missed at first.

    The Fallback Hold over the menu second-press layers needed landings (2026-10-03); it was in the layouts
    from 90.11 to 90.14 and is fixed in 90.15. The menu Tap Cover over a pad layer needed every stack of the
    walk with extra presses to be tested (2026-10-04); it has been in the layouts since 90.10."""
    FALLBACK_HOLD = {("Steering | LS: Fallback Hold", lower) for lower in (
        "Menu Left: Escape", "Menu Left: Double Tap Cover", "Menu Right: Tab", "Menu Right: Double Tap Cover")}
    TAP_COVER = {(upper, lower) for upper in ("Menu Left: Entry Point", "Menu Right: Entry Point")
                 for lower in ("RST: Entry Point", "RST: Tap Cover", "RST: Temporary Gyro")}

    @classmethod
    def setUpClass(cls):
        cls.data = {v: json.loads((ROOT / f"versions/neptune/90.13/single-set-{v}_hold-gyro_90.13.json")
                                  .read_text(encoding="utf-8")) for v in ("default", "alternative")}

    def test_the_only_findings_outside_the_touchpad_exception_are_the_fallback_hold_landings(self):
        for variant, data in self.data.items():
            with self.subTest(variant):
                report = audit(data, {"cleanups": {"touchpad_exits": "set aside"}})
                hidden = [f for f in report["findings"] if f["check"] == "hidden exit"]
                self.assertEqual({(f["layer"], f["target"]) for f in hidden}, self.FALLBACK_HOLD | self.TAP_COVER)
                for finding in hidden:                     # the stack, and the binding that put the upper layer on it
                    if (finding["layer"], finding["target"]) in self.FALLBACK_HOLD:
                        self.assertTrue(finding["example"].startswith("Base > Steering > Menu "), finding["example"])
                        self.assertIn("Steering joystick/dpad_", finding["path"][-1], finding["path"])
                    else:
                        self.assertTrue(finding["example"].endswith("Menu Buttons: Tap Cover"), finding["example"])
                self.assertEqual(len([e for e in report["excepted"] if e["on_keeper"]]), 68)
                self.assertEqual(len([e for e in report["excepted"] if not e["on_keeper"]]), 26)
                self.assertEqual({(i["layer"], i["target"]) for i in report["information"]["hidden exit"]},
                                 {("Menu Buttons: Tap Cover", "Menu Buttons: Left Stick Guard"),
                                  ("Menu Buttons: Tap Cover", "Menu Buttons: Right Stick Guard")})

    def test_the_touchpad_pairs_fail_without_the_exception(self):
        report = audit(self.data["default"], {})
        self.assertEqual(len([f for f in report["findings"] if f["check"] == "hidden exit"]), 68 + 4 + 6)

    def test_the_working_layouts_have_no_hidden_exit(self):
        for variant in ("default", "alternative"):
            data = json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text(encoding="utf-8"))
            report = audit(data, {"cleanups": {"touchpad_exits": "set aside"}})
            with self.subTest(variant):
                self.assertEqual(sorted(f"{f['layer']} over {f['target']}" for f in report["findings"]
                                        if f["check"] == "hidden exit"), [])


class SteeringDirectionRecoveryBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.convert_runtime_ids import generate_lookup, ids_to_titles
        from tests.scenario import frozen_layout_data
        path = ROOT / 'findings/2026-10-09-steering-entry-and-feedback/modifier_recovery.py'
        spec = importlib.util.spec_from_file_location('direction_recovery', path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.layouts = {}
        for variant in ('default', 'alternative'):
            baseline = frozen_layout_data(variant, '90.42')
            readable, _ = ids_to_titles(json.dumps(baseline), generate_lookup(baseline))
            before = json.loads(readable.replace('Steering | LS: Fallback Guard', 'Steering | LS: Entry Guard'))
            after = copy.deepcopy(before)
            report = cls.module.apply(after, variant)
            cls.layouts[variant] = before, after, report

    def test_owner_direction_adds_keep_outputs_and_timing_and_gain_owner_guard(self):
        for variant, (before, after, report) in self.layouts.items():
            old, new = Layout(before), Layout(after)
            self.assertEqual(len(report['owner_direction_entries']), 4)
            for row in report['owner_direction_entries']:
                with self.subTest(variant=variant, owner=row['layer'], direction=row['input']):
                    previous = old.active(row['layer'])['joystick']['inputs']
                    acts = new.active(row['layer'])['joystick']['inputs'][row['input']]['activators']
                    self.assertEqual(list(acts), ['Full_Press', 'chord'])
                    self.assertEqual(acts['Full_Press'], previous['edge']['activators']['Full_Press'])
                    add = copy.deepcopy(acts['chord'])
                    self.assertEqual(add['settings'].pop('gyro_ratchet_button_mask'), row['owner_mask'])
                    self.assertEqual(add['settings'].pop('gyro_ratchet_button_requireany_or_all'), '0')
                    self.assertEqual(add, previous[row['input']]['activators']['Full_Press'])

    def test_upper_modifiers_keep_hold_delays_and_resets_while_carrying_recovery(self):
        for variant, (before, after, report) in self.layouts.items():
            old, new = Layout(before), Layout(after)
            self.assertEqual(len(report['upper_direction_recovery']), 8)
            for title, primary, opposite in (('Steering | LS Up: Modifier 1', 'dpad_north', 'dpad_south'),
                                             ('Steering | LS Down: Modifier 0', 'dpad_south', 'dpad_north')):
                with self.subTest(variant=variant, layer=title):
                    previous = old.active(title)['joystick']['inputs']
                    inputs = new.active(title)['joystick']['inputs']
                    acts = inputs[primary]['activators']
                    self.assertEqual(acts['chord'], previous[primary]['activators']['chord'])
                    self.assertEqual(acts['Full_Press'], [previous['edge']['activators']['Full_Press'],
                                                         previous[primary]['activators']['Full_Press']])
                    cancellation = copy.deepcopy(inputs[opposite]['activators']['Full_Press'])
                    self.assertEqual(cancellation['settings'].pop('hold_repeats'), '1')
                    self.assertEqual(cancellation, previous[opposite]['activators']['Full_Press'])

    def test_repeat_scroll_covers_keep_wheel_timing_and_release(self):
        title = 'Steering | LS: Double Tap Cover'
        for variant, (before, after, _) in self.layouts.items():
            old, new = Layout(before), Layout(after)
            for direction in ('dpad_north', 'dpad_south'):
                with self.subTest(variant=variant, direction=direction):
                    previous = old.active(title)['joystick']['inputs'][direction]['activators']
                    acts = new.active(title)['joystick']['inputs'][direction]['activators']
                    self.assertEqual(acts['release'], previous['release'])
                    wheel = copy.deepcopy(acts['chord'])
                    self.assertEqual(wheel['settings'].pop('gyro_ratchet_button_mask'),
                                     '50331648' if variant == 'alternative' else '12')
                    self.assertEqual(wheel['settings'].pop('gyro_ratchet_button_requireany_or_all'), '0')
                    self.assertEqual(wheel, previous['Full_Press'])

    def test_guarded_directions_fit_command_budget_and_reapplying_is_idempotent(self):
        from tools.audit_command_budget import audit_layout
        for variant, (_, after, _) in self.layouts.items():
            with self.subTest(variant=variant):
                self.assertFalse(audit_layout(after)['violations'])
                reapplied = copy.deepcopy(after)
                self.module.apply(reapplied, variant)
                self.assertEqual(reapplied, after)


class SnapshotTests(unittest.TestCase):
    """The frozen 90.10 snapshots: the audit reproduces what was measured on 2026-10-02."""

    @classmethod
    def setUpClass(cls):
        cls.reports, cls.cleanups = {}, {}
        for variant in ("default", "alternative"):
            path = ROOT / f"versions/neptune/90.10/single-set-{variant}_hold-gyro_90.10.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            cls.cleanups[variant] = Cleanups(Layout(data))
            cls.reports[variant] = audit(data, {}, extras=None)       # the six list checks; 90.10 predates R136

    def pairs(self, variant, check):
        return {(f["layer"], f["target"]) for f in self.reports[variant]["findings"] if f["check"] == check}

    def test_the_stateful_layers_are_gyro_and_steering(self):
        for variant, c in self.cleanups.items():
            self.assertEqual({t for t in c.layers if c.keeper(t)[0] == "mode"}, {"Gyro", "Steering"}, variant)

    def test_keepers_of_named_layers(self):
        c = self.cleanups["default"]
        for title, expected in {"L1: Modifier 0": {"LB"}, "L1!R1: Modifier 2": {"LB", "RB"}, "L1: Tap Cover": {"LB"},
                                "L1&R1: Tap Cover": {"LB", "RB"}, "Menu Left: Fn Layer": {"Select"},
                                "Menu Left: Entry Point": {"Select"}, "Steering | R1: W Key": {"RB"},
                                "Menu Buttons: Left Stick Guard": {"Select", "Start"}}.items():
            self.assertEqual(c.keeper(title), ("button", frozenset(expected)), title)
        self.assertEqual(c.keeper("L1: Double Tap")[0], "timer")
        self.assertEqual(c.keeper("LST: Entry Point")[0], "thumb")
        self.assertEqual(c.keeper("Steering | LS Down: Modifier 0")[0], "inside")
        alt = self.cleanups["alternative"]
        self.assertEqual(alt.keeper("L2: Modifier 0"), ("button", frozenset({"LT"})))
        self.assertEqual(alt.keeper("L2!R2: Modifier 2"), ("button", frozenset({"LT", "RT"})))

    def test_only_the_cursor_edges_leave_the_layer_below(self):
        self.assertEqual(self.pairs("default", "left below"),
                         {("L1: Temp Cursor Gyro", "L1: Modifier 0"), ("L1: Temp Cursor Gyro", "Gyro | L1: Modifier 0"),
                          ("R1: Temp Cursor Gyro", "R1: Modifier 1"), ("R1: Temp Cursor Gyro", "Gyro | R1: Modifier 1")})
        self.assertEqual(self.pairs("default", "left above"), set())

    def test_modifier_2_hides_the_touch_cleanup(self):
        hiding = {layer for layer, _ in self.pairs("default", "hidden cleanup")}
        self.assertEqual(hiding, {"L1!R1: Modifier 2", "R1!L1: Modifier 2",
                                  "Gyro | L1!R1: Modifier 2", "Gyro | R1!L1: Modifier 2"})
        inputs = {i for f in self.reports["default"]["findings"] if f["check"] == "hidden cleanup" for i in f["inputs"]}
        self.assertEqual(inputs, {"LSt", "RSt"})

    def test_only_steering_removes_outside_a_guard(self):
        outside = self.pairs("default", "outside the guard")
        self.assertTrue(all(layer.startswith("Steering | ") for layer, _ in outside))
        windows = {"Steering | LS Up: Double Tap", "Steering | LS Down: Double Tap"}
        self.assertEqual(len({layer for layer, target in outside if target in windows}), 6)
        # The other bumper's layers: a driver's cleanup, guarded by its own bumper, lists the
        # Modifier 2 and the Tap Cover that the second bumper keeps.
        self.assertEqual({pair for pair in outside if pair[1] not in windows},
                         {("Steering | R1: W Key", "Steering | R1!L1: Modifier 2"), ("Steering | R1: W Key", "L1: Tap Cover"),
                          ("Steering | L1: S Key", "Steering | L1!R1: Modifier 2"), ("Steering | L1: S Key", "R1: Tap Cover"),
                          ("Steering | R1!L1: Modifier 2", "L1: Tap Cover"), ("Steering | L1!R1: Modifier 2", "R1: Tap Cover")})

    def test_steering_modifier_2_guards_its_touches_differently(self):
        self.assertEqual({layer for layer, _ in self.pairs("default", "guard mismatch")},
                         {"Steering | R1!L1: Modifier 2", "Steering | L1!R1: Modifier 2"})

    def test_the_twin_is_never_there(self):
        never = self.pairs("default", "never there")
        self.assertIn(("L1: Modifier 0", "Gyro | L1: Modifier 0"), never)
        self.assertIn(("Gyro | L1: Modifier 0", "L1: Modifier 0"), never)
        self.assertIn(("Steering | R1: W Key", "Steering | L1: S Key"), never)
        self.assertNotIn(("L1: Tap Cover", "Gyro | L1: Modifier 0"), never)     # a shared layer keeps each parent

    def test_the_hold_layer_layers_are_left_out(self):
        self.assertEqual(self.reports["default"]["omitted"], ["LTP: Arrow Keys", "RTP: Mouse Buttons"])
        self.assertNotIn(("RTP: Circular Scroll", "RTP: Mouse Buttons"), self.pairs("default", "never there"))

    def test_the_variants_agree(self):
        count = lambda v: sorted((f["check"], len(f["inputs"])) for f in self.reports[v]["findings"])  # noqa: E731
        self.assertEqual(count("default"), count("alternative"))


class FixedSnapshotTests(unittest.TestCase):
    """The fix on the frozen 90.10 snapshots: the six list checks come out clean, within the entry budget.

    The fix doesn't resolve hidden exits (R136), and 90.10 predates that rule."""

    def test_the_audit_is_clean_after_the_fix(self):
        for variant in ("default", "alternative"):
            data = json.loads((ROOT / f"versions/neptune/90.10/single-set-{variant}_hold-gyro_90.10.json").read_text())
            report = cleanup_lists.fix(data, {})
            with self.subTest(variant):
                self.assertEqual(audit(data, {}, extras=None)["findings"], [])
                self.assertEqual(report["remaining"], 0)
                layout = Layout(data)
                for title in layout.presets:
                    for source, group in layout.active(title).items():
                        for name, value in group.get("inputs", {}).items():
                            count = sum(1 for _ in entries(value.get("activators", {})))
                            self.assertLessEqual(count, 4, f"{title} {source}/{name}")


if __name__ == "__main__":
    unittest.main()
