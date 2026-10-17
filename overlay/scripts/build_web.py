#!/usr/bin/env python3
"""Build the shared Rust app into a static, relative-path web bundle."""
from pathlib import Path
import hashlib
import shutil
import subprocess
from dependency_notices import write_notices
from release_manifest import ASSETS

ROOT = Path(__file__).resolve().parents[1]


def write_web_assets(bundle, source=ROOT / 'web'):
    for name in ('index.html', 'start.js', 'steam-hid.js'):
        shutil.copyfile(source / name, bundle / name)
    # The entry URL changes whenever any runtime asset changes. The bootstrap
    # carries this version into every import and the explicit WASM fetch.
    digest = hashlib.sha256()
    for name in ASSETS:
        digest.update(name.encode() + b'\0' + hashlib.sha256((bundle / name).read_bytes()).digest())
    index = bundle / 'index.html'
    html = index.read_text()
    if html.count('src="./start.js"') != 1:
        raise ValueError('Expected one viewer bootstrap script in index.html')
    index.write_text(html.replace('src="./start.js"', f'src="./start.js?v={digest.hexdigest()}"'))


def main():
    subprocess.run(['wasm-pack', 'build', '--target', 'web', '--out-dir', 'dist/pkg',
                    str(ROOT), '--no-default-features', '--features', 'web', '--locked'], check=True)
    write_web_assets(ROOT / 'dist')
    write_notices(ROOT / 'dist/THIRD_PARTY_NOTICES.txt', 'wasm32-unknown-unknown', 'web')
    print(f'Static viewer: {ROOT / "dist"}')
    print('Serve with: python3 -m http.server 8080 --bind 127.0.0.1 --directory overlay/dist')


if __name__ == '__main__':
    main()
