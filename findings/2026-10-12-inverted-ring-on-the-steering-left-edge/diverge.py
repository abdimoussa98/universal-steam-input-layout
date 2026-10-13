"""The walks of proof.py whose log differs between 90.62 and 90.63: where each first differs.

    PYTHONPATH=.:tests python3 findings/2026-10-12-inverted-ring-on-the-steering-left-edge/diverge.py [walks per seed] [seeds]

For each such walk: the rate of missed releases, the stack and the held controls just before, and the next
log lines on each build.
"""
import json
import random
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / '2026-10-12-remove-list-audit'))

import walk  # noqa: E402
from steam_layout.model import Layout  # noqa: E402

MISSED = (0.0, 0.10)


def layouts(variant):
    return {'90.62': json.loads((ROOT / f'versions/neptune/90.62/single-set-{variant}_hold-gyro_90.62.json').read_text()),
            '90.63': json.loads((HERE / f'{variant}-candidate.json').read_text())}


def replay(variant, data, seed, index, missed):
    rng = random.Random(seed * 100003 + index)
    pad = walk.new_pad(variant, Layout(data), rng, Counter(), Counter(), Counter())
    walk.walk(pad, rng, missed)
    return [(when, what, detail) for when, what, detail in pad.sim.log]


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for variant in ('default', 'alternative'):
        data = layouts(variant)
        jobs = [(variant, label, data[label], seed, count, missed) for label in data for missed in MISSED
                for seed in range(101, 101 + seeds)]
        with Pool() as pool:
            found = pool.map(walk.batch, jobs)
        digests = {(job[1], job[5], job[3]): result[-1] for job, result in zip(jobs, found)}
        for missed in MISSED:
            for seed in range(101, 101 + seeds):
                a, b = digests[('90.62', missed, seed)], digests[('90.63', missed, seed)]
                for index in [i for i, (x, y) in enumerate(zip(a, b)) if x != y]:
                    old, new = (replay(variant, data[label], seed, index, missed) for label in ('90.62', '90.63'))
                    at = next((i for i, (x, y) in enumerate(zip(old, new)) if x != y), min(len(old), len(new)))
                    print(f'\n{variant}, seed {seed}, walk {index}, one release in {round(1 / missed) if missed else "none"} missed: '
                          f'first differs at log line {at} of {len(old)} and {len(new)}')
                    for line in old[max(0, at - 14):at]:
                        print('    both  ', line)
                    for label, log in (('90.62', old), ('90.63', new)):
                        for line in log[at:at + 6]:
                            print(f'    {label} ', line)


if __name__ == '__main__':
    main()
