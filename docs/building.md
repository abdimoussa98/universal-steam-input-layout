# How the layouts are built

Both working layouts, `neptune/single-set-default_hold-gyro_latest` and
`neptune/single-set-alternative_hold-gyro_latest` (JSON and VDF), are
**generated**. They have 88 layers each since 90.33. A hand edit in `neptune/`
is lost on the next install.

## The builder

The current builder is in the newest build folder under `findings/`: at 90.36,
[findings/2026-10-06-cleanup-entry-order](../findings/2026-10-06-cleanup-entry-order/README.md).

```bash
python3 findings/2026-10-06-cleanup-entry-order/build_candidate.py            # builds the candidates in that folder
python3 findings/2026-10-06-cleanup-entry-order/install_neptune.py --deck     # a trial copy in that folder's deck/
python3 findings/2026-10-06-cleanup-entry-order/install_neptune.py --version 90.37   # writes neptune/ and exports the VDFs
```

`install_neptune.py` runs the fix pipeline (`steam_layout.fixes`) and writes
`neptune/`. Saving the snapshot under `versions/` is a separate step
([publishing](publishing.md)).

## The chain

Each builder extends the one before it and loads it by file path, back to the
09-29 baseline. The earlier builders stay frozen: a change goes in a new folder.

| Release | Builder | What it added |
|---|---|---|
| 90.36 | [cleanup-entry-order](../findings/2026-10-06-cleanup-entry-order/README.md) | One change to the finished layout and no bind changes: every input with a cleanup function stores its entries as Regular Press, guard, Release. 121 inputs per layout were stored otherwise, among them the stick touches of the four menu Entry Points |
| 90.35 | [steering-fallback-swap](../findings/2026-10-06-steering-fallback-swap/README.md) | Changes to the finished layout: `Steering` and its fallback guard swap places (the bind that adds one removes the other), so the guard's eight-way stick is never over `Steering`'s four-way one; the guard carries `Steering`'s Start, Select and right pad; a driver's press removes the ramp layers before it adds its layer |
| 90.34 | [steering-four-way-and-open-edges](../findings/2026-10-05-steering-four-way-and-open-edges/README.md) | Four changes to the finished layout: `Steering` stops blocking both stick edges, so turn assist runs in Steering base and in the fallback guard; its left stick is four-way; up and down add the guard at once with a repeating press; the guard states eight-way |
| 90.33 | [steering-fallback-guard](../findings/2026-10-05-steering-fallback-guard/README.md) | Changes to the finished layout, walking back the fallback window: `Steering \| LS: Entry Guard` becomes `Steering \| LS: Fallback Guard`, which Steering's up and down bring in after 100 ms and which stays; in it the modifier pair adds the Gyro modifiers with the stick out and ends the guard at centre; the Fallback Hold and its window are deleted (88 layers); the Gyro Modifier 2 quick tap also removes Steering, the guard and the Base modifiers |
| 90.32 | [fallback-window-replacements](../findings/2026-10-04-fallback-window-replacements/README.md) | One change to the finished layout: in the fallback's window the drivers scroll and Start and Select type Tab and Escape, where 90.31 had them remove the window |
| 90.31 | [fallback-window](../findings/2026-10-04-fallback-window/README.md) | Changes to the finished layout: a new window, `Steering \| LS: Fallback Window`, counts the fallback's second (90 layers); the Fallback Hold leaves Steering on a Release; 62 stick groups stop stating an outer ring radius; the Entry Guard ends on any direction's Release |
| 90.30 | [window-releases-and-tap-cover-resets](../findings/2026-10-04-window-releases-and-tap-cover-resets/README.md) | Three changes to the finished layout: in `RTP: Double Tap` Start, Select and the two modifier buttons get a Release; the fallback hold's outer edge loses its Release; the Tap Cover reset comes off the three Entry Points |
| 90.29 | [quiet-resets-and-beeps](../findings/2026-10-04-quiet-resets-and-beeps/README.md) | Two changes to the finished layout: the three Tap Cover resets state `haptic_intensity` 0, and the 22 layer commands written `1 0` become `0 1`, because the beep is the second flag |
| 90.28 | [menu-chain-and-window-pads](../findings/2026-10-04-menu-chain-and-window-pads/README.md) | The chorded menu chain runs on every press: the Fn layers add its Entry Point, and Steering and Cursor Gyro get Fn layers of their own (89 layers). In the Double Tap windows the right pad's touch is a Release. Its first part is built inside the 90.25 build, before that build's last step |
| 90.27 | [pad-bump-removal](../findings/2026-10-04-pad-bump-removal/README.md) | The pad touch bump of 90.25 comes out: three layers fewer (87), and Base has the pad clicks and the swipes again. It runs the 90.25 build without its two pad steps, then 90.26's delays and click resets |
| 90.26 | [standard-delays](../findings/2026-10-04-standard-delays/README.md) | No hold delay over 200 ms; a reset on the pad's touch for the Click Entry Points' outer bind; the touch layers' outer bind starts at the inner one's radius, with no delay |
| 90.25 | [pad-bumps-and-menu-keys](../findings/2026-10-04-pad-bumps-and-menu-keys/README.md) | Pad touch bumps, the middle-click mouse, the chorded menu chains and `Menu Keys`, the Tap Cover resets (90 layers). Its class sits under the required-cleanups one, so those run last |
| 90.24 | [required-cleanups](../findings/2026-10-04-required-cleanups/README.md) | Every layer has a cleanup function on both stick touches, the stick edges and every button it retypes or blocks (R169 to R171) |
| 90.23 | [tap-cover-stick-touches](../findings/2026-10-04-tap-cover-stick-touches/README.md) | The menu Tap Cover binds both stick touches |
| 90.22 | [gamepad](../findings/2026-10-03-gamepad/README.md) | The Gamepad layer and the third transition (78 layers) |
| 90.21 | [cursor-gyro](../findings/2026-10-03-cursor-gyro/README.md) | The stateful Cursor Gyro layer (76 layers) |
| 90.20 | [base-pad-click-one-add](../findings/2026-10-03-base-pad-click-one-add/README.md) | Base adds the Click Entry Point with one Soft Press |
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
