"""Check recovery scope and timed-layer isolation in the actual Neptune layouts.

These verify saved configuration contracts, not Steam's runtime scheduling.
"""
import json
from pathlib import Path
import re
import unittest

from tools.audit_command_budget import audit_layout, command_entries, unique_object
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

ROOT = Path(__file__).resolve().parents[1]
EMPTY = "controller_action empty_binding, , "


def removal(title):
    return "controller_action remove_layer {{Base::" + title + "}} 0 0, , "


def addition(title):
    return "controller_action add_layer {{Base::" + title + "}} 0 0, , "


def load_layouts():
    layouts = {}
    for variant in ("default", "alternative"):
        raw = (ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()
        original = json.loads(raw, object_pairs_hook=unique_object)
        lookup = generate_lookup(original)
        readable, count = ids_to_titles(raw, lookup)
        cm = json.loads(readable)["controller_mappings"]
        names = {key: val["title"] for key, val in {**cm["actions"], **cm["action_layers"]}.items()}
        layouts[variant] = dict(raw=raw, original=original, readable=readable, count=count,
                                lookup=lookup, cm=cm, groups={g["id"]: g for g in cm["group"]},
                                presets={names[p["name"]]: p for p in cm["preset"]})
    return layouts


def recovery_specs(variant):
    left, right, lc, rc = ("L1", "R1", "1", "2") if variant == "default" else ("L2", "R2", "7", "8")
    singles = [left + ": Modifier 0", right + ": Modifier 1"]
    covers = {left + ": Tap Cover", right + ": Tap Cover", left + "&" + right + ": Tap Cover"}
    # Cleanup rules (author, 2026-10-02; findings/2026-10-02-cleanup-boundaries): a list names only
    # layers that can be on the stack with its host. The Gyro and normal modifiers never are, and a
    # cursor is cancelled before Modifier 2 goes on, so neither is listed.
    specs = {}
    for name, button, selector in zip(singles, (left, right), (lc, rc)):
        for prefix in ("", "Gyro | "):
            specs[prefix + name] = ({selector}, {prefix + name, button + ": Tap Cover", button + ": Temp Cursor Gyro"})
    for name in (left + "!" + right + ": Modifier 2", right + "!" + left + ": Modifier 2"):
        for prefix in ("", "Gyro | "):
            specs[prefix + name] = ({lc, rc}, {prefix + name} | {prefix + single for single in singles} | covers)
    for side, selector in (("Left", "15"), ("Right", "14")):
        prefix = "Menu " + side
        specs[prefix + ": Entry Point"] = ({selector}, {prefix + ": Entry Point", prefix + ": Fn Layer"})
    for button, direction, selector in ((left, "Down", lc), (right, "Up", rc)):
        specs[button + ": Scroll " + direction] = ({selector}, {button + ": Scroll " + direction, button + ": Double Tap Cover"})
    parents = {"Menu " + side + ": " + kind for side in ("Left", "Right") for kind in ("Entry Point", "Fn Layer")}
    for title in ("Transition Set 0", "Transition Set 1", "Transition Set 2"):
        specs[title] = ({"14", "15"}, parents | {title})
    return specs


class NeptuneRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = load_layouts()

    def active_groups(self, layout, title):
        return [layout["groups"][gid] for gid, state in layout["presets"][title]["group_source_bindings"].items()
                if state.endswith(" active")]

    def source(self, layout, title, source):
        groups = [layout["groups"][gid] for gid, state in layout["presets"][title]["group_source_bindings"].items()
                  if state == source + " active"]
        self.assertEqual(len(groups), 1, (title, source))
        return groups[0]

    def assert_recovery(self, input_value, selectors, targets, cursor_override=None):
        activators = input_value["activators"]
        chords = activators["chord"]
        chords = chords if isinstance(chords, list) else [chords]
        guards = [c for c in chords if "chord_button" in c["settings"]]
        self.assertEqual({c["settings"]["chord_button"] for c in guards}, selectors)
        for chord in guards:
            self.assertEqual(chord["bindings"]["binding"], EMPTY)
            if cursor_override:
                self.assertNotEqual(chord["settings"].get("interruptable"), "0")
            else:
                self.assertEqual(chord["settings"]["interruptable"], "0")
        if cursor_override:
            mask, cover = cursor_override
            self.assertEqual(len(chords), 2)
            override = [c for c in chords if c not in guards]
            self.assertEqual(len(override), 1)
            self.assertEqual(override[0]["bindings"]["binding"], addition(cover))
            self.assertEqual(override[0]["settings"]["gyro_ratchet_button_mask"], str(mask))
            self.assertEqual(override[0]["settings"]["gyro_ratchet_button_requireany_or_all"], "1")
            self.assertEqual(override[0]["settings"]["interruptable"], "0")
            self.assertEqual(override[0]["settings"].get("hold_repeats"), "1")
        else:
            self.assertEqual(len(chords), len(selectors))
        fallback = activators["Full_Press"]
        self.assertEqual(fallback["settings"]["hold_repeats"], "1")
        self.assertNotEqual(fallback["settings"].get("interruptable"), "0")
        bindings = fallback["bindings"]["binding"]
        bindings = bindings if isinstance(bindings, list) else [bindings]
        self.assertEqual(set(bindings), {removal(t) for t in targets})
        self.assertEqual(len(bindings), len(targets))
        self.assertLessEqual(len(command_entries(activators, "edge")), 3)
        self.assertFalse(input_value.get("disabled_activators"))

    def test_selected_edges_have_expected_guards_scope_and_outer_geometry(self):
        for variant, layout in self.layouts.items():
            specs = recovery_specs(variant)
            self.assertEqual(len(specs), 15)                 # the third transition came with 90.22
            for title, (selectors, targets) in specs.items():
                with self.subTest(variant=variant, layer=title):
                    ls = self.source(layout, title, "joystick")
                    rs = self.source(layout, title, "right_joystick")
                    self.assertEqual(ls["mode"], "dpad")
                    self.assertEqual(ls["settings"]["edge_binding_invert"], "0")
                    if title in ('Transition Set 0', 'Transition Set 1', 'Transition Set 2'):
                        for group in (ls, rs):                      # a cleanup since 90.24 (R170)
                            self.assert_menu_cleanup(group['inputs']['edge']['activators'], title)
                    elif title in ('Menu Left: Entry Point', 'Menu Right: Entry Point'):
                        # Both sticks are D-pads with the same edge; each adds its own stick guard.
                        for group, stick in ((ls, 'Left'), (rs, 'Right')):
                            self.assertEqual(group['mode'], 'dpad')
                            self.assertEqual(group['settings']['edge_binding_radius'], '4915')
                            self.assertEqual(group['settings']['edge_binding_invert'], '0')
                            activators = group['inputs']['edge']['activators']
                            self.assertEqual(set(activators), {'chord', 'Full_Press'})
                            cleanup = activators['Full_Press']      # since 90.24 (R170); the chord is its guard
                            self.assertEqual(cleanup['settings'], {'hold_repeats': '1'})
                            self.assertIn(removal(title), cleanup['bindings']['binding'])
                            chord = activators['chord']
                            self.assertEqual(chord['settings'], {'chord_button': next(iter(selectors)), 'hold_repeats': '1',
                                                                 'repeat_rate': '50', 'interruptable': '0'})
                            self.assertEqual(chord['bindings']['binding'], addition(f'Menu Buttons: {stick} Stick Guard'))
                    elif title.endswith((": Modifier 0", ": Modifier 1")):
                        button = title.removeprefix("Gyro | ").split(":")[0]
                        owner_mask = {"L1": 8, "R1": 4, "L2": 33554432, "R2": 16777216}[button]
                        # Steam adds source-specific hysteresis when entering the outer region:
                        # 10% on LS dpad and 3% on RS joystick_mouse. These encode ~25% entry.
                        for group, opposite_mask, radius in ((ls, 1 << 31, "4915"), (rs, 1 << 30, "7209")):
                            self.assertEqual(group["settings"]["edge_binding_radius"], radius)
                            self.assertEqual(group["settings"]["edge_binding_invert"], "0")
                            self.assert_recovery(group["inputs"]["edge"], selectors, targets,
                                                 (owner_mask | opposite_mask, button + ": Tap Cover"))
                    else:
                        self.assertEqual(ls["settings"]["edge_binding_radius"], "21000")
                        self.assert_recovery(ls["inputs"]["edge"], selectors, targets)
                        self.assertEqual(ls["inputs"]["edge"], rs["inputs"]["edge"])

    def assert_menu_cleanup(self, activators, title, also=()):
        """A cleanup function guarded by either menu button, beside the entries named in `also`."""
        self.assertEqual(set(activators), {'Full_Press', 'chord', *also})
        self.assertEqual(activators['chord'], {'bindings': {'binding': EMPTY}, 'settings': {
            'gyro_ratchet_button_mask': '20480', 'gyro_ratchet_button_requireany_or_all': '0', 'interruptable': '0'}})
        cleanup = activators['Full_Press']
        self.assertEqual(cleanup['settings'], {'hold_repeats': '1'})
        stored = cleanup['bindings']['binding']
        self.assertIn(removal(title), stored if isinstance(stored, list) else [stored])

    def test_transitions_have_a_cleanup_on_the_stick_edges_and_touches_and_the_release_only_clears_the_trio(self):
        # From 90.10 to 90.23 a transition had no stick-touch or edge recovery: a stuck one ended on the
        # next tap of either menu button. Since 90.24 it has a cleanup function on both (R169, R170).
        for variant, layout in self.layouts.items():
            for title in ("Transition Set 0", "Transition Set 1", "Transition Set 2"):
                for source in ("joystick", "right_joystick"):
                    for name in ("touch", "edge"):
                        with self.subTest(variant=variant, layer=title, source=source, input=name):
                            value = self.source(layout, title, source)["inputs"][name]
                            if name == 'edge':
                                self.assert_menu_cleanup(value['activators'], title)
                            else:
                                self.assert_menu_cleanup(value['activators'], title, also=('release',))
                                prefix = 'LST' if source == 'joystick' else 'RST'
                                self.assertEqual(value['activators']['release']['bindings']['binding'],
                                    [removal(prefix + ': ' + suffix) for suffix in
                                     ('Temporary Gyro', 'Tap Cover', 'Entry Point')])

    def test_timed_windows_block_both_edges_and_preserve_ordered_boundaries(self):
        blank = {"activators": {"Full_Press": {"bindings": {"binding": EMPTY}}}, "disabled_activators": {}}
        for variant, layout in self.layouts.items():
            timed = {title for title in layout["presets"]
                     if any("always_on_action" in g.get("inputs", {}) for g in self.active_groups(layout, title))}
            # The Always On layers are exactly the Double Tap windows, so none is skipped below.
            self.assertEqual(timed, {title for title in layout["presets"] if title.endswith(": Double Tap")})
            for title in timed:
                with self.subTest(variant=variant, layer=title):
                    for source in ("joystick", "right_joystick"):
                        self.assertEqual(self.source(layout, title, source)["inputs"]["edge"], blank)
            entered, left = set(), set()
            for owner in layout["presets"]:
                for group in self.active_groups(layout, owner):
                    for value in group.get("inputs", {}).values():
                        for entry in command_entries(value.get("activators", {}), "input"):
                            actions = entry["actions"]
                            operations = [b for b in actions if re.match(r"controller_action (?:add_layer|remove_layer|hold_layer|CHANGE_PRESET) ", b)]
                            for title in timed:
                                add = "controller_action add_layer {{Base::" + title + "}}"
                                if any(b.startswith(add) for b in operations):
                                    self.assertTrue(actions[0].startswith(add), (owner, title))     # R146
                                    entered.add(title)
                            if owner in timed and operations:
                                self.assertEqual(actions[-1], removal(owner), owner)                # R147, R148
                                left.add(owner)
            # Every window has an entry and an exit that the loop checked: neither rule passed on nothing.
            self.assertEqual((entered, left), (timed, timed))

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
