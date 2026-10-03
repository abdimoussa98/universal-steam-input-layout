#!/usr/bin/env python3
"""The below/above table of measure.py for the archived multi-set layouts.

Those layouts repeat every layer title once per action set, so this script keys layers by
preset instead of by title and doesn't use the backward chains. A cleanup function here is a
press that only removes layers, sits beside a chord on the same input, stays interruptible
and isn't a delayed-apply reset. Hold to Repeat wasn't standard yet, so it isn't required.

    python3 findings/2026-10-02-cleanup-boundaries/measure_multiset.py archived/universal-layout-default__hold-gyro__latest.json [-v]

Read-only; run from the repo root.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, str(Path(__file__).parent))
from measure import BUTTONS, plus  # noqa: E402
from steam_layout.flow_model import chord_condition  # noqa: E402
from steam_layout.model import TARGET, actions, entries  # noqa: E402

path = sys.argv[1]
cm = json.loads(Path(path).read_text(encoding="utf-8"))["controller_mappings"]
order = list(cm["actions"]) + list(cm["action_layers"])
sets = set(cm["actions"])
title = {k: v["title"] for k, v in cm["actions"].items()}
title.update({k: f'{cm["actions"][v["parent_set_name"]]["title"]}/{v["title"]}' for k, v in cm["action_layers"].items()})
groups = {g["id"]: g for g in cm["group"]}
active = {p["name"]: {state.split(" ")[0]: groups[gid] for gid, state in p["group_source_bindings"].items()
                      if state.endswith(" active")} for p in cm["preset"]}
windows = {k for k, sources in active.items()
           if any(g.get("inputs", {}).get("always_on_action", {}).get("activators") for g in sources.values())}


def ops(entry):
    return [(m.group(1), order[int(m.group(2)) - 1]) for a in reversed(actions(entry)) if (m := TARGET.search(a))]


def guard(activators):
    out = set()
    for kind, entry in entries(activators):
        cond = chord_condition(entry.get("settings", {})) if kind == "chord" else None
        if cond and cond.known:
            for group in cond.groups:
                out |= {BUTTONS[c] for c in group if c in BUTTONS}
    return frozenset(out)


adds, adders = defaultdict(set), defaultdict(set)
cleanups, released = defaultdict(list), defaultdict(set)
for layer, sources in active.items():
    for source, group in sources.items():
        for inp, value in group.get("inputs", {}).items():
            activators = value.get("activators", {})
            listed = list(entries(activators))
            delayed = {t for _, e in listed if e.get("settings", {}).get("delay_start", "0") not in ("", "0")
                       for op, t in ops(e) if op == "add_layer"}
            for kind, entry in listed:
                found = ops(entry)
                for op, target in found:
                    if op in ("add_layer", "hold_layer") and target != layer:
                        adds[layer].add(target)
                        adders[target].add(layer)
                scope = frozenset(t for op, t in found if op == "remove_layer")
                if not scope:
                    continue
                if kind == "release":
                    if layer in scope:
                        released[layer].add(BUTTONS.get((source, inp), f"{source}/{inp}"))
                elif kind != "chord" and len(scope) == len(found) and any(k == "chord" for k, _ in listed) \
                        and entry.get("settings", {}).get("interruptable") != "0" and not scope <= delayed \
                        and (source, inp) != ("switch", "always_on_action"):
                    cleanups[layer].append((guard(activators), scope))


def keeper(layer):
    if layer in sets:
        return "mode", frozenset()
    if layer in windows:
        return "timer", frozenset()
    guards = set().union(*[g for g, _ in cleanups[layer]])
    keep = (released[layer] & guards) or released[layer] or guards
    return ("button", frozenset(keep)) if keep else ("other", frozenset())


counts, rows = Counter(), []
hosts = [layer for layer in active if cleanups[layer]]
for host in hosts:
    union = set().union(*[s for _, s in cleanups[host]])
    guards = set().union(*[g for g, _ in cleanups[host]])
    for kind, others in (("below", adders[host] - sets), ("above", adds[host])):
        for other in others:
            how, keep = keeper(other)
            same = how == "button" and keep <= guards
            many = kind == "above" and same and len(cleanups[other]) >= 5
            counts[kind, same, many, other in union] += 1
            rows.append(f"{'REMOVED' if other in union else 'left   '} {kind}: {title[other]} under/over {title[host]} "
                        f"(keeper {how} {plus(keep)}, guard {plus(guards)}, {len(cleanups[other])} own cleanups)")
total = sum(len(v) for v in cleanups.values())
print(path)
print(f"  layers {len(active) - len(sets)}, hosts {len(hosts)}, cleanup functions {total}, "
      f"of which remove their host {sum(1 for h in hosts for _, s in cleanups[h] if h in s)}")
print(f"  scope sizes: {dict(sorted(Counter(len(s) for v in cleanups.values() for _, s in v).items()))}")
print(f"  below, same keeper: removed {counts['below', True, False, True]}, left {counts['below', True, False, False]}")
print(f"  below, other keeper: removed {counts['below', False, False, True]}, left {counts['below', False, False, False]}")
print(f"  above, same keeper, 0 to 4 own cleanups: removed {counts['above', True, False, True]}, left {counts['above', True, False, False]}")
print(f"  above, same keeper, 5+ own cleanups: removed {counts['above', True, True, True]}, left {counts['above', True, True, False]}")
print(f"  above, other keeper: removed {counts['above', False, False, True]}, left {counts['above', False, False, False]}")
if "-v" in sys.argv:
    print("\n".join("  " + row for row in sorted(rows)))
