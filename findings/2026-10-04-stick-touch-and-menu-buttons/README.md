# Stick touches and the menu buttons

**Status:** an investigation on 90.29, 2026-10-04. Nothing is changed. The
simulator shows three ways a stick stops a menu button; it does not show the
early beep the author heard. Two questions for the author are at the end.

Start and Select are the menu buttons. The **Fn beep** is the beep on the Fn
layer's delayed add, 200 ms into a menu hold.

## What the author saw on the Deck

1. "the menubuttons weren't working when touching them" (the sticks).
2. "after releasing the stick touches the menu buttons were immediately beeping
   as if the fn layer was applied."

## What the layout does, on the simulator

[sweep.py](sweep.py) runs 1,152 cases: a thumb on either stick (resting,
pushed, or lifted 10 to 260 ms before), then a tap or a 700 ms hold of either
menu button.

| The stick | A menu tap | A menu hold |
|---|---|---|
| Thumb resting, stick centred | Types Escape or Tab | Fn at 200 ms, with the beep |
| Stick pushed, still out | Types Escape or Tab | No Fn, however long |
| Stick pushed, back to centre inside 200 ms of the menu press | | Fn 200 ms after the stick is back, with the beep. At once and silent if the thumb also lifts |
| Thumb lifts during the hold, stick centred | | Fn at once, silent |
| Touch shorter than 150 ms, lifted less than 200 ms ago | Nothing | Fn 210 to 490 ms after the press |
| Right stick pushed and let go, thumb off less than 200 ms ago | Nothing | Fn 210 to 490 ms after the press |
| Thumb off for more than 200 ms | Types Escape or Tab | Fn at 200 ms |

Three mechanisms are behind the rows where a menu button doesn't do its job.

### 1. The stick guards (90.10)

In `Menu Left: Entry Point` and `Menu Right: Entry Point` a stick that is out
adds `Menu Buttons: Left Stick Guard` or `Menu Buttons: Right Stick Guard`.
The guard holds the Fn layer off. After 200 ms it adds `Menu Buttons: Tap
Cover`, which uses up the hold: no Fn comes until the menu button is pressed
again.

"Out" here is 15% of the stick's travel (`edge_binding_radius` 4915 of 32767),
far less than the 40% at which the right stick's directions start. A thumb
that leans on a stick can be past it.

This is the description's "Fn waits until both sticks are centered", and the
author checked it on the Deck on 2026-10-01 (A15).

### 2. A stick's Double Tap window blocks both menu buttons

`LST: Double Tap` and `RST: Double Tap` are on for 200 ms after a stick touch
ends while its Tap Cover is not on. Both bind Start and Select to nothing,
because no layer command may run under an Always On layer (R140).

The Tap Cover is not on in two cases:

- **A short touch:** the thumb was down for less than 150 ms.
- **The right stick after a push:** pushing it adds the ramp-up layers, which
  take the stick's touch over and stop the Tap Cover's delay. If the thumb
  comes off as the stick returns, the window opens however long the touch was.

So for 200 ms after a thumb leaves the right stick in normal play, a menu tap
is lost and a menu hold starts late.

### 3. The thumb-lift entry (since 90.9 or earlier)

With a menu button held, lifting a thumb from either stick adds the Fn layer
at once, as lifting it under a modifier adds the cursor response. This add has
no beep.

## What the simulator does not show

In no case does the Fn layer come sooner than 200 ms after the menu press, and
in no case does it beep at the moment a thumb lifts. If the Deck beeped at
once, Steam did something there that the simulator doesn't model.

Two candidates, both on assumptions that are not verified:

- **A14 and A16:** when a guard comes off and the Fn layer's delayed add is
  answering the held button again, the simulator starts its 200 ms from zero.
  If Steam counts from the button's press, the add fires the moment the guard
  goes: an Fn beep as the stick is let go.
- **A12:** a delayed add that was interrupted is left in a bad state, which is
  why every delayed add has a reset. The author's observation was that it can
  fail to fire on the next press. Firing at once on the next press would be
  the same fault from the other side.

## Reproduced: a menu release lost inside the right pad's window

The author, later on 2026-10-04: touching the pad and a menu button "at the
same time", and then "the subsequent click will just immediately go to the FN
layer."

This one is on the simulator ([pad_sweep.py](pad_sweep.py): 184 of 2,700
cases leave a layer on).

`RTP: Double Tap` is the window that is on for 150 ms after a touch of the
right pad shorter than 150 ms. It binds Start and Select to nothing. A menu
button that is let go inside it has its Release covered: the layers that
button holds stay on with nothing held.

| Time | You | What happens |
|---|---|---|
| 0 ms | Select down | `Menu Left: Entry Point` |
| 200 ms | | `Menu Left: Fn Layer`, with the beep |
| 300 ms | Thumb on the right pad | `RTP: Entry Point` |
| 360 ms | Thumb off | `RTP: Entry Point` goes, `RTP: Double Tap` comes on |
| 410 ms | Select up | Nothing: the window answers Select |
| 510 ms | | The window ends. The Entry Point and the Fn layer are still on |
| Later | Select down | The Fn layer answers at once |

With the pad touched first and Select let go before 200 ms, only
`Menu Left: Entry Point` stays on. The next Select release clears it.

The same happens to a modifier: L1 let go inside the window leaves
`L1: Modifier 0` and `L1: Temp Cursor Gyro` on. The left pad has no window
and doesn't do this. The 90.9 snapshot does the same, so it is not new.

It is the known gap of the [touchpad exception](../../todos.md#steering) to
the hidden-exit rule (R136), set aside by the author on 2026-10-02 with its
fix undecided: "`RTP: Double Tap` binds the buttons whose Releases other
layers need."

A fix in the pattern of 90.28, not built: in `RTP: Double Tap`, give Start,
Select and the two bumpers a Release that removes the window first and then
that button's own layers, as the stick touches and the pad's touch have in
the other windows.

## The author's candidate: the stick Entry Points' delay fix

The author, 2026-10-04: could the repeated removal on the stick touches be
behind this, and isn't it covered by the Tap Cover?

By the layout it is covered. The reset on `LST: Entry Point` and
`RST: Entry Point` stops answering the touch as soon as a layer above binds
that touch:

| What covers it | When |
|---|---|
| The stick's Tap Cover | 150 ms into the touch, before the first repeat at 200 ms |
| A menu Entry Point | The moment a menu button goes down: it binds both stick touches |
| A modifier, or the right stick's ramp-up layers | The moment they come on |

On the simulator the reset fires once as the thumb lands, once more when the
ramp-up layers come off a right stick that was pushed, and never during a menu
hold. A menu hold lands at 200 ms in every case.

It would be the cause only if Steam keeps a repeat running after a layer
covers its input. No assumption row says either way; A15 covers a running
delay, not a running repeat. The reset would then fire every 200 ms for as
long as a thumb rests on a stick, and each removal restarts the Fn layer's
200 ms delay (A13). That fits both observations: no Fn while touching, and
the Fn beep shortly after the thumb comes off.

Two ways to settle it:

- **The pad on 90.28.** Its reset pulsed. One pulse per touch means the cover
  stops the repeat. A pulse every 200 ms while the thumb rested means it
  doesn't.
- **A trial copy of 90.29 without the two stick resets.** If the menu buttons
  work there with a thumb resting, the resets are the cause.

## What is new here and has not run on the Deck before today

| Release | Change |
|---|---|
| 90.24 | A cleanup function on both stick touches and both stick edges of the menu Entry Points: a repeating press that removes the Entry Point, kept quiet by a chord while the menu button is held. `L1: Modifier 0` has had the same pair on its stick touches since the July layout |
| 90.25 | The Tap Cover reset on `LST: Entry Point` and `RST: Entry Point` |
| 90.26 | Every hold delay at 200 ms |
| 90.28 | The Fn layers add the chorded chain's Entry Point |

## Questions for the author

1. **Which gesture failed:** a tap (no Escape or Tab) or a hold (no Fn)? And
   was the stick only touched, or moved?
2. **The beep:** did it come while the menu button was still held, at the
   moment the thumb left the stick? Or on a later, fresh press of the menu
   button?

## On the Deck, to tell them apart

1. Rest a thumb on the right stick without moving it. Tap Select: Escape. Hold
   Select: the Fn beep at 200 ms. If either fails, the fault is in the touch
   alone, and the 90.24 cleanup functions are the first suspect.
2. Push the right stick, hold Select for a second, let the stick go: nothing
   should come. An Fn beep there points at the guard's Tap Cover.
3. Push the right stick, press Select and let the stick go at once: the Fn
   beep should come 200 ms after the stick is back. At once points at A14.
4. Flick the right stick and let go, then tap Select at once: nothing is
   typed. That is the window of mechanism 2.
