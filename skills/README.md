# Skills

Agent skills for working on this repository's Steam Input layouts. Each folder
holds one `SKILL.md`.

This directory belongs to no tool. `.claude/skills` and `.agents/skills` are
symlinks to it, so Claude Code and Codex discover the same skills without copies.
In Codex, use `/skills` to list them or `$<skill-name>` to invoke one. If newly
added skills do not appear, restart Codex.

| Skill | Use it to |
|---|---|
| `steam-layout-prep` | Get a layout into JSON, run the pre-flight checks, and turn numeric runtime IDs into `{{Base::Title}}` tokens before reading or editing |
| `steam-layout-apply` | Finish an edit: convert back to numeric IDs, export the VDF, save the version snapshot |
| `steam-binding-order` | Write or review activators and binding arrays: allowed activation types, three entries per input, bottom-to-top execution |
| `steam-layer-duplicate` | Copy a layer without shifting any runtime ID, then retarget and wire the copy |
| `steam-actionset-delete` | Remove an action set and remap the IDs that shift (older multi-set layouts and imports) |
| `steam-runtimeid-remap` | Apply an explicit old → new runtime ID mapping to a numeric file |

## Git: all work is on `main`

Author's rule, 2026-10-03. It applies to every skill here and to any other
work in this repository.

- Stay on `main`. Don't create a branch or a worktree for a change, also when
  an agent's own default says to branch before committing.
- If a session finds itself on another branch, say so and ask before moving
  anything.
- This changes where commits go, not when: commit only when the author asks,
  and don't push unless asked.

The skills restate rules next to their IDs (R108 and so on). The rules
themselves are in the
[Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md#rule-tables),
and `tests/test_rule_registry.py` checks that every ID a skill names exists.
