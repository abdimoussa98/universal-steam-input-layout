# Todo:

## Done

- [x] Make L1&R1: Tap Cover interruptable (in R1!L1, L1!R1, R2!L2, and L2!R2 layers)

## Manual testing (Deck)

- Covers the untested changes:
  - the trigger / ramp-up port
  - the Start / Select gyro shifts and nav keys
  - the menu entry split
  - the 90.1 layer reorder
  - the 90.2 ramp-up chord consolidation
- Load both VDFs fresh, not in the live editing session, and run every check on both layouts
- Written for the default. In the alternative, swap LB / RB ↔ LT / RT: the bumpers fire, and the soft-pull triggers are the modifiers
- If a bind applies the wrong layer, suspect the load-order swap (`findings/2026-07-11-layer-order-swap/`)

### Menu buttons

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
- [ ] Stick touch release: hold Start, touch a stick and lift off, then release Start. Menu Right: Fn comes up on the lift, and no Tab is sent. Select does the same with Menu Left: Fn, and no Escape
- [ ] Steam button recovery:
  - Hold a menu button until its Fn layer is up, press the Steam button, let go, and close the Steam menu
  - RS to the edge (or a face button) clears the Fn and entry layers, and the menu buttons work normally again
  - Enter / Backspace can survive the lower stack's cleanup. Another related-button press/release is an accepted lightweight-cover tradeoff; verify the local exit then restores the underlying controls. Gyro suppression during menu use is intentional
- [ ] Stuck entry layer (for example, the Steam button within 300 ms of a menu press)
  - The other menu button clears it and then works normally
  - In the alternative, RS to the edge no longer makes it worse

### Modifier layers

- [ ] Nav keys with Start / Select: LB gives Insert / Delete, RB gives Home / End, and LB + RB (either order) gives PgUp / PgDn
- [ ] The same nav keys in Gyro mode
- [ ] Holding Start or Select in any modifier layer, in Base or Gyro mode, doesn't change the gyro. Confirm that's what you want
- [ ] After a nav chord, releasing the modifier doesn't fire its tap / scroll action, and Start or Select alone in a modifier layer still clears it

### Triggers and ramp-up

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

## Gamepad layer

- [ ] Move gamepad layer → Menu Right + RS click / Menu Left + LS click
  - Note: requires same-side input (claw style); not frequent, so acceptable tradeoff

## Steering

- [ ] Add steering stateful set
- [ ] Add steering layer → Right Menu + LS click
- [ ] Include W / S modifiers on bumpers or left stick up / down
  - Intent: steering is primarily handled via bumpers
  - Left stick up / down acts as fallback to base layer behavior without exiting the stateful set
- [ ] Duplicate bumper mod 0 / 1 layers
  - Mod 0 when `L1!R1`: "W" + R1 (empty)
  - Mod 1 when `R1!L1`: "S" + L1 (empty)
  - Use opposite bumper to increment layer from mod 0–2
- [ ] Scroll wheel on joystick; hold up / down to exit

## Menu stateful set

- [ ] Add menu stateful set
  - Enter: Menu Left + Right
  - Exit: both sticks deflected, or one stick deflected + any face button
  - Inputs: D-pad → arrow keys; face buttons → Enter / Tab / Escape / Backspace
  - On entry: remove gyro stateful set

## Menu gyro

- [ ] Stateful menu gyro
  - Activate via Left Menu + RS click
  - Only remove when both left and right sticks are deflected
- [ ] Temporary menu gyro
  - Activate via L1 / R1 holds (tap covers)
  - Ensure proper add / remove behavior during hold lifecycle
  - Match Enter / Backspace to current Menu Left / Menu Right behavior

## Ramp up / triggers

- [ ] Remove trigger layers and chorded ramp ups
- [ ] Move ramp up gyro on / off logic to base layer
- [ ] In ramp up layers, have trigger remove gyro off layer
- [ ] Convert triggers to proper hip fire triggers

## Sticks

- [ ] Add left-stick edge cleanup only where needed, matching appropriate right-stick recovery
  - Review the 15 non-ramp candidates in cleanup audit F4 individually; these are not 15 mandatory additions. The Fn layers already cover both edges
  - LS edge cleanup overrides the inherited WASD modifier; RS edge cleanup overrides ramp-up. Prefer an adequate existing recovery path when an edge override would unnecessarily remove those functions
  - Ramp-up is more frequently blocked because its layer add/remove logic carries timer and ordering constraints; that asymmetry alone does not justify another LS cleanup
  - Preserve each exit's guards and family scope, movement behavior, timer protection, and Always On isolation; trace inherited LS-edge bindings through Double Tap windows before adding lower-layer cleanup
  - Document the recovery need and inherited action displaced for each chosen layer; see [the edge-cleanup tradeoff](resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions)
- [ ] Add WASD modifier scaffold (user-defined)
  - Empty bind on left stick (soft press) for WASD modifier
  - Supports: WASD only, modifier only, or both (hipfire aggressive / relax compatible)
  - User defines modifier key
- [ ] Add haptics to FN layers
  - Apply to LS and RS

## Global stateful behavior

- [ ] L1 + R1 clears all stateful sets
  - Exception: gamepad stateful set is preserved

## Bugs

- [ ] Fix tap cover / menu entry bug (start delay interrupt)
- [ ] Fix tap covers not properly re-adding after interrupt
- [ ] Split menu entry layer into separate Menu Left / Menu Right layers
- [x] Confirm menu helper/cover overrides are intentional within the lightweight design
  - Keep Backspace / Enter, Escape / Tab, and the two Menu Double Tap Covers local to their button/action; the underlying stack owns recovery. Release-only cleanup and another related-button press are accepted tradeoffs, not automatic reasons to add edge cleanup
  - Author confirmed: Start/Select menu interactions are not used during gameplay. Preserve disabled gyro in all six layers and the Escape / Tab RS-edge blocks; WASD modifiers and ramp-up are not required in menu context
  - Preserve the still-held second menu button; do not add Enter / Backspace removal to the first Fn button's release
  - Background: [lightweight covers and inherited cleanup](resources/Steam%20Input%20JSON%20Structure.md#lightweight-covers-and-inherited-cleanup) and both audits

## Layer cleanup

- [x] Complete the static [cleanup audit](findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) and [blocking audit](findings/2026-09-28-neptune-blocking-audit/AUDIT.md) for both layouts, including all layers, entry/exit references, dormant groups, and Always On ordering
- [x] Document per-layer cleanup and blocking, with [concrete scope examples](resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) and guidance in the editing skills
- [ ] Validate recovery on the Deck after missed releases, in both layouts
  - Trace the underlying recovery owner and which overlays expose or block it; do not require every lightweight cover to duplicate that recovery
  - Stale-state fallbacks must preserve valid held interactions. Normal releases, delayed-apply resets, timed expiry, and deliberate transitions are allowed during normal use
  - Verify intended survivors, including persistent Gyro, the still-held modifier side, and accepted residual covers; record when another gesture is needed
- [ ] Verify whether interrupted transitions can leave both Mod 2 press orders active and cause a recovery problem
  - Retain the nine-layer current-branch fallback unless that problem is demonstrated; do not automatically expand it to eleven removals
  - Preserve the combined tap cover's eight-layer released-side cleanup and persistent Gyro. The uncovered Mod 2 release has a separate eleven-layer cleanup plus an intentional Gyro state change

## Carried over

- [ ] Make base gyro activation dependent on: left stick deflect, right stick deflect, left stick touch, right stick touch, Select, and Start all being held at the same time. This removes the need for mode shifts everywhere we want to hold Start and Select (L1/R1 layers and Menu button layers)
- [ ] Handle cursor gyro layer (may be covered by Menu gyro above)
- [ ] Clear all unnecessary layers on action set swap
- [ ] Add temp gyro to both right and left stick touch
