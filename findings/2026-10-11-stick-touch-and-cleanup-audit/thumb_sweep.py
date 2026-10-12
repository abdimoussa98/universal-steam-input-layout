"""Thumb lifts and touches during a Steering stick sequence, under every either-way setting of the simulator."""
import itertools, json, collections
from tests.scenario import Pad
data = json.load(open('neptune/single-set-default_hold-gyro_latest.json'))
SIDES = (('up', 'Steering | LS Up: Modifier 1', 'SCROLL_UP'), ('down', 'Steering | LS Down: Modifier 0', 'SCROLL_DOWN'))
DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))
STAGES = ('modifier', 'marker', 'window', 'scroll', 'cover')
SWITCHES = ('exposed_fires', 'any_removal_resets', 'reverse_ties', 'hold_releases')
def wheels(pad): return len([x for x in pad.typed() if x.startswith('mouse_wheel')])
def reach(pad, stage, direction):
    if stage == 'modifier': pad.push('LS', direction).wait(60)
    elif stage == 'marker': pad.push('LS', direction).wait(300)
    else:
        pad.flick('LS', direction).wait(20)
        if stage != 'window': pad.push('LS', direction).wait(60 if stage == 'scroll' else 300)
drops = collections.Counter(); runs = 0; taps = collections.Counter()
for way in itertools.product((True, False), repeat=len(SWITCHES)):
    options = dict(zip(SWITCHES, way))
    for (driver, owner, key), (direction, modifier, wheel), stage in itertools.product(DRIVERS, SIDES, STAGES):
        for thumb in ('LS off-on', 'LS off', 'RS lift', 'RS touch', 'RS lift-touch'):
            pad = Pad('default', start=('Base', 'Steering'), data=data, **options)
            pad.hold(driver).touch('LS')
            if thumb.startswith('RS lift'): pad.touch('RS')
            pad.wait(300)
            reach(pad, stage, direction)
            pad.mark()
            if thumb == 'LS off-on':
                pad.sim.release(('joystick', 'touch')); pad.wait(40); pad.sim.press(('joystick', 'touch')); pad.wait(40)
            elif thumb == 'LS off':
                pad.sim.release(('joystick', 'touch')); pad.wait(40)
            elif thumb == 'RS lift': pad.lift('RS').wait(40)
            elif thumb == 'RS touch': pad.touch('RS').wait(40)
            else: pad.lift('RS').wait(40).touch('RS').wait(40)
            runs += 1
            ok = pad.has('Steering', owner) and key in pad.down()
            if not ok:
                drops[(stage, thumb, tuple(k for k, v in options.items() if not v))] += 1
            # then the stick comes back: does a pending tap still scroll?
            for part in ('dpad_north', 'dpad_south', 'edge'):
                if ('joystick', part) in pad.sim.held: pad.sim.release(('joystick', part))
            pad.wait(400)
            if all(way):
                taps[(stage, thumb)] += wheels(pad)
            if not (pad.has('Steering', owner) and key in pad.down()):
                drops[('after return ' + stage, thumb, tuple(k for k, v in options.items() if not v))] += 1
print('runs:', runs, '| the driver layer or Steering lost under a held driver:', len(drops) and dict(drops) or 'never')
print('wheel steps after the thumb event, then the stick back (default switches; 4 runs each = 2 drivers x 2 directions):')
for stage in STAGES:
    print('  ', stage, {thumb: taps[(stage, thumb)] for thumb in ('LS off-on', 'LS off', 'RS lift', 'RS touch', 'RS lift-touch')})
# the same with no thumb event, for comparison
base = collections.Counter()
for (driver, owner, key), (direction, modifier, wheel), stage in itertools.product(DRIVERS, SIDES, STAGES):
    pad = Pad('default', start=('Base', 'Steering'), data=data)
    pad.hold(driver).touch('LS').wait(300); reach(pad, stage, direction); pad.mark().wait(40)
    for part in ('dpad_north', 'dpad_south', 'edge'):
        if ('joystick', part) in pad.sim.held: pad.sim.release(('joystick', part))
    pad.wait(400); base[stage] += wheels(pad)
print('   no thumb event:', dict(base))
