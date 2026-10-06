"""Sweep: in Steering with no driver, things done around an LS up hold; then a fresh up hold must give W, pulses and the 1.5 s exit.

Read-only. Run from the repository root:

    python3 findings/2026-10-04-fallback-hold-on-the-deck/sweep.py
"""
import sys, collections, itertools
sys.path.insert(0, '.')
from tests.scenario import Pad
HOLD = 'Steering | LS: Fallback Hold'
OTHERS = {
 'nothing': lambda p: p,
 'RS touched': lambda p: p.touch('RS'),
 'RS pushed': lambda p: p.push('RS'),
 'RS pushed and let go': lambda p: p.push('RS').wait(120).lift('RS'),
 'RS tapped': lambda p: p.touch('RS').wait(60).lift('RS'),
 'R1 tapped': lambda p: p.tap('R1', 60),
 'L1 tapped': lambda p: p.tap('L1', 60),
 'R1 held 400': lambda p: p.hold('R1').wait(400).let_go('R1'),
 'Select tapped': lambda p: p.tap('Select', 60),
 'Select held 400': lambda p: p.hold('Select').wait(400).let_go('Select'),
 'right pad tapped': lambda p: p.touch('RP').wait(60).lift('RP'),
 'right pad touched': lambda p: p.touch('RP'),
 'A pressed': lambda p: p.tap('A', 60),
 'LS thumb lifted and back': lambda p: p.lift('LS').wait(80).touch('LS'),
}
MOVES = {
 'stays up': lambda p: p,
 'rolls to the side and back up': lambda p: p.roll('LS', 'left').wait(300).roll('LS', 'up'),
 'centre and up again': lambda p: p.recentre('LS').wait(120).push('LS', 'up'),
 'quick flick: centre 40 ms, up': lambda p: p.recentre('LS').wait(40).push('LS', 'up'),
 'down instead': lambda p: p.recentre('LS').wait(60).push('LS', 'down'),
}
out = collections.defaultdict(list)
for opts in ({}, {'exposed_fires': False}, {'any_removal_resets': False}, {'reverse_ties': True}):
    for before in (100, 700, 1400):
        for other, do in OTHERS.items():
            for when in ('before the move', 'after the move'):
                for move, mv in MOVES.items():
                    pad = Pad('default', **opts); pad.enter_steering()
                    try:
                        pad.push('LS', 'up').wait(before)
                        if when == 'before the move': do(pad); pad.wait(50)
                        mv(pad)
                        if when == 'after the move': pad.wait(50); do(pad)
                        pad.wait(300)
                        steering = 'Steering' in pad.names()
                        key = 'S' if move == 'down instead' else 'W'
                        state = ('in Steering' if steering else 'left Steering', 'hold on' if HOLD in pad.names() else 'no hold', f'{key} down' if key in pad.down() else f'no {key}')
                        n = len(pad.sim.log); pad.wait(1700)
                        pulses = sum(1 for _, w, d in pad.sim.log[n:] if w == 'haptic')
                        after = 'left Steering' if 'Steering' not in pad.names() else 'still in Steering'
                        res = state + (after if steering else '',)
                    except Exception as e:
                        res = ('ERROR', str(e)[:60])
                    out[res].append((other, when, move, before, tuple(opts)))
for res, cases in sorted(out.items(), key=lambda kv: -len(kv[1])):
    print(f'{len(cases):5d} | {res}')
    if len(cases) < 400:
        seen = collections.Counter((c[0], c[1], c[2]) for c in cases)
        for k, n in seen.most_common(12): print('         ', n, k)
