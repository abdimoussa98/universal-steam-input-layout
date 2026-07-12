# Finding: Steam Input swaps action layers on load when layer list order diverges from Preset numbering

- **Date:** 2026-07-11
- **Layout:** `single-set-default :: always-gyro :: example` (revision 14001, `controller_triton`, export_type `personal_local`)
- **Files:**
  - `MOST_RECENT_LAYOUT.pre-fix.json` — exact snapshot of the layout as exported from Steam, before the fix
  - `MOST_RECENT_LAYOUT.post-fix.json` — snapshot after the fix
  - Repo working copy fixed in place: `../../MOST_RECENT_LAYOUT.json`

## Symptom

The layout was built and working in the Steam Input GUI. On a fresh load of the exported VDF
into Steam, action layers were silently swapped on multiple bindings. Most visibly: the Base
set right-joystick **outer edge** bind, which is supposed to add **"Gyro Off Ramp Up"**,
instead added **"Split Stick"**. Other layer bindings were also mis-targeted with no obvious
pattern.

## Root cause

A Steam Input layout file carries **two implicit layer orderings**:

1. **List order** — the order the layer blocks appear in `action_layers` (and the matching
   `preset` blocks). This is the order the GUI displays.
2. **Numeric key order** — the order of the `Preset_10000XX` numeric keys (creation /
   renumbering order).

`controller_action add_layer / remove_layer / hold_layer / CHANGE_PRESET` commands reference
action sets and layers **positionally** (runtime ID 1..N), not by Preset key. When the two
orderings agree, the positional references are unambiguous. In this layout they diverged in
exactly one place — four layers at runtime positions 53–56:

| runtime ID | list order (what the binds meant) | numeric key order (what Steam resolved on load) |
|---|---|---|
| 53 | Gyro Off Ramp Up (`Preset_1000057`) | Split Stick (`Preset_1000055`) |
| 54 | Gated Gyro (`Preset_1000058`) | Split Stick Fallback (`Preset_1000056`) |
| 55 | Split Stick (`Preset_1000055`) | Gyro Off Ramp Up (`Preset_1000057`) |
| 56 | Split Stick Fallback (`Preset_1000056`) | Gated Gyro (`Preset_1000058`) |

The saved binding runtime IDs reflected **list order**, but on load Steam resolved them in
**numeric key order**, producing exactly two pair-swaps:

- **Split Stick ↔ Gyro Off Ramp Up** (the observed outer-edge swap)
- **Split Stick Fallback ↔ Gated Gyro** (the "other" unexplained swaps)

No other layer in the file could be affected — everywhere else the two orderings agree.
Blast radius: **43 bindings** reference the four layers (19× Gyro Off Ramp Up,
15× Split Stick Fallback, 7× Split Stick, 2× Gated Gyro); every one of them retargeted
on load.

### How the divergence was introduced

The Preset keys are contiguous (`1000004`–`1000061`), meaning Steam renumbered all presets
at some point in list order — immediately after that renumbering, key order and list order
matched by construction. For `1000057`/`1000058` to end up *above* `1000055`/`1000056` in the
list, the layer list must have been **reordered in the GUI afterwards** (dragging
"Gyro Off Ramp Up"/"Gated Gyro" above the Split Stick layers, or the GUI inserting newly
created layers mid-list while numbering them max+1).

Inside a live editing session everything is handle-based in memory, so the layout keeps
working no matter how the list is ordered. The corruption only surfaces on the next **fresh
load** of the VDF, when Steam re-derives positional runtime IDs — this is why the layout
"always worked before" and broke only on reload.

Note: older layouts in this repo (`neptune/*`, April 2026, Steam Deck) have wildly
non-numeric list order and loaded correctly, so the key-order resolution on load appears to
be device- or client-path-dependent (this layout is `controller_triton`). Regardless of which
side Steam picks, a file where both orderings agree cannot be misread — hence the fix below.

## How the two orderings were identified

The "numeric key order" interpretation was **not prior knowledge** — no documentation
(Valve's or this repo's) describes it. This repo's docs only state the *list order* rule
("runtime IDs are assigned by order of appearance"). The second ordering was **inferred by
differential diagnosis**: it is the only enumeration of the layers that reproduces the
observed in-game behavior.

1. **The anomaly:** a structural audit showed `action_layers` keys ascending everywhere
   except one 4-layer window (`1000057, 1000058, 1000055, 1000056`) — and two of those four
   were exactly the layers reported swapped. One anomaly, co-located with the symptom.
2. **Candidate enumerations:** for Steam to resolve a positional runtime ID like `53`, it
   must walk the layers in *some* order. The plausible candidates in the file:
   - (a) **list order** (the documented rule) → ID 53 = Gyro Off Ramp Up. This predicts *no
     swap at all* (the file is self-consistent under list order) — contradicted by what was
     observed in Steam.
   - (b) **preset `id` field order** → the `id` fields are sequential in list order in this
     file, so identical to (a) — also contradicted.
   - (c) **numeric `Preset_` key order** (equivalently lexicographic, since keys are
     same-width; equivalently creation/renumbering order) → ID 53 = Split Stick — **matches
     the observed swap exactly.**
3. **Falsifiable cross-check:** hypothesis (c) predicts *exactly one* additional swapped
   pair (Gated Gyro ↔ Split Stick Fallback) and **zero** effects on any other layer — which
   matched the report of "a few other layers" swapping rather than layout-wide chaos.
4. **Supporting evidence that key order is a real internal ordering:** the keys are
   contiguous (`1000004`–`1000061`), proving Steam renumbers presets in list order at some
   point. Numeric key order is therefore a frozen snapshot of a *past* list order — a
   natural sequence for a loader to walk (e.g. an internal map keyed by preset number).
5. **Counter-evidence, handled:** the April `neptune/*` layouts have wildly non-numeric list
   order and always loaded correctly, so key-order resolution is not universal — it appears
   client- or device-path-dependent (`controller_triton` here vs. `neptune`). That is why the
   fix makes the two orderings *agree* instead of betting on either one: a file where they
   match cannot be misread by any loader.

### Audit results (everything else was clean)

- `preset` block `id` fields: sequential 0–58, matching block order ✓
- `preset` block name order: matches `actions` + `action_layers` order ✓ (i.e. presets shared
  the same divergence, consistently)
- Group IDs: 421 groups, no duplicates, no orphans, no dangling `group_source_bindings` ✓
- Preset key gap `1000001 → 1000004`: leftover from old deletions, harmless
- **Hazard (unrelated to this bug):** two layers are both titled `DEPRECATED`
  (`Preset_1000015`, `Preset_1000016`). Steam doesn't care (it uses IDs), but any name-based
  tooling — including this repo's `convert_runtime_ids.py to-ids` — will resolve both
  `{{Base::DEPRECATED}}` tokens to the *later* layer. There are live `add_layer
  {{Base::DEPRECATED}}` bindings, so rename these layers uniquely before relying on
  title-token round-trips.

## Resolution

Eliminate the ambiguity by making list order match numeric key order, so positional runtime
IDs resolve identically under either interpretation. Applied to `MOST_RECENT_LAYOUT.json`
(which is in `{{title}}` token form, so binding intent is preserved by name):

1. **Reordered `action_layers`** into numeric key order — only four entries moved:
   positions 52–55 (0-based 51–54) changed from
   `1000057, 1000058, 1000055, 1000056` → `1000055, 1000056, 1000057, 1000058`.
2. **Reordered the four matching `preset` blocks** the same way and **resequenced all preset
   `id` fields** to 0..58 so they stay aligned with block position.
3. Bindings were left as `{{Base::...}}` title tokens — converting titles → IDs after the
   reorder yields runtime IDs that are correct under both list order and key order.

Verified after the fix:

- list order == numeric key order for all 59 presets ✓
- preset block order matches, `id` fields sequential ✓
- content otherwise byte-identical to the pre-fix snapshot (only the four blocks moved and
  preset `id`s resequenced) ✓

### To finalize for Steam

1. `python3 convert_runtime_ids.py to-ids MOST_RECENT_LAYOUT.json` (titles → numeric runtime IDs)
2. Convert JSON → VDF (VSCode extension `pfwobcke.vscode-vdf`)
3. Load into Steam and spot-check the four layers, especially:
   - Base set, right joystick, outer edge Full Press → must add **Gyro Off Ramp Up**
   - Split Stick Fallback joystick edge binds → must toggle **Split Stick / Split Stick Fallback**

### Guardrail for the future

After any GUI session where layers were added or reordered, re-export and check that
`action_layers` appears in `Preset_` numeric order. If it doesn't, normalize the order
(as above) before treating positional runtime IDs as trustworthy.

## Tooling / provenance

- **Model:** Claude Fable 5 (`claude-fable-5`), Anthropic — via Claude Code (background session)
- **Method:** static analysis of the exported layout JSON only; no conversion scripts were
  implicated. The divergence was found by comparing the file's two implicit orderings and
  confirming the predicted swap pairs matched the observed in-game behavior.

### Prompts given (verbatim)

**Prompt 1 (initial report):**

> take a look at this layout /Users/abdi/Documents/codes/universal-steam-input-layout/MOST_RECENT_LAYOUT.json, when i load this into steam as vdf for some reason the layers are being swapped around. the "Split Stick" and "Gyro Off Ramp Up" were being swapped on the joystick outer edge bind for some reason. THere were other layers that were swapped be i dont understand why this is happening. This was always working before

**Prompt 2 (mid-investigation redirect):**

> this has nothing to do with with the conversion scripts. This layout was built in steam input gui and i've just been analyzing this in this repo. So i want you to find patterns into how steam input could fail to properly load this

**Prompt 3 (documentation request):**

> before you do this document these finding and save this most recent layout with it and you preposed fix in it that documentation. I want to document this find and how you resolved this. Also include the info of which model was used to fix this and the prompts that were given

**Prompt 4 (doc propagation + methodology request):**

> Ok i want you to update any documentation that is relavant with these findigns and also as a part of the findings document. mention how you knew the of the two different types of runtime ids (list order vs numeric key order) since i never knew about the numeric key ordering being a thing
