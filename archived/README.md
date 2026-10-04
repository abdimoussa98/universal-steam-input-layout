# Archived

Things that are deprecated, retired or superseded. Nothing here is used by the
layouts, the builders, the audits or the tests. It is kept for reference.

**To run any of it,** check out commit `1e4eb6e`, the last one before it was
moved here (2026-10-02). The modules below import each other by their old
`steam_layout.` and `tests/` paths, so they don't run from this folder.

| Folder | What | Deprecated | Why | Record |
|---|---|---|---|---|
| [exhaustive-stack-search/](exhaustive-stack-search/) | The exhaustive stack search (`held_model`, `stackdb`, the C++ engine in `tools/stack_search`), the untimed proofs (`symbolic`, `invariants`) and the timed model, search and proof tooling (`timed_*`, `source_geometry`), 31 modules with their 35 test files and `requirements-proof.txt` | 2026-09-30 | The search never finished, and the author chose audits that follow intended flows | [archive note](../findings/2026-09-30-stack-search/ARCHIVE.md) |
| [depth-search-and-family-walk/](depth-search-and-family-walk/) | The depth-limited search (`StackSpace` and `explore`, in the full `stacks.py` of that day), the family walk (`flow_paths`, `flow_covers`), the family rules as they were at 90.9, and the tests that compared both with the backward chains | 2026-10-01 | Every audit builds its stacks from backward chains (`steam_layout/chains.py`) | [deprecation record](../findings/2026-10-01-backward-chain-stacks/README.md#deprecated) |
| [capped-walk-and-first-engines/](capped-walk-and-first-engines/) | The capped walk (`walk.py`: every stack with at most N layers on at once), the first compiled engine (`walk_engine.cpp`), the first version of the chain engine, and the hidden-exit check that read one stack for each pair of layers. Never committed while live: the files are as they were on 2026-10-03 | 2026-10-04 | The author chose a cap on extra presses over a cap on layers. One engine remains, `steam_layout/engine/chain_engine.cpp`, and the check reads the chain walk with 6 extra presses | [findings/2026-10-03-simultaneous-cap](../findings/2026-10-03-simultaneous-cap/README.md) |
| [retired-fixes/](retired-fixes/) | `transition_set_0`, the 90.6 fix that gave Transition Set 0 its stick-touch release | 2026-10-01 | Since 90.10 the builder writes both transition layers whole | [90.10 build](../findings/2026-10-01-stateful-transitions/README.md) |
| [plans/](plans/) | Three superseded copies of the steering plans (the baseline plan, the 25-layer plan and the previous brainstorm) | 2026-09-30 | Replaced by the sixteen-layer plan and the current brainstorm in `plans/` | [current plan](../plans/2026-09-29-steering-implementation-plan.md) |
| [Layer Reverse Lookup.md](Layer%20Reverse%20Lookup.md), [manual-testing.md](manual-testing.md), [scratch-paper/](scratch-paper/), `empty_0.vdf` | A hand-kept table of layer IDs as of release 31.0, for the four-set layouts; the stub left by the retired Deck checklist; two pasted JSON fragments and four empty files from `resources/`; an empty template from `neptune/` | 2026-10-03 | The reorganization. The lookup is replaced by `convert_runtime_ids to-titles` and `duplicate_layer --list`; nothing pointed at the others | [plan](../plans/2026-10-03-repo-reorganization.md) |
| [dse/](dse/) and the loose files | The older `universal-layout-*` multi-set layouts, the DualSense Edge layouts and the one-off scripts that edited them | Before the Neptune layouts | Replaced by the single-set layouts in `neptune/` | |

Five test files were split, not moved: `test_audit_inheritance.py`,
`test_stacks.py`, `test_chains.py`, `test_covers.py` and
`test_flow_inheritance.py`. Their copies under
`depth-search-and-family-walk/tests/` are the full files of that day; the
live ones in `tests/` keep only the tests of code that is still used.

Not archived, although they look old:

- `findings/2026-09-29-steering-implementation/` and
  `findings/2026-09-30-steering-lean/`: frozen, but the current builder
  extends them.
- `findings/`, `plans/` and `versions/`: dated records and snapshots. One
  thing in them was changed after the fact: on 2026-10-03 the scripts at the
  repo root moved to `tools/`, and the 26 builders, installers and inventory
  scripts under `findings/` had their imports (`from tools.audit_command_budget
  import ...`) and the exporter's path (`tools/convert_vdf.mjs`) updated, because
  the current builder loads the earlier ones by path. Nothing else in them
  changed, and the commands in their prose are as they were run that day.
  The `*_generator_sha256` values in each `manifest.json` are the builders'
  hashes as built, before that edit; a rebuild writes the new hash and the
  same candidate.
  In 14 records, 31 links to files that moved the same day had their target
  repointed; the link text is unchanged.
- `out/`: generated search data, ignored by Git. It can be deleted
  ([note](../findings/2026-09-30-stack-search/ARCHIVE.md#deleting-out)).
