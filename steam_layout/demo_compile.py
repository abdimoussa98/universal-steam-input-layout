"""Compile immutable Steam layouts into the browser runtime's executable model.

No binding table is authored here: ordering, inheritance, conditions and commands
come from the layout. Unknown behavior fails closed. See demo_coverage.py for
the explicit distinction between runtime semantics and analog approximations.
"""
import collections
import hashlib
import json
import re

from .flow_model import chord_condition
from .model import Layout, actions, entries
from .demo_coverage import coverage
from .convert import gyro_layer

SCHEMA = 1
KINDS = {'Full_Press', 'Start_Press', 'release', 'chord', 'Soft_Press', 'Long_Press', 'Double_Press'}
COMMAND = re.compile(r'controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|\d+)(?: (\d+))?(?: (\d+))?')


def condition(settings):
    found = chord_condition(settings)
    if found is None:
        return None
    if not found.known:
        raise ValueError(found.label)
    return dict(all=found.mode == 'all', groups=[['/'.join(c) for c in g] for g in found.groups])


def command(raw, layout, layers, groups):
    match = COMMAND.match(raw)
    if match:
        return dict(op=match[1], target=layers[layout.resolve(match[2])], beep=match[4] == '1')
    words = raw.split(',')[0].split()
    if words == ['controller_action', 'empty_binding']:
        return dict(op='empty')
    if len(words) == 2 and words[0] in {'key_press', 'mouse_button', 'xinput_button', 'mouse_wheel'}:
        return dict(op=words[0], value=words[1])
    if len(words) == 3 and words[0] == 'mode_shift' and words[2] in groups:
        return dict(op='mode_shift', source=words[1], target=groups[words[2]])
    raise ValueError(f'Unknown demo command: {raw}')


def compile_layout(raw, *, controller, variant, version, tag):
    layout = Layout(json.loads(raw))
    cm = layout.cm
    keys = [int(k.split('_')[1]) for k in cm['action_layers']]
    if keys != sorted(keys) or [p['name'] for p in cm['preset']] != layout.order:
        raise ValueError('Layer/preset order mismatch')
    if [p['id'] for p in cm['preset']] != [str(i) for i in range(len(cm['preset']))]:
        raise ValueError('Nonsequential preset IDs')
    if len(set(layout.titles.values())) != len(layout.titles):
        raise ValueError('Duplicate titles')
    layer_ids = {title: i for i, title in enumerate(layout.presets)}
    group_ids = {gid: i for i, gid in enumerate(layout.groups)}
    layers = [dict(title=t, sources={s: group_ids[g['id']] for s, g in layout.active(t).items()})
              for t in layout.presets]
    compiled = []
    inventory = collections.defaultdict(collections.Counter)
    for gid, group in layout.groups.items():
        inputs = {}
        inventory['mode'][group['mode']] += 1
        inventory['group_setting'].update((group.get('settings') or {}).keys())
        for name, value in group.get('inputs', {}).items():
            found = []
            for kind, entry in entries(value.get('activators') or {}):
                if kind not in KINDS:
                    raise ValueError(f'Unknown activator: {kind}')
                settings = entry.get('settings') or {}
                inventory['activator'][kind] += 1
                inventory['entry_setting'].update(settings.keys())
                commands = [command(a, layout, layer_ids, group_ids) for a in reversed(actions(entry))]
                inventory['command'].update(c['op'] for c in commands)
                found.append(dict(kind=kind, settings=settings, condition=condition(settings), commands=commands))
            if found:  # An absent/empty input inherits; explicit empty commands block.
                inputs[name] = found
        gate = condition(group.get('settings') or {})
        # R185 explicitly clears activation selectors on DSE's Gyro family;
        # response-only overlays still inherit the resolved activation gate.
        if controller == 'dse' and group['mode'] == 'gyro_to_mouse' and gate is None and any(
                gyro_layer(t) and layout.active(t).get('gyro', {}).get('id') == gid for t in layout.presets):
            gate = dict(all=True, groups=[])
        compiled.append(dict(id=gid, mode=group['mode'], settings=group.get('settings') or {},
                             condition=gate, inputs=inputs))
    report = coverage(inventory)
    return dict(schema=SCHEMA, controller=controller, variant=variant, version=version,
                tag=tag, sha256=hashlib.sha256(raw).hexdigest(), layers=layers, groups=compiled,
                coverage=report)
