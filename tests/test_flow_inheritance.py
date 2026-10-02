"""The family walk (deprecated 2026-10-01) and the audit that used to run on it.

The fixture classes test steam_layout/flow_paths.py and flow_covers.py, which are kept for
reference; the walker's Neptune tests run on the frozen 90.9 layouts with the family rules
as they were then. GateTests and the CLI test cover audit_flow_inheritance.py as it is now,
on backward chains (steam_layout/chains.py, covers.py).

Plan: plans/2026-10-01-intended-flow-inheritance.md, section 5.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from steam_layout.flow_covers import check_cover
from steam_layout.flow_inheritance import inspect_target, nearest
from steam_layout.flow_model import Inventory
from steam_layout.flow_paths import Family, FlowWalker, families, load_config
from steam_layout.model import Layout

ROOT = Path(__file__).resolve().parents[1]
FROZEN_RULES = json.loads((ROOT / "tests/data/flow_families_90.9.json").read_text())


def frozen(variant):
    return Layout(json.loads((ROOT / f"versions/neptune/90.9/single-set-{variant}_hold-gyro_90.9.json").read_text()))
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


def family(controls=(L, R), contexts=(("Base",),), exclude=None, live=(), may_hold=(), held=()):
    contexts = [tuple(c) for c in contexts]
    return Family("fixture", contexts, set(controls), frozenset(held), exclude or {},
                  restricted=frozenset(t for c in contexts for t in c) - set(live), may_hold=frozenset(may_hold))


def walk(layout, fam=None):
    return FlowWalker(layout).walk(fam or family())


def switches(**inputs):
    return {"switch": {"mode": "switches", "inputs": inputs}}


class FlowFixtureTests(unittest.TestCase):
    def test_both_modifier_orders_keep_distinct_lower_stacks(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1)),
                             right_bumper=inp(chord=entry(add("B"), chord_button=2))),
            "A": switches(right_bumper=inp(chord=entry(add("C"), chord_button=1)),
                          left_bumper=inp(release=entry(rem("C"), rem("A")))),
            "B": switches(left_bumper=inp(chord=entry(add("C"), chord_button=2)),
                          right_bumper=inp(release=entry(rem("C"), rem("B")))),
            "C": {}})
        result = walk(lay)
        self.assertEqual(set(result.lower_stacks("C")), {("Base", "A"), ("Base", "B")})
        _, steps = result.path(result.lower_stacks("C")[("Base", "B")])
        self.assertEqual([(s.event, s.control, s.layer) for s in steps if s.fired],
                         [("press", R, "Base"), ("press", L, "B")])

    def test_removal_before_add_and_window_expiry_cycle(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": switches(left_bumper=inp(release=entry(rem("A"), add("W")))),
            "W": switches(always_on_action=inp(Full_Press=entry(rem("W"), delay_start=150)),
                          left_bumper=inp(Full_Press=entry(rem("W"), add("S")))),
            "S": switches(left_bumper=inp(release=entry(rem("S"), add("W"))))})
        result = walk(lay)
        self.assertTrue(result.complete)
        self.assertEqual(set(result.lower_stacks("W")), {("Base",)})
        self.assertFalse(any("A" in s and "W" in s for s, _ in result.states))
        self.assertEqual(set(result.lower_stacks("S")), {("Base",)})
        roles = {t.role for t in Inventory.of(lay).transitions}
        self.assertTrue({"expiry", "second-press", "release", "entry"} <= roles)

    def test_readd_keeps_position_and_remove_add_moves_to_top(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": switches(right_bumper=inp(chord=entry(add("B"), chord_button=1))),
            "B": {"button_diamond": {"mode": "four_buttons", "inputs": {
                "button_a": inp(Full_Press=entry(add("A"))),
                "button_b": inp(Full_Press=entry(rem("A"), add("A")))}}}})
        result = walk(lay, family(controls=(L,)))
        stacks = {s for s, _ in result.states}
        self.assertIn(("Base", "A", "B"), stacks)
        self.assertIn(("Base", "B", "A"), stacks)
        self.assertNotIn(("Base", "A", "B", "A"), stacks)
        self.assertEqual(set(result.lower_stacks("B")), {("Base", "A"), ("Base",)})

    def test_overridden_lower_binding_does_not_fire(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("A"), add("D")))}},
                  "button_diamond": {"mode": "four_buttons", "inputs": {"button_a": inp(Full_Press=entry(add("X")))}}},
            "X": switches(left_bumper=inp(Full_Press=entry(EMPTY))),
            "D": {}})
        fam = family(controls=(L,))
        walker = FlowWalker(lay)
        result = walker.walk(fam)
        state = (("Base", "A", "X"), frozenset({L}))
        self.assertIn(state, result.states)
        # X's empty left_bumper overrides A's release: letting go adds nothing.
        release = [(nxt, step) for nxt, step in walker.successors(fam, state)
                   if step.event == "release" and step.control == L]
        self.assertEqual(release[0][0], (("Base", "A", "X"), frozenset()))
        self.assertEqual((release[0][1].layer, release[0][1].fired), ("X", ()))

    def test_hold_branch_and_early_release(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": switches(left_bumper=inp(chord=entry(add("H"), chord_button=1, delay_start=300),
                                          Full_Press=entry(rem("H"), hold_repeats=1, repeat_rate=350, interruptable=0),
                                          release=entry(rem("H"), rem("A")))),
            "H": {}})
        inv = Inventory.of(lay)
        self.assertEqual({t.role for t in inv.by_layer("A")}, {"hold", "reset", "release"})
        result = walk(lay, family(controls=(L,)))
        self.assertEqual(set(result.lower_stacks("H")), {("Base", "A")})
        self.assertIn((("Base",), frozenset()), result.states)

    def test_recoveries_and_resets_are_listed_not_followed(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            # No release entry: A outlives the press, like a layer left by a missed release.
            "A": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_a": inp(
                chord=entry(add("T"), chord_button=1, hold_repeats=1, interruptable=0),
                Full_Press=entry(rem("T"), rem("A"), hold_repeats=1))}}},
            "T": {}})
        roles = {(t.activator, t.role) for t in Inventory.of(lay).by_layer("A")}
        self.assertIn(("Full_Press", "recovery"), roles)
        result = walk(lay, family(controls=(L,)))
        # With L1 released, A's tap only has the guarded recovery: listed, not followed.
        self.assertIn((("Base", "A"), frozenset()), result.states)
        self.assertNotIn((("Base",), frozenset()), [s for s, step in result.states.items() if step])
        self.assertTrue(any(r.startswith("recovery") for r in result.skipped.values()))
        self.assertEqual(set(result.lower_stacks("T")), {("Base", "A")})

    def test_context_layers_fire_only_on_declared_controls(self):
        lay = fixture({
            "Base": {"switch": {"mode": "switches", "inputs": {
                "left_bumper": inp(chord=entry(add("A"), chord_button=1))}},
                "button_diamond": {"mode": "four_buttons", "inputs": {"button_a": inp(Full_Press=entry(add("Other")))}}},
            "A": switches(left_bumper=inp(release=entry(rem("A")))),
            "Other": {}})
        result = walk(lay, family(controls=(L,)))
        self.assertNotIn("Other", result.layers())

    def test_exclusions_stop_a_route_and_are_reported(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("A")))}},
                  "joystick": {"mode": "dpad", "inputs": {"click": inp(chord=entry(add("Elsewhere"), chord_button=1))}}},
            "Elsewhere": {}})
        fam = family(controls=(L,), exclude={("A", ("joystick", "click")): "another family"})
        result = walk(lay, fam)
        self.assertNotIn("Elsewhere", result.layers())
        self.assertIn("excluded: another family", set(result.skipped.values()))


    def test_inverted_edge_removal_is_a_center_exit(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"joystick": {"mode": "dpad", "inputs": {"edge": inp(Full_Press=entry(rem("A"), hold_repeats=1))}}}})
        lay.active("A")["joystick"]["settings"] = {"edge_binding_invert": "1"}
        roles = {t.role for t in Inventory.of(lay).by_layer("A")}
        self.assertEqual(roles, {"center"})
        lay.active("A")["joystick"]["settings"] = {}
        self.assertEqual({t.role for t in Inventory.of(lay).by_layer("A")}, {"recovery"})

    def test_live_context_layers_fire_on_every_input(self):
        lay = fixture({
            "Base": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_a": inp(Full_Press=entry(add("Other")))}}},
            "P": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_b": inp(Full_Press=entry(add("Q")))}}},
            "Q": {}, "Other": {}})
        result = walk(lay, family(controls=(), contexts=(("Base", "P"),), live=("P",)))
        self.assertEqual(set(result.layers()), {"P", "Q"})

    def test_may_hold_controls_satisfy_chords_without_firing(self):
        trigger = ("left_trigger", "click")
        lay = fixture({
            "Base": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(chord=entry(add("A"), chord_button=5))}},
                     "left_trigger": {"mode": "trigger", "inputs": {"click": inp(Full_Press=entry(add("Other")))}}},
            "A": switches(left_bumper=inp(release=entry(rem("A")))), "Other": {}})
        self.assertNotIn("A", walk(lay, family(controls=(L,))).layers())
        result = walk(lay, family(controls=(L,), may_hold=(trigger,)))
        self.assertIn("A", result.layers())
        self.assertNotIn("Other", result.layers())

    def test_a_stick_points_one_way(self):
        north, east = ("joystick", "dpad_north"), ("joystick", "dpad_east")
        lay = fixture({
            "Base": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(chord=entry(add("A"), chord_button=1))}}},
            "A": {"joystick": {"mode": "dpad", "inputs": {
                "dpad_north": inp(Full_Press=entry(add("N"), delay_start=5)),
                "dpad_east": inp(Full_Press=entry(add("E"), delay_start=5))}}},
            "N": {}, "E": {}})
        result = walk(lay, family(controls=(L,)))
        self.assertFalse(any(north in held and east in held for _, held in result.states))
        self.assertTrue({"N", "E"} <= set(result.layers()))

    def test_layers_only_held_by_legacy_commands_are_listed(self):
        lay = fixture({
            "Base": {"right_trackpad": {"mode": "absolute_mouse", "inputs": {"click": inp(Soft_Press=entry(
                "controller_action hold_layer {{Base::M}} 0 0, , "))}}},
            "M": {}})
        inv = Inventory.of(lay)
        self.assertEqual({t.role for t in inv.transitions}, {"legacy-hold"})
        self.assertTrue(inv.legacy_only("M"))


    def test_a_source_mode_change_blocks_inheritance(self):
        touch = ("right_trackpad", "touch")
        lay = fixture({
            "Base": {"right_trackpad": {"mode": "absolute_mouse", "inputs": {"touch": inp(Full_Press=entry(add("Entry")))}},
                     "switch": {"mode": "switches", "inputs": {"left_bumper": inp(chord=entry(add("Win"), chord_button=1))}}},
            "Win": {"right_trackpad": {"mode": "dpad", "inputs": {"dpad_north": inp(Full_Press=entry(rem("Win")))}}},
            "Entry": {}})
        result = walk(lay, family(controls=(L, touch)))
        self.assertIn("Entry", result.layers())
        self.assertFalse(any(s[-2:] == ("Win", "Entry") for s, _ in result.states))
        kind, layer, _, _ = nearest(lay, ("Base", "Win"), *touch)
        self.assertEqual((kind, layer), ("mode", "Win"))
        report = next(r for r in inspect_target(lay, "Entry", [("Base", "Win")]) if (r.source, r.name) == touch)
        self.assertEqual(report.status, "blocks by mode")


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

    def test_clean_cover_and_owner_is_the_layer_below(self):
        lay = self.layout()
        report = check_cover(lay, {"f": walk(lay, family(controls=(L,)))}, "Cover")
        self.assertEqual(report["owners"], ["A", "Mid"])
        self.assertEqual(report["findings"], [])

    def test_cover_that_outlives_its_owner(self):
        lay = self.layout()
        # Now the owner's release no longer removes the cover.
        lay.active("Cover")["switch"]["inputs"]["left_bumper"] = inp(release=entry(rem("A")))
        report = check_cover(lay, {"f": walk(lay, family(controls=(L,)))}, "Cover")
        # Later steps cascade from the stray cover; the root finding must be there.
        self.assertIn("outlives owners", {f["check"] for f in report["findings"]})
        allowed = check_cover(lay, {"f": walk(lay, family(controls=(L,)))}, "Cover", {"outlives owners": "by design"})
        self.assertEqual({f["allowed"] for f in allowed["findings"] if f["check"] == "outlives owners"}, {"by design"})

    def test_layers_above_the_cover_are_listed(self):
        lay = self.layout()
        lay.active("Mid")["switch"] = {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("Mid")))},
                                       "settings": {}}
        report = check_cover(lay, {"f": walk(lay, family(controls=(L,)))}, "Cover")
        # Mid can sit above the cover and takes its release without removing the cover.
        self.assertEqual(report["above"].get("Mid"), {"switch/left_bumper": False})

    def test_owner_above_the_cover(self):
        lay = fixture({
            "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
            "A": {"switch": {"mode": "switches", "inputs": {"left_bumper": inp(release=entry(rem("A")))}},
                  "button_diamond": {"mode": "four_buttons", "inputs": {
                      "button_a": inp(chord=entry(add("Cover"), chord_button=1)),
                      "button_b": inp(chord=entry(rem("A"), add("A"), chord_button=1))}}},
            "Cover": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_x": inp(Full_Press=entry(EMPTY))}}}})
        report = check_cover(lay, {"f": walk(lay, family(controls=(L,)))}, "Cover")
        self.assertIn("below its owner", {f["check"] for f in report["findings"]})


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
        result = walk(self.lay)
        self.lowers = {t: list(result.lower_stacks(t)) for t in ("T", "T2")}

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

    def audit(self, layout, *args, rules=None):
        with tempfile.TemporaryDirectory() as tmp:
            path, rules_path = Path(tmp, "layout.json"), Path(tmp, "rules.json")
            path.write_text(json.dumps({"controller_mappings": layout.cm}))
            rules_path.write_text(json.dumps(rules or self.RULES))
            rules = rules_path
            out = subprocess.run([sys.executable, str(ROOT / "audit_flow_inheritance.py"), str(path),
                                  "--config", str(rules), *args], capture_output=True, text=True)
            return out, json.loads(subprocess.run(
                [sys.executable, str(ROOT / "audit_flow_inheritance.py"), str(path), "--config", str(rules), "--json"],
                capture_output=True, text=True).stdout)

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

    def test_a_layer_outside_every_family_still_fails(self):
        layout = self.varying()
        cm = layout.cm
        cm["action_layers"]["Preset_1009999"] = {"title": "Orphan"}
        cm["preset"].append({"id": str(len(cm["preset"])), "name": "Preset_1009999", "group_source_bindings": {}})
        out, report = self.audit(Layout({"controller_mappings": cm}))
        self.assertEqual(report["unreached"], ["Orphan"])
        self.assertFalse(report["clean"])
        self.assertEqual(out.returncode, 1)
        self.assertIn("no chain of adding bindings reaches: Orphan", out.stdout)

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
        layout = CoverFixtureTests().layout()
        # The owner's release no longer removes the cover: it outlives its owner.
        layout.active("Cover")["switch"]["inputs"]["left_bumper"] = inp(release=entry(rem("A")))
        out, report = self.audit(layout)
        self.assertIn("outlives owners", {f["check"] for c in report["covers"] for f in c["findings"]})
        self.assertFalse(report["clean"])
        self.assertEqual(out.returncode, 1)


class NeptuneFlowTests(unittest.TestCase):
    EXPECTED = {
        "modifiers": {"Gyro", "{l}: Modifier 0", "{r}: Modifier 1", "{l}!{r}: Modifier 2", "{r}!{l}: Modifier 2",
                      "Gyro | {l}: Modifier 0", "Gyro | {r}: Modifier 1", "Gyro | {l}!{r}: Modifier 2",
                      "Gyro | {r}!{l}: Modifier 2", "{l}: Tap Cover", "{r}: Tap Cover", "{l}&{r}: Tap Cover",
                      "{l}: Temp Cursor Gyro", "{r}: Temp Cursor Gyro", "{l}: Double Tap", "{r}: Double Tap",
                      "{l}: Scroll Down", "{r}: Scroll Up", "{l}: Double Tap Cover", "{r}: Double Tap Cover"},
        "menu_left": {"Gyro", "Transition Set 0", "Transition Set 1", "Menu Left: Entry Point", "Menu Left: Fn Layer", "Menu Left: Double Tap", "Menu Left: Escape",
                      "Menu Left: Double Tap Cover", "Steering | Menu Left: Entry Point",
                      "Steering | Menu Left: Tap Cover"},
    }

    def test_both_variants_cover_the_documented_families_quickly(self):
        for variant, (l, r) in (("default", ("L1", "R1")), ("alternative", ("L2", "R2"))):
            lay = frozen(variant)
            walker = FlowWalker(lay)
            reached = set()
            start = time.perf_counter()
            for name, fam in families(lay, FROZEN_RULES).items():
                with self.subTest(variant=variant, family=name):
                    result = walker.walk(fam)
                    self.assertTrue(result.complete)
                    reached |= set(result.layers())
                    if name in self.EXPECTED:
                        self.assertEqual(set(result.layers()), {t.format(l=l, r=r) for t in self.EXPECTED[name]})
            self.assertLess(time.perf_counter() - start, 30)
            missing = set(lay.presets) - reached - {lay.base}
            self.assertEqual(missing, {t for t in missing if walker.inventory.legacy_only(t)})
            self.assertEqual(missing, {"LTP: Arrow Keys", "RTP: Mouse Buttons"})

    def test_documented_recipe_paths(self):
        lay = frozen("default")
        fams = families(lay, FROZEN_RULES)
        result = FlowWalker(lay).walk(fams["modifiers"])
        # Double tap: L1 tap, release into the window, second press into Scroll Down.
        self.assertEqual(set(result.lower_stacks("L1: Scroll Down")), {("Base",), ("Base", "Gyro")})
        # Both Modifier 2 orders put the combined cover on different lower stacks.
        lowers = set(result.lower_stacks("L1&R1: Tap Cover"))
        self.assertIn(("Base", "L1: Modifier 0", "L1: Tap Cover", "R1: Modifier 1", "R1: Tap Cover", "L1!R1: Modifier 2"), lowers)
        self.assertIn(("Base", "R1: Modifier 1", "R1: Tap Cover", "L1: Modifier 0", "L1: Tap Cover", "R1!L1: Modifier 2"), lowers)
        menu = FlowWalker(lay).walk(fams["menu_left"])
        self.assertIn(("Base", "Menu Left: Entry Point"), set(menu.lower_stacks("Menu Left: Fn Layer")))
        self.assertIn(("Base",), set(menu.lower_stacks("Menu Left: Escape")))

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
            self.assertEqual(len(report["covers"]), 15)
            self.assertEqual(len(report["targets"]), 67)   # 69 layers, less the two hold_layer ones
            self.assertLess(report["view"]["seconds"], 5)
            # Inherited bindings that vary between stacks are listed, and don't decide the result.
            self.assertTrue([i for x in report["targets"].values() for i in x["inputs"] if i["finding"] == "varies"])
            self.assertFalse([i for x in report["targets"].values() for i in x["inputs"] if i["finding"] == "conflict"])
            open_covers = {c["cover"] for c in report["covers"] for f in c["findings"] if not f["allowed"]}
            self.assertEqual(open_covers, set())
            self.assertTrue(report["clean"])


if __name__ == "__main__":
    unittest.main()
