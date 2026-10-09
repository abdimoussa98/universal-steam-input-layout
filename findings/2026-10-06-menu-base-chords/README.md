# Base menu chords and the July gyro comparison (90.37)

**Status:** built and exported locally as **90.37**, 2026-10-06, for both
variants. Build audit clean; 216 simulator scenarios pass. Both variants
were 90.36 before this change. No Deck result yet.

The author asked to compare Base's menu buttons and Gyro Modifier 0–2 against
the [July post-fix layout](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json),
restore the menu chords, and defer the delay test rig. The working hypothesis
for the missing menu Fn layer is now the Base menu activator difference.
This is a candidate cause, not a demonstrated explanation of the failure.

## Exact comparison

`button_menu` is Select / Menu Left; `button_escape` is Start / Menu Right.

| Base input | July post-fix | 90.36 | 90.37 |
|---|---|---|---|
| Select | Self-chord, mask `4096`, repeat on, Interruptable off | Regular Press, repeat on, default interruption | July's activator/settings, current left Entry Point target |
| Start | Self-chord, mask `16384`, repeat on, Interruptable off | Regular Press, repeat on, default interruption | July's activator/settings, current right Entry Point target |

July added the shared `Menu Buttons: Entry Point`; today these are separate
`Menu Left: Entry Point` and `Menu Right: Entry Point` layers. The targets stay
separate. No delay, reset, release, cleanup order, or stateful-menu binding changes.
Both descriptions were read in full; the controls and behavior described remain
accurate, so their wording stays. Both release titles advance to 90.37.

### The active gyro masks and settings already match

Comparison uses **active sources**, with titles mapped across the rename, in
both default and alternative layouts. Group IDs are identifiers, not settings.

| July title | Current title (default) | Mask | Any/All |
|---|---|---|---|
| Base | Base | `211109453778944` | All (`1`) |
| Gyro | Gyro | `211109453758464` | Any (`0`) |
| `*L1: Modifier 0` | `Gyro \| L1: Modifier 0` | `211109453758464` | Any (`0`) |
| `*R1: Modifier 1` | `Gyro \| R1: Modifier 1` | `211109453758464` | Any (`0`) |
| `*L1!R1: Modifier 2` | `Gyro \| L1!R1: Modifier 2` | `211109453758464` | Any (`0`) |
| `*R1!L1: Modifier 2` | `Gyro \| R1!L1: Modifier 2` | `211109453758464` | Any (`0`) |

Alternative uses L2/R2 in those titles, with identical gyro settings. The Base
mask selects both stick touches, both deflections, and both menu buttons.
The Gyro mask selects the four stick inputs only. These are selector values;
runtime response still depends on the exposed stack and Steam inheritance.

All six sources use `gyro_to_mouse`. Base's entire settings object matches:
natural sensitivity 300, rotation calibration 3853, vertical/horizontal ratio
200, conversion style 4, speed deadzone 0, precision speed 300, plus its mask
and All flag. Gyro and its four modifier sources specify only `layer: 1`,
their mask, and Any. They inherit response settings. There is no active gyro
mask or response-setting correction to import from July in this scope.

July also contains dormant gyro groups and mode-shift groups. In `Gyro`,
trigger bindings explicitly target gyro groups 373 (D-pad) and 374
(`gyro_to_mouse`, same four-stick mask/Any). The current layer has no such
gyro mode shifts. The July modifiers also list gyro mode-shift slots, which
are not their normal active source. Copying whole groups would restore older
structure beyond this request. The current Temp Cursor Gyro response overlays,
menu-disabled gyro sources and ramp suppression can change effective response
while the matching activation sources are underneath; those are retained.

The reference is already in title form and has duplicate `DEPRECATED` titles.
It is read only, never round-tripped or installed. Both working layouts have
unique titles and pass layer/preset ordering preflight.

## Inheritance and held inputs

- Base and Gyro: Gyro inherits Base's menu inputs. Stick Entry Points, Tap
  Covers and Temporary Gyro also omit those menu inputs, so a thumb resting
  on either stick can expose the new Base chord. Ramp and ordinary pad layers
  can expose it too, subject to any intervening input override.
- Modifier parents supply their own navigation-key chords. Their covers
  inherit those parent inputs; cursor overlays keep their self-cancellation
  route. No Base menu entry is substituted for modifier navigation.
- Menu Entry/Fn layers and their guards keep their existing inputs. Once an
  Entry Point lands, its hold delay and release handle the button. Merely
  changing Base does not prove that a stick-touch cleanup guard works in Steam.
- Steering, its fallback guard, and Cursor Gyro retain their stateful-menu
  entries; Gamepad and Menu Keys retain their explicit overrides.
- Double Tap windows retain explicit menu blocks or ordered exits. A button
  held across a window's expiry must re-enter through Base's repeating chord
  even if a removal does not fire newly exposed inputs immediately (A9).
  Repeat is preserved for that reason (R114). Always On entry/exit order stays.
- The self-selector must be recognized when the input first answers, including
  re-exposure (A36). The simulator already models this. Its passing result
  cannot distinguish the observed Steam failure from a scheduling/guard issue.

## The issue and the deferred tests

The missing Fn while a thumb rests on a stick was previously discussed in the
[menu stick-touch audit](../2026-10-06-menu-entry-point-stick-touches/README.md)
and [cleanup-order change](../2026-10-06-cleanup-entry-order/README.md).
Track this menu activator difference as the current candidate cause. The
separate historical interrupted-delay observation is still evidence; it is
not disproved by this comparison. No delay rule or reset is removed.

The [delay test plan](../../plans/2026-10-06-delay-test-layout.md) is deferred
to [todos](../../todos.md#deferred-delay-tests-and-the-menu-entry-issue).
Its scenarios stay intact for later work; no test rig is built in this release.

On a fresh Deck load, compare 90.36 and 90.37 with a thumb resting on LS, then
RS: hold Select and Start separately for a second, looking for Fn at 200 ms.
Also check a thumb added during the hold, a quick tap, and a menu button held
through a stick Double Tap window. If Fn still fails, record whether the Entry
Point lands and stays; that separates entry failure from its delayed Fn action.
If only 90.37 works, that supports the chord/interruption change as a workaround;
it does not by itself establish Steam's internal cause.

## Flow audit review

Changing Base triggers R139 review for existing inherited inputs it provides,
including inputs untouched by the patch. The first build audit passed Budget,
Window and Cleanup but requested review of `right_trackpad/touch` on the four
Gyro modifiers and the two Scroll layers, in both variants.

Each inherits one of two bindings: Base's repeating `RTP: Entry Point` add,
or the explicit empty touch on `Steering | LS: Fallback Guard`. The latter
preserves Steering's documented mouse-only right pad even while using a
modifier or scroll layer from the fallback. These providers and their bindings
are unchanged from 90.36. The exact two-input comparison test also verifies
that every other layout field apart from the release title is unchanged.

Recorded an R139 allowance for those six layers and that one input in
`steam_layout/flow_config.json`, based on this review. No pad binding was changed,
and no general audit exemption was added.

## Build and validation

[build_candidate.py](build_candidate.py) extends the frozen 90.36 builder.
It copies only July's two Base chord settings and retains the current bindings,
then uses the existing fix pipeline and title/ID round-trip checks.

- [Static comparison tests](../../tests/test_menu_base_chords.py): generated
  working layouts, exact two-input diff against 90.36, and reference gyro equality.
- [Scenarios M1–M3](../../tests/test_scenarios_90_37.py): resting thumbs,
  held-button re-exposure after a window, and recovery after a missed release,
  in both variants. Existing menu/modifier scenarios cover taps and navigation.
- Build audit, change reports and scenario assumption report accompany release
  validation. Simulator results are not Deck verification.

Validation: [all four build audits passed](build-audit.txt) for both variants;
216 scenario tests, 27 Neptune regression tests, 12 layout hygiene/rule tests,
27 rule-registry tests, 15 exception-register tests, four cleanup-order tests
and the two new comparison tests passed. Source ordering, unique working titles and resolved references
passed. The VDF exporter verified keys, values and stored order for both files.
The reviewed inherited pad providers/activators are saved in
[inherited-pad-review.json](inherited-pad-review.json).

Both JSON/VDF pairs are in `neptune/`, with identical backups under
`versions/neptune/90.37/`; [installation hashes](neptune-installation.json).
No commit or Steam upload was performed.

### Full test-suite follow-up, 2026-10-06

The complete active suite was run after the author asked whether all tests
had been run. All **941 Python tests across 83 modules passed**, in 1,309.680
seconds, and all **6 VDF exporter tests passed**. No failures, errors or skips.
The Python run used the documented `PYTHONPATH=.:tests` setup and every
`tests/test_*.py` module, in sorted order; the exporter command was
`node --test tests/test_convert_vdf.mjs`. Archived suites are not part of the
repository's documented active suite.

Logs: [Python suite](full-python-tests.txt), [VDF exporter](exporter-tests.txt).
The earlier targeted checks above were not the full suite; this follow-up is.
No layout changes were needed. The clean four-audit result still applies,
and Deck behavior remains unverified.
