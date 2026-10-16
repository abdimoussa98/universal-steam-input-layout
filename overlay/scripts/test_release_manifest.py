"""Check the packaged web release over HTTP, without a deployment service."""
import functools
import http.server
from pathlib import Path
import tempfile
import threading
import unittest

from release_manifest import verify_site, write_manifest

REV = 'c' * 40


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.bundle = Path(self.directory.name)
        (self.bundle / 'pkg').mkdir()
        for path, data in [('index.html', b'<html>viewer</html>'), ('start.js', b'boot'),
                           ('pkg/keybind_overlay.js', b'glue'), ('pkg/keybind_overlay_bg.wasm', b'\0asmtest')]:
            (self.bundle / path).write_bytes(data)
        write_manifest(self.bundle, REV)
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=self.directory.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def test_new_release_requires_matching_version_and_all_assets(self):
        self.assertEqual(verify_site(self.url, REV), REV)
        with self.assertRaisesRegex(RuntimeError, 'expected release'):
            verify_site(self.url, 'f' * 40)
        (self.bundle / 'pkg/keybind_overlay_bg.wasm').write_bytes(b'broken')
        with self.assertRaisesRegex(RuntimeError, 'mismatched'):
            verify_site(self.url, REV)

    def test_html_error_page_cannot_pass_as_webassembly(self):
        (self.bundle / 'pkg/keybind_overlay_bg.wasm').write_bytes(b'<html>error</html>')
        write_manifest(self.bundle, REV)
        with self.assertRaisesRegex(RuntimeError, 'WebAssembly'):
            verify_site(self.url, REV)


if __name__ == '__main__':
    unittest.main()
