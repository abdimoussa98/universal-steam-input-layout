"""Differential checks for atomic symbolic batches, including every order."""
import importlib.util
import itertools
import random
import unittest

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.symbolic_batch import apply_batch


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class SymbolicBatchTests(unittest.TestCase):
    @staticmethod
    def concrete(stack, opslists, order):
        stack = list(stack)
        for entry in order:
            for op, target in opslists[entry]:
                if target == 0:
                    continue
                if op == "r" and target in stack:
                    stack.remove(target)
                elif op == "a" and target not in stack:
                    stack.append(target)
        return tuple(stack)

    def compare(self, n, stack, opslists):
        ranks = tuple(z3.Int(f"r_{i}") for i in range(n))
        choices = tuple(z3.Bool(f"s_{i}") for i in range(len(opslists)))
        relation, output, orders = apply_batch(ranks, opslists, choices, "batch")
        solver = z3.Solver()
        solver.add(relation)
        solver.add(*(rank == (stack.index(i) + 1 if i in stack else 0)
                     for i, rank in enumerate(ranks)))
        for bits in itertools.product((False, True), repeat=len(opslists)):
            chosen = [i for i, bit in enumerate(bits) if bit]
            expected = {self.concrete(stack, opslists, order)
                        for order in itertools.permutations(chosen)}
            solver.push()
            solver.add(*(choice == bit for choice, bit in zip(choices, bits)))
            actual = set()
            while solver.check() == z3.sat:
                model = solver.model()
                values = [model.eval(rank).as_long() for rank in output]
                reached = tuple(sorted((i for i, rank in enumerate(values) if rank > 0),
                                       key=values.__getitem__))
                self.assertNotIn(reached, actual)
                self.assertIn(reached, expected, (stack, opslists, bits))
                actual.add(reached)
                # Block this represented stack, not its noncanonical rank
                # values: order-variable gaps can encode the same stack.
                same = [rank > 0 if i in reached else rank == 0
                        for i, rank in enumerate(output)]
                same.extend(output[a] < output[b] for a, b in zip(reached, reached[1:]))
                solver.add(z3.Not(z3.And(*same)))
            self.assertEqual(actual, expected, (stack, opslists, bits))
            solver.pop()
        return relation, output, orders

    def test_empty_batch_and_empty_entries(self):
        self.compare(3, (0, 2), ())
        self.compare(3, (0, 2), ((), (), ()))

    def test_add_remove_add_and_immutable_base(self):
        ops = ((('a', 1), ('r', 1), ('a', 1)),
               (('a', 2), ('r', 0), ('a', 0)),
               (('r', 1), ('a', 3)))
        for stack in ((0,), (0, 1), (0, 2, 1), (0, 3, 1, 2)):
            self.compare(4, stack, ops)

    def test_readding_existing_layer_keeps_position(self):
        self.compare(4, (0, 2, 1), ((('a', 2), ('a', 3)),
                                  (('r', 1), ('a', 1)), (('a', 2),)))

    def test_entry_commands_cannot_interleave(self):
        # Interleaving these entries could leave only Base, whereas either
        # whole-entry order leaves exactly one of the two other layers.
        self.compare(3, (0,), ((('a', 1), ('r', 2)), (('a', 2), ('r', 1))))

    def test_pure_removal_targets_keep_exact_presence_without_add_timestamps(self):
        self.compare(4, (0, 3, 1, 2), ((('r', 1),), (('r', 2),),
                                      (('r', 1), ('r', 3)), (('r', 2),)))
        # A removal-only target also commutes beside targets with additions.
        self.compare(4, (0, 2, 3), ((('r', 2), ('a', 1)), (('r', 2), ('r', 1)),
                                   (('a', 3), ('a', 1))))

    def test_many_extremum_candidates_preserve_all_selected_orders(self):
        ops = ((('a', 1),), (('r', 1),), (('a', 2), ('a', 1)),
               (('r', 2), ('r', 1)), (('a', 1), ('a', 3)), (('r', 3),))
        for stack in ((0,), (0, 3, 1, 2)):
            self.compare(4, stack, ops)

    def test_random_batches_every_subset_and_permutation(self):
        rng = random.Random(9302026)
        for _ in range(24):
            n = rng.randrange(2, 6)
            active = rng.sample(range(1, n), rng.randrange(n))
            ops = tuple(tuple((rng.choice(('a', 'r')), rng.randrange(n))
                              for _ in range(rng.randrange(5)))
                        for _ in range(rng.randrange(1, 5)))
            self.compare(n, (0, *active), ops)

    def test_order_domain_and_frozen_selection(self):
        ranks = tuple(z3.Int(f"rank_{i}") for i in range(3))
        selected = (ranks[1] == 0, ranks[1] > 0, z3.BoolVal(True))
        relation, output, orders = apply_batch(
            ranks, ((('a', 1),), (('a', 2),), ()), selected, 'frozen')
        solver = z3.Solver()
        solver.add(relation, ranks[0] == 1, ranks[1] == 0, ranks[2] == 0)
        solver.add(z3.Or(output[1] <= 0, output[2] != 0, orders[1] != 0,
                         orders[0] < 1, orders[0] > 3, orders[0] == orders[2]))
        self.assertEqual(solver.check(), z3.unsat)

    def test_invalid_inputs_fail(self):
        with self.assertRaises(ValueError):
            apply_batch((), (), (), 'empty')
        with self.assertRaises(ValueError):
            apply_batch((z3.IntVal(1),), ((),), (), 'length')
        with self.assertRaises(TypeError):
            apply_batch((z3.Real('r'),), (), (), 'real')
        with self.assertRaises(TypeError):
            apply_batch((z3.IntVal(1),), ((),), (z3.IntVal(1),), 'selection')
        for op in (('x', 0), ('a', 1), ('r', True)):
            with self.assertRaises(ValueError):
                apply_batch((z3.IntVal(1),), ((op,),), (z3.BoolVal(True),), 'op')
