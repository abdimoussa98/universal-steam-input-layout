"""Random gestures in Steering on the simulator. After everything is let go: is anything left on, and does a fresh up hold give W and the hold?

Read-only. Run from the repository root, with the seconds to run for:

    python3 findings/2026-10-04-fallback-hold-on-the-deck/fuzz.py 120
"""
import sys, random, collections, time
sys.path.insert(0, '.')
from tests.scenario import Pad
HOLD = 'Steering | LS: Fallback Hold'
BUTTONS = ['L1', 'R1', 'Select', 'Start', 'A']
WAITS = [10, 30, 60, 120, 180, 260, 420, 700]
def actions(pad, rng, held):
    kind = rng.choice(['button', 'button', 'ls', 'ls', 'ls', 'rs', 'rp'])
    if kind == 'button':
        b = rng.choice(BUTTONS)
        if b in held: pad.let_go(b); held.discard(b); return f'{b} up'
        pad.hold(b); held.add(b); return f'{b} down'
    if kind == 'ls':
        what = rng.choice(['up', 'down', 'left', 'centre', 'lift', 'touch'])
        if what in ('up', 'down', 'left'):
            from tests.scenario import DIRECTIONS
            if pad._held('LS', DIRECTIONS[what]): return f'LS {what} (already)'
            (pad.roll if pad._held('LS', 'edge') else pad.push)('LS', what); return f'LS {what}'
        if what == 'centre': pad.recentre('LS'); return 'LS centre'
        if what == 'lift': pad.lift('LS'); return 'LS lift'
        pad.touch('LS'); return 'LS touch'
    if kind == 'rs':
        what = rng.choice(['touch', 'push', 'lift'])
        {'touch': lambda: pad.touch('RS'), 'push': lambda: pad.push('RS'), 'lift': lambda: pad.lift('RS')}[what](); return f'RS {what}'
    what = rng.choice(['touch', 'lift'])
    (pad.touch if what == 'touch' else pad.lift)('RP'); return f'RP {what}'
found = collections.defaultdict(list)
rng = random.Random(7); t_end = time.time() + float(sys.argv[1]) if len(sys.argv) > 1 else time.time() + 150
runs = 0
while time.time() < t_end:
    runs += 1
    opts = rng.choice([{}, {'exposed_fires': False}, {'any_removal_resets': False}])
    pad = Pad('default', **opts); pad.enter_steering(); held = set(); steps = []
    try:
        for _ in range(rng.randint(3, 9)):
            steps.append(actions(pad, rng, held)); w = rng.choice(WAITS); pad.wait(w); steps.append(w)
            if 'Steering' not in pad.names(): break
        for b in list(held): pad.let_go(b)
        pad.lift('LS').lift('RS').lift('RP').wait(1500)
        if 'Steering' not in pad.names(): continue
        left = tuple(t for t in pad.names() if t not in ('Base', 'Steering'))
        pad.mark().push('LS', 'up').wait(400)
        ok = HOLD in pad.names() and 'W' in pad.down() and pad.seen('haptic')
        state = 'up works' if ok else f'up: hold {"on" if HOLD in pad.names() else "off"}, W {"down" if "W" in pad.down() else "not down"}, pulses {len(pad.seen("haptic"))}, top {pad.top}'
        if left or not ok: found[(left, state)].append((tuple(opts), steps))
    except Exception as e:
        found[('ERROR', str(e)[:80])].append((tuple(opts), steps))
print(runs, 'runs')
for key, cases in sorted(found.items(), key=lambda kv: -len(kv[1])):
    print(len(cases), '|', key)
    for c in sorted(cases, key=lambda c: len(c[1]))[:2]: print('      ', c)
