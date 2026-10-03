# Plan: follow up on the held-input rule audit

Date: 2026-09-29. **Status: Phase 1 implemented.** The F1 JSON fix came with the
cursor self-removal change. The held-input regression tests were added on
2026-09-29. Real-layout Deck checks (Phase 2) and the result-driven work
(Phase 3) are pending. Rule 3 is deliberately left unverified for now. Source:
the [held-input audit](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)
and the [rule as documented](../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes).

The rule, in short:

1. Adding a layer over a held input doesn't fire that layer's immediate layer
   command on the input.
2. Fire Start Delay and Hold to Repeat still fire.
3. **Unverified:** removing a layer fires the newly exposed binding on a held input.

Rules 1 and 2 come from the author's runtime experience and are treated as
established. Rule 3 hasn't been isolated. In these layouts every layer command
it would fire also repeats, so the layouts don't depend on it; the repeats are
the guarantee. Settling it is optional and not scheduled.

## Completion criteria (runtime checks still pending)

- The alternative layout's missing R2 → Mod 2 repeat (F1) is fixed in JSON and
  covered by static regression tests. Its Deck check is still pending.
- Regression tests protect the settings that exist because of rules 1–2, and the
  repeats that cover for rule 3. A future "cleanup" can't strip them without
  failing a test that explains why.
- The real layouts must still confirm the output questions: keys on add (F3.1),
  and mouse and key outputs on remove (F3.2).
- The staggered Gyro toggle (F3.3) must still be measured, then either accepted
  or handed to a separate design.
- The docs state rules 1–2 as established, and state rule 3 as unverified with
  the repeats as its guarantee.

| Issue | Now | Action | Phase |
|---|---|---|---|
| F1: alt `R2: Modifier 1` / `Gyro \| R2: Modifier 1` LT → Mod 2 chord had no repeat | Fixed in JSON; Deck pending | Added `hold_repeats: "1"`; cursor regression test covers it | 1 |
| F2: docs treated rule 3 inconsistently | Done | None | — |
| Rule 3 unverified | Called out in docs; covering repeats protected by tests | Optional T4 in `rule-test.vdf`, not scheduled | — |
| F3.1: do key outputs fire on add? | Unknown | Real-layout check; conditional fix | 2 → 3 |
| F3.2: do mouse/key outputs fire on remove? | Unknown | Real-layout check; conditional design | 2 → 3 |
| F3.3: staggered Mod 2 → Gyro toggle | Unknown | Measure; accept or design | 2 → 3 |
| Tribal knowledge only in docs | Protected by [`test_neptune_held_inputs.py`](../tests/test_neptune_held_inputs.py) | None | 1 |

## Decisions

1. **F1 is applied.** The self-removal implementation adds the two missing repeat
   settings and checks them in the cursor tests. The default serves as the control;
   the alternative VDF already on the Deck can still serve as the before case.
2. **Rule 3 stays unverified for now.** Rather than testing it, the docs call it
   out and the regression tests protect the repeats that make it irrelevant.
   The generated [`rule-test.vdf`](../findings/2026-09-29-held-input-layer-transitions/rule-test.vdf)
   remains available. Its T4 settles rule 3 in a few minutes if it's ever needed,
   for example before removing a Base repeat.
3. **Version:** 90.2 is unchanged, as with the cursor work.

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

**Implemented.** Seven tests; the full suite passes (33 tests). They reuse
`load_layouts` from `test_neptune_recovery` and `owners` from `test_neptune_cursor`.
They check saved configuration in both layouts, not runtime behavior:

1. **Ramp handoffs keep their start delays.** `Gyro Off Ramp Up` → `Turning Ramp Up 0`
   keeps 5 ms, and `Turning Ramp Up 0` → `Turning Ramp Up 1` keeps 250 ms. Both
   stay non-inverted Soft Presses at 29031. The failure message explains that
   the delay is what lets the apply fire on the held stick.
2. **Threshold exits repeat.** Every inverted activator that runs a layer command
   has Hold to Repeat. The test also requires that the five known exits are
   found, so it can't pass vacuously.
3. **Layers added over a held input repeat their next add:**
   - Gyro's two modifier entries.
   - The four Fn stick-click → Transition Set chords.

   The four Mod 0/1 → Mod 2 entries per layout, including the F1 pair, are
   already covered by `test_neptune_cursor`.
4. **Base's entries repeat.** This covers the menu buttons, both modifiers,
   LS/RS/RTP touch, and both RS-edge ramp entries. Base only comes back through
   removals, and while rule 3 is unverified these repeats are what re-enter a
   held interaction.
5. **`Gyro Off Ramp Up`'s firing-control removal** stays a single repeating,
   uninterruptible removal.
6. **The held-input guard.** For every press that adds or holds layers on input I:
   - It takes the layer that ends up on top among those added that define I.
     Arrays run bottom to top, so that's the first such target in stored order.
   - That layer's binding on I must not contain an immediate layer command.
   - A layer re-adding itself is ignored, since that has no effect.
   - Checking the top layer instead of every target makes an allowlist
     unnecessary. Menu Entry → Fn passes because `Menu Right: Enter` /
     `Menu Left: Backspace` is added last and owns the button.
7. **The guard catches known regressions.** A self-test breaks a copy of the
   default layout in two ways: it removes the 5 ms delay, and it drops Menu
   Left Entry's explicit Enter add. The guard must flag both.

Review changes from the original proposal:
- The original item 1, "every delayed add keeps `delay_start > 0`", was true by
  definition. The guard now covers the general case, and item 1 pins the two
  ramp handoffs.
- The original allowlist is replaced by the top-layer rule.
- Item 4 was added when rule 3 was marked unverified.

### 1.3 Record and export

- **Done:** `todos.md` entry added, and the audit marks F1 as fixed in JSON with
  Deck confirmation pending.
- **Done:** exported `rule-test.vdf` and refreshed both Neptune VDFs using
  `convert_vdf.mjs` and the installed VS Code extension's serializer. Command
  budgets, layer/preset order, and exported keys/values/order pass. Fresh-load
  Deck tests remain pending.

## Phase 2: real-layout Deck checks (you)

Fresh load, both layouts. These are listed in
[manual testing](../archived/manual-testing.md):

- One held stick click from Menu Entry reaches a Transition Set.
- The staggered Gyro toggle: which modifier variants appear, and whether
  releasing the held bumper scrolls (F3.3).
- F1 scenario (alternative): with the fix, Mod 2 enters without re-pulling.
- The existing first-click check during `Gyro Off Ramp Up` (F3.2, mouse on remove).
- The Enter/Backspace and double-tap-hold Escape/Tab checks (F3.1, keys on add).

## Phase 3: act on the results

| Result | Meaning | Action |
|---|---|---|
| Enter/Backspace or Escape/Tab miss the first key | Key outputs follow rule 1 | Small follow-up: add `delay_start: "5"` to the key Regular Press in `Menu Left: Backspace`, `Menu Right: Enter`, `Menu Left: Escape`, `Menu Right: Tab`. This is the same trick as the ramp handoff and adds no command entries. Test and Deck-check it separately |
| The first click during `Gyro Off Ramp Up` is lost | Outputs don't pass through removal | Needs its own design plan. Emitting the click from `Gyro Off Ramp Up`'s repeating removal would turbo-fire, and a separate click entry on a layer that removes itself risks a stuck button. Also check cursor self-removal's key hand-off. Don't patch in this pass |
| Staggered toggle leaves both variants, or scrolls | Possible side effect of rule 1 and, if it holds, rule 3 | Decide whether it bothers you in play. The scroll is the re-entered modifier's normal short-tap behavior; holding past 300 ms applies the cursor overlay and avoids it. If it's unwanted, write a separate design plan. Covers added by the release array would sit *below* the re-entered modifier, so the obvious patch doesn't work |
| Fn stick click needs a second click, or the F1 scenario fails | Repeats aren't firing on a held input | Rules 1–2 need revisiting. Investigate before changing anything |

## Phase 4: close out

- **Structure doc:** record the client version and date of the checks, and
  state the confirmed output scope. Leave rule 3 marked unverified unless T4 is run.
- **Audit:** add a Deck results section.
- **Manual testing:** tick the checks that passed.
- **`todos.md`:** close the entry, leaving rule 3 as an optional note.
- **Memory:** record the output-scope results.

## Out of scope

- Testing rule 3 now. It stays called out, not tested; run T4 first if a Base
  repeat is ever proposed for removal.
- Removing Base's repeating entries. While rule 3 is unverified, they are the guarantee.
- Adding repeats to delayed applies, or extending delayed-apply resets. That is
  the separate todo from the [delayed-apply audit](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md).
- Reordering existing binding arrays.
- Any F3 layout change before its Deck result exists.
