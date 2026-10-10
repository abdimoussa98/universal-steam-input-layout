"""Run the scenario registry and regressions affected by release 90.44."""
import argparse
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tests import scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparisons-already-run', action='store_true',
                        help='Omit the separately recorded frozen-90.43 comparison suite')
    args = parser.parse_args()
    loader = unittest.defaultTestLoader
    runner = unittest.TextTestRunner(verbosity=2)
    scenarios = runner.run(unittest.TestSuite(loader.loadTestsFromModule(module) for module in scenario.modules()))
    scenario._ran[:] = [True]
    modules = ('test_steering_entry_feedback',
               'test_fn_feedback_steering_clear', 'test_cleanups', 'test_required_cleanups',
               'test_exceptions', 'test_layout_rules', 'test_rule_registry',
               'test_scenario_registry', 'test_flow_inheritance', 'test_audit_build', 'test_fixes')
    if not args.comparisons_already_run:
        modules = ('test_steering_entry_quiet_drivers',) + modules
    regressions = runner.run(loader.loadTestsFromNames(['tests.' + name for name in modules]))

    def counts(result):
        return {'tests': result.testsRun, 'failures': len(result.failures),
                'errors': len(result.errors), 'skipped': len(result.skipped)}

    report = {'scenarios': counts(scenarios), 'regressions': counts(regressions),
              'frozen_comparisons_run_separately': args.comparisons_already_run,
              'uncovered': {variant: scenario.uncovered(variant) for variant in scenario.VARIANTS}}
    (HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'unverified-assumptions.txt').write_text(scenario.report() + '\n')
    (HERE / 'scenario-coverage.txt').write_text(scenario.coverage() + '\n')
    print(json.dumps(report, indent=2))
    return int(not (scenarios.wasSuccessful() and regressions.wasSuccessful()
                    and not any(report['uncovered'].values())))


if __name__ == '__main__':
    raise SystemExit(main())
