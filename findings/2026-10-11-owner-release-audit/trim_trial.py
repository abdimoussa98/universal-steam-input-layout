"""What the scenario tests say when the two Steering Modifier 2 quick tap lists are shortened. In memory only.

    PYTHONPATH=. python3 findings/2026-10-11-owner-release-audit/trim_trial.py

Each trial copies both working layouts, cuts the Release of the second driver in the two
Steering Modifier 2 layers down to one of the lists below, hands the copies to the scenario
tests in place of the files, and runs every `tests/test_scenarios_*.py`. Nothing is written.
A test whose result differs from the run on the layouts as they are is listed. The five
runs go side by side, one process each; about ten minutes. Run summary.py first: it writes
the two lists this reads.

    never out    the 61 removes that neither the chains nor the walks ever saw on the stack are dropped
    own          only the layer itself and its cover (the target of its 200 ms timer)
    own + gyro   the same, and `Gyro`
    own + driver the same, and the first driver's layer (the W or S layer)
"""
import copy
import json
import unittest
from multiprocessing import Pool
from pathlib import Path

from steam_layout.model import TARGET, Layout, actions, map_title
from tests import scenario

HERE = Path(__file__).resolve().parent
RENAME = {"L1": "L2", "R1": "R2"}
HOSTS = {"Steering | L1!R1: Modifier 2": ("R1", "R1: Tap Cover", "Steering | L1: S Key"),     # layer -> its button,
         "Steering | R1!L1: Modifier 2": ("L1", "L1: Tap Cover", "Steering | R1: W Key")}     # its cover, the first driver's layer


def keep_lists():
    either = {button: set(json.loads((HERE / f"lists-{button}.json").read_text())["either"])
              for button in ("L1", "R1")}
    return {"never out": lambda host, button, cover, driver: either[button],
            "own": lambda host, button, cover, driver: {host, cover},
            "own + gyro": lambda host, button, cover, driver: {host, cover, "Gyro"},
            "own + driver": lambda host, button, cover, driver: {host, cover, driver}}


def trimmed(variant, keep):
    """A copy of the working layout with the two quick tap lists cut to `keep`; (data, removes left per list)."""
    data = copy.deepcopy(scenario.layout_data(variant))
    layout = Layout(data)
    name = (lambda title: map_title(title, RENAME)) if variant == "alternative" else (lambda title: title)
    left = []
    for host, (button, cover, driver) in HOSTS.items():
        kept = {name(title) for title in keep(host, button, cover, driver)}
        source, inp = scenario.BUTTONS[scenario.ROLES[variant][button]]
        release = layout.active(name(host))[source]["inputs"][inp]["activators"]["release"]
        found = [a for a in actions(release) if not (m := TARGET.search(a)) or m.group(1) != "remove_layer"
                 or layout.resolve(m.group(2)) in kept]
        release["bindings"]["binding"] = found
        left.append(len(found))
    return data, left


def results():
    """{test id: outcome} for every scenario test, on whatever layouts the scenario module holds now."""
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in scenario.modules())
    result = unittest.TestResult()
    suite.run(result)
    outcome = {}
    for kind in ("failures", "errors", "expectedFailures", "unexpectedSuccesses"):
        for item in getattr(result, kind):
            test = item[0] if isinstance(item, tuple) else item
            outcome[test.id()] = kind
    return result.testsRun, outcome


def trial(label):
    """One run of every scenario test, in its own process: on the layouts as they are (None) or on one trial's copies."""
    left = None
    if label is not None:
        for variant in scenario.VARIANTS:
            scenario._layouts[variant], left = trimmed(variant, keep_lists()[label])
    ran, outcome = results()
    return label, left, ran, outcome


def main():
    labels = list(keep_lists())
    with Pool(len(labels) + 1) as pool:
        found = {label: rest for label, *rest in pool.map(trial, [None, *labels])}
    _, ran, before = found[None]
    print(f"{ran} scenario tests on the layouts as they are: "
          f"{sum(1 for kind in before.values() if kind in ('failures', 'errors'))} fail")
    for label in labels:
        left, _, after = found[label]
        changed = sorted(test for test in set(before) | set(after) if before.get(test) != after.get(test))
        print(f"\n{label}: {left[0]} removes left in each list; {len(changed)} tests change")
        for test in changed:
            print(f"  {test.split('.', 1)[1]}: {before.get(test, 'passes')} -> {after.get(test, 'passes')}")


if __name__ == "__main__":
    main()
