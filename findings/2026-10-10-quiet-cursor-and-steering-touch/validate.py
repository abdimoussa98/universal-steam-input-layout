"""Validate 90.47 behavior, contracts and coverage before snapshotting."""
import argparse
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
# Older contract modules use sibling imports, as unittest discovery does.
sys.path.insert(0, str(ROOT / 'tests'))
from tests import scenario


def counts(result):
    return {'tests': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios-only', action='store_true',
                        help='Repeat behavior and coverage after scenario-only corrections')
    args = parser.parse_args()
    loader = unittest.defaultTestLoader
    runner = unittest.TextTestRunner(verbosity=2)
    scenarios = runner.run(unittest.TestSuite(loader.loadTestsFromModule(module)
                                             for module in scenario.modules()))
    scenario._ran[:] = [True]
    modules = ('test_steering_touch_windows', 'test_neptune_cursor',
               'test_steering_entry_feedback', 'test_fn_feedback_steering_clear',
               'test_rule_registry', 'test_scenario_registry', 'test_layout_rules',
               'test_required_cleanups', 'test_cleanups', 'test_neptune_recovery',
               'test_flow_inheritance', 'test_audit_inheritance', 'test_double_tap_windows',
               'test_fixes', 'test_menu_chain_and_window_pads',
               'test_window_releases_and_tap_cover_resets')
    regressions = None if args.scenarios_only else runner.run(
        loader.loadTestsFromNames(['tests.' + m for m in modules]))
    uncovered = {variant: scenario.uncovered(variant, ROOT /
                 f'findings/2026-10-10-ramp-menu-and-driver-chords/{variant}-candidate.json')
                 for variant in scenario.VARIANTS}
    report = {'scenarios': counts(scenarios), 'uncovered': uncovered}
    if regressions is not None:
        report['regressions'] = counts(regressions)
    name = 'scenario-validation.json' if args.scenarios_only else 'validation.json'
    (HERE / name).write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'unverified-assumptions.txt').write_text(scenario.report() + '\n')
    (HERE / 'scenario-coverage.txt').write_text(scenario.coverage() +
        '\nChanged-layer comparison against validated 90.46 candidates:\n' +
        json.dumps(uncovered, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(not (scenarios.wasSuccessful() and (regressions is None or regressions.wasSuccessful())
                    and not any(uncovered.values())))


if __name__ == '__main__':
    raise SystemExit(main())
