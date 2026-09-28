# Plan: consolidate Neptune ramp-up selection to three command entries

Date: 2026-09-27. **Status: 90.2 JSON implementation, static checks, and VDF export
verification complete; fresh-load Deck tests pending.** Based on the
[complete 90.1 command-budget audit](../findings/2026-09-27-neptune-command-budget/AUDIT.md)
of commit `7cee48d`. The author's rule is at most three GUI command entries per
input; subcommand arrays are allowed beyond three actions.

Implementation results: [record and remaining handoff](../findings/2026-09-27-neptune-command-budget/IMPLEMENTATION.md),
[post-implementation audit summary](../findings/2026-09-27-neptune-command-budget/post-implementation-summary.json).
Steps 1–5 and step 6's VDF conversion/verification are complete; the Deck checks
below remain pending. Static results for step 7 are recorded with the
implementation; runtime results are not yet recorded. After the original
change-only-the-edge repair, the user requested the 90.2 title and description
update. Both JSONs and their matching VDF exports include it. The earlier
post-implementation summary preserves the original 90.1 repair snapshot.

## Intended change

In both layouts, replace Base → right joystick → edge's six individual chords
with **two multi-button Any chords**. Keep its Regular Press entry. This yields
exactly three command entries and retains the July reference's selection design.
No new helper layer is needed, and no trigger layer needs to return.

| Command entry | Default selector | Alternative selector | Binding |
|---|---|---|---|
| Regular Press | None | None | Add Gyro Off Ramp Up |
| Trigger-held chord | Any LT/RT partial or full pull: `50331651` | Any LB/RB: `12` | Add Turning Ramp Up 0 |
| Modifier-held chord | Any LB/RB: `12` | Any LT/RT partial or full pull: `50331651` | Empty binding |

These values are actual button masks from the July reference, not bitwise
combinations of legacy selector IDs:

- `50331651 = (1 << 0) | (1 << 1) | (1 << 24) | (1 << 25)`.
- `12 = (1 << 2) | (1 << 3)`.
- Use `gyro_ratchet_button_mask` and explicit
  `gyro_ratchet_button_requireany_or_all: "0"` (**Any**). Do not use **All**;
  either relevant button must satisfy the chord by itself.
- Remove `chord_button` from the two replacement chord objects rather than
  keeping two competing selector formats on one command.

The exact button bits and **Any = 0** value have since been independently
[verified against the installed Steam UI](../findings/2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md).
The older decode table's inferred left/right soft-pull labels were corrected;
these combined masks include both bits and remain unchanged. Confirm the
imported selections and **Any** setting in the target Deck GUI.

Preserve Regular Press's `{hold_repeats: "1", haptic_intensity: "0"}`. Preserve
the trigger chord's `hold_repeats: "1"` with no new interruption override, and
the modifier chord's `{hold_repeats: "1", interruptable: "0"}`. Leave every
binding payload unchanged and retain the command order: regular, trigger, modifier.

## Required behavior

When Base's edge selection is exposed:

| Trigger role held | Modifier role held | Required outcome |
|---|---|---|
| No | No | Enter Gyro Off Ramp Up, then the existing timed ramp-up flow. |
| Yes | No | Enter Turning Ramp Up 0 while gyro remains on. |
| No | Yes | Suppress Base ramp-up through the empty chord; preserve modifier operation. |
| Yes | Yes | Preserve modifier suppression; no unwanted gyro-off or ramp-up entry. |

The overlapping trigger+modifier case needs runtime verification. The repo's
bottom-to-top execution rule governs subcommands within a binding array, **not**
priority between independent chord activators. Do not claim this truth table is
proven by JSON object order or by the static predicate check.

## Implementation sequence

1. **Record the baseline and prepare readable copies.** Run the layout-prep
   ordering/title checks and the budget checker on both files. Expect one
   seven-entry violation per file. Run `convert_runtime_ids.py to-titles --output`
   before editing, and keep the originals for comparison. The July reference
   is already readable and has duplicate `DEPRECATED` titles; do not convert it
   to IDs or use its entire layout as a replacement.
2. **Change only the two Base edge definitions.** Find Base's preset and its
   active `right_joystick` group; currently this is group 15 in both variants.
   Build the two new chord objects from the existing identical-output groups
   using the selector table above. Avoid a global conversion of every legacy
   chord, and do not change group IDs, preset keys, layer order, or metadata.
3. **Preserve adjacent flow.** Keep the plain mouse trigger bindings, Gyro's
   inactive right-stick override, Gyro Off Ramp Up's trigger-removal paths,
   ramp-up threshold/delay/reset settings, modifier cleanup arrays, and RTP
   stale-entry cleanup. Keep the RTP trackball-momentum exception: no new
   repeating removal alongside its delayed touch apply. Sensitivities remain
   130/77 and 160/63, with Turning Ramp Up 0 and 1 first in the layer list.
4. **Check equivalence and the full budget.** Run the checks below. If merging
   exposes different timing/settings, preserve the distinct behavior rather
   than merging it silently. The two known sets have matching non-selector
   settings, so no redesign beyond selector consolidation is presently needed.
5. **Finalize numeric IDs.** Run the apply skill's command-budget and ordering
   preflight checks, then `to-ids --output`. Confirm no tokens/warnings remain
   and that a readback to titles matches the edited copy. Only then replace
   the two JSON files. Conversion back to numeric IDs must not change targets.
6. **Export and exercise the saved layout.** Convert JSON → VDF using
   `pfwobcke.vscode-vdf`, verify the exports match the JSONs, and load them fresh
   in Steam. Run the Deck checks below. A live editing session alone is not
   enough. If a mask/Any selector is not retained by the target client, document
   that exact export and resolve it without reintroducing more than three
   entries. Re-export after GUI edits and rerun the same checks.
7. **Record results.** Add the implemented commit and actual runtime test
   results to this plan and link a new audit snapshot. Preserve the 90.1 audit
   as historical evidence rather than overwriting its counts. Decide release
   metadata as part of the implementation; this planning pass does not bump it.

## Static acceptance checks

- `audit_command_budget.py` exits **0** for both complete files: no input,
  including dormant/unreferenced groups, exceeds three command entries.
- Both Base edges have exactly one Regular Press and two chord objects, no
  leftover `chord_button`, the correct role-specific masks, and explicit Any.
- Enabled histogram becomes default `{1: 342, 2: 114, 3: 138}`, alternative
  `{1: 378, 2: 114, 3: 138}`. Input/group counts and empty disabled banks stay
  unchanged. Total command entries become 984 and 1,020 respectively.
- After resolving runtime IDs to titles, differences are confined to those
  two edge chord lists. The bindings' target titles and non-selector settings
  must match their original groups; all other file content must compare equal.
- Compare the selected payload/settings sets for all 64 combinations of the
  six old selectors against the two Any masks. This was prototyped successfully
  in memory during the audit; rerun against the actual edited data. It does not
  prove runtime interruption or event ordering.
- Preset keys ascend; preset blocks match actions plus layers; preset IDs are
  sequential 0–53; titles are unique; all runtime references resolve.
- Numeric/title round-trip passes; no unresolved tokens remain. The reference
  snapshot's separate Split Stick budget violations are not imported.

## Deck acceptance checks, both variants

1. Confirm the right-stick outer-edge GUI shows **three** command entries, the
   correct four-trigger/two-bumper selections, and **Any** on both chords.
2. With neither role held, move to the edge: gyro turns off, stage 0 begins,
   then stage 1 follows after the existing 250 ms delay. Move inward at each
   stage: gyro returns and both ramp layers clear at their existing thresholds.
3. Hold each trigger-role button independently before reaching the edge.
   Default: partial and full L2, partial and full R2, then both together.
   Alternative: L1, R1, then both. Ramp-up must retain gyro; mouse output must
   still work without unwanted repeats.
4. Press a trigger-role button after entering gyro-off, in both ramp stages.
   Gyro must return and the first mouse press must register. Release one of
   two held trigger-role buttons and verify the remaining one still satisfies
   the Any chord. Test full-to-partial trigger transitions in default.
5. Hold each modifier-role button, then both, and approach the edge. Repeat
   with a trigger also held and with press/release orders reversed. No unwanted
   Base ramp-up or gyro-off path should leak through.
6. Enter a modifier during ramp-up: default bumpers should exit ramp-up;
   alternative partial pulls should keep the existing block and full pulls
   should exit. The correct regular/gyro modifier variant must enter.
7. Repeat the edge/trigger/modifier cases in Gyro mode, confirming its inactive
   right-stick group still exposes Base's flow.
8. Interrupt the 250 ms stage transition, recenter, then retry; preserve the
   300 ms reset behavior. Exercise modifier → RTP touch → release both → edge
   in both release orders; stale entry/cover state must clear and trackball
   momentum must remain intact. Confirm no extra edge haptic was introduced.

These are required future checks, not reported runtime test results.
