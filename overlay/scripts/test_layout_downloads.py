"""Release packaging uses tagged bytes, excluding local edits and candidates."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from layout_downloads import package_layouts
from steam_layout import controllers


class LayoutDownloadsTests(unittest.TestCase):
    def test_tagged_versions_are_flat_distinct_and_newer_releases_replace_old_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
            git('init')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.invalid')
            for controller in controllers.CONTROLLERS:
                for variant in controllers.VARIANTS:
                    path = root / 'versions' / controller.name / '1.9' / f'{controller.stem(variant)}_1.9.vdf'
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(f'{controller.name} {variant} release'.encode())
            git('add', 'versions'); git('commit', '-m', 'release')
            for controller in controllers.CONTROLLERS:
                git('tag', f'{controller.name}-v1.9')
            bundle = root / 'dist'
            entries = package_layouts(bundle, root)
            self.assertEqual(len(entries), 6)
            self.assertEqual(len({e['filename'] for e in entries}), 6)
            for entry in entries:
                data = (bundle / 'layouts' / entry['filename']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
            controller = controllers.IBEX
            for variant in controllers.VARIANTS:
                path = root / 'versions/ibex/1.10' / f'{controller.stem(variant)}_1.10.vdf'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'new released template')
            git('add', 'versions'); git('commit', '-m', 'next release'); git('tag', 'ibex-v1.10')
            path.write_bytes(b'local changes must not ship')
            entries = package_layouts(bundle, root)
            latest = [e for e in entries if e['version'] == '1.10']
            self.assertEqual(len(latest), 2)
            self.assertEqual((bundle / 'layouts' / latest[0]['filename']).read_bytes(), b'new released template')
            self.assertEqual(len(list((bundle / 'layouts').glob('*.vdf'))), 6)
            self.assertEqual(json.loads((bundle / 'layouts/index.json').read_text())['layouts'], entries)
