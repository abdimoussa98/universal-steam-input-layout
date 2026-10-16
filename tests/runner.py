"""Run canonical Python tests once, then validate explicit scenario evidence.

    python -m tests.runner
    python -m tests.runner --shard 1 4 --evidence out/part-1.json --run-id BUILD_ID
    python -m tests.runner --finalize out/part-*.json --run-id BUILD_ID
"""
import argparse
from fnmatch import fnmatchcase
import io
import itertools
import json
from pathlib import Path
import sys
import subprocess
import time
import unittest
import uuid

from tests.support.discovery import test_modules
from tests.support.evidence import (EvidenceResult, document, finalize_documents,
                                    flatten, make_manifest, validate_shard_records)

ROOT = Path(__file__).resolve().parents[1]


def peak_python_rss():
    """Process high-water mark, excluding native children; unavailable on Windows."""
    try:
        import resource
    except ImportError:
        return None
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


class ModuleSuite(unittest.TestSuite):
    """Keep class/module fixtures together and include their teardown in timing."""
    def __init__(self, name, tests):
        super().__init__(tests)
        self.name = name

    def run(self, result, debug=False):
        began = time.monotonic()
        nested = getattr(result, "_testRunEntered", False)
        try:
            return super().run(result, debug=debug)
        finally:
            # The outer suite otherwise charges this module's teardown to the
            # following module. Complete it here, once, before stopping its timer.
            if nested:
                self._tearDownPreviousClass(None, result)
                self._handleModuleTearDown(result)
                result._previousTestClass = None
            result.module_seconds[self.name] = time.monotonic() - began


def grouped_suite(tests):
    return unittest.TestSuite(ModuleSuite(name, list(group)) for name, group in
                              itertools.groupby(tests, key=lambda test: test.__class__.__module__))


def collect(modules=None, loader=None):
    loader = loader or unittest.TestLoader()
    cases = []
    for name in test_modules() if modules is None else modules:
        cases.extend(flatten(loader.loadTestsFromName(name)))
    if loader.errors:
        raise ValueError("Test collection failed:\n" + "\n".join(loader.errors))
    return cases


def manifest_for(tests):
    from tests import scenario
    scenario.validate_fixture_integrity()
    return make_manifest(ROOT, tests, scenario.coverage_manifest())


def execute(tests, manifest, *, run_id, index=1, count=1, stream=None, verbosity=1):
    suite = grouped_suite(tests)
    del tests  # the suite owns its cases; exhausted iterators must not retain their input
    selected = [test.id() for test in flatten(suite)]
    runner = unittest.TextTestRunner(stream=stream or sys.stderr, verbosity=verbosity,
                                     resultclass=EvidenceResult)
    began = time.monotonic()
    result = runner.run(suite)
    artifact = document(manifest, result, selected, run_id=run_id, index=index, count=count)
    artifact["timing"] = {"execution_seconds": time.monotonic() - began,
                          "peak_python_rss_bytes": peak_python_rss()}
    return artifact, result


def run_scenarios():
    """Standalone reporting explicitly executes only decorated scenarios once."""
    from tests import scenario
    tests = scenario.scenario_tests()
    manifest = manifest_for(tests)
    selected = iter(tests)
    del tests
    run_id = str(uuid.uuid4())
    evidence, _ = execute(selected, manifest, run_id=run_id)
    return finalize_documents([evidence], manifest_for(scenario.scenario_tests()), run_id=run_id)


class RecordingResult:
    """Forward unittest callbacks while collecting evidence for its normal runner."""
    def __init__(self, result):
        object.__setattr__(self, "result", result)
        object.__setattr__(self, "recording", EvidenceResult(unittest.runner._WritelnDecorator(io.StringIO()), True, 0))

    def __getattr__(self, name):
        if name == "module_seconds":
            return self.recording.module_seconds
        return getattr(self.result, name)

    def __setattr__(self, name, value):
        setattr(self.result, name, value)


def _forward(name):
    def callback(self, *args, **kwargs):
        getattr(self.recording, name)(*args, **kwargs)
        return getattr(self.result, name)(*args, **kwargs)
    return callback


for _name in ("startTest", "stopTest", "addSuccess", "addFailure", "addError", "addSkip",
              "addExpectedFailure", "addUnexpectedSuccess", "addSubTest"):
    setattr(RecordingResult, _name, _forward(_name))


class EvidenceSuite(unittest.TestSuite):
    """Package discovery uses the same finalization gate as the explicit CLI."""
    def run(self, result, debug=False):
        if debug:
            return super().run(result, debug=True)
        suite = grouped_suite(flatten(self))
        selected = [test.id() for test in flatten(suite)]
        manifest = manifest_for(flatten(suite))
        self._removed_tests += self.countTestCases()
        self._tests.clear()  # transfer ownership so successful cases can be released during execution
        recording = RecordingResult(result)
        suite.run(recording)
        run_id = str(uuid.uuid4())
        artifact = document(manifest, recording.recording, selected, run_id=run_id)

        def finalizer():
            finalize_documents([artifact], manifest_for(collect()), run_id=run_id)

        unittest.FunctionTestCase(finalizer, description="Complete scenario evidence and live layer coverage (R165)").run(result)
        return result


def discovery_suite(loader=None, pattern=None):
    """Honor unittest filters; only unrestricted discovery can prove full coverage."""
    loader = loader or unittest.TestLoader()
    modules = test_modules()
    if pattern is not None:
        modules = [name for name in modules if fnmatchcase(name.rsplit(".", 1)[-1] + ".py", pattern)]
    tests = collect(modules=modules, loader=loader)
    full = pattern in (None, "test*.py", "test_*.py") and loader.testNamePatterns is None
    return EvidenceSuite(tests) if full else unittest.TestSuite(tests)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--shard", nargs=2, type=int, metavar=("INDEX", "COUNT"))
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--finalize", nargs="+", type=Path, metavar="FILE")
    parser.add_argument("--python-only", action="store_true", help="omit the separate Node lane on a full local run")
    args = parser.parse_args(argv)
    if args.finalize and (args.shard or args.evidence):
        parser.error("--finalize cannot be combined with execution options")
    if (args.shard or args.finalize) and not args.run_id:
        parser.error("Shard execution and finalization require --run-id")
    if args.shard and not args.evidence:
        parser.error("Shard execution requires --evidence")
    run_id = args.run_id or str(uuid.uuid4())
    try:
        began = time.monotonic()
        all_tests = collect()
        collected = time.monotonic()
        manifest = manifest_for(all_tests)
        prepared = time.monotonic()
        if args.finalize:
            del all_tests
            documents = [json.loads(path.read_text(encoding="utf-8")) for path in args.finalize]
            observed = finalize_documents(documents, manifest, run_id=run_id)
        else:
            index, count = args.shard or (1, 1)
            if args.shard:
                from tools.release import shard
                names = set(shard(index, count))
                selected = (test for test in all_tests if test.__class__.__module__ in names)
            else:
                selected = iter(all_tests)
            del all_tests
            artifact, result = execute(selected, manifest, run_id=run_id, index=index, count=count)
            revalidate_started = time.monotonic()
            current = manifest_for(collect())
            artifact["timing"].update(collection_seconds=collected - began, manifest_seconds=prepared - collected,
                                       revalidation_seconds=time.monotonic() - revalidate_started)
            if current != manifest:
                raise ValueError("Test inputs changed while the suite was running")
            if args.evidence:
                args.evidence.parent.mkdir(parents=True, exist_ok=True)
                args.evidence.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if args.shard:
                validate_shard_records(artifact, current)
                print(f"Shard {index}/{count}: {len(artifact['selected'])} outcomes written to {args.evidence}")
                return 0
            finalize_started = time.monotonic()
            observed = finalize_documents([artifact], current, run_id=run_id)
            print(f"Evidence finalization: {time.monotonic() - finalize_started:.3f}s; "
                  f"peak Python RSS: {artifact['timing']['peak_python_rss_bytes']} bytes (children excluded)")
            if not args.python_only:
                node_tests = sorted((ROOT / "tests").rglob("test_*.mjs"))
                if not node_tests:
                    raise ValueError("No Node tests discovered")
                completed = subprocess.run(["node", "--test", *(str(path) for path in node_tests)], cwd=ROOT)
                if completed.returncode:
                    return completed.returncode
        from tests import scenario
        print(scenario.coverage(observed))
        print(f"Validated {len(manifest['tests'])} test outcomes for run {run_id}")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Test evidence failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
