# Steam behaviour assumptions

**Status:** started 2026-10-02, 41 entries on 2026-10-03, from the
[rule inventory](../findings/2026-10-02-rule-inventory/README.md), phase 10 of
the [rule registry plan](../plans/2026-10-02-rule-registry.md).

An **assumption** is what we believe Steam does. The layout's rules
([Layer Definition of Done](Layer%20Definition%20of%20Done.md#rule-tables)) and
the tools rest on them. Each one is here once, with whether it has been
checked.

The Deck is used to settle an assumption, once, and again after a Steam update
that could change it. It is not used per layer or per release. When an
assumption is settled, change its status here; the rules, the simulator and
the tests that name its ID follow.

## How to read the table

A test reads it ([test_rule_registry.py](../tests/test_rule_registry.py),
through [rules.py](../steam_layout/rules.py)), so the shape is fixed.

| Column | What it holds |
|---|---|
| ID | `A` plus a number. Never reused or renumbered |
| Assumption | One plain statement of what Steam does |
| Status | **Verified** (by whom, when), **Reported** (the author has seen it in play, but it was never isolated), **Unverified**, or **Refuted** |
| The layout | **Relies on it**: the layout breaks if it is false. **Works either way**: the layout is built so that it doesn't matter, and a scenario test that touches it runs both ways |
| How to verify on the Deck | One short procedure |
| What rests on it | Rule IDs, and the layers or tools that depend on it. A test keeps the rule IDs in step with each rule's "Rests on" |

## The assumptions

| ID | Assumption | Status | The layout | How to verify on the Deck | What rests on it |
|---|---|---|---|---|---|
| A1 | The topmost layer that defines an input answers it. An input a layer leaves unbound comes from the stack below. Binding an input replaces all of its activators | Verified: Valve's documentation and the author's use | Relies on it | Add a layer that binds only A over Base: A sends the layer's key, B still sends Base's | R116, R130, R139, R140; every audit (`steam_layout/stacks.py`, `flow_model.py`) |
| A2 | A disabled source stops the lookup, and a group in a different source mode blocks the whole source: none of the lower mode's inputs carry over | Verified by the author, 2026-10-01 | Relies on it | Tap the right pad twice inside 150 ms (RTP Double Tap, a D-pad pad over Base's mouse pad): no `RTP: Entry Point` behaviour appears inside the window | R140, R145; the Window and Flow audits |
| A3 | Re-adding a layer that is already active doesn't move it | Verified: Valve's documentation, and the author on the Deck, 2026-09-30 | Relies on it | Hold L1, add R1, let go of L1, press L1 again, let go of R1, let go of L1: no scroll at any point (the rocking sequence) | R110; the Modifier 2 rocking order; every stack the chains build |
| A4 | A binding array runs bottom to top: the last stored command runs first | Verified by the author (long-standing) | Relies on it | One bind stored as [add X, remove X] leaves X on: the removal ran first | R110, R118, R123, R146, R147, R148; the rocking order |
| A5 | A layer added over an input that is already held doesn't fire its immediate layer command on that input (held-input rule 1). Layer commands only | Verified by the author's experience, 2026-09-29 | Relies on it | In [rule-test.vdf](../findings/2026-09-29-held-input-layer-transitions/rule-test.vdf): hold a button, add a layer whose Regular Press on it adds another layer. Nothing happens until the button is pressed again | R113, R115 |
| A6 | In that layer, an activator with a start delay still fires when the delay ends, and one with Hold to Repeat fires on its next repeat (held-input rule 2) | Verified by the author's experience, 2026-09-29 | Relies on it | The same test with a 5 ms delay, then with Hold to Repeat: both fire without a new press | R113, R115; every 5 ms delay and repeating add |
| A7 | A Release in a layer that was added over a held button fires when that button is released | Verified by the author's experience | Relies on it | Hold L1, press A (the Tap Cover lands over held L1), let go of L1: the cover's Release clears the modifier | R124, R157; every cover's Release; the transitions |
| A8 | A stick edge's Release fires in a layer that was added while the stick was already out | Unverified | Relies on it | Hold Start, flick the left stick out and back inside 200 ms, keep holding Start for 1 s, press a face button: an F-key means the guard came off on the edge Release (Deck gate G3 of 90.10) | R111, R137; the stick guards, Steering's stick modifiers, the Fallback Hold |
| A9 | Removing a layer fires the exposed layer command on an input that is held (held-input rule 3) | Unverified, by the author's choice | Works either way | T4 in rule-test.vdf: press Select (adds R), hold RB; R's RB removes R and exposes Base's RB add. If the add fires without a new press, it holds | R114; every command that needs it also repeats |
| A10 | A key or mouse output fires on an input that is already held when its layer is added | Reported by the author, not isolated | Relies on it | Hold Start, press Select before Fn is up: one Backspace types, from the Fn layer that landed over held Select | R138; Fn's Backspace and Enter; W and S in a Steering window; since 90.14 every pad click's output, which lands on a click that is already down |
| A11 | A key or mouse output fires when a removal exposes it under an input that is held | Unverified | Relies on it | Push the right stick past the ramp threshold, then pull a trigger: the pull removes `Gyro Off Ramp Up`. If the first click registers on that pull, it holds | The first click after `Gyro Off Ramp Up`; keys exposed when the cursor removes itself; W and S after a Steering window |
| A12 | An interrupted delayed `add_layer` can fail to fire on the next press. A repeated `remove_layer` of its target restarts the delay: it waits the full delay again, it isn't cancelled | Verified by the author's observation, clarified 2026-09-30 | Relies on it | Hold Select, let go before 200 ms, hold again: the Fn layer still comes up | R120, R121, R122 |
| A13 | Any `remove_layer` can reset a running start delay; an `add_layer` doesn't | Reported by the author, not isolated | Relies on it | In a test layout: a button with a 300 ms delayed add. At 200 ms fire an unrelated removal on another button. If the add lands near 500 ms, it holds | R123, R126, R141 |
| A14 | A delay starts again when a removal exposes it under a button that is held | Unverified | Relies on it | Push both sticks out while holding Start, recentre the right one before 200 ms, keep holding 1 s, release Start: silent means the first guard's Tap Cover delay came back (Deck gate G6 of 90.10) | Fn following a stick guard that came off; a guard's Tap Cover delay after a second guard comes off |
| A15 | A layer that binds a button while a delay is running on that button cancels the delayed action | Verified by the author, 2026-10-01 | Relies on it | Hold the left stick north, then hold Start for 500 ms: no `\` is typed, because the guard landed inside the Fn delay and Fn never came (Deck check G4 of 90.10) | R122; the stick guards; every Tap Cover over a delayed add |
| A16 | A delay's clock starts when its layer is added, not at the physical press | Unverified | Relies on it | In Steering with no driver, hold A for 3 s, roll up and hold: an exit about 1.5 s after reaching up means the clock started with the layer (Deck check F4 of 90.11) | The Fallback Hold's 1.5 s exit; the Steering windows' 150 ms |
| A17 | Chords latch: once a chorded activator is active, releasing the chord button doesn't end it. It ends when the button it is bound to is released | Verified by the author's test, 2026-10-01 | Relies on it | Hold a chord button and the bound button, let go of the chord button: the chord's output carries on until the bound button is released | R112 |
| A18 | A `remove_layer` call makes Steam re-evaluate held inputs | Unverified (the author's hypothesis) | Works either way | T4 in rule-test.vdf settles it together with A9 | Nothing yet |
| A19 | On a D-pad-mode stick an inverted edge isn't caught reliably. A normal outer edge and its Release are. Mouse-mode sticks aren't affected | Verified by the author on the Deck, 2026-10-01 | Relies on it | Bind an inverted edge on a D-pad stick to a key and move the stick back to centre several times: some returns are missed | R111 |
| A20 | Long Press and Double Press misbehave when combined with layers | Verified by the author's report, 2026-09-30 | Relies on it | Not rechecked: the layouts have none since 90.6 | R108 |
| A21 | The desktop configuration drops every command entry after the third on an input | Verified by the author, 2026-09-30. That only the 4th is lost is unchecked | Relies on it | Apply a layout to the desktop configuration: the four second-press inputs show three entries, and the reset is the one missing (Deck check R3 of 90.6) | R109 |
| A22 | On a fresh VDF load, Steam can resolve runtime IDs by `Preset_` key order instead of list order | Verified: observed 2026-07-11 on `controller_triton` | Relies on it | Load a layout whose layer list and `Preset_` numbers disagree: the out-of-order layers swap ([findings](../findings/2026-07-11-layer-order-swap/FINDINGS.md)) | R104 |
| A23 | Deleting a layer shifts every later runtime ID down by one | Verified (the documented file format) | Relies on it | Not needed: it follows from IDs being positions | R103 |
| A24 | Adding or removing another layer while a layer with an Always On action is active caused crashes | Reported by the author: a historical bug, not rechecked on a current client | Works either way | Not checked on purpose. The isolation rules stay whether or not it still happens | R140, R146, R147, R148, R149 |
| A25 | A release made while the Steam menu is open is missed: the layers stay on although no button is held | Verified by the author's observation | Relies on it | Hold Start until Fn is up, press the Steam button, let go, close the menu: the Fn layer is still on | R133; every cleanup function |
| A26 | Stick inputs inherit through the middle of the stack like any other input | Unverified. A 2022 community report says sticks inherit only from the top layer and the action set | Relies on it | Hold the left stick out, hold Start (the guard lands), click and release the stick, release Start: Steering comes on. A Q at the click means the click skipped the Entry Point under the guard (Deck gate G1 of 90.10) | R140; the stick guards and Fn layers inheriting the stick clicks; every audit's stick lookups |
| A27 | An active chord suppresses an interruptible Regular Press on the same input. How two chords on one input are ordered is not known | Reported: relied on since the July layout, not isolated | Relies on it | In `L1: Modifier 0` touch the right stick with LB held: nothing clears. Without LB held: the modifier clears | R133, R135 |
| A28 | A repeated layer removal on the right trackpad's touch breaks trackball momentum | Verified by the author's observation | Relies on it | Not rechecked: RTP touch has no reset for this reason | R120 |
| A29 | An explicit empty binding overrides the lower binding. An omitted input, an empty `inputs` object and an `inactive` group don't | Verified: documented, and used by every block. That the GUI saves a cleared binding as `empty_binding` is assumed | Relies on it | In a Double Tap window push the left stick to the edge: nothing below fires | R140, R141; the Window audit |
| A30 | A chord selector's Any is `0` and All is `1`. Legacy `chord_button` values are selector IDs, not bitmasks | Verified in the installed Steam chord UI schema, 2026-09-27 | Relies on it | Open a merged chord in the editor: both buttons show, set to Any | R127, R133; the guards the Cleanup audit reads |
| A31 | A repeating activator keeps its schedule when another layer is removed | Unverified | Works either way | In a test layout: a button repeating a key every 500 ms. Fire an unrelated removal at 300 ms. If the next repeat still lands at 500 ms, it holds | R114 |
| A32 | When two separate activators on one input are due at the same moment, their order is not fixed. Inside one activator the array still runs bottom to top | Unverified | Works either way | In `L1: Modifier 0` press A with L1 held: the output chord and the cover chord both fire, in either order | The cursor parents' two chords on each cancel input |
| A33 | Steam loads an exported VDF as written: the same layers, groups and bindings as the JSON it was made from | Reported: the author plays on exported layouts, but no fresh-load check is recorded for 90.6 to 90.13 | Relies on it | Load both VDFs fresh, not in the live editing session, and spot-check a modifier, Modifier 2, both Fn layers and the Steering entry | R151; every release; `convert_vdf.mjs` |
| A34 | A group marked `inactive modeshift` takes effect only while a `mode_shift` binding that targets it is held | Unverified | Relies on it | Under a regular and a Gyro modifier, touch each trackpad and press the face buttons and the D-pad: record the keys, and whether the normal Tap Cover still lands | The face and D-pad mode-shift targets under Base's trackpads; the cursor's cancel inputs |
| A35 | Hold to Repeat with no stated rate repeats at one fixed default interval | Unverified: the interval isn't known. The simulator uses 100 ms | Works either way | In a test layout: a key with Hold to Repeat and no rate. Count the repeats in one second | Most repeating entries state no rate, the cleanup functions among them; the simulator's `default_repeat_ms` |
| A36 | A chord is decided when its binding starts answering a held input: at the press, or when its layer lands or is exposed. Pressing the chord button afterwards doesn't start it | Unverified | Relies on it | Hold A, then hold LB: if A's chord with LB doesn't start, it holds | Every cleanup function's guard; the simulator |
| A37 | When the layer that answers a held input changes and the new binding sends the same key, the key stays down with no release in between | Unverified | Works either way | In Steering hold a driver, flick the left stick, and watch W through the 150 ms window in a key tester: a gap means it doesn't hold | W and S through a Steering window; the simulator's `typed` |
| A38 | A stick group that doesn't state `edge_binding_invert` has a normal edge. It doesn't take the inverted setting of the group it replaces in a lower layer | Unverified | Relies on it | Under a held modifier wait for the cursor (300 ms). Push the right stick out: the cursor stays. Push the left stick out as well: the normal cover replaces it. If the cursor already ends with only the right stick out, its left edge is inverted | R111; the left-stick edge of the two Temp Cursor Gyro layers, which removes the layer over Base's inverted edge and states no setting; the Budget audit's inverted-edge check and the simulator, which read a group's own setting |
| A39 | An active Soft Press that is not interruptible suppresses an interruptible Soft Press on the same input | Unverified. A web search on 2026-10-02 found no report either way; the community Steam Input Wiki lists the Interruptible setting only for Regular, Release and Chorded Press | Relies on it | In a test layout put two Soft Presses on a D-pad pad's outer ring: one inverted at 24996 with Interruptible off, typing A, and one normal at 23000 with Interruptible on, typing B. Rest the thumb about three quarters of the way out, where both are active. Only A means it holds | The middle click's priority where a pad's centre and outer ranges overlap (`LTP: Click Entry Point`, `RTP: Click Entry Point`). If it is false, one of the two layers lands there and which one isn't known |
| A40 | A Soft Press on a pad's outer ring reads the thumb's distance from the centre, on the scale of the D-pad deadzone and the outer ring radius (0 to 32767). An inverted one is active inside its threshold, and it fires reliably on a D-pad-mode pad | Unverified. The layout used Soft Presses on stick edges only, and A19 found inverted edges unreliable on a D-pad stick. Community threads describe Soft Presses on a pad's outer ring | Relies on it | Click the right pad dead centre, then at each rim, twenty times each: the centre is always the middle click, the rim always Back, Forward or one scroll step | The two ranges of the Click Entry Points; the budget audit's inverted-edge check looks at sticks only |
| A41 | A D-pad group that inverts its outer ring and states no radius uses a radius of about 24996 of 32767 | Unverified. Inferred on 2026-10-03: Valve's bundled templates write 24995, 24996 or 24999 on all 30 D-pad groups that carry the setting, and none of those binds the ring. No documentation states the default | Relies on it | Load 90.13, open `RTP: Mouse Buttons`, right pad settings: read the Outer Ring Command Radius slider | The size of the centre range in the Click Entry Points (`CENTRE_RADIUS` in the 90.14 builder). If the default is different, the middle click's zone changed size in 90.14 |

A33 and A34 were found while sorting the Deck checks
([record](../findings/2026-10-03-deck-check-sorting/README.md)). A31 and A32 come from the timing contract of the archived replay
([TIMED-MODEL.md](../findings/2026-09-30-stack-search/TIMED-MODEL.md)), which
had to choose a behaviour for each.

A35, A36 and A37 are choices the press simulator
([simulator.py](../steam_layout/simulator.py)) had to make. Its docstring says
which assumption each of its behaviours models: A1 to A17, A21, A25, A27, A31,
A32 and A35 to A38.

A38 was an open Deck check in the [to-do list](../todos.md#cursor-gyro) since
2026-10-01. It got its row when that list was re-sorted at the end of the plan.

## Tuning notes

Things to try on the Deck that are about feel, not about which layer answers.
None of them is a gate. Each comes from a check in the retired Deck checklist
([migration record](../findings/2026-10-03-deck-check-sorting/README.md)).

| From | What to try |
|---|---|
| Reference gyro RG1 to RG3 | The gyro and the right stick are set to the July reference's values (tests check the numbers). Does aiming feel like the reference: in Base, with the cursor on, and through the two ramp stages? |
| WASD modifier scaffold WM2 | Assign a key such as Walk to the empty WASD Modifier slot on the left stick's edge. Try a slow, a quick and a held push: are the WASD-only, modifier-only and combined regions where you want them? |
| Temp cursor gyro TC2 | The cursor's entry gives one strong pulse at 300 ms and nothing after. Is one pulse right, and is there any buzzing while the cursor stays on, or on a retried hold? |
| Temp cursor gyro TC8 | Both sticks at about a quarter of their travel end the cursor (radius 4915 on the left, 7209 on the right). Do the two sticks feel alike, and is a quarter the right distance? |
| Menu buttons MB7 | In each Menu Fn layer the eight stick directions type punctuation with a haptic tick. Hold them, change direction, and try the same directions inside a transition: is there unwanted buzzing, or a duplicate key? |
| 90.6 P1 | In a Double Tap window a left-pad swipe types its key directly. Does the swipe feel like Base's, in sensitivity and haptics? |
| 90.11 F2 | The Fallback Hold's warning: a strong pulse every 250 ms from the moment the stick goes up or down, and the exit with one beep at 1.5 s. Is the pulse too strong, and is 1.5 s the right length? (90.6 C1 had pulses from 1 s and the exit at 2.5 s.) |

## Two that are kept apart

A7 and A8 look like one assumption and were written as one in places. A
Release on a **button**, in a layer added while the button was held, is
established (A7): every Tap Cover works that way. The same on a **stick
edge** has never been isolated (A8). The stick guards, Steering's stick
modifiers and the Fallback Hold rest on A8.
