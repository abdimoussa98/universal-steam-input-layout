"""`Steering` ends while the bumpers are rocked with the stick up (the author's report on 90.58).

Read-only: replays press sequences on the simulator, on the 90.58 snapshot in `versions/neptune/` (the working
layouts became 90.59 while this was written). Run from the repo root:

    PYTHONPATH=. python3 findings/2026-10-12-steering-ends-while-rocking/probe.py > .../results.txt

Sections: who removes `Steering`; a rock with a bumper always down; a rock with a gap; a short touch of the
right pad before the rock; a stick window; the same on older builds; one trial change, in memory.
"""
import copy
import itertools
import json
import random

from steam_layout.model import Layout
from steam_layout.simulator import Simulator
from tests.scenario import BUTTONS, ROLES, ROOT, VARIANTS, Pad, frozen_layout_data

STEERING = 'Steering'
W, S = 'Steering | R1: W Key', 'Steering | L1: S Key'
A9 = (True, False)                 # a bind exposed under a held input fires at once, or at its next repeat
ORDERS = (('R1', 'L1'), ('L1', 'R1'))
VERSION = '90.58'
_snapshots = {}


def snapshot(variant, version=VERSION):
    key = variant, version
    if key not in _snapshots:
        path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
        _snapshots[key] = json.loads(path.read_text(encoding='utf-8'))
    return _snapshots[key]


def steering(variant, data=None, **way):
    """A pad in `Steering`, on the snapshot or on `data`."""
    return Pad(variant, start=('Base', STEERING), data=data or snapshot(variant), **way)


def start(variant, first, data=None, **way):
    """`first` held, the stick up at the rim, past the stick's 200 ms hold timer."""
    return steering(variant, data, **way).hold(first).wait(300).push('LS', 'up').wait(400)


def ends(pad):
    return not pad.has(STEERING)


def removers(variant):
    layout = Layout(snapshot(variant))
    sim = Simulator(layout)
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name in group.get('inputs', {}):
                for entry in sim._entries_of(title, source, name):
                    if ('remove_layer', STEERING) in entry.ops:
                        yield title, f'{source}/{name}', entry.kind, len(entry.ops)


def rock(variant, seed, steps=14, **way):
    """Random rocking, a bumper down at every moment, the stick up throughout. True if `Steering` leaves."""
    rng = random.Random(seed)
    first = rng.choice(('R1', 'L1'))
    pad = steering(variant, **way)
    pad.hold(first).wait(rng.choice((20, 60, 150, 300))).push('LS', 'up').wait(rng.choice((20, 60, 150, 250, 400)))
    held = {first}
    for _ in range(steps):
        if len(held) == 2:
            who = rng.choice(('L1', 'R1'))
            pad.let_go(who)
            held.discard(who)
        else:
            who = 'L1' if 'R1' in held else 'R1'
            pad.hold(who)
            held.add(who)
        pad.wait(rng.choice((1, 5, 15, 30, 49, 51, 80, 120, 199, 201, 260, 400)))
        if ends(pad):
            return True
    return False


def gap(variant, first, second, ms, data=None, **way):
    """The held bumper comes up, the other goes down `ms` later."""
    pad = start(variant, first, data, **way)
    return pad.let_go(first).wait(ms).hold(second).wait(300)


def brush(variant, first, second, t1, t2, touch=30, data=None, **way):
    """A touch of the right pad, `second` down `t1` ms after the thumb lifts, `first` up `t2` ms after that."""
    pad = start(variant, first, data, **way)
    return pad.touch('RP').wait(touch).lift('RP').wait(t1).hold(second).wait(t2).let_go(first).wait(400)


def stick_window(variant, back, **way):
    """R1, L1, R1 up (the S layer), the stick let go inside 200 ms, R1 down and L1 up inside the stick's
    window, the stick at the rim again `back` ms later."""
    pad = start(variant, 'R1', **way)
    pad.hold('L1').wait(100).let_go('R1').wait(80).recentre('LS').wait(20).hold('R1').wait(40).let_go('L1')
    return pad.wait(back).push('LS', 'up').wait(300)


def older(version):
    try:
        return frozen_layout_data('default', version)
    except KeyError:
        return snapshot('default', version)


def trial(variant):
    """In memory only: the cleanup press on the other driver's bumper also adds that driver's layer, stored
    last so that it runs first (the shape of R174's hand-over)."""
    data = copy.deepcopy(snapshot(variant))
    layout, pad = Layout(data), Pad(variant, data=data)
    number = {layout.titles[key]: index + 1 for index, key in enumerate(layout.order)}
    for own, other, bumper in ((W, S, 'L1'), (S, W, 'R1')):
        source, name = BUTTONS[ROLES[variant][bumper]]
        press = layout.active(pad.title(own))[source]['inputs'][name]['activators']['Full_Press']
        press['bindings']['binding'].append(f'controller_action add_layer {number[pad.title(other)]} 0 0, , ')
    return data


def log_of(pad, since):
    return '\n'.join(f'    {ms:5d} {what:8s} {detail}' for ms, what, detail in pad.sim.log[since:])


def main():
    print('1. Every bind that removes `Steering` (default layout): layer, input, activator, commands in the bind')
    for row in removers('default'):
        print('   ', *row)

    print('\n2. A bumper down at every moment, the stick up throughout, nothing else touched: 3,000 random rocks')
    for variant, exposed, ties in itertools.product(VARIANTS, A9, (False, True)):
        lost = sum(rock(variant, seed, exposed_fires=exposed, reverse_ties=ties) for seed in range(3000))
        print(f'    {variant:11s} A9={exposed!s:5s} ties reversed={ties!s:5s} `Steering` ends in {lost} of 3000')

    gaps = (0, 1, 10, 20, 40, 49, 50, 80)
    print('\n3. The held bumper up, the other down some ms later (no bumper down in between). Columns: ms ' + ' '.join(f'{g:>5d}' for g in gaps))
    for variant, (first, second), exposed in itertools.product(VARIANTS, ORDERS, A9):
        row = ['ENDS ' if ends(gap(variant, first, second, ms, exposed_fires=exposed)) else 'stays' for ms in gaps]
        print(f'    {variant:11s} {first} then {second}, A9={exposed!s:5s}      ' + ' '.join(row))
    pad = start('default', 'R1', exposed_fires=False)
    since = len(pad.sim.log)
    pad.let_go('R1').wait(60).hold('L1').wait(100)
    print('    The log of a 60 ms gap, default layout, A9=False:\n' + log_of(pad, since))

    t1s, t2s = (5, 40, 80, 120, 149, 151), (5, 30, 60, 100, 140, 160, 250)
    print('\n4. A 30 ms touch of the right pad, then the rock. Rows: the second bumper down t1 ms after the thumb lifts.'
          '\n   Columns: the first bumper up t2 ms after that:        ' + ' '.join(f'{t:>4d}' for t in t2s))
    for (first, second), exposed in itertools.product(ORDERS, A9):
        print(f'    default, {first} then {second}, A9={exposed}')
        for t1 in t1s:
            row = ['ENDS' if ends(brush('default', first, second, t1, t2, exposed_fires=exposed)) else ' ok ' for t2 in t2s]
            print(f'        t1={t1:>4d}                                        ' + ' '.join(row))
    print('    How long the touch can be (second bumper 30 ms after the lift, first up 40 ms later):')
    for touch in (1, 30, 100, 140, 150, 300, 800):
        pad = start('default', 'R1').touch('RP').wait(touch).lift('RP').wait(1)
        window = pad.has('RTP: Double Tap')
        pad.wait(29).hold('L1').wait(40).let_go('R1').wait(400)
        print(f"        {touch:>4d} ms: {'window' if window else 'no window'}, `Steering` {'ENDS' if ends(pad) else 'stays'}")
    print('    The stick elsewhere (R1 held, 30 ms touch, L1 down 30 ms after the lift, R1 up 40 ms later):')
    for where in ('centre', 'left'):
        pad = steering('default').hold('R1').wait(300)
        if where != 'centre':
            pad.push('LS', where).wait(400)
        pad.touch('RP').wait(30).lift('RP').wait(30).mark().hold('L1').wait(40).let_go('R1').wait(400)
        print(f"        stick {where}: {' > '.join(pad.names())}, down {pad.down()}, typed {pad.typed()}")
    for exposed in A9:
        pad = start('default', 'L1', exposed_fires=exposed)
        since = len(pad.sim.log)
        pad.touch('RP').wait(3).lift('RP').wait(57).hold('R1').wait(77).let_go('L1').wait(300)
        print(f'    The log, default layout, L1 then R1, A9={exposed}:\n' + log_of(pad, since))

    backs = (5, 20, 40, 49, 51, 80)
    print('\n5. A stick window. Columns: the stick back at the rim after ms ' + ' '.join(f'{b:>5d}' for b in backs))
    for variant, exposed in itertools.product(VARIANTS, A9):
        row = ['ENDS ' if ends(stick_window(variant, back, exposed_fires=exposed)) else 'stays' for back in backs]
        print(f'    {variant:11s} A9={exposed!s:5s}                                 ' + ' '.join(row))

    print('\n6. Older builds, default layout: a 60 ms gap, and the right pad touch (t1 30, t2 40)')
    for version in ('90.38', '90.48', '90.54', '90.56', '90.57', '90.58'):
        data, row = older(version), []
        for exposed in A9:
            row.append(f"A9={exposed}: gap {'ENDS' if ends(gap('default', 'R1', 'L1', 60, data, exposed_fires=exposed)) else 'stays'}, "
                       f"pad {'ENDS' if ends(brush('default', 'R1', 'L1', 30, 40, data=data, exposed_fires=exposed)) else 'stays'}")
        print(f'    {version:9s} ' + '    '.join(row))

    print('\n7. A trial in memory, not installed: the cleanup press on the other bumper also adds that driver\'s layer.'
          '\n   The right pad touch then the rock, over 1,496 timings a layout (both orders, both A9, t1 1 to 193, t2 1 to 253)')
    for variant in VARIANTS:
        for label, data in (('90.58', None), ('trial', trial(variant))):
            lost = inside = 0
            for exposed, (first, second), t1, t2 in itertools.product(A9, ORDERS, range(1, 200, 12), range(1, 260, 12)):
                if ends(brush(variant, first, second, t1, t2, data=data, exposed_fires=exposed)):
                    lost += 1
                    inside += t1 + t2 < 150
            print(f'    {variant:11s} {label:9s} `Steering` ends in {lost} of 1496, {inside} of them with the first bumper up inside the window')


if __name__ == '__main__':
    main()
