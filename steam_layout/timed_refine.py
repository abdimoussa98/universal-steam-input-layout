"""Refine a checked timed certificate with unresolved fact exclusions.

The baseline classification is recomputed from a replayed witness archive and
an independently validated certificate. Equivalent raw-input formulas share
one hypothesis, but the final report still classifies every original fact.
An optional checkpoint contains unvalidated hypotheses for manual recovery;
it is deliberately not a certificate and cannot authorize exclusions.
"""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

from .model import Layout
from .timed_audit import (TimedAudit, _predicate_data, _write_json,
                          load_certificate, proof_identity, save_certificate)
from .timed_discover import load_witnesses
from .timed_facts import FactCatalogue
from .timed_model import TimedModel
from .timed_predicates import FactExclusion, RequiresBelowAny, RequiresBetweenAny


CHECKPOINT_FORMAT = "timed-refinement-checkpoint-v1"


def facts_for_layers(catalogue, layers=None):
    """Select all three questions, including relations above each layer."""
    titles = tuple(catalogue.names if layers is None else layers)
    if not titles or len(set(titles)) != len(titles):
        raise ValueError("select distinct, nonempty layer names")
    for title in titles:
        if title not in catalogue.model.spec.index:
            raise ValueError(f"Unknown layer: {title}")
    indices = {catalogue.model.spec.index[title] for title in titles}
    return frozenset(fact for fact in catalogue.facts
                     if fact.x in indices or (fact.kind == "below" and fact.y in indices))


def _formula_key(fact):
    return (fact.kind, fact.x, fact.y,
            tuple(sorted(fact.definers)) if fact.kind == "inherit" else ())


def propose_exclusions(baseline, catalogue, witnesses, *, layers=None):
    """Return deduplicated hypotheses and a freshly checked classification.

    These are candidates, never exclusions. Only subsequent induction and
    independent validation can establish that their facts are impossible.
    """
    selected = facts_for_layers(catalogue, layers)
    classification = baseline.classify(catalogue, witnesses)
    observed = {_formula_key(fact) for fact in witnesses.facts}
    unique = {}
    for fact in sorted(classification["possible"] & selected):
        key = _formula_key(fact)
        if fact not in witnesses.facts and key not in observed:
            unique.setdefault(key, FactExclusion(fact))
    return tuple(unique.values()), classification


def load_family_hypotheses(path, model):
    """Read explicitly proposed family predicates; proof checks them later."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
        raise ValueError("family hypotheses must contain a candidates list")
    kinds = {RequiresBelowAny.kind: RequiresBelowAny, RequiresBetweenAny.kind: RequiresBetweenAny}
    candidates = []
    for row in payload["candidates"]:
        if not isinstance(row, dict) or row.get("kind") not in kinds:
            raise ValueError("unsupported family hypothesis kind")
        candidates.append(kinds[row["kind"]].from_data(row))
    count = len(model.spec.layer_names)
    if any(candidate.x >= count or getattr(candidate, "y", 0) >= count or
           any(member >= count for member in candidate.members)
           for candidate in candidates):
        raise ValueError("family hypothesis references an unknown layer")
    return tuple(dict.fromkeys(candidates))


def _counts(classification, facts):
    return {status: len(classification[status] & facts)
            for status in ("proven", "possible", "excluded")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("baseline", type=Path, help="checked baseline certificate")
    parser.add_argument("certificate", type=Path, help="refined certificate output")
    parser.add_argument("report", type=Path, help="full global report output")
    parser.add_argument("--ignore-hold-bindings", action="store_true")
    parser.add_argument("--default-repeat-ms", type=int)
    parser.add_argument("--timeout-ms", type=int, default=10000,
                        help="individual validation/query timeout in milliseconds (default: 10000)")
    parser.add_argument("--refine-timeout-ms", type=int,
                        help="individual refinement timeout (default: --timeout-ms)")
    parser.add_argument("--layer", action="append", dest="layers",
                        help="restrict generated fact hypotheses to this layer's three questions; "
                             "repeat to select more layers; the saved report remains global")
    parser.add_argument("--family-hypotheses", type=Path,
                        help="optional JSON candidates list of additional family hypotheses; "
                             "these are checked regardless of --layer")
    parser.add_argument("--checkpoint", type=Path,
                        help="save unvalidated fixed-point hypotheses before final validation; "
                             "this file is not a certificate")
    args = parser.parse_args(argv)
    progress = lambda message: print(message, file=sys.stderr, flush=True)
    try:
        refinement_timeout = args.timeout_ms if args.refine_timeout_ms is None else args.refine_timeout_ms
        if args.timeout_ms < 1 or refinement_timeout < 1:
            raise ValueError("timeout-ms and refine-timeout-ms must be positive")
        paths = [args.layout, args.archive, args.baseline, args.certificate, args.report]
        paths.extend(path for path in (args.family_hypotheses, args.checkpoint) if path is not None)
        if len({path.resolve() for path in paths}) != len(paths):
            raise ValueError("all input and output paths must differ")
        model = TimedModel(Layout(json.loads(args.layout.read_text(encoding="utf-8"))),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        catalogue = FactCatalogue(model)
        selected = facts_for_layers(catalogue, args.layers)
        families = (() if args.family_hypotheses is None else
                    load_family_hypotheses(args.family_hypotheses, model))
        witnesses = load_witnesses(model, catalogue, args.archive)
        baseline = load_certificate(model, args.baseline, timeout_ms=args.timeout_ms, progress=progress)
        exclusions, classification = propose_exclusions(baseline, catalogue, witnesses, layers=args.layers)
        details = {
            "selected_layers": list(catalogue.names if args.layers is None else args.layers),
            "baseline_counts": _counts(classification, set(catalogue.facts)),
            "baseline_selected_counts": _counts(classification, selected),
            "fact_hypotheses": len(exclusions), "family_hypotheses": len(families),
            "refine_timeout_ms": refinement_timeout, "validation_timeout_ms": args.timeout_ms,
        }
        progress(f"Refining {len(exclusions)} distinct fact hypotheses and {len(families)} family hypotheses")
        refined = baseline.refine((*exclusions, *families), timeout_ms=refinement_timeout)
        if args.checkpoint is not None:
            _write_json(args.checkpoint, {
                "format": CHECKPOINT_FORMAT, "identity": proof_identity(model),
                "stage": "fixed_point_unvalidated", "verified": False,
                "scope": "Unvalidated hypotheses for manual recovery; not a certificate or exclusion report.",
                "refinement": details, "stats": refined.stats,
                "invariants": [_predicate_data(candidate) for candidate in refined.invariants],
            })
        refined.timeout_ms = args.timeout_ms
        # Saving validates independently. A failure leaves only the explicitly
        # unvalidated checkpoint, never a new certificate or exclusion report.
        save_certificate(refined, args.certificate)
        audit = TimedAudit(refined, catalogue, witnesses)
        report = audit.report()
        selected_counts = _counts(audit.classification, selected)
        details.update({"selected_counts": selected_counts,
                        "selected_complete_for_model": selected_counts["possible"] == 0})
        report["refinement"] = details
        _write_json(args.report, report)
        print(json.dumps({"complete_for_model": report["complete_for_model"],
                          "global_complete_for_model": report["global_complete_for_model"],
                          "selected_complete_for_model": details["selected_complete_for_model"],
                          "counts": report["counts"], "selected_counts": selected_counts,
                          "fact_hypotheses": len(exclusions), "family_hypotheses": len(families),
                          "certificate": str(args.certificate), "report": str(args.report)},
                         indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
