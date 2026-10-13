# The press and its guard back on the left edge of ten Steering layers, 5 ms late (90.65)

Built on 2026-10-13 from the **90.64** snapshot, both layouts, on the author's
word: "change the steering left stick clean up back to the non inverted chord
with interruptible regular press removals pattern we'd had before. Make the
left in those steering layers also no longer have the edge inverted. Last i
would now like the regular press removal to also have a start delay of 5ms".
90 layers in each layout. Nothing here has run on the Deck.

It is for the fault recorded in
[`Steering` ends on a right stick touch with a bumper held](../2026-10-12-steering-ends-on-a-stick-touch/README.md).

| | Default | Alternative |
|---|---|---|
| Left edges changed | 10 | 10 |
| Rings changed | 10 | 10 |
| Removes in 90.64 | 2,885 | 2,943 |
| **Removes in 90.65** | **2,885** | **2,943** |

## Terms

- **The press:** a Regular Press on the edge with Hold to Repeat, left
  interruptible, whose commands only remove layers. It is the layer's cleanup
  function on that input.
- **The guard:** an empty Chorded Press on the same edge, on the layer's
  drivers, not interruptible. While a driver is held it is active and holds
  the press back (A27).
- **Driver:** R1 or L1 (R2 and L2 in the alternative layout).
- **The ring:** the stick's outer ring, the edge input. Inverted, it counts
  as pressed inside the ring.
- **The ten layers:** the two driver layers (W and S), the two stick
  modifiers, `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`,
  the two stick scroll layers and the two Steering Modifier 2 layers.

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt), against
90.64: 10 layers, 20 changes each.

| On the left stick of each of the ten layers | 90.64 | 90.65 |
|---|---|---|
| The edge's cleanup | One chord with Invert Activation on the drivers, repeating | The press, then the guard |
| The press's start delay | No press | 5 ms |
| Outer Ring Binding Invert | On | Off |
| The edge's timer (four layers) | A Soft Press, stored last | Unchanged |

The press and the guard take the settings they had on 90.58, the last build
with them. The press carries the chord's commands as they are, so the two
Modifier 2 lists keep the remove 90.62 added. `Steering | LS: Entry Guard`
is untouched and is the only layer with an inverted chord again.

| When the edge's cleanup runs | 90.58 | 90.63, 90.64 | 90.65 |
|---|---|---|---|
| A driver held, stick anywhere | Never | Never | Never |
| No driver, stick reaches the rim | At once | At once | 5 ms later |
| No driver, stick off the rim | Never | Never | Never |

## What you would feel

Nothing while a driver is held. After a missed driver release, the layer
left on clears 5 ms after the stick reaches the rim. A stick that is back
off the rim inside 5 ms leaves it for the next reach.

## One tool changed

The Cleanup audit called any bind with a start delay a hold, so it reported
the ten edges as having no cleanup function (R170). It now reads a
repeating, interruptible Regular Press of removes as a cleanup function with
or without a start delay
([`steam_layout/flow_model.py`](../../steam_layout/flow_model.py)). No
earlier snapshot has such a press, so no older build reads differently.

## Rules, the register and the tests

- **R133:** the ten edges have the rule's shape again. Its row says so, and
  that the press may start late. The register's entry for the inverted chord
  stays for the 90.61 to 90.64 builds.
- **R111:** the ten registered chords match no bind on the working layout.
  Their entries stay for the same builds.
- **A68** is new and unverified: a start delay on an interruptible press
  does not take it out from under its guard. **A19, A27, A61, A66, A67** say
  what 90.65 changed for them.
- **New tests,** [`tests/test_scenarios_90_65.py`](../../tests/test_scenarios_90_65.py),
  eleven: only the ten edges and ten rings differ from 90.64; each press
  carries the chord's list; the press and guard have their 90.58 settings
  and the press its 5 ms; no Steering ring is inverted and only the Entry
  Guard has an inverted chord; and scenarios 90.65 P1 to P6 (a driver held
  keeps its layer at the rim; a missed release clears 5 ms after the rim; a
  reach shorter than 5 ms clears nothing; pressing the driver again holds
  the press back; the fault's gesture; the timers).
- **On the 90.64 build** (`frozen`): scenarios 90.61 E1 and E3 to E6, 90.63
  G1 to G4, and the shape tests of 90.61 and 90.63 that state the chord and
  the inverted ring.
- **Changed for the press being back:** one line each in the 90.52, 90.55
  and 90.62 tests and in `test_steering_rtp_menu_chords`.

## Validation

- **Build audit:** clean on both installed layouts (Budget, Window, Flow,
  Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **Random walks, the whole log compared** ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with one release in
  ten missed. "No delay" is 90.65 with the 5 ms taken off, built in memory.

  | Layout, releases missed | Walks that finish | Log differs from 90.64 | From no delay | A layer left on, 90.64 | 90.65 | After a thumb on each stick |
  |---|---|---|---|---|---|---|
  | Default, none | 11,715 | 1 | 1 | 21 | 21 | 0 and 0 |
  | Default, one in ten | 11,723 | 35 | 37 | 299 | 298 | 0 and 0 |
  | Alternative, none | 12,000 | 1 | 1 | 23 | 23 | 0 and 0 |
  | Alternative, one in ten | 12,000 | 32 | 35 | 188 | 187 | 0 and 0 |

- **The walks that differ:** `proof.txt` lists how each first differs, by
  kind. The two replayed both have a Steering layer that nobody holds
  removed at another moment: 5 ms later than on 90.64 in one with a missed
  release, and 20 ms earlier in the one walk that differs with no release
  missed (the first point below). The others were not replayed.
- **Full suite:** 1,268 tests in 112 modules pass, with the same 25 expected
  failures. A first run failed seven tests in six modules that stated the
  chord or the inverted ring; they are the ones listed above.
- **Unverified assumptions:** 50, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). 401 scenarios.

## What it rests on

- **A delayed press also runs when it lands under a stick that is already
  out.** On the simulator a bind without a delay sends no layer commands
  for an input that was held before the bind was there (A5, A10); one with a
  delay does, when the delay ends. So with the stick at the rim and no
  driver held, the cleanup now runs 5 ms after its layer lands or is
  uncovered. That is the one walk above: L1's release was answered by a
  right pad layer, the S layer stayed with the stick down, and 90.65 cleared
  it 5 ms later where 90.64 waited for the next input.
- **It is the bind the fault happened on, plus 5 ms.** On 90.58 this press
  ran at the rim although a bumper was held. Whether the delay gives the
  guard time to see the bumper is A68, unverified. 90.61 to 90.64 have no
  Deck result on record.
- **The simulator cannot show the fault.** It never misses a held driver.

## On the Deck

Check first that the configurator's title shows `:: 90.65`.

1. The fault's gesture: hold R1, tap the right stick touch rapidly, flick
   the left stick to the rim in every direction. `Steering` stays, W stays.
2. Hold R1, push the stick up or down halfway, lift a thumb from either
   stick: `Steering` stays, W stays.
3. Hold R1 and tap the stick up eight times, with a hold past 200 ms in
   between: one wheel step per tap, none for a hold.
4. Rock R1 and L1 with the stick out: W, S, W, S.
