# Neptune 90.1 command-entry audit

Follow-up: the JSON repair has since been applied and statically verified. See
[IMPLEMENTATION.md](IMPLEMENTATION.md) for the passing results and pending
Steam handoff. The baseline counts and source hashes below are preserved.

Date: 2026-09-27. Audited both current Neptune JSONs at commit `7cee48d`.
**Result: one violation in each file. Base → right joystick → edge has seven
GUI command entries; the maximum is three.** All other input definitions pass.
The layouts and VDF exports were not changed during this audit. The repair is
described in the [implementation plan](../../plans/2026-09-27-neptune-command-budget.md).

## Counting rule and scope

The author explicitly clarified: **“Max 3 command entries; subcommands allowed.”**
This audit therefore counts every activator object on each individual input,
across all activation types. A list of six chord objects counts as six, while a
`bindings.binding` array of twelve actions still belongs to one command entry.
This is the author's required limit; no claim is made that all Steam client
versions have an independently verified engine limit of three.

The scan covered every `group[].inputs.<input>` in both files: buttons, edges,
clicks, touches, trigger pulls, active groups, dormant groups, mode-shift targets,
and unreferenced groups. Each group/input is counted once, with its preset owners
recorded separately. Disabled activator banks were also inspected; all are empty.
Different inputs and definitions in different layers are not added together.

This is a complete static audit of the command budget and a focused review of
the affected ramp-up flow. It does not certify every gameplay interaction.

| Coverage / result | Default | Alternative |
|---|---:|---:|
| Action sets / layers | 1 / 53 | 1 / 53 |
| Groups scanned, including empty groups | 531 | 530 |
| Input definitions scanned | 594 | 630 |
| Enabled command entries | 988 | 1,024 |
| Inputs with one entry | 342 | 378 |
| Inputs with two entries | 114 | 114 |
| Inputs with three entries | 137 | 137 |
| Inputs with more than three entries | **1 (seven)** | **1 (seven)** |
| Disabled command entries | 0 | 0 |
| Largest subcommand array, allowed | 12 | 12 |

The [complete CSV inventory](input-inventory.csv) records all **1,224 inputs**,
their owners, source states, counts, and JSON Pointers. The
[JSON summary](audit-summary.json) contains source hashes and every offending
command's numeric binding, settings, and path. Human-readable targets below were
resolved with the repo's `to-titles` script before reviewing the logic.

Group coverage, with mutually exclusive categories:

| Category | Default groups / inputs | Alternative groups / inputs | Largest entry count |
|---|---:|---:|---:|
| Referenced as active | 319 / 486 | 319 / 522 | 7 |
| Additional targets of mode-shift commands from active groups | 6 / 36 | 6 / 36 | 1 |
| Remaining referenced inactive groups | 156 / 34 | 155 / 34 | 3 |
| Unreferenced groups | 50 / 38 | 50 / 38 | 1 |

“Active” here means configured active in any preset, not proof that all layers
are reached at runtime. The six additional mode-shift targets in each file are
`1039`, `1043`, `1290`, `1291`, `12900`, and `12910`. All groups were scanned
regardless of this classification. The orphan groups are included, not proposed
for deletion as part of this repair.

## Findings

### 1. Both Base right-stick edges exceed the budget

Both violations are group **15**, array index **7**, input **edge**, owned by
**Base**, source **right_joystick active**:

`/controller_mappings/group/7/inputs/edge/activators`

Locations in the audited revision:

- [Default JSON, edge at line 787](../../neptune/single-set-default_hold-gyro_latest.json#L787).
- [Alternative JSON, edge at line 793](../../neptune/single-set-alternative_hold-gyro_latest.json#L793).

| Command entry | Default condition / result | Alternative condition / result |
|---|---|---|
| `Full_Press` | Add Gyro Off Ramp Up | Add Gyro Off Ramp Up |
| `chord[0]` | Selector 5: add Turning Ramp Up 0 | Selector 1: add Turning Ramp Up 0 |
| `chord[1]` | Selector 6: add Turning Ramp Up 0 | Selector 2: add Turning Ramp Up 0 |
| `chord[2]` | Selector 7: add Turning Ramp Up 0 | Selector 5: empty binding |
| `chord[3]` | Selector 8: add Turning Ramp Up 0 | Selector 6: empty binding |
| `chord[4]` | Selector 1: empty binding | Selector 7: empty binding |
| `chord[5]` | Selector 2: empty binding | Selector 8: empty binding |

Selectors 1/2 are the bumpers; 5/6 are full trigger pulls; 7/8 are partial
trigger pulls. Default uses the triggers for mouse buttons and the bumpers for
modifiers; alternative swaps those roles. All seven entries repeat. The regular
press keeps `haptic_intensity: "0"`; the empty chords additionally have
`interruptable: "0"`. The trigger chords have no explicit interruption override.
Each command here has exactly one binding action: this is seven entries, not a
single seven-subcommand array.

### 2. The port expanded selector alternatives into extra commands

In the [July reference](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json#L692),
Base right-stick group **5** uses exactly three entries:

| Entry | Selection | Result |
|---|---|---|
| Regular Press | Default edge path | Add Gyro Off Ramp Up |
| Chord | Mask `50331651`: either trigger, partial or full pull | Add Turning Ramp Up 0 |
| Chord | Mask `12`: either bumper | Empty binding |

The [original port plan](../../plans/2026-09-27-neptune-trigger-rampup-port.md)
explicitly chose one chord per button because Neptune used legacy `chord_button`
selectors. That confused the format of the existing export with device
capability. Valve's [March 9, 2026 update](https://steamcommunity.com/games/593110/announcements/detail/524243918833846834)
introduced the multiple-button selector for chord activators; the same change
appears in the [official Deck release notes](https://www.steamdeck.com/en/news/?p=26).
The latter is a paginated news listing, so its page number can change.

Git history independently identifies the introduction:

- Before `4c351cd`, Base's edge had one Soft Press entry with two subcommands.
- `4c351cd` replaced that edge with seven entries in each variant.
- Older menu-button violations also existed then; the current files no longer
  contain those. They are not additional present-day findings.
- `7cee48d` preserved the seven-entry binding while reordering layers. Its
  validation checked target preservation and preset ordering, not this budget.

### 3. Subcommand arrays are not additional violations

Counting individual binding actions would flag 232 inputs per variant. That
would misapply the author's rule. Examples include modifier cleanup arrays and
Turning Ramp Up 0's three entries in group **423**: delayed add, inverted cleanup,
and repeating reset. The latter has five binding actions across **three** entries
and is compliant. Preserve its three-entry structure and subcommand ordering.

### 4. The July snapshot is a reference for this flow, not blanket validation

Its Base edge is compliant. A full scan of that snapshot additionally found two
four-entry inputs in Split Stick's switch group **383**: `left_bumper` and
`right_bumper`. These are outside the requested Neptune repair and must not be
copied as approved examples. The snapshot also has duplicate `DEPRECATED` layer
titles. It was already in readable title form; it was not round-tripped to IDs.

## Ramp-up review relevant to consolidation

| Behavior | Current evidence in the two Neptune files |
|---|---|
| Plain mouse triggers | Default Base groups 13/14: one analog `edge` mouse binding each. Alternative Base group 10: one bumper mouse binding each. |
| No dedicated trigger layers | The former L2/R2 trigger layers in default and L1/R1 trigger layers in alternative, including gyro variants, are absent. |
| Base owns edge selection | Group 15 contains the seven-entry selector described above. Gyro's own right-stick group is inactive, allowing Base's flow. |
| Gyro-off entry | Gyro Off Ramp Up edge group 13041 (default), 13038 (alternative): inverted removal at 25807; delayed Turning Ramp Up 0 apply at 29031 after 5 ms. Two entries. |
| Turning Ramp Up 0 | Group 423: Turning Ramp Up 1 after 250 ms at 29031; inverted cleanup at 29031; 300 ms repeating removal of stage 1. Three entries. Sensitivity 130, vertical scale 77. |
| Turning Ramp Up 1 | Group 551: inverted cleanup at 25807. One edge entry. Sensitivity 160, vertical scale 63. |
| Trigger pressed while gyro-off | Default groups 13030/13031 `edge`; alternative group 13029 bumpers: repeating removal of Gyro Off Ramp Up. |
| Modifier during ramp-up | Default groups 414/542 bumpers; alternative groups 412/413/540/541 trigger `click`: cleanup subcommands in one entry. The alternative also keeps its partial-pull empty override. |

Existing preset-key order, preset block order, sequential IDs, and unique titles
pass in both Neptune files. All 1,440 default and 1,438 alternative runtime
references resolve. These checks are independent of the failed command budget.

## Reproduce and follow up

```bash
python3 audit_command_budget.py neptune/single-set-default_hold-gyro_latest.json neptune/single-set-alternative_hold-gyro_latest.json
python3 audit_command_budget.py neptune/single-set-default_hold-gyro_latest.json neptune/single-set-alternative_hold-gyro_latest.json --json
python3 -m unittest discover -s tests -v
```

At this revision the first two commands correctly exit **1**, reporting the two
violations. The seven checker regression tests pass. The checker neither edits
files nor interprets runtime IDs, so the count is identical in numeric/title form.
The audit used `to-titles --output` on temporary copies before analyzing targets.

An in-memory candidate replaced the six single-selector chords with two Any
chords. Both complete candidate layouts pass the three-entry check. For each
variant, all **64** Boolean combinations of the six legacy selectors produced
the same set of selected outputs and non-selector settings. This checks selector
equivalence only: it does not simulate Steam's interruption priority, repeated
event timing, or layer-stack transitions. No candidate was installed or saved
over a layout; fresh-load Deck testing remains in the implementation plan.

Audit source hashes (SHA-256):

- Default: `cfa0fb70c72289a101f7a1c3dab82820495a24c2d9003e09db9be2f723bfea76`
- Alternative: `519b66ca3bbddd2f2e6aaae89dc8426c1aa5811577a0a406be5c615e33432afd`

The inventory and summary are snapshots of these hashes, not a claim that future
edits will still pass. Rerun the checker whenever activators are edited or copied.
