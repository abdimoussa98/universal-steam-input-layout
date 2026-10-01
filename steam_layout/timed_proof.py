"""Inductive exclusions over a full-stack relaxation of the timed runtime.

Timing is forgotten only for the upper bound. Reachability claims require
separate concrete timed witnesses. A result is complete only when those bounds
meet for every requested fact, never because an arbitrary search limit passed.
"""
from types import SimpleNamespace
from itertools import chain
import time

import z3

from .invariants import Candidate, InvariantProof, candidates_from_states
from .timed_analog_envelope import TimedAnalogEnvelope


class TimedProof(InvariantProof):
    def __init__(self, model, seeds=(), *, timeout_ms=10000, progress=None):
        self.timed_model = model
        self.symbolic = TimedAnalogEnvelope(model)
        controls = tuple(self.symbolic.controls)
        index = {c: i for i, c in enumerate(controls)}
        self.model = SimpleNamespace(layer_names=model.spec.layer_names,
                                     index=model.spec.index, controls=controls,
                                     owner=[True] * len(controls))

        def converted():
            for state in chain(model.start(), seeds):
                yield state.stack, frozenset(index[c] for c in state.held if c in index), False

        self.candidates = tuple(candidates_from_states(self.model, converted()))
        self.timeout_ms = timeout_ms
        self.progress = progress or (lambda message: None)
        self.invariants, self.stats, self.finished = (), {}, False
        self._validated_invariants = None
        self._baseline = ()

    def initial_valuations(self):
        for state in self.symbolic.start_states:
            ranks = [0] * len(self.model.layer_names)
            for rank, layer in enumerate(state.stack, 1):
                ranks[layer] = rank
            yield ranks, [control in state.held for control in self.model.controls]

    def _check_predicate_context(self, predicates):
        """Do not let a caller change the binding context of a named fact."""
        from .timed_facts import FactCatalogue
        from .timed_predicates import FactExclusion, RequiresBelowAny, RequiresBetweenAny
        count = len(self.model.layer_names)
        for predicate in predicates:
            if type(predicate) is Candidate:
                if (predicate.kind not in ("absent", "requires", "excludes", "not_below", "held", "released")
                        or type(predicate.x) is not int or not 0 <= predicate.x < count
                        or type(predicate.y) is not int):
                    raise ValueError("invalid timed invariant")
                limit = len(self.model.controls) if predicate.kind in ("held", "released") else count
                if (predicate.y != -1 if predicate.kind == "absent" else not 0 <= predicate.y < limit):
                    raise ValueError("invalid timed invariant dependency")
            elif type(predicate) is RequiresBelowAny:
                if predicate.x >= count or any(member >= count for member in predicate.members):
                    raise ValueError("family predicate references an unknown layer")
            elif type(predicate) is RequiresBetweenAny:
                if (predicate.x >= count or predicate.y >= count or
                        any(member >= count for member in predicate.members)):
                    raise ValueError("between predicate references an unknown layer")
            elif type(predicate) is FactExclusion:
                if not hasattr(self, "_fact_catalogue"):
                    self._fact_catalogue = FactCatalogue(self.timed_model)
                canonical = FactExclusion.from_data(predicate.to_data(), self._fact_catalogue)
                if canonical.fact.definers != predicate.fact.definers:
                    raise ValueError("fact exclusion has noncanonical definer context")
            else:
                raise ValueError("unsupported timed invariant type")

    @staticmethod
    def _groups(candidates):
        groups = {}
        for i, candidate in enumerate(candidates):
            key = tuple(sorted(candidate.dependencies()[0]))
            groups.setdefault(key, set()).add(i)
        return sorted(groups.items(), key=lambda item: (len(item[0]), item[0]))

    def run(self):
        """Check small postcondition projections over the full pre-state.

        Projection only removes batch operations irrelevant to the checked
        predicates. Every guard and invariant still sees the entire ordered
        stack. Unknown disjunctions are split before individual unproved
        hypotheses are discarded; no timeout can become an exclusion.
        """
        started = last_progress = time.monotonic()
        sm = self.symbolic
        self._check_predicate_context((*self._baseline, *self.candidates))
        initial = tuple(self.initial_valuations())
        active = {i for i, c in enumerate(self.candidates)
                  if all(c.holds(ranks, held) for ranks, held in initial)}
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        solver.add(sm.domain)
        solver.add([c.formula(sm.ranks, sm.held) for c in self._baseline])
        switches = [z3.Bool(f"timed_candidate_{i}") for i in range(len(self.candidates))]
        switch_ids = {switch.get_id(): i for i, switch in enumerate(switches)}
        preconditions = {i: self.candidates[i].formula(sm.ranks, sm.held) for i in active}
        for i in active:
            solver.add(z3.Implies(switches[i], preconditions[i]))
        groups = self._groups(self.candidates)
        checks = unknown = rounds = skipped = 0
        cores, postconditions = {}, {}
        self.progress(f"Checking {len(active)} candidates in {len(groups)} dependency groups")
        while True:
            rounds += 1
            before = len(active)
            for number, (layers, candidates) in enumerate(groups):
                if not (active & candidates):
                    continue
                for event_number, transition in enumerate(sm.project_transitions(layers)):
                    key = (layers, event_number)
                    if key in cores and cores[key] <= active:
                        skipped += 1
                        continue
                    remaining = active & candidates
                    if not remaining:
                        break
                    if key not in postconditions:
                        values = {i: self.candidates[i].formula(transition.ranks, transition.held)
                                  for i in remaining}
                        postconditions[key] = {i: z3.Not(value) for i, value in values.items()
                                               if not z3.eq(value, preconditions[i])}
                    post = postconditions[key]
                    remaining.intersection_update(post)
                    if not remaining:
                        cores[key] = set()
                        skipped += 1
                        continue
                    solver.push()
                    solver.add(transition.guard)
                    queue = [remaining]
                    successful_cores = set()
                    while queue:
                        subset = queue.pop() & active
                        if not subset:
                            continue
                        solver.push()
                        solver.add(z3.Or([post[i] for i in sorted(subset)]))
                        result = solver.check(*[switches[i] for i in sorted(active)])
                        checks += 1
                        if result == z3.sat:
                            assignment = solver.model()
                            rejected = {i for i in remaining & active
                                        if z3.is_true(assignment.eval(post[i], model_completion=True))}
                            if not rejected:
                                raise AssertionError("counterexample violated no timed hypothesis")
                            active.difference_update(rejected)
                            queue.append(subset - rejected)
                        elif result == z3.unknown:
                            unknown += 1
                            ordered = sorted(subset)
                            if len(ordered) > 1:
                                middle = len(ordered) // 2
                                queue.extend((set(ordered[:middle]), set(ordered[middle:])))
                            else:
                                active.difference_update(subset)
                        else:
                            successful_cores.update(switch_ids[s.get_id()] for s in solver.unsat_core())
                        solver.pop()
                    solver.pop()
                    # Successful checks can precede a later rejection of an
                    # assumption. Reuse them only while every dependency lives.
                    cores[key] = successful_cores
                if time.monotonic() - last_progress >= 10:
                    self.progress(f"Round {rounds}, group {number + 1}/{len(groups)}: "
                                  f"{len(active)} candidates remain; {checks} checks, {unknown} unknown")
                    last_progress = time.monotonic()
            self.progress(f"Round {rounds}: {before} -> {len(active)} candidates")
            if before == len(active):
                break
        self.invariants = self._baseline + tuple(self.candidates[i] for i in sorted(active))
        self.compact()
        self.stats = {"candidates": len(self.candidates), "invariants": len(active),
                      "rounds": rounds, "checks": checks, "unknown_checks": unknown,
                      "reused_checks": skipped, "groups": len(groups),
                      "seconds": round(time.monotonic() - started, 3)}
        self.stats["invariants_before_compaction"] = len(self._baseline) + len(active)
        self.stats["baseline_invariants"] = len(self._baseline)
        self.stats["invariants"] = len(self.invariants)
        self.finished = True
        self._validated_invariants = None
        return self

    def refine(self, candidates, *, timeout_ms=None):
        """Check new hypotheses while preserving an independently proved base.

        The existing conjunction is already inductive without the proposed
        additions. Rechecking only new postconditions is therefore sufficient;
        the final combined certificate still receives independent validation.
        """
        self._check_predicate_context(self.invariants)
        if self._validated_invariants != self.invariants or not self.finished:
            self.validate()
        result = TimedProof(self.timed_model,
                            timeout_ms=self.timeout_ms if timeout_ms is None else timeout_ms,
                            progress=self.progress)
        result._baseline = self.invariants
        baseline = set(self.invariants)
        result.candidates = tuple(dict.fromkeys(c for c in candidates if c not in baseline))
        return result.run()

    def compact(self):
        """Drop simple logical consequences without weakening the conjunction.

        An absent layer makes every implication from its presence vacuous.
        Exclusion of a pair implies both relative-order exclusions. Keeping
        just their reasons reduces independent validation and query formulas.
        """
        absent = {c.x for c in self.invariants if c.kind == "absent"}
        excluded_pairs = {frozenset((c.x, c.y)) for c in self.invariants if c.kind == "excludes"}
        retained = []
        for candidate in self.invariants:
            if candidate.kind != "absent" and candidate.x in absent:
                continue
            if candidate.kind in ("excludes", "not_below") and candidate.y in absent:
                continue
            if (candidate.kind == "not_below" and
                    frozenset((candidate.x, candidate.y)) in excluded_pairs):
                continue
            retained.append(candidate)
        self.invariants = tuple(retained)
        self._validated_invariants = None
        return self

    def validate(self):
        """Independently check initialization and each retained conjunction."""
        if not self.finished:
            raise ValueError("finish induction before checking its certificate")
        self._check_predicate_context(self.invariants)
        sm = self.symbolic
        pre = z3.And([c.formula(sm.ranks, sm.held) for c in self.invariants])
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        solver.add(sm.domain, sm.start, z3.Not(pre))
        if solver.check() != z3.unsat:
            raise ValueError("timed invariant certificate failed initialization")
        checks = 1
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        solver.add(sm.domain, pre)
        groups = self._groups(self.invariants)
        last_progress = time.monotonic()
        for number, (layers, candidates) in enumerate(groups):
            for transition in sm.project_transitions(layers):
                changed = []
                for i in sorted(candidates):
                    value = self.invariants[i].formula(transition.ranks, transition.held)
                    if not z3.eq(value, self.invariants[i].formula(sm.ranks, sm.held)):
                        changed.append(value)
                if not changed:
                    continue
                solver.push()
                post = z3.And(changed)
                solver.add(transition.guard, z3.Not(post))
                if solver.check() != z3.unsat:
                    raise ValueError(f"timed invariant certificate failed {transition.label} {layers}")
                solver.pop()
                checks += 1
            if time.monotonic() - last_progress >= 10:
                self.progress(f"Certificate group {number + 1}/{len(groups)}: {checks} checks")
                last_progress = time.monotonic()
        self._validated_invariants = self.invariants
        return {"verified": True, "checks": checks, "invariants": len(self.invariants),
                "scope": "full-stack timed envelope; concrete witnesses remain required"}

    def classify(self, catalogue, witnesses):
        """Find upper-bound possibilities in batches of facts about one layer.

        A SAT assignment supplies many possible facts at once. An UNSAT query
        excludes the remaining disjunction. Unknowns keep all affected facts
        open. Witnesses are replayed before a fact can become proven.
        """
        if not self.finished:
            raise ValueError("finish induction before classifying facts")
        if catalogue.model is not self.timed_model or witnesses.model is not self.timed_model:
            raise ValueError("proof, catalogue and witnesses must share the same TimedModel")
        if witnesses.catalogue is not catalogue:
            raise ValueError("witnesses must use this fact catalogue")
        self._check_predicate_context(self.invariants)
        if self._validated_invariants != self.invariants:
            self.validate()
        started = time.monotonic()
        sm = self.symbolic
        solver = self.query_solver()
        possible, excluded = set(), set()
        queries = unknown = 0
        for x in range(len(self.model.layer_names)):
            remaining = {fact for fact in catalogue.facts if fact.x == x}
            predicates = {fact: fact.formula(sm.ranks) for fact in remaining}
            solver.push()
            solver.add(sm.ranks[x] > 0)
            while remaining:
                solver.push()
                solver.add(z3.Or([predicates[fact] for fact in sorted(remaining)]))
                result = solver.check()
                queries += 1
                if result == z3.sat:
                    assignment = solver.model()
                    ranks = [assignment.eval(r, model_completion=True).as_long() for r in sm.ranks]
                    stack = tuple(sorted((i for i, r in enumerate(ranks) if r), key=ranks.__getitem__))
                    admitted = remaining & catalogue.facts_of(stack)
                    if not admitted:
                        raise AssertionError("solver fact assignment and concrete projection disagree")
                    possible.update(admitted)
                    remaining.difference_update(admitted)
                elif result == z3.unsat:
                    excluded.update(remaining)
                    remaining.clear()
                else:
                    unknown += 1
                    possible.update(remaining)
                    remaining.clear()
                solver.pop()
            solver.pop()
            self.progress(f"Facts for {self.model.layer_names[x]}: {len(excluded)} excluded, "
                          f"{len(possible)} possible ({unknown} unknown checks)")
        observed = set(witnesses.facts)
        if observed & excluded:
            raise ValueError("an envelope exclusion contradicts a concrete timed witness")
        for fact in observed:
            witnesses.verify(fact)
        if possible | excluded != set(catalogue.facts):
            raise AssertionError("the upper bound did not classify every catalogue alternative")
        return {"proven": observed, "possible": possible - observed, "excluded": excluded,
                "complete_for_model": not (possible - observed),
                "queries": queries, "unknown_queries": unknown,
                "seconds": round(time.monotonic() - started, 3)}
