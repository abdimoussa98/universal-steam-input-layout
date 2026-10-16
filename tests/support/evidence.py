"""Explicit, portable test outcomes and scenario reach; never executes tests.

Artifacts belong to one run and one exact input manifest. A partial shard is
useful evidence, but only the finalizer can establish complete-suite coverage.
"""
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import time
import unittest

SCHEMA = 1
# Preserve the one pre-existing dependency-conditioned release check. This is
# a specific documented exception, not permission to skip other test coverage.
PERMITTED_SKIPS = {
    "tests.integration.release.test_release.CheckTests.test_a_vdf_that_is_not_the_export_of_its_json_fails":
        "needs the VDF exporter"
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def input_fingerprint(root):
    """Hash tracked and pending source/fixture inputs, excluding outputs and overlay.

Git's ignore rules exclude native build caches; filenames and bytes both matter.
The list includes historical builders and fixtures, not just working layouts.
"""
    root = Path(root)
    found = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                           cwd=root, check=True, capture_output=True).stdout.decode().split("\0")
    directories = {"tests", "steam_layout", "tools", "resources", "findings", "versions", "docs", "skills",
                   ".github", "archived", "neptune", "ibex", "dse"}
    root_files = {"CHANGELOG.md", "README.md", "todos.md"}
    suffixes = {".py", ".json", ".vdf", ".cpp", ".hpp", ".h", ".mjs", ".md", ".csv", ".yml", ".yaml", ".toml"}
    files = {}
    for name in sorted(set(found)):
        path = Path(name)
        if not name or (path.parts[0] not in directories and name not in root_files) or path.suffix not in suffixes:
            continue
        if name == ".github/workflows/overlay.yml":
            continue
        source = root / path
        if source.is_file():
            files[name] = hashlib.sha256(source.read_bytes()).hexdigest()
        else:
            files[name] = "missing"
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True).stdout.decode().strip()
    tags = subprocess.run(["git", "for-each-ref", "--sort=refname", "--format=%(refname) %(objectname)", "refs/tags"],
                          cwd=root, check=True, capture_output=True).stdout.decode().splitlines()
    return {"sha256": digest({"files": files, "head": head, "tags": tags}), "head": head, "tags": tags, "files": files}


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def test_spec(test):
    method = getattr(test, test._testMethodName)
    meta = getattr(method, "scenario", None)
    contract = None
    if meta:
        from tests import scenario
        kind = "frozen" if meta.frozen else getattr(test, "fixture_kind", "live")
        controller = "neptune" if meta.frozen else meta.controller or getattr(test, "fixture_controller", None) or scenario.CONTROLLER
        contract = {"kind": kind, "controller": controller,
                    "source_controller": "neptune" if kind != "live" else controller,
                    "version": meta.frozen or getattr(test, "fixture_version", None),
                    "variants": list(meta.variants), "stage": meta.stage,
                    "rules": list(meta.rules), "rests": list(meta.rests), "either": list(meta.either),
                    "switches": {scenario.SWITCHES[a][0]: list(scenario.SWITCHES[a][1]) for a in meta.either}}
    return {"scenario": meta.check if meta else None, "contract": contract,
            "allowed_skip": PERMITTED_SKIPS.get(test.id()),
            "expected_failure": bool(getattr(method, "__unittest_expecting_failure__", False)
                                     or getattr(test, "__unittest_expecting_failure__", False))}


def make_manifest(root, tests, coverage=(), fingerprint=None):
    expected = {}
    for test in tests:
        if test.id() in expected:
            raise ValueError(f"Duplicate discovered test: {test.id()}")
        expected[test.id()] = test_spec(test)
    return {"schema": SCHEMA, "inputs": input_fingerprint(root) if fingerprint is None else fingerprint,
            "tests": expected, "coverage": list(coverage)}


class EvidenceResult(unittest.TextTestResult):
    """Record subtest failures as the parent outcome and retain each gesture cell."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self._active = {}
        self.module_seconds = {}

    def startTest(self, test):
        super().startTest(test)
        test._evidence_cells = []
        self._active[id(test)] = {"id": test.id(), **test_spec(test), "outcome": "incomplete",
                                  "cells": test._evidence_cells, "started": time.monotonic()}

    def _outcome(self, test, outcome):
        if id(test) in self._active:
            self._active[id(test)]["outcome"] = outcome

    def addSuccess(self, test):
        self._outcome(test, "success")
        super().addSuccess(test)

    def addFailure(self, test, err):
        self._outcome(test, "failure")
        super().addFailure(test, err)

    def addError(self, test, err):
        self._outcome(test, "error")
        super().addError(test, err)

    def addSkip(self, test, reason):
        parent = getattr(test, "test_case", test)
        self._outcome(parent, "skipped" if parent is test else "skipped_subtest")
        if id(parent) in self._active:
            if parent is test:
                self._active[id(parent)]["skip_reason"] = reason
            else:
                self._active[id(parent)].setdefault("subtest_skips", []).append(reason)
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self._outcome(test, "expected_failure")
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self._outcome(test, "unexpected_success")
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self._outcome(test, "failure" if issubclass(err[0], test.failureException) else "error")
        super().addSubTest(test, subtest, err)

    def stopTest(self, test):
        record = self._active.pop(id(test))
        record["seconds"] = time.monotonic() - record.pop("started")
        record["cell_count"] = len(record["cells"])
        self.records.append(record)
        super().stopTest(test)


def document(manifest, result, selected, *, run_id, index=1, count=1):
    return {"schema": SCHEMA, "run_id": run_id, "manifest": manifest,
            "shard": {"index": index, "count": count}, "selected": list(selected),
            "successful": result.wasSuccessful(), "records": result.records,
            "module_seconds": dict(result.module_seconds)}


def validate_shard_records(item, manifest):
    """Validate local execution before a shard may report success."""
    selected = item.get("selected", [])
    found = item.get("records", [])
    ids = [record.get("id") for record in found]
    if len(selected) != len(set(selected)) or len(ids) != len(set(ids)) or set(ids) != set(selected):
        raise ValueError("Incomplete or duplicate shard test records")
    if not item.get("successful"):
        raise ValueError("Shard contains test failures")
    for record in found:
        identity = record["id"]
        spec = manifest["tests"].get(identity)
        if spec is None or any(record.get(key) != value for key, value in spec.items()):
            raise ValueError(f"Unexpected test identity or metadata: {identity}")
        expected = "expected_failure" if spec["expected_failure"] else "success"
        permitted_skip = (record.get("outcome") == "skipped" and spec.get("allowed_skip") is not None
                          and record.get("skip_reason") == spec["allowed_skip"])
        if record.get("subtest_skips") or (record.get("outcome") != expected and not permitted_skip):
            raise ValueError(f"Unsuccessful test evidence: {identity} ({record.get('outcome')})")
        if spec["scenario"] and not record.get("cells"):
            raise ValueError(f"Scenario has no execution cells: {identity}")
        if record.get("cell_count") != len(record.get("cells", [])):
            raise ValueError(f"Missing execution cells: {identity}")
    return found


def finalize_documents(documents, manifest, *, run_id):
    """Reject incomplete/stale/duplicate/failed evidence and enforce live R165.

Returns reach by (controller, variant). Historical and candidate cells remain
in the artifact for attribution but cannot satisfy current-layer coverage.
"""
    if not documents or not run_id:
        raise ValueError("Evidence and a nonempty run ID are required")
    records, seen_shards, count = {}, set(), None
    for item in documents:
        if item.get("schema") != SCHEMA or item.get("run_id") != run_id:
            raise ValueError("Evidence schema or run ID mismatch")
        if item.get("manifest") != manifest:
            raise ValueError("Stale evidence: source, fixtures, selection or coverage baseline changed")
        shard = item.get("shard", {})
        n, total = shard.get("index"), shard.get("count")
        if not isinstance(n, int) or not isinstance(total, int) or total < 1 or not 1 <= n <= total:
            raise ValueError("Invalid shard identity")
        if count is not None and count != total:
            raise ValueError("Inconsistent shard counts")
        count = total
        if n in seen_shards:
            raise ValueError(f"Duplicate shard {n}")
        seen_shards.add(n)
        for record in validate_shard_records(item, manifest):
            identity = record["id"]
            if identity in records:
                raise ValueError(f"Duplicate test evidence: {identity}")
            records[identity] = record
    if seen_shards != set(range(1, count + 1)):
        raise ValueError("Incomplete shard set")
    if set(records) != set(manifest["tests"]):
        missing = sorted(set(manifest["tests"]) - set(records))
        raise ValueError("Incomplete test selection: " + ", ".join(missing[:10]))
    reached = {}
    live = {(entry["controller"], entry["variant"]): entry for entry in manifest["coverage"]}
    for record in records.values():
        contract = manifest["tests"][record["id"]].get("contract")
        if not contract:
            continue                 # a helper called from a static test is never scenario coverage
        switches = contract["switches"]
        combinations = set()
        for cell in record.get("cells", []):
            required = {"controller", "source_controller", "variant", "kind", "version", "stage",
                        "options", "start", "fingerprint", "reached"}
            if not isinstance(cell, dict) or not required <= cell.keys():
                raise ValueError(f"Incomplete scenario cell: {record['id']}")
            if cell["kind"] not in {"live", "frozen", "candidate"}:
                raise ValueError(f"Unknown fixture kind: {cell['kind']}")
            for key in ("kind", "controller", "source_controller", "stage"):
                if cell[key] != contract[key]:
                    raise ValueError(f"Scenario fixture {key} mismatch: {record['id']}")
            if cell["variant"] not in contract["variants"]:
                raise ValueError(f"Unexpected scenario variant: {record['id']}")
            chosen = tuple(cell["options"].get(name) for name in switches)
            if any(value not in switches[name] for name, value in zip(switches, chosen)):
                raise ValueError(f"Missing or invalid assumption option: {record['id']}")
            combinations.add((cell["variant"], chosen))
            if cell["kind"] != "live":
                if cell["version"] != contract["version"]:
                    raise ValueError(f"Historical fixture version mismatch: {record['id']}")
                continue
            key = cell["controller"], cell["variant"]
            entry = live.get(key)
            if entry is None or cell["source_controller"] != cell["controller"]:
                raise ValueError(f"Unexpected live controller/variant: {key}")
            if cell["fingerprint"] != entry["fingerprint"]:
                raise ValueError(f"Stale live fixture in scenario: {record['id']}")
            if cell["version"] != entry["version"]:
                raise ValueError(f"Live fixture version mismatch: {record['id']}")
            if not set(cell["reached"]) <= set(entry["titles"]):
                raise ValueError(f"Unknown reached layer: {record['id']}")
            reached.setdefault(key, set()).update(cell["reached"])
        if record["outcome"] == "success":
            required = {(variant, tuple(way)) for variant in contract["variants"]
                        for way in itertools.product(*switches.values())}
            if combinations != required:
                raise ValueError(f"Incomplete scenario variant/assumption matrix: {record['id']}")
    for key, entry in live.items():
        if key not in reached:
            raise ValueError(f"No live scenario evidence for {key}")
        missing = set(entry["changed"]) - reached[key]
        if missing:
            raise ValueError(f"R165 {key}: changed layers have no scenario: {', '.join(sorted(missing))}")
        missing = set(entry.get("required", [])) - reached[key]
        if missing:
            raise ValueError(f"Missing established scenario reach {key}: {', '.join(sorted(missing))}")
    return reached
