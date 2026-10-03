"""Production compiler separating elapsed repeats from immediate activations.

Production certificates include this module. It does not change the concrete
timed runtime.
"""
from collections import defaultdict
from dataclasses import replace

import z3

from .timed_progress_envelope import TimedProgressEnvelope
from .timed_spec import canonical_control


class TimedElapsedEnvelope(TimedProgressEnvelope):
    """Qualifying automatic repeats cannot share a new one-shot's batch.

    An unconditional Full_Press or positive chord whose complete fingerprint
    family satisfies the press-only criteria can start immediately only in a
    first physical-press batch.  For a repeating entry, later exposure while
    held waits a full interval, and activation transfer retains the already
    advanced deadline.  Its automatic firings therefore require elapsed time.

    A zero-delay nonrepeating entry is due only when created.  The runtime
    advances every old due activation before executing the batch and exposing
    new entries.  Thus an elapsed repeat cannot share an automatic batch with
    a newly created zero-delay one-shot.  Their first press batch may contain
    both.  Analog supports and Always On remain exempt, as in the parent
    press-only criteria; complete fingerprint closure excludes release-unblock
    activations transferred from a conditional Full_Press occurrence.
    """

    def __init__(self, runtime, prefix="timed_elapsed_envelope"):
        super().__init__(runtime, prefix)
        families = defaultdict(list)
        for entry in self.spec.entries.values():
            families[entry.fingerprint].append(entry)
        self.elapsed_full_entries = frozenset(
            entry.id
            for entries in families.values()
            if all(entry.repeat_ms is not None and self._unconditional_press_only(
                replace(entry, repeat_ms=None)) for entry in entries)
            for entry in entries)
        self.elapsed_chord_entries = frozenset(
            entry.id
            for entries in families.values()
            if all(entry.repeat_ms is not None and self._chord_press_only(
                replace(entry, repeat_ms=None)) for entry in entries)
            for entry in entries)

    def _compile(self, kind, layers=None):
        transition = super()._compile(kind, layers)
        conditions = [transition.guard]
        if kind == "automatic":
            immediate_once = z3.Or(*(take for eid, take in transition.selected
                                     if self.spec.entries[eid].delay_start_ms == 0
                                     and self.spec.entries[eid].repeat_ms is None))
            elapsed_repeat = z3.Or(*(take for eid, take in transition.selected
                                     if eid in self.elapsed_full_entries
                                     or eid in self.elapsed_chord_entries))
            conditions.append(z3.Not(z3.And(immediate_once, elapsed_repeat)))
        elif kind == "press":
            conditions.extend(z3.Implies(
                take, transition.event[1] == self.cid[canonical_control(
                    (self.spec.entries[eid].source, self.spec.entries[eid].input))])
                for eid, take in transition.selected if eid in self.elapsed_full_entries)
        return replace(transition, guard=z3.And(*conditions))
