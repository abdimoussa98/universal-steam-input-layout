# The outer ring's bump and the stick tap (90.50)

**Status:** an investigation of 90.50, both layouts, on 2026-10-10, asked for
by the author. Read-only: no layout, VDF, version, rule or test changed.
Nothing was run on the Deck. The plan that follows from it is
[plans/2026-10-10-pad-ring-bump-and-stick-tap.md](../../plans/2026-10-10-pad-ring-bump-and-stick-tap.md),
and the to-do list has an entry for both.

The author's report, after running 90.50:

- "I'm only getting one haptic bump when I click, but that's only when I click
  the center. I'm not seeing that on the edge D-pad."
- "Tapping the left stick north or south is supposed to kick off the scroll
  lifecycle ... it's not working as intended still."

I read the first as: a click on the outer ring gives no bump at all. If it
gives more than one, part 1 is wrong.

**Corrected the same day.** I read the second as "a tap never scrolls". The
author, after reading the plan: "The 'tap' I was trying to get fixed was one
stick up or stick down deflect. That quick motion is supposed to add the
scroll up or down layer window but it's only happening once." So the deflect
works once and then stops. Part 2 is a real hole, but a different one.
[Part 3](#3-the-reported-fault-a-deflect-scrolls-once-then-not-again) is what
was found for the reported fault. It is not diagnosed yet.

The script is [probe.py](probe.py), about a minute; its output is
[results.txt](results.txt).

## Terms

| Term | Meaning |
|---|---|
| **Ring** | The outer part of a pad. A click there lands in `LTP: Arrow Keys` (the arrows) or `RTP: Mouse Buttons` (Back, Forward and scroll). Both are D-pad pads. On a stick, the ring is its outer edge |
| **Override** | A D-pad pad's Haptic Intensity Override (`haptic_intensity_override`). It is a setting of the whole pad, not of one bind |
| **Driver** | The button that drives in `Steering`: R1 for W and L1 for S, the triggers in the alternative |
| **Stick modifier** | `Steering \| LS Up: Modifier 1` or `Steering \| LS Down: Modifier 0`: what up or down on the left stick brings in while a driver is held |
| **Hold marker** | `Steering \| LS: Tap Cover`. Once it is on, letting the stick go ends the modifier and doesn't scroll |
| **Window** | `Steering \| LS Up: Double Tap` or its Down twin: 150 ms, then one wheel step. A second push inside it scrolls for as long as it is held |
| **Push** | The counting unit of part 2: one 60 ms push of the left stick up or down with a driver held, played on the press simulator |
| **Deflect** | The author's word for the tap: one quick push up or down and back. In part 3 the thumb stays on the stick throughout |
| **W layer** | `Steering \| R1: W Key`, the layer `Steering` adds while R1 is held. `Steering \| L1: S Key` is its twin. Up and down add a stick modifier only from these two |

## 1. The ring gives no bump because its pad says "no haptics"

What asks for a bump on a pad click, per release. The two layouts agree.

| | 90.48 | 90.49 | 90.50 |
|---|---|---|---|
| Base's click, which adds the Click Entry Point | Low | Low | Off |
| Centre: the middle click and Caps Lock | Low | Off | **Low** |
| Ring: the override of the two D-pad pads | Low | Off | **Off** |
| Ring: the arrows, Back and Forward | Low | Off | **Low** |
| Ring: the right pad's two scroll directions | Off | Off | **Low** |

90.50 moved the bump to the final output. On the ring it set the direction
binds to Low and left the override at Off.

The override is not one more source of a bump. In Steam's editor it has five
choices:

| Value | The editor's name | The editor's description |
|---|---|---|
| 5 | Use Activator Settings | "The haptics will be controlled by the settings in each activator." |
| 0 | Off | "Do not use haptics for this mode." |
| 1, 2, 3 | Low, Medium, High | "Use low intensity haptics.", and so on |

At Off the pad is silent whatever its binds ask for. Only at 5 do the binds
decide. The centre layers are not D-pad pads: a single button on the left, a
mouse pad on the right. They have no override, so their output's Low is what
the author feels.

How sure:

- **Read, not measured.** The names and numbers are from the Steam client on
  this Mac: the strings `ControllerBinding_HapticIntensityDpad_*` in
  `steamui/localization/steamui_english-json.js`, and the choices of
  `HapticIntensityDpad` in `steamui/chunk~2dcc5aaf7.js` (`ActivatorPref` 5,
  `Off` 0, `Low` 1, `Medium` 2, `High` 3).
- **Valve's own Deck layout has the same pair.** In
  `controller_base/desktop_neptune.vdf` the D-pad's four arrows state Low
  under an override of Off.
- **It fits the report.** In 90.50 the centre and the ring ask for the same
  bump on the same kind of bind. The override is what the ring's pad adds.
- **Nothing else in the layout has it.** Twelve groups per layout state an
  override. These two are the only ones at Off over a bind that asks for a bump.
- **The tools could not see it.** The simulator reads a bind's own
  `haptic_intensity` and not the override. The 90.50 test
  `test_single_configured_bump_is_on_each_final_click_output` asserts the
  silent pair: override `0` beside directions at `1`.

Until 90.48 the ring's bump came from the override, High up to 90.40 and Low
from 90.41, whatever its binds said. That covered the two scroll directions
too, whose binds stated Off.

## 2. A stick tap doesn't scroll when the thumb leaves the stick first

The lifecycle as built, with R1 held:

1. Up on the left stick: the W layer adds `Steering | LS Up: Modifier 1`.
2. Up held for 200 ms in the modifier adds the hold marker.
3. The stick comes back inside the ring. The ring's Release ends the modifier
   and opens the window. With the hold marker on, the marker's own ring
   Release ends both and opens nothing.
4. The window scrolls once after 150 ms.

### What is certain

The modifier's left-stick touch Release adds the hold marker. That is R123: a
stick-touch Release completes the pending add. So a thumb that leaves the
stick before the stick is back turns the tap into a hold.

| ms | What happens | On top of `Steering` |
|---|---|---|
| 0 | R1 goes down | W layer |
| 300 | The thumb lands and pushes up | W layer, Modifier 1 |
| 360 | The thumb leaves the stick: Modifier 1's touch Release adds the hold marker | W layer, Modifier 1, hold marker |
| 370 | The stick is back inside the ring: the marker's ring Release removes the marker and the modifier | W layer |
| | No window and no wheel step | |

This follows from the binds and from A7, which is verified: a Release fires in
a layer that was added while its button was held. Neither either-way
assumption changes it.

A flicked stick snaps back on its own after the thumb is gone, so this is the
order I expect from a quick tap. That part is not measured.

Pushes that give exactly one wheel step, of 1,728 per release:

| How the push ends | 90.48 | 90.50 | With the plan's change |
|---|---|---|---|
| The thumb stays on the stick | 768 of 768 | 768 of 768 | 768 of 768 |
| The thumb leaves before the stick is back | 0 of 576 | 0 of 576 | 576 of 576 |
| The thumb leaves after the stick is back, inside the window | 0 of 384 | 384 of 384 | 384 of 384 |

90.49 fixed the third row and not the second. The touch Release has added the
hold marker since 90.5.

The 1,728 are 2 layouts, `Steering` over Base and over `Gyro`, 2 drivers, up
and down, 3 surroundings (nothing else, the right thumb resting on its stick,
or on its pad), the two either-way assumptions each way (A9, A32), and 9 ways
of the push. The 9: the thumb stays on, with the ring pressed after the
direction or before it; a resting thumb leaves first; the thumb leaves inside
the window; each of those four with the thumb on the stick before the driver
goes down and after; and the thumb that lands with the tap and leaves first.

The right thumb does the same on its own stick: if it leaves the right stick
during the push, the right-stick touch Release adds the hold marker and the
tap is lost, before and after the plan's change. A right thumb that leaves its
stick while the left one holds up is usually reaching for a button of the map,
so the plan leaves it.

### What can't be computed

The tap rests on two more things. The simulator assumes both, and only the
Deck can say.

**The ring's Release (A8, A55).** The modifier ends on the ring's Release
(R111), and a Release needs its press.

| Releases | The ring's radius in the stick modifiers | When the ring is pressed |
|---|---|---|
| 90.10 to 90.30 | 4915, below the 13276 at which up and down start | Before the modifier lands |
| 90.31 to 90.48 | Not stated: Steam's default, near the rim (A50) | After it lands. A push too short to reach the rim never pressed it and left the modifier on |
| 90.49, 90.50 | 13276, the same number | In the same stick report. The modifier lands with the ring already out, unless Steam applies a new layer between reading the direction and reading the ring |

So since 90.49 every push most likely rests on A8: a ring's Release fires in a
layer that was added while the stick was already past the ring. A8 has never
been checked. The same for a button, A7, is verified. If A8 is false, a push
leaves the modifier on, and the next push, which starts with the modifier
already there, scrolls: every second tap.

**The 200 ms hold marker (A13).** The author's note of 2026-10-09: when layers
are added and removed in the same moment, a following delay can appear to fire
at once ([Delay Timers and Repeat Rates](../../resources/Delay%20Timers%20and%20Repeat%20Rates.md)).
The stick modifier has that shape. It lands on a direction that is held, its
reset removes the marker at once (A6), and the marker's 200 ms add follows. If
that add fires at once, every tap is a hold and no push scrolls.

One check tells the three apart, on 90.50 as installed. Hold a driver in
`Steering`, keep the left thumb on the stick the whole time and leave the
right thumb where it is. Tap up four times to the rim, a second apart.

| Wheel steps of the four taps | What it means |
|---|---|
| 1, 1, 1, 1 | A8 and the delay hold. The thumb leaving first is the fault |
| 0, 1, 0, 1 | A8 is false with the two numbers equal. The ring has to be pressed after the modifier lands |
| 0, 0, 0, 0 | The hold marker lands early, or something this record doesn't model |

The middle row is the simulator's, with the ring's press left out of every
push whose modifier isn't on yet.

The author's correction of the same day, that a deflect scrolls once and then
not again, is none of these three rows. Part 3 takes it up.

If those four scroll, four more taps that stop just past half way settle A55.
1, 1, 1, 1 says 90.49's radius is in effect. 0, 0, 0, 0 says the ring is still
near the rim: the eight groups' 13276 did not replace the radius of
`Steering`'s own group, which states none. On 90.34 a layer's `layout` didn't
replace the one under it either (A51).

## 3. The reported fault: a deflect scrolls once, then not again

On the simulator a deflect with the thumb on the stick scrolls every time: on
the twelve live releases from 90.38 to 90.50, each way of A9 and A32. Nothing
in the binds, as the tools read them, stops it after the first. So the Deck does
something the simulator assumes away, and what follows is a lead, not a
diagnosis.

### The one way the model gives "once"

For a second deflect to do nothing, the driver's W or S layer has to be gone
and stay gone while the driver is held: up and down then have nothing that
adds a stick modifier. One assumption turned off gives exactly that: a guard's
chord does not start when a removal uncovers its bind under an input that is
still held. That is A36, for the uncovering case. It is unverified.

Four deflects in a row, the driver held, a thumb resting on the stick, with
that one assumption off:

| Releases | Wheel steps | Why |
|---|---|---|
| 90.38 to 90.45 | 1, 1, 1, 1 | The W layer is removed after each window and `Steering` adds it again within 50 ms |
| 90.46 to 90.50, and with the plan's change | 1, 0, 0, 0 | The W layer is removed after the first window and never comes back |

What happens, on 90.50:

| ms | What happens |
|---|---|
| 360 | The stick is back: the ring's Release ends the modifier and opens the window |
| 510 | The window scrolls once and removes itself. The W layer is uncovered, under the resting thumb and the held driver |
| 510 to 610 | The W layer's stick-touch cleanup fires, because its guard, a chord with the driver, did not start. It removes the W layer |
| After that | `Steering`'s driver entry is uncovered too. Until 90.45 it was a repeating Regular Press, which adds the W layer again. Since 90.46 it is a chord of the driver with itself, which does not start either |
| The next deflect | No W layer answers. Short of the rim nothing happens. At the rim it is `Steering`'s own exit |

With no thumb on a stick as the window closes, every deflect scrolls. With the
driver let go and pressed again before each deflect, every one scrolls too.

The two Steering stick windows meet this on every use: they open on the
stick's ring while their own driver is still held and the thumbs rest. Every
other window opens on its owner's Release, so its owner is up when it closes.
It can still close over another button that is held.

### What speaks against it

- **The same assumption, off everywhere, breaks an everyday gesture.** Thumbs
  resting, L1 held past the cursor's 200 ms, then A: G on the simulator as it
  is. With the assumption off it is never a clean G, and in half the cases
  the modifier is gone. Nothing like that is on record.
- **The author's note of 2026-10-07** says a normal chord re-evaluates on
  Remove Layer, where an inverted one does not.

So if this is the cause, it is narrower than "no chord starts when it is
uncovered": only when an Always On layer removes itself, for one. That can't
be told from here.

### What would settle it

On 90.50 as installed, with the driver held and the left thumb on the stick,
deflect once for the scroll. Then:

| Observation | The W layer is being lost | It is not |
|---|---|---|
| Is W still held: is the driver still driving? | No | Yes |
| Let go of the driver, press it again, deflect | One more scroll | Still none |
| A deflect to the rim | Leaves `Steering`, with the pulse and the beep | Stays in `Steering` |
| The same deflects on 90.45, to the rim | Every one scrolls | Once there too |

If the W layer is not being lost, the next question is whether the other
direction still works once. That would point at one modifier's own 200 ms
delay (A12, A13) and not at anything the two share.

### Also on these inputs

Since 90.43 four inputs per layout have a cleanup function whose only guard is
a chord with a start delay: up in Modifier 1 and down in Modifier 0 (200 ms),
and up and down in `Steering | LS: Double Tap Cover` (5 ms). 90.42 had none.
The cleanup removes the modifier and both drivers' layers. Steam's text for
Interruptible says such a press waits for the other activator's conditions,
and "If those other activators fire, this one will not." It does not say what
a deflect let go inside the 200 ms does. Noted, not followed up: I found no
way from it to "once".

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

## Tried and dropped

**The thumb's lift opens the window itself:** the touch Release removes the
modifier and adds the window, as the ring's Release does. In the simulator
every push scrolls, and it would not need the ring's Release at all. But a
Release on a stick touch that removes the modifier makes the Cleanup audit
read the modifier as a stick-touch helper, kept by the thumb. The
`cleanup_lists` fix then rewrites 23 cleanup functions in the default layout:
the W and S layers' stop removing the two stick modifiers and both covers, and
the hold marker's stop removing the modifiers. The plan's change leaves the
fix pipeline and all four audits as they are.

## Not a finding

A first sweep also had the right stick pushed out. In the alternative layout a
soft pull of a trigger then brought in no W or S layer, and the push reached
`Steering`'s own exit. A full pull brings the layer in. That is the ramp
layers' block of the soft pull, as built, so the sweep leaves the right stick
at centre.

## Also found: tests that fail on 90.50 as it stands

All 99 test modules, 1,118 tests, were run on a scratch copy with the plan's
change installed, and the failing modules again on the repo itself. One test
fails because of the change: the 90.50 test that pins the override at `0`.
Six modules fail on the repo as it stands, without it:

| Module | Fails | Why |
|---|---|---|
| `test_double_tap_windows` | 1 test, 8 cases | Since 90.49. The R118 check can't read the wheel step in the two Steering windows' stick-touch Releases. That step completes a delayed output on a thumb's release, which R125 says not to do, and the register has no entry for it |
| `test_steering_entry_quiet_drivers` | 1 test | Since 90.49. It expects the W and S layers' stick group without a radius |
| `test_steering_rtp_menu_chords` | 5 of 5 | One since 90.49: the stick-touch completions lost the three click layers. Four older: three look up `Steering \| LS: Fallback Guard`, renamed in 90.43, and one compares the working layout with the 90.38 build |
| `test_neptune_gyro` | 1 test, 6 cases | Older: the right-stick sensitivities of 90.45 |
| `test_layer_report` | 1 test | Older: it expects `Gyro Off Ramp Up` under a modifier |
| `test_fallback_window_backport` | 1 test | Older: the 90.39 candidate's stored rules no longer match the register |

## Limits

- The simulator holds a control or doesn't. It knows no stick distance, no pad
  pressure and no haptic motor. Nothing in part 1 was simulated.
- The 10 ms between the thumb leaving and the stick coming back is my choice.
  In the simulator only the order matters.
- "With the plan's change" is 90.50 edited in memory by the probe. A scratch
  build of the same change, outside the repo, was left unchanged by the fix
  pipeline and passed the four audits on both layouts against 90.50.
