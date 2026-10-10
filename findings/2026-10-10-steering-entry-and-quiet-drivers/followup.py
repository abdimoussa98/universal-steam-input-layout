"""90.44 changes, applied only to a readable 90.43 layout."""
import re

from steam_layout.model import Layout, actions, entries, map_title

GUARD = 'Steering | LS: Entry Guard'
COMMAND = re.compile(r'controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}) ([01]) ([01])')


def transform(data, variant):
    if variant not in ('default', 'alternative'):
        raise ValueError(variant)
    layout = Layout(data)
    assert not any(re.search(r'controller_action (?:add_layer|remove_layer|hold_layer) \d+', command)
                   for group in layout.groups.values() for slot in group.get('inputs', {}).values()
                   for bank in ('activators', 'disabled_activators')
                   for _, entry in entries(slot.get(bank) or {}) for command in actions(entry))
    mapping = {} if variant == 'default' else {'L1': 'L2', 'R1': 'R2'}
    drivers = {map_title(title, mapping) for title in ('Steering | R1: W Key', 'Steering | L1: S Key')}
    report = {'quiet_entries': [], 'quiet_modes': [], 'removed_commands': []}

    edge = layout.active(GUARD)['joystick']['inputs']['edge']['activators']
    assert set(edge) == {'release'}
    chord = {'bindings': {'binding': f'controller_action remove_layer {{{{Base::{GUARD}}}}} 0 0, , '},
             'settings': {'gyro_ratchet_button_mask': '12' if variant == 'default' else '50331648',
                          'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                          'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}}
    layout.active(GUARD)['joystick']['inputs']['edge']['activators'] = {'chord': chord, **edge}
    report['guard_edge'] = chord

    def quiet(title, source, name, kind, entry):
        old = entry.get('settings', {}).get('haptic_intensity')
        entry.setdefault('settings', {})['haptic_intensity'] = '0'
        if old != '0':
            report['quiet_entries'].append({'layer': title, 'source': source, 'input': name,
                                            'activation': kind, 'before': old})

    # These groups are exclusively owned, active, and contain no disabled bank.
    # Fail rather than unintentionally mute another owner if that ever changes.
    for title in sorted(drivers):
        for gid, state in layout.presets[title]['group_source_bindings'].items():
            assert state.endswith(' active')
            assert [owner for owner, preset in layout.presets.items()
                    if gid in preset['group_source_bindings']] == [title]
            source = state.split()[0]
            group = layout.groups[gid]
            for name, slot in group.get('inputs', {}).items():
                assert not slot.get('disabled_activators')
                for kind, entry in entries(slot.get('activators', {})):
                    quiet(title, source, name, kind, entry)
        stick = layout.active(title)['joystick']
        assert stick['mode'] == 'dpad'
        stick.setdefault('settings', {})['haptic_intensity_override'] = '0'
        report['quiet_modes'].append({'layer': title, 'source': 'joystick'})

    incoming = []
    for title in ('Steering', GUARD):
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                for kind, entry in entries(slot.get('activators', {})):
                    if any(op == 'add_layer' and target in drivers for op, target in layout.layer_ops(entry)):
                        quiet(title, source, name, kind, entry)
                        incoming.append([title, source, name, kind])
    assert len(incoming) == 4
    report['driver_entries'] = incoming

    for title in ('Steering | LS Down: Modifier 0', 'Steering | LS Up: Modifier 1'):
        entry = layout.active(title)['joystick']['inputs']['edge']['activators']['release']
        quiet(title, 'joystick', 'edge', 'release', entry)
    for title in ('Steering | LS Down: Double Tap', 'Steering | LS Up: Double Tap'):
        entry = layout.active(title)['switch']['inputs']['always_on_action']['activators']['Full_Press']
        assert entry['settings']['delay_start'] == '150'
        quiet(title, 'switch', 'always_on_action', 'Full_Press', entry)

    counts = {'Steering': 0, 'Cursor Gyro': 0}
    for title in layout.presets:
        if not (title.startswith(('Gyro | ', 'Steering | ')) and title.endswith(': Modifier 2')):
            continue
        protected = {'Cursor Gyro'} | ({'Steering'} if title.startswith('Steering | ') else set())
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                for kind, entry in entries(slot.get('activators', {})):
                    if kind != 'release':
                        continue
                    stored = actions(entry)
                    keep = []
                    for command in stored:
                        match = COMMAND.search(command)
                        target = layout.resolve(match.group(2)) if match else None
                        if match and match.group(1) == 'remove_layer' and target in protected:
                            assert match.group(3) == '0'
                            assert match.group(4) == ('1' if target == 'Steering' else '0')
                            counts[target] += 1
                            report['removed_commands'].append({'layer': title, 'source': source,
                                'input': name, 'activation': kind, 'command': command})
                        else:
                            keep.append(command)
                    if keep != stored:
                        assert isinstance(entry['bindings']['binding'], list) and keep
                        entry['bindings']['binding'] = keep
    assert counts == {'Steering': 2, 'Cursor Gyro': 6}, counts
    assert len(report['quiet_entries']) == 54
    report['removal_counts'] = counts
    return report
