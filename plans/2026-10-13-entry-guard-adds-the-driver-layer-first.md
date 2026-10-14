# Plan: the Entry Guard adds the driver's layer first, then removes itself

**Status, 2026-10-13:** built as **90.68**, from 90.67 (author: "Just do the order
change"; [release record](../findings/2026-10-13-entry-guard-adds-the-driver-layer-first/README.md)).
The question at the end stays open: the swap was built alone. Another
approach, the guard staying under the driver layers until the driver's
Release, was talked through and dropped by the author the same day.

The author, 2026-10-13: "the only change in this one is in the steering
left stick guard change the execution order so that the first thing that
happens is we add either the W layer on the right bumper slash right
trigger depending on the layout then we remove the guard and then the same
for the opposite side."

## Terms

- **Driver:** R1 or L1 in the default layout; R2 or L2, on the trigger's soft
  pull, in the alternative.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key`.
- **The Entry Guard:** `Steering | LS: Entry Guard`. Each driver there has
  one repeating chord on itself with two commands: one removes the guard,
  one adds the driver's layer.
- **Run order:** a binding array runs bottom to top (A4), so the command
  stored last runs first.

## The change

One bind on each of two inputs a layout: the driver chords in the Entry
Guard. The two commands swap places in the stored array. Nothing else.

| The driver chord in the Entry Guard | 90.67 | 90.68 |
|---|---|---|
| Stored | Add the driver layer, remove the guard | Remove the guard, add the driver layer |
| Runs first | Remove the guard | Add the driver layer |
| Runs second | Add the driver layer | Remove the guard |
| Settings (repeating, 50 ms, not interruptible, quiet) | | Unchanged |

Not touched: Start and Select in the Entry Guard, which also remove the
guard before they add; `Steering`'s own driver chords; the ten cleanup
presses of 90.67. No add or remove more or fewer: 380 adds, and 2,885 and
2,943 removes.

## What it does

With R1 pressed while the guard is on, stick up:

| Step | 90.67, stack above Base | 90.68, stack above Base |
|---|---|---|
| Before | `Steering`, guard | `Steering`, guard |
| First command | `Steering` | `Steering`, guard, W layer |
| Second command | `Steering`, W layer | `Steering`, W layer |

Both end the same. The difference is the middle row: on 90.67 `Steering`
is the top layer for that moment, with its exit on up and down, and on
90.68 it never is. That is the same exit the guard is there to keep the
stick away from, also after a cleanup press that ran past its guard chord
(A69, R176).

## What it rests on

- **The order is the point** (author, 2026-10-13): "I want the W layer to
  be applied first, then the removal of the guard because I don't want for
  a split second that the steering base is shown."
- **The W layer lands over the guard** for that moment. R137 says no layer
  is added over a temporary guard and that a hand-over removes the guard
  first, so its Releases cannot be hidden. Here the guard is removed by
  the same bind, so nothing of it stays hidden.
- **The repeat of this chord.** It has two commands, and you called out on
  2026-10-10 that a repeating chord with more than one command does not
  fire its repeat. Swapping the order does not change that. It matters for
  90.67's leak case, where the guard lands on a driver that is already
  held and this chord has to run without a fresh press. If it does not
  run there, the guard stays until the stick comes back.

## Tools, rules and tests

- **R137:** its row gets the exception: the Entry Guard's two driver
  chords add first and then remove the guard (author, 2026-10-13). The
  rule stands for Start and Select and for every other guard.
- **Audits:** the chains apply a whole bind at once, so the build audit
  should read the layout as before. The build shows whether it does.
- **Simulator:** it applies a bind's commands in run order with nothing in
  between, so every existing scenario should pass unchanged. It cannot
  show the difference between the two orders.
- **Tests:** a shape test (the add is stored last in both chords, in both
  layouts; only those two inputs differ from 90.67). Any older test that
  states the stored order reads the 90.67 build.

## Build steps

1. A builder in a new findings folder, reading the 90.67 snapshot: swap
   the two commands on the two inputs.
2. The R137 row and the shape test.
3. Build audit, full suite, random walks against 90.67 (expected: no log
   differs), VDFs, snapshot, record.

## Questions

1. **Split the chord so its repeat fires?** The swap alone leaves a
   repeating chord with two commands. If the repeat is what has to rescue
   a held driver after a leak, the bind would need two chords, one command
   each: one adds the driver layer, one removes the guard. That is a
   second change, and you asked for one. **My pick: build the swap alone
   as asked,** and decide on the split after the Deck shows whether a held
   driver takes the guard over.
