"""Budgeted concrete search for requested stack facts; no negative conclusions.

The frontier and sampled time jumps are deliberately incomplete. A missing
witness is unresolved even if this frontier runs out. Every sampled event is
executed by TimedModel, retaining every command-order branch before pruning
future exploration. Saved evidence is independently replayed and compacted.
"""
import argparse
import heapq
import itertools
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

from .model import Layout
from .timed_discover import (candidate_events, compact_archive, load_witnesses,
                             save_witnesses)
from .timed_facts import Fact, FactCatalogue, FactWitnesses
from .timed_model import TimedModel
from .timed_spec import canonical_control
from .timed_store import encode_state


def parse_targets(catalogue, payload):
    """Read strict ``[kind, x, y, j]`` rows, returning canonical Fact objects.

    JSON may be a row list or an object with ``facts`` and optional text ``scope``.
    Indices must be JSON integers (not booleans); every alternative must exist
    in this model's catalogue. Duplicates retain their first position.
    """
    if (isinstance(payload, dict) and "facts" in payload and
            set(payload) <= {"facts", "scope"} and
            ("scope" not in payload or isinstance(payload["scope"], str))):
        payload = payload["facts"]
    if not isinstance(payload, list):
        raise ValueError("targets must be a fact-row list or a {facts: [...]} object")
    result = []
    for index, row in enumerate(payload):
        if (not isinstance(row, list) or len(row) != 4 or
                not isinstance(row[0], str) or any(type(v) is not int for v in row[1:])):
            raise ValueError(f"target {index}: expected [kind, integer x, integer y, integer j]")
        key = tuple(row)
        if key not in catalogue._lookup:
            raise ValueError(f"target {index}: fact is outside this model's catalogue: {row!r}")
        result.append(catalogue._lookup[key])
    return tuple(dict.fromkeys(result))


def _row(fact):
    return [fact.kind, fact.x, fact.y, fact.j]


def _positive(value, name, integer=False, optional=False):
    if value is None and optional:
        return
    valid = type(value) is int if integer else type(value) in (int, float)
    if not valid or value <= 0 or (type(value) is float and not math.isfinite(value)):
        raise ValueError(f"{name} must be a finite positive {'integer' if integer else 'number'}")


def _score(fact, state, distance):
    stack = state.stack
    if fact.holds(stack):
        return 10000
    proximity = sum(1 / (d + 1) for layer, d in distance.items() if layer in stack)
    if fact.x not in stack:
        return (20 if fact.y in stack or fact.y < 0 else 0) + proximity
    lower = stack[:stack.index(fact.x)]
    if fact.kind == "below":
        return 10 + proximity
    if fact.y < 0:
        blockers = sum(layer in fact.definers for layer in lower)
    elif fact.y in lower:
        blockers = sum(layer in fact.definers for layer in lower[lower.index(fact.y) + 1:])
    else:
        return 15 if fact.y in stack else 10
    return 100 - min(70, blockers * 10) + proximity / 10


def seek(witnesses, targets, *, seconds=None, max_events=None,
         per_target_events=2000, per_target_seconds=None, max_frontier=1000,
         seed_limit=40, progress=None):
    """Try requested predicates using a finite best-first concrete search.

    At least one total time/event budget is mandatory. Time is checked between
    event evaluations, so a single runtime batch or final verification can
    outlast it. Event limits count evaluated events, not returned branches.
    Equivalent inheritance predicates share a search. Existing witness nodes
    seed each target; ancestors remain valid even when frontier nodes are
    discarded. This function never returns an exclusion or completeness claim.
    """
    _positive(seconds, "seconds", optional=True)
    _positive(max_events, "max_events", integer=True, optional=True)
    _positive(per_target_seconds, "per_target_seconds", optional=True)
    for name, value in (("per_target_events", per_target_events),
                        ("max_frontier", max_frontier), ("seed_limit", seed_limit)):
        _positive(value, name, integer=True)
    if seconds is None and max_events is None:
        raise ValueError("a total seconds or max_events budget is required")
    raw = []
    for fact in targets:
        if not isinstance(fact, Fact):
            raise ValueError("seek targets must be Fact objects")
        raw.append(_row(fact))
    targets = parse_targets(witnesses.catalogue, raw)
    groups = {}
    for fact in targets:
        key = (fact.kind, fact.x, fact.y,
               tuple(sorted(fact.definers)) if fact.kind == "inherit" else ())
        groups.setdefault(key, []).append(fact)
    entries = tuple(witnesses.model.spec.entries.values())
    removers = {}
    for entry in entries:
        control = canonical_control((entry.source, entry.input))
        for op, layer in entry.ops:
            if op == "r":
                removers.setdefault(layer, set()).add(control)
    before = len(witnesses.facts)
    started = time.monotonic()
    sampled = 0
    attempts = {}
    progress = progress or (lambda message: None)

    def total_remaining():
        return ((seconds is None or time.monotonic() - started < seconds) and
                (max_events is None or sampled < max_events))

    for group in groups.values():
        if all(fact in witnesses.facts for fact in group):
            continue
        if not total_remaining():
            break
        fact = group[0]
        begin, events = time.monotonic(), 0
        distance = {fact.x: 0}
        changed = True
        while changed:
            changed = False
            for entry in entries:
                candidates = [distance[layer] + 1 for op, layer in entry.ops
                              if op == "a" and layer in distance]
                if (type(entry.owner) is int and candidates and
                        min(candidates) < distance.get(entry.owner, math.inf)):
                    distance[entry.owner] = min(candidates)
                    changed = True
        priorities = {}
        for entry in entries:
            values = [distance[layer] for op, layer in entry.ops if op == "a" and layer in distance]
            if values:
                control = canonical_control((entry.source, entry.input))
                priorities[control] = min(priorities.get(control, math.inf), min(values))
        score = lambda state: _score(fact, state, distance)
        pool = heapq.nlargest(seed_limit, witnesses.node_states,
                              key=lambda node: (score(witnesses.node_states[node]),
                                                -len(witnesses.node_states[node].held), -node))
        # Roots allow building a new order when all good-looking seeds carry X
        # too early. Prefer Y-present states but never require Y to remain held.
        pool.extend(witnesses.roots)
        counter = itertools.count()
        queue, visited = [], set()
        for node in pool:
            state = witnesses.node_states[node]
            if node in visited:
                continue
            visited.add(node)
            heapq.heappush(queue, (-score(state), 0, next(counter), node))
        while (queue and fact not in witnesses.facts and total_remaining() and
               events < per_target_events and
               (per_target_seconds is None or time.monotonic() - begin < per_target_seconds)):
            _, depth, _, node = heapq.heappop(queue)
            state = witnesses.node_states[node]
            lower = state.stack[:state.stack.index(fact.x)] if fact.x in state.stack else ()
            if fact.y in lower:
                lower = lower[lower.index(fact.y) + 1:]
            blockers = set(lower) & set(fact.definers or ())
            helpful = set().union(*(removers.get(layer, set()) for layer in blockers))

            def priority(event):
                operation, value = next(iter(event.items()))
                if operation == "wait_ms":
                    return -2
                control = tuple(value["control"] if operation == "analog" else value)
                return -1 if control in helpful else priorities.get(control, math.inf)

            for event in sorted(candidate_events(witnesses, state), key=priority):
                if (not total_remaining() or events >= per_target_events or
                        (per_target_seconds is not None and time.monotonic() - begin >= per_target_seconds)):
                    break
                following = witnesses.quotient.step(state, event)
                sampled += 1
                events += 1
                witnesses._last_edge, witnesses._last_following = (node, event), following
                # Do not stop halfway through a frozen batch: all outcomes of
                # this selected event are retained, including after a success.
                for after in sorted(following, key=encode_state):
                    successor = witnesses.record(node, after, event)
                    if successor not in visited:
                        visited.add(successor)
                        heapq.heappush(queue, (-score(after), depth + 1, next(counter), successor))
                if fact in witnesses.facts:
                    break
            if len(queue) > max_frontier:
                queue = heapq.nsmallest(max_frontier, queue)
                heapq.heapify(queue)
        for member in group:
            attempts[member] = events
        progress(f"{len(attempts)}/{len(targets)} targets attempted; "
                 f"{sampled} events; {len(witnesses.facts)} witnessed facts")
    for fact in witnesses.facts:
        witnesses.verify(fact)
    return {"method": "budgeted concrete target search", "complete_for_model": False,
            "identity": witnesses.identity, "sampled_events": sampled,
            "seconds": round(time.monotonic() - started, 3),
            "witnessed_facts": len(witnesses.facts), "new_facts": len(witnesses.facts) - before,
            "states": len(witnesses.node_states),
            "targets": [{"fact": _row(fact), "status": "witnessed" if fact in witnesses.facts else "unresolved",
                         "attempted": fact in attempts, "group_sampled_events": attempts.get(fact, 0)}
                        for fact in targets]}


def save_compact(witnesses, destination):
    """Atomically publish a compact, replay-verified archive of positive facts."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".timed-seek-", dir=destination.parent) as directory:
        raw, compact = (Path(directory) / name for name in ("raw.sqlite", "compact.sqlite"))
        save_witnesses(witnesses, raw)
        result = compact_archive(witnesses.model, witnesses.catalogue, raw, compact)
        os.replace(compact, destination)
    return result


def _aliases(first, second):
    """Recognize normalized paths, symbolic links, and existing hard links."""
    return (first.resolve() == second.resolve() or
            (first.exists() and second.exists() and first.samefile(second)))


def _validate_paths(args, summary):
    for name in ("layout", "targets"):
        if _aliases(args.output, getattr(args, name)):
            raise ValueError(f"output must not alias {name}")
    for name in ("layout", "targets", "input_archive", "output"):
        source = getattr(args, name)
        if source is not None and _aliases(summary, source):
            raise ValueError(f"summary must not alias {name.replace('_', '-')}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("targets", type=Path, help="JSON fact rows or {facts: [...]} object")
    parser.add_argument("output", type=Path, help="compact positive-witness SQLite archive")
    parser.add_argument("--input-archive", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--max-events", type=int)
    parser.add_argument("--per-target-events", type=int, default=2000)
    parser.add_argument("--per-target-seconds", type=float)
    parser.add_argument("--max-frontier", type=int, default=1000)
    parser.add_argument("--seed-limit", type=int, default=40)
    parser.add_argument("--ignore-hold-bindings", action="store_true")
    parser.add_argument("--default-repeat-ms", type=int)
    args = parser.parse_args(argv)
    try:
        summary = args.summary or Path(str(args.output) + ".summary.json")
        _validate_paths(args, summary)
        model = TimedModel(Layout(json.loads(args.layout.read_text())),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        catalogue = FactCatalogue(model)
        targets = parse_targets(catalogue, json.loads(args.targets.read_text()))
        witnesses = (load_witnesses(model, catalogue, args.input_archive) if args.input_archive
                     else FactWitnesses(model, catalogue))
        report = seek(witnesses, targets, seconds=args.seconds, max_events=args.max_events,
                      per_target_events=args.per_target_events,
                      per_target_seconds=args.per_target_seconds, max_frontier=args.max_frontier,
                      seed_limit=args.seed_limit, progress=lambda message: print(message, file=sys.stderr))
        compact = save_compact(witnesses, args.output)
        report.update(archive=str(args.output), archive_states=len(compact.node_states))
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.error(str(error))
    print(json.dumps({key: report[key] for key in ("complete_for_model", "sampled_events",
                                                 "witnessed_facts", "new_facts", "archive_states")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
