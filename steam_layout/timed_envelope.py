"""A conservative symbolic envelope of the explicit timed runtime.

The envelope forgets activation clocks and mode-shift history, not the ordered
stack.  A physical event is followed by zero or more automatic entry batches.
Every batch freezes binding selection before executing its entries in any
order.  Consequently a timed transition has a path in this larger system;
extra prefix states and arbitrary timer firings are intentionally admitted.

This is an upper bound for TimedModel's declared contract, not for Steam's
undocumented behavior.  In particular it does not justify sensor geometry.
"""
from dataclasses import dataclass
from types import SimpleNamespace

import z3

from .held_model import ALWAYS, DIRS, THUMBS
from .symbolic_batch import apply_batch
from .timed_spec import canonical_control, chord_selectors


def _and(*parts):
    return z3.simplify(z3.And(*parts))


def _or(parts):
    return z3.simplify(z3.Or(*parts))


@dataclass(frozen=True)
class EnvelopeTransition:
    guard: object
    ranks: tuple
    held: tuple
    analog: tuple
    label: str
    event: tuple
    selected: tuple = ()
    lookup_choices: tuple = ()
    orders: tuple = ()
    projected_layers: object = None
    # One tuple of original entry IDs per order variable.  Projected batches
    # can combine equivalent pure removals; selected retains original entries.
    order_groups: tuple = ()


class TimedEnvelope:
    """Compile four guarded event families over full ranks and physical state.

    Real analog variables preserve fractional thresholds and samples.  ``-1``
    denotes an absent sample.  Non-Soft-Press controls have no analog variable:
    their samples affect only held membership in the reference model.
    """

    def __init__(self, runtime, prefix="timed_envelope"):
        self.runtime = runtime
        self.spec = runtime.spec
        self.prefix = prefix
        self.controls = tuple(sorted(runtime.controls))
        self.cid = {c: i for i, c in enumerate(self.controls)}
        self.n = len(self.spec.layer_names)
        self.model = SimpleNamespace(layer_names=self.spec.layer_names,
                                     controls=self.controls, cid=self.cid,
                                     index=self.spec.index,
                                     owner=(True,) * len(self.controls), missed=False)
        self.ranks = tuple(z3.Int(f"{prefix}_rank_{i}") for i in range(self.n))
        self.held = tuple(z3.Bool(f"{prefix}_held_{i}") for i in range(len(self.controls)))
        self.analog_controls = frozenset(
            self.cid[canonical_control((entry.source, entry.input))]
            for entry in self.spec.entries.values()
            if entry.kind == "Soft_Press" and (entry.source, entry.input) != ALWAYS)
        self.analog = tuple(z3.Real(f"{prefix}_analog_{i}") if i in self.analog_controls
                            else z3.RealVal(-1) for i in range(len(self.controls)))
        rs = self.ranks
        constraints = [rs[0] > 0]
        constraints.extend(z3.And(r >= 0, r <= self.n) for r in rs)
        constraints.extend(z3.Implies(rs[i] > 0, rs[i] > rs[0]) for i in range(1, self.n))
        constraints.extend(z3.Or(rs[i] == 0, rs[j] == 0, rs[i] != rs[j])
                           for i in range(1, self.n) for j in range(i + 1, self.n))
        constraints.extend((self.valid(self.held), self.valid_analog(self.held, self.analog)))
        self.domain = _and(*constraints)
        self.start_states = tuple(runtime.start())
        self.start = _or(self.state_formula(state) for state in self.start_states)
        self._definitions = {}
        for _, control in self.spec.bindings:
            self._definitions.setdefault(control, set())
        for control in self._definitions:
            self._definitions[control] = tuple(
                lid for lid in range(self.n)
                if (lid, control) in self.spec.bindings or control[0] in self.spec.blocked.get(lid, ()))
        self._shift_groups = {}
        self._shift_origins = {}
        for entry in self.spec.entries.values():
            for source, group in entry.shifts:
                groups = self._shift_groups.setdefault(source, [])
                if group not in groups:
                    groups.append(group)
                self._shift_origins.setdefault((source, group), []).append(entry)
        self._compiled = None
        self._projections = {}
        self._contexts = {}

    def valid(self, held):
        constraints = []
        for i, control in enumerate(self.controls):
            thumb = THUMBS.get(control, THUMBS.get(control[0]))
            location = control[0] if control not in THUMBS else "/".join(control)
            for j in range(i + 1, len(self.controls)):
                other = self.controls[j]
                other_thumb = THUMBS.get(other, THUMBS.get(other[0]))
                other_location = other[0] if other not in THUMBS else "/".join(other)
                if thumb is not None and thumb == other_thumb and location != other_location:
                    constraints.append(z3.Or(z3.Not(held[i]), z3.Not(held[j])))
        sources = {}
        for i, (source, name) in enumerate(self.controls):
            sources.setdefault(source, {})[name] = i
        for source, inputs in sources.items():
            if source.endswith(("joystick", "trackpad")):
                directions = [(DIRS[name], i) for name, i in inputs.items() if name in DIRS]
                for a, i in directions:
                    for b, j in directions:
                        if i < j and (a - b) % 4 == 2:
                            constraints.append(z3.Or(z3.Not(held[i]), z3.Not(held[j])))
                if "touch" in inputs:
                    constraints.extend(z3.Implies(held[i], held[inputs["touch"]])
                                       for name, i in inputs.items() if name != "touch")
            if source.endswith("trigger") and "click" in inputs and "edge" in inputs:
                constraints.append(z3.Implies(held[inputs["click"]], held[inputs["edge"]]))
        return _and(*constraints)

    def valid_analog(self, held, analog):
        return _and(*(z3.And(z3.Or(analog[i] == -1, z3.And(analog[i] >= 0, analog[i] <= 32767)),
                            z3.Implies(analog[i] >= 0, held[i] == (analog[i] > 0)))
                      for i in self.analog_controls))

    def state_formula(self, state, ranks=None, held=None, analog=None):
        """Constrain a symbolic projection to a concrete state, ignoring clocks."""
        ranks = self.ranks if ranks is None else ranks
        held = self.held if held is None else held
        analog = self.analog if analog is None else analog
        present = set(state.stack)
        values = dict(state.analog_values)
        return _and(*(rank > 0 if i in present else rank == 0 for i, rank in enumerate(ranks)),
                    *(ranks[a] < ranks[b] for a, b in zip(state.stack, state.stack[1:])),
                    *(value == (control in state.held) for control, value in zip(self.controls, held)),
                    *(analog[i] == z3.RealVal(str(values.get(self.controls[i], -1)))
                      for i in self.analog_controls))

    def _condition(self, entry, held):
        if not entry.chord:
            return z3.BoolVal(True)
        all_, selectors = chord_selectors(dict(entry.chord), entry.id)
        hits = []
        for selector in selectors:
            if isinstance(selector, str):
                kind, source = selector.split(":")
                if kind == "pad":
                    controls = [(source, "touch")]
                else:
                    controls = [c for c in self.controls if c[0] == source and c[1] not in ("touch", "click")]
            else:
                controls = [canonical_control(c) for c in selector]
            hits.append(_or(held[self.cid[c]] for c in controls if c in self.cid))
        return _and(*hits) if all_ else _or(hits)

    def _pressed(self, entry, held, analog):
        control = canonical_control((entry.source, entry.input))
        if control == ALWAYS:
            return z3.BoolVal(True)
        i = self.cid[control]
        if entry.kind != "Soft_Press":
            return held[i]
        threshold = z3.RealVal(str(entry.threshold if entry.threshold is not None else 0))
        known = analog[i] >= 0
        outside = analog[i] > threshold
        sampled = z3.Not(outside) if entry.invert else outside
        missing = (z3.BoolVal(False) if entry.threshold is not None else
                   z3.Not(held[i]) if entry.invert else held[i])
        return z3.If(known, sampled, missing)

    def _lookups(self, held, prefix):
        choices, constraints = {}, []
        for source, groups in self._shift_groups.items():
            choice = z3.Int(f"{prefix}_shift_{source}")
            choices[source] = choice
            constraints.append(z3.And(choice >= 0, choice <= len(groups)))
            for number, group in enumerate(groups, 1):
                origins = []
                for entry in self._shift_origins[(source, group)]:
                    control = canonical_control((entry.source, entry.input))
                    if control in self.cid:
                        origins.append(_and(held[self.cid[control]], self._condition(entry, held)))
                constraints.append(z3.Implies(choice == number, _or(origins)))
        return choices, constraints

    def _binding(self, owner, control, choices):
        source = control[0]
        if isinstance(owner, str):
            group = owner.split(":", 2)[2]
            return choices[source] == self._shift_groups[source].index(group) + 1
        if source in self.spec.blocked.get(owner, ()):
            return z3.BoolVal(False)
        constraints = [self.ranks[owner] > 0]
        if source in choices:
            constraints.append(choices[source] == 0)
        constraints.extend(z3.Or(self.ranks[other] == 0, self.ranks[other] < self.ranks[owner])
                           for other in self._definitions[control] if other != owner)
        return _and(*constraints)

    def _entries(self, held, analog, choices, release=False, layers=None):
        result = []
        for (owner, control), entries in self.spec.bindings.items():
            relevant = [entry for entry in entries
                        if entry.ops and (entry.kind == "release") == release
                        and (layers is None or any(target in layers for _, target in entry.ops))]
            if not relevant:
                continue
            binding = self._binding(owner, control, choices)
            blocked = _or(_and(self._pressed(e, held, analog), self._condition(e, held))
                          for e in entries if e.kind == "chord")
            for entry in relevant:
                checks = [binding]
                if not release:
                    checks.append(self._pressed(entry, held, analog))
                    if entry.kind == "chord":
                        checks.append(self._condition(entry, held))
                    if entry.kind == "Full_Press" and entry.interruptible:
                        checks.append(z3.Not(blocked))
                result.append((entry, _and(*checks)))
        return result

    def _context(self, kind):
        if kind in self._contexts:
            return self._contexts[kind]
        prefix = f"{self.prefix}_{kind}"
        held, analog = self.held, self.analog
        control = z3.Int(f"{prefix}_control")
        sample = None
        constraints, event = [], (kind,)
        if kind in ("press", "release"):
            constraints.append(z3.And(control >= 0, control < len(self.controls)))
            constraints.extend(z3.Implies(control == i, z3.Not(h) if kind == "press" else h)
                               for i, h in enumerate(self.held))
            held = tuple(z3.If(control == i, kind == "press", h) for i, h in enumerate(self.held))
            analog = tuple(z3.If(control == i, z3.RealVal(-1), a) if i in self.analog_controls else a
                           for i, a in enumerate(self.analog))
            event = (kind, control)
        elif kind == "analog":
            sample = z3.Real(f"{prefix}_sample")
            constraints.extend((_or(control == i for i in self.analog_controls), sample >= 0, sample <= 32767))
            held = tuple(z3.If(control == i, sample > 0, h) if i in self.analog_controls else h
                         for i, h in enumerate(self.held))
            analog = tuple(z3.If(control == i, sample, a) if i in self.analog_controls else a
                           for i, a in enumerate(self.analog))
            event = (kind, control, sample)
        constraints.extend((self.valid(held), self.valid_analog(held, analog)))
        release = kind in ("release", "analog")
        lookup_held = self.held if release else held
        lookup_analog = self.analog if release else analog
        choices, lookup_constraints = self._lookups(lookup_held, prefix)
        constraints.extend(lookup_constraints)
        entries = self._entries(lookup_held, lookup_analog, choices, release=release)
        context = (held, analog, tuple(constraints), event, control, sample, choices, tuple(entries))
        self._contexts[kind] = context
        return context

    def _compile(self, kind, layers=None):
        prefix = f"{self.prefix}_{kind}"
        if layers is not None:
            prefix += "_layers_" + "_".join(str(layer) for layer in sorted(layers))
        held, analog, common, event, control, sample, choices, entries = self._context(kind)
        constraints = list(common)
        release = kind in ("release", "analog")
        selected, operations, selection_records = [], [], []
        for entry, eligible in entries:
            if layers is not None and not any(target in layers for _, target in entry.ops):
                continue
            physical = canonical_control((entry.source, entry.input))
            if kind == "analog" and self.cid.get(physical) not in self.analog_controls:
                continue
            own = control == self.cid[physical] if physical in self.cid else z3.BoolVal(False)
            if release:
                take = _and(eligible, own)
                if kind == "analog":
                    take = _and(take, self.held[self.cid[physical]], sample == 0) if physical in self.cid else z3.BoolVal(False)
            else:
                if kind == "press" and entry.delay_start_ms:
                    continue
                take = z3.Bool(f"{prefix}_select_{len(selected)}")
                constraints.append(z3.Implies(take, eligible))
                if kind == "press":
                    constraints.append(z3.Implies(_and(own, eligible), take))
            selected.append(take)
            operations.append(entry.ops if layers is None else tuple((op, target) for op, target in entry.ops
                                                                      if target in layers))
            selection_records.append((entry.id, take))
        if kind == "automatic" and layers is None:
            constraints.append(_or(selected))
        order_groups = tuple((eid,) for eid, _ in selection_records)
        if layers is not None:
            groups, keys = [], {}
            for index, (ops, choice, (eid, _)) in enumerate(zip(operations, selected, selection_records)):
                if all(op == "r" for op, _ in ops):
                    targets = frozenset(target for _, target in ops if target)
                    key = ("remove", targets)
                    ops = tuple(("r", target) for target in sorted(targets))
                else:
                    key = ("entry", index)
                if key not in keys:
                    keys[key] = len(groups)
                    groups.append((ops, [], []))
                _, choices_in_group, entry_ids = groups[keys[key]]
                choices_in_group.append(choice)
                entry_ids.append(eid)
            operations = [ops for ops, _, _ in groups]
            selected = [_or(choices_in_group) for _, choices_in_group, _ in groups]
            order_groups = tuple(tuple(ids) for _, _, ids in groups)
        batch_constraints, ranks, orders = apply_batch(self.ranks, operations, selected, prefix)
        constraints.append(batch_constraints)
        return EnvelopeTransition(_and(*constraints), tuple(ranks), tuple(held), tuple(analog),
                                  kind, event, tuple(selection_records), tuple(choices.items()), tuple(orders), layers,
                                  order_groups)

    def transitions(self):
        if self._compiled is None:
            self._compiled = tuple(self._compile(kind) for kind in ("press", "release", "analog", "automatic"))
        return iter(self._compiled)

    def project_transitions(self, layers):
        """Relations sufficient for predicates over these layers and held state.

        Eligibility still reads the complete input stack.  Only batch effects
        are projected: irrelevant operations and entries are deleted, retaining
        the order of the remaining commands and entries.  This preserves the
        presence and relative order of the requested layers.  Their numeric
        ranks may be renumbered, just as in ordinary stack normalization.

        Identical pure-removal target sets share one representative selected
        by the OR of their original selections.  Retain the last such entry:
        earlier identical removals cannot affect final presence/order because
        selection is frozen and the last removal erases their targets again.
        Conversely, insert selected duplicates next to the representative to
        recover an original order.  Adds are never grouped by this rule.
        ``selected`` retains all original entry records; ``order_groups`` maps
        each returned order variable to its represented original entry IDs.

        Other output ranks are placeholders equal to their inputs and MUST NOT
        be used to establish predicates about nonprojected layers.  Invariants
        over any input layer remain valid hypotheses.  Automatic stutters are
        included because a concrete batch may affect only omitted layers.
        """
        layers = frozenset(layers)
        if any(type(layer) is not int or not 0 <= layer < self.n for layer in layers):
            raise ValueError("projection layers must be valid integer layer IDs")
        if layers not in self._projections:
            self._projections[layers] = tuple(self._compile(kind, layers) for kind in
                                               ("press", "release", "analog", "automatic"))
        return iter(self._projections[layers])


SymbolicTimedEnvelope = TimedEnvelope
