"""Symbolic, one-event semantics of :class:`HeldModel`.

Ranks encode the complete ordered stack: zero means absent, and increasing
positive ranks run from bottom to top. Input ranks are bounded by the number
of layers; output ranks may have gaps or exceed that bound. Renumbering the
positive ranks preserves the represented state. Invariants using presence and
relative order are therefore suitable for induction without an event bound.

The optional ``z3-solver`` package is needed only when this module is imported.
"""
from dataclasses import dataclass
import itertools

import z3

from .held_model import (ALWAYS, DIRS, LATER, PRESS, RELEASE, SHIFT_TAP, TAP,
                         TAP_HELD, TIMER)
from .search_model import REMOVE


def _and(*args):
    return z3.simplify(z3.And(*args))


def _or(args):
    return z3.simplify(z3.Or(*args))


@dataclass(frozen=True)
class Transition:
    guard: object
    ranks: tuple
    held: tuple
    label: str
    event: tuple


@dataclass(frozen=True)
class _Branch:
    guard: object
    ranks: tuple
    ceiling: int


class SymbolicModel:
    """Compile exact HeldModel events into guarded symbolic stack updates.

    Every transition is evaluated under ``domain``. An arbitrary satisfying
    assignment to the ranks is a full stack, not a pair abstraction. The
    transition may inspect any layer or held control in that stack.
    """

    def __init__(self, model, prefix="state"):
        if model.missed:
            raise ValueError("SymbolicModel requires missed=False")
        self.model = model
        self.n = len(model.layer_names)
        self.ranks = tuple(z3.Int(f"{prefix}_rank_{i}") for i in range(self.n))
        self.held = tuple(z3.Bool(f"{prefix}_held_{i}") for i in range(len(model.controls)))
        rs = self.ranks
        constraints = [rs[0] > 0]
        constraints.extend(z3.And(r >= 0, r <= self.n) for r in rs)
        constraints.extend(z3.Implies(rs[i] > 0, rs[i] > rs[0]) for i in range(1, self.n))
        constraints.extend(z3.Or(rs[i] == 0, rs[j] == 0, rs[i] != rs[j])
                           for i in range(1, self.n) for j in range(i + 1, self.n))
        constraints.extend(z3.Not(self.held[c]) for c, tracked in enumerate(model.owner) if not tracked)
        constraints.append(self.valid(self.held))
        self.domain = _and(*constraints)
        self.start = _and(rs[0] == 1, *(r == 0 for r in rs[1:]), *(z3.Not(h) for h in self.held))
        self._definers = {}
        for jid in range(len(model.inputs)):
            self._definers[jid] = tuple(l for l in range(self.n)
                                        if jid in model.binds.get(l, ()) or jid in model.blocks.get(l, ()))

    def valid(self, held):
        """HeldModel.valid, including temporary controls during atomic taps."""
        m = self.model
        constraints = []
        for c in range(len(held)):
            for d in range(c + 1, len(held)):
                if m.thumb[c] in "LR" and m.thumb[c] == m.thumb[d] and m.thumb_source[c] != m.thumb_source[d]:
                    constraints.append(z3.Or(z3.Not(held[c]), z3.Not(held[d])))
        sources = {}
        for c, (source, name) in enumerate(m.controls):
            sources.setdefault(source, {})[name] = c
        for source, controls in sources.items():
            if source.endswith("joystick") or source.endswith("trackpad"):
                directions = [(DIRS[name], c) for name, c in controls.items() if name in DIRS]
                for (a, c), (b, d) in itertools.combinations(directions, 2):
                    if (a - b) % 4 == 2:
                        constraints.append(z3.Or(z3.Not(held[c]), z3.Not(held[d])))
                touch = controls.get("touch")
                if touch is not None and m.owner[touch]:
                    constraints.extend(z3.Implies(held[c], held[touch])
                                       for name, c in controls.items() if name != "touch")
            if source.endswith("trigger") and "click" in controls and "edge" in controls and m.owner[controls["edge"]]:
                constraints.append(z3.Implies(held[controls["click"]], held[controls["edge"]]))
        return _and(*constraints)

    def satisfied(self, cond, held, for_blocking=False):
        if cond < 0:
            return z3.BoolVal(True)
        key = self.model.conds[cond]
        if key == ("unknown",):
            return z3.BoolVal(not for_blocking)
        hits = [_or([held[self.model.cid[j]] for j in spec if j in self.model.cid]) for spec in key[1]]
        return _and(*hits) if key[0] == "all" else _or(hits)

    def _selected(self, ents, held, phase):
        blocked = _or([self.satisfied(e["cond"], held, True) for e in ents if e["kind"] == "C"])
        chosen = []
        for e in ents:
            if phase == "release":
                ok = z3.BoolVal(e["kind"] == "R")
            elif e["kind"] == "R":
                ok = z3.BoolVal(False)
            else:
                checks = []
                if e["kind"] == "C":
                    checks.append(self.satisfied(e["cond"], held))
                if e["kind"] == "P" and e["interruptible"]:
                    checks.append(z3.Not(blocked))
                if phase == "press":
                    checks.append(z3.BoolVal(not e["delay"]))
                elif phase != "always":
                    checks.append(z3.BoolVal(e["delay"] or e["repeat"]))
                ok = _and(*checks)
            chosen.append(ok)
        return chosen

    def owner(self, ranks, key, lid):
        """Whether lid is the topmost binding (a disabled source stops lookup)."""
        m = self.model
        if key == "always":
            if ALWAYS not in m.input_index:
                return z3.BoolVal(False)
            jid = m.input_index[ALWAYS]
        else:
            jid = m.input_index[m.controls[key]]
        if jid not in m.binds.get(lid, ()) or jid in m.blocks.get(lid, ()):
            return z3.BoolVal(False)
        return _and(ranks[lid] > 0, *(z3.Or(ranks[other] == 0, ranks[other] < ranks[lid])
                                      for other in self._definers[jid] if other != lid))

    def _apply(self, branch, ops):
        ranks, ceiling = list(branch.ranks), branch.ceiling
        for op, target in ops:
            if op == REMOVE:
                if target:
                    ranks[target] = z3.IntVal(0)
            else:
                ceiling += 1
                ranks[target] = z3.simplify(z3.If(ranks[target] == 0, ceiling, ranks[target]))
        return _Branch(branch.guard, tuple(ranks), ceiling)

    def _fire(self, branch, held, key, phase, explicit=None):
        """Fire one phase; entry selection precedes execution of all commands."""
        m = self.model
        if explicit is None:
            choices = [(self.owner(branch.ranks, key, lid), ents)
                       for (lid, c), ents in m.entries.items() if c == key]
        else:
            choices = [(z3.BoolVal(True), explicit)]
        effect_guards, output = [], []
        for owner_guard, ents in choices:
            if z3.is_false(owner_guard):
                continue
            selected = self._selected(ents, held, phase)
            relevant = [(e, ok) for e, ok in zip(ents, selected) if e["ops"] and not z3.is_false(ok)]
            if not relevant:
                continue
            # Enumerate only the conditional entries; most bindings have none.
            fixed = [i for i, (_, ok) in enumerate(relevant) if z3.is_true(ok)]
            conditional = [i for i, (_, ok) in enumerate(relevant) if not z3.is_true(ok)]
            for bits in itertools.product((False, True), repeat=len(conditional)):
                chosen = set(fixed) | {i for i, bit in zip(conditional, bits) if bit}
                if not chosen:
                    continue
                guard = _and(owner_guard, *(relevant[i][1] if bit else z3.Not(relevant[i][1])
                                            for i, bit in zip(conditional, bits)))
                if z3.is_false(guard):
                    continue
                effect_guards.append(guard)
                lists = [relevant[i][0]["ops"] for i in sorted(chosen)]
                orders = itertools.permutations(lists) if len(lists) <= 3 else [lists]
                for order in orders:
                    effect = _Branch(_and(branch.guard, guard), branch.ranks, branch.ceiling)
                    if not z3.is_false(effect.guard):
                        output.append(self._apply(effect, itertools.chain.from_iterable(order)))
        unchanged = _Branch(_and(branch.guard, z3.Not(_or(effect_guards))), branch.ranks, branch.ceiling)
        if not z3.is_false(unchanged.guard):
            output.append(unchanged)
        if phase == "release" and key in m.holds:
            output = [self._apply(b, [(REMOVE, target) for target in sorted(m.holds[key])]) for b in output]
        return output

    def _transition(self, branch, held, event):
        return Transition(branch.guard, branch.ranks, tuple(held), self.model.label(event), event)

    def _tap(self, branch, held, key, more, kind, explicit=None):
        for pressed in self._fire(branch, more, key, "press", explicit):
            for held_long in (False, True):
                mids = self._fire(pressed, more, key, "later", explicit) if held_long else [pressed]
                for mid in mids:
                    for released in self._fire(mid, more, key, "release", explicit):
                        phase = (TAP_HELD if held_long else TAP) if kind == TAP else kind
                        yield self._transition(released, held, (key, phase))

    def _shifted(self, ranks, held):
        guards = {gid: [] for gid in self.model.shift_groups}
        for (lid, key), ents in self.model.entries.items():
            if key == "always" or not any(e["shift"] for e in ents):
                continue
            owner_guard = self.owner(ranks, key, lid)
            for e, selected in zip(ents, self._selected(ents, held, "press")):
                for gid in e["shift"]:
                    guards[gid].append(_and(held[key], owner_guard, selected))
        return {gid: _or(parts) for gid, parts in guards.items()}

    def transitions(self):
        """All guarded complete events; apply under domain, never to partial entries."""
        m, held = self.model, self.held
        for key, tracked in enumerate(m.owner):
            more = tuple(z3.BoolVal(True) if c == key else h for c, h in enumerate(held))
            if tracked:
                initial = _Branch(_and(z3.Not(held[key]), self.valid(more)), self.ranks, self.n)
                for branch in self._fire(initial, more, key, "press"):
                    yield self._transition(branch, more, (key, PRESS))
                initial = _Branch(held[key], self.ranks, self.n)
                for branch in self._fire(initial, held, key, "later"):
                    yield self._transition(branch, held, (key, LATER))
                rest = tuple(z3.BoolVal(False) if c == key else h for c, h in enumerate(held))
                initial = _Branch(_and(held[key], self.valid(rest)), self.ranks, self.n)
                for branch in self._fire(initial, held, key, "release"):
                    yield self._transition(branch, rest, (key, RELEASE))
            else:
                initial = _Branch(self.valid(more), self.ranks, self.n)
                yield from self._tap(initial, held, key, more, TAP)
        for gid, active in self._shifted(self.ranks, held).items():
            for key, ents in m.shift_groups[gid].items():
                more = tuple(z3.BoolVal(True) if c == key else h for c, h in enumerate(held))
                initial = _Branch(_and(active, z3.Not(held[key]), self.valid(more)), self.ranks, self.n)
                yield from self._tap(initial, held, key, more, SHIFT_TAP, ents)
        initial = _Branch(z3.BoolVal(True), self.ranks, self.n)
        for branch in self._fire(initial, held, "always", "always"):
            yield self._transition(branch, held, (-1, TIMER))

    def assignment(self, state):
        """Concrete state's canonical substitution, useful for witness checking."""
        stack, held, missed = state
        if missed:
            raise ValueError("SymbolicModel excludes missed releases")
        ranks = {layer: rank for rank, layer in enumerate(stack, 1)}
        return [(r, z3.IntVal(ranks.get(i, 0))) for i, r in enumerate(self.ranks)] + [
            (h, z3.BoolVal(c in held)) for c, h in enumerate(self.held)]

    def successor_states(self, state, transitions=None):
        """Evaluate the formulas at a concrete state (primarily for differential tests)."""
        subst = self.assignment(state)
        if not z3.is_true(z3.simplify(z3.substitute(self.domain, subst))):
            raise ValueError("State is outside the symbolic domain")
        result = set()
        for transition in transitions if transitions is not None else self.transitions():
            if not z3.is_true(z3.simplify(z3.substitute(transition.guard, subst))):
                continue
            ranks = [z3.simplify(z3.substitute(r, subst)).as_long() for r in transition.ranks]
            stack = tuple(sorted((l for l, r in enumerate(ranks) if r), key=ranks.__getitem__))
            held = frozenset(c for c, h in enumerate(transition.held)
                             if z3.is_true(z3.simplify(z3.substitute(h, subst))))
            result.add(((stack, held, False), transition.event))
        return result
