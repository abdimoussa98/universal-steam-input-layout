---
name: steam-binding-order
description: Enforce the maximum of three GUI command entries per input and bottom-to-top execution of binding subcommand arrays. Use when writing, copying, consolidating, or reviewing activators, chords, and layer cleanup bindings in this repo.
---

# Binding array execution order

## Maximum three command entries per input

This is a hard requirement from the layout author. Count **activator objects across all
activation types on one input**, not the strings in `bindings.binding`:

- A single `Full_Press` object counts as one command entry.
- A `chord` list of six objects counts as six entries. Adding one `Full_Press` makes seven, even though `activators` has only two keys.
- A `binding` array is subcommands within one entry. Arrays with more than three subcommands are allowed; preserve their execution order.
- Count each `group.inputs.<input>` separately, including edge, touch, click, and trigger pulls. Scan inactive groups, mode-shift groups, and unreferenced groups too. Check disabled activator banks separately before restoring them.

Run `python3 audit_command_budget.py path/to/layout.json` after edits. A nonzero exit
means the file is not ready to finalize (1 = over budget, 2 = malformed input).

To consolidate identical chord outputs/settings, use one multi-button chord with **Any**
semantics rather than one command per possible button. Modern selectors use
`gyro_ratchet_button_mask` and `gyro_ratchet_button_requireany_or_all`; legacy
`chord_button` IDs are not bitmasks. Keep different outputs, delays, repeat settings,
and interruption behavior distinct. Do not merge independent conditions into an
unconditional subcommand array or move overflow into disabled entries.

See [the counting rule and chord format](../../../resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)
and [the Neptune consolidation plan](../../../plans/2026-09-27-neptune-command-budget.md).

## The rule

When `"binding"` is an array, the commands execute **from bottom to top**. The top entry runs last, so it decides the final state.

Example (comments are only for illustration; JSON doesn't allow them):

```json
"binding": [
  "controller_action add_layer {{Base::Turning Ramp Up 0}} 0 0, , ",      // runs LAST
  "controller_action remove_layer {{Base::Turning Ramp Up 1}} 0 0, , ",
  "controller_action remove_layer {{Base::Gyro Off Ramp Up}} 0 0, , "     // runs FIRST
]
```

## Checklist

- For ordinary cleanup-then-apply transitions, put cleanup `remove_layer` commands **below** the main action so they run first, and the final `add_layer` or `hold_layer` **above** them so it runs last.
- For "remove, then add" semantics, the add goes **above** the removal.
- **Preserve touch-release completion before cleanup.** Some stick-touch releases apply the pending delayed target **first**, then remove the corresponding LST/RST family so those removals cannot postpone the apply. Keep that add at the bottom of its stored array. Retarget it when the primary delayed target changes, and trace upper covers so their touch releases cannot re-add a superseded target. This differs from a periodic delayed-apply reset and never overrides Always On isolation. See [the pattern and concrete example](../../../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release).

## Guardrails

- **Recheck upper-layer isolation after lower-binding changes.** Trace which upper layers inherit any added, changed, or newly exposed action, including pending timers and stale stacks. A held-owner chord is not an unconditional block. Keep useful overlay inheritance; block unsafe inherited mutations in protected windows or use a self-first ordered exit. The seven Double Tap LS-edge blocks are the concrete example in the [inheritance review](../../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes). Record affected stacks and displaced actions, not just edited groups.
- **Preserve the guarded recovery shape.** On the same input, an owner-held chord (real output or explicit empty) suppresses an interruptible Regular Press cleanup. Keep the removal entry's default Interruptable setting; do not set `interruptable: "0"` on that fallback. Require Hold to Repeat on every guarded recovery removal, including buttons, clicks, touches, and edges; this does not change other lifecycle exits. Protect either valid owner in Mod 2, retain the three-entry cap, and distinguish activator interruption from bottom-to-top subcommand execution. Release cleanup, Always On expiry, threshold exits, and deliberate delayed-apply resets have different shapes; the resets intentionally use Interruptable Off. See [the exact structure](../../../resources/Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape).
- Keep ordinary modifier output and cover repeats separate. On face/D-pad/menu/stick-click inputs, use two same-owner chords: original output and cover-add only. Both set `interruptable: "0"`; only cover-add gains `hold_repeats: "1"`, with no delay or feedback. Preserve the output's existing repeat settings and the interruptible repeating family fallback as the third entry. Do not apply this interruption setting to the empty owner guard on dual-stick edges. Cursor cancellation repeats self-removal only and exposes the lower output/cover route; it must not repeat keyboard output itself. Chord-list order does not preserve the old combined array's execution ordering. See [cursor cancellation](../../../resources/Steam%20Input%20JSON%20Structure.md#cursor-cancellation-and-repeating-cover-chords).
- **Preserve Always On isolation.** The author observed crashes when unrelated layers were added/removed while an Always On layer remained active; current fix status is unknown. Finish other layer changes before adding that layer (add at the top of the stored array). On any early exit, remove the Always On layer first (self-removal at the bottom), then run other removals/additions. Never sort those removals into a self-last order. The seven Double Tap windows use this contract; Double Tap Covers are not Always On layers.
- **Treat blocking as intentional until traced.** Removals can reset Fire Start Delay timers. Empty bindings, disabled source modes, chord guards, and replacement outputs suppress unrelated layer changes. Do not widen cleanup into a protected timing window; either keep it blocked or leave the timed layer first. See [timer blocking and Always On isolation](../../../resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) before changing these paths.
- Edit these arrays in `{{title}}` form so every target is readable. Use the `steam-layout-prep` skill to convert first.
- After copying binds from another layer, re-read every target title. The exploratory audit found RTP: Mouse Buttons' center release targeting LTP: Arrow Keys; that historical copy-paste error is fixed in the current 90.2 layouts (see [cleanup audit F8](../../../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md#f8-a-historical-copypaste-warning-is-stale-for-these-files)). Do not assume an old finding still describes the current file.
- When you add a new layer, review the related cleanup lists and add it where that cleanup's intended scope requires it. Preserve partial-family exits, valid held states, timer blocks, and Always On isolation; do not append a removal to every cleanup merely because the layer exists.
- **Preserve cleanup ownership and scope.** Overlays can inherit recovery and keep a local release exit, but the layer applying one owns its recovery and must account for invalid covers in its stale-state cleanup. Preserve shared or still-held interactions; review existing residual-helper cases under [overlay ownership](../../../resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership). Menu gyro suppression and Escape/Tab edge blocks are intentional. Keep Mod 2's current-branch fallback and the combined cover's released-side exit distinct from the mode-changing release; dependent overlays can increase their target counts without changing those boundaries. See [concrete cleanup examples](../../../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples); do not broaden these lists solely to make them equal.
- **Limit edge cleanup to justified recovery needs.** LS edge overrides the inherited WASD modifier; RS edge overrides ramp-up. Ramp-up's layer API/timer constraints justify more frequent RS blocking, not automatic LS symmetry. Check existing exits and record the displaced action before adding an edge fallback. See [the tradeoff](../../../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions).
- `CHANGE_PRESET` switches the whole action set and invalidates assumptions about which layers are active. The current layouts are single-set, so it only matters for multi-set files in `archived/`.

## References

- Explanation and example: `resources/Steam Input JSON Structure.md` (section "Binding Execution Order")
- Title ↔ ID conversion: `convert_runtime_ids.py`

Terminology: [Layout Vocabulary](../../../resources/Layout%20Vocabulary.md). Use **button overlay** for a layer whose primary role is changing one button/action on top of an existing interaction; **overlay** is the short form.
