"""Which removes 90.58 takes out: the audit's rows, cut down to the ones the plan names.

    python3 findings/2026-10-12-removes-that-never-take-a-layer-off/select_removes.py

Reads `removes-<variant>.json` of the audit of every remove on 90.57
(findings/2026-10-12-remove-list-audit/audit.py) and writes `taken-out-<variant>.json` here, one row per
bind: its layer, input, activation type, place among the input's entries, and the layers it stops naming.
The builder reads only that file, so a rerun of the audit does not change what 90.58 is.

A remove goes when its verdict is "never there" or "answers first" and no rule fixes it whatever the stack
holds: a timer's reset (R120), the layer's own hold target in one of its Releases (R120 to R122) and a stick
touch Release's three helpers (R123) stay.
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent / '2026-10-12-remove-list-audit'
VERDICTS = ('never there', 'answers first')
FIXED = ("a timer's reset (R120)", "a stick touch Release's helper (R123)",
         "the layer's own hold target, in a Release (R120 to R122)")


def main():
    for variant in ('default', 'alternative'):
        rows = json.loads((AUDIT / f'removes-{variant}.json').read_text(encoding='utf-8'))
        binds = {}
        for row in rows:
            if row['verdict'] in VERDICTS and row['rule'] not in FIXED:
                key = (row['layer'], row['input'], row['kind'], row['index'])
                bind = binds.setdefault(key, {'layer': row['layer'], 'input': row['input'], 'kind': row['kind'],
                                              'index': row['index'], 'role': row['role'], 'listed': row['size'],
                                              'fired': row['fired'], 'removes': []})
                bind['removes'].append({'layer': row['target'], 'verdict': row['verdict'], 'rule': row['rule']})
        found = sorted(binds.values(), key=lambda b: (b['layer'], b['input'], b['kind'], b['index']))
        (HERE / f'taken-out-{variant}.json').write_text(json.dumps(found, indent=1) + '\n', encoding='utf-8')
        tally = Counter(r['rule'] for b in found for r in b['removes'])
        print(f"{variant}: {sum(len(b['removes']) for b in found)} removes in {len(found)} binds; {dict(tally)}")


if __name__ == '__main__':
    main()
