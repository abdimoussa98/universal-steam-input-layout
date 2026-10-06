"""What stays on when a button is let go inside the right pad's Double Tap window.

Read-only, on the working layout. Run from the repository root; it writes the layers found to the given file:

    python3 findings/2026-10-04-stick-touch-and-menu-buttons/window_left.py /tmp/left.json
"""
import sys, json, copy, collections, itertools
sys.path.insert(0, '.')
from tests.scenario import Pad, layout_data
from steam_layout.model import Layout
WINDOW = 'RTP: Double Tap'
STARTS = (('Base',), ('Base', 'Gyro'), ('Base', 'Gyro', 'Cursor Gyro'))
def gestures():
    for b in ('L1', 'R1', 'Select', 'Start'):
        for ms in (60, 150, 260, 500):
            yield f'{b} held {ms}', (b,), lambda p, b=b, ms=ms: p.hold(b).wait(ms)
        yield f'{b} double tap and hold', (b,), lambda p, b=b: p.tap(b, 50).wait(60).hold(b).wait(300)
        yield f'{b} held, A pressed', (b,), lambda p, b=b: p.hold(b).wait(300).tap('A', 50).wait(50)
    for a, b in (('L1', 'R1'), ('R1', 'L1'), ('Select', 'Start'), ('Start', 'Select')):
        for ms in (60, 300):
            yield f'{a} then {b}, {ms}', (b, a), lambda p, a=a, b=b, ms=ms: p.hold(a).wait(ms).hold(b).wait(120)
            yield f'{a} then {b}, {ms}, first let go first', (a, b), lambda p, a=a, b=b, ms=ms: p.hold(a).wait(ms).hold(b).wait(120)
def sweep(data):
    left = collections.defaultdict(collections.Counter); cases = stuck = 0
    for start in STARTS:
        for name, order, do in gestures():
            for touch_first in (False, True):
                for gap in (20, 100):
                    pad = Pad('default', start=start, data=copy.deepcopy(data)) if data else Pad('default', start=start)
                    try:
                        if touch_first: pad.touch('RP').wait(40)
                        do(pad)
                        if not touch_first: pad.touch('RP').wait(60)
                        pad.lift('RP').wait(gap)
                        if WINDOW not in pad.names(): continue
                        cases += 1
                        for b in order: pad.let_go(b)
                        pad.wait(1500)
                        extra = [t for t in pad.names() if t not in start]
                        if extra:
                            stuck += 1
                            for t in extra: left[order[0]][t] += 1
                    except Exception as e:
                        left['ERROR'][f'{name}: {str(e)[:70]}'] += 1
    return cases, stuck, left
if __name__ == "__main__":
    cases, stuck, left = sweep(None)
    print(f'as built: {stuck} of {cases} cases leave a layer on')
    for b, c in left.items(): print('  ', b, dict(c))
    json.dump({b: sorted(c) for b, c in left.items() if b != 'ERROR'}, open(sys.argv[1], 'w'), indent=1)
