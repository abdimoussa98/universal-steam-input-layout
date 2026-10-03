"""Polynomial-size symbolic execution of an atomic, unordered entry batch.

Positive integer ranks encode stack order and zero means absent. Input ranks
must describe a stack with ranks at most ``len(ranks)`` and immutable Base at
index zero. Outputs may have gaps or exceed that bound: canonical renumbering
preserves presence and every relative-order predicate.

Selection is supplied by the caller and evaluated against its frozen input
snapshot. Selected entries execute in an arbitrary order; the operations
inside each entry execute consecutively in their supplied order. The relation
encodes all such orders without enumerating permutations or selected subsets.
It does not model intermediate entry or command states as observable states.
"""

import z3


def apply_batch(ranks, opslists, selected, prefix):
    """Return ``(constraints, output_ranks, order_variables)`` for a batch.

    ``opslists[i]`` contains ``("a", target)`` and ``("r", target)`` commands
    for entry ``i``. ``selected[i]`` is a Boolean expression over the caller's
    input state. Entry order variables range from one through the number of
    entries when selected and equal zero otherwise. Distinct positive order
    values leave every selected permutation possible, including orders with
    gaps. ``prefix`` must be unique within the caller's symbolic relation.

    The returned constraints include auxiliary integer timestamps. No stack
    domain constraints are added: the caller supplies the input-stack domain.
    Base commands have no effect, so Base's input rank is always preserved.
    """
    ranks, opslists, selected = tuple(ranks), tuple(opslists), tuple(selected)
    if not ranks:
        raise ValueError("ranks must include Base at index zero")
    if len(opslists) != len(selected):
        raise ValueError("one selection expression is required per entry")
    if any(not z3.is_int(rank) for rank in ranks):
        raise TypeError("stack ranks must be Z3 integer expressions")
    if any(not z3.is_bool(choice) for choice in selected):
        raise TypeError("entry selections must be Z3 Boolean expressions")
    opslists = tuple(tuple(ops) for ops in opslists)
    for ops in opslists:
        for op, target in ops:
            if op not in ("a", "r"):
                raise ValueError(f"unknown layer operation: {op!r}")
            if type(target) is not int or not 0 <= target < len(ranks):
                raise ValueError(f"invalid layer target: {target!r}")

    count = len(opslists)
    orders = tuple(z3.Int(f"{prefix}_order_{i}") for i in range(count))
    constraints = [z3.If(choice, z3.And(order >= 1, order <= count), order == 0)
                   for choice, order in zip(selected, orders)]
    if count > 1:
        constraints.append(z3.Distinct(*(z3.If(choice, order, -i - 1)
                                         for i, (choice, order) in
                                         enumerate(zip(selected, orders)))))

    stride = max((len(ops) for ops in opslists), default=0) + 1
    sentinel = (count + 1) * stride
    additions, removals = {}, {}
    for choice, order, ops in zip(selected, orders, opslists):
        for position, (op, target) in enumerate(ops, 1):
            if target == 0:
                continue
            timestamp = order * stride + position
            table = additions if op == "a" else removals
            table.setdefault(target, []).append((choice, timestamp))

    outputs = list(ranks)
    for target in sorted(additions.keys() | removals.keys()):
        removed = removals.get(target, ())
        added = additions.get(target, ())
        if not added:
            # No addition can compete with these removals, so entry order is
            # irrelevant to this target.  Preserve the complete order relation
            # above for other targets and for callers inspecting order values.
            choices = {choice.get_id(): choice for choice, _ in removed}
            outputs[target] = z3.If(z3.Or(*choices.values()), 0, ranks[target])
            continue
        if not removed:
            last_remove = z3.IntVal(0)
        elif len(removed) == 1:
            choice, timestamp = removed[0]
            last_remove = z3.If(choice, timestamp, 0)
        else:
            # Characterize the maximum directly.  The disjunction supplies a
            # witness; the bounds make it the last selected removal.  This is
            # equivalent to a nested conditional maximum but does not create
            # a long chain of dependent comparison expressions.
            last_remove = z3.Int(f"{prefix}_last_remove_{target}")
            constraints.append(z3.Or(last_remove == 0, *(z3.And(choice, last_remove == timestamp)
                                                        for choice, timestamp in removed)))
            constraints.extend(z3.Implies(choice, last_remove >= timestamp) for choice, timestamp in removed)

        if len(added) == 1:
            choice, timestamp = added[0]
            first_add = z3.If(z3.And(choice, timestamp > last_remove), timestamp, sentinel)
        else:
            # Likewise, the first surviving add is the minimum selected add
            # timestamp after the last removal, or the out-of-range sentinel.
            first_add = z3.Int(f"{prefix}_first_add_{target}")
            surviving = [(z3.And(choice, timestamp > last_remove), timestamp) for choice, timestamp in added]
            constraints.append(z3.Or(first_add == sentinel, *(z3.And(valid, first_add == timestamp)
                                                              for valid, timestamp in surviving)))
            constraints.extend(z3.Implies(valid, first_add <= timestamp) for valid, timestamp in surviving)

        # A retained layer keeps its original place. Otherwise only adds after
        # the last removal survive, and the first such add fixes its place.
        outputs[target] = z3.If(
            z3.And(ranks[target] > 0, last_remove == 0), ranks[target],
            z3.If(first_add < sentinel, len(ranks) + first_add, 0))

    return z3.And(*constraints), tuple(outputs), orders
