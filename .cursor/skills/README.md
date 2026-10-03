## Project skills

> Four of these (`steam-layout-prep`, `steam-layout-apply`, `steam-layer-duplicate`, `steam-binding-order`)
> have a newer, maintained copy under `.claude/skills/`. The copies here were last revised on 2026-09-30.

These are project-local Agent Skills for working on this repository’s Steam Input layouts.

### Skills included
- `steam-layout-prep`: VDF → JSON (external) → `to-titles` for readable editing
- `steam-layout-apply`: `to-ids` to finalize layouts for Steam
- `steam-layer-duplicate`: safely duplicate a layer without shifting existing runtime IDs
- `steam-actionset-delete`: safely delete an action set and remap shifted IDs
- `steam-runtimeid-remap`: apply an explicit old→new runtime ID mapping (two-pass)
- `steam-binding-order`: guardrails around bottom-to-top execution of binding arrays

### Repo references
- Scripts and workflows: `README.md`
- JSON structure and pitfalls: `resources/Steam Input JSON Structure.md`

