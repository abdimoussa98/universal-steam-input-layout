"""Exact relevance projection for layer-stack reachability.

The observable is the full ordered layer stack, hence every inherited binding
derived from it. Keyboard/mouse output and physical held-state reporting are
not observables of this projection. See ``LayerRelevance`` for the argument.
"""
from dataclasses import replace
from decimal import Decimal
import hashlib
from itertools import groupby
from pathlib import Path

from .held_model import ALWAYS
from .timed_search import TimedQuotient
from .timed_spec import canonical_control, chord_selectors
from .timed_trace import parse_trace


class LayerRelevance:
    """Discard inputs that cannot affect present or future layer operations.

    Retain every control with a layer command or mode shift in any binding,
    including hidden layers and recursively parsed shift groups. Retain chord
    selectors used by those commands and by otherwise inert chords that can
    interrupt a regular command. Finally retain physical touch/edge parents.

    A discarded input cannot alter eligibility, timers, shifts, or the stack.
    Its press/release can only restrict physical events. Erasing it preserves
    validity because every retained child's parent is retained. Each concrete
    path projects to a path with these inert events omitted; each projected
    path is concrete with discarded inputs always released. This is exact for
    stack reachability, not the set of all physical input traces.

    Activation.fired is erased independently: no transition reads that field.
    Activation identities/stages remain because they control rearming and
    suppression when a held binding is exposed.

    Shift priority only compares shifts of the same source. Their relative
    order is retained except within consecutive runs selecting the same group,
    where every surviving member selects identical bindings. Reordering these
    runs does not affect binding selection or the exact-shift membership test
    used when executing a new shift.
    """

    def __init__(self, model):
        self.model = model
        retained = set()
        relevant_soft = []
        for entries in model.spec.bindings.values():
            effectful = [entry for entry in entries if entry.ops or entry.shifts]
            can_interrupt = any(entry.kind == "Full_Press" and entry.interruptible
                                for entry in effectful)
            for entry in entries:
                relevant = entry in effectful
                blocker = entry.kind == "chord" and can_interrupt
                if not relevant and not blocker:
                    continue
                retained.add(canonical_control((entry.source, entry.input)))
                # A Soft Press without a numeric threshold already depends
                # only on held membership (including the inverted case).
                # Explicit zero samples and missing samples are equivalent.
                if relevant and entry.kind == "Soft_Press" and entry.threshold is not None:
                    relevant_soft.append(entry)
                if entry.chord:
                    _, selectors = chord_selectors(dict(entry.chord), entry.id)
                    for selector in selectors:
                        if isinstance(selector, str):
                            kind, source = selector.split(":", 1)
                            if kind == "pad":
                                retained.add((source, "touch"))
                            else:
                                retained.update(control for control in model.controls
                                                if control[0] == source and
                                                control[1] not in ("touch", "click"))
                        else:
                            retained.update(canonical_control(control) for control in selector)
        for source, name in tuple(retained):
            if source.endswith(("joystick", "trackpad")) and name != "touch":
                parent = (source, "touch")
            elif source.endswith("trigger") and name == "click":
                parent = (source, "edge")
            else:
                continue
            if parent in model.controls:
                retained.add(parent)
        retained.discard(ALWAYS)
        self.controls = tuple(sorted(retained & model.controls))
        self.retained = frozenset(self.controls)
        self.discarded = model.controls - self.retained
        bounds = {}
        for entry in relevant_soft:
            control = canonical_control((entry.source, entry.input))
            values = bounds.setdefault(control, {Decimal(0), Decimal(32767)})
            if entry.threshold is not None and 0 <= entry.threshold <= 32767:
                values.add(entry.threshold)
        self.analog_regions = {control: tuple(sorted(values))
                               for control, values in sorted(bounds.items())}
        self.identity = {
            "projection": "layer-relevance-v1",
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "observable": "full ordered layer stack and inherited binding owners",
            "retained_controls": [list(control) for control in self.controls],
            "discarded_controls": [list(control) for control in sorted(self.discarded)],
            "erase_fired": True,
            "shift_order": "source-local priority; sorted equal-group runs",
            "analog_regions": [{"control": list(control),
                                "representatives": [str(value) for value in values]}
                               for control, values in self.analog_regions.items()],
        }

    def normalize(self, state):
        """Project a settled state, without modifying its clock origin."""
        analog = []
        for control, value in state.analog_values:
            control = canonical_control(control)
            if control not in self.analog_regions:
                continue
            representative = next(bound for bound in self.analog_regions[control]
                                  if value <= bound)
            analog.append((control, representative))
        shifts = []
        # Stable source sorting retains the chronological priority within each
        # source. Only identical-group runs may then exchange their members.
        for _, run in groupby(sorted(state.shifts, key=lambda shift: shift.source),
                              key=lambda shift: (shift.source, shift.group)):
            shifts.extend(sorted(run, key=lambda shift: (shift.control, shift.entry_id)))
        return replace(state, held=state.held & self.retained,
                       analog_values=tuple(sorted(analog)),
                       activations=tuple(replace(a, fired=False) for a in state.activations),
                       shifts=tuple(shifts))


class ReducedTimedQuotient(TimedQuotient):
    """Search-compatible exact quotient for ordered-stack observables.

    Clock and full analog normalization run through an unchanged reference
    TimedQuotient before relevance projection. Successors use the smaller
    event alphabet; every omitted event either stutters or is represented by a
    retained digital event. Search stores are identified separately, so a full
    quotient database cannot accidentally be resumed with this quotient.

    This preserves stack reachability, not physical held-state snapshots or
    output-key histories. Replay traces mentioning discarded controls through
    ``reference`` first and project the resulting states with ``normalize``.
    """

    def __init__(self, model):
        if model.semantics.get("version") != "timed-layer-replay-v1":
            raise ValueError("layer relevance requires the reviewed timed-layer-replay-v1 contract")
        self.reference = TimedQuotient(model)
        self.model = model
        self.relevance = LayerRelevance(model)
        self.controls = self.relevance.controls
        self.analog_regions = self.relevance.analog_regions
        implementation = hashlib.sha256()
        implementation.update(self.reference.identity["implementation_sha256"].encode("ascii"))
        implementation.update(self.relevance.identity["implementation_sha256"].encode("ascii"))
        self.identity = {
            **self.reference.identity,
            "quotient": "relative-clocks-layer-relevance-v1",
            "implementation_sha256": implementation.hexdigest(),
            "reference_quotient": self.reference.identity,
            "reduction": self.relevance.identity,
            "controls": [list(control) for control in self.controls],
            "analog_regions": self.relevance.identity["analog_regions"],
        }

    def normalize(self, state):
        return self.relevance.normalize(self.reference.normalize(state))

    def step(self, state, event):
        event = parse_trace([event])[0]
        operation, value = next(iter(event.items()))
        if operation != "wait_ms":
            control = canonical_control(value["control"] if operation == "analog" else value)
            if control not in self.relevance.retained:
                raise ValueError("control is outside the reduced event alphabet; "
                                 "replay the full trace through reference before projection")
        return super().step(state, event)
