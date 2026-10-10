# Haptic levels in the current layouts

Audit of both live **90.40** variants on 2026-10-09. Layouts were read only;
no settings, versions or exports were changed. Levels are **0 Off, 1 Low,
2 Medium, 3 High**. A configured level describes a binding or mode, not how
many pulses a complete gesture produces.

## Main findings

- **Circular scrolling is Low; entering it is High.** The right-pad scrollwheel
  group is 1. The north/south entry bindings in `RTP: Double Tap` remain 3.
- **Pad clicks have multiple High feedback sources.** Base's click entry and
  the final centre-click output both specify 3. Arrow/Back/Forward outputs also
  specify 3. This is the existing two-source design documented in the
  [pad-click findings](../2026-10-03-pad-click-exits/README.md#haptics), not a
  measurement of the number of pulses Steam produces.
- **Right-pad button scrolling has separate settings to consider.** In
  `RTP: Mouse Buttons`, north/south wheel activators are explicitly Off, but
  the D-pad mode's `haptic_intensity_override` is High. These are separate
  feedback sources. The static audit cannot establish their combined feel.
- **Four High activators per variant repeat at a configured 50 ms.** They are
  Steering north/south entering the fallback guard and the guard's two driver
  inputs returning to Steering. The driver inputs are L1/R1 in default and
  L2/R2 in alternative. The actions change layers and normally replace their
  own bindings; this is not proof of sustained 20 Hz vibration. See the
  [timing limitations](../../resources/Delay%20Timers%20and%20Repeat%20Rates.md).
- **Unspecified does not mean Off.** Base gyro has no explicit intensity in
  these files; an earlier native-client inspection documented an Off default.
  Gamepad pad clicks and many cleanup activators also omit intensity. Unknown
  mode/client defaults and inherited settings must not be reported as explicit
  silence.

## Feedback by interaction

These levels apply to both variants except where noted. Modifier names are
L1/R1 in default and L2/R2 in alternative.

| Interaction or mode | Configured level | Detail |
|---|---|---|
| Right-pad circular scroll movement | Low | Mode setting; click and release activators in that mode are Off |
| Right-pad double-tap north/south entry into circular scroll | High | Entry confirmation; distinct from the scrollwheel's Low setting |
| Left-pad swipes | Low | Four directions in Base and each of the 11 Double Tap windows, 48 activators |
| Start/Select hold in Gamepad | Low | Two Long Press activators, threshold 200 ms |
| Both sticks' four directions in Fn layers | Medium | Ordinary and Stateful Menu Left/Right Fn layers, 32 activators |
| Trigger click feedback in Double Tap windows | Medium | 12 activators in default; 14 in alternative; exact owners below |
| Double touch of either stick, entering Temporary Gyro | High | LST/RST Double Tap touch activators |
| Modifier hold entering Temp Cursor Gyro | High | Four normal/Gyro parent bindings; configured delay 200 ms |
| Modifier 2 hold entering the combined Tap Cover | High | Both modifier orders, normal and Gyro; configured delay 200 ms |
| Steering Modifier 2 hold entering a modifier Tap Cover | High | Both modifier orders; configured delay 200 ms |
| Steering north/south entering fallback walking | High | Two Soft Press activators; repeat enabled, 50 ms |
| Fallback driver press returning to Steering | High | Two activators; repeat enabled, 50 ms |
| Start/Select release confirming a mode transition | High | Transition Set 0, 1 and 2; six activators |
| Holding the second menu button to enter Menu Keys | High | Both menu-button orders; configured delay 200 ms |
| Initial left/right pad click in Base | High | Soft Press entry; separate repeating entry is Off |
| Centre-click outputs | High | Right pad Middle Mouse; left pad Caps Lock |
| Left-pad outer arrow outputs | High | All four activators; D-pad mode override is also High |
| Right-pad outer Back/Forward outputs | High | Both activators; D-pad mode override is also High |
| Right-pad outer up/down wheel outputs | Off at activator | Immediate and repeating wheel activators are 0; enclosing D-pad mode override is 3 |
| Normal right-pad mouse mode | Off | Base mode setting |
| Temp Cursor Gyro and persistent Cursor Gyro movement | Off | Three explicit mode settings; their entry pulses are separate |
| Pad Click Entry Point modes | Off | Left and right D-pad mode overrides |
| Physical D-pad mode overrides | Off | Base, Base mode shift, Gamepad, Menu Keys and both combined-menu Double Tap windows |
| Cleanup, release and reset feedback | Mixed explicit Off / unspecified | Complete inventory distinguishes each binding; no assumption that an omitted value is 0 |
| Gamepad trackpad clicks | Unspecified | Neither the local single-button mode nor click activator states intensity |
| Normal Base gyro movement | Unspecified locally | Earlier native inspection found default 0; this audit did not reverify the installed client's native default |

Medium trigger-click owners differ between variants:

| Variant | Windows with Medium on both trigger clicks |
|---|---|
| Default | L1 Double Tap, R1 Double Tap, Menu Left Double Tap, Menu Right Double Tap, Menu Left!Right Double Tap, Menu Right!Left Double Tap |
| Alternative | LST Double Tap, RST Double Tap, RTP Double Tap, Menu Left Double Tap, Menu Right Double Tap, Menu Left!Right Double Tap, Menu Right!Left Double Tap |

## Counts of explicit intensity settings

These count saved fields, including mode overrides and activators, not unique
gestures or physical pulses. Shared/inherited behavior is not counted again
for each possible stack.

| Level | Default | Alternative |
|---|---:|---:|
| Off | 365 | 347 |
| Low | 51 | 51 |
| Medium | 44 | 46 |
| High | 38 | 38 |
| Total intensity fields | 498 | 482 |

Each variant also has three `flickstick_haptic_bump_per_angle: "1"` fields in
the two Temp Cursor Gyro modes and persistent Cursor Gyro. This is an angular
spacing parameter, **not Low intensity**; those modes' intensity is Off.
The [native-default record](../2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#normal-value-verification)
documents normal gyro's omitted intensity default 0 and bump-angle default 5.

The scanner also inventories all places where local intensity is unspecified:
515 group settings and 1,737 activators in default; 531 group settings and
1,809 activators in alternative. Many groups merely inherit behavior or have
no relevant feedback source. These counts are not findings that every such
location requires an explicit haptic setting.

## Complete inventory and scope

- [Default settings by layer and input](default.md),
  [individual explicit fields](default-explicit.csv),
  [unspecified settings](default-unspecified.csv).
- [Alternative settings by layer and input](alternative.md),
  [individual explicit fields](alternative-explicit.csv),
  [unspecified settings](alternative-unspecified.csv).
- [Machine-readable summary and source hashes](summary.json).
- [Read-only scanner](audit.py): run
  `python3 findings/2026-10-09-haptics-audit/audit.py` to refresh this inventory.

Both layouts pass order, preset-ID and unique-title preflight checks. The
scanner converts commands to title form in memory and inspects every group,
including mode shifts, inactive/unreferenced groups and disabled activator
banks. An independent recursive scan confirms every haptic-related property
was captured. No explicit haptic field was found in an unreferenced group or
disabled activator. The Base D-pad mode shift has an explicit Off override.
No additional rumble/vibration/feedback-named setting was found. The exported
VDFs contain matching haptic property/value counts for their JSONs.

Runtime inheritance depends on the active stack and source mode. Ordinary
Steering and its fallback guard expose Base right-pad gestures; Circular
Scroll supplies its own Low mode, while a pad click can temporarily replace
it with another mode. The inventory records declared settings and owners,
not an exhaustive runtime-stack or physical-feedback simulation. It does not
assume an omitted activator level is silent or that a group override and an
activator level cancel each other. Physical feedback and client defaults
remain device checks. No layout tests or exports were needed for this audit.
