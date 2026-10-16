"""Runner/evidence contracts on synthetic tests and fixtures, never the real suite."""
import copy
import gc
import io
import json
from pathlib import Path
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
import weakref
from unittest.mock import patch

from tests import runner, scenario
from tests.support import evidence


def case(name="Example", body=None, *, marked=False, expected_failure=False, controller="neptune",
         kind="live", variants=("default",), either=()):
    def runTest(self):
        if body:
            body(self)
    if marked:
        runTest.scenario = scenario.Meta(name, name, (), tuple(either), tuple(either),
                                         "90.41" if kind == "frozen" else None, controller, variants, "controller")
    if expected_failure:
        runTest = unittest.expectedFailure(runTest)
    return type(name, (unittest.TestCase,), {"runTest": runTest, "fixture_kind": kind,
                                           "fixture_version": "90.39" if kind == "candidate" else None})()


def matrix(controller="neptune"):
    return {"controller": controller, "variant": "default", "version": "1.0", "fingerprint": "source",
            "titles": ["Base", "Layer"], "changed": ["Layer"], "required": ["Base"]}


def cell(controller="neptune", kind="live"):
    return {"controller": controller, "source_controller": "neptune" if kind != "live" else controller,
            "variant": "default", "kind": kind,
            "version": {"live": "1.0", "candidate": "90.39", "frozen": "90.41"}[kind], "stage": "controller",
            "options": {}, "start": None, "fingerprint": "source", "reached": ["Base", "Layer"]}


def manifest(tests, coverage=()):
    return evidence.make_manifest(Path("unused"), tests, coverage, fingerprint={"fixture": "unchanged"})


def run(tests, expected=None, **kwargs):
    return runner.execute(tests, expected or manifest(tests), run_id="run", stream=io.StringIO(), **kwargs)[0]


class EvidenceTests(unittest.TestCase):
    def test_two_shards_execute_each_case_once_and_merge_both_controllers(self):
        calls = []
        def body(controller):
            def gesture(test):
                calls.append(controller)
                test._evidence_cells.append(cell(controller))
            return gesture
        a, b = case("Deck", body("neptune"), marked=True), case("Edge", body("dse"), marked=True, controller="dse")
        expected = manifest([a, b], [matrix(), matrix("dse")])
        documents = [run([a], expected, index=1, count=2), run([b], expected, index=2, count=2)]
        found = evidence.finalize_documents(documents, expected, run_id="run")
        self.assertEqual(calls, ["neptune", "dse"])
        self.assertEqual(found, {("neptune", "default"): {"Base", "Layer"},
                                 ("dse", "default"): {"Base", "Layer"}})

    def test_missing_duplicate_stale_wrong_run_and_failed_shards_are_rejected(self):
        a, b = case("A"), case("B")
        expected = manifest([a, b])
        documents = [run([a], expected, index=1, count=2), run([b], expected, index=2, count=2)]
        for kind in ("missing", "duplicate_shard", "stale", "run", "failed", "duplicate_test", "record_missing"):
            broken = copy.deepcopy(documents)
            if kind == "missing": broken.pop()
            elif kind == "duplicate_shard": broken.append(copy.deepcopy(broken[0]))
            elif kind == "stale": broken[0]["manifest"]["inputs"] = {"changed": True}
            elif kind == "run": broken[0]["run_id"] = "another-run"
            elif kind == "failed": broken[0]["successful"] = False
            elif kind == "duplicate_test":
                broken[1]["selected"] = broken[0]["selected"][:]
                broken[1]["records"] = copy.deepcopy(broken[0]["records"])
            else: broken[0]["records"] = []
            with self.subTest(kind), self.assertRaises(ValueError):
                evidence.finalize_documents(broken, expected, run_id="run")

    def test_complete_shard_numbers_do_not_hide_a_missing_test(self):
        a, b = case("A"), case("B")
        expected = manifest([a, b])
        with self.assertRaisesRegex(ValueError, "Incomplete test selection"):
            evidence.finalize_documents([run([a], expected)], expected, run_id="run")

    def test_subtest_failure_and_skips_are_not_success_evidence(self):
        def failed(test):
            with test.subTest("broken"):
                test.assertEqual(1, 2)
        for body in (failed, lambda test: test.skipTest("unavailable")):
            test = case(body=body)
            expected = manifest([test])
            artifact = run([test], expected)
            self.assertIn(artifact["records"][0]["outcome"], ("failure", "skipped"))
            with self.assertRaises(ValueError):
                evidence.finalize_documents([artifact], expected, run_id="run")

    def test_expected_failure_is_explicit_and_unexpected_success_fails(self):
        for fails in (True, False):
            test = case(body=lambda test: test.assertFalse(fails), expected_failure=True)
            expected = manifest([test])
            artifact = run([test], expected)
            if fails:
                self.assertEqual(artifact["records"][0]["outcome"], "expected_failure")
                self.assertEqual(evidence.finalize_documents([artifact], expected, run_id="run"), {})
            else:
                with self.assertRaises(ValueError):
                    evidence.finalize_documents([artifact], expected, run_id="run")

    def test_candidate_and_frozen_reach_cannot_cover_a_live_layer(self):
        for kind in ("candidate", "frozen"):
            test = case(body=lambda test: test._evidence_cells.append(cell(kind=kind)), marked=True, kind=kind)
            expected = manifest([test], [matrix()])
            artifact = run([test], expected)
            with self.subTest(kind), self.assertRaisesRegex(ValueError, "No live scenario"):
                evidence.finalize_documents([artifact], expected, run_id="run")

    def test_neptune_reach_cannot_satisfy_dse_coverage(self):
        test = case(body=lambda test: test._evidence_cells.append(cell()), marked=True)
        expected = manifest([test], [matrix(), matrix("dse")])
        with self.assertRaisesRegex(ValueError, "No live scenario.*dse"):
            evidence.finalize_documents([run([test], expected)], expected, run_id="run")

    def test_missing_changed_layer_and_wrong_fixture_fingerprint_fail(self):
        for problem in ("reach", "fingerprint", "source_controller", "stage_metadata"):
            observation = cell()
            if problem == "reach": observation["reached"] = ["Base"]
            elif problem == "stage_metadata": del observation["stage"]
            else: observation[problem] = "wrong"
            test = case(body=lambda test: test._evidence_cells.append(observation), marked=True)
            expected = manifest([test], [matrix()])
            with self.subTest(problem), self.assertRaises(ValueError):
                evidence.finalize_documents([run([test], expected)], expected, run_id="run")

    def test_empty_scenario_execution_is_not_complete(self):
        test = case(marked=True)
        expected = manifest([test])
        with self.assertRaisesRegex(ValueError, "no execution cells"):
            evidence.finalize_documents([run([test], expected)], expected, run_id="run")

    def test_omitted_variant_or_assumption_combination_is_rejected(self):
        cells = []
        for variant in ("default", "alternative"):
            for exposed in (True, False):
                observation = cell()
                observation.update(variant=variant, options={"exposed_fires": exposed})
                cells.append(observation)
        for missing in (cells[:2], cells[:-1]):
            test = case(body=lambda test: test._evidence_cells.extend(missing), marked=True,
                        variants=("default", "alternative"), either=("A9",))
            both = [matrix(), {**matrix(), "variant": "alternative"}]
            expected = manifest([test], both)
            with self.subTest(count=len(missing)), self.assertRaisesRegex(ValueError, "variant/assumption matrix"):
                evidence.finalize_documents([run([test], expected)], expected, run_id="run")

    def test_dropping_a_cell_is_detected_even_when_other_cells_cover_its_matrix(self):
        test = case(body=lambda test: test._evidence_cells.extend([cell(), cell()]), marked=True)
        expected = manifest([test], [matrix()])
        artifact = run([test], expected)
        artifact["records"][0]["cells"].pop()
        with self.assertRaisesRegex(ValueError, "Missing execution cells"):
            evidence.finalize_documents([artifact], expected, run_id="run")

    def test_static_test_cells_never_satisfy_scenario_coverage(self):
        test = case(body=lambda test: test._evidence_cells.append(cell()))
        expected = manifest([test], [matrix()])
        with self.assertRaisesRegex(ValueError, "No live scenario"):
            evidence.finalize_documents([run([test], expected)], expected, run_id="run")

    def test_historical_version_and_live_stage_must_match_the_contract(self):
        for kind, field in (("frozen", "version"), ("candidate", "controller"), ("live", "stage")):
            observation = cell(kind=kind)
            observation[field] = "wrong"
            test = case(body=lambda test: test._evidence_cells.append(observation), marked=True, kind=kind)
            expected = manifest([test], [matrix()])
            with self.subTest(kind), self.assertRaises(ValueError):
                evidence.finalize_documents([run([test], expected)], expected, run_id="run")

    def test_only_the_existing_exporter_skip_reason_is_permitted(self):
        name = "test_a_vdf_that_is_not_the_export_of_its_json_fails"
        for module, classname, reason in (
                ("tests.integration.release.test_release", "CheckTests", "needs the VDF exporter"),
                ("tests.integration.release.test_release", "CheckTests", "needs the VDF exporter"),
                ("tests.integration.release.test_release", "CheckTests", "some new excuse"),
                (__name__, "CheckTests", "needs the VDF exporter"),
                ("tests.integration.release.test_release", "UnrelatedTests", "needs the VDF exporter")):
            method = unittest.skip(reason)(lambda self: None)
            test = type(classname, (unittest.TestCase,), {name: method, "__module__": module})(name)
            expected = manifest([test])
            artifact = run([test], expected)
            if test.id() in evidence.PERMITTED_SKIPS and reason == "needs the VDF exporter":
                self.assertEqual(evidence.finalize_documents([artifact], expected, run_id="run"), {})
            else:
                with self.assertRaisesRegex(ValueError, "Unsuccessful test evidence"):
                    evidence.finalize_documents([artifact], expected, run_id="run")

    def test_duplicate_collection_is_rejected(self):
        test = case()
        with self.assertRaisesRegex(ValueError, "Duplicate discovered test"):
            manifest([test, test])

    def test_json_roundtrip_preserves_evidence(self):
        test = case(body=lambda test: test._evidence_cells.append(cell()), marked=True)
        expected = manifest([test], [matrix()])
        artifact = json.loads(json.dumps(run([test], expected)))
        self.assertEqual(evidence.finalize_documents([artifact], expected, run_id="run"),
                         {("neptune", "default"): {"Base", "Layer"}})

    def test_fingerprint_tracks_pending_fixtures_and_excludes_overlay_and_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = ("tests/example.py", "findings/frozen.json", "overlay/test.rs", "out/evidence.json")
            for name in paths:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("one")
            listed = SimpleNamespace(stdout=("\0".join(paths) + "\0").encode())
            with patch.object(evidence.subprocess, "run", return_value=listed):
                first = evidence.input_fingerprint(root)
                self.assertEqual(set(first["files"]), set(paths[:2]))
                (root / paths[1]).write_text("two")
                self.assertNotEqual(evidence.input_fingerprint(root)["sha256"], first["sha256"])

    def test_data_fingerprint_keeps_stored_dictionary_order(self):
        self.assertNotEqual(scenario.data_fingerprint({"first": 1, "second": 2}),
                            scenario.data_fingerprint({"second": 2, "first": 1}))

    def test_run_boundary_rejects_in_memory_source_mutation(self):
        with patch.object(scenario, "_data_digests", {}):
            source = {"fixture": {"layer": "original"}}
            scenario.data_fingerprint(source)
            scenario.validate_fixture_integrity()
            source["fixture"]["layer"] = "changed"
            with self.assertRaisesRegex(ValueError, "changed in memory"):
                runner.manifest_for([])

    def test_fixture_integrity_is_established_before_the_first_gesture(self):
        from tests.support.fixtures import scenarios_90_39 as candidate
        for owner, base, load in ((scenario, scenario.ScenarioCase, "layout_data"),
                                 (candidate, candidate.ScenarioCase, "candidate")):
            source = {"controller_mappings": {
                "title": "original", "actions": {"Base": {"title": "Base"}}, "action_layers": {},
                "group": [], "preset": [{"name": "Base", "group_source_bindings": {}}]}}
            def gesture(test):
                for pad in test.each(variants=("default",)):
                    source["controller_mappings"]["title"] = "mutated"
            test = type("MutatesSource", (base,), {"runTest": gesture})()
            with self.subTest(loader=load), patch.object(owner, load, return_value=source), \
                    patch.object(scenario, "_data_digests", {}), patch.object(scenario, "REACHED", {}), \
                    patch.object(candidate, "CANDIDATE_REACHED", {}):
                result = unittest.TestResult()
                test.run(result)
                self.assertTrue(result.wasSuccessful(), result.errors)
                with self.assertRaisesRegex(ValueError, "changed in memory"):
                    scenario.validate_fixture_integrity()


class RunnerTests(unittest.TestCase):
    def test_owned_successful_cases_and_fixtures_are_released_before_later_tests(self):
        from tools import release
        for mode in ("cli", "shard", "package", "scenarios"):
            references, collections = [], []
            class Payload:
                pass
            class First(unittest.TestCase):
                def runTest(self):
                    self.payload = Payload()
                    references.extend((weakref.ref(self), weakref.ref(self.payload)))
            class Later(unittest.TestCase):
                def runTest(self):
                    gc.collect()
                    self.assertEqual(len(references), 2)
                    self.assertTrue(all(reference() is None for reference in references),
                                    "a completed successful case or fixture is still retained")
            def fresh_cases(*args, **kwargs):
                collections.append("collected")
                return [First(), Later()]
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder, \
                    patch.object(runner, "collect", new=fresh_cases), \
                    patch.object(scenario, "scenario_tests", new=fresh_cases), \
                    patch.object(runner, "manifest_for", new=manifest), \
                    patch.object(runner, "test_modules", return_value=[__name__]), \
                    patch.object(release, "shard", return_value=[__name__]), \
                    patch.object(scenario, "coverage", return_value="coverage"), \
                    patch("sys.stdout", new_callable=io.StringIO), \
                    patch("sys.stderr", new_callable=io.StringIO):
                if mode == "package":
                    suite = runner.discovery_suite()
                    result = unittest.TestResult()
                    suite.run(result)
                    self.assertTrue(result.wasSuccessful(), result.errors or result.failures)
                    self.assertEqual(result.testsRun, 3)
                    self.assertEqual(suite.countTestCases(), 2)
                elif mode == "scenarios":
                    self.assertEqual(runner.run_scenarios(), {})
                else:
                    arguments = ["--python-only"] if mode == "cli" else [
                        "--shard", "1", "1", "--run-id", "run", "--evidence", str(Path(folder) / "part.json")]
                    self.assertEqual(runner.main(arguments), 0)
                self.assertEqual(collections, ["collected", "collected"])
                self.assertTrue(all(reference() is None for reference in references))

    def test_execute_consumes_an_iterator_once_and_preserves_external_list_ownership(self):
        calls = []
        expected = manifest([case("A"), case("B")])
        generated = (case(name, body=lambda test: calls.append(test.__class__.__name__)) for name in ("A", "B"))
        artifact, result = runner.execute(generated, expected, run_id="run", stream=io.StringIO())
        self.assertTrue(result.wasSuccessful(), result.errors)
        self.assertEqual(calls, ["A", "B"])
        self.assertEqual(artifact["selected"], list(expected["tests"]))
        self.assertEqual(list(generated), [])
        owned = [case("External")]
        reference = weakref.ref(owned[0])
        run(owned)
        self.assertEqual(len(owned), 1)
        self.assertIs(owned[0], reference())

    def test_shard_rejects_fixture_and_subtest_skips_without_a_success_message(self):
        from tools import release
        for scope in ("setUpClass", "setUpModule", "subTest"):
            module_name = "fixture_skipping"
            module = ModuleType(module_name)
            def skip(*args):
                raise unittest.SkipTest("unavailable fixture")
            def body(test):
                if scope == "subTest":
                    with test.subTest("unavailable cell"):
                        test.skipTest("unavailable fixture")
            attributes = {"__module__": module_name, "runTest": body}
            if scope == "setUpClass":
                attributes["setUpClass"] = classmethod(skip)
            elif scope == "setUpModule":
                module.setUpModule = skip
            test = type("SkippedFixture", (unittest.TestCase,), attributes)()
            expected = manifest([test])
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as folder, \
                    patch.dict("sys.modules", {module_name: module}), \
                    patch.object(runner, "collect", return_value=[test]), \
                    patch.object(runner, "manifest_for", return_value=expected), \
                    patch.object(release, "shard", return_value=[module_name]), \
                    patch("sys.stdout", new_callable=io.StringIO) as output, \
                    patch("sys.stderr", new_callable=io.StringIO) as errors:
                path = Path(folder) / "evidence.json"
                self.assertEqual(runner.main(["--shard", "1", "1", "--run-id", "run",
                                              "--evidence", str(path)]), 1)
                self.assertNotIn("outcomes written", output.getvalue())
                self.assertIn("Test evidence failed", errors.getvalue())
                artifact = json.loads(path.read_text())
                with self.assertRaises(ValueError):
                    evidence.finalize_documents([artifact], expected, run_id="run")
                if scope == "subTest":
                    self.assertEqual(artifact["records"][0]["outcome"], "skipped_subtest")
                    self.assertEqual(artifact["records"][0]["subtest_skips"], ["unavailable fixture"])
                else:
                    self.assertEqual(artifact["records"], [])

    def test_package_discovery_honors_filename_and_name_filters_without_finalizer(self):
        import tests as test_package
        modules = {}
        for name in ("test_native", "test_scenarios"):
            module = modules[name] = ModuleType(name)
            module.Example = type("Example", (unittest.TestCase,), {
                "__module__": name, "test_selected": lambda self: None, "test_other": lambda self: None})
        for pattern, names, expected in (
                ("test_native.py", None, ["test_native.Example.test_other", "test_native.Example.test_selected"]),
                ("test_*.py", ["*selected*"], ["test_native.Example.test_selected", "test_scenarios.Example.test_selected"]),
                ("test_native.py", ["*selected*"], ["test_native.Example.test_selected"]),
                ("test_*.py", [], []),
                ("test_missing.py", None, [])):
            loader = unittest.TestLoader()
            loader.testNamePatterns = names
            with self.subTest(pattern=pattern, names=names), patch.dict("sys.modules", modules), \
                    patch.object(runner, "test_modules", return_value=list(modules)), \
                    patch.object(runner, "manifest_for", side_effect=AssertionError("partial finalizer")):
                suite = test_package.load_tests(loader, unittest.TestSuite(), pattern)
                self.assertNotIsInstance(suite, runner.EvidenceSuite)
                self.assertEqual([test.id() for test in evidence.flatten(suite)], expected)
                result = unittest.TestResult()
                suite.run(result)
                self.assertTrue(result.wasSuccessful(), result.errors)
                self.assertEqual(result.testsRun, len(expected))

    def test_unrestricted_package_discovery_keeps_the_complete_evidence_gate(self):
        import tests as test_package
        for pattern in (None, "test*.py", "test_*.py"):
            test = case()
            with self.subTest(pattern=pattern), patch.object(runner, "test_modules", return_value=["test_example"]), \
                    patch.object(runner, "collect", return_value=[test]) as collect:
                suite = test_package.load_tests(unittest.TestLoader(), unittest.TestSuite(), pattern)
                self.assertIsInstance(suite, runner.EvidenceSuite)
                self.assertEqual(list(evidence.flatten(suite)), [test])
                self.assertEqual(collect.call_args.kwargs["modules"], ["test_example"])

    def test_module_and_class_fixtures_run_once_including_errors(self):
        for hook in (False, True):
            for failure in (None, "setUpModule", "setUpClass", "tearDownClass", "tearDownModule"):
                calls, modules, tests = [], {}, []
                for label in ("first", "second"):
                    name = "fixture_lifecycle_" + label
                    module = modules[name] = ModuleType(name)
                    def callback(event, label=label):
                        def invoke(*args):
                            calls.append((label, event))
                            if label == "first" and event == failure:
                                raise RuntimeError("fixture error")
                        return invoke
                    module.setUpModule = callback("setUpModule")
                    module.tearDownModule = callback("tearDownModule")
                    tests.append(type("Example", (unittest.TestCase,), {
                        "__module__": name, "runTest": callback("body"),
                        "setUpClass": classmethod(callback("setUpClass")),
                        "tearDownClass": classmethod(callback("tearDownClass")),
                    })())
                expected = manifest(tests)
                with self.subTest(hook=hook, failure=failure), patch.dict("sys.modules", modules):
                    if hook:
                        result = unittest.TestResult()
                        with patch.object(runner, "manifest_for", return_value=expected), \
                                patch.object(runner, "collect", return_value=[]):
                            runner.EvidenceSuite(tests).run(result)
                    else:
                        _, result = runner.execute(tests, expected, run_id="run", stream=io.StringIO())
                    self.assertEqual(result.wasSuccessful(), failure is None)
                    first = ["setUpModule"]
                    if failure != "setUpModule":
                        first.append("setUpClass")
                        if failure != "setUpClass":
                            first.extend(("body", "tearDownClass"))
                        first.append("tearDownModule")
                    all_events = ([("first", event) for event in first]
                                  + [("second", event) for event in
                                     ("setUpModule", "setUpClass", "body", "tearDownClass", "tearDownModule")])
                    self.assertEqual(calls, all_events)

    def test_module_timing_includes_class_setup_and_teardown_once(self):
        clock, calls = [0], []
        def setup(cls):
            clock[0] += 3
            calls.append("setup")
        def body(test):
            clock[0] += 5
            calls.append("body")
        def teardown(cls):
            clock[0] += 7
            calls.append("teardown")
        test = type("Timed", (unittest.TestCase,), {"runTest": body, "setUpClass": classmethod(setup),
                                                   "tearDownClass": classmethod(teardown)})()
        with patch.object(runner.time, "monotonic", side_effect=lambda: clock[0]):
            artifact = run([test])
        self.assertEqual(calls, ["setup", "body", "teardown"])
        self.assertEqual(artifact["module_seconds"], {__name__: 15})
        self.assertEqual(artifact["records"][0]["seconds"], 5)

    def test_package_discovery_runs_cases_once_and_adds_finalizer(self):
        calls = []
        test = case(body=lambda test: calls.append("ran"))
        expected = manifest([test])
        result = unittest.TestResult()
        with patch.object(runner, "manifest_for", return_value=expected), \
                patch.object(runner, "collect", return_value=[]):
            runner.EvidenceSuite([test]).run(result)
        self.assertTrue(result.wasSuccessful(), result.errors)
        self.assertEqual(calls, ["ran"])
        self.assertEqual(result.testsRun, 2)

    def test_package_discovery_surfaces_finalizer_failure(self):
        test = case(marked=True)
        with patch.object(runner, "manifest_for", return_value=manifest([test])), \
                patch.object(runner, "collect", return_value=[]):
            result = unittest.TestResult()
            runner.EvidenceSuite([test]).run(result)
        self.assertFalse(result.wasSuccessful())
        self.assertIn("no execution cells", result.errors[0][1])

    def test_standalone_selection_contains_only_decorated_cases(self):
        marked = case(marked=True)
        ordinary = case("Static")
        suite = unittest.TestSuite([marked, ordinary])
        with patch.object(scenario, "modules", return_value=[ModuleType("fixture")]), \
                patch.object(unittest.defaultTestLoader, "loadTestsFromModule", return_value=suite):
            self.assertEqual(scenario.scenario_tests(), [marked])

    def test_nonempty_reach_does_not_execute_tests_or_establish_completeness(self):
        observed = {("neptune", "default"): {"Base"}}
        with patch.object(scenario, "REACHED", observed), patch.object(scenario, "modules", side_effect=AssertionError):
            self.assertIs(scenario.reached(), observed)

    def test_scenario_cli_reports_failures_and_does_not_write_a_release_report(self):
        def fail():
            raise ValueError("missing scenario")
        with tempfile.TemporaryDirectory() as folder, patch.object(scenario, "report", return_value="Assumptions"), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(scenario.main(["--out", folder], executor=fail), 1)
            self.assertIn("missing scenario", output.getvalue())
            self.assertFalse((Path(folder) / scenario.RELEASE_LIST).exists())

    def test_scenario_rule_lookup_never_executes(self):
        with patch.object(scenario, "for_rule", return_value=[]), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(scenario.main(["R165"], executor=lambda: self.fail("executed")), 0)

    def test_explicit_start_constructs_one_pad_and_records_options(self):
        data = {"controller_mappings": {"actions": {"Base": {"title": "Base"}}, "action_layers": {},
                "group": [], "preset": [{"name": "Base", "group_source_bindings": {}}]}}
        class Gesture(scenario.ScenarioCase):
            def runTest(self):
                for pad in self.each(start=("Base",), controller="dse", variants=("default",), reverse_ties=True):
                    self.assertEqual(pad.names(), ("Base",))
        test = Gesture()
        with patch.object(scenario, "layout_data", return_value=data), patch.object(scenario, "REACHED", {}), \
                patch.object(scenario, "Pad", wraps=scenario.Pad) as constructor:
            result = unittest.TestResult()
            test.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors)
        self.assertEqual(constructor.call_count, 1)
        self.assertEqual(test._evidence_cells[0]["controller"], "dse")
        self.assertEqual(test._evidence_cells[0]["options"], {"reverse_ties": True})


if __name__ == "__main__":
    unittest.main()
