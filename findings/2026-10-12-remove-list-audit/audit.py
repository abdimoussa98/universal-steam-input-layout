"""Is every remove needed? Each remove of the working layouts, judged three ways.

    PYTHONPATH=.:tests:findings/2026-10-12-remove-list-audit python3 findings/2026-10-12-remove-list-audit/audit.py [walks per seed] [seeds]

Read-only. For every bind that removes layers, and every layer it names:

    rules     what the bind is (the tools' role for it) and whether a rule fixes its list: the layer itself, a
              timer's reset (R120), the layer's own hold target in one of its Releases (the hold recipe, R120
              to R122), a stick touch Release's three helpers (R123), or, for a cleanup function, whether the
              Cleanup audit would ask for the remove if it were missing (R128, R129)
    chains    can the layer be on the stack with the bind's layer at all (the backward chains, which the
              Cleanup audit's "never there" uses), and is it only ever above it. They follow no chord, no
              delayed add and no `hold_layer`
    walks     random press sequences over the whole pad (walk.py): how often the bind fired, how often the
              layer was on the stack at that moment, and how often it was under the bind's layer when that
              layer was added

A remove gets one verdict:

    needed         the layer was on the stack at least once when the bind fired
    never there    the chains say the two are never on the stack together, and in at least 30 firings the
                   walks never met it
    answers first  the layer binds the bind's own input and is only ever above the bind's layer (chains; the
                   walks never met it under that layer, nor on the stack when the bind fired). While it is on,
                   it answers the input and the bind does not run (A1). This is R132 as tightened in 90.57
    not shown      possible by the chains, not met by the walks; or the bind fired under 30 times

Writes `removes-<variant>.json` (one row per remove) and prints the tables of the record.
"""
import json
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

from steam_layout import exceptions
from steam_layout.cleanups import Cleanups, kept, release_of
from steam_layout.model import Layout
import scenario
import walk

HERE = Path(__file__).resolve().parent
MISSED = (0.0, 0.10)
TRIO = {"joystick": ("LST: Entry Point", "LST: Tap Cover", "LST: Temporary Gyro"),
        "right_joystick": ("RST: Entry Point", "RST: Tap Cover", "RST: Temporary Gyro")}
ENOUGH = 30                                   # firings before "never on the stack" counts as evidence
VERDICTS = ("needed", "never there", "answers first", "not shown")


def static_rows(variant, data):
    """One row per remove, with the rule and the chains' answers. The walks' counts come later."""
    layout = Layout(data)
    c = Cleanups(layout)
    keep = kept(exceptions.load_config(), variant, set(layout.presets), release_of(layout.cm.get("title")))
    held = {t for host in layout.presets for x in c.inv.by_layer(host) for op, t in x.ops if op == "hold_layer"}
    rows = []
    for host in layout.presets:
        base = host == c.base
        present = None if base else c.present(host)
        below = set() if base else c.below(host)
        holds = {x for t in c.inv.by_layer(host) if t.role == "hold" for op, x in t.ops if op == "add_layer"}
        for t in c.inv.by_layer(host):
            removed = [x for op, x in t.ops if op == "remove_layer"]
            if not removed:
                continue
            required = None
            if t.role == "recovery":
                required = {x for x, _ in c.left(host, t, c.guard(host, t.source, t.input), frozenset())} | {host}
            clear = t.role != "recovery" and c.is_clear(removed)
            for target in dict.fromkeys(removed):
                if target == host:
                    rule = "its own layer"
                elif t.role == "reset":
                    rule = "a timer's reset (R120)"
                elif t.role == "release" and t.input == "touch" and target in TRIO.get(t.source, ()):
                    rule = "a stick touch Release's helper (R123)"
                elif t.role == "release" and target in holds:
                    rule = "the layer's own hold target, in a Release (R120 to R122)"
                elif (host, target) in keep:
                    rule = "kept by a register entry (R132)"
                elif required is not None:
                    rule = "a cleanup function: required (R128, R129)" if target in required else \
                        "a cleanup function: allowed, not required"
                elif clear:
                    rule = "a whole-stack clear (R163)"
                else:
                    rule = "no rule fixes it"
                rows.append({"layer": host, "input": f"{t.source}/{t.input}", "kind": t.activator, "index": t.index,
                             "role": t.role, "size": len(removed), "target": target, "rule": rule,
                             "chains": base or target in present,
                             "above only": target != host and target not in below and (base or target in c.above(host)),
                             "answers": target != host and not c.leaves_alone(target, host, t.source, t.input),
                             "hold_layer": target in held})
    return rows


def judge(row):
    if row["target"] == row["layer"] or row["on"]:
        return "needed"
    if row["hold_layer"]:
        return "not shown"                    # the chains and the simulator's walks both miss `hold_layer` stacks
    if row["answers"] and row["above only"] and not row["under"]:
        return "answers first"
    if not row["chains"] and row["fired"] >= ENOUGH:
        return "never there"
    return "not shown"


def table(rows, by, title):
    print(f"\n{title}")
    groups = defaultdict(Counter)
    for row in rows:
        groups[by(row)][row["verdict"]] += 1
    print("  " + " | ".join(["group", "removes", *VERDICTS]))
    for name in sorted(groups, key=lambda n: (-n if isinstance(n, int) else 0, str(n))):
        found = groups[name]
        print("  " + " | ".join([str(name), str(sum(found.values())), *[str(found[v]) for v in VERDICTS]]))
    total = Counter(row["verdict"] for row in rows)
    print("  " + " | ".join(["all", str(len(rows)), *[str(total[v]) for v in VERDICTS]]))


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    for variant in scenario.VARIANTS:
        data = scenario.layout_data(variant)
        rows = static_rows(variant, data)
        pairs = defaultdict(set)
        for row in rows:
            if row["target"] != row["layer"]:
                pairs[row["layer"]].add(row["target"])
        pairs = {host: sorted(targets) for host, targets in pairs.items()}
        with Pool() as pool:
            found = pool.map(walk.batch, [(variant, "working", data, seed, count, missed, pairs)
                                          for missed in MISSED for seed in range(1, seeds + 1)])
        fired, on, modes, ends, added, under = Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
        for _, _, _, f, o, m, e, _, a, u, _ in found:
            fired.update(f); on.update(o); modes.update(m); ends.update(e); added.update(a); under.update(u)
        for row in rows:
            source, name = row["input"].split("/")
            key = (row["layer"], (source, name), row["kind"], row["index"])
            row["fired"], row["on"] = fired[key], on[(*key, row["target"])]
            row["host added"], row["under"] = added[row["layer"]], under[(row["layer"], row["target"])]
            row["verdict"] = judge(row)
        (HERE / f"removes-{variant}.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        binds = {(r["layer"], r["input"], r["kind"], r["index"]) for r in rows}
        print(f"\n===== {variant}: {Layout(data).cm['title']}")
        print(f"{count * seeds * len(MISSED)} walks of {walk.EVENTS} events, half with one release in ten missed: {dict(ends)}")
        print("bind firings by mode on the stack: " + ", ".join(f"{m} {modes[m]}" for m in walk.MODES))
        print(f"{len(rows)} removes in {len(binds)} binds; binds that fired: "
              f"{len({(r['layer'], r['input'], r['kind'], r['index']) for r in rows if r['fired']})}")
        top = sorted({r["size"] for r in rows}, reverse=True)[:10]
        table([r for r in rows if r["size"] in top], lambda r: r["size"], "The ten largest sizes, by size")
        table(rows, lambda r: r["rule"], "Every remove, by what fixes it")
        table(rows, lambda r: r["role"], "Every remove, by the bind's role")
        # Where the two lines of evidence disagree.
        odd = [r for r in rows if r["on"] and not r["chains"]]
        print(f"\nMet on the stack although the chains say never ({len(odd)} removes): "
              + ", ".join(f"{t} ({n})" for t, n in Counter(r["target"] for r in odd).most_common(12)))
        wrong = [r for r in rows if r["on"] and r["answers"] and r["above only"]]
        print(f"Met on the stack although it answers the input and the chains put it only above ({len(wrong)} removes): "
              + ", ".join(f"{r['layer']} | {r['input']} {r['kind']} -> {r['target']}" for r in wrong[:8]))
        lower = [r for r in rows if r["under"] and r["answers"] and r["above only"]]
        print(f"Met under its host although the chains put it only above ({len(lower)} removes): "
              + ", ".join(sorted({f"{r['target']} under {r['layer']}" for r in lower})[:8]))
        first = [r for r in rows if r["verdict"] == "answers first"]
        print(f"\n\"answers first\": {len(first)} removes in {len({(r['layer'], r['input'], r['kind'], r['index']) for r in first})} binds; "
              f"their binds fired {sum(r['fired'] for r in first)} times with the layer never on")
        groups = Counter((r["layer"], r["target"]) for r in first)
        for (layer, target), number in sorted(groups.items(), key=lambda item: (-item[1], item[0])):
            print(f"    {number:3d}  {layer} names {target}")
        clears = defaultdict(list)
        for row in rows:
            if row["size"] == top[0]:
                clears[(row["layer"], row["input"], row["kind"])].append(row)
        print(f"\nThe {len(clears)} binds of {top[0]} removes:")
        for (layer, control, kind), found_rows in clears.items():
            tally = Counter(r["verdict"] for r in found_rows)
            print(f"  {layer} | {control} {kind}: fired {found_rows[0]['fired']}; "
                  + ", ".join(f"{v} {tally[v]}" for v in VERDICTS))


if __name__ == "__main__":
    main()
