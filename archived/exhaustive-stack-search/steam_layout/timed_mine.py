"""Propose lower-layer family hypotheses from replayed timed witnesses.

Covering every sampled stack is not induction. These candidates can be false
on an unseen timed trace; this module establishes no invariant or exclusion.
Its typed candidates may be passed to timed_refine for independent proof work.
"""
import argparse
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

from .model import Layout
from .timed_discover import load_witnesses
from .timed_facts import FactCatalogue, FactWitnesses
from .timed_model import TimedModel
from .timed_predicates import RequiresBelowAny


@dataclass(frozen=True)
class FamilyHypotheses:
    """Unvalidated proposals plus the bounds of sample-only enumeration."""
    candidates: tuple
    identity: dict
    max_members: int
    max_search_nodes: int
    search_nodes: int
    sampled_states: int
    distinct_stacks: int
    layers: tuple
    budget_exhausted: object = None
    seconds_budget: object = None

    def to_data(self):
        return {
            "format": "timed-below-family-hypotheses-v1",
            "validation": "unvalidated",
            "scope": "Sample-derived hypotheses only; no invariants or exclusions are established.",
            "complete_for_model": False,
            "identity": self.identity,
            "max_members": self.max_members,
            "max_search_nodes": self.max_search_nodes,
            "seconds_budget": self.seconds_budget,
            "search_nodes": self.search_nodes,
            "sampled_states": self.sampled_states,
            "distinct_stacks": self.distinct_stacks,
            "enumeration_complete_for_samples": all(layer["enumerated"] for layer in self.layers),
            "budget_exhausted": self.budget_exhausted,
            "candidates": [candidate.to_data() for candidate in self.candidates],
            "layers": list(self.layers),
        }


class _Budget:
    def __init__(self, max_nodes, seconds):
        self.max_nodes, self.nodes, self.exhausted = max_nodes, 0, None
        self.started, self.seconds = time.monotonic(), seconds

    def consume(self):
        if self.nodes >= self.max_nodes:
            self.exhausted = "max_search_nodes"
            return False
        if self.seconds is not None and time.monotonic() - self.started >= self.seconds:
            self.exhausted = "seconds"
            return False
        self.nodes += 1
        return True


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit
        mask -= bit


def _minimal_prefixes(masks):
    """A superset prefix adds no constraint to the hitting-set problem."""
    result = []
    for mask in sorted(set(masks), key=lambda value: (bin(value).count("1"), value)):
        if not any(existing & mask == existing for existing in result):
            result.append(mask)
    return tuple(result)


def _hitting_sets(prefixes, max_members, budget):
    """Enumerate inclusion-minimal bounded covers without trying every tuple.

    Branch on members of an uncovered prefix. A solution is checked for
    minimality against every prefix before publishing, so interruption cannot
    cause a nonminimal provisional cover to escape.
    """
    if not prefixes or 0 in prefixes:
        return (), True
    pending, visited, solutions = [0], set(), set()
    complete = True
    while pending:
        chosen = pending.pop()
        if chosen in visited:
            continue
        if not budget.consume():
            complete = False
            break
        visited.add(chosen)
        if any(solution & chosen == solution for solution in solutions):
            continue
        remaining = tuple(prefix for prefix in prefixes if not prefix & chosen)
        if not remaining:
            if all(any(not prefix & (chosen ^ bit) for prefix in prefixes)
                   for bit in _bits(chosen)):
                solutions.add(chosen)
            continue
        if bin(chosen).count("1") >= max_members:
            continue
        first = min(remaining, key=lambda value: (bin(value).count("1"), value))
        pending.extend(chosen | bit for bit in reversed(tuple(_bits(first))))
    return tuple(sorted(solutions, key=lambda value: (bin(value).count("1"), value))), complete


def _validate_budgets(max_members, max_search_nodes, seconds):
    for name, value in (("max_members", max_members), ("max_search_nodes", max_search_nodes)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if seconds is not None and (type(seconds) not in (int, float) or seconds <= 0 or
                                (type(seconds) is float and not math.isfinite(seconds))):
        raise ValueError("seconds must be finite and positive or None")


def mine_below_families(witnesses, *, max_members=3, max_search_nodes=1000000,
                       seconds=None, progress=None):
    """Suggest minimal RequiresBelowAny predicates covering sampled stacks.

    ``witnesses`` must be a FactWitnesses forest, whose nodes were checked when
    recorded or replayed on archive loading. No unchecked stack list is
    accepted. Base, the target itself, and unobserved targets are excluded.
    Duplicate prefixes and prefixes containing stricter sampled prefixes are
    removed before enumeration. Search-node limits are global and exact;
    optional time limits are checked between search nodes. Final proposals are
    deterministically ordered, but a time-limited subset may vary between runs.
    """
    if not isinstance(witnesses, FactWitnesses):
        raise ValueError("mining requires replayed FactWitnesses")
    _validate_budgets(max_members, max_search_nodes, seconds)
    progress = progress or (lambda message: None)
    budget = _Budget(max_search_nodes, seconds)
    stacks = {state.stack for state in witnesses.node_states.values()}
    prefixes = [set() for _ in witnesses.catalogue.names]
    for stack in stacks:
        lower = 0
        for layer in stack:
            if layer == 0:
                continue
            prefixes[layer].add(lower)
            lower |= 1 << layer
    candidates, details = [], []
    for target in range(1, len(prefixes)):
        minimal = _minimal_prefixes(prefixes[target])
        covers, complete = _hitting_sets(minimal, max_members, budget)
        for cover in covers:
            members = tuple(bit.bit_length() - 1 for bit in _bits(cover))
            candidates.append(RequiresBelowAny(target, members))
        details.append({"x": target, "observed_prefixes": len(prefixes[target]),
                        "minimal_prefixes": len(minimal), "candidate_count": len(covers),
                        "enumerated": complete})
        progress(f"Layer {target}: {len(prefixes[target])} sampled prefixes; "
                 f"{len(covers)} unvalidated family hypotheses")
    return FamilyHypotheses(tuple(sorted(candidates)), witnesses.identity, max_members,
                            max_search_nodes, budget.nodes, len(witnesses.node_states),
                            len(stacks), tuple(details), budget.exhausted, seconds)


def _aliases(first, second):
    return (first.resolve() == second.resolve() or
            (first.exists() and second.exists() and first.samefile(second)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("archive", type=Path, help="replayed positive-witness SQLite archive")
    parser.add_argument("output", type=Path, help="unvalidated typed family hypotheses JSON")
    parser.add_argument("--max-members", type=int, default=3)
    parser.add_argument("--max-search-nodes", type=int, default=1000000)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--ignore-hold-bindings", action="store_true")
    parser.add_argument("--default-repeat-ms", type=int)
    args = parser.parse_args(argv)
    temporary = None
    try:
        for name in ("layout", "archive"):
            if _aliases(args.output, getattr(args, name)):
                raise ValueError(f"output must not alias {name}")
        _validate_budgets(args.max_members, args.max_search_nodes, args.seconds)
        model = TimedModel(Layout(json.loads(args.layout.read_text())),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        catalogue = FactCatalogue(model)
        witnesses = load_witnesses(model, catalogue, args.archive)
        result = mine_below_families(witnesses, max_members=args.max_members,
                                    max_search_nodes=args.max_search_nodes, seconds=args.seconds,
                                    progress=lambda message: print(message, file=sys.stderr))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".timed-mine-",
                                         dir=args.output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result.to_data(), stream, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, args.output)
        temporary = None
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"validation": "unvalidated", "candidates": len(result.candidates),
                      "search_nodes": result.search_nodes,
                      "enumeration_complete_for_samples": result.to_data()["enumeration_complete_for_samples"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
