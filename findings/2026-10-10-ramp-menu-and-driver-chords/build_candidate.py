"""90.46: atomic ramp/menu handoffs and repeating Steering driver chords."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

PREVIOUS = ROOT / 'findings/2026-10-10-right-stick-sensitivity/build_candidate.py'
spec = importlib.util.spec_from_file_location('driver_chords_previous', PREVIOUS)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
preflight = previous.previous.preflight
RAMPS = ('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1')
GUARD = 'Steering | LS: Entry Guard'


def command(op, title):
    return f'controller_action {op}_layer {{{{Base::{title}}}}} 0 0, , '


def drivers(variant):
    if variant == 'default':
        return (('switch', 'left_bumper', 'L1', 'S', '8'),
                ('switch', 'right_bumper', 'R1', 'W', '4'))
    return (('left_trigger', 'edge', 'L2', 'S', '33554434'),
            ('right_trigger', 'edge', 'R2', 'W', '16777217'))


def transform(data, variant):
    layout = Layout(data)
    changes = {'menu_entries': [], 'driver_entries': [], 'mod2_entries': [],
               'gyro_off_driver_exits': []}
    # Cleanup and contextual menu entry must finish in one array. A standalone
    # ramp removal exposes the held RS and can rebuild the ramp before the menu.
    for title in ('Base', 'Steering', GUARD):
        group = layout.active(title)['switch']
        for name in ('button_menu', 'button_escape'):
            kind = 'Start_Press' if title == GUARD else 'chord'
            entry = group['inputs'][name]['activators'][kind]
            assert not any(op == 'remove_layer' and target in RAMPS
                           for op, target in layout.layer_ops(entry))
            entry['bindings']['binding'] = actions(entry) + [command('remove', t) for t in RAMPS]
            changes['menu_entries'].append([title, name])

    for title in ('Steering', GUARD):
        for source, name, side, key, mask in drivers(variant):
            node = layout.active(title)[source]['inputs'][name]
            old = node['activators']
            assert set(old) == {'Full_Press', 'chord'}
            entry = copy.deepcopy(old['Full_Press'])
            assert len(layout.layer_ops(entry)) == 5
            entry['bindings']['binding'] = [c for c in actions(entry)
                                           if c not in {command('remove', t) for t in RAMPS}]
            entry['settings'].update(gyro_ratchet_button_mask=mask,
                                     gyro_ratchet_button_requireany_or_all='0',
                                     interruptable='0')
            assert entry['settings']['hold_repeats'] == '1'
            assert entry['settings']['repeat_rate'] == '50'
            assert entry['settings']['haptic_intensity'] == '0'
            assert layout.layer_ops(entry) == [('remove_layer', GUARD),
                                                ('add_layer', f'Steering | {side}: {key} Key')]
            # The opposite-button empty chord cannot suppress another chord;
            # remove it along with the old Regular Press entry.
            node['activators'] = {'chord': entry}
            changes['driver_entries'].append([title, source, name])

    for source, name, side, key, mask in drivers(variant):
        title = f'Steering | {side}: {key} Key'
        other = next(d for d in drivers(variant) if d[2] != side)
        entry = layout.active(title)[other[0]]['inputs'][other[1]]['activators']['chord']
        assert len(layout.layer_ops(entry)) == 11
        assert 'hold_repeats' not in entry['settings']
        # Both controls may already be held when the self-chord adds its owner.
        # Repetition lets that owner's existing Mod 2 chord run on held input.
        entry['settings'].update(hold_repeats='1', repeat_rate='50')
        changes['mod2_entries'].append([title, other[0], other[1]])

        # The initial gyro-off stage can also be entered directly from Steering
        # (and persist below the ramp threshold), without a menu handoff.
        group = layout.active('Gyro Off Ramp Up')[source]
        assert name not in group.get('inputs', {})
        group.setdefault('inputs', {})[name] = {'activators': {'Full_Press': {
            'bindings': {'binding': [command('remove', t) for t in RAMPS]},
            'settings': {'hold_repeats': '1', 'repeat_rate': '50',
                         'interruptable': '0', 'haptic_intensity': '0'},
        }}}
        changes['gyro_off_driver_exits'].append([source, name])
    return changes


def build_from(numeric, variant):
    preflight(numeric)
    assert numeric['controller_mappings']['title'].endswith(' :: 90.45')
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    before = Layout(copy.deepcopy(data))
    report = {'previous_builder_sha256': hashlib.sha256(PREVIOUS.read_bytes()).hexdigest(),
              'changes': transform(data, variant)}
    expected = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    assert data == expected, 'Inspect any unexpected pipeline edits before installation'
    preflight(data)
    after = Layout(data)
    assert after.order == before.order and after.titles == before.titles
    for title in ('Base', *RAMPS):
        assert after.active(title)['right_joystick'] == before.active(title)['right_joystick']
    data['controller_mappings']['title'] = data['controller_mappings']['title'].rsplit(' :: ', 1)[0] + ' :: 90.46'
    # Descriptions still accurately describe both variants' features and controls.
    text, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in text
    restored, _ = ids_to_titles(text, generate_lookup(data))
    assert json.loads(restored) == data
    return json.loads(text), report


def build(variant):
    numeric, _ = previous.build(variant)
    return build_from(numeric, variant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--from-working', action='store_true',
                        help='Use working 90.45, requiring equality with the previous validated candidate')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        live = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        if args.from_working:
            numeric = json.loads(live.read_text())
            assert numeric == json.loads((previous.HERE / f'{variant}-candidate.json').read_text())
            data, report = build_from(numeric, variant)
        else:
            data, report = build(variant)
        text = json.dumps(data, indent='\t') + '\n'
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        if args.install:
            live.write_text(text)
        print(variant, report['changes'], flush=True)


if __name__ == '__main__':
    main()
