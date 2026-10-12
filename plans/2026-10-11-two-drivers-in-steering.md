# Plan: both drivers held in Steering

**Status, 2026-10-12:** built as **90.57** on the author's word ("yes now
start building"): parts 1, 3, 4 and 6
([release record](../findings/2026-10-12-driver-handover-and-fewer-removes/README.md)).
Part 2, the stick windows, is not built. Every question is answered
([answers](#answers)). Where the build differs from the text below, the
release record says so; the one difference is the two register entries of
part 6, which end at 90.56 and are not deleted. Revised three
times on 2026-10-12: on the author's word ("go ahead and edit the plan"), to
take in three answers from the
[owner release audit](../findings/2026-10-11-owner-release-audit/README.md)
(part 3); for the author's two answers here and the reminder to reduce
unnecessary removals (part 6); and to leave the stick windows as they are,
on the author's word (part 2). Then the author asked for the `Cursor Gyro`
note and what the new rules do (part 4), and whether the necessary layers
are still cleaned up (part 6), accepted both rules, left the right pad's
window as it is and took eight more removes into part 6. The evidence is in
the
[record](../findings/2026-10-11-two-drivers-in-steering/README.md) and in
that audit.

The author's report (2026-10-11), on 90.56:

1. R1 held for W, L1 pressed for Modifier 2. Letting go of R1 with the stick
   still up or down ends `Steering` before the S layer applies, although L1 is
   held.
2. Applying Modifier 2 should take you out of the stick's scroll layer, and
   out of its window too: back on the W or S layer, with Modifier 2 on top.

I read "the mod 0 or 1 steering layer" as the S or W layer.

And in the owner release audit (2026-10-12):

3. "I don't want to be cleared out of steering in mod 2." Letting go of the
   second driver leaves `Gyro` alone (D1) and leaves the first driver's layer
   on (D2), and the 200 ms timer on the second driver goes, with its cover
   (D4).

And on this plan's two questions (2026-10-12):

4. "a chorded dual bumper/trigger press should just remove the window
   properly", and no to clearing stuck menu layers. With them: "remember i
   still want to reduce unnecessay removals".
5. Then, shown what the window answer rests on on the Deck: "just dont touch
   the window for now and have it remove itself as today".

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (the triggers' soft pull in
  the alternative layout). **W layer:** `Steering | R1: W Key`; the **S
  layer** is its twin.
- **First driver, second driver:** the one held first, and the one pressed
  while it is held. `Steering | R1!L1: Modifier 2` is R1 first.
- **Stick window:** `Steering | LS Up: Double Tap` or
  `Steering | LS Down: Double Tap`. It opens when a stick tap ends, scrolls
  once at 50 ms and closes itself at 150 ms.
- **Steering's exit:** up or down past 29031 (near the rim) in `Steering`
  itself. Any layer on top that binds up and down covers it.
- **Cover (90.56):** `L1: Tap Cover` or `R1: Tap Cover` over a Steering
  Modifier 2 layer. The layer's 200 ms timer on the second driver adds it; so
  do a used command and a lifted thumb. Once it is on, its Release answers
  the second driver.
- **Quick tap (90.56):** the second driver let go before the cover is on. The
  Modifier 2 layer's own Release answers, and removes 88 of the 90 layers:
  everything except `Steering` and `Cursor Gyro` (R159). After part 3 there
  is no cover here and no quick tap.

## What 90.56 does

On the press simulator, the same in both layouts
([results](../findings/2026-10-11-two-drivers-in-steering/results.txt)):

| Gesture | What happens | Why |
|---|---|---|
| In Modifier 2, the first driver let go with the stick at the rim | `Steering` ends. The reported fault | The Modifier 2 layer doesn't bind the first driver, so the W layer's own Release answers. It removes Modifier 2 and the W layer. `Steering` is then the top layer under a held L1 and a stick at the rim, and its exit runs before its L1 bind adds the S layer |
| The second driver pressed while a stick window is open | L1 types S beside W until the window closes itself, up to 150 ms. Modifier 2 only comes after that, so an L1 hold of up to 350 ms can still count as a quick tap | The window retypes both drivers as plain W and S (author, 2026-10-01: "no chords, so Modifier 2 can't be entered during the window") |
| The quick tap with the stick at the rim | `Steering` ends | The quick tap's list removes the first driver's layer as well, with the same result as the first row |
| The quick tap, wherever the stick is | W or S is let go and taken up again. `Gyro` goes when it is on. A pad click held through it is let go | The same list. It is the clear to Base of 90.10, with `Steering` taken out in 90.44 ([owner release audit, section 3](../findings/2026-10-11-owner-release-audit/README.md#3-the-two-steering-modifier-2-lists)) |

Already as asked: from a stick modifier, its Tap Cover, a scroll layer or its
Double Tap Cover, the second driver's press removes those layers and adds
Modifier 2 at once. They don't bind the drivers, so the W layer's chord
answers.

The first and third rows have one cause: a Release takes the last driver
layer off while a driver is still held. The layout already has the answer in
`Steering | LS: Entry Guard`, which removes itself and adds the driver's layer
in one array, so that the stick never meets `Steering` alone.

## Part 1: the first driver's Release hands over

In each of the two Steering Modifier 2 layers, bind the first driver:

| Entry | What it does |
|---|---|
| Regular Press, not interruptible | The first driver's key: W in `R1!L1`, S in `L1!R1`. The key stays down while Modifier 2 is on, as a stick window keeps it |
| Release | Adds the second driver's layer, then removes the Modifier 2 layer and the first driver's layer |

So R1 let go in Modifier 2 puts you on the S layer at once, at any stick
position. With the stick out, the S layer's own up or down bind then adds the
stick modifier. Rocking works both ways: R1, L1, R1 up (S layer), R1 down
(`L1!R1` Modifier 2), L1 up (W layer).

- **The add runs first** (stored last), so `Steering` is never the top layer
  at any point of the array. R110 puts removals first in a new array; this one
  departs from it on purpose, as the pad Click Entry Point's hand-over does.
- Base's Modifier 2 layers bind both bumpers' Releases too.
- In the alternative layout each Modifier 2 layer gets a trigger group for the
  first driver, with the settings of the W or S layer's group.
- The first version of this Release also removed the second driver's cover.
  With part 3 no cover lands here.

What it costs:

- W passes from the W layer's bind to the Modifier 2 layer's when Modifier 2
  lands on the held driver, and back when it leaves (A10). Whether the key
  blinks there is A37, unverified; the stick windows have rested on both
  since 90.10. With part 3 alone W is never touched while the second driver
  is pressed and let go: this part is what makes it change hands
  ([owner release audit, section 8](../findings/2026-10-11-owner-release-audit/README.md#8-against-the-two-driver-plan)).
- The add is blind: a Release can't ask whether the second driver is held.
  When the Modifier 2 layer is on but the second driver is not held, the
  hand-over adds a layer nobody holds. That takes a release of the second
  driver that never reached the Modifier 2 layer: missed in the Steam menu,
  or answered by the right pad's window (`RTP: Double Tap` binds both
  bumpers' Releases and lists no Steering layer). The layer types nothing
  and goes on the next touch of a stick (part 6, measured). 90.56 ends on
  `Steering` alone there.
- After the hand-over with the stick out, the stick modifier's 200 ms timer
  starts. Bringing the stick back inside 200 ms is a stick tap: one wheel
  step.

## Part 2: the stick windows stay as they are, for now

Not built (report item 5). The two stick windows keep every bind of 90.56,
and each closes itself at 150 ms as today. So the second row of the table
above stays, and with it the second half of report item 2:

- **The second driver pressed in a window** types its drive key beside the
  first driver's until the window closes itself. Modifier 2 comes after that,
  from the W or S layer's entry.
- **A driver let go in a window** removes the window and both driver layers.
  With the other driver held, that takes its layer off under it: 60 of 471
  window Releases on the random walks of 90.56, and 89 of 623 with this plan
  ([`window-release.txt`](../findings/2026-10-11-owner-release-audit/window-release.txt)).
  `Steering` puts the layer back at its next repeat.

**What was planned and why it waits.** Two versions of a chord on the other
driver were written for this part: one that removes the window and adds
Modifier 2, and one that only removes the window (report item 4). The second
leaves Modifier 2 to the W or S layer's entry, a repeating chord with several
sub-commands that would have to fire under a bumper that is already down,
the shape the author reported on 2026-10-10 as not firing its repeat. 90.56
rests on the same entry once the window has closed itself. The versions are
compared in the
[owner release audit, section 9](../findings/2026-10-11-owner-release-audit/README.md#9-after-a-stick-window-making-modifier-2-come).

**The Deck check that decides it,** on 90.56 as installed and with a key
tester open: hold R1, flick the stick, press and hold L1 as the stick comes
back (an S shows you were inside the window), wait half a second, press A. M
means Modifier 2 came and the entry does fire on the Deck. F means it did
not.

## Part 3: the second driver's Release removes the Modifier 2 layer, and nothing else

The author's three answers of 2026-10-12 (report item 3). The first version
of this part only left the first driver's layer on and kept the rest of the
list. In each Steering Modifier 2 layer:

| Bind | 90.56 | After |
|---|---|---|
| The second driver, Chorded Press, 200 ms | Adds the cover, with a low bump | Gone (D4) |
| The second driver, Regular Press repeating at 250 ms | The timer's reset: removes the cover | Gone (D4) |
| The second driver, Release | 88 removes | One: the Modifier 2 layer. `Gyro` stays (D1), and so does the first driver's layer (D2) |
| The twelve command binds and the two stick touch Releases | Add the cover first | No add of the cover (D4) |

So a tap and a hold of the second driver end the same way: Modifier 2 goes
and you are on the first driver's layer, wherever the stick is. With R1 held
and the stick up, a quick L1 tap leaves you on the W layer, and `Steering`
stays.

What follows from it:

- The fix pipeline trims 42 binds per layout (R132): the Steering Modifier 2
  layer leaves the three lists of each cover, and the cover leaves the
  sixteen cleanup functions of each Modifier 2 layer and the two Releases of
  the W and of the S layer.
- The builder takes six more removes of a cover out of four binds the
  pipeline does not read: the Modifier 2 entry of the W and of the S layer,
  and `Steering`'s exit on up and on down, which lists both covers.
- `L1: Tap Cover` and `R1: Tap Cover` keep their binds for the plain
  modifiers. Only their lists change.

What it costs
([owner release audit, sections 6 and 7](../findings/2026-10-11-owner-release-audit/README.md#6-decisions-for-the-author)):

- The low bump at 200 ms is gone.
- One cleanup the cover had by its guard. When the second driver's Release
  never reached the Modifier 2 layer (missed in the Steam menu, or answered
  by the right pad's window), a thumb on a stick cleared the stale Modifier 2
  although the first driver was held. Without the cover it stays until the
  first driver is let go or the second is tapped again: 20 of 5,913 random
  walks with no release missed, 99 of 5,916 with one in ten missed.
- After the first driver is let go unseen (in the Steam menu, or answered
  by the right pad's window), the second driver's Release leaves the first
  driver's layer on. It types nothing and
  goes on the next tap of either driver, touch or push of a stick, Start or
  Select. 90.56 takes it off only inside the second driver's first 200 ms.
- A pad click whose release was missed is no longer taken off by the second
  driver's Release (a scenario of 90.14 expects it). Its own cleanup
  functions do that.
- Menu layers left on by a missed release are no longer taken off by it
  either (the author's answer, report item 4). They go on the next touch of a
  stick or tap of Start or Select.

Tried in a scratch copy, this part alone on 90.56: the pipeline's 42 trims,
and the build audit clean on both layouts. On the audit's walks `Steering` is
never gone after the second driver's Release while the first is held (0 of
3,047 Releases, against 86 of 2,905 on 90.56).

## Part 4: the model, the rules and the register

The whole plan was built as one trial layout in a scratch directory
([`plan_candidate.py`](../findings/2026-10-11-owner-release-audit/plan_candidate.py)),
with the tools as they are. The fix pipeline trims 38 binds per layout and
adds to none (part 3's 42, less four the trial builder does itself), the
build audit is clean on both layouts, and the 640-gesture sweep has no flag
outside the three stick window states (part 5).

**No change to the model.** The first version of part 2 needed a relay role
in `flow_model` for a window's chord, and the first version of part 3 a
change to `cleanups.is_clear`. With the windows left alone and the Release
down to one remove, neither is needed.

### A new rule: R174

Accepted by the author, 2026-10-12.

**Letting go of one driver never leaves `Steering` bare under the other.**
"Bare" means that `Steering` itself is the top layer that answers the stick
and the drivers.

- **Why.** Bare `Steering` answers a stick at the rim with its exit, and it
  only adds the held driver's layer back at its next repeat. Hold R1, then
  L1, with the stick up at the rim, and let go of R1: on 90.56 `Steering`
  ends although L1 is held.
- **What it asks.** A Release that takes a driver's layer off while the other
  driver can be held either adds that driver's layer in the same array
  (part 1) or leaves the held driver's layer on (part 3).
- **What it does to the removes.** Nothing. It adds no remove and takes none
  out, and no cleanup function changes for it. It is about one add and the
  order of one array.
- **What it costs.** The add is blind (part 1's costs): a layer nobody
  holds, on in 4 of 5,796 random walks with no release missed, gone at the
  next touch of a stick (part 6).
- **Checked by** scenario tests: the sweep of part 5.
- **Not met yet** by the two stick windows (part 2). The register names them
  as a to-do.

### R132, tightened

Accepted by the author, 2026-10-12.

**A list names only layers that can be on the stack when its bind fires.**
Today's wording asks whether the layer can be on the stack with the host.

- **The difference** is a layer above the host that binds the same input.
  While it is on, it answers that input and the host's bind does not run
  (A1, A7). With R1 held, a stick flick opens a window. R1 let go inside the
  window is answered by the window's Release, never by the W layer's. So the
  window in the W layer's Release list has never taken a layer off.
- **What it does to the removes.** The sixteen of part 6, each checked on
  walks. (The eight in the Gyro Modifier 2 Releases there are today's R132:
  the Cleanup audit already calls them "never there", and a register entry
  kept them.)
- **What it does to cleanup.** It can't take one away: a remove that never
  runs while its layer is on is not what takes that layer off. The layer's
  own binds and the cleanup functions do that, and they stay.
- **Not an audit check yet.** The first version of this part said the
  Cleanup audit gets the check. Tried on the whole layout, the simple test
  (does the target bind the same input) marks about 2,250 removes per
  layout, and at least 630 of them were on the stack when their bind fired:
  the target can also sit below the host, and then the remove is the one
  that takes it off
  ([`leftover.txt`](../findings/2026-10-11-owner-release-audit/leftover.txt)).
  A right check needs the order of the two layers from the chains, and the
  stick touch Releases keep their three helpers by their own rule (R123).
  Until it is written, the rule is applied bind by bind with walks, as in
  part 6, and the builder makes those sixteen trims itself.
- **Checked by** a shape test on the binds it has been applied to.

### The register and the notes

- **R159 stops covering the Steering Modifier 2 layers:** their Release is
  not a clear any more. **The same holds in `Cursor Gyro`, since 90.44:** no
  Modifier 2 Release removes it, and inside it the Release only toggles
  `Gyro` (the Gyro Modifier 2 layers answer there; scenario 90.44 C1). So
  after this build the Modifier 2 Release removes no stateful layer but
  `Gyro`, its own toggle: `Steering`, `Cursor Gyro`, `Gamepad` and
  `Menu Keys` all stay (the Gyro Modifier 2 Releases stop naming `Steering`
  as well: part 6). R159's row and its register entry say so for both
  layers, and so do the notes under §11 of the Definition of Done, the
  Modifier 2 row of `resources/Stateful Layer Transitions.md` and the to-do
  "L1 + R1 clears all stateful layers". That to-do still said the two Gyro
  Modifier 2 releases remove `Cursor Gyro` (its 90.21 line); corrected on
  2026-10-12. The "six release clears" of the row become four: the two
  bumpers in each Gyro Modifier 2 layer. Gyro's Modifier 2 keeps its toggle.
- The two R132 register entries of 90.43 that keep the Gyro Modifier 2
  lists end at 90.56 (part 6).
- The register gets a to-do for the right pad's window in `Steering`
  (part 6), beside the stick windows' under R174.
- R120 to R123 no longer apply to the two Steering Modifier 2 layers: they
  have no delay left.
- A10, A11 and A37 list the Modifier 2 layers, for the first driver's key
  there (part 1).
- The owner release audit also proposes three rule wordings (what a deliberate
  clear is, a boundary for a button's Release, stated exceptions). They are
  the author's to accept and this build does not need them.

## Part 5: tests and the build

- The next version, 90.57 if nothing is built before it.
  `tests/test_scenarios_90_57.py`, both layouts, A9 both ways: the traces of
  the record that do not start in a window, each repeated inside one hold;
  the rocking sequence; a tap and a hold of the second driver ending alike,
  with `Gyro` on and off; a missed release of either driver in Modifier 2;
  and the 640-gesture sweep as one test. On the trial layout the sweep has no
  flag outside its three window states, and 480 per layout inside them, all
  of them part 2's first bullet: the two faults that end `Steering` are gone.
- `tests/test_modifier_rocking.py` passes unchanged: the two covers' lists
  change, their binds and the plain modifiers' order do not.
- Twelve tests are known to state the old behaviour. They run frozen on 90.56
  or are rewritten. Ten are scenario tests, the whole of what fails of the
  395 on the trial layout
  ([`plan-candidate-tests.txt`](../findings/2026-10-11-owner-release-audit/plan-candidate-tests.txt)):
  - 90.44 E3, both drivers held under a window: it expects the timer's bump
    (part 3);
  - 90.44 S4, a full push carried through the quick tap ends `Steering`
    (part 3);
  - three that expect `Gyro` to go at the quick tap, in
    `test_scenarios_90_33`, `test_scenarios_90_43` and `test_scenarios_90_44`
    (part 3);
  - three that expect a pad click's layers to go at the quick tap, one each
    in `test_scenarios_90_14`, `test_scenarios_90_16` (X3) and
    `test_scenarios_90_17` (part 3);
  - the Steering modifiers taking 200 ms, in `test_scenarios_90_26` (part 3);
  - the shape test of the Modifier 2 entry's list in `test_scenarios_90_55`
    (parts 3 and 6).

  Two are not scenarios, and come from a run of 24 test modules on the first
  prototype: the shape test of the quick tap's list in
  `test_steering_entry_quiet_drivers`, and the shape test of the Tap Covers'
  stick touch lists in `test_neptune_cursor` (both part 3).

  The modules that are not scenarios have not been run on the plan as it is
  now: they read the layout files, and a scratch copy of the repository does
  not run them (the frozen builders put the repository itself back on the
  import path). More tests that state the cover or the long list are to be
  expected there. On 90.56 as it is the suite passes (1,193 tests, 25
  expected failures).
- The builder starts from the 90.56 snapshot, in its own findings folder, with
  the change report, both VDFs and the snapshot (R151, R164).

## Part 6: fewer removes

The author's reminder (report item 4). Counted on the trial layout; both
layouts lose the same 264:

| Where, per layout | 90.56 | After |
|---|---|---|
| The second driver's Release in the two Steering Modifier 2 layers | 176 | 2 |
| Their two resets | 2 | 0 |
| The cover in their 32 cleanup functions | 32 | 0 |
| The cover in the W and S layers' Releases and Modifier 2 entries, and in `Steering`'s exit | 10 | 0 |
| A Steering Modifier 2 layer in the two covers' lists | 6 | 0 |
| Removes that can never take a layer off (below) | 16 | 0 |
| Seven layers that are never there in each of the four Gyro Modifier 2 Releases (below) | 28 | 0 |
| New: the first driver's Release (part 1) | 0 | 4 |
| **Every remove in the default layout** | **4,277** | **4,013** |

In the Steering layers alone that is 738 to 508.

**The sixteen that can never take a layer off.** In the W and in the S layer,
three binds on the drivers list layers that bind the same driver themselves.
Such a layer sits above the W or S layer and answers the driver whenever it
is on (A1, A7), so the W or S layer's bind never fires with it on the stack:

| Bind, in the W and in the S layer | No longer removes | Why it is never there |
|---|---|---|
| The Modifier 2 entry, on the other driver | The two stick windows | A window binds both drivers |
| The layer's own Release | The two stick windows and the Modifier 2 layer | A window binds both drivers. With part 1 the Modifier 2 layer binds the first driver |
| The other driver's Release | The two stick windows and the Modifier 2 layer | A window binds both drivers. The Modifier 2 layer binds the second |

On 24,000 random walks of the trial layout, half of them with one release in
ten missed, these binds fired 26,637, 23,244 and 36 times, never with a stick
window or a Steering Modifier 2 layer on the stack
([`part6-check.txt`](../findings/2026-10-11-owner-release-audit/part6-check.txt)).
R132 as it stands does not find them (part 4).

**Is anything left on without them?** 90.56 and the trial layout played the
same 23,595 random walks, half of them with one button release in ten missed
([`leftover.txt`](../findings/2026-10-11-owner-release-audit/leftover.txt)).
At the end of each, everything is let go and both thumbs are lifted.

| Walks with a layer still on that nobody holds | 90.56 | Plan |
|---|---|---|
| Default, no release missed (5,796 walks): after letting go | 29 | 40 |
| The same, after a thumb on each stick and off again | 0 | 0 |
| Default, one release in ten missed (5,799): after letting go | 189 | 232 |
| The same, after a thumb on each stick | 0 | 0 |

The alternative layout gives 27 and 38, then 142 and 168, and 0 after the
sticks every time. So the cleanup functions still take off everything that
is left: none of them loses a remove of a layer that can be there, and the
Cleanup audit passes. What the long Release did besides was sweep up layers
that other binds had left on. Without the sweep they wait for the next touch
of a stick. With no release missed that is 13 walks more, 2 fewer:

- **A W or S layer, 6 walks.** In all six a bumper was let go while the
  right pad's window was open. `RTP: Double Tap` binds both bumpers'
  Releases; it removes itself and the plain modifier layers and lists no
  Steering layer, so the bumper's own layer never sees the release. 90.56
  does the same: hold R1, tap the right pad, let go of R1 inside the window,
  and the W layer stays on. With Modifier 2 on, 90.56's next Release swept
  that up. Here the hand-over adds the other bumper's layer (4 walks, part
  1), the second driver's Release leaves the first's on (1, part 3), or it is
  the 90.56 gesture as it stands (1).
- **`RTP: Tap Cover` or a left pad key layer, 7 walks.** A thumb lifted from
  a pad while a stick window is open. The window answers the pad's Release;
  for the right pad it removes itself and `RTP: Entry Point` and leaves the
  cover. 90.56 does the same (5 walks); there the walk had often been swept,
  or had left `Steering`, before it got that far.

Both go back to binds this plan leaves alone: the right pad's window and the
stick windows answer a Release for a layer under them and don't list it. The
removes that would close that belong in those windows' lists, a handful
where the layer is on the stack. **The author, 2026-10-12: leave it.** The
right pad's window got its bumper Releases for the plain and Gyro modifiers
after the same fault with the menu buttons (the to-do "Stick touches and the
menu buttons", 2026-10-04); the Steering layers were never added to them. It
is registered as a to-do with the stick windows.

**The eight in the Gyro Modifier 2 Releases** (the author, 2026-10-12:
"ok"). Each of the four bumper Releases in `Gyro | L1!R1: Modifier 2` and
`Gyro | R1!L1: Modifier 2` names `Steering` and `Steering | LS: Entry Guard`.
The author asked for that on 2026-10-04, when the Gyro Modifier 2 quick tap
was the way to Base from the Steering fallback; the fallback went in 90.42
and a register entry has kept the two removes since. `Steering` binds both
bumpers and sits above `Gyro`, so a Gyro Modifier 2 layer can't be entered
while it is on, and entering `Steering` clears the stack first (R163). The
Cleanup audit calls both "never there", and in 953 firings on 12,000 walks
neither was on the stack. With them out the fix pipeline adds nothing back,
the build audit is clean on both layouts, and the same ten scenario tests
fail and no other. The tests that state the old list build their own frozen
layouts.

The same register entry kept five more layers in each of those Releases
that the audit also calls "never there": the two plain modifiers, the two
plain Modifier 2 layers and the other Gyro Modifier 2 layer. Twenty removes
per layout, on the stack in none of the 953 firings. **The author,
2026-10-12: "yes"**, so they go as well: 28 in all. Tried without them, the
audit is clean and the same ten tests fail.

The two register entries were to be deleted. They can't be: the frozen
builders of 90.43 to 90.56 read the same register and rebuild a different
layout without them (tried on three of them). No layer tells 90.57 from
90.56, so the entries get a new scope key, `until: "90.56"`, and hold on
layouts up to that release only.

**Left as they are:** the six stick layers in those lists, which bind no
driver and do get removed; and the fourteen binds with the longest list in
the layout, 89 removes each: the eight stick click Releases that enter a
transition, the four stick click chords of `Gamepad` and `Menu Keys`, and
the two menu chords that enter `Menu Keys`. Those still leave a mode (R163)
and are not part of this plan. They are the next largest block: 1,246 of
the 4,013. (This part first counted only the eight Releases, 712.)

## What stays as it is

- The two stick windows, every bind of them (part 2).
- `Steering`'s exit. With no driver held, a full push up or down still leaves
  `Steering`, also when the last driver is let go with the stick at the rim.
- Base's Modifier 2 layers, Gyro's but for the 28 removes of part 6, and
  the rocking order.
- The stick modifiers, the scroll layers and the stick's two covers. The W
  and S layers keep their binds; their three lists on the drivers get shorter
  (parts 3 and 6). No new layer, no delay, no right pad removes, no chord with
  Invert Activation.

## Not verified on the Deck

Everything above is the simulator's. It holds a control or not, so it can't
tell a half push from the rim, and it runs one array as one step. Part 1
rests on A10 and A11 (a key on a button that is already held) and A37. Parts
3 and 6 take binds out and rest on nothing new. Part 2's Deck check is the
one thing here that can be run on 90.56 today.

## Answers

Every question is answered, all by the author on 2026-10-12: this plan's
two, the three of the owner release audit that part 3 rests on, and those
that came up with part 4.

| Question | Answer | Where |
|---|---|---|
| In a stick window, does the second driver's press add Modifier 2 itself, or only close the window? | First "a chorded dual bumper/trigger press should just remove the window properly"; then "just dont touch the window for now and have it remove itself as today". Neither is built | Part 2 |
| Should the second driver's Release keep clearing menu layers that a missed release left on? | No | Part 3 |
| Should that Release still turn `Gyro` off? (the audit's D1) | No | Part 3 |
| Should it still take off the first driver's layer? (D2; question 2 of the first version) | "I like the scenario where we leave it" | Part 3 |
| Should the 200 ms timer and its cover stay on the second driver? (D4) | No, they come out | Part 3 |
| The two rules of part 4: R174 and the tighter R132 | Yes to both | Part 4 |
| The right pad's window answers a bumper's Release in `Steering` and lists no Steering layer. Fix it in this build? | "leave it" | Part 6 |
| `Steering` and its Entry Guard in the four Gyro Modifier 2 Releases, eight removes that never take a layer off. Drop them? | "ok" | Part 6 |
| The twenty further removes the same register entry keeps there. Drop them too? | "yes" | Part 6 |
| Build it? | "yes now start building" | 90.57 |
