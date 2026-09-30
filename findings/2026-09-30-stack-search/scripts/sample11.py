import json, collections, random, time
from steam_layout.model import Layout
from steam_layout.stackdb import StackDB
from steam_layout.search_model import SearchModel
L = Layout(json.loads(open('neptune/single-set-default_hold-gyro_latest.json').read()))
db = StackDB('out/stack_search/default-held', L)
sm = SearchModel(L)
# per-layer overrides: input id -> code (layer id binds, 128+id blocked)
over = {}
for lid in range(len(db.layers)):
    d = {}
    for j in sm.binds.get(lid, ()): d[j] = lid
    for j in sm.blocks.get(lid, ()): d[j] = 128 + lid
    over[lid] = d
idx = {t: n for n, t in enumerate(db.layers)}
memo = {(): tuple([255] * len(db.inputs))}
def owners(ids):
    if ids in memo: return memo[ids]
    base = list(owners(ids[:-1])); base_over = over[ids[-1]]
    for j, c in base_over.items(): base[j] = c
    r = tuple(base); memo[ids] = r; return r
rows = list(db.distinct_stacks())
by_depth = collections.Counter(r['depth'] for r in rows)
print('distinct stacks by fewest events:', dict(sorted(by_depth.items())))
old = [r for r in rows if r['depth'] <= 10]
new = [r for r in rows if r['depth'] == 11]
old_sets = collections.defaultdict(list)
for r in old: old_sets[frozenset(r['stack'])].append(r['stack'])
old_stacks = {r['stack'] for r in old}
# facts: (top, input, value it inherits)
def facts(r):
    ids = tuple(idx[t] for t in r['stack'])
    below = owners(ids[:-1])
    return {(r['top'], j, c) for j, c in enumerate(below)}
t = time.time()
old_facts = set()
for r in old: old_facts |= facts(r)
cat = collections.Counter(); newfact_rows = []
for r in new:
    s = r['stack']; fs = frozenset(s)
    if fs in old_sets: k = 'same layers as a shallower stack, different order'
    elif any(fs - {x} in old_sets for x in s[1:]): k = 'a shallower stack plus one more layer'
    else: k = 'other'
    cat[k] += 1
    nf = facts(r) - old_facts
    if nf: newfact_rows.append((r, nf))
print(f'{len(new)} stacks first reached at 11 events (partial level):')
for k, v in cat.most_common(): print(f'   {v:7d}  {k}')
allnew = set().union(*[nf for _, nf in newfact_rows]) if newfact_rows else set()
print(f'stacks at 11 that give a layer a NEW inherited value: {len(newfact_rows)}; new (top, input, value) facts: {len(allnew)}')
bytop = collections.Counter(t for t, _, _ in allnew)
print('   new facts by top layer:', dict(bytop.most_common(10)))
def code(c): return 'nothing' if c == 255 else (f'blocked by {db.layers[c-128]}' if c >= 128 else db.layers[c])
random.seed(7)
def show(r, nf=None):
    s = r['stack']; fs = frozenset(s)
    print('\n  STACK:', ' > '.join(s))
    if fs in old_sets:
        near = min(old_sets[fs], key=lambda o: sum(a != b for a, b in zip(o, s)))
        print('  closest at <=10 events (same layers):', ' > '.join(near))
    else:
        for x in s[1:]:
            if fs - {x} in old_sets:
                print(f'  closest at <=10 events: same without "{x}":', ' > '.join(old_sets[fs - {x}][0])); break
    print('  button events:', ' ; '.join(lbl for lbl, _ in db.witness(r['witness'])[1:]))
    if nf:
        for top, j, c in sorted(nf)[:4]: print(f'  NEW: {top} inherits {"/".join(db.inputs[j])} from {code(c)}')
print('\n=== samples: reordered ===')
for r in random.sample([r for r in new if frozenset(r['stack']) in old_sets], 2): show(r)
print('\n=== samples: one more layer ===')
for r in random.sample([r for r in new if frozenset(r['stack']) not in old_sets], 2): show(r)
print('\n=== samples: giving a new inherited value ===')
for r, nf in random.sample(newfact_rows, min(3, len(newfact_rows))): show(r, nf)
print(f'\n({time.time()-t:.1f}s)')
