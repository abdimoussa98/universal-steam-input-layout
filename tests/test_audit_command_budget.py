import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit_command_budget import audit_layout, unique_object


def command(actions="controller_action empty_binding, , "):
    return {"bindings": {"binding": actions}}


def layout(activators, disabled=None):
    return {"controller_mappings": {
        "actions": {"Preset_1": {"title": "Base"}}, "action_layers": {},
        "preset": [{"name": "Preset_1", "group_source_bindings": {"1": "right_joystick active"}}],
        "group": [{"id": "1", "inputs": {"edge": {
            "activators": activators, "disabled_activators": disabled or {}}}}]}}


class CommandBudgetTests(unittest.TestCase):
    def test_seven_entries_under_two_activation_types_fail(self):
        result = audit_layout(layout({"Full_Press": command(), "chord": [command()] * 6}))
        self.assertEqual(result["summary"]["max_commands"], 7)
        self.assertEqual(result["violations"][0]["input"], "edge")

    def test_subcommands_do_not_consume_command_entries(self):
        data = layout({"Full_Press": command(["key_press A"] * 12),
                       "chord": [command(), command()]})
        before = copy.deepcopy(data)
        result = audit_layout(data)
        self.assertFalse(result["violations"])
        self.assertEqual(result["summary"]["max_commands"], 3)
        self.assertEqual(result["summary"]["max_actions_in_one_command"], 12)
        self.assertEqual(data, before)

    def test_all_activation_types_share_the_budget(self):
        result = audit_layout(layout({key: command() for key in
                                      ("Full_Press", "Soft_Press", "release", "chord")}))
        self.assertEqual(result["violations"][0]["count"], 4)

    def test_last_entry_delay_reset_may_be_a_fourth_entry(self):
        add = "controller_action add_layer 9 0 0, , "
        reset = {"bindings": {"binding": add.replace("add_layer", "remove_layer")},
                 "settings": {"hold_repeats": "1", "repeat_rate": "200", "interruptable": "0"}}
        delayed = {"bindings": {"binding": add}, "settings": {"delay_start": "150"}}
        ok = audit_layout(layout({"release": command(), "chord": delayed,
                                  "Full_Press": [command("key_press TAB, , "), reset]}))
        self.assertFalse(ok["violations"])
        self.assertEqual(ok["summary"]["allowed_fourth"], 1)
        rejected = {
            "reset not last": {"release": command(), "Full_Press": [reset, command()], "chord": delayed},
            "no matching delay": {"release": command(), "chord": {**delayed, "settings": {}},
                                  "Full_Press": [command(), reset]},
            "interruptible": {"release": command(), "chord": delayed,
                              "Full_Press": [command(), {**reset, "settings": {"hold_repeats": "1"}}]},
            "five entries": {"release": command(), "chord": [delayed, command()],
                             "Full_Press": [command(), reset]},
        }
        for name, activators in rejected.items():
            with self.subTest(name):
                self.assertEqual(len(audit_layout(layout(activators))["violations"]), 1)

    def test_inactive_and_unreferenced_groups_are_scanned(self):
        data = layout({"chord": [command()] * 4})
        data["controller_mappings"]["preset"][0]["group_source_bindings"]["1"] = "right_joystick inactive modeshift"
        extra = copy.deepcopy(data["controller_mappings"]["group"][0])
        extra["id"] = "2"
        data["controller_mappings"]["group"].append(extra)
        result = audit_layout(data)
        self.assertEqual(len(result["violations"]), 2)
        self.assertEqual(result["summary"]["unreferenced_groups"], 1)

    def test_disabled_bank_is_reported_separately(self):
        result = audit_layout(layout({"Full_Press": command()}, {"chord": [command()] * 4}))
        self.assertEqual(result["summary"]["max_commands"], 1)
        self.assertEqual(result["violations"][0]["bank"], "disabled_activators")

    def test_long_and_double_press_are_banned_in_every_bank(self):
        for kind in ("Long_Press", "Double_Press"):
            result = audit_layout(layout({"Full_Press": command()}, {kind: command()}))
            self.assertFalse(result["violations"])
            self.assertEqual([(r["activation"], r["bank"]) for r in result["banned_activators"]],
                             [(kind, "disabled_activators")])
        result = audit_layout(layout({key: command() for key in ("Full_Press", "Start_Press", "release")}))
        self.assertFalse(result["banned_activators"])

    def test_plain_inactive_slots_are_counted(self):
        data = layout({"Full_Press": command()})
        data["controller_mappings"]["preset"][0]["group_source_bindings"]["1"] = "right_joystick inactive"
        self.assertEqual(audit_layout(data)["summary"]["plain_inactive_slots"], 1)
        data["controller_mappings"]["preset"][0]["group_source_bindings"]["1"] = "right_joystick inactive modeshift"
        self.assertEqual(audit_layout(data)["summary"]["plain_inactive_slots"], 0)

    def test_malformed_and_duplicate_data_are_rejected(self):
        with self.assertRaises(ValueError):
            audit_layout(layout({"chord": ["not a command object"]}))
        with self.assertRaises(ValueError):
            json.loads('{"chord": {}, "chord": {}}', object_pairs_hook=unique_object)

    def test_cli_pass_fail_and_parse_error_exit_codes(self):
        script = Path(__file__).resolve().parents[1] / "audit_command_budget.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layout.json"
            for content, expected in (
                (json.dumps(layout({"chord": [command()] * 3})), 0),
                (json.dumps(layout({"chord": [command()] * 4})), 1),
                (json.dumps(layout({"Long_Press": command()})), 1),
                ("not json", 2),
            ):
                path.write_text(content)
                result = subprocess.run([sys.executable, str(script), str(path), "--json"], capture_output=True)
                self.assertEqual(result.returncode, expected)
                if expected != 2:
                    self.assertEqual(len(json.loads(result.stdout)), 1)


if __name__ == "__main__":
    unittest.main()
