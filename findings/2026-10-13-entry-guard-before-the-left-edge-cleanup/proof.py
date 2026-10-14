"""90.67 on the same random walks as 90.66 and as itself without the guard add: what differs, is any layer left on?

    PYTHONPATH=.:tests python3 findings/2026-10-13-entry-guard-before-the-left-edge-cleanup/proof.py [walks per seed] [seeds]

Reads the 90.66 snapshot and this folder's candidates, so it says the same whatever is installed. "No add" is
90.67 with the ten adds of the Entry Guard taken out again, built in memory: 90.65 without its 5 ms, the layout
this build would be with only the mode shift reverted. The walks are the audit's
(findings/2026-10-12-remove-list-audit/walk.py): 90 events from Base over every control, through every mode. Half
the runs miss one release in ten (the Steam menu, A25). The walks never run a press past its guard chord (A69),
so they show what the add changes in an ordinary cleanup, not the fault.

    log        every key, wheel step, haptic and beep, and every layer going on or off, with its time
    left on    a layer other than a mode still on the stack: after everything is let go, and then after a
               thumb on each stick and off again
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / '2026-10-12-remove-list-audit'))

import walk  # noqa: E402

MISSED = (0.0, 0.10)
NEW, OTHERS = '90.67', ('90.66', 'no add')


def no_add(data):
    text = json.dumps(data)
    data = json.loads(text)
    gone = 0

    def visit(node):
        nonlocal gone
        if isinstance(node, dict):
            found = (node.get('bindings') or {}).get('binding') if isinstance(node.get('bindings'), dict) else None
            settings = node.get('settings') or {}
            if isinstance(found, list) and 'add_layer' in found[-1] and all('remove_layer' in a for a in found[:-1]) \
                    and settings.get('hold_repeats') == '1' and settings.get('interruptable') != '0':
                node['bindings']['binding'] = found[:-1] if len(found) > 2 else found[0]
                gone += 1
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(data)
    assert gone == 10, gone
    return data


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for variant in ('default', 'alternative'):
        new = json.loads((HERE / f'{variant}-candidate.json').read_text())
        data = {'90.66': json.loads((ROOT / f'versions/neptune/90.66/single-set-{variant}_hold-gyro_90.66.json').read_text()),
                'no add': no_add(new), NEW: new}
        jobs = [(variant, label, data[label], seed, count, missed) for label in data for missed in MISSED
                for seed in range(101, 101 + seeds)]                 # seeds the audit did not use
        with Pool() as pool:
            found = pool.map(walk.batch, jobs)
        runs = {(label, missed, seed): (left, digests)
                for (_, label, missed, *_rest, left, _a, _u, digests), (_, _, _, seed, _, _) in zip(found, jobs)}
        print(f'\n{variant}: {count * seeds} walks at each rate of missed releases')
        for missed in MISSED:
            print(f'  one release in {round(1 / missed) if missed else "none"} missed')
            on = {label: [0, 0, 0] for label in data}
            for label in data:
                for seed in range(101, 101 + seeds):
                    for left in runs[(label, missed, seed)][0]:
                        if left is not None:
                            on[label][0] += 1
                            on[label][1] += bool(left[0])
                            on[label][2] += bool(left[1])
            for other in OTHERS:
                same = differ = unfinished = 0
                for seed in range(101, 101 + seeds):
                    (left_a, dig_a), (left_b, dig_b) = runs[(other, missed, seed)], runs[(NEW, missed, seed)]
                    for la, lb, a, b in zip(left_a, left_b, dig_a, dig_b):
                        if la is None or lb is None:
                            unfinished += 1
                        else:
                            same += a == b
                            differ += a != b
                print(f'    against {other}: {same + differ} walks finish on both; the whole log is the same in {same}, '
                      f'differs in {differ} ({unfinished} did not finish)')
            for label in data:
                print(f'    {label}: {on[label][0]} walks finish; a layer left on after everything is let go in '
                      f'{on[label][1]}; after a thumb on each stick in {on[label][2]}')


if __name__ == '__main__':
    main()
