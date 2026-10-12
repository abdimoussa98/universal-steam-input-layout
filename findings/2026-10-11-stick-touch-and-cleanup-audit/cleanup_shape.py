"""Every cleanup function against the shape rule (R133), and which stick-touch binds can remove a driver layer."""
import json, sys, collections
from steam_layout.model import Layout, entries, actions, EMPTY
from steam_layout.cleanups import Cleanups
for variant in ('default', 'alternative'):
    layout = Layout(json.load(open(f'neptune/single-set-{variant}_hold-gyro_latest.json')))
    c = Cleanups(layout)
    found = [t for t in c.inv.transitions if t.role == 'recovery']
    where = collections.Counter()
    bad = collections.defaultdict(list)
    guards = collections.Counter()
    for t in found:
        stored = layout.active(t.layer)[t.source]['inputs'][t.input]['activators']
        listed = list(entries(stored))
        settings = dict(t.settings)
        place = ('stick touch' if t.input == 'touch' and 'joystick' in t.source else
                 'stick edge' if t.input == 'edge' and 'joystick' in t.source else
                 'stick click' if t.input == 'click' and 'joystick' in t.source else
                 'stick direction' if t.input.startswith('dpad') and 'joystick' in t.source else
                 'pad' if 'trackpad' in t.source else 'button')
        where[place] += 1
        label = f'{t.layer} {t.source}/{t.input}'
        if t.activator == 'chord':                                   # the inverted chord: its own guard
            guards['inverted chord'] += 1
            if settings.get('edge_binding_invert') != '1' or settings.get('hold_repeats') != '1':
                bad['inverted chord without invert or repeat'].append(label)
            continue
        if t.activator != 'Full_Press':
            bad['not a Regular Press'].append(f'{label} {t.activator}'); continue
        if settings.get('hold_repeats') != '1':
            bad['no Hold to Repeat'].append(label)
        if settings.get('interruptable') == '0':
            bad['not interruptible'].append(label)
        chords = [e for kind, e in listed if kind == 'chord']
        if not chords:
            bad['no guard chord on the input'].append(label)
        for e in chords:
            s = e.get('settings') or {}
            empty = actions(e) == [EMPTY + ', , ']
            guards[('empty' if empty else 'with an output') + (', repeats' if s.get('hold_repeats') == '1' else ', no repeat')
                   + (', not interruptible' if s.get('interruptable') == '0' else ', interruptible')
                   + (', delayed' if s.get('delay_start') not in (None, '', '0') else '')] += 1
        kinds = list(stored)
        if kinds != [k for k in ('Full_Press', 'chord', 'release', 'Soft_Press') if k in kinds]:
            bad['stored order'].append(f'{label} {kinds}')
        if any(op != 'remove_layer' for op, _ in t.ops):
            bad['does more than remove'].append(label)
    print(f'== {variant}: {len(found)} cleanup functions in {len({t.layer for t in found})} layers: {dict(where)}')
    print('   guard chords beside them:', dict(guards))
    print('   shape findings:', {k: len(v) for k, v in bad.items()} or 'none')
    for k, v in bad.items():
        for label in v[:12]:
            print('      ', k, '|', label)
    if variant == 'default':
        drivers = ('Steering | R1: W Key', 'Steering | L1: S Key')
        rows = collections.defaultdict(list)
        for t in c.inv.transitions:
            if t.input == 'touch' and 'joystick' in t.source and any(op == 'remove_layer' and x in drivers for op, x in t.ops):
                rows[(t.role, t.activator)].append(f'{t.layer} / {"LS" if t.source == "joystick" else "RS"}')
        print('   stick-touch binds that remove the W or S layer:')
        for (role, kind), layers in rows.items():
            print(f'      {role} ({kind}), {len(layers)}: ' + '; '.join(layers))
