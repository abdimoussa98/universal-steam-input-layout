"""Inductive bounds on the complete HeldModel state, with no event/depth cap.

Houdini removes candidate invariants contradicted by an initial state or a
single complete event. Only the conjunction surviving a full fixed point is
used for queries. A solver timeout discards affected candidates; it never
counts as a proof. Search samples suggest candidates, not assumptions.

These are proofs about HeldModel's untimed semantics, not Steam hardware.
"""
from dataclasses import dataclass
import time

import z3

from .held_model import HeldModel
from .symbolic import SymbolicModel, Transition


@dataclass(frozen=True, order=True)
class Candidate:
    kind: str
    x: int
    y: int = -1

    def formula(self, ranks, held):
        x, y = self.x, self.y
        if self.kind == "absent":
            return ranks[x] == 0
        if self.kind == "requires":
            return z3.Or(ranks[x] == 0, ranks[y] > 0)
        if self.kind == "excludes":
            return z3.Or(ranks[x] == 0, ranks[y] == 0)
        if self.kind == "not_below":
            return z3.Or(ranks[x] == 0, ranks[y] == 0, ranks[x] >= ranks[y])
        if self.kind == "held":
            return z3.Or(ranks[x] == 0, held[y])
        if self.kind == "released":
            return z3.Or(ranks[x] == 0, z3.Not(held[y]))
        raise ValueError(self.kind)

    def holds(self, ranks, held):
        x, y = self.x, self.y
        if not ranks[x]:
            return True
        return {"absent": lambda: False,
                "requires": lambda: bool(ranks[y]),
                "excludes": lambda: not ranks[y],
                "not_below": lambda: not ranks[y] or ranks[x] >= ranks[y],
                "held": lambda: held[y],
                "released": lambda: not held[y]}[self.kind]()

    def dependencies(self):
        layers = {self.x}
        if self.kind in ("requires", "excludes", "not_below"):
            layers.add(self.y)
        return layers, {self.y} if self.kind in ("held", "released") else set()

    def describe(self, model):
        x = model.layer_names[self.x]
        if self.kind == "absent":
            return f"{x} is absent"
        if self.kind in ("held", "released"):
            return f"{x} implies {'/'.join(model.controls[self.y])} is {self.kind}"
        y = model.layer_names[self.y]
        return {"requires": f"{x} implies {y} is present",
                "excludes": f"{x} and {y} cannot coexist",
                "not_below": f"{x} is never below {y}"}[self.kind]


def candidates_from_states(model, states):
    """Infer templates in one streaming pass; absence from samples proves nothing."""
    n = len(model.layer_names)
    tracked = {c for c, owner in enumerate(model.owner) if owner}
    seen = set()
    together = [set() for _ in range(n)]
    required = [set(range(n)) for _ in range(n)]
    above = [set() for _ in range(n)]
    always_held = [set(tracked) for _ in range(n)]
    ever_held = [set() for _ in range(n)]
    for stack, held, missed in states:
        if missed:
            raise ValueError("Missed-release samples are outside the proof model")
        layers = set(stack)
        for i, x in enumerate(stack):
            seen.add(x)
            together[x].update(layers)
            required[x].intersection_update(layers)
            above[x].update(stack[i + 1:])
            always_held[x].intersection_update(held)
            ever_held[x].update(held)
    result = []
    for x in range(1, n):
        if x not in seen:
            result.append(Candidate("absent", x))
        result.extend(Candidate("requires", x, y) for y in sorted(required[x] - {0, x}))
        result.extend(Candidate("held", x, c) for c in sorted(always_held[x]))
        result.extend(Candidate("released", x, c) for c in sorted(tracked - ever_held[x]))
        for y in range(1, n):
            if x == y:
                continue
            if y not in together[x]:
                if x < y:
                    result.append(Candidate("excludes", x, y))
            # Keep the weaker order facts even beside an exclusion: if the
            # exclusion is not inductive, a one-way order may still be.
            if y not in above[x]:
                result.append(Candidate("not_below", x, y))
    return sorted(result)


def induction_transitions(symbolic):
    """Identical updates share one obligation under the union of their guards.

    This merges formulas, not concrete states or stack order. Event labels
    are irrelevant to induction; the reference transition stream keeps them.
    Z3 AST IDs identify exact nodes within this one solver context.
    """
    groups = {}
    for transition in symbolic.transitions():
        key = tuple(e.get_id() for e in (*transition.ranks, *transition.held))
        if key not in groups:
            groups[key] = transition, []
        groups[key][1].append(transition.guard)
    return [Transition(z3.simplify(z3.Or(guards)), t.ranks, t.held, t.label, t.event)
            for t, guards in groups.values()]


class InvariantProof:
    def __init__(self, model, candidates, timeout_ms=10000, progress=None):
        if type(model) is not HeldModel or model.missed:
            raise ValueError("Proofs require HeldModel with missed releases disabled")
        self.model = model
        self.symbolic = SymbolicModel(model)
        self.timeout_ms = timeout_ms
        self.progress = progress or (lambda message: None)
        self.candidates = tuple(candidates)
        self.invariants = ()
        self.stats = {}
        self.finished = False

    def initial_valuations(self):
        """Concrete initial rank/held valuations used to filter hypotheses."""
        yield [1] + [0] * (len(self.model.layer_names) - 1), [False] * len(self.model.controls)

    def run(self):
        start = time.monotonic()
        sm = self.symbolic
        initial = tuple(self.initial_valuations())
        if not initial:
            raise ValueError("an inductive proof requires an initial state")
        active = {i for i, candidate in enumerate(self.candidates)
                  if all(candidate.holds(ranks, held) for ranks, held in initial)}
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        solver.add(sm.domain)
        switches = [z3.Bool(f"candidate_{i}") for i in range(len(self.candidates))]
        switch_ids = {switch.get_id(): i for i, switch in enumerate(switches)}
        for i in active:
            solver.add(z3.Implies(switches[i], self.candidates[i].formula(sm.ranks, sm.held)))
        transitions = induction_transitions(sm)
        self.progress(f"Checking {len(active)} candidates against {len(transitions)} complete event variants")
        affected = []
        deps = [c.dependencies() for c in self.candidates]
        for t in transitions:
            layers = {i for i, (a, b) in enumerate(zip(sm.ranks, t.ranks)) if not z3.eq(a, b)}
            buttons = {i for i, (a, b) in enumerate(zip(sm.held, t.held)) if not z3.eq(a, b)}
            affected.append({i for i, (ls, bs) in enumerate(deps) if ls & layers or bs & buttons})
        checks = unknown = rounds = skipped = 0
        # An unsat core records precisely which assumptions a successful
        # obligation needed. Later rounds only drop candidates, so the old
        # proof still suffices while all of its assumptions survive.
        cores = {}
        while True:
            rounds += 1
            before = len(active)
            for number, (t, relevant) in enumerate(zip(transitions, affected)):
                remaining = active & relevant
                if not remaining:
                    continue
                if number in cores and cores[number] <= active:
                    skipped += 1
                    continue
                solver.push()
                solver.add(t.guard)
                post = {i: z3.Not(self.candidates[i].formula(t.ranks, t.held)) for i in remaining}
                while remaining:
                    solver.push()
                    solver.add(z3.Or([post[i] for i in sorted(remaining)]))
                    result = solver.check(*[switches[i] for i in sorted(active)])
                    checks += 1
                    if result == z3.sat:
                        value = solver.model()
                        post_ranks = [value.eval(r, model_completion=True).as_long() for r in t.ranks]
                        post_held = [z3.is_true(value.eval(h, model_completion=True)) for h in t.held]
                        rejected = {i for i in remaining if not self.candidates[i].holds(post_ranks, post_held)}
                        if not rejected:
                            raise AssertionError("Symbolic counterexample did not violate a candidate")
                    elif result == z3.unknown:
                        # Weakening the final conjunction is sound. Keeping a candidate
                        # because its induction check timed out would not be.
                        rejected = set(remaining)
                        unknown += 1
                    else:
                        rejected = set()
                        cores[number] = {switch_ids[s.get_id()] for s in solver.unsat_core()}
                    solver.pop()
                    if not rejected:
                        break
                    active.difference_update(rejected)
                    remaining.difference_update(rejected)
                solver.pop()
                if number % 100 == 0:
                    self.progress(f"Round {rounds}, event {number + 1}/{len(transitions)}, "
                                  f"{len(active)} candidates remain ({unknown} unknown checks)")
            self.progress(f"Round {rounds}: {before} -> {len(active)} candidates")
            if before == len(active):
                break
        self.invariants = tuple(self.candidates[i] for i in sorted(active))
        self.stats = {"candidates": len(self.candidates), "invariants": len(active), "rounds": rounds,
                      "checks": checks, "unknown_checks": unknown, "reused_checks": skipped,
                      "transitions": len(transitions),
                      "seconds": round(time.monotonic() - start, 3)}
        self.finished = True
        return self

    def query_solver(self):
        if not self.finished:
            raise ValueError("Run induction to a fixed point before querying its invariants")
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        solver.add(self.symbolic.domain)
        solver.add([c.formula(self.symbolic.ranks, self.symbolic.held) for c in self.invariants])
        return solver
