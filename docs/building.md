# How the layouts are built

Every working layout is **generated**; a hand edit is lost on the next build.
Since 2026-10-15 **Ibex, the Steam Controller 2, is the base layout** (R177):

| Directory | Made by | Layers |
|---|---|---|
| `ibex/` | A builder in `findings/<date>-<slug>/`, as below | 90 |
| `neptune/` | `python3 -m tools.convert neptune`, from an Ibex snapshot (R179). Built by the builders below up to 90.74 | 90 |
| `dse/` | `python3 -m tools.convert dse`, from an Ibex snapshot (R180 to R185) | 74 |

A change is built on Ibex, and then the two conversions are run. A change for
the Deck or the Edge alone is a new conversion rule in `steam_layout/convert.py`
and the [Layer Definition of Done §12](../resources/Layer%20Definition%20of%20Done.md#12-controllers-and-conversions),
never an edit of their layouts. A test fails when a converted layout is not
what `tools.convert` makes from the Ibex release its CHANGELOG section names
(C1, `test_convert`).

```bash
python3 findings/<date>-<slug>/build_candidate.py --install   # writes ibex/*_latest.json
python3 -m tools.convert neptune                                # writes neptune/*_latest.json
python3 -m tools.convert dse                                    # writes dse/*_latest.json
python3 -m tools.convert dse --check                            # exit 1 if dse/ is not that conversion
```

`tools.convert` reads the newest Ibex snapshot, so export Ibex's VDFs and save
its snapshot first (`python3 -m tools.release snapshot ibex`). It writes a
controller's latest release version again when nothing changed for it, and its
next version when something did.

The separate [90.39 fallback-window testing candidate](../findings/2026-10-09-fallback-window-backport/README.md)
extends frozen 90.32 with compatible later fixes. It has 90 layers and writes
to its findings folder, with distinctly named snapshots under
`versions/neptune/90.39/`. It is an inactive experiment: the live release
continues from 90.38 through 90.40–90.58, 90.61–90.68 and 90.70 to 90.74. Its build/validation commands, local rules and
scenario coverage remain separate from the live layouts.

## The builder

The current live builder is
[findings/2026-10-16-fn-right-stick-owner](../findings/2026-10-16-fn-right-stick-owner/README.md),
for Ibex 1.1. It reads the Ibex 1.0 snapshot and writes `ibex/`; Neptune 90.77
and DSE 1.1 are its conversions. Ibex 1.0's builder,
[ibex-base](../findings/2026-10-15-ibex-base/README.md), reads the Neptune 90.74
snapshot: the bootstrap, the one change that went from the Deck to Ibex.
Neptune's own builders end at 90.74
([fn-right-stick](../findings/2026-10-15-fn-right-stick/README.md), from the
90.73 snapshot). 90.76 is a Deck trial off the line, made from the 90.75
snapshot and never installed or saved under `versions/`
([record](../findings/2026-10-16-entry-point-requires-click/README.md));
Neptune goes from 90.75 to 90.77. 90.70's builder reads the 90.68 snapshot: 90.69 is a trial from 90.68 too, a snapshot off the line that was never the
working layout. Since 90.49 a builder reads the snapshot of the release before it. Two lines do not: 90.54 reads the
90.52 snapshot, the author's trial of one change, so 90.53 is a snapshot off the line and 90.55 continues from 90.54;
and 90.61 reads the 90.58 snapshot. 90.59 and 90.60 were two trials for the same fault that did not help; their
files were removed (author, 2026-10-12) and the [fault's record](../findings/2026-10-12-steering-ends-on-a-stick-touch/README.md)
says what they were. A separately named testing candidate does not become the live
builder merely by having a newer version number.

```bash
python3 findings/2026-10-16-fn-right-stick-owner/build_candidate.py            # candidates in that folder
python3 findings/2026-10-16-fn-right-stick-owner/build_candidate.py --install  # writes ibex/*_latest.json
```

A test holds Ibex's working layouts to their builder (R156,
`test_steering_rtp_menu_chords`): it finds the findings folder whose stored
`default-candidate.json` carries the working layout's version and Steam's
`controller_type` for it, and runs that folder's `build_candidate.py`. A
release's folder needs both files. Neptune's layouts were held to theirs up to
90.74.

The builder runs the fix pipeline (`steam_layout.fixes`), and so does each
conversion. After installation, validate, export the sibling VDFs and save the
snapshots of each controller that changed using `steam-layout-apply`
([publishing](publishing.md)). Older builders use a separate
`install_neptune.py` for installation.

## The chain

Each builder extends the one before it and loads it by file path, back to the
09-29 baseline. The earlier builders stay frozen: a change goes in a new folder.

| Release | Builder | What it added |
|---|---|---|
| Ibex 1.1 | [fn-right-stick-owner](../findings/2026-10-16-fn-right-stick-owner/README.md) | From Ibex 1.0. The Fn layers take over from the Entry Points: the Entry Points, both stick guards and the Tap Cover keep Base's mouse mode on the right stick, edge at 21000; every bind that adds an Fn layer removes its Entry Point; the stick clicks add Fn at the press, silent and repeating, and Fn's own click Release does the transition. No `requires_click` on a stick, `deadzone` 13276 on the Fn and Entry Point sticks, and 84 pairs of chords that differ only in their button are one Any chord. Neptune 90.77 and DSE 1.1 are its conversions. 84 removes fewer and 8 adds more a layout |
| Ibex 1.0 | [ibex-base](../findings/2026-10-15-ibex-base/README.md) | From Neptune 90.74, the bootstrap: the Steam Controller 2's Steam names and Player Space in all eleven gyro-to-mouse groups; no bind changes. Neptune 90.75 and DSE 1.0 are its conversions |
| 90.74 | [fn-right-stick](../findings/2026-10-15-fn-right-stick/README.md) | From 90.73. The right stick of the four Fn layers takes the left stick's group settings: `deadzone` 13276 and `requires_click` 0 come off. Its keys (`;` `'` `.` `,`), Low bumps, R3 guard and cleanups are unchanged. Removes and adds unchanged |
| 90.73 | [key-layer-click](../findings/2026-10-15-key-layer-click/README.md) | From 90.72. In `Escape`, `Tab`, `Backspace` and `Enter` the left pad's click is a repeating, silent Soft Press, not interruptible, that removes the layer; Base's repeating click then adds its Click Entry Point. Four removes more a layout |
| 90.72 | [pad-stick-edge-cleanups](../findings/2026-10-14-pad-stick-edge-cleanups/README.md) | From 90.71. The pad click layers get a cleanup function on both stick edges and the key layers on the left, a copy of their stick-touch cleanup guarded by the pad's touch, for controllers without stick touch. What those edges hide is done on the pad's click: the Steering stick layers add their cover, the ramp layers remove themselves. The menu Entry Points block the pad clicks (R172). 90 removes and 9 adds more a layout |
| 90.71 | [pad-click-touch-layers](../findings/2026-10-14-pad-click-touch-layers/README.md) | From 90.70. The adders of the Click Entry Points repeat every 50 ms, silent. The D-pad layers have Requires Click off, and each direction and the centre gets a Release that removes the layer; their outputs are silent and the scroll repeats bump Low. The four final layers' click is the self-hold alone, High; the inverted repeating removal is gone. The Middle Click output is its own Soft Press, silent. Ten removes in, four out, a layout |
| 90.70 | [entry-guard-in-every-steering-cleanup](../findings/2026-10-13-entry-guard-in-every-steering-cleanup/README.md) | From 90.68, not 90.69. Every cleanup press of the ten Steering layers adds `Steering \| LS: Entry Guard` before it removes (R176): the 80 that are not on the left stick's edge get the add 90.67 gave the ten that are. 80 adds more a layout, no remove more or fewer |
| 90.69 | [steering-cleanup-presses-without-repeat](../findings/2026-10-13-steering-cleanup-presses-without-repeat/README.md) | From 90.68, off the line and not installed. The 90 cleanup presses of the Steering layers lose Hold to Repeat and stay interruptible; the ten left-edge ones lose the Entry Guard add. A Deck trial for A69, saved under `versions/neptune/90.69/` |
| 90.68 | [entry-guard-adds-the-driver-layer-first](../findings/2026-10-13-entry-guard-adds-the-driver-layer-first/README.md) | From 90.67. One change on two inputs a layout: in `Steering \| LS: Entry Guard` each driver's chord runs its add of the driver's layer first and the guard's removal second (R137), so `Steering` is never the top layer between the two. The two commands swap places; no bind, setting or count changes |
| 90.67 | [entry-guard-before-the-left-edge-cleanup](../findings/2026-10-13-entry-guard-before-the-left-edge-cleanup/README.md) | From 90.66. The mode shift of 90.66 is gone: `Steering`'s drivers and groups are 90.65's. On the left stick's edge of ten Steering layers the cleanup press adds `Steering \| LS: Entry Guard` before it removes, stored last (R176): a press that runs past its guard (A69) leaves the guard on top, not `Steering`'s exit. No start delay. Ten adds more a layout, no remove more or fewer |
| 90.66 | [steering-mode-shift-on-the-drivers](../findings/2026-10-13-steering-mode-shift-on-the-drivers/README.md) | From 90.65. In `Steering` each driver gets a Regular Press, not interruptible, that mode-shifts the left stick to one new group with empty up and down (R175): a cleanup that runs past its guard (A69) no longer ends `Steering`. The 5 ms start delay of 90.65 comes off the ten left-edge presses. One group more a layout; removes unchanged. The simulator models a mode shift held from a layer (A70) and can take a layer off by hand (`drop`) |
| 90.65 | [steering-left-edge-press-and-guard](../findings/2026-10-13-steering-left-edge-press-and-guard/README.md) | From 90.64. On the left stick's edge of ten Steering layers the chord with Invert Activation becomes the repeating, interruptible Regular Press and its guard chord again, with their 90.58 settings and today's lists; the press starts 5 ms late; Outer Ring Binding Invert goes off in those ten groups. Removes unchanged. The Cleanup audit reads such a press as a cleanup function with a start delay on it |
| 90.64 | [layer-order](../findings/2026-10-12-layer-order/README.md) | From 90.63. The layer list in a new order and nothing else: the two ramp layers, the five stateful layers (`Gyro`, `Steering`, `Cursor Gyro`, `Menu Keys`, `Gamepad`), then the other layers by parent. The `Preset_` keys and preset blocks follow (R104); every layer is bind for bind what it was |
| 90.63 | [inverted-ring-on-the-steering-left-edge](../findings/2026-10-12-inverted-ring-on-the-steering-left-edge/README.md) | From 90.62. One setting in ten groups a layout: Outer Ring Binding Invert on the left stick of the ten Steering layers whose edge holds the cleanup chord. The chord then runs with the stick at the rim and no driver held, where it ran off the rim. No bind or list changes; removes unchanged. The simulator and the Budget audit read a Soft Press by its own inversion setting (A67) |
| 90.62 | [steering-rocking-like-the-bumper-modifiers](../findings/2026-10-12-steering-rocking-like-the-bumper-modifiers/README.md) | From 90.61. Rocking the two drivers in `Steering` follows the bumper modifiers: the second driver's press adds its layer and then Modifier 2 over it, and a Release inside Modifier 2 only removes. The hand-over add of 90.57 is gone. 34 removes more a layout: two on the second driver's Release, 32 the fix pipeline adds to Modifier 2's cleanup functions (R128) |
| 90.61 | [inverted-chord-on-the-steering-left-edge](../findings/2026-10-12-inverted-chord-on-the-steering-left-edge/README.md) | From 90.58. One change on ten inputs a layout: on the left stick's edge of ten Steering layers the cleanup press and its guard chord become one repeating chord with Invert Activation on the same drivers, carrying the press's list command for command. For the open fault [`Steering` ends on a right stick touch](../findings/2026-10-12-steering-ends-on-a-stick-touch/README.md). 90.55 had this chord with longer lists |
| 90.58 | [removes-that-never-take-a-layer-off](../findings/2026-10-12-removes-that-never-take-a-layer-off/README.md) | From 90.57. Only removes are taken out, none added: 1,162 in the default layout and 1,174 in the alternative that never take a layer off, by the [audit of every remove](../findings/2026-10-12-remove-list-audit/README.md). The fourteen clears name 5 to 27 layers where they named 89 (R163), `Steering`'s exit removes `Steering` alone, and no cleanup function names a layer above it that answers the same input (R132). Every log is the same as 90.57's on the simulator |
| 90.57 | [driver-handover-and-fewer-removes](../findings/2026-10-12-driver-handover-and-fewer-removes/README.md) | From 90.56. In the two Steering Modifier 2 layers the first driver's Release hands over to the other driver's layer (R174) and the second driver's Release removes only the Modifier 2 layer: no clear, no 200 ms timer, no cover. 264 removes fewer a layout, among them 28 in the four Gyro Modifier 2 Releases; the stick windows are left as they are |
| 90.56 | [edge-cleanup-press-and-guard](../findings/2026-10-11-edge-cleanup-press-and-guard/README.md) | From 90.55. One change: the left edge of ten Steering layers cleans up with the repeating press and its guard chord again, as in 90.54; only the Entry Guard keeps a chord with Invert Activation (A66) |
| 90.55 | [edge-soft-press-timers](../findings/2026-10-11-edge-soft-press-timers/README.md) | From 90.54. The four timers of the Steering stick are Soft Presses on the left stick's edge (13276; A64, A65); the left edge of ten Steering layers cleans up with one inverted chord, at the default radius; no right pad removes in the four Steering modifier layers; up and down in the W and S layers carry no cleanup; A and D in the stick modifiers send only the key; three removes leave each Modifier 2 entry |
| 90.54 | [hold-timer-on-the-edge](../findings/2026-10-11-hold-timer-on-the-edge/README.md) | From 90.52, not 90.53. One change: in the two Steering stick modifiers the 200 ms chord that adds the Tap Cover moves from up or down to the left stick's edge (A64) |
| 90.53 | [steering-entry-and-edge-chords](../findings/2026-10-10-steering-entry-and-edge-chords/README.md) | The stick's hold timer and cover timer sit on the drivers, in one shared stick modifier, with the reset left on the stick; in the W and S layers up and down add the stick modifier with one chord on the driver and the deflect, with no cleanup; the left stick's edge of ten Steering layers cleans up with one inverted chord, at the default radius; no right pad removes in the Steering modifier layers; left and right send only A and D |
| 90.52 | [stick-lifecycle-on-bumper-pattern](../findings/2026-10-10-stick-lifecycle-on-bumper-pattern/README.md) | The Steering stick deflect follows the bumper modifier lifecycle: the hold timer chords on the deflect, a tap ends on the direction's own Release, the window scrolls at 50 ms, and a second deflect has its own scroll layer (90 layers) |
| 90.51 | [ring-bump-and-modifier-direction](../findings/2026-10-10-ring-bump-and-modifier-direction/README.md) | The two ring pads leave haptics to their binds (override 5); the Steering stick modifiers lose the cleanup on their own direction, under an R130 exception |
| 90.50 | [click-final-feedback](../findings/2026-10-10-click-final-feedback/README.md) | Pad click feedback moves from the entry adds to the final outputs |
| 90.49 | [steering-scroll-and-pad-click-fix](../findings/2026-10-10-steering-scroll-and-pad-click-fix/README.md) | Outer ring radius 13276 in the eight Steering scroll groups; a thumb lifting in a Steering window scrolls; one pad click bump |
| 90.48 | [quiet-gyro-and-guard-handoff](../findings/2026-10-10-quiet-gyro-and-guard-handoff/README.md) | Silent normal/Gyro two-driver hold; Steering adds W/S without redundant Guard removal; atomic Guard handoff retained |
| 90.47 | [quiet-cursor-and-steering-touch](../findings/2026-10-10-quiet-cursor-and-steering-touch/README.md) | Silent delayed Temp Cursor adds; Steering inherits LST/RST; both touch windows override LS up/down with plain W/S |
| 90.46 | [ramp-menu-and-driver-chords](../findings/2026-10-10-ramp-menu-and-driver-chords/README.md) | Both menu entries clear all three ramps before opening their contextual menu; Steering/Guard use quiet repeating driver self-chords; Gyro Off Ramp Up owns its driver exits |
| 90.45 | [right-stick-sensitivity](../findings/2026-10-10-right-stick-sensitivity/README.md) | Right-stick sensitivity 150 → 200 → 250; ramp vertical scales 75%/60% keep the configured vertical target at 150 |
| 90.44 | [steering-entry-and-quiet-drivers](../findings/2026-10-10-steering-entry-and-quiet-drivers/README.md) | Driver-conditioned inward Entry Guard exit; explicit quiet W/S and modifier-release feedback; Steering Modifier 2 retains Steering; dual-driver releases retain Cursor Gyro |
| 90.43 | [steering-entry-and-feedback](../findings/2026-10-09-steering-entry-and-feedback/README.md) | Reuses the fallback slot as Entry Guard; protects held/first movement; preserves held W/S during modifier recovery and prevents stale re-adds; one beep per mode change |
| 90.42 | [fn-haptics-and-steering-clear](../findings/2026-10-09-fn-haptics-and-steering-clear/README.md) | Low feedback on every Fn entry; full-deflection Steering up/down clears its family and shared single-side covers; Fallback Guard retained dormant, with no new layers |
| 90.41 | [low-haptics-and-silent-fn](../findings/2026-10-09-low-haptics-and-silent-fn/README.md) | All explicit enabled haptics use Low; ordinary and Stateful Fn-layer adds are silent |
| 90.40 | [circular-scroll-haptics](../findings/2026-10-09-circular-scroll-haptics/README.md) | Extends 90.38 directly: right-trackpad circular-scroll haptics change from Off to Low in both variants |
| 90.38 | [steering-rtp-and-menu-chords](../findings/2026-10-08-steering-rtp-and-menu-chords/README.md) | Repeating menu chords, RTP access and ordered delayed completion in Steering, near-rim fallback entry and the local inverted-edge return |
| 90.37 | [menu-base-chords](../findings/2026-10-06-menu-base-chords/README.md) | Base's repeating, uninterruptible menu self-chords |
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
[test_scenarios_90_11.py](../tests/scenarios/neptune/test_scenarios_90_11.py); each later
release has its own `tests/scenarios/<controller>/test_scenarios_<version>.py`.
Static contracts and frozen comparisons live separately; follow the
[testing pattern](testing.md) and retain each scenario's release label and source.

## Starting the next release

Copy the newest build folder to `findings/<date>-<slug>/` and point its
`build_candidate.py` at the folder it was copied from. The copy already imports
the scripts from `tools/` (`from tools.audit_command_budget import ...`) and
exports with `tools/convert_vdf.mjs`.

Each `manifest.json` records a SHA-256 of the builder before it. On 2026-10-03
the builders' import lines changed when the scripts moved to `tools/`, so the
hashes in the older manifests are of the builders as built. A rebuild writes
the new hash and the same layout.
