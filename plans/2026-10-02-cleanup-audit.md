# Plan: the Cleanup audit

**Status:** built and shipped, 2026-10-02. Steps 1 to 3 (the audit, tests
first) and the first run are recorded in
[findings/2026-10-02-cleanup-audit](../findings/2026-10-02-cleanup-audit/README.md).
Step 4 became one fix-pipeline step, `steam_layout/fixes/cleanup_lists.py`,
which resolves exactly the audit's findings; 90.12 is the release. Step 5 is
done: the audit is the fourth gate of `audit_build.py`. One change from the
plan, by the author: layers that only `hold_layer` adds are left out of the
audit instead of counting `hold_layer` as an add. Deck checks are C1 to C8 in
[manual-testing.md](../manual-testing.md#9012-cleanup-lists).

It builds on the
[cleanup boundaries findings](../findings/2026-10-02-cleanup-boundaries/README.md)
and the author's answers of the same day. It replaces steps 1 to 3 of
the [cleanup generator plan](2026-09-30-cleanup-generator.md), which worked
out scopes from hand-listed families; this one works them out from keepers.

## Goal

One read-only script, `audit_cleanups.py`, that reads a layout and lists
every place a cleanup function or a release breaks the
[six rules](../findings/2026-10-02-cleanup-boundaries/README.md#the-rules).
Its output is the list of what to fix in the layouts. Once the layouts are
clean it joins `audit_build.py` as the fourth audit.

## Is there enough to build it?

Yes. Every check below rests on a rule the author has stated or answered.
Three things are not known yet, and all three come out of the first run
rather than blocking it:

1. Which "never there" removals to keep as a safety net. The run lists them;
   outside Steering they fall into four groups
   ([below](#what-the-first-run-is-expected-to-find)).
2. Whether the keeper of Steering's left-stick layers can be worked out, or
   has to be declared.
3. The author's read of the revised rules. The checks follow the answers
   already given, so a correction changes a check, not the tool.

## The checks

| Check | Rule | Fails when | Applies to |
|---|---|---|---|
| **Outside the guard** | 1, 5 | A list removes a layer whose keeper is not inside the guard: another button's layer, a stateful layer, a stick-touch helper or a window | Cleanup functions |
| **Left below** | 2 | A layer under the host has its keeper inside the guard and isn't removed | Cleanup functions |
| **Left above** | 3 | A layer on top of the host has its keeper inside the guard, leaves the cleanup's input alone, and isn't removed | Cleanup functions |
| **Hidden cleanup** | 4 | A layer of the same interaction binds an input that has a cleanup below, and puts neither a cleanup that also removes the layer below nor an accepted shape there | Every layer above a cleanup |
| **Never there** | 6 | A list removes a layer that can never be on the stack with the host | Cleanup functions, ordinary releases, the Modifier 2 quick tap |
| **Guard mismatch** | 1 | A layer's cleanups don't all have the same guard buttons, or the guard leaves out the host's own keeper | Cleanup functions |

"Left below" has no exceptions since the author's one-step answer.

Accepted shapes for **Hidden cleanup**: the layer's own keeper button, an
Always On window, and a cancellation (no guard, removes only itself,
repeating).

Printed as information, never a failure: layers that no cleanup function
removes and that have none of their own (`Menu Left: Escape`, the Transition
Sets), for review against
[Definition of Done §7](../resources/Layer%20Definition%20of%20Done.md#7-cleanup).

## What the tool has to work out

| Thing | How | Source today |
|---|---|---|
| Cleanup function | The Flow model's `recovery` role | `steam_layout/flow_model.py` |
| Guard | The buttons of the chords on the same input | `measure.py` in the findings |
| Keeper | Mode, timer, or the buttons whose Release removes the layer, checked against its own guards | `measure.py` |
| Can be below, can be above | The backward chains | `steam_layout/chains.py` |
| Leaves the input alone | The Flow model's `resolve` on the two-layer stack | `flow_model.py` |

Four additions the measurements showed are needed:

- **Stateful layers are worked out, not listed.** A layer is stateful if it
  outlives the binding that added it, has no Always On action and has no
  Release that removes it. A test pins the answer to `Gyro` and `Steering`.
- **A layer that lives inside another layer's hold takes that layer's
  keeper.** If a layer's own Release is on a stick, not a button, it counts
  as inside the guard when a layer that adds it, and can be on the stack with
  the host, is inside the guard. Steering's left-stick layers are the test
  case. If this doesn't resolve them, their keeper is declared in
  `flow_config.json`, with a reason.
- **Layers that only `hold_layer` adds are left out** (author, 2026-10-02,
  who doesn't intend to keep `hold_layer`): `LTP: Arrow Keys` and
  `RTP: Mouse Buttons`. They aren't audited and aren't counted when another
  list removes them. The plan first proposed counting `hold_layer` as an add.
- **A deliberate clear is recognized by shape:** a binding that removes every
  layer that isn't stateful. It is exempt from "Never there". The
  stick-touch release's fixed three layers are exempt too.

## Decisions file

A "Never there" removal the author wants to keep is recorded in
`steam_layout/flow_config.json`, under a new `cleanups` key, with a reason,
the way the cover findings are. An undecided one fails. A decision that no
longer matches anything is reported as stale.

## Steps

Tests first, as with the chains.

1. **Module.** `steam_layout/cleanups.py`: guard, keeper, the four additions
   above, and one function per check. The logic moves out of
   `findings/2026-10-02-cleanup-boundaries/measure.py`, which stays as the
   frozen evidence.
   - Tests on small hand-made layouts, one per check, each with a passing
     and a failing case.
   - Tests on the working layouts that pin the keeper of about ten named
     layers and the two stateful layers.
2. **Script.** `audit_cleanups.py <layout>`: findings grouped by check and by
   layer, each with the binding, its guard, and the reason. `--json` for the
   same data. Exit 0 when clean, 1 on a finding, 2 on bad input.
   `--layer TITLE` limits it to one layer.
3. **First run and review.** Run it on both layouts and save the output in
   `findings/<date>-cleanup-audit/`. The author goes through the "Never
   there" groups; kept ones go into the decisions file.
4. **Fix list.** From the reviewed output, write the changes the layouts
   need as a separate plan. No layout is edited in this plan.
5. **Join the build audit.** After the layouts are fixed and the audit is
   clean on both: add it to `audit_build.py`, to
   [Definition of Done §7 and §10](../resources/Layer%20Definition%20of%20Done.md#10-ship-it)
   and to the layout-apply skill, and close the question list in
   [Cleanup Functions](../resources/Cleanup%20Functions.md#questions-for-the-author).

## What the first run is expected to find

From the measurements, per layout (the two variants match):

| Check | Expected | Decision already made |
|---|---|---|
| Left below | The cursor layers' edge cleanups (4 bindings), `RTP: Mouse Buttons`' touch cleanups (2) | One step |
| Hidden cleanup | Both stick touches of the four Modifier 2 layers (8 inputs) | Add the cleanup |
| Outside the guard | Six Steering layers list the two Steering windows | No windows in a cleanup list |
| Guard mismatch | The two Steering Modifier 2 layers: stick touches guarded by one bumper, buttons by either (4 bindings) | Either bumper |
| Never there, Gyro and normal twins | 20 host and layer pairs, 272 removals | Drop |
| Never there, Steering lists | 78 pairs, 614 removals | Drop, through the builder |
| Never there, the rest | 31 pairs, 281 removals, in four groups | To review, below |

The four groups to review:

| Group | Pairs | What it is |
|---|---|---|
| Cursor and Tap Cover naming each other; cursors in the Modifier 2 lists | 14 | The cursor is cancelled before a cover or Modifier 2 goes on |
| The other Modifier 2 order | 4 | `L1!R1` and `R1!L1` name each other in their Release. The cleanup audit of 2026-09-28 left open whether rocking can leave both |
| Fn layers and the stick guards with the menu Tap Cover | 12 | Timing race: a guard normally cancels Fn's 200 ms delay. 90.10 added these on purpose |
| `RTP: Circular Scroll` naming `RTP: Mouse Buttons` | 1 | Goes away once `hold_layer` counts as an add |

## Not in this plan

- Editing a layout or a builder. That is the fix plan of step 4.
- Which inputs must carry a cleanup function (open question 3 in Cleanup
  Functions). The audit only checks an input that hides one.
- Stacks left by a missed release that the chains can't reach, and timing.
  The Deck checks cover those.
- Rewriting lists automatically. The generator plan's writer stays a later
  option.

## Risks

- **A wrong keeper makes wrong findings.** The keeper is computed. The tests
  in step 1 pin it for named layers, and every finding prints the keeper it
  used, so a wrong one is visible.
- **"Never there" is only as good as the chains.** They ignore chords, which
  can only add stacks, and they don't model timing. That is why an undecided
  removal fails the audit but is deleted only after review.
- **Misreading a rule.** The Flow audit once failed on 296 "conflicts" that
  broke no rule of the author's. This audit joins the build audit only after
  the first run has been reviewed (step 5).
