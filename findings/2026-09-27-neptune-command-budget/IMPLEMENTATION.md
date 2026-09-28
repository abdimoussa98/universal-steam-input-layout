# Neptune command-budget implementation

Date: 2026-09-27. The [plan](../../plans/2026-09-27-neptune-command-budget.md)
has been applied to both Neptune JSON files. **All 1,224 input definitions now
meet the three-command-entry limit.** The earlier [audit](AUDIT.md), inventory,
and summary retain their pre-repair counts and hashes from commit `7cee48d`.
This record accompanies the repair and the subsequent 90.2 JSON/VDF release
metadata. No Deck runtime results have been recorded.

## Applied change

The [pre-commit selector verification](CHORD_SELECTOR_VERIFICATION.md) independently
confirms the field names, Any/All values, and button masks from the Steam UI and
Valve's explanation. It checks the subsequent 90.2 metadata version; the static
implementation snapshot below retains its original 90.1 hashes.

Only Base's active right-stick group's `edge.activators.chord` list changed
(group 15 in each file). Six single-button chords became two multi-button Any
chords. The separate Regular Press entry is preserved exactly.

| Command | Default mask | Alternative mask | Output |
|---|---|---|---|
| Regular Press | None | None | Add Gyro Off Ramp Up |
| Trigger-held chord | `50331651` | `12` | Add Turning Ramp Up 0 |
| Modifier-held chord | `12` | `50331651` | Empty binding |

Both replacement chords explicitly set
`gyro_ratchet_button_requireany_or_all: "0"`. Their legacy `chord_button`
settings were removed. Each retains `hold_repeats: "1"`; the modifier chord
also retains `interruptable: "0"`. Regular Press retains its suppressed haptic.

The two files were first converted with `convert_runtime_ids.py to-titles
--output` into temporary copies. Changes and preflight checks were performed in
title form. `to-ids --output` then produced the finalized numeric JSONs, with no
warnings or unresolved tokens. Reading those files back with `to-titles`
reproduced the edited readable copies byte for byte before installation.

## Verified results

| Check | Default | Alternative |
|---|---:|---:|
| Groups scanned | 531 | 530 |
| Inputs scanned | 594 | 630 |
| Maximum command entries per input | **3** | **3** |
| Budget violations | **0** | **0** |
| Total enabled command entries | 984 | 1,020 |
| Inputs with 1 / 2 / 3 entries | 342 / 114 / 138 | 378 / 114 / 138 |
| Disabled command entries | 0 | 0 |
| Numeric runtime references resolved | 1,437 | 1,437 |
| Selector combinations checked | 64 | 64 |

The full scan includes inactive, mode-shift, and unreferenced groups; subcommands
inside one command entry remain permitted. The runtime-reference total shrank
because redundant copies of the Turning Ramp Up 0 apply were removed.

For all 64 Boolean combinations of the six legacy selectors, the consolidated
chords select the same set of output bindings and non-selector settings. This
proves equivalence of those predicates, not Steam's scheduling or interruption
priority when both roles are held.

Structural comparisons in both numeric and title forms verified that restoring
the old Base edge chord list reproduces the entire original JSON object. The
title-form comparison also reproduces the original bytes. Thus all other
bindings, command arrays, layer/group IDs, delays, sensitivities, preset order,
metadata, and the 90.1 title/description are preserved. Preset keys ascend;
preset blocks match actions plus layers; preset IDs remain 0–53; titles are
unique. Turning Ramp Up 0 and 1 remain the first two layers.

The [post-implementation summary](post-implementation-summary.json) records the
new file hashes and static results. Reproduce the full budget check with:

```bash
python3 audit_command_budget.py neptune/single-set-default_hold-gyro_latest.json neptune/single-set-alternative_hold-gyro_latest.json
```

Expected exit status: **0** for both files. The budget checker's seven regression
tests also pass (`python3 -m unittest discover -s tests -v`).

## 90.2 export verification

The user subsequently requested the 90.2 title/description update, and both
paired `.vdf` exports now contain that metadata and the three-entry edge.
Before commit, an ordered token comparison verified every key, value, repeated
entry, and block against each JSON: 32,063 tokens for default and 32,514 for
alternative. Both full command-budget checks and all seven regression tests
pass. Preset ordering, unique titles, and the numeric/title round-trip also pass,
with 1,437 resolved runtime references in each variant. The earlier
`post-implementation-summary.json` remains the historical 90.1 repair snapshot.

## Remaining Steam handoff

Load the verified 90.2 exports fresh on the Deck, following the
[steam-layout-apply skill](../../.claude/skills/steam-layout-apply/SKILL.md).

Execute the plan's [Deck acceptance checks](../../plans/2026-09-27-neptune-command-budget.md#deck-acceptance-checks-both-variants),
especially trigger-plus-modifier overlap, partial/full trigger transitions,
mid-turn gyro recovery, interrupted ramp-up, and the RTP cleanup/momentum path.
No Steam/Deck runtime test was available in this workspace, so those checks
remain pending rather than being inferred from the static results.
