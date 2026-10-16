"""Collect dependency metadata and bundled license texts for an artifact."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def write_notices(destination, target, feature):
    result = subprocess.run(['cargo', 'metadata', '--manifest-path', str(ROOT / 'Cargo.toml'),
                             '--format-version', '1', '--locked', '--no-default-features',
                             '--features', feature, '--filter-platform', target],
                            check=True, capture_output=True, text=True)
    metadata = json.loads(result.stdout)
    nodes = {node['id']: node for node in metadata['resolve']['nodes']}
    pending = [metadata['resolve']['root']]
    reachable = set()
    while pending:
        node = pending.pop()
        if node not in reachable:
            reachable.add(node)
            pending.extend(dep['pkg'] for dep in nodes[node]['deps'])
    texts = ['Third-party dependencies. The application itself does not assign a new license to the repository.\n']
    for package in sorted(metadata['packages'], key=lambda p: (p['name'], p['version'])):
        if package['id'] not in reachable or package['id'] == metadata['resolve']['root']:
            continue
        texts.append(f'\n=== {package["name"]} {package["version"]} ===\nDeclared license: {package.get("license") or "see source"}\nSource: {package.get("repository") or package.get("source") or "local"}\n')
        directory = Path(package['manifest_path']).parent
        licenses = sorted(p for p in directory.rglob('*') if p.is_file() and p.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE')))
        for path in licenses:
            texts.append(f'\n--- {path.relative_to(directory)} ---\n{path.read_text(errors="replace")}\n')
    Path(destination).write_text(''.join(texts), encoding='utf-8')
