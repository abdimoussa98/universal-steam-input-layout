"""A changed browser bundle must stop reusing the previous release's URLs."""
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from build_web import write_web_assets


class WebAssetTests(unittest.TestCase):
    def test_every_runtime_dependency_changes_the_entry_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'web'
            shutil.copytree(Path(__file__).resolve().parents[1] / 'web', source)
            bundle = root / 'dist'
            (bundle / 'pkg').mkdir(parents=True)
            (bundle / 'layouts').mkdir()
            (bundle / 'layouts/index.json').write_text('{"layouts": []}')
            (bundle / 'pkg/keybind_overlay.js').write_text('glue')
            (bundle / 'pkg/keybind_overlay_bg.wasm').write_bytes(b'\0asmtest')

            def entry_url():
                write_web_assets(bundle, source)
                return re.search(r'<script type="module" src="([^"]+)"',
                                 (bundle / 'index.html').read_text()).group(1)

            previous = entry_url()
            self.assertRegex(previous, r'^\./start\.js\?v=[0-9a-f]{64}$')
            self.assertEqual(entry_url(), previous, 'Unchanged builds keep stable URLs')
            for path in (source / 'steam-hid.js', source / 'start.js', source / 'downloads.js', bundle / 'layouts/index.json',
                         bundle / 'pkg/keybind_overlay.js',
                         bundle / 'pkg/keybind_overlay_bg.wasm'):
                with self.subTest(asset=path.name):
                    path.write_bytes(path.read_bytes() + b'\nchanged')
                    updated = entry_url()
                    self.assertNotEqual(updated, previous)
                    previous = updated


if __name__ == '__main__':
    unittest.main()
