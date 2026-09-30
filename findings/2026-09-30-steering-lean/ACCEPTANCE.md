# Sixteen-layer candidate acceptance

All device cases are **UNTESTED for this build**. Record the new
[manifest hash](manifest.json), variant and Steam build. Use the
[observer](../2026-09-29-steering-native-probes/observer.html).

| Gate | Exercise | Required result |
|---|---|---|
| S1 owner takeover | W + opposite held → release W owner; repeat S→W, center/Up/Down | Old movement ends; held opposite acquires within the acquisition cadence, no stuck or overlapping W/S, old Mod 2/history cleared |
| S2 guard | Enter with W held >5 s; center or acquire driver | Initial hold has no timeout; guard ends once and does not return |
| S3 normal center | Short Up/Down→center; hold >250 ms; use modified action | Short eligible gesture scrolls once; hold/action consumes; no map survives center |
| S3 reversal/sideways | Up→Down or sideways without center, then center | Correct new bank or no bank; no fabricated single/double scroll |
| S3 window | Center after short stroke, wait 150 ms; pause in center-to-direction gap; same/different second direction | One pending single or correct repeat; no frozen/restarted clock or duplicate tick |
| S4 fallback | Release owner without opposite held and LS Up; touch pads/change RS/gyro | Fresh 1/2.5 s clock; unrelated actions do not drift deadlines |
| S5 feedback | Warn, release W or acquire driver, then retry and exit | Repeated warning stops; new hold starts fresh; exit beep/vibration once |
| S6 held maps | Hold mapped buttons through normal bank/Mod 2/center changes | Old changed output releases; replacement waits fresh press; unchanged mapping survives |
| S7 shared cover | Double Up/Down; reverse fast, slowly through diagonals, or go sideways; repeat near 5 ms tick boundaries | Old repeat stops, no unintended opposite tick; no final release tick; normal repeat Base mappings |
| S7 used-up tap | Hold Up/Down past 250 ms, reverse, then center; enter a driver or leave Mod 2 with Up/Down held, then center | While the cover is active, up/down do nothing and center never scrolls; the next fresh push selects the bank normally |
| S8 menu | Either stick before/during both menu entries, partial deflection/deadline, explicit Fn | Fresh protected tap window once; no automatic Fn leak; explicit and next centered Fn work |
| S8 commit | Right Menu+LS click then release; held touch/edge; Left Menu abort | One entry, no Tab/Q/punctuation, no stale prefixed menu helpers/mode shifts |
| S9 interruptions | Overlay/focus loss, missed release, existing Base/menu/RTP Always On paths | No stuck output/owner/timer; existing AO self-first/isolation rules preserved |
| S10 Mod 2 | Fresh and preheld Up/Down, hold, reverse, release opposite after a long hold, use faces | Direct wheel and repeat only; no tap/double flow or release tick; face maps unaffected; covered release stops Mod 2 repeat and restores normal consumed mapping without dropping its owner |

The shared repeat's 5 ms cancellation and cover reassertion are native gates,
not established by array order. Also measure held-stick Mod 2 wheel onset and
both-driver acquisition/release races. A failed case blocks promotion and must
be fixed rather than relabelled as passed. Previous 25/36-layer device results
do not apply automatically to these changed bindings.

## Touch cleanup regression

For every new layer, lift LS and RS separately: only the matching LST/RST
Entry Point, Tap Cover and Temporary Gyro helpers clear. In normal Modifier
0/1 or protected menu entry, release before the cover delay: the matching cover
must apply before those removals. Inside the completed cover, repeat the thumb
lift: no parent, Fn or wheel action may be re-added/emitted. Transition commit
must survive thumb lift. Test old-owner-missed-release with opposite still held,
menu owner already released, and simultaneous touch/owner release; keep fallback
and ordinary-window timing checks under thumb-release removals. See
[cleanup audit](CLEANUP-AUDIT.md). Results remain UNTESTED on this build.

## Reused opposite-side tap-cover regression

For both owners/variants, hold opposite <200 ms then release it uncovered: clear
all layers to Base. Hold past 200 ms or use a mapped action/thumb release:
apply only the opposite single cover (L1/L2 for W, R1/R2 for S). Covered opposite
release retains its movement owner and exposes normal consumed mapping;
dominant release, covered or uncovered, permits held-opposite takeover.

Confirm neither reused cover overrides the dominant movement input. Verify the
parent's 250 ms reset is hidden while covered, interrupted delays recover, and
thumb releases stay cleanup-only inside the shared cover. Test normal Base and
Gyro modifier taps/holds too: shared cover release/recovery must preserve their
old side-local behavior and must never create a Steering/consumed layer.

Mod 2 now has consumed normal state beneath it. Enter with preheld Up/Down,
scroll immediately, use face controls, and exit with direction still held: no
normal map may appear during Mod 2, no stale selector may fire above it, and
exit must restore the current bank consumed without an extra scroll. Test near
5/200/250 ms boundaries and overlay/missed releases. Native results are UNTESTED.

## Interrupted-apply reset regression

Interrupt protected-menu entry before 300 ms repeatedly, then hold: its silent
cover must still apply, with no further 350 ms reset once covered. Repeat with
both W/S owners and both 5 ms direction selectors. The selected bank must
retire the parent's 50 ms reset; hold a mapped button across several intervals
and confirm no output drop, map flicker or reopened tap window.

The LS Tap Cover no longer routes (90.6). Hold a mapped button in the covered
bank across several seconds and confirm no output drop; exit Mod 2 with the
stick held and confirm no scroll leak. Exercise thumb release and owner release
around 5/50/200/250/300/350 ms boundaries. These reset cases remain UNTESTED on
device.

## Chorded delays (90.6)

All UNTESTED. These replace the Long Press timers; timings are unchanged.

| Gate | Exercise | Required result |
|---|---|---|
| C1 fallback | In fallback, hold LS up; release at 0.8 s, 2.0 s and 3 s; drift so deflection drops while W stays | Warning pulses from 1 s, exit at 2.5 s with one beep; early release cancels both; losing deflection cancels rather than firing late |
| C2 entry carry | Enter Steering with W held for more than 3 s | No warning or exit until center and a fresh push |
| C3 window clock | Short flick to center, wait; flick, pause, flick again | One scroll about 150 ms after center, counted from the window's add, not the original press; second flick still reaches repeat |
| C4 consume | Hold down/up past 250 ms; release at about 240 ms, then hold fully; tap repeatedly | Consume only past 250 ms; an interrupted hold never blocks the next one; no leftover Tap Cover |
| C5 reset vs cover | Hold past 250 ms and keep holding for 1 s or more; then center | The cover stays (the 300 ms reset is hidden under it); no scroll at center |
