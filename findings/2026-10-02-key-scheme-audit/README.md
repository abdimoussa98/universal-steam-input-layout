# Key scheme audit: Base and Modifier 0 to 2

**Status:** audit only. Nothing in the layouts changed. First pass 2026-10-02;
second pass 2026-10-03 adds data on which keys games bind and a review of the
stick clicks. Two changes are proposed for the author
([changes I would make](#changes-i-would-make)); scroll on the bumper taps is
fixed and not part of any of them.

The question (author, 2026-10-02): audit how the keys are organised across
Base and Modifier 0 to 2, the clusters such as F R C V, and the roll from the
left of a QWERTY keyboard to the right. Is there a better way to organise it?
Follow-up (2026-10-03): look for data on the most used keys and combinations
in PC gaming, look at the stick clicks, and give a second opinion.

Read from both Neptune layouts at 90.13. The keys are the same in both: the
default layout holds L1 / R1 for the modifiers, the alternative holds L2 / R2.
This page says L1 / R1 throughout.

## Contents

| Section | What it covers |
|---|---|
| [Answer](#answer) | The second opinion in short |
| [Terms](#terms) | Slot, cluster, column, roll, share, two-bumper load |
| [The map](#the-map) | Every key in Base and Mod 0 to 2 |
| [The rules the scheme follows](#the-rules-the-scheme-follows) | Three placement rules, as I read them |
| [What games bind](#what-games-bind) | Default keys of 46 games, laid over the map |
| [What holds](#what-holds) | Where the scheme and the data agree |
| [Where it breaks its own rules](#where-it-breaks-its-own-rules) | Five places, two that matter |
| [The stick clicks](#the-stick-clicks) | What consoles put there, and what Q and E do |
| [Changes I would make](#changes-i-would-make) | M and I on one bumper; C and V on the stick clicks |
| [Changes I would not make](#changes-i-would-not-make) | The layer reorder I floated first, and the number swap |
| [Method and limits](#method-and-limits) | Where the data comes from and what it can't show |

## Answer

The scheme holds up. The data backs its two biggest decisions:

- **Base** carries all 19 keys that at least 61% of the games bind.
- **Mod 0** carries T G Z X, four of the eight most-bound keys outside Base.

I would change two things, both small:

1. **M needs one bumper, not two.** 54% of the games bind M, the same as T and
   G. Nothing else on Mod 2 passes 28%. Put M and I on the R1 stick clicks,
   which carry Mouse Back and Forward today (one game each, and both are
   already on the right pad).
2. **Swap the Base pairs: Q E on the X and B buttons, C V on the stick
   clicks.** Console layouts put crouch and melee on stick clicks and interact
   on a face button. Q is an ability, consumable or drop in 17 of the 36 games
   that bind it, which makes an accidental left-stick click expensive.

I take back the layer reorder I leaned towards on the first pass. The data
shows its gain was almost all M.

## Terms

| Term | Meaning | Example |
|---|---|---|
| **Slot** | One physical input in one layer that can carry a key | The Y button while L1 is held |
| **Cluster** | The four slots of one physical group in one layer | Base's face buttons: R F C V |
| **Column** | A touch-typing column of the keyboard, counted from the left | Column 5 is 5 T G B |
| **Roll** | The order in which the layers walk across the keyboard | R → T → Y → U on the Y button |
| **Bumper state** | Which bumpers are held: none, L1, R1 or both | L1 alone is Mod 0 |
| **Share** | The percentage of the 46 games that bind a key by default. A key counts once per game | M is 54%: 25 games bind it |
| **Two-bumper load** | The shares of every key that needs both bumpers, added up. It is the number of keys an average game binds on Mod 2 | Today 1.76: an average game binds 1.76 keys that need L1 + R1 |

## The map

| Input | Base | Mod 0 (L1) | Mod 1 (R1) | Mod 2 (L1 + R1) |
|---|---|---|---|---|
| Y (top) | R | T | Y | U |
| A (bottom) | F | G | H | M |
| X (left) | C | Z | B | O |
| B (right) | V | X | N | P |
| D-pad up | 1 | 9 | 5 | I |
| D-pad right | 2 | 0 | 6 | L |
| D-pad down | 3 | - | 7 | K |
| D-pad left | 4 | = | 8 | J |
| Left stick click | Q | Caps Lock | Mouse Back | Num Lock |
| Right stick click | E | Middle mouse | Mouse Forward | ` |
| Select | Escape (tap), Fn (hold) | Insert | Home | Page Up |
| Start | Tab (tap), Fn (hold) | Delete | End | Page Down |
| Left stick | W A S D | same | same | same |
| L2 / R2 | Left / right mouse | same | same | same |
| L4 / L5 / R4 / R5 | Shift / Ctrl / Space / Alt | same | same | same |

Base's left pad types Escape (left), Tab (up), Enter (right) and Backspace
(down), and its click gives the arrow keys.

The same thing seen from the keyboard. Under each key is the layer that holds
it: `B` for Base, then 0, 1 or 2.

```
1 2 3 4 5 6 7 8 9 0 - =
B B B B 1 1 1 1 0 0 0 0

Q W E R T Y U I O P
B B B B 0 1 2 2 2 2

A S D F G H J K L
B B B B 0 1 2 2 2

Z X C V B N M
0 0 B B 1 1 2
```

The Fn layers (hold Select or Start) continue to the right edge with
`[ ] \ /` on the left stick, `; ' , .` on the right stick, and F1 to F12.

## The rules the scheme follows

None of this is written down in the repo. It is my reading of the map.

1. **Face buttons: a column and a pair.** Y and A take one column's top-row
   and home-row key. X and B take a pair of neighbours, left key on the left
   button. Y rolls R → T → Y → U, A rolls F → G → H, and the pairs are C V,
   Z X, B N.
2. **D-pad sequences run clockwise from the top.** 1 2 3 4, then 5 6 7 8 and
   9 0 - =. The Fn layers do the same with F5 to F8, and with F1 to F4 on the
   face buttons.
3. **Some keys keep their keyboard shape.** W A S D on the left stick, I J K L
   on the D-pad in Mod 2, Q and E on the two stick clicks either side of W,
   and the navigation block: Select and Start are its top and bottom row, and
   Mod 0, 1 and 2 are its left, middle and right column.

## What games bind

The default PC keys of 46 games, from keymap.io's controls library
([method](#method-and-limits)). The full list is in
[key-share.txt](key-share.txt).

The 19 keys bound by at least 61% of the games: W A S D (96 to 100%), Shift,
Space and left mouse (91%), Tab, E and right mouse (89%), 1 and R (83%), 2
(80%), Q (78%), Ctrl (76%), 3 and F (74%), 4 (67%), C (61%). After those:
M, T and Enter (54%), G (52%), V and middle mouse (48%), B (46%), 5 and Z
(43%), Alt (41%), X (39%).

The same shares laid over the map:

| Slots | Key and share | Added up |
|---|---|---|
| Base face | R 83, F 74, C 61, V 48 | 2.65 |
| Base stick clicks | Q 78, E 89 | 1.67 |
| Base D-pad | 1 83, 2 80, 3 74, 4 67 | 3.04 |
| Mod 0 face | T 54, G 52, Z 43, X 39 | 1.89 |
| Mod 0 D-pad | 9 20, 0 15, - 4, = 7 | 0.46 |
| Mod 0 stick clicks | Caps Lock 11, Middle mouse 48 | 0.59 |
| Mod 1 face | Y 15, H 22, B 46, N 13 | 0.96 |
| Mod 1 D-pad | 5 43, 6 28, 7 26, 8 22 | 1.20 |
| Mod 1 stick clicks | Mouse Back 2, Mouse Forward 2 | 0.04 |
| Mod 2 face | U 9, **M 54**, O 11, P 13 | 0.87 |
| Mod 2 D-pad | I 28, J 22, K 20, L 15 | 0.85 |
| Mod 2 stick clicks | Num Lock 0, ` 4 | 0.04 |

**Combinations.** A binding that needs two keys at once is rare in defaults:
52 distinct ones, and only seven of them appear in more than one game (Shift
+ left mouse in three; Ctrl + Q, W, E and R, Ctrl + left mouse and Shift +
Enter in two each). They start with Ctrl, Shift or Alt 52 times out of 60.

## What holds

- **Coverage.** 26 letters, 10 digits, `-` and `=`: 10 letters and 4 digits in
  Base, 4 letters and 4 number-row keys each in Mod 0 and Mod 1, 8 letters in
  Mod 2. Not bound anywhere: Print Screen, Scroll Lock, Pause and the numpad.
- **Base matches the data.** It holds all 19 keys bound by at least 61% of
  the games, plus V, Alt, Enter and Escape.
- **L1 matches the data.** The eight most-bound keys outside Base are M, T,
  G, middle mouse, B, 5, Z and X. Five of them are on L1, two on R1. Only M
  needs both bumpers.
- **Combinations work in every layer.** They start with Ctrl, Shift or Alt,
  which sit on the back buttons and are never rebound by a modifier layer.
- **The X and B buttons are the lower-left row.** C V, then Z X with L1, then
  B N with R1. With Ctrl on L5, undo, cut, copy and paste are all on those two
  buttons.
- **The letters roll cleanly.** Base is columns 1 to 4, Mod 0 is column 5
  (T G), Mod 1 is column 6 (Y H N), Mod 2 is columns 7 to 10.

## Where it breaks its own rules

1. **Number blocks are reversed.** Mod 0 has the nearest letters (T G Z X) and
   the furthest numbers (9 0 - =). Mod 1 has the reverse. The older multi-set
   layout in `archived/` has the same order, so it is long-standing and may be
   deliberate. I found no reason for it written down.
2. **Mod 0 and Mod 1 are neighbours on the keyboard and opposites on the
   bumpers.** Bumper states form a loop: none → L1 → both → R1 → none, one
   bumper per step. The keyboard is a line. The current order walks none → L1
   → R1 → both, which jumps across the loop between T G and Y H.
3. **B is cut off from T and G.** The left hand's overflow is five keys
   (T G B Z X) for four face slots. B went to Mod 1, which keeps the B N pair.
   Forced by the slot count; I would leave it.
4. **Mod 2's face buttons leave rule 1.** A is M, not J, and X and B are O P
   from the top row, because I J K L took the D-pad. Eight right-hand letters
   fill eight slots exactly; I would leave it.
5. **Mod 2's stick clicks are mirrored.** The left stick has Num Lock, a
   far-right key, and the right stick has `` ` ``, a far-left key. Small.

Neither 1 nor 2 costs anything the data can measure: L1 and R1 are one bumper
each. They are about how easy the map is to remember.

## The stick clicks

**What consoles put there.** 48 of the library's games list controller
buttons.

| Stick click | Games that use it | What it does |
|---|---|---|
| Left | 29 | Sprint in 22, crouch or sneak in 3, walk in 1, something else in 3 |
| Right | 31 | Melee in 10, crouch or sneak in 4, lock-on or target in 4, something else in 13 |

Interact or use has 45 controller bindings in those games: 35 on a face
button, 1 on a stick click, 9 elsewhere.

On a keyboard those actions are Shift (sprint), Ctrl or C (crouch) and most
often V (melee: V in 7 games, F in 3, E in 3).

**What Q and E do.** The layout has Q on the left stick click and E on the
right.

| Key | Share | What it does, by number of games |
|---|---|---|
| E | 89% | Interact or use in 17, an ability or consumable in 12, lean in 4, melee in 3 |
| Q | 78% | An ability, consumable, kill or drop in 17, lean in 4, other things in 14 (item and ping wheels, take cover, last weapon) |
| C | 61% | Crouch in 13, an ability in 4 |
| V | 48% | Melee in 7, an ability in 1 |

Three things follow:

- **The clicks carry the two most-bound action keys.** E and Q are bound
  more often than three of the four face keys (F 74, C 61, V 48).
- **An accidental left click fires Q.** Pressing down while pushing the stick
  hard is the usual complaint about sprint on a stick click. Sprint is
  harmless when it fires by accident. Q is the ultimate in Overwatch 2 and
  Marvel Rivals, the tactical in Apex Legends and drop item in Minecraft.
- **Interact is often a hold**, and a held stick click nudges the stick. The
  data flags a hold on only 5 of the 50 E bindings, which undercounts it:
  the tables list keys, not how long they are held.

**The modifier stick clicks.** Mod 0's are fine (Caps Lock and middle mouse,
the only extra mouse button games bind often). Mod 2's carry two rare keys on the
rarest layer, which is the right place for them; no game in the sample binds
Num Lock. Mod 1's are the spare capacity: Mouse Back and Forward are bound by
one game each, and the right pad's click layer already has both.

## Changes I would make

### 1. M and I on the R1 stick clicks

| Input | Today | Proposed |
|---|---|---|
| R1 + left stick click | Mouse Back | M |
| R1 + right stick click | Mouse Forward | I |

M and I stay on Mod 2 as well, so I J K L keeps its shape. Mouse Back and
Forward stay on the right pad's click layer.

- **Effect.** The two-bumper load falls from 1.76 to 0.93. Map and inventory
  become one bumper and a click, with no thumb travel.
- **Cost.** Mouse Back and Forward leave the sticks. If those two are used
  often, swap M and N instead (M on the B button with R1, N on the A button
  with both): the load falls to 1.35 and nothing leaves the sticks, but the
  B N pair is split.
- **Size.** 8 binding strings per layout, 16 over both.

### 2. Swap the Base pairs

| Input | Today | Proposed |
|---|---|---|
| X (left) | C | Q |
| B (right) | V | E |
| Left stick click | Q | C |
| Right stick click | E | V |

Y and A keep R and F. The two pairs trade places, and each stays left key on
the left input.

- **For it.** The face buttons get the four most-bound action keys (E 89,
  R 83, Q 78, F 74) and the clicks get the two least-bound (C 61, V 48).
  Crouch and melee are what consoles put on stick clicks, and the pressed
  mid-fight actions keep the no-travel slots. Interact moves to a button that
  can be held without moving the camera. An accidental click crouches or
  swings instead of spending an ability.
- **Against it.** These are the most practised buttons in the layout. Q and
  E lose the no-travel slots, which matters most in the four games that lean
  with them. Copy and paste (Ctrl + C, Ctrl + V) move from X and B to the
  stick clicks, so the lower-left row is no longer all on two buttons.
- **What decides it.** Whether accidental stick clicks or held interacts
  bother the author in play. The data can say what the keys do, not how often
  the Deck's sticks click by accident.
- **Size.** 6 binding strings per layout (X and B have a mode-shift copy),
  12 over both.

Both changes replace key names inside existing entries. No layer command,
cover or add order changes, and the bumper taps and their scroll are
untouched. I haven't checked which tests pin key names against the real
layouts; the suite needs a run after either change.

## Changes I would not make

- **Reordering the layers by bumper state** (L1, then both, then R1; Mod 1
  and Mod 2 trade contents). I leaned towards this on the first pass, on the
  belief that M, I, J, K and L are bound more often than Y, H, B and N. The
  data says the gain is almost all M. The reorder would lower the two-bumper
  load from 1.76 to 1.46 and push B (46%) onto both bumpers, for two layers
  relearned. Change 1 reaches 0.93 by moving two keys.
- **Swapping the number blocks** (5 to 8 on Mod 0, 9 0 - = on Mod 1). It
  would make every cluster roll in the same order. Both blocks need one
  bumper either way, so the data is neutral. Worth doing only if the current
  order is an accident and not a habit: 32 binding strings per layout.
- **A free reorder by share alone.** Giving the 16 most-bound of the 24
  modifier keys to the one-bumper layers would bring the load to about 0.9,
  where change 1 already lands, and would break every cluster and the roll
  that makes the map possible to remember.

## Method and limits

- **Source.** keymap.io's controls library lists each game's default PC keys
  and controller buttons, citing the publisher's settings. 60 games listed;
  46 counted. Skipped: games with no PC key table or fewer than nine
  bindings, and Tekken 8, whose table is arcade notation.
  [key_share.py](key_share.py) downloads the pages and produces
  [key-share.txt](key-share.txt).
- **It counts bindings, not presses.** A share says how many games bind a
  key, not how often players press it. I found no public press-frequency data
  split by game key: WhatPulse has it and sells it.
- **The sample leans to shooters and action games**, the kind this layout is
  built for. It is one third-party site, and I spot-checked only Apex Legends
  against what I know of its defaults.
- **The action groups are mine.** "Ability, consumable, kill or drop" and
  the like were sorted by keyword and then read through, not by a tool.
- **One more thing the data shows, outside the scope:** Tab is a scoreboard
  in 16 games, usually held to view. Start gives Tab as a tap, so holding it
  takes the left pad.
- **Not covered:** the Fn layers beyond noting that they finish the roll, and
  layer mechanics (taps, covers, cleanups, Steering).

Sources: [keymap.io controls library](https://keymap.io/controls/);
[Gfinity on sprint on the left stick click](https://www.gfinityesports.com/article/pressing-the-l3-button-to-sprint-needs-to-stop).
