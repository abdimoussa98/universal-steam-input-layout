"""History-free batch restrictions derived from the timed runtime's phases.

This strengthens TimedEnvelope without adding clocks or changing the
runtime.  Its extra restrictions concern reachable batches, not arbitrary
manually constructed TimedState objects.  TimedProof uses this compiler, and
production certificates include this module in their algorithm identity.
"""
from collections import defaultdict
from dataclasses import replace

import z3

from .held_model import ALWAYS
from .timed_envelope import TimedEnvelope
from .timed_spec import canonical_control, chord_selectors


class TimedPhaseEnvelope(TimedEnvelope):
    """Exclude impossible combinations of activation stages.

    A positive-delay entry cannot share a due batch with a zero-delay,
    nonrepeating entry.  The latter is due only at its creation instant;
    positive delays are created/reset strictly in the future.  _settle advances
    every currently due activation before executing or refreshing any of them.
    Thus a refresh cannot introduce a new immediate entry beside an old,
    still-due delayed entry.  Fingerprint transfer preserves those deadlines.

    An unconditional zero-delay nonrepeating Full_Press can fire only on its
    own rising edge.  An already held newly exposed binding is suppressed;
    an identical transferred activation remains completed.  This criterion
    must hold for EVERY occurrence of the fingerprint: an interruptible copy
    with a chord could otherwise become due on a different control's release
    and transfer to a locally unconditional copy before it executes.

    Always-on and analog-controlled entries are excluded from the second rule.
    The parent envelope represents analog activation in a separate automatic
    batch, and always-on binding exposure can create an immediate activation.

    A singleton delayed one-shot D cannot fire while a singleton zero-delay
    repeating remover R of the same numeric owner is eligible, when D's delay
    exceeds R's period and no mode shift targets R's raw source.  At batch
    selection, pending D and active R satisfy D.deadline > R.deadline.  Each
    R firing resets D.  A newly eligible, already bound R fires immediately;
    exposing a new R binding requires either adding its owner (D is fresh) or
    removing a blocker (D resets).  A layer add cannot expose an existing lower
    binding.  Singleton fingerprints prevent importing aged activation clocks.
    An eligible R always has a finite activation, and no deadline is in the
    past at reachable batch-selection points.  D due now would contradict the
    strict deadline inequality.  R's full eligibility guard is retained even
    when a projected batch omits all its layer effects.

    A physical press cannot fire an already eligible entry of another control:
    the preceding public state is quiescent and the press advances no time.
    Before its first batch it only changes held/analog state.  Existing shifts
    remain latched because their positive chord conditions remain true when a
    held control is added.  Reusing the same lookup choices for pre-eligibility
    therefore retains every concrete press batch, including newly true chords.
    Every newly eligible zero-delay entry must also fire: its unchanged binding
    was already selected, no exact old activation exists, and another owner
    cannot transfer a fingerprint while that binding remains unchanged.

    Zero-delay nonrepeating chords whose own control and every positive chord
    support are non-analog can fire only in that first press batch.  Releases
    cannot make a positive held condition become true; newly exposed bindings
    suppress one-shots; retained or transferred activations remain completed.
    Analog supports and always-on inputs are exempt because their immediate
    commands are represented in separate automatic prefix batches.  Unlike an
    unconditional Full_Press, a chord may be triggered by another control.
    """

    def __init__(self, runtime, prefix="timed_phase_envelope"):
        super().__init__(runtime, prefix)
        families = defaultdict(list)
        for entry in self.spec.entries.values():
            families[entry.fingerprint].append(entry)
        self.press_only_entries = frozenset(
            entry.id
            for entries in families.values()
            if all(self._unconditional_press_only(entry) for entry in entries)
            for entry in entries)
        self.chord_press_entries = frozenset(
            entry.id
            for entries in families.values()
            if all(self._chord_press_only(entry) for entry in entries)
            for entry in entries)
        singletons = [entries[0] for entries in families.values() if len(entries) == 1]
        removers = [entry for entry in singletons
                    if isinstance(entry.owner, int) and entry.delay_start_ms == 0
                    and entry.repeat_ms is not None
                    and any(op == "r" for op, _ in entry.ops)
                    and entry.source not in self._shift_groups]
        self.reset_starvation_pairs = tuple(sorted(
            (delayed.id, remover.id)
            for delayed in singletons
            if delayed.ops and isinstance(delayed.owner, int)
            and delayed.delay_start_ms > 0 and delayed.repeat_ms is None
            for remover in removers
            if delayed.owner == remover.owner
            and delayed.delay_start_ms > remover.repeat_ms))
        self._press_previous_eligibility = None

    def _unconditional_press_only(self, entry):
        control = (entry.source, entry.input)
        return (entry.kind == "Full_Press" and entry.delay_start_ms == 0
                and entry.repeat_ms is None and control != ALWAYS
                and self.cid[canonical_control(control)] not in self.analog_controls
                and (not entry.interruptible or not any(
                    other.kind == "chord"
                    for other in self.spec.bindings[(entry.owner, control)])))

    def _chord_press_only(self, entry):
        control = canonical_control((entry.source, entry.input))
        if (entry.kind != "chord" or entry.delay_start_ms != 0
                or entry.repeat_ms is not None or control == ALWAYS):
            return False
        supports = {control}
        if entry.chord:
            _, selectors = chord_selectors(dict(entry.chord), entry.id)
            for selector in selectors:
                if isinstance(selector, str):
                    kind, source = selector.split(":")
                    if kind == "pad":
                        supports.add((source, "touch"))
                    else:
                        supports.update(other for other in self.controls
                                        if other[0] == source and other[1] not in ("touch", "click"))
                else:
                    supports.update(canonical_control(other) for other in selector)
        return not any(control in self.cid and self.cid[control] in self.analog_controls
                       for control in supports)

    def _compile(self, kind, layers=None):
        transition = super()._compile(kind, layers)
        conditions = [transition.guard]
        if kind == "automatic":
            selected = dict(transition.selected)
            eligible = {entry.id: guard for entry, guard in self._context(kind)[-1]}
            positive = z3.Or(*(take for eid, take in transition.selected
                               if self.spec.entries[eid].delay_start_ms > 0))
            immediate_once = z3.Or(*(take for eid, take in transition.selected
                                     if self.spec.entries[eid].delay_start_ms == 0
                                     and self.spec.entries[eid].repeat_ms is None))
            conditions.append(z3.Not(z3.And(positive, immediate_once)))
            conditions.extend(z3.Not(take) for eid, take in transition.selected
                              if eid in self.press_only_entries or eid in self.chord_press_entries)
            conditions.extend(z3.Not(z3.And(selected[delayed], eligible[remover]))
                              for delayed, remover in self.reset_starvation_pairs
                              if delayed in selected)
        elif kind == "press":
            eligible = {entry.id: guard for entry, guard in self._context(kind)[-1]}
            if self._press_previous_eligibility is None:
                choices = self._context(kind)[6]
                self._press_previous_eligibility = {
                    entry.id: guard for entry, guard in self._entries(
                        self.held, self.analog, choices)}
            for eid, take in transition.selected:
                control = canonical_control((self.spec.entries[eid].source,
                                             self.spec.entries[eid].input))
                own = (transition.event[1] == self.cid[control] if control in self.cid
                       else z3.BoolVal(False))
                conditions.append(z3.Implies(take, z3.Or(
                    own, z3.Not(self._press_previous_eligibility[eid]))))
                conditions.append(z3.Implies(z3.And(
                    eligible[eid], z3.Not(self._press_previous_eligibility[eid])), take))
            conditions.extend(z3.Implies(
                take, transition.event[1] == self.cid[canonical_control(
                    (self.spec.entries[eid].source, self.spec.entries[eid].input))])
                for eid, take in transition.selected if eid in self.press_only_entries)
        return replace(transition, guard=z3.And(*conditions))
