"""Audit the separate candidates, run their scenarios, and optionally export/back up."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout import changes, rules
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids
from tests import test_scenarios_90_39 as scenarios

spec = importlib.util.spec_from_file_location('window_backport_validation', HERE / 'build_candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_assumptions():
    from tests.scenario import SCENARIOS
    assumptions = rules.load_assumptions()
    registry = rules.load()
    candidate_rules = {r for m in SCENARIOS if m.check.startswith('90.39 ') for r in m.rules}
    physical = {'A50': 'Retained default stick outer-ring radius; verify on the Deck.',
                'A52': 'Stored cleanup-entry order is checked in JSON/VDF; its interruption effect is a Deck check.'}
    lines = ['90.39 candidate assumptions; simulator results are not Deck verification.']
    for key, assumption in assumptions.items():
        rests = [m.check for m in SCENARIOS if m.check.startswith('90.39 ') and key in m.rests]
        ruled = sorted(r for r in candidate_rules if key in registry[r].rests_on)
        if (rests or ruled or key in physical) and not assumption.verified:
            lines.append(f'\n{key} ({assumption.status}): {assumption.statement}')
            if rests:
                lines.append('  Scenarios: ' + ', '.join(rests))
            if ruled:
                lines.append('  Rules: ' + ', '.join(ruled))
            if key in physical:
                lines.append('  Physical check: ' + physical[key])
    (HERE / 'unverified-assumptions.txt').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    preflight = {}
    for variant in build.VARIANTS:
        path = build.path(variant)
        raw = path.read_text()
        data = json.loads(raw)
        build.preflight(data)
        assert '{{' not in raw
        readable, _ = ids_to_titles(raw, generate_lookup(data))
        restored, _ = titles_to_ids(readable, generate_lookup(data))
        assert json.dumps(json.loads(restored)) == json.dumps(data)
        preflight[variant] = {'layer_order': True, 'preset_order': True, 'sequential_ids': True,
                              'unique_titles': True, 'roundtrip': True, 'layer_count': 90}
        command = [sys.executable, '-m', 'tools.audit_build', str(path), '--rules', str(HERE / 'candidate-rules.json'),
                   '--baseline', str(build.snapshot(variant)), '--verbose']
        with (HERE / f'{variant}-build-audit.txt').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        print((HERE / f'{variant}-build-audit.txt').read_text(), flush=True)
        if result.returncode:
            return result.returncode
    (HERE / 'preflight.json').write_text(json.dumps(preflight, indent=2) + '\n')

    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(scenarios))
    (HERE / 'candidate-scenarios.txt').write_text(output.getvalue())
    print(output.getvalue(), flush=True)
    if not result.wasSuccessful():
        return 1
    coverage = {}
    for variant in build.VARIANTS:
        changed = changes.changed_since(scenarios.candidate(variant), build.snapshot(variant))
        reached = scenarios.CANDIDATE_REACHED[variant]
        coverage[variant] = {'changed': sorted(changed), 'reached': sorted(reached), 'uncovered': sorted(changed - reached)}
        assert not changed - reached, (variant, changed - reached)
    (HERE / 'scenario-coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
    write_assumptions()

    if args.export:
        destination = ROOT / 'versions/neptune' / build.VERSION
        marker = destination / 'candidate-manifest.json'
        if destination.exists():
            assert marker.exists() and json.loads(marker.read_text())['source'] == str(HERE.relative_to(ROOT)), \
                'release number already belongs to another build'
        # Export both before creating a version directory, so failures never
        # leave a partial snapshot advertised as a complete release.
        for variant in build.VARIANTS:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(build.path(variant))], check=True, cwd=ROOT)
        manifest = {'version': build.VERSION, 'role': 'testing candidate', 'source': str(HERE.relative_to(ROOT)), 'files': {}}
        destination.mkdir(exist_ok=True)
        for variant in build.VARIANTS:
            for source in (build.path(variant), build.path(variant).with_suffix('.vdf')):
                target = destination / source.name
                shutil.copyfile(source, target)
                assert source.read_bytes() == target.read_bytes()
                manifest['files'][str(target.relative_to(ROOT))] = sha(target)
        marker.write_text(json.dumps(manifest, indent=2) + '\n')
        (HERE / 'export-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
