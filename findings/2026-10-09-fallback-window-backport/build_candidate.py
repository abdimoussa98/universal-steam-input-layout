"""90.39 testing candidate: 90.32's fallback window with compatible later fixes.

Writes this folder only. The live Neptune builder remains 90.38. Candidate
rules are local so keeping full-clear removals cannot affect frozen builders.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout import changes, exceptions
from steam_layout.fixes import PIPELINE, apply_all
from steam_layout.model import Layout, actions, entries, map_title
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

VERSION = '90.39'
VARIANTS = ('default', 'alternative')
WINDOW = 'Steering | LS: Fallback Window'
HOLD = 'Steering | LS: Fallback Hold'
GUARD = 'Steering | LS: Entry Guard'
RTP = ('RTP: Entry Point', 'RTP: Tap Cover', 'RTP: Circular Scroll',
       'RTP: Click Entry Point', 'RTP: Mouse Buttons', 'RTP: Middle Click')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


previous = module('window_backport_previous', 'findings/2026-10-04-fallback-window-replacements/build_candidate.py')
ordering = module('window_backport_order', 'findings/2026-10-06-cleanup-entry-order/build_candidate.py')


def title(variant, value):
    return map_title(value, {'L1': 'L2', 'R1': 'R2'}) if variant == 'alternative' else value


def op(kind, target, beep=False):
    return f'controller_action {kind}_layer {{{{Base::{target}}}}} 0 {int(beep)}, , '


def path(variant):
    return HERE / f'single-set-{variant}-fallback-window_hold-gyro_{VERSION}.json'


def snapshot(variant, version='90.32'):
    return ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'


def readable(data):
    text, _ = ids_to_titles(json.dumps(data), generate_lookup(data))
    return json.loads(text)


def preflight(data):
    cm = data['controller_mappings']
    keys = [int(k.split('_')[1]) for k in cm['action_layers']]
    assert keys == sorted(keys)
    assert [p['name'] for p in cm['preset']] == list(cm['actions']) + list(cm['action_layers'])
    assert [p['id'] for p in cm['preset']] == list(map(str, range(len(cm['preset']))))
    assert len({v['title'] for v in cm['action_layers'].values()}) == len(keys) == 90


def local_rules(data):
    config = json.loads(exceptions.REGISTER.read_text())
    config['exceptions'].append({
        'rule': 'R132', 'scope': {'layers': [WINDOW, 'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'],
                                'removes': list(RTP[:3]), 'where': HOLD},
        'status': 'allow', 'why': '90.39 P4/P5: RTP held or double-tapped before Steering window entry leaves '
        'its Tap Cover or Circular Scroll below the window. The pad release must remove those helpers after '
        'the window. The cleanup chain approximation misses this arrival order and otherwise drops the removals.',
        'decided': 'Implementation review of approved backport plan, 2026-10-09', 'todo': None})
    # Candidate-only allowances: deliberate emergency clears may name stale
    # helpers that a normal backward chain never puts below a Gyro modifier.
    for owner, other in (('L1!R1', 'R1!L1'), ('R1!L1', 'L1!R1')):
        config['exceptions'].append({
            'rule': 'R132', 'scope': {
                'layers': [f'Gyro | {owner}: Modifier 2'],
                'removes': ['L1: Modifier 0', 'R1: Modifier 1', 'L1!R1: Modifier 2', 'R1!L1: Modifier 2',
                            f'Gyro | {other}: Modifier 2', 'Steering'] +
                           [t for t in Layout(data).presets if t.startswith('Steering |')],
                'where': HOLD},
            'status': 'allow', 'why': '90.39 testing candidate: retain the 90.33 full-clear intent for the restored '
            '90.32 Steering family, including stale helpers. Window removals execute first. '
            'This local register is never used by the historical or live builders.',
            'decided': 'Author approved fallback-window backport plan, 2026-10-09', 'todo': None})
    return config


def pipeline(data, rules):
    expanded = exceptions.expand(rules)
    window = exceptions.window(json.loads((ROOT / 'steam_layout/traced_stacks.json').read_text()), rules['exceptions'])
    return {name: fix(data, expanded if name == 'cleanup_lists' else window)
            if name in ('cleanup_lists', 'window_routes') else fix(data) for name, fix in PIPELINE}


def baseline(variant):
    saved = json.loads(snapshot(variant).read_text())
    preflight(saved)
    built = previous.Builder(variant).finish()
    apply_all(built)
    numeric, _ = titles_to_ids(json.dumps(built), generate_lookup(built))
    a, b = copy.deepcopy(json.loads(numeric)), copy.deepcopy(saved)
    for data in (a, b):
        for field in ('title', 'description'):
            data['controller_mappings'].pop(field)
    assert a == b, 'frozen 90.32 builder no longer reproduces snapshot'
    # Restore the reviewed release metadata, not the builder's placeholder.
    for field in ('title', 'description'):
        built['controller_mappings'][field] = saved['controller_mappings'][field]
    return built


def patch(data, variant):
    layout = Layout(data)
    log = {'cleanup_order': ordering.reorder(data), 'rtp_completions': []}
    for owner in ('Base', 'Steering', 'Cursor Gyro'):
        for button, mask in (('button_menu', '4096'), ('button_escape', '16384')):
            slot = layout.active(owner)['switch']['inputs'][button]
            assert list(slot['activators']) == ['Full_Press']
            entry = slot['activators']['Full_Press']
            entry['settings'] = {'gyro_ratchet_button_mask': mask, 'hold_repeats': '1', 'interruptable': '0'}
            slot['activators'] = {'chord': entry}
    for side, button in (('Left', 'button_escape'), ('Right', 'button_menu')):
        for owner in (f'Menu {side}: Entry Point', f'Menu {side}: Fn Layer', f'Stateful | Menu {side}: Entry Point'):
            entry = layout.active(owner)['switch']['inputs'][button]['activators']['chord']
            assert not entry.get('settings', {}).get('delay_start')
            entry['settings'].update(hold_repeats='1', interruptable='0')

    steering_family = [t for t in layout.presets if t.startswith('Steering |')]
    windows = [t for t in steering_family if t == WINDOW or t.endswith(': Double Tap')]
    for owner, other in (('L1!R1', 'R1!L1'), ('R1!L1', 'L1!R1')):
        groups = layout.active(title(variant, f'Gyro | {owner}: Modifier 2'))
        extras = [title(variant, t) for t in ('L1: Modifier 0', 'R1: Modifier 1', 'L1!R1: Modifier 2',
                   'R1!L1: Modifier 2', f'Gyro | {other}: Modifier 2')] + steering_family + ['Steering']
        for group in groups.values():
            for slot in group.get('inputs', {}).values():
                release = slot.get('activators', {}).get('release')
                if not release or ('remove_layer', 'Gyro') not in layout.layer_ops(release):
                    continue
                commands = actions(release)
                present = {t for kind, t in layout.layer_ops(release) if kind == 'remove_layer'}
                added = [op('remove', t, t == 'Steering') for t in extras if t not in present and t not in windows]
                # Window-first in execution; retain the relative order/flags of
                # existing release commands. Ordinary extras finish the clear.
                release['bindings']['binding'] = list(reversed(added)) + commands + [op('remove', t) for t in reversed(windows)]

    group = layout.active('Steering')['right_trackpad']
    assert list(group['inputs']) == ['touch']
    assert actions(group['inputs']['touch']['activators']['Full_Press']) == ['controller_action empty_binding, , ']
    del layout.presets['Steering']['group_source_bindings'][group['id']]

    # These windows were built when Steering blocked RTP entry. A touch
    # release must now also clear the ordinary pad helpers underneath.
    for owner in (WINDOW, 'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'):
        release = layout.active(owner)['right_trackpad']['inputs']['touch']['activators']['release']
        assert layout.layer_ops(release)[0] == ('remove_layer', owner)
        release['bindings']['binding'] = [op('remove', t) for t in reversed(RTP[:3])] + actions(release)

    for owner in layout.presets:
        if not owner.startswith(('Steering |', 'Stateful |')):
            continue
        groups = layout.active(owner)
        delayed = {target for group in groups.values() for slot in group.get('inputs', {}).values()
                   for _, entry in entries(slot.get('activators', {}))
                   if int(entry.get('settings', {}).get('delay_start', '0'))
                   for kind, target in layout.layer_ops(entry) if kind == 'add_layer'}
        for source, group in groups.items():
            for name, slot in group.get('inputs', {}).items():
                for kind, entry in entries(slot.get('activators', {})):
                    completes = int(entry.get('settings', {}).get('delay_start', '0')) or (kind == 'release' and name == 'touch')
                    if completes and any(k == 'add_layer' and t in delayed for k, t in layout.layer_ops(entry)):
                        entry['bindings']['binding'] = [op('remove', t) for t in reversed(RTP)] + actions(entry)
                        log['rtp_completions'].append([owner, source, name, kind])
    assert len(log['rtp_completions']) == 18
    return log


def build(variant):
    data = baseline(variant)
    rules = local_rules(readable(json.loads(snapshot('default').read_text()))) if variant == 'alternative' else local_rules(data)
    log = patch(data, variant)
    log['fixes'] = pipeline(data, rules)
    log['final_cleanup_order'] = ordering.reorder(data)
    before = json.dumps(data)
    log['fixed_point'] = pipeline(data, rules)
    assert json.dumps(data) == before, 'fix pipeline must reach a fixed point'
    cm = data['controller_mappings']
    cm['title'] = f'single-set-{variant} :: always-gyro :: fallback-window testing :: {VERSION}'
    old = 'While steering, right-pad touch modes such as circular scroll are off, so the pad is just the mouse, and right-stick turn assist is off, so the gyro also stays on while the right stick turns.'
    assert old in cm['description']
    cm['description'] = cm['description'].replace(old,
        'Right-pad gestures, including circular scroll, work in Steering outside timed windows. '
        'RTP Double Tap can briefly suppress left-stick movement for 150 ms. '
        'Right-stick turn assist stays off in Steering, so gyro stays on while the right stick turns.')
    preflight(data)
    text = json.dumps(data, indent='\t') + '\n'
    numeric, count = titles_to_ids(text, generate_lookup(data))
    assert '{{' not in numeric
    restored, _ = ids_to_titles(numeric, generate_lookup(data))
    assert json.loads(restored) == data
    log['resolved_references'] = count
    return data, json.loads(numeric), rules, log


def main():
    manifest = {'version': VERSION, 'role': 'testing candidate', 'baseline': '90.32', 'variants': {}}
    for variant in VARIANTS:
        data, numeric, rules, log = build(variant)
        path(variant).write_text(json.dumps(numeric, indent='\t') + '\n')
        (HERE / f'{variant}.readable.json').write_text(json.dumps(data, indent='\t') + '\n')
        (HERE / 'candidate-rules.json').write_text(json.dumps(rules, indent=2) + '\n')
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(log, indent=2) + '\n')
        for version in ('90.32', '90.38'):
            report = changes.diff(json.loads(snapshot(variant, version).read_text()), numeric)
            (HERE / f'{variant}-changes-from-{version}.txt').write_text(changes.text(report, version, VERSION) + '\n')
        manifest['variants'][variant] = {
            'source_sha256': hashlib.sha256(snapshot(variant).read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(path(variant).read_bytes()).hexdigest(),
            'json': str(path(variant).relative_to(ROOT)), 'layer_count': 90, 'device_status': 'UNTESTED'}
        print(path(variant).relative_to(ROOT), flush=True)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
