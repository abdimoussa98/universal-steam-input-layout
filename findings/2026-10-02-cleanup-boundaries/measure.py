#!/usr/bin/env python3
"""Measure what the cleanup functions remove, against one boundary rule.

A cleanup function is a guarded recovery (flow_model role "recovery"): a repeating,
interruptible removal that a chord with the owner's button suppresses. For each one:

    host      the layer that carries it
    guard     the buttons whose chords sit beside it on the same input
    scope     the layers it removes

    keeper(T) what keeps layer T alive:
                mode    a stateful layer (Gyro, Steering)
                timer   an Always On window
                button  the buttons whose Release removes T, confirmed by the guards of T's
                        own cleanup functions when it has both; else whichever it has
                other   none of these (a threshold or pressure exit)

The rule under test: a cleanup removes its host, plus every layer that can be on the stack
with the host (backward chains), is kept alive only by the guard's buttons, and leaves the
cleanup's input alone (a layer on top that binds the input fires its own binding instead).

    python3 findings/2026-10-02-cleanup-boundaries/measure.py summary
    python3 findings/2026-10-02-cleanup-boundaries/measure.py detail neptune/single-set-default_hold-gyro_latest.json
    python3 findings/2026-10-02-cleanup-boundaries/measure.py pairs  <layout>
    python3 findings/2026-10-02-cleanup-boundaries/measure.py above  <layout>

Read-only; run from the repo root. The multi-set layouts in archived/ repeat titles per
action set, so they have their own script (measure_multiset.py).
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, ".")
from steam_layout.chains import Chains  # noqa: E402
from steam_layout.flow_model import chord_condition, resolve  # noqa: E402
from steam_layout.model import EMPTY, LAYER_COMMAND, Layout, actions, always_on_layers, entries  # noqa: E402

BUTTONS = {("switch", "left_bumper"): "LB", ("switch", "right_bumper"): "RB",
           ("switch", "button_escape"): "Start", ("switch", "button_menu"): "Select",
           ("joystick", "touch"): "LSt", ("right_joystick", "touch"): "RSt",
           ("joystick", "click"): "L3", ("right_joystick", "click"): "R3",
           ("left_trigger", "click"): "LT", ("right_trigger", "click"): "RT",
           ("left_trigger", "edge"): "LT", ("right_trigger", "edge"): "RT",
           ("left_trackpad", "touch"): "LTP", ("right_trackpad", "touch"): "RTP"}
STATEFUL = ("Gyro", "Steering")
STICK_HELPERS = {f"{side}: {kind}" for side in ("LST", "RST") for kind in ("Entry Point", "Tap Cover", "Temporary Gyro")}
SNAPSHOTS = [("July reference", "findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json")] + \
    [(v, f"versions/neptune/{v}/single-set-default_hold-gyro_{v}.json") for v in ("90.4", "90.5", "90.6", "90.7", "90.8", "90.9")] + \
    [("90.10 default", "neptune/single-set-default_hold-gyro_latest.json"),
     ("90.10 alternative", "neptune/single-set-alternative_hold-gyro_latest.json")]


def name(control):
    return BUTTONS.get(control, f"{control[0]}/{control[1]}")


def plus(buttons):
    return "+".join(sorted(buttons)) or "-"


class Boundary:
    def __init__(self, path):
        self.layout = Layout(json.loads(Path(path).read_text(encoding="utf-8")))
        self.chains = Chains.of(self.layout)
        self.inv = self.chains.inventory
        self.windows = set(always_on_layers(self.layout))
        self.layers = [t for t in self.layout.presets if t != self.layout.base]
        self.adds, self.adders = defaultdict(set), defaultdict(set)
        for t in self.inv.transitions:
            for op, target in t.ops:
                if op in ("add_layer", "hold_layer") and target != t.layer:
                    self.adds[t.layer].add(target)
                    self.adders[target].add(t.layer)
        self._keeper = {}

    def guard(self, host, source, inp):
        """Buttons whose chord sits beside this input's entries (stick-deflection conditions dropped)."""
        acts = self.layout.active(host)[source]["inputs"][inp]["activators"]
        out = set()
        for kind, entry in entries(acts):
            cond = chord_condition(entry.get("settings", {})) if kind == "chord" else None
            if cond and cond.known:
                for group in cond.groups:
                    out |= {BUTTONS[c] for c in group if c in BUTTONS}
        return frozenset(out)

    def cleanups(self, host):
        """(transition, guard, scope) for each cleanup function of `host`."""
        for t in self.inv.by_layer(host):
            if t.role == "recovery":
                yield t, self.guard(host, t.source, t.input), frozenset(x for op, x in t.ops if op == "remove_layer")

    def keeper(self, layer):
        if layer not in self._keeper:
            if layer in STATEFUL:
                self._keeper[layer] = ("mode", frozenset())
            elif layer in self.windows:
                self._keeper[layer] = ("timer", frozenset())
            else:
                guards = set().union(*[g for _, g, _ in self.cleanups(layer)])
                released = {name(t.control) for t in self.inv.by_layer(layer)
                            if t.role == "release" and ("remove_layer", layer) in t.ops}
                keep = (released & guards) or released or guards
                self._keeper[layer] = ("button", frozenset(keep)) if keep else ("other", frozenset())
        return self._keeper[layer]

    def inside(self, layer, guard):
        kind, keep = self.keeper(layer)
        return kind == "button" and keep <= guard

    def clear_on(self, upper, host, source, inp):
        """True if `upper` on top of `host` still lets the host's binding on this input fire."""
        kind, layer, _, _ = resolve(self.layout, (host, upper), source, inp)
        return kind == "binding" and layer == host

    def judge(self, host):
        """One dict per cleanup function: each other layer as (verdict, position)."""
        below = set().union(*self.chains.below(host)) - {self.layout.base, host}
        above = set(self.chains.above(host))
        for t, guard, scope in self.cleanups(host):
            clear = {u for u in above if self.clear_on(u, host, t.source, t.input)}
            cells = {}
            for layer in (below | above | scope) - {host}:
                where = "below" if layer in below else "above, leaves the input alone" if layer in clear else \
                    "above, binds the input" if layer in above else "never on the stack with it"
                expected = where in ("below", "above, leaves the input alone") and self.inside(layer, guard)
                if expected:
                    cells[layer] = ("removed, expected" if layer in scope else "LEFT, expected", where)
                elif layer in scope:
                    cells[layer] = ("removed, not expected", where)
            yield {"input": name(t.control), "guard": guard, "scope": scope, "cells": cells}


def summary(snapshots):
    print("| Layout | Layers | Cleanup functions | Below, same keeper: removed / left | Below, other keeper: removed / left | "
          "Above, same keeper, 0 to 4 own cleanups: removed / left | Above, same keeper, 5+ own cleanups: removed / left | "
          "Above, other keeper: removed / left | Stateful, stick helpers, windows removed | Expected but left |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for label, path in snapshots:
        b = Boundary(path)
        c, total, left = Counter(), 0, 0
        for host in b.layers:
            found = list(b.cleanups(host))
            if not found:
                continue
            total += len(found)
            union = set().union(*[s for _, _, s in found])
            guard = set().union(*[g for _, g, _ in found])
            c["stateful"] += len(union & set(STATEFUL))
            c["helpers"] += len(union & STICK_HELPERS)
            c["windows"] += len(union & b.windows)
            for parent in b.adders[host] - {b.layout.base}:
                c["below", b.inside(parent, guard), parent in union] += 1
            for child in b.adds[host]:
                same = b.inside(child, guard)
                many = same and sum(1 for _ in b.cleanups(child)) >= 5
                c["above", same, many, child in union] += 1
            left += sum(1 for row in b.judge(host) for verdict, _ in row["cells"].values() if verdict == "LEFT, expected")
        print(f"| {label} | {len(b.layers)} | {total} | {c['below', True, True]} / {c['below', True, False]} | "
              f"{c['below', False, True]} / {c['below', False, False]} | "
              f"{c['above', True, False, True]} / {c['above', True, False, False]} | "
              f"{c['above', True, True, True]} / {c['above', True, True, False]} | "
              f"{c['above', False, False, True]} / {c['above', False, False, False]} | "
              f"{c['stateful']}, {c['helpers']}, {c['windows']} | {left} |")


def detail(path):
    b = Boundary(path)
    for host in b.layers:
        groups = defaultdict(lambda: defaultdict(list))
        for row in b.judge(host):
            for layer, (verdict, where) in row["cells"].items():
                if verdict != "removed, expected":
                    groups[verdict][f"{layer} ({where}; keeper {b.keeper(layer)[0]} {plus(b.keeper(layer)[1])}; "
                                    f"guard {plus(row['guard'])})"].append(row["input"])
        if groups:
            print(f"\n{host}")
            for verdict, items in sorted(groups.items()):
                print(f"  {verdict}:")
                for item, inputs in sorted(items.items()):
                    print(f"    {item} on {len(inputs)} input(s)")


def pairs(path):
    b = Boundary(path)
    for host in b.layers:
        found = list(b.cleanups(host))
        if not found:
            continue
        union = set().union(*[s for _, _, s in found])
        guard = set().union(*[g for _, g, _ in found])
        inputs = [(t.source, t.input) for t, _, _ in found]
        print(f"\n{host}  ({len(found)} cleanup functions, guard {plus(guard)})")
        for kind, others in (("below", b.adders[host] - {b.layout.base}), ("above", b.adds[host])):
            for other in sorted(others):
                how, keep = b.keeper(other)
                own = sum(1 for _ in b.cleanups(other))
                covered = sum(1 for s, i in inputs if not b.clear_on(other, host, s, i)) if kind == "above" else 0
                cover = f", binds {covered} of {len(inputs)} cleanup inputs" if kind == "above" else ""
                print(f"  {'REMOVED' if other in union else 'left   '} {kind}: {other}  "
                      f"(keeper {how} {plus(keep)}, {own} own cleanups{cover})")


def above(path):
    """What a layer of the same interaction, or a window, puts on an input that hosts a cleanup function below it."""
    b = Boundary(path)
    kinds, examples = Counter(), defaultdict(set)
    for host in b.layers:
        above = set(b.chains.above(host))
        for t, guard, scope in b.cleanups(host):
            for upper in above:
                how, keep = b.keeper(upper)
                same = how == "button" and (keep <= guard or b.keeper(host)[1] <= keep)
                if b.clear_on(upper, host, t.source, t.input) or not (same or upper in b.windows):
                    continue
                group = b.layout.active(upper).get(t.source)
                if group is None or not group.get("inputs", {}).get(t.input, {}).get("activators"):
                    what = "disables the source or changes its mode"
                else:
                    mine = [x for x in b.inv.by_layer(upper) if x.control == t.control]
                    commands = [c for _, e in entries(group["inputs"][t.input]["activators"]) for c in actions(e)]
                    own = [x for x in mine if x.role == "recovery"]
                    removed = {target for x in own for op, target in x.ops if op == "remove_layer"}
                    if own and host in removed:
                        what = "its own cleanup, which also removes the layer below"
                    elif own or any(x.role == "cancel" for x in mine):
                        what = "removes only itself, repeating (staged)"
                    elif all(c.startswith(EMPTY) for c in commands):
                        what = "cleared"
                    elif not any(LAYER_COMMAND.search(c) for c in commands):
                        what = "output only"
                    elif all(x.role == "release" for x in mine):
                        what = "a release only, no cleanup"
                    else:
                        what = "its own button: " + "/".join(sorted({x.role for x in mine}))
                key = ("window" if upper in b.windows else "layer", what)
                kinds[key] += 1
                examples[key].add(f"{upper} over {host} on {name(t.control)}")
    for key, count in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"{count:5}  {key[0]:7} {key[1]}")
        for example in sorted(examples[key])[:6]:
            print(f"         {example}")


if __name__ == "__main__":
    command, rest = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("summary", [])
    if command == "summary":
        summary([tuple(a.split("=", 1)) for a in rest] or SNAPSHOTS)
    elif command in ("detail", "pairs", "above") and rest:
        {"detail": detail, "pairs": pairs, "above": above}[command](rest[0])
    else:
        sys.exit(__doc__)
