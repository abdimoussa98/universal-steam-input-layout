"""Working Neptune layouts: allowed activators only, no dead groups."""
import json
from pathlib import Path
import re
import unittest

from tools.audit_command_budget import audit_layout

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"Full_Press", "chord", "Start_Press", "release", "Soft_Press"}
RIGHT_PAD_TOUCH = str(1 << 20)


class LayoutHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {v: json.loads((ROOT / f"neptune/single-set-{v}_hold-gyro_latest.json").read_text())
                       for v in ("default", "alternative")}

    def test_only_allowed_activation_types_in_any_bank(self):
        for variant, data in self.layouts.items():
            report = audit_layout(data)
            self.assertFalse(report["banned_activators"], variant)
            for group in data["controller_mappings"]["group"]:
                for name, binding in group.get("inputs", {}).items():
                    for bank in ("activators", "disabled_activators"):
                        with self.subTest(variant=variant, group=group["id"], input=name, bank=bank):
                            self.assertLessEqual(set(binding.get(bank, {})), ALLOWED)

    def test_no_unreferenced_groups_or_plain_inactive_slots(self):
        for variant, data in self.layouts.items():
            cm = data["controller_mappings"]
            targets = set(re.findall(r"mode_shift \S+ (\d+)", json.dumps(cm["group"])))
            referenced = {g for p in cm["preset"] for g in p["group_source_bindings"]}
            ids = {g["id"] for g in cm["group"]}
            with self.subTest(variant=variant):
                self.assertEqual(ids - referenced - targets, set())
                self.assertLessEqual(targets, ids)  # every mode-shift target still exists
                states = [s for p in cm["preset"] for s in p["group_source_bindings"].values()]
                self.assertNotIn("inactive", {s.split(" ", 1)[-1] for s in states})

    def test_rtp_scroll_repeat_is_a_touch_chorded_delay(self):
        for variant, data in self.layouts.items():
            cm = data["controller_mappings"]
            key = next(k for k, v in cm["action_layers"].items() if v["title"] == "RTP: Mouse Buttons")
            preset = next(p for p in cm["preset"] if p["name"] == key)
            gid = next(g for g, s in preset["group_source_bindings"].items() if s == "right_trackpad active")
            group = next(g for g in cm["group"] if g["id"] == gid)
            for name, wheel in (("dpad_north", "SCROLL_UP"), ("dpad_south", "SCROLL_DOWN")):
                with self.subTest(variant=variant, input=name):
                    activators = group["inputs"][name]["activators"]
                    self.assertEqual(set(activators), {"chord", "Full_Press"})
                    self.assertEqual(activators["Full_Press"]["bindings"]["binding"], f"mouse_wheel {wheel}, , ")
                    chord = activators["chord"]
                    self.assertEqual(chord["bindings"]["binding"], f"mouse_wheel {wheel}, , ")
                    self.assertEqual(chord["settings"], {
                        "gyro_ratchet_button_mask": RIGHT_PAD_TOUCH,
                        "gyro_ratchet_button_requireany_or_all": "0",
                        "delay_start": "150", "hold_repeats": "1", "haptic_intensity": "0"})

    def test_only_second_press_cover_resets_use_a_last_fourth_entry(self):
        expected = {"default": {"L1: Scroll Down", "R1: Scroll Up", "Menu Left: Escape", "Menu Right: Tab"},
                    "alternative": {"L2: Scroll Down", "R2: Scroll Up", "Menu Left: Escape", "Menu Right: Tab"}}
        for variant, data in self.layouts.items():
            with self.subTest(variant=variant):
                allowed = audit_layout(data)["allowed_fourth"]
                self.assertEqual({o["title"] for row in allowed for o in row["owners"]}, expected[variant])
                for row in allowed:
                    last = row["entries"][-1]
                    self.assertEqual([e["activation"] for e in row["entries"]],
                                     ["release", "chord", "Full_Press", "Full_Press"])
                    self.assertIn("Double Tap Cover", " ".join(last["actions"]) if "{{" in last["actions"][0]
                                  else self.title_of(data, last["actions"][0]))
                    self.assertEqual(last["settings"], {"hold_repeats": "1", "repeat_rate": "200",
                                                        "interruptable": "0"})

    @staticmethod
    def title_of(data, action):
        cm = data["controller_mappings"]
        order = list(cm["actions"]) + list(cm["action_layers"])
        key = order[int(action.split()[2]) - 1]
        return cm["action_layers"][key]["title"]


if __name__ == "__main__":
    unittest.main()
