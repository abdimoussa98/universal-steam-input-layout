"""A trial in memory, nothing installed: `Steering`'s exit on up and down without Hold to Repeat, on 90.58.

    PYTHONPATH=. python3 findings/2026-10-12-steering-ends-while-rocking/trial_exit.py > .../trial-exit.txt

The gap and the right pad touch of probe.py again, then the exit itself: a fresh push to the rim, and a bumper
let go at the rim with the stick then brought back and pushed out again.
"""
import copy
import importlib.util
import itertools
from pathlib import Path

from steam_layout.model import Layout
from tests.scenario import VARIANTS

spec = importlib.util.spec_from_file_location('probe', Path(__file__).with_name('probe.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
GAPS = (0, 1, 10, 20, 40, 49, 50, 80, 150, 400)


def no_repeat(variant):
    data = copy.deepcopy(probe.snapshot(variant))
    group = Layout(data).active('Steering')['joystick']
    for name in ('dpad_north', 'dpad_south'):
        settings = group['inputs'][name]['activators']['Soft_Press']['settings']
        assert settings.pop('hold_repeats') == '1'
        settings.pop('repeat_rate')
    return data


for variant in VARIANTS:
    for label, data in (('90.58', None), ('no repeat on the exit', no_repeat(variant))):
        for exposed in probe.A9:
            gap = sum(probe.ends(probe.gap(variant, first, second, ms, data, exposed_fires=exposed))
                      for (first, second), ms in itertools.product(probe.ORDERS, GAPS))
            pad = sum(probe.ends(probe.brush(variant, first, second, t1, t2, data=data, exposed_fires=exposed))
                      for (first, second), t1, t2 in itertools.product(probe.ORDERS, range(1, 200, 24), range(1, 260, 24)))
            fresh = probe.steering(variant, data, exposed_fires=exposed).push('LS', 'up').wait(100)
            again = probe.start(variant, 'R1', data, exposed_fires=exposed).let_go('R1').wait(400)
            kept = again.has('Steering')
            again.recentre('LS').wait(100).push('LS', 'up').wait(100)
            print(f'{variant:11s} {label:22s} A9={exposed!s:5s} gap: ends in {gap:2d} of 20   right pad touch: ends in {pad:2d} of 198   '
                  f'a fresh push exits: {probe.ends(fresh)}   the last bumper off at the rim keeps Steering: {kept}, '
                  f'and the stick back and out again exits: {probe.ends(again)}')
