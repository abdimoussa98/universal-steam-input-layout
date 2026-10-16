"""The exceptions register: every accepted finding in one list (steam_layout/exceptions.py).

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.exceptions import *

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

    def test_a_kept_removal_carries_the_release_it_ends_at(self):
        config = exceptions.expand({"exceptions": [entry("R132", {"layers": ["P"], "removes": ["Ghost"], "until": "90.56"})]})
        self.assertEqual(config["cleanups"]["keep"][0]["until"], "90.56")

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


if __name__ == "__main__":
    unittest.main()
