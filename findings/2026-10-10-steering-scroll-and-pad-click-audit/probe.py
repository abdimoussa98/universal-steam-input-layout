"""Read-only 90.48 scroll/click characterization; no analog or native haptic model."""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout, actions, entries
from tests.scenario import Pad
from tools.convert_runtime_ids import generate_lookup, ids_to_titles
HERE = Path(__file__).resolve().parent


def record(p):
    return {'stack': p.names(), 'outputs': p.typed(), 'down': p.down(),
            'haptics': p.seen('haptic'), 'events': p.sim.log[p._mark:]}


def main():
    result = {'sources': {}, 'scroll': [], 'clicks': [], 'feedback_bindings': []}
    for variant in ('default', 'alternative'):
        path = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        numeric = json.loads(path.read_text()); cm = numeric['controller_mappings']
        order = list(cm['actions']) + list(cm['action_layers'])
        nums = [int(k.split('_')[1]) for k in cm['action_layers']]
        assert nums == sorted(nums)
        assert [p['name'] for p in cm['preset']] == order
        assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(cm['preset']))]
        assert all(n == 1 for n in collections.Counter(x['title'] for x in cm['action_layers'].values()).values())
        readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
        data = json.loads(readable); layout = Layout(data)
        result['sources'][variant] = {'title': cm['title'], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                      'preflight': 'passed'}
        cases = ('single_flick', 'shallow_flick', 'hold_300', 'double_hold', 'flick_lift_left', 'flick_lift_right')
        for gyro, driver, direction, case, exposed, reverse in itertools.product(
                (False, True), ('L1', 'R1'), ('up', 'down'), cases, (True, False), (False, True)):
            p = Pad(variant, start=('Base', 'Gyro', 'Steering') if gyro else ('Base', 'Steering'),
                    data=data, exposed_fires=exposed, reverse_ties=reverse)
            p.hold(driver).wait(50)
            if case == 'flick_lift_right': p.touch('RS').wait(50)
            p.mark()
            part = 'dpad_north' if direction == 'up' else 'dpad_south'
            if case == 'single_flick': p.flick('LS', direction).wait(200)
            elif case == 'shallow_flick': p.touch('LS').hold('LS ' + part).wait(60).let_go('LS ' + part).wait(300)
            elif case == 'hold_300': p.push('LS', direction).wait(300).recentre('LS').wait(200)
            elif case == 'double_hold': p.flick('LS', direction).wait(50).push('LS', direction).wait(300)
            elif case == 'flick_lift_left': p.flick('LS', direction).lift('LS').wait(200)
            elif case == 'flick_lift_right': p.flick('LS', direction).lift('RS').wait(200)
            wheels = [o for o in p.typed() if 'mouse_wheel' in o]
            assert len(wheels) == (1 if case == 'single_flick' else 6 if case == 'double_hold' else 0)
            if case == 'shallow_flick':
                assert p.has('Steering | LS Up: Modifier 1' if direction == 'up' else 'Steering | LS Down: Modifier 0')
                assert not p._held('LS', part) and not p._held('LS', 'edge')
            result['scroll'].append({'variant': variant, 'gyro': gyro, 'driver': driver, 'direction': direction,
                'case': case, 'exposed_fires': exposed, 'reverse_ties': reverse, **record(p)})
        for context, stick, where, exposed in itertools.product(
                ('Base', 'Steering', 'W', 'S', 'Mod0', 'Mod1', 'Mod0 covered', 'Mod1 covered'),
                ('LP', 'RP'), ('centre', 'left', 'up'), (True, False)):
            p = Pad(variant, start=('Base',) if context == 'Base' else ('Base', 'Steering'),
                    data=data, exposed_fires=exposed)
            if context in ('W', 'S'): p.hold('R1' if context == 'W' else 'L1').wait(50)
            if context.startswith('Mod'):
                p.hold('R1').push('LS', 'up' if 'Mod1' in context else 'down').wait(250 if 'covered' in context else 30)
            p.mark().press_pad(stick, where).wait(600)
            duplicate = context in ('Mod0', 'Mod1') and stick == 'RP' and exposed
            assert len(p.seen('haptic')) == (2 if duplicate else 1)
            result['clicks'].append({'variant': variant, 'context': context, 'pad': stick, 'where': where,
                                     'exposed_fires': exposed, **record(p)})
        for title in ('Base', 'LTP: Click Entry Point', 'RTP: Click Entry Point', 'LTP: Middle Click',
                      'RTP: Middle Click', 'LTP: Arrow Keys', 'RTP: Mouse Buttons'):
            for source, group in layout.active(title).items():
                if source not in ('left_trackpad', 'right_trackpad'): continue
                node = {'variant': variant, 'owner': title, 'source': source, 'mode': group['mode'],
                        'mode_settings': group.get('settings', {}), 'activators': []}
                for name, slot in group.get('inputs', {}).items():
                    for kind, entry in entries(slot.get('activators', {})):
                        if 'haptic_intensity' in entry.get('settings', {}):
                            node['activators'].append({'input': name, 'kind': kind, 'settings': entry['settings'],
                                                       'actions': actions(entry)})
                result['feedback_bindings'].append(node)
    summary = {'scroll_cases': len(result['scroll']), 'click_cases': len(result['clicks']),
               'duplicate_click_entry_haptic_cases': sum(len(r['haptics']) > 1 for r in result['clicks']),
               'all_characterization_assertions_passed': True,
               'limits': ['Binary input simulation cannot measure physical stick thresholds.',
                          'Haptic events omit mode feedback and output feedback on held-input landing.',
                          'Native layer timing and exposed held-input behavior remain assumptions.']}
    (HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
