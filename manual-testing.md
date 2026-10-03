# Manual testing (Deck)

Implementation work is tracked in [todos.md](todos.md). Unchecked items below remain pending runtime validation.

- Covers every release from 90.6 to 90.13, newest first, and below them the
  areas from before 90.6 that were never run (menu buttons, modifiers, cursor
  gyro, triggers and ramp-up, recovery, held inputs)
- Nothing here has been run on the Deck
- Load both VDFs fresh, not in the live editing session, and run every check on both layouts
- Written for the default. In the alternative, swap LB / RB ↔ LT / RT: the bumpers fire, and the soft-pull triggers are the modifiers
- If a bind applies the wrong layer, suspect the load-order swap (`findings/2026-07-11-layer-order-swap/`)

## 90.12: cleanup lists

Load 90.12 fresh in both variants (71 layers). Record: [first run and fix](findings/2026-10-02-cleanup-audit/README.md) · [rules](findings/2026-10-02-cleanup-boundaries/README.md#the-rules). Nothing here has run on the Deck. 90.12 changes only cleanup and release lists: about a third fewer removals, three new or changed cleanups, no add and no add order. "Miss the release" means: hold the buttons, press the Steam button, let go of everything, close the Steam menu.

New behaviour:

- [ ] C1 (Modifier 2, stick touch): hold L1 then R1, miss both releases, touch either stick: back to Base, typing works. Repeat with Gyro on (you return to Gyro) and R1 first
- [ ] C2 (Modifier 2 held, stick touch): hold L1 and R1 and rest a thumb on each stick: nothing clears, Modifier 2 keys still work. Repeat holding only one bumper of a stuck Modifier 2: nothing clears until that bumper is released too
- [ ] C3 (cursor, one step): hold L1 for 300 ms (cursor), miss the release, push the right stick to the edge once: cursor and modifier are both gone in that one push (before: cursor first, modifier on the repeat). Repeat with R1 and with the left stick
- [ ] C4 (Steering Modifier 2): in Steering hold R1 then L1, miss R1's release only (keep L1 held), touch a stick: nothing clears. Release L1: back to Steering

Unchanged, check they still work:

- [ ] C5 (rocking): hold L1, add R1, wait 200 ms, let go of L1, press L1 again, wait, let go of R1, let go of L1: no scroll at any point, Base at the end. Repeat starting with R1, and with Gyro on
- [ ] C6 (taps): tap L1 twice quickly: scroll down. Hold L1 and press A, let go, tap L1 at once: no scroll. Hold L1 and tap R1 within 200 ms: Gyro toggles
- [ ] C7 (stuck, still clears): miss the release of L1 alone, of Start's Fn layer, and of a Steering driver, then press A or touch a stick: each clears
- [ ] C8 (menu): hold Start, push a stick (guard), release: Tab or the window as before; hold Start past 200 ms for Fn, release: Fn gone, nothing left behind

## 90.11: Steering fallback hold

Load 90.11 fresh in both variants (71 layers). Record: [build](findings/2026-10-02-steering-fallback-hold/README.md). Nothing here has run on the Deck. These replace D2 (90.10) and C1 (90.6). All checks are in Steering with no driver held.

- [ ] F1 (the fix): hold the left stick up for about 1 s, roll to A or D without recentring and hold for 3 s: the pulses stop on A or D and Steering stays. Repeat from down
- [ ] F2 (exit): hold the left stick up: W, pulses from the start, and Steering exits with one beep at about 1.5 s. Repeat with down and S
- [ ] F3 (early release): hold up for 1 s, recentre, hold up again: the exit comes 1.5 s after the second push, not sooner
- [ ] F4 (after A or D): hold A for 3 s, roll up and hold: the exit comes about 1.5 s after reaching up. An instant exit means the timer counted the time on A; an exit near 3 s means the reset on the edge restarted it
- [ ] F5 (diagonal): hold up-left: W and A together, pulses carry on, exit at 1.5 s
- [ ] F6 (driver): hold up, press R1 before 1.5 s: the pulses stop, no exit, and the R1 modifier map is up. Release R1 with the stick still up: note whether W and the pulses come back
- [ ] F7 (entry): enter Steering with the stick centred, push up and hold: W with no pulse and no exit until the stick has been back to centre once (D9 in 90.10). Repeat entering with the stick already held up
- [ ] F8 (menu while holding up): hold up, tap Start: one Tab, W carries on, and the exit still comes 1.5 s after the push. Hold Start for 1 s: Tab held, no Fn. Recentre, push A: no pulse. Repeat with Select (Escape)
- [ ] F10 (menu held, then push up): hold Start with the stick centred, push up and hold for 3 s: W, no pulses, and Steering stays. Release Start: Fn or Tab as usual
- [ ] F11 (Entry Guard): enter Steering and leave the stick centred: Start and Select type Tab and Escape, with no Fn and no leave gesture. Push the stick out and back once, or press a driver: Start's tap and Fn come back
- [ ] F9 (desktop): apply the layout to the desktop configuration and repeat F1 and F2

## 90.10: stateful transitions

Load 90.10 fresh in both variants (70 layers). Record: [build](findings/2026-10-01-stateful-transitions/README.md) · [design](resources/Stateful%20Layer%20Transitions.md) · [plan](plans/2026-10-01-stateful-transitions-implementation.md). Nothing here has run on the Deck; the two gates were assumed. These replace K1 (90.9) and S5 and S8 (90.7), which test behaviour this release changed.

Gates first. If G3 shows the edge Release doesn't fire, stop: the stick guards and Steering's left stick need a new design.

- [ ] G1 (gate 1, stick inheritance from the middle of the stack): hold the left stick out, then hold Start (the guard lands), click and release the stick, release Start: Steering is on (R1 drives W). A Q typed at the click means the click skipped the Entry Point under the guard
- [ ] G2 (gate 1, Fn): hold Start past 200 ms so Fn is up, click and release the left stick, release Start: Steering is on
- [ ] G3 (gate 2, edge Release in a layer added with the stick already out): hold Start, flick the left stick out and back inside 200 ms, keep holding Start for 1 s, then press a face button: an F-key means the guard came off on the edge Release and Fn followed. If there is no F-key, release Start: a silent release means the guard never came off (gate 2 fails, the Tap Cover landed on it); a Tab means the guard came off but the Fn delay didn't come back (assumption 6)
- [ ] G4 (stick already out): hold the left stick north, then hold Start for 500 ms: no `\` is typed, and the release is silent. A `\` means the guard landed after the 200 ms Fn delay
- [ ] G5 (tap with a stick out): hold the left stick north, tap Start: one Tab
- [ ] G6 (eaten delay comes back): push both sticks out while holding Start, recentre the right one before 200 ms, keep holding for 1 s, release Start: silent. A Tab means the first guard's Tap Cover delay didn't come back (assumption 6)

Menu flow and transitions:

- [ ] T1: each gesture from Base and from `Gyro`: Start + LS click enters Steering; Select + RS click, Start + RS click and Select + LS click clear to Base and keep `Gyro`. The stick click is released first, then the menu button. Every one of them beeps and gives a strong haptic pulse on the menu release, with no on-screen notification
- [ ] T2 (clear): in Steering, each of the four gestures leaves it, with the beep and pulse on the menu release; `Gyro` stays as it was
- [ ] T3 (cancel): hold Start, click and hold the left stick, release Start first, then the click: no Steering. Note what the click's release does
- [ ] T4 (missed release): in each transition, release the menu button while the Steam menu is open, close it: everything is blocked until the next tap of either menu button, which ends the transition (a Start tap in the cross transition enters Steering)
- [ ] T5 (guards): guard on and off for each stick, and both together; with a guard on, a quick menu tap types Tab or Escape, and a 200 ms hold or a thumb lift makes the release silent
- [ ] T6 (stale guard): with a stick out, release the menu button while the Steam menu is open, close it: touching a stick clears the guard, and the next menu tap behaves normally
- [ ] T7 (accepted): under the menu Tap Cover, bump the other menu button: the cover returns within about 200 ms, and a release inside that gap types its key. With a stick out and no cover yet, a bump of the other menu button types its key
- [ ] T8 (K1 reworded): hold Start, press Select before Fn is up: exactly one Backspace, repeating while held. Mirror for Enter
- [ ] T9: the camera stick is dead while a menu button is held, and comes back on release
- [ ] T10 (mouse buttons through a window): tap L1, or flick the left stick while driving, and pull a trigger inside the 150 ms window: the mouse button fires. Repeat with the right stick past the ramp threshold first, so `Gyro Off Ramp Up` is underneath: the mouse button still fires. Then hold a trigger and tap L1: note whether the click is interrupted when the window lands and when it times out. In the alternative, the same with the bumpers inside a Steering window

Steering:

- [ ] D1 (menu): with no driver held, tap Start: one Tab and Steering stays; hold Start: Fn. Hold R1 and tap Start: Tab; Select: Escape
- [ ] D2 (hold exit): replaced by F1 to F5 in 90.11
- [ ] D3 (modifier and roll): hold R1, hold the left stick up: the R1 modifier map. Roll to the side: A or D steers and the map stays until the stick is back at centre. Roll straight to down inside 250 ms: the L1 modifier map takes over
- [ ] D4 (stick first): hold the left stick up, then press R1: the modifier map is there at once; held 250 ms, recentring is silent; recentred sooner, one scroll
- [ ] D5 (double taps): flick up and back: one scroll about 150 ms after centre. Flick, then flick and hold: repeating scroll; releasing stops it and adds nothing. Flick up, then push down inside 150 ms: no scroll, the down modifier map. Flick, then push sideways inside 150 ms: A or D at once and the scroll still lands at 150 ms
- [ ] D6 (W and S through the window): hold a driver, flick the stick once: W or S carries on through the window and after it. Release the driver inside the window: back on `Steering` with plain WASD
- [ ] D7 (other driver in the window): flick the stick, bump the other driver inside 150 ms: its key for that moment, no two-modifier map, and driving carries on
- [ ] D8 (mapped buttons): in a modifier map, press a face button: its key, and recentring is then silent. Missed release: in a modifier map, release the driver while the Steam menu is open, close it, press a face button: the steering branch clears
- [ ] D9 (entry with the stick centred): enter Steering with the stick centred, push up and hold: W with no exit warning until the stick has been back to centre once

## 90.9: Enter / Backspace typed by the menu chords

Load 90.9 fresh in both variants. The `Menu Left: Backspace` and `Menu Right: Enter` layers are gone (69 layers). Record: [author decisions](findings/2026-10-01-intended-flow-checker/README.md#author-decisions-2026-10-01). 90.8 was an intermediate build; don't test it.

- [ ] K1 (early path): hold Start and press Select within 300 ms, before Fn is up: Backspace types on that first press, repeats while Select is held, and stops cleanly on release with no stuck key. Then release Start: no Tab. Mirror with Select then Start for Enter (no Escape)
- [ ] K2: with Fn up (hold Start past 300 ms), Select types Backspace on every press and repeats while held. Mirror for Enter
- [ ] K3 (accepted): hold Start, press and keep holding Select, lift Start first. Select falls through to Base and opens Menu Left; releasing it within 300 ms sends Escape. Mirror: Tab. Confirm this is the only extra output, and that releasing Select first never sends anything extra
- [ ] K4: other Fn keys behave the same way (hold Start, hold LB for F10, lift Start: LB becomes the L1 modifier)
- [ ] K5: every layer still does what it did: spot-check a modifier, Mod 2, both menus' Fn keys, the Transition Sets and steering entry. The two removed layers shifted later runtime IDs, so this must be a fresh load
- [ ] M5: RTP double tap: tap the right pad, tap again north or south within 150 ms for Circular Scroll; a second tap elsewhere returns to mouse mode. The bumpers keep their modifiers right after

## 90.7: slim steering overlays

Load 90.7 fresh in both variants. Record: [steering 90.7](findings/2026-09-30-steering-lean/README.md#slim-overlays-and-dod-fixes-907).

- [ ] S1: drive, flick LS up to center, press A within 150 ms: F fires once, one scroll lands about 150 ms after center, and nothing is left stuck
- [ ] S2: flick, then flick and hold: repeat scroll; releasing stops it; the next push gives no scroll until center. Sideways during the repeat steers with A/D and a true diagonal keeps scrolling until up/down is released
- [ ] S3: hold LS up past 250 ms, lift the left thumb, put it back: LST layers clear, the stick stays consumed until center, no phantom scroll
- [ ] S4: hold LS up past 250 ms, release the driver while the Steam menu is open, close it and touch a stick: owner recovery clears the steering branch through the cover
- [ ] S5: protected menu entry (Start with a stick deflected), hold past 300 ms, release: silent release, both protected layers gone, gyro stays off throughout; repeat with a thumb lift during the hold
- [ ] S6: while steering, tap and touch the right pad: the cursor moves and pad clicks work, but no RTP touch mode (Circular Scroll) starts. Outside steering, RTP double tap is unchanged
- [ ] S7: while steering, turn assist (RS past the ramp threshold) works while just driving, and does nothing while LS holds a modifier map, in the two-modifier map, or right after a scroll flick
- [ ] S8: flick LS up to center, then push sideways within 150 ms: one scroll fires at once, A/D steers, and pushing up again before center gives no scroll or modifier map

## 90.6: chorded delays and dead-group prune

Load 90.6 fresh in both variants. Gate details: [steering C1–C5](findings/2026-09-30-steering-lean/ACCEPTANCE.md#chorded-delays-906)
and [prune D1–D5](findings/2026-09-30-dead-group-prune/README.md#deck-gates-untested).

- [ ] D1: both variants load without error; every layer's sources look the same as 90.5 in the editor
- [ ] D2/D3: right pad clicked, tap up/down gives one wheel tick; hold repeats from 150 ms at the old cadence and stops on release; forward/back and edge middle click unchanged
- [ ] D4/D5: Base dpad/face and Menu Fn stick mode shifts unchanged; stick double-touch temporary gyro unchanged
- [ ] C1: steering fallback, hold LS up: warning pulses from 1 s, exit with one beep at 2.5 s; releasing early cancels both
- [ ] C2: enter Steering with W held for more than 3 s: no warning or exit until center and a fresh push
- [ ] C3: short flick to center scrolls once about 150 ms after center; flick-flick-hold still repeats
- [ ] C4/C5/S7: holding down/up past 250 ms consumes the tap and keeps the modifier map while held; an interrupted hold never blocks the next; after that, reversing does nothing and center never scrolls. After a driver takeover or Mod 2 exit with the stick held, center never scrolls
- [ ] R1: second-press cover. Double-tap Select and hold past 150 ms: Escape holds, and release ends cleanly with no extra Escape. Repeat with Start/Tab and with a modifier double-tap-hold scroll ([change record](findings/2026-09-30-second-press-cover-reset/README.md))
- [ ] R2: interrupt that hold (release before 150 ms, then double-tap-hold again); the cover still arrives, so the release ends cleanly. A fast tap chain still re-enters the window
- [ ] R3: apply either layout to the **desktop** configuration; those four inputs show three entries, the reset is the one missing, and tap, double tap and hold still work
- [ ] T1: `Transition Set 0` (Fn + RS click). While either menu button is held, touching a stick doesn't clear the menu stack. With both menu buttons released, touching still clears it. Lifting a thumb clears only that side's LST/RST layers. Confirm in the editor that the merged chord shows both Select and Start set to Any ([record](findings/2026-09-30-touch-release-rule/README.md))
- [ ] P1: during any Double Tap window (within 150 ms of a tap), a left-pad swipe sends Escape, Enter, Tab or Backspace directly and adds no key layer; left-pad click and touch do nothing. In the six other windows, the right pad still moves the cursor with Base's feel, and right-pad click and touch do nothing. In RTP Double Tap, right-pad click does nothing and north/south/east/west still select or cancel. Check that the swipe feel (sensitivity and haptics) matches Base ([record](findings/2026-09-30-double-tap-pad-blocks/README.md))
- [ ] B1: derived window blocks. Default only: push RS past the ramp threshold (Gyro Off Ramp Up), tap L1, and pull a trigger inside the window. Nothing fires and gyro stays off until the window ends. Both layouts: quick-tap the right pad while holding Start or Select (Fn). In RTP Double Tap, the four back buttons do nothing. Right-pad selection is unchanged: a second tap north or south goes to Circular Scroll, and anywhere else returns to mouse mode ([record](findings/2026-09-30-derived-window-blocks/README.md))

## Menu buttons

- [ ] MB1: Tapping Select sends Escape, and tapping Start sends Tab
- [ ] MB2: Holding either for 300 ms brings up its Fn layer, and the F-keys work
  - On release nothing is sent
  - The face buttons are back to normal
  - The next tap still sends Tab / Escape
- [ ] MB3: Start-delay reset: after an interrupted hold, keep holding or hold again, and the Fn layer comes up
- [ ] MB4: Enter / Backspace: Select → Start sends Enter, and Start → Select sends Backspace. Try both quickly (under 300 ms) and with the Fn layer up
  - Releasing the second button first sends nothing extra. Lifting the first button first drops the still-held second button to Base (accepted since 90.9; see the 90.9 checks)
  - Holding the second button repeats the key, and pressing it again while holding the first sends it again
- [ ] MB5: Double tap and hold repeats Escape / Tab, and releasing stops it
  - Note whether a quick double tap sends the key two or three times (known, not fixed)
- [ ] MB6: Menu button + stick click opens a Transition Set, and with the menu button held, the stick directions type punctuation
- [ ] MB7: In each Menu Fn layer, its eight directional keybinds (four LS + four RS) give haptic feedback with their punctuation keys. Check holds, direction changes, and inherited Fn directions in Transition Sets for unwanted buzzing or duplicate keys. Separate held-click mode-shift bindings retain their previous haptic settings
- [ ] MB8: Stick touch release: hold Start, touch a stick and lift off, then release Start. Menu Right: Fn comes up on the lift, and no Tab is sent. Select does the same with Menu Left: Fn, and no Escape
- [ ] MB9: Steam button recovery:
  - Hold a menu button until its Fn layer is up, press the Steam button, let go, and close the Steam menu
  - RS to the edge (or a face button) clears the Fn and entry layers, and the menu buttons work normally again
  - Enter / Backspace are plain chords since 90.9, so nothing of theirs can be left behind. Gyro suppression during menu use is intentional
- [ ] MB10: Stuck entry layer (for example, the Steam button within 300 ms of a menu press)
  - The other menu button clears it and then works normally
  - In the alternative, RS to the edge no longer makes it worse

## Modifier layers

- [ ] ML1: Nav keys with Start / Select: LB gives Insert / Delete, RB gives Home / End, and LB + RB (either order) gives PgUp / PgDn
- [ ] ML2: The same nav keys in Gyro mode
- [ ] ML3: Holding Start or Select in any modifier layer, in Base or Gyro mode, doesn't change the gyro. Confirm that's what you want
- [ ] ML4: After a nav chord, releasing the modifier doesn't fire its tap / scroll action, and Start or Select alone in a modifier layer still clears it

## Temp cursor gyro

Run both sides, both layouts, and both regular/Gyro modifier variants after a
fresh load. See the [implementation and inheritance record](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md).

- [ ] TC1: Hold the primary modifier for 300 ms: its Temp Cursor Gyro overlay applies,
  with precision speed 750, haptic intensity 0, haptic bump 1, and movement
  threshold 5. Natural sensitivity remains 300 and activation follows the
  existing regular/Gyro rules. Releasing the modifier sends no tap/scroll output
- [ ] TC2: The 300 ms hold entry gives one high-intensity haptic pulse. Keep holding:
  no ongoing gyro vibration or repeated entry pulse. Early thumb-lift entry and
  subsequent touch releases remain silent. Check both regular/Gyro owners and
  interrupted/retried holds in both layouts
- [ ] TC3: Before 300 ms, lift either thumb: cursor applies immediately, then only
  that stick's LST/RST helpers clear. Repeated thumb lifts after cursor entry
  inherit the same cursor-add-before-helper-removal path; an already-active cursor
  stays active. After cancellation, normal-cover touch releases only clean up
- [ ] TC4: Check every ordinary face/D-pad/click input, Start/Select, and opposite
  modifier before, at, and after 300 ms. Active cursor removes itself, exposing
  the parent's output and repeating normal-cover add. Gyro inherits normal
  precision/haptic/bump/threshold 300/0/5/0. The cover wins for the whole hold,
  preserves the intended key/mouse output, and blocks cursor on later thumb lifts
- [ ] TC5: Check the twelve ordinary inputs in all four regular/Gyro owners: output
  chord and cover-add chord are both uninterruptible; only the cover chord gains
  repeat. Test owner-first and input-first presses, with inputs held across cursor
  entry/removal. Both chords must run without lost/duplicate keys, new key repeats,
  or stuck mouse buttons. Same-selector chord order is not a binding-array order
- [ ] TC6: Trigger a normal-cover input and thumb release together near the 300 ms
  boundary. No delayed or release-driven cursor add may defeat the normal cover
- [ ] TC7: Confirm each single-modifier edge has three entries: interruptible owner
  guard, uninterruptible All chord selecting the owner and opposite deflection,
  and repeating interruptible cleanup. The All chord repeats: parents add the
  normal cover; cursor edges remove only cursor. Alternative ownership uses soft pulls
- [ ] TC8: One stick alone preserves cursor; both sticks around 25% should override
  it. Test both activation orders, simultaneous movement, sticks already held
  before modifier entry, and crossing the threshold while the other stick stays
  deflected. LS radius 4915 and RS 7209 account for different native hysteresis;
  verify physical travel and the opposing-stick selector threshold separately
- [ ] TC9: Release/lose the modifier while sticks stay deflected: recovery clears its
  four-target family, and no chord keeps adding covers. Repeat via Steam-menu
  interruption, including a thumb already touching before the owner is lost
  and lifted afterward; no orphan cursor overlay should remain
- [ ] TC10: Test both Mod 2 orders and release orders, including alternative partial/
  full pulls. Normal properties remain in effect, the still-held opposite side
  survives, and persistent Gyro changes only through its existing intended exit
- [ ] TC11: Alternative R2 regular/Gyro → L2 now repeats its Mod 2 entry. With LT already
  pulled before the R2 layer appears, entry must work without re-pulling; keep the
  existing destination and cleanup order
- [ ] TC12: Fresh modifier holds become eligible for cursor again. A short primary
  tap before either overlay retains Double Tap behavior. Check repeated attempts
  after an interrupted delay: the parent's 350 ms reset must let the 300 ms
  cursor apply recover without releasing/repressing indefinitely
- [ ] TC13: Confirm each cursor-entry primary input has exactly three entries: release,
  the 300 ms chorded cursor apply, and an uninterruptible Regular Press that
  removes only the owning cursor overlay with Hold to Repeat and interval 350 ms
- [ ] TC14: Keep holding for several 350 ms intervals after cursor entry, early
  stick-touch completion, and an early/late normal-cover override. Either overlay
  must retire the parent's apply/reset pair: no flickering or repeated removals,
  no normal-cover loss, and no cursor re-entry after an override. Include the
  reset boundary and held inputs across transitions into Always On windows
- [ ] TC15: Hold/move/touch inputs across all seven Double Tap windows and menu/Fn/
  Transition stacks. Timer isolation, self-first exits, menu gyro suppression,
  movement, and existing mode shifts must remain intact
- [ ] TC16: During a modifier hold, quickly touch/release RTP, before and after cursor
  entry. RTP Double Tap must block face buttons, D-pad directions, and both stick
  clicks while its Always On window is active. Test inputs already held and newly
  pressed; no inherited cover-add or cursor removal may run before its safe exit
- [ ] TC17: Cancel cursor during RTP Entry's 150 ms wait: check the touch/trackball
  lifecycle still completes acceptably if that removal restarts its delay. Keep
  RTP touch's intentional reset exclusion. In RTP Double Tap, confirm its existing
  trackpad source-mode replacement prevents Base click/touch layer mutations
- [ ] TC18: First verify whether touching either trackpad actually activates face/D-pad
  mode-shift targets 1039/1043 under regular/Gyro modifiers in both layouts. They
  are marked `inactive modeshift`; enabled Base references alone do not prove
  activation. Record key outputs and normal-cover behavior before and after the
  300 ms cursor apply, including trackpad touches held across layer transitions.
  Only propose a fix if an actual cover bypass is reproduced; otherwise close
  this concern without changing bindings

## Reference gyro and right-stick tuning

Run both layouts after a fresh load. See the [exact settings and inheritance policy](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#reference-tuning-and-gyro-inheritance-follow-up).

- [ ] RG1: Base gyro matches the July reference's feel and settings: natural sensitivity
  300, rotation calibration 3853, vertical ratio 200, conversion style 4, speed
  deadzone 0, precision 300. Existing Base All and Gyro Any activation rules remain
  intact; LST/RST Temporary Gyro change activation without changing response
- [ ] RG2: In regular and Gyro modifier holds, cursor response is 750/0/1/5 and removing
  cursor exposes 300/0/5/0 for precision/haptic/bump/threshold. Normal covers have
  no active gyro source. Both responses inherit
  natural sensitivity 300 and the new Base calibration/conversion. Exercise
  LST/RST helpers before and during each profile; menu and Gyro Off modes still
  disable gyro when intended
- [ ] RG3: Base right stick retains its reference settings and feel. Ramp 0 changes
  sensitivity/vertical scale to 150/80, then Ramp 1 to 200/67; recentering restores
  the exposed lower settings. Modifier sensitivity 75 and its local edge region
  remain intact; repeat the trigger-held and gyro-off ramp paths below

## Triggers and ramp-up

- [ ] TR1: LT / RT fire left / right click, and Start / Select work while a trigger is held
- [ ] TR2: In the Deck GUI, Base's right-stick outer edge shows three command entries, and both chords are set to Any
  - Default: the trigger chord selects LT / RT (partial and full pull), and the modifier chord selects LB / RB
  - Alternative: the other way around
- [ ] TR3: RS to the edge with nothing held:
  - The gyro turns off and Turning Ramp Up 0 starts
  - Turning Ramp Up 1 follows after about 250 ms
  - Moving back in restores the gyro and ends ramp-up, at either stage
- [ ] TR4: RS to the edge while holding a trigger keeps the gyro on during ramp-up, with no unwanted mouse repeats
  - Try each trigger alone at partial and full pull, then both
- [ ] TR5: Pulling a trigger after the gyro turns off, in both stages, brings the gyro back, and the first click registers
  - Letting go of one of two held triggers keeps the chord
  - Partial ↔ full pull changes work
- [ ] TR6: Holding a modifier on the way to the edge lets no ramp-up or gyro-off leak through
  - Try each modifier alone, then both
  - Try it again with a trigger held, and with the press / release order reversed
- [ ] TR7: Pressing a modifier during ramp-up ends ramp-up and enters the right modifier, the `Gyro |` version in Gyro mode
  - In the alternative, a partial pull keeps the block, and a full pull exits
- [ ] TR8: The edge / trigger / modifier checks above work the same in Gyro mode
- [ ] TR9: Interrupting the 250 ms stage change, recentering and retrying still reaches Turning Ramp Up 1 (the 300 ms reset)
- [ ] TR10: Stuck right trackpad:
  - Hold RB, touch the right trackpad, let go of both (try both orders), then push RS to the edge
  - Ramp-up works, and trackball momentum is intact
  - A thumb on the trackpad still blocks the edge
- [ ] TR11: Two-bumper tap cover:
  - A quick LB + RB tap still toggles Gyro mode
  - Holding both past 200 ms and releasing doesn't, even right after an interrupted attempt
- [ ] TR12: No new haptic pulse when RS hits the edge

## Default trigger reference match

- [ ] DT1: Load the default layout fresh and confirm both Base triggers match the July reference's trigger settings and mouse outputs (LT → left click, RT → right click)
- [ ] DT2: Check partial/full pulls, quick pulls, held firing, and release in Base, Gyro, and both ramp stages; a pull during Gyro Off Ramp Up restores gyro and registers the intended click
- [ ] DT3: Check inherited trigger behavior through modifier/cover layers, menu Fn outputs, and all seven Double Tap windows, including a trigger already held across entry/exit. Existing trigger overrides and blocks must retain their behavior

This change removes only Base's explicit `adaptive_threshold: "0"` settings.
Upper layers retain their existing settings and bindings: inherited trigger
settings may be affected, while explicit click/edge overrides remain in place.
No new layer mutations or timer operations were introduced. This follows the
reference configuration; it does not add a Soft Press hip-fire activator.
The alternative layout is unchanged.

## Left-stick recovery and Transition Sets

- [ ] LR1: Validate the new LS-edge recovery and Transition Set depth on the Deck in both layouts
  - Follow the [fresh-load checks](findings/2026-09-28-left-stick-recovery/CHANGES.md#verification-and-deck-checks), including both Mod 2 orders/Gyro variants, either-owner guards, outer-region behavior, and LS deflection held across every Double Tap window

## WASD modifier scaffold

Run on both layouts after a fresh load. The shipped modifier slot is empty;
assign a temporary modifier in a test copy for the checks that need output.

- [ ] WM1: Base left stick shows one empty Soft Press command named **WASD Modifier** on its edge, with the reference's style/threshold settings. No `*` or other modifier key is sent by the shipped layout; WASD and Q click still work
- [ ] WM2: With a test modifier assigned, check slow deflection, quick deflection, held deflection, and return to neutral. Verify the intended WASD-only, modifier-only, and combined regions; adjust the user's key and preferred Hip Fire Aggressive/Relaxed style as needed, without changing the shared scaffold just to fit one game
- [ ] WM3: Verify inherited modifier behavior in Base, Gyro, ramp stages, stick-touch layers, and button overlays where the underlying stack exposes Base's LS edge
- [ ] WM4: Verify the modifier is displaced by the 16 LS-edge recovery layers (including both Fn layers), all seven Double Tap windows, and both menu Fn left-stick mode shifts; their cleanup, timers, and punctuation outputs retain their behavior
- [ ] WM5: Enter and leave those overrides while the stick is already deflected, as well as deflecting after entry. Check that no modifier stays held after release or after Steam-button recovery

## Missed releases and cleanup scope

- [ ] MR1: Validate recovery on the Deck after missed releases, in both layouts
  - Trace the underlying recovery owner and which overlays expose or block it; do not require every overlay to duplicate that recovery
  - Stale-state fallbacks must preserve valid held interactions. Normal releases, delayed-apply resets, timed expiry, and deliberate transitions are allowed during normal use
  - Verify intended survivors, including persistent Gyro, the still-held modifier side, and valid shared overlays; flag invalid residual overlays requiring another gesture for the ownership review
- [ ] MR2: Verify whether interrupted transitions can leave both Mod 2 press orders active and cause a recovery problem
  - Retain current-branch fallback unless that problem is demonstrated. Its eleven targets include both cursor overlays but still exclude the opposite Mod 2 order
  - Preserve the combined tap cover's nine-layer released-side cleanup and persistent Gyro. The uncovered Mod 2 release has a separate thirteen-layer cleanup plus an intentional Gyro state change

## Held inputs across layer changes

Real-layout checks for [Held Inputs Across Layer Changes](resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes).
See the [audit](findings/2026-09-29-held-input-layer-transitions/AUDIT.md#deck-checks) for the reasoning behind each check.
Rule 3 (a removal firing the exposed layer command) stays unverified and isn't
scheduled. These layouts back it with repeats. If it's ever needed, the
[optional T4 check](findings/2026-09-29-held-input-layer-transitions/AUDIT.md#optional-settle-rule-3)
settles it.

- [ ] HI1: One held stick click from Menu Left / Right Entry (before 300 ms) goes Entry → Fn → Transition Set without a second click. This relies on Fn's repeating click chord
- [ ] HI2: Staggered Gyro toggle: hold LB, press RB, then release RB about 100 ms before LB. Gyro toggles, and `Gyro | L1: Modifier 0` becomes active while LB is held. Record whether the regular L1 modifier also appears, and whether releasing LB then scrolls down through L1: Double Tap. Repeat for Gyro → regular, with both press orders, and in the alternative with L2 / R2
- [ ] HI3: Alternative only: soft-pull both triggers during ramp-up, then fully pull one to exit. Mod 2 should enter without re-pulling, in both regular and Gyro mode. Also pull both triggers together from Base. This checks the F1 fix: `R2: Modifier 1` and its Gyro variant now repeat their LT → Mod 2 chord, like the other three pairs
- [ ] HI4: Output scope: the existing first-click check (a trigger pulled during Gyro Off Ramp Up) tests whether a removal fires an exposed **mouse** output. The double-tap-hold Escape / Tab checks test whether **key** outputs fire on the press that adds their layer; since 90.9 Enter / Backspace are typed by the chord itself (check K1). Record both results in the audit
