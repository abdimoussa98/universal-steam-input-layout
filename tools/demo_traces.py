"""Reference traces for the browser runtime, using the reviewed Python simulator."""
import json
from pathlib import Path
import subprocess
from steam_layout import controllers
from steam_layout.model import Layout
from steam_layout.simulator import Simulator
from tools.release import latest_release, tags

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'overlay/tests/fixtures/demo-traces.json'


def sequences():
    controls = ['button_diamond/button_' + c for c in 'abxy'] + [
        'dpad/dpad_' + d for d in ('north', 'east', 'south', 'west')] + [
        'switch/' + c for c in ('left_bumper', 'right_bumper', 'button_menu', 'button_escape',
                               'button_back_left', 'button_back_right', 'button_back_left_upper', 'button_back_right_upper')]
    controls += ['left_trigger/edge', 'right_trigger/edge', 'joystick/click', 'right_joystick/click']
    for control in controls:
        for duration in (60, 199, 200, 250, 500):
            yield f'{control} hold {duration}', [(0, control, True), (duration, control, False), (500, '', False)]
        yield f'{control} double hold', [(0, control, True), (60, control, False), (50, control, True), (400, control, False), (500, '', False)]
    for menu in ('switch/button_menu', 'switch/button_escape'):
        for stick in ('joystick/click', 'right_joystick/click'):
            for cancel in (False, True):
                sequence = [(0, menu, True), (60, stick, True)]
                sequence += [(60, menu if cancel else stick, False), (60, stick if cancel else menu, False)]
                sequence += [(100, 'button_diamond/button_a', True), (60, 'button_diamond/button_a', False)]
                # Repeat the transition to prove the stateful exit too.
                sequence += [(100, menu, True), (60, stick, True), (60, stick, False), (60, menu, False), (500, '', False)]
                yield f'{menu} + {stick} cancel={cancel}', sequence
        other = 'switch/button_escape' if menu.endswith('menu') else 'switch/button_menu'
        for duration in (60, 199, 200, 500):
            yield f'paired menus {menu} {duration}', [(0, menu, True), (400, other, True), (duration, other, False), (100, menu, False), (500, '', False)]
    for pad in ('left_trackpad', 'right_trackpad', 'center_trackpad'):
        for direction in ('dpad_north', 'dpad_east', 'dpad_south', 'dpad_west'):
            yield f'{pad} double touch {direction}', [(0, pad+'/touch', True), (60, pad+'/touch', False),
                (50, pad+'/touch', True), (0, pad+'/'+direction, True), (80, pad+'/'+direction, False), (0, pad+'/touch', False), (500, '', False)]
    for bumper in ('switch/left_bumper', 'switch/right_bumper', 'left_trigger/edge', 'right_trigger/edge'):
        yield f'{bumper} concurrent chord and release', [(0, bumper, True), (60, 'button_diamond/button_a', True),
            (100, bumper, False), (300, 'button_diamond/button_a', False), (500, '', False)]


def generate():
    traces = []
    releases = tags(cwd=ROOT)
    for controller in controllers.CONTROLLERS:
        version = latest_release(controller.name, cwd=ROOT, every=releases)
        for variant in controllers.VARIANTS:
            path = f'versions/{controller.name}/{version}/{controller.stem(variant)}_{version}.json'
            raw = subprocess.run(['git', 'show', f'{controller.name}-v{version}:{path}'], cwd=ROOT, check=True, capture_output=True).stdout
            layout = Layout(json.loads(raw))
            for name, events in sequences():
                if ('center_trackpad' in name) != (controller.name == 'dse') and 'trackpad' in name:
                    continue
                sim = Simulator(layout)
                steps = []
                for wait, control, down in events:
                    sim.wait(wait)
                    if control:
                        (sim.press if down else sim.release)(tuple(control.split('/')))
                    steps.append(dict(at=sim.now, control=control, down=down, stack=sim.stack, outputs=sim.down(), typed=sim.typed()))
                traces.append(dict(controller=controller.name, variant=variant, name=name, steps=steps))
    return json.dumps(traces, separators=(',', ':')) + '\n'


if __name__ == '__main__':
    OUTPUT.write_text(generate())
    print(f'Wrote {OUTPUT}')
