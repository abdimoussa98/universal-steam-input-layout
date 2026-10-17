# The Entry Point stays under Fn: Ibex 1.2, Neptune 90.78 and DSE 1.2

Built on 2026-10-17 from the **Ibex 1.0** snapshot, both variants, as Ibex 1.1
less one thing ([build_candidate.py](build_candidate.py), which runs
[1.1's builder](../2026-10-16-fn-right-stick-owner/build_candidate.py)).
Device status: **the fix seen on the Deck** by the author, 2026-10-17, on 90.78: "just tested and seems to have resolved it".

| Release | What it is | Removes, adds (default; alternative) |
|---|---|---|
| ibex 1.2 | This folder's builder | 2,973, 477; 3,031, 477 (1.1: 2,881, 477; 2,939, 477) |
| neptune 90.78 | `python3 -m tools.convert neptune --version 90.78` | as Ibex 1.2 |
| dse 1.2 | `python3 -m tools.convert dse` | 1,777, 381; 1,835, 381 (1.1: 1,689, 381; 1,747, 381) |

## Why

On the Deck, 90.77 (the author, 2026-10-17): hold Start; within the 200 ms push
a stick, so the stick guard lands; then the next time Start is held, the Fn
layer comes on at once. 90.76 doesn't do it. The author: "My assumuption is its
the hand over so 3. I think the issue is we are removing the entry point layer.
i think everything else is fine".

The guard binds the menu buttons, so it eats the Entry Point's 200 ms delayed
chord (A15). On 1.0 the Entry Point then stayed under Fn until the menu
button's Release. In 1.1 every bind that adds an Fn layer also removed its
Entry Point (the hand-over), so the stick-touch Release that brings Fn in when
the guard leaves removed the layer whose delay had just been eaten. After that
the next delay fired at once, a delay going stale under a removal (A12, A13).
The simulator doesn't model that: there the next hold waits its 200 ms on 90.77
too.

## The change

Six removes for each of the four menu Entry Points, the ones 1.1's hand-over
added, in the binds that add its Fn layer:

- the 200 ms chord on its menu button;
- the chord on the other menu button;
- the two stick-touch Releases;
- the two stick-click presses, which still remove both guards and the Tap
  Cover.

The fix pipeline then keeps the Fn layers' cleanups of their Entry Point (1.1
had dropped them, since the Entry Point couldn't be under Fn). That gives 14
layers changed per layout (the change reports here: 140 changes on Ibex and
Neptune, 120 on the Edge). Once the Entry Point removes are set aside, the
binds are the same as 1.1's, compared bind by bind.

Everything else of 1.1 stays. The right stick is still Fn's to answer (A77):
the Entry Point under Fn is in Base's mouse mode on that stick, as are the
guards and the Tap Cover, so no D-pad sits under Fn's D-pad. The chains confirm
it in every stack under each Fn layer: 524 under each plain Fn layer, 30 under
each Stateful one.

## Tests

- **`test_fn_right_stick_owner`** now checks only the right stick: no stack
  puts a D-pad under an Fn layer. It still fails on 1.0.
- **The 1.1 scenarios** check that each Fn adder lands Fn over its Entry Point,
  with no guard or Tap Cover.
- **The five scenario files and `test_neptune_held_inputs`**, which 1.1 had
  changed to the hand-over, are back as they were before 1.1.
- **The new scenario `ibex 1.2 G1`** (`tests/scenarios/ibex/test_scenarios_ibex_1_2.py`)
  is the gesture from the Deck: the Entry Point stays under Fn after the guard,
  and the next hold waits.

## On the Deck

Confirm the title shows `:: 90.78`. Hold Start, push the left stick within the
first half second, let it come back and lift the thumb, let go of Start. Hold
Start again: Fn should come in after half a second, not at once. Then do the
same with the right stick and with Select.
