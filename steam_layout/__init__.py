"""Shared library for the Steam Input layout tools in this repo.

- `model`: read a layout JSON (numeric IDs or `{{Base::Title}}` tokens): layer
  titles, active groups per source, binding parsing, Always On layers.
- `chains`: backward chains, the stacks that can be under a layer (who adds it,
  back to the action set, plus bystanders), each with the bindings that built
  it. The stack source for every audit since 2026-10-01.
- `inheritance`: the Window audit, the blocking rule for Always On layers
  (resources/Layer Definition of Done.md, section 8).
- `covers`: the cover check. `layer_report`: the per-layer report.
- `stacks`: applying layer commands and replaying one input sequence. Its
  `StackSpace` search, and the family walk in `flow_paths` and `flow_covers`,
  are deprecated and kept for reference.
- `fixes`: idempotent post-install fixes for the Neptune layouts, run as one
  ordered pipeline (`python3 -m steam_layout.fixes`).

Root CLIs (`audit_inheritance.py`, `prune_dead_groups.py`, ...) keep their
names and wrap this package.
"""
