# Universal Steam Input Layout

Custom Steam Input controller layouts with advanced layer management.

Current design uses explicit `add_layer` / `remove_layer` commands only:
never Steam's buggy `hold_layer` API, and never action-set switching. See
[runtime rules and remaining migration conflicts](resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).

## Installation

Drop layout files in `/home/deck/.steam/steam/controller_base/templates/`

---

## Layout Variants

This repository contains two layout variants with different button mappings:

| Layout | Triggers | Modifiers |
|--------|----------|-----------|
| **Default** | L2/R2 | L1/R1 (bumpers add modifier layers) |
| **Alternative** | L1/R1 | L2/R2 (triggers add modifier layers) |

**Default layout:** Traditional FPS-style where L2/R2 are used as triggers (aim/fire) and L1/R1 bumpers activate modifier layers for alternate button mappings.

**Alternative layout:** Inverted scheme where L1/R1 are used as triggers and L2/R2 activate modifier layers. Useful for games where analog trigger control is less important.

---

## Scripts

This repository includes several Python scripts for managing Steam Input layout JSON files.

### 1. `duplicate_layer.py` - Duplicate Action Layers

Duplicates an action layer along with all its children relationships (groups, bindings, etc.). The duplicated layer is added to the **end** of `action_layers` to preserve runtime ID ordering.

**Use Cases:**
- Create a variant of an existing layer with different bindings
- Clone a complex layer as a starting point for a new one
- Back up a layer before making experimental changes

**Usage:**

```bash
# List all available layers in a layout
python3 duplicate_layer.py layout.json --list

# Duplicate a layer (auto-generates title with " (Copy)" suffix)
python3 duplicate_layer.py layout.json Preset_1000006

# Duplicate with a custom title
python3 duplicate_layer.py layout.json Preset_1000006 "My Custom Layer"

# Output to a different file instead of modifying in-place
python3 duplicate_layer.py layout.json Preset_1000006 --output new_layout.json

# Skip creating a backup file
python3 duplicate_layer.py layout.json Preset_1000006 --no-backup
```

**What gets duplicated:**
- The layer definition in `action_layers`
- All groups referenced in `group_source_bindings`
- The preset entry with updated group references

**Important:** The new layer gets a new runtime ID (appended to the end), so existing `controller_action` commands remain unaffected.

---

### 2. `delete_action_set_complete.py` - Delete Action Sets

Deletes an entire action set and **all** its associations from a layout file. This includes child layers, presets, groups, and automatically updates all `controller_action` runtime ID references.

**Use Cases:**
- Remove an unused action set (e.g., "Gyro" or "Gamepad" mode)
- Clean up a layout by removing experimental sets
- Reduce layout complexity

**Usage:**

```bash
python3 delete_action_set_complete.py layout.json Preset_1000014
```

**What gets deleted:**
1. The action set from `actions`
2. All action layers with `parent_set_name` referencing this set
3. All preset entries for the set and its child layers
4. All groups referenced by those presets
5. All `group_source_bindings` in remaining presets that reference deleted groups

**What gets updated:**
- All `controller_action` commands (`CHANGE_PRESET`, `add_layer`, `remove_layer`, `hold_layer`) that reference runtime IDs affected by the deletion

**Warning:** Deleting an action set shifts all subsequent runtime IDs down. The script handles this automatically using a two-pass replacement to prevent cascading issues.

---

### 3. `convert_runtime_ids.py` - Convert Runtime IDs to Titles

Converts between numeric runtime IDs and human-readable titles in `controller_action` commands. Makes layouts easier to read and edit manually.

**Use Cases:**
- Make a layout human-readable for manual editing
- Debug which layers are being activated by `controller_action` commands
- Convert back to numeric IDs before using the layout in Steam

**Usage:**

```bash
# Convert numeric IDs to readable titles
# e.g., "controller_action add_layer 5 0 0" -> "controller_action add_layer {{L2}} 0 0"
python3 convert_runtime_ids.py to-titles layout.json

# Convert titles back to numeric IDs
# e.g., "controller_action add_layer {{L2}} 0 0" -> "controller_action add_layer 5 0 0"
python3 convert_runtime_ids.py to-ids layout.json

# Output to a different file instead of modifying in-place
python3 convert_runtime_ids.py to-titles layout.json --output readable_layout.json
```

**Title Format:**
- Action sets: `{{Base}}`, `{{Gyro}}`
- Action layers: `{{Base::L2}}`, `{{Base::RST: Temporary Gyro}}`

The `Parent::Title` format for layers ensures unique identification when multiple sets have layers with the same name.

---

### 4. `audit_inheritance.py` - Inheritance and Blocking Check

Derives every stack each Always On layer (and any layer named in
`traced_stacks.json`) can be applied on, by following the layout's own layer
transitions for up to `--depth` input events (default 5). It then checks
whether any stack puts a layer command under an input the layer leaves open.
Each such route must be blocked, or have a recorded decision in
`traced_stacks.json`. The tool recommends the block: replace with the
underlying output if it's identical in every stack, otherwise clear. The check
also fails if the search isn't saturated, meaning the last depth level still
found new routes. Read-only. Exit codes: **0** = pass, **1** = undecided route
or unsaturated search, **2** = invalid input.
See [Layer Definition of Done §8](resources/Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking).

```bash
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json --entries "RTP: Double Tap"
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json --untraced   # review list
```

### 5. `steam_layout/` - Shared Library and Fix Pipeline

The reusable code behind the scripts above. Import it from the repo root.

| Module | Use it for |
|---|---|
| `steam_layout.model` | Read a layout (numeric IDs or title tokens): layer titles, active groups per source, bindings in execution order, Always On layers |
| `steam_layout.stacks` | `StackSpace`: every stack reachable from Base, and the queries `below`, `containing`, `when_effective` and `co_active` |
| `steam_layout.inheritance` | The inheritance and blocking audit that `audit_inheritance.py` wraps |
| `steam_layout.fixes` | The ordered, idempotent post-install fixes that `install_neptune.py` runs |
| `steam_layout.held_model` | Historical untimed stack model: held buttons, chords, boolean delays/repeats and generic legacy `hold_layer` support |
| `steam_layout.timed_model` | Replay presses, releases, analog thresholds and individual millisecond timers with explicit layer commands |
| `steam_layout.timed_search` | Resumable timed search, replayed witnesses and independently checked graph closure; `run`, `show`, `witness`, `check` |
| `steam_layout.timed_trace` | Run a JSON event trace and record all timed model branches, clocks and model identity |
| `steam_layout.timed_facts`, `steam_layout.timed_discover` | Catalogue the three layer-query alternatives and discover independently replayed timed witnesses; compact witness archives |
| `steam_layout.timed_seek` | Target selected unresolved facts with a bounded concrete search and save compact verified witnesses ([usage](findings/2026-09-30-stack-search/TIMED-MODEL.md#seek-witnesses-for-selected-facts)) |
| `steam_layout.timed_envelope`, `steam_layout.timed_proof` | Check inductive exclusions over a full-stack relaxation of the timed runtime |
| `steam_layout.timed_phase_envelope` | Six runtime-derived press/timer restrictions; included in certificate identity |
| `steam_layout.timed_progress_envelope` | Ordered-owner repeater/delay restrictions; included in certificate identity |
| `steam_layout.timed_elapsed_envelope` | Separate elapsed repeats from newly activated one-shots; included in certificate identity |
| `steam_layout.timed_analog_envelope` | Production compiler: the preceding rules plus atomic first batches for positive analog samples and five event families |
| `steam_layout.timed_predicates` | Family-order and exact-fact hypotheses for additional checked induction |
| `steam_layout.timed_mine`, `steam_layout.timed_between` | Suggest small lower-layer or conditional between-layer families from replayed samples; every output still requires induction |
| `steam_layout.timed_audit` | Combine witnesses and checked induction into per-layer reports; `run` / `show` with identity-bound certificates |
| `steam_layout.timed_refine` | Extend a checked baseline with unresolved fact hypotheses; independently validate a new certificate and full report |
| `steam_layout.timed_minimize` | Remove logically redundant predicates from a checked certificate, then independently validate the smaller proof |
| `steam_layout.timed_reduction` | Exact relevance quotient for stack reachability, reusable with the timed search APIs |
| `steam_layout.source_geometry` | Resolve saved source geometry and its inherited owners without inventing omitted defaults |
| `steam_layout.stackdb` | Run the exhaustive search (`tools/stack_search`, C++) and query its results: what every input does in any stack, what a layer inherits, the button sequence that reaches a state |

```python
from steam_layout.model import Layout
from steam_layout.stacks import StackSpace

space = StackSpace.of(Layout(data), depth=5)
space.when_effective("L1: Modifier 0", "switch", "left_bumper")  # stacks where that binding fires
space.co_active("L1: Modifier 0", "switch", "left_bumper")       # layers a cleanup there could find
```

```bash
python3 -m steam_layout.fixes neptune/*_latest.json --dry-run   # what the pipeline would change
```

The exhaustive search visits every state (stack plus held buttons) reachable from Base, breadth first, one button event per level. `--disk` keeps it within a memory budget by storing states on disk; it can be stopped (Ctrl-C) and continued with `--resume`. `summary.json` records `exact_depth`: every state within that many events is included.

```bash
python3 -m steam_layout.stackdb run neptune/single-set-default_hold-gyro_latest.json out/stack_search/default \
    --disk --memory 12 --disk-limit 150 --max-depth 12
python3 -m steam_layout.stackdb sqlite neptune/single-set-default_hold-gyro_latest.json out/stack_search/default
```

```python
db = StackDB("out/stack_search/default", Layout(data))
db.inheritance("L1: Double Tap")          # every input: what the layers below it give it, with stack counts
db.values(("Base", "L1: Modifier 0"))     # what every input does in that stack
db.moment(gid)                            # a state: stack, held buttons, every input, the events that reach it
db.sql("SELECT name, owner, summary FROM inherited WHERE top = 'L1: Double Tap' GROUP BY name, owner")
```

**Deprecated for routine audits (2026-09-30):** exhaustive stack search and
timed proof tooling are retained for reference, reuse and targeted investigations.
The replacement is an intended-flow inheritance checker, still to be built.
See the [decision, next steps and preserved checkpoint](findings/2026-09-30-stack-search/ARCHIVE.md).
Historical commands below may reference disposable files under `out/`.

The historical HeldModel inductive bound remains available. Install the
optional proof dependency and query a matching untimed search:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-proof.txt
.venv/bin/python -m steam_layout.stackdb show 'L1: Double Tap' --search out/stack_search/default-held
```

This reports layers below/above X and inherited binding owners with X anywhere
in the stack. `proven` has a search witness; `possible` remains unresolved.
All claims are relative to the current untimed model, which has known runtime
gaps. See [usage and proof scope](findings/2026-09-30-stack-search/README.md#the-helper)
and [model limits](findings/2026-09-30-stack-search/MODEL-LIMITS.md).

The new timed simulator can replay a supplied input sequence with numeric
clock deadlines, including removal-driven timer restarts:

```bash
python3 -m steam_layout.timed_trace versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
    findings/2026-09-30-stack-search/timed-example.json \
    --ignore-hold-bindings --default-repeat-ms 50
```

The author accepted 50 ms for omitted repeat intervals in this analysis;
it is not a verified Steam default. Hold commands are omitted only from the
simulation. Analog events supply logical threshold coordinates, not raw
sensor readings. See [timed replay and its contract](findings/2026-09-30-stack-search/TIMED-MODEL.md).

The current timed audit targets the original default **90.6** layout, as
requested after `latest` advanced to 90.7. The tracked versioned file matches
the frozen input's [recorded identity](findings/2026-09-30-stack-search/TIMED-MODEL.md).
The newer 90.7 layout is not covered by these results.

**The timed audit tools are implemented and checked; the full 90.6
classification remains incomplete.** The audit combines replayed timed
witnesses with independently checked induction over all 46,904 below/above
and raw-inheritance alternatives. Every alternative needs a witness or a
checked exclusion; a time budget or solver timeout never establishes one.
The current checkpoint has **11,491 witnessed, 31,644 excluded and 3,769
unresolved** alternatives. Its 901 invariants passed 3,409 independent checks.
Read the [current summary](out/stack_search/timed-facts/default-summary.json),
[full report](out/stack_search/timed-facts/default-audit.json), and
[certificate](out/stack_search/timed-facts/default-certificate.json).
The [four readable layer reports](findings/2026-09-30-stack-search/README.md#checked-current-checkpoint)
provide smaller examples. The full regression suite passed **531 tests**.

Inspect a layer in the saved checkpoint with:

```bash
.venv/bin/python -m steam_layout.timed_audit show \
    versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
    out/stack_search/timed-facts/default-evidence.sqlite \
    out/stack_search/timed-facts/default-certificate.json \
    'L1: Double Tap' --json --ignore-hold-bindings --default-repeat-ms 50
```

To collect more evidence or rebuild a baseline, use the
[discovery, compaction and certificate workflow](findings/2026-09-30-stack-search/TIMED-MODEL.md#discover-compact-and-check).
A fresh `timed_audit run` infers primitive invariants and may produce a weaker
baseline than the saved proof; the workflow writes separate `regenerated-*`
outputs. Use `timed_refine` to retain and extend the checked baseline.
`show` replays archived edges and independently validates the loaded invariant
certificate before using exclusions. Check `complete_for_model` and unresolved
counts in the output; exit 0 only means the report was generated. The older
[exhaustive timed search](findings/2026-09-30-stack-search/TIMED-MODEL.md#reachability-search-and-proof-checks)
and its graph-closure certificates remain available. Neither timed route
imports HeldModel exclusions or certifies Steam hardware equivalence.
To strengthen an existing certificate, use the [refinement command](findings/2026-09-30-stack-search/TIMED-MODEL.md#refine-an-existing-certificate).
It accepts the latest matching witness archive and preserves the checked
baseline. Even with `--layer`, its output report remains global and separately
records whether the selected questions are complete.

## Command entry limit and audit

Every input in these layouts must have **at most three GUI command entries**.
Count each activator object across all activation types, including every element
of a repeated `chord` or `Soft_Press` list. A `bindings.binding` array is
subcommands inside one entry, so its length does not count against this limit.
This is the layout author's requirement, confirmed on 2026-09-27. It exists
because Steam's desktop configuration drops every entry after the third. The one
allowed exception is a delayed-apply reset as a **last** 4th entry, which is the
entry desktop drops; see [the exception](resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget).

```bash
python3 audit_command_budget.py neptune/single-set-default_hold-gyro_latest.json neptune/single-set-alternative_hold-gyro_latest.json
```

The read-only checker scans all groups, including inactive, mode-shift, and
unreferenced groups. It checks disabled activator banks separately. Add `--json`
for a complete input inventory, counts, owners, and exact violation paths.
Exit codes: **0** = pass (allowed 4th-entry resets are listed, not failed), **1** = over budget or a banned activator, **2** = invalid input/schema.
Run it before finalizing edited layouts; it accepts numeric IDs or title tokens.

The same audit fails on **Long Press** and **Double Press**, which misbehave
with Steam's layer API (see [allowed activation types](resources/Steam%20Input%20JSON%20Structure.md#allowed-activation-types)),
and reports unreferenced groups and plain-inactive slots. To remove dead groups
(unreferenced groups and plain-inactive source slots; active, mode-shift and
mode-shift-target groups are kept, and no ID is renumbered):

```bash
python3 prune_dead_groups.py --dry-run neptune/*_latest.json   # report only
python3 prune_dead_groups.py neptune/*_latest.json
```

The baseline 90.1 [audit](findings/2026-09-27-neptune-command-budget/AUDIT.md) found one
violation in each variant: Base's right-stick edge has seven command entries.
The [consolidation plan](plans/2026-09-27-neptune-command-budget.md) has now been
applied to both JSON files: each edge has three entries using two multi-button
Any chords, and the full command-budget checks pass. The
[implementation record](findings/2026-09-27-neptune-command-budget/IMPLEMENTATION.md)
tracks the results. Both 90.4 JSONs and regenerated VDFs include the cursor tuning and hold-entry haptic
and refreshed descriptions; export verification passes. Fresh-load Deck tests
remain pending.
See [counting and chord rules](resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget).

## Runtime ID System

Steam Input assigns runtime IDs based on the **order of appearance** in the JSON:

1. **Action sets** are numbered first, starting at **1**
2. **Action layers** are numbered after all action sets

Example:
```
actions:
  Preset_1000001 (Base)     -> Runtime ID 1
  
action_layers:
  Preset_1000006 (L2)       -> Runtime ID 2
  Preset_1000007 (R2)       -> Runtime ID 3
  ...
```

**Critical:** If you delete or reorder action sets/layers, all subsequent runtime IDs shift. Always use the provided scripts to handle this automatically.

### ⚠️ Load-time hazard: list order vs. Preset numbering (found 2026-07-11)

A layout file actually carries **two implicit orderings**, and Steam can resolve runtime IDs by either one:

1. **List order** — the order blocks appear in `actions` / `action_layers` (what the GUI shows, and what this repo's scripts use)
2. **Numeric key order** — the order of the `Preset_10000XX` numeric keys (creation/renumbering order)

Normally they match. If they diverge (observed after reordering layers in the Steam GUI), a layout that works perfectly in the live editing session can come back with **silently swapped layers on the next fresh VDF load** — Steam's loader resolved the positional runtime IDs against numeric key order while the binds were saved against list order.

**Before trusting or finalizing any exported layout, verify `action_layers` keys are in ascending numeric order.** If they aren't, normalize while the file is in `{{title}}` token form: reorder `action_layers` (and the matching `preset` blocks) into numeric order and resequence the preset `id` fields, then run `to-ids`.

Full case study with pre/post snapshots: `findings/2026-07-11-layer-order-swap/FINDINGS.md`

---

## Resources

See the `resources/` folder for additional documentation:

- [Layout Vocabulary](resources/Layout%20Vocabulary.md) - button overlays, owning layers, interaction stacks, and recovery terminology
- [Steam Input JSON Structure](resources/Steam%20Input%20JSON%20Structure.md) - JSON format, binding execution order, and [interrupted delayed layer applies](resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies), including the repeating-removal workaround and RTP trackball-momentum exception
  - [Stuck layers and why there is so much cleanup](resources/Steam%20Input%20JSON%20Structure.md#stuck-layers-and-why-there-is-so-much-cleanup) - how the Steam button leaves layers active with no button held, and the chord-guarded cleanup pattern that recovers from it
  - [Cleanup scopes and concrete examples](resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) - overlays and inherited recovery, nine-layer Mod 2 branch cleanup, and eight-layer combined-cover cleanup that preserves the still-held side
  - [Stick-edge cleanup and inherited actions](resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions) - why edge recovery is selective: LS overrides the WASD modifier, RS overrides ramp-up
  - [Inheritance review for binding changes](resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) - trace effects through upper layers, protected timers, and stale stacks; the seven Double Tap LS-edge blocks are the worked example
- `Action Sets.md` - List of action set IDs
- `Layer Reverse Lookup.md` - Complete mapping of layer IDs to names

Detailed comparisons and runtime observations:

- [R1 and L1&R1 tap-cover findings](findings/2026-09-27-r1-tap-cover/FINDINGS.md)
- [Delayed-apply reset coverage audit](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md) - every delayed apply in both Neptune layouts, intentional exclusions, and proposed extensions within the three-command limit
- [Held inputs across layer changes](findings/2026-09-29-held-input-layer-transitions/AUDIT.md) - why adding a layer over a held input doesn't fire its layer commands (removal pass-through is unverified and backed by repeats), the ramp-up walkthrough, and which repeats and short delays exist because of it
- [Guarded recovery repeat convention](findings/2026-09-28-repeating-recovery/CHANGES.md) - the separate change enabling Hold to Repeat on every guarded recovery removal
- [Selected LS-edge recovery](findings/2026-09-28-left-stick-recovery/CHANGES.md) - fourteen recovery layers, seven timed-window blocks, and the approved Transition Set cleanup depth in both layouts
- [Stuck RTP entry layer blocking right-stick ramp-up](findings/2026-09-27-rtp-entry-ramp-up/FINDINGS.md)
- [Timer blocking and the Always On crash workaround](resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) — why unrelated layer changes are blocked, and why timed layers must be added last and removed first
- [Complete Neptune cleanup audit](findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) and [per-layer blocking audit](findings/2026-09-28-neptune-blocking-audit/AUDIT.md)

---

## Publishing layout changes

Every time a changed layout is published, **revalidate its description and bump
its release version**. Apply this before committing a layout update, exporting
it for delivery, or publishing it to Steam:

1. Read the full `controller_mappings.description` and compare it with the final
   layout. Check default/alternative controls, active features, response settings,
   and which features remain planned. Update stale text; do not rewrite accurate
   wording just to create a diff.
2. Increment the release suffix in `controller_mappings.title`, such as `90.2`
   to `90.3`, from the last published release. Use one bump for the release batch,
   including its follow-up edits and export; align both variants when released
   together. This is separate from schema `version`, export `revision`, and runtime
   layer IDs, which must not be changed for a release bump.
3. Complete command-budget, ordering, reference, and relevant regression checks.
   **Always regenerate the sibling VDF after every successful, validated JSON
   edit, in the same task.** This includes settings, bindings, title/version, and
   description changes. Export the final metadata with the layout so JSON and
   VDF agree; no separate export request or permission is needed. This standing
   instruction supersedes the earlier preference to leave VDFs to the user.
   Only a newer explicit instruction for the task can opt out. If conversion
   fails, report the blocker; do not claim the edit is complete. Local VDF export
   does not authorize a commit or Steam upload.
4. **Save a version snapshot after the export.** Copy each variant's final JSON
   and VDF into `versions/neptune/<version>/`, with `_latest` in the filename
   replaced by the version, such as
   `versions/neptune/90.4/single-set-default_hold-gyro_90.4.vdf`. `neptune/`
   remains the live working copy. Follow-up edits in the same release batch
   refresh that version's snapshot; snapshots of other versions are never
   changed. The `steam-layout-apply` skills have the copy command.
5. Keep manual Deck checks explicitly pending until performed. Committing JSON
   is not evidence of a successful Steam upload or runtime test.

Read-only audits and documentation-only changes do not publish a changed layout.
The `.claude` and `.cursor` `steam-layout-apply` skills enforce this workflow.

## File Formats

- `.json` - Human-readable format for editing with these scripts
- `.vdf` - Valve Data Format used by Steam

Export JSON directly using the serializer from the installed
`pfwobcke.vscode-vdf` VS Code extension:

```bash
node convert_vdf.mjs neptune/single-set-default_hold-gyro_latest.json
node convert_vdf.mjs neptune/single-set-alternative_hold-gyro_latest.json
node convert_vdf.mjs findings/2026-09-29-held-input-layer-transitions/rule-test.json
```

Each command writes/replaces the sibling `.vdf`, leaving the JSON intact. Use
`-o path/to/output.vdf` for a different destination. This requires Node.js with
`node:module.stripTypeScriptTypes` (tested on Node 26.7.0) and the installed
extension (tested on 5.12.3); no npm install or open VS Code window is needed.
It discovers the latest version under `~/.vscode/extensions`; use
`--extension /path/to/pfwobcke.vscode-vdf-version` for another location. The loader
uses the extension's bundled source map and reports an error if its structure
changes. Node may print an experimental API warning.

The exporter preserves repeated keys, binding order, and empty blocks, and checks
every output token before writing. It preserves existing VDF escape sequences
and escapes literal quotes, tabs, and line breaks introduced during JSON editing.
Like the extension, it uses JavaScript's JSON parsing and property order: use
arrays for repeated keys, and expect integer-like object keys in numeric order.
Unsupported values (including numbers, booleans, null, and empty arrays) and
unresolved `controller_action {{title}}` targets fail before writing.

Run the command-budget and layer-order checks before exporting, and use
`convert_runtime_ids.py to-ids` first when editing with title tokens. Fresh-load
Deck testing remains necessary. Converter tests: `node --test tests/test_convert_vdf.mjs`.

python3 convert_runtime_ids.py to-ids neptune/single-set-alternative_hold-gyro_latest.json &&
python3 convert_runtime_ids.py to-ids neptune/single-set-default_hold-gyro_latest.json

python3 convert_runtime_ids.py to-titles neptune/single-set-alternative_hold-gyro_latest.json &&
python3 convert_runtime_ids.py to-titles neptune/single-set-default_hold-gyro_latest.json


### Steering in the Neptune layouts

Both `neptune/*_hold-gyro_latest` JSON/VDF pairs now include the 16-layer steering
implementation (71 layers total), including scoped delayed-apply resets and
reused Mod 2 covers. Release 90.6 replaced its Long Press timers with chorded
delays, fixed the RTP scroll Long Press and pruned dead groups
([record](findings/2026-09-30-dead-group-prune/README.md)). Reinstall with
`findings/2026-09-30-steering-lean/install_neptune.py`, which repeats that cleanup. See the [implementation and exports](findings/2026-09-30-steering-lean/README.md),
[installation hashes and backups](findings/2026-09-30-steering-lean/neptune-installation.json),
and [pending Deck checks](findings/2026-09-30-steering-lean/ACCEPTANCE.md).
