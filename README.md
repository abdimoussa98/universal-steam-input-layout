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

### Build audit: `audit_build.py`

The gate for every version. It runs the Budget audit
(`audit_command_budget.py`), the Window audit (`audit_inheritance.py`), the
Flow audit (`audit_flow_inheritance.py`) and the Cleanup audit
(`audit_cleanups.py`) on both working layouts, prints one line per audit and
exits **0** only when all pass. Read-only, about ten seconds. See [Layer Definition of Done §10](resources/Layer%20Definition%20of%20Done.md#10-ship-it).

```bash
python3 audit_build.py              # both neptune/*_latest.json
python3 audit_build.py --verbose    # also print each failing audit's output
```

### 4. `audit_inheritance.py` - Window Audit (Inheritance and Blocking Check)

For each Always On layer (and any layer named in `traced_stacks.json`), works
out the stacks it can sit on and checks whether any of them puts a layer
command under an input the layer leaves open. Each such route must be blocked,
or be an exception to R140 in the
[exceptions register](resources/Layer%20Definition%20of%20Done.md#exceptions-register). The tool recommends the
block: replace with the underlying output if it's identical in every stack,
otherwise clear.

The stacks come from **backward chains** (`steam_layout/chains.py`): start at
the layer, ask which bindings add it, then which add those layers, back to
Base. Other layers that leave the chain's inputs alone are placed underneath
as bystanders. There is no depth cap and no config, and each open route is
printed with the bindings that built its stack. A layer no stack reaches is
"not checked", which fails. Runs in under a second per layout. Read-only. Exit codes:
**0** = pass, **1** = undecided route or unchecked layer, **2** = invalid
input.
See [Layer Definition of Done §8](resources/Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)
and the [record](findings/2026-10-01-backward-chain-stacks/README.md).

```bash
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json --entries "RTP: Double Tap"
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json --untraced   # review list
```

### 4a. `audit_layer.py` - Layer Report (Below, Above, Inherited, Exits)

Answers the three stack questions for one layer, from the same backward
chains: what can be below it and above it, which inputs it inherits and from
which layer, and, for each of its bindings that removes layers, what it
removes that is present, what is present and left, and what it removes that is
never there. The exits section is a list for review, not a check. Takes about
two seconds. Read-only. Exit codes: **0** = report printed, **2** = invalid
input or unknown layer.

```bash
python3 audit_layer.py neptune/single-set-default_hold-gyro_latest.json --layer "L1: Modifier 0"
python3 audit_layer.py <layout> --layer "Menu Right: Fn Layer" --json
```

### 4b. `audit_flow_inheritance.py` - Flow Audit (Cover Check and Coverage)

For every layer the backward chains reach, reports the stacks that can be
under it, each with the bindings that built it, and what each input inherits
on those stacks. Inherited bindings that differ between stacks are listed as
information only. It fails on two things:

- **A cover finding:** a cover that outlives its owners, sits below its
  owner, or inherits an input through a layer between it and its owner.
- **A coverage gap:** a layer no chain of adding bindings reaches, or a
  lookup the chains can't model.

The chains start from the contexts in `steam_layout/flow_config.json` (Base,
and Base with `Gyro`) and keep each chain to its own layers, so a cover is
judged with its own family. Nothing else is declared: a new layer is picked
up from the layout. Runs in about 0.1 s per variant. Read-only. Exit codes:
**0** = clean, **1** = cover findings or coverage gaps, **2** = invalid input.
Until 2026-10-01 it walked families declared in the rules; see the
[deprecation record](findings/2026-10-01-backward-chain-stacks/README.md#deprecated).

```bash
python3 audit_flow_inheritance.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_flow_inheritance.py <layout> --layer 'L1: Tap Cover'               # stacks, bindings, layers above
python3 audit_flow_inheritance.py <layout> --inventory --layer 'L1: Modifier 0'  # what the chains follow
```

### 4c. `audit_cleanups.py` - Cleanup Audit (What Cleanups and Releases Remove)

Checks every cleanup function and release against the six cleanup rules: a
layer takes care of itself and what is below it, and of what is above it if it
has that responsibility
([rules](findings/2026-10-02-cleanup-boundaries/README.md#the-rules)), and
checks that no layer hides another's exit (R136). It fails on seven things:

| Check | Fails when |
|---|---|
| Outside the guard | A cleanup removes a layer kept by another button, a stateful layer, a stick-touch helper or a window |
| Left below | A layer under the host has the same keeper and isn't removed |
| Left above | A layer on top has the same keeper, leaves the cleanup's input alone, and isn't removed |
| Hidden cleanup | A layer binds an input that has a cleanup below without carrying it |
| Never there | A cleanup, a release or a Modifier 2 quick tap removes a layer that can never be on the stack with it |
| Guard mismatch | One layer's cleanups have different guard buttons |
| Hidden exit | A layer that can land on top of another covers an exit on what keeps the lower layer alive, and doesn't remove it there |

The stacks are the backward chains. Deliberate clears and the stick-touch
release's fixed layers are exempt from "Never there", and layers that only
`hold_layer` adds are left out. A removal that is kept on purpose is an
exception to R132 in the exceptions register (`steam_layout/flow_config.json`),
with a reason. Part of
the build audit since 90.12; the `cleanup_lists` step of the fix pipeline
resolves its findings ([first run and fix](findings/2026-10-02-cleanup-audit/README.md)).
About two seconds.
Read-only. Exit codes: **0** = clean, **1** = findings, **2** = invalid input.

```bash
python3 audit_cleanups.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_cleanups.py <layout> --layer "L1: Modifier 0"
python3 audit_cleanups.py <layout> --check "never there" --json
```

### 4d. `change_report.py` - Change Report (What Differs Between Two Layouts)

Compares two layouts by layer and input: mode, settings and each input's
activators, with layer commands compared by title so a shifted runtime ID is
not a change. With no arguments it compares each working layout with its
newest snapshot under `versions/neptune/`. Read it before shipping (rule R164):
a fix or a builder can change a binding nobody decided, and this is where it
shows. It is a report, not a check.

```bash
python3 change_report.py                                   # working layouts against their newest snapshots
python3 change_report.py BEFORE.json AFTER.json            # any two layouts
python3 change_report.py --out findings/<date>-<slug>/     # also write <name>-changes.txt there
```

### 5. `steam_layout/` - Shared Library and Fix Pipeline

The reusable code behind the scripts above. Import it from the repo root.

| Module | Use it for |
|---|---|
| `steam_layout.model` | Read a layout (numeric IDs or title tokens): layer titles, active groups per source, bindings in execution order, Always On layers |
| `steam_layout.chains` | `Chains`: the stacks under a layer from backward chains (who adds it, back to Base, plus bystanders), each with its reason; `below`, `above`, `lineage`, `reached` |
| `steam_layout.layer_report` | The per-layer report that `audit_layer.py` wraps |
| `steam_layout.covers` | The cover check on chains, and the rules loader for `flow_config.json` |
| `steam_layout.cleanups` | `Cleanups`: guard and keeper of every layer, and the six cleanup checks that `audit_cleanups.py` wraps |
| `steam_layout.flow_model`, `steam_layout.flow_inheritance` | Every layer-changing binding, classified by role, and what a layer inherits on each lower stack |
| `steam_layout.inheritance` | The inheritance and blocking audit that `audit_inheritance.py` wraps |
| `steam_layout.stacks` | `apply_ops`, `definer` and `effective_input`, which the chains build on, and `walk` / `fire` to replay one concrete input sequence |
| `steam_layout.fixes` | The ordered, idempotent post-install fixes that `install_neptune.py` runs, including `cleanup_lists`, which resolves every Cleanup audit finding |

```bash
python3 -m steam_layout.fixes neptune/*_latest.json --dry-run   # what the pipeline would change
```

**Deprecated tooling is in [archived/](archived/README.md):** the exhaustive
stack search and timed proofs (2026-09-30), and the depth-limited search and
family walk (2026-10-01). Nothing live imports them. Their records stay in
[findings/2026-09-30-stack-search](findings/2026-09-30-stack-search/ARCHIVE.md)
and [findings/2026-10-01-backward-chain-stacks](findings/2026-10-01-backward-chain-stacks/README.md#deprecated).

## Command entry limit and audit

**Rule: R109** ([Layer Definition of Done §3](resources/Layer%20Definition%20of%20Done.md#3-activators)).
This section explains it; the rule text is there.

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
- [Stateful Layer Transitions](resources/Stateful%20Layer%20Transitions.md) - the menu-plus-stick-click gesture map, Entry Points, stick guards and transition layers every stateful layer goes through (agreed design, not built yet)
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

Both `neptune/*_hold-gyro_latest` JSON/VDF pairs are generated (71 layers
since 90.11). The builder in `findings/2026-10-02-steering-fallback-hold/`
extends the frozen 10-01 stateful transitions builder, which extends the
09-30 lean steering builder and the 09-29 baseline; `install_neptune.py`
there runs the fix pipeline and writes `neptune/`. A hand edit in `neptune/`
is lost on the next install. See the
[90.11 build record](findings/2026-10-02-steering-fallback-hold/README.md),
the [90.10 build record](findings/2026-10-01-stateful-transitions/README.md),
the earlier [lean steering record](findings/2026-09-30-steering-lean/README.md)
and the [Deck checks](manual-testing.md#9011-steering-fallback-hold).
