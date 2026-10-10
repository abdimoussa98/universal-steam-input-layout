# Quiet Temp Cursor entry and Steering stick-touch inheritance

Status: **implemented as 90.47**, both variants, on 2026-10-10. All four
audits pass; 311 scenarios and 304 regression methods pass. JSON/VDF exports
and matching version backups are saved. See the
[release record](../findings/2026-10-10-quiet-cursor-and-steering-touch/README.md).
The design below records the approved changes from 90.46.

The author selected LST/RST inheritance in Steering on 2026-10-10 and
confirmed that the double-tap windows should block driver-layer entry.
During those windows, explicitly bind left-stick up/down to plain **W/S**
so Steering's layer-removal commands cannot be inherited. This follows
existing rules R140/R141. It replaces the earlier proposal to close the
window and clear Steering. The cursor-add haptic changes remain in scope.

Here LST/RST means the **left/right stick-touch gesture families**, including
their Entry Point, Tap Cover, Double Tap and Temporary Gyro layers. These are
separate from the bumper/trigger **Temp Cursor Gyro** response overlays.

## 1. Silence the bumper/trigger Temp Cursor adds

Change the existing delayed Chorded Press's `haptic_intensity` from `"1"`
to `"0"` in these four owners per variant:

| Default owner and input | Alternative owner and input |
|---|---|
| `L1: Modifier 0`, left bumper | `L2: Modifier 0`, left trigger soft pull |
| `R1: Modifier 1`, right bumper | `R2: Modifier 1`, right trigger soft pull |
| `Gyro \| L1: Modifier 0`, left bumper | `Gyro \| L2: Modifier 0`, left trigger soft pull |
| `Gyro \| R1: Modifier 1`, right bumper | `Gyro \| R2: Modifier 1`, right trigger soft pull |

These are **eight activator settings in total**. The changes belong in the
modifier owners that add the cursor overlays; the Temp Cursor Gyro layers
themselves need no edits.

Keep the 200 ms delay, owner chord, nonrepeating apply, reset, release,
cancellation and gyro response settings. The add commands already request
no beep. Each owner also has two stick-touch Release completion adds; all
eight of those per variant already have haptics Off. A scan of all groups
and disabled activator banks found no additional Temp Cursor add routes.

Fn bumps, Steering full-clear feedback, and the LST/RST second-touch bump
are separate behaviors and stay as configured.

Update the current Low expectation in
[`tests/test_neptune_cursor.py`](../tests/test_neptune_cursor.py), the R125
example in [Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md),
and the outdated TC2 pulse instruction in
[Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md).
Keep historical release records intact. An in-memory haptic-only candidate
remained an exact `apply_all` fixed point in both variants.

## 2. Inherit the touch gestures with protected windows

`Steering` currently replaces both stick-touch inputs with quiet Release
cleanup of that side's Entry Point, Tap Cover and Temporary Gyro. These are
release-only overrides, not empty Press bindings. Deleting the whole input
node exposes Base's repeating touch-entry binding and its helper lifecycle.

The shared touch helpers will behave as follows:

| Gesture | Inherited behavior in Steering |
|---|---|
| Touch and keep holding | Entry Point, then Tap Cover after 150 ms; release removes the helpers. |
| Short touch, then lift | Open that stick's Double Tap window for 200 ms. |
| Touch again inside the window | Remove the window, add Entry Point and Temporary Gyro; lifting ends the temporary gyro. |
| Driver press during the window | Scroll down/up instead of entering S/W. A short press is consumed; a held press can acquire the driver after expiry. |
| Start/Select during the window | A short press is blocked; a held menu must wait for the window to end. |
| Right-stick deflection during the window | The window blocks the inherited ramp entry. |
| Left-stick up/down during the window | Explicit Regular Press W/S output, with no layer commands or haptic feedback. Steering remains active for the window's lifetime. |

The driver controls are bumpers in default and trigger soft pulls in
alternative. Their inherited layer adds are blocked by the existing direct
scroll replacements. These controls are not currently empty bindings: a
short press scrolls. Preserve those replacements, the existing menu blocks,
and window timing. The author accepts this temporary driver isolation.

The new W/S replacements are necessary because a bare two-input deletion
would expose an unsafe path:

1. In armed Steering, briefly touch and release RS.
2. `RST: Double Tap` opens its 200 ms Always On window.
3. Fully deflect LS up or down.
4. The inherited Steering clear removes Steering while the RST window is
   still active. The current clear list does not include either ordinary
   stick-touch Double Tap window.

R140 requires a window to handle an inherited layer-changing route, using
the obvious key output where possible. R141 explicitly says a block must
never be a removal. Override north/south in each window with W/S; do not
add touch-window removals to Steering's clear arrays or register an
exception that allows the clear through. These rules already exist in
[Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)
and are implemented by `steam_layout/fixes/window_routes.py`.

## 3. Changes by layer

Use the existing layers and keep the total at **88**.

| Layer | Planned edit |
|---|---|
| `Steering` | Delete only `joystick/touch` and `right_joystick/touch`, exposing Base's touch entries. Preserve both sources' other settings and bindings. |
| `LST: Double Tap` | Add explicit `joystick/dpad_north` → `key_press W` and `joystick/dpad_south` → `key_press S`. Use one `Full_Press` activator per direction with haptics Off and no layer command, delay or repeat. |
| `RST: Double Tap` | Add the same two direction overrides. |
| `Steering`, north and south | Keep the existing full-deflection Soft Press clear unchanged: threshold `29031`, 50 ms repeats, existing beep and Low bump. It is unavailable while either window replaces these directions. |
| `Steering \| LS: Entry Guard` | Keep its two touch overrides and movement/edge exits. Touching or lifting a thumb must not end first-movement protection or open touch helpers over the guard. |
| W/S, Steering Mod 0/1/2, covers, menu and ramp owners | Preserve their existing touch replacements and guarded recovery; exposing Base through Steering must not override these higher owners. |
| Other shared LST/RST helpers | Reuse existing Entry Point, Tap Cover and Temporary Gyro gestures, gyro selectors, timing and feedback. |

When Entry Guard disarms, Base's repeating touch entries can resume for a
thumb that is still resting on a stick. This must work with either result of
the unverified exposed-held-input assumption A9. Driver/menu handoffs keep
their current explicit removal of Entry Guard.

Window protection ends when that window expires or its second-touch exit
runs. The then-exposed lower binding resumes. In armed Steering with no
driver covering the direction, a still-held full up/down can therefore run
the existing repeating clear after the window ends; a fresh push is not
required. This change does not extend Entry Guard's first-push protection
to every later double-tap window.

The four new W/S bindings per variant also apply when these shared windows
are entered from Base/Gyro. Verify their normal W/S movement and release
behavior there as well as Steering. No driver/menu adds are introduced into
the windows.

## 4. Evidence and remaining validation

Both live layouts passed the layer-order, preset-order, sequential-ID and
unique-title preflight. Numeric commands were converted in memory or in
temporary files before inspection. The initial inheritance investigation
established:

- All 16 tested short driver presses during the touch windows scrolled;
  all 16 short Start taps were swallowed, across both variants and A9/A32
  settings. Held drivers acquired W after the window expired.
- All 16 guarded entries with resting thumbs retained Entry Guard;
  helpers resumed after movement disarmed it and subsequently cleaned up.

Earlier cleanup prototypes tested adding window removals to Steering. That
approach is superseded; their passing counts are not validation of the
selected W/S replacement design.

The revised temporary W/S candidate passed **116/116 focused dynamic
probes**. A 96-case matrix covered both variants, both windows, Base/Gyro/
Steering contexts, up/down, A9 and A32. The windows kept plain W/S output
with no layer mutation, beep or haptic through 199 ms. After the 200 ms
expiry, the exposed full-deflection Steering clear resumed within its
50 ms retry interval; Base/Gyro kept their movement output. Twenty additional
cases covered actual touch entry, driver/menu restrictions, second-touch
Temporary Gyro and Entry Guard. Four explicit window-over-Steering stack
checks found no open inherited routes with the replacements present.
These are simulator results, not full release or native Steam validation.

The initial temporary Window audit passed, but a manual
`check_stack(window, [Base, Steering])` review revealed that its automatically
derived stacks omitted these new inherited Steering routes. Do not treat
that pass as full coverage.

Implementation and validation sequence:

1. Add explicit Steering-under-LST/RST-window stacks, including Gyro where
   applicable, to the audit coverage or repair the missing derivation.
   Demonstrate that deleting either window's north/south replacement fails
   the Window audit. Then install the four W/S replacements per variant and
   verify that those routes are handled and the fixes pipeline preserves
   them. Use existing R140/R141; no new exception is needed.
2. Test both directions, both drivers, both menu buttons, both stick-touch
   orders, real short-touch double taps, and long holds. Run with Gyro on/off
   and both outcomes of A9 and timer-tie ordering A32. During an active
   window, W/S must work without adding/removing Steering layers, resetting
   the window timer, or requesting the Steering clear's beep/haptic.
3. Preserve held-stick and centered-first-push Entry Guard protection.
   Include guard disarm with thumbs held, release of up/down before window
   expiry, held-full-deflection exposure after expiry, and second-touch
   exits. Check W/S and Mod 0/1/2 handoffs, missed releases, menu/Fn paths,
   and all three ramp stages. Verify no stuck movement or orphaned helper
   after releases settle.
4. Keep the unrelated held-full-deflection Mod 2 release gap and deferred
   two-driver release-order redesign separate from this change.

Extend the frozen 90.46 builder, recheck the requested edits and
fixes-pipeline fixed point, run the appropriate existing
cursor/Steering scenarios and Budget, Window, Flow and Cleanup audits.
Review the descriptions, bump the release once, export both JSON/VDF pairs
and save matching version backups. These steps are complete for 90.47;
native Steam checks remain listed in the release record.
