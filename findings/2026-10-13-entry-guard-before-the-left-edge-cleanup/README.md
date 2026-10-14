# The mode shift out, the Entry Guard added before the left-edge cleanup (90.67)

Built on 2026-10-13 from the **90.66** snapshot, both layouts, on the author's
word: "revert the mode shift change. I still want keep the removal of the
delays on the clean up functions though. The other thing i want is for the
left stick clean up removals to before cleaning up i want you to add the
left stick steering guard, this is a precaution for the weird edge case
where the guard would fail for repeated removal calls", then "ok start
building". 90 layers in each layout. Nothing here has run on the Deck.

It builds the [plan](../../plans/2026-10-13-entry-guard-before-the-left-edge-cleanup.md),
for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| Driver binds in `Steering` back to 90.65's | 2 | 2 |
| Mode-shift groups deleted | 1 | 1 |
| Left-edge presses with the add | 10 | 10 |
| Adds in 90.66 | 370 | 370 |
| **Adds in 90.67** | **380** | **380** |
| Removes in 90.66 | 2,885 | 2,943 |
| **Removes in 90.67** | **2,885** | **2,943** |

## Terms

- **Driver:** R1 or L1 in the default layout; R2 or L2, on the trigger's soft
  pull, in the alternative.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key`.
- **The ten layers:** the two driver layers, the two stick modifiers,
  `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the two
  stick scroll layers and the two Steering Modifier 2 layers.
- **The press:** on the left stick's edge of each of the ten, a repeating,
  interruptible Regular Press that removes layers. An empty chord on the
  drivers beside it, its guard chord, holds it back while a driver is held.
- **The leak:** the press running although a driver is held (A69, confirmed
  on the Deck: a burst of `remove_layer` calls can fail the chord).
- **The Entry Guard:** `Steering | LS: Entry Guard`, the layer that entering
  `Steering` adds. Its stick types W, S, A and D. It leaves on a
  direction's or the edge's Release, on a driver (whose repeating chord
  removes it and adds the driver's layer), and inside the ring with no
  driver held.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.66: 11 layers, 13 changes each.

| Bind | 90.66 | 90.67 |
|---|---|---|
| `Steering`, each driver | A mode-shift press, then the chord that adds the driver layer | The chord only, as on 90.65 |
| `Steering`'s mode-shift group | There | Deleted |
| The press on the ten left edges | Removes its list | Adds the Entry Guard, then removes its list |
| The press's start delay | None | None |

- **Stored last.** A binding array runs bottom to top (A4), so the add is
  stored after the removes and runs before them.
- **The builder asserts** that 90.66 without its mode shift is 90.65
  without its 5 ms, bind for bind.

Not touched: the guard chords, the Entry Guard itself, `Steering`'s exit.

## What it does

With R1 held, the stick up at the rim, and the W layer's press leaking:

| Step | 90.65 | 90.67 |
|---|---|---|
| The press leaks | The W layer goes; `Steering`'s exit sees the stick and `Steering` ends | The Entry Guard lands and the W layer goes; the guard answers the stick: W |
| R1's repeating chord in the guard | | The guard goes and the W layer is back |

This table is read from the binds. No test runs it (below).

The add also runs in an ordinary cleanup, which the author accepted. On the
simulator, with a driver's release missed and the stick then pushed out:

| Stick | 90.66 | 90.67 |
|---|---|---|
| Up or down, at the rim | The driver layer goes, `Steering` ends | The driver layer goes, `Steering` stays, the guard types W or S |
| Back to centre | | The guard leaves; bare `Steering` |
| Up or down again | | `Steering` ends |

## One tool changed

The Cleanup audit read a press with an add as an ordinary entry, so the
chains followed the Entry Guard from ten more places. The first candidate
then failed the fix pipeline, and a throwaway one failed the Cleanup and
Flow audits (the plan lists the counts).

The classifier now reads a repeating, interruptible Regular Press beside a
chord, with removes and an add of the Entry Guard only, as a cleanup
function ([`steam_layout/flow_model.py`](../../steam_layout/flow_model.py),
`CLEANUP_GUARDS`). With that the build audit is clean. Two things follow:

- **The chains do not follow the add,** as they follow no cleanup function.
  The audits therefore do not look at what the Entry Guard lands over when
  it comes from a cleanup.
- **No earlier build reads differently:** none has such a press.

## Rules, the register and the tests

- **R176** is new: a left-edge cleanup function inside `Steering` adds the
  Entry Guard before it removes, and no other cleanup function adds a
  layer. **R175** (the mode shift) is retired. **R133** and **R137** say
  what changed for them.
- **A70** (a mode shift in a layer) is no longer relied on. **A4, A10,
  A25, A61, A69** name R176.
- **New tests,** [`tests/test_scenarios_90_67.py`](../../tests/test_scenarios_90_67.py),
  ten: no mode shift outside Base and no mode-shift group; each of the ten
  presses is 90.66's with the add stored last and no start delay; the ten
  are still cleanup functions; no other cleanup function adds a layer;
  only the two drivers and ten edges differ from 90.66, with ten adds more
  and no remove; and scenarios 90.67 G1 to G5 (the second table above; the
  same cleanup ends `Steering` on 90.66; with the driver held the press
  does not run and no guard lands; a driver pressed over the guard takes
  it over).
- **On the 90.66 build** (`frozen`): every test in `test_scenarios_90_66`,
  and scenarios 90.10 D8, 90.43 D4 and D5.
- **No scenario forces the leak** (author, 2026-10-13: "I don't think we
  need to necessarily account for that super edge case").

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Random walks, the whole log compared** ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with one release
  in ten missed. "No add" is 90.67 with the ten adds taken out, built in
  memory.

  | Layout, releases missed | Walks that finish | Log differs from 90.66 | From no add | A layer left on, 90.66 | 90.67 | After a thumb on each stick |
  |---|---|---|---|---|---|---|
  | Default, none | 11,715 | 257 | 1 | 21 | 21 | 0 and 0 |
  | Default, one in ten | 11,723 | 279 | 42 | 299 | 299 | 0 and 0 |
  | Alternative, none | 12,000 | 252 | 1 | 23 | 23 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 269 | 39 | 188 | 189 | 0 and 0 |

  The differences from 90.66 are mostly the mode shift going (90.66
  differed from 90.65 in about as many). The walks that differ from "no
  add" were not replayed one by one; nearly all need a missed release,
  which is where a cleanup press runs.
- **Full suite:** 1,288 tests in 114 modules, with the same 25 expected
  failures. A first run failed seven tests in six modules; the ten modules
  touched since were run again and pass, the whole suite was not:
  - Three older scenarios (90.10 D8, 90.43 D4 and D5) state that a stale
    driver layer cleared with the stick out ends `Steering`. They read the
    90.66 build now; R176 is the new behaviour.
  - One 90.62 shape test counted the add among a press's removes.
  - Two registry tests rejected the wording of the R175 and R176 rows.
  - One timing test (the Window audit under five seconds) took 5.9 s with
    the walks running beside it, and passes alone.
- **Unverified assumptions:** 51, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 411 scenarios.

## What it rests on

- **A4:** the add runs before the removes because it is stored last.
- **A61:** the Entry Guard's inverted chord does not run at the rim. If it
  did with no driver held, the guard would leave at once.
- **A driver's repeating chord in the guard runs on a driver that is
  already held** when the guard lands. If it did not, the guard would stay
  until the stick comes back and the driver's key would be missing for
  that long. Scenario G5 presses the driver afresh; it does not show this.
- **With the stick down and R1 held,** a leak leaves the guard typing S
  until R1's chord runs. Whether that shows as a key blip is not known.
- **After a leak from a stick modifier or scroll layer,** that layer is
  gone and the driver layer is back with the stick still out. What the
  stick does next there has not been run.
- **The audits do not see the guard landing from a cleanup** (above).
- **The leak still happens,** and nothing here shows the fault is gone:
  the simulator never runs a press past its guard.

## On the Deck

Check first that the configurator's title shows `:: 90.67`.

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays.
2. Hold R1 and push the stick to the rim and back a few times: W stays
   down, and the stick's scroll taps work as before.
3. Rock R1 and L1 with the stick out: W, S, W, S.
4. With no driver held, push the stick fully up: `Steering` ends.
