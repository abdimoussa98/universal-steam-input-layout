---
name: steam-layout-prep
description: Prepare a Steam Input layout in this repo for editing or analysis. Gets it into JSON, runs pre-flight checks (layer list order vs. Preset_ numbering, preset block order, duplicate layer titles), and converts numeric runtime IDs into readable {{Base::Title}} tokens with convert_runtime_ids.py to-titles. Use this whenever you're about to read, audit, diff, or edit a layout (neptune/, findings/, archived/), when a file shows `controller_action add_layer 32 0 0`-style numeric IDs, or when the user reports layers being swapped or mis-targeted after loading into Steam.
---

# Prep a layout for editing

Rule IDs (R108 and so on) point at the [Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#rule-tables), which holds each rule's full text, example and check.

Runtime IDs in `controller_action` commands are positional: action sets are numbered first (from 1), then layers, in the order they appear. That makes numeric IDs fragile, so all editing happens in `{{title}}` token form.

## 1. Get to JSON

The editing scripts read JSON. VDF → JSON conversion uses the VS Code extension `pfwobcke.vscode-vdf`. If you only have a `.vdf`, ask the user to convert it, and keep the `.vdf` as the source export. After every successful, validated JSON edit, the agent **must** regenerate the sibling VDF with `node tools/convert_vdf.mjs path/to/layout.json` after the `steam-layout-apply` checks. This is a standing user instruction, including metadata-only edits, and supersedes the earlier leave-VDFs-alone preference. Do not ask for separate export permission or finish with only the JSON updated.

## 2. Run the pre-flight check

```bash
python3 - path/to/layout.json <<'EOF'
import json, sys, collections
cm = json.load(open(sys.argv[1]))["controller_mappings"]
order = list(cm["actions"]) + list(cm["action_layers"])
keys = [int(k.split("_")[1]) for k in cm["action_layers"]]
dups = [t for t, n in collections.Counter(v["title"] for v in cm["action_layers"].values()).items() if n > 1]
print("layer order:  ", "OK" if keys == sorted(keys) else "OUT OF ORDER (list order != Preset_ numeric order)")
print("preset blocks:", "OK" if [p["name"] for p in cm["preset"]] == order else "MISMATCH (not in actions + layers order)")
print("preset ids:   ", "OK" if [p["id"] for p in cm["preset"]] == [str(i) for i in range(len(cm["preset"]))] else "not sequential 0..N")
print("dup titles:   ", dups or "none")
print("title form:   ", "yes" if "controller_action add_layer {{" in open(sys.argv[1]).read() else "no (numeric IDs)")
EOF
```

What each result means (R104, R105):

- **dup titles** (for example the two `DEPRECATED` layers): rename them so each title is unique *before* step 3. `to-titles` turns both IDs into the same token, and after that they can't be told apart. `to-ids` resolves every duplicate token to the last layer with that title.
- **layer order OUT OF ORDER**: the `action_layers` list order and the `Preset_` numeric order disagree. On a fresh VDF load Steam can resolve runtime IDs by either order, which silently swaps layers. This is the July 2026 bug; see `findings/2026-07-11-layer-order-swap/FINDINGS.md`. Fix it after step 3, while the file is in title form:
  1. Reorder `action_layers` into numeric key order.
  2. Move the matching `preset` blocks the same way.
  3. Resequence the preset `id` fields to 0..N.

  Older Neptune exports were out of order and loaded on the Deck; the current 90.1 files were normalized. Check each file rather than assuming either state from its device name.
- **preset blocks MISMATCH / preset ids not sequential**: fix these together with the reorder above.
- **title form: yes**: the file is already readable (the `findings/` snapshots are), so skip step 3.

## 3. Convert IDs to titles

```bash
python3 -m tools.convert_runtime_ids to-titles path/to/layout.json                                   # in place
python3 -m tools.convert_runtime_ids to-titles path/to/layout.json --output path/to/layout_readable.json
```

Token format:
- Action sets: `{{Base}}`
- Layers: `{{Base::RST: Temporary Gyro}}`, where the `Parent::` prefix tells apart layers with the same name in different sets

## Reading the file

- **Chord encoding depends on export/client format, not just device.**
  - Older Neptune chords use single-selector `chord_button` IDs.
  - The July reference uses modern `gyro_ratchet_button_mask` selectors; multi-button chords are also supported by modern Deck clients. Do not expand a multi-button chord into one command per button merely because the layout is Neptune.
  - Preserve Any/All semantics. Legacy selector IDs are not masks; decode them before combining buttons.
  - The decode table is in the appendix of `findings/2026-09-27-exploratory-layout-audit/AUDIT.md`.
  - `button_escape` is the user's "Menu Right" and `button_menu` is "Menu Left".
- **Only some groups are live.** In `group_source_bindings`, groups marked `inactive` are dormant alternate modes. Only `active` groups and `mode_shift` targets affect behavior.
- **Trace inheritance beyond the edited layer.** Identify the lower bindings it exposes and upper layers that can inherit each changed input/source, including timed windows and plausible stale stacks. Resolve active groups, mode shifts, settings, and actual application order; omission is not a block, and GUI order is not the runtime stack. Use the [inheritance review](../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) before deciding a change is local.
- **Keep gyro overrides scoped.** Base owns normal response settings. Gyro and LST/RST activation layers change only their selector/Any-All fields; cursor overlays change only response properties and remove themselves on cancellation. Normal Tap Covers and ordinary modifier parents inherit response without an active gyro source. Preserve intentional active `disabled` gyro modes. See [gyro settings inheritance](../../resources/Steam%20Input%20JSON%20Structure.md#gyro-settings-inheritance).
- **Trace cursor cancellation through the lower input.** A cursor-local repeating self-removal exposes the parent's output and repeating cover/Mod 2 transition; do not duplicate outputs inside that removal. The two ordinary output/cover chords are both uninterruptible, while their repeating family fallback stays interruptible. Cursor inherits touch-release completion; normal covers replace it with cleanup only to prevent re-entry. Review RTP Double Tap's explicit face/D-pad/click blocks before allowing these mutations through a timed window. See [the exact convention](../../resources/Steam%20Input%20JSON%20Structure.md#cursor-cancellation-and-repeating-cover-chords).
- **Audit blocking as well as cleanup.** Distinguish explicit empty bindings, active `disabled` source modes, conditional chord protection, and replacement outputs/releases. Empty `inputs` objects and inactive groups are not explicit blocks. Find every active `always_on_action` owner and trace its entry/exit order: add it last; remove it first before other layer changes. This preserves the author's historical crash workaround and timer isolation. Read [the documented contract](../../resources/Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround); do not treat a blocked input as an invitation to add cleanup.
- **Classify the cleanup shape.** Guarded recovery pairs an owner-held chord with an interruptible Regular Press removal on the same input; every guarded recovery removal must enable Hold to Repeat. Inspect both siblings and interruption settings before calling a removal guarded. Release cleanup, timed expiry, threshold exits, and uninterruptible delayed-apply resets are different types. See [the exact recovery structure](../../resources/Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape) and [owning-layer responsibility for overlays](../../resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership).
- **Recognize touch-release completion paths.** A stick-touch release may intentionally apply the pending delayed target before clearing its LST/RST helpers, preventing those removals from postponing the apply. Audit it alongside the primary delay and the upper cover's replacement touch input; do not classify add-before-removal as an ordering defect by itself. See [the documented pattern](../../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release).
- **Check held inputs across layer changes (R113 to R115).** A layer added over a held input does not fire its immediate layer command on that input. Its delayed and repeating activators still fire. Short delays (such as `Gyro Off Ramp Up`'s 5 ms), repeating adds outside Base, and repeating threshold exits often exist for this reason, not for timing; don't strip them or "normalize" them. Whether removing a layer fires the newly exposed binding on a held input is **unverified**. Base's repeating entries and the other covering repeats are what guarantee re-entry after a removal, so keep them. Give any new layer command that must fire after a removal Hold to Repeat, and still trace what each removal exposes on inputs that may be held. See [held inputs across layer changes](../../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes).
- **Identify the recovery owner before reporting omissions.** Overlays can inherit recovery and use a local release exit; other layers clear a current branch or the released side. Record intended survivors and actual gyro/edge overrides. Release-only cleanup or a shorter target list is not automatically a defect. Use [cleanup scopes and examples](../../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) when evaluating consistency.
- **Treat unequal edge coverage as a review question.** LS cleanup displaces the WASD modifier; RS cleanup displaces ramp-up, whose layer API/timer constraints make blocking more common. Recommend edge cleanup only where recovery requires that tradeoff, not merely to match the other stick. See [edge cleanup and inheritance](../../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions).
- **Respect menu context.** The author intentionally suppresses gyro and accepts edge blocking in menu layers; WASD modifiers and ramp-up are unnecessary during Start/Select menu use. Do not classify those confirmed overrides as defects or remove them to make overlays pass through all gameplay actions.

## Check the command budget

Run `python3 -m tools.audit_command_budget path/to/layout.json` for a complete scan, or add
`--json` for every input's counts and exact violation paths. The maximum (R109) is **three
GUI command entries per input**, summed over all activator types/list elements.
Subcommands in a `binding` array share one entry and may exceed three. Inactive and
unreferenced groups are included; disabled banks are checked separately. A failure
is an audit finding to document or fix, not a reason to skip the remaining audit.
See `steam-binding-order` for consolidation rules.

## Guardrails

- Work on `main`. Don't create a branch or a worktree for an edit (author, 2026-10-03;
  [skills README](../README.md#git-all-work-is-on-main)).
- Plan publication metadata with every layout change: before commit/export/publication,
  revalidate the full description and bump the title's release version once for that
  release batch. See [the publication rule](../../docs/publishing.md)
  and `steam-layout-apply`; schema versions and runtime IDs are unrelated.
- Never hand-edit numeric runtime IDs; convert to titles first.
- In a numeric file, don't reorder or insert entries in `actions` / `action_layers`, because every ID after the change shifts. In title form, reordering is safe as long as the `preset` blocks move in step.
- Use `--output` while experimenting so you can diff and roll back.
- Watch out for a numeric file whose layers were reordered or deleted without remapping. Its IDs no longer match list order, so `to-titles` would mislabel every bind. Either re-export from Steam, or remap using a known old→new mapping with the legacy `tools/id_replacement/replace_layer_ids_flexible.py` (`-i`, `-m`, `-o`, `--dry-run`).

## References

- Script usage: `docs/tools.md`
- JSON structure and runtime ID rules: `resources/Steam Input JSON Structure.md`
- Converter: `convert_runtime_ids.py`

Terminology: [Layout Vocabulary](../../resources/Layout%20Vocabulary.md). Use **button overlay** for a layer whose primary role is changing one button/action on top of an existing interaction; **overlay** is the short form.
