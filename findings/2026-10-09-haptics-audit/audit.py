"""Read-only inventory of haptic settings in both working layouts."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout
from tools.convert_runtime_ids import generate_lookup, ids_to_titles

LEVELS = {'0': 'Off', '1': 'Low', '2': 'Medium', '3': 'High'}
KEYS = ('haptic_intensity', 'haptic_intensity_override', 'flickstick_haptic_bump_per_angle')


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def table(rows, columns):
    return '\n'.join(['| ' + ' | '.join(columns) + ' |',
                      '|' + '|'.join('---' for _ in columns) + '|'] +
                     ['| ' + ' | '.join(cell(row[c]) for c in columns) + ' |' for row in rows])


def main():
    summary = {}
    for variant in ('default', 'alternative'):
        path = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        raw = path.read_text()
        original = json.loads(raw)
        readable, _ = ids_to_titles(raw, generate_lookup(original))
        data = json.loads(readable)
        layout = Layout(data)
        cm = layout.cm
        order = [int(k.split('_')[1]) for k in cm['action_layers']]
        assert order == sorted(order)
        assert [p['name'] for p in cm['preset']] == list(cm['actions']) + list(cm['action_layers'])
        assert [p['id'] for p in cm['preset']] == list(map(str, range(len(cm['preset']))))
        assert len(set(v['title'] for v in cm['action_layers'].values())) == len(cm['action_layers'])
        rows, unspecified = [], []
        owners = collections.defaultdict(list)
        for title, preset in layout.presets.items():
            for gid, source in preset.get('group_source_bindings', {}).items():
                owners[gid].append(f'{title}: {source}')

        def record(settings, context):
            found = False
            for key in KEYS:
                if key in settings:
                    value = settings[key]
                    rows.append({**context, 'setting': key, 'value': value,
                                 'level': LEVELS.get(value, 'Unknown') if key != KEYS[2] else 'Angle parameter, not intensity'})
                    found = found or key != KEYS[2]
            if not found:
                unspecified.append({**context, 'setting': 'haptic intensity', 'value': '',
                                    'level': 'Unspecified locally; inheritance/mode/client default may apply'})

        for gi, group in enumerate(cm['group']):
            base = {'group': group['id'], 'owners': '; '.join(owners[group['id']]) or 'Unreferenced',
                    'mode': group['mode'], 'scope': 'group', 'input': '', 'activator': '',
                    'bank': '', 'delay_start': '', 'long_press_time': '', 'hold_repeats': '',
                    'repeat_rate': '', 'bindings': '', 'path': f'controller_mappings/group/{gi}/settings'}
            record(group.get('settings', {}), base)
            for name, slot in group.get('inputs', {}).items():
                for bank in ('activators', 'disabled_activators'):
                    for kind, values in slot.get(bank, {}).items():
                        for index, entry in enumerate(values if isinstance(values, list) else [values]):
                            settings = entry.get('settings', {})
                            ctx = {**base, 'scope': 'activator', 'input': name, 'activator': f'{kind}[{index}]',
                                   'bank': bank, 'bindings': json.dumps(entry.get('bindings', {}).get('binding', [])),
                                   'path': f'controller_mappings/group/{gi}/inputs/{name}/{bank}/{kind}' +
                                           (f'/{index}' if isinstance(values, list) else '') + '/settings'}
                            for key in ('delay_start', 'long_press_time', 'hold_repeats', 'repeat_rate'):
                                ctx[key] = settings.get(key, '')
                            record(settings, ctx)

        # Independently scan the entire document to catch properties outside the
        # expected group/activator scopes rather than silently omitting them.
        raw_fields = collections.Counter()
        def walk(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if any(word in key.lower() for word in ('haptic', 'rumble', 'vibrat', 'feedback')):
                        assert key in KEYS, (key, value)
                        raw_fields[(key, str(value))] += 1
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)
        walk(original)
        assert raw_fields == collections.Counter((r['setting'], str(r['value'])) for r in rows)
        vdf = path.with_suffix('.vdf')
        vdf_fields = collections.Counter(re.findall(
            r'"(haptic_intensity|haptic_intensity_override|flickstick_haptic_bump_per_angle)"\s+"([^"\n]+)"',
            vdf.read_text()))
        assert raw_fields == vdf_fields, 'JSON/VDF haptic property counts differ'
        for name, records in (('explicit', rows), ('unspecified', unspecified)):
            with (HERE / f'{variant}-{name}.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(records[0]))
                writer.writeheader()
                writer.writerows(records)

        groups = [r for r in rows if r['scope'] == 'group']
        merged = collections.defaultdict(list)
        for r in rows:
            if r['scope'] != 'activator':
                continue
            key = tuple(r[k] for k in ('owners', 'mode', 'activator', 'bank', 'setting', 'value', 'level',
                                      'delay_start', 'long_press_time', 'hold_repeats', 'repeat_rate'))
            merged[key].append(r['input'])
        activators = []
        for key, inputs in merged.items():
            r = dict(zip(('owners', 'mode', 'activator', 'bank', 'setting', 'value', 'level',
                          'delay_start', 'long_press_time', 'hold_repeats', 'repeat_rate'), key))
            r['inputs'] = ', '.join(inputs)
            activators.append(r)
        activators.sort(key=lambda r: (-int(r['value']), r['owners'], r['activator']))
        text = f'# {variant.title()} haptic settings\n\nSource: `{path.relative_to(ROOT)}`, {cm["title"]}.\n\n'
        text += 'Every explicit setting is listed below, including Off. Rows combine inputs only when their owner, activator, level and timing match. CSV files retain each individual binding and path.\n\n'
        text += '## Mode settings\n\n' + table(groups, ['owners', 'mode', 'setting', 'value', 'level']) + '\n\n'
        text += '## Activator settings\n\n' + table(activators, ['owners', 'inputs', 'activator', 'level', 'delay_start', 'long_press_time', 'hold_repeats', 'repeat_rate']) + '\n'
        (HERE / f'{variant}.md').write_text(text)
        summary[variant] = {
            'title': cm['title'], 'source': str(path.relative_to(ROOT)),
            'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'vdf_sha256': hashlib.sha256(vdf.read_bytes()).hexdigest(),
            'groups': len(cm['group']), 'layers': len(cm['action_layers']), 'preflight': 'pass',
            'explicit_properties': len(rows),
            'intensity_counts': dict(collections.Counter(r['level'] for r in rows if r['setting'] != KEYS[2])),
            'counts_by_property': {key: dict(collections.Counter(r['value'] for r in rows if r['setting'] == key)) for key in KEYS},
            'activator_intensity_counts': dict(collections.Counter(r['level'] for r in rows if r['scope'] == 'activator')),
            'explicit_disabled_activator_properties': sum(r['bank'] == 'disabled_activators' for r in rows),
            'explicit_unreferenced_properties': sum(r['owners'] == 'Unreferenced' for r in rows),
            'unspecified_group_rows': sum(r['scope'] == 'group' for r in unspecified),
            'unspecified_activator_rows': sum(r['scope'] == 'activator' for r in unspecified),
            'json_vdf_haptic_property_count_match': True,
            'repeating_positive_haptics': [r for r in rows if r['scope'] == 'activator' and r['value'] != '0' and r['hold_repeats'] == '1'],
        }
        assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(raw.encode()).hexdigest()
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for variant, record in summary.items():
        print(variant, record['intensity_counts'], 'unspecified:', record['unspecified_group_rows'], 'groups,', record['unspecified_activator_rows'], 'activators')


if __name__ == '__main__':
    main()
