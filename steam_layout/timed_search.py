"""Finite, resumable reachability search for the integer-millisecond runtime.

Clocks retain every possible remaining millisecond. Only absolute time and
analog values indistinguishable by every parsed threshold are quotiented out.
Resource stops leave an open frontier; they never establish an exclusion.
"""
import argparse
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import time

from .model import Layout
from .timed_model import TimedModel
from .timed_spec import canonical_control
from .timed_store import TimedStore, encode_state
from .timed_trace import parse_trace


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class TimedQuotient:
    """Exact finite state representation of TimedModel's discrete contract.

    The graph has an input edge for each valid physical event and a 1 ms edge
    whenever a timer is pending. A wait of arbitrary integer length decomposes
    into those edges. No event-count or elapsed-time bound is imposed.
    """

    def __init__(self, model):
        self.model = model
        thresholds = {}
        for entry in model.spec.entries.values():
            if entry.kind != "Soft_Press":
                continue
            control = canonical_control((entry.source, entry.input))
            bounds = thresholds.setdefault(control, {Decimal(0), Decimal(32767)})
            if entry.threshold is not None and 0 <= entry.threshold <= 32767:
                bounds.add(entry.threshold)
        self.analog_regions = {c: tuple(sorted(bounds)) for c, bounds in sorted(thresholds.items())
                               if c in model.controls}
        self.controls = tuple(sorted(model.controls))
        implementation = hashlib.sha256()
        for name in ("timed_search.py", "timed_store.py"):
            implementation.update(name.encode("utf-8"))
            implementation.update(Path(__file__).with_name(name).read_bytes())
        self.identity = {
            "model_family": "TimedModel",
            "quotient": "relative-clocks-analog-regions-v1",
            "implementation_sha256": implementation.hexdigest(),
            "layout_sha256": hashlib.sha256(_json(model.layout.cm).encode("utf-8")).hexdigest(),
            "runtime": model.semantics,
            "clock_step_ms": 1,
            "analog_regions": [{"control": list(c), "representatives": [str(v) for v in values]}
                               for c, values in self.analog_regions.items()],
        }

    def normalize(self, state):
        analog = []
        for control, value in state.analog_values:
            control = canonical_control(control)
            if control not in self.analog_regions:
                # Without any Soft Press on this physical control, only held
                # membership matters, which the state retains separately.
                continue
            if not value.is_finite() or not 0 <= value <= 32767:
                raise ValueError("invalid analog sample in timed state")
            representative = next(bound for bound in self.analog_regions[control] if value <= bound)
            analog.append((control, representative))
        activations = tuple(replace(a, deadline_ms=None if a.deadline_ms is None else
                                    a.deadline_ms - state.now_ms) for a in state.activations)
        if any(a.deadline_ms is not None and a.deadline_ms <= 0 for a in activations):
            raise ValueError("timed search requires a settled state with future deadlines")
        return replace(state, now_ms=0, analog_values=tuple(sorted(analog)), activations=activations)

    def initial(self):
        return frozenset(self.normalize(state) for state in self.model.start())

    def step(self, state, event):
        """Apply a trace event and canonicalize every resulting branch."""
        event = parse_trace([event])[0]
        operation, value = next(iter(event.items()))
        if operation == "wait_ms":
            following = self.model.wait(state, value)
        elif operation == "analog":
            following = self.model.analog(state, tuple(value["control"]), value["value"])
        else:
            following = getattr(self.model, operation)(state, tuple(value))
        return frozenset(self.normalize(result) for result in following)

    def successors(self, state):
        state = self.normalize(state)
        for control in self.controls:
            held = state.held - {control} if control in state.held else state.held | {control}
            if self.model._valid(held):
                operation = "release" if control in state.held else "press"
                event = {operation: list(control)}
                # Runtime errors are deliberately not swallowed as invalid
                # physical events: a bad command cycle must stop the search.
                for following in sorted(self.step(state, event), key=encode_state):
                    yield following, event
            for value in self.analog_regions.get(control, ()):
                held = state.held | {control} if value > 0 else state.held - {control}
                if not self.model._valid(held):
                    continue
                if dict(state.analog_values).get(control) == value:
                    continue
                event = {"analog": {"control": list(control), "value": str(value)}}
                for following in sorted(self.step(state, event), key=encode_state):
                    yield following, event
        if any(a.deadline_ms is not None for a in state.activations):
            event = {"wait_ms": 1}
            for following in sorted(self.step(state, event), key=encode_state):
                yield following, event


def run_search(quotient, store, *, max_states=None, max_seconds=None, progress=None):
    """Expand a persistent frontier without an event/depth cap."""
    if _json(store.identity) != _json(quotient.identity):
        raise ValueError("search store belongs to a different timed model or quotient")
    if max_states is not None and (type(max_states) is not int or max_states < 1):
        raise ValueError("max_states must be a positive integer")
    if max_seconds is not None and (not isinstance(max_seconds, (int, float)) or
                                    isinstance(max_seconds, bool) or max_seconds <= 0 or
                                    not Decimal(str(max_seconds)).is_finite()):
        raise ValueError("max_seconds must be a finite positive number")
    progress = progress or (lambda message: None)
    started = time.monotonic()
    if not store.seeded:
        roots = sorted(quotient.initial(), key=encode_state)
        if max_states is not None and len(roots) > max_states:
            return {"complete": False, "stopped": "max_states", "states": 0,
                    "expanded": 0, "frontier": 0, "seconds": 0}
        store.seed(roots)
    stop = None
    while True:
        pending = store.pending()
        if pending is None:
            break
        if max_seconds is not None and time.monotonic() - started >= max_seconds:
            stop = "max_seconds"
            break
        sid, state = pending
        if not store.commit_expansion(sid, quotient.successors(state), max_states=max_states):
            stop = "max_states"
            break
        if store.expanded_count % 100 == 0:
            progress(f"{store.expanded_count} expanded; {store.count} states; "
                     f"{store.count - store.expanded_count} pending")
    return {"complete": store.complete, "stopped": stop, "states": store.count,
            "expanded": store.expanded_count, "frontier": store.count - store.expanded_count,
            "seconds": round(time.monotonic() - started, 3)}


class WitnessVerifier:
    """Replay each retained parent edge; cache only independently checked IDs."""

    def __init__(self, quotient, store):
        if _json(store.identity) != _json(quotient.identity):
            raise ValueError("witness model and search identity do not match")
        self.quotient, self.store = quotient, store
        self.roots = quotient.initial()
        self.verified = set()

    def __call__(self, sid):
        previous = None
        for current_id, state, event in self.store.path(sid):
            if current_id not in self.verified:
                if event is None:
                    if state not in self.roots:
                        raise ValueError(f"state {current_id}: invalid initial-state witness")
                elif previous is None or state not in self.quotient.step(previous, event):
                    raise ValueError(f"state {current_id}: witness fails timed replay")
                self.verified.add(current_id)
            previous = state
        return True


def verify_closure(quotient, store, progress=None):
    """Recompute reachability witnesses and closure independently of flags.

    A verified finite set contains all initial states and every successor of
    each member. These are the initialization and inductive-closure obligations
    for an exact reachable-state certificate; no untimed solver facts are used.
    """
    if _json(store.identity) != _json(quotient.identity):
        raise ValueError("closure certificate model identity does not match")
    if not store.complete:
        raise ValueError("open frontier: a partial search cannot certify exclusions")
    progress = progress or (lambda message: None)
    states = {state: sid for sid, state in store.iter_states()}
    if not quotient.initial() <= states.keys():
        raise ValueError("closure certificate is missing an initial state")
    verifier = WitnessVerifier(quotient, store)
    edges = 0
    for number, (state, sid) in enumerate(states.items(), 1):
        verifier(sid)
        for following, _ in quotient.successors(state):
            edges += 1
            if following not in states:
                raise ValueError(f"state {sid}: graph is not closed under timed transitions")
        if number % 100 == 0:
            progress(f"Verified closure of {number}/{len(states)} states")
    return {"verified": True, "states": len(states), "edges": edges,
            "scope": "initialization, reachability and closure under the versioned timed model"}


def compact_trace(events):
    result = []
    for event in events:
        if "wait_ms" in event and result and "wait_ms" in result[-1]:
            result[-1] = {"wait_ms": result[-1]["wait_ms"] + event["wait_ms"]}
        else:
            result.append(event)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "show", "witness", "check"):
        command = sub.add_parser(name)
        command.add_argument("layout", type=Path)
        command.add_argument("database", type=Path)
        command.add_argument("--ignore-hold-bindings", action="store_true")
        command.add_argument("--default-repeat-ms", type=int)
        if name == "run":
            command.add_argument("--resume", action="store_true")
            command.add_argument("--max-states", type=int, help="resource budget, leaves search incomplete")
            command.add_argument("--max-seconds", type=float, help="checked between complete state expansions")
        elif name == "show":
            command.add_argument("layer")
            command.add_argument("--json", action="store_true")
        elif name == "witness":
            command.add_argument("state_id", type=int)
    args = parser.parse_args(argv)
    progress = lambda message: print(message, file=sys.stderr, flush=True)
    try:
        model = TimedModel(Layout(json.loads(args.layout.read_text(encoding="utf-8"))),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        quotient = TimedQuotient(model)
        resume = args.command != "run" or args.resume
        with TimedStore(args.database, model, quotient.identity, resume=resume) as store:
            if args.command == "run":
                result = run_search(quotient, store, max_states=args.max_states,
                                    max_seconds=args.max_seconds, progress=progress)
                result["model"] = quotient.identity
            elif args.command == "check":
                result = verify_closure(quotient, store, progress)
            elif args.command == "witness":
                WitnessVerifier(quotient, store)(args.state_id)
                result = {"state_id": args.state_id, "events": compact_trace(store.trace(args.state_id)),
                          "state": model.snapshot(store.get(args.state_id)),
                          "clock_origin": "relative; reconstruct elapsed time from events",
                          "verified": True, "model": quotient.identity}
            else:
                from .timed_report import timed_layer_report, format_timed_report
                result = timed_layer_report(model, store, args.layer,
                                            verify_witness=WitnessVerifier(quotient, store),
                                            verify_complete=lambda: verify_closure(quotient, store, progress))
                if not args.json:
                    print(format_timed_report(result))
                    return 0
            print(json.dumps(result, indent=2, allow_nan=False))
            return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"timed_search: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("timed_search: interrupted; unfinished expansions remain on the resumable frontier", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
