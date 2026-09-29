# Manual testing (Deck)

Implementation work is tracked in [todos.md](todos.md). Unchecked items below remain pending runtime validation.

- Covers the untested changes:
  - the trigger / ramp-up port
  - the Start / Select gyro shifts and nav keys
  - the menu entry split
  - the 90.1 layer reorder
  - the 90.2 ramp-up chord consolidation
- Load both VDFs fresh, not in the live editing session, and run every check on both layouts
- Written for the default. In the alternative, swap LB / RB ↔ LT / RT: the bumpers fire, and the soft-pull triggers are the modifiers
- If a bind applies the wrong layer, suspect the load-order swap (`findings/2026-07-11-layer-order-swap/`)

## Menu buttons

- [ ] Tapping Select sends Escape, and tapping Start sends Tab
- [ ] Holding either for 300 ms brings up its Fn layer, and the F-keys work
  - On release nothing is sent
  - The face buttons are back to normal
  - The next tap still sends Tab / Escape
- [ ] Start-delay reset: after an interrupted hold, keep holding or hold again, and the Fn layer comes up
- [ ] Enter / Backspace: Select → Start sends Enter, and Start → Select sends Backspace. Try both quickly (under 300 ms) and with the Fn layer up
  - Releasing in either order sends nothing extra, and the gyro stays off until both are released
  - Holding the second button repeats the key, and pressing it again while holding the first sends it again
- [ ] Double tap and hold repeats Escape / Tab, and releasing stops it
  - Note whether a quick double tap sends the key two or three times (known, not fixed)
- [ ] Menu button + stick click opens a Transition Set, and with the menu button held, the stick directions type punctuation
- [ ] In each Menu Fn layer, its eight directional keybinds (four LS + four RS) give haptic feedback with their punctuation keys. Check holds, direction changes, and inherited Fn directions in Transition Sets for unwanted buzzing or duplicate keys. Separate held-click mode-shift bindings retain their previous haptic settings
- [ ] Stick touch release: hold Start, touch a stick and lift off, then release Start. Menu Right: Fn comes up on the lift, and no Tab is sent. Select does the same with Menu Left: Fn, and no Escape
- [ ] Steam button recovery:
  - Hold a menu button until its Fn layer is up, press the Steam button, let go, and close the Steam menu
  - RS to the edge (or a face button) clears the Fn and entry layers, and the menu buttons work normally again
  - Enter / Backspace can currently survive the lower stack's cleanup. Verify their local overlay exits, and review invalid residual helpers under the owning-layer cleanup rule. Preserve still-held buttons; gyro suppression during menu use is intentional
- [ ] Stuck entry layer (for example, the Steam button within 300 ms of a menu press)
  - The other menu button clears it and then works normally
  - In the alternative, RS to the edge no longer makes it worse

## Modifier layers

- [ ] Nav keys with Start / Select: LB gives Insert / Delete, RB gives Home / End, and LB + RB (either order) gives PgUp / PgDn
- [ ] The same nav keys in Gyro mode
- [ ] Holding Start or Select in any modifier layer, in Base or Gyro mode, doesn't change the gyro. Confirm that's what you want
- [ ] After a nav chord, releasing the modifier doesn't fire its tap / scroll action, and Start or Select alone in a modifier layer still clears it

## Triggers and ramp-up

- [ ] LT / RT fire left / right click, and Start / Select work while a trigger is held
- [ ] In the Deck GUI, Base's right-stick outer edge shows three command entries, and both chords are set to Any
  - Default: the trigger chord selects LT / RT (partial and full pull), and the modifier chord selects LB / RB
  - Alternative: the other way around
- [ ] RS to the edge with nothing held:
  - The gyro turns off and Turning Ramp Up 0 starts
  - Turning Ramp Up 1 follows after about 250 ms
  - Moving back in restores the gyro and ends ramp-up, at either stage
- [ ] RS to the edge while holding a trigger keeps the gyro on during ramp-up, with no unwanted mouse repeats
  - Try each trigger alone at partial and full pull, then both
- [ ] Pulling a trigger after the gyro turns off, in both stages, brings the gyro back, and the first click registers
  - Letting go of one of two held triggers keeps the chord
  - Partial ↔ full pull changes work
- [ ] Holding a modifier on the way to the edge lets no ramp-up or gyro-off leak through
  - Try each modifier alone, then both
  - Try it again with a trigger held, and with the press / release order reversed
- [ ] Pressing a modifier during ramp-up ends ramp-up and enters the right modifier, the `Gyro |` version in Gyro mode
  - In the alternative, a partial pull keeps the block, and a full pull exits
- [ ] The edge / trigger / modifier checks above work the same in Gyro mode
- [ ] Interrupting the 250 ms stage change, recentering and retrying still reaches Turning Ramp Up 1 (the 300 ms reset)
- [ ] Stuck right trackpad:
  - Hold RB, touch the right trackpad, let go of both (try both orders), then push RS to the edge
  - Ramp-up works, and trackball momentum is intact
  - A thumb on the trackpad still blocks the edge
- [ ] Two-bumper tap cover:
  - A quick LB + RB tap still toggles Gyro mode
  - Holding both past 200 ms and releasing doesn't, even right after an interrupted attempt
- [ ] No new haptic pulse when RS hits the edge

## Default trigger reference match

- [ ] Load the default layout fresh and confirm both Base triggers match the July reference's trigger settings and mouse outputs (LT → left click, RT → right click)
- [ ] Check partial/full pulls, quick pulls, held firing, and release in Base, Gyro, and both ramp stages; a pull during Gyro Off Ramp Up restores gyro and registers the intended click
- [ ] Check inherited trigger behavior through modifier/cover layers, menu Fn outputs, and all seven Double Tap windows, including a trigger already held across entry/exit. Existing trigger overrides and blocks must retain their behavior

This change removes only Base's explicit `adaptive_threshold: "0"` settings.
Upper layers retain their existing settings and bindings: inherited trigger
settings may be affected, while explicit click/edge overrides remain in place.
No new layer mutations or timer operations were introduced. This follows the
reference configuration; it does not add a Soft Press hip-fire activator.
The alternative layout is unchanged.

## Left-stick recovery and Transition Sets

- [ ] Validate the new LS-edge recovery and Transition Set depth on the Deck in both layouts
  - Follow the [fresh-load checks](findings/2026-09-28-left-stick-recovery/CHANGES.md#verification-and-deck-checks), including both Mod 2 orders/Gyro variants, either-owner guards, outer-region behavior, and LS deflection held across every Double Tap window

## WASD modifier scaffold

Run on both layouts after a fresh load. The shipped modifier slot is empty;
assign a temporary modifier in a test copy for the checks that need output.

- [ ] Base left stick shows one empty Soft Press command named **WASD Modifier** on its edge, with the reference's style/threshold settings. No `*` or other modifier key is sent by the shipped layout; WASD and Q click still work
- [ ] With a test modifier assigned, check slow deflection, quick deflection, held deflection, and return to neutral. Verify the intended WASD-only, modifier-only, and combined regions; adjust the user's key and preferred Hip Fire Aggressive/Relaxed style as needed, without changing the shared scaffold just to fit one game
- [ ] Verify inherited modifier behavior in Base, Gyro, ramp stages, stick-touch layers, and button overlays where the underlying stack exposes Base's LS edge
- [ ] Verify the modifier is displaced by the 16 LS-edge recovery layers (including both Fn layers), all seven Double Tap windows, and both menu Fn left-stick mode shifts; their cleanup, timers, and punctuation outputs retain their behavior
- [ ] Enter and leave those overrides while the stick is already deflected, as well as deflecting after entry. Check that no modifier stays held after release or after Steam-button recovery

## Missed releases and cleanup scope

- [ ] Validate recovery on the Deck after missed releases, in both layouts
  - Trace the underlying recovery owner and which overlays expose or block it; do not require every overlay to duplicate that recovery
  - Stale-state fallbacks must preserve valid held interactions. Normal releases, delayed-apply resets, timed expiry, and deliberate transitions are allowed during normal use
  - Verify intended survivors, including persistent Gyro, the still-held modifier side, and valid shared overlays; flag invalid residual overlays requiring another gesture for the ownership review
- [ ] Verify whether interrupted transitions can leave both Mod 2 press orders active and cause a recovery problem
  - Retain the nine-layer current-branch fallback unless that problem is demonstrated; do not automatically expand it to eleven removals
  - Preserve the combined tap cover's eight-layer released-side cleanup and persistent Gyro. The uncovered Mod 2 release has a separate eleven-layer cleanup plus an intentional Gyro state change
