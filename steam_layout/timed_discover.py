"""Budgeted timed witness discovery; sampling never certifies an exclusion."""
import argparse
import json
import math
from pathlib import Path
import random
import sqlite3
import sys
import time

from .model import Layout
from .timed_facts import FactCatalogue, FactWitnesses
from .timed_model import TimedModel
from .timed_spec import canonical_control
from .timed_store import decode_state, encode_state


FORMAT = "timed-fact-witnesses-v1"


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def candidate_events(witnesses, state):
    """All physical changes plus useful deadline jumps and their predecessors.

    This event sample deliberately omits some intermediate time choices. Each
    chosen jump is replayed through TimedModel, which processes every crossed
    deadline. Sampling coverage therefore supports witnesses only.
    """
    quotient, model = witnesses.quotient, witnesses.model
    for control in quotient.controls:
        held = state.held - {control} if control in state.held else state.held | {control}
        if model._valid(held):
            yield {"release" if control in state.held else "press": list(control)}
        for value in quotient.analog_regions.get(control, ()):
            if dict(state.analog_values).get(control) == value:
                continue
            held = state.held | {control} if value > 0 else state.held - {control}
            if model._valid(held):
                yield {"analog": {"control": list(control), "value": str(value)}}
    deadlines = {a.deadline_ms for a in state.activations if a.deadline_ms is not None}
    if deadlines:
        jumps = {min(deadlines)} | {a.deadline_ms for a in state.activations
                                   if a.deadline_ms is not None and a.stage == "start"}
        jumps.update(value - 1 for value in tuple(jumps) if value > 1)
        for milliseconds in sorted(jumps):
            yield {"wait_ms": milliseconds}


def _weight(witnesses, state, event, reached_layers):
    model = witnesses.model
    operation, value = next(iter(event.items()))
    if operation == "wait_ms":
        entries = [model.spec.entries[a.entry_id] for a in state.activations
                   if a.deadline_ms is not None and a.deadline_ms <= value]
        weight = 3.0
    else:
        control = tuple(value["control"] if operation == "analog" else value)
        entries = [entry for raw in model.raw_controls
                   if control == canonical_control(raw)
                   for entry in model._binding(state, raw)
                   if (entry.kind == "release") == (operation == "release")]
        weight = 1.0
    additions = {target for entry in entries for op, target in entry.ops if op == "a"}
    return weight + 2 * bool(additions) + 10 * bool(additions - reached_layers)


def discover(witnesses, *, seconds=120, max_steps=None, seed=0, fanout=6,
             progress=None, checkpoint=None):
    """Explore short, branching walks and retain only concretely valid edges.

    ``max_steps`` limits evaluated input events, not runtime event depth.
    Restart nodes are drawn from retained witnesses, recent improvements, and
    arbitrary explored states. All command-order outcomes of a sampled event
    are retained even though the next walk follows one of them.
    """
    if seconds is not None and (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
                                or not math.isfinite(seconds) or seconds <= 0):
        raise ValueError("seconds must be finite and positive or None")
    if max_steps is not None and (type(max_steps) is not int or max_steps < 1):
        raise ValueError("max_steps must be a positive integer")
    if seconds is None and max_steps is None:
        raise ValueError("a discovery resource budget is required")
    if type(fanout) is not int or fanout < 1:
        raise ValueError("fanout must be a positive integer")
    progress = progress or (lambda message: None)
    rng = random.Random(seed)
    started = last_progress = time.monotonic()
    before = len(witnesses.facts)
    steps, walks, length = 0, 1, 0
    node = rng.choice(witnesses.roots)
    reached_layers = {layer for state in witnesses.node_states.values() for layer in state.stack}
    improvements = list(dict.fromkeys(witnesses.witness_nodes.values())) or list(witnesses.roots)
    while (max_steps is None or steps < max_steps) and (seconds is None or time.monotonic() - started < seconds):
        if length >= 40 or rng.random() < 0.04:
            restart_choice = rng.random()
            if restart_choice < 0.2:
                node = rng.choice(witnesses.roots)
            elif restart_choice < 0.75:
                node = rng.choice(improvements[-2000:])
            else:
                node = rng.randrange(len(witnesses.node_states))
            length, walks = 0, walks + 1
        state = witnesses.node_states[node]
        events = list(candidate_events(witnesses, state))
        weights = [_weight(witnesses, state, event, reached_layers) for event in events]
        choices = []
        for _ in range(min(fanout, len(events))):
            index = rng.choices(range(len(events)), weights=weights)[0]
            choices.append(events.pop(index))
            weights.pop(index)
        outcomes = []
        for event in choices:
            if max_steps is not None and steps >= max_steps:
                break
            if seconds is not None and time.monotonic() - started >= seconds:
                break
            following = witnesses.quotient.step(state, event)
            steps += 1
            # record() still validates the membership of every returned branch;
            # reuse this exact runtime result to avoid executing it twice.
            witnesses._last_edge, witnesses._last_following = (node, event), following
            for next_state in sorted(following, key=encode_state):
                unseen_stack = next_state.stack not in witnesses._fact_stacks
                unseen_layers = len(set(next_state.stack) - reached_layers)
                old_facts = len(witnesses.facts)
                old_nodes = len(witnesses.node_states)
                next_node = witnesses.record(node, next_state, event)
                gain = len(witnesses.facts) - old_facts
                reached_layers.update(next_state.stack)
                if gain:
                    improvements.append(next_node)
                score = (30 * gain + 100 * unseen_layers + 3 * unseen_stack +
                         0.2 * (len(witnesses.node_states) > old_nodes) +
                         0.05 * len(next_state.stack) + rng.random())
                outcomes.append((score, next_node))
        if outcomes:
            node = max(outcomes)[1]
        elif not events and not choices:
            break
        length += 1
        now = time.monotonic()
        if now - last_progress >= 10:
            progress(f"{steps} sampled events; {len(witnesses.facts)} witnessed facts; "
                     f"{len(reached_layers)}/{len(witnesses.catalogue.names)} layers; "
                     f"{len(witnesses.node_states)} retained states")
            if checkpoint:
                checkpoint(witnesses)
            last_progress = now
    for fact in witnesses.facts:
        witnesses.verify(fact)
    return {"complete_for_model": False, "method": "budgeted concrete witness sampling",
            "identity": witnesses.identity, "seed": seed, "sampled_events": steps,
            "walks": walks, "seconds": round(time.monotonic() - started, 3),
            "states": len(witnesses.node_states), "distinct_stacks": len(witnesses._fact_stacks),
            "witnessed_facts": len(witnesses.facts), "new_facts": len(witnesses.facts) - before,
            "total_alternatives": len(witnesses.catalogue.facts),
            "reached_layers": [witnesses.catalogue.names[x] for x in sorted(reached_layers)],
            "unreached_layers": [name for x, name in enumerate(witnesses.catalogue.names)
                                 if x not in reached_layers]}


def save_witnesses(witnesses, path):
    """Append a transactional checkpoint of the retained parent forest."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not tables:
            connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("CREATE TABLE nodes (id INTEGER PRIMARY KEY, state TEXT NOT NULL, parent INTEGER, event TEXT)")
            connection.executemany("INSERT INTO metadata VALUES (?, ?)",
                                   (("format", FORMAT), ("identity", _json(witnesses.identity))))
        else:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            if metadata.get("format") != FORMAT or metadata.get("identity") != _json(witnesses.identity):
                raise ValueError("witness archive format or model identity mismatch")
        last = connection.execute("SELECT max(id) FROM nodes").fetchone()[0]
        start = 0 if last is None else last + 1
        if start > len(witnesses.node_states):
            raise ValueError("cannot replace a longer witness archive with a shorter forest")
        if start:
            saved = connection.execute("SELECT state FROM nodes WHERE id = ?", (start - 1,)).fetchone()[0]
            if saved != encode_state(witnesses.node_states[start - 1]):
                raise ValueError("archive and witness forest have different node histories")
        connection.executemany("INSERT INTO nodes VALUES (?, ?, ?, ?)",
                               ((node, encode_state(witnesses.node_states[node]), witnesses._parents[node],
                                 None if witnesses._events[node] is None else _json(witnesses._events[node]))
                                for node in range(start, len(witnesses.node_states))))


def load_witnesses(model, catalogue, path):
    """Restore a saved forest, independently checking every stored edge."""
    witnesses = FactWitnesses(model, catalogue)
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if metadata.get("format") != FORMAT or metadata.get("identity") != _json(witnesses.identity):
            raise ValueError("witness archive format or model identity mismatch")
        for node, encoded, parent, event in connection.execute("SELECT id, state, parent, event FROM nodes ORDER BY id"):
            state = decode_state(encoded)
            if parent is None:
                found = witnesses._ids.get(state)
                if event is not None or found not in witnesses.roots:
                    raise ValueError("invalid archived root")
            else:
                if event is None:
                    raise ValueError("archived edge is missing its event")
                found = witnesses.record(parent, state, json.loads(event))
            if found != node:
                raise ValueError("invalid archived node numbering or duplicate state")
    return witnesses


def import_search(witnesses, path, *, progress=None):
    """Import concrete parent edges from a compatible timed-search database."""
    progress = progress or (lambda message: None)
    mapping = {}
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if metadata.get("identity") != _json(witnesses.identity):
            raise ValueError("timed-search identity does not match witness model")
        for sid, encoded, parent, event in connection.execute("SELECT id, state, parent, event FROM states ORDER BY id"):
            state = decode_state(encoded)
            if parent is None:
                node = witnesses._ids.get(state)
                if event is not None or node not in witnesses.roots:
                    raise ValueError("timed search contains an invalid root")
            else:
                if parent not in mapping or event is None:
                    raise ValueError("timed search contains a missing parent or event")
                node = witnesses.record(mapping[parent], state, json.loads(event))
            mapping[sid] = node
            if len(mapping) % 1000 == 0:
                progress(f"Replayed {len(mapping)} stored timed-search states; {len(witnesses.facts)} facts")
    return len(mapping)


def compact_archive(model, catalogue, source, destination, *, progress=None):
    """Replay only ancestors needed to witness all facts in an archive.

    Discovery checkpoints retain restart states as well as proof evidence.
    This produces a separate, smaller archive containing the same positive
    facts; neither file supplies an exhaustive-search certificate.
    """
    progress = progress or (lambda message: None)
    witnesses = FactWitnesses(model, catalogue)
    with sqlite3.connect(Path(source).resolve().as_uri() + "?mode=ro", uri=True) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if metadata.get("format") != FORMAT or metadata.get("identity") != _json(witnesses.identity):
            raise ValueError("witness archive format or model identity mismatch")
        claims, selected = set(), set()
        for node, encoded_stack in connection.execute(
                "SELECT min(id), json_extract(state, '$.stack') FROM nodes "
                "GROUP BY json_extract(state, '$.stack') ORDER BY min(id)"):
            found = catalogue.facts_of(tuple(json.loads(encoded_stack)))
            if found - claims:
                claims.update(found)
                selected.add(node)
        parents = dict(connection.execute("SELECT id, parent FROM nodes"))
        needed = set()
        for node in selected:
            while node is not None and node not in needed:
                needed.add(node)
                node = parents[node]
        needed.update(node for node, parent in parents.items() if parent is None)
        progress(f"Retaining {len(needed)}/{len(parents)} parent nodes for {len(claims)} facts")
        mapping = {}
        ordered = sorted(needed)
        for start in range(0, len(ordered), 500):
            chunk = ordered[start:start + 500]
            query = "SELECT id,state,parent,event FROM nodes WHERE id IN (" + ",".join("?" * len(chunk)) + ") ORDER BY id"
            for node, encoded, parent, event in connection.execute(query, chunk):
                state = decode_state(encoded)
                if parent is None:
                    found = witnesses._ids.get(state)
                    if event is not None or found not in witnesses.roots:
                        raise ValueError("invalid archived root")
                else:
                    found = witnesses.record(mapping[parent], state, json.loads(event))
                mapping[node] = found
            progress(f"Replayed {min(start + len(chunk), len(ordered))}/{len(ordered)} witness ancestors")
    for fact in claims:
        witnesses.verify(fact)
    if witnesses.facts != claims:
        raise ValueError("compacted archive does not preserve the original witnessed facts")
    save_witnesses(witnesses, destination)
    return witnesses


def _hint_events(witnesses, node, phase, control):
    """Turn one untimed hint into candidate concrete event sequences."""
    from .held_model import LATER, PRESS, RELEASE, SHIFT_TAP, TAP, TAP_HELD, TIMER
    state, model = witnesses.node_states[node], witnesses.model
    if phase in (LATER, TIMER):
        deadlines = {a.deadline_ms for a in state.activations if a.deadline_ms is not None and
                     (phase == TIMER or canonical_control((model.spec.entries[a.entry_id].source,
                                                            model.spec.entries[a.entry_id].input)) == control)}
        return [[{"wait_ms": value}] for value in sorted(deadlines)] or [[]]
    if control not in model.controls:
        return []
    if phase == RELEASE:
        if control not in state.held:
            return [[]]
        return [[{"release": list(control)}]] if model._valid(state.held - {control}) else []
    if phase not in (PRESS, TAP, TAP_HELD, SHIFT_TAP):
        return []
    if control in state.held:
        return [[]] if phase == PRESS else []
    if not model._valid(state.held | {control}):
        return []
    presses = [{"press": list(control)}]
    presses.extend({"analog": {"control": list(control), "value": str(value)}}
                   for value in witnesses.quotient.analog_regions.get(control, ()) if value > 0)
    if phase == PRESS:
        return [[event] for event in presses]
    release = {"release": list(control)}
    if phase != TAP_HELD:
        return [[event, release] for event in presses]
    delays = {entry.delay_start_ms for entry in model.spec.entries.values()
              if canonical_control((entry.source, entry.input)) == control and entry.delay_start_ms}
    repeats = {entry.repeat_ms for entry in model.spec.entries.values()
               if canonical_control((entry.source, entry.input)) == control and entry.repeat_ms}
    return [[event, {"wait_ms": value}, release] for event in presses
            for value in sorted(delays | repeats or {50})]


def discover_from_untimed(witnesses, database, *, seconds=120, max_traces=None,
                         beam=8, progress=None, checkpoint=None):
    """Use old search paths as suggestions, accepting only fresh timed replay.

    Old stacks and old reachability claims never become evidence. Every hinted
    physical event, delay choice, and command-order outcome is replayed through
    the timed runtime. A bounded beam follows branches closest to each hinted
    intermediate stack, so this remains incomplete witness discovery.
    """
    from .held_model import PHASE_NAMES
    progress = progress or (lambda message: None)
    if seconds <= 0 or not math.isfinite(seconds) or beam < 1:
        raise ValueError("positive finite seconds and beam are required")
    start = last_progress = time.monotonic()
    before = len(witnesses.facts)
    traces = events = attempted = 0
    ids = dict.fromkeys(gid for table in (database._under, database._below, database._top)
                        for gid in table.values())
    for gid in ids:
        if time.monotonic() - start >= seconds or (max_traces is not None and traces >= max_traces):
            break
        attempted += 1
        expected = tuple(witnesses.model.spec.index[title] for title in database.stack(gid))
        if not (witnesses.catalogue.facts_of(expected) - witnesses.facts):
            continue
        traces += 1
        current = set(witnesses.roots)
        for label, target in database.witness(gid)[1:]:
            if not current or time.monotonic() - start >= seconds:
                break
            phase_name, name = label.split(": ", 1)
            phase = PHASE_NAMES.index(phase_name)
            control = None if name == "Always On" else canonical_control(tuple(name.split("/", 1)))
            following = set()
            for parent in sorted(current):
                for plan in _hint_events(witnesses, parent, phase, control):
                    branches = {parent}
                    for event in plan:
                        next_branches = set()
                        for previous in sorted(branches):
                            old = witnesses.node_states[previous]
                            if 'release' in event and (tuple(event['release']) not in old.held or
                                    not witnesses.model._valid(old.held - {tuple(event['release'])})):
                                continue
                            outcomes = witnesses.quotient.step(old, event)
                            events += 1
                            witnesses._last_edge, witnesses._last_following = (previous, event), outcomes
                            next_branches.update(witnesses.record(previous, state, event)
                                                 for state in sorted(outcomes, key=encode_state))
                        branches = next_branches
                    following.update(branches)
            wanted = tuple(witnesses.model.spec.index[title] for title in target)
            def proximity(node):
                actual = witnesses.node_states[node].stack
                matched = sum(a == b for a, b in zip(actual, wanted))
                return (actual == wanted, matched, -len(set(actual) ^ set(wanted)), -node)
            current = set(sorted(following, key=proximity, reverse=True)[:beam])
        now = time.monotonic()
        if now - last_progress >= 10:
            progress(f"{traces} old trace hints replayed; {len(witnesses.facts)} timed facts; "
                     f"{len(witnesses.node_states)} states")
            if checkpoint:
                checkpoint(witnesses)
            last_progress = now
    for fact in witnesses.facts:
        witnesses.verify(fact)
    return {"complete_for_model": False, "method": "timed replay of untimed trace hints",
            "seconds": round(time.monotonic() - start, 3), "hint_candidates": attempted,
            "traces": traces, "events": events, "witnessed_facts": len(witnesses.facts),
            "new_facts": len(witnesses.facts) - before, "states": len(witnesses.node_states)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fanout", type=int, default=6)
    parser.add_argument("--ignore-hold-bindings", action="store_true")
    parser.add_argument("--default-repeat-ms", type=int)
    parser.add_argument("--import-search", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    progress = lambda text: print(text, file=sys.stderr, flush=True)
    try:
        model = TimedModel(Layout(json.loads(args.layout.read_text())),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        catalogue = FactCatalogue(model)
        witnesses = (load_witnesses(model, catalogue, args.archive) if args.archive.exists()
                     else FactWitnesses(model, catalogue))
        if args.import_search:
            import_search(witnesses, args.import_search, progress=progress)
        summary = discover(witnesses, seconds=args.seconds, max_steps=args.max_steps,
                           seed=args.seed, fanout=args.fanout, progress=progress,
                           checkpoint=lambda forest: save_witnesses(forest, args.archive))
        save_witnesses(witnesses, args.archive)
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"timed_discover: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
