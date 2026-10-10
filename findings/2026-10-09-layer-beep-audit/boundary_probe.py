#!/usr/bin/env python3
"""Read-only release-gap and clean Steering-entry boundary checks for 90.42."""
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('beep_probe', HERE / 'probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def main():
    toggles = []
    for variant, start, first, release_order, gap, exposed in itertools.product(
            ('default', 'alternative'), (('Base',), ('Base', 'Gyro')),
            ('L1', 'R1'), ('first', 'second'), (0, 1, 49, 50, 51), (True, False)):
        pad = probe.fresh(variant, start, exposed_fires=exposed)
        second = 'R1' if first == 'L1' else 'L1'
        a, b = (first, second) if release_order == 'first' else (second, first)
        pad.hold(first).wait(30).hold(second).wait(30).let_go(a).wait(gap).let_go(b).wait(400)
        toggles.append(probe.report(pad, 'release_gap_boundary', {
            'start': start, 'first': first, 'release_order': release_order,
            'release_gap_ms': gap, 'exposed_fires': exposed}))

    transitions = []
    for variant, held, release_order, exposed in itertools.product(
            ('default', 'alternative'), ((), ('L1',), ('R1',), ('L1', 'R1'), ('R1', 'L1')),
            ('forward', 'reverse'), (True, False)):
        pad = probe.fresh(variant, ('Base', 'Gyro'), exposed_fires=exposed)
        pad.hold('Start').click('LS')
        before_held = list(pad.stack)
        for button in held:
            pad.hold(button).wait(30)
        pad.let_go('Start').wait(30)
        after_commit = list(pad.stack)
        for button in (held if release_order == 'forward' else tuple(reversed(held))):
            pad.let_go(button).wait(30)
        pad.lift('LS').wait(400)
        transitions.append(probe.report(pad, 'held_drivers_across_steering_entry', {
            'held_in_transition': held, 'release_order': release_order, 'exposed_fires': exposed,
            'transition_stack_before_driver_holds': before_held,
            'stack_after_menu_release_commits': after_commit,
            'gyro_mod2_added': any(what == 'add' and 'Gyro | ' in target and 'Modifier 2' in target
                                   for _, what, target in pad.sim.log)}))

    request_counts = {}
    for case in toggles:
        key = str(tuple(case['start']))
        request_counts.setdefault(key, set()).add(case['beep_request_count'])
    report = {
        'scope': 'Clean current 90.42 stacks; exact command observation, no fault injection',
        'preflight': probe.PREFLIGHT,
        'limitations': [
            'A zero-millisecond gap uses sequential release calls at the same timestamp. Native Steam may batch two hardware releases differently; such batching is not modeled.',
            'Counts represent configured command requests and modeled stack mutations, not measured audible sounds.',
            'Entry tests exercise held buttons across the one normal Steering entry route; they do not prove exhaustive reachability across arbitrary event histories.',
        ],
        'toggle_count': len(toggles),
        'toggle_request_counts_by_start': {key: sorted(values) for key, values in request_counts.items()},
        'all_toggle_counts_match_simulator': all(c['beep_request_count'] == len(c['sim_beeps']) for c in toggles),
        'max_flagged_targets_changed_per_toggle': max(c['beep_requests_on_changed_targets'] for c in toggles),
        'steering_entry_count': len(transitions),
        'steering_entries_that_added_gyro_mod2': sum(c['gyro_mod2_added'] for c in transitions),
        'toggle_cases': toggles,
        'steering_entry_cases': transitions,
    }
    (HERE / 'boundary-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('toggle_cases', 'steering_entry_cases', 'preflight', 'limitations')}, indent=2))


if __name__ == '__main__':
    main()
