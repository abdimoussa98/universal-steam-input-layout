"""Prototype, nothing written: a Release on Start, Select, L1 and R1 in RTP: Double Tap that removes the window, then the button's family.

Run from the repository root, with the file window_left.py wrote:

    python3 findings/2026-10-04-stick-touch-and-menu-buttons/window_proto.py /tmp/left.json
"""
import sys, json, copy
from pathlib import Path
sys.path.insert(0, '.'); sys.path.insert(0, str(Path(__file__).resolve().parent))
import window_left as wl
from tests.scenario import layout_data
from steam_layout.model import Layout
left = json.load(open(sys.argv[1]))
FAMILY = {'bumpers': sorted(set(left['L1']) | set(left['R1'])), 'menu': sorted(set(left['Select']) | set(left['Start']))}
BUTTON = {'left_bumper': 'bumpers', 'right_bumper': 'bumpers', 'button_menu': 'menu', 'button_escape': 'menu'}
def fixed():
    data = copy.deepcopy(layout_data('default'))
    layout = Layout(data)
    ids = {t: str(i + 1) for i, k in enumerate(layout.order) for t in [layout.titles[k]]}
    group = layout.active(wl.WINDOW)['switch']
    for button, family in BUTTON.items():
        commands = [f'controller_action remove_layer {ids[t]} 0 0, , ' for t in [wl.WINDOW] + FAMILY[family]]
        acts = group['inputs'][button]['activators']
        acts['release'] = {'bindings': {'binding': list(reversed(commands))}, 'settings': {'haptic_intensity': '0'}}
    return data
print({k: len(v) for k, v in FAMILY.items()})
cases, stuck, left2 = wl.sweep(fixed())
print(f'with the Release: {stuck} of {cases} cases leave a layer on')
for b, c in left2.items(): print('  ', b, dict(c))
