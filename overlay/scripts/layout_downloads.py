"""Package each controller's latest tagged VDFs as loose, versioned files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from steam_layout import controllers
from tools.release import latest_release, tags


def package_layouts(bundle, repo=REPO):
    destination = bundle / 'layouts'
    destination.mkdir(parents=True, exist_ok=True)
    entries = []
    releases = tags(cwd=repo)
    for controller in controllers.CONTROLLERS:
        version = latest_release(controller.name, cwd=repo, every=releases)
        if version is None:
            raise ValueError(f'No release tag for {controller.name}; fetch the full Git history and tags')
        tag = f'{controller.name}-v{version}'
        for variant in controllers.VARIANTS:
            filename = f'{controller.stem(variant)}_{version}.vdf'
            path = f'versions/{controller.name}/{version}/{filename}'
            # Read the immutable release, never an uncommitted working layout.
            data = subprocess.run(['git', 'show', f'{tag}:{path}'], cwd=repo,
                                  check=True, capture_output=True).stdout
            if not data:
                raise ValueError(f'Empty release layout: {path}')
            (destination / filename).write_bytes(data)
            entries.append(dict(controller=controller.label, variant=variant, version=version,
                                filename=filename, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    (destination / 'index.json').write_text(json.dumps({'layouts': entries}, indent=2) + '\n')
    # A reused dist directory should contain only this build's latest files.
    for old in destination.glob('*.vdf'):
        if old.name not in {entry['filename'] for entry in entries}:
            old.unlink()
    return entries
