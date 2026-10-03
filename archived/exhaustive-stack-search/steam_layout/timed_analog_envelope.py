"""Production compiler that executes a positive analog sample's first batch.

Production certificates include this module. It does not change TimedModel
or sensor geometry.
"""
from dataclasses import replace

import z3

from .held_model import ALWAYS
from .symbolic_batch import apply_batch
from .timed_elapsed_envelope import TimedElapsedEnvelope
from .timed_envelope import EnvelopeTransition, _and, _or
from .timed_spec import canonical_control


class TimedAnalogEnvelope(TimedElapsedEnvelope):
    """Retain the mandatory immediate batch of every positive analog sample.

    A public event starts quiescent. A positive sample only adds or preserves
    held membership, so existing shifts' positive conditions remain true.
    The first refresh therefore has the same stack and binding lookups as
    before the sample. Every newly eligible zero-delay entry was already
    bound and becomes due now; every previously eligible activation remains
    done or in the future. Equal fingerprints include the raw input, so an
    unchanged binding cannot transfer a different owner's activation into a
    newly eligible entry. All new entries execute together in every order.

    Zero samples retain the original mandatory release-command prefix. An
    inverted Soft_Press can become newly eligible there, so its immediate
    activation remains allowed in subsequent automatic batches.

    Non-Always positive chords and unconditional Full_Press one-shots can now
    be forbidden in automatic batches even when a control has Soft_Press
    occurrences. Their own held/positive chord conditions can become true
    only on a physical press or positive sample, both handled atomically.
    Releases only shrink held membership; later exposure while held suppresses
    immediate one-shots. The same family criteria classify repeating versions
    as elapsed-only in automatic batches: exposure schedules a future period.
    Whole-fingerprint unconditional checks still exclude release-unblock Full
    activations, and Soft_Press and Always On entries retain their exceptions.
    """

    KINDS = ("press", "release", "analog_positive", "analog_zero", "automatic")

    def _unconditional_press_only(self, entry):
        control = (entry.source, entry.input)
        return (entry.kind == "Full_Press" and entry.delay_start_ms == 0
                and entry.repeat_ms is None and control != ALWAYS
                and (not entry.interruptible or not any(
                    other.kind == "chord"
                    for other in self.spec.bindings[(entry.owner, control)])))

    def _chord_press_only(self, entry):
        return (entry.kind == "chord" and entry.delay_start_ms == 0
                and entry.repeat_ms is None
                and canonical_control((entry.source, entry.input)) != ALWAYS)

    def _compile(self, kind, layers=None):
        if kind == "analog_zero":
            transition = super()._compile("analog", layers)
            sample = self._context("analog")[5]
            return replace(transition, label=kind, guard=_and(transition.guard, sample == 0))
        if kind != "analog_positive":
            return super()._compile(kind, layers)

        held, analog, common, event, control, sample, choices, _ = self._context("analog")
        prefix = f"{self.prefix}_{kind}"
        if layers is not None:
            prefix += "_layers_" + "_".join(str(layer) for layer in sorted(layers))
        if not hasattr(self, "_positive_analog_entries"):
            before = {entry.id: eligible for entry, eligible in
                      self._entries(self.held, self.analog, choices)}
            self._positive_analog_entries = tuple(
                (entry, _and(eligible, z3.Not(before[entry.id])))
                for entry, eligible in self._entries(held, analog, choices)
                if entry.delay_start_ms == 0)
        operations, selections, records = [], [], []
        for entry, selected in self._positive_analog_entries:
            if layers is not None and not any(target in layers for _, target in entry.ops):
                continue
            records.append((entry.id, selected))
            selections.append(selected)
            operations.append(entry.ops if layers is None else tuple(
                (op, target) for op, target in entry.ops if target in layers))
        order_groups = tuple((eid,) for eid, _ in records)
        if layers is not None:
            # As in TimedEnvelope, identical pure removals can share their
            # last occurrence. Keep original records for replay diagnostics.
            groups, keys = [], {}
            for index, (ops, selected, (eid, _)) in enumerate(zip(operations, selections, records)):
                if all(op == "r" for op, _ in ops):
                    targets = frozenset(target for _, target in ops if target)
                    key = ("remove", targets)
                    ops = tuple(("r", target) for target in sorted(targets))
                else:
                    key = ("entry", index)
                if key not in keys:
                    keys[key] = len(groups)
                    groups.append((ops, [], []))
                _, selected_group, entry_ids = groups[keys[key]]
                selected_group.append(selected)
                entry_ids.append(eid)
            operations = [ops for ops, _, _ in groups]
            selections = [_or(group) for _, group, _ in groups]
            order_groups = tuple(tuple(ids) for _, _, ids in groups)
        constraints, ranks, orders = apply_batch(self.ranks, operations, selections, prefix)
        return EnvelopeTransition(
            _and(*common, sample > 0, constraints), tuple(ranks), tuple(held), tuple(analog),
            kind, event, tuple(records), tuple(choices.items()), tuple(orders), layers, order_groups)

    def transitions(self):
        if self._compiled is None:
            self._compiled = tuple(self._compile(kind) for kind in self.KINDS)
        return iter(self._compiled)

    def project_transitions(self, layers):
        """Keep all pre-state guards and project only the batch's layer effects."""
        layers = frozenset(layers)
        if any(type(layer) is not int or not 0 <= layer < self.n for layer in layers):
            raise ValueError("projection layers must be valid integer layer IDs")
        if layers not in self._projections:
            self._projections[layers] = tuple(self._compile(kind, layers) for kind in self.KINDS)
        return iter(self._projections[layers])
