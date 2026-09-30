import json, time
from steam_layout.model import Layout
from steam_layout.held_model import HeldModel, REMOVE
from steam_layout.stackdb import StackDB
t0 = time.time()
L = Layout(json.loads(open('neptune/single-set-default_hold-gyro_latest.json').read()))
m = HeldModel(L); n = len(m.layer_names)
binds_or_blocks = {lid: m.binds.get(lid, set()) | m.blocks.get(lid, set()) for lid in range(n)}
reach = {0}; C = {x: set() for x in range(n)}; U = {x: set() for x in range(n)}
changed = True
while changed:
    changed = False
    for (lid, key), ents in list(m.entries.items()):
        if lid not in reach: continue
        jid = m.input_index[('switch', 'always_on_action')] if key == 'always' else m.input_index[m.controls[key]]
        # layers possibly present when this entry fires: co-present with lid; for Base, none may bind the input
        ctx = {y for y in C[lid] if not (lid == 0 and jid in binds_or_blocks[y])} | {lid, 0}
        for e in ents:
            s = set(ctx)
            for op, t in e['ops']:
                if op == REMOVE:
                    if t != 0: s.discard(t)
                    continue
                if t not in reach: reach.add(t); changed = True
                new = s - {t} - U[t]
                if new: U[t] |= new; changed = True
                for y in s - {t}:
                    if t not in C[y]: C[y].add(t); C[t].add(y); changed = True
                s.add(t)
print(f'rule: {len(reach)} reachable layers, {time.time()-t0:.1f}s')
db = StackDB('out/stack_search/default-held', L)
proven = {}
for y, x in db.under_pairs(): proven.setdefault(x, set()).add(y)
names = m.layer_names
print(f'{"layer":34} {"proven below":>13} {"rule: possible below":>21}')
for t in [t for t in names if 'Double Tap' in t and 'Cover' not in t] + ['L1: Modifier 0', 'Menu Right: Entry Point']:
    x = m.index[t]
    rule = {names[y] for y in U[x]} - {'Base'}
    pv = proven.get(t, set())
    assert pv <= rule, (t, pv - rule)
    print(f'{t:34} {len(pv):13d} {len(rule):21d}')
