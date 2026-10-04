"""Read-only: the walk with no limit on extra presses, until it settles or memory runs out.

From Base, fire every adding binding and every removal-only binding that answers on a stack, on every
stack, breadth first. Every stack gets the hidden-exit test. Nothing is written to disk except a short
progress log (counts only, no stacks). Stacks live in memory as bytes of layer numbers.

    python3 findings/2026-10-03-simultaneous-cap/measure_walk.py <layout.json> <memory cap in GB> [log file or -] [layers on at once]

The trial behind steam_layout/walk.py. Kept as the record of the measurements in README.md.
"""
import json
import os
import resource
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout.chains import Chains                        # noqa: E402
from steam_layout.cleanups import PADS, Cleanups, name        # noqa: E402
from steam_layout.flow_model import resolve                   # noqa: E402
from steam_layout.model import Layout, defined, entries       # noqa: E402
from steam_layout.stacks import apply_ops                     # noqa: E402

layout = Layout(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
CAP = float(sys.argv[2]) * 1024 ** 3
LOG = open(sys.argv[3], "a", buffering=1) if len(sys.argv) > 3 and sys.argv[3] != "-" else None
MAX_LAYERS = int(sys.argv[4]) if len(sys.argv) > 4 else None      # layers on at once, Base not counted
STOP = object()


def say(text):
    print(text, flush=True)
    if LOG:
        LOG.write(text + "\n")


titles = list(layout.presets)
ident = {t: i for i, t in enumerate(titles)}
BASE = ident[layout.base]
controls = {}                                   # (source, input) -> small number


def cid(source, inp):
    return controls.setdefault((source, inp), len(controls))


# Per layer: its groups as (source, mode or None when disabled, the inputs it binds).
groups = []
carries = {}                                    # (layer, control) -> layers any entry on that input removes
for t in titles:
    rows = []
    for source, group in layout.active(t).items():
        if group["mode"] == "disabled":
            rows.append((source, None, ()))
            continue
        bound = []
        for inp, value in group.get("inputs", {}).items():
            if not defined(group, inp):
                continue
            c = cid(source, inp)
            bound.append(c)
            removed = {ident[x] for _, e in entries(value["activators"]) for op, x in layout.layer_ops(e)
                       if op == "remove_layer" and x in ident}
            if removed:
                carries[(ident[t], c)] = frozenset(removed)
        rows.append((source, group["mode"], tuple(bound)))
    groups.append(tuple(rows))

chains = Chains(layout)
moves = [[] for _ in titles]                    # per layer: (control, ops) of every binding the walk follows
for table in (chains._adding, chains._removing):
    for t, found in table.items():
        for tr in found:
            ops = tuple((op != "remove_layer", ident[x]) for op, x in tr.ops)
            moves[ident[t]].append((cid(tr.source, tr.input), ops, tr))

cleanups = Cleanups(layout)
exits = {ident[l]: [(cid(*c), c) for c in cleanups.keeper_exits(l, f)]
         for l in cleanups.layers if (f := cleanups.exits(l))}
pads = {ident[t] for t in cleanups.touchpad_layers()}
today = {(ident[u], ident[l]) for (u, l), row in cleanups.covered_exits().items() if row["hidden"] and u in ident}


def answers(stack):
    """{control: the layer that answers it} on a stack (flow_model.resolve, for every input at once)."""
    found, state = {}, {}
    for layer in reversed(stack):
        for source, mode, bound in groups[layer]:
            seen = state.get(source)
            if seen is STOP:
                continue
            if mode is None:
                state[source] = STOP
                continue
            if seen is None:
                state[source] = mode
            elif seen != mode:
                state[source] = STOP
                continue
            for c in bound:
                if c not in found:
                    found[c] = layer
    return found


def successors(stack, found):
    out = []
    for layer in stack:
        for c, ops, _ in moves[layer]:
            if found.get(c) != layer:
                continue
            new = list(stack)
            for add, target in ops:
                if add:
                    if target not in new:
                        new.append(target)
                elif target != BASE and target in new:
                    new.remove(target)
            if MAX_LAYERS is None or len(new) - 1 <= MAX_LAYERS:
                out.append(bytes(new))
    return out


def lost(stack, found):
    """(culprit, lower, control) for every keeper exit in the stack that its layer doesn't answer and nobody carries."""
    out = []
    for at, lower in enumerate(stack):
        for c, control in exits.get(lower, ()):
            who = found.get(c)
            if who == lower:
                continue
            if who is not None:
                if lower in carries.get((who, c), ()):
                    continue
            else:
                mine = next(mode for source, mode, _ in groups[lower] if source == control[0])
                who = next((x for x in stack[at + 1:] for source, mode, _ in groups[x]
                            if source == control[0] and mode != mine), stack[-1])
            out.append((who, lower, control))
    return out


def self_check(limit=3000):
    """The fast lookup against the repo's own resolve and apply_ops, on the first stacks of the walk."""
    seen, todo, checked = {bytes([BASE])}, [bytes([BASE])], 0
    while todo and checked < limit:
        stack = todo.pop(0)
        found = answers(stack)
        named = tuple(titles[i] for i in stack)
        slow = []
        for layer in named:
            for tr in list(chains._adding.get(layer, ())) + list(chains._removing.get(layer, ())):
                if chains.fires(tr, named):
                    slow.append(bytes(ident[x] for x in apply_ops(named, tr.ops, layout.base)))
        fast = successors(stack, found)
        assert sorted(fast) == sorted(slow), named
        for lower in named:
            for c, control in exits.get(ident[lower], ()):
                kind, layer, acts, _ = resolve(layout, named, *control)
                ok = (kind == "binding" and layer == lower) or bool(
                    acts and any(("remove_layer", lower) in layout.layer_ops(e) for _, e in entries(acts)))
                mine = not any(l == ident[lower] and cc == control for _, l, cc in lost(stack, found))
                assert ok == mine, (named, lower, control)
        checked += 1
        for new in fast:
            if new not in seen:
                seen.add(new)
                todo.append(new)
    return checked


def rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss      # bytes on macOS (peak)


def main():
    say(f"{layout.cm['title']}: {len(titles)} layers, memory cap {CAP / 1024 ** 3:.1f} GB, at most {MAX_LAYERS} layers on at once")
    if MAX_LAYERS is None:
        say(f"self-check: {self_check()} stacks agree with the repo's own lookup")
    start = bytes([BASE])
    seen = {start}
    frontier, depth, pairs, tested, longest = [start], 0, {}, 0, 1
    began = time.perf_counter()
    stopped = None
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
    try:
        while frontier and not stopped:
            new, fresh, done = [], 0, 0
            for stack in frontier:
                found = answers(stack)
                for who, lower, control in lost(stack, found):
                    if (who, lower) not in pairs:
                        pairs[(who, lower)] = (depth, control, stack)
                        fresh += 1
                for nxt in successors(stack, found):
                    if nxt not in seen:
                        seen.add(nxt)
                        new.append(nxt)
                        if len(nxt) > longest:
                            longest = len(nxt)
                done += 1
                tested += 1
                if tested % 250000 == 0:
                    used = rss()
                    if used > CAP:
                        stopped = (f"memory cap reached inside depth {depth}: {done} of {len(frontier)} "
                                   f"stacks of this depth were tested")
                        break
                    if tested % 2000000 == 0:
                        say(f"    ... {tested:,} tested, {len(seen):,} known, {used / 1024 ** 3:.1f} GB, "
                            f"{time.perf_counter() - began:.0f} s")
            say(f"  depth {depth:>2}: {done:>11,} stacks tested, {len(new):>11,} new, {len(seen):>12,} known, "
                f"{fresh:>3} new pairs, {rss() / 1024 ** 3:5.1f} GB, {time.perf_counter() - began:6.0f} s")
            if not stopped:
                frontier, depth = new, depth + 1
    except KeyboardInterrupt:
        stopped = f"interrupted inside depth {depth}"
    say("RESULT: " + (stopped or f"FIXED POINT. The walk settled: no new stack after depth {depth - 1}"))
    say(f"  stacks known {len(seen):,}; tested {tested:,}; longest stack {longest} layers; "
        f"distinct sets of layers {len({frozenset(s) for s in seen}):,}; peak memory {rss() / 1024 ** 3:.1f} GB; "
        f"{time.perf_counter() - began:.0f} s")
    new_pairs = {p: v for p, v in pairs.items() if p not in today}
    aside = {p for p, (_, control, _) in new_pairs.items() if p[0] in pads or p[1] in pads or control[0] in PADS}
    say(f"  pairs on a keeper's exit: {len(pairs)} found; {len(today)} are in today's audit; "
        f"{len(new_pairs)} are new ({len(aside)} under the touchpad exception, {len(new_pairs) - len(aside)} would fail)")
    missing = today - set(pairs)
    if missing:
        say(f"  in today's audit but not met by this walk: {len(missing)}")
    by_depth = {}
    for p, (d, _, _) in new_pairs.items():
        by_depth.setdefault(d, [0, 0])[0 if p in aside else 1] += 1
    for d in sorted(by_depth):
        say(f"    first seen at depth {d}: {by_depth[d][0]} touchpad, {by_depth[d][1]} would fail")
    for p in sorted(set(new_pairs) - aside, key=lambda p: (new_pairs[p][0], titles[p[0]], titles[p[1]])):
        d, control, stack = new_pairs[p]
        say(f"    WOULD FAIL (depth {d}) {titles[p[0]]} over {titles[p[1]]} [{name(control)}]: "
            + " > ".join(titles[i] for i in stack))
    for p in sorted(aside, key=lambda p: (new_pairs[p][0], titles[p[0]], titles[p[1]])):
        d, control, stack = new_pairs[p]
        say(f"    touchpad (depth {d}) {titles[p[0]]} over {titles[p[1]]} [{name(control)}]: "
            + " > ".join(titles[i] for i in stack))


if __name__ == "__main__":
    main()
