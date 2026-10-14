# The Entry Guard adds the driver's layer first, then removes itself (90.68)

Built on 2026-10-13 from the **90.67** snapshot, both layouts, on the author's
word: "in the steering left stick guard change the execution order so that
the first thing that happens is we add either the W layer on the right
bumper slash right trigger depending on the layout then we remove the guard
and then the same for the opposite side", then "Just do the order change".
90 layers in each layout. Nothing here has run on the Deck.

It builds the [plan](../../plans/2026-10-13-entry-guard-adds-the-driver-layer-first.md),
for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| Chords reordered | 2 | 2 |
| Adds, 90.67 and 90.68 | 380 | 380 |
| Removes, 90.67 and 90.68 | 2,885 | 2,943 |

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

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.67: 1 layer, 2 changes each.

| The driver chord in the Entry Guard | 90.67 | 90.68 |
|---|---|---|
| Stored | Add the driver layer, remove the guard | Remove the guard, add the driver layer |
| Runs first | Remove the guard | Add the driver layer |
| Runs second | Add the driver layer | Remove the guard |
| Settings | Repeating, 50 ms, not interruptible, quiet | Unchanged |

The builder asserts that nothing else differs: every bind has the same
commands and settings as on 90.67.

Not touched: Start and Select in the Entry Guard, which still remove the
guard before they add; `Steering`'s own driver chords; the ten cleanup
presses of 90.67.

## What it does

With R1 pressed while the guard is on:

| Step | 90.67, stack above Base | 90.68, stack above Base |
|---|---|---|
| Before | `Steering`, guard | `Steering`, guard |
| First command | `Steering` | `Steering`, guard, W layer |
| Second command | `Steering`, W layer | `Steering`, W layer |

Both end the same. On 90.67 `Steering` was the top layer in the middle row,
with its exit on up and down; on 90.68 it never is.

## Rules and tests

- **R137** (temporary guards) said a hand-over removes the guard before it
  adds. Its row now states the two driver chords of the Entry Guard as the
  other way round, on the author's word, and rests on A4.
- **New tests,** [`tests/test_scenarios_90_68.py`](../../tests/test_scenarios_90_68.py),
  three: each driver chord stores the add last; only those two chords
  differ from 90.67, and only in their order; scenario 90.68 H1 (a driver
  pressed in the guard ends with its layer directly on `Steering` and no
  guard, for both drivers and four stick directions).
- No tool changed.

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Random walks, the whole log compared** with 90.67 ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with
  one release in ten missed.

  | Layout, releases missed | Walks that finish | Log differs | A layer left on, 90.67 | 90.68 | After a thumb on each stick |
  |---|---|---|---|---|---|
  | Default, none | 11,715 | 1,182 | 21 | 21 | 0 and 0 |
  | Default, one in ten | 11,723 | 1,133 | 299 | 299 | 0 and 0 |
  | Alternative, none | 12,000 | 729 | 23 | 23 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 713 | 189 | 189 | 0 and 0 |

  The logs that differ were expected to be none, and are not: the log
  records each layer going on and off in order, and the hand-over now
  writes the add before the removal. Replayed from 4,500 walks (3,000
  default, 1,500 alternative), all 391 that differ are equal again once
  the events of one instant are put in one order. No key, wheel step,
  haptic, beep or time differs.
- **Full suite:** 1,291 tests in 115 modules, with the same 25 expected
  failures. Two older tests stated the old order of the two commands
  (`test_steering_entry_feedback`, `test_steering_entry_quiet_drivers`);
  they state the new one, and both modules pass run again. The whole
  suite was not run a second time.
- **Unverified assumptions:** 51, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 412 scenarios.

## What it rests on

- **The order is the point** (author, 2026-10-13): "I want the W layer to
  be applied first, then the removal of the guard because I don't want for
  a split second that the steering base is shown." Commands run one after
  the other, so with the removal first `Steering` is the top layer until
  the add runs.
- **The simulator cannot tell the two orders apart:** it runs a bind's
  commands with nothing in between. The tests show the binds are as asked
  and the hand-over ends the same. That is a limit of the simulator, not
  a doubt about the order.
- **The chord still has two commands.** The author called out on
  2026-10-10 that a repeating chord with more than one command does not
  fire its repeat. In 90.67's leak case the guard lands on a driver that
  is already held, and this chord has to run there without a fresh press.
  If it does not, the guard stays until the stick comes back. Splitting
  the chord in two was offered in the plan and not built.

## On the Deck

Check first that the configurator's title shows `:: 90.68`.

1. Enter `Steering` with the stick held up, then press R1: W, and
   `Steering` stays. The same with the stick down and L1: S.
2. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays.
3. Rock R1 and L1 with the stick out: W, S, W, S.
4. With no driver held, push the stick fully up: `Steering` ends.
