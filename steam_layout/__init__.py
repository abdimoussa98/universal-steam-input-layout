"""Shared library for the Steam Input layout tools in this repo.

- `model`: read a layout JSON (numeric IDs or `{{Base::Title}}` tokens): layer
  titles, active groups per source, binding parsing, Always On layers.
- `stacks`: `StackSpace`, every layer stack reachable from the action set, and
  queries over it: what's below a layer, what can be active with it, and where
  a given binding actually fires.
- `inheritance`: the inheritance/blocking audit built on `stacks`
  (resources/Layer Definition of Done.md, section 8).
- `fixes`: idempotent post-install fixes for the Neptune layouts, run as one
  ordered pipeline (`python3 -m steam_layout.fixes`).

Root CLIs (`audit_inheritance.py`, `prune_dead_groups.py`, ...) keep their
names and wrap this package.
"""
