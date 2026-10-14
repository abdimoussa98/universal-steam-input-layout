"""90.69 and 90.70 on the same random walks as 90.68: does any log differ, and is any layer left on?

    PYTHONPATH=.:tests python3 findings/2026-10-13-entry-guard-in-every-steering-cleanup/proof.py [walks per seed] [seeds]

Reads the 90.68 snapshot and the two builds' candidates, so it says the same whatever is installed. Both builds are
from 90.68: 90.69 takes Hold to Repeat off the cleanup presses of the Steering layers and the Entry Guard add out
of their left edge; 90.70 puts the Entry Guard add on every cleanup press of those layers. The walks are the
audit's (findings/2026-10-12-remove-list-audit/walk.py): 90 events from Base over every control, through every
mode. Half the runs miss one release in ten (the Steam menu, A25). The walks never run a press past its guard
chord (A69), so they show what the builds change in an ordinary cleanup, not the fault.

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
OLD, NEW = '90.68', ('90.69', '90.70')
FOLDER = {'90.69': HERE.parent / '2026-10-13-steering-cleanup-presses-without-repeat', '90.70': HERE}


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for variant in ('default', 'alternative'):
        data = {OLD: json.loads((ROOT / f'versions/neptune/{OLD}/single-set-{variant}_hold-gyro_{OLD}.json').read_text())}
        data.update({label: json.loads((FOLDER[label] / f'{variant}-candidate.json').read_text()) for label in NEW})
        jobs = [(variant, label, data[label], seed, count, missed) for label in data for missed in MISSED
                for seed in range(101, 101 + seeds)]                 # seeds the audit did not use
        with Pool() as pool:
            found = pool.map(walk.batch, jobs)
        runs = {(label, missed, seed): (left, digests)
                for (_, label, missed, *_rest, left, _a, _u, digests), (_, _, _, seed, _, _) in zip(found, jobs)}
        print(f'\n{variant}: {count * seeds} walks at each rate of missed releases')
        for missed in MISSED:
            print(f'  one release in {round(1 / missed) if missed else "none"} missed')
            for label in data:
                done = on = after = 0
                for seed in range(101, 101 + seeds):
                    for left in runs[(label, missed, seed)][0]:
                        if left is not None:
                            done, on, after = done + 1, on + bool(left[0]), after + bool(left[1])
                print(f'    {label}: {done} walks finish; a layer left on after everything is let go in {on}; '
                      f'after a thumb on each stick in {after}')
            for label in NEW:
                same = differ = unfinished = 0
                for seed in range(101, 101 + seeds):
                    (left_a, dig_a), (left_b, dig_b) = runs[(OLD, missed, seed)], runs[(label, missed, seed)]
                    for la, lb, a, b in zip(left_a, left_b, dig_a, dig_b):
                        if la is None or lb is None:
                            unfinished += 1
                        else:
                            same, differ = same + (a == b), differ + (a != b)
                print(f'    {label} against {OLD}: {same + differ} walks finish on both; the whole log is the same in '
                      f'{same}, differs in {differ} ({unfinished} did not finish)')


if __name__ == '__main__':
    main()
