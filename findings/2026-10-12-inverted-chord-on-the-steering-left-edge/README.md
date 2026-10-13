# One inverted chord as the left-edge cleanup in the Steering layers (90.61)

Built on 2026-10-12 from the **90.58** snapshot, both layouts, on the author's
word: "I think we're good to start building", keeping 90.58's remove lists.
90 layers in each layout. Nothing here has run on the Deck.

It builds the
[plan](../../plans/2026-10-12-inverted-chord-on-the-steering-left-edge.md)
for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).
That record has what was tried and learned on the way here.

| | Default | Alternative |
|---|---|---|
| Inputs changed | 10 | 10 |
| Removes in 90.58 | 2,851 | 2,909 |
| **Removes in 90.61** | **2,851** | **2,909** |

## Terms

- **Press and guard:** what the left edge had: a repeating, interruptible
  Regular Press that removes layers, and beside it an empty Chorded Press on
  the bumpers, not interruptible, meant to hold the press back.
- **Inverted chord:** a Chorded Press with Invert Activation. It runs while
  its own input is released and no chord button is held (A61). On the edge:
  stick off the rim and no bumper held.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key` (R2 and
  L2 in the alternative layout).
- **The ten layers:** the two driver layers, the two stick modifiers,
  `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the two
  stick scroll layers and the two Steering Modifier 2 layers.

## Why

On the Deck the W layer's press on the left edge ran although R1 was held,
while right stick touch Releases were sending `remove_layer` calls. The W
layer went, and `Steering`'s exit at the rim ended `Steering`. The author,
2026-10-12: "instead of using a repeating regular press that's interruptible,
and a chord that is a guard, I want you to just use a single inverted chord
that is repeating ... all we're doing is updating the edge cleanup bind on
the left stick. And all the steering layers."

With one chord there is no press on the edge for a guard to miss.

## The one change

On the left stick's edge of the ten layers
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt): 10 layers,
10 inputs each):

| Edge entry | 90.58 | 90.61 |
|---|---|---|
| Cleanup | Regular Press, repeating, interruptible | One Chorded Press on the same bumpers with Invert Activation, repeating, not interruptible, haptics off |
| Guard | Empty Chorded Press on the bumpers | Gone |
| The list | | The press's 90.58 list, command for command |
| Timer, in the four timer layers | Soft Press at 13276 | Unchanged, stored after the chord |

The builder stops unless exactly ten inputs differ from 90.58, each chord
carries its press's commands in their order, and the count of removes is the
same. The fix pipeline changed nothing.

Not touched: both stick touches (still a press and guard), the right edge,
the buttons, the bumper Releases, `Steering`'s exit, the Entry Guard.

## What you would feel

| | 90.58 | 90.61 |
|---|---|---|
| Bumper held, stick anywhere | Nothing runs, if the guard holds | Nothing runs, if Steam sees the bumper |
| No bumper, stick at the rim | The cleanup runs | Nothing runs |
| No bumper, stick off the rim | Nothing runs | The cleanup runs |

A driver or stick layer left on by a missed bumper release clears as soon as
the stick is off the rim. On 90.58 it waited for the rim, a stick touch or
the next bumper press.

## How it differs from 90.55

90.55 had one inverted chord on the same ten edges, and 90.56 took it out
after a report that a thumb lifting with a bumper held ended `Steering`
(A66, never isolated on the Deck). The chord's settings are the same. What
differs:

- **Sub-commands.** 90.55's chords had three to seven each. Here the two
  driver layers' chords have one, and the other eight have two, three or
  five. A repeating chord with more than one sub-command does not fire its
  repeat (author, 2026-10-10); its first run still happens.
- **`Steering`'s exit** removed all fourteen family layers in 90.55. It
  removes `Steering` alone.
- **The lists around it** are 90.58's, shorter throughout.

## Rules, the register and the tests

- **R111:** ten register entries for the exact chords, as 90.55 had. The
  Budget audit matches them.
- **R133:** one entry for the shape on these ten edges.
- **A66** has these ten edges under "rests on" again. **A27** records that
  the guard failed on the Deck.
- **New tests,** [`tests/test_scenarios_90_61.py`](../../tests/test_scenarios_90_61.py),
  twelve: only the ten edges differ from 90.58; each chord carries its
  press's list; the edge's shape; one sub-command in the driver layers;
  inverted chords nowhere else but the Entry Guard; and scenarios 90.61 E1
  to E7.
- **Scenarios:** flicking with a driver held keeps the driver layer (E1); a
  missed driver release clears with the stick off the rim (E2, E3);
  pressing the driver again shuts the chord off (E4); the fault's gesture
  (E5) and a thumb lifting with the stick out (E6) keep `Steering` on the
  simulator; a driver layer added with nobody holding it clears itself (E7).
- **On the 90.58 build** (`frozen`): three tests of 90.56 that state the
  press and guard on the edge, and scenario 90.57 M2, which E7 replaces.
- **Reworded:** the edge's activator list in `test_scenarios_90_52`, and the
  count of registered inverted edge chords in
  `test_steering_rtp_menu_chords` (11, was 1).

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files, which equal the builder's output.
- **Random walks, the whole log compared** with 90.58
  ([`proof.py`](proof.py), [`proof.txt`](proof.txt)): 24,000 walks a layout,
  half with one release in ten missed.

  | Layout, releases missed | Walks that finish | Log differs | A layer left on, 90.58 | 90.61 | After a thumb on each stick |
  |---|---|---|---|---|---|
  | Default, none | 11,715 | 4 | 24 | 20 | 0 and 0 |
  | Default, one in ten | 11,723 | 53 | 301 | 281 | 0 and 0 |
  | Alternative, none | 12,000 | 1 | 22 | 21 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 43 | 181 | 174 | 0 and 0 |

- **The walks that differ** ([`diverge.py`](diverge.py),
  [`diverge.txt`](diverge.txt)): 103 are listed with where each first
  differs. In 56 the first difference is 90.61 removing a driver layer that
  nobody holds, earlier than 90.58 did. The other 47 were not read one by
  one; none leaves a layer on that a thumb does not clear.
- **Rocking the bumpers:** the nine tests of `tests/test_modifier_rocking.py`
  pass. No bumper bind changed.
- **Full suite:** 1,236 tests in 108 modules, with the same 25 expected
  failures as before. A first run failed in six modules: four stated the
  press and guard on the edge (frozen or reworded, above), one wanted the
  snapshot, one wanted R133's row. On the rerun one test failed, a 5-second
  limit in `test_audit_inheritance` missed while another run shared the
  machine; that module passes on its own.
- **Unverified assumptions:** 48, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 386 scenarios;
  every layer is on the stack in one (R165).

## What it rests on

The simulator reads an inverted chord as off while a bumper is held, always
(A61, A66). The fault is Steam missing a held bumper. If it misses one for
this chord too, the chord is live through most of a deflect, where the press
could only misfire at the rim. The second Deck check below decides that.

## On the Deck

Check first that the configurator's title shows `:: 90.61`. The author found
the Deck sometimes keeps the previous layout after a new one is applied.

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays, W stays.
2. Hold R1, push the stick up or down, lift a thumb from either stick.
   `Steering` stays, W stays. If it ends, A66 fails, and an inverted chord
   cannot be a cleanup under a held bumper.
3. Rock L1 and R1 in `Steering` with the stick out.
4. Let go of everything with the stick centred: `Steering` alone, no key
   held.
