"""Check recovery scope and timed-layer isolation in the actual Neptune layouts.

These verify saved configuration contracts, not Steam's runtime scheduling.
"""
import json
from pathlib import Path
import re
import unittest

from audit_command_budget import audit_layout, command_entries, unique_object
from convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

ROOT = Path(__file__).resolve().parents[1]
EMPTY = "controller_action empty_binding, , "


def removal(title):
    return "controller_action remove_layer {{Base::" + title + "}} 0 0, , "


def recovery_specs(variant):
    left, right, lc, rc = ("L1", "R1", "1", "2") if variant == "default" else ("L2", "R2", "7", "8")
    singles = [left + ": Modifier 0", right + ": Modifier 1"]
    all_singles = {title for name in singles for title in (name, "Gyro | " + name)}
    covers = {left + ": Tap Cover", right + ": Tap Cover", left + "&" + right + ": Tap Cover"}
    specs = {}
    for name, button, selector in zip(singles, (left, right), (lc, rc)):
        for title in (name, "Gyro | " + name):
            specs[title] = ({selector}, {name, "Gyro | " + name, button + ": Tap Cover"})
    for name in (left + "!" + right + ": Modifier 2", right + "!" + left + ": Modifier 2"):
        for title in (name, "Gyro | " + name):
            specs[title] = ({lc, rc}, {name, "Gyro | " + name} | all_singles | covers)
    for side, selector in (("Left", "15"), ("Right", "14")):
        prefix = "Menu " + side
        specs[prefix + ": Entry Point"] = ({selector}, {prefix + ": Entry Point", prefix + ": Fn Layer"})
    for button, direction, selector in ((left, "Down", lc), (right, "Up", rc)):
        specs[button + ": Scroll " + direction] = ({selector}, {button + ": Scroll " + direction, button + ": Double Tap Cover"})
    parents = {"Menu " + side + ": " + kind for side in ("Left", "Right") for kind in ("Entry Point", "Fn Layer")}
    for title in ("Transition Set 0", "Transition Set 1"):
        specs[title] = ({"14", "15"}, parents | {title})
    return specs


class NeptuneRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {}
        for variant in ("default", "alternative"):
            raw = (ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()
            original = json.loads(raw, object_pairs_hook=unique_object)
            lookup = generate_lookup(original)
            readable, count = ids_to_titles(raw, lookup)
            cm = json.loads(readable)["controller_mappings"]
            names = {key: val["title"] for key, val in {**cm["actions"], **cm["action_layers"]}.items()}
            cls.layouts[variant] = dict(raw=raw, original=original, readable=readable, count=count,
                                        lookup=lookup, cm=cm, groups={g["id"]: g for g in cm["group"]},
                                        presets={names[p["name"]]: p for p in cm["preset"]})

    def active_groups(self, layout, title):
        return [layout["groups"][gid] for gid, state in layout["presets"][title]["group_source_bindings"].items()
                if state.endswith(" active")]

    def source(self, layout, title, source):
        groups = [layout["groups"][gid] for gid, state in layout["presets"][title]["group_source_bindings"].items()
                  if state == source + " active"]
        self.assertEqual(len(groups), 1, (title, source))
        return groups[0]

    def assert_recovery(self, input_value, selectors, targets):
        activators = input_value["activators"]
        chords = activators["chord"]
        chords = chords if isinstance(chords, list) else [chords]
        self.assertEqual({c["settings"]["chord_button"] for c in chords}, selectors)
        for chord in chords:
            self.assertEqual(chord["bindings"]["binding"], EMPTY)
            self.assertEqual(chord["settings"]["interruptable"], "0")
        fallback = activators["Full_Press"]
        self.assertEqual(fallback["settings"]["hold_repeats"], "1")
        self.assertNotEqual(fallback["settings"].get("interruptable"), "0")
        bindings = fallback["bindings"]["binding"]
        bindings = bindings if isinstance(bindings, list) else [bindings]
        self.assertEqual(set(bindings), {removal(t) for t in targets})
        self.assertEqual(len(bindings), len(targets))
        self.assertLessEqual(len(command_entries(activators, "edge")), 3)
        self.assertFalse(input_value.get("disabled_activators"))

    def test_selected_ls_edges_have_expected_guards_scope_and_outer_geometry(self):
        for variant, layout in self.layouts.items():
            specs = recovery_specs(variant)
            self.assertEqual(len(specs), 14)
            for title, (selectors, targets) in specs.items():
                with self.subTest(variant=variant, layer=title):
                    ls = self.source(layout, title, "joystick")
                    rs = self.source(layout, title, "right_joystick")
                    self.assertEqual(ls["mode"], "dpad")
                    self.assertEqual(ls["settings"]["edge_binding_radius"], "21000")
                    self.assertEqual(ls["settings"]["edge_binding_invert"], "0")
                    self.assert_recovery(ls["inputs"]["edge"], selectors, targets)
                    self.assertEqual(ls["inputs"]["edge"], rs["inputs"]["edge"])

    def test_transition_recovery_is_consistent_and_removes_transition_first(self):
        for variant, layout in self.layouts.items():
            for title in ("Transition Set 0", "Transition Set 1"):
                selectors, targets = recovery_specs(variant)[title]
                for source in ("joystick", "right_joystick"):
                    for name in ("touch", "edge"):
                        with self.subTest(variant=variant, layer=title, source=source, input=name):
                            value = self.source(layout, title, source)["inputs"][name]
                            self.assert_recovery(value, selectors, targets)
                            self.assertEqual(value["activators"]["Full_Press"]["bindings"]["binding"][-1], removal(title))

    def test_timed_windows_block_ls_edge_and_preserve_ordered_boundaries(self):
        blank = {"activators": {"Full_Press": {"bindings": {"binding": EMPTY}}}, "disabled_activators": {}}
        for variant, layout in self.layouts.items():
            timed = {title for title in layout["presets"]
                     if any("always_on_action" in g.get("inputs", {}) for g in self.active_groups(layout, title))}
            self.assertEqual(len(timed), 7)
            for title in timed:
                with self.subTest(variant=variant, layer=title):
                    self.assertEqual(self.source(layout, title, "joystick")["inputs"]["edge"], blank)
            incoming, outgoing = 0, 0
            for owner in layout["presets"]:
                for group in self.active_groups(layout, owner):
                    for value in group.get("inputs", {}).values():
                        for entry in command_entries(value.get("activators", {}), "input"):
                            actions = entry["actions"]
                            operations = [b for b in actions if re.match(r"controller_action (?:add_layer|remove_layer|hold_layer|CHANGE_PRESET) ", b)]
                            for title in timed:
                                add = "controller_action add_layer {{Base::" + title + "}}"
                                if any(b.startswith(add) for b in operations):
                                    self.assertTrue(actions[0].startswith(add), (owner, title))
                                    incoming += 1
                            if owner in timed and operations:
                                self.assertEqual(actions[-1], removal(owner), owner)
                                outgoing += 1
            self.assertEqual((incoming, outgoing), (13, 30))

    def test_all_guarded_removals_repeat_and_rtp_stays_out_of_ls_scope(self):
        for variant, layout in self.layouts.items():
            for group in layout["cm"]["group"]:
                for value in group.get("inputs", {}).values():
                    for bank in ("activators", "disabled_activators"):
                        activators = value.get(bank, {})
                        if "chord" not in activators:
                            continue
                        for entry in command_entries(activators, "input"):
                            if (entry["activation"] == "Full_Press" and entry["settings"].get("interruptable") != "0"
                                    and any(b.startswith("controller_action remove_layer ") for b in entry["actions"])):
                                self.assertEqual(entry["settings"].get("hold_repeats"), "1", (variant, group["id"]))
            self.assertNotIn("edge", self.source(layout, "RTP: Entry Point", "joystick")["inputs"])

    def test_command_budget_and_runtime_reference_order(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                self.assertFalse(audit_layout(layout["original"])["violations"])
                cm = layout["cm"]
                self.assertEqual([p["name"] for p in cm["preset"]], list(cm["actions"]) + list(cm["action_layers"]))
                self.assertEqual([p["id"] for p in cm["preset"]], list(map(str, range(len(cm["preset"])))))
                keys = [int(key.split("_")[1]) for key in cm["action_layers"]]
                self.assertEqual(keys, sorted(keys))
                self.assertEqual(titles_to_ids(layout["readable"], layout["lookup"])[0], layout["raw"])
                self.assertNotRegex(layout["readable"], r"controller_action (?:add_layer|remove_layer|hold_layer|CHANGE_PRESET) \d+")


if __name__ == "__main__":
    unittest.main()
