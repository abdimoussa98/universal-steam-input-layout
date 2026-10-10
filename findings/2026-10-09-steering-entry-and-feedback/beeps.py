"""One beep request per mode-changing release; leave feedback settings alone."""
import re

from steam_layout.model import Layout, actions, entries

COMMAND = re.compile(r'(controller_action (?:add_layer|remove_layer) (\{\{.+?\}\}) [01] )([01])(?=,)')


def apply(data, variant):
    layout = Layout(data)
    changed = []
    counts = {'gyro_releases': 0, 'steering_releases': 0, 'flags_changed': 0}
    for title in layout.presets:
        gyro = title.startswith('Gyro | ') and title.endswith(': Modifier 2')
        steering = title.startswith('Steering | ') and title.endswith(': Modifier 2')
        if not (gyro or steering):
            continue
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                for kind, entry in entries(slot.get('activators', {})):
                    ops = layout.layer_ops(entry)
                    if kind != 'release' or ('remove_layer', 'Gyro') not in ops:
                        continue
                    assert ('remove_layer', 'Steering') in ops
                    audible_target = 'Gyro' if gyro else 'Steering'
                    count = 0

                    def replace(command):
                        nonlocal count
                        found = COMMAND.search(command)
                        if not found:
                            return command
                        target = layout.resolve(found.group(2))
                        beep = str(int(target == audible_target))
                        if found.group(3) != beep:
                            count += 1
                        return COMMAND.sub(lambda match: match.group(1) + beep, command)

                    stored = entry['bindings']['binding']
                    entry['bindings']['binding'] = ([replace(command) for command in stored]
                                                    if isinstance(stored, list) else replace(stored))
                    assert sum(COMMAND.search(command).group(3) == '1'
                               for command in actions(entry) if COMMAND.search(command)) == 1
                    counts['gyro_releases' if gyro else 'steering_releases'] += 1
                    counts['flags_changed'] += count
                    changed.append({'layer': title, 'source': source, 'input': name,
                                    'beep_target': audible_target, 'flags_changed': count})
    assert counts['gyro_releases'] == 4 and counts['steering_releases'] == 2, counts
    return {'counts': counts, 'entries': changed}
