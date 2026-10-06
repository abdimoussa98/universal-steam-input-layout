# Plan: pad touch bumps, the middle-click mouse, the menu stateful layer and the Tap Cover resets

**Status, 2026-10-04:** built the same day as **90.25**, one release
([record](../findings/2026-10-04-pad-bumps-and-menu-keys/README.md)). It is
installed in `neptune/` with its snapshot; it has not run on the Deck. Every
question put to the author was answered before the build
([Decisions](#decisions)).

**Part 1, the pad touch bump, was taken out again in 90.27** (author,
2026-10-04; [removal](../findings/2026-10-04-pad-bump-removal/README.md),
[how it was built](../findings/2026-10-04-pad-touch-bump/README.md)). The
other parts stand.

What differs from the plan as written, with the reasons in the
[record](../findings/2026-10-04-pad-bumps-and-menu-keys/README.md#what-differs-from-the-plan):

- **The left pad has the hand-over layer too**, `LTP: Touch Entry Point`. On
  the press simulator an inverted ring on Base counts as on with no thumb, so
  the bump planned there would never come at a touch. Twelve new layers, not
  eleven: 78 to 90.
- **`Menu Keys` has no Entry Points.** Start and Select are blocked there, and
  the menu-plus-click exit is a chord on the stick clicks, as in `Gamepad`.
  With Entry Points a Double Tap window could land on the layer, and would
  have to clear the face buttons and the D-pad on every stack (R140).
- **The stick touches do nothing in `Menu Keys`**, for the same reason.
- **The chorded Entry Point removes itself on its Release**, as every Entry
  Point does. So the tap, the hold and the double tap are for the first press
  of a hold; later presses type the key at once, from the Fn layer.
- **Repeats, not delays** (author, 2026-10-04, while building). The
  hand-over's two binds are the Click Entry Point's own: the inner one
  repeats, and only the outer one has the 5 ms delay. The click's add in the
  pad Entry Points repeats too. So the bump and the click agree at every spot,
  and "Which radius the bump uses" below no longer applies.
- **The held-input rule was corrected** (author, 2026-10-04): a repeating
  action always triggers. It fires as its layer lands on a held input, not one
  repeat later. The simulator and A6 follow.
- **The face buttons** are A Enter, B Escape, X Backspace, Y Tab, and it is
  one release (author, 2026-10-04, after the plan was written).

The layer structure of part 3, the titles, every line marked **Note**, the
Deck checks, the build order and the build steps are mine, not the author's.
The author left part 3's layers open ("whatever will allow" the chorded tap,
hold, and double tap and hold), asked to reuse what exists, and left the
titles to me.

Names used below: **Select** is Menu Left (`button_menu`), **Start** is Menu
Right (`button_escape`). A **stateful layer** stays on until it is left on
purpose, like `Steering`. A **window** is a Double Tap window: an Always On
layer that removes itself after 150 ms. A **hand-over layer** is on for a few
milliseconds: it reads where the thumb is and adds the next layer, as
`RTP: Click Entry Point` does for a click. A **reset** is the repeating
removal that stands beside a delayed add (R120).

## Summary

| Part | What the player gets | New layers |
|---|---|---|
| 1. Pad touch bumps | A low bump when the thumb lands where a click would be the centre click | 2: `RTP: Touch Entry Point`, `LTP: Entry Point` |
| 2. Middle-click mouse | The cursor keeps moving while middle mouse is held | 0 |
| 3. Menu stateful layer | Hold both menu buttons 150 ms: arrow keys on the D-pad, Enter / Escape / Backspace / Tab on A / B / X / Y. A chorded tap still types Enter or Backspace | 9: `Menu Keys` and two chains of four |
| 4. Five extra presses | The Cleanup audit takes half the time and memory | 0 (tooling) |
| 5. Tap Cover resets | A stick or pad Tap Cover that failed to land comes up 200 ms later, not never | 0 |

Eleven new layers, 78 to 89 per layout. No part depends on another.

The titles follow the ones in the layout. `RTP: Touch Entry Point` stands
beside `RTP: Click Entry Point`. `Menu Keys` says what the inputs become, as
`Gamepad` does. `Menu Left!Right` is Select held first, then Start, the way
`L1!R1: Modifier 2` is L1 first, then R1.

## 1. A bump on touch where the centre click is

The centre click and the D-pad buttons share each pad. A bump on touch tells
the thumb that a press right there is the centre click. It is a low haptic on
both pads: `haptic_intensity` 1, the level Base's left-pad swipes have. The
pad clicks keep 3.

### Right pad: a hand-over layer

- Base's right pad stays a mouse and binds only the touch. The touch adds
  `RTP: Touch Entry Point` where it adds `RTP: Entry Point` today.
- `RTP: Touch Entry Point`'s pad is a D-pad with two binds on its ring. The
  inner one (thumb inside the centre range) adds `RTP: Entry Point` with the
  bump. The outer one adds it without. Both remove `RTP: Touch Entry Point`
  first, then add the Entry Point.
- The click's add, the Soft Press that adds `RTP: Click Entry Point`, moves
  from Base to `RTP: Entry Point`. A click never comes without a touch.
- `Steering` binds that add itself, so a pad click still works there. It is
  the one layer that would lose it, in both layouts: its pad is a mouse whose
  touch is an empty binding, so neither layer lands there, and its click comes
  from Base today. `RTP: Tap Cover` always has the Entry Point under it;
  `Gamepad` and the Double Tap windows bind their own click.

Why this way: `RTP: Entry Point` sits on Base's mouse as it does today, so the
layers above inherit the click from the Entry Point and the mouse's settings
(friction, acceleration, haptics off) from Base. Nothing is stated twice.

**Note:** it is the Click Entry Point's recipe, so it rests on the same A40
and A41. The thumb is already on the pad when the layer lands, so both ring
binds need that recipe's 5 ms delay (A5). The layer also needs a touch Release
for a thumb that lifts before the hand-over. Its order is the reverse of the
Click Entry Point's, which adds first and then removes itself.

**Note:** Base's touch add repeats. If a cleanup removes `RTP: Entry Point`
under a resting thumb, the hand-over runs again and bumps again.

### Left pad: Base becomes a D-pad

- Base's left pad becomes a D-pad. Its outer ring binding is inverted and
  carries the bump, so it fires when the thumb lands inside the centre range.
- Its touch adds a new layer, `LTP: Entry Point`, which has today's directional
  swipes. Base's left pad is in swipe mode today and binds no touch.
- Swipe mode has no touch Release. So each swipe also removes
  `LTP: Entry Point`, and the layer gets cleanup functions for when no swipe
  comes. Their lists have to be accurate.

**Note:** `LTP: Entry Point` binds the click's add itself, because its mode
differs from Base's D-pad
([a mode change blocks inheritance](../resources/Layer%20Definition%20of%20Done.md#a-source-mode-change-blocks-inheritance)).
No other layer inherits Base's left click today.

**Note:** after a touch with no swipe and no click, `LTP: Entry Point` stays on
until a cleanup function on another input removes it. Until then the next
touch lands on it, not on Base's ring, and gives no bump.

**Deck check, the bump:** a touch in the centre makes two things due at the
same moment, the touch's add and the ring's bump, and Steam promises no order.
If the add goes first, the Entry Point's mode has replaced Base's ring and the
bump may not come. Also unknown: whether an inverted ring already counts as on
with no thumb on the pad (A40). If it does, a touch in the centre changes
nothing and gives no bump. One check settles both: touch the centre ten times
and the rim ten times. It should bump every time on the centre and never on
the rim. If it fails, the right pad's hand-over layer is the fallback.

### Which radius the bump uses

The Click Entry Point picks the middle click inside 24996 and the D-pad
buttons outside 23000. Between the two, both are true. On the press simulator
a click in that ring is the D-pad button, not the middle click (on the right
pad it sends mouse Back). The Deck check for that ring is still open
([todos](../todos.md#trackpads)).

**Note:** the bump must not promise a centre click where the D-pad button
wins. So its radius is **23000** until the Deck shows the centre winning in
the ring; then it is 24996. `RTP: Touch Entry Point`'s two binds use the same
radius, so exactly one of them is true at any spot and they need no tie-break.

## 2. `RTP: Middle Click` becomes a mouse pad

Its pad is in `single_button` mode with middle mouse on the click, so the
cursor stops while the click is held. The pad becomes a mouse with middle
mouse on the mouse mode's click, so the cursor keeps moving while middle mouse
is held.

**Note:** only the pad's mode changes. The click's three entries stay: middle
mouse, the self-hold and the inverted removal. So does the touch Release.

## 3. The menu stateful layer, `Menu Keys`

It replaces the parked
[menu stateful layer](../todos.md#menu-stateful-layer) to-do.

| Gesture | Result |
|---|---|
| Hold Select and Start for 150 ms, from Base or `Gyro` | `Menu Keys` comes on with a beep and a strong pulse, and `Gyro` goes. No Enter or Backspace is typed |
| Hold Select, tap Start | Enter |
| Hold Select, double tap Start and hold | Enter held down |
| Hold Start, tap Select / double tap and hold | Backspace, the same way |
| Both sticks deflected | Out |
| One stick deflected plus a face button or a D-pad direction | Out |
| A menu button plus a stick click | Out, as in the other stateful layers (R158) |

Inside `Menu Keys`:

| Input | Does |
|---|---|
| D-pad | The arrow keys |
| A, B, X, Y | Enter, Escape, Backspace, Tab (author, 2026-10-04) |
| The modifier buttons | Nothing. The modifiers can't be reached from the layer |
| Start, Select | Add the `Stateful` Entry Points, for the menu-plus-click exit |
| Everything else | What it does on Base. The layer doesn't bind it, and with `Gyro` gone Base is what lies under it |

**Note:** the stick edges carry the both-sticks exit, so Base's own edge binds
don't answer in the layer. The ramp-up doesn't start from it, as in
`Cursor Gyro`, where the author accepted that.

### The layers

The chorded tap and double tap is the chain the single menu buttons already
use (R119's example), on the second menu button. Each side gets four layers:

| Part of the chain | Today, for Start alone | New, for Start with Select held | How it is built |
|---|---|---|---|
| Decides tap or hold | `Menu Right: Entry Point` | `Menu Left!Right: Entry Point` | New. Start has an Entry Point's three entries: a Release that opens the window, the 150 ms hold as a chorded delay, and the hold's reset (R120) |
| Types the key on a tap | `Menu Right: Double Tap` | `Menu Left!Right: Double Tap` | Copy. It types Enter where the original types Tab, 50 ms after it opens. Select is held under it, so Select's empty binding gains a Release that removes the window first, then the Fn layer's family |
| Holds the key on a second press | `Menu Right: Tab` | `Menu Left!Right: Enter` | Copy, with Enter. Its Release reopens the window, which lets quick taps chain |
| Ends a long hold cleanly | `Menu Right: Double Tap Cover` | `Menu Left!Right: Double Tap Cover` | Copy, with Enter |

The Backspace chain is the mirror, copied from the `Menu Left` layers:
`Menu Right!Left: Entry Point`, `Menu Right!Left: Double Tap`,
`Menu Right!Left: Backspace` and `Menu Right!Left: Double Tap Cover`. With
`Menu Keys` that is nine layers.

### The flow, with Select held first

1. Start adds `Menu Left: Fn Layer` with `Menu Left!Right: Entry Point` on top
   of it.
2. Start held for 150 ms: `Menu Keys` comes on, with the beep and the pulse.
   `Menu Left!Right: Entry Point`, the Fn layer, `Menu Left: Entry Point` and
   `Gyro` go.
3. Start released before 150 ms: the window opens and types Enter.
4. The window runs out with Select still held: back on
   `Menu Left!Right: Entry Point` and the Fn layer, which were never removed.
5. Start pressed again inside the window: `Menu Left!Right: Enter` holds Enter
   for as long as Start is held. Held past 150 ms, the cover lands and letting
   go ends it. Let go sooner, and the window reopens for the next tap.

### Why it is built this way

- **The plain Entry Points add the new Entry Point, not the Fn layer.** The Fn
  layers are shared: the plain Entry Points and the `Stateful |` ones both add
  them. If the Fn layer added it, the hold would also work inside `Steering`
  and `Cursor Gyro`. So it goes into each of the four bindings of a plain
  Entry Point that add the Fn layer: the same binding, no extra entry. It
  stays for as long as the Fn layer does.
- **One Entry Point for each side.** A Release can't ask for a chord button
  (none of the layout's 227 Releases has one), so one layer can't tell which
  menu button came second. With Select held and Start tapped, letting go of
  Select first would type Backspace.
- **The pattern is not in `Menu Keys`.** After the hold the tap's Release
  would still be live there, and the next tap of Start would open the window
  and type Enter. Keeping it out also keeps R162: the stateful layer has no
  Release and no delayed binding on Start or Select.
- **The pattern is not in the Fn layer.** The Release, the hold and its reset
  are three entries, all that Start may have (R109), and the Fn layer's Start
  already carries its cleanup function.
- **The covers stay** (author). Without them a third quick press held down
  would enter `Menu Keys`; with them it holds Enter, as Escape and Tab do
  today.

### Reused, with no new layer

- The tap's key is typed by the window's Always On action, as Tab and Escape
  are today. No Release has to send a key.
- The menu-plus-stick-click exit goes through `Stateful | Menu Left: Entry Point`
  and `Stateful | Menu Right: Entry Point`, which `Steering` and `Cursor Gyro`
  share. `Menu Keys` adds them with a repeating press, as those two do. The
  clear behind them gets the new layers in its list.
- Both sticks deflected is `Cursor Gyro`'s exit: a repeating chord on each
  stick's edge with the other stick out.
- The arrow keys as `LTP: Arrow Keys` binds them.
- The beep and the strong pulse as the transitions give them (R161): the beep
  flag on the add of the stateful layer, `haptic_intensity` 3 on its activator.

### Not reusable

- The two existing menu windows: each types its own key, Tab or Escape, 50 ms
  after it opens.
- `Menu Right: Tab` and `Menu Left: Escape` for a second key: their button
  already has four entries.
- One window for both sides: a window types one key. One key layer for both
  sides: both menu buttons are held when it lands, so both keys would fire
  (A10).
- The Fn layer's own Enter and Backspace chord for the held key: the new Entry
  Point covers it, and nothing in the shared Fn layer could put that Entry
  Point back afterwards.
- Base's mode-shift groups for the D-pad and the face buttons: they type 1 to
  4 and F, V, C, R.

## 4. Five extra presses in the hidden-exit check

The check's chain walk allows six
[extra presses](../resources/Layout%20Vocabulary.md#terms) by default. The
default becomes five; `--extras` still takes 0 to 14.

| Extra presses | Stacks | Time, whole Cleanup audit | Memory at peak |
|---|---|---|---|
| 5 | 2,684,100 | 10 s | 2.4 GB |
| 6 (today) | 7,728,211 | 19 s | 5.9 GB |

Measured on 90.23, one layout. The output is the same apart from the stack
count. On 90.22 the 12 findings were there from four extra presses on
([record](../findings/2026-10-03-simultaneous-cap/README.md)).

What changes: `DEFAULT_EXTRAS` in `steam_layout/cleanups.py`, the test that
pins six (`tests/test_native.py`), and the wording in `tools/audit_cleanups.py`,
`docs/tools.md` and R136's text in the Definition of Done.

## 5. The Tap Cover reset on the three Entry Points

`LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point` each add their
Tap Cover 150 ms after the touch. They are the layout's only delayed adds
without a reset. Each touch gets one (author, 2026-10-04): a Regular Press
that removes only that Tap Cover, with Hold to Repeat every 200 ms and
`interruptable` 0 (R120, R121). It is the third entry on the input (R109).

What it fixes: a delayed add that was interrupted can fail on the next touch
(A12). The cover then never lands, the Release after a long rest opens the
Double Tap window, and a quick lift and re-touch counts as a double tap.
On a stick that turns Temporary Gyro on unasked. No such failure is recorded.

Checked on copies of 90.24 with the reset on all three, in both layouts: the
build audit is clean. Nothing removes a Tap Cover without its Entry Point (69
removals for each stick, 23 for the pad), so on a normal touch the reset stays
silent: the cover lands at 150 ms and takes the input over before the first
tick at 200 ms.

**Note, the pad:** this reverses a recorded exception to R120. The reset was
left off the right pad's touch because a repeated removal broke trackball
momentum (A28, the author's observation, not rechecked since). It is built
here as asked. The glide is the first thing to check on the Deck: flick the
cursor and see whether it still glides. If it doesn't, the pad's reset comes
out again and the exception goes back; the sticks keep theirs.

**Note, cross-talk:** thumbs rest on the sticks most of the time. If a cover
is late, the reset ticks every 200 ms until it lands, and each tick is a
removal that can restart a delay running somewhere else (A13). Example: L1's
300 ms cursor apply is pending, the stick's reset ticks, and the 300 ms start
again from that tick. This is timing, so no audit sees it.

**Note:** it takes the last free entry on those three touch inputs. Nothing is
waiting for it; the stick-touch helpers are left out of the required cleanups
(R169).

The [investigation to-do](../todos.md#investigations) stays open. Its three
Deck checks are how this part is verified.

## Rules and exceptions

| Rule | What changes |
|---|---|
| R120, a reset beside every delayed add | The exception for the right pad's touch is **withdrawn** (part 5). The new Entry Points' hold and the new key layers' cover each get a reset |
| R157, stateful layers enter through a transition | Already a recorded exception for the menu stateful layer (author, 2026-10-01) |
| R158, a menu button plus a stick click clears | Followed, through the shared `Stateful` Entry Points |
| R159, the Modifier 2 clear removes every stateful layer | **New exception** for `Menu Keys`, as `Gamepad` has: the modifiers can't be reached from it |
| R161, the beep and the strong pulse | Given on the 150 ms hold. The rule is written for a transition's menu Release; this entry has no transition |
| R162, no Release or delayed binding on Start or Select at entry | Followed: the pattern lives in the new Entry Points |
| R119, the whole double-tap recipe | Followed for both chorded chains, covers included |
| R169 to R171, required cleanups | Every new layer that isn't a window or stateful gets its cleanup functions |

## Assumptions

Nothing here is verified on the Deck.

| Rests on | For |
|---|---|
| A5, A40, A41 | `RTP: Touch Entry Point`, as the Click Entry Point does |
| A40, A32 | The left pad's bump on Base's ring (the Deck check in part 1) |
| A16 | The new Entry Points' 150 ms clock starts when the layer lands |
| A10, A12, A27 | The chorded chains, as the Menu Left and Menu Right chains do |
| A12 | The three new resets |
| A28 | Stands against the pad's reset: if it holds, the glide breaks |

To add as rows when built: the left pad's bump (order of the touch's add and
the ring's bump; an inverted ring with no thumb), and which click wins in the
ring where the pad's two ranges overlap.

## Decisions

Answered by the author on 2026-10-03 and 2026-10-04:

| Question | Decision |
|---|---|
| The bump's strength | Low, on both pads |
| Right pad | The hand-over layer; Base stays a mouse and binds only the touch |
| The pad click on the right | Moves to `RTP: Entry Point`; Base doesn't need it |
| Pad clicks in `Steering` | Still work; `Steering` binds the add itself |
| Left pad | Keeps the bump, with Base as a D-pad and `LTP: Entry Point`; no hand-over layer |
| `RTP: Middle Click` | A mouse: the cursor keeps moving while middle mouse is held |
| Enter and Backspace sides | As today: Select held and Start for Enter, Start held and Select for Backspace |
| Where the hold works | From Base and `Gyro` only |
| `Gyro` at entry | Entering removes it |
| Feedback at entry | The beep and the strong pulse, as the other stateful layers have |
| The face buttons' keys | A Enter, B Escape, X Backspace, Y Tab (2026-10-04; the swipe compass was offered and not taken) |
| The other inputs in `Menu Keys` | They do what Base does |
| Menu button plus stick click | Also clears `Menu Keys` |
| How many menu layers | Left to me: one stateful layer and four for each side |
| The covers | Kept |
| The titles | Left to me, on the pattern of the existing ones |
| Extra presses | Five by default |
| The Tap Cover reset | On all three Entry Points, in this plan. The investigation stays in the to-dos |

## Build order

**One release for all five parts** (author, 2026-10-04): 90.25. The extra
presses are tooling and ship with it.

## For the build to settle

With the audits, not the author:

- **R171 on the new Entry Points.** Start has three entries there and no room
  for a cleanup function. It passes as the layer's own button only if the
  audit reads it that way; otherwise the layer needs another shape.
- **The new windows over the Fn layer.** The Window audit lists what they
  inherit from the Entry Point and the Fn layer; each is cleared or replaced
  (R140).
- **What else the hold removes.** Other layers can be on the stack when
  `Menu Keys` lands, the stick-touch helpers for one. The Cleanup audit says
  what has to go with the entry.
- **`RTP: Touch Entry Point`'s haptics.** The Click Entry Point's pad turns its
  haptics off (`haptic_intensity_override` 0). Whether that would also silence
  a bind's own bump isn't recorded.

## Build steps

The release follows [building](../docs/building.md): a new builder folder
copied from the newest one, both layouts, the fix pipeline, scenarios before
the snapshot (R165), then the change report (R164) and the unverified list
(R167). Then `audit_build`, and a read of the new layers' "varies",
"needs review" and "exit to review" entries
(`python3 -m tools.audit_layer <layout> --layer TITLE`).

**The middle-click mouse**

1. `RTP: Middle Click`'s pad group: mode `single_button` to the mouse.
2. Scenario: click the centre, slide the thumb, the cursor moves with middle
   mouse down; the lift still clears the layer.

**The Tap Cover resets**

1. The touch of the three Entry Points: the reset as a third entry.
2. Exceptions register: take out the R120 entry for the right pad's touch.
3. Scenarios: a normal touch fires no reset; a cover that didn't land comes
   up after the next tick; a tap and a double tap on each stick and on the
   pad as before.

**The right pad's bump**

1. Add `RTP: Touch Entry Point` at the end of the layer list.
2. Base: the touch adds it; the click goes. `RTP: Entry Point` and `Steering`
   get the click's add.
3. Cleanup lists: wherever `RTP: Entry Point` is removed, as the Cleanup audit
   asks.
4. Scenarios: a touch in the centre and at the rim (bump, no bump, the Entry
   Point on top both times); a click after each; a lift before the hand-over;
   a pad click in `Steering`; the pad's tap and double tap as before.

**The left pad's bump**

1. Add `LTP: Entry Point`: the swipes, each also removing it; the click's add;
   its cleanup functions.
2. Base's left pad: a D-pad with the inverted ring bump and the touch add.
3. Scenarios: each swipe from a touch; a click from a touch; a touch and lift
   with nothing else, then the cleanup; the windows' left pad unchanged.

**`Menu Keys`**

1. Exceptions register: R159.
2. Copy the two windows, two key layers and two covers with
   `duplicate_layer`; change the keys, the titles and the targets. Add the two
   new Entry Points and `Menu Keys`.
3. The plain Entry Points: the four Fn adds on each also add the new Entry
   Point.
4. `Menu Keys`: the arrow keys, the face buttons' keys, the modifier buttons
   closed, the `Stateful` Entry Points on Start and Select.
5. The exits: both stick edges, the stick-plus-button chords, and the clear's
   list.
6. Scenarios: the hold from Base and from `Gyro`, with `Gyro` gone after it;
   the tap, the double tap and hold, and a third quick press, on both sides;
   the window running out with the first button held; the first button
   released first; each exit; a pad click and a stick push inside the layer
   do what they do on Base; the hold inside `Steering` and `Cursor Gyro` does
   nothing new.

**Five extra presses:** the default, its test, the wording.

## Documents to update

- `todos.md`: the brainstormed-ideas item, the menu stateful layer, the
  trackpads, the reset review under Bugs.
- `resources/Layer Definition of Done.md`: R120's exception column, the R159
  exception, R136's text for the extra presses.
- `resources/Steam Behaviour Assumptions.md`: the new rows; A28's status.
- `resources/Steam Input JSON Structure.md`: the paragraph on the pad's reset
  exception.
- `resources/Stateful Layer Transitions.md`: `Menu Keys` in the exceptions
  table.
- `docs/building.md`: the chain table and the layer count. `docs/tools.md`:
  the extra presses.
