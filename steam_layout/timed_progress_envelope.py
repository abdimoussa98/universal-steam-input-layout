"""Production compiler with ordered-owner progress restrictions on timed batches.

These restrictions follow the recorded runtime contract; they do not change
the simulator. Production certificates include this module in their identity.
"""
from collections import defaultdict
from dataclasses import dataclass, replace

import z3

from .held_model import ALWAYS
from .timed_phase_envelope import TimedPhaseEnvelope
from .timed_spec import canonical_control


@dataclass(frozen=True)
class ProgressRule:
    delayed: str
    repeater: str
    delayed_owners: tuple
    adds: tuple
    removes: bool


class TimedProgressEnvelope(TimedPhaseEnvelope):
    """Require a faster repeater to make progress before a delayed firing.

    Let D be a delayed one-shot and R a zero-delay repeater with period P less
    than D's delay.  Every occurrence of their fingerprints must have a numeric
    owner, and D's raw source must have no mode shifts.  R's source must either
    be unshifted or have every shift origin physically incompatible with D and
    R remaining held together.  Whenever R is eligible
    and every PRESENT D-family owner is at or above R's owner, D cannot fire if
    R removes any layer or if any layer added by R is absent.

    At batch-selection points, while the eligibility, owner-order and
    removal-or-absent-target conditions hold and D is pending,
    D.deadline > R.deadline.  R's remaining time is at most P.  A batch firing R
    either removes something (resetting pending D) or makes every added target
    present.  Making one absent again requires another removal/reset.  New D
    activations are fresh; fingerprint transfers preserve the old activation.

    A newly eligible R in its previous binding fires immediately.  Exposing a
    new R binding without a removal requires adding its owner.  Any older D
    owner then lies below it, making the order condition false.  Transferring
    an aged D to a new upper owner does not erase that older owner.  Removing
    the older owner resets D.  These facts also cover R fingerprint transfer;
    no singleton-family assumption is needed.  Source-shift exclusions ensure
    that a new binding cannot appear through a shift ending without a removal
    while an aged D and held R both persist.
    """

    def __init__(self, runtime, prefix="timed_progress_envelope"):
        super().__init__(runtime, prefix)
        families = defaultdict(list)
        for entry in self.spec.entries.values():
            families[entry.fingerprint].append(entry)
        normal = [entries for entries in families.values()
                  if all(isinstance(entry.owner, int) for entry in entries)]
        delayed = [entries for entries in normal
                   if entries[0].delay_start_ms > 0 and entries[0].repeat_ms is None
                   and entries[0].kind != "release" and entries[0].ops
                   and entries[0].source not in self._shift_groups]
        repeating = [entry for entries in normal for entry in entries
                     if entry.delay_start_ms == 0 and entry.repeat_ms is not None
                     and entry.kind != "release" and entry.ops]
        self._shift_compatibility = {}
        self.progress_rules = tuple(
            ProgressRule(entry.id, repeater.id, tuple(sorted({e.owner for e in entries})),
                         tuple(sorted({target for op, target in repeater.ops if op == "a" and target})),
                         any(op == "r" for op, _ in repeater.ops))
            for entries in delayed for entry in entries
            for repeater in repeating if entry.delay_start_ms > repeater.repeat_ms
            and self._safe_repeater_source(entry, repeater))

    def _safe_repeater_source(self, delayed, repeater):
        if repeater.source not in self._shift_groups:
            return True
        controls = tuple(canonical_control((entry.source, entry.input))
                         for entry in (delayed, repeater))
        if (any(entry.kind == "Soft_Press" for entry in (delayed, repeater))
                or any(control == ALWAYS or control not in self.cid for control in controls)):
            return False
        key = (*controls, repeater.source)
        if key not in self._shift_compatibility:
            safe = True
            for group in self._shift_groups[repeater.source]:
                for origin in self._shift_origins[(repeater.source, group)]:
                    control = canonical_control((origin.source, origin.input))
                    if control not in self.cid:
                        safe = False
                        break
                    required = {*controls, control}
                    # A missing touch is repairable, so testing the bare triple
                    # would wrongly call a compatible combination impossible.
                    # Close dependencies first.  All remaining _valid failures
                    # are conflicts that no larger held set can repair.
                    for source, name in tuple(required):
                        if source.endswith(("joystick", "trackpad")) and name != "touch":
                            if (source, "touch") in self.cid:
                                required.add((source, "touch"))
                        if source.endswith("trigger") and name == "click":
                            if (source, "edge") in self.cid:
                                required.add((source, "edge"))
                    if self.runtime._valid(frozenset(required)):
                        safe = False
                        break
                if not safe:
                    break
            self._shift_compatibility[key] = safe
        return self._shift_compatibility[key]

    def _compile(self, kind, layers=None):
        transition = super()._compile(kind, layers)
        if kind != "automatic":
            return transition
        selected = dict(transition.selected)
        eligible = {entry.id: guard for entry, guard in self._context(kind)[-1]}
        conditions = [transition.guard]
        for rule in self.progress_rules:
            if rule.delayed not in selected:
                continue
            owner = self.spec.entries[rule.repeater].owner
            order = z3.And(*(z3.Or(self.ranks[other] == 0, self.ranks[other] >= self.ranks[owner])
                             for other in rule.delayed_owners))
            incomplete = (z3.BoolVal(True) if rule.removes else
                          z3.Or(*(self.ranks[target] == 0 for target in rule.adds)))
            conditions.append(z3.Not(z3.And(selected[rule.delayed], eligible[rule.repeater],
                                             order, incomplete)))
        return replace(transition, guard=z3.And(*conditions))
