"""Explicit geometry resolution and boundary sampling, not hardware emulation."""
from decimal import Decimal
import json
from pathlib import Path
import unittest

from steam_layout.model import Layout
from steam_layout.source_geometry import (RingRegion, SourceGeometry, UnresolvedGeometry,
                                          boundary_representatives)
from test_audit_inheritance import EMPTY, act, build


ROOT = Path(__file__).resolve().parents[1]


class SourceGeometryTests(unittest.TestCase):
    def fixture(self):
        layout = Layout(build({
            "Base": {"right_joystick": ("joystick_mouse", {"edge": act(EMPTY)})},
            "Lower": {"right_joystick": ("joystick_mouse", {})},
            "Cover": {"right_joystick": ("joystick_mouse", {})},
            "Mode": {"right_joystick": ("dpad", {})},
            "Disabled": {"right_joystick": ("disabled", {})},
        }, modeshift={"90": ("right_joystick", "dpad", {"edge": act(EMPTY)})}))
        settings = {
            "Base": {"edge_binding_radius": "32767", "deadzone_inner_radius": "3280",
                     "deadzone_outer_radius": "32000", "sensitivity": "100"},
            "Lower": {"edge_binding_radius": "7209", "edge_binding_invert": "0"},
            "Cover": {"sensitivity": "80"},
            "Mode": {"deadzone": "13276"},
        }
        for title, values in settings.items():
            layout.active(title)["right_joystick"]["settings"] = values
        layout.groups["90"]["settings"] = {"edge_binding_radius": "21000"}
        return SourceGeometry(layout)

    def test_sensitivity_cover_inherits_lower_geometry_with_provenance(self):
        resolved = self.fixture().resolve(("Base", "Lower", "Cover"), "right_joystick")
        values, owners = dict(resolved.settings), dict(resolved.owners)
        self.assertEqual(resolved.mode, "joystick_mouse")
        self.assertEqual(values["edge_binding_radius"], "7209")
        self.assertEqual(values["deadzone_inner_radius"], "3280")
        self.assertEqual(values["sensitivity"], "80")
        self.assertEqual(owners["edge_binding_radius"], "Lower")
        self.assertEqual(owners["deadzone_inner_radius"], "Base")
        self.assertEqual(owners["sensitivity"], "Cover")

    def test_removing_lower_layer_exposes_base_setting(self):
        geometry = self.fixture()
        self.assertEqual(dict(geometry.resolve((0, 1, 2), "right_joystick").settings)
                         ["edge_binding_radius"], "7209")
        self.assertEqual(dict(geometry.resolve((0, 2), "right_joystick").settings)
                         ["edge_binding_radius"], "32767")

    def test_missing_exported_default_is_required_and_never_overrides_explicit_value(self):
        geometry = self.fixture()
        base = geometry.resolve((0,), "right_joystick")
        with self.assertRaisesRegex(UnresolvedGeometry, "edge_binding_invert"):
            base.ring()
        self.assertFalse(base.ring(defaults={"edge_binding_invert": "0"}).contains(1))
        lower = geometry.resolve((0, 1), "right_joystick")
        self.assertFalse(lower.ring(defaults={"edge_binding_invert": "1"}).inverted)

    def test_equality_is_not_guessed_including_the_maximum_endpoint(self):
        ring = RingRegion(Decimal(32767), False)
        self.assertFalse(ring.contains(1))
        with self.assertRaisesRegex(UnresolvedGeometry, "equality"):
            ring.contains(32767)
        self.assertTrue(ring.contains(32767, equality_outside=True))
        self.assertFalse(ring.contains(32767, equality_outside=False))

    def test_inversion_is_complement_and_deadzone_does_not_silently_clip_it(self):
        ring = RingRegion(Decimal(6553), True)
        self.assertTrue(ring.contains(0))
        self.assertTrue(ring.contains(1))
        self.assertFalse(ring.contains(32767))
        self.assertFalse(ring.contains(6553, equality_outside=True))
        self.assertTrue(ring.contains(6553, equality_outside=False))

    def test_mode_changes_recorded_for_caller_coordinate_policy(self):
        resolved = self.fixture().resolve((0, 1, 3), "right_joystick")
        self.assertEqual(resolved.mode, "dpad")
        self.assertEqual(resolved.mode_changes[-1], ("Mode", "joystick_mouse", "dpad"))
        self.assertEqual(dict(resolved.settings)["deadzone"], "13276")
        self.assertEqual(dict(resolved.settings)["edge_binding_radius"], "7209")

    def test_disabled_source_cannot_silently_provide_an_active_ring(self):
        disabled = self.fixture().resolve((0, 1, 4), "right_joystick")
        with self.assertRaisesRegex(UnresolvedGeometry, "disabled"):
            disabled.ring()

    def test_shift_inheritance_requires_explicit_choice(self):
        geometry = self.fixture()
        with self.assertRaisesRegex(UnresolvedGeometry, "inheritance policy"):
            geometry.resolve((0, 1), "right_joystick", shift_group="90")
        inherited = geometry.resolve((0, 1), "right_joystick", shift_group="90",
                                     inherit_shift_settings=True)
        isolated = geometry.resolve((0, 1), "right_joystick", shift_group="90",
                                    inherit_shift_settings=False)
        self.assertEqual(inherited.ring().radius, Decimal(21000))
        self.assertEqual(inherited.shift_policy, "inherit-explicit-layer-settings")
        with self.assertRaisesRegex(UnresolvedGeometry, "edge_binding_invert"):
            isolated.ring()

    def test_candidate_boundaries_include_layer_and_shift_settings(self):
        geometry = self.fixture()
        self.assertEqual(geometry.candidate_boundaries("right_joystick"),
                         tuple(map(Decimal, (0, 3280, 7209, 13276, 21000, 32000, 32767))))

    def test_shift_command_association_is_enough_without_a_preset_declaration(self):
        geometry = self.fixture()
        base = geometry.layout.presets["Base"]
        del base["group_source_bindings"]["90"]
        geometry.layout.groups["1"]["inputs"]["click"] = {
            "activators": act("mode_shift right_joystick 90, , ")}
        self.assertIn(Decimal(21000), geometry.candidate_boundaries("right_joystick"))

    def test_samples_distinguish_both_strict_and_inclusive_threshold_predicates(self):
        points = boundary_representatives((10, 20))
        self.assertEqual(points, tuple(map(Decimal, (0, 5, 10, 15, 20, "16393.5", 32767))))
        for threshold in (Decimal(10), Decimal(20)):
            self.assertTrue(any(value < threshold for value in points))
            self.assertIn(threshold, points)
            self.assertTrue(any(value > threshold for value in points))

    def test_samples_preserve_arbitrary_decimal_precision(self):
        lower = Decimal("10.00000000000000000000000000001")
        upper = Decimal("10.00000000000000000000000000002")
        samples = boundary_representatives((lower, upper))
        self.assertTrue(any(lower < sample < upper for sample in samples))

    def test_current_layout_base_right_stick_geometry_and_modifier_overlay(self):
        layout = Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text()))
        geometry = SourceGeometry(layout)
        base = geometry.resolve(("Base",), "right_joystick")
        self.assertEqual(dict(base.settings)["edge_binding_radius"], "32767")
        self.assertEqual(dict(base.settings)["deadzone_inner_radius"], "3280")
        with self.assertRaisesRegex(UnresolvedGeometry, "edge_binding_invert"):
            base.ring()
        self.assertFalse(base.ring(defaults={"edge_binding_invert": "0"}).contains(1))
        cover = geometry.resolve(("Base", "L1: Modifier 0", "L1: Temp Cursor Gyro"),
                                 "right_joystick")
        self.assertEqual(cover.ring().radius, Decimal(7209))
        self.assertEqual(dict(cover.owners)["edge_binding_radius"], "L1: Modifier 0")


if __name__ == "__main__":
    unittest.main()
