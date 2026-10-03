"""Build isolated steering diagnostics, never edit delivery layouts.

Run with Python 3; --vdf also invokes the repository's verified serializer.
Candidates intentionally expose native behavior questions, not proven steering.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from tools.audit_command_budget import audit_layout

spec = importlib.util.spec_from_file_location('rule_test', HERE.parent / '2026-09-29-held-input-layer-transitions/build_rule_test_layout.py')
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)
EMPTY = 'controller_action empty_binding, , '
LAYERS = ('Steering', 'Entry Guard', 'W Owner', 'S Owner', 'Rearm')


def action(verb, title):
    return f'controller_action {verb}_layer {{{{Base::{title}}}}} 0 0, , '


def sequence(*commands):
    """Arguments are chronological; Steam binding arrays execute in reverse."""
    return list(reversed(commands))


def entry(binding, **settings):
    result = {'bindings': {'binding': binding}}
    if settings:
        result['settings'] = {k: str(v) for k, v in settings.items()}
    return result


def inp(**activators):
    return {'activators': activators, 'disabled_activators': {}}


def key(k):
    return f'key_press {k}, , '


def full(binding, **settings):
    return inp(Full_Press=entry(binding, **settings))


def build(variant='default', output_site='owner', clock=False):
    source = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
    original = json.loads(source.read_text())['controller_mappings']
    base_preset = original['preset'][0]['group_source_bindings']
    ls = next(g for g in original['group'] if base_preset.get(g['id']) == 'joystick active')
    mask = '12' if variant == 'default' else '50331651'
    titles = ('Steering', 'Clock Disturbance') if clock else LAYERS
    cm = copy.deepcopy(reference.build()['controller_mappings'])
    cm['title'] = f'Steering probe {variant} ' + ('clock' if clock else output_site)
    cm['description'] = 'Diagnostic only. Right Menu enter; Left Menu reset; D-pad Right reports F1-F6. See steering-native-probes/README.md.'
    cm['group'], cm['preset'], cm['action_layers'] = [], [], {}
    groups = []
    reset = sequence(*(action('remove', t) for t in reversed(titles)))

    def add_group(mode, source_name, inputs, settings, layer):
        gid = str(len(cm['group']))
        settings = dict(settings)
        if layer != 'Base':
            settings['layer'] = '1'
        cm['group'].append(reference.group(gid, mode, inputs, settings))
        groups.append((gid, source_name + ' active'))

    def controls(layer):
        mapping = {}
        for side, letter in [('right', 'W'), ('left', 'S')]:
            owner = letter + ' Owner'
            if clock or layer == 'Base':
                binding = full(EMPTY)
            elif layer in ('Steering', 'Entry Guard'):
                commands = [action('remove', 'Entry Guard'), action('add', owner)]
                if output_site == 'entry':
                    commands.append(key(letter))
                binding = full(sequence(*commands), interruptable=0)
            elif layer == owner:
                binding = inp(
                    Full_Press=entry(key(letter) if output_site == 'owner' else EMPTY, interruptable=0),
                    release=entry(sequence(action('remove', owner), action('add', 'Rearm'))))
            elif layer == 'Rearm':
                # A release is only a candidate. The held-any chord and stick
                # recovery independently exercise interruption/exposure rules.
                binding = inp(release=entry(action('remove', 'Rearm')),
                    chord=entry(EMPTY, gyro_ratchet_button_mask=mask,
                        gyro_ratchet_button_requireany_or_all=0, interruptable=0))
            else:
                binding = full(EMPTY)  # Opposite never emits opposing movement.
            mapping[side] = binding
        return mapping

    for index, layer in enumerate(('Base',) + titles):
        groups = []
        preset_name = f'Preset_{1000001 + index}'
        if index:
            cm['action_layers'][preset_name] = {'title': layer, 'legacy_set': '1',
                'set_layer': '1', 'parent_set_name': 'Preset_1000001'}
        enter = sequence(action('add', 'Steering'), *([] if clock else [action('add', 'Entry Guard')]))
        switches = {'button_menu': full(reset),
                    'button_escape': full(enter if layer == 'Base' else EMPTY)}
        drive = controls(layer)
        if variant == 'default':
            switches.update({f'{side}_bumper': binding for side, binding in drive.items()})
        else:
            for side, binding in drive.items():
                add_group('trigger', side+'_trigger', {'edge': binding},
                          {'deadzone_inner_radius': '0', 'adaptive_threshold': '0'}, layer)
        add_group('switches', 'switch', switches, {}, layer)
        stick = {name: copy.deepcopy(ls['inputs'][name]) for name in
                 ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west')}
        settings = copy.deepcopy(ls['settings'])
        if layer in ('W Owner', 'S Owner'):
            stick['dpad_north'] = full(EMPTY)
            stick['dpad_south'] = full(EMPTY)
        if layer == 'Entry Guard':
            # Candidate hysteresis: nominal 20%, enter near 10%, leave near 30%.
            settings.update(edge_binding_invert='1', edge_binding_radius='6553')
            stick['edge'] = full(action('remove', 'Entry Guard'), hold_repeats=1, repeat_rate=50)
        if layer == 'Rearm':
            # Center region overlaps movement region to avoid a sensing gap.
            settings.update(edge_binding_invert='1', edge_binding_radius='17000')
            recover = entry(action('remove', 'Rearm'), hold_repeats=1, repeat_rate=50)
            guard = entry(EMPTY, gyro_ratchet_button_mask=mask,
                          gyro_ratchet_button_requireany_or_all=0, interruptable=0)
            for name in list(stick):
                stick[name]['activators']['Full_Press'] = [stick[name]['activators']['Full_Press'], copy.deepcopy(recover)]
                # Output must not be interrupted by the guard; only recovery is.
                stick[name]['activators']['chord'] = copy.deepcopy(guard)
            stick['edge'] = inp(Full_Press=copy.deepcopy(recover), chord=copy.deepcopy(guard))
        if clock and layer == 'Steering':
            # F9/F10 instrument timing. F9 is deliberately NOT a vibration claim.
            stick['dpad_north'] = inp(Full_Press=[
                entry(key('W'), interruptable=0),
                entry(key('F9'), delay_start=2500, hold_repeats=1, repeat_rate=250, interruptable=0),
                entry(sequence(key('F10'), action('remove', 'Steering')), delay_start=5000, interruptable=0)])
            # B repeatedly removes an absent layer to probe global timer resets.
            add_group('four_buttons', 'button_diamond', {'button_b': full(action('remove', 'Clock Disturbance'), hold_repeats=1, repeat_rate=100)}, {}, layer)
        add_group('dpad', 'joystick', stick, settings, layer)
        add_group('dpad', 'dpad', {'dpad_east': full(key(f'F{index+1}'))},
                  {'requires_click': '0', 'layout': '0'}, layer)
        cm['preset'].append({'id': str(index), 'name': preset_name,
                            'group_source_bindings': dict(groups)})
    return {'controller_mappings': cm}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vdf', action='store_true')
    args = parser.parse_args()
    manifest = {}
    for variant in ('default', 'alternative'):
        for kind in ('owner', 'entry', 'clock', 'long-clock'):
            stem = f'{variant}-{kind}'
            data = build(variant, kind, clock=kind in ('clock','long-clock'))
            if kind=='long-clock':
                data['controller_mappings']['title'] += ' native-long-press'
                for g in data['controller_mappings']['group']:
                    a=g.get('inputs',{}).get('dpad_north',{}).get('activators',{})
                    full_entries=a.get('Full_Press')
                    if isinstance(full_entries,list) and len(full_entries)==3:
                        a['Full_Press']=full_entries[0]
                        a['Long_Press']=full_entries[1:]
                        for e in a['Long_Press']:
                            e['settings']['long_press_time']=e['settings'].pop('delay_start')
            report = audit_layout(data)
            if report['violations']:
                raise ValueError(report['violations'])
            readable = json.dumps(data, indent='\t') + '\n'
            numeric, count = titles_to_ids(readable, generate_lookup(data))
            assert '{{' not in numeric
            (HERE / (stem + '.readable.json')).write_text(readable)
            target = HERE / (stem + '.json')
            target.write_text(numeric)
            if args.vdf:
                subprocess.run(['node', str(ROOT/'tools'/'convert_vdf.mjs'), str(target)], check=True)
            manifest[stem] = {'sha256': hashlib.sha256(numeric.encode()).hexdigest(),
                              'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
