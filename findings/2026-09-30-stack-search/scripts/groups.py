import json, collections
from steam_layout.model import Layout, entries
L = Layout(json.loads(open('neptune/single-set-default_hold-gyro_latest.json').read()))
titles = list(L.presets); base = titles[0]
edges = collections.defaultdict(set); ops_by = collections.defaultdict(lambda: collections.Counter())
for t in titles:
    for source, g in L.active(t).items():
        if g['mode'] == 'disabled': continue
        for name, v in g.get('inputs', {}).items():
            for kind, e in entries(v.get('activators') or {}):
                for op, target in L.layer_ops(e):
                    ops_by[t][op] += 1
                    if t != base and target != t and op != 'remove_layer':
                        edges[t].add(target); edges[target].add(t)
seen, comps = set(), []
for t in titles[1:]:
    if t in seen: continue
    stack, comp = [t], set()
    while stack:
        x = stack.pop()
        if x in comp: continue
        comp.add(x); stack.extend(edges[x] - comp)
    seen |= comp; comps.append(sorted(comp))
comps.sort(key=len, reverse=True)
print(f'{len(titles)-1} layers (Base excluded) -> {len(comps)} groups by add/remove:')
for c in comps: print(f'  [{len(c)}]', ', '.join(c) if len(c) < 12 else ', '.join(c[:12]) + f', ... (+{len(c)-12})')
# what ties the biggest group together: layers touching the most others
big = set(comps[0])
deg = sorted(((len(edges[x] & big), x) for x in big), reverse=True)[:10]
print('\nmost connected layers in the biggest group (neighbors):')
for d, x in deg: print(f'  {d:3d}  {x}')

group_of = {x: i for i, c in enumerate(comps) for x in c}
names = ['Main', 'RTP', 'LST', 'RST', 'Ramp', 'LTP Arrows', 'Escape', 'Tab', 'Backspace', 'Enter']
# inputs whose entries change layers, per group; and every input bound per group
changes = collections.defaultdict(set); binds = collections.defaultdict(set)
for t in titles[1:]:
    for source, g in L.active(t).items():
        if g['mode'] == 'disabled':
            binds[group_of[t]].add((source, '*disabled*')); continue
        for name, v in g.get('inputs', {}).items():
            acts = v.get('activators') or {}
            if not acts: continue
            binds[group_of[t]].add((source, name))
            if any(L.layer_ops(e) for _, e in entries(acts)): changes[group_of[t]].add((source, name))
print('\nlayer-changing inputs of one group that another group also binds (so its layers can override them):')
for i in range(len(comps)):
    for k in range(len(comps)):
        if i == k: continue
        both = changes[i] & binds[k]
        if both: print(f'  {names[i]:>10} inputs also bound by {names[k]:<10}: {len(both):2d}  e.g. ' + ', '.join('/'.join(j) for j in sorted(both)[:4]))
