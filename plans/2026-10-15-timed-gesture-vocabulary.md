# Plan: consistent timed-gesture vocabulary

**Status, 2026-10-15: implemented.**

The user approved **Hold / Tap, then hold** as the wording for the two
gestures and requested a project-wide documentation plan, then asked for its
implementation. The implementation keeps the distinct single Tap output visible.

## Agreed vocabulary

| Concept | Wording | Meaning |
|---|---|---|
| Overall concept | **Timed gestures** | Actions distinguished by press, release and hold timing. |
| Pair of gestures | **Hold / Tap, then hold** | Two alternative gestures on the same control. |
| First gesture | **Hold** | Press and keep holding. |
| Second gesture | **Tap, then hold** | Press and release, then press again within the release window and keep holding. |
| Initial timing stage | **Initial hold** | The first press and its hold deadline. |
| Between presses | **Release window** | The interval in which the next press can begin the second gesture. |
| Second timing stage | **Second hold** | Holding the second press, including its own deadline. |

Use the exact pair wording in headings, instructions and compact labels.
Use ordinary sentence casing in prose. Avoid `||`, `tap & hold`, ambiguous
`tap/hold`, and “double tap and hold” when they mean this pair or second gesture.
Use **Initial hold → Release window → Second hold** when describing the
second gesture's timeline; explain that the first gesture stays on the initial
hold branch. These are alternative paths, not three mandatory steps for Hold.

**Tap** still means a single press and release. **Tap / Hold** remains valid
where those really are the two actions. Do not rename actual tap output,
repeated taps, ordinary double taps, chord holds or pressure stages to imply
a second hold. A source's delay values and activation behavior remain authoritative.

## 1. Inventory and classify occurrences

Before implementation, use repository-wide searches for spelling, punctuation
and case variants of tap/hold, tap-and-hold, double-tap-and-hold, hold-or-tap,
and existing timeline labels. Exclude dependency caches and build artifacts.
Classify each match as maintained explanatory prose, display text, generated
text, exact technical identifier, or historical evidence. Record the changed
files and justified remaining matches in implementation findings.

Cover menu buttons, bumper modifiers and trigger modifiers in the alternative
layout. Review stick-direction, stick-touch and trackpad interactions too;
apply the vocabulary only where their actual sequence matches. Do not infer
that every control supports both gestures or that every profile has identical
timings. Distinguish default L1/R1 modifiers from alternative L2/R2 modifiers.

## 2. Establish one documentation source

Update [Layout Vocabulary](../resources/Layout%20Vocabulary.md) with the table,
plain-language gesture sequences and the distinction between gestures and
implementation layers. Link other maintained explanations to this definition.

Review and update relevant explanatory passages in:

- Root [README](../README.md), controller READMEs under `ibex/`, `neptune/`
  and `dse/`, and the [viewer README](../overlay/README.md).
- `docs/`, especially the reading guide and any build/publishing guidance
  that defines or generates user-facing layout descriptions.
- `resources/`, particularly Stateful Layer Transitions, Steam Input JSON
  Structure, Delay Timers and Repeat Rates, and Layer Definition of Done.
  Preserve rule IDs and the substance of author-confirmed behavior.
- Relevant repository skills and templates, so future work uses the same terms.
- Active plans, live TODOs and maintained findings used as current guidance,
  including the overlay implementation plan and findings.
- New changelog/release prose and current generated descriptions, where applicable.

Preserve quotations, past release records, completed experiment evidence,
archived plans and immutable `versions/` snapshots. Where an old term could
mislead readers of a maintained entry point, add a vocabulary link or a short
terminology note instead of rewriting what the historical record says.

## 3. Update display and generated wording

Audit [shared UI](../overlay/src/ui.rs), phase descriptions in
[gesture core](../overlay/src/core/gestures.rs), and labels emitted by the
[profile exporter](../steam_layout/overlay_profile.py).

- Use **Hold / Tap, then hold** when naming that pair, with separate outcomes
  for each gesture. Keep any genuine single-tap output explicitly labeled Tap.
- Use Initial hold, Release window and Second hold for the corresponding
  timeline stages. Keep output markers and remaining-time explanations clear.
- Explain release-before-deadline versus release-after-deadline behavior using
  the actual recipe. A terminology edit must not alter timing or inheritance.
- Review tooltips, status/history messages, help text, profile descriptions,
  export assumptions and examples for the same distinctions.
- Update the generating source before regenerating affected profile text or
  layout descriptions. Preserve profile schema and runtime behavior unless a
  concrete display requirement needs a separately explained change.

The existing timer says “Tap or hold” and displays TAP/HOLD outcomes. Review
what those outcomes represent before changing the heading: simply renaming
TAP to “Tap, then hold” would misdescribe the current single-tap output.

## 4. Preserve technical references and layout behavior

`Tap Cover`, `Double Tap`, `Double Tap Cover`, activator names, serialized phase
values and layer-title tokens are technical references, not interchangeable
gesture labels. Keep those identifiers stable and explain their relationship
to the reader-facing terms in the vocabulary document. No blanket replacement
across layer names, commands, JSON, filenames or test fixtures.

When implementation requires reading or changing current layout descriptions,
follow the repository layout-prep workflow. If generated layout metadata is
changed, use the appropriate builder/converter and layout-apply workflow,
including required JSON/VDF synchronization and release metadata checks.
Do not edit immutable release snapshots to modernize their wording. A semantic
diff must show unchanged bindings, activation types, delays, masks, thresholds,
layer order and inheritance. Renaming technical layer identifiers would be a
separate migration, outside this wording plan.

## 5. Validation

- For any new shared presentation mapping or display behavior, add a failing
  behavioral test first, implement it, then run the existing native/WASM tests.
  Include a single-tap example and a tap-then-hold example so the two cannot be
  accidentally conflated. Do not add brittle tests for every prose sentence.
- Run exporter tests and regenerate affected profiles; verify binding outputs
  and timing values are unchanged. Run applicable layout checks if metadata
  regeneration touches layouts.
- Build the shared UI and inspect the browser/native presentation at the
  default size and a smaller size. Longer labels must not hide actions or
  timing markers. Reuse the browser smoke checks for affected UI paths.
- Check Markdown links and anchors affected by heading edits. Run a final
  terminology search and classify intentional old-wording matches.
- Review examples across menu, default bumper, alternative trigger and applicable
  stick/pad gestures. Ensure documentation does not imply unsupported viewer
  profiles or automatic Steam mode tracking.

## Completion criteria

- The central vocabulary defines the approved pair and both sequences.
- All relevant maintained documentation and display text use those definitions
  consistently, with genuine single taps still accurately described.
- Generated text agrees with its source; technical identifiers and historical
  records retain traceable meaning.
- No input behavior, timing, inheritance or layout structure changes as a
  side effect of the terminology update.
- Relevant tests and visual checks pass; the final implementation report lists
  updated areas, intentional exceptions and any remaining acceptance checks.

Implementation was requested and completed on 2026-10-15. See the
[implementation record](../findings/2026-10-15-timed-gesture-vocabulary/README.md)
for validation and intentional exceptions.
