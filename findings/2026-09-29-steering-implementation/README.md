# Steering implementation candidates

Status: **full candidate bindings generated for both variants; device acceptance
pending.** These are complete copies of the current 90.4 layout with steering
integrated. They are not the earlier minimal probes and do not overwrite the
working Neptune exports. Load a candidate as a separate test layout first.

- [Default candidate VDF](default-steering-candidate.vdf)
- [Alternative candidate VDF](alternative-steering-candidate.vdf)
- [Default readable bindings](default-steering-candidate.readable.json)
- [Alternative readable bindings](alternative-steering-candidate.readable.json)
- [Build hashes, layer counts and changed sources](manifest.json)
- [Default input manifest](default-bindings.json) / [Alternative input manifest](alternative-bindings.json)
- [Event observer](../2026-09-29-steering-native-probes/observer.html)

```sh
python3 findings/2026-09-29-steering-implementation/build_candidate.py --vdf
python3 findings/2026-09-29-steering-native-probes/build_native_gestures.py
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_convert_vdf.mjs tests/test_steering_observer.mjs
```

The generator resolves bindings by title and source, edits copied groups,
appends fresh IDs, converts title references and verifies the full command
budget before export. The VDF converter checks serialized keys, values and
order. Product descriptions identify these files as unverified candidates.

## Implemented flow

1. Either stick deflected selects protected menu entry. Later deflection
   transfers normal entry, clears only automatic Fn ancestry, and starts a
   fresh 300 ms silent-cover deadline. Protected entry has no delayed/touch
   automatic Fn path. An early menu release emits Escape/Tab; the silent cover
   suppresses that output on a longer hold. Explicit click-to-Fn remains.
2. Right Menu + LS click selects Transition Set 1; releasing Right Menu commits
   steering. Competing transition stick recoveries and click aliases are
   explicitly blocked. Left Menu aborts the transition. Commit removes transient
   predecessor layers, preserves persistent Gyro, then adds Steering + Guard.
3. Guard keeps WASD without exit timing. Center or driving acquisition retires
   it permanently for the session. An already-centered entry uses repeating
   center detection, not a presumed new press.
4. R1/default or R2/alternative owns W; left owns S. The owner's opposite input
   enters Mod 2 and never emits opposing movement. Simultaneous acquisition is
   guarded by the opposite physical control and routes to Rearm. A carried LS
   stroke starts consumed. Neither owner contains a modifier map.
5. Fresh LS up/down selects Mod 1/0. A 250 ms hold, modified action or lateral/
   reversed stroke consumes tap eligibility. Center after an eligible short
   stroke opens the matching owner/context/direction window. The window emits
   one wheel tick at 50 ms and expires at 150 ms; same-direction second entry
   starts 50 ms repeat with no final release tick. These are prototype timings.
6. Mod 2 cancels normal history. Its faces, D-pad, clicks and menu key mappings
   remain Mod 2 during its separate gesture window/repeat; face use does not
   consume its scroll. Opposite release clears Mod 2 history and restores the
   current direction bank as consumed until center.
7. Dominant release removes all driving/maps/gesture helpers and returns to
   fallback through Rearm. Rearm inherits fallback WASD **and its exit timer**.
   A held opposite cannot acquire through a repeat; fresh acquisition remains
   guarded until the opposite is released.
8. Fallback W has native Long Press activators for a 2500 ms repeated haptic-only binding and a 5000 ms whole-family
   exit with haptic intensity and the layer-command beep flag. Releasing W or
   acquiring an owner replaces/cancels that input route. Actual pulse delivery,
   sound and pending-delay cancellation remain S4/S5 device checks.

All Mod 0/1/2 keyboard/mouse payloads for face buttons, D-pad, stick clicks and
menu keys are copied from the corresponding current variant. Menu buttons while
a bank is selected retain that bank's Insert/Delete, Home/End or Page Up/Down
bindings. In fallback, centered normal driving and normal scroll repeat, menu
entry instead exits steering before opening the menu. This preserves access to
those modifier key binds while still supporting a clean new steering session.

## Layer count and reuse

Each candidate adds **36 definitions**, bringing the existing 55 to **91**.
Only a small subset is active together; this is not 36 simultaneous overlays.

| Family | Definitions | Why it remains distinct |
|---|---:|---|
| Membership, disposable Guard, W/S owners | 4 | Persistent session versus one-time protection versus dominant identity |
| Shared Mod 0/1/2 maps | 3 | No built-in bank; shared by both owners |
| W/S × Normal/Mod2 × Up/Down stroke | 8 | Stores direction, owner and context until actual center; owns hold consumption |
| Corresponding Double Windows | 8 | Knows exact self-removal and dominant/opposite exit meanings |
| Normal/Mod2 × Up/Down repeat | 4 | Normal exposes Base, Mod 2 preserves its map; direction determines wheel |
| Normal/Mod2 consumed | 2 | Shared across owners and directions; normal restores direction maps, Mod 2 keeps its map |
| Rearm | 1 | Fresh acquisition after dominant release or simultaneous entry |
| Protected Entry/Silent Cover per menu | 4 | Fresh release eligibility without automatic Fn |
| Automatic Fn provenance per menu | 2 | Deflection can cancel automatic Fn without removing deliberate Fn |

Two initially considered Mod 2 routing layers were eliminated: each W/S owner
uses an opposite-control chord to route its stick input into the correct
context. Payload templates, consumed layers and repeats are otherwise shared
where lifecycle rules permit. **36 is an implemented candidate count, not a
proven minimum.** The native-activator comparison below is the next reduction
experiment; no semantic requirement was declared passed merely to lower a count.

## Native gesture comparison

[Native comparison VDF](../2026-09-29-steering-native-probes/native-gestures.vdf)
uses no Always On windows. Right Menu enters Native Normal; R1 selects Native
Mod2; its release returns to consumed Normal. LS up/down each have exactly three
activators: interruptible Regular wheel, silent Long Press, repeating Double
Press. A sends H and consumes Normal; in Mod2 it sends M without consumption.
D-pad Right reports F1 Base / F2 Normal / F3 Mod2 / F4 Consumed. Left Menu resets.
This is a control-independent diagnostic; R1 is deliberately fixed in this probe.

Record whether a short stroke sends exactly one tick, a long stroke sends none,
a second held stroke repeats without a release tick, and context/consumption
layer changes cancel histories. Test A held across a context change, direct
reversal, carried entry and Mod2 A during the gap between taps. Native history
reset and interruptible Regular behavior are unverified. This probe does not
implement the complete direction-bank selector; it determines whether replacing
the explicit stroke/window machinery is worth the next integration experiment.

## Isolation and cleanup checks

Every new Always On window owns all active-source inputs capable of inherited
mutation, including mode-shift aliases. It uses output-only payloads while
active. Timeout only removes itself. Every directly encoded early exit removes
the actual window first; every entry adds the window last. The eight windows
are distinct so no exit guesses an owner or blindly removes absent windows
before the live one. Existing seven Always On definitions remain unchanged.

The generated input manifests list source settings, native activator types,
conditions, delays/repeats and subcommands in **execution order**. Ordinary
mutation routes that are intentionally inherited outside windows still need
native timing/coexistence tests. Whole-input overrides and configured command
order do not establish cancellation of already-scheduled Steam callbacks.

## Native limitations and release gates

The bindings are wired; the following acceptance claims are **not established**:

- S1/S2: owner output acquired over an already-held control, W→W continuity,
  release exposure, radial center thresholds and diagonals. The full candidate
  provisionally uses the owner-output route from the earlier two-way comparison.
- S3/S7: pending lower callbacks and same-sample ties. Static traces verify
  ordered command arrays, not Steam's ordering between independent activators.
  In particular test center versus vertical release and opposite versus fresh LS.
- S4/S5: the candidate uses Long Press hold timing rather than Fire Start Delay,
  because unrelated removals are known to reset the latter. The new
  `default-long-clock` / `alternative-long-clock` probes compare native hold
  timing against the original delay probes under the same B-removal stressor.
  Preservation of long-hold timing, accepted 2500/5000 ms thresholds and both
  Long Press activators firing independently are still unverified. The candidate
  retains ordinary Base pad/ramp/gyro routes; it does not claim isolation is proven. If warning/exit timing slips, use the plan's
  isolation redesign branch. Empty-binding haptic repeat and actual beep delivery
  must be measured; field presence is not feedback verification.
- S6: independent changed-held-output suppression. This candidate relies on
  native output handoff; it does **not** implement separate per-input latch
  memory. If held controls synthesize new outputs on a map change, S6 fails and
  those latches (and their layer cost) are still required before delivery.
- S8: physical AxisDeflection threshold, delayed Fn cancellation on transfer and
  the next centered press, both menus, Fn mode shifts, held menu release, and
  protected tap eligibility. Edge radii are native-code-derived estimates,
  not calibrated Deck travel.
- S9: overlay/missed-release recovery. Owner LS-touch recovery checks the actual
  dominant; map recovery checks that neither driving control remains held.
  An either-control map gate alone cannot repair a stale dominant while the
  opposite remains held. Test owner-specific recovery and timer/pending work
  after returning from Steam overlay, not only normal release cleanup.

No claim of a bug-free or final minimal implementation is made. Do not promote
these candidates to working `latest` or publish a release until these checks
pass or the recorded failures are fixed. The user authorized implementation;
this is an evidence boundary, not another permission requirement.
