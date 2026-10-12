"""Every bind that removes the W or S layer, and every chord with Invert Activation.

    PYTHONPATH=. python3 findings/2026-10-11-stick-touch-and-cleanup-audit/driver_layer_removes.py [default|alternative]
"""
import collections, json, sys
from steam_layout.cleanups import Cleanups
from steam_layout.model import Layout, actions, entries, map_title

variant = sys.argv[1] if len(sys.argv) > 1 else 'default'
layout = Layout(json.load(open(f'neptune/single-set-{variant}_hold-gyro_latest.json')))
rename = {'L1': 'L2', 'R1': 'R2'} if variant == 'alternative' else {}
DRIVERS = [map_title(t, rename) for t in ('Steering | R1: W Key', 'Steering | L1: S Key')]
INPUT = {('joystick', 'touch'): 'left stick touch', ('right_joystick', 'touch'): 'right stick touch',
         ('joystick', 'edge'): 'left stick edge', ('right_joystick', 'edge'): 'right stick edge',
         ('joystick', 'click'): 'left stick click', ('right_joystick', 'click'): 'right stick click'}
KIND = {'Full_Press': 'Regular Press', 'chord': 'Chorded Press', 'release': 'Release', 'Soft_Press': 'Soft Press', 'Start_Press': 'Start Press'}


def where(t):
    return INPUT.get((t.source, t.input), f'{t.source}/{t.input}')


def describe(layout, t):
    settings = dict(t.settings)
    stored = layout.active(t.layer)[t.source]['inputs'][t.input]['activators']
    guards = [e for kind, e in entries(stored) if kind == 'chord' and e is not None and actions(e) and 'remove_layer' not in ' '.join(actions(e))]
    if t.activator == 'chord' and settings.get('edge_binding_invert') == '1':
        return 'Chorded Press with Invert Activation, repeating'
    if t.activator == 'Full_Press' and t.role == 'recovery':
        return f'Regular Press, repeating, beside {len(guards)} guard chord(s)'
    extra = ', repeating' if settings.get('hold_repeats') == '1' else ''
    return KIND.get(t.activator, t.activator) + extra


c = Cleanups(layout)
rows = collections.defaultdict(lambda: collections.defaultdict(list))
clears = collections.Counter()
for t in c.inv.transitions:
    removed = [x for op, x in t.ops if op == 'remove_layer']
    hit = [x for x in removed if x in DRIVERS]
    if not hit:
        continue
    if len(removed) > 12:                       # a clear of a whole mode or to Base
        clears[(t.layer, where(t), KIND.get(t.activator, t.activator), len(removed))] += 1
        continue
    rows[t.layer][(describe(layout, t), tuple(sorted(x.split(': ')[-1] for x in hit)))].append(where(t))
print(f'== {variant}: binds that remove {" or ".join(DRIVERS)}')
for layer, kinds in rows.items():
    print(f'\n{layer}')
    for (kind, hit), inputs in sorted(kinds.items()):
        print(f'   {kind} [{" and ".join(hit)}]: {len(inputs)}: ' + ', '.join(sorted(set(inputs))))
print('\nClears of a whole mode (more than 12 removes), which also list them:')
for (layer, inp, kind, n), count in sorted(clears.items()):
    print(f'   {layer} | {inp} | {kind} | {n} removes')

print('\n== every chord with Invert Activation')
for title in layout.presets:
    for source, group in layout.active(title).items():
        for name, value in (group.get('inputs') or {}).items():
            for kind, e in entries(value.get('activators', {})):
                s = e.get('settings') or {}
                if kind == 'chord' and s.get('edge_binding_invert') == '1':
                    ops = layout.layer_ops(e)
                    mask = s.get('gyro_ratchet_button_mask') or s.get('chord_button')
                    print(f'   {title} | {INPUT.get((source, name), source + "/" + name)} | chord buttons mask {mask} | '
                          f'repeat {s.get("hold_repeats")} | ' + ' ; '.join(('-' if op == 'remove_layer' else '+') + x for op, x in ops))
