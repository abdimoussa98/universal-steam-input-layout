## Skill: Prep a Steam Input layout for editing (VDF → JSON → readable titles)

### When to use
- You’re about to edit a Steam Input layout from this repo.
- You see lots of `controller_action add_layer 32 0 0` style numeric runtime IDs and want it readable.
- You’ve exported or copied a `.vdf` template and need to get to an editable JSON workflow.

### Prereqs / constraints
- **You must start from a JSON layout file** (this repo’s scripts expect JSON).
- **VDF ↔ JSON conversion is external**: use the VSCode extension `pfwobcke.vscode-vdf` to convert a `.vdf` layout to `.json` before running any scripts here.
- Runtime IDs are assigned by **order of appearance**: action sets first (`controller_mappings.actions`), then layers (`controller_mappings.action_layers`). Reordering those blocks will shift IDs.

### Steps
1. **Convert VDF to JSON (external)**
   - In VSCode, use the VDF extension (`pfwobcke.vscode-vdf`) to convert your `*.vdf` to `*.json`.
   - Keep the original `.vdf` around; treat it as the “source export”.

2. **Make the JSON readable (IDs → titles)**
   - Run:
     - `python3 convert_runtime_ids.py to-titles path/to/layout.json`
   - Or write to a separate file:
     - `python3 convert_runtime_ids.py to-titles path/to/layout.json --output path/to/layout_readable.json`

3. **Confirm the title token format**
   - Action sets appear as `{{Base}}`, `{{Gyro}}`, etc.
   - Layers appear as `{{Base::L2}}`, `{{Base::RST: Temporary Gyro}}`, etc.
   - If you see `{{Parent::Title}}`, that’s intentional: it disambiguates duplicate layer names across sets.

### Guardrails
- Trace inheritance beyond the edited layer: identify lower bindings it exposes and upper layers that can inherit changed inputs/sources, including timed windows and plausible stale stacks. Resolve active groups, mode shifts, settings, and actual application order; omission is not a block, and GUI order is not the runtime stack. Follow the [inheritance review](../../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) before treating a change as local.
- Keep gyro overrides scoped: Base owns normal response settings. Gyro and LST/RST activation layers change only selector/Any-All fields; cursor overlays change only response properties and remove themselves on cancellation. Normal Tap Covers and ordinary modifier parents inherit response without an active gyro source. Preserve intentional active `disabled` gyro modes. See [gyro settings inheritance](../../../resources/Steam%20Input%20JSON%20Structure.md#gyro-settings-inheritance).
- Trace cursor cancellation through the lower input: a cursor-local repeating self-removal exposes the parent's output and repeating cover/Mod 2 transition; do not duplicate outputs inside that removal. The two ordinary output/cover chords are both uninterruptible, while their repeating family fallback stays interruptible. Cursor inherits touch-release completion; normal covers replace it with cleanup only to prevent re-entry. Review RTP Double Tap's explicit face/D-pad/click blocks before allowing these mutations through a timed window. See [the exact convention](../../../resources/Steam%20Input%20JSON%20Structure.md#cursor-cancellation-and-repeating-cover-chords).
- Classify cleanup before comparing it: guarded recovery uses an owner-held chord and an interruptible Regular Press removal on the same input, with Hold to Repeat required on every guarded recovery removal. Inspect interruption settings as well as sibling chords. Release/expiry/threshold exits and uninterruptible delayed-apply resets have different shapes. See [the recovery structure](../../../resources/Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape) and [overlay ownership](../../../resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership).
- Recognize touch-release completion paths: a stick-touch release may intentionally apply the pending delayed target before clearing its LST/RST helpers, preventing those removals from postponing the apply. Audit it alongside the primary delay and the upper cover's replacement touch input; add-before-removal is not an ordering defect by itself. See [the documented pattern](../../../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release).
- Check held inputs across layer changes: a layer added over a held input does not fire its immediate layer command on that input. Its delayed and repeating activators still fire. Removing a layer fires the newly exposed lower binding on a held input. Short delays (such as `Gyro Off Ramp Up`'s 5 ms), repeating adds outside Base, and repeating threshold exits often exist for this reason, not for timing; don't strip or "normalize" them. When adding a removal, trace what it exposes on inputs that may still be held. See [held inputs across layer changes](../../../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes).
- Menu gyro suppression and Escape/Tab edge blocks are confirmed design choices. The author does not use Start/Select menu interactions during gameplay, so WASD modifiers and ramp-up need not remain available there; do not reopen these overrides as defects merely because the layers are overlays.
- Unequal LS/RS edge coverage is not automatically a defect. Edge cleanup displaces the LS WASD modifier or RS ramp-up; add it only where the recovery need justifies that loss. Ramp-up has extra layer API/timer constraints, so more frequent RS blocking is expected. See [the documented tradeoff](../../../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions).
- Identify who owns recovery and what an exit intentionally preserves. Overlays can inherit the underlying cleanup and keep a local release exit; release-only behavior or a shorter current-branch list is not automatically a defect. Compare intended inheritance with actual gyro/edge overrides. See [cleanup scopes and examples](../../../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples).
- Audit explicit empty bindings, active disabled source modes, chord guards, and replacement outputs separately; empty input objects and inactive groups are not proven blocks. Identify active `always_on_action` layers and verify add-last entry / remove-self-first exit before proposing cleanup changes. Preserve the author's historical crash workaround and timer protection; see `resources/Steam Input JSON Structure.md`, **Always-On Layer Isolation and the Historical Crash Workaround**.
- Audit with `python3 audit_command_budget.py path/to/layout.json` (add `--json` for a complete inventory). Each input may have at most three GUI command entries across activator objects/types; binding-array subcommands are allowed beyond three. Scan inactive/unreferenced groups too; report failures while continuing a read-only audit.
- Do not assume Neptune requires a separate command for every chord button. Modern multi-button mask selectors support grouped Any/All conditions; see `resources/Steam Input JSON Structure.md`, **Command Entry Budget**.
- **Do not hand-edit numeric runtime IDs** in `controller_action` commands. Convert to titles first.
- **Do not reorder** keys in `controller_mappings.actions` or `controller_mappings.action_layers` unless you also plan to remap runtime IDs.
- **Check for list-order vs. numeric-key-order divergence FIRST**: verify `action_layers` keys are in ascending `Preset_` numeric order. Steam's loader can resolve runtime IDs by numeric key order while the saved binds reflect list order — a divergence (e.g. from reordering layers in the Steam GUI) silently swaps layers on the next fresh load. If keys are out of order, normalize (reorder layers + matching `preset` blocks, resequence preset `id` fields) while the file is in `{{title}}` form. See `findings/2026-07-11-layer-order-swap/FINDINGS.md`.
- Prefer `--output` when you’re experimenting so you can diff/rollback easily.

### References
- Repo overview & script usage: `README.md`
- Converter script: `convert_runtime_ids.py`
- Why runtime IDs are fragile: `resources/Steam Input JSON Structure.md`

Terminology: [Layout Vocabulary](../../../resources/Layout%20Vocabulary.md). Use **button overlay** for a layer whose primary role is changing one button/action on top of an existing interaction; **overlay** is the short form.
