#!/usr/bin/env python3
"""Build the shared Rust app into a static, relative-path web bundle."""
from pathlib import Path
import shutil
import subprocess
from dependency_notices import write_notices

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run(['wasm-pack', 'build', '--target', 'web', '--out-dir', 'dist/pkg',
                    str(ROOT), '--no-default-features', '--features', 'web', '--locked'], check=True)
    for name in ('index.html', 'start.js'):
        shutil.copyfile(ROOT / 'web' / name, ROOT / 'dist' / name)
    write_notices(ROOT / 'dist/THIRD_PARTY_NOTICES.txt', 'wasm32-unknown-unknown', 'web')
    print(f'Static viewer: {ROOT / "dist"}')
    print('Serve with: python3 -m http.server 8080 --bind 127.0.0.1 --directory overlay/dist')


if __name__ == '__main__':
    main()
