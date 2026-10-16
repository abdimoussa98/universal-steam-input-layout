"""The controller registry (steam_layout/controllers.py): directories, Steam names and file names.

Fixture responsibility: contracts/shared. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.controllers import *

class RegistryTests(unittest.TestCase):
    """Current registry contracts on all six controller/variant files; no conversion is reused."""
    @classmethod
    def setUpClass(cls):
        cls.data = {path: load_json(path) for path in controllers.working_layouts()}

    def test_ibex_is_the_base_and_comes_first(self):                                        # R177
        self.assertEqual([c.name for c in controllers.CONTROLLERS], ["ibex", "neptune", "dse"])
        self.assertIs(controllers.BASE, controllers.get("ibex"))
        self.assertEqual([c.name for c in controllers.CONTROLLERS if c.base], ["ibex"])
        self.assertEqual(controllers.BASE.controller_type, "controller_triton")

    def test_every_controller_has_its_directory(self):
        for controller in controllers.CONTROLLERS:
            with self.subTest(controller.name):
                self.assertTrue(controller.directory.is_dir())
                self.assertEqual(controller.directory, ROOT / controller.name)
                self.assertEqual(controller.versions, ROOT / "versions" / controller.name)

    def test_new_stems_start_with_the_controller(self):
        for controller in controllers.CONTROLLERS:
            for variant in controllers.VARIANTS:
                with self.subTest(controller.name, variant=variant):
                    stem = controller.stem(variant)
                    expected = "" if controller is controllers.NEPTUNE else controller.name + "_"
                    self.assertEqual(stem, f"{expected}single-set-{variant}_hold-gyro")
        stems = [c.stem(v) for c in controllers.CONTROLLERS for v in controllers.VARIANTS]
        self.assertEqual(len(stems), len(set(stems)))           # no two controllers' files can overwrite each other

    def test_every_working_layout_is_named_and_headed_for_its_controller(self):
        for controller in controllers.CONTROLLERS:
            names = sorted(path.name for path in controller.directory.glob("*_latest.json"))
            self.assertEqual(names, sorted(path.name for path in controller.working()))
            for path in controller.working():
                variant = controller.variant_of(path)
                cm = self.data[path]["controller_mappings"]
                with self.subTest(path.name):
                    self.assertTrue(path.with_suffix(".vdf").exists())
                    self.assertIs(controllers.for_path(path), controller)
                    self.assertIs(controllers.for_type(cm["controller_type"]), controller)
                    self.assertEqual((cm["controller_type"], cm["controller_caps"], cm["url"], cm["description"]),
                                     (controller.controller_type, controller.controller_caps,
                                      controller.urls[variant], controller.descriptions[variant]))

    def test_a_file_is_placed_by_its_directory_or_its_name(self):
        self.assertIs(controllers.for_name("dse_single-set-default_hold-gyro_latest.json"), controllers.DSE)
        self.assertIs(controllers.for_name("ibex_single-set-alternative_hold-gyro_1.0.vdf"), controllers.IBEX)
        self.assertIs(controllers.for_name("single-set-default_hold-gyro_90.74.json"), controllers.NEPTUNE)
        self.assertIs(controllers.for_path(ROOT / "versions/dse/1.0/dse_single-set-default_hold-gyro_1.0.json"),
                      controllers.DSE)
        self.assertIs(controllers.for_path(ROOT / "ibex/anything.json"), controllers.IBEX)
        self.assertIsNone(controllers.for_type("controller_xboxone"))
        with self.assertRaises(ValueError):
            controllers.get("deck")

    def test_the_edge_lacks_stick_touch_and_the_right_pad(self):                          # R178, R182, R183
        dse = controllers.DSE
        for source, name in (("joystick", "touch"), ("right_joystick", "touch"), ("right_trackpad", "click")):
            with self.subTest(source=source, input=name):
                self.assertTrue(dse.lacks(source, name))
                self.assertFalse(controllers.IBEX.lacks(source, name))
                self.assertFalse(controllers.NEPTUNE.lacks(source, name))
        self.assertFalse(dse.lacks("joystick", "click"))
        self.assertFalse(dse.lacks("left_trackpad", "click"))
        for switch in ("left_trackpad_touch", "right_trackpad_touch"):      # the touchpad's two halves (A76)
            self.assertFalse(dse.lacks("switch", switch))

    def test_gyro_styles(self):                                                                  # R177, R179, R180
        self.assertEqual({c.name: controllers.GYRO_STYLES[c.gyro_style] for c in controllers.CONTROLLERS},
                         {"ibex": "Player Space", "neptune": "Yaw + Roll", "dse": "Player Space"})

    def test_every_gyro_to_mouse_group_states_its_controllers_style(self):                 # R177, R179, R180
        for controller in controllers.with_layouts():
            for path in controller.working():
                groups = [g for g in self.data[path]["controller_mappings"]["group"]
                          if g["mode"] == "gyro_to_mouse"]
                with self.subTest(path.name):
                    self.assertTrue(groups)
                    self.assertEqual({g["settings"].get("gyro_to_2d_conversion_style") for g in groups},
                                     {str(controller.gyro_style)})


class VersionTests(unittest.TestCase):


    def test_a_working_layouts_snapshots_are_its_controllers(self):
        for controller in controllers.with_layouts():
            for path in controller.working():
                with self.subTest(path.name):
                    newest = changes.newest_snapshot(path.name)
                    self.assertEqual(newest.parent.parent, controller.versions)
                    self.assertEqual(changes.baseline_for(path), newest)


if __name__ == "__main__":
    unittest.main()
