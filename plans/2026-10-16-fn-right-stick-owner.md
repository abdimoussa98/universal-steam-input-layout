# Plan: the Fn layers take over from the Entry Points (Ibex 1.1, Neptune 90.77, DSE 1.1)

**Status, 2026-10-16:** built as Ibex 1.1, Neptune 90.77 and DSE 1.1 on the
author's word ("implement this plan";
[record](../findings/2026-10-16-fn-right-stick-owner/README.md)). Not tagged or
committed. Where the build differs from this plan:

- **The click guard rests on a new row, A78:** a chord that is not
  interruptible holds back an interruptible chord on the same input. The
  simulator ran both chords, so it couldn't show the guard working. The author
  verified A78 on 2026-10-17, the simulator models it since, and scenario F4
  checks that nothing types with a click held.
- **Three new register entries.** The Stateful Fn layers keep the ten removes
  the Stateful Entry Points kept in their click Releases (R132). The combo
  Double Tap windows may cover the Fn layer's clicks, as they did the Entry
  Point's (R136, twice).
- **Two scenarios are narrower:**
  - "Fn follows on the hold" holds when the stick comes back within 200 ms,
    before the guard's Tap Cover lands. That is 1.0's behaviour.
  - Start alone doesn't reach a key of `Menu Left: Fn Layer`, so the merged
    keys are tested with their own menu button and with both; a static test
    checks each merged chord against the two it replaced for every combination
    of buttons.

The author, 2026-10-16, on the fault: "fn is always going to inherit from entry
point for that stick since we've changed the mod from base so we cant have base =
mouse -> entry = dpad -> fn = dpad, and expect a partial inheritence in the fn
layer. its just inheriting everything." On the requested settings: "for dpads on
actual joysticks it doesn't seem like we need the requires click settings so we
can remove that. Also for include the deadzone setting for the fn and entry
layers on the sticks". And on the design: "the entrypoint layers will just
inherit the left and right stick modes and just override the stick clicks for
the appropriate fn layers and the edge binds to add the stick guards (which will
also just have the sticks inherited). The fn layers will have the stick click
with the correct transition layer and the correct binds for the stick binds up,
down, left, & right. the layers above do not need to be duplicated. Also on fn
being apply we'll remove the stick guards and the entry point layers." The
guards keep their own touch and edge binds, the guards' right stick no longer
has to be empty, and the Entry Point's right edge is at 21000 (author's answers,
same day).

## Terms

- **Entry Points:** `Menu Left: Entry Point`, `Menu Right: Entry Point` and their
  two `Stateful | …` copies. Each one adds one **Fn layer**
  (`Menu Left: Fn Layer` and so on). In every stack the chains find, each Fn
  layer sits right on its own Entry Point. The two **combo Entry Points**,
  `Menu Left!Right:` and `Menu Right!Left: Entry Point`, and their windows sit
  above an Fn layer.
- **Guards:** `Menu Buttons: Left Stick Guard` and `Menu Buttons: Right Stick Guard`.
  An Entry Point's stick edge adds its stick's guard while the menu button is
  held. The guard binds the menu buttons, which cancels Fn's 200 ms delay (A15),
  so a stick that is out keeps Fn away. The guards' 200 ms hold adds the menu
  **Tap Cover**.
- **Mode change:** a layer's group in another mode than the group under it, such
  as a D-pad over Base's mouse stick. It replaces the whole source (A2).
- **Owner:** the layer that made the mode change. On 90.75, under
  `Menu Left: Fn Layer`, the right stick is Base (mouse), then
  `Menu Left: Entry Point` (D-pad, the owner), then the Fn layer (D-pad).
- **Hand-over:** a bind that adds a layer and removes its own layer, adds first
  (R137), as the pad Click Entry Points do.

## The fault and the rule

On the Deck the right stick types nothing in the Fn layers (90.74, 90.75; the
[90.76 trial](../findings/2026-10-16-entry-point-requires-click/README.md),
`requires_click` off the Entry Points, has no Deck result yet). The left stick
works there, and the July layout's right stick worked. The simulator types the
keys: it follows A1, where the topmost layer that binds an input answers.

The author's rule, as a new assumption **A77**: *a layer's group in the same mode
as the owner's, above it, doesn't answer; the owner answers the whole source.*
Status: reported by the author, 2026-10-16. Whether an input the owner leaves
unbound comes from a group above it is not known; this plan doesn't need it.

| Stick | Base | Entry Point | Fn layer | On the Deck |
|---|---|---|---|---|
| Right, July | mouse | mouse | D-pad, the owner | works |
| Left, 90.75 | D-pad | D-pad | D-pad: no mode change, A1 holds | works |
| Right, 90.75 | mouse | D-pad, the owner | D-pad | nothing |

**The check for A77's row**, on 90.75 with a key tester open. Hold Select. After
half a second push the right stick all the way out and back, then lift the
thumb. Wait another half second, let go of Select, and press A twice.

- With A77, the first A types nothing and the second types F. The push ran the
  Entry Point's edge chord, which put the right stick guard over Fn. Select's
  release then went to the guard's cover, which leaves Fn on, and A's first
  press clears Fn.
- Without A77, the first A types F.

A scan with the chains finds 13 menu layers whose right-stick D-pad sits over an
Entry Point's D-pad. Eleven do in every stack the chains find: the four Fn
layers, the two combo Entry Points, both guards, the Tap Cover and the two combo
Double Tap Covers. `Menu Left!Right: Enter` and `Menu Right!Left: Backspace` do
in half; in the other half they sit on the combo Double Tap window's mouse-mode
stick and are the owner themselves. By A77 their right-stick binds don't answer
there; the Entry Point's do.

## Part 1: no `requires_click` on a stick

28 stick D-pad groups in each variant state `requires_click` 0. Seven become
mouse groups in part 3 and lose every D-pad setting: the right sticks of the
four Entry Points, the two guards and the Tap Cover. The other 21 lose
`requires_click`: Base's and `Steering`'s left stick, 13 more Steering left
sticks, and the right sticks of the two combo Entry Points and their four
windows. The three pad groups keep theirs. The Fn layers' left stick never
stated it and works on the Deck, and the Steam client shows Requires Click for
trackpads only ([90.74 record](../findings/2026-10-15-fn-right-stick/README.md)).

## Part 2: `deadzone` 13276 on the Entry Point and Fn sticks

13276 is the value on Base's left stick and on today's Entry Point right stick,
and July's Fn layers had it on the right stick. It goes on both sticks of the
four Fn layers and on the left stick of the six Entry Points, combo ones
included. The combo Entry Points' right stick already has it. A direction then
fires past about 40% of the stick's travel, as on Base's left stick. The four
Entry Points' right stick is a mouse group (part 3), which has no D-pad
deadzone.

## Part 3: the hand-over

### The four Entry Points

- **Sticks in Base's modes.** The left stick stays a D-pad. The right stick
  becomes a mouse group stating `layer` 1, `edge_binding_invert` 0 and
  `edge_binding_radius` 21000. Without a stated radius it would take Base's
  32767, the very rim. The four empty directions go. The camera takes Base's
  settings, as in the 62 layers whose mouse group states no more.
- **Each stick click adds the Entry Point's Fn layer, at the press.** A
  Regular Press, silent (`haptic_intensity` 0), not interruptible, with Hold to
  Repeat every 50 ms (author, 2026-10-16: "no bump on this and make it
  repeating"). The repeat makes it fire also on a click already held when the
  Entry Point lands (A6). Fn then lands over the held click, and its click
  Release does the transition when the click is let go (A7). Base's stick-click
  keys stay blocked, because the input is bound.
- **The edges and touches stay as they are.** The edges add the guards; the
  touches keep their cleanup and the Release that adds Fn (R123).

### Every bind that adds an Fn layer hands over

Each Fn layer has six adders, all in its Entry Point. These four exist today:
- the 200 ms chord on its own menu button;
- the chord on the other menu button, which also adds the combo Entry Point;
- the two stick-touch Releases.

The two new stick-click presses make six. All 24 adders remove their Entry
Point after their adds.

The two click presses also remove both guards and the Tap Cover. They're the
only adders that can run while those layers are up: the guards and the Tap
Cover bind both menu buttons and both stick touches, but no stick click, so the
click comes through from the Entry Point. The other four adders get no removes
that could never take a layer off, a standing goal. So Fn always sits on what
was under the Entry Point: Base, `Gyro`, `Steering` or `Cursor Gyro`, with any
stick or pad layer on them. In every one of those stacks (1,108 a variant) the
right stick is in mouse mode, so Fn's right-stick D-pad is the owner, July's
shape.

### The four Fn layers

- **Both sticks** keep their four keys, bumps and edge and touch cleanups.
- **Each key's click guard holds while either stick is clicked** (author,
  2026-10-16: "just make the guard an any both of the stick clicks"). Today the
  guard is an empty chord, not interruptible, on the key's own stick click:
  `chord_button` 9 on the left keys and 20 on the right keys. It becomes one
  guard on a mask of both stick clicks, bits 22 and 26 (71303168), Any. The
  direction keeps two entries: its key and that one guard. Without this, a stick
  click while the other stick is out brings Fn in over that stick, which then
  types its Fn key until the click's Release clears Fn (A10, A36, A17). That is
  new: today the click goes straight to the transition, and Fn never lands.
- **Their binds that are doubled per menu button become one chord on either**
  ([part 4](#part-4-one-any-chord-where-two-differ-only-in-their-button)).
- **Both sticks get the click Release of their Entry Point,** command for
  command:
  - Menu Left's left stick goes to Transition Set 0 and its right stick to 1;
  - Menu Right has those two swapped;
  - the Stateful pair go to 2 on both sticks.
- **Both trackpad groups their Entry Point binds today**, copied, because
  nothing under Fn has them any more. On the left pad these are the swipe keys
  (Escape, Enter, Tab, Backspace) and the click and touch blocks. On the right
  pad they are the click block and the touch cleanup. Fn inherits them today; no
  other input of the Entry Point reaches Fn.

### The guards and the Tap Cover

- **The guards' right stick becomes a mouse group** with the Entry Point's three
  settings. It keeps its own touch binds, and the right stick guard keeps its
  edge binds. Their left stick is unchanged. They take the stick clicks from
  the Entry Point.
- **The Tap Cover's right stick becomes the same mouse group,** keeping its edge
  and touch binds. As a D-pad it would now be the owner over the guards' mouse
  group, and in the Tap Cover the camera would stop and R3 would do nothing.

### The layers above Fn

Nothing changes there. The combo layers bind no stick click, so they take Fn's.

### What changes for the player

- The camera keeps working while a menu button is held, until Fn lands: in the
  Entry Point, the guards and the Tap Cover. In Fn the right stick types the Fn
  keys.
- A stick click before Fn lands brings Fn in at the press, silently, and does
  the transition on the release, as from Fn.
- The right stick guard lands at 21000, about two thirds of the stick's travel.
  Today it lands at Steam's default radius, near the rim (A50).
- While a stick is clicked, neither stick types an Fn key (the wider click
  guard). Today a click holds back only its own stick's keys.

## Part 4: one Any chord where two differ only in their button

The author, 2026-10-16: "we should just have one bind that is an any. and
anywhere you see this in the fn layers we should address this", then of the
face buttons, the D-pad and the other layers: "yeah lets also make the change
for the other layers".

Where an input has two chords with the same bind and the same settings, each
waiting for a different button, they become one chord on a mask of both
buttons, Any (`gyro_ratchet_button_requireany_or_all` 0). It fires when either
button is held, as the two did. It takes the place of the first of the two.
Mask bits are from [the chord ID table](../resources/Neptune%20Chorded%20Button%20Ids.md).
That is 84 inputs a variant, one entry fewer each:

| Layers | Inputs | The two chords | One chord |
|---|---|---|---|
| The four Fn layers | 16 keys each: the four face buttons, the four D-pad directions, both trigger clicks, both bumpers and the four back grips | The key on Select (15) and the same key on Start (14) | Mask 20480, Select or Start |
| The four Fn layers | Both stick edges' cleanup guard | Empty, not interruptible, on Select and on Start | Mask 20480: the guard their stick touches already use |
| The two combo Entry Points | Both stick edges' cleanup guard | Empty, on Select and on Start | Mask 20480 |
| The four Modifier 2 layers | Both stick edges' cleanup guard | Empty, on the two modifiers: L1 and R1 (default), L2 and R2 soft pulls (alternative) | Mask 12, bits 3 and 2 (default); mask 50331648, bits 25 and 24 (alternative) |

Not merged: `Steering | LS Up: Modifier 1` and `Steering | LS Down: Modifier 0`,
13 inputs each. Their two chords are All chords, the stick's deflection with one
modifier and with the other, and one mask is either all of its buttons or any of
them, so it can't say "the deflection and either modifier".

The Fn layers' stick keys have one chord each, on their own menu button, and
stay so. Their click guard is part 3's.

## Part 5: records and tests

- Add A77 to [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md)
  with the check above. The layout works either way for the Fn layers, the
  Entry Points and the guards: Fn is the owner, and the others are in Base's
  mode.
- Scenarios go in `tests/scenarios/ibex/test_scenarios_ibex_1_1.py` (R165–R167):
  - each direction of each Fn layer types its key with a Low bump, over Base,
    `Gyro`, `Steering` and `Cursor Gyro`, with the thumb landing after the hold
    and with it resting on the stick before the hold;
  - for each of the six adders, Fn lands with no Entry Point, guard or Tap Cover
    under it;
  - a stick click from the Entry Point, from each guard, from the Tap Cover and
    from Fn reaches its transition, with no bump at the press;
  - a stick click while the other stick is out types no Fn key;
  - in each Fn layer, a stick at its edge runs no cleanup while either menu
    button is held, and runs it when neither is;
  - each merged key types with Select held, with Start held and with both, and
    each merged guard holds with either of its buttons (part 4);
  - the right stick moves the camera in the Entry Point and the guards;
  - a stick out at the menu press: the guard lands, the guard leaves when the
    stick comes back, and Fn follows on the hold;
  - a release missed while the Steam menu is open.
- A contract test checks that in every stack the chains give, each Fn layer is
  its right stick's owner and no menu Entry Point or guard is under it. The
  90.75 shape then fails a test, though the simulator doesn't model A77.
- A contract test checks that no input has two chords that differ only in a
  button an Any mask could hold (part 4). Tests that read these chords as
  `chord_button` 15 and 14 read the mask instead.
- The scan's list goes in the release's record. Modelling A77 in the simulator
  and the audits is not in this plan, because it changes every audit's stick
  lookup.

## Part 6: build and release

1. A builder in `findings/2026-10-16-fn-right-stick-owner/` reads the Ibex 1.0
   snapshot, applies parts 1 to 4 and then the fix pipeline, and installs `ibex/`
   as **Ibex 1.1**.
2. Read the change report (R164) and the description (R151), and run the build
   audit and the tests. Export the VDFs, then run
   `python3 -m tools.release snapshot ibex`.
3. Run `python3 -m tools.convert neptune --version 90.77`; 90.76 stays the trial's
   number, which may still be on your Deck. Run `python3 -m tools.convert dse`
   for 1.1. Export and snapshot both. The Edge's mask rules (R178) change only
   stick-touch and left-pad-touch bits, none of which part 4 uses; the
   conversion test (C1) confirms it.
4. Count the removes and adds before and after. The Fn layers' removes of their
   Entry Point can no longer take a layer off; the fix pipeline and the remove
   audit say which go.
5. No tag and no commit until you say. `docs/building.md` lists 90.76 as a
   trial off the line, as it does 90.69.

## Not in this plan

- **The click in the key layers stays as 90.73 built it** (author, 2026-10-16:
  "nevermind then since the current day implementation is what i want. so long
  as its actually silent"). In `Escape`, `Tab`, `Backspace` and `Enter` it is a
  repeating Soft Press, not interruptible, that removes the layer at the press,
  and it states `haptic_intensity` 0 in all four layers and both variants. Base's
  click, which then takes the held click, states 0, and `LTP: Click Entry Point`
  overrides its pad's haptics to Off. The one bump on that click is the normal
  pad click's: the High self-hold of `LTP: Middle Click` or `LTP: Arrow Keys`.
  The key layers' left-stick touch and edge cleanups, which also remove the
  layer, state no haptic at all, and what Steam does with an unstated one is not
  known here.

- The combo layers' right-stick touch and edge binds, which by A77 don't answer
  over Fn's, and `LTP: Middle Click` over a key layer (21 of 1,664 stacks).
- The right pad's double tap on Ibex against Neptune (today's first question).
