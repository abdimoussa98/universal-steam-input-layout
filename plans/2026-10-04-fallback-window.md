# Plan: the fallback's timer moves into a window, and the outer ring is fixed in every layer

**Status, 2026-10-04:** built the same day as **90.31**, one release
([record](../findings/2026-10-04-fallback-window/README.md)). It is installed
in `neptune/` with its snapshot; it has not run on the Deck. The design is the
author's, described by voice and clarified three times.

**90.32, the same day:** the author replaced one part after seeing it built.
In the window a driver or a menu button no longer removes the window: the
drivers scroll and Start and Select type Tab and Escape, and no layer changes
([record](../findings/2026-10-04-fallback-window-replacements/README.md)). The
tables below show 90.31.

**Walked back, the same day:** the author dropped the window for a fallback
layer that the stick brings in and the bumpers take out, as in the July layout. The plan for that is
[2026-10-04-steering-fallback-layer.md](2026-10-04-steering-fallback-layer.md);
it is built as 90.33. Part 2 below stays; the Entry Guard of part 3 became the
fallback guard.

What differs from the plan as written:

- **The new layer is added to the finished layout**, not inside the build
  before the required cleanups. A window gets no cleanup functions, and the
  fix pipeline gives it its blocks at install either way.
- **The fix pipeline shortens the Fallback Hold's Release** to the three
  layers that can be on with it: the Fallback Hold, the window and `Steering`.
- **A register entry keeps `Steering` in the Fallback Hold's cleanup binds.**
  The pipeline had taken it out, because a cleanup function never removes a
  stateful layer (R131). The Cleanup audit was changed to honour the entry.
- **No assumption about two layers landing together is needed.** The Fallback
  Hold has nothing that fires as it lands: its up and down are a key and a
  Release.

Three parts: the fallback window, the outer ring radius of every Steering
layer, and the rest: the outer ring in the other layers and the Entry Guard.
The author approved all three on 2026-10-04.

The **fallback** is what the left stick does in `Steering` with no driver
held: up or down types W or S, and holding it for a second and letting go
leaves `Steering`. A **driver** is the button that drives: R1 for W and L1 for
S in the default layout, the triggers in the alternative. A **window** is a
layer with an Always On timer that removes it.

## 1. The fallback window

### The author's design

First description: "If you go up and down, it's not going to do anything other
than add a window that has north and south bound to W and S. And when that
window expires, underneath it will be the current fallback ... I want the
timer to not live in the fallback layer. I want it to live in a window ...
it'll just be a full second. We won't even need the delay fix because it
doesn't apply to windows."

The clarification: "once you are in the window you'll be in the north or south
region. If you release from the edge bind it'll clear both the window first
and then the fallback. If you stay in that region for the full second the
window closes and you'll be in the fallback in the north or south region with
a release bind that once released clears all steering layers necessary. The
bumpers and menu buttons and edge binds and touch binds should all have clean
ups to clear the steering layers as well, guarded by that left stick deflect."

The second clarification: "In the window, if you release W or you release S,
those clear the window. So you can roll to A, you just will be out of the
window ... if you're in the window and you press the bumpers, or the menu
button, it also clears the window. And when it clears the window, it also
clears the fallback as well. So if you ever exit the window manually, it'll
clear the fallback ... If you hit the bumpers or the triggers ... it'll clear
you from all the steering if you're in the fallback. If you hit a driver
within the window, it only clears the window and the fallback ... the pulse
can just live on north or south, in the window."

The correction: "If you're in the window, and you press either of the drivers
or a menu button, it'll just remove the window and you'll go into the fallback
and it'll clear you out completely. That's a little bit more sound, versus ...
add[ing] the other layers because the stick's still up."

### How it works

One layer is added, `Steering | LS: Fallback Window`, at the end of the layer
list: 90 layers.

| Time | You | What happens |
|---|---|---|
| 0 ms | Stick up | `Steering`'s up adds `Steering \| LS: Fallback Hold`, then the window on top. The window types W |
| Before 1000 ms | Let up go, or the edge lets go | The window goes, then the Fallback Hold. `Steering` stays |
| Before 1000 ms | Press a driver or a menu button | The window goes. The Fallback Hold is on top and clears the Steering layers: out of `Steering` |
| 1000 ms | Stick still up | The window's timer removes it. The Fallback Hold is on top and types W |
| After that | Let up go, or press a driver or a menu button | The Fallback Hold clears the Steering layers: out of `Steering`, with the beep |

So the gesture to leave `Steering` is: hold up or down for a full second, then
let go. Nothing leaves `Steering` while the stick is still held.

### The three layers

#### `Steering`, up and down

| Bind | Today | Plan |
|---|---|---|
| Regular Press, repeating every 50 ms | Adds the Fallback Hold | Adds the Fallback Hold, then the window |

#### `Steering | LS: Fallback Window` (new)

| Input | Bind | What it does |
|---|---|---|
| Always On | 1000 ms | Removes the window |
| Up, down | Regular Press | W, S |
| Up, down | Release | Removes the window, then the Fallback Hold |
| Up, down | Chord on the stick being out, repeating every 250 ms, no start delay | The strong pulse |
| Left, right | Regular Press | A, D |
| Outer edge | Release | Removes the window, then the Fallback Hold |
| The two drivers, Start, Select | Regular Press | Removes the window, and nothing else. The Fallback Hold underneath then answers the button |
| Both stick touches, the right pad's touch | Release | Removes the window, then the Fallback Hold, then that input's own touch layers |
| Everything else | | The window rules (R140 to R149), as in the two Steering windows there are today |

**Two ways out of the window leave the Fallback Hold on top: the timer, and a
driver or menu button.** Every other way out (up or down let go, the edge let
go, a thumb lifted) removes the Fallback Hold with the window, and `Steering`
stays. If one of those removed the window alone, the Fallback Hold would be on
top before the second was up, and letting go would leave `Steering` early.

**A driver or a menu button pressed in the window leaves `Steering`.** The
window's bind removes the window only. The button is still down, and the
Fallback Hold's bind for it clears the Steering layers. That bind repeats, so
it fires on a button that was already down when the layer came on top. With
`Steering` gone, nothing is left to put the window back.

#### `Steering | LS: Fallback Hold`

| Input | Today | Plan |
|---|---|---|
| Up, down | W or S; the 1.5 s exit; a Release that removes the layer | W or S; a Release that clears the Steering layers, with the beep and the strong pulse |
| Left, right | A, D from `Steering` | Unchanged |
| Outer edge | The pulse; the delay fix | Nothing |
| The two drivers | Nothing of its own: `Steering`'s bind hands over to the driver | A repeating press clears the Steering layers, with the stick out or not (author) |
| Start, Select | Tab or Escape while the stick is out; a cleanup bind that removes the Fallback Hold | A repeating press clears the Steering layers, with the stick out or not (author). No Tab or Escape here any more |
| Both stick touches, the right stick's edge | A cleanup bind that removes the Fallback Hold | The cleanup bind clears the Steering layers |

A **cleanup bind** is a repeating press that does what a missed Release would
have done, with a chord that holds it back while the layer's owner is held.
Here the owner is the left stick being out. The left stick's own edge can't
carry one: it is only out when the stick is, which is the guard (R170's
exception today).

"Clears the Steering layers" is the list today's 1.5 s exit runs: the Fallback
Hold, the Steering windows and covers, the stick modifiers, the drivers'
layers, the Entry Guard and `Steering`.

### What the design gains

- **The only timer left is the window's** (author, 2026-10-04: "we won't be
  having timers anymore unless it's the window"). It is one second and has no
  delay fix. Steam caps a delay and a repeat rate at 1000 ms
  ([limits](../resources/Steam%20Input%20JSON%20Structure.md#limits-the-steam-editor-sets)),
  so today's 1500 ms exit and its 1550 ms delay fix probably both run at
  1000 ms and collide. The pulse loses its 5 ms start delay too: a repeating
  bind fires as its layer lands (A6).
- **Nothing in the Fallback Hold fires as it lands.** Its up and down are a
  key and a Release. It lands under the window on a stick that is up, and
  there is nothing there to go off early.
- **The exit is a Release.** It needs the stick to have been held past the
  second and then let go.

### Decided

The author, 2026-10-04:

1. **Up or down let go inside the second clears the window and the Fallback
   Hold.** "You can roll to A, you just will be out of the window."
2. **A driver or a menu button pressed in the fallback leaves `Steering`.**
3. **A driver or a menu button pressed inside the second leaves `Steering`
   too.** The window's bind removes only the window, and the Fallback Hold
   does the rest. A first version cleared the two layers and added the
   driver's layer; the author replaced it with this.
4. **The pulse lives on up and down, in the window.**

## 2. The outer ring in the Steering layers

The author, 2026-10-04: "we will be fixing the outer edge binds in all of the
steering layers." And earlier the same day: "why are they being set? It should
just be the default outer bind threshold."

### What is there

| Stick | Layers | Radius |
|---|---|---|
| Left stick (D-pad) | All thirteen Steering layers | 4915, not inverted |
| Right stick (mouse) | Eight: the two stick modifiers, the two Modifier 2 layers, the two drivers, the Entry Guard, the Fallback Hold | 7209, not inverted |

The editor's Outer Ring Command Radius on a D-pad goes from 10,000 to 32,000,
so 4915 is not a value it can set
([limits](../resources/Steam%20Input%20JSON%20Structure.md#limits-the-steam-editor-sets)).

### The change

No Steering layer states a radius on either stick, and the new window doesn't
either. Steam's default applies. "Not inverted" is stated on every one of
them (author, 2026-10-04: "I want Steam's default radius. And explicitly not
inverted ... we're using it as the threshold for a release press").

### What the edge means afterwards

Today the layers assume the edge is on almost anywhere off centre and lets go
at centre. With the default it is on near the rim and lets go when the stick
eases off it. By the same calculation that produced 4915, and taking the
default as 25,000: on near 86% of travel, off near 66%. Calculated, not
measured.

| Layer | What the edge does | With the default radius |
|---|---|---|
| The two stick modifiers | Its Release ends the modifier and opens the flick window | The modifier ends as the stick eases off the rim, not at centre |
| `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover` | Its Release removes the cover | The same: they go as the stick eases off the rim |
| `Steering \| LS: Entry Guard` | Its Release ends the guard | The guard ends only after the stick has been to the rim and eased off |
| The drivers, the Modifier 2 layers, both stick modifiers | A cleanup bind on the edge | It fires only at the rim |
| The new window | Its Release clears the window and the Fallback Hold | Easing off the rim with up still held clears both; `Steering` puts them back and the second starts over |
| `Steering`, the two Steering windows | Bound to nothing | No change |

### What a Release on the edge needs

A Release only fires after its press. With the default radius the edge is
pressed near the rim, so a push that stops short of the rim never presses it
and gets no Release from it.

| Layer | Other ways it ends | A push that stops short of the rim |
|---|---|---|
| The new window | Up or down let go; the timer | Fine: up or down's own Release clears it |
| The two stick modifiers | The opposite direction; the driver let go | The modifier stays on with the stick back at centre, until the driver is let go |
| `Steering \| LS: Entry Guard` | A driver press; its cleanup binds | The guard stays on until the stick has been to the rim once |
| `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover` | The driver let go; up or down let go (the second one) | The first stays on with its stick modifier |

The Entry Guard gets another way to end and the stick modifiers are left as
they are ([part 3](#3-the-rest)).

## 3. The rest

The author asked on 2026-10-04 for a suggested fix for each thing this plan
had left out, and approved them the same day: "update the plan with the
suggested fixes and that seems good to me."

### 3a. The outer ring in the other layers

Outside Steering, the left stick has 4915 in 21 layers, and the right stick
has 4915 in 7 and 7209 in 13.

**The same fix as Steering.** No radius stated, "not inverted" stated. Then no layer holds a radius the editor can't set. Base (21700
inverted, and 32767) and the layers that state 21000 are inside the range and
stay.

| Layers | What the edge does there | With the default radius |
|---|---|---|
| The four single modifiers (`L1: Modifier 0`, `R1: Modifier 1` and their `Gyro \|` pair) | A cleanup bind; and both sticks out with the bumper held ends the cursor response | The cursor ends with both sticks at the rim, not a quarter out |
| The menu Entry Points, their `Stateful \|` pair, the two stick guards, the menu Tap Cover | A stick that is out holds the Fn layer off, through a guard | Only a stick at the rim holds Fn off. A thumb leaning on a stick no longer does |
| `Cursor Gyro`, `Menu Keys` | Both sticks out leaves the layer | Both sticks at the rim |
| The menu second-press layers and their covers, the three transitions | A cleanup bind | It fires at the rim |

The second row is the trouble the author had on the Deck with the menu
buttons doing nothing while a thumb was on a stick.

### 3b. The Entry Guard

`Steering | LS: Entry Guard` is on from the moment `Steering` is entered until
the left stick has moved once. It ends on the edge's Release. With the default
radius that needs a push to the rim.

**The fix:** up, down, left and right each get a Release that removes the
guard, next to the key they already type. Any push then ends it. The edge's
Release stays.

### 3c. The stick modifiers

While a driver is held, stick up or down gives a modifier map
(`Steering | LS Up: Modifier 1`, `Steering | LS Down: Modifier 0`). They end on
the edge's Release, so that the map stays while the stick rolls sideways.

**Left as they are.** With the default radius a push that stops short of
the rim leaves the map on until the driver is let go, which clears it. Ending
them on up or down's Release would end the map on a roll to the side.

### 3d. Two timers that need nothing

Both are inside Steam's 1000 ms and stay as they are.

- **The 200 ms hold in the stick modifiers.** Holding the stick up or down
  for 200 ms while driving adds `Steering | LS: Tap Cover`. That marks the
  push as a hold. Without it the push counts as a flick when the stick comes
  back.
- **The 150 ms Steering windows.** `Steering | LS Up: Double Tap` and
  `Steering | LS Down: Double Tap` come on for 150 ms after a flick. The flick
  scrolls once; a second flick held inside the 150 ms keeps scrolling.

They were listed only because "no timers but the window's" is about the
fallback, not about these.

### 3e. The cleanup binds in the fallback

These are the binds 90.24 gave `Steering | LS: Fallback Hold`. They are not
removed. Part 1 already changes them, and nothing more is needed.

| Input | Today | After part 1 |
|---|---|---|
| Left stick touch, right stick touch, right stick's edge | A repeating press that removes the Fallback Hold, held back while the left stick is out | The same, but it clears all the Steering layers |
| Start, Select | The same press; Tab or Escape while the stick is out | A repeating press that clears all the Steering layers, stick out or not |
| The two drivers | None | A repeating press that clears all the Steering layers, stick out or not |

With part 2 the right stick's edge there is pressed at the rim.

## What it rests on

| Assumption | Status | Where |
|---|---|---|
| The chord on the left stick being out is seen as a layer is exposed | Unverified | At the 1000 ms mark the Fallback Hold's cleanup binds are exposed under thumbs resting on the sticks. If the chord is missed there, a cleanup bind clears the Steering layers: `Steering` ends at the second with the stick still up. First Deck check |
| A8: a stick's Release fires in a layer added while the stick was out | Unverified | The window's Releases on up, down and the edge. If none fires, the stick is back at centre with the window still counting; after the second the Fallback Hold is exposed with no stick out, and a cleanup bind leaves `Steering` |
| A11: a key fires when a removal exposes it under a held input | Unverified | W carries on past the second, from the window's bind to the Fallback Hold's |
| A9: a layer command exposed under a held input fires | Unverified, works either way | A driver or menu button pressed in the window: the Fallback Hold's bind for it repeats, so it fires on its next repeat if not at once |
| A10: a key fires as its layer lands on an input that is held | Reported | W and S in the window |
| A7: a Release fires in the layer that answers the input when it is let go | Verified for buttons | The exit |
| A13: a removal restarts a counting delay | Reported | Nothing removes a layer while the window counts; its own exits end it |

The first two are the ones that can leave `Steering` when you didn't mean to.
For the second, up and down's own Release clears the window too, so it
doesn't depend on where the edge lets go.

## Rules

| Rule | Change |
|---|---|
| R137 | It says no layer is added over the Fallback Hold. The window is, on purpose; the rule gets that case |
| R136 | The window covers the Fallback Hold's binds and carries the early exit |
| R140 to R149 | The new window follows them |
| R169 to R171 | The Fallback Hold's cleanup binds run the exit. A driver's or a menu button's press there runs it outright |
| R120, R121 | Nothing: no delayed add is left in the fallback |
| R161 | The exit keeps its beep and strong pulse, on the Release |
| R111 and the edge rules | The edge is pressed near the rim in every layer that binds it; the tuning note about a quarter of travel (TC8) goes |
| A new assumption, next to A41 | A stick group that states no radius uses Steam's default, near the rim, and not the radius of the group it replaces. 62 stick groups rest on it. Unverified |
| R156 | The working layouts are the new builder's output |

The note of 2026-10-04 about moving the exit to 950 ms and its delay fix to
1000 ms is replaced by this plan.

## Not in this plan

Nothing is left out on purpose. What was listed here is in
[part 3](#3-the-rest).

## Build steps

1. A new builder under `findings/`, extending the 90.30 builder by file path.
2. The window is built from `Steering | LS Up: Double Tap`, inside the build
   before the required cleanups run, so it gets its blocks like any window.
3. `Steering`'s up and down, and the Fallback Hold, are changed as above.
4. The radius comes off every stick group that states 4915 or 7209, in every
   layer: the left stick in 34 layers, the right stick in 28. Each keeps "not
   inverted". The Entry Guard's four directions get their Release.
5. A test keeps every delay and repeat rate at or under 1000 ms and every
   D-pad radius inside the editor's range, in every layer.
6. On the simulator first: hold up past the second and let go (out of
   `Steering`); let go early (stays in); roll to A and back; a driver and a
   menu button before and after the second; each thumb lifted; a missed
   Release.
7. Tests, static and scenarios, with each gesture repeated inside one stay in
   `Steering`. The Fallback Hold scenarios of 90.11 and 90.30 change with it.
8. The build audit, the change report, the snapshot, the documents and the
   description: the exit gesture, and Fn being held off only by a stick at
   the rim.

## On the Deck, after the build

1. In `Steering`, rest both thumbs on the sticks and hold up for three
   seconds: W the whole time, and still in `Steering`.
2. Let go: out of `Steering`, with the beep.
3. Push up and let go inside the second, several times: `Steering` stays, W
   each time.
4. Hold up and press a driver, then again with a menu button, inside the
   second and after it: out of `Steering` each time.
5. Outside `Steering`, rest a thumb on a stick and hold Select: the Fn beep at
   200 ms. Push that stick to the rim and hold Select: no Fn until it comes
   off the rim.
6. Enter `Steering` and nudge the stick a little: the Entry Guard is gone, and
   the next push up starts the fallback's second.
