"""Replay updated contracts against validated 90.43 candidates (not snapshots).

The full run imported the old contract before its haptic expectation was
updated. Reuse its validated historical fixture to avoid another full rebuild.
"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout
from tests.contracts.neptune import test_steering_entry_quiet_drivers as contracts


def previous(variant):
    return Layout(json.loads((ROOT / 'findings/2026-10-09-steering-entry-and-feedback' /
                              f'{variant}-candidate.json').read_text()))


if __name__ == '__main__':
    with patch.object(contracts, 'previous', previous):
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(contracts))
    report = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'fixture': 'validated 90.43 candidates'}
    Path(__file__).with_name('contract-recheck.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
