# How the July layout clears on the sticks, and its fallback

**Status:** a reading of the author's July layout on 2026-10-04, asked for by
the author: "see how this layout does the stick clears ... I'm pretty sure
that the fallback that I had built here actually works well." Nothing is
changed.

The layout is
[MOST_RECENT_LAYOUT.post-fix.json](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json).
Its steering layers are `Split Stick`, `Split Stick Fallback`,
`Split Stick: W Key` and `Split Stick: S Key`. [dump.py](dump.py) prints any
of its layers.

A **stick clear** is a bind on a stick that removes a layer left on after its
button was let go.

## 1. It almost never sets the outer ring radius

| Where | Radius |
|---|---|
| Base, left stick | 21700, inverted: the WASD modifier slot |
| Base, right stick | 32767 |
| The two Fn layers, both sticks | 21000 |
| Every other layer | Not stated |

The working layouts today state 4915 on the left stick in 34 layers and 7209
or 4915 on the right stick in 28. None of that is in the July layout. Those
values came later, from a calculation, and are below what the Steam editor can
set ([to-do](../../todos.md#investigations)).

## 2. Its stick clears

The same shape everywhere, on the right stick's outer edge and on both stick
touches:

| Entry | What |
|---|---|
| Regular Press, Hold to Repeat | Removes the layer and its helpers |
| Chord on the layer's own button, uninterruptible | Empty: holds the press back while the button is held |

On the left stick's edge the modifiers bind nothing (an empty press): Base's
left edge is the WASD modifier, so no clear goes there.

No layer ends on the Release of a stick's edge.

## 3. Where it needs "the stick came back", it uses a Soft Press with a threshold

The turn-assist layers on the right stick:

| Layer | Edge bind | Threshold |
|---|---|---|
| `Gyro Off Ramp Up` | Soft Press, 5 ms: adds `Turning Ramp Up 0` | 29031 |
| | Inverted Soft Press, repeating: removes the layer | 25807 |
| `Turning Ramp Up 0` | Soft Press, 250 ms: adds `Turning Ramp Up 1` | 29031 |
| | Inverted Soft Press, repeating: removes the ramp layers | 29031 |
| `Turning Ramp Up 1` | Inverted Soft Press, repeating: removes the ramp layers | 25807 |

An inverted, repeating Soft Press fires for as long as the stick is inside its
threshold. The threshold is the activator's own setting, on its own scale, and
has nothing to do with the outer ring radius.

`Split Stick Fallback` has three more of these on the left stick, with
thresholds 9738, 13769 and 16188, removing the fallback when the stick comes
in. All three are in groups the layer does not use. That fits what the author
found on 2026-10-01 (A19): an inverted edge is not caught reliably on a D-pad
stick.

## 4. Its fallback

| Layer | Input | Bind |
|---|---|---|
| `Split Stick` | Up, down | Chord on the left stick being out, 100 ms, strong pulse, uninterruptible: adds `Split Stick Fallback` |
| | Up, down | Regular Press repeating every 150 ms: removes `Split Stick Fallback`. The delay fix, on the same input |
| `Split Stick Fallback` | Up, down | W, S |
| | Left, right | Not bound: A and D come from below |
| | Either bumper, left stick out | Chord on the left stick being out and the bumper itself, both required, repeating every 50 ms, uninterruptible: adds that bumper's Gyro modifier (`*L1: Modifier 0`, `*R1: Modifier 1`) |
| | Either bumper, left stick at centre | Regular Press repeating every 50 ms, strong pulse: removes the layer |

**Corrected 2026-10-04.** The first version of this table left out the chord
row and said a bumper only removes the layer. With the stick out a bumper is
the normal Gyro modifier; only at centre does it end the fallback.

That is all. The fallback layer has no Release, no timer, no pulse, nothing on
the edge and nothing on the touch. Once it is on it stays on, through centre
and through A and D, until a bumper is pressed with the stick at centre.
Nothing in it can take W or S away while the stick is held.

Both bumpers together from there reach `*L1!R1: Modifier 2`. Its quick tap
removes `Split Stick`, `Split Stick Fallback`, the Base modifiers, the Gyro
modifiers, the covers and `Gyro`: everything, to Base.

## Against the fallback of today

| | July | 90.30 |
|---|---|---|
| Getting in | A 100 ms delayed add, with its delay fix on up and down | An add at once, repeating every 50 ms |
| W and S | In the fallback layer | The same |
| Leaving W or S | The layer stays | The Release removes the layer |
| Stick at centre | The layer stays | Gone already |
| Leaving `Steering` | Both bumpers' quick tap, through the Gyro modifiers. No exit by the stick | A 1.5 s chord on up and down |
| The pulse | One, as the layer comes on | Every 250 ms, on the outer edge |
| The outer edge | Not used | The pulse and the delay fix |
| Cleanup binds in the layer | The two bumpers | Stick touches, the right stick's edge, Start and Select (90.24) |
| Outer ring radius | Not stated | 4915 |

## What it suggests

1. **Drop the outer ring radius from the layers that don't need one.** July
   ran without it.
2. **Don't hang an exit on the edge's Release.** July never does. The stick
   modifiers and the Entry Guard do today.
3. **Keep the fallback layer small.** July's holds two keys and one way out.
   Each thing added since (the Release, the exit, the pulse, the cleanup
   binds) is something that has to work as the layer lands on a stick that is
   already out.
4. **Enter the fallback through a short delay with its delay fix**, as July
   does, not through a repeating add.

What July does not have, and the author asked for on 2026-10-02: leaving
`Steering` by holding up or down, the pulses, and the hold ending on A and D.
Those have to be decided again, not copied.
