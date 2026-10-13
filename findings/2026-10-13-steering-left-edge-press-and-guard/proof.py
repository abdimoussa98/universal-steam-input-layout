"""90.65 on the same random walks as 90.64, and as itself without the 5 ms: does any log differ, is a layer left on?

    PYTHONPATH=.:tests python3 findings/2026-10-13-steering-left-edge-press-and-guard/proof.py [walks per seed] [seeds]

Reads the 90.64 snapshot and this folder's candidates, so it says the same whatever is installed. The walks
are the audit's (findings/2026-10-12-remove-list-audit/walk.py): 90 events from Base over every control, through
every mode. Half the runs miss one release in ten (the Steam menu, A25).

    90.64      the left edge of ten Steering layers holds one chord with Invert Activation, on an inverted ring
    no delay   90.65 with the start delay taken off the ten presses, built in memory: what the 5 ms changes
    log        every key, wheel step, haptic and beep, and every layer going on or off, with its time
    left on    a layer other than a mode still on the stack: after everything is let go, and then after a
               thumb on each stick and off again

For each pair it also says where the differing walks first differ, as a count by kind and three examples.
"""
import copy
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
from steam_layout.model import Layout, entries  # noqa: E402

MISSED = (0.0, 0.10)
NEW = '90.65'


def without_the_delay(data):
    data, layout, taken = copy.deepcopy(data), None, 0
    layout = Layout(data)
    for title in layout.presets:
        if not title.startswith('Steering') or 'joystick' not in layout.active(title):
            continue
        for kind, entry in entries(layout.active(title)['joystick']['inputs'].get('edge', {}).get('activators') or {}):
            if kind == 'Full_Press' and entry.get('settings', {}).get('delay_start') == '5':
                del entry['settings']['delay_start']
                taken += 1
    assert taken == 10, taken
    return data


def layouts(variant):
    new = json.loads((HERE / f'{variant}-candidate.json').read_text())
    return {'90.64': json.loads((ROOT / f'versions/neptune/90.64/single-set-{variant}_hold-gyro_90.64.json').read_text()),
            'no delay': without_the_delay(new), NEW: new}


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
                for seed in range(101, 101 + seeds)]                 # seeds the audit did not use
        with Pool() as pool:
            found = pool.map(walk.batch, jobs)
        runs = {(label, missed, seed): (left, digests)
                for (_, label, missed, *_rest, left, _a, _u, digests), (_, _, _, seed, _, _) in zip(found, jobs)}
        print(f'\n{variant}: {count * seeds} walks at each rate of missed releases')
        for other in ('90.64', 'no delay'):
            for missed in MISSED:
                same = unfinished = 0
                differ = []
                on = {label: [0, 0] for label in (other, NEW)}
                for seed in range(101, 101 + seeds):
                    (left_a, dig_a), (left_b, dig_b) = runs[(other, missed, seed)], runs[(NEW, missed, seed)]
                    for index, (la, lb, a, b) in enumerate(zip(left_a, left_b, dig_a, dig_b)):
                        if la is None or lb is None:
                            unfinished += 1
                            continue
                        same += a == b
                        if a != b:
                            differ.append((seed, index))
                        for label, left in ((other, la), (NEW, lb)):
                            on[label][0] += bool(left[0])
                            on[label][1] += bool(left[1])
                rate = f'one release in {round(1 / missed)}' if missed else 'no release'
                print(f'  {other} and {NEW}, {rate} missed: {same + len(differ)} walks finish on both; '
                      f'the whole log is the same in {same}, differs in {len(differ)} ({unfinished} did not finish)')
                for label in on:
                    print(f'    {label}: a layer left on after everything is let go in {on[label][0]}; '
                          f'after a thumb on each stick in {on[label][1]}')
                kinds, shown = Counter(), {}
                for seed, index in differ[:400]:
                    old, new = (replay(variant, data[label], seed, index, missed) for label in (other, NEW))
                    at = next((i for i, (x, y) in enumerate(zip(old, new)) if x != y), min(len(old), len(new)))
                    first = tuple((log[at][1], log[at][2]) if at < len(log) else ('end', '') for log in (old, new))
                    kinds[first] += 1
                    shown.setdefault(first, (seed, index, old[max(0, at - 4):at], old[at:at + 3], new[at:at + 3]))
                for first, number in kinds.most_common(8):
                    seed, index, both, old, new = shown[first]
                    print(f'    {number} first differ with {other}: {first[0]}  |  {NEW}: {first[1]}  (seed {seed}, walk {index})')
                if len(kinds) > 8:
                    print(f'    and {len(kinds) - 8} more kinds')


if __name__ == '__main__':
    main()
