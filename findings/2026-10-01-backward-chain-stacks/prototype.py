"""Prototype: backward adder chains, a settle step and the bystander check, for "what can be below X".

A throwaway experiment kept as the evidence for README.md in this folder; not a supported tool.
The plan to build the real one is plans/2026-10-01-backward-chain-audit.md.

chains(X)   every way X gets added, followed back to the action set (who adds X, who adds that layer, ...).
            A step counts only if its layer answers that input on the stack so far.
settle      between two adds, the stack may shrink through removal-only bindings (a cover lifting at
            stick centre).
below(X)    X's own chain stacks, plus each other layer's chain stack placed underneath when X's chain
            still replays on top of it: no step intercepted, and the layer not removed.

It then compares the inputs that have a layer command beneath each window with the depth-5 search and
the intended-flow stacks, and prints "above" as the inverse of "below" for three layers.

Run from the repo root:
    python3 findings/2026-10-01-backward-chain-stacks/prototype.py [default|alternative] [settle roles]
"""
import json, sys, time
sys.path.insert(0, '.')
from steam_layout.model import Layout, always_on_layers
from steam_layout.flow_model import Inventory
from steam_layout.flow_paths import FlowWalker, families, load_config
from steam_layout.inheritance import check_stack
from steam_layout.stacks import StackSpace, apply_ops, definer

variant = sys.argv[1] if len(sys.argv) > 1 else 'default'
# Frozen inputs: the 90.9 layouts and the family rules of that day (the family walk is deprecated).
layout = Layout(json.load(open(f'versions/neptune/90.9/single-set-{variant}_hold-gyro_90.9.json')))
FROZEN_RULES = json.load(open('tests/data/flow_families_90.9.json'))
inv = Inventory.of(layout)
adders = {}
for t in inv.transitions:
    if any(op == 'add_layer' for op, _ in t.ops) and t.role not in ('recovery', 'reset', 'legacy-hold', 'mode-shift'):
        for op, target in t.ops:
            if op == 'add_layer':
                adders.setdefault(target, []).append(t)

SETTLE_ROLES = tuple(sys.argv[2].split(',')) if len(sys.argv) > 2 else ('center',)
removers = [t for t in inv.transitions if t.role in SETTLE_ROLES and all(op == 'remove_layer' for op, _ in t.ops)]

def settle(stack, path):
    """The stack plus every stack it can shrink to through removal-only bindings (a cover lifting at stick
    centre, for example). Adds are only ever followed along the chain."""
    seen = {stack: path}
    todo = [stack]
    while todo:
        cur = todo.pop()
        for t in removers:
            if t.layer in cur:
                found = definer(layout, cur, t.source, t.input)
                if found and found[0] == t.layer:
                    new = apply_ops(cur, t.ops, layout.base)
                    if new not in seen:
                        seen[new] = seen[cur] + (t,)
                        todo.append(new)
    return seen

memo = {}
def chains(x, visiting=()):
    """{full stack right after x was added: the transitions that built it}, following adders back to the action set.

    A step only counts if its layer is the one that answers that input on the stack so far: a layer the
    previous step put on top (a cover, a Modifier 2) intercepts it.
    """
    if x == layout.base:
        return {(x,): ()}
    if x in memo:
        return memo[x]
    if x in visiting:
        return {}
    out = {}
    for t in adders.get(x, []):
        for stack0, path0 in chains(t.layer, visiting + (x,)).items():
            for stack, path in settle(stack0, path0).items():
                if t.layer not in stack:
                    continue
                found = definer(layout, stack, t.source, t.input)
                if not found or found[0] != t.layer:
                    continue
                new = apply_ops(stack, t.ops, layout.base)
                if x in new:
                    out.setdefault(new, path + (t,))
    if not visiting:
        memo[x] = out
    return out

def replay(path, stack):
    """Replay a chain on top of `stack`; None if a layer in the stack intercepts a step."""
    for t in path:
        found = definer(layout, stack, t.source, t.input)
        if not found or found[0] != t.layer:
            return None
        stack = apply_ops(stack, t.ops, layout.base)
    return stack

def below(x):
    """{lower stack: reason} for x: its own chains, plus one bystander layer's chain stack underneath."""
    out = {}
    for stack, path in chains(x).items():
        out.setdefault(stack[:stack.index(x)], 'chain: ' + ' > '.join(t.layer + ' ' + t.input for t in path))
        for y in layout.presets:
            if y == layout.base or y in stack:
                continue
            for ystack in chains(y):
                done = replay(path, ystack)
                if done and x in done and y in done[:done.index(x)]:
                    out.setdefault(done[:done.index(x)], f'bystander {y}')
    return out

def keys(w, stacks):
    out = {}
    for s in stacks:
        routes, blocked = check_stack(layout, w, list(s))
        for r in routes + blocked: out.setdefault((r['source'], r['input']), set()).add(r['from_layer'])
    return out

if __name__ == '__main__':
    t0 = time.time()
    targets = always_on_layers(layout) + [t for t in layout.presets if t.startswith('Steering | LS') and t.endswith(': Double Tap')]
    lower = {w: below(w) for w in targets}
    print('chains + bystander check, %d targets: %.2fs' % (len(targets), time.time() - t0))
    t0 = time.time(); everything = {x: below(x) for x in layout.presets if x != layout.base}
    print('same for all %d layers: %.2fs' % (len(everything), time.time() - t0))
    space = StackSpace.of(layout, 5)
    walker = FlowWalker(layout); flow = {w: set() for w in targets}
    for f in families(layout, FROZEN_RULES).values():
        r = walker.walk(f)
        for w in targets: flow[w] |= set(r.lower_stacks(w))
    for w in targets:
        b, d, f = keys(w, lower[w]), keys(w, space.below(w)), keys(w, flow[w])
        extra = sorted(set(b) - set(d) - set(f))
        print(f'{w}: stacks={len(lower[w])} (flow {len(flow[w])}, depth-5 {len(space.below(w))})')
        print('     missed vs depth-5:', sorted(set(d) - set(b)), '| missed vs flow:', sorted(set(f) - set(b)))
        print('     extra:', [(k, sorted(b[k])[:2]) for k in extra][:4], '...' if len(extra) > 4 else '')
        open_routes = sorted({(r['source'], r['input'], r['from_layer']) for s in lower[w] for r in check_stack(layout, w, list(s))[0]})
        print('     open routes:', open_routes[:4], '...' if len(open_routes) > 4 else '')

    print('=== above, as the inverse of below (no second algorithm)')
    under = {x: {t for s in lows for t in s[1:]} for x, lows in everything.items()}
    for x, src, inp in (('L1: Modifier 0', 'switch', 'left_bumper'), ('Menu Right: Fn Layer', 'switch', 'button_escape'),
                        ('Steering | LS Up: Modifier 1', 'joystick', 'edge')):
        if x not in everything: continue
        above = sorted(z for z, layers in under.items() if x in layers)
        removed = {t_ for t in inv.on(x, (src, inp)) for op, t_ in t.ops if op == 'remove_layer'} - {x}
        print(x); print('   below:', sorted(under[x])); print('   above:', above)
        print('   exit removes:', sorted(removed))
        print('   removed but never present:', sorted(removed - under[x] - set(above)))
