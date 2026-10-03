# Tools

The command-line scripts are in `tools/`. Run them from the repo root, as
modules: `python3 -m tools.<name>`. The exporter is `node tools/convert_vdf.mjs`
([file formats](file-formats.md)).

| Tool | What it does | Writes |
|---|---|---|
| [`audit_build`](#build-audit-audit_build) | Runs the four audits on both working layouts. The gate for every version | Nothing |
| [`audit_command_budget`](#budget-audit-audit_command_budget) | Budget audit: three entries per input, no banned activators | Nothing |
| [`audit_inheritance`](#window-audit-audit_inheritance) | Window audit: what an Always On layer inherits, and whether it is blocked | Nothing |
| [`audit_flow_inheritance`](#flow-audit-audit_flow_inheritance) | Flow audit: covers, coverage, entries to review | Nothing |
| [`audit_cleanups`](#cleanup-audit-audit_cleanups) | Cleanup audit: what cleanups and releases remove | Nothing |
| [`audit_layer`](#layer-report-audit_layer) | Report on one layer: below, above, inherited, exits | Nothing |
| [`change_report`](#change-report-change_report) | What differs between two layouts | Only with `--out` |
| [`convert_runtime_ids`](#convert_runtime_ids-ids-and-titles) | Numeric runtime IDs to `{{Base::Title}}` tokens and back | The layout |
| [`duplicate_layer`](#duplicate_layer-copy-a-layer) | Copies a layer without shifting any ID | The layout, and a backup |
| [`delete_action_set_complete`](#delete_action_set_complete-delete-an-action-set) | Deletes an action set and remaps the IDs that shift | The layout, and a backup |
| [`prune_dead_groups`](#budget-audit-audit_command_budget) | Removes unreferenced groups and inactive slots | The layout |
| [`id_replacement/`](#id_replacement-remap-from-an-explicit-table) | Applies an explicit old → new ID table | A new file |

The skills in [`skills/`](../skills/README.md) wrap these in the order an edit needs them.

## Audits

### Build audit: `audit_build`

The gate for every version. It runs the Budget audit
(`audit_command_budget.py`), the Window audit (`audit_inheritance.py`), the
Flow audit (`audit_flow_inheritance.py`) and the Cleanup audit
(`audit_cleanups.py`) on both working layouts, prints one line per audit and
exits **0** only when all pass. Read-only, about ten seconds. See [Layer Definition of Done §10](../resources/Layer%20Definition%20of%20Done.md#10-ship-it).

```bash
python3 -m tools.audit_build              # both neptune/*_latest.json
python3 -m tools.audit_build --verbose    # also print each failing audit's output
```

### Budget audit: `audit_command_budget`

**Rule: R109** ([Layer Definition of Done §3](../resources/Layer%20Definition%20of%20Done.md#3-activators)).
This section explains it; the rule text is there.

Every input in these layouts must have **at most three GUI command entries**.
Count each activator object across all activation types, including every element
of a repeated `chord` or `Soft_Press` list. A `bindings.binding` array is
subcommands inside one entry, so its length does not count against this limit.
This is the layout author's requirement, confirmed on 2026-09-27. It exists
because Steam's desktop configuration drops every entry after the third. The one
allowed exception is a delayed-apply reset as a **last** 4th entry, which is the
entry desktop drops; see [the exception](../resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget).

```bash
python3 -m tools.audit_command_budget neptune/single-set-default_hold-gyro_latest.json neptune/single-set-alternative_hold-gyro_latest.json
```

The read-only checker scans all groups, including inactive, mode-shift, and
unreferenced groups. It checks disabled activator banks separately. Add `--json`
for a complete input inventory, counts, owners, and exact violation paths.
Exit codes: **0** = pass (allowed 4th-entry resets are listed, not failed), **1** = over budget or a banned activator, **2** = invalid input/schema.
Run it before finalizing edited layouts; it accepts numeric IDs or title tokens.

The same audit fails on **Long Press** and **Double Press**, which misbehave
with Steam's layer API (see [allowed activation types](../resources/Steam%20Input%20JSON%20Structure.md#allowed-activation-types)),
and reports unreferenced groups and plain-inactive slots. To remove dead groups
(unreferenced groups and plain-inactive source slots; active, mode-shift and
mode-shift-target groups are kept, and no ID is renumbered):

```bash
python3 -m tools.prune_dead_groups --dry-run neptune/*_latest.json   # report only
python3 -m tools.prune_dead_groups neptune/*_latest.json
```

The baseline 90.1 [audit](../findings/2026-09-27-neptune-command-budget/AUDIT.md) found one
violation in each variant: Base's right-stick edge has seven command entries.
The [consolidation plan](../plans/2026-09-27-neptune-command-budget.md) has now been
applied to both JSON files: each edge has three entries using two multi-button
Any chords, and the full command-budget checks pass. The
[implementation record](../findings/2026-09-27-neptune-command-budget/IMPLEMENTATION.md)
tracks the results. Both 90.4 JSONs and regenerated VDFs include the cursor tuning and hold-entry haptic
and refreshed descriptions; export verification passes. That Steam loads an
exported VDF as written is assumption A33 in
[Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md):
reported, with no fresh-load check on record.
See [counting and chord rules](../resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget).

### Window audit: `audit_inheritance`

For each Always On layer (and any layer named in `steam_layout/traced_stacks.json`), works
out the stacks it can sit on and checks whether any of them puts a layer
command under an input the layer leaves open. Each such route must be blocked,
or be an exception to R140 in the
[exceptions register](../resources/Layer%20Definition%20of%20Done.md#exceptions-register). The tool recommends the
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
See [Layer Definition of Done §8](../resources/Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)
and the [record](../findings/2026-10-01-backward-chain-stacks/README.md).

```bash
python3 -m tools.audit_inheritance neptune/single-set-default_hold-gyro_latest.json
python3 -m tools.audit_inheritance neptune/single-set-default_hold-gyro_latest.json --entries "RTP: Double Tap"
python3 -m tools.audit_inheritance neptune/single-set-default_hold-gyro_latest.json --untraced   # review list
```

### Layer report: `audit_layer`

Answers the three stack questions for one layer, from the same backward
chains: what can be below it and above it, which inputs it inherits and from
which layer, and, for each of its bindings that removes layers, what it
removes that is present, what is present and left, and what it removes that is
never there. The exits section is a list for review, not a check. Takes about
two seconds. Read-only. Exit codes: **0** = report printed, **2** = invalid
input or unknown layer.

```bash
python3 -m tools.audit_layer neptune/single-set-default_hold-gyro_latest.json --layer "L1: Modifier 0"
python3 -m tools.audit_layer <layout> --layer "Menu Right: Fn Layer" --json
```

### Flow audit: `audit_flow_inheritance`

For every layer the backward chains reach, reports the stacks that can be
under it, each with the bindings that built it, and what each input inherits
on those stacks. It fails on three things:

- **A cover finding:** a cover that outlives its owners, sits below its
  owner, or inherits an input through a layer between it and its owner.
- **A coverage gap:** a layer no chain of adding bindings reaches, or a
  lookup the chains can't model.
- **An entry to review (R139):** an inherited binding that differs between
  stacks, on a layer that changed since the newest snapshot or that a changed
  layer feeds. Fix it, or accept it in the exceptions register with a reason.
  On unchanged layers these are listed as information.

The chains start from the contexts in `steam_layout/flow_config.json` (Base,
and Base with `Gyro`) and keep each chain to its own layers, so a cover is
judged with its own family. Nothing else is declared: a new layer is picked
up from the layout. Runs in about 0.1 s per variant. Read-only. Exit codes:
**0** = clean, **1** = cover findings or coverage gaps, **2** = invalid input.
Until 2026-10-01 it walked families declared in the rules; see the
[deprecation record](../findings/2026-10-01-backward-chain-stacks/README.md#deprecated).

```bash
python3 -m tools.audit_flow_inheritance neptune/single-set-default_hold-gyro_latest.json
python3 -m tools.audit_flow_inheritance <layout> --layer 'L1: Tap Cover'               # stacks, bindings, layers above
python3 -m tools.audit_flow_inheritance <layout> --inventory --layer 'L1: Modifier 0'  # what the chains follow
```

### Cleanup audit: `audit_cleanups`

Checks every cleanup function and release against the six cleanup rules: a
layer takes care of itself and what is below it, and of what is above it if it
has that responsibility
([rules](../findings/2026-10-02-cleanup-boundaries/README.md#the-rules)), and
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
resolves its findings ([first run and fix](../findings/2026-10-02-cleanup-audit/README.md)).
About two seconds.
Read-only. Exit codes: **0** = clean, **1** = findings, **2** = invalid input.

```bash
python3 -m tools.audit_cleanups neptune/single-set-default_hold-gyro_latest.json
python3 -m tools.audit_cleanups <layout> --layer "L1: Modifier 0"
python3 -m tools.audit_cleanups <layout> --check "never there" --json
```

### Change report: `change_report`

Compares two layouts by layer and input: mode, settings and each input's
activators, with layer commands compared by title so a shifted runtime ID is
not a change. With no arguments it compares each working layout with its
newest snapshot under `versions/neptune/`. Read it before shipping (rule R164):
a fix or a builder can change a binding nobody decided, and this is where it
shows. It is a report, not a check.

```bash
python3 -m tools.change_report                                   # working layouts against their newest snapshots
python3 -m tools.change_report BEFORE.json AFTER.json            # any two layouts
python3 -m tools.change_report --out findings/<date>-<slug>/     # also write <name>-changes.txt there
```

## Editing scripts

### `convert_runtime_ids`: IDs and titles

Converts between numeric runtime IDs and human-readable titles in `controller_action` commands. Makes layouts easier to read and edit manually.

**Use Cases:**
- Make a layout human-readable for manual editing
- Debug which layers are being activated by `controller_action` commands
- Convert back to numeric IDs before using the layout in Steam

**Usage:**

```bash
# Convert numeric IDs to readable titles
# e.g., "controller_action add_layer 5 0 0" -> "controller_action add_layer {{L2}} 0 0"
python3 -m tools.convert_runtime_ids to-titles layout.json

# Convert titles back to numeric IDs
# e.g., "controller_action add_layer {{L2}} 0 0" -> "controller_action add_layer 5 0 0"
python3 -m tools.convert_runtime_ids to-ids layout.json

# Output to a different file instead of modifying in-place
python3 -m tools.convert_runtime_ids to-titles layout.json --output readable_layout.json
```

**Title Format:**
- Action sets: `{{Base}}`, `{{Gyro}}`
- Action layers: `{{Base::L2}}`, `{{Base::RST: Temporary Gyro}}`

The `Parent::Title` format for layers ensures unique identification when multiple sets have layers with the same name.

### `duplicate_layer`: copy a layer

Duplicates an action layer along with all its children relationships (groups, bindings, etc.). The duplicated layer is added to the **end** of `action_layers` to preserve runtime ID ordering.

**Use Cases:**
- Create a variant of an existing layer with different bindings
- Clone a complex layer as a starting point for a new one
- Back up a layer before making experimental changes

**Usage:**

```bash
# List all available layers in a layout
python3 -m tools.duplicate_layer layout.json --list

# Duplicate a layer (auto-generates title with " (Copy)" suffix)
python3 -m tools.duplicate_layer layout.json Preset_1000006

# Duplicate with a custom title
python3 -m tools.duplicate_layer layout.json Preset_1000006 "My Custom Layer"

# Output to a different file instead of modifying in-place
python3 -m tools.duplicate_layer layout.json Preset_1000006 --output new_layout.json

# Skip creating a backup file
python3 -m tools.duplicate_layer layout.json Preset_1000006 --no-backup
```

**What gets duplicated:**
- The layer definition in `action_layers`
- All groups referenced in `group_source_bindings`
- The preset entry with updated group references

**Important:** The new layer gets a new runtime ID (appended to the end), so existing `controller_action` commands remain unaffected.

### `delete_action_set_complete`: delete an action set

Deletes an entire action set and **all** its associations from a layout file. This includes child layers, presets, groups, and automatically updates all `controller_action` runtime ID references.

**Use Cases:**
- Remove an unused action set (e.g., "Gyro" or "Gamepad" mode)
- Clean up a layout by removing experimental sets
- Reduce layout complexity

**Usage:**

```bash
python3 -m tools.delete_action_set_complete layout.json Preset_1000014
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

The working layouts have one action set, so this is for older multi-set
layouts and imports. It rewrites numeric IDs: run it on a file in numeric form.

### `id_replacement/`: remap from an explicit table

`tools/id_replacement/replace_layer_ids_flexible.py` rewrites the numeric ID of
every `add_layer`, `remove_layer` and `hold_layer` command from a JSON table of
`old_id` and `new_id`, in two passes so that no ID is replaced twice. It is for
a numeric file whose layers were reordered without remapping, or a deliberate
migration. Day-to-day editing uses title tokens and needs no remapping.

```bash
python3 tools/id_replacement/replace_layer_ids_flexible.py -i layout.json -m mapping.json --dry-run
python3 tools/id_replacement/replace_layer_ids_flexible.py -i layout.json -m mapping.json -o layout_updated.json
```

The folder's own notes and its `old_to_new_ids.json` are from the April
migration and don't describe the current layouts.

## The library: `steam_layout/`

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

**Deprecated tooling is in [archived/](../archived/README.md):** the exhaustive
stack search and timed proofs (2026-09-30), and the depth-limited search and
family walk (2026-10-01). Nothing live imports them. Their records stay in
[findings/2026-09-30-stack-search](../findings/2026-09-30-stack-search/ARCHIVE.md)
and [findings/2026-10-01-backward-chain-stacks](../findings/2026-10-01-backward-chain-stacks/README.md#deprecated).

## Running the tests

```bash
PYTHONPATH=.:tests python3 -m unittest $(ls tests/test_*.py | sed 's#/#.#; s#\.py$##' | tr '\n' ' ')
node --test tests/test_convert_vdf.mjs
```

The first command runs every Python test: 627 at release 90.19, in about five
minutes. `tests/` has to be on the path because four test modules import a
sibling by its bare name, and `python3 -m unittest discover` does not work
here. One module: `PYTHONPATH=.:tests python3 -m unittest tests.test_rule_registry`.

`python3 -m tests.scenario` lists the press-by-press scenario tests and which
of them rest on an unverified Steam assumption.
