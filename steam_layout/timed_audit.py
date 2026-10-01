"""Complete layer-query reports from checked timed witnesses and induction.

Certificates store hypotheses, never trusted exclusions. Loading one repeats
the initialization and inductive-step checks before it may support a report.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

from .invariants import Candidate
from .model import Layout
from .stackdb import describe
from .timed_discover import load_witnesses
from .timed_facts import FactCatalogue
from .timed_model import TimedModel
from .timed_predicates import FactExclusion, RequiresBelowAny, RequiresBetweenAny
from .timed_proof import TimedProof
from .timed_search import TimedQuotient


CERTIFICATE_FORMAT = "timed-invariant-certificate-v1"
ALGORITHM_FILES = ("timed_proof.py", "timed_envelope.py", "timed_phase_envelope.py",
                   "timed_progress_envelope.py", "timed_elapsed_envelope.py",
                   "timed_analog_envelope.py", "symbolic_batch.py",
                   "invariants.py", "timed_facts.py", "timed_predicates.py")
SCOPE = (
    "Complete ordered-stack projections under the recorded TimedModel contract; "
    "not a claim of Steam hardware equivalence. Inheritance means original raw "
    "bindings below the requested layer, irrespective of upper layers or mode shifts. "
    "Reachability requires replayed timed witnesses; exclusions require checked induction."
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def proof_identity(model):
    digest = hashlib.sha256()
    for filename in ALGORITHM_FILES:
        digest.update(filename.encode("utf-8"))
        digest.update(Path(__file__).with_name(filename).read_bytes())
    return {"quotient": TimedQuotient(model).identity,
            "algorithm_sha256": digest.hexdigest(), "algorithm_files": list(ALGORITHM_FILES)}


def _predicate_data(predicate):
    if isinstance(predicate, (FactExclusion, RequiresBelowAny, RequiresBetweenAny)):
        return predicate.to_data()
    if isinstance(predicate, Candidate):
        return asdict(predicate)
    raise ValueError(f"unsupported timed invariant type: {type(predicate).__name__}")


def _predicate_from_data(row, proof, catalogue=None):
    if not isinstance(row, dict):
        raise ValueError("invalid serialized invariant fields")
    if row.get("kind") == FactExclusion.kind:
        if catalogue is None:
            catalogue = FactCatalogue(proof.timed_model)
        return FactExclusion.from_data(row, catalogue)
    if row.get("kind") == RequiresBetweenAny.kind:
        if set(row) != {"kind", "x", "y", "members"}:
            raise ValueError("invalid serialized requires_between_any fields")
        if (any(type(row[key]) is not int or not 0 <= row[key] < len(proof.model.layer_names)
                for key in ("x", "y")) or row["x"] == row["y"]):
            raise ValueError("invalid serialized predicate endpoint indices")
        if (not isinstance(row["members"], list) or not row["members"] or
                any(type(layer) is not int or not 0 <= layer < len(proof.model.layer_names)
                    or layer in (row["x"], row["y"]) for layer in row["members"])):
            raise ValueError("invalid serialized predicate member indices")
        return RequiresBetweenAny.from_data(row)
    if row.get("kind") == RequiresBelowAny.kind:
        if set(row) != {"kind", "x", "members"}:
            raise ValueError("invalid serialized requires_below_any fields")
        if type(row["x"]) is not int or not 0 <= row["x"] < len(proof.model.layer_names):
            raise ValueError("invalid serialized predicate target index")
        if (not isinstance(row["members"], list) or not row["members"] or
                any(type(layer) is not int or not 0 <= layer < len(proof.model.layer_names)
                    or layer == row["x"] for layer in row["members"])):
            raise ValueError("invalid serialized predicate member indices")
        return RequiresBelowAny.from_data(row)
    if set(row) != {"kind", "x", "y"}:
        raise ValueError("invalid serialized invariant fields")
    kind, x, y = row["kind"], row["x"], row["y"]
    if (kind not in ("absent", "requires", "excludes", "not_below", "held", "released") or
            type(x) is not int or not 0 <= x < len(proof.model.layer_names) or type(y) is not int):
        raise ValueError("invalid serialized invariant kind or layer index")
    if kind == "absent":
        valid_y = y == -1
    elif kind in ("held", "released"):
        valid_y = 0 <= y < len(proof.model.controls)
    else:
        valid_y = 0 <= y < len(proof.model.layer_names)
    if not valid_y:
        raise ValueError("invalid serialized invariant dependency index")
    return Candidate(kind, x, y)


def _decode_predicates(rows, proof):
    # Resolve raw-input identities through one canonical catalogue. This
    # restores definer context from the current layout, never from the file.
    catalogue = (FactCatalogue(proof.timed_model) if any(
        isinstance(row, dict) and row.get("kind") == FactExclusion.kind for row in rows) else None)
    return tuple(_predicate_from_data(row, proof, catalogue) for row in rows)


def validate_proof(proof):
    """Cache only validation performed in this process for this exact proof."""
    if not proof.finished:
        raise ValueError("finish induction before checking its certificate")
    identity = proof_identity(proof.timed_model)
    serialized = [_predicate_data(candidate) for candidate in proof.invariants]
    decoded = _decode_predicates(serialized, proof)
    if any(isinstance(original, FactExclusion) and original.fact.definers != canonical.fact.definers
           for original, canonical in zip(proof.invariants, decoded)):
        raise ValueError("fact exclusion definer context does not match the current catalogue")
    signature = _json({"identity": identity, "invariants": serialized})
    cached = getattr(proof, "_timed_audit_validation", None)
    if cached is None or cached[0] != signature:
        validation = proof.validate()
        if not isinstance(validation, dict) or validation.get("verified") is not True:
            raise ValueError("timed induction validation did not produce a verified certificate")
        proof._timed_audit_validation = (signature, validation)
    return dict(proof._timed_audit_validation[1])


def _write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def save_certificate(proof, path):
    validation = validate_proof(proof)
    data = {"format": CERTIFICATE_FORMAT, "identity": proof_identity(proof.timed_model),
            "invariants": [_predicate_data(candidate) for candidate in proof.invariants],
            "proof_stats": proof.stats, "validation": validation, "scope": SCOPE}
    _write_json(path, data)
    return data


def load_certificate(model, path, *, timeout_ms=10000, progress=None):
    """Reconstruct and independently validate untrusted serialized hypotheses."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != CERTIFICATE_FORMAT:
        raise ValueError("unsupported timed invariant certificate format")
    if _json(data.get("identity")) != _json(proof_identity(model)):
        raise ValueError("timed invariant certificate identity mismatch")
    raw = data.get("invariants")
    if not isinstance(raw, list):
        raise ValueError("certificate invariants must be a list")
    proof = TimedProof(model, timeout_ms=timeout_ms, progress=progress)
    invariants = _decode_predicates(raw, proof)
    if len(set(invariants)) != len(invariants):
        raise ValueError("duplicate serialized invariants")
    proof.invariants = tuple(invariants)
    proof.stats = data.get("proof_stats", {})
    if not isinstance(proof.stats, dict):
        raise ValueError("certificate proof_stats must be an object")
    proof.finished = True
    # The file's validation field is informational and is deliberately ignored.
    validate_proof(proof)
    return proof


def fact_id(fact):
    return f"{fact.kind}:{fact.x}:{fact.y}:{fact.j}"


class TimedAudit:
    """One validated proof/classification reused for any number of layers."""

    def __init__(self, proof, catalogue, witnesses):
        if (catalogue.model is not proof.timed_model or witnesses.model is not proof.timed_model or
                witnesses.catalogue is not catalogue):
            raise ValueError("proof, catalogue and witnesses must share the same timed model")
        self.identity = proof_identity(proof.timed_model)
        if _json(witnesses.identity) != _json(self.identity["quotient"]):
            raise ValueError("witness archive and proof quotient identities differ")
        self.proof, self.catalogue, self.witnesses = proof, catalogue, witnesses
        self.validation = validate_proof(proof)
        self.classification = proof.classify(catalogue, witnesses)
        sets = [set(self.classification[key]) for key in ("proven", "possible", "excluded")]
        if (set.union(*sets) != set(catalogue.facts) or any(
                sets[a] & sets[b] for a, b in ((0, 1), (0, 2), (1, 2)))):
            raise ValueError("classification must partition every catalogue alternative")
        if sets[0] != set(witnesses.facts):
            raise ValueError("classified positive facts do not match replayed witnesses")
        if self.classification["complete_for_model"] != (not sets[1]):
            raise ValueError("classification completeness does not match unresolved alternatives")
        self.status = {fact: kind for kind in ("proven", "possible", "excluded")
                       for fact in self.classification[kind]}

    def _layer_facts(self, title):
        if title not in self.catalogue.model.spec.index:
            raise ValueError(f"Unknown layer: {title}")
        x = self.catalogue.model.spec.index[title]
        return tuple(fact for fact in self.catalogue.facts if
                     fact.x == x or (fact.kind == "below" and fact.y == x))

    def _counts(self, facts):
        return {kind: sum(self.status[fact] == kind for fact in facts)
                for kind in ("proven", "possible", "excluded")}

    def _traces(self, facts):
        result = {}
        for fact in sorted(facts):
            if self.status[fact] == "proven":
                node = self.witnesses.witness_nodes[fact]
                if str(node) not in result:
                    result[str(node)] = {"node": node, "events": self.witnesses.trace(fact)}
        return result

    def layer_report(self, title, *, include_traces=True):
        facts = self._layer_facts(title)
        x = self.catalogue.model.spec.index[title]
        result = {"layer": title, "scope": SCOPE, "identity": self.identity,
                  "complete_for_model": all(self.status[fact] != "possible" for fact in facts),
                  "validation": self.validation, "below": [], "above": [], "inherited": [],
                  "excluded": {"below": [], "above": [], "inherited": []},
                  "counts": self._counts(facts)}
        inherited = {j: [] for j in self.catalogue.inherited_by_layer[x]}
        for fact in facts:
            status = self.status[fact]
            node = self.witnesses.witness_nodes.get(fact) if status == "proven" else None
            row = {"fact": fact_id(fact), "status": status, "witness": node,
                   "trace_id": str(node) if node is not None else None}
            if fact.kind == "below":
                direction = "below" if fact.x == x else "above"
                other = fact.y if fact.x == x else fact.x
                row["layer"] = self.catalogue.names[other]
                (result["excluded"][direction] if status == "excluded" else
                 result[direction]).append(row)
            else:
                row.update(self.catalogue.valuesmetadata(fact))
                row["summary"] = describe(row["activators"])
                if status == "excluded":
                    source, name = self.catalogue.controls[fact.j]
                    result["excluded"]["inherited"].append({"source": source, "input": name, **row})
                else:
                    inherited[fact.j].append(row)
        for j, values in inherited.items():
            source, name = self.catalogue.controls[j]
            result["inherited"].append({"source": source, "input": name, "values": values})
        if include_traces:
            result["witness_traces"] = self._traces(facts)
        return result

    def report(self, titles=None):
        titles = tuple(self.catalogue.names if titles is None else titles)
        if len(set(titles)) != len(titles):
            raise ValueError("report layers must be distinct")
        selected = {fact for title in titles for fact in self._layer_facts(title)}
        return {"format": "timed-fact-audit-v1", "scope": SCOPE, "identity": self.identity,
                "complete_for_model": all(self.status[fact] != "possible" for fact in selected),
                "global_complete_for_model": self.classification["complete_for_model"],
                "validation": self.validation, "proof": self.proof.stats,
                "queries": {key: value for key, value in self.classification.items()
                            if key not in ("proven", "possible", "excluded", "complete_for_model")},
                "counts": self._counts(selected),
                "witnesses": {"nodes": len(self.witnesses.node_states),
                              "facts": len(self.witnesses.facts)},
                "layers": [self.layer_report(title, include_traces=False) for title in titles],
                "witness_traces": self._traces(selected)}


def format_report(report):
    lines = [report["layer"], report["scope"],
             f"Complete for model: {str(report['complete_for_model']).lower()}"]
    for direction in ("below", "above"):
        lines.append(f"\n{direction.capitalize()}:")
        lines.extend(f"  [{row['status']}] {row['layer']}" for row in report[direction])
    lines.append("\nInherited raw bindings:")
    for row in report["inherited"]:
        lines.append(f"  {row['source']}/{row['input']}")
        for value in row["values"]:
            owner = value["owner"] or (f"blocked by {value['blocked_by']}" if value["blocked_by"] else "unbound")
            suffix = f": {value['summary']}" if value["summary"] else ""
            lines.append(f"    [{value['status']}] {owner}{suffix}")
    counts = report["counts"]
    lines.append(f"\n{counts['proven']} witnessed; {counts['possible']} unresolved; "
                 f"{counts['excluded']} excluded by checked induction.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "show"):
        command = commands.add_parser(name)
        command.add_argument("layout", type=Path)
        command.add_argument("archive", type=Path)
        command.add_argument("certificate", type=Path)
        command.add_argument("--ignore-hold-bindings", action="store_true")
        command.add_argument("--default-repeat-ms", type=int)
        command.add_argument("--timeout-ms", type=int, default=10000)
        if name == "run":
            command.add_argument("report", type=Path)
            command.add_argument("--layer", action="append", dest="layers")
        else:
            command.add_argument("layer")
            command.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    progress = lambda message: print(message, file=sys.stderr, flush=True)
    try:
        if args.timeout_ms < 1:
            raise ValueError("timeout-ms must be positive")
        if args.command == "run":
            paths = [args.layout, args.archive, args.certificate, args.report]
            if len({path.resolve() for path in paths}) != len(paths):
                raise ValueError("layout, witness archive, certificate and report paths must differ")
        model = TimedModel(Layout(json.loads(args.layout.read_text(encoding="utf-8"))),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        catalogue = FactCatalogue(model)
        titles = args.layers if args.command == "run" else [args.layer]
        if titles is not None:
            if len(set(titles)) != len(titles):
                raise ValueError("report layers must be distinct")
            for title in titles:
                if title not in model.spec.index:
                    raise ValueError(f"Unknown layer: {title}")
        witnesses = load_witnesses(model, catalogue, args.archive)
        if args.command == "run":
            proof = TimedProof(model, witnesses.node_states.values(),
                               timeout_ms=args.timeout_ms, progress=progress).run()
            audit = TimedAudit(proof, catalogue, witnesses)
            report = audit.report(args.layers)
            save_certificate(proof, args.certificate)
            _write_json(args.report, report)
            result = {"complete_for_model": report["complete_for_model"], "counts": report["counts"],
                      "certificate": str(args.certificate), "report": str(args.report)}
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            proof = load_certificate(model, args.certificate, timeout_ms=args.timeout_ms, progress=progress)
            report = TimedAudit(proof, catalogue, witnesses).layer_report(args.layer)
            print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_report(report))
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
