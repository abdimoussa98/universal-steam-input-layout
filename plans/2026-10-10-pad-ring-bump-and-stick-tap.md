# Plan: the ring bumps by its own binds, and the stick deflect in Steering

**Status, 2026-10-10:** part 1 and the second lead of part 3 are built as
**90.51** on the author's go-ahead
([record](../findings/2026-10-10-ring-bump-and-modifier-direction/README.md)):
the ring pads' override, and the cleanup off the stick modifiers' own
direction, under an R130 exception. Part 2 is not built. Nothing has run on
the Deck. The investigation is in
[findings/2026-10-10-pad-ring-bump-and-stick-tap](../findings/2026-10-10-pad-ring-bump-and-stick-tap/README.md).
The text below is the plan as proposed.

**Corrected the same day.** The first version of this plan read the Steering
fault as "a tap never starts the scroll" and offered part 2 as its fix. The
author: "That quick motion is supposed to add the scroll up or down layer
window but it's only happening once." Part 2 does not fix that.

Two faults on 90.50, from the author on 2026-10-10:

1. A click on a pad's outer ring gives no bump, where the centre gives one.
2. In `Steering`, a quick deflect of the left stick up or down adds the scroll
   window once, and then not again.

## Terms

- **Ring:** the outer part of a pad, which a click sends to `LTP: Arrow Keys`
  or `RTP: Mouse Buttons`. On a stick, its outer edge.
- **Override:** a D-pad pad's Haptic Intensity Override, a setting of the whole
  pad.
- **Driver:** R1 for W and L1 for S in `Steering`, the triggers in the
  alternative.
- **W layer:** `Steering | R1: W Key`, which `Steering` adds while R1 is held.
  `Steering | L1: S Key` is its twin. Up and down add a stick modifier only
  from these two.
- **Stick modifier:** `Steering | LS Up: Modifier 1` or
  `Steering | LS Down: Modifier 0`.
- **Hold marker:** `Steering | LS: Tap Cover`. Once it is on, letting the stick
  go doesn't scroll.
- **Window:** `Steering | LS Up: Double Tap` or its Down twin, which scrolls
  once after 150 ms.

## 1. The ring's bump

**Cause.** 90.50 set the ring's direction binds to Low and left the two pads'
override at Off. Off means "Do not use haptics for this mode": it silences the
binds. Read from the Steam client, not measured
([record, part 1](../findings/2026-10-10-pad-ring-bump-and-stick-tap/README.md#1-the-ring-gives-no-bump-because-its-pad-says-no-haptics)).

| Layer | Setting | 90.50 | Plan |
|---|---|---|---|
| `LTP: Arrow Keys`, `RTP: Mouse Buttons` | The pad's Haptic Intensity Override | Off (`0`) | Use Activator Settings (`5`) |
| The same two | Haptic intensity of the ring's empty block (`edge`) | Not stated | Off (`0`) |

Four settings per layout. What then asks for a bump on the ring is what 90.50
already wrote: the arrows, Back, Forward and the two scroll directions at Low.
The repeating scroll, the holds and the exits stay Off.

- **Why 5 and not Low.** At Low the pad sends its own bump "when the input
  turns on or off", for every direction, whatever the binds say. That is what
  90.41 to 90.48 had. 5 is one of the editor's own choices, but no layout here
  has stated it before.
- **Why the block states Off.** At 5 every bind's own setting counts, and this
  one stated none.
- **What stays.** Base's click and `RTP: Circular Scroll`'s click (Off), the
  two Click Entry Points (override Off, every bind Off), the two centre layers.

## 2. A tap whose thumb leaves the stick first (not the reported fault)

**What it is.** In a stick modifier, the left-stick touch Release adds the
hold marker (R123). If the thumb leaves the stick before the stick is back,
the marker lands first and the tap is taken as a hold. On the simulator no
such push scrolls on 90.50, and every one does with the change below
([record, part 2](../findings/2026-10-10-pad-ring-bump-and-stick-tap/README.md#2-a-stick-tap-doesnt-scroll-when-the-thumb-leaves-the-stick-first)).
The author's deflect keeps the thumb on the stick, so this is a hole beside
the reported fault, and building it is the author's call.

| Layer | Input | 90.50, in the order it runs | Change |
|---|---|---|---|
| The two stick modifiers | Left-stick touch, Release | Add the hold marker. Remove the three `LST` helpers. Remove `RTP: Entry Point`, `RTP: Tap Cover`, `RTP: Circular Scroll` | Remove the three `LST` helpers |

Two binds per layout. It needs an exception to R123, the author's rule of
2026-09-29: there the thumb leaving is the end of the push the delay is
timing, where in every other layer the delay's own button is still held. The
right-stick touch Release would keep adding the marker.

## 3. The reported fault: once, then not again

**Not diagnosed.** On the simulator a deflect with the thumb on the stick
scrolls every time, on the twelve live releases from 90.38 to 90.50. So the
Deck does something the simulator assumes away
([record, part 3](../findings/2026-10-10-pad-ring-bump-and-stick-tap/README.md#3-the-reported-fault-a-deflect-scrolls-once-then-not-again)).

**The lead.** The model gives "once" in one way only: the W layer is removed
when the first window closes and does not come back while the driver stays
held. After that, up and down have nothing that adds a stick modifier.

- **What would remove it.** When the window closes, the W layer is uncovered
  under the resting thumb. Its stick-touch cleanup is held back only by a
  chord with the driver, and the layout assumes that chord comes alive again
  at that moment (A36, unverified).
- **Why it would not come back.** Since 90.46 `Steering` adds the W layer with
  a chord of the driver with itself. Until 90.45 it was a repeating Regular
  Press. With that one assumption off, the model scrolls on every deflect up
  to 90.45 and once from 90.46 on.
- **What speaks against it.** The same assumption, off everywhere, would also
  drop the L1 modifier when the cursor cancels under a resting thumb, and
  nothing like that is on record. If this is the cause, it is narrower than
  the model's version of it.

**What is needed from the Deck**, on 90.50 as installed. Hold a driver, keep
the left thumb on the stick, deflect once for the scroll, and then:

| Observation | The W layer is being lost | It is not |
|---|---|---|
| Is W still held: is the driver still driving? | No | Yes |
| Let go of the driver, press it again, deflect | One more scroll | Still none |
| A deflect to the rim | Leaves `Steering`, with the pulse and the beep | Stays in `Steering` |
| The same deflects on 90.45, to the rim, thumb on | Every one scrolls | Once there too |

**What follows.**

- **The W layer is being lost:** two things to design with the author, from
  existing layers. What brings the W layer back when it is removed under a
  held driver, where 90.45's repeating press did. And whether the window's
  closing may uncover the W and S layers' cleanups at all.
- **It is not:** the next check is whether the other direction still works
  once. That would point at one stick modifier's own 200 ms delay (A12, A13)
  and not at anything the two directions share.

### The author's answers, 2026-10-10, and a second lead

On 90.50, after the one scroll with the driver held: W is still held; letting
go of the driver and pressing it again gives no further scroll; a deflect to
the rim sometimes leaves `Steering`, also with the driver held. 90.45 could
not be tested.

That rules out the first lead: the W layer is not lost for good. It fits the
four inputs noted under "Also on these inputs". In a stick modifier, the
cleanup on its own direction removes the modifier and both drivers' layers,
and its only guard is a chord that waits 200 ms. If Steam lets that cleanup
fire before the chord has fired, each deflect removes the modifier and the W
layer as the modifier lands. `Steering` adds the W layer again within 50 ms,
so W looks held; no window opens; and at the rim `Steering`'s own exit can
fire in the gap. With that one what-if the simulator gives no scroll and
`Steering` left, from 90.43 on, and four scrolls on 90.42, which has no such
input. It does not explain why the first deflect works. Unverified.

## For the author to decide

1. **Part 1 alone, now?** It does not depend on the rest.
2. **My reading of the pad report:** that the ring gives no bump at all on
   90.50. If it gives more than one, part 1 is wrong and needs another look
   before anything is built.
3. **Part 2, and its exception to R123.** Example: hold R1, flick the stick up
   and let it snap back. Today the thumb leaving the stick means "the hold is
   complete", and the scroll is lost. With the exception it means nothing, the
   stick coming back decides, and under 200 ms that is a tap.
4. **90.49's scroll when a thumb lifts inside the window.** It completes a
   delayed output on a thumb's release, which R125 says not to do, and the
   register has no entry for it. `tests/test_double_tap_windows.py` fails on
   90.50 because of it: the R118 check can't read a wheel step in a window's
   touch Release. Kept, it needs an R125 entry and the check taught to read
   it. Taken back, a thumb that lifts inside the 150 ms loses the tap again.

## What parts 1 and 2 rest on

| Assumption | Status | What it means here |
|---|---|---|
| New row at the build: a D-pad pad's override at Off silences its binds, and at 5 leaves each bind to its own setting | Read from the client on 2026-10-10. Unverified | The ring's bump |
| A56: a final click layer's output bumps once | Unverified. The centre shows it on the Deck (author, 2026-10-10) | The ring has the same kind of bind, but its layer lands 5 ms later than the centre's. On a fast click it may land after the click is full |
| A13: a removal can disturb a pending delay | Reported by the author | Part 2: the three helper removals run while the 200 ms is pending, until the stick is back. A restart is harmless. If the delay fires instead, that tap is lost, as today |

## On the Deck, for part 1

The pad can be tried today, without a build. In Steam's editor open
`RTP: Mouse Buttons`, the right pad's settings, and set Haptic Intensity
Override to Use Activator Settings. One bump on a ring click confirms part 1.

After the build:

| Check | Expect | If not |
|---|---|---|
| Click both pads at the centre and at the four sides of the ring, slowly and fast | One bump a click, the same at the centre and the ring | No ring bump on fast clicks only: the layer lands after the click (A56). Two bumps, down and up: say so |
| Hold a ring click. Hold up or down on the right ring | No further bump. Scrolling repeats without pulses | The repeating scroll's bind is the source |

## Build steps, for part 1 and, if wanted, part 2

The release follows [building](../docs/building.md) and
[publishing](../docs/publishing.md).

1. A new builder folder under `findings/`, in the shape of the 90.50 builder:
   it reads the 90.50 snapshot, asserts what it expects to find, makes the
   changes and runs the fix pipeline. The pipeline must change nothing. On a
   scratch build of both parts it changed nothing, and the four audits passed
   on both layouts.
2. Scenario tests, `tests/test_scenarios_90_51.py`, on both layouts:
   - Static: the two pads' override is `5`, their directions Low, every other
     bind of theirs Off.
   - With part 2, inside one driver hold, both drivers: a tap with the thumb
     leaving first, the same again, a tap followed by a held push, a 300 ms
     hold, and a tap after it. One step, one step, repeats, none, one.
     `Pad.lift` recentres the stick before it lets go of the touch, so no
     scenario has had the thumb leave first. These release the touch on its
     own.
3. The tests and documents below.
4. `audit_build`, the change report, the unverified list, the description
   check, the title, both VDFs and the snapshot in `versions/neptune/90.51/`.

| File | Change |
|---|---|
| `tests/test_scenarios_90_49.py` | `test_single_configured_bump_is_on_each_final_click_output` expects the override `5` and the block Off |
| `resources/Steam Behaviour Assumptions.md` | The new override row. A56 says the ring's pads are at Use Activator Settings |
| `docs/building.md` | Rows for 90.49, 90.50 and 90.51. It stops at 90.48 today |
| `todos.md` | The Deck checks above |
| With part 2: `tests/test_steering_rtp_menu_chords.py` | `test_delayed_targets_complete_before_rtp_cleanup_including_touch_completion`: the left stick's Release in the two stick modifiers completes nothing. Failing since 90.49, which took the three click layers out of those lists |
| With part 2: `steam_layout/flow_config.json`, `resources/Layer Definition of Done.md` | An R123 entry for the two stick modifiers' `joystick/touch`, and R123's exception column |
| With decision 4: `tests/test_double_tap_windows.py`, the register, the Definition of Done | The R118 check reads the wheel step, and R125 gets its entry. Failing since 90.49 |

Every test module was run against a scratch copy with parts 1 and 2
installed: 1,118 tests. One test fails because of them, the first row. Six
test modules already fail on 90.50 as it stands, three of them since 90.49.
They are listed in the
[record](../findings/2026-10-10-pad-ring-bump-and-stick-tap/README.md#also-found-tests-that-fail-on-9050-as-it-stands)
and are not part of this plan unless the author wants them in.
