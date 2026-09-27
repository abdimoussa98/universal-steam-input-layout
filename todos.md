# Todo:

## Done

- [x] Make L1&R1: Tap Cover interruptable (in R1!L1, L1!R1, R2!L2, and L2!R2 layers)

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

- [ ] Add left stick layer cleanups to match right stick cleanup behavior
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

## Carried over

- [ ] Make base gyro activation dependent on: left stick deflect, right stick deflect, left stick touch, right stick touch, Select, and Start all being held at the same time. This removes the need for mode shifts everywhere we want to hold Start and Select (L1/R1 layers and Menu button layers)
- [ ] Handle cursor gyro layer (may be covered by Menu gyro above)
- [ ] Clear all unnecessary layers on action set swap
- [ ] Add temp gyro to both right and left stick touch
