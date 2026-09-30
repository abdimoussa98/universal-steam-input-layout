import json, time
from steam_layout.model import Layout, entries
from steam_layout.search_model import SearchModel
t0 = time.time()
L = Layout(json.loads(open('neptune/single-set-default_hold-gyro_latest.json').read()))
sm = SearchModel(L); titles = sm.layer_names
over = {lid: {**{j: lid for j in sm.binds.get(lid, ())}, **{j: 128 + lid for j in sm.blocks.get(lid, ())}} for lid in range(len(titles))}
removable = set()
for t in titles:
    for g in L.active(t).values():
        for v in g.get('inputs', {}).values():
            for _, e in entries(v.get('activators') or {}):
                for op, target in L.layer_ops(e):
                    if op in ('remove_layer', 'hold_layer'): removable.add(sm.index[target])
removable.discard(0)
print(f'{len(removable)} of {len(titles)-1} layers are removable by some entry')
# prefix trie: (parent prefix id, layer) -> prefix id; per prefix: profile id, removable set id, removable order id
child, prof_of, rset_of, rord_of = {}, [], [], []
profiles, rsets, rords = {}, {}, {}
empty = tuple([255] * len(sm.inputs))
prof_vec = [None]
def intern(d, k): return d.setdefault(k, len(d))
prof_vec[0] = empty; prof_of.append(intern(profiles, empty)); rset_of.append(intern(rsets, frozenset())); rord_of.append(intern(rords, ()))
rord_val = [()]
k_stack, k_prof, k_prof_set, k_prof_ord = set(), set(), set(), set()
n = 0
for line in open('out/stack_search/default-held/stacks.tsv'):
    ids = [int(x) for x in line.split('\t')[0].split()]
    n += 1
    p = 0  # empty prefix
    for pos, lid in enumerate(ids):
        if pos > 0:  # layer lid sits on context p
            k_stack.add((lid, p))
            k_prof.add((lid, prof_of[p]))
            k_prof_set.add((lid, prof_of[p], rset_of[p]))
            k_prof_ord.add((lid, prof_of[p], rord_of[p]))
        key = (p, lid)
        q = child.get(key)
        if q is None:
            q = len(prof_vec); child[key] = q
            v = list(prof_vec[p])
            for j, c in over[lid].items(): v[j] = c
            v = tuple(v); prof_vec.append(v); prof_of.append(intern(profiles, v))
            ro = rord_val[p] + ((lid,) if lid in removable else ())
            rord_val.append(ro); rord_of.append(intern(rords, ro)); rset_of.append(intern(rsets, frozenset(ro)))
        p = q
print(f'{n:,} distinct stacks, {len(prof_vec):,} distinct contexts (stack prefixes)')
print(f'(layer X, exact context below)                        {len(k_stack):>12,}')
print(f'(layer X, profile below)                              {len(k_prof):>12,}')
print(f'(layer X, profile below, removable layers below: set) {len(k_prof_set):>12,}')
print(f'(layer X, profile below, removable layers below: order){len(k_prof_ord):>11,}')
print(f'({time.time()-t0:.0f}s)')

# removals each layer can make
removes = {lid: set() for lid in range(len(titles))}
for t in titles:
    for g in L.active(t).values():
        for v in g.get('inputs', {}).values():
            for _, e in entries(v.get('activators') or {}):
                for op, target in L.layer_ops(e):
                    if op in ('remove_layer', 'hold_layer'): removes[sm.index[t]].add(sm.index[target])
above = {lid: set() for lid in range(len(titles))}
for line in open('out/stack_search/default-held/stacks.tsv'):
    ids = [int(x) for x in line.split('\t')[0].split()]
    for i, x in enumerate(ids):
        above[x].update(ids[i + 1:])
reach = {x: (removes[x] | set().union(*(removes[y] for y in above[x]))) - {0} for x in above}
print('layers whose removal can fire while X is on the stack: median', sorted(len(r) for r in reach.values())[len(reach)//2], 'of 71')
keys = set()
for line in open('out/stack_search/default-held/stacks.tsv'):
    ids = [int(x) for x in line.split('\t')[0].split()]
    p = 0
    for pos, lid in enumerate(ids):
        if pos > 0:
            keys.add((lid, prof_of[p], tuple(y for y in rord_val[p] if y in reach[lid])))
        p = child[(p, lid)]
print(f'(layer X, profile below, order of layers below that a removal while X is present can hit) {len(keys):,}')
