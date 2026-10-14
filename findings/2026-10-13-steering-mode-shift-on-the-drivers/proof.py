"""90.65 and 90.66 on the same random walks: does any log differ, and is any layer left on?

    PYTHONPATH=.:tests python3 findings/2026-10-13-steering-mode-shift-on-the-drivers/proof.py [walks per seed] [seeds]

Reads the 90.65 snapshot and this folder's candidates, so it says the same whatever is installed. The walks
are the audit's (findings/2026-10-12-remove-list-audit/walk.py): 90 events from Base over every control, through
every mode. Half the runs miss one release in ten (the Steam menu, A25). The walks never leak a guard (A69),
so they show what else the mode shift and the missing 5 ms change, not the fault.

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


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for variant in ('default', 'alternative'):
        data = {'90.65': json.loads((ROOT / f'versions/neptune/90.65/single-set-{variant}_hold-gyro_90.65.json').read_text()),
                '90.66': json.loads((HERE / f'{variant}-candidate.json').read_text())}
        jobs = [(variant, label, data[label], seed, count, missed) for label in data for missed in MISSED
                for seed in range(101, 101 + seeds)]                 # seeds the audit did not use
        with Pool() as pool:
            found = pool.map(walk.batch, jobs)
        runs = {(label, missed, seed): (left, digests)
                for (_, label, missed, *_rest, left, _a, _u, digests), (_, _, _, seed, _, _) in zip(found, jobs)}
        print(f'\n{variant}: {count * seeds} walks at each rate of missed releases')
        for missed in MISSED:
            same = differ = unfinished = 0
            on = {label: [0, 0] for label in data}
            for seed in range(101, 101 + seeds):
                (left_a, dig_a), (left_b, dig_b) = runs[('90.65', missed, seed)], runs[('90.66', missed, seed)]
                for la, lb, a, b in zip(left_a, left_b, dig_a, dig_b):
                    if la is None or lb is None:
                        unfinished += 1
                        continue
                    same += a == b
                    differ += a != b
                    for label, left in (('90.65', la), ('90.66', lb)):
                        on[label][0] += bool(left[0])
                        on[label][1] += bool(left[1])
            print(f'  one release in {round(1 / missed) if missed else "none"} missed: {same + differ} walks finish on both; '
                  f'the whole log is the same in {same}, differs in {differ} ({unfinished} did not finish)')
            for label in data:
                print(f'    {label}: a layer left on after everything is let go in {on[label][0]}; '
                      f'after a thumb on each stick in {on[label][1]}')


if __name__ == '__main__':
    main()
