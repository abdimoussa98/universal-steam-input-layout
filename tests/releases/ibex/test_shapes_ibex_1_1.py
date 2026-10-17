"""Ibex 1.1 against Ibex 1.0: the shape of the hand-over and of the merged chords.

The record is findings/2026-10-16-fn-right-stick-owner/README.md; the plan is
plans/2026-10-16-fn-right-stick-owner.md, parts 3 and 4.

- Every bind that adds an Fn layer removes its Entry Point after its adds; the stick clicks' two presses also
  remove both stick guards and the Tap Cover.
- Each Fn layer's two click Releases are its Entry Point's 1.0 Releases, command for command, less the removes of
  the Entry Point, the guards and the Tap Cover, which can no longer be under Fn (the cleanup_lists fix took them).
- Each Fn layer's two trackpad groups are copies of its Entry Point's.
- Each merged chord fires exactly when one of the two it replaced did, for every combination of their buttons.

Source: the frozen snapshots versions/ibex/1.0 and versions/ibex/1.1, both variants, read-only.
Fixture responsibility: releases/ibex. See docs/testing.md.
"""
from itertools import chain, combinations
import json
import unittest

from steam_layout import controllers, convert
from steam_layout.flow_model import chord_condition
from steam_layout.model import Layout, entries
from tests.support.sources import load_json

FN = {"Menu Left: Fn Layer": "Menu Left: Entry Point", "Menu Right: Fn Layer": "Menu Right: Entry Point",
      "Stateful | Menu Left: Fn Layer": "Stateful | Menu Left: Entry Point",
      "Stateful | Menu Right: Fn Layer": "Stateful | Menu Right: Entry Point"}
GONE = ("Menu Buttons: Left Stick Guard", "Menu Buttons: Right Stick Guard", "Menu Buttons: Tap Cover")
CHORD_KEYS = ("chord_button", convert.MASK, convert.ANY_OR_ALL)


def snapshot(version, variant):
    return Layout(convert.readable(load_json(controllers.IBEX.snapshot(variant, version))))


def chords(layout, title, source, name):
    group = layout.active(title).get(source) or {}
    value = (group.get("inputs") or {}).get(name) or {}
    return [entry for kind, entry in entries(value.get("activators") or {}) if kind == "chord"]


def shape(entry):
    settings = entry.get("settings") or {}
    return json.dumps([entry.get("bindings"), {k: v for k, v in settings.items() if k not in CHORD_KEYS}])


class HandOver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = {variant: (snapshot("1.0", variant), snapshot("1.1", variant)) for variant in controllers.VARIANTS}

    def test_every_fn_adder_removes_its_entry_point_after_its_adds(self):
        for variant, (_, after) in self.pairs.items():
            for fn, ep in FN.items():
                found = []
                for source, group in after.active(ep).items():
                    for name, value in (group.get("inputs") or {}).items():
                        for kind, entry in entries(value.get("activators") or {}):
                            ops = after.layer_ops(entry)
                            if ("add_layer", fn) not in ops:
                                continue
                            found.append(f"{source}/{name}")
                            last_add = max(i for i, (op, _) in enumerate(ops) if op == "add_layer")
                            removed = {t for op, t in ops[last_add + 1:] if op == "remove_layer"}
                            with self.subTest(variant, adder=f"{ep} {source}/{name} {kind}"):
                                self.assertIn(ep, removed)
                                if name == "click":
                                    self.assertEqual(entry["settings"], {"hold_repeats": "1", "repeat_rate": "50",
                                                                         "haptic_intensity": "0", "interruptable": "0"})
                                    self.assertLessEqual(set(GONE), removed)
                with self.subTest(variant, layer=fn):
                    self.assertEqual(sorted(found), ["joystick/click", "joystick/touch", "right_joystick/click",
                                                     "right_joystick/touch", "switch/button_escape", "switch/button_menu"])

    def test_the_fn_click_releases_are_the_entry_points_less_what_can_no_longer_be_under_fn(self):
        for variant, (before, after) in self.pairs.items():
            for fn, ep in FN.items():
                for stick in ("joystick", "right_joystick"):
                    old = before.active(ep)[stick]["inputs"]["click"]["activators"]["release"]
                    new = after.active(fn)[stick]["inputs"]["click"]["activators"]["release"]
                    expected = [(op, t) for op, t in before.layer_ops(old) if not (op == "remove_layer" and t in (ep, *GONE))]
                    with self.subTest(variant, layer=fn, stick=stick):
                        self.assertEqual(after.layer_ops(new), expected)
                        self.assertEqual(new.get("settings"), old.get("settings"))

    def test_each_fn_layer_has_copies_of_its_entry_points_trackpad_groups(self):
        for variant, (before, after) in self.pairs.items():
            for fn, ep in FN.items():
                for pad in ("left_trackpad", "right_trackpad"):
                    copy, model = after.active(fn)[pad], before.active(ep)[pad]
                    with self.subTest(variant, layer=fn, pad=pad):
                        self.assertNotEqual(copy["id"], model["id"])
                        self.assertEqual({k: v for k, v in copy.items() if k != "id"},
                                         {k: v for k, v in model.items() if k != "id"})


class MergedChords(unittest.TestCase):
    def test_each_merged_chord_fires_exactly_when_one_of_the_two_it_replaced_did(self):
        for variant in controllers.VARIANTS:
            before, after = snapshot("1.0", variant), snapshot("1.1", variant)
            merged = 0
            for title in before.presets:
                for source, group in before.active(title).items():
                    for name in (group.get("inputs") or {}):
                        old = [e for e in chords(before, title, source, name) if "chord_button" in (e.get("settings") or {})]
                        by_shape = {}
                        for entry in old:
                            by_shape.setdefault(shape(entry), []).append(entry)
                        for key, pair in by_shape.items():
                            if len(pair) != 2:
                                continue
                            new = [e for e in chords(after, title, source, name) if shape(e) == key]
                            conditions = [chord_condition(e["settings"]) for e in pair]
                            controls = sorted(set().union(*(c.controls() for c in conditions)))
                            with self.subTest(variant, input=f"{title} / {source}/{name}"):
                                self.assertEqual(len(new), 1)
                                self.assertEqual(new[0]["settings"][convert.ANY_OR_ALL], "0")
                                one = chord_condition(new[0]["settings"])
                                for held in chain.from_iterable(combinations(controls, n) for n in range(len(controls) + 1)):
                                    self.assertEqual(one.satisfied(set(held)), any(c.satisfied(set(held)) for c in conditions),
                                                     held)
                            merged += 1
            self.assertEqual(merged, 84, variant)


if __name__ == "__main__":
    unittest.main()
