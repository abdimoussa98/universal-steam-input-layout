"""Sweep: a stick touch (resting, tapped, pushed) around a menu tap or hold. What is typed, when Fn lands, what beeps.

Read-only, on the working layout. Run from the repository root:

    python3 findings/2026-10-04-stick-touch-and-menu-buttons/sweep.py
"""
import sys, collections, itertools
sys.path.insert(0, '.')
from tests.scenario import Pad
FN = {'Select': 'Menu Left: Fn Layer', 'Start': 'Menu Right: Fn Layer'}
KEY = {'Select': 'ESCAPE', 'Start': 'TAB'}
def fn_at(pad, n, t0, menu):
    return next((ms - t0 for ms, what, d in pad.sim.log[n:] if what == 'add' and d == FN[menu]), None)
out = collections.defaultdict(set)
for opts in ({}, {'exposed_fires': False}):
    for menu in ('Select', 'Start'):
        for stick in ('LS', 'RS'):
            for push in (False, True):
                for touch_ms in (30, 100, 140, 160, 300, 600):            # how long the thumb has been down
                    for gap in (None, 10, 60, 120, 190, 260):              # None: thumb still down at the press; else lifted this long before
                        for gesture in ('tap', 'hold'):
                            pad = Pad('default', **opts)
                            (pad.push(stick, 'up' if stick == 'LS' else None) if push else pad.touch(stick))
                            pad.wait(touch_ms)
                            if gap is not None:
                                if push: pad.recentre(stick)
                                pad.lift(stick).wait(gap)
                            t0, n = pad.sim.now, len(pad.sim.log); pad.mark()
                            if gesture == 'tap':
                                pad.tap(menu, 60).wait(700)
                                res = ('typed', tuple(k for k in pad.typed() if k in KEY.values()))
                            else:
                                pad.hold(menu).wait(700)
                                res = ('fn at', fn_at(pad, n, t0, menu), 'beeps', len(pad.seen('beep')))
                                pad.let_go(menu).wait(300)
                            if gap is None:
                                if push: pad.recentre(stick)
                                pad.lift(stick).wait(400)
                            left = tuple(t for t in pad.names() if t != 'Base')
                            if gap is None:
                                where = 'thumb down, ' + ('stick pushed' if push else 'resting')
                            else:
                                where = ('short touch' if touch_ms < 150 else 'long touch') + (', pushed' if push else '') + f', lifted {gap} ms before'
                            key = (gesture, where, res + ((('left on', left),) if left else ()))
                            out[key].add((menu, stick, touch_ms, tuple(opts.items())))
for (gesture, where, res), cases in sorted(out.items(), key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2]))):
    print(f'{gesture:4s} | {where:42s} | {res} | {len(cases)} cases')
