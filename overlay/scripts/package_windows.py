#!/usr/bin/env python3
"""Package an already built Windows executable separately from Steam layouts."""
from pathlib import Path
import shutil
from dependency_notices import write_notices

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = ROOT / 'target/release/keybind-overlay.exe'
    if not executable.is_file():
        raise SystemExit('First run cargo build --release --features desktop on Windows')
    output = ROOT / 'windows-bundle'
    output.mkdir(exist_ok=True)
    shutil.copyfile(executable, output / executable.name)
    shutil.copyfile(ROOT / 'README.md', output / 'README.md')
    shutil.copytree(ROOT / 'profiles', output / 'profiles', dirs_exist_ok=True)
    write_notices(output / 'THIRD_PARTY_NOTICES.txt', 'x86_64-pc-windows-msvc', 'desktop')
    print(f'Windows bundle: {output}')
    print('For browser companion mode, put the separately built web bundle in windows-bundle/web.')


if __name__ == '__main__':
    main()
