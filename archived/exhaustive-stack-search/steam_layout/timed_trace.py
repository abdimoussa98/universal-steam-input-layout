"""Replay explicit input events with elapsed time, retaining every model branch."""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys

from .model import Layout
from .timed_model import TimedModel


SCOPE = ("Timed-model replay under the reported semantics and scenario options; "
         "this is not a reachability proof or hardware verification. "
         "Untimed search evidence does not establish these timed traces.")


def _control(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or any(not isinstance(part, str) or not part for part in value)):
        raise ValueError("control must be a [source, input] pair of nonempty strings")
    return tuple(value)


def parse_trace(trace):
    """Validate a JSON event list and return its normalized, JSON-safe form."""
    if not isinstance(trace, list):
        raise ValueError("trace must be a JSON list of input events")
    result = []
    for index, event in enumerate(trace, 1):
        try:
            if not isinstance(event, dict) or len(event) != 1:
                raise ValueError("event must contain exactly one operation")
            operation, value = next(iter(event.items()))
            if operation in ("press", "release"):
                normalized = list(_control(value))
            elif operation == "wait_ms":
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise ValueError("wait_ms must be a nonnegative integer")
                normalized = value
            elif operation == "analog":
                if not isinstance(value, dict) or set(value) != {"control", "value"}:
                    raise ValueError("analog must contain exactly control and value")
                control = _control(value["control"])
                number = value["value"]
                if isinstance(number, bool) or not isinstance(number, (str, int, float)):
                    raise ValueError("analog value must be a finite decimal number")
                try:
                    decimal = Decimal(str(number))
                except InvalidOperation as exc:
                    raise ValueError("analog value must be a finite decimal number") from exc
                if not decimal.is_finite():
                    raise ValueError("analog value must be a finite decimal number")
                normalized = {"control": list(control), "value": str(decimal)}
            else:
                raise ValueError(f"unknown operation: {operation}")
        except ValueError as exc:
            raise ValueError(f"trace step {index}: {exc}") from exc
        result.append({operation: normalized})
    return result


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _ordered_states(model, states):
    return sorted(set(states), key=lambda state: _canonical(model.snapshot(state)))


def replay(model, trace, *, layout_data, options=None):
    """Replay all branches, with per-step edges to keep branch histories usable.

    ``layout_data`` is the original JSON layout. The identity includes that
    layout, the model's semantic contract and caller-provided scenario options;
    it deliberately does not share the untimed model's evidence identity.
    """
    trace = parse_trace(trace)
    semantics = model.semantics
    scenario = dict(options or {})
    layout_digest = hashlib.sha256(_canonical(layout_data).encode("utf-8")).hexdigest()
    identity = {"model_family": "TimedModel", "trace_format_version": 1,
                "layout_sha256": layout_digest, "semantics": semantics,
                "scenario": scenario}
    model_digest = hashlib.sha256(_canonical(identity).encode("utf-8")).hexdigest()
    current = _ordered_states(model, model.start())
    if not current:
        raise ValueError("model has no initial states")
    report = {**identity, "model_sha256": model_digest, "scope": SCOPE,
              "initial_states": [model.snapshot(state) for state in current], "steps": []}
    for index, event in enumerate(trace, 1):
        operation, value = next(iter(event.items()))
        transitions = []
        successors = set()
        for previous_index, state in enumerate(current):
            try:
                if operation == "wait_ms":
                    following = model.wait(state, value)
                elif operation == "analog":
                    following = model.analog(state, tuple(value["control"]), value["value"])
                else:
                    following = getattr(model, operation)(state, tuple(value))
            except ValueError as exc:
                raise ValueError(f"trace step {index}: {exc}") from exc
            for following_state in following:
                transitions.append((previous_index, following_state))
                successors.add(following_state)
        current = _ordered_states(model, successors)
        if not current:
            raise ValueError(f"trace step {index}: no valid successor states")
        positions = {state: position for position, state in enumerate(current)}
        edges = sorted({(previous, positions[state]) for previous, state in transitions})
        report["steps"].append({"step": index, "event": event, "state_count": len(current),
                                "states": [model.snapshot(state) for state in current],
                                "transitions": [{"from": previous, "to": following}
                                                for previous, following in edges]})
    report["final_state_count"] = len(current)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path, help="Steam Input layout JSON")
    parser.add_argument("trace", type=Path,
                        help="JSON list of press/release/wait_ms/analog events (analog uses Steam raw units)")
    parser.add_argument("--ignore-hold-bindings", action="store_true",
                        help="explicitly omit legacy hold_layer commands from this scenario")
    parser.add_argument("--default-repeat-ms", type=int,
                        help="explicit scenario interval for repeat bindings missing repeat_rate")
    args = parser.parse_args(argv)
    if args.default_repeat_ms is not None and args.default_repeat_ms <= 0:
        parser.error("--default-repeat-ms must be positive")
    try:
        data = json.loads(args.layout.read_text(encoding="utf-8"))
        trace = parse_trace(json.loads(args.trace.read_text(encoding="utf-8")))
        options = {"ignore_hold_bindings": args.ignore_hold_bindings,
                   "default_repeat_ms": args.default_repeat_ms}
        model = TimedModel(Layout(data), **options)
        report = replay(model, trace, layout_data=data, options=options)
        report["layout"] = str(args.layout.resolve())
        report["trace"] = str(args.trace.resolve())
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"timed_trace: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
