# Cleanup audit: first run

**Status:** 2026-10-02. The audit was built and run on both working layouts
(90.10): 190 findings per layout, the same in both variants. The author
decided all of them, and **90.12 fixes them**: the `cleanup_lists` step of the
fix pipeline resolves exactly the audit's findings, and the audit is now the
fourth gate of the build audit. Both layouts are clean. Deck checks are C1 to
C8 in [manual-testing.md](../../manual-testing.md#9012-cleanup-lists).

- Tool: [audit_cleanups.py](../../audit_cleanups.py), on
  [steam_layout/cleanups.py](../../steam_layout/cleanups.py), with
  [40 tests](../../tests/test_cleanups.py)
- Rules: [cleanup boundaries](../2026-10-02-cleanup-boundaries/README.md#the-rules)
- Plan: [the Cleanup audit](../../plans/2026-10-02-cleanup-audit.md)
- Full output: [default.txt](default.txt), [alternative.txt](alternative.txt)

```bash
python3 audit_cleanups.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_cleanups.py <layout> --layer "L1: Modifier 0"
python3 audit_cleanups.py <layout> --check "never there"
```

## Definitions

Stacks are drawn top first. Steam uses the topmost layer that binds an input.

| Term | Definition |
|---|---|
| **Keeper** | What keeps a layer alive. For most layers it's the button whose Release ends the layer. `L1: Modifier 0`, `L1: Tap Cover` and `L1: Temp Cursor Gyro` are all kept by L1. Other keepers: a thumb on a stick (the `LST`/`RST` layers), a timer (the Double Tap windows) and a mode (`Gyro`, `Steering`, which stay until you turn them off) |
| **Guard** | The buttons on a cleanup's chord. While any of them is held, the cleanup doesn't fire. So when it does fire, all it knows is "these buttons are up" |
| **Cleanup function** | A backup removal on another input (A, the D-pad, a stick) that fires only when its guard buttons are up, which means a release was missed |
| **Host** | The layer the cleanup function is on |

```
  L1: Tap Cover        kept by L1
  L1: Modifier 0       kept by L1    <- host. On A: chord with L1 = A's normal use,
  Base                                         no L1 held = the cleanup
```

The six checks, each with what it catches:

| Check | Definition | Example from the first run |
|---|---|---|
| **Outside the guard** | The cleanup removes a layer that its guard buttons don't keep alive: another button's layer, a stateful layer, a stick-touch helper or a window. It's reaching into something it knows nothing about | `Steering \| R1: W Key`'s cleanup, guarded by R1, removes `Steering \| R1!L1: Modifier 2`, which L1 keeps |
| **Left below** | A layer under the host is kept by the same button, and the cleanup doesn't remove it. It's stale too, so it needs a second step | The cursor's edge cleanup removes the cursor and leaves `L1: Modifier 0` under it |
| **Left above** | A layer on top of the host is kept by the same button, doesn't bind the cleanup's input, and isn't in the list. The host's cleanup is the only thing that can fire under it, so it would stay stuck | None today. It would happen if `L1: Modifier 0`'s list dropped `L1: Tap Cover` |
| **Hidden cleanup** | A layer on top binds an input where the layer below has a cleanup, and puts no cleanup there itself. Steam uses the top layer, so the cleanup below can never fire on that input | `L1!R1: Modifier 2` binds both stick touches with only a Release, hiding `L1: Modifier 0`'s stick-touch cleanup |
| **Guard mismatch** | One layer's cleanups don't agree on which buttons protect it | `Steering \| R1!L1: Modifier 2`: on A, either bumper held protects it; on a stick touch, only R1 does |
| **Never there** | A removal list names a layer that can never be on the stack at the same time. The removal does nothing | `L1: Modifier 0`'s Release removes `Gyro \| L1: Modifier 0`, which only exists while Gyro is on, when `L1: Modifier 0` can't |

"Left below" and "Left above" are the two halves of the author's rule: take
care of yourself and what's below, and what's above if it's yours. "Outside
the guard" is the other side of it: nothing that isn't yours.

## Result

Per layout: 257 cleanup functions on 34 of 68 layers. `LTP: Arrow Keys` and
`RTP: Mouse Buttons` are left out, because only `hold_layer` adds them
(author, 2026-10-02).

| Check | Findings | Bindings | Decided? |
|---|---|---|---|
| Outside the guard | 18 | 132 | Yes |
| Left below | 4 | 8 | Yes |
| Left above | 0 | 0 | |
| Hidden cleanup | 16 | 32 | Yes |
| Guard mismatch | 2 | 4 | Yes |
| Never there | 150 | 1,040 | Yes: drop all |

A finding is one layer and one removed layer. "Bindings" is how many
bindings carry it, which for "Never there" is the number of removals that
would go.

## The fix list

Names are the default layout's; the alternative has L2 and R2.

### 1. Left below: the cursor's edge cleanups (4 findings, 8 bindings)

`L1: Temp Cursor Gyro` and `R1: Temp Cursor Gyro` each have two edge cleanups
that remove only the cursor. **Fix (decided):** they take the modifier's
list, so the modifier below goes in the same step.

### 2. Hidden cleanup: Modifier 2's stick touches (16 findings, 32 bindings)

All four Modifier 2 layers bind both stick touches with a Release only. That
hides the touch cleanup of the single modifiers and of `L1: Tap Cover` and
`R1: Tap Cover` underneath. **Fix (decided):** add the guarded cleanup to
both touch inputs of the four layers.

### 3. Guard mismatch: Steering's Modifier 2 (2 findings, 4 bindings)

`Steering | R1!L1: Modifier 2` and `Steering | L1!R1: Modifier 2` guard their
two stick-touch cleanups with one bumper and their other twelve with either.
**Fix (decided):** either bumper on the touches too.

### 4. Outside the guard (18 findings, 132 bindings)

All in Steering layers.

| What | Findings | Fix |
|---|---|---|
| Six layers list the two Steering Double Tap windows | 12 | Decided: a cleanup doesn't list a window |
| The two Steering Modifier 2 layers' touch cleanups remove the other side's Tap Cover | 2 | Goes away with fix 3: once either bumper guards them, the cover is inside the guard |
| `Steering \| R1: W Key` (guard RB) removes `Steering \| R1!L1: Modifier 2` and `L1: Tap Cover`, which LB keeps. `Steering \| L1: S Key` is the mirror | 4 | Drop (author, 2026-10-02) |

**The four new ones.** These were not in the list predicted before the run.
A driver's cleanup is guarded by its own bumper and removes two layers the
second bumper keeps. Both of those layers bind the stick touches themselves,
so the driver's cleanup can't fire while either is on top. Dropping them from
the two drivers' lists follows from the author's "either bumper protects
Steering's Modifier 2". The author agreed the same day.

### 5. Never there (150 findings, 1,040 removals)

| Group | Findings | Removals | Fix |
|---|---|---|---|
| The Gyro or normal twin | 36 | 272 | Decided: drop |
| In a Steering layer's list | 68 | 490 | Decided: drop, through the builder |
| Cursor in a cover's or Modifier 2's list, and the cover in the cursor's | 24 | 138 | Drop. The cursor is cancelled before a cover or Modifier 2 goes on; only a timing race puts both on, and the author chose no race rule |
| Fn layers and the stick guards with the menu Tap Cover | 18 | 132 | Drop: a timing race only. Each layer still has its own cleanup (author) |
| The other Modifier 2 order | 4 | 8 | Drop, from Modifier 2's own release only. The combined cover's lists keep both |

A removal that is kept goes into `steam_layout/flow_config.json` under
`cleanups.keep` with its reason, and the audit then passes on it.

## Review before fixing (2026-10-02)

Checked against the bindings before any fix is written:

- **Size.** One layout has 3,538 removal subcommands. The fix drops 1,172
  ("Never there" and "Outside the guard") and adds about 56 (the Modifier 2
  touch cleanups and the cursor's one-step edges), so about a third fewer.
- **Modifier 2's touch cleanup needs one either-bumper chord.** Its other 14
  cleanups use two chords (LB, RB) beside the removal. On a stick touch,
  which already has the Release, that would be four entries, and Steam drops
  the fourth. One chord with an Any mask over both bumpers (as Steering's
  layers already use) keeps it at three.
- **The rocking lists lose only their cursor removals.** The combined cover's
  two releases drop `L1: Temp Cursor Gyro` / `R1: Temp Cursor Gyro`, which
  is never under it. Both Modifier 2 orders and both Gyro kinds stay. No add
  and no order changes anywhere.
- **The cursor's one-step edge list** becomes the cursor plus both of its
  modifiers (normal and Gyro: the cursor can sit on either). The Tap Cover
  isn't added: it is never there with the cursor.
- **Steering's lists come from the builder**, but `install_neptune.py` runs
  the fix pipeline after the build, so a pipeline fix covers them.

## Information, not a failure

No cleanup function removes these, and they have none of their own:
`Menu Left: Escape`, `Menu Right: Tab`, their two Double Tap Covers, and the
two Transition Sets. The first four were accepted on 2026-09-28 (cleanup
audit F2). A Transition Set has nothing under it since 90.10.

## How the stacks are worked out

From the backward chains only (`steam_layout/chains.py`): start at a layer,
ask which bindings add it, back to Base, plus one unrelated layer underneath.
No other stack search is used; a test asserts that the audit's stacks are
exactly the chains' `below` and `above`.

Limits that follow from that:

- Chords are ignored, which can add a stack that can't happen and never drops
  one that can.
- Timing isn't modelled. That is why the Fn and stick-guard group is a
  review, not a deletion.
- A stack left by a missed release is only seen as far as a normal sequence
  builds the same stack.

## What the tool works out, and what it can get wrong

- **Stateful layers are worked out:** a layer that outlives every binding
  that adds it, has no Always On action and no Release of its own. Both
  layouts give `Gyro` and `Steering`, and a test pins that.
- **The keeper is worked out** from the Releases and the guards. A layer
  whose Release is on a stick, such as `Steering | LS Down: Modifier 0`,
  counts as living inside the hold of the layer that adds it. That rule
  resolved all of Steering's left-stick layers, so nothing had to be
  declared.
- Every finding prints the keeper and the guard it used, so a wrong one is
  visible.

## Author answers, 2026-10-02

- **The four new Steering findings: drop.** The drivers' lists lose the
  second bumper's Modifier 2 and Tap Cover. This means fewer removals; the
  rules compute it ("outside the guard").
- **What the algorithm and the rules decide needs no question.** Findings
  that follow from them go straight onto the fix list. Only what the
  algorithm can't see comes back to the author, as a proposed rule.
- **No race rule** (author, the same day, after seeing the proposal):
  "even if that happens, each layer is always going to take care of itself.
  Each layer has a cleanup. And that weird edge case, which is very unlikely,
  let's not balloon the amount of removals just based on it." So the Fn and
  stick-guard group and the whole cursor group are dropped like the rest of
  "never there". The proposal, for the record: a delayed add counts as on the
  stack with whatever the same layer's other presses add; it would have kept
  26 findings (160 removals).
- **The other Modifier 2 order: drop it from Modifier 2's own release.** The
  author confirmed the rocking explanation. Only the quick tap's list loses
  the other order; the combined cover's releases, which the rocking uses,
  keep both. Written up in
  [Rocking Between Modifiers](../../resources/Steam%20Input%20JSON%20Structure.md#rocking-between-modifiers-0-1-and-2)
  and tested in [test_modifier_rocking.py](../../tests/test_modifier_rocking.py).

So every finding of the first run is now decided. The fix list is the five
sections above, with all of "Never there" dropped.

## Applied in 90.12

- **The fix:** [steam_layout/fixes/cleanup_lists.py](../../steam_layout/fixes/cleanup_lists.py),
  in the pipeline before `window_routes`. It runs the audit, then: widens an
  odd guard, adds what a cleanup leaves below or above, drops what is outside
  the guard or never there, and lets a layer that hides a cleanup carry it.
  It does nothing when the audit is already clean, so the working layouts stay
  a fixed point of the pipeline. Tests: `FixTests` and `FixedSnapshotTests` in
  [tests/test_cleanups.py](../../tests/test_cleanups.py).
- **Applied on top of 90.11** (the Steering fallback hold, built in another
  session the same day): the working layouts are exactly the 90.11 snapshot
  plus this fix. Released as 90.12; the 90.11 snapshot is untouched.
- **Result per layout:** 278 changed bindings, about a third fewer removals,
  the Modifier 2 stick-touch cleanups added with one either-bumper chord, no
  add and no add order touched. All four build audits pass.
- **Old tests updated** where they pinned the old lists (the Gyro twin, the
  cursor in the Modifier 2 and combined-cover lists, Fn with the stick guards,
  the other LS modifier). Each now states the rule that changed it.
- **Rocking unchanged:** [tests/test_modifier_rocking.py](../../tests/test_modifier_rocking.py)
  passes on 90.12.
