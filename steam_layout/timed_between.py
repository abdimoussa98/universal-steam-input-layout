"""Suggest conditional blockers between witnessed ordered layer pairs.

Every result is an unproved hypothesis. Replayed samples suggest a small
family of raw-input definers between an upper layer and a proposed inherited
owner; only subsequent induction can establish the corresponding exclusion.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from .model import Layout
from .timed_discover import load_witnesses
from .timed_facts import Fact, FactCatalogue, FactWitnesses
from .timed_mine import _Budget, _aliases, _bits, _minimal_prefixes, _validate_budgets
from .timed_model import TimedModel
from .timed_predicates import RequiresBetweenAny
from .timed_seek import parse_targets


def _first_cover(constraints, max_members, budget):
    """Find one minimum-cardinality sampled hitting set within explicit bounds."""
    constraints = _minimal_prefixes(constraints)
    if not constraints or 0 in constraints:
        return None
    for limit in range(1, max_members + 1):
        failed = set()

        def visit(remaining, left):
            if not budget.consume():
                return None
            if not remaining:
                return 0
            if not left or (remaining, left) in failed:
                return None
            first = min(remaining, key=lambda mask: (bin(mask).count("1"), mask))
            frequency = Counter(bit for mask in remaining for bit in _bits(mask))
            for bit in sorted(_bits(first), key=lambda value: (-frequency[value], value)):
                rest = tuple(mask for mask in remaining if not mask & bit)
                found = visit(rest, left - 1)
                if found is not None:
                    return bit | found
                if budget.exhausted:
                    return None
            failed.add((remaining, left))
            return None

        found = visit(constraints, limit)
        if found is not None or budget.exhausted:
            return found
    return None


@dataclass(frozen=True)
class BetweenHypotheses:
    candidates: tuple
    identity: dict
    targets: tuple
    sampled_states: int
    distinct_stacks: int
    max_members: int
    max_search_nodes: int
    seconds_budget: object
    search_nodes: int
    budget_exhausted: object

    def to_data(self):
        return {
            "format": "timed-between-hypotheses-v1", "validation": "unvalidated",
            "scope": "Sample-derived hypotheses only; no invariants or exclusions are established.",
            "complete_for_model": False, "identity": self.identity,
            "candidates": [candidate.to_data() for candidate in self.candidates],
            "targets": list(self.targets), "target_status_counts": dict(Counter(
                target["status"] for target in self.targets)),
            "sampled_states": self.sampled_states, "distinct_stacks": self.distinct_stacks,
            "max_members": self.max_members, "max_search_nodes": self.max_search_nodes,
            "seconds_budget": self.seconds_budget, "search_nodes": self.search_nodes,
            "budget_exhausted": self.budget_exhausted,
        }


def mine_between_families(witnesses, targets, *, max_members=5,
                          max_search_nodes=1000000, seconds=None):
    """Propose one small between family per distinct unwitnessed formula.

    Only inheritance targets with an observed ordered pair are considered.
    Members are canonical raw-input definers. Each proposed family intersects
    every sampled segment between the target and its proposed owner. The
    search bounds affect suggestions only, never the model or a proof claim.
    Equivalent target formulas share work; duplicate hypotheses are merged.
    """
    if not isinstance(witnesses, FactWitnesses):
        raise ValueError("mining requires replayed FactWitnesses")
    _validate_budgets(max_members, max_search_nodes, seconds)
    rows = []
    for fact in targets:
        if not isinstance(fact, Fact):
            raise ValueError("mining targets must be catalogue Facts")
        rows.append([fact.kind, fact.x, fact.y, fact.j])
    targets = parse_targets(witnesses.catalogue, rows)
    stacks = {state.stack for state in witnesses.node_states.values()}
    pairs = {(fact.x, fact.y) for fact in targets if fact.kind == "inherit" and fact.y >= 0}
    segments = {pair: set() for pair in pairs}
    for stack in stacks:
        for lower, y in enumerate(stack):
            between = 0
            for x in stack[lower + 1:]:
                if (x, y) in segments:
                    segments[x, y].add(between)
                between |= 1 << x
    budget = _Budget(max_search_nodes, seconds)
    candidates, details, cache = set(), [], {}
    for fact in targets:
        row = {"fact": [fact.kind, fact.x, fact.y, fact.j]}
        if fact in witnesses.facts:
            row["status"] = "already_witnessed"
        elif fact.kind != "inherit" or fact.y < 0:
            row["status"] = "outside_between_scope"
        elif not segments[fact.x, fact.y]:
            row["status"] = "ordered_pair_unwitnessed"
        else:
            key = (fact.x, fact.y, tuple(sorted(fact.definers)))
            if key not in cache:
                definers = sum(1 << layer for layer in fact.definers)
                constraints = _minimal_prefixes(mask & definers for mask in segments[fact.x, fact.y])
                cover = _first_cover(constraints, max_members, budget)
                cache[key] = (cover, budget.exhausted)
            cover, exhausted = cache[key]
            row["observed_pair_segments"] = len(segments[fact.x, fact.y])
            if cover is None:
                row["status"] = "budget_exhausted" if exhausted else "no_cover_within_member_bound"
            else:
                members = tuple(bit.bit_length() - 1 for bit in _bits(cover))
                candidate = RequiresBetweenAny(fact.x, fact.y, members)
                candidates.add(candidate)
                row.update(status="hypothesis_proposed", hypothesis=candidate.to_data())
        details.append(row)
    return BetweenHypotheses(tuple(sorted(candidates)), witnesses.identity, tuple(details),
                             len(witnesses.node_states), len(stacks), max_members,
                             max_search_nodes, seconds, budget.nodes, budget.exhausted)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("archive", type=Path, help="replayed positive witness archive")
    parser.add_argument("targets", type=Path, help="strict [kind,x,y,j] target rows JSON")
    parser.add_argument("output", type=Path, help="unvalidated typed hypotheses JSON")
    parser.add_argument("--max-members", type=int, default=5)
    parser.add_argument("--max-search-nodes", type=int, default=1000000)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--ignore-hold-bindings", action="store_true")
    parser.add_argument("--default-repeat-ms", type=int)
    args = parser.parse_args(argv)
    temporary = None
    try:
        for name in ("layout", "archive", "targets"):
            if _aliases(args.output, getattr(args, name)):
                raise ValueError(f"output must not alias {name}")
        _validate_budgets(args.max_members, args.max_search_nodes, args.seconds)
        model = TimedModel(Layout(json.loads(args.layout.read_text(encoding="utf-8"))),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        catalogue = FactCatalogue(model)
        targets = parse_targets(catalogue, json.loads(args.targets.read_text(encoding="utf-8")))
        witnesses = load_witnesses(model, catalogue, args.archive)
        result = mine_between_families(witnesses, targets, max_members=args.max_members,
                                      max_search_nodes=args.max_search_nodes, seconds=args.seconds)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", prefix=".timed-between-",
                                         dir=args.output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(result.to_data(), handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        os.replace(temporary, args.output)
        temporary = None
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"validation": "unvalidated", "candidates": len(result.candidates),
                      "target_status_counts": result.to_data()["target_status_counts"],
                      "budget_exhausted": result.budget_exhausted}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
