# How the layouts are built

Both working layouts, `neptune/single-set-default_hold-gyro_latest` and
`neptune/single-set-alternative_hold-gyro_latest` (JSON and VDF), are
**generated**. They have 75 layers each since 90.14. A hand edit in `neptune/`
is lost on the next install.

## The builder

The current builder is in the newest build folder under `findings/`: at 90.19,
[findings/2026-10-03-pad-click-holds](../findings/2026-10-03-pad-click-holds/README.md).

```bash
python3 findings/2026-10-03-pad-click-holds/build_candidate.py            # builds the candidates in that folder
python3 findings/2026-10-03-pad-click-holds/install_neptune.py --deck     # a trial copy in that folder's deck/
python3 findings/2026-10-03-pad-click-holds/install_neptune.py --version 90.20   # writes neptune/ and exports the VDFs
```

`install_neptune.py` runs the fix pipeline (`steam_layout.fixes`) and writes
`neptune/`. Saving the snapshot under `versions/` is a separate step
([publishing](publishing.md)).

## The chain

Each builder extends the one before it and loads it by file path, back to the
09-29 baseline. The earlier builders stay frozen: a change goes in a new folder.

| Release | Builder | What it added |
|---|---|---|
| 90.19 | [pad-click-holds](../findings/2026-10-03-pad-click-holds/README.md) | The final pad click layers hold themselves |
| 90.18 | [pad-click-handoff](../findings/2026-10-03-pad-click-handoff/README.md) | The Click Entry Point hands over |
| 90.17 | [pad-click-soft-press-only](../findings/2026-10-03-pad-click-soft-press-only/README.md) | Pad clicks on Soft Presses only |
| 90.16 | [pad-click-exits](../findings/2026-10-03-pad-click-exits/README.md) | Pad click exits |
| 90.15 | [menu-second-press-keys](../findings/2026-10-03-menu-second-press-keys/README.md) | Menu second-press keys |
| 90.14 | [pad-middle-click](../findings/2026-10-03-pad-middle-click/README.md) | Pad clicks, the first build |
| 90.11 | [steering-fallback-hold](../findings/2026-10-02-steering-fallback-hold/README.md) | The Steering fallback hold (71 layers) |
| 90.10 | [stateful-transitions](../findings/2026-10-01-stateful-transitions/README.md) | Stateful layer transitions |
| earlier | [steering-lean](../findings/2026-09-30-steering-lean/README.md) | Lean steering, on the 09-29 baseline in `findings/2026-09-29-steering-implementation/` |

The scenario tests of 90.11 and 90.13 are in
[tests/test_scenarios_90_11.py](../tests/test_scenarios_90_11.py); each later
release has its own `tests/test_scenarios_90_<n>.py`.

## Starting the next release

Copy the newest build folder to `findings/<date>-<slug>/` and point its
`build_candidate.py` at the folder it was copied from. The copy already imports
the scripts from `tools/` (`from tools.audit_command_budget import ...`) and
exports with `tools/convert_vdf.mjs`.

Each `manifest.json` records a SHA-256 of the builder before it. On 2026-10-03
the builders' import lines changed when the scripts moved to `tools/`, so the
hashes in the older manifests are of the builders as built. A rebuild writes
the new hash and the same layout.
