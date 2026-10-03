"""Remove logically redundant timed hypotheses without asserting induction.

The CLI loads a checked certificate and independently checks the smaller result.
The lower-level helper only preserves a conjunction under the symbolic domain;
it cannot turn unproved input hypotheses into a valid certificate.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import z3

from .model import Layout
from .timed_audit import load_certificate, save_certificate
from .timed_model import TimedModel


def minimize_hypotheses(proof, *, timeout_ms=100, progress=None):
    """Return an equivalent subset and diagnostics; do not mutate the proof.

    Each removed predicate follows from the predicates still retained. Unknown
    checks retain their predicate. Larger dependencies are considered first,
    since removing them can avoid expensive projected induction obligations.
    The returned hypotheses still require independent induction validation.
    """
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError("timeout_ms must be a positive integer")
    predicates = tuple(proof.invariants)
    proof._check_predicate_context(predicates)
    progress = progress or (lambda message: None)
    symbolic = proof.symbolic
    formulas = [p.formula(symbolic.ranks, symbolic.held) for p in predicates]
    switches = [z3.FreshBool("minimize") for _ in predicates]
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    solver.add(symbolic.domain)
    solver.add([z3.Implies(s, f) for s, f in zip(switches, formulas)])
    active = set(range(len(predicates)))
    order = sorted(active, key=lambda i: (len(predicates[i].dependencies()[0]),
                                         len(str(formulas[i]))), reverse=True)
    started = last_progress = time.monotonic()
    unknown = 0
    for number, i in enumerate(order, 1):
        solver.push()
        solver.add(z3.Not(formulas[i]))
        result = solver.check(*[switches[j] for j in sorted(active) if j != i])
        solver.pop()
        if result == z3.unsat:
            active.remove(i)
        elif result == z3.unknown:
            unknown += 1
        if time.monotonic() - last_progress >= 10:
            progress(f"Logical reduction {number}/{len(order)}: {len(active)} retained; "
                     f"{unknown} unknown checks")
            last_progress = time.monotonic()
    result = tuple(predicates[i] for i in sorted(active))
    return result, {"input": len(predicates), "retained": len(result),
                    "checks": len(order), "unknown_checks": unknown,
                    "seconds": round(time.monotonic() - started, 3),
                    "scope": "Logical equivalence only; induction must be checked separately."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=10000)
    parser.add_argument("--minimize-timeout-ms", type=int, default=100)
    parser.add_argument("--ignore-hold-bindings", action="store_true")
    parser.add_argument("--default-repeat-ms", type=int)
    args = parser.parse_args(argv)
    try:
        if (args.output.resolve() == args.layout.resolve() or
                (args.output.exists() and args.layout.exists() and
                 args.output.samefile(args.layout))):
            raise ValueError("output must not alias the layout")
        if args.timeout_ms <= 0 or args.minimize_timeout_ms <= 0:
            raise ValueError("solver timeouts must be positive")
        model = TimedModel(Layout(json.loads(args.layout.read_text())),
                           ignore_hold_bindings=args.ignore_hold_bindings,
                           default_repeat_ms=args.default_repeat_ms)
        progress = lambda message: print(message, file=sys.stderr, flush=True)
        proof = load_certificate(model, args.certificate, timeout_ms=args.timeout_ms,
                                 progress=progress)
        reduced, stats = minimize_hypotheses(proof, timeout_ms=args.minimize_timeout_ms,
                                           progress=progress)
        proof.invariants = reduced
        proof._validated_invariants = None
        proof.stats = {**proof.stats, "logical_minimization": stats}
        saved = save_certificate(proof, args.output)
        print(json.dumps({"logical_minimization": stats, "validation": saved["validation"]}))
    except (OSError, ValueError, KeyError, TypeError, z3.Z3Exception) as exc:
        print(f"timed_minimize: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
