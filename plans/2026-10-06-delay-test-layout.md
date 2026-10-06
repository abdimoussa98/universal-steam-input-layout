# Plan: a test layout for start delays and layer changes

**Status, 2026-10-06:** step 1 of the author's request: the scenarios, for
review. Nothing is built. The layout and the sheet to fill in come after the
author has picked the scenarios. Revised the same day, after the author
redescribed the delay fix: group 1 is new, and comes first.

The author: "create a layout to help me determine how each of these
interactions work with audible beeps and haptics with a testing scenarios
sheet."

It follows the [audit](../findings/2026-10-06-delay-interruptions/README.md)
and [what is written online](../findings/2026-10-06-delay-interruptions/ONLINE.md).

## What the author observed: the fault behind the delay fix

The author, from memory, 2026-10-06: "If you enter a layer with a delay that
adds another layer and you interrupt it (only tested with a cover layer
interruption that adds the layer that was in the intended delay) the next time
you enter that layer the delay does not fire. This was tested with l1 mod 0
before the cursor temp gyro layer was added, so the release would always fire
after re-entering after the interrupt."

In that layout, which is the July reference's shape:

| Layer | Input | Bind |
|---|---|---|
| `L1: Modifier 0` | LB | After 300 ms: adds `L1: Tap Cover`. No delay fix |
| `L1: Modifier 0` | LB let go | Removes the modifier, opens `L1: Double Tap`: a scroll step |
| `L1: Modifier 0` | A, with LB held | Types G and adds `L1: Tap Cover` |
| `L1: Tap Cover` | LB let go | Removes the cover and the modifier. No window |

The fault, step by step:

1. Hold LB. Inside 300 ms press A: the Tap Cover lands early, by A's bind.
   The delay is interrupted by its own target.
2. Let go. The cover's Release cleans up.
3. Hold LB again, for as long as you like. The cover never lands.
4. Let go. The modifier's own Release fires: the window opens and scrolls.

**What was tested:** one kind of interruption, the target landing by another
bind. **Not tested**, by the author's account: a tap, another layer covering
the button, a removal elsewhere, and how long the fault lasts.

## What the author suspects, beside it

"It keeps restarting and then eventually a repeated click would just skip the
delay and instantly activate, given you re-enter the layer with the previously
interrupted delay." Tap LB at 0 ms, press again at 150 ms: the cursor would
land at 200 ms. Press again later: at once.

## The possible answers

| Name | What Steam would be doing | Who says so |
|---|---|---|
| **Fresh** | An interrupted delay is forgotten. Every press waits the full delay | The simulator; what the layouts assume |
| **Stuck** | After an interrupted delay the next entry never fires, until a removal of the target starts it again | The author's observation above (A12) |
| **Carried** | The first press's clock is kept while its layer is away. On re-entry the action fires when that clock runs out: early, or at once | The author's suspicion |
| **Shift** | The delayed press happens one delay after every physical press, tap or hold | Valve's description of the setting |

Apart from these: **Restart**, whether a removal elsewhere starts a running
delay again (A13).

My reading, to be tested and not a fact: Stuck and Carried could be one cause.
In step 2 the cover answers LB when it is let go, so the modifier's delayed
bind never sees the button come up. It may still count as pressed at the next
entry. Valve's 2017 note says an activator keeps its state across a layer
change. If so, the fault needs a cover that is still on at the let-go, and a
plain tap, where the modifier's own Release fires, would not cause it. O5
tests exactly that.

## How a result is read

| Signal | Means |
|---|---|
| Light pulse | The rig's layer started answering the button |
| Beep and strong pulse | The delayed add fired: the target landed by the delay |
| Medium pulse on letting go | The host's own Release fired: the target was not on. After a long hold this is the fault |
| Nothing on letting go | The target's Release fired |
| A typed line, if a text field is open | A letter per event. Holding L4 types a dot every 100 ms, as a clock |

- **Two copies of the layout.** A slow one, four times the real values (delay
  800 ms, delay fix 1000 ms), to judge by ear. A real-speed one (200 and
  250 ms), read from the typed line.
- **A tap** is down and up well inside the delay. **Inside** is before the
  first press's delay would have ended. **Hold** is three seconds.
- **Probe:** D-pad Up types the top layer's digit. **Clear:** Start removes
  every rig layer.
- The typed line needs Gaming Mode with a text editor added as a non-Steam
  game: the desktop configuration drops a button's fourth entry (A21).

## The rigs

A rig is a small set of layers on one button. The mapping is a proposal; the
calibration buttons of group 0 go on the D-pad and the triggers.

| Rig | Button | Shape |
|---|---|---|
| **Leave** | B | July's `L1: Modifier 0`, as in the table above, without the delay fix. Base's repeating press adds the host. The host's delayed chord adds the target. The host's Release removes the host. The target's Release removes both |
| **Leave, fixed** | X | The same, with the delay fix: a repeating press that removes the target, 50 ms slower than the delay (R120, R121) |
| **Stay** | A | The host is always on. The delayed action is a strong pulse and a letter. No Release. On Select: the same with an add |
| **Target helper** | R1 | With the rig button held: adds that rig's target. This is A under a held LB in July |
| **Cover helpers** | R4, R5 | R4 adds a plain cover that binds the button's Release only. R5 adds a cover that removes itself after half a delay, like a window |
| **Removal helpers** | L1, Y, L5 | L1 fires one removal of a layer that is not on. Y fires one removal of the rig's target. L5 repeats a removal every quarter delay while held |

## Scenarios

Outcomes are lettered so a result can be given as "O1: b".

### 0. The signals work

| # | Do | Outcomes |
|---|---|---|
| C1 | Press the two calibration buttons: one adds a layer written `0 1`, the other `1 0` | Which beeps, which shows a name (A49) |
| C2 | Press the three pulse buttons | Can light, medium and strong be told apart |
| C3 | Hold L4 for five seconds, then the button whose repeat states no rate | Dots per second: 10 for L4. The other gives the default rate (A35) |
| C4 | Hold B three seconds, let go. Then tap B | Hold: light pulse, beep one delay later, nothing on letting go. Tap: light pulse, medium pulse on letting go |

### 1. The fault as observed

| # | Do | Outcomes |
|---|---|---|
| O1 | Hold B. Inside the delay press R1: beep, the target lands early. Let go of both. Then hold B three seconds and let go | a: beep one delay in, nothing on letting go (Fresh). **b: no beep, medium pulse on letting go: the fault (Stuck)**. c: beep at once (Carried) |
| O2 | After O1, hold B again, three times in a row | How long it lasts: a: back to normal on the next hold. b: never by itself |
| O3 | After O1 b: tap L1, then hold B. Clear and repeat with Y in place of L1 | What starts it again: any removal (A13), only the target's (A12), or neither |
| O4 | O1 on X, the rig with the delay fix | a: beep one full delay in: the fix works as described. b: still the fault. c: beep later than one delay: how much |
| O5 | O1 with another interruption in place of R1. i: a tap of B alone. ii: R4, still held when B is let go. iii: R4, let go before B. iv: a tap of L1 | Per kind: does the next hold beep. This says which interruptions cause the fault |
| O6 | Control. Hold B past the delay, let go. Hold B again | Beep both times, expected |
| O7 | O1, but press R1 after the delay has ended | As O6, expected: nothing was interrupted |

### 2. Leave: the suspicion

| # | Do | Outcomes |
|---|---|---|
| L1 | Tap B. Wait two seconds. Probe | a: nothing, Base on top. b: beep one delay later with nothing held, target on (Shift) |
| L2 | Tap B, press again inside, hold | a: beep one delay after the second press (Fresh). b: sooner, one delay after the first (Carried). c: two beeps. d: none (Stuck) |
| L3 | Tap B, wait three seconds, hold | a: one delay later (Fresh). b: at once (Carried). c: none (Stuck) |
| L4 | Hold B to just short of the delay, let go, press again at once, hold | a: one delay later. b: almost at once. c: none |
| L5 | Tap B five times quickly, then hold | As L2. Note if it differs from L2: that is "eventually" |
| L6 | Click B ten times, two a second, never holding | a: no beep. b: a beep on some click: which one |
| L7 | L2 with three gaps: a quarter, a half, three quarters of the delay | If b: is the wait always the delay minus the gap. That is the old clock, exactly |
| F1 to F7 | The same seven on X, with the delay fix | Per scenario: same as B, or different |

### 3. Stay: is the delay a shift?

| # | Do | Outcomes |
|---|---|---|
| S1 | Tap A | a: nothing. b: strong pulse one delay later, with nothing held (Shift) |
| S2 | Tap A, press again inside, hold | a: one delay after the second press. b: one delay after the first. c: both. d: nothing |
| S3 | Tap A five times quickly | Count the strong pulses: 0, 1 or 5 |
| S4 | S1 and S2 on Select, the add. Probe after each | The same letters, and whether the target is on with nothing held |

### 4. Covered while pending

| # | Do | Outcomes |
|---|---|---|
| V1 | Hold B. Half-way, press and hold R4. Keep both three seconds | a: no beep (A15). b: beep at the delay anyway |
| V2 | As V1, then let go of R4 and keep holding B | a: beep one delay after R4 is let go (A14). b: at once. c: never |
| V3 | Hold B. Half-way, tap R5. Keep holding | After the cover ends, a: beep one delay later. b: at once. c: never. This is the right pad's window over a held bumper |

### 5. A removal elsewhere while pending

| # | Do | Outcomes |
|---|---|---|
| U1 | Hold B. Half-way, tap L1 | a: beep on time (no restart). b: one delay after the tap (A13) |
| U2 | Hold B. At once, hold L5 for three seconds, then let it go | a: beep on time. b: no beep while L5 is held, then one delay after it is let go: the delay kept restarting |
| U3 | Hold X. Half-way, tap L1 | a: on time. b: one delay after the tap. c: the fix's interval plus one delay: the restart ran into the delay fix (R121) |

### 6. On 90.36 as it is, no build needed

Today's nearest match to the observed fault is Modifier 2: a face button
under both bumpers adds `L1&R1: Tap Cover`, the delay's own target. It has the
delay fix, so this checks the fix, not the fault.

| # | Do | Outcomes |
|---|---|---|
| R1 | Hold LB and RB, press A at once, let go of all. Hold LB and RB a second, let go | a: `Gyro` stays as it was: the cover landed at 200 ms. b: `Gyro` toggles, as after a quick tap of both: the cover never landed |
| R2 | Tap LB, wait a second, hold LB | The cursor's pulse, a: 200 ms in. b: at once. c: never |
| R3 | Click LB ten times, four a second | a: no pulse. b: a pulse on some click |

## What the results would point to

| Result | Points to |
|---|---|
| O1 b | The fault is reproduced, in its own shape. Everything else is read against it |
| O1 a | Not reproduced on this client. Run O1 at real speed before trusting it |
| O4 a | The delay fix does what the rule says |
| O5: only ii stuck | The fault needs a cover that is still on at the let-go. A tap is safe without the fix |
| O5: i stuck | A plain tap causes it too. The three touch Entry Points, which have no fix, are exposed (R120's exception) |
| O3: L1 clears it | Any removal starts a delay again (A13) |
| L2 b, L3 b | Carried: the suspicion, as stated |
| L2 b, L3 a, and L1 b or S1 b | Shift: the first press still fires on its own schedule |
| S1 b | The four delays whose host stays fire after a quick let-go, and the simulator is wrong there |

## Left for a second sheet

The guards: a chord holding back a cleanup (A27), with the other input down
first (A36), and the stored order (A52). A cover with the same delayed chord
(A16). A window's own timer. The same delays on a stick touch and on a
trigger's soft pull.

## To decide before the build

My defaults, if the author says nothing:

1. The typed line and the L4 clock are in, beside the beeps and pulses.
2. Both copies are built from one builder: slow and real-speed.
3. Groups 0 to 5 are in the first layout. Group 6 needs none.
