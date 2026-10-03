"""The cover check on backward chains (steam_layout/covers.py).

Small fixtures first, then both 90.9 layouts against the cover check it
replaces, which ran on the family walk (steam_layout/flow_covers.py).
"""
import json
from pathlib import Path
import unittest

from steam_layout import flow_covers
from steam_layout.chains import Chains
from steam_layout.covers import check_cover, family_view
from steam_layout.flow_paths import FlowWalker, families
from steam_layout.model import Layout, map_title
from tests.test_flow_inheritance import EMPTY, add, entry, fixture, inp, rem, switches

ROOT = Path(__file__).resolve().parents[1]
FROZEN_RULES = ROOT / "tests/data/flow_families_90.9.json"   # the family rules as they were at 90.9


def frozen(variant):
    return Layout(json.loads((ROOT / f"versions/neptune/90.9/single-set-{variant}_hold-gyro_90.9.json").read_text()))


class CoverFixtureTests(unittest.TestCase):
    def layout(self):
        return fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"switch": {"mode": "switches", "inputs": {
                "left_bumper": inp(release=entry(rem("A"), add("W")))}},
                "button_diamond": {"mode": "four_buttons", "inputs": {
                    "button_a": inp(chord=entry(add("Cover"), chord_button=1)),
                    "button_b": inp(chord=entry(add("Mid"), chord_button=1))}}},
            "Mid": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_y": inp(Full_Press=entry("key_press Y, , "))}}},
            # The cover only changes the release: it removes the owner, then itself.
            "Cover": switches(left_bumper=inp(release=entry(rem("A"), rem("Cover")))),
            "W": switches(always_on_action=inp(Full_Press=entry(rem("W"), delay_start=150)))})

    def check(self, layout, allowed=None):
        return check_cover(layout, family_view(layout), "Cover", allowed)

    def test_clean_cover_and_owner_is_the_layer_below(self):
        report = self.check(self.layout())
        self.assertEqual(report["owners"], ["A", "Mid"])
        self.assertEqual(report["findings"], [])

    def test_cover_that_outlives_its_owner(self):
        layout = self.layout()
        # Now the owner's release no longer removes the cover.
        layout.active("Cover")["switch"]["inputs"]["left_bumper"] = inp(release=entry(rem("A")))
        report = self.check(layout)
        finding = next(f for f in report["findings"] if f["check"] == "outlives owners")
        self.assertEqual(finding["stack"], ["Base", "Cover"])
        self.assertIn("settle: Cover switch/left_bumper release#0: -A", finding["path"])
        allowed = self.check(layout, {"outlives owners": "by design"})
        self.assertEqual({f["allowed"] for f in allowed["findings"] if f["check"] == "outlives owners"}, {"by design"})

    def test_layers_above_the_cover_are_listed(self):
        layout = self.layout()
        layout.active("Mid")["switch"] = {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("Mid")))},
                                          "settings": {}}
        # Mid can sit above the cover and takes its release without removing the cover.
        self.assertEqual(self.check(layout)["above"].get("Mid"), {"switch/left_bumper": False})

    def test_owner_above_the_cover(self):
        layout = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("A")))}},
                  "button_diamond": {"mode": "four_buttons", "inputs": {
                      "button_a": inp(chord=entry(add("Cover"), chord_button=1)),
                      "button_b": inp(chord=entry(rem("A"), add("A"), chord_button=1))}}},
            "Cover": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_x": inp(Full_Press=entry(EMPTY))}}}})
        self.assertIn("below its owner", {f["check"] for f in self.check(layout)["findings"]})

    def test_an_input_from_a_layer_between_the_cover_and_its_owner(self):
        # The cover is added over A, and also over M at the top of A > N > M. When M leaves, N is left
        # between the cover and its owner A, and the cover inherits N's key.
        key = inp(Full_Press=entry("key_press Y, , "))
        layout = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": switches(button_a=inp(Full_Press=entry(add("Cover"))), button_n=inp(Full_Press=entry(add("N")))),
            "N": switches(button_a=inp(Full_Press=entry(EMPTY)), button_m=inp(Full_Press=entry(add("M"))), button_y=key),
            "M": switches(button_c=inp(Full_Press=entry(add("Cover"))), button_r=inp(release=entry(rem("M")))),
            "Cover": switches(button_x=inp(Full_Press=entry(EMPTY)))})
        report = self.check(layout)
        self.assertEqual(report["owners"], ["A", "M"])
        self.assertIn("switch/button_y comes from N, between the cover and its owner A",
                      {f["detail"] for f in report["findings"] if f["check"] == "intervening layer"})

    def test_a_context_is_part_of_the_view(self):
        layout = self.layout()
        layout.cm["action_layers"]["Preset_1009000"] = {"title": "G"}
        layout.cm["preset"].append({"id": "99", "name": "Preset_1009000", "group_source_bindings": {}})
        layout = Layout({"controller_mappings": layout.cm})
        view = family_view(layout, {"contexts": [["Base"], ["Base", "G"]]})
        self.assertIn(("Base", "G", "A", "Cover"), view.stacks())
        self.assertEqual(check_cover(layout, view, "Cover")["owners"], ["A", "Mid"])


class NeptuneCoverParityTests(unittest.TestCase):
    """On both 90.9 layouts the chain-based check gives what the family-walk check gave, cover by cover."""

    def test_owners_findings_and_layers_above_match_the_family_walk(self):
        rules = json.loads(FROZEN_RULES.read_text())
        for variant in ("default", "alternative"):
            layout = frozen(variant)
            mapping = rules["variants"].get(variant, {})
            walker = FlowWalker(layout)
            results = {name: walker.walk(family) for name, family in families(layout, rules).items()}
            view = family_view(layout, {"contexts": [["Base"], ["Base", "Gyro"]]})
            suffixes = rules["covers"]["suffixes"]
            not_covers = {map_title(t, mapping) for t in rules["covers"]["not_covers"]}
            titles = {map_title(t, mapping) for t in rules["covers"]["titles"]}
            covers = sorted(t for t in layout.presets if t not in not_covers
                            and (t in titles or any(t.endswith(s) for s in suffixes)) and view.reached(t))
            self.assertEqual(len(covers), 15, variant)
            for cover in covers:
                old = flow_covers.check_cover(layout, results, cover)
                new = check_cover(layout, view, cover)
                with self.subTest(variant=variant, cover=cover):
                    self.assertEqual(new["owners"], old["owners"])
                    self.assertEqual({(f["check"], f["detail"]) for f in new["findings"]},
                                     {(f["check"], f["detail"]) for f in old["findings"]})
                    self.assertEqual(new["above"], old["above"])


if __name__ == "__main__":
    unittest.main()
