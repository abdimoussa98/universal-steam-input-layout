"""Conversions (steam_layout/convert.py, tools/convert.py): Ibex is the base layout, and Neptune's and the DualSense
Edge's layouts are made from it by their rules (R177 to R185, Layer Definition of Done section 12).

Each rule has a test on a small layout; the checks C1, C2, C3 and C5 of the plan run on the real ones
(plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4). The Edge's scenarios are in
tests/scenarios/dse/test_scenarios_dse_1_0.py.

Fixture responsibility: integration/convert. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.convert import *

class ConversionTests(unittest.TestCase):
    """C1 independently converts current Neptune/DSE from each named Ibex release.

    Both variants are checked. C2 audits current Ibex/DSE through the real
    CLI in a fresh process. Converter and CLI results are not shared.
    """

    def test_c1_each_conversion_is_what_tools_convert_makes_from_its_ibex_release(self):  # R177
        checked = 0
        for controller in controllers.with_layouts():
            if controller.base:
                continue
            version = release.working_version(controller)
            if controller.built_until and controllers.version_key(version) <= controllers.version_key(
                    controller.built_until):
                continue
            base = release.base_release(release.changelog_section(controller.name, version))
            with self.subTest(controller.name):
                self.assertIsNotNone(base, f"CHANGELOG.md: {controller.name} {version} names no Ibex release")
                for variant in controllers.VARIANTS:
                    source = load_json(controllers.IBEX.snapshot(variant, base))
                    made, _ = convert.convert(source, controller.name, variant, version)
                    working = load_json(controller.working_json(variant))
                    self.assertEqual(made, working, f"{controller.working_json(variant).name} was edited by hand")
                    checked += 1
        self.assertGreaterEqual(checked, 4)

    def test_c2_every_layout_passes_the_build_audit(self):                                # R150, R178 (g)
        layouts = [str(path) for c in (controllers.IBEX, controllers.DSE) for path in c.working()]
        result = subprocess.run([sys.executable, "-m", "tools.audit_build", *layouts], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)






if __name__ == "__main__":
    unittest.main()
