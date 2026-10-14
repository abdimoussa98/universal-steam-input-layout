# Plan: mode shift out, the Entry Guard added before the left-edge cleanup

**Status, 2026-10-13:** built as **90.67**, from 90.66 (author: "ok start building";
[release record](../findings/2026-10-13-entry-guard-before-the-left-edge-cleanup/README.md)).
The audit findings listed below went away with one change, the first under
"Tools": the chains no longer follow the add, so the second was not needed.

**Decided by the author, 2026-10-13,** on reading this plan:

- The simulator does not have to show the leak ("I don't think we need to
  necessarily account for that super edge case"): no `leak` helper and no
  forced-leak scenarios.
- The guard landing on an ordinary cleanup is fine: the add is there for
  the leak, and it sits in the ordinary cleanup.
- The audit failures do not stop the change ("we might have to just look
  at what fails and address that in the audit later or update some
  rules"). It is needed: the guards do fail on the Deck, and this is the
  clean way not to be put out of `Steering` on a leak.

The author, 2026-10-13: "create a plan to revert the mode shift change. I
still want keep the removal of the delays on the clean up functions though.
The other thing i want is for the left stick clean up removals to before
cleaning up i want you to add the left stick steering guard, this is a
precaution for the weird edge case where the guard would fail for repeated
removal calls."

"The left stick steering guard" is read as the layer
`Steering | LS: Entry Guard`.

## Terms

- **Driver:** R1 or L1 in the default layout; R2 or L2, on the trigger's soft
  pull, in the alternative.
- **Driver layer:** `Steering | R1: W Key` or `Steering | L1: S Key`.
- **The ten layers:** the two driver layers, the two stick modifiers,
  `Steering | LS: Tap Cover`, `Steering | LS: Double Tap Cover`, the two
  stick scroll layers and the two Steering Modifier 2 layers.
- **The press:** on the left stick's edge of each of the ten, a repeating,
  interruptible Regular Press that removes layers. An empty chord on the
  drivers beside it (its guard chord) holds it back while a driver is held.
- **The leak:** the press running although a driver is held (A69, confirmed
  on the Deck: a burst of `remove_layer` calls can fail the chord).
- **The Entry Guard:** `Steering | LS: Entry Guard`, the layer added on
  entering `Steering`. What it binds today, unchanged by this plan:

  | Input | Bind |
  |---|---|
  | Stick up, down, left, right | W, S, A, D; each direction's Release removes the guard |
  | Stick edge | Its Release removes the guard. An inverted chord removes it while the stick is inside the ring and no driver is held |
  | Each driver | A repeating chord, every 50 ms: removes the guard and adds the driver's layer |
  | Start, Select | Remove the guard and add a menu Entry Point |

## The change

| Bind | 90.66 | 90.67 |
|---|---|---|
| `Steering`, each driver | A mode-shift press, then the chord that adds the driver layer | The chord only, as on 90.65 |
| `Steering`'s mode-shift group (13360, 13373) | There | Deleted |
| The press on the ten left edges | Removes its list | Adds the Entry Guard, then removes its list |
| The press's start delay | None | None |

- **Stored last.** A binding array runs bottom to top (A4), so the add is
  stored after the removes to run before them.
- **Adds:** ten more a layout. **Removes:** 2,885 and 2,943, unchanged.
- **The guard chords, the Entry Guard itself and `Steering`'s exit** are not
  touched.

## What it does

With R1 held, the stick up at the rim, and the W layer's press leaking:

| Step | Stack above Base | 90.65 | 90.67 |
|---|---|---|---|
| The press leaks | 90.65: `Steering`. 90.67: `Steering`, Entry Guard | `Steering`'s exit sees the stick: `Steering` ends | The guard answers the stick: W |
| R1's chord in the guard, at once or within 50 ms | `Steering`, W layer | | The guard is gone and the W layer is back |

`Steering` is never the layer that answers the stick, so its exit cannot
run. Nothing in the guard at the rim is an interruptible bind beside a
chord, so a second leak has nothing to run there.

**It also changes the cleanup when nothing leaks.** After a missed driver
release, the press runs as it should when the stick reaches the rim. Run on
the simulator, default layout, R1's release missed, then the stick pushed
out:

| Stick | 90.66 | With the guard add |
|---|---|---|
| Up or down | The W layer goes, `Steering` ends | The W layer goes, `Steering` stays, W or S is typed while the stick is out |
| Left | The W layer goes, A | The same, by the guard |
| Back to centre | | The guard leaves; bare `Steering` |

So a stale layer no longer costs `Steering` either. Ending `Steering` with
the stick then takes a second push.

## What it rests on

- **A4:** the add runs before the removes because it is stored last.
- **A61, the inverted chord:** the guard's chord must not run at the rim.
  If it did with no driver held, the guard would leave at once and the
  exit would be back.
- **A driver's repeating chord fires on a driver that is already held**
  when the guard lands (the author's held-input rule for a repeating bind).
  If it did not, the guard would stay until the stick comes back, and the
  driver's key would be missing for that long.
- **With the stick down and R1 held,** the guard types S until R1's chord
  runs. Whether that shows as a key blip on the Deck is not known.
- **After a leak from a stick modifier or scroll layer,** that layer is
  gone and the driver layer is back with the stick still out. What the
  stick does next there has not been run; the build's scenarios will.
- **The simulator never leaks,** so it shows what the binds do after a
  forced leak, not that the fault is gone.

## Tools, rules and tests

The findings below are sorted after the build, each kind into an audit
correction or a rule update; what is still open then is reported with the
release, not held against it (the author's decision above).

A throwaway candidate, built outside the repo, was put through the build
audit against 90.66 (which is clean). Budget and Window pass. The audit's
own verdicts on the rest:

| Audit | Check | Findings |
|---|---|---|
| Cleanup | Edge without cleanup, R170 | 10: a press with an add is not read as a cleanup function |
| Cleanup | Hidden exit, R136 | 440, and 10 to review |
| Cleanup | Left below, R128 | 6 |
| Cleanup | Hidden cleanup, R130 | 2 |
| Flow | Needs review, R139 | 4 inputs that vary, on the two stick scroll layers |

My reading, not the audit's: most of these come from the chains now
following the Entry Guard from ten more adders and stacking it on layers
the same press removes. Each kind has to be sorted in the build into a
tool reading to correct or a real finding to fix; none is accepted unseen.

- **Cleanup audit:** read a repeating, interruptible press whose only add
  is the Entry Guard as a cleanup function.
- **Chains:** an add whose own list removes its owner is a hand-over, not
  a layer landing on the owner.
- **Simulator:** no change. The mode shift model and `drop` stay for the
  90.66 tests.
- **R133** (the cleanup shape): its row allows the Entry Guard add on the
  ten edges. **R137** (nothing added over a temporary guard) is unchanged;
  its row notes the guard now also lands from a cleanup.
- **R175** (no exit on the stick while a driver is held) ends with 90.66.
  A new rule in its place: a left-edge cleanup in `Steering` never leaves
  `Steering` answering the stick.
- **A70** (a mode shift in a layer) is no longer relied on. **A69** stays.
- **Tests:** the shape (no mode shift anywhere outside Base, the group
  gone, the add last in ten presses, no start delay, only those binds
  differ from 90.66); the missed release table above; rocking. No
  forced-leak scenario (the author's decision above).
  The 90.66 tests move to the frozen 90.66 build.

## Build steps

1. A builder in a new findings folder, reading the 90.66 snapshot. It
   asserts that 90.66 without the shift equals 90.65 without its delay.
2. The audit and simulator changes, then the tests.
3. Build audit, full suite, random walks against 90.66, VDFs, snapshot,
   record.

## Questions

None. The one asked here, the guard landing on an ordinary cleanup, is
answered above: keep it.
