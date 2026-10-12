"""The author's suspicion (2026-10-11): after a remove_layer call that takes a layer off, a chord with Invert
Activation fires although a chord button is held. The simulator assumes it stays off (A61). This runs the
simulator both ways on 90.55 and prints what each predicts.

    PYTHONPATH=.:tests python3 findings/2026-10-11-stick-touch-and-cleanup-audit/suspicion_probe.py
"""
import json

import steam_layout.simulator as simulator
from tests.scenario import Pad

data = json.load(open('neptune/single-set-default_hold-gyro_latest.json'))
EDGE = ('joystick', 'edge')
plain = simulator.Simulator._run
state = {'on': False, 'busy': False}


def run(self, entry, act=None, tap=False, commands=True):
    before = self.stack
    plain(self, entry, act, tap, commands)
    took_off = any(t not in self.stack for t in before)
    if state['on'] and took_off and not state['busy'] and EDGE not in self.held:
        state['busy'] = True
        _, found = self.binding(EDGE)                       # the one layer that answers the left edge now
        for e in found:
            if e.kind == 'chord' and e.inverted:
                plain(self, e)                              # whatever the chord buttons are doing
        state['busy'] = False


simulator.Simulator._run = run


def half(pad, direction):
    """Deflect past the deadzone but inside the outer ring: the direction without the edge."""
    pad.touch('LS')
    pad.sim.press(('joystick', {'up': 'dpad_north', 'down': 'dpad_south'}[direction]))
    return pad


def back(pad):
    for part in ('dpad_north', 'dpad_south'):
        if ('joystick', part) in pad.sim.held:
            pad.sim.release(('joystick', part))
    return pad


for label, on in (('As the simulator assumes (the chord stays off while a bumper is held)', False),
                  ('The suspicion (a removal fires the chord anyway)', True)):
    print(f'\n{label}')
    # The thumbs rest on the sticks before the bumper goes down, so the helpers are on the stack under the W
    # layer and a thumb lift takes real layers off. With the bumper first the W layer answers the touch and
    # the helpers never land.
    for first in ('thumbs first, then R1', 'R1 first, then thumbs'):
        def start():
            state['on'] = False
            pad = Pad('default', start=('Base', 'Steering'), data=data)
            if first.startswith('thumbs'):
                pad.touch('LS').touch('RS').wait(400).hold('R1').wait(300)
            else:
                pad.hold('R1').wait(100).touch('LS').touch('RS').wait(400)
            state['on'] = on
            return pad

        def show(pad, what):
            print(f'   [{first}] {what:52s} W down: {"W" in pad.down()!s:5s} | Steering on: {pad.has("Steering")}')

        pad = start()
        pad.lift('RS').wait(100)
        show(pad, 'stick centred, the right thumb lifts')
        pad = start()
        half(pad, 'up').wait(60)
        back(pad).wait(400)
        wheels = len([x for x in pad.typed() if x.startswith('mouse_wheel')])
        show(pad, f'a plain tap up, thumbs stay on (wheel steps {wheels})')
        pad = start()
        half(pad, 'up').wait(60)
        pad.lift('RS').wait(100)
        show(pad, 'stick up in Modifier 1, the right thumb lifts')
        pad = start()
        half(pad, 'up').wait(60)
        pad.sim.release(('joystick', 'touch'))
        pad.wait(100)
        show(pad, 'stick up in Modifier 1, the left thumb loses touch')
