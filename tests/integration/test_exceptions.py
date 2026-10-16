"""The exceptions register: every accepted finding in one list (steam_layout/exceptions.py).

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.exceptions import *

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
