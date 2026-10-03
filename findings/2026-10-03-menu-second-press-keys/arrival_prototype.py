"""Prototype: let the hidden-exit check (R136) count a layer that lands through an arrival.

Today the check asks `chains.above(lower)`: the layers whose own chain, or one bystander replay of it,
has `lower` underneath. A layer that a lower layer's binding adds on a stack the walk already visited
(an arrival) is on top of everything in that stack too, but `above` doesn't read those stacks.

This takes every stack the walk visited, fires every adding binding that answers there, and runs the
check's own test on the result: is an exit on a lower layer's keeper now answered by another layer that
doesn't remove the lower layer there? It prints the pairs the current check doesn't have.

    python3 findings/2026-10-03-menu-second-press-keys/arrival_prototype.py [layout.json ...]

Read-only. It changes no audit. Record: README.md in this folder.
"""
import collections
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout.cleanups import PADS, Cleanups, name      # noqa: E402
from steam_layout.flow_model import resolve                 # noqa: E402
from steam_layout.model import Layout, entries              # noqa: E402
from steam_layout.stacks import apply_ops                   # noqa: E402

DEFAULT = [ROOT / f"versions/neptune/90.14/single-set-{v}_hold-gyro_90.14.json" for v in ("default", "alternative")] + \
          [ROOT / f"neptune/single-set-{v}_hold-gyro_latest.json" for v in ("default", "alternative")]


def arrival_pairs(cleanups):
    """{(upper, lower): (stack, binding, exit)} for every exit on a keeper that a layer landing by one more
    adding binding covers, on any stack the walk visited."""
    layout, chains, found = cleanups.layout, cleanups.chains, {}
    for stack in list(chains.stacks()):
        for t in (t for layer in stack for t in chains._adding.get(layer, ())):
            if not chains.fires(t, stack):
                continue
            full = apply_ops(stack, t.ops, layout.base)
            for upper in [x for op, x in t.ops if op == "add_layer" and x in full and x not in stack]:
                for lower in full[:full.index(upper)]:
                    if lower == layout.base or lower not in cleanups.layers:
                        continue
                    exits = cleanups.exits(lower)
                    for control in cleanups.keeper_exits(lower, exits) if exits else ():
                        kind, layer, acts, _ = resolve(layout, full, *control)
                        if kind == "binding" and layer == lower:
                            continue
                        if acts and any(("remove_layer", lower) in layout.layer_ops(e) for _, e in entries(acts)):
                            continue                # carried: the upper layer removes it there
                        found.setdefault((layer, lower), (full, t, control))
    return found


def main(paths):
    for path in paths:
        layout = Layout(json.loads(Path(path).read_text(encoding="utf-8")))
        cleanups = Cleanups(layout)
        today = {pair for pair, row in cleanups.covered_exits().items() if row["hidden"]}
        started = time.perf_counter()
        found = arrival_pairs(cleanups)
        seconds = time.perf_counter() - started
        new = {pair: row for pair, row in found.items() if pair not in today}
        pads = cleanups.touchpad_layers()
        aside = {pair for pair, (_, _, control) in new.items() if pair[0] in pads or pair[1] in pads or control[0] in PADS}
        print(f"{layout.cm['title']}: {len(cleanups.chains.stacks())} visited stacks, {seconds:.1f} s for the arrivals")
        print(f"  pairs on a keeper's exit today: {len(today)}; new with arrivals: {len(new)} "
              f"({len(aside)} under the touchpad exception, {len(new) - len(aside)} findings)")
        rows = collections.defaultdict(list)
        for (upper, lower), (full, t, control) in sorted(new.items()):
            if (upper, lower) not in aside:
                rows[upper].append(f"{lower} [{name(control)}], on {' > '.join(full)}; landed by {t.describe()}")
        for upper, lines in rows.items():
            print(f"  {upper} over:")
            for line in lines:
                print(f"    {line}")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
