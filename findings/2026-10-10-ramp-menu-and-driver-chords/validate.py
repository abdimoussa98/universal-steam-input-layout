"""Validate 90.46 scenarios, binding contracts and changed-layer coverage."""
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tests import scenario


def counts(result):
    return {'tests': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped)}


def main():
    loader = unittest.defaultTestLoader
    runner = unittest.TextTestRunner(verbosity=2)
    scenarios = runner.run(unittest.TestSuite(loader.loadTestsFromModule(module)
                                             for module in scenario.modules()))
    scenario._ran[:] = [True]
    # The expensive frozen90.43 comparison contracts run separately in
    # contracts.log; this suite covers rule and binding invariants affected here.
    modules = ('test_steering_entry_feedback', 'test_fn_feedback_steering_clear',
               'test_rule_registry', 'test_scenario_registry', 'test_layout_rules',
               'test_required_cleanups', 'test_cleanups', 'test_neptune_recovery',
               'test_flow_inheritance')
    regressions = runner.run(loader.loadTestsFromNames(['tests.' + m for m in modules]))
    uncovered = {variant: scenario.uncovered(variant, ROOT /
                 f'findings/2026-10-10-right-stick-sensitivity/{variant}-candidate.json')
                 for variant in scenario.VARIANTS}
    report = {'scenarios': counts(scenarios), 'regressions': counts(regressions),
              'uncovered': uncovered}
    (HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'unverified-assumptions.txt').write_text(scenario.report() + '\n')
    (HERE / 'scenario-coverage.txt').write_text(scenario.coverage() +
        '\nChanged-layer comparison against validated 90.45 candidates:\n' +
        json.dumps(uncovered, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(not (scenarios.wasSuccessful() and regressions.wasSuccessful()
                    and not any(uncovered.values())))


if __name__ == '__main__':
    raise SystemExit(main())
