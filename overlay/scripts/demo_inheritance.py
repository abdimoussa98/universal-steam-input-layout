"""Source-layout inheritance expectations for every layer in the family-chain model.

The Python audit supplies the oracle independently of the executable compiler.
This checks binding ownership, including empty inputs and mode barriers. It does
not claim exhaustive gesture timing or arbitrary stale-stack coverage.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout import controllers
from steam_layout.covers import family_view, load_rules
from steam_layout.flow_model import resolve
from steam_layout.model import Layout

OUTPUT = ROOT / 'overlay/tests/fixtures/demo-inheritance.json'


def expectations(item):
    controller = next(c for c in controllers.CONTROLLERS if c.name == item['controller'])
    version = item['version']
    path = f'versions/{controller.name}/{version}/{controller.stem(item["variant"])}_{version}.json'
    raw = subprocess.run(['git', 'show', f'{item["tag"]}:{path}'], cwd=ROOT,
                         check=True, capture_output=True).stdout
    assert hashlib.sha256(raw).hexdigest() == item['sha256'], path
    data = json.loads(raw)
    layout = Layout(data)
    layers = {title: i for i, title in enumerate(layout.presets)}
    groups = {gid: i for i, gid in enumerate(layout.groups)}
    controls = sorted({(source, name) for title in layout.presets
                       for source, group in layout.active(title).items()
                       for name in group.get('inputs', {})})
    stacks = family_view(layout, load_rules(data=data)).stacks()
    seen = {title for stack in stacks for title in stack}
    if missing := set(layers) - seen:
        raise ValueError(f'{path}: layers missing from inheritance coverage: {sorted(missing)}')
    answers, indices, cases = [], {}, []
    for stack in sorted(stacks):
        row = []
        for source, name in controls:
            kind, owner, _, _ = resolve(layout, stack, source, name)
            row.append(None if kind == 'none' else
                       (layers[owner], groups[layout.active(owner)[source]['id']]))
        key = tuple(row)
        if key not in indices:
            indices[key] = len(answers)
            answers.append(row)
        cases.append(([layers[title] for title in stack], indices[key]))
    return dict(controller=item['controller'], variant=item['variant'], sha256=item['sha256'],
                controls=['/'.join(c) for c in controls], answers=answers, cases=cases)


def generate():
    catalog = json.loads((ROOT / 'overlay/profiles/demo-layouts.json').read_text())
    return json.dumps([expectations(item) for item in catalog], separators=(',', ':')) + '\n'


if __name__ == '__main__':
    OUTPUT.write_text(generate())
    for item in json.loads(OUTPUT.read_text()):
        layers = {i for stack, _ in item['cases'] for i in stack}
        print(item['controller'], item['variant'], len(layers), 'layers,',
              len(item['cases']), 'stacks,', len(item['cases'])*len(item['controls']), 'binding lookups')
