"""The Steering fallback hold on the simulator, as built and with the deflection chords' guard failing as a layer lands.

Read-only. Run from the repository root:

    python3 findings/2026-10-04-fallback-hold-on-the-deck/guards.py
"""
import sys, json, collections
sys.path.insert(0, '.')
from tests.scenario import Pad
from steam_layout import simulator as sm
from steam_layout import flow_model as fm
HOLD = 'Steering | LS: Fallback Hold'
orig = sm.Simulator._establish
STATE = {'mode': 'pressed', 'on': False}
def establish(self, control, phase, mode):
    STATE['mode'] = mode
    try: return orig(self, control, phase, mode)
    finally: STATE['mode'] = 'pressed'
orig_sat = fm.Condition.satisfied
def satisfied(self, held):
    deflect = any(part in ('edge',) for group in self.groups for _, part in group)
    if STATE['on'] and deflect and STATE['mode'] != 'pressed':
        return False                      # a deflection chord isn't decided as its layer lands
    return orig_sat(self, held)
sm.Simulator._establish = establish
fm.Condition.satisfied = satisfied
def summary(pad, n=0, upto=None):
    log = pad.sim.log[n:]
    adds = sum(1 for _, w, d in log if w == 'add' and d == HOLD)
    rems = sum(1 for _, w, d in log if w == 'remove' and d == HOLD)
    hap = sum(1 for _, w, d in log if w == 'haptic')
    beeps = [d for _, w, d in log if w == 'beep']
    w_down = [(ms, w, d) for ms, w, d in log if d in ('W', 'S') and w in ('down', 'up')]
    held_ms, last = 0, None
    for ms, w, d in w_down:
        if w == 'down': last = ms
        elif last is not None: held_ms += ms - last; last = None
    if last is not None: held_ms += pad.sim.now - last
    return f'Fallback Hold added {adds}x, removed {rems}x | pulses {hap} | W or S down for {held_ms} ms | beeps {beeps} | stack {pad.names()[1:]}'
def run(name, steps, variant, version=None, right_thumb=False):
    STATE['on'] = variant
    data = json.load(open(f'versions/neptune/{version}/single-set-default_hold-gyro_{version}.json')) if version else None
    pad = Pad('default', data=data, exposed_fires=not variant)
    STATE['on'] = False; pad.enter_steering(); STATE['on'] = variant
    if right_thumb: pad.touch('RS').wait(300)
    n = len(pad.sim.log)
    try: steps(pad)
    except RuntimeError as e: print(f'  {name:58s} | LOOP: {e}'); return
    print(f'  {name:58s} | {summary(pad, n)}')
CASES = (
 ('hold up 1 s (no exit yet)', lambda p: p.push('LS', 'up').wait(1000)),
 ('hold up 2 s (exit at 1.5 s)', lambda p: p.push('LS', 'up').wait(2000)),
 ('up 1 s, roll to the side 1 s, back up 1 s', lambda p: (p.push('LS', 'up').wait(1000), p.roll('LS', 'left').wait(1000), p.roll('LS', 'up').wait(1000))),
 ('up 1 s, centre, up 1 s', lambda p: (p.push('LS', 'up').wait(1000), p.recentre('LS').wait(200), p.push('LS', 'up').wait(1000))),
)
for version in (None, '90.23'):
    for variant in (False, True):
        for right in (False, True):
            print(f'=== {version or "90.29"}; deflection chords at landing: {"not decided" if variant else "decided (as the simulator has it)"}; right thumb {"on its stick" if right else "off"}')
            for name, steps in CASES:
                run(name, steps, variant, version, right)
