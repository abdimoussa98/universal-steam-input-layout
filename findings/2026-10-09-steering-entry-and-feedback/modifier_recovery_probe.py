#!/usr/bin/env python3
"""Record isolated modifier-recovery regressions against the frozen 90.42 inputs.

No live files are read or written. The fallback title is renamed in memory to
satisfy the new module's Entry Guard precondition; the guard is never entered
in these cases. This isolates owner recovery from the separate entry changes.
Complete 90.43 candidate scenarios validate their integration independently.
"""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from tests.scenario import DIRECTIONS, Pad
from tools.convert_runtime_ids import generate_lookup, ids_to_titles


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('modifier_recovery', HERE / 'modifier_recovery.py')
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    layouts, sources = {}, {}
    for variant in ('default', 'alternative'):
        path = ROOT / f'findings/2026-10-09-fn-haptics-and-steering-clear/{variant}-candidate.json'
        raw = path.read_text()
        data = json.loads(raw)
        readable, _ = ids_to_titles(raw, generate_lookup(data))
        data = json.loads(readable.replace('Steering | LS: Fallback Guard', 'Steering | LS: Entry Guard'))
        edits = recovery.apply(data, variant)
        layouts[variant] = data
        sources[variant] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path),
                            'entries_reviewed': edits['entries_reviewed'],
                            'owner_removal_commands_deleted': sum(row['removed_owner_commands'] for row in edits['entries']),
                            'owner_direction_entries': len(edits['owner_direction_entries']),
                            'upper_direction_recovery': len(edits['upper_direction_recovery'])}

    dwells, gaps = (1, 30, 199, 200, 201, 300), (0, 1, 49, 50)
    held_cases = 0
    for variant, driver, direction, dwell, gap, exposed, ties in itertools.product(
            layouts, ('R1', 'L1'), ('up', 'down'), dwells, gaps, (True, False), (True, False)):
        pad = Pad(variant, data=layouts[variant], start=('Base', 'Steering'),
                  exposed_fires=exposed, reverse_ties=ties)
        key = 'W' if driver == 'R1' else 'S'
        title = f'Steering | {driver}: {key} Key'
        owner = pad.title(title)
        control = 'LS ' + DIRECTIONS[direction]
        # Deliberately omit LS edge: a shallow direction excursion cannot
        # release an edge that was never active.
        pad.hold(driver).touch('LS').hold(control).wait(dwell).let_go(control).mark()
        pad.push('RS').wait(gap).hold(control).wait(500)
        context = (variant, driver, direction, dwell, gap, exposed, ties)
        assert pad.has('Steering', title), (context, pad.stack)
        assert not any(event == 'remove' and detail == owner
                       for _, event, detail in pad.sim.log[pad._mark:]), context
        held_cases += 1

    stale_cases = 0
    for variant, driver, direction, exposed in itertools.product(
            layouts, ('R1', 'L1'), ('up', 'down'), (True, False)):
        pad = Pad(variant, data=layouts[variant], start=('Base', 'Steering'), exposed_fires=exposed)
        control = 'LS ' + DIRECTIONS[direction]
        pad.hold(driver).touch('LS').hold(control).wait(30).let_go(control).miss(driver).push('RS').wait(300)
        context = (variant, driver, direction, exposed)
        assert pad.has('Steering') and not any(title.startswith('Steering |') for title in pad.names()), (context, pad.stack)
        # A still-out RS legitimately re-enters the normal ramp layers once
        # owner recovery exposes Base. They end when that stick is released.
        pad.lift('RS').lift('LS').wait(300)
        assert pad.names() == ('Base', 'Steering') and not pad.down(), (context, pad.stack, pad.down())
        stale_cases += 1

    files = [Path(__file__), HERE / 'modifier_recovery.py', ROOT / 'steam_layout/cleanups.py',
             ROOT / 'steam_layout/simulator.py', ROOT / 'steam_layout/flow_model.py', ROOT / 'tests/scenario.py']
    report = {
        'scope': 'Isolated modifier-recovery correction on frozen 90.42 inputs; no live files changed',
        'sources': sources,
        'code_sha256': {str(path.relative_to(ROOT)): digest(path) for path in files},
        'held_owner': {'cases': held_cases, 'passed': held_cases, 'owner_removals': 0, 'steering_exits': 0,
                       'partial_direction_hold_ms': list(dwells), 'repush_gap_ms': list(gaps),
                       'variants': ['default', 'alternative'], 'driver_roles': ['R1', 'L1'],
                       'directions': ['up', 'down'], 'A9_exposed_fires': [True, False], 'A32_reverse_ties': [True, False]},
        'missed_owner_release': {'cases': stale_cases, 'passed': stale_cases,
                                 'final_stack_after_stick_release': ['Base', 'Steering'], 'held_outputs': []},
        'limitations': [
            'Uses the runtime model, not Steam hardware.',
            'Initial shallow movement is a direction without outer edge; the model has no continuous radial threshold.',
            'The guard is renamed only to isolate the new correction module; these cases never enter it.',
            'The complete candidate, Entry Guard handoff and fix-pipeline integration are tested separately.',
        ],
    }
    target = HERE / 'modifier-recovery-verification.json'
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{held_cases} held-owner and {stale_cases} stale-owner cases passed; saved {target.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
