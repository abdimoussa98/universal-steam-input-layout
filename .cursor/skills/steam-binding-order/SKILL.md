## Skill: Avoid layer-management bugs caused by binding array execution order

### When to use
- You’re editing a group binding where `"binding"` is an array of multiple `controller_action ...` commands.
- You’re seeing surprising behavior where a layer is added/removed “in the wrong order”.

### Key rule (critical)
- In Steam Input JSON bindings, when `"binding"` is an array, the commands execute **from bottom to top**.
- **Maximum three GUI command entries per input.** Count every activator object across all types; a list of six chords plus one Regular Press is seven entries. Subcommands in a `binding` array share one entry and may exceed three.
- Consolidate identical chord outputs/settings using a multi-button **Any** selector, preserving timing and interruption behavior. Legacy `chord_button` IDs are not masks; modern mask selectors are not exclusive to Triton.
- Run `python3 audit_command_budget.py path/to/layout.json` after edits; it scans every group, including inactive/unreferenced groups, and checks disabled banks separately. Do not hide overflow in disabled entries.
- Counting details and selector rules: `resources/Steam Input JSON Structure.md`, section **Command Entry Budget**.

### Practical checklist for layer cleanup + apply
- Recheck upper-layer isolation after lower-binding changes, including newly exposed actions, pending timers, and stale stacks. Held-owner chords are conditional protection. Keep useful overlay inheritance; block unsafe inherited mutations in protected windows or use a self-first ordered exit. Record affected stacks and displaced actions; see the seven Double Tap LS-edge blocks in the [inheritance review](../../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes).
- Preserve Always On isolation: finish other layer changes before adding the timed layer (add at the top); remove that layer first on early exit (self-removal at the bottom) before any other removals/additions. The author observed crashes otherwise; current fix status is unknown. Double Tap Covers do not have Always On binds.
- Empty bindings, disabled source modes, chord guards, and replacement outputs can protect Fire Start Delay timers from unrelated layer changes. Do not add cleanup through these blocks without tracing the timer lifetime. See `resources/Steam Input JSON Structure.md`, **Blocking to Protect Layer Timers** and **Always-On Layer Isolation and the Historical Crash Workaround**.
- Put cleanup `remove_layer` operations **lower in the array** so they execute **earlier**.
- Put the final “desired state” operation (often `add_layer` or `hold_layer`) **higher in the array** so it executes **last**.
- If you need “remove then add” semantics, ensure the `add_layer` is placed **above** removals in the array.

### Guardrails
- Preserve the guarded recovery shape: an owner-held chord (real output or explicit empty) on the same input suppresses an interruptible Regular Press removal. Keep the fallback's default Interruptable setting and require Hold to Repeat on every guarded recovery removal, including buttons, clicks, touches, and edges. Other lifecycle exits retain their own settings. Guard either valid owner in Mod 2 and stay within three entries. Activator interruption is separate from array execution order. Release/expiry/threshold exits are different operations; delayed-apply resets deliberately use Interruptable Off. See [the exact structure](../../../resources/Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape).
- Preserve intentional menu gyro suppression and Escape/Tab edge blocks: Start/Select menu use does not require simultaneous gameplay, WASD modifiers, or ramp-up. Overlay cleanup does not require passing through every gameplay action.
- Add stick-edge cleanup only where recovery needs it: LS overrides the inherited WASD modifier, RS overrides ramp-up. Ramp-up's layer API/timer restrictions explain more frequent RS blocking; do not mechanically mirror that onto LS. Check other exits and document the displaced action; see [edge cleanup and inheritance](../../../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions).
- Preserve cleanup ownership and scope: overlays may inherit recovery and keep a local release exit, but their applying layer owns recovery of invalid covers. Preserve shared or still-held interactions and review residual helpers under [overlay ownership](../../../resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership). Keep the nine-target Mod 2 current-branch fallback, eight-target combined-cover released-side exit, and eleven-target mode-changing release distinct. Verify actual source overrides before claiming a cover passes through unrelated controls. See [concrete examples](../../../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples); do not broaden lists merely to make them equal.
- After editing these arrays, re-run `convert_runtime_ids.py to-titles` if you need to re-verify targets by name.
- Be careful mixing `CHANGE_PRESET` with add/remove layer commands; mode switches can invalidate assumptions about active layers.

### References
- Explanation and example: `resources/Steam Input JSON Structure.md`
- Title↔ID conversion helper: `convert_runtime_ids.py`

Terminology: [Layout Vocabulary](../../../resources/Layout%20Vocabulary.md). Use **button overlay** for a layer whose primary role is changing one button/action on top of an existing interaction; **overlay** is the short form.
