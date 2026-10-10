"""The exceptions register: every accepted finding in one list (steam_layout/exceptions.py)."""
import copy
import json
from pathlib import Path
import unittest

from steam_layout import exceptions, rules

ROOT = Path(__file__).resolve().parents[1]


def entry(rule="R139", scope=None, **changes):
    row = {"rule": rule, "scope": scope or {"layers": ["P"], "inputs": ["switch/button_a"]}, "status": "allow",
           "why": "by design", "decided": "Author, 2026-10-02", "todo": None}
    row.update(changes)
    return row


class ShapeTests(unittest.TestCase):
    def test_a_complete_entry_passes(self):
        self.assertEqual(exceptions.check([entry()]), [entry()])

    def test_an_entry_needs_every_field(self):
        for label, bad in (("no reason", entry(why="")), ("no decider", entry(decided="")),
                           ("no rule", entry(rule="")), ("a bad rule ID", entry(rule="R7")),
                           ("an unknown status", entry(status="fine")), ("no scope", dict(entry(), scope={})),
                           ("a to-do status with no to-do", entry(status="todo"))):
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    exceptions.check([bad])
        missing = entry()
        del missing["todo"]
        with self.assertRaises(ValueError):
            exceptions.check([missing])

    def test_a_scope_must_fit_its_rule(self):
        with self.assertRaises(ValueError):
            exceptions.check([entry("R132", {"layers": ["P"]})])            # the Cleanup audit needs `removes`
        with self.assertRaises(ValueError):
            exceptions.check([entry("R140", {"target": "Win"})])            # the Window audit needs source and input
        exceptions.check([entry("R101", {"note": "five legacy commands"})])  # a rule no audit reads: a note
        exceptions.check([entry("R139", {"kind": "covers"}), entry("R136", {"kind": "touchpad"}),
                          entry("R136", {"upper": "C", "lower": "P"})])       # a rule with two shapes of scope
        with self.assertRaises(ValueError):
            exceptions.check([entry("R136", {"upper": "C"})])

    def test_a_dormant_scope_names_exact_layers_and_does_not_accept_input_decisions(self):
        exceptions.check([entry("R145", {"layers": ["Dormant"], "dormant": True})])
        for scope in ({"layers": ["Dormant"], "dormant": False},
                      {"layers": [], "dormant": True},
                      {"layers": "Dormant", "dormant": True},
                      {"layers": ["Dormant"], "dormant": True, "inputs": ["switch/button_a"]}):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                exceptions.check([entry("R145", scope)])


class ExpandTests(unittest.TestCase):
    """Each audit still reads the section it always read; `expand` fills it from the register."""

    def test_flow_decisions(self):
        config = exceptions.expand({"exceptions": [entry(), entry("R145", status="todo", todo="todos.md: x")]})
        self.assertEqual(config["decisions"], [
            {"layers": ["P"], "inputs": ["switch/button_a"], "status": "allow", "why": "by design"},
            {"layers": ["P"], "inputs": ["switch/button_a"], "status": "todo", "why": "by design"}])

    def test_flow_scopes_preserve_presence_and_absence_gates(self):
        gates = {"where": "Present", "not_where": "Absent"}
        config = exceptions.expand({"exceptions": [
            entry(rule, {"layers": ["P"], "inputs": ["joystick/edge"], **gates})
            for rule in ("R139", "R145")]})
        for decision in config["decisions"]:
            self.assertEqual({key: decision[key] for key in gates}, gates)

    def test_cover_findings(self):
        config = exceptions.expand({"covers": {"titles": ["C"]}, "exceptions": [
            entry("R144", {"cover": "C", "checks": ["outlives owners"]})]})
        self.assertEqual(config["covers"]["allow"], [{"cover": "C", "checks": ["outlives owners"], "reason": "by design"}])
        self.assertEqual(config["covers"]["titles"], ["C"])

    def test_dormant_layers_are_separate_from_inherited_input_decisions(self):
        config = exceptions.expand({"exceptions": [entry("R145", {"layers": ["Dormant"], "dormant": True},
                                                         status="todo", todo="todos.md: deferred interaction")]})
        self.assertEqual(config["dormant_layers"], [{"layers": ["Dormant"], "status": "todo", "why": "by design",
                                                     "todo": "todos.md: deferred interaction"}])
        self.assertNotIn("decisions", config)

    def test_kept_removals(self):
        config = exceptions.expand({"exceptions": [entry("R132", {"layers": ["P"], "removes": ["Ghost"]})]})
        self.assertEqual(config["cleanups"]["keep"], [{"layers": ["P"], "removes": ["Ghost"], "why": "by design"}])

    def test_cleanup_scopes_preserve_presence_and_absence_gates(self):
        gates = {"where": "New", "not_where": "Retired"}
        config = exceptions.expand({"exceptions": [
            entry("R132", {"layers": ["P"], "removes": ["Ghost"], **gates}),
            entry("R170", {"layers": ["P"], "inputs": ["joystick/edge"], **gates})]})
        for section in ("keep", "required"):
            self.assertEqual({key: config["cleanups"][section][0][key] for key in gates}, gates)

    def test_review_scopes(self):
        config = exceptions.expand({"exceptions": [entry("R139", {"kind": "covers"}),
                                                   entry("R136", {"upper": "C", "lower": "P"})]})
        self.assertEqual(config["review"], {"covers": "by design"})
        self.assertEqual(config["cleanups"]["accepted_exits"], [{"upper": "C", "lower": "P", "why": "by design"}])
        self.assertNotIn("decisions", config)

    def test_sections_written_the_old_way_are_kept(self):
        old = {"layers": ["Q"], "inputs": ["switch/button_b"], "status": "allow", "why": "old"}
        config = exceptions.expand({"decisions": [old], "exceptions": [entry()]})
        self.assertEqual([d["layers"] for d in config["decisions"]], [["Q"], ["P"]])

    def test_the_input_is_not_changed(self):
        config = {"exceptions": [entry()]}
        exceptions.expand(config)
        self.assertNotIn("decisions", config)

    def test_window_decisions_join_the_stacks_config(self):
        route = entry("R140", {"target": "Win", "source": "switch", "input": "button_a"})
        merged = exceptions.window({"targets": {"Other": {"stacks": []}}}, [route])
        self.assertEqual(merged["targets"]["Win"]["decisions"],
                         [{"source": "switch", "input": "button_a", "status": "allow", "why": "by design"}])
        self.assertEqual(merged["targets"]["Other"], {"stacks": []})

    def test_of_selects_by_rule(self):
        rows = [entry(), entry("R136", {"kind": "touchpad"}, status="todo", todo="todos.md: touchpad")]
        self.assertEqual([e["scope"] for e in exceptions.of(rows, "R136")], [{"kind": "touchpad"}])


class RegisterTests(unittest.TestCase):
    """The real register, steam_layout/flow_config.json."""

    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(exceptions.REGISTER.read_text(encoding="utf-8"))
        cls.entries = exceptions.load()
        cls.rules = rules.load()

    def test_every_exception_names_a_rule_in_the_registry(self):
        self.assertTrue(self.entries)
        for row in self.entries:
            with self.subTest(row["rule"]):
                self.assertIn(row["rule"], self.rules)

    def test_a_rule_lists_exceptions_exactly_when_the_register_has_one(self):
        registered = {row["rule"] for row in self.entries}
        listed = {rule.id for rule in self.rules.values() if rule.exceptions != "None"}
        self.assertEqual(registered, listed)

    def test_no_exception_lives_anywhere_else(self):
        self.assertFalse(self.config.get("decisions"))
        self.assertFalse(self.config.get("covers", {}).get("allow"))
        self.assertFalse(self.config.get("cleanups", {}).get("keep"))
        self.assertFalse(self.config.get("dormant_layers"))
        stacks = json.loads((ROOT / "steam_layout" / "traced_stacks.json").read_text(encoding="utf-8"))
        self.assertFalse([t for t, spec in stacks.get("targets", {}).items() if spec.get("decisions")])

    def test_the_audits_read_the_register(self):
        from steam_layout.covers import load_rules
        expanded = load_rules()
        flow = [e for e in self.entries if e["rule"] in exceptions.FLOW and "inputs" in e["scope"]]
        self.assertEqual(len(expanded.get("decisions", [])), len(flow))
        self.assertTrue(flow)
        self.assertTrue(expanded["review"]["covers"])                # cover layers aren't reviewed input by input
        self.assertTrue(expanded["cleanups"]["touchpad_exits"])      # the touchpad exception to the hidden-exit rule

    def test_the_fallback_edge_decision_does_not_apply_to_the_reused_entry_guard(self):
        from tools.audit_flow_inheritance import decisions
        config = exceptions.load_config()
        key = ("Steering", "joystick/edge")
        for variant in ("default", "alternative"):
            mapping = config.get("variants", {}).get(variant, {})
            with self.subTest(variant=variant):
                self.assertIn(key, decisions(config, variant, mapping,
                                             {"Base", "Steering", "Steering | LS: Fallback Guard"}))
                self.assertNotIn(key, decisions(config, variant, mapping,
                                                {"Base", "Steering", "Steering | LS: Entry Guard"}))

    def test_entry_guard_inverted_edge_exception_accepts_only_the_quiet_driver_self_removal(self):
        from tools.audit_command_budget import allowed_inverted
        guard = "Steering | LS: Entry Guard"
        scope = next(row['scope'] for row in self.entries
                     if row['rule'] == 'R111' and row['scope']['layers'] == [guard])
        for variant in ('default', 'alternative'):
            data = {'controller_mappings': {'title': variant, 'actions': {'Base': {'title': 'Base'}},
                    'action_layers': {'P1': {'title': 'Steering'}, 'P2': {'title': guard}}}}
            owners = [{'title': guard, 'source_state': 'joystick active'}]
            entry = {'activation': 'chord', 'settings': copy.deepcopy(scope['settings'][variant]),
                     'actions': [f'controller_action remove_layer {{{{Base::{guard}}}}} 0 0, , ']}
            with self.subTest(variant=variant):
                self.assertTrue(allowed_inverted(entry, owners, data))
                numeric = copy.deepcopy(entry)
                numeric['actions'] = ['controller_action remove_layer 3 0 0, , ']
                self.assertTrue(allowed_inverted(numeric, owners, data))
            mutations = {}
            for name, value in (('gyro_ratchet_button_mask', '4096'),
                                ('gyro_ratchet_button_requireany_or_all', '1'),
                                ('edge_binding_invert', '0'), ('hold_repeats', '0'),
                                ('interruptable', '1'), ('haptic_intensity', '1'),
                                ('repeat_rate', '50')):
                mutant = copy.deepcopy(entry)
                mutant['settings'][name] = value
                mutations[name] = mutant
            for name, command in (
                    ('wrong target', 'controller_action remove_layer {{Base::Steering}} 0 0, , '),
                    ('add instead of remove', f'controller_action add_layer {{{{Base::{guard}}}}} 0 0, , '),
                    ('name feedback', f'controller_action remove_layer {{{{Base::{guard}}}}} 1 0, , '),
                    ('beep feedback', f'controller_action remove_layer {{{{Base::{guard}}}}} 0 1, , '),
                    ('missing flags', f'controller_action remove_layer {{{{Base::{guard}}}}}, , ')):
                mutant = copy.deepcopy(entry)
                mutant['actions'] = [command]
                mutations[name] = mutant
            extra = copy.deepcopy(entry)
            extra['actions'].append('controller_action remove_layer {{Base::Steering}} 0 0, , ')
            mutations['extra cleanup'] = extra
            for name, mutant in mutations.items():
                with self.subTest(variant=variant, mutation=name):
                    self.assertFalse(allowed_inverted(mutant, owners, data))
            for other in ([{'title': guard, 'source_state': 'joystick inactive'}],
                          [{'title': guard, 'source_state': 'right_joystick active'}],
                          owners + [{'title': 'Steering', 'source_state': 'joystick active'}], []):
                with self.subTest(variant=variant, owners=other):
                    self.assertFalse(allowed_inverted(entry, other, data))

    def test_historical_fallback_inverted_edge_exception_remains_available(self):
        from tools.audit_command_budget import allowed_inverted
        guard = 'Steering | LS: Fallback Guard'
        scope = next(row['scope'] for row in self.entries
                     if row['rule'] == 'R111' and row['scope']['layers'] == [guard])
        for variant in ('default', 'alternative'):
            data = {'controller_mappings': {'title': variant, 'actions': {'Base': {'title': 'Base'}},
                    'action_layers': {'P1': {'title': 'Steering'}, 'P2': {'title': guard}}}}
            entry = {'activation': 'chord', 'settings': scope['settings'][variant],
                     'actions': ['controller_action add_layer {{Base::Steering}} 0 0, , ']}
            with self.subTest(variant=variant):
                self.assertTrue(allowed_inverted(entry, [{'title': guard, 'source_state': 'joystick active'}], data))


if __name__ == "__main__":
    unittest.main()
