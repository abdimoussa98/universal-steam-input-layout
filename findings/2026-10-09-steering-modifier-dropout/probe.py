#!/usr/bin/env python3
"""Read-only 90.42 Steering dropout probe; writes only its report.

Run from any directory: python3 findings/2026-10-09-steering-modifier-dropout/probe.py
The working layouts must still be 90.42. Numeric IDs are converted in memory
before inspection/simulation. No binding or simulator behavior is modified.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.scenario import DIRECTIONS, Pad  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles  # noqa: E402


VARIANTS = ('default', 'alternative')
DRIVERS = ('R1', 'L1')
DIRECTIONS_TO_TRY = ('up', 'down')
TRACE_EVENTS = {'press', 'release', 'lose', 'add', 'remove', 'haptic', 'beep'}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def load_layouts():
    layouts, evidence = {}, {}
    for variant in VARIANTS:
        path = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        raw = path.read_bytes()
        data = json.loads(raw)
        cm = data['controller_mappings']
        keys = [int(k.split('_')[1]) for k in cm['action_layers']]
        duplicate_titles = [title for title, count in Counter(
            item['title'] for item in cm['action_layers'].values()).items() if count > 1]
        checks = {
            'layer_order': keys == sorted(keys),
            'preset_blocks': [p['name'] for p in cm['preset']] == list(cm['actions']) + list(cm['action_layers']),
            'preset_ids': [p['id'] for p in cm['preset']] == [str(i) for i in range(len(cm['preset']))],
            'unique_layer_titles': not duplicate_titles,
        }
        if not all(checks.values()) or not cm['title'].endswith(' :: 90.42'):
            raise RuntimeError(f'{variant}: requires valid, ordered 90.42 input: {checks}')
        readable, replacements = ids_to_titles(raw.decode(), generate_lookup(data))
        layouts[variant] = json.loads(readable)
        evidence[variant] = {
            'path': str(path.relative_to(ROOT)), 'title': cm['title'],
            'sha256': digest(raw), 'action_sets': len(cm['actions']),
            'layers': len(cm['action_layers']), 'preflight': checks,
            'title_conversion_replacements': replacements,
            'readable_sha256': digest(readable.encode()),
        }
    return layouts, evidence


def record(pad):
    return {'stack': list(pad.stack), 'normalized_stack': list(pad.names()),
            'held_controls': [list(c) for c in sorted(pad.sim.held)],
            'outputs_down': pad.down(),
            'trace': [list(row) for row in pad.sim.log if row[1] in TRACE_EVENTS]}


def edge_first(pad, direction):
    pad.sim.release(('joystick', 'edge'))
    pad.wait(30)
    pad.sim.release(('joystick', DIRECTIONS[direction]))
    pad.wait(400)


def touch_first(pad, direction):
    pad.sim.release(('joystick', 'touch'))
    pad.wait(30).push('RS').wait(300)


def edge_held_direction(pad, direction):
    pad.sim.release(('joystick', 'edge'))
    pad.wait(500).push('RS').wait(500)


def roll(pad, direction):
    pad.roll('LS', 'left').wait(100).roll('LS', 'down' if direction == 'up' else 'up').wait(400)


def flicks(pad, direction):
    pad.recentre('LS').wait(50).push('LS', direction).wait(400).recentre('LS').wait(400)


def rs_cleanups(pad, direction):
    pad.push('RS').wait(100).lift('RS').wait(300).push('RS').wait(300)


def pad_cleanups(pad, direction):
    pad.touch('RP').wait(30).lift('RP').wait(400).touch('LP').wait(50).lift('LP').wait(400)


def simultaneous_release(pad, direction):
    pad.sim.release(('joystick', 'edge'))
    pad.sim.release(('joystick', DIRECTIONS[direction]))
    pad.wait(400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('results.json'))
    args = parser.parse_args()
    layouts, evidence = load_layouts()

    def fresh(variant, exposed=True, ties=False):
        return Pad(variant, data=layouts[variant], start=('Base', 'Steering'),
                   exposed_fires=exposed, reverse_ties=ties)

    tails = (edge_first, touch_first, edge_held_direction, roll, flicks, rs_cleanups,
             pad_cleanups, simultaneous_release)
    normal_rows = []
    for variant, driver, direction, dwell, tail, exposed, ties in itertools.product(
            VARIANTS, DRIVERS, DIRECTIONS_TO_TRY, (30, 300), tails, (True, False), (False, True)):
        pad = fresh(variant, exposed, ties)
        pad.hold(driver).wait(30).push('LS', direction).wait(dwell)
        tail(pad, direction)
        normal_rows.append([variant, driver, direction, dwell, tail.__name__, exposed, ties,
                            not pad.has('Steering')])
    print(f'Normal held-driver controls: {len(normal_rows)} cases, {sum(row[-1] for row in normal_rows)} exits', flush=True)

    released = []
    for variant, driver, direction, dwell in itertools.product(VARIANTS, DRIVERS, DIRECTIONS_TO_TRY, (30, 300)):
        pad = fresh(variant).hold(driver).wait(30).push('LS', direction).wait(dwell)
        pad.let_go(driver).wait(400)
        result = {'variant': variant, 'driver': driver, 'direction': direction,
                  'initial_direction_hold_ms': dwell, 'steering_exited': not pad.has('Steering'),
                  **record(pad)}
        pad.lift('LS').wait(400)
        result['after_all_controls_released'] = list(pad.stack)
        released.append(result)
    print(f'Actual driver release: {len(released)} cases, {sum(row["steering_exited"] for row in released)} exits', flush=True)

    partial_rows = []
    dwells = (1, 30, 49, 50, 51, 100, 199, 200, 201, 300)
    gaps = (0, 1, 19, 20, 21, 49, 50, 51, 100)
    for variant, driver, direction, dwell, gap, exposed, ties in itertools.product(
            VARIANTS, DRIVERS, DIRECTIONS_TO_TRY, dwells, gaps, (True, False), (False, True)):
        pad = fresh(variant, exposed, ties)
        control = 'LS ' + DIRECTIONS[direction]
        pad.hold(driver).touch('LS').hold(control).wait(dwell).let_go(control)
        pad.push('RS').wait(gap).hold(control).wait(500)
        partial_rows.append([variant, driver, direction, dwell, gap, exposed, ties,
                             not pad.has('Steering')])
    print(f'Partial LS return + RS recovery + full LS press: {len(partial_rows)} cases, {sum(row[-1] for row in partial_rows)} exits', flush=True)

    traces = []
    for variant, driver, direction, exposed, gap in itertools.product(
            VARIANTS, DRIVERS, DIRECTIONS_TO_TRY, (True, False), (0, 50)):
        pad = fresh(variant, exposed)
        control = 'LS ' + DIRECTIONS[direction]
        pad.hold(driver).touch('LS').hold(control).wait(30).let_go(control)
        centered = list(pad.stack)
        pad.push('RS')
        recovered = list(pad.stack)
        pad.wait(gap).hold(control).wait(500)
        traces.append({'variant': variant, 'driver': driver, 'direction': direction,
                       'exposed_fires': exposed, 'repush_gap_ms': gap,
                       'stack_after_partial_direction_release': centered,
                       'stack_after_rs_push': recovered,
                       'steering_exited': not pad.has('Steering'), **record(pad)})

    report = {
        'scope': 'Read-only simulation of installed 90.42, no binding/condition fault injection',
        'layouts': evidence,
        'model_sha256': {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in (
            ROOT / 'steam_layout/simulator.py', ROOT / 'steam_layout/flow_model.py', ROOT / 'tests/scenario.py')},
        'limitations': [
            'A9 immediate exposed-input activation remains unverified in Steam; both outcomes are model switches.',
            'A32 same-time activator ordering is swept in both directions.',
            'The simulator has binary stick inputs. Initial partial LS movement is represented by direction without edge; a later fresh direction press is treated as reaching the Steering Soft Press threshold 29031.',
            'Actual direction, edge, Soft Press and chord radial thresholds/timing need a Deck check; the simulator does not prove these physical distances.',
            'LS deflection chord bit30 is modeled as any held direction or edge, an over-approximation near thresholds.',
            'Normal matrix cases deliberately keep the owner driver pressed throughout. Actual-release cases intentionally release it.',
        ],
        'normal_held_driver': {
            'count': len(normal_rows), 'steering_exits': sum(row[-1] for row in normal_rows),
            'columns': ['variant', 'driver_role', 'direction', 'initial_direction_hold_ms', 'tail', 'exposed_fires', 'reverse_ties', 'steering_exited'],
            'cases': normal_rows,
        },
        'actual_driver_release': {'count': len(released), 'steering_exits': sum(row['steering_exited'] for row in released), 'cases': released},
        'partial_ls_recovery': {
            'count': len(partial_rows), 'steering_exits': sum(row[-1] for row in partial_rows),
            'columns': ['variant', 'driver_role', 'direction', 'initial_partial_direction_hold_ms', 'repush_gap_ms', 'exposed_fires', 'reverse_ties', 'steering_exited'],
            'cases': partial_rows,
            'trace_examples': traces,
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Saved {args.output}')


if __name__ == '__main__':
    main()
