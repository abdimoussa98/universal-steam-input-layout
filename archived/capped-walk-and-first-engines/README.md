# The capped walk and the first engines

Archived 2026-10-04 at the author's request, one day after they were built.
They were never committed while live, so there is no commit to check out. The
files here are as they were on the evening of 2026-10-03.

## What is here

| File | What it was |
|---|---|
| `steam_layout/walk.py` | The capped walk in Python: every stack the bindings can build with at most N layers on at once, in any order. `Walk(layout, max_layers).run()`, on every core |
| `steam_layout/engine/walk_engine.cpp` | The first compiled engine. Mode 0 was the capped walk, mode 1 the chain walk with extra presses. It kept the stack every stack came from, 84 bytes a state |
| `steam_layout/engine/chain_engine.cpp` | The first version of the chain engine, without paths. The live one grew out of it |
| `steam_layout/native.py` | The wrapper that built and ran those two programs |
| `steam_layout/cleanups.py` | The Cleanup audit of that day, with three ways to read the hidden-exit check: the chain stacks (one stack for each pair, plus landings), `walked_exits` and `chained_exits` |
| `steam_layout/chains.py` | The chains with `workers` (every core) and `landings()` |
| `tools/audit_cleanups.py` | The command line with `--walk N`, `--extras K` and `--python` |
| `tests/test_walk.py`, `tests/test_native.py` | Their tests |

The modules import each other by their old `steam_layout.` paths, so they
don't run from this folder.

## Why

- **The capped walk.** The author chose a cap on extra presses over a cap on
  layers on at once: "the chain is more accurate than the walk". A cap on
  layers also cuts off long chains, and 1,866 of the chain stacks on 90.22
  hold more than 10 layers.
- **The first engine.** It needed 4.6 GB for 6 extra presses and about 47 GB
  for 8. The chain engine does 6 in 1 GB (2 GB with paths) and 8 in 11 GB.
- **The old hidden-exit check.** It tested one example stack for each pair of
  layers and missed the menu Tap Cover gap, which has been in the layouts
  since 90.10. The live check tests every stack of the chain walk with 6
  extra presses.
- **`workers` and `landings()` in `chains.py`.** Only these walks and the old
  check used them.

## What replaced them

`steam_layout/engine/chain_engine.cpp`, run by `steam_layout/native.py`, read
by `Cleanups.covered_exits`. `chains.py` is its reference
(`tests/test_native.py`).

Record, with every measurement:
[findings/2026-10-03-simultaneous-cap](../../findings/2026-10-03-simultaneous-cap/README.md).
