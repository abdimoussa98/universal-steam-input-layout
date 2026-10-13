# Rocking in `Steering` the way the bumper modifiers do it (90.62)

Built on 2026-10-12 from the **90.61** snapshot, both layouts, on the author's
word: "start building". 90 layers in each layout. Nothing here has run on the
Deck.

It builds the
[plan](../../plans/2026-10-12-steering-rocking-like-the-bumper-modifiers.md).

| | Default | Alternative |
|---|---|---|
| Removes in 90.61 | 2,851 | 2,909 |
| Added by hand | 2 | 2 |
| Added by the fix pipeline (R128) | 32 | 32 |
| **Removes in 90.62** | **2,885** | **2,943** |

## Terms

- **Rocking:** holding one bumper, pressing the other, letting go of the
  first, and so on back and forth, with one bumper down at all times.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key` (R2 and
  L2 in the alternative layout).
- **Modifier 2:** the layer on top while both bumpers are held:
  `Steering | R1!L1: Modifier 2` when R1 went down first, `Steering | L1!R1:
  Modifier 2` when L1 did.
- **Hand-over:** from 90.57 to 90.61, the first bumper's Release inside
  Modifier 2 added the other driver's layer and removed its own.

## Why

The author on the Deck, 2026-10-12: holding W, pressing L1 and letting go of
R1 gives S, "and that is working. But if I try and go back, it isn't." On the
way back, pressing R1 keeps S ("s stays just like how if we started with w
then w would stay"), so the fault is at the next step, letting go of L1,
where Modifier 2's Release added the W layer over an R1 that was already
held.

The simulator played both directions on 90.58 and 90.61, and the two
directions are mirror images bind for bind. So the layout did not show why.

What the author pointed at: "compare how we do rocking and mod two outside of
steering ... if I'm in R1 and I hit L1, it's like adding S ... even though
it's getting overwritten."

| Step, R1 held first | Bumper modifiers (works on the Deck) | `Steering`, 90.57 to 90.61 |
|---|---|---|
| Press L1 | One chord adds R1's cover, `L1: Modifier 0`, L1's cover, then Modifier 2 on top | One chord adds Modifier 2 |
| Release R1 | Removes only. The L1 modifier is uncovered | Adds the S layer, removes Modifier 2 and the W layer |

Outside `Steering` no layer is added on a Release during a rock. The
hand-over was the one place a bumper's layer landed that way.

Checked on the Deck before the build, on 90.61: with R1 held, pressing and
letting go of L1 leaves W held. So a layer uncovered under a held bumper
types its key, which this build relies on.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.61: 4 layers, 38 inputs each. Shown for R1 first; L1 first is the mirror.

| Bind | 90.61 | 90.62 |
|---|---|---|
| W layer, L1's chord on R1 | Removes six stick layers, adds Modifier 2 | The same, and adds the S layer just before Modifier 2, so it sits under it |
| Modifier 2, R1's Release | Adds the S layer, removes Modifier 2 and the W layer | Removes Modifier 2 and the W layer |
| Modifier 2, L1's Release | Removes Modifier 2 | Removes Modifier 2 and the S layer |
| Modifier 2, sixteen cleanup functions | Remove Modifier 2 and the W layer | Also remove the S layer |

The last row is the fix pipeline's: the cleanup rule for a layer below
(R128) asks for it, and the author chose to keep the rule ("add them"). The
builder stops if the pipeline does anything else.

Not touched: `Steering`'s own bumper binds, the driver layers' Releases, the
stick layers, the bumper modifiers outside `Steering`.

## What you would feel

| Step | Stack above `Steering` | Key |
|---|---|---|
| Hold R1 | W layer | W |
| Press L1 | W layer, S layer, Modifier 2 | W |
| Release R1 | S layer | S |
| Press R1 | S layer, W layer, Modifier 2 | S |
| Release L1 | W layer | W |
| Press L1, release L1 | W layer | W throughout |

Which key is held when is the same as on 90.61. The difference is on the
Deck: going back should now work.

After a missed release:

- **The second bumper's release missed, then the first let go:** the second
  driver's layer is left on, typing nothing, until a thumb is on a stick. On
  90.61 the hand-over's layer cleared itself at once; here an inverted chord
  does not start when its layer is uncovered (A61).
- **Both releases missed:** A, pressed twice at most, clears Modifier 2 and both driver
  layers.

## Rules, the register and the tests

- **R174** keeps its statement (letting go of one driver never leaves bare
  `Steering` under the other). Its example is rewritten: the held driver's
  layer is left on, where the hand-over added it.
- **R111:** two more register entries, for the two Modifier 2 left-edge
  chords with their three removes. The 90.61 entries stay for that build.
- **R128:** met by the 32 removes. The Cleanup audit is clean.
- **New tests,** [`tests/test_scenarios_90_62.py`](../../tests/test_scenarios_90_62.py),
  nine: the chord adds the second layer and then Modifier 2; no Release in
  Modifier 2 adds a layer; all sixteen cleanups of a Modifier 2 layer remove
  both driver layers; only four layers differ from 90.61; and scenarios
  90.62 R1 to R3 (rocking three times round, the second let go first, the
  other key never typed while the first is held) and M1, M2 (missed
  releases).
- **On the 90.61 build** (`frozen`): scenario 90.57 H2 and two shape tests of
  90.57 that state the hand-over, 90.61 E7 and 90.46 E2.

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Rocking the bumpers outside `Steering`:** the nine tests of
  `tests/test_modifier_rocking.py` pass. No bind there changed.
- **Random walks, the whole log compared** with 90.61 ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with one release
  in ten missed.

  | Layout, releases missed | Walks that finish | Log differs | A layer left on, 90.61 | 90.62 | After a thumb on each stick |
  |---|---|---|---|---|---|
  | Default, none | 11,715 | 994 | 20 | 21 | 0 and 0 |
  | Default, one in ten | 11,723 | 977 | 281 | 298 | 0 and 0 |
  | Alternative, none | 12,000 | 829 | 21 | 23 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 824 | 174 | 186 | 0 and 0 |

  A few more walks end with a layer left on: the second driver's layer
  after a missed release, as said above. A thumb on a stick clears every one.
- **The walks that differ** ([`diverge.py`](diverge.py),
  [`diverge.txt`](diverge.txt)): in all 3,631 the first difference is 90.62
  adding the second driver's layer at that driver's press.
- **Full suite:** 1,245 tests in 109 modules, with the same 25 expected
  failures. One test failed on the first run: scenario 90.46 E2 stated one
  driver layer under Modifier 2. It now runs on the 90.61 build.
- **Unverified assumptions:** 48, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 391 scenarios.

## What it rests on

- **A guess about the cause.** The layout does not show why the way back
  failed. This removes the one place `Steering` left the pattern that works.
- **A possible flash of the second key.** The chord adds the S layer and
  then Modifier 2 in one list. If Steam lets a frame pass between the two, S
  is typed for that frame while W is held. The bumper modifiers' chord has
  the same shape with no key behind it, so the Deck has never shown this.
- **A repeating chord with eight sub-commands** (seven before). Its repeat
  may not fire (author, 2026-10-10); its first run does.

## On the Deck

Check first that the configurator's title shows `:: 90.62`.

1. Rock R1, L1, R1, L1 without letting both go: W, S, W, S each time.
2. The same starting with L1.
3. While both are held: only the first key, no flash of the other.
4. Hold both, let go of the second one first: the first key stays.
5. Rock with the left stick pushed up, and with a thumb tapping the right
   stick: `Steering` stays.
