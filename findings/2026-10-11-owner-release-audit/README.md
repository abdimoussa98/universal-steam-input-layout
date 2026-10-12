# Owner releases: the rules, and what the Releases remove (audit of 90.56)

Read-only, 2026-10-11, on the author's request: the Steering Modifier 2
layers remove too many layers on the bumpers. Are those removes needed, and
do the owner release rules need refining? Nothing in the layouts changed.
Both layouts give the same counts; the layer names are the default layout's.

    PYTHONPATH=. python3 findings/2026-10-11-owner-release-audit/releases.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/walks.py 1500 8 4
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/walks.py 1500 8 20
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/walks.py 1500 8 8 1
    PYTHONPATH=. python3 findings/2026-10-11-owner-release-audit/summary.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/gestures.py
    PYTHONPATH=. python3 findings/2026-10-11-owner-release-audit/trim_trial.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/first_driver.py walks 750
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/menu_layers.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/cover_timer.py walks 750 trial
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/cover_diverge.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/menu_stale.py
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/with_two_driver_plan.py <scratch dir>
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/plan_candidate.py <scratch dir>
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/part6_check.py <scratch dir>
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/window_release.py <dir> [<dir>]
    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/window_fix.py <scratch dir>

Their output is in `releases.txt`, the three `walks-*.txt`, `summary.txt`,
`gestures.txt` and `trim-trial.txt`. The trial takes about ten minutes.

**Since then (2026-10-12):** the author answered decision 1 (no, the quick
tap leaves `Gyro` alone) and, after the replays of section 6, decision 2
(leave the first driver's layer on). The author then asked why the second
driver has a 200 ms timer at all: section 7, from `cover_timer.py` and
`cover_diverge.py`. Decision 4 followed: yes, the timer and its cover come
out. Decision 3, restated in section 6, was answered no. The decisions are
now part 3 of the two-driver plan (section 8). Nothing is built.

## In short

- Each Steering Modifier 2 layer binds one bumper, with three entries. Two
  are small. The third, the Release, removes **88 of the layout's 90
  layers**.
- That list is the old "clear to Base". 90.44 took `Steering` and
  `Cursor Gyro` out of it, so the gesture no longer leaves `Steering`. The
  other 88 stayed.
- **61 of the 88 are never on the stack when it fires. 25 are kept on by
  something else: the other driver, a mode, a thumb or a menu button. 2 are
  the layer's own.**
- No audit reads this list. The rules let a "deliberate clear" keep its
  whole list, and the Cleanup audit tells a clear by its list being whole.
- The other bumper Releases are small and hold up. The fault is these two
  lists and the rule that shelters them, not owner releases in general.

## Terms

- **Release:** a Release Press. It fires in the layer that answers the button
  at the moment the button is let go.
- **Owner release:** the Release on the button that keeps a layer on, which
  removes that layer. `L1: Modifier 0`'s L1 Release is one.
- **Driver:** L1 or R1 inside `Steering`. R1 types W, L1 types S. The **first
  driver** is the one held first; its layer (`Steering | R1: W Key` or
  `Steering | L1: S Key`) is on the stack. Pressing the **second driver** adds
  a Steering Modifier 2 layer on top, and that layer binds only the second
  driver.
- **Cover:** `L1: Tap Cover` or `R1: Tap Cover`. The Modifier 2 layer adds it
  over itself after 200 ms, or at once when a command is used or a thumb
  lifts. Once it is on, the cover's Release answers the second driver.
- **Quick tap:** the second driver let go before the cover is on. Only then
  does the Modifier 2 layer's own Release fire.
- **Whole-layout list:** a list that removes every layer that isn't a mode.
- **On the stack, by the chains:** the audits' stack model. It does not follow
  chords or delayed adds, so it misses layers.
- **On the stack, in the walks:** 36,000 random press sequences per layout on
  the press simulator, 60 events each, starting with the entry into
  `Steering`. Between 4% and 20% of button releases are missed (let go with
  the Steam menu open); a third of the walks use waits of 1 to 80 ms. A
  sample, not a proof, and not the Deck.

## 1. What the rules say about an owner release

| Rule | What it says | Checked on a Release |
|---|---|---|
| §7, "Normal exit" | It removes only the state it owns | No |
| R110 | Removes run before the add | Scenarios, in part |
| R124 | A cover's Release doesn't reopen the window | Tests, in part |
| R132 | A Release lists only layers that can be on the stack with its host. A deliberate clear keeps its whole list | Cleanup audit, "never there". Skipped when the list is whole |
| R138 | The held button's layer owns its combos; another held button falls through | In part |
| R159 | The Modifier 2 clear removes stateful layers and helpers, except `Steering` and `Cursor Gyro` since 90.44 | Tests, in part |
| R163 | Entering a transition clears the whole stack first | Tests |
| R127 to R131 | The boundary: never a stateful layer, a stick helper, a window, another button's layer | Cleanup functions only, not Releases |

[Cleanup Functions](../../resources/Cleanup%20Functions.md) adds that an owner
release's scope "has to be stated per gesture". No table of those scopes
exists.

## 2. Every Release, by size

276 Releases remove layers, 1,823 removes in all.

| Where | Releases | Removes |
|---|---|---|
| Buttons | 70 | 516 |
| Stick touches | 160 | 516 |
| Stick clicks | 8 | 712 |
| Pads, stick edges and directions | 38 | 79 |

- **Ten Releases hold 888 of the 1,823.** Eight are the stick click Releases
  of the four menu Entry Points: 89 removes each, then they add a transition
  (R163). Two are the Steering Modifier 2 Releases: 88 each, and they add
  nothing.
- Of the 516 removes on button Releases, 176 are in those two. The other 68
  Releases share 340: five on average, 22 at most (`RTP: Double Tap`).
- The Cleanup audit's "never there" check passes on all 68, the four Gyro
  Modifier 2 quick taps by their registered exception.

## 3. The two Steering Modifier 2 lists

`Steering | L1!R1: Modifier 2` binds R1; `Steering | R1!L1: Modifier 2` binds
L1. The three entries:

| Entry | Does | Removes |
|---|---|---|
| Chorded Press, 200 ms | Adds the cover | 0 |
| Regular Press, repeating at 250 ms | The timer's reset (R120) | 1, the cover |
| Release | The quick tap | 88 |

**Where the 88 come from.** In 90.10 the quick tap was the way out of
`Steering` to Base: the author's rule of 2026-10-01, as `todos.md` records
it, is that the Modifier 2 clear "always clears everything to Base,
including Gyro". It listed all 70 layers, and one more with every layer
added since. 90.44 took `Steering` and `Cursor Gyro` out on the author's
request and left the rest. The to-do "L1 + R1 clears all stateful layers"
still states the older rule.

**What the 88 are** when the Release fires (13,567 times in the walks):

| Layers | Count | Kept on by | Removing it |
|---|---|---|---|
| The Modifier 2 layer | 1 | The second driver | The job |
| Its cover | 1 | The second driver | Its own. Never on at that moment: the cover would answer |
| The first driver's layer | 1 | The first driver, still held | Lets W or S go. The held driver puts the layer back |
| `Gyro` | 1 | A mode | Turns Gyro off. Nothing in `Steering` turns it on |
| The six `LST` and `RST` helpers | 6 | A thumb on a stick | A resting thumb puts its Entry Point back |
| Pad layers, with `RTP: Double Tap` | 14 | A thumb on a pad | Takes off a click whose release was missed. A click still held is let go as well |
| The two menu stick guards, `Menu Buttons: Tap Cover` | 3 | Start or Select | Not replayed |
| Everything else | 61 | Never on the stack | Nothing |

The 61 are never on by the chains and never in the walks: the plain and Gyro
modifiers and their layers, the menu chains, the transitions, the ramp
layers, `Gamepad`, `Menu Keys`, and eleven Steering layers (the eight stick
layers, which the Modifier 2 entry removes, the other order's two layers and
the Entry Guard). They can't be left over from before `Steering` either:
entering it clears the whole stack (R163). The lists are in `lists-L1.json`
and `lists-R1.json`.

**What the quick tap does today**, on the simulator (`gestures.txt`):

1. R1 held, W down. L1 down: the Modifier 2 layer lands.
2. L1 up after 60 ms: the Modifier 2 layer and the W layer go, and W lets go.
   The other 86 removes find nothing.
3. R1 is still held, so `Steering` adds the W layer again and W goes down:
   at once, or 50 ms later, depending on A9 (unverified).
4. The stack is what it was before L1 went down.

Holding L1 past 200 ms instead, the cover's Release takes off the cover and
the Modifier 2 layer, and nothing else moves. The quick tap differs in five
ways:

- W or S is let go and taken up again.
- `Gyro`, when it is on under `Steering`, is removed.
- With the stick held fully up or down, taking the W layer off uncovers
  `Steering`'s own exit on a full push, and `Steering` ends (scenario
  90.44 S4).
- A pad click held through the tap is let go. It comes back only if Steam
  fires the bind the removal uncovers (A9; scenario 90.16 X3).
- Resting thumbs get layers they did not have. With R1 held and both thumbs
  on the sticks, the stack went from the W layer alone to
  `LST: Entry Point > RST: Entry Point > W layer`.

**The scenario tests with shorter lists** (`trim-trial.txt`; in memory, no
file changed; 395 tests):

- **Without the 61:** no scenario changes its outcome. One test of the
  list's shape fails: it expects more than 50 entries.
- **Down to the layer and its cover:** 7 change. Three expect `Gyro` to go
  (90.33, 90.43, 90.44). Three expect a pad click's layers to go (90.14,
  90.16, 90.17). One expects the first driver's layer to go (90.44 S4).

**My reading.** The 61 do nothing and can go. Of the other 27, only the
layer and its cover are the Release's own; the rest is the author's call
(section 6).

## 4. The other bumper Releases in the Steering layers

Both layouts, all walks:

| Release | Lists | Fired | On the stack at least once |
|---|---|---|---|
| The W layer's R1, the S layer's L1 (their own) | 11 | 81,686 | 9 |
| The W layer's L1, the S layer's R1 (the other driver) | 10 | 161 | 5 |
| The two stick windows, either driver | 3 | 1,724 | 3 |
| `L1: Tap Cover`, `R1: Tap Cover` | 4 | 37,341 | 4 |
| `L1&R1: Tap Cover`, either bumper | 8 | 12,958 | 8 |

- **Twelve removes in the W and S layers never take anything off.** The two
  stick windows are in all four lists; the Modifier 2 layer and its cover
  are also in the other driver's two. Each of those layers binds the bumper
  in question, so while it is on it answers the Release itself. My reading:
  harmless. The windows are stored to run first, the shape R148 asks for
  around an Always On layer. Not worth a change by themselves. Since then the
  author's reminder (2026-10-12: "remember i still want to reduce unnecessay
  removals") put them in the two-driver plan's part 6, with four more that
  the plan itself makes dead.
- **The other driver's Release in the W and S layers** fires only when the
  second driver is let go with no Modifier 2 layer on: 161 times against
  81,686. I found no record of what it is for.

## 5. Where the rules fall short

1. **A clear is told by its list.** The Cleanup audit calls a Release a
   deliberate clear when it removes every layer that isn't stateful
   (`cleanups.is_clear`). So a whole list exempts itself, whatever the
   gesture does. The Steering quick tap stopped being a way out in 90.44 and
   kept the exemption.
2. **No boundary for a Release.** R127 to R131 bind cleanup functions. A
   button's Release may remove a mode, a thumb's helper or a pad layer and
   nothing reports it.
3. **Scopes are not written down.** On the other 68 button Releases, 72 of
   the 276 removes of another layer target one that only another button
   keeps on: the plain Modifier 2 quick tap, the first driver ending the
   second driver's Modifier 2, the menu pairs, `RTP: Double Tap`. Each is
   designed, so a blanket rule would be wrong, but nothing tells a designed
   one from a leftover.

**Proposed wording, for the author to accept or change:**

- **A deliberate clear is a Release that leaves a mode:** it adds a
  transition, or it removes the stateful layer its host sits in. Only a
  deliberate clear keeps a whole-layout list (R132, R163), and the audit
  tests for that, not for the list. The eight stick click Releases still
  qualify. The two Steering Modifier 2 Releases don't.
- **A button's Release that is not a deliberate clear never removes a
  stateful layer, a stick helper or a pad layer.** This is part of R131's
  boundary, applied to Releases. Outside the two lists, the only Releases
  that cross it today are the four Gyro Modifier 2 quick taps, which remove
  `Gyro` and `Steering` by a registered exception.
- **A Release that removes a layer only another button keeps on says so:**
  one line per gesture in the register. That is the "stated per gesture" of
  Cleanup Functions, made checkable.

Under the first two, each Steering Modifier 2 list is at most six: the
layer, its cover, the first driver's layer and the three menu layers.

## 6. Decisions for the author

**D1. Answered: no** (author, 2026-10-12). Inside `Steering` a quick tap of
the second driver leaves `Gyro` alone.

**D2. Answered: leave it** (author, 2026-10-12: "I like the scenario where we
leave it"). The question was whether the quick tap should take off the first
driver's layer. Replayed in memory on four versions of the Release
(`first_driver.py`, output in `first-driver.txt`), each on both layouts, both
orders of the drivers and both ways of A9:

- **Take it off:** the Modifier 2 layer, its cover and the first driver's
  layer. In every gesture below it does what 90.56 does today.
- **Leave it:** the Modifier 2 layer and its cover.
- **Off and back:** take it off, and end the Release by adding it again.

| Gesture | Today, which takes it off | Leave it |
|---|---|---|
| Hold R1, tap L1 | W is let go; back at once or after 50 ms (A9) | W stays down |
| Both held, stick fully up, L1 let go | `Steering` ends | `Steering` stays |
| R1 held, thumbs resting on both sticks, tap L1 | Stick helper layers land under the W layer, in half the runs | Nothing changes |
| Both held, R1 let go unseen in the Steam menu, L1 let go inside 200 ms | Nothing is left on | The W layer is left on, typing nothing |
| The same, L1 held past 200 ms first | The W layer is left on: the cover's Release answers, in every version | The same |
| Both let go unseen, then L1 tapped | Both stale layers go | The Modifier 2 layer goes, the W layer is left on |

**What taking it off buys** is the fourth row and the sixth: a first driver
let go unseen, with the second driver still inside its first 200 ms. A W or S
layer left on types nothing. It goes on the next tap of either driver, touch
or push of either stick, Start or Select. It stays through a face button, a
thumb on the right pad, and waiting.

**How often**, on the same 12,000 random walks per version (both layouts, one
button release in ten missed):

| | Today, which takes it off | Leave it |
|---|---|---|
| Quick taps with the first driver held | 1,989 | 2,060 |
| The drive key let go at the tap | 1,989 | 0 |
| `Steering` gone before the next press | 169 | 0 |
| Walks ending with a W or S layer left on | 99 | 105 |
| Walks ending with any layer left on | 319 | 318 |

The counts differ a little because the walks part ways after the first tap.
The short take-it-off list gives today's picture: the key let go in all
1,985 taps, `Steering` gone in 164.

**Off and back** gives the results of leaving it: every gesture, and each
count to within one walk. Two cautions. It also puts the layer back when the
first driver was let go unseen, so it cleans up no more than leaving it does.
And the simulator applies a Release's commands as one step: on the Deck the
key has to come back on a bumper that is already down, with no gap, when its
layer goes and returns inside one Release (A10 and A37, neither verified).
Leaving it asks nothing of Steam.

**The same question from the stick's side.** Part 3 of the
[two-driver plan](../../plans/2026-10-11-two-drivers-in-steering.md) of the
same day reaches it through the second row of the table, picks "leave it" as
well, and has off and back as its other way. One answer serves both.

**Why leave it** (my pick, and the author's answer). The cost is a stale
layer in one Steam-menu case, which types nothing and goes on the next input.
Taking it off costs a let-go of W or S on every quick tap, and `Steering`
itself when the stick is fully up or down.

**D3. Answered: no** (author, 2026-10-12). Should the quick tap keep clearing
stuck menu layers? First asked as "the three menu layers"; the author: "i
dont know what you mean". Restated as a gesture (`menu_stale.py`,
`menu-stale.txt`):

1. In `Steering`, hold Start and push the left stick. Two helper layers of
   that gesture come on: `Menu Buttons: Left Stick Guard`, and after 200 ms
   `Menu Buttons: Tap Cover`.
2. Open the Steam menu and let go there. The layout never sees the release,
   so both stay on. Nothing is typed.
3. Back in the game, in both versions, they go on the first touch of either
   stick or tap of Start or Select. A tap of A or of one bumper leaves them.
4. The one difference: hold R1, tap L1. Today the 88 removes happen to
   include them, so they go. With the one-remove Release they stay until R1
   is up and a thumb is on a stick; with a thumb already resting they go the
   moment R1 is let go.

They are under a quick tap only after such a missed release: 0 of 7,565 quick
taps with none missed, 35 of 7,188 with one in ten missed (`menu_layers.py`).
They are not kept in the list. They clear themselves on the next stick
touch, which is the rule that every layer takes care of itself.

With D1, D2 and D3 each list is two removes: the Modifier 2 layer and its
cover. That is what the cover's Release removes on this stack, so a quick tap
and a hold end the same way. Section 7 follows that up, and D4 takes the
cover out as well: one remove.

## 7. The 200 ms timer on the second driver

The author, 2026-10-12: "why is there a 200 millisecond delay on the bumpers?
For mod 2, I thought we got rid of the whole tapping the bumpers clears you
out of steering. I don't want to be cleared out of steering in mod 2."

**Why it is there.** It was built with the clear. In the Steering design of
2026-09-30 a quick tap of the second driver left `Steering` for Base, and a
hold, a used command or a lifted thumb had to stay. The timer is what told
them apart: after 200 ms it puts the cover over the Modifier 2 layer, and the
cover answers the Release with a short list instead of the clear.

**What 90.44 did.** It took `Steering` out of the tap's list and left the
timer, its reset and every add of the cover. The tap could still end
`Steering` one way, through the first driver's layer (D2).

**Is the author cleared out of `Steering`?** Every Release of the second
driver out of a Steering Modifier 2, 6,000 walks, no release missed:

| | Today | Leave it (D1, D2) |
|---|---|---|
| Releases of the second driver | 2,905 | 3,047 |
| `Steering` gone, the first driver still held | 86 | 0 |
| `Steering` gone, no driver held | 3 | 3 |

The last row is not Modifier 2. No bumper is down and the stick is fully up
or down: that is `Steering`'s own exit on a full push.

**What the timer still decides, once the tap is short.** Compared in memory
with a version that never adds the cover (no timer, no reset, no add of the
cover; the second driver's Release removes the Modifier 2 layer):

- Seven gestures, among them a tap, a hold, a used command, a thumb lift and
  the first driver let go first: the same keys and the same end.
- 395 scenario tests: two tell them apart, and both test the timer itself,
  its 200 ms (90.26) and its bump (90.44 E3).
- The same 6,000 walks: 27 of 5,913 differ with no release missed, 105 of
  5,916 with one in ten missed.

**What would be lost with it:**

- **A low bump** at 200 ms.
- **One cleanup, which the cover has by its guard.** Its cleanup function on
  the stick touches is guarded by the second driver alone; the Modifier 2
  layer's own are guarded by either driver. So when the second driver's
  Release never reached the Modifier 2 layer (missed in the Steam menu, or
  answered by the right pad's window in the ones traced), a thumb on a stick
  clears the stale Modifier 2 although the first driver is held. Without the
  cover it stays until the first driver is let go or the second is tapped
  again. That is 20 of the 27 and 99 of the 105. Before the cover lands,
  90.56 has the same gap.

Of the rest, 4 and 3 are another timer landing at a different time. In the
two traced it is the right pad's 150 ms: the reset's repeating remove
restarts it, so it lands late while the cover's timer runs (A13). 3 and 3
were not traced.

**What would go**, per layout: the two timers and their resets, the other 28
adds of the cover, 48 removes of a cover in the Steering layers, and the 6
removes of a Steering Modifier 2 layer in the two covers' own lists. The
second driver's input goes from three entries to one Release with one
remove. `L1: Tap Cover` and `R1: Tap Cover` are also the plain modifiers'
covers, so the rocking tests have to pass before and after.

**D4. Answered: yes** (author, 2026-10-12). The timer and the cover come out
of the two Steering Modifier 2 layers. It tells nothing apart any more, and
the stale case it helps with ends when the first driver is let go or the
second is tapped again.

## 8. Against the two-driver plan

The author, 2026-10-12: does
[the two-driver plan](../../plans/2026-10-11-two-drivers-in-steering.md)
align with this? Yes in what it is for: staying in `Steering` while a driver
is held. Its part 3 is D2. Its parts 1 and 2 close two faults this audit does
not touch. The plan's own sweep of 640 two-driver gestures, where a flag is
one thing gone wrong in one gesture (`with_two_driver_plan.py`):

| Version | Flags per layout |
|---|---|
| 90.56 | 664 |
| D1, D2 and D4 alone | 608: the first driver let go with the stick at the rim still ends `Steering` (128), and a second driver pressed in a stick window still types its key (480) |
| The plan's parts 1 and 2 alone | 32: the second driver let go with the stick at the rim ends `Steering` |
| Both | 0 |

**Where the plan was behind the decisions.** It was written before D1 and
D4. The author, 2026-10-12: "go ahead and edit the plan". The plan is revised
on each point below; its part 3 is now D1, D2 and D4 together, and D3 was
its second question until the author answered it.

- Its quick tap still "clears everything except `Steering` and
  `Cursor Gyro`". After D1, D2 and D4 the second driver's Release removes one
  layer, there is no quick tap apart from a hold, and part 3 is absorbed.
- Part 1's new Release removes the second driver's Tap Cover, and part 1
  counts on the two covers' stick touch cleanups. Part 2 starts "the
  Modifier 2 hold timer" at the press. After D4 neither the cover nor the
  timer is in these layers.
- Part 4's change to `cleanups.is_clear` is not needed: a list of one remove
  is an ordinary Release to the audit as it stands.
- Part 4 adds the first driver's layer to R159's "Modifier 2 clear". After the
  decisions the Steering Modifier 2 Release is no clear at all, so R159 and
  the to-do "L1 + R1 clears all stateful layers" have to say that.
- Part 5's tests: eight more scenario tests state the old behaviour. Three
  expect `Gyro` to go (90.33, 90.43, 90.44), three a pad click's layers
  (90.14, 90.16, 90.17), one the 200 ms (90.26) and one a list of more than
  50 removes (90.55). 90.44 E3, already on the plan's list, also expects the
  timer's bump.

Tried for the revision, in a scratch copy: with D1, D2 and D4 alone the fix
pipeline trims 42 binds per layout and the build audit is clean on both
layouts. The plan's parts 1 and 2 went through the pipeline with them only
after the two answers below.

**The plan's two questions, answered 2026-10-12.** In a stick window the
other driver's chord only removes the window, and D3 is no. With the reminder
about removals the plan gained a part 6. The whole of it as one trial layout
(`plan_candidate.py`, `plan-candidate.txt`, `part6-check.txt`): the fix
pipeline trims 38 binds and adds to none, the build audit is clean on both
layouts with the tools as they are, the sweep gives no flag, and each layout
has 236 removes fewer (4,277 to 4,041 in the default). Part 2 also gained one
change found on the way (`window_release.py`): a stick window's Release on a
driver removes that driver's own layer and no longer the other driver's,
which on 90.56 took a held driver's layer off in 60 of 471 such Releases.
Both window changes came out again the same day (section 9): the windows
stay as they are, and that fault with them.

**One cost to weigh.** Part 1 binds the first driver inside the Modifier 2
layer, so its key is typed there too. With D1, D2 and D4 alone W is never
touched while L1 is pressed and let go. With part 1 W changes hands twice,
when Modifier 2 lands and when it leaves. That is seamless only if a key
handed from one layer to another stays down (A10 and A37, not verified), the
dependence D2 avoided. The plan names it. A layer that binds a button takes
the whole input, so part 1 cannot have its Release without the key. The stick
windows have handed W over the same way since 90.10.

## 9. After a stick window: making Modifier 2 come

The author, 2026-10-12, after the plan's part 2 was set to "the chord only
removes the window": "give me suggestions to fix this". Read as the cost
that answer carries: Modifier 2 then depends on the W or S layer's entry, a
repeating chord with seven sub-commands, firing under a bumper that is
already down, the shape the author reported on 2026-10-10 as not firing its
repeat.

Three versions on two simulators (`window_fix.py`, `window-fix.txt`). The
strict one builds that report in, with the slow reading of A9: a bind
uncovered under a held button waits for its repeat, and a repeating chord
with more than one sub-command never runs on a repeat. The gesture: first
driver held, stick flicked, second driver pressed 20 ms into the window and
held, then A.

| Version | Simulator as it is | Strict | Removes | Build audit |
|---|---|---|---|---|
| 90.56 | Modifier 2 comes, after a stray key. 664 flags in the sweep | No Modifier 2: A types F. 832 flags | 4,277 | Clean |
| As answered: the chord only removes the window | Modifier 2 comes. 0 flags | No Modifier 2. 336 flags: 288 presses without it, and `Steering` ending 48 times when the first driver is let go | 4,041 | Clean |
| The window's chord removes the window, then adds Modifier 2 | Modifier 2 comes. 0 flags | Modifier 2 comes. 0 flags | 4,041 | Needs the relay change the plan's first version had; clean with it, by the two-driver record |
| The W and S layers' entry split in two chords, one of them a single repeating add | Modifier 2 comes. 0 flags | Modifier 2 comes. 0 flags | 4,029 | Fails: the single add can land Modifier 2 over a stick modifier when the stick moves inside 50 ms, and that layer's cleanups are then open under a later window (R140) |

So 90.56 has the weakness already; the plan neither adds nor removes it.

**Suggested, in this order:**

1. **Test before fixing.** On 90.56 as installed: hold R1, flick the stick,
   press and hold L1 inside the window, wait half a second, press A. M means
   the uncovered entry does fire on the Deck and nothing needs fixing. F
   means it does not.
2. **If F: the window's chord adds Modifier 2 as well,** after removing the
   window, in the one bind on the fresh press. It is the shape of every
   other window's second press (R148). It adds four add commands and no
   remove.
3. **Not the split entry.** It is the fewest removes and holds on the strict
   simulator, but it can strand a stick layer under Modifier 2.
4. **Or leave it:** the press that closes the window gives no Modifier 2 and
   the second driver is pressed again.

**The author's answer** (2026-10-12): "just dont touch the window for now and
have it remove itself as today". The plan's part 2 is not built: the two
stick windows keep every bind of 90.56, the chord and the shorter window
Release included. The comparison above was run while the trial layout still
had the chord; `plan_candidate.py` now builds without it, and with
`window` as a last argument builds the earlier version. On the trial layout
as it is now: the build audit is clean on both layouts, each layout has 236
removes fewer (4,277 to 4,041), the sweep's two faults that end `Steering`
are gone and its 480 window flags stay, and ten of the 395 scenario tests
state the old behaviour (`plan-candidate.txt`, `plan-candidate-tests.txt`).
With the eight removes of section 10 the count is 244 fewer (4,033); the two
output files are from that layout.

## 10. With fewer removes, is anything left on?

The author, 2026-10-12, on the plan's part 4: "i want let removals, but i
also wanna ensure we are properly cleaning up the necessary layers".

**Left over** here means a layer on the stack that is not a mode (`Base`,
`Gyro`, `Steering`, `Cursor Gyro`, `Gamepad`, `Menu Keys`) once every button
is let go and both thumbs are lifted.

[`leftover.py`](leftover.py) plays the same random walks on 90.56 and on the
plan's trial layout, lets everything go, then puts a thumb on each stick and
off again, then taps each bumper ([`leftover.txt`](leftover.txt)):

| Walks with a layer left over | 90.56 | Plan | Only the plan | Only 90.56 |
|---|---|---|---|---|
| Default, no release missed (5,796 walks): after letting go | 29 | 40 | 13 | 2 |
| after a thumb on each stick | 0 | 0 | | |
| Default, one release in ten missed (5,799): after letting go | 189 | 232 | 58 | 15 |
| after a thumb on each stick | 0 | 0 | | |
| Alternative, no release missed (6,000): after letting go | 27 | 38 | 13 | 2 |
| after a thumb on each stick | 0 | 0 | | |
| Alternative, one release in ten missed (6,000): after letting go | 142 | 168 | 34 | 8 |
| after a thumb on each stick | 0 | 0 | | |

So the cleanup functions take off everything that is left, on both versions.
What the 88-remove Release did besides was sweep up layers that other binds
had left on; without it they wait for the next touch of a stick.

The thirteen walks of the first row, traced (the simulator's answer):

- **A W or S layer, 6.** In all six a bumper is let go while the right pad's
  window is open. `RTP: Double Tap` binds both bumpers' Releases, removes
  itself and seventeen plain and Gyro modifier layers and helpers, and lists
  no Steering layer. So the bumper's own layer never sees the release. Replayed on both
  versions: hold R1, tap the right pad, let go of R1 inside the window, and
  the W layer stays on, typing nothing, until a thumb touches a stick. With
  Modifier 2 on, 90.56's next Release swept that up. On the plan the
  hand-over adds the other bumper's layer (4 walks), or the second driver's
  Release leaves the first's on (1); the sixth is the plain gesture.
- **`RTP: Tap Cover`, 6, and `Escape`, 1.** A thumb is lifted from a pad
  while a stick window is open. The window answers the pad's Release: for the
  right pad it removes itself and `RTP: Entry Point` and leaves the cover.
  90.56 leaves the cover in 5 walks of its own. I did not get this one as a
  clean replay.

Both are binds the plan leaves alone. Closing them means a few removes in the
windows' own lists, where the layer is on the stack. **The author,
2026-10-12: "leave it".** The right pad's window got its bumper Releases
after the same fault with the menu buttons (the to-do "Stick touches and the
menu buttons", 2026-10-04); they cover the plain and Gyro modifiers, and the
Steering layers were never added.

**The tightened R132, tried on the whole layout.** The same run counts the
removes whose target binds the bind's own input: 2,252 per layout on 90.56
(default), 2,116 on the plan. Of those the walks saw 630 on the stack when
their bind fired, 617 never, and 1,005 in binds that never fired. The target
can sit below its host, and then the remove is what takes it off; and the
stick touch Releases list their three helpers by R123. So the test "the
target binds the same input" is not the rule. It needs the order of the two
layers, and it is not an audit check yet. The plan's part 4 says so now, and
its sixteen trims stay a list checked bind by bind
([`part6-check.txt`](part6-check.txt)).

**The Gyro Modifier 2 Releases and `Steering`.** Each of the four lists
`Steering` and `Steering | LS: Entry Guard`. On 12,000 walks per layout they
fired 953 times (default) and neither was on the stack. `Steering` binds
both bumpers and sits above `Gyro`, so those layers can't be entered while it
is on. Eight removes per layout. The author asked for them on 2026-10-04,
when the Gyro Modifier 2 quick tap was the way to Base from the Steering
fallback; two R132 register entries of 90.43 have kept them since the
fallback went, and without those entries the Cleanup audit calls both "never
there". **The author, 2026-10-12: "ok"**, so they are in the plan's part 6
and in `plan_candidate.py`. With them out the fix pipeline adds nothing
back, the build audit is clean on both layouts, the same ten scenario tests
fail, and the walks of this section give the same table.

The same two entries keep five more layers in each of those four Releases:
`L1: Modifier 0`, `R1: Modifier 1`, the two plain Modifier 2 layers and the
other Gyro Modifier 2 layer. Twenty removes per layout, "never there" by the
audit, and on the stack in none of the 953 firings (`L1&R1: Tap Cover` was
not either, but it is the target of the bind's own delay and stays). Tried
without them: audit clean, the same ten tests, 4,013 removes. Not in the
plan; the author has not been asked yet.

## 11. Built as 90.57

The author, 2026-10-12: "yes" to the twenty further removes, and "yes now
start building". The release record is
[findings/2026-10-12-driver-handover-and-fewer-removes](../2026-10-12-driver-handover-and-fewer-removes/README.md).
Its layouts equal the last trial layout of this audit bind for bind, and the
table of section 10 came out the same on the 90.56 snapshot against the
installed layouts.

The two register entries could not be deleted, as section 10 had it: the
frozen builders of 90.43 to 90.56 rebuild a different layout without them.
They end at 90.56 instead (`until`).

**To run a script of this folder again:** they read the working layouts as
"90.56", which was true when they ran. Since the install the working layouts
are 90.57, so point `scenario._layouts` at the 90.56 snapshot first.

## Seen on the way, not followed up

- **Default layout, simulator:** 1,084 of 36,000 walks stopped early. In the
  four I looked at, the right stick was out with a trigger held, and a bumper
  press made `Turning Ramp Up 0` go on and off without time passing. The
  simulator reads a stick as out or not, so this may be the model.
- **Alternative layout, simulator:** with the right stick pushed out in
  `Steering` before a driver, `Turning Ramp Up 1` answers both triggers with
  an empty bind, and the W or S layer does not come. Driver first, then the
  stick, works.
- **The right pad's window in `Steering`:** it answers a bumper's Release and
  lists no Steering layer, so a W or S layer or a Steering Modifier 2 layer
  stays on after its bumper is let go inside the window (section 10). In
  90.56 as well. The author, 2026-10-12: leave it.
- **A stick window and the right pad:** its right pad touch Release removes
  `RTP: Entry Point` and not `RTP: Tap Cover` (section 10). In 90.56 as well.
