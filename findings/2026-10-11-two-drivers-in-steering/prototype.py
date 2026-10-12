"""A prototype of the two-driver changes, on the 90.56 snapshot. It installs nothing and is not a release builder.

    python3 findings/2026-10-11-two-drivers-in-steering/prototype.py <out dir> [changes]

Writes `<variant>-prototype.json` into the out directory, for matrix.py and traces.py. `changes` is a
comma-separated list (default: handover,window,quicktap):

    handover           part 1 of the plan: in each Steering Modifier 2 layer the first driver keeps its key
                       and gets a Release that adds the other driver's layer, then removes its own
    window             part 2: in the two stick windows the other driver's press removes the window and adds
                       Modifier 2 in one Chorded Press; the key beside it becomes interruptible
    window-leave       part 2 the other way: that chord only removes the window
    quicktap           part 3: the Modifier 2 quick tap leaves the first driver's layer on
    quicktap-add-back  part 3 the other way: it keeps its whole list and adds that layer back at the end

The fix pipeline is left out: it needs the two model changes of the plan's part 4. Without them the chains
follow the window's chord from the wrong driver's layer and lengthen 46 cleanup lists, and the Cleanup audit
stops reading the shortened quick tap as a deliberate clear and trims it.

Plan: plans/2026-10-11-two-drivers-in-steering.md.
"""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from steam_layout.model import Layout, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

RENAME = {'L1': 'L2', 'R1': 'R2'}
W, S = 'Steering | R1: W Key', 'Steering | L1: S Key'
# Modifier 2 layer -> (first driver, its layer, second driver, the second driver's layer, the second driver's cover)
MOD2 = {'Steering | R1!L1: Modifier 2': ('R1', W, 'L1', S, 'L1: Tap Cover'),
        'Steering | L1!R1: Modifier 2': ('L1', S, 'R1', W, 'R1: Tap Cover')}
WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')
INPUT = {'default': {'R1': ('switch', 'right_bumper'), 'L1': ('switch', 'left_bumper')},
         'alternative': {'R1': ('right_trigger', 'edge'), 'L1': ('left_trigger', 'edge')}}


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def named(title, variant):
    return map_title(title, RENAME) if variant == 'alternative' else title


def command(op, title, variant):
    return f'controller_action {op}_layer {{{{Base::{named(title, variant)}}}}} 0 0, , '


def group_of(data, layout, title, source, like):
    """The layer's active group on a source. The alternative's Modifier 2 layers have none on the first
    driver's trigger, so one is made with the settings of `like`'s group there."""
    active = layout.active(title)
    if source in active:
        return active[source]
    cm = data['controller_mappings']
    group = copy.deepcopy(layout.active(like)[source])
    group['id'] = str(max(int(g['id']) for g in cm['group']) + 1)
    group['inputs'] = {}
    cm['group'].append(group)
    layout.groups[group['id']] = group
    layout.presets[title]['group_source_bindings'][group['id']] = f'{source} active'
    layout._active.pop(title, None)
    return group


def handover(data, variant):
    layout, done = Layout(data), []
    for title, (first, own, second, other, cover) in MOD2.items():
        source, name = INPUT[variant][first]
        model = layout.active(named(own, variant))[source]['inputs'][name]['activators']
        group = group_of(data, layout, named(title, variant), source, like=named(own, variant))
        assert name not in group['inputs'], (title, name)
        release = copy.deepcopy(model['release'])
        # Stored top to bottom, run bottom to top (A4): the add first, so `Steering` is never the top layer.
        release['bindings']['binding'] = [command('remove', own, variant), command('remove', title, variant),
                                          command('remove', cover, variant), command('add', other, variant)]
        group['inputs'][name] = {'activators': {'Full_Press': copy.deepcopy(model['Full_Press']), 'release': release},
                                 'disabled_activators': {}}
        done.append(f'{title}: {first}')
    return done


def window(data, variant, add=True):
    layout, done = Layout(data), []
    for host in WINDOWS:
        for title, (first, own, second, other, cover) in MOD2.items():
            source, name = INPUT[variant][second]
            entry = layout.active(named(host, variant))[source]['inputs'][name]
            found = entry['activators']
            assert set(found) == {'Full_Press', 'release'}, (host, name, set(found))
            model = layout.active(named(own, variant))[source]['inputs'][name]['activators']['chord']
            settings = {k: v for k, v in model['settings'].items() if k not in ('hold_repeats', 'repeat_rate')}
            leave = command('remove', host, variant)
            chord = {'bindings': {'binding': [command('add', title, variant), leave] if add else leave},
                     'settings': settings}
            key = copy.deepcopy(found['Full_Press'])
            key['settings'].pop('interruptable', None)
            entry['activators'] = {'Full_Press': key, 'chord': chord, 'release': found['release']}
            done.append(f'{host}: {second}')
    return done


def window_leave(data, variant):
    return window(data, variant, add=False)


def quicktap(data, variant, add_back=False):
    layout, done = Layout(data), []
    for title, (first, own, second, other, cover) in MOD2.items():
        source, name = INPUT[variant][second]
        release = layout.active(named(title, variant))[source]['inputs'][name]['activators']['release']
        listed, gone = release['bindings']['binding'], command('remove', own, variant)
        assert listed.count(gone) == 1, title
        release['bindings']['binding'] = [command('add', own, variant)] + listed if add_back else \
            [binding for binding in listed if binding != gone]
        done.append(f'{title}: {second}')
    return done


def quicktap_add_back(data, variant):
    return quicktap(data, variant, add_back=True)


CHANGES = {'handover': handover, 'window': window, 'window-leave': window_leave, 'quicktap': quicktap,
           'quicktap-add-back': quicktap_add_back}


def build(variant, which):
    data = readable('90.56', variant)
    report = {name: CHANGES[name](data, variant) for name in which}
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, report


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    which = sys.argv[2].split(',') if len(sys.argv) > 2 else ['handover', 'window', 'quicktap']
    assert out.resolve() != (ROOT / 'neptune').resolve(), 'not a builder: write somewhere else'
    out.mkdir(parents=True, exist_ok=True)
    for variant in ('default', 'alternative'):
        text, report = build(variant, which)
        (out / f'{variant}-prototype.json').write_text(text)
        print(variant, {name: len(done) for name, done in report.items()})


if __name__ == '__main__':
    main()
