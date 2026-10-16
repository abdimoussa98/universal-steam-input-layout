"""Inheritance/blocking audit (Layer Definition of Done, section 8).

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.audit_inheritance import *

class NeptuneLayoutTests(unittest.TestCase):
    """The committed traced stacks cover every Always On layer with every route decided."""

    @classmethod
    def setUpClass(cls):
        cls._window_observations = {}

    @classmethod
    def tearDownClass(cls):
        cls._window_observations.clear()

    @classmethod
    def working_window_observation(cls, variant):
        """Reuse only this class's exact live source/configuration and immutable assertion views."""
        source = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
        configuration = ROOT / "steam_layout" / "traced_stacks.json"
        raw, config_raw = source.read_bytes(), configuration.read_bytes()
        key = (str(source), raw, str(configuration), config_raw)
        previous = cls._window_observations.get(variant)
        if previous is None or previous[0] != key:
            data = json.loads(raw)
            report = audit(data, json.loads(config_raw))
            observation = window_observation(report, always_on_layers(Layout(data)))
            cls._window_observations[variant] = (key, observation)
        return cls._window_observations[variant][1]

    def test_working_layouts_have_no_undecided_routes(self):
        for variant in ("default", "alternative"):
            with self.subTest(variant=variant):
                observation = self.working_window_observation(variant)
                self.assertEqual(observation.variant, variant)
                # R140 covers every layer with an Always On action: each one is audited, whatever their number.
                self.assertEqual(observation.targets, observation.expected_windows)
                self.assertEqual(observation.undecided, ())
                self.assertTrue(observation.ok)

    def test_every_window_is_checked_on_chain_stacks(self):
        for variant in ("default", "alternative"):
            with self.subTest(variant=variant):
                observation = self.working_window_observation(variant)
                self.assertEqual(observation.without_chain_stacks, ())
                self.assertTrue(observation.ok)

    def test_a_steering_window_is_checked_with_no_config(self):
        # Seven inputs from Base: the old depth-5 search never reached it.
        title = "Steering | LS Up: Double Tap"
        cfg = {"targets": {title: {}}}
        data = json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text())
        row = audit(data, cfg)["targets"][title]
        self.assertTrue(row["checked"])
        self.assertIn(("Base", "Steering", "Steering | R1: W Key"),
                      {tuple(b["stack"]) for b in row["blocked"]} | {tuple(r["stack"]) for r in row["routes"]})

    def test_the_window_audit_stays_faster_than_the_old_search(self):
        # Plan step 3b: mid-chain arrivals must not make the audit slow. The old depth-5 search took 3.3 s.
        # The limit was 1 s until 90.14. The pad click layers were out of the chains while `hold_layer` added
        # them; with `add_layer` they are bystanders under every window, and the stacks went from 5,092 to
        # 10,426 (0.85 s to about 1.9 s).
        # The limit was 3 s until 90.34. The layout kept growing: 18,366 stacks and about 2.9 s on 90.34, 18,502
        # and about 3.2 s on 90.35, where the fallback guard stands in Steering's place under the windows. The
        # old search's 3.3 s was measured on the 69 layers of 90.9, so the name no longer compares like with
        # like; what this still guards is that the audit doesn't blow up.
        cfg = json.loads((ROOT / "steam_layout" / "traced_stacks.json").read_text())
        data = json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text())
        started = time.perf_counter()
        audit(data, cfg)
        self.assertLess(time.perf_counter() - started, 5.0)

    def test_removing_a_window_block_is_caught(self):
        cfg = json.loads((ROOT / "steam_layout" / "traced_stacks.json").read_text())
        data = json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text())
        cm = data["controller_mappings"]
        key = next(k for k, v in cm["action_layers"].items() if v["title"] == "Menu Left: Double Tap")
        preset = next(p for p in cm["preset"] if p["name"] == key)
        gid = next(g for g, s in preset["group_source_bindings"].items() if s == "right_joystick active")
        del next(g for g in cm["group"] if g["id"] == gid)["inputs"]["edge"]
        report = audit(data, cfg)
        self.assertFalse(report["ok"])
        self.assertIn(("right_joystick", "edge", "open"),
                      {(r["source"], r["input"], r["status"])
                       for r in report["targets"]["Menu Left: Double Tap"]["routes"]})


if __name__ == "__main__":
    unittest.main()
