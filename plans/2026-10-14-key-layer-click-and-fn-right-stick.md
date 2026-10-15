# Plan: the click in the left-pad key layers (90.73), the right stick in the Fn layers (90.74)

**Status, 2026-10-15:** built, on the author's word ("these are the ones i want
now go ahead and build these", of `;` `'` `.` `,`): **90.73** from 90.72
([record](../findings/2026-10-15-key-layer-click/README.md)) and **90.74** from
90.73 ([record](../findings/2026-10-15-fn-right-stick/README.md)). One change
from part 1: the click's Soft Press is `interruptable` 0 (see the 90.73 record).

The author, 2026-10-14: "when you are swiping on the left trackpad and you go
into enter, backspace, tab, escape layers the click is not behaving the same way
as from base. Click should remove the layer you are in and it should be a
repeated silent soft press then by default you'll be going through the base left
pad click." And: "in the right stick directions on the stick arent having haptic
in the fn layer nor are the correct binds there either."

## Terms

- **Key layers:** `Escape`, `Tab`, `Backspace`, `Enter`. Base's left-pad swipes
  add them: west, north, south and east. Only Base adds them.
- **Fn layers:** `Menu Left: Fn Layer`, `Menu Right: Fn Layer` and their two
  `Stateful | …` copies. Holding Select or Start for 200 ms adds one.

## Part 1: 90.73, the click in the key layers

### What is wrong

In each key layer the left pad is a `single_button` group with one input bound:
the touch types the key (Full Press) and lifting removes the layer (Release).
The click is not bound, and a layer's group replaces the whole pad source. So
while a key layer is on, the click does nothing. From Base the same click is a
repeating, silent Soft Press that adds `LTP: Click Entry Point`. That layer then
hands over to `LTP: Middle Click` at the centre or `LTP: Arrow Keys` at the ring.

### The change (both variants)

| Layer | Input | 90.72 | 90.73 |
|---|---|---|---|
| Key layers | left pad click | not bound | Soft Press that removes the layer itself: `haptic_intensity` 0, Hold to Repeat every 50 ms, interruptible as Base's (not set) |
| Key layers | left pad touch | key on the press, remove self on the Release | unchanged |

Base's click settings are copied as they are: haptic 0, `hold_repeats` 1,
`repeat_rate` 50, no threshold. The new entry is the input's only one, so R109
(at most three entries) and the storage order are not affected.

### The gesture

1. Swipe east: Base adds `Enter`; the touch types Return.
2. Click: `Enter`'s Soft Press removes `Enter`.
3. The click is still down over Base's Soft Press, which repeats, so it fires
   within 50 ms (R114). Base adds `LTP: Click Entry Point`.
4. From there it is a click from Base: the thumb at the ring goes to
   `LTP: Arrow Keys` (Right Arrow), at the centre to `LTP: Middle Click`.

Tried in memory on 90.72 with the simulator (`Pad(data=…)`, both variants, all
four directions). The key is typed on the swipe; the click then lands in
`LTP: Arrow Keys` and types that direction's arrow, the same stack as a click
from Base. Lifting the thumb returns to Base. On 90.72 the same click leaves the
key layer on and types nothing.

### What it does not change

- The key is still typed on the swipe, before the click. Only the click is new.
- The 90.72 left-stick edge cleanups of the key layers, and the menu Entry
  Points that block the pad clicks over them (R172), stay as they are.
- What fires after the removal rests on A9 (a binding a removal exposes fires).
  The repeat of Base's click covers either way, as it does for the Click Entry
  Point hand-overs.

### Build

- `findings/2026-10-14-key-layer-click/`, copied from
  `findings/2026-10-14-pad-stick-edge-cleanups/`, reading the 90.72 snapshot.
- `tests/test_scenarios_90_73.py`: swipe then click in each direction, at the
  ring and at the centre, matches a click from Base; a click and a lift with no
  swipe is unchanged; both variants.
- The build audit, the scenario run, VDF export and the `versions/neptune/90.73/`
  snapshot (`steam-layout-apply`); todos, `docs/building.md` and the record.
- Expected count: four removes more in each layout, no adds.

### On the Deck

1. Swipe right, click at the ring: one Return, then Right Arrow; no bump on the
   click until the Arrow Keys self-hold (High).
2. Swipe up, slide back to the centre, click: Tab, then Caps Lock (Middle Click).
3. Swipe and lift without a click: the key once, and back to Base.

## Part 2: 90.74, the right stick in the Fn layers

### What the layout says

All four Fn layers have the same right stick. Its group is unchanged since 90.8,
apart from the haptic going from 2 to 1 (Low) in 90.41:

| Direction | Key | Haptic | Chord |
|---|---|---|---|
| up | `;` | 1 (Low) | the layer's menu button (Select 15, Start 14) |
| down | `'` | 1 | same |
| right | `.` | 1 | same |
| left | `,` | 1 | same |

Each direction also has an empty uninterruptible chord on R3 (button 20). The
left stick has the same shape with `\` `/` `]` `[` and L3 (9). The only
differences are on the right stick's group: `deadzone` 13276 and
`requires_click` 0.

On the simulator the right stick types the key from the Fn layer every way I
tried. Select or Start held for 300 ms, then the stick pushed, in Base and in
`Steering`, with the thumb resting on the stick first, after a touch and a lift,
and after a push before the 200 ms. So by the binds alone it works. The fault is
in a Steam behaviour the simulator assumes, and a Deck observation decides it.

### The candidate

Pushing the stick out, or touching it, runs the Fn layer's cleanup function on
that input. It is a repeating removal of the Fn layer and its Entry Point, held
back only by an empty chord on the menu buttons:

- **edge** (21000): the removal, and a chord on Select (15) and one on Start (14);
- **touch**: the removal, and a chord on bits 12 and 14 (`gyro_ratchet_button_mask` 20480).

If that guard leaks (A69: confirmed on the Deck, under a burst of
`remove_layer` calls), the Fn layer and the Entry Point come off. The right stick
then falls through to Base's group: a mouse stick, with no keys and no bump.
That is "no haptic, and not the right binds". The left stick has the same guards,
so this candidate predicts that the left stick fails too. One more way in: with
the thumb already on the stick when the Fn layer lands, its repeating touch
removal fires at once (A6). Then the guard has to win at the moment the layer
lands.

A second reading: "not the correct binds" means you want different keys or
behaviour there, not that the keys are missing. Then 90.74 is a bind change, and
the leak is not in play.

### The author's answers (2026-10-15)

- What the stick does: "i dont remember but its not the keys i want for sure nor
  are there haptics".
- When it goes wrong: not sure.
- The left stick in the Fn layer works, with its keys and bumps.

The left stick shares the right stick's guards, so the leak above would hit it
too. It works, so the leak is unlikely. What tells the two sticks apart is their
group:

| Setting | Left stick (works) | Right stick |
|---|---|---|
| `deadzone` | not set (Steam's default) | 13276 |
| `requires_click` | not set | 0 (the Steam client shows this setting for trackpads only) |
| everything else | the same shape: four chorded keys at haptic 1, the stick-click guard, the edge and touch cleanups | same |

Checked further on 90.72, and none of it explains the fault:

- **The VDF the Deck loads** has the right stick's `;` `'` `.` `,` at haptic 1.
- **The July layout**
  (`findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json`) has
  the same keys and the same two settings.
- **The simulator** types the key from every mode with an Fn layer: Base, Gyro,
  `Steering` and Cursor Gyro. `Menu Keys` and `Gamepad` have none.
- **3,000 random walks** with Select or Start held: the only layers that take the
  right stick from an Fn layer are the two menu double-tap windows. They come
  from tapping the other menu button, by design.

### Answered

- **Which keys?** `;` up, `'` down, `.` right, `,` left, the ones 90.72 has
  (author, 2026-10-15: "these are the ones i want").

### What 90.74 would be

Copy the pattern that works. Each Fn layer's right stick group becomes a copy of
that layer's left stick group (no `deadzone`, no `requires_click`), with:

- the keys the author names,
- the guard on R3 (button 20) in place of L3,
- the right stick's cleanups (the `RST:` trio on the touch Release), and
- haptic 1 (Low) on every direction, as the left stick has.

That covers all four Fn layers, in both variants. If the bump is still missing
on the Deck after that, the next step is a Deck observation with a key tester
open. Write down what the right stick types, on the first push and on a second
push.

The build steps are those of part 1: `findings/2026-10-14-fn-right-stick/` from
90.73, `tests/test_scenarios_90_74.py` (each direction types its new key with a
haptic, in each Fn layer, both variants), the audits, export and the snapshot.

### On the Deck

1. Hold Select for half a second, push the right stick each way: the new keys,
   each with a Low bump. The same with Start.
2. The same in `Steering` and in Cursor Gyro (the `Stateful` Fn layers).
3. The same with the thumb already resting on the right stick before the hold.
