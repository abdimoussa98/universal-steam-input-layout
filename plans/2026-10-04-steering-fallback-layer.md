# Plan: the fallback is a layer the stick brings in and the bumpers take out

**Status, 2026-10-05:** built the same day as **90.33**
([record](../findings/2026-10-05-steering-fallback-guard/README.md)), on the
author's go-ahead. It is installed in `neptune/` with its snapshot; it has not
run on the Deck. It walks back the fallback window of
[90.31](2026-10-04-fallback-window.md) and its replacements of 90.32.

**90.34, the same day:** the author changed `Steering`'s side of it. The add
has no delay, `Steering`'s left stick is four-way and its stick edges are open
([record](../findings/2026-10-05-steering-four-way-and-open-edges/README.md)).
The tables below show 90.33.

What differs from the plan as written:

- **After a bumper hold with the stick let go, the fallback goes** in the
  simulator: its cleanup function answers the thumb resting at centre once the
  modifier leaves. The table below says it stays. The Deck may do either; the
  next bumper at centre drives both ways.
- **The register entries are scoped to the build** with a new `where` key,
  because the frozen builders read the same register.

**Third version.** The first, of 2026-10-04, had this model but asked whether
a bumper at centre should end the fallback. The second, of 2026-10-05, read
the author's "handoff" as a guard that ends when the stick is let go; that was
wrong. The author's third description settles both: the stick's release does
not end the fallback, and the bumpers do.

The reference is the July layout,
[MOST_RECENT_LAYOUT.post-fix.json](../findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json),
read in
[findings/2026-10-04-july-stick-clears](../findings/2026-10-04-july-stick-clears/README.md#4-its-fallback).
The plan is July's fallback, with today's Gyro modifiers, cleanup rules and
clear lists.

## Terms

- **Steering base:** `Steering` with nothing of its own on top. The stick's
  left and right are A and D, and the drivers type W and S.
- **Driver:** the button that drives. R1 for W and L1 for S in the default
  layout, the triggers in the alternative. The same two buttons are the
  **modifier pair** outside `Steering`. "Bumper" below means one of the pair.
- **The fallback:** the layer the left stick's up and down bring in when no
  driver is held, here `Steering | LS: Fallback Guard`. The author calls it
  the fallback guard.
- **Gyro modifiers:** `Gyro | L1: Modifier 0`, `Gyro | R1: Modifier 1` and the
  two `Gyro | … Modifier 2` layers (L2 and R2 in the alternative).
- **Base modifiers:** the same four without `Gyro |`.
- **The clear:** a menu button held plus a stick click. It goes through
  `Transition Set 2` and removes everything above Base except `Gyro`.
- **Quick tap of Modifier 2:** both of the pair pressed and let go inside
  200 ms, before `L1&R1: Tap Cover` lands.

## The author's design

2026-10-04: "I want to walk back the fallback window. Instead we'll follow
this [the July layout] pretty closely. We'll have in steering base 'w' and 's'
will add fallback guard and that layer will no longer be disposable. Every
time in steering base you push the left stick north or south you'll go there.
In there we'll have the gyro mod 0 & 1 add layer on their respective
bumpers/triggers. We'll need to update gyro mod 2 to also clear the related
steering layers and base mod layers too and update appropriate clean up
functions everywhere. I'll also want the mod 2 to clear the related gyro
layers so that whether you are in the fallback layer or are in the steering
ones if you press bumpers/triggers together it'll take you to the base layer
every time. Menu buttons in fallback should inherit from steering base so the
proper clear transitions layer is triggered, we might need to update what
layers get removed from there. That clear transition should still just clear
the steering layers, but also needs to include the mod 0-2 gyro layers but not
the gyro base layer. We want bumper/triggers to take you to base (clearing all
stateful layers) and stick & menu buttons to clean just your stateful layer."

2026-10-05: "I want like a handoff of sorts. So when you hold W, in the
fallback, first I want W or S to get into the fallback to have a strong haptic
bump so you know you're in the fallback. And from there if you hold the
bumpers you can actually let go of the stick and it's not going to clean up
because you're transferring the hold to the bumpers ... if you're in the
fallback and you press the bumpers, it'll actually remove the fallback before
you go in, because if you let go of either bumper and you go all the way back
to the base, the stick will be in the correct position to push you back into
the fallback layer."

2026-10-05, after the second version: "So we'll override up and down on the
fallback layer. That'll be W and S. So pushing the stick will get you into the
fallback layer, but releasing it won't. So the bumpers themselves will release
the fallback guard if you're going into steering."

## What it does

In Steering base:

| You | What happens |
|---|---|
| Push the stick up or down, no driver held | After 100 ms: a strong bump, the fallback, and W or S |
| Press a driver inside those 100 ms | The driver's layer takes the stick; no fallback |
| Everything else | As today |

In the fallback:

| You | What happens |
|---|---|
| Stick up, down | W, S, at once |
| Stick left, right | A, D, from `Steering` |
| Let the stick go | The fallback stays |
| Press a bumper with the stick out | That bumper's Gyro modifier, as in `Gyro`: a tap scrolls, a hold is Temp Cursor Gyro, the face buttons are its keys. The fallback stays underneath and keeps typing W or S |
| Let the stick go while that bumper is held | Nothing changes. After the bumper is let go the fallback is still on |
| Press a bumper with the stick at centre | A strong bump; the fallback goes and the bumper drives at once |
| Let that bumper go with the stick up or down | Steering base, so the fallback comes on again, with its bump |
| Lift a thumb and put it back on a stick, left stick at centre | The fallback goes: its cleanup function (R169). Not while a bumper is held |
| Quick tap of both bumpers | Everything is cleared, to Base, with the beep |
| Start or Select | `Steering`'s own: a tap is Tab or Escape, a hold is Fn |
| A menu button held plus a stick click | The clear: `Steering` and the fallback go, `Gyro` stays |

**Leaving `Steering` by holding the stick is gone:** the one second of 90.31
and the 1.5 s of 90.11.

Two things that follow:

- **Coming back to driving needs the stick at centre.** With the stick held
  left for A, R1 is the Gyro modifier, not W.
- **The Gyro modifier brings its own gyro.** If `Steering` was entered from
  Base with `Gyro` off, the gyro moves the mouse while a bumper is held in the
  fallback.

## The binds

`Steering`, left stick up and down:

| Entry | Today (90.32) | Planned, from July |
|---|---|---|
| The add | Regular Press repeating every 50 ms: adds the Fallback Hold, then the window | Chord on the left stick being out, 100 ms delay, strong pulse, uninterruptible: adds the fallback |
| Its reset | None | Regular Press repeating every 150 ms, uninterruptible: removes the fallback (R120) |

`Steering`'s driver press only adds the driver's layer. With the fallback on,
the fallback's own bind answers the bumper.

`Steering | LS: Fallback Guard`:

| Input | Planned |
|---|---|
| Up, down | W or S, uninterruptible. No Release |
| Left, right, the edge | Not bound: A and D come from `Steering` |
| Each of the modifier pair | July's two entries. A chord on the left stick being out, repeating every 50 ms, uninterruptible: adds its Gyro modifier. And a Regular Press repeating every 50 ms, with a strong pulse: removes the fallback |
| Start, Select | Not bound: `Steering`'s add of its `Stateful \|` Entry Point comes through |
| Both stick touches | A cleanup function that removes the fallback, held back while the left stick is out (R169) |
| The right stick's edge | Nothing. The fallback binds no button that R170 asks an edge cleanup for |

- July's chord also names the bumper itself. On the bumper's own input that
  adds nothing, and without it every guard in the layer is the same one: the
  left stick being out.
- The bumper's two entries are a cleanup function in shape (R133), so the
  bumpers carry theirs (R171).
- No modifier layer, Tap Cover or bumper window binds the stick's up or down
  (checked on all 90 layers). So under a held modifier the fallback's W and S
  answer the stick, and `Steering`'s add stays covered.

In the alternative layout the modifier pair is the two triggers' pull.

## One guard layer

The Entry Guard exists to type plain W when `Steering` is entered with the
stick held up. `Steering`'s own up and down now do that, entry included. So:

- `Steering | LS: Entry Guard` becomes `Steering | LS: Fallback Guard`.
- `Transition Set 1` stops adding a guard with `Steering`. With the stick held
  left at entry a guard would sit there and turn a bumper into a modifier.
- `Steering | LS: Fallback Hold` and `Steering | LS: Fallback Window` are
  deleted: 88 layers. The Fallback Hold is in the middle of the list, so the
  18 layers after it move up by one.

## The Gyro Modifier 2 quick tap

The Release of both buttons in `Gyro | L1!R1: Modifier 2` and
`Gyro | R1!L1: Modifier 2`:

| | Removes |
|---|---|
| Today | Itself, the three Tap Covers, the two Gyro modifiers, `Cursor Gyro`, `Gyro` |
| Planned | The same, and both Gyro Modifier 2 layers, the four Base modifiers, the fallback and `Steering` |

- The beep goes on the removal of `Steering` as well as on `Gyro`'s. Leaving
  `Steering` then beeps when `Gyro` was never on (R161).
- The Base modifiers can never be on together with a Gyro modifier, so the
  Cleanup audit would call them "never there" and the fix pipeline would take
  them out (R132). A register entry keeps them, with the author's words as
  its reason.
- From Steering base nothing changes: both drivers already reach
  `Steering | … Modifier 2`, whose quick tap clears everything to Base.

So both bumpers together end in Base from the fallback and from Steering base.

## The clear, and the other lists

The clear already does what the design asks. The Release of a stick click in
both `Stateful |` Entry Points removes every layer but `Gyro`, the Gyro
modifiers included, and adds `Transition Set 2`.

What changes:

- Every list that removes the window or the Fallback Hold loses that entry:
  14 and 13 layers. Every list that removes the Entry Guard removes the
  fallback.
- The Gyro modifiers and the menu layers can now sit over `Steering` and the
  fallback. The fix pipeline and the Cleanup audit work out again what each
  cleanup function, Release and window has to remove there. What they find
  goes on the fix list by the rules; only a race goes to the author.

## What stays from 90.31

No stick group states an outer ring radius: Steam's default.

## Rules, register and assumptions

| What | Change |
|---|---|
| R120 | The fallback's delayed add has its reset at 150 ms |
| R125 | Needs a new example: the fallback's second is gone |
| R132 | The entry that keeps `Steering` in the Fallback Hold's cleanup binds goes. A new entry keeps the Base modifiers in the Gyro Modifier 2 quick tap |
| R137 | No temporary guard is left in `Steering`: the fallback has no Release that a layer on top could hide |
| R157 | Steering's hold exit comes out of the exceptions. The Modifier 2 clear also runs from the Gyro modifiers |
| R161 | The Gyro Modifier 2 quick tap beeps on `Steering` too |
| R169, R171 | The fallback carries its cleanup functions: both stick touches and both of the modifier pair |
| R170 | The entry for the Entry Guard and the Fallback Hold goes with those two layers |
| R173 | Its example changes; the rule stays |
| R156 | The working layouts are the new builder's output |
| A10, reported | W or S as the fallback lands on a stick that is already out |
| A6, reported | `Steering`'s reset fires as `Steering` lands on a stick held up at entry, and the add follows |
| "A layer that binds an input eats its pending delay", established | A driver pressed inside the 100 ms cancels the add |
| A8, A36, A11 | Nothing in the fallback rests on them any more |

The description loses the paragraph on leaving `Steering` by the stick and
says what the bumpers do in the fallback.

## How it is built

A new builder,
`findings/2026-10-05-steering-fallback-guard/build_candidate.py`, in front of
the 90.32 builder, which stays frozen. Its `finish` works on the finished
layout: it deletes the window and the Fallback Hold, renames and rebuilds the
guard, rewrites `Steering`'s up, down and driver binds and the transition's
commit, extends the two Gyro Modifier 2 Releases, and cleans the lists. Each
step checks what it expects and stops the build otherwise. Then the usual: the
fix pipeline, the build audit, the change report against 90.32, the install,
the VDF, the snapshot in `versions/neptune/90.33/`.

## Tests

- New: the static contracts of the fallback, `Steering`'s add and reset, the
  Gyro Modifier 2 lists and the two deleted layers; scenarios for each row of
  the two tables above, for the 100 ms race with a driver, for a bumper held
  while the stick is let go and pushed again, for both bumpers from the
  fallback with `Gyro` on and off, for the clear from the fallback with a
  Gyro modifier held, and for entering `Steering` with the stick held up and
  held left.
- Rewritten or retired, each with a comment: the fallback and Entry Guard
  scenarios of 90.10, 90.11, 90.15, 90.30, 90.31 and 90.32,
  `test_fallback_window.py`, `test_fallback_window_replacements.py`,
  `test_steering_fallback_hold.py`, and the checks in
  `test_double_tap_windows.py`, `test_stateful_transitions.py` and
  `test_scenario_registry.py` that name the three layers.

## On the Deck, after the build

1. In `Steering`, push up: a bump and W after a tenth of a second. Let go and
   push again: W at once, no bump.
2. Stick at centre, press R1: a bump, and R1 drives.
3. Hold up, tap L1: a scroll step, W the whole time, no bump.
4. Hold up, hold L1, let the stick go, let L1 go, push up: W at once.
5. Hold up, quick tap of both bumpers: Base, with the beep. Try it with
   `Gyro` on and with it off.
6. Hold Select and click a stick: `Steering` is gone and `Gyro` is as it was.
7. Press R1 and push the stick up together, several times: R1 drives each
   time and no fallback comes on.
8. Enter `Steering` with the stick held up: W after the bump. Enter it with
   the stick held left and press R1: it drives.

## Filled in, for the author to check

1. **The stick decides what a bumper does in the fallback.** Out: its Gyro
   modifier. At centre: it ends the fallback and drives. That is July's split,
   and the only condition a bind can use to tell "going into steering" from a
   modifier.
2. **One guard layer.** The Entry Guard is folded into the fallback,
   [above](#one-guard-layer). The other way: the Entry Guard is left as it is,
   and there are two guard layers.
