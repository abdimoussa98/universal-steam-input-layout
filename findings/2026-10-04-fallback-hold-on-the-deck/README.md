# The Steering fallback hold on the Deck

**Status:** an investigation on 90.29, 2026-10-04. Nothing is changed. One
suspect, with a Deck check that settles it, and one fault that is in the
simulator too.

The **fallback hold** is what the left stick does in `Steering` with no bumper
held: up or down types W or S, pulses, and leaves `Steering` after 1.5 s. Its
layer is `Steering | LS: Fallback Hold`, added by `Steering`'s up and down.

## What the author saw

On the Deck, 2026-10-04: it "starts clicking or beeping"; going to east and
west "will pull me out, I think"; "sometimes it'll just block up and down
altogether", with no forward movement and "not bumping anymore"; and "I can't
reliably exit".

## What it is built to do

| You | What happens |
|---|---|
| Hold the stick up or down | W or S, a strong pulse every 250 ms from the start |
| Keep holding for 1.5 s | `Steering` ends, with the beep (audible since 90.29) |
| Roll to the left or right | The hold ends and its timer with it. A or D; `Steering` stays |
| Back to up or down | A new hold: W or S, the pulses, and 1.5 s from zero |

So the clicking is the pulses, and rolling to the side is meant to end the
hold, not `Steering`.

On the simulator all of this works. A sweep of 1,680 cases
([sweep.py](sweep.py)) with other inputs around the hold finds no case where
a stick that is held up or down types nothing.

## The author's two expectations

The author, 2026-10-04: rolling to east or west ending the hold with
`Steering` staying on is correct. "On the fallback though, W and S should be
bound. And there should be a delay fix on there as well. Because it feels
like ... sometimes I'm not getting into the fallback."

Both are there, as the author designed them on 2026-10-02:

| | Where | What |
|---|---|---|
| W and S | `Steering \| LS: Fallback Hold`, stick up and down | A Regular Press that types W or S |
| The delay fix | The same layer, the stick's outer edge | A Regular Press that repeats every 1550 ms and removes `Steering \| LS: Entry Guard`, a layer that is not on then. It restarts the 1.5 s exit if that delay is stuck |

Two things follow from how they are placed:

- **W and S are bound nowhere else.** `Steering`'s own up and down only add
  the hold. So whenever the hold layer is not on, up and down type nothing:
  "not in the fallback" and "can't move forward" are the same state.
- **Getting into the fallback has no delay.** `Steering`'s up and down add the
  hold at once and repeat every 50 ms. A delay fix restarts a delay, so there
  is nothing for one to fix on the way in. The one that exists serves the
  exit. It is on the edge because up and down already hold three entries.

Random gestures in `Steering` on the simulator ([fuzz.py](fuzz.py), 10,839
runs) never leave a layer on and never leave up without W, the hold and the
pulses. So the Deck is doing something the simulator doesn't.

## The suspect: the cleanup binds of 90.24

The required cleanups of 90.24 (R169 to R171) gave the layer four new binds.
Each is a repeating press that removes `Steering | LS: Fallback Hold`:

| Input | Removes the hold unless |
|---|---|
| Left stick touch | The left stick is out |
| Right stick touch | The left stick is out |
| Right stick, pushed | The left stick is out |
| Start and Select | The left stick is out |

"The left stick is out" is a chord on Steam's stick-deflection button (bit 30
of the chord mask). Before 90.24 the layer could only be removed by its own
Releases and its exit.

The left thumb is always on the stick during a hold. So since 90.24 the layer
survives only if Steam sees that chord at the moment the layer lands on the
thumb. A repeating bind fires as its layer lands (A6); a chord that is active
holds it back (A27), if the chord is decided as the layer lands (A36,
unverified). Nothing here has checked a stick-deflection chord that way, and
its threshold is not known. `Steering` adds the hold from 40% of the stick's
travel.

With that chord missed as the layer lands ([guards.py](guards.py)):

| Layout | Hold up for 2 s |
|---|---|
| 90.29 | The layer is added and removed 41 times. W is never down, no pulse, no exit |
| 90.23 | The layer stays. W for the whole 2 s, the pulses come; only the 1.5 s exit is lost |

That is "block up and down altogether" and "not bumping anymore". If the
chord is seen on some pushes and missed on others, the hold works on some and
is dead on others.

`Steering | LS: Entry Guard` got the same four binds in 90.24.

## A fault that is in the simulator too

Any layer removal restarts a delay that is counting (A13). Lifting the right
thumb from its stick fires layer removals, so it restarts the 1.5 s. The
hold's own reset then fires at 1.55 s and restarts it once more.

| During a hold | `Steering` ends at |
|---|---|
| Nothing else | 1.5 s |
| The right thumb taps its stick at 0.7 s | 3.05 s |
| The right stick is pushed and let go at 0.7 s | 3.05 s |
| The right thumb rests on its stick | 1.5 s |

It is the same on 90.23. A right thumb that keeps moving the camera can keep
the exit from coming.

## On the Deck

Load `versions/neptune/90.23/single-set-default_hold-gyro_90.23.vdf`, enter
`Steering`, and hold the stick up a few times, with and without the right
thumb on its stick. 90.23 has the fallback hold without the cleanup binds.

- **Reliable there:** the 90.24 binds are the cause.
- **The same trouble there:** they are not, and the stick-deflection chord
  itself is next: the hold's exit and its pulses use it too.

## A fix, not built

Take the four cleanup binds out of `Steering | LS: Fallback Hold`, as an
exception to R169 to R171. The layer's owner is the stick itself: a hold that
is left on after a missed release is used, not stuck, the next time the stick
goes up or down.

Open for the author: whether `Steering | LS: Entry Guard` loses its four too,
and whether the 1.5 s exit should survive a right-thumb lift.
