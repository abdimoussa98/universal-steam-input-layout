"""Join concrete search witnesses with inductive upper bounds for one layer."""
import argparse
import json
from pathlib import Path
import sys

import z3

from .held_model import HeldModel
from .invariants import InvariantProof, candidates_from_states
from .model import Layout
from .stack_evidence import Evidence
from .stackdb import StackDB, Value, describe

DEFAULT_LAYOUT = Path(__file__).resolve().parents[1] / "neptune/single-set-default_hold-gyro_latest.json"
MODEL_SCOPE = ("Results are relative to HeldModel, an untimed model. It simplifies delay ordering, "
               "analog thresholds, mode shifts and hold ownership; hardware reachability is not established.")


def layer_report(proof, title, evidence=None):
    """All lower owners with X anywhere in the stack, and layers above/below X.

    'proven' means a search witness exists in this model. 'possible' means
    induction did not exclude it, including solver unknown. Completeness is
    claimed only when every upper-bound fact has a witness.
    """
    model = proof.model
    if title not in model.index:
        raise ValueError(f"Unknown layer: {title}")
    evidence = evidence or Evidence(model)
    if evidence.model is not model:
        raise ValueError("Evidence and proof must share the same HeldModel instance")
    observed = evidence.facts(title)
    ranks = proof.symbolic.ranks
    x = model.index[title]
    solver = proof.query_solver()
    report = {"layer": title, "scope": MODEL_SCOPE, "proof": proof.stats,
              "invariants": [c.describe(model) for c in proof.invariants],
              "below": [], "above": [], "inherited": [],
              "excluded": {"below": [], "above": [], "inherited": []}}
    queries = unknown = 0

    def classify(predicate, witness):
        nonlocal queries, unknown
        solver.push()
        solver.add(predicate)
        result = solver.check()
        queries += 1
        solver.pop()
        if result == z3.unsat:
            if witness is not None:
                raise ValueError("An inductive exclusion contradicts a search witness; check model/evidence consistency")
            return None
        if result == z3.unknown:
            unknown += 1
        return {"status": "proven" if witness is not None else "possible",
                "witness": witness, "solver": str(result)}

    for direction in ("below", "above"):
        for y, name in enumerate(model.layer_names):
            if x == y:
                continue
            order = ranks[y] < ranks[x] if direction == "below" else ranks[y] > ranks[x]
            info = classify(z3.And(ranks[x] > 0, ranks[y] > 0, order), observed[direction].get(name))
            if info is None:
                report["excluded"][direction].append(name)
            else:
                report[direction].append({"layer": name, **info})

    own = model.binds.get(x, set()) | model.blocks.get(x, set())
    for jid, (source, name) in enumerate(model.inputs):
        if jid in own:
            continue
        definers = [y for y in range(len(ranks))
                    if jid in model.binds.get(y, ()) or jid in model.blocks.get(y, ())]
        lower = {y: z3.And(ranks[y] > 0, ranks[y] < ranks[x]) for y in definers}
        values = []
        for y in [*definers, None]:
            if y is None:
                predicate = z3.And(ranks[x] > 0, *[z3.Not(lower[z]) for z in definers])
                value = Value()
            else:
                predicate = z3.And(ranks[x] > 0, lower[y],
                                   *[z3.Or(z3.Not(lower[z]), ranks[z] < ranks[y]) for z in definers if z != y])
                owner = model.layer_names[y]
                if jid in model.blocks.get(y, ()):
                    value = Value(blocked_by=owner)
                else:
                    group = model.layout.active(owner)[source]
                    value = Value(owner=owner, activators=group["inputs"][name]["activators"])
            info = classify(predicate, observed["inherited"].get((source, name), {}).get(value))
            row = {"owner": value.owner, "blocked_by": value.blocked_by,
                   "summary": describe(value.activators), "activators": value.activators}
            if info is None:
                report["excluded"]["inherited"].append({"source": source, "input": name, **row})
            else:
                values.append({**row, **info})
        report["inherited"].append({"source": source, "input": name, "values": values})
    rows = report["below"] + report["above"] + [v for j in report["inherited"] for v in j["values"]]
    report["counts"] = {"proven": sum(r["status"] == "proven" for r in rows),
                        "possible": sum(r["status"] == "possible" for r in rows),
                        "excluded": sum(map(len, report["excluded"].values())),
                        "queries": queries, "unknown_queries": unknown}
    report["complete_for_model"] = report["counts"]["possible"] == 0
    return report


def format_report(report):
    lines = [report["layer"], report["scope"],
             "proven = witnessed in the model; possible = unresolved (not evidence of reachability).",
             f"Complete for model: {str(report['complete_for_model']).lower()}"]
    for direction in ("below", "above"):
        lines.append(f"\n{direction.capitalize()}:")
        lines.extend(f"  [{r['status']}] {r['layer']}" for r in report[direction])
    lines.append("\nInherited inputs (layers above this layer do not change its lower bindings):")
    for row in report["inherited"]:
        lines.append(f"  {row['source']}/{row['input']}")
        for v in row["values"]:
            owner = v["owner"] or (f"blocked by {v['blocked_by']}" if v["blocked_by"] else "unbound")
            lines.append(f"    [{v['status']}] {owner}" + (f": {v['summary']}" if v["summary"] else ""))
    c = report["counts"]
    lines.append(f"\n{c['proven']} witnessed; {c['possible']} unresolved; {c['excluded']} excluded by induction.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layer")
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--search", type=Path, help="matching --held search output, used only for concrete witnesses and candidate seeding")
    parser.add_argument("--timeout-ms", type=int, default=10000, help="per solver call; unknown remains unproven (default: 10000)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.timeout_ms < 1:
        parser.error("--timeout-ms must be positive")
    db = None
    try:
        layout = Layout(json.loads(args.layout.read_text(encoding="utf-8")))
        model = HeldModel(layout)
        if args.layer not in model.index:
            raise ValueError(f"Unknown layer: {args.layer}")
        if args.search:
            db = StackDB(args.search, layout)
        evidence = Evidence(model, db)
        candidates = candidates_from_states(model, evidence.seed_states())
        proof = InvariantProof(model, candidates, timeout_ms=args.timeout_ms,
                               progress=lambda msg: print(msg, file=sys.stderr, flush=True)).run()
        report = layer_report(proof, args.layer, evidence)
        report["layout"] = str(args.layout.resolve())
        report["search"] = str(args.search.resolve()) if args.search else None
        print(json.dumps(report, indent=2) if args.json else format_report(report))
        return 0
    except (ValueError, OSError) as exc:
        print(f"stackdb show: {exc}", file=sys.stderr)
        return 2
    finally:
        if db is not None:
            db.close()
