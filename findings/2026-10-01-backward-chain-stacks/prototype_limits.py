"""Prototype 2: three attempted fixes for the limits in README.md. A throwaway experiment, not a tool.

    arrivals    0/1/2  layers that land between two chain steps (a Tap Cover on its Entry Point)
    chords      0/1    track which buttons the chain has pressed and released, and reject impossible chords
    bystanders  1/2    a bystander that has its own bystander underneath

Run from the repo root (results are in README.md, "Fixing the limits"):
    python3 findings/2026-10-01-backward-chain-stacks/prototype_limits.py default 1 0 1     # about 4 s
    python3 findings/2026-10-01-backward-chain-stacks/prototype_limits.py default 1 1 1     # about 70 s
"""
import json, sys, time
sys.path.insert(0, '.')
from steam_layout.model import Layout, always_on_layers
from steam_layout.flow_model import Inventory
from steam_layout.flow_paths import FlowWalker, families, load_config
from steam_layout.inheritance import check_stack
from steam_layout.stacks import StackSpace, apply_ops, definer

variant, ARRIVALS, CHORDS, BYSTANDERS = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
# Frozen inputs: the 90.9 layouts and the family rules of that day (the family walk is deprecated).
layout = Layout(json.load(open(f'versions/neptune/90.9/single-set-{variant}_hold-gyro_90.9.json')))
FROZEN_RULES = json.load(open('tests/data/flow_families_90.9.json'))
inv = Inventory.of(layout)
SKIP = ('recovery', 'reset', 'legacy-hold', 'mode-shift')
adding = [t for t in inv.transitions if t.role not in SKIP and any(op == 'add_layer' for op, _ in t.ops)]
adders = {}
for t in adding:
    for op, target in t.ops:
        if op == 'add_layer': adders.setdefault(target, []).append(t)
removers = [t for t in inv.transitions if t.role == 'center' and all(op == 'remove_layer' for op, _ in t.ops)]

def fires(t, stack):
    if t.layer not in stack: return False
    f = definer(layout, stack, t.source, t.input)
    return bool(f) and f[0] == t.layer

def held_after(t, held):
    """Held-button bookkeeping along a chain. None = the step is impossible.
    held: {control: True (pressed by the chain) / False (released by the chain)}; a control the chain never touched is unknown."""
    if not CHORDS: return held
    held = dict(held)
    if t.condition is not None and t.condition.known:
        need = t.condition.controls()
        released = [c for c in need if held.get(c) is False]
        # an "all" chord needs every control; an "any" chord needs one that the chain hasn't released
        if (t.condition.mode == 'all' and released) or (t.condition.mode != 'all' and len(released) == len(need)):
            return None
    if t.event == 'release':
        if held.get(t.control) is False: return None       # released twice with no press in between
        held[t.control] = False
    elif t.event in ('press', 'hold') and t.source != 'switch' or t.event in ('press', 'hold'):
        if t.control[1] != 'always_on_action': held[t.control] = True
    return tuple(sorted(held.items())) and held

def settle(states):
    out = dict(states); todo = list(states)
    while todo:
        key = todo.pop(); stack, used, held = key
        for t in removers:
            if fires(t, stack):
                new = (apply_ops(stack, t.ops, layout.base), used, held)
                if new not in out: out[new] = out[key] + (t,); todo.append(new)
    return out

def arrive(states, x):
    out = dict(states)
    for (stack, used, held), path in states.items():
        if used >= ARRIVALS: continue
        for t in adding:
            if any(op == 'add_layer' and target == x for op, target in t.ops) or not fires(t, stack): continue
            h = held_after(t, dict(held))
            if h is None: continue
            new = apply_ops(stack, t.ops, layout.base)
            if new != stack: out.setdefault((new, used + 1, tuple(sorted(h.items()))), path + (t,))
    return out

memo = {}
def chains(x, visiting=()):
    if x == layout.base: return {((x,), 0, ()): ()}
    if x in memo: return memo[x]
    if x in visiting: return {}
    out = {}
    for t in adders.get(x, []):
        before = settle(arrive(settle(chains(t.layer, visiting + (x,))), x))
        for (stack, used, held), path in before.items():
            if not fires(t, stack): continue
            h = held_after(t, dict(held))
            if h is None: continue
            new = apply_ops(stack, t.ops, layout.base)
            if x in new: out.setdefault((new, used, tuple(sorted(h.items()))), path + (t,))
    if not visiting: memo[x] = out
    return out

def replay(path, stack):
    for t in path:
        if not fires(t, stack): return None
        stack = apply_ops(stack, t.ops, layout.base)
    return stack

def own(x):
    return {stack: path for (stack, _, _), path in chains(x).items()}

def below(x, depth=BYSTANDERS):
    out = {}
    starts = {y: set(own(y)) for y in layout.presets if y != layout.base}
    if depth >= 2:   # a bystander that itself has a bystander underneath
        for y in list(starts):
            for ystack, ypath in own(y).items():
                for z in layout.presets:
                    if z == layout.base or z in ystack: continue
                    for zstack in own(z):
                        done = replay(ypath, zstack)
                        if done and y in done and z in done: starts[y].add(done)
    for stack, path in own(x).items():
        out.setdefault(stack[:stack.index(x)], None)
        for y, ystacks in starts.items():
            if y in stack: continue
            for ystack in ystacks:
                done = replay(path, ystack)
                if done and x in done and y in done[:done.index(x)]:
                    out.setdefault(done[:done.index(x)], y)
    return out

def keys(w, stacks):
    out = set()
    for s in stacks:
        routes, blocked = check_stack(layout, w, list(s))
        out |= {(r['source'], r['input']) for r in routes + blocked}
    return out

t0 = time.time()
targets = always_on_layers(layout) + [t for t in layout.presets if t.startswith('Steering | LS') and t.endswith(': Double Tap')]
low = {x: below(x) for x in layout.presets if x != layout.base}
secs = time.time() - t0
space = StackSpace.of(layout, 5)
walker = FlowWalker(layout); flow = {}
for f in families(layout, FROZEN_RULES).values():
    r = walker.walk(f)
    for x in r.layers(): flow.setdefault(x, set()).update(r.lower_stacks(x))
bad = []
for w in targets:
    b, d, f = keys(w, low[w]), keys(w, space.below(w)), keys(w, flow.get(w, ()))
    if (d | f) - b or b - d - f: bad.append((w, sorted((d | f) - b)[:4], sorted(b - d - f)[:4]))
lacking = {x: len(flow.get(x, set()) - set(low[x])) for x in low if flow.get(x, set()) - set(low[x])}
print(f'{variant} arrivals={ARRIVALS} chords={CHORDS} bystanders={BYSTANDERS}: {secs:.2f}s, total stacks {sum(len(v) for v in low.values())}, '
      f'chain states {sum(len(v) for v in memo.values())}')
print('   windows not exact (missed, extra):', bad or 'none - all 9 exact')
print('   layers lacking flow stacks:', lacking or 'none')
