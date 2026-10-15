"""Ibex 1.0, the base layout: made once from Neptune 90.74 (R177, the bootstrap).

The author, 2026-10-15: "That the IBEX controller is the base controller. That's the default for everything. And
there should be rules for converting from IBEX to the other ones" (plans/2026-10-15-controller-dirs-and-release-
pipeline.md, part 4). Ibex, the Steam Controller 2, has no layout of its own yet, so its first one is the Steam Deck's
90.74 with Ibex's Steam names (`controller_triton`, its capabilities, no Workshop link), the ibex file names,
version 1.0, and Player Space (`gyro_to_2d_conversion_style` 4) in all eleven gyro-to-mouse groups, where only
Base's stated it. No bind changes. This is the one change that goes from the Deck to Ibex: from here on a change is
built on Ibex, and `python3 -m tools.convert` makes the Deck's and the DualSense Edge's layouts from it.
"""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout import controllers, convert  # noqa: E402
from steam_layout.fixes import apply_all  # noqa: E402

BEFORE, AFTER = '90.74', '1.0'


def changed(before, after, path=''):
    """Every value that differs between two layouts, as (path, before, after)."""
    if isinstance(before, dict) and isinstance(after, dict):
        return [row for key in dict.fromkeys([*before, *after])
                for row in changed(before.get(key), after.get(key), f'{path}/{key}')]
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [row for index, (a, b) in enumerate(zip(before, after)) for row in changed(a, b, f'{path}[{index}]')]
    return [] if before == after else [(path, before, after)]


def build(variant):
    deck = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
    assert deck['controller_mappings']['title'].endswith(f' :: {BEFORE}')
    data = convert.readable(convert.bootstrap(deck, variant, AFTER))
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed something: 90.74 was a fixed point'
    final = convert.dumps(data)
    result = json.loads(final)
    diff = changed(deck, result)
    styles = [row for row in diff if row[0].endswith('/gyro_to_2d_conversion_style')]
    gyros = [g for g in result['controller_mappings']['group'] if g['mode'] == 'gyro_to_mouse']
    assert len(gyros) == 11 and all(g['settings']['gyro_to_2d_conversion_style'] == '4' for g in gyros)
    assert len(styles) == 10 and all(old is None for _, old, _ in styles), styles      # Base's stated 4 already
    others = sorted(path.rsplit('/', 1)[-1] for path, _, _ in diff if path not in {row[0] for row in styles})
    assert others == ['controller_caps', 'controller_type', 'title', 'url'], others   # the description is the same
    return final, {'from': f'neptune {BEFORE}', 'version': AFTER,
                   'header': {path.rsplit('/', 1)[-1]: [old, new] for path, old, new in diff if path not in
                              {row[0] for row in styles}},
                   'gyro styles': {'gyro-to-mouse groups': len(gyros), 'stated before (Base)': len(gyros) - len(styles),
                                   'added, 4 (Player Space)': len(styles)},
                   'fixes': fixes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in controllers.VARIANTS:
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
        if args.install:
            controllers.IBEX.working_json(variant).write_text(text)
        print(variant, report['header']['title'][1], '| gyro styles:', report['gyro styles'])


if __name__ == '__main__':
    main()
