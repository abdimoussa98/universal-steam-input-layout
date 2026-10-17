#!/usr/bin/env python3
"""Reject oversized hand-maintained Rust files in the overlay crate."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_LINES = 400


def violations(root):
    if not (root / 'src').is_dir():
        raise ValueError(f'Rust source directory not found: {root / "src"}')
    files = [path for folder in ('src', 'tests', 'examples', 'benches')
             for path in (root / folder).rglob('*.rs')]
    if (root / 'build.rs').is_file():
        files.append(root / 'build.rs')
    return [(path.relative_to(root), count)
            for path in sorted(files)
            if (count := len(path.read_text(encoding='utf-8').splitlines())) > MAX_LINES]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Overlay crate directory')
    args = parser.parse_args()
    try:
        failures = violations(args.root)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for path, count in failures:
        print(f'{path}: {count} lines (maximum {MAX_LINES}); split by responsibility')
    if not failures:
        print(f'Rust file-size check passed (maximum {MAX_LINES} lines).')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
