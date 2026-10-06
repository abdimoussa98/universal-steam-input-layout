"""A pad touch and a menu button together, then a second menu press: what is left on, and when Fn comes.

Read-only, on the working layout. Run from the repository root:

    python3 findings/2026-10-04-stick-touch-and-menu-buttons/pad_sweep.py
"""
import sys, collections, itertools
sys.path.insert(0, '.')
from tests.scenario import Pad
FN = {'Select': 'Menu Left: Fn Layer', 'Start': 'Menu Right: Fn Layer'}
out = collections.defaultdict(list)
for opts in ({}, {'exposed_fires': False}, {'any_removal_resets': False}):
  for menu in ('Select', 'Start'):
    for pad_name in ('RP', 'LP'):
      for offset in (-200, -100, -20, -5, 0, 5, 20, 100, 190):          # pad touch relative to the menu press
        for menu_ms in (40, 120, 190, 210, 400):                        # how long the menu button is held
          for pad_ms in (40, 120, 160, 300, 700):                       # how long the thumb is on the pad
            pad = Pad('default', **opts)
            events = sorted([(max(0, -offset) + 0, 'm+'), (max(0, -offset) + menu_ms, 'm-'), (max(0, offset), 'p+'), (max(0, offset) + pad_ms, 'p-')])
            if offset < 0: events = sorted([(0, 'p+'), (pad_ms, 'p-'), (-offset, 'm+'), (-offset + menu_ms, 'm-')])
            else: events = sorted([(0, 'm+'), (menu_ms, 'm-'), (offset, 'p+'), (offset + pad_ms, 'p-')])
            now = 0
            for t, e in events:
                pad.wait(t - now); now = t
                {'m+': lambda: pad.hold(menu), 'm-': lambda: pad.let_go(menu), 'p+': lambda: pad.touch(pad_name), 'p-': lambda: pad.lift(pad_name)}[e]()
            pad.wait(800)
            left = tuple(t for t in pad.names() if t != 'Base')
            t0, n = pad.sim.now, len(pad.sim.log); pad.mark()
            pad.hold(menu).wait(700)
            fn = next((ms - t0 for ms, what, d in pad.sim.log[n:] if what == 'add' and d == FN[menu]), None)
            pad.let_go(menu).wait(400)
            after = tuple(t for t in pad.names() if t != 'Base')
            out[(left, fn, after)].append((menu, pad_name, offset, menu_ms, pad_ms, tuple(opts)))
for (left, fn, after), cases in sorted(out.items(), key=lambda kv: -len(kv[1])):
    print(f'left on after the first gesture: {left or "nothing"} | second hold: Fn at {fn} | left after: {after or "nothing"} | {len(cases)} cases')
    if left or fn != 200 or after: print('    e.g.', cases[:3])
