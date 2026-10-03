"""Backward chains: what can be below a layer (plans/2026-10-01-backward-chain-audit.md).

Tiny layouts first, one rule per test, then both Neptune layouts against the
two existing stack sources.
"""
import json
from pathlib import Path
import unittest

from steam_layout.chains import Chains
from steam_layout.flow_paths import FlowWalker, families
from steam_layout.inheritance import check_stack
from steam_layout.model import Layout, always_on_layers
from steam_layout.stacks import StackSpace
from tests.test_audit_inheritance import EMPTY, add, build, remove

ROOT = Path(__file__).resolve().parents[1]
FROZEN_RULES = ROOT / "tests/data/flow_families_90.9.json"   # the family rules as they were at 90.9

SW = "switches"


def on(kind, *commands, **settings):
    """One activator entry; commands in execution order (stored bottom to top)."""
    stored = list(reversed(commands)) if len(commands) > 1 else commands[0]
    return {kind: {"bindings": {"binding": stored}, "settings": {k: str(v) for k, v in settings.items()}}}


def press(*commands, **settings):
    return on("Full_Press", *commands, **settings)


def release(*commands, **settings):
    return on("release", *commands, **settings)


def chains(layers, arrivals=0):
    """Chains for a tiny layout. Mid-chain arrivals are off unless a test asks, so each rule is tested alone."""
    return Chains(Layout(build(layers)), arrivals=arrivals)


class ChainTests(unittest.TestCase):
    """Step 1: who adds this layer, back to the action set."""

    def test_a_layer_added_by_base_has_base_under_it(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("A"))})}, "A": {}})
        self.assertEqual(set(c.lineage("A")), {("Base",)})

    def test_a_parent_that_removes_itself_is_not_under_the_layer(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                    "P": {"switch": (SW, {"button_a": release(remove("P"), add("W"))})}, "W": {}})
        self.assertEqual(set(c.lineage("W")), {("Base",)})

    def test_a_parent_that_stays_is_under_the_layer(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                    "P": {"switch": (SW, {"button_b": press(add("C"))})}, "C": {}})
        self.assertEqual(set(c.lineage("C")), {("Base", "P")})

    def test_layers_added_earlier_in_the_same_binding_sit_below(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("S"), add("G"))})}, "S": {}, "G": {}})
        self.assertEqual(set(c.lineage("S")), {("Base",)})
        self.assertEqual(set(c.lineage("G")), {("Base", "S")})

    def test_two_bindings_that_add_the_layer_give_two_stacks(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P")), "button_b": press(add("Q"))})},
                    "P": {"switch": (SW, {"button_x": press(add("W"))})},
                    "Q": {"switch": (SW, {"button_x": press(add("W"))})}, "W": {}})
        self.assertEqual(set(c.lineage("W")), {("Base", "P"), ("Base", "Q")})

    def test_a_step_is_intercepted_by_a_layer_on_top_that_binds_its_input(self):
        # Base adds P and a cover together; the cover binds button_x, so P's button_x never fires.
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"), add("Cover"))})},
                    "P": {"switch": (SW, {"button_x": press(add("W"))})},
                    "Cover": {"switch": (SW, {"button_x": press(EMPTY)})}, "W": {}})
        self.assertEqual(c.lineage("W"), {})
        self.assertFalse(c.reached("W"))
        self.assertTrue(c.reached("P"))

    def test_a_loop_ends(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("A"))})},
                    "A": {"switch": (SW, {"button_b": press(remove("A"), add("B"))})},
                    "B": {"switch": (SW, {"button_b": press(remove("B"), add("A"))})}})
        self.assertEqual(set(c.lineage("A")), {("Base",)})
        self.assertEqual(set(c.lineage("B")), {("Base",)})

    def test_a_disabled_source_on_top_stops_the_step(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"), add("Off"))})},
                    "P": {"joystick": ("dpad", {"click": press(add("W"))})},
                    "Off": {"joystick": ("disabled", {})}, "W": {}})
        self.assertFalse(c.reached("W"))

    def test_a_different_source_mode_on_top_stops_the_step(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"), add("Mouse"))})},
                    "P": {"joystick": ("dpad", {"click": press(add("W"))})},
                    "Mouse": {"joystick": ("joystick_mouse", {})}, "W": {}})
        self.assertFalse(c.reached("W"))

    def test_hold_layer_is_not_followed(self):
        hold = "controller_action hold_layer {{Base::H}} 0 0, , "
        c = chains({"Base": {"switch": (SW, {"button_a": press(hold)})}, "H": {}})
        self.assertFalse(c.reached("H"))
        self.assertEqual(c.lineage("H"), {})

    def test_the_reason_is_the_shortest_chain(self):
        # W sits on Base by two routes: through X (two steps) or through P and Q (three). The reason is the short one.
        c = chains({"Base": {"switch": (SW, {"button_x": press(add("X")), "button_a": press(add("P"))})},
                    "X": {"switch": (SW, {"button_w": press(remove("X"), add("W"))})},
                    "P": {"switch": (SW, {"button_b": press(remove("P"), add("Q"))})},
                    "Q": {"switch": (SW, {"button_c": press(remove("Q"), add("W"))})}, "W": {}})
        self.assertEqual([t.layer for _, t in c.lineage("W")[("Base",)].steps], ["Base", "X"])

    def test_every_stack_comes_with_the_bindings_that_built_it(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                    "P": {"switch": (SW, {"button_a": release(remove("P"), add("W"))})}, "W": {}})
        why = c.lineage("W")[("Base",)]
        self.assertEqual([(kind, t.layer, t.input, t.activator) for kind, t in why.steps],
                         [("step", "Base", "button_a", "Full_Press"), ("step", "P", "button_a", "release")])
        self.assertIsNone(why.bystander)
        self.assertEqual(why.describe(), ["Base switch/button_a Full_Press#0: +P",
                                          "P switch/button_a release#0: -P ; +W"])


def covered(cover_inputs, source="switch", mode=SW):
    """Base adds P with a Cover on top. The Cover binds button_x, which P needs to add W; P's button_z adds Z."""
    inputs = {"button_x": press(EMPTY)} if source == "switch" else {}
    layers = {"Base": {"switch": (SW, {"button_a": press(add("P"), add("Cover"))})},
              "P": {"switch": (SW, {"button_x": press(add("W")), "button_z": press(add("Z"))})},
              "Cover": {"switch": (SW, {"button_x": press(EMPTY)})}, "W": {}, "Z": {}, "D": {}}
    layers["Cover"].setdefault(source, (mode, inputs))[1].update(cover_inputs)
    return layers


class SettleTests(unittest.TestCase):
    """Step 2: between two adds, the stack can shrink through a removal-only binding."""

    def test_a_cover_lifted_by_a_release_lets_the_next_step_fire(self):
        c = chains(covered({"button_y": release(remove("Cover"))}))
        self.assertEqual(set(c.lineage("W")), {("Base", "P")})
        self.assertEqual([(kind, t.layer, t.input) for kind, t in c.lineage("W")[("Base", "P")].steps],
                         [("step", "Base", "button_a"), ("settle", "Cover", "button_y"), ("step", "P", "button_x")])

    def test_both_the_covered_and_the_lifted_stack_are_kept(self):
        c = chains(covered({"button_y": release(remove("Cover"))}))
        self.assertEqual(set(c.lineage("Z")), {("Base", "P", "Cover"), ("Base", "P")})

    def test_plain_and_cancel_removals_settle_too(self):
        for name, binding in (("removal", press(remove("Cover"))),
                              ("cancel", press(remove("Cover"), hold_repeats=1, interruptable=0))):
            with self.subTest(role=name):
                self.assertEqual(set(chains(covered({"button_y": binding})).lineage("W")), {("Base", "P")})

    def test_a_cover_lifted_at_stick_centre_settles(self):
        # The inverted-edge centre exit Steering uses today (role "center").
        data = build(covered({"edge": press(remove("Cover"), hold_repeats=1)}, source="joystick", mode="dpad"))
        next(g for g in data["controller_mappings"]["group"] if "edge" in g["inputs"])["settings"] = {
            "edge_binding_invert": "1"}
        self.assertEqual(set(Chains(Layout(data), arrivals=0).lineage("W")), {("Base", "P")})

    def test_a_cover_lifted_by_an_edge_release_settles(self):
        # The stateful transitions plan replaces the centre exit with a normal edge's Release.
        c = chains(covered({"edge": release(remove("Cover"))}, source="joystick", mode="dpad"))
        self.assertEqual(set(c.lineage("W")), {("Base", "P")})

    def test_a_recovery_removal_never_settles(self):
        c = chains(covered({"button_y": press(remove("Cover"), hold_repeats=1)}))
        self.assertEqual(c.lineage("W"), {})

    def test_a_binding_that_also_adds_a_layer_never_settles(self):
        c = chains(covered({"button_y": release(remove("Cover"), add("D"))}))
        self.assertEqual(c.lineage("W"), {})


def three_buttons(l60=None, exit_ops=None, extra=None):
    """The author's example. Button 1 enters L70, whose release adds the window W. Button 3 adds L60."""
    layers = {"Base": {"switch": (SW, {"button_1": press(add("L70")), "button_3": press(add("L60"))})},
              "L60": {"switch": (SW, l60 or {"button_2": press(remove("L60"))})},
              "L70": {"switch": (SW, {"button_1": release(*(exit_ops or (remove("L70"), add("W"))))})},
              "W": {}}
    layers.update(extra or {})
    return layers


class BystanderTests(unittest.TestCase):
    """Step 3: a layer that added nothing in the chain can still be under the layer."""

    def test_a_layer_that_leaves_the_chain_inputs_alone_is_under_the_window(self):
        c = chains(three_buttons())
        self.assertEqual(set(c.lineage("W")), {("Base",)})
        self.assertEqual(set(c.below("W")), {("Base",), ("Base", "L60")})

    def test_the_reason_names_the_bystander_and_keeps_the_chain(self):
        why = chains(three_buttons()).below("W")[("Base", "L60")]
        self.assertEqual(why.bystander, "L60")
        self.assertEqual([t.layer for _, t in why.steps], ["Base", "L70"])
        self.assertIsNone(chains(three_buttons()).below("W")[("Base",)].bystander)

    def test_a_layer_that_binds_a_chain_input_is_not_under_the_window(self):
        c = chains(three_buttons(l60={"button_1": press(EMPTY), "button_2": press(remove("L60"))}))
        self.assertEqual(set(c.below("W")), {("Base",)})

    def test_a_layer_the_chain_removes_is_not_under_the_window(self):
        c = chains(three_buttons(exit_ops=(remove("L70"), remove("L60"), add("W"))))
        self.assertEqual(set(c.below("W")), {("Base",)})

    def test_a_bystander_brings_its_own_parent(self):
        c = chains(three_buttons(l60={"button_4": press(add("Fn"))}, extra={"Fn": {}}))
        self.assertEqual(set(c.below("W")), {("Base",), ("Base", "L60"), ("Base", "L60", "Fn")})

    def test_a_layer_never_reached_has_nothing_below(self):
        c = chains(three_buttons(extra={"Orphan": {}}))
        self.assertEqual(c.below("Orphan"), {})


class AboveTests(unittest.TestCase):
    """Step 6: "above X" is every layer that has X in one of its own stacks."""

    def test_a_child_that_stays_on_its_parent_is_above_it(self):
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                    "P": {"switch": (SW, {"button_b": press(add("C"))})}, "C": {}})
        self.assertEqual(set(c.above("P")), {"C"})
        self.assertEqual(set(c.above("C")), set())
        self.assertEqual(set(c.above("Base")), {"P", "C"})

    def test_a_layer_is_above_its_bystanders(self):
        # The window blocks buttons 1 and 3, as a real one does, so nothing can be added on top of it.
        blocked = {"W": {"switch": (SW, {"button_1": press(EMPTY), "button_3": press(EMPTY)})}}
        c = chains(three_buttons(extra=blocked))
        self.assertEqual(set(c.above("L60")), {"L70", "W"})
        self.assertEqual(set(c.above("W")), set())

    def test_a_layer_that_binds_nothing_can_have_anything_added_over_it(self):
        # Base's buttons fire straight through an empty layer, so both other layers can land on top of W.
        self.assertEqual(set(chains(three_buttons()).above("W")), {"L60", "L70"})

    def test_each_layer_above_comes_with_the_stack_and_its_reason(self):
        stack, why = chains(three_buttons()).above("L60")["W"]
        self.assertEqual(stack, ("Base", "L60"))
        self.assertEqual(why.bystander, "L60")


def menu(cover=None, entry=None):
    """Base adds an Entry Point. Holding adds its Tap Cover; a stick click adds the Fn layer."""
    hold = {"button_a": press(add("TC"), delay_start=300)}
    hold.update(entry or {})
    return {"Base": {"switch": (SW, {"button_a": press(add("EP"))})},
            "EP": {"switch": (SW, hold), "joystick": ("dpad", {"click": press(add("Fn"))})},
            "TC": {"joystick": ("dpad", cover or {})}, "TC2": {}, "Fn": {}}


class ArrivalTests(unittest.TestCase):
    """Step 3b: a layer that lands between two steps of the chain."""

    def test_a_cover_that_lands_before_the_next_step_is_under_the_layer(self):
        self.assertEqual(set(chains(menu()).lineage("Fn")), {("Base", "EP")})
        self.assertEqual(set(chains(menu(), arrivals=1).lineage("Fn")), {("Base", "EP"), ("Base", "EP", "TC")})

    def test_arrivals_are_on_by_default(self):
        self.assertIn(("Base", "EP", "TC"), Chains(Layout(build(menu()))).lineage("Fn"))

    def test_an_arrival_that_binds_the_next_input_intercepts_it(self):
        c = chains(menu(cover={"click": press(EMPTY)}), arrivals=1)
        self.assertEqual(set(c.lineage("Fn")), {("Base", "EP")})

    def test_at_most_one_arrival_per_chain(self):
        layers = menu(entry={"button_b": press(add("TC2"), delay_start=300)})
        one = set(chains(layers, arrivals=1).lineage("Fn"))
        self.assertEqual(one, {("Base", "EP"), ("Base", "EP", "TC"), ("Base", "EP", "TC2")})
        two = set(chains(layers, arrivals=2).lineage("Fn"))
        self.assertEqual(two - one, {("Base", "EP", "TC", "TC2"), ("Base", "EP", "TC2", "TC")})

    def test_the_reason_names_the_arriving_binding(self):
        why = chains(menu(), arrivals=1).lineage("Fn")[("Base", "EP", "TC")]
        self.assertEqual([(kind, t.layer, t.input) for kind, t in why.steps],
                         [("step", "Base", "button_a"), ("arrival", "EP", "button_a"), ("step", "EP", "click")])
        self.assertEqual(why.describe()[1], "arrival: EP switch/button_a Full_Press#0: +TC")

    def test_a_removal_that_also_adds_is_an_arrival_not_a_settle(self):
        # SettleTests shows this never settles; with arrivals on it lifts the cover and leaves D behind.
        c = chains(covered({"button_y": release(remove("Cover"), add("D"))}), arrivals=1)
        self.assertEqual(set(c.lineage("W")), {("Base", "P", "D")})


class FamilyViewTests(unittest.TestCase):
    """The view the cover check uses: start from declared contexts, and let only the chain's own layers arrive."""

    def view(self, layers, contexts=()):
        return Chains(Layout(build(layers)), contexts=contexts, foreign_arrivals=False)

    def test_a_context_is_a_stack_the_chains_may_start_from(self):
        layers = {"Base": {"switch": (SW, {"button_a": press(add("A"))})}, "G": {}, "A": {}}
        self.assertEqual(set(chains(layers).lineage("A")), {("Base",)})
        self.assertEqual(set(self.view(layers, contexts=[("Base", "G")]).lineage("A")), {("Base",), ("Base", "G")})

    def test_a_context_layer_that_binds_the_input_intercepts_it(self):
        layers = {"Base": {"switch": (SW, {"button_a": press(add("A"))})},
                  "G": {"switch": (SW, {"button_a": press(EMPTY)})}, "A": {}}
        self.assertEqual(set(self.view(layers, contexts=[("Base", "G")]).lineage("A")), {("Base",)})

    def test_an_unknown_context_layer_is_an_error(self):
        with self.assertRaises(ValueError):
            self.view({"Base": {}}, contexts=[("Base", "Nope")]).states

    def test_a_layer_the_chain_added_may_arrive_but_a_base_one_may_not(self):
        # The Entry Point adds its own Tap Cover mid-chain; L60 is added by Base, which belongs to no chain.
        self.assertIn(("Base", "EP", "TC"), self.view(menu()).lineage("Fn"))
        self.assertEqual(set(self.view(three_buttons()).lineage("W")), {("Base",)})
        self.assertIn(("Base", "L60"), Chains(Layout(build(three_buttons()))).lineage("W"))

    def test_a_context_layer_may_not_arrive_either(self):
        # G is a context, like Gyro: its own bindings belong to other chains.
        layers = {"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                  "G": {"switch": (SW, {"button_g": press(add("X"))})},
                  "P": {"switch": (SW, {"button_b": press(add("W"))})}, "X": {}, "W": {}}
        self.assertEqual(set(self.view(layers, contexts=[("Base", "G")]).lineage("W")),
                         {("Base", "P"), ("Base", "G", "P")})

    def test_stacks_lists_every_stack_visited_including_settled_ones(self):
        c = chains(covered({"button_y": release(remove("Cover"))}))
        self.assertIn(("Base", "P", "Cover"), c.stacks())
        self.assertIn(("Base", "P"), c.stacks())           # the cover lifted; no later step is needed to see it
        self.assertEqual([kind for kind, _ in c.stacks()[("Base", "P")].steps], ["step", "settle"])

    def test_added_lists_only_the_stacks_where_the_layer_was_just_added(self):
        # A's button_b removes A and adds it again above the cover. A was already on the stack before
        # that binding, so it doesn't count as newly added there (the old cover check used the same test).
        c = chains({"Base": {"switch": (SW, {"button_a": press(add("A"))})},
                    "A": {"switch": (SW, {"button_c": press(add("Cover")), "button_b": press(remove("A"), add("A"))})},
                    "Cover": {}}, arrivals=1)
        self.assertEqual(set(c.added("Cover")), {("Base", "A", "Cover")})
        self.assertIn(("Base", "Cover", "A"), c.stacks())
        self.assertEqual(set(c.added("A")), {("Base", "A")})


def beneath(layout, title, stacks):
    """The inputs that have a layer command somewhere under `title`, over these lower stacks."""
    found = set()
    for stack in stacks:
        routes, blocked = check_stack(layout, title, list(stack))
        found |= {(row["source"], row["input"]) for row in routes + blocked}
    return found


class NeptuneParityTests(unittest.TestCase):
    """Step 4: chains against the depth-5 search and the family walk, on both 90.9 layouts.

    These guarded the switch-over. Both older searches were deprecated on 2026-10-01, so the comparison
    is frozen: the 90.9 snapshots and the family rules of that day. It stays as the record that chains
    found everything the old searches did, and is not meant to follow later layouts.
    """
    HOLD_ONLY = {"LTP: Arrow Keys", "RTP: Mouse Buttons"}   # added by hold_layer only: out of scope (author)
    # Inputs chains report under the two Steering windows that neither old search can see, traced
    # 2026-10-01 (findings/2026-10-01-backward-chain-stacks/README.md, "Under the Steering windows").
    # Both come from a layer Base adds while Steering is already on: a ramp layer from the right
    # stick, or a left-pad key layer from a swipe. Not failures today: these windows aren't Always On yet.
    RAMPS = {"Gyro Off Ramp Up", "Turning Ramp Up 0", "Turning Ramp Up 1"}
    PAD_KEYS = {"Escape", "Enter", "Tab", "Backspace"}
    STEERING_ONLY = {
        "default": {("left_trigger", "edge"): RAMPS, ("right_trigger", "edge"): RAMPS,
                    ("left_trackpad", "touch"): PAD_KEYS},
        "alternative": {("left_trigger", "click"): RAMPS, ("right_trigger", "click"): RAMPS,
                        ("switch", "left_bumper"): RAMPS, ("switch", "right_bumper"): RAMPS,
                        ("left_trackpad", "touch"): PAD_KEYS},
    }

    @classmethod
    def setUpClass(cls):
        cls.cases = {}
        for variant in ("default", "alternative"):
            layout = Layout(json.loads(
                (ROOT / f"versions/neptune/90.9/single-set-{variant}_hold-gyro_90.9.json").read_text()))
            flow = {}
            walker = FlowWalker(layout)
            for family in families(layout, json.loads(FROZEN_RULES.read_text())).values():
                result = walker.walk(family)
                for title in result.layers():
                    flow.setdefault(title, set()).update(result.lower_stacks(title))
            steering = [t for t in layout.presets if t.startswith("Steering | LS") and t.endswith(": Double Tap")]
            cls.cases[variant] = (layout, Chains.of(layout), StackSpace.of(layout, 5), flow,
                                  always_on_layers(layout), steering)

    def test_every_window_has_a_stack(self):
        for variant, (layout, chains, _, _, windows, steering) in self.cases.items():
            self.assertEqual((len(windows), len(steering)), (7, 2), variant)
            for title in windows + steering:
                with self.subTest(variant=variant, window=title):
                    self.assertTrue(chains.below(title))

    def test_always_on_windows_match_the_depth_search_and_the_flow_walk(self):
        for variant, (layout, chains, space, flow, windows, _) in self.cases.items():
            for title in windows:
                with self.subTest(variant=variant, window=title):
                    old = beneath(layout, title, space.below(title)) | beneath(layout, title, flow[title])
                    self.assertEqual(beneath(layout, title, chains.below(title)), old)

    def test_steering_windows_find_everything_the_flow_walk_finds(self):
        # The depth search can't reach these (seven inputs from Base).
        for variant, (layout, chains, space, flow, _, steering) in self.cases.items():
            for title in steering:
                with self.subTest(variant=variant, window=title):
                    self.assertEqual(space.below(title), {})
                    new = beneath(layout, title, chains.below(title))
                    self.assertEqual(beneath(layout, title, flow[title]) - new, set())
                    expected = self.STEERING_ONLY[variant]
                    self.assertEqual(new - beneath(layout, title, flow[title]), set(expected))
                    providers = {}
                    for lower in chains.below(title):
                        routes, blocked = check_stack(layout, title, list(lower))
                        for row in routes + blocked:
                            providers.setdefault((row["source"], row["input"]), set()).add(row["from_layer"])
                    for key, allowed in expected.items():
                        self.assertLessEqual(providers[key], allowed, key)

    def test_chains_contain_every_flow_stack(self):
        for variant, (layout, chains, _, flow, _, _) in self.cases.items():
            missing = {title: len(stacks - set(chains.below(title)))
                       for title, stacks in flow.items() if stacks - set(chains.below(title))}
            with self.subTest(variant=variant):
                self.assertEqual(missing, {})
                unreached = {t for t in layout.presets if t != layout.base and not chains.reached(t)}
                self.assertEqual(unreached, set(self.HOLD_ONLY))

    def test_two_bystanders_find_the_same_inputs_as_one(self):
        # Guards the "one bystander at a time" default. Arrivals are off to keep this to a few seconds.
        for variant, (layout, _, _, _, windows, steering) in self.cases.items():
            chains = Chains(layout, arrivals=0)
            starts = {lower + (title,) for title in layout.presets if title != layout.base
                      for lower in chains.below(title)}
            for title in windows + steering:
                two = set(chains.below(title))
                for (own, _), why in chains.states[title].items():
                    for start in starts:
                        done = chains.replay(why, start)
                        if done and title in done:
                            two.add(done[:done.index(title)])
                with self.subTest(variant=variant, window=title):
                    self.assertEqual(beneath(layout, title, two), beneath(layout, title, chains.below(title)))


if __name__ == "__main__":
    unittest.main()
