# Plan: follow up on the held-input rule audit

Date: 2026-09-29. **Status: F1 JSON fix implemented with cursor self-removal;
remaining follow-ups and Deck validation pending.** Source: the
[held-input audit](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)
and the [rule as documented](../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes).

The rule, in short:

1. Adding a layer over a held input doesn't fire that layer's immediate layer
   command on the input.
2. Fire Start Delay and Hold to Repeat still fire.
3. Removing a layer fires the newly exposed binding on a held input.

It is author-reported and consistent with both layouts, but not confirmed on the
current Steam client.

## What "addressed" means

- The alternative layout's missing R2 → Mod 2 repeat (F1) is fixed and checked on the Deck.
- Regression tests protect the settings that exist because of the rule. A future
  "cleanup" can't strip the 5 ms delay or the load-bearing repeats without failing
  a test that explains why.
- A minimal test layout confirms or corrects the three rules on the current client,
  including whether key and mouse outputs follow them (F3.1, F3.2).
- The staggered Gyro toggle (F3.3) is measured, then either accepted or handed to
  a separate design.
- The docs say "confirmed" or "corrected" instead of "author-reported".

| Issue | Now | Action | Phase |
|---|---|---|---|
| F1: alt `R2: Modifier 1` / `Gyro \| R2: Modifier 1` LT → Mod 2 chord had no repeat | Fixed in JSON; Deck pending | Added `hold_repeats: "1"`; cursor regression test covers it | 1 |
| F2: docs contradicted rule 3 | Done in the audit | None | — |
| Rule itself unconfirmed | Author-reported | Minimal test layout | 2 |
| F3.1: do key outputs fire on add? | Unknown | Test; conditional fix | 2 → 3 |
| F3.2: do mouse outputs fire on remove? | Unknown | Test; conditional design | 2 → 3 |
| F3.3: staggered Mod 2 → Gyro toggle | Unknown | Measure; accept or design | 2 → 3 |
| Tribal knowledge only in docs | Docs | Regression tests | 1 |

## Decisions for you before starting

1. **F1 is applied.** The self-removal implementation adds the two missing repeat
   settings and checks them in the cursor tests. The default serves as the control;
   the alternative VDF already on the Deck can still serve as the before case.
2. **How to build the rule-test layout?**
   - **Recommended:** I generate `rule-test.json` from the Neptune file's
     header and structure, and you convert it to VDF with `pfwobcke.vscode-vdf`.
     It lives in the repo and can be re-run after Steam client updates.
   - **Alternative:** you build it in the Steam configurator from
     `neptune/empty_0.vdf`. That is about a dozen bindings, but nothing gets recorded.
3. **Version:** keep 90.2, as the cursor work did, unless you want a bump for F1.

## Phase 1: static changes (no Deck needed)

### 1.1 Fix F1 in the alternative layout

Implemented as part of [cursor self-removal](2026-09-29-cursor-self-removal.md).
The F1 portion changes exactly two settings; other changes in that implementation
belong to the cursor redesign. Deck validation remains pending.

| Layer | Group | Input / activator | Change |
|---|---|---|---|
| `R2: Modifier 1` | 258 | `left_trigger` `edge` chord (`chord_button: "8"`) | add `hold_repeats: "1"` |
| `Gyro \| R2: Modifier 1` | 12940 | same | add `hold_repeats: "1"` |

- Match the L2 side (groups 257, 12923) and all four default pairs: no
  `repeat_rate`, keep `interruptable: "0"`, and leave the binding array and its
  order untouched.
- Procedure: `steam-layout-prep` → `to-titles --output` to scratch. Edit by
  (layer title, source, input, activator), not by line. Then `to-ids`, the
  pre-flight check, and `audit_command_budget.py` (the entry count doesn't change).
  The numeric diff must be exactly two added settings lines.
- **Inheritance review, already traced:**
  - The repeat stops once Mod 2 is on top, because both `R2!L2: Modifier 2`
    variants and `L2&R2: Tap Cover` define LT `edge`.
  - `R2: Tap Cover` inherits LT. The self-removal redesign gives `R2: Temp Cursor
    Gyro` a repeating LT self-exit, exposing the parent's repeating Mod 2 chord.
    Default's R1 overlays use the corresponding bumper path.
  - All seven Double Tap windows override LT `edge`, so the repeat can't run
    inside an Always On window.
  - In a stale stack (RT not held), the chord's RT selector is false, so
    guarded recovery still wins.
  - Repeated fires re-add layers that are already active, which has no effect.
- The default layout is unchanged.

### 1.2 Regression tests: `tests/test_neptune_held_inputs.py`

Reuse `load_layouts` from `test_neptune_recovery`, as the cursor and gyro tests
do. Assert on saved configuration only, in both layouts:

1. **Delayed applies keep their delay.** Every delayed layer add keeps
   `delay_start > 0`, including `Gyro Off Ramp Up` → `Turning Ramp Up 0`.
   The failure message links to the doc section and explains that the delay is
   what lets it fire on the held stick.
2. **Threshold exits repeat.** Every inverted Soft Press that runs a layer
   command has Hold to Repeat. There are five per layout.
3. **Load-bearing repeating adds stay repeating:**
   - Gyro's two modifier entries.
   - All four Mod 0/1 → Mod 2 entry chords per layout.
   - The four Fn stick-click → Transition Set chords.

   The alternative's R2 pair is fixed and covered by the cursor regression test.
   The broader held-input regression module remains follow-up work.
4. **`Gyro Off Ramp Up`'s firing-control removal repeats.**
5. **The held-input guard.** For every press-type activator that adds layer T
   on input I, T's binding on I must not contain an immediate layer command
   (no delay, no repeat, not release). The only allowed exceptions are the two
   Menu Entry → Fn chords, and they must add their Enter/Backspace overlay in
   the same array. A new binding with this shape fails and points to the rule.

The module docstring says these are configuration contracts, not runtime proof,
matching the other test files.

### 1.3 Record and export

- Add a `todos.md` entry linking this plan, with F1 marked implemented and Deck
  validation pending.
- Mark F1 in the audit as "fixed in JSON; Deck pending".
- Run `steam-layout-apply` for both layouts. The pending cursor-gyro JSON changes
  need an export too. You convert both to VDF.

## Phase 2: Deck session (you)

### 2.1 Minimal rule-test layout

**Probe:** in each layer, D-pad Up types a different digit. With the test's
buttons still held, tap D-pad Up in a text field; the digit tells you which
layer is on top. No test layer binds D-pad Up for anything else, and this
doesn't depend on layer notifications.

**Reset:** Start removes every test layer. No test layer binds Start, so it
always reaches Base.

| Layer | Probe digit | Added by (in Base) | Test binding in the layer |
|---|---|---|---|
| Base | 0 | — | B: nothing. RB: Regular Press → add Target. R4: Regular Press → key Q |
| X1 | 1 | A | B: Regular Press → add Target |
| X2 | 2 | X | B: Regular Press → add Target, Fire Start Delay 5 ms |
| X3 | 3 | Y | B: Regular Press → add Target, Hold to Repeat |
| K | 4 | LB | B: Regular Press → key K |
| R | 5 | L4 | RB: Regular Press → remove R. R4: Regular Press → remove R |
| Target | 9 | — | none |

None of the Base bindings that the tests rely on repeat, so each test isolates one rule.

| Test | Steps | Rule predicts |
|---|---|---|
| T1 add, immediate | Hold B, press A, keep holding B, probe | **1** (X1's B didn't fire) |
| T2 add, delayed | Hold B, press X, wait, probe | **9** |
| T3 add, repeat | Hold B, press Y, wait about 1 s, probe | **9** |
| T4 remove, layer command | Press L4, then press and hold RB, probe | **9** (Base RB fired once R was removed) |
| T5 add, key output | Hold B, press LB, keep holding B | Record whether K is typed (F3.1) |
| T6 remove, key output | Press L4, then press and hold R4 | Record whether Q is typed (F3.2) |

Run each test five times, reset between runs, and note the Steam client version.
A single miss in T2–T4 matters as much as a pattern. It would mean the rule is
timing-dependent.

### 2.2 Checks in the real layouts (fresh load, both layouts)

These are already listed in
[manual testing](../manual-testing.md#held-inputs-across-layer-changes):

- One held stick click from Menu Entry reaches a Transition Set.
- The staggered Gyro toggle: which modifier variants appear, and whether
  releasing the held bumper scrolls.
- F1 scenario (alternative): with the fix, Mod 2 enters without re-pulling.
- The existing first-click check during `Gyro Off Ramp Up`.
- The Enter/Backspace and double-tap-hold Escape/Tab checks.

## Phase 3: act on the results

| Result | Meaning | Action |
|---|---|---|
| T1–T4 as predicted | Rule confirmed for layer commands | Phase 4 only |
| T1 shows 9 | Adds do fire held layer commands | Correct the docs. The repeats are harmless and stay. Re-read the audit's "why it repeats" column as redundancy |
| T2 shows 2 | Delays don't fire on a held input | The ramp handoff must work for another reason. Investigate before changing anything |
| T3 shows 3 | Repeats don't fire on a held input | The Gyro, Mod 2, and Fn-click repeats aren't doing what the audit says. Re-check each against the layout checks in 2.2 |
| T4 shows 0 | Removal doesn't pass through | Base's repeating entries become load-bearing; keep them. Every layer-command exposure in the audit is Base-backed, so no layout change. Correct the docs |
| T5: no K | Key outputs follow rule 1 | Small follow-up: add `delay_start: "5"` to the key Regular Press in `Menu Left: Backspace`, `Menu Right: Enter`, `Menu Left: Escape`, `Menu Right: Tab`. This is the same trick as the ramp handoff and adds no command entries. Test and Deck-check it separately |
| T6: no Q, or the first click is lost | Outputs don't pass through removal | Needs its own design plan. Emitting the click from `Gyro Off Ramp Up`'s repeating removal would turbo-fire, and a separate click entry on a layer that removes itself risks a stuck button. Don't patch in this pass |
| Staggered toggle leaves both variants, or scrolls | Expected side effect of rules 1 and 3 | Decide whether it bothers you in play. The scroll is the re-entered modifier's normal short-tap behavior; holding past 300 ms applies the cursor overlay and avoids it. If it's unwanted, write a separate design plan. Covers added by the release array would sit *below* the re-entered modifier, so the obvious patch doesn't work |

## Phase 4: close out

- **Structure doc:** replace "Author-reported" with the client version and
  date, state the confirmed output scope, and remove "not yet confirmed" wording.
- **Audit:** add a Deck results section with the T1–T6 table.
- **Manual testing:** tick the checks that passed.
- **`todos.md`:** close the entry.
- **Memory:** update so it no longer says "not Deck-confirmed".

## Out of scope

- Removing Base's repeating entries. They're redundant only if T4 passes, and cheap to keep.
- Adding repeats to delayed applies, or extending delayed-apply resets. That is
  the separate todo from the [delayed-apply audit](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md).
- Reordering existing binding arrays.
- Any F3 layout change before its Deck result exists.
