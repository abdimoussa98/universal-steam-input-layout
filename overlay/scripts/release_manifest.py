#!/usr/bin/env python3
"""Identify the packaged browser bundle and verify the container serves it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request
from urllib.parse import urlparse


ASSETS = ('index.html', 'start.js', 'pkg/keybind_overlay.js', 'pkg/keybind_overlay_bg.wasm')
REVISION = re.compile(r'[a-f0-9]{40}')


def write_manifest(bundle, revision):
    if not REVISION.fullmatch(revision):
        raise ValueError('Expected a full Git commit SHA')
    assets = {}
    for path in ASSETS:
        data = (bundle / path).read_bytes()
        if not data:
            raise ValueError(f'Empty asset: {path}')
        assets[path] = hashlib.sha256(data).hexdigest()
    (bundle / 'version.json').write_text(json.dumps({'revision': revision, 'assets': assets}) + '\n')


def verify_site(base_url, revision=None):
    parsed = urlparse(base_url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.query or parsed.fragment:
        raise ValueError('Viewer URL must be an HTTP(S) base URL without query or fragment')
    def read(path):
        request = urllib.request.Request(base_url.rstrip('/') + '/' + path,
                                         headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read(), response.headers.get_content_type()
    manifest, _ = read('version.json')
    manifest = json.loads(manifest)
    actual = manifest['revision']
    if not REVISION.fullmatch(actual) or (revision is not None and actual != revision):
        raise RuntimeError('Server is not serving the expected release')
    for path in ASSETS:
        data, mime = read(path)
        if not data or hashlib.sha256(data).hexdigest() != manifest['assets'][path]:
            raise RuntimeError(f'Release asset missing or mismatched: {path}')
        if path.endswith('.wasm') and (mime != 'application/wasm' or not data.startswith(b'\0asm')):
            raise RuntimeError('WebAssembly response has incorrect MIME type or content')
    return actual


def wait_for_site(base_url, revision, timeout=90):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return verify_site(base_url, revision)
        except Exception:
            if time.monotonic() >= deadline:
                raise
            time.sleep(3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    write_manifest(args.bundle, args.revision)
