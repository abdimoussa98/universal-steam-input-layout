# Plan: take out the removes that never take a layer off

**Status, 2026-10-12:** built as **90.58** on the author's word ("start
building";
[release record](../findings/2026-10-12-removes-that-never-take-a-layer-off/README.md)).
Both questions were answered first ([Answers](#answers)): the clears are
trimmed, and so are the bumpers' own cleanup functions. It follows the
[audit of every remove](../findings/2026-10-12-remove-list-audit/README.md)
on 90.57. Where the build differs from the text below, the record says so:
the walks of step 3 were run again on fresh seeds, and the Deck check on a
missed bumper takes two presses of A at most, not one.

The author, 2026-10-12: "I want you to audit whether all these removes are
necessary". Then, before this plan: "I want to make sure that this is
reductive and not additive. So we're not going to be adding any layer
removals right now. We're just reducing them."

## The constraint: nothing is added

Every bind in 90.58 has its 90.57 commands with some `remove_layer` commands
taken out. Nothing else in the layout changes but the title.

- **No bind gains a remove.** No add changes, no command changes place, no
  setting, bind or layer is added or dropped.
- **Checked on the trial layouts**
  ([`reductive.txt`](../findings/2026-10-12-remove-list-audit/reductive.txt)):
  against 90.57 they differ in 142 binds (154 in the alternative), by 1,162
  removes taken out (1,174); commands added 0, order changed 0, any other
  difference 0.
- **The fix pipeline adds nothing either.** Run on the trial, it takes 16
  removes out and adds none. Those 16 are needed, so the build stops it
  ([Rules and tools](#rules-and-tools)).
- **The builder refuses anything else:** it stops if a bind gains a command,
  loses anything but a remove, or changes order. A test states the same of
  the installed layout against the 90.57 snapshot.

Two places where a layer is left on today would need a remove **added**: the
right pad's `RTP: Double Tap` answering a bumper's Release in `Steering`,
and a stick window's right pad touch Release leaving `RTP: Tap Cover`. Both
were left alone on the author's word ("leave it") and are not in this plan.

## Terms

- **Bind:** one activator entry on one input of one layer. Its **list** is
  the layers its removes name. Its **host** is the layer it sits in.
- **Never there:** the chains say the named layer and the host are never on
  the stack together, and the bind fired 30 times or more in the walks
  without meeting it.
- **Answers first:** the named layer binds the bind's own input and only
  ever sits above the host. While it is on, it answers that input and the
  bind underneath does not run (R132 as tightened in 90.57).
- **Candidate:** a remove with one of those two verdicts that no rule fixes.
  A remove seen on the stack even once is not a candidate.
- **Modifier family:** the 19 layers a bumper owns outside `Steering` (the
  triggers' soft pull in the alternative): the two modifiers, the two
  Modifier 2 layers, their four `Gyro` twins, the covers, the Double Tap
  windows, the two scroll layers and the two `Temp Cursor Gyro` layers.

## What goes

Every candidate: the set the trial layouts were built and tested without.

| Group | Default | Alternative |
|---|---|---|
| 1. The fourteen clears of 89 removes each | 950 | 950 |
| 2. Answers first, outside the modifier family | 124 | 128 |
| 3. Answers first, hosted in the modifier family | 88 | 96 |
| **Taken out** | **1,162** | **1,174** |
| **Removes in the layout** | **4,013 to 2,851** | **4,083 to 2,909** |

1. **The clears.** The binds that enter a transition, `Gamepad` or `Menu
   Keys`. Each names every layer but one. After the trim they name 5 to 27:
   every layer that was on the stack at least once when the clear fired,
   and every one the audit could not rule out.
2. **Outside the family.** 48 in the W and S layers' cleanup functions (the
   six Steering stick layers, each with a cleanup of its own on the same
   inputs); 26 in `Steering`'s exit on up and down (its thirteen family
   layers all bind up and down); the other 50 (54) in the Steering stick
   layers, the Fn layers, the stick guards, the Entry Guard, the ramp layers
   and the right pad's layers, where a cover or second-press layer binds the
   same input.
3. **In the family.** All in cleanup functions, which run only after a
   missed release: a modifier naming its `Temp Cursor Gyro` on 17 inputs
   (the cursor binds each as a cancel), and a modifier, Modifier 2 or scroll
   layer naming its cover on the two stick touches (the cover binds both).
   No Release, reset, hold or entry bind of the family is a candidate.

## What stays

- **2,006 needed:** on the stack at least once when their bind fired.
- **768 not shown either way.** Possible by the chains, not met by the walks.
- **Every remove of `L1: Tap Cover` on a button** (and of R1's): needed
  where its bind fired, not shown where it never did.
- **Every remove in a Modifier 2 Release** outside `Steering`: of 76, 65 are
  needed, 3 not shown and 8 are the layer's own hold target.
- **77 fixed by a rule** whatever the stack holds: the timer resets (R120),
  a layer's own hold target in its Release, the stick touch trio (R123).
- **The 16 at the four Stateful Entry Points** (`LST: Tap Cover`, `LST:
  Temporary Gyro` and the right stick's two). The chains say they can't be
  there; the walks met them.

## Rules and tools

- **R163** reads "entering a transition clears the whole stack first". It
  becomes "clears every layer that can be on the stack there". The author's
  words when it was made: "clean everything below you that is possible".
- **R163's check becomes a walk test.** In seeded walks, each time one of
  the fourteen clears fires, nothing is left on the stack but what the
  clear is meant to keep (`Gyro`, or `Menu Keys`). Today the tests state
  the whole list; a short list needs a test that would catch a layer added
  later and not named.
- **One register entry (R132)** keeps the 16. Cut short, a clear is no
  longer exempt from the Cleanup audit's "never there" check, and the chains
  follow no delayed add.
- **A test keeps groups 2 and 3 out.** No cleanup function names a layer
  above its host that the cleanup rules do not ask for (R128, R129). Eight
  such removes stay and the test names them: the right pad's two click
  layers, which come on by `hold_layer`, a path neither the chains nor the
  simulator follow.
- **Not an audit check yet.** The same check inside the Cleanup audit would
  also run in the fix pipeline, and so change what the builders of earlier
  releases rebuild. It stays the to-do it is, now with the test as its
  statement.

## Build steps

1. A builder in a new findings folder, reading the 90.57 snapshot and the
   audit's rows. It asserts the constraint above.
2. The fix pipeline. It must change nothing.
3. The same 48,000 walks per layout on 90.57 and the candidate, half with
   one release in ten missed: every walk's whole log the same (every key,
   wheel step, haptic and beep, every layer on or off, with its time), and
   the same count of walks with a layer left over.
4. Rocking: the nine tests of `tests/test_modifier_rocking.py`, and every
   bumper sequence of five steps from Base and from `Gyro` (236,196 per
   layout), and of four steps with missed releases (25,600), log for log
   ([`rocking.py`](../findings/2026-10-12-remove-list-audit/rocking.py)).
5. Build audit, full suite. Tests that state a whole list are reworded for
   R163; the ones that state 90.57's lists are frozen on its snapshot.
   Scenario 90.42 S3 is one: it seeds a stack no press reaches and expects
   `Steering`'s exit to clear it.
6. VDFs, snapshot, record with the count before and after.

Steps 3 and 4 have been run once already, on the trial layouts: every log
the same.

## What it costs

- **A layer Steam leaves on with no press sequence behind it** is no longer
  wiped by entering a mode. It stays until its own cleanup runs (a thumb on
  a stick).
- **A short clear can go stale** when a layer is added later; a whole list
  could not. The walk test is the guard.
- **Thin evidence for 123 of the 1,162** (132 of the 1,174): their binds
  fired under 30 times in the walks. All are "answers first" in cleanup
  functions, 63 (68) of them in the modifier family. They rest on the layer
  above binding the same input, read from the layout, and on the chains'
  order.
- **All of it is the simulator's.** It runs one command list as one step and
  cannot produce an order of same-instant events it does not model.

## Answers

The author, 2026-10-12: "1. trim 2. are you asking me if i want to trim, if
so yes i want to trim".

1. **The clears: trim.** Hold Start and click the left stick to enter
   `Cursor Gyro`: that Release named 89 layers, and in 17,906 firings 26
   were ever on the stack. It names 27. The 950 go.
2. **The modifier family: trim.** Hold L1 past 200 ms, open the Steam menu,
   let go there: the modifier and `L1: Temp Cursor Gyro` are left on. Press
   A: the cursor layer binds A as a cancel, answers it, and removes itself.
   The modifier's own cleanup on A is exposed after that and removes the
   modifier, on the same press or on the next (A9). It also named the cursor
   layer, which is always gone by the time it can run. That remove goes,
   with the rest of the 88 (96). I had offered to leave them for a first
   build.

## On the Deck afterwards

The logs are the same, so there is nothing new to feel. Four checks:

1. Enter and leave `Cursor Gyro`, `Steering`, `Gamepad` and `Menu Keys`
   from each side, with a thumb on a pad and with a bumper tapped just
   before: nothing is left on.
2. Rock L1 and R1 in Base and in `Gyro`: no scroll.
3. Hold a bumper for a moment, open the Steam menu, let go inside it and
   close it, then press A, twice at most: the layout is back to normal. The
   first press ends the cursor layer; the modifier goes on that press or on
   the next, depending on A9.
4. The same with both bumpers held, then a thumb on the right stick: the
   layout is back to normal.

On the simulator both end on Base alone, on 90.57 and on 90.58.
