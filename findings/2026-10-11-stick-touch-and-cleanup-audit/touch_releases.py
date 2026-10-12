"""Stick-touch Releases of every layer: which add a layer, and what that layer is.

    PYTHONPATH=. python3 findings/2026-10-11-stick-touch-and-cleanup-audit/touch_releases.py [default|alternative]
"""
import json, sys, collections
from steam_layout.model import Layout, entries
variant = sys.argv[1] if len(sys.argv) > 1 else 'default'
layout = Layout(json.load(open(f'neptune/single-set-{variant}_hold-gyro_latest.json')))
total = with_add = 0
by_add = collections.defaultdict(list)
plain = collections.Counter()
none = []
for title in layout.presets:
    for source in ('joystick', 'right_joystick'):
        value = ((layout.active(title).get(source) or {}).get('inputs') or {}).get('touch') or {}
        releases = [e for kind, e in entries(value.get('activators', {})) if kind == 'release']
        if not releases:
            none.append(f'{title}/{source}')
            continue
        for e in releases:
            total += 1
            ops = layout.layer_ops(e)
            adds = tuple(t for op, t in ops if op in ('add_layer', 'hold_layer'))
            removes = [t for op, t in ops if op == 'remove_layer']
            if adds:
                with_add += 1
                by_add[adds].append((title, source, ops))
            else:
                plain[tuple(removes)] += 1
print(f'{variant}: {total} stick-touch Releases in {len(layout.presets)} layers; {with_add} add a layer; {len(none)} layer-sticks have no touch Release')
for adds, rows in sorted(by_add.items(), key=lambda kv: -len(kv[1])):
    print(f'\n+ {", ".join(adds)}   ({len(rows)} Releases)')
    for title, source, ops in rows:
        order = ' ; '.join(('+' if op != 'remove_layer' else '-') + t for op, t in ops)
        print(f'     {title} / {"LS" if source == "joystick" else "RS"}: {order}'[:300])
print('\nReleases with no add, by list:')
for removes, n in plain.most_common():
    print(f'  {n:3d} x  -' + ' ; -'.join(removes)[:200])
