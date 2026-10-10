"""90.43: preserve held driving owners and recover stale owners without re-entry."""
import copy

from steam_layout.flow_model import chord_condition
from steam_layout.model import EMPTY, Layout, TARGET, actions, entries, map_title


MODIFIERS = ('Steering | LS Down: Modifier 0', 'Steering | LS Up: Modifier 1')
OWNERS = ('Steering | R1: W Key', 'Steering | L1: S Key')
INPUTS = {
    ('button_diamond', 'button_a'), ('button_diamond', 'button_b'),
    ('button_diamond', 'button_x'), ('button_diamond', 'button_y'),
    ('dpad', 'dpad_north'), ('dpad', 'dpad_south'),
    ('dpad', 'dpad_east'), ('dpad', 'dpad_west'),
    ('switch', 'button_escape'), ('switch', 'button_menu'),
    ('joystick', 'click'), ('right_joystick', 'click'),
    ('right_joystick', 'edge'),
}


def apply(data, variant):
    """Scope 26 modifier recoveries and guard four owner direction entries.

    Entry Guard transformation runs first. Preserve all conditions, activator
    settings, output bindings, retained command order and other release paths.
    Cleanups.protects_held_owner enforces this scope during later fix passes.
    Each owner direction also needs its own guard and fallback: otherwise a
    missed driver release can re-add the modifier every time it is recovered
    while the direction stays held. Its existing edge cleanup owns that exit.
    """
    layout = Layout(data)
    assert 'Steering | LS: Entry Guard' in layout.presets
    assert 'Steering | LS: Fallback Hold' not in layout.presets
    mapping = {'L1': 'L2', 'R1': 'R2'} if variant == 'alternative' else {}
    owners = {map_title(title, mapping) for title in OWNERS}
    changed = []
    for title in MODIFIERS:
        found = set()
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                control = (source, name)
                if control not in INPUTS:
                    continue
                acts = slot.get('activators', {})
                conditions = [chord_condition(entry.get('settings', {}))
                              for kind, entry in entries(acts) if kind == 'chord']
                assert len(conditions) == 2 and all(c and c.known and c.mode == 'all' for c in conditions), (title, control)
                assert all(any(c[0] == 'joystick' and c[1].startswith(('dpad_', 'edge'))
                               for c in condition.controls()) for condition in conditions), (title, control)
                recovery = acts['Full_Press']
                assert recovery.get('settings', {}).get('hold_repeats') == '1'
                assert recovery.get('settings', {}).get('interruptable') != '0'
                before = actions(recovery)
                commands = [command for command in before
                            if not ((match := TARGET.search(command)) and match.group(1) == 'remove_layer'
                                    and layout.resolve(match.group(2)) in owners)]
                assert commands and ('remove_layer', title) in layout.layer_ops(recovery)
                recovery['bindings']['binding'] = commands[0] if len(commands) == 1 else commands
                found.add(control)
                changed.append({'layer': title, 'source': source, 'input': name,
                                'removed_owner_commands': len(before) - len(commands)})
        assert found == INPUTS, (title, found ^ INPUTS)
    assert len(changed) == 26
    direction_entries = []
    for owner, mask in ((OWNERS[0], 1 << (24 if variant == 'alternative' else 2)),
                        (OWNERS[1], 1 << (25 if variant == 'alternative' else 3))):
        title = map_title(owner, mapping)
        inputs = layout.active(title)['joystick']['inputs']
        recovery = inputs['edge']['activators']['Full_Press']
        assert recovery.get('settings', {}).get('hold_repeats') == '1'
        assert recovery.get('settings', {}).get('interruptable') != '0'
        for name, target in (('dpad_north', MODIFIERS[1]), ('dpad_south', MODIFIERS[0])):
            acts = inputs[name]['activators']
            entry = copy.deepcopy(acts.get('chord', acts['Full_Press']))
            assert layout.layer_ops(entry) == [('add_layer', target)], (title, name)
            assert entry['settings']['hold_repeats'] == '1' and entry['settings']['repeat_rate'] == '50'
            entry['settings'].update(gyro_ratchet_button_mask=str(mask), gyro_ratchet_button_requireany_or_all='0')
            inputs[name]['activators'] = {'Full_Press': copy.deepcopy(recovery), 'chord': entry}
            direction_entries.append({'layer': title, 'input': name, 'owner_mask': str(mask), 'target': target})

    # Those new owner recoveries must remain recoverable through the existing
    # directional modifiers and covers. Reuse each upper layer's established
    # driver-only edge cleanup; do not broaden the deflection-conditioned 26
    # entries above. Always On windows retain their intentional isolation.
    upper_entries = []
    for title, primary, opposite in ((MODIFIERS[0], 'dpad_south', 'dpad_north'),
                                     (MODIFIERS[1], 'dpad_north', 'dpad_south')):
        inputs = layout.active(title)['joystick']['inputs']
        acts = inputs[primary]['activators']
        resets = [entry for kind, entry in entries(acts)
                  if kind == 'Full_Press' and entry.get('settings', {}).get('interruptable') == '0']
        assert len(resets) == 1 and resets[0]['settings']['repeat_rate'] == '250'
        inputs[primary]['activators'] = {
            'Full_Press': [copy.deepcopy(inputs['edge']['activators']['Full_Press']), copy.deepcopy(resets[0])],
            'chord': copy.deepcopy(acts['chord']),
        }
        # Reversal already leaves the old modifier. Repeat makes this a
        # guaranteed cancellation when it is exposed under a held direction.
        inputs[opposite]['activators']['Full_Press'].setdefault('settings', {})['hold_repeats'] = '1'
        upper_entries.extend({'layer': title, 'input': name} for name in (primary, opposite))

    mask = str((1 << 24) | (1 << 25)) if variant == 'alternative' else '12'
    for title in ('Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'):
        inputs = layout.active(title)['joystick']['inputs']
        for name in ('dpad_north', 'dpad_south'):
            acts = inputs[name]['activators']
            if title.endswith('LS: Tap Cover'):
                output = {'bindings': {'binding': EMPTY + ', , '}, 'settings': {'interruptable': '0'}}
            else:
                output = copy.deepcopy(acts.get('chord', acts['Full_Press']))
                assert output['settings']['delay_start'] == '5' and output['settings']['repeat_rate'] == '50'
            output['settings'].update(gyro_ratchet_button_mask=mask, gyro_ratchet_button_requireany_or_all='0')
            inputs[name]['activators'] = {
                'Full_Press': copy.deepcopy(inputs['edge']['activators']['Full_Press']),
                'chord': output,
                **({'release': copy.deepcopy(acts['release'])} if 'release' in acts else {}),
            }
            upper_entries.append({'layer': title, 'input': name})
    return {'entries_reviewed': len(changed), 'entries': changed,
            'owner_direction_entries': direction_entries, 'upper_direction_recovery': upper_entries}
