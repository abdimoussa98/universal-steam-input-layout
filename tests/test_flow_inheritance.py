"""The transition inventory, what a layer inherits per lower stack, and the Flow audit.

The Flow audit (audit_flow_inheritance.py) runs on backward chains (steam_layout/chains.py,
covers.py). The family walk it first ran on is deprecated; its tests are in
archived/depth-search-and-family-walk/.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.flow_inheritance import inspect_target, nearest
from steam_layout.flow_model import Inventory
from steam_layout.model import Layout

ROOT = Path(__file__).resolve().parents[1]
EMPTY = "controller_action empty_binding, , "
L, R = ("switch", "left_bumper"), ("switch", "right_bumper")


def add(t):
    return f"controller_action add_layer {{{{Base::{t}}}}} 0 0, , "


def rem(t):
    return f"controller_action remove_layer {{{{Base::{t}}}}} 0 0, , "


def entry(*commands, **settings):
    """Commands in execution order (stored bottom to top)."""
    e = {"bindings": {"binding": list(reversed(commands)) if len(commands) > 1 else commands[0]}}
    if settings:
        e["settings"] = {k: str(v) for k, v in settings.items()}
    return e


def inp(**activators):
    return {"activators": activators}


def fixture(layers):
    """layers: {title: {source: {"mode": ..., "inputs": {...}}}}; the first title is the action set."""
    cm = {"title": "fixture", "actions": {}, "action_layers": {}, "preset": [], "group": []}
    for n, (title, sources) in enumerate(layers.items()):
        key = f"Preset_{1000001 + n}"
        (cm["actions"] if n == 0 else cm["action_layers"])[key] = {"title": title}
        bindings = {}
        for source, spec in sources.items():
            gid = str(len(cm["group"]))
            cm["group"].append({"id": gid, "mode": spec.get("mode", "switches"),
                                "inputs": spec.get("inputs", {}), "settings": {}})
            bindings[gid] = source + " active"
        cm["preset"].append({"id": str(n), "name": key, "group_source_bindings": bindings})
    return Layout({"controller_mappings": cm})


def switches(**inputs):
    return {"switch": {"mode": "switches", "inputs": inputs}}


def cover_layout():
    """An owner (A) that applies a cover and a second overlay (Mid), and releases into a window (W)."""
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


class InventoryTests(unittest.TestCase):


    def test_inverted_edge_removal_is_a_center_exit(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"joystick": {"mode": "dpad", "inputs": {"edge": inp(Full_Press=entry(rem("A"), hold_repeats=1))}}}})
        lay.active("A")["joystick"]["settings"] = {"edge_binding_invert": "1"}
        roles = {t.role for t in Inventory.of(lay).by_layer("A")}
        self.assertEqual(roles, {"center"})
        lay.active("A")["joystick"]["settings"] = {}
        self.assertEqual({t.role for t in Inventory.of(lay).by_layer("A")}, {"recovery"})

    def test_layers_only_held_by_legacy_commands_are_listed(self):
        lay = fixture({
            "Base": {"right_trackpad": {"mode": "absolute_mouse", "inputs": {"click": inp(Soft_Press=entry(
                "controller_action hold_layer {{Base::M}} 0 0, , "))}}},
            "M": {}})
        inv = Inventory.of(lay)
        self.assertEqual({t.role for t in inv.transitions}, {"legacy-hold"})
        self.assertTrue(inv.legacy_only("M"))


class InheritanceFixtureTests(unittest.TestCase):
    def setUp(self):
        x = inp(Full_Press=entry("key_press X, , "))
        self.lay = fixture({
            "Base": {"switch": {"mode": "switches", "inputs": {
                "left_bumper": inp(chord=entry(add("A"), chord_button=1)),
                "right_bumper": inp(chord=entry(add("B"), chord_button=2))}},
                "button_diamond": {"mode": "four_buttons", "inputs": {"button_b": inp(Full_Press=entry("key_press B, , "))}},
                "gyro": {"mode": "gyro_to_mouse", "inputs": {}}},
            "A": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("T"), rem("T2"), rem("A"))),
                                                            "right_bumper": inp(Full_Press=entry(EMPTY))}},
                  "button_diamond": {"mode": "four_buttons", "inputs": {
                      "button_a": inp(Full_Press=entry(add("T"), add("T2"))), "button_x": x,
                      "button_y": inp(Full_Press=entry("key_press Y, , ")),
                      "button_b": inp(Full_Press=entry("key_press A, , "))}}},
            "B": {"switch": {"mode": "switches", "inputs": {"right_bumper": inp(release=entry(rem("T"), rem("T2"), rem("Z"), rem("B"))),
                                                            "left_bumper": inp(Full_Press=entry(EMPTY))}},
                  "button_diamond": {"mode": "four_buttons", "inputs": {
                      "button_a": inp(Full_Press=entry(add("T"), add("T2"))), "button_x": x,
                      "button_y": inp(Full_Press=entry(add("Z")))}},
                  "gyro": {"mode": "disabled", "inputs": {}}},
            "T": {},
            "T2": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_y": inp(Full_Press=entry(EMPTY))}}},
            "Z": {}})
        self.lowers = {"T": [("Base", "A"), ("Base", "B")], "T2": [("Base", "A", "T"), ("Base", "B", "T")]}

    def report(self, target, source, name):
        return next(r for r in inspect_target(self.lay, target, self.lowers[target])
                    if (r.source, r.name) == (source, name))

    def test_same_binding_from_two_owners_is_one_variant(self):
        r = self.report("T", "button_diamond", "button_x")
        self.assertEqual(len(r.variants), 1)
        self.assertEqual(r.variants[0].providers, {"A", "B"})
        self.assertIsNone(r.finding)

    def test_two_different_non_base_bindings_are_reported_as_varying(self):
        r = self.report("T", "button_diamond", "button_y")
        self.assertEqual(r.finding, "varies")
        self.assertEqual({v.label() for v in r.non_base}, {"A", "B"})
        self.assertEqual([v.changes_layers for v in r.variants if v.providers == {"B"}], ["direct"])

    def test_one_non_base_binding_with_base_fallback_is_review(self):
        r = self.report("T", "button_diamond", "button_b")
        self.assertEqual(r.finding, "review")
        self.assertEqual({(v.label(), v.base) for v in r.variants}, {("A", False), ("Base", True)})

    def test_existing_clear_is_satisfied(self):
        r = self.report("T2", "button_diamond", "button_y")
        self.assertEqual((r.status, r.finding), ("clears", "satisfied"))

    def test_disabled_source_stops_the_lookup(self):
        for lower in self.lowers["T"]:
            self.assertEqual(nearest(self.lay, lower, "gyro", "x")[0], "disabled" if "B" in lower else "none", lower)
        self.assertTrue(any("B" in lower for lower in self.lowers["T"]))


class GateTests(unittest.TestCase):
    """What fails the Flow audit. An inherited binding that differs between stacks does not (author,
    2026-10-01): blocking is only required under an Always On layer, which the Window audit checks."""
    RULES = {"version": 1, "covers": {"titles": ["Cover"]}}   # no families: the chains need none

    def audit(self, layout, *args, rules=None, baseline=None):
        with tempfile.TemporaryDirectory() as tmp:
            path, rules_path = Path(tmp, "layout.json"), Path(tmp, "rules.json")
            path.write_text(json.dumps({"controller_mappings": layout.cm}))
            rules_path.write_text(json.dumps(rules or self.RULES))
            rules = rules_path
            against = []
            if baseline is not None:
                Path(tmp, "before.json").write_text(json.dumps({"controller_mappings": baseline.cm}))
                against = ["--baseline", str(Path(tmp, "before.json"))]
            out = subprocess.run([sys.executable, str(ROOT / "audit_flow_inheritance.py"), str(path),
                                  "--config", str(rules), *against, *args], capture_output=True, text=True)
            return out, json.loads(subprocess.run(
                [sys.executable, str(ROOT / "audit_flow_inheritance.py"), str(path), "--config", str(rules),
                 *against, "--json"], capture_output=True, text=True).stdout)

    def varying(self):
        """T sits on A or on B, and button_y is a different binding in each (InheritanceFixtureTests)."""
        case = InheritanceFixtureTests()
        case.setUp()
        return case.lay

    def test_a_binding_that_varies_between_stacks_does_not_fail(self):
        out, report = self.audit(self.varying())
        row = next(i for i in report["targets"]["T"]["inputs"] if i["input"] == "button_y")
        self.assertEqual((row["finding"], row.get("decision")), ("varies", None))
        self.assertTrue(report["clean"])
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("Result: clean", out.stdout)

    def test_the_varying_binding_is_still_shown_for_the_layer(self):
        out, _ = self.audit(self.varying(), "--layer", "T")
        self.assertIn("varies: button_diamond/button_y", out.stdout)

    # --- on a changed layer, an entry fails until it is fixed or accepted (author, 2026-10-02) ---

    def before(self, layer, name, binding="key_press OLD, , "):
        """The varying layout as it was before `layer`'s face button `name` changed."""
        import copy
        old = Layout(copy.deepcopy({"controller_mappings": self.varying().cm}))
        old.active(layer)["button_diamond"]["inputs"][name] = inp(Full_Press=entry(binding))
        return old

    def review(self, report):
        return {(row["layer"], row["input"], row["finding"]) for row in report["needs_review"]}

    def test_an_unchanged_layout_needs_no_review(self):
        out, report = self.audit(self.varying(), baseline=self.varying())
        self.assertEqual((report["needs_review"], report["changed_layers"], out.returncode), ([], [], 0))

    def test_a_changed_provider_puts_the_entries_it_feeds_up_for_review(self):
        out, report = self.audit(self.varying(), baseline=self.before("A", "button_x"))
        self.assertEqual(report["changed_layers"], ["A"])
        self.assertLessEqual({("T", "button_diamond/button_y", "varies"), ("T", "button_diamond/button_b", "review")},
                             self.review(report))
        self.assertFalse(report["clean"])
        self.assertEqual(out.returncode, 1)
        self.assertIn("Needs review [R139]", out.stdout)
        self.assertIn("T: button_diamond/button_y (varies)", out.stdout)

    def test_a_changed_target_puts_its_own_entries_up_for_review(self):
        _, report = self.audit(self.varying(), baseline=self.before("T2", "button_y"))
        self.assertEqual(report["changed_layers"], ["T2"])
        self.assertEqual({layer for layer, _, _ in self.review(report)}, {"T2"})

    def test_an_accepted_entry_passes(self):
        accepted = {"rule": "R139", "status": "allow", "why": "T is meant to take either owner's Y",
                    "decided": "Author, 2026-10-02", "todo": None,
                    "scope": {"layers": ["T", "T2"], "inputs": ["button_diamond/button_y", "button_diamond/button_b",
                                                                "switch/left_bumper", "switch/right_bumper"]}}
        out, report = self.audit(self.varying(), baseline=self.before("A", "button_x"),
                                 rules={**self.RULES, "exceptions": [accepted]})
        self.assertEqual(report["needs_review"], [])
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_cover_layers_are_accepted_by_the_cover_rule_when_the_register_says_so(self):
        covers = {"version": 1, "covers": {"titles": ["T", "T2"]}}
        _, report = self.audit(self.varying(), baseline=self.before("A", "button_x"), rules=covers)
        self.assertTrue(self.review(report))                      # without the entry, a cover's inputs are reviewed too
        entry_ = {"rule": "R139", "scope": {"kind": "covers"}, "status": "allow", "why": "the cover check judges them",
                  "decided": "Author, 2026-10-02", "todo": None}
        _, report = self.audit(self.varying(), baseline=self.before("A", "button_x"),
                               rules={**covers, "exceptions": [entry_]})
        self.assertEqual(report["needs_review"], [])

    def test_a_layer_outside_every_family_still_fails(self):
        layout = self.varying()
        cm = layout.cm
        cm["action_layers"]["Preset_1009999"] = {"title": "Orphan"}
        cm["preset"].append({"id": str(len(cm["preset"])), "name": "Preset_1009999", "group_source_bindings": {}})
        out, report = self.audit(Layout({"controller_mappings": cm}))
        self.assertEqual(report["unreached"], ["Orphan"])
        self.assertFalse(report["clean"])
        self.assertEqual(out.returncode, 1)
        self.assertIn("Coverage gap [R145]: no chain of adding bindings reaches: Orphan", out.stdout)

    def test_a_cover_finding_is_printed_with_its_rule(self):
        import contextlib
        import io
        import audit_flow_inheritance as flow
        finding = {"check": "outlives owners", "detail": "no owner is present", "stacks": 1,
                   "stack": ["Base", "Cover"], "allowed": None, "path": ["Base a: +Cover"]}
        report = {"layout": {"title": "T", "variant": "default", "sha256": "0" * 64},
                  "rules": {"version": 1, "sha256": "0" * 64, "path": "rules.json"},
                  "view": {"stacks": 1, "contexts": [["Base"]], "seconds": 0}, "targets": {}, "unsupported": [],
                  "uncovered": [], "unreached": [], "clean": False,
                  "covers": [{"cover": "Cover", "owners": [], "above": {}, "findings": [finding]}]}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            flow.print_report(report, detail=False)
        self.assertIn("outlives owners [R144]: no owner is present", out.getvalue())

    def test_a_layer_only_added_by_hold_layer_is_out_of_scope_not_a_gap(self):
        layout = self.varying()
        cm = layout.cm
        cm["action_layers"]["Preset_1009999"] = {"title": "Held"}
        cm["preset"].append({"id": str(len(cm["preset"])), "name": "Preset_1009999", "group_source_bindings": {}})
        cm["group"][0]["inputs"]["button_h"] = inp(Full_Press=entry("controller_action hold_layer {{Base::Held}} 0 0, , "))
        out, report = self.audit(Layout({"controller_mappings": cm}))
        self.assertEqual((report["unreached"], report["legacy_only"]), ([], ["Held"]))
        self.assertTrue(report["clean"])

    def test_the_lower_stacks_come_with_the_bindings_that_built_them(self):
        _, report = self.audit(self.varying())
        stacks = {tuple(row["stack"]): row["path"] for row in report["targets"]["T"]["lower_stacks"]}
        # Z is B's own layer (B's button_y adds it), so it may arrive on B before T is added.
        self.assertEqual(set(stacks), {("Base", "A"), ("Base", "B"), ("Base", "B", "Z")})
        self.assertEqual(len(stacks[("Base", "A")]), 2)
        self.assertTrue(stacks[("Base", "A")][0].startswith("Base switch/left_bumper"))
        self.assertTrue(stacks[("Base", "B", "Z")][1].startswith("arrival: B button_diamond/button_y"))

    def test_a_context_in_the_rules_is_a_starting_stack(self):
        layout = self.varying()
        cm = layout.cm
        cm["action_layers"]["Preset_1009999"] = {"title": "G"}
        cm["preset"].append({"id": str(len(cm["preset"])), "name": "Preset_1009999", "group_source_bindings": {}})
        rules = dict(self.RULES, contexts=[["Base"], ["Base", "G"]])
        _, report = self.audit(Layout({"controller_mappings": cm}), rules=rules)
        self.assertIn(["Base", "G", "A"], [row["stack"] for row in report["targets"]["T"]["lower_stacks"]])
        self.assertEqual(report["unreached"], [])      # a context layer counts as covered

    def test_inventory_lists_what_the_chains_follow(self):
        out, _ = self.audit(self.varying(), "--inventory", "--layer", "A")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("follow entry", out.stdout)
        self.assertIn("settle release", out.stdout)

    def test_a_cover_finding_still_fails(self):
        layout = cover_layout()
        # The owner's release no longer removes the cover: it outlives its owner.
        layout.active("Cover")["switch"]["inputs"]["left_bumper"] = inp(release=entry(rem("A")))
        out, report = self.audit(layout)
        self.assertIn("outlives owners", {f["check"] for c in report["covers"] for f in c["findings"]})
        self.assertFalse(report["clean"])
        self.assertEqual(out.returncode, 1)


class NeptuneFlowTests(unittest.TestCase):

    def test_cli_runs_without_out_and_reports_json(self):
        for variant in ("default", "alternative"):
            run = subprocess.run([sys.executable, str(ROOT / "audit_flow_inheritance.py"),
                                  str(ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"), "--json"],
                                 capture_output=True, text=True, cwd="/")
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertNotIn("families", report)
            self.assertEqual(report["view"]["contexts"], [["Base"], ["Base", "Gyro"]])
            self.assertEqual(report["layout"]["variant"], variant)
            self.assertEqual(report["unreached"], [])
            self.assertEqual(report["legacy_only"], ["LTP: Arrow Keys", "RTP: Mouse Buttons"])
            self.assertEqual(report["unsupported"], [])
            self.assertEqual(report["stale_decisions"], [])
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            # R145: a chain reaches every layer, except the ones only hold_layer adds.
            self.assertEqual(set(report["targets"]), set(layout.presets) - {layout.base} - set(report["legacy_only"]))
            # R144: every cover-type layer is cover-checked, and nothing else is.
            checked = {c["cover"] for c in report["covers"]}
            self.assertEqual(checked, {title for title, row in report["targets"].items() if row["cover"]})
            modifier = "L2" if variant == "alternative" else "L1"
            self.assertLessEqual({f"{modifier}: Tap Cover", "Gyro Off Ramp Up"}, checked)   # by suffix, and by title
            self.assertNotIn("LST: Tap Cover", checked)                                     # a stick-touch helper
            self.assertLess(report["view"]["seconds"], 5)
            # Inherited bindings that vary between stacks are listed, and don't decide the result.
            self.assertTrue([i for x in report["targets"].values() for i in x["inputs"] if i["finding"] == "varies"])
            self.assertFalse([i for x in report["targets"].values() for i in x["inputs"] if i["finding"] == "conflict"])
            open_covers = {c["cover"] for c in report["covers"] for f in c["findings"] if not f["allowed"]}
            self.assertEqual(open_covers, set())
            self.assertTrue(report["clean"])


if __name__ == "__main__":
    unittest.main()
