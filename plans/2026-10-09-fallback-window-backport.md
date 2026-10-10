# Plan to update the 90.32 fallback window for testing

Status: implemented as **90.39 fallback-window testing**, 2026-10-09, for both variants. See the [build, exports and validation record](../findings/2026-10-09-fallback-window-backport/README.md). The approved plan below bases the candidate on **90.32**, brings forward compatible fixes through **90.38**, and preserves the one-second removal window. Deck testing remains pending.

Implementation findings: the retained Steering entry/edge bindings already prevent hidden ramp layers, so no extra driver ramp cleanup was needed. New RTP scenarios exposed pad helpers remaining beneath Steering windows; their self-first exits now retain the required RTP removals through a candidate-local rule entry. Candidate snapshots use distinct filenames so the live 90.38 baseline stays separate.

The baseline is `versions/neptune/90.32/`, with 90 action layers. Default uses L1/R1 as drivers; alternative uses L2/R2. Start from the frozen [90.32 builder](../findings/2026-10-04-fallback-window-replacements/build_candidate.py), and compare its output with the snapshots before adding changes. Build into a new findings folder as a separate testing candidate. The existing 90.32 exports remain the control for Deck comparisons.

## Behavior to preserve

- Keep `Steering | LS: Entry Guard`, `Steering | LS: Fallback Hold`, and `Steering | LS: Fallback Window`. Entering Steering retains the original Entry Guard route.
- In Steering without a driver held, LS up/down applies Fallback Hold, then Fallback Window. The window is added last and lasts 1000 ms.
- During that second, W/S works and the strong pulse repeats every 250 ms. Releasing the direction/edge or the documented touches removes the window first, then the Hold, and keeps Steering.
- During the window, drivers send scroll up/down and Start/Select send Tab/Escape. These inputs do not enter menu layers or end the window.
- Once the second finishes, the window removes itself. Releasing up/down, or pressing a driver/menu button, exits Steering through Fallback Hold. A driver/menu button held across expiry must still trigger its repeating exit.
- Keep the original eight-way stick configuration and entry threshold for this test. Keep the current 90.32 stick-edge restrictions except for a separately identified hidden-exit correction.

These are the [90.31 lifecycle](../findings/2026-10-04-fallback-window/README.md) with the [90.32 replacements](../findings/2026-10-04-fallback-window-replacements/README.md). New menu-entry chords must not overwrite the Entry Guard's guarded key outputs, the Window's replacement outputs, or the Hold's exit bindings.

## Every later release and its applicability

| Release | Later change | Treatment in this candidate |
|---|---|---|
| [90.33](../findings/2026-10-05-steering-fallback-guard/README.md) | Replaces Entry Guard with a persistent Fallback Guard; deletes Hold and Window; changes Steering entry, driver behavior, and cleanup targets | Exclude this redesign. Keep the 90.32 layer family and all its cleanup references. The broad changes to transition/menu/Gamepad cleanup lists largely follow that deletion and rename, rather than representing independent fixes to copy. |
| 90.33 | Gyro Modifier 2 quick-tap releases also clear the other Gyro Modifier 2, Base modifiers, and Steering | Adapt the full-clear behavior to the retained 90.32 family; see the cleanup step below. Do not create a Fallback Guard or import its driver-to-Gyro route. |
| 90.33 | Exception register supports build-scoped `where` entries | Use the current tooling. Retain existing Fallback Hold exceptions; scope any new candidate-specific exceptions so historical and live builders retain their contracts. |
| [90.34](../findings/2026-10-05-steering-four-way-and-open-edges/README.md) | Opens Steering's stick edges, enabling right-stick turn assist; four-way Steering, eight-way fallback; immediate repeating fallback entry | Opening the edges and changing the stick layout are optional behavior changes, excluded from the first test candidate. 90.32 already repeats its immediate Hold/Window entry. Its timed window must continue blocking inherited layer changes. |
| 90.34 | Derived firing-button replacements and alternative-trigger blocks in windows | Recalculate from the candidate's actual reachable stacks. These fixes depended on the newly open edges and ramp layers; do not copy the resulting bindings indiscriminately. |
| [90.35](../findings/2026-10-06-steering-fallback-swap/README.md) | Swaps Steering and Fallback Guard to work around four-way settings carrying into an eight-way overlay; copies menu/pad groups into standalone fallback | Exclude. This candidate keeps Steering below its original eight-way helpers, so the swap and duplicated standalone-fallback bindings do not apply. The reported Steam settings inheritance problem is a reason to avoid importing four-way Steering alone. |
| 90.35 | Driver entry removes all three ramp layers before adding the driver layer | Review and apply wherever a reachable ramp can be left under a driver that covers its exit. Preserve the existing Hold/Entry Guard cleanup too. With the 90.32 edges retained, the new 90.34/90.35 ramp-entry routes are absent; establish the candidate's reachable route before adding removals. |
| 90.35 | Beep when clearing the standalone Fallback Guard | Exclude the nonexistent target. Preserve the original Steering exit beep and strong feedback. |
| [90.36](../findings/2026-10-06-cleanup-entry-order/README.md) | Cleanup inputs stored as Regular Press, guard, Release | Include throughout both candidates, including the retained Entry Guard and Hold. Discover the inputs from this candidate; the reported 121 reordered inputs belonged to 90.35 and is not a target count. |
| [90.37](../findings/2026-10-06-menu-base-chords/README.md) | Base Start/Select become repeating, uninterruptible self-chords | Include, retaining the separate left/right Entry Point targets. |
| 90.37 | Gyro comparison against July | No gyro correction to import: active gyro masks and response settings already matched in that comparison. Preserve the candidate's response settings. |
| [90.38](../findings/2026-10-08-steering-rtp-and-menu-chords/README.md) | Same menu self-chords in Steering, Fallback Guard, Cursor Gyro | Include in Steering and Cursor Gyro. Fallback Guard does not exist in 90.32; its changes must not be mapped onto the original Hold or Window. |
| 90.38 | Opposite-menu-button entry chords repeat in six menu owners | Include all six, retaining the first-button condition and targets. |
| 90.38 | RTP gestures available in ordinary Steering contexts; inherited Base touch entry is silent | Include, adapted to the retained Entry Guard/Hold and their Window. Keep timed-window isolation. |
| 90.38 | Six delayed applies and twelve stick-touch completions add their target before clearing ordinary RTP helpers | Include on the matching six owners. Preserve their conditions and delays; preserve self-first removal of any active Always On window. |
| 90.38 | RTP Double Tap blocks ambiguous LS directions; Steering Double Tap pad exits clear underlying RTP Entry Point | Include and regenerate the window/cleanup fixes for the additional Fallback Window. This is necessary for the new RTP routes. |
| 90.38 | Up/down fallback entry uses Soft Press threshold 29031; inverted driver chord adds Steering on inward edge | Exclude from the first candidate. These change fallback entry/return, and the inverted return targets the later persistent fallback design. |
| After 90.35/90.36 | Menu touch audit and delay-interruption inventory; proposed delay test rig | Use the findings to choose regression scenarios. The audits introduced no separate binding fix, and the delay rig remains deferred. |

The proposed scope therefore includes shared reliability fixes and RTP access, while preserving the old fallback gesture. Four-way Steering, open-edge turn assist, and near-rim fallback entry can be separate experiments after the removal-window test.

## Implementation sequence

### 1. Establish the candidate and a reproducible baseline

Create `findings/2026-10-09-fallback-window-backport/` with a new builder extending the frozen 90.32 builder. Require its unmodified result to match each 90.32 snapshot after accounting for metadata and the documented fix pipeline. Record source hashes and any current-tooling differences before changing bindings.

Work in readable title form. Validate layer list order, preset block order, sequential preset IDs, and unique titles before conversion. Keep 90 layers and the existing layer identities. Use active groups and mode-shift targets for behavior; raw numeric/group-ID diffs are insufficient.

Generate candidates in the findings folder and test them explicitly by path. Keep the live builder's working-layout equality tests attached to the live release. Give the candidate its own reproducibility tests and scenario loader instead of making archived tests accidentally read `neptune/`.

### 2. Normalize cleanup entry order

Reuse the `cleanup_inputs`/`reorder` logic from the 90.36 builder on the 90.32-derived data. Every applicable input stores `Full_Press`, `chord`, then `release`, omitting types it does not have. Preserve individual entries, settings, selector conditions, and binding-array order.

Assert that this step changes only activator type order. Check the four menu Entry Points' stick touches, both Scroll layers, modifiers, and the retained fallback helpers. Repeat the check after the fix pipeline so later generated cleanups cannot reintroduce the old ordering. Verify the VDF preserves the stored order too.

### 3. Bring forward menu entry fixes

Convert Start/Select in **Base, Steering, and Cursor Gyro** to repeating, uninterruptible self-chords. Select uses mask `4096`; Start uses `16384`. Base keeps its ordinary Entry Point targets; Steering and Cursor Gyro keep their Stateful targets. This is six entries per variant.

In the two ordinary menu Entry Points, two ordinary Fn layers, and two Stateful menu Entry Points, enable repeating, uninterruptible entry on the opposite menu button's existing first-button chord. Keep its selector and target. Stateful Fn Enter/Backspace outputs remain key outputs.

Retain 200 ms Fn delays, 250 ms resets, interruptible guarded cleanups, modifier navigation outputs, Gamepad behavior, and window-specific replacements. Classify by purpose before changing a menu binding; neither a replacement key nor a fallback exit is a menu entry.

### 4. Adapt full clears and investigate hidden ramp exits

Carry forward 90.33's Gyro Modifier 2 full-clear intent on both release inputs in both modifier orders. Retain removal of the opposite Gyro Modifier 2 and four Base modifiers. Resolve the Steering-family cleanup against this candidate's Entry Guard, Hold, Window, driver helpers and covers; no command may name the later Fallback Guard.

Trace the reachable stacks and retain justified cleanup scope. An early exit from an active Always On window removes that window before any unrelated layer command. Do not put a Gyro full-clear binding over the Fallback Window's scroll/Tab/Escape replacements. Verify short two-driver clears separately from held two-driver transitions and menu-plus-stick clears, including which exits preserve Gyro.

For the 90.35 ramp correction, trace entry into Steering with each ramp stage already active, a driver pressed during the 5 ms initial ramp delay, and a held driver exposed by cleanup. If a driver can cover a ramp's exit, remove `Gyro Off Ramp Up`, `Turning Ramp Up 0`, and `Turning Ramp Up 1` before adding that driver layer, in the same entry. Preserve the old driver entry's Hold/Entry Guard removals. If all such routes are excluded by the retained edge/transition bindings, record that result and leave the fix conditional on enabling open edges later.

### 5. Restore RTP access and complete delayed targets in order

Remove Steering's explicit empty right-pad touch source when its only input is that block, as in 90.38. Confirm mouse response, click routing, and Base's silent repeating RTP Entry Point add are inherited correctly. Trace ordinary Entry Guard, Hold, driver, cover, and menu contexts; a pending ordinary delay alone is not a reason to block RTP.

Apply the 90.38 completion change to these six owners, with L1/R1 mapped to L2/R2 for alternative:

| Owner | Delayed target |
|---|---|
| `Steering | LS Down: Modifier 0` | `Steering | LS: Tap Cover` |
| `Steering | LS Up: Modifier 1` | `Steering | LS: Tap Cover` |
| `Steering | R1!L1: Modifier 2` | `L1: Tap Cover` |
| `Steering | L1!R1: Modifier 2` | `R1: Tap Cover` |
| `Stateful | Menu Left: Entry Point` | `Stateful | Menu Left: Fn Layer` |
| `Stateful | Menu Right: Entry Point` | `Stateful | Menu Right: Fn Layer` |

For each delayed apply and its two existing stick-touch release completions, add the valid target first, then clear the applicable non-window RTP helpers: Entry Point, Tap Cover, Circular Scroll, Click Entry Point, Mouse Buttons, Middle Click. Preserve any existing stick-helper cleanup and directional/owner conditions. Arrays execute bottom to top. Do not add a new unconditional RTP-touch-release completion or attach this cleanup to every face-button cover entry.

`RTP: Double Tap` is an Always On window and cannot be treated as an ordinary helper removed after the add. Its isolation and self-first exits remain mandatory.

### 6. Rebuild isolation for the restored window

Review both orders: RTP already active when fallback begins, and RTP touched while fallback is active. Include ordinary RTP helpers and RTP Double Tap, held clicks, and missed releases. The restored Fallback Window introduces stacks absent from 90.38.

Keep the Fallback Window's own touch replacement/exit, its 1000 ms timer, and its driver/menu replacement outputs. While it is active, inherited inputs must not add RTP layers, ramps, menu layers, or a second Always On window. On entry, finish any required ordinary-helper cleanup before adding Hold and then Window. If a different Always On window is active, entry must be blocked by it or leave it first.

In RTP Double Tap, retain explicit blocks for the four ambiguous LS directions and verify no underlying fallback add/exit escapes. Account for its 150 ms movement suppression in the test description. In Steering's two Double Tap windows, preserve self-first pad-release exits followed by removal of the underlying RTP Entry Point where reachable. Apply the same ownership review to Fallback Window's pad release: remove itself first, then Hold and any proven underlying RTP cleanup. Retain useful surviving layers instead of copying a maximal removal list.

Run the current fix pipeline, inspect every resulting change, and require a fixed point. Recalculate derived replacements and cleanup lists from this candidate rather than copying 90.34/90.38's generated output. Scope Flow allowances to the actual inherited providers; do not restore obsolete global right-pad exemptions or import the persistent Fallback Guard's inverted-edge exception.

## Verification and delivery

Add candidate-specific tests based on the archived [90.31 scenarios](../archived/fallback-window/tests/test_scenarios_90_31.py) and [90.32 scenarios](../archived/fallback-window/tests/test_scenarios_90_32.py). Their existing `ScenarioCase` loads working layouts, so reuse the gestures with an explicit candidate loader. Preserve the historical files.

| Area | Required checks in both variants |
|---|---|
| Original fallback | Up and down; release before expiry; release after expiry; direction/edge/touch exits; pulses; repeated entry; already-held stick; missed-release recovery. Test just before, at, and after 1000 ms. |
| Window replacements | Tap each driver/menu button inside the second; multiple taps do not restart it; hold a button across expiry; press after expiry. Original 90.32 outputs and exits remain. |
| Cleanup ordering | All discovered recovery inputs have the specified stored order; guarded recovery removals remain interruptible; exported VDF order agrees. |
| Menu | Resting LS/RS thumbs, touch during hold, lift during hold, quick tap, Fn hold, both menu orders, missed release, held-button re-entry after a window. Verify original Entry Guard/Hold/Window menu overrides. |
| RTP | Touch before/after Steering and fallback entry; hold, tap, double tap, circular scroll, clicks; touch release and missed release; silent touch and strong click settings. |
| Delayed completion | Six delayed entries and twelve stick-touch completions; target before ordinary RTP cleanup; correct owner/direction; no reapplication from a completed cover. |
| Isolation | Every Always On window, particularly restored Fallback Window and RTP Double Tap; no unrelated mutations; self-first exits; window-last entry; no timer restart from ordinary cleanup. |
| Full clears and ramps | Both driver orders and release orders; Gyro/Base/Steering/cursor survivors; no retained fallback helpers after a full clear; reachable hidden ramp exits and alternative soft/full trigger distinctions. |

Require Budget, Window, Flow, and Cleanup audits on the candidate paths, the candidate regression/scenario tests, title/ID roundtrip, and VDF exporter validation. Run the documented active Python suite and Node exporter tests after integration to check shared tooling and frozen builders. Do not expect current-release fallback-swap scenarios to describe this candidate; preserve their original fixtures and add separate candidate expectations.

Use `python3 -m tools.change_report` against both 90.32 and 90.38: the first exposes every backported change, the second identifies deliberate design differences. Record test output, build hashes, change reports, and assumption dependencies in the findings folder.

For delivery, follow the layout-apply skill: review the full descriptions, assign the next unused release number once to both variants (90.39 if still available), label the titles as fallback-window testing, export sibling JSON/VDF pairs, and save matching `versions/neptune/<version>/` snapshots. Keep candidate outputs in the findings folder until selected as the working layout. Historical snapshots are immutable.

On a fresh Deck load, compare untouched 90.32 with the candidate. First verify the one-second fallback behavior alone; then menu holds with resting thumbs; then RTP interactions and full clears. Stored activator order, held-input scheduling, release delivery and haptic feel remain physical checks. The 90.36 order change and 90.37 menu chords are proposed remedies for the reported Fn failure, not established explanations of Steam's internal cause.

## Review evidence

Before implementation, the plan was checked against both variants of every saved release from 90.32 through 90.38, their title-resolved per-release change reports, the frozen builders, and the release records linked above. All fourteen snapshots passed layer/preset ordering, sequential-ID, and unique-title preflight. Both untouched 90.32 snapshots also passed the current Budget, Window, Flow, and Cleanup audits. Final implementation results are recorded in the linked build record.
