# The menu Entry Points' stick-touch binds: their order and where it came from

**Status:** an audit on 90.35, 2026-10-06, asked for by the author. Nothing was
changed by it. [90.36](../2026-10-06-cleanup-entry-order/README.md) then gave
every cleanup input one stored order, on the author's word. The author sees "some oddities" with Start, Select and the stick
touches; this does not find the cause, and says what would.

**Later follow-up:** the [July Base-menu comparison and 90.37 change](../2026-10-06-menu-base-chords/README.md)
restore July's repeating, uninterruptible self-chords on Base's Start/Select.
The author now wants that activator difference investigated as the candidate
cause of the missing Fn layer, with the broader delay tests deferred. The
cleanup-order experiment below remains part of the history, not a proven cause.

- **Menu Entry Points:** `Menu Left: Entry Point` (Select) and
  `Menu Right: Entry Point` (Start), and their `Stateful |` copies for
  `Steering` and `Cursor Gyro`. Each is on while its button is held.
- **Stick-touch layers:** `LST: Entry Point`, `LST: Tap Cover`,
  `LST: Temporary Gyro` and `LST: Double Tap` for the left stick, and the same
  four with `RST` for the right. The first three are the stick's **trio**.
- **Cleanup function:** a repeating Regular Press that removes a layer whose
  button is no longer held. Its **guard** is a chord on that button, on the
  same input, which holds it back while the button is held (R133).
- **Entry:** one activator on an input. The order here is the order the
  entries are stored in, which is the order the Steam editor lists them.

## The short answers

| Question | Answer |
|---|---|
| Is "regular press, release, guard" common? | No. Only the four menu Entry Points have it: 8 inputs. 56 other layers have "regular press, guard, release" on their stick touches: 112 inputs |
| Was it always like this? | No. From the July layout to 90.23 the touch had two entries: the Release, then the guard. There was no regular press |
| When did it change? | In 90.24, on 2026-10-04: the required cleanups (R169) gave every layer a cleanup function on both stick touches. In the Entry Points it was put in front of the two entries that were there |
| Did the split cause it? | No. The split of 2026-09-27 (commit `a4c2fe5`) only turned the two guards into one per layer, and made the right-hand layer add its own Fn layer |
| Does the order matter? | Not known. The simulator gives the same result either way. See [below](#does-the-order-matter) |

## What is on a stick touch in an Entry Point today

Both sticks, all four layers, in the stored order:

| # | Entry | What it does |
|---|---|---|
| 1 | Regular Press, Hold to Repeat | Removes the Entry Point. The cleanup function: it is for a release that was missed, and fires on a touch when the menu button is not held |
| 2 | Release, no haptic | Adds the Fn layer, then removes that stick's trio. So lifting a thumb during a menu hold brings Fn at once, without the beep |
| 3 | Chord on the layer's own menu button, uninterruptible, empty | The guard: with the button held, entry 1 does nothing |

## How it got there

[history.py](history.py) prints these binds for every saved version.

| When | The touch in the menu Entry Point |
|---|---|
| Before the split (85.8) | One layer, `Menu Buttons: Entry Point`. Release (adds `Menu Left: Fn Layer`, removes the trio), then a guard for Select, then a guard for Start |
| The split, 2026-09-27 | Two layers. Release, then one guard: Select's in the left layer, Start's in the right. The right layer's Release adds `Menu Right: Fn Layer` |
| 90.4 to 90.23 | The same |
| **90.24** | **A cleanup function in front: Regular Press, Release, guard** |
| 90.25 to 90.27 | The Release also added the chorded chain's Entry Point |
| 90.28 to 90.35 | As 90.24. The `Stateful \|` copies add their own Fn layers |

The 90.24 builder has one branch for "an owner chord is already there". It
writes the new Regular Press and then copies the old entries after it, in the
order they had. Every other branch writes Regular Press, guard, Release. So the
Entry Points kept July's "Release, then guard" behind a new first entry.

## Against the other stick cleanups

[order.py](order.py) counts the stored order on every stick input that has a
cleanup function and a guard. On 90.35:

| Input | Order | Inputs | Layers |
|---|---|---|---|
| Touch | Regular Press, guard, Release | 112 | 56 |
| Touch | **Regular Press, Release, guard** | 8 | The four menu Entry Points |
| Touch | Release, Regular Press, guard | 4 | `L1: Scroll Down`, `R1: Scroll Up` |
| Edge | Regular Press, guard | 40 | 20 |
| Edge | guard, guard, Regular Press | 32 | 16 |
| Edge | Regular Press, guard, Release | 6 | 6 |
| Edge | guard, Regular Press | 5 | 3 |
| Click | Regular Press, guard, guard | 16 | The eight modifier layers |
| Click | guard first | 8 | Four Steering modifier layers |

So there is no one order across the layout: the edges and clicks have the
guard first about as often as last. On the touches, though, the Entry Points
are the odd ones out.

Two more things set those four apart from every other menu layer:

- **Their guard is written the old way**, as `chord_button` 15 or 14. The Fn
  layers, the stick guards, the menu Tap Cover and the chain layers use the
  button mask (4096 for Select, 16384 for Start, 20480 for either). The old
  form is in 115 other chords for each button, and those work.
- **Their guard names only the layer's own button.** The Fn layers and the
  stick guards name either menu button.

## Does the order matter

- **The tools' verdict:** no. The simulator does not read the order of the
  entries, and none of the sequences below changes when two entries that are
  due together are taken in the other order (A32).
- **What is not known:** how Steam orders a Regular Press and its guard when
  the layer lands on a thumb that is already resting. The layout assumes the
  guard is decided at that moment (A36, unverified) and that it then holds the
  Regular Press back (A27, reported). The modifiers have had this shape on the
  stick touches since 2026-09-28 and work with thumbs resting. The Entry
  Points have had it only since 90.24, and with a Release between the two.
- **My judgment:** the order is the one structural difference on this input,
  so it is worth making it the common one before looking further. It is not
  evidence that the order is the cause.

If the guard did not hold on a resting thumb, this is what would happen: the
Entry Point lands, its cleanup fires on the thumb and removes it, and Base's
repeating bind adds it again, over and over. Fn would never come while a
thumb rests on a stick, and would come once the thumb lifts. The author
reported something like that on 90.29 ("the menubuttons weren't working when
touching them"), and 90.30 took the Tap Cover resets off for it. That fix has
not been confirmed on the Deck.

## What is written online

Searched on 2026-10-06, after 90.36 was built. Nothing found says the stored
order of an input's entries changes what Steam does, and nothing says it
can't.

| Source | What it says |
|---|---|
| [Valve's activator page](https://partner.steamgames.com/doc/features/steam_controller/activators) | Nothing about order. "Interruptable activators can be paused or stopped by other activators", with Long Press and Double Press as its examples. Of the Chorded Press it says only that the chord button must be held as the input is pressed; it does not say a chord interrupts anything |
| [A 2020 Steam Controller thread](https://steamcommunity.com/app/353370/discussions/0/3014556944200392295/) | "Currently chord presses will work to bypass a regular press only ... not if you need to bypass a regular style release press." So a chord holds back a Regular Press on the same input, and never a Release. That agrees with A27 |
| [A 2016 thread](https://steamcommunity.com/app/353370/discussions/0/358415738210221380/) | "Make the first Press Be Regular Press, Double Press next, Long Press last": advice on how to set a button up, with no claim that the order changes anything |

A search summary also said the chord button "needs to be active first",
before the input that carries the chord. The page behind it could not be
opened, so it is not confirmed. If it is right, a thumb that rests on a stick
before the menu button goes down is the case to worry about, whatever the
stored order; the modifiers have the same shape and work with thumbs resting,
which speaks against it (A36).

## The Entry Points and the stick-touch layers, on the simulator

[sequences.py](sequences.py) replays six gestures for each menu button and
each stick, on both layouts, four ways each (A9 and A32 either way).

| Gesture | What happens |
|---|---|
| Thumb resting, a tap | Escape or Tab. The stick's Entry Point and Tap Cover stay under it |
| Thumb resting, a hold | Fn at 200 ms, with the beep. After the button is let go the stick's two layers are still there |
| Thumb resting, lift it 100 ms into the hold | Fn at once, silent. The stick's layers go |
| Hold, then put a thumb on a stick | Nothing at the touch: no stick layer comes while the button is held. Fn at 200 ms. After the button is let go the stick's Entry Point and Tap Cover come on for the resting thumb |
| Hold, touch and lift inside 80 ms | Fn at the lift, silent |
| The menu release is missed, then a fresh touch | The touch clears the Entry Point and the Fn layer. Before 90.24 it did not |

Only the last row depends on an assumption (A9), and only in whether the
stick's Tap Cover follows. Against 90.23 the last row is the one thing that
differs, which is what the cleanup function was added for.

## Other ways a stick stops a menu button

Known from the
[90.29 audit](../2026-10-04-stick-touch-and-menu-buttons/README.md), and still
in 90.35:

- **A stick's Double Tap window blocks both menu buttons** for 200 ms after a
  touch shorter than 150 ms, or after the right stick was pushed and let go.
  A tap inside it types nothing, and a hold gets Fn late.
- **A stick at its rim holds Fn off**, through the stick guards.

## What would tell

On the Deck, with either layout:

1. Rest a thumb on a stick for a second, then hold Select for a second. The
   Fn beep should come at 200 ms. If it doesn't, the cleanup is firing under
   its guard.
2. Thumbs off both sticks, hold Select, and put a thumb on a stick before
   200 ms. The beep should still come at 200 ms.
3. Rest a thumb, hold Select, lift the thumb at once. Fn should be there with
   no beep.

And what the oddity looks like: which button, which stick, thumb resting or
moving, and whether it is a missing Fn, an early one or a lost tap.

## What could be changed

Not built. In order of how little they touch:

1. **Give the four Entry Points the common order**: Regular Press, guard,
   Release. One step in a new builder; nothing changes on the simulator.
2. **Write their guard as the button mask**, like the other menu layers.
3. **Take the stick's Double Tap window off the menu buttons' path**, if the
   oddity is a lost tap right after a short touch. That one needs a design.

## Files

| File | What |
|---|---|
| [history.py](history.py) | The binds through every saved version |
| [order.py](order.py) | The order survey |
| [sequences.py](sequences.py) | The six gestures on the simulator |
