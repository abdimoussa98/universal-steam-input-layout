"""Generate/check the executable browser catalog from the latest release tags."""
import argparse
import json
from pathlib import Path
import subprocess

from steam_layout import controllers
from steam_layout.demo_compile import compile_layout
from tools.release import latest_release, tags

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'overlay/profiles/demo-layouts.json'


def catalog(repo=ROOT):
    releases = tags(cwd=repo)
    result = []
    for controller in controllers.CONTROLLERS:
        version = latest_release(controller.name, cwd=repo, every=releases)
        if version is None:
            raise ValueError(f'Missing release tags for {controller.name}; fetch tags first')
        tag = f'{controller.name}-v{version}'
        for variant in controllers.VARIANTS:
            path = f'versions/{controller.name}/{version}/{controller.stem(variant)}_{version}.json'
            raw = subprocess.run(['git', 'show', f'{tag}:{path}'], cwd=repo,
                                 check=True, capture_output=True).stdout
            result.append(compile_layout(raw, controller=controller.name, variant=variant, version=version, tag=tag))
    return json.dumps(result, separators=(',', ':'), ensure_ascii=False) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    data = catalog()
    if args.check:
        if not args.output.exists() or args.output.read_text() != data:
            parser.error('Stale demo catalog; run python3 -m tools.compile_demo')
    else:
        args.output.write_text(data)
    print(f'{args.output.name}: six released layouts, reviewed construct inventory, source digests verified')


if __name__ == '__main__':
    main()
