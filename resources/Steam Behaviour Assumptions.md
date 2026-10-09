# Steam behaviour assumptions

**Status:** started 2026-10-02, 42 entries on 2026-10-03, from the
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
| A2 | A disabled source stops the lookup, and a group in a different source mode blocks the whole source: none of the lower mode's inputs carry over | Verified by the author, 2026-10-01 | Relies on it | Tap the right pad twice inside 150 ms (RTP Double Tap, a D-pad pad over Base's mouse pad): no `RTP: Entry Point` behaviour appears inside the window | R140, R145, R168; the Window and Flow audits; `Gamepad`'s sticks and pads, which are in other modes than Base's |
| A3 | Re-adding a layer that is already active doesn't move it | Verified: Valve's documentation, and the author on the Deck, 2026-09-30 | Relies on it | Hold L1, add R1, let go of L1, press L1 again, let go of R1, let go of L1: no scroll at any point (the rocking sequence) | R110; the Modifier 2 rocking order; every stack the chains build |
| A4 | A binding array runs bottom to top: the last stored command runs first | Verified by the author (long-standing) | Relies on it | One bind stored as [add X, remove X] leaves X on: the removal ran first | R110, R118, R123, R146, R147, R148; the rocking order |
| A5 | A layer added over an input that is already held doesn't fire its immediate layer command on that input (held-input rule 1). Layer commands only | Verified by the author's experience, 2026-09-29 | Relies on it | In [rule-test.vdf](../findings/2026-09-29-held-input-layer-transitions/rule-test.vdf): hold a button, add a layer whose Regular Press on it adds another layer. Nothing happens until the button is pressed again | R113, R115; since 90.16 also which layer a pad click lands in where its two ranges overlap: the outer Soft Press has a 5 ms delay and the centre one repeats, so the centre one fires first (A6) and the middle click wins the ring |
| A6 | In that layer, an activator with a start delay still fires when the delay ends, and one with Hold to Repeat fires at once: **a repeating action always triggers** (held-input rule 2). Until 2026-10-04 this row said "on its next repeat", which the simulator and the docs read as one repeat interval later; the author corrected that | Verified by the author's experience, 2026-09-29; the timing of the repeat stated by the author, 2026-10-04 | Relies on it | The same test with a 5 ms delay, then with Hold to Repeat: both fire without a new press | R113, R115; every 5 ms delay and repeating add |
| A7 | A Release in a layer that was added over a held button fires when that button is released | Verified by the author's experience | Relies on it | Hold L1, press A (the Tap Cover lands over held L1), let go of L1: the cover's Release clears the modifier | R124, R157, R172; every cover's Release; the transitions; since 90.28 the chorded menu chain's Entry Point, which the Fn layer adds on a button that is already down |
| A8 | A stick edge's Release fires in a layer that was added while the stick was already out | Unverified | Relies on it | Hold Start, flick the left stick out and back inside 200 ms, keep holding Start for 1 s, press a face button: an F-key means the guard came off on the edge Release (Deck gate G3 of 90.10) | R111; the stick guards, Steering's stick modifiers. Until 90.32 also the Entry Guard and the Fallback Hold |
| A9 | Removing a layer fires the exposed layer command on an input that is held (held-input rule 3) | Unverified, by the author's choice | Works either way | T4 in rule-test.vdf: press Select (adds R), hold RB; R's RB removes R and exposes Base's RB add. If the add fires without a new press, it holds | R114; every command that needs it also repeats |
| A10 | A key or mouse output fires on an input that is already held when its layer is added | Reported by the author, not isolated | Relies on it | Hold Start, press Select before Fn is up: one Backspace types, from the Fn layer that landed over held Select | R138; Fn's Backspace and Enter; W and S in a Steering window; since 90.33 W and S as Steering's fallback guard lands on a stick that is already out; since 90.14 every pad click's output, which lands on a click that is already down |
| A11 | A key or mouse output fires when a removal exposes it under an input that is held | Unverified | Relies on it | Push the right stick past the ramp threshold, then pull a trigger: the pull removes `Gyro Off Ramp Up`. If the first click registers on that pull, it holds | The first click after `Gyro Off Ramp Up`; keys exposed when the cursor removes itself; W and S after a Steering window. In 90.31 and 90.32 also W and S carrying on from the fallback's window to the Fallback Hold |
| A12 | An interrupted delayed `add_layer` can fail to fire on the next press. A repeated `remove_layer` of its target restarts the delay: it waits the full delay again, it isn't cancelled | Verified by the author's observation, clarified 2026-09-30 | Relies on it | Hold Select, let go before 200 ms, hold again: the Fn layer still comes up | R120, R121, R122 |
| A13 | Any `remove_layer` can reset a running start delay; an `add_layer` doesn't | Reported by the author, not isolated | Relies on it | In a test layout: a button with a 300 ms delayed add. At 200 ms fire an unrelated removal on another button. If the add lands near 500 ms, it holds | R123, R126, R141 |
| A14 | A delay starts again when a removal exposes it under a button that is held | Unverified | Relies on it | Push both sticks out while holding Start, recentre the right one before 200 ms, keep holding 1 s, release Start: silent means the first guard's Tap Cover delay came back (Deck gate G6 of 90.10) | Fn following a stick guard that came off; a guard's Tap Cover delay after a second guard comes off; in 90.33 Steering's 100 ms add of the fallback guard after a driver was let go with the stick still up; since 90.34 that add has no delay and repeats |
| A15 | A layer that binds a button while a delay is running on that button cancels the delayed action | Verified by the author, 2026-10-01 | Relies on it | Hold the left stick north, then hold Start for 500 ms: no `\` is typed, because the guard landed inside the Fn delay and Fn never came (Deck check G4 of 90.10) | R122; the stick guards; every Tap Cover over a delayed add; in 90.33 a driver pressed inside the 100 ms before Steering's fallback guard came on |
| A16 | A delay's clock starts when its layer is added, not at the physical press | Unverified | Relies on it | In Steering with no driver, hold A for 3 s, roll up and hold for 2 s, then let go: leaving Steering means the window's second started with the layer. Letting go half a second after reaching up should keep Steering (Deck check F4 of 90.11, for the 1.5 s exit until 90.30) | The Steering windows' 150 ms. In 90.31 and 90.32 also the fallback window's one second |
| A17 | Chords latch: once a chorded activator is active, releasing the chord button doesn't end it. It ends when the button it is bound to is released | Verified by the author's test, 2026-10-01 | Relies on it | Hold a chord button and the bound button, let go of the chord button: the chord's output carries on until the bound button is released | R112 |
| A18 | A `remove_layer` call makes Steam re-evaluate held inputs | Unverified (the author's hypothesis) | Works either way | T4 in rule-test.vdf settles it together with A9 | Nothing yet |
| A19 | On a D-pad-mode stick an inverted edge isn't caught reliably. A normal outer edge and its Release are. Mouse-mode sticks aren't affected | Verified by the author on the Deck, 2026-10-01 | Relies on it | Bind an inverted edge on a D-pad stick to a key and move the stick back to centre several times: some returns are missed | R111 |
| A20 | Long Press and Double Press misbehave when combined with layers | Verified by the author's report, 2026-09-30 | Relies on it | Not rechecked: the layouts had none from 90.6 to 90.21. Since 90.22 `Gamepad` has four, under an exception that rests on A44 | R108 |
| A21 | The desktop configuration drops every command entry after the third on an input | Verified by the author, 2026-09-30. That only the 4th is lost is unchecked | Relies on it | Apply a layout to the desktop configuration: the four second-press inputs show three entries, and the reset is the one missing (Deck check R3 of 90.6) | R109 |
| A22 | On a fresh VDF load, Steam can resolve runtime IDs by `Preset_` key order instead of list order | Verified: observed 2026-07-11 on `controller_triton` | Relies on it | Load a layout whose layer list and `Preset_` numbers disagree: the out-of-order layers swap ([findings](../findings/2026-07-11-layer-order-swap/FINDINGS.md)) | R104 |
| A23 | Deleting a layer shifts every later runtime ID down by one | Verified (the documented file format) | Relies on it | Not needed: it follows from IDs being positions | R103 |
| A24 | Adding or removing another layer while a layer with an Always On action is active caused crashes | Reported by the author: a historical bug, not rechecked on a current client | Works either way | Not checked on purpose. The isolation rules stay whether or not it still happens | R140, R146, R147, R148, R149 |
| A25 | A release made while the Steam menu is open is missed: the layers stay on although no button is held | Verified by the author's observation | Relies on it | Hold Start until Fn is up, press the Steam button, let go, close the menu: the Fn layer is still on | R133; every cleanup function |
| A26 | Stick inputs inherit through the middle of the stack like any other input | Unverified. A 2022 community report says sticks inherit only from the top layer and the action set | Relies on it | Hold the left stick out, hold Start (the guard lands), click and release the stick, release Start: Steering comes on. A Q at the click means the click skipped the Entry Point under the guard (Deck gate G1 of 90.10) | R140; the stick guards and Fn layers inheriting the stick clicks; every audit's stick lookups |
| A27 | An active chord suppresses an interruptible Regular Press on the same input. How two chords on one input are ordered is not known | Reported: relied on since the July layout, not isolated | Relies on it | In `L1: Modifier 0` touch the right stick with LB held: nothing clears. Without LB held: the modifier clears | R133, R135 |
| A28 | A repeated layer removal on the right trackpad's touch breaks trackball momentum | Verified by the author's observation | Works either way | The procedure of A48 | Nothing: from 90.25 to 90.29 `RTP: Entry Point` had the reset, by the author's decision; since 90.30 it is off again, with the sticks', for another reason (the author's decision of 2026-10-04). Until 90.24 the pad's touch had none because of this |
| A29 | An explicit empty binding overrides the lower binding. An omitted input, an empty `inputs` object and an `inactive` group don't | Verified: documented, and used by every block. That the GUI saves a cleared binding as `empty_binding` is assumed | Relies on it | In a Double Tap window push the left stick to the edge: nothing below fires | R140, R141; the Window audit |
| A30 | A chord selector's Any is `0` and All is `1`. Legacy `chord_button` values are selector IDs, not bitmasks | Verified in the installed Steam chord UI schema, 2026-09-27 | Relies on it | Open a merged chord in the editor: both buttons show, set to Any | R127, R133; the guards the Cleanup audit reads |
| A31 | A repeating activator keeps its schedule when another layer is removed | Unverified | Works either way | In a test layout: a button repeating a key every 500 ms. Fire an unrelated removal at 300 ms. If the next repeat still lands at 500 ms, it holds | R114 |
| A32 | When two separate activators on one input are due at the same moment, their order is not fixed. Inside one activator the array still runs bottom to top | Unverified | Works either way | In `L1: Modifier 0` press A with L1 held: the output chord and the cover chord both fire, in either order | The cursor parents' two chords on each cancel input |
| A33 | Steam loads an exported VDF as written: the same layers, groups and bindings as the JSON it was made from | Reported: the author plays on exported layouts, but no fresh-load check is recorded for 90.6 to 90.13 | Relies on it | Load both VDFs fresh, not in the live editing session, and spot-check a modifier, Modifier 2, both Fn layers and the Steering entry | R151; every release; `convert_vdf.mjs` |
| A34 | A group marked `inactive modeshift` takes effect only while a `mode_shift` binding that targets it is held | Unverified | Relies on it | Under a regular and a Gyro modifier, touch each trackpad and press the face buttons and the D-pad: record the keys, and whether the normal Tap Cover still lands | The face and D-pad mode-shift targets under Base's trackpads; the cursor's cancel inputs |
| A35 | Hold to Repeat with no stated rate repeats at one fixed default interval | Unverified: the interval isn't known. The simulator uses 100 ms | Works either way | In a test layout: a key with Hold to Repeat and no rate. Count the repeats in one second | Most repeating entries state no rate, the cleanup functions among them; the simulator's `default_repeat_ms` |
| A36 | A chord is decided when its binding starts answering a held input: at the press, or when its layer lands or is exposed. Pressing the chord button afterwards doesn't start it | Unverified | Relies on it | Hold A, then hold LB: if A's chord with LB doesn't start, it holds | Every cleanup function's guard; the simulator; since 90.37 Base's Start/Select self-chords, including re-exposure after a window; `Cursor Gyro`'s both-sticks exit, which has a chord on each stick edge so that either stick can be the second; since 90.33 the chords of Steering's fallback guard on the left stick being out: on a bumper they choose between its Gyro modifier and ending the guard, and on the stick touches they hold the cleanup function back. In 90.31 and 90.32 the Fallback Hold's cleanup binds as its window closed over resting thumbs |
| A37 | When the layer that answers a held input changes and the new binding sends the same key, the key stays down with no release in between | Unverified | Works either way | In Steering hold a driver, flick the left stick, and watch W through the 150 ms window in a key tester: a gap means it doesn't hold | W and S through a Steering window; the simulator's `typed` |
| A38 | A stick group that doesn't state `edge_binding_invert` has a normal edge. It doesn't take the inverted setting of the group it replaces in a lower layer | Unverified | Relies on it | Under a held modifier wait for the cursor (200 ms). Push the right stick out: the cursor stays. Push the left stick out as well: the normal cover replaces it. If the cursor already ends with only the right stick out, its left edge is inverted | R111; the left-stick edge of the two Temp Cursor Gyro layers, which removes the layer over Base's inverted edge and states no setting; the Budget audit's inverted-edge check and the simulator, which read a group's own setting |
| A39 | An active Soft Press that is not interruptible suppresses an interruptible Soft Press on the same input | Unverified. A web search on 2026-10-02 found no report either way; the community Steam Input Wiki lists the Interruptible setting only for Regular, Release and Chorded Press | Works either way | In a test layout put two Soft Presses on a D-pad pad's outer ring: one inverted at 24996 with Interruptible off, typing A, and one normal at 23000 with Interruptible on, typing B. Rest the thumb about three quarters of the way out, where both are active. Only A means it holds | Nothing since 90.16, where both Soft Presses of the Click Entry Points are uninterruptible. 90.14 and 90.15 relied on it for the middle click's priority where a pad's two ranges overlap |
| A40 | A Soft Press on a pad's outer ring reads the thumb's distance from the centre, on the scale of the D-pad deadzone and the outer ring radius (0 to 32767). An inverted one is active inside its threshold, and it fires reliably on a D-pad-mode pad | Unverified. The layout used Soft Presses on stick edges only, and A19 found inverted edges unreliable on a D-pad stick. Community threads describe Soft Presses on a pad's outer ring | Relies on it | Click the right pad dead centre, then at each rim, twenty times each: the centre is always the middle click, the rim always Back, Forward or one scroll step | The two ranges of the Click Entry Points; the budget audit's inverted-edge check looks at sticks only |
| A41 | A D-pad group that inverts its outer ring and states no radius uses a radius of about 24996 of 32767 | Unverified. Inferred on 2026-10-03: Valve's bundled templates write 24995, 24996 or 24999 on all 30 D-pad groups that carry the setting, and none of those binds the ring. No documentation states the default | Relies on it | Load 90.13, open `RTP: Mouse Buttons`, right pad settings: read the Outer Ring Command Radius slider | The size of the centre range in the Click Entry Points (`CENTRE_RADIUS` in the 90.14 builder). If the default is different, the middle click's zone changed size in 90.14 |
| A42 | A layer held with `hold_layer` is taken off when the activator that holds it is no longer active, also when `add_layer` put the layer on first and the layer holds itself | Unverified. The author expects it ("a hold would behave like a Release with a removal") and calls holds unreliable; in 90.13 the same self-hold sat on layers that Base's own hold had put on | Works either way | In a test layout: A adds layer P, and P's B is a Regular Press that holds P. Press A, then hold B and let go: P gone means it holds. Then the 90.19 shape: let P's A hold P, press A once and let go | The self-holds of the four final pad click layers (90.19). If it is false, or the hold never fires because the layer lands on a pad that is already pressed (A5), the inverted repeating Soft Press removes the layer |
| A43 | On a button with an interruptible Regular Press, a Double Press and a Long Press: a tap sends the Regular Press once, after the Double Press time; a hold sends only the Long Press; a second press inside the Double Press time sends only the Double Press, for as long as it is held | Unverified | Relies on it | In `Gamepad`, with a gamepad tester open: tap Start (one Start, a moment late); hold Start for a second (no Start, a light pulse); tap Start and press it again at once, holding (Start stays down until let go). Any Start during the plain hold means it fails, and Start and Select move to the pad clicks alone | R108's exception and R168; `Gamepad`'s Start and Select; the simulator |
| A44 | Long Press and Double Press behave in a layer that no other layer is added over. This is the limit of A20 | Unverified | Relies on it | The procedure of A43, run a few times in a row and again after leaving and re-entering `Gamepad`: the three gestures keep working | R108's exception and R168; `Gamepad`'s Start and Select |
| A45 | A chord reads a button as held while that button carries Long Press and Double Press activators | Unverified | Relies on it | In `Gamepad`, hold Start for half a second and click a stick: the layout leaves `Gamepad` with the beep and pulse on Start's release. Nothing happening means it fails, and `Gamepad` needs Entry Points | R158's exception; `Gamepad`'s exit chord on both stick clicks |
| A46 | A Soft Press on a pad's outer ring is read on a touch alone, with no click, when the pad's D-pad group doesn't require a click | Unverified. The right pad's Double Tap window has read its ring on a touch since 90.6, with a Regular Press and the group's own radius; the Click Entry Points read Soft Presses on a pad that is clicked (A40) | Works either way | On 90.25 or 90.26: touch the right pad in the centre and at the rim, ten times each, then the left pad: a light bump every time in the centre, never at the rim, and the cursor or the swipes work after each touch | Nothing since 90.27. The two Touch Entry Points of 90.25 and 90.26 relied on it for the pad touch bump, which the author took out ([how it was built](../findings/2026-10-04-pad-touch-bump/README.md)). It is the first thing to check if the bump comes back |
| A47 | A pad in directional swipe mode gives no touch Release | Reported by the author, 2026-10-03: "there is no touch release for directional swipe modes" | Works either way | On 90.25 or 90.26: touch the left pad without swiping and lift, then touch its centre again: no bump the second time means `LTP: Entry Point` stayed on, so no Release fired | Nothing since 90.27: Base's left pad binds no touch. `LTP: Entry Point` of 90.25 and 90.26 bound a touch Release anyway and also ended on a swipe, a pad click's lift or the next stick touch |
| A48 | On a normal touch the right pad's Tap Cover reset fires once, as `RTP: Entry Point` lands on the thumb (A6), and not again: the Tap Cover lands at 150 ms and takes the touch over before the first repeat at 200 ms. That one removal leaves the trackball glide alone | Reported by the author, 2026-10-04: the one fire was felt on the Deck, where the reset stated no haptic until 90.29 and pulsed once at every touch. The glide: the author ran 90.28 and kept the reset ("it triggers once ... the tap cover gets applied; that'll override it"); not isolated. Until 2026-10-04 this row said the reset never fires, which A6 contradicts | Works either way | On 90.25 to 90.29: flick the cursor and lift, and it still glides | Nothing since 90.30: the reset is off the three Entry Points. It was the Tap Cover reset on `RTP: Entry Point` (90.25 to 90.29) |
| A49 | A layer command's two flags are the on-screen name and then the beep: `add_layer <layer> 0 1` beeps and shows no name | Unverified: not heard on the Deck yet. Read from the installed Steam client on 2026-10-04, whose message for the command lists `display` and then `beep`, and whose dialog has "Display name when changed" above "Beep when changed". On the Deck the author heard no beep from the commands written `1 0` (90.28) | Relies on it | Hold Select and Start together: `Menu Keys` comes on with a beep and no name on screen. Then hold Select alone until the Fn layer is up: its add has been `0 1` since February 2026, so it should beep as well | R161; every transition, the stateful layers' own exits and the `Menu Keys` entry (`0 1` since 90.29); the simulator's `beep` |
| A50 | A stick group that states no outer ring radius uses Steam's default, near the rim. It doesn't take the radius of the group it replaces in a lower layer | Unverified. The author's July layout states a radius only in Base and the Fn layers, and its stick clears work at the rim | Relies on it | Hold Select outside `Steering` with a stick half way out: the Fn beep comes at 200 ms, because the guard only lands at the rim | The 62 stick groups that stated 4915 or 7209 until 90.30: the modifiers' cursor cancel, the menu stick guards, `Cursor Gyro`'s and `Menu Keys`' both-sticks exits, the Steering layers |
| A51 | A D-pad group's `layout` 0 is "Radial Without Overlap": a diagonal presses only the nearest direction. `layout` 1 is "Radial With Overlap", which a group that states none also gets. A layer's group does not change the layout of a four-way group under it | Reported by the author, 2026-10-06, on the Deck with 90.34: `Steering`'s four-way took effect over Base, and the fallback guard's eight-way over `Steering` did not. The numbers were read from the installed Steam client on 2026-10-05, whose choices list `RadialWithOverlap` as 1 and `RadialNoOverlap` as 0. Whether a layer that states no layout takes the four-way of the layer under it is not checked | Relies on it | In `Steering` with no driver, hold the stick left and tilt it slowly up: A alone until past the diagonal, then the fallback's pulse and W, and from there W and A together. Then hold a driver and try a diagonal: one direction or two | Steering base's four-way left stick (90.34). Since 90.35 the fallback guard takes `Steering`'s place, so its eight-way group is never over the four-way one. The drivers' layers and the stick modifiers still sit over it. The simulator does not read the setting |
| A52 | The stored order of an input's entries can change what Steam does: a Release stored between a Regular Press and its guard chord can stop the chord from interrupting the Regular Press | Unverified: the author's suspicion, 2026-10-06. On a first load, with a thumb on a stick and a menu button held, the Fn layer's delayed add never came; the menu Entry Points' stick touches were stored that way from 90.24 to 90.35. Nothing found online says the stored order matters or that it can't (searched 2026-10-06): Valve's activator page is silent on it | Works either way | Load 90.36 fresh, rest a thumb on a stick and hold Select for a second: the Fn beep at 200 ms. If it comes there and did not on 90.35, it holds | R133; since 90.36 every cleanup input stores its Regular Press, then its guard, then its Release, so nothing depends on it |
| A53 | A Soft Press on a D-pad stick direction with activation_threshold 29031 activates only near full deflection, and its repeating layer add fires on entry above that threshold | Unverified, author requested the right-stick ramp threshold for Steering up/down, 2026-10-07 | Relies on it | In Steering push up/down shallowly: no fallback; approach the rim: one strong pulse and fallback W/S. Enter Steering while already beyond the threshold | 90.38 Steering fallback entry; simulator checks binary full deflection only, not numeric distance |
| A54 | An activator-local inverted D-pad edge can reliably run a repeating chord on either driver when that edge binding answers the inward input | Unverified; explicitly requested by the author, 2026-10-07, despite the earlier R111 ban | Relies on it | In fallback, inspect the active edge provider while moving inward with either driver held; test re-exposure after a covering layer exits | 90.38 fallback edge return; Gyro modifiers and covers can replace this input (A1), independently of whether inversion works |

A33 and A34 were found while sorting the Deck checks
([record](../findings/2026-10-03-deck-check-sorting/README.md)). A31 and A32 come from the timing contract of the archived replay
([TIMED-MODEL.md](../findings/2026-09-30-stack-search/TIMED-MODEL.md)), which
had to choose a behaviour for each.

A35, A36 and A37 are choices the press simulator
([simulator.py](../steam_layout/simulator.py)) had to make. Its docstring says
which assumption each of its behaviours models: A1 to A17, A21, A25, A27, A31,
A32, A35 to A39, A42, A43 and A49.

A38 was an open Deck check in the [to-do list](../todos.md#cursor-gyro) since
2026-10-01. It got its row when that list was re-sorted at the end of the plan.

A43, A44 and A45 came with the `Gamepad` layer in 90.22
([record](../findings/2026-10-03-gamepad/README.md)), whose Start and Select
use Steam's own Double Press and Long Press. The simulator models A43.

## Inverted Chorded Press in action layers

**Reported by the author, 2026-10-07.** These observations concern
**Chorded Press + Invert** inside action layers. Here, the **owner button**
is the button carrying the bind; the **chorded button** is the button selected
in the Chorded Press settings. This use of “owner” describes the binding,
not necessarily an interaction family's owning layer.

### Owner and chorded buttons

The inverted chord starts active. Pressing the owner button turns the bind
off; after releasing the owner, the bind can come back on. Pressing the
owner again can also reactivate or retrigger the inverted bind.

The chorded button behaves differently: pressing it shuts the bind off
completely. Pressing the chorded button again does not restore it. Once the
chorded button has killed the bind, it will not reactivate through that
button alone; the owner button must be pressed again, or the layer loaded
again as described below.

| Event | Observed effect |
|---|---|
| Owner button pressed | Can turn the inverted bind off, and on a later press reactivate or retrigger it |
| Owner button released | The bind can come back on |
| Chorded button pressed | Shuts the bind off completely |
| Chorded button pressed again | Does not reactivate the bind by itself |
| Layer loaded | Activates the inverted chord again |
| Remove Layer | Does not stop the active bind as it does with an inverted Regular Press; does not reactivate a stopped inverted chord |

### Layer workaround and removal limitation

Using L1/R1 as the chorded button works as a workaround when those buttons
also add/remove a layer: loading the layer activates the inverted chord
again, providing another way to restore a bind that has been shut off.

**Remove Layer does not stop the bind** the way it does with an inverted
Regular Press. Unlike normal Chorded Press behavior, however, the inverted
chord **does not reactivate on Remove Layer**.

This is the main limitation for cleanup: **inverted Chorded Press activates
on layer load, but does not reactivate on Remove Layer.** If removal caused
it to reevaluate and reactivate the way a normal chord does, this setup
could provide a clean state-reset mechanism. That is a proposed behavior,
not the observed behavior.

### Timing edge cases

The bind can also stop when:

- A Release Press is timed just as the owner/chorded-button interaction
  occurs.
- A layer is added and removed very quickly.

The fast add/remove case may result from layer removal and the inverted
chord's activation on layer load happening almost simultaneously. This
explanation is the author's hypothesis; the timing cause is not confirmed.

These observations describe an alternative cleanup mechanism under
investigation; they do not change the required guarded-recovery shape in
[Cleanup Functions](Cleanup%20Functions.md#the-kinds).

## Tuning notes

Things to try on the Deck that are about feel, not about which layer answers.
None of them is a gate. Each comes from a check in the retired Deck checklist
([migration record](../findings/2026-10-03-deck-check-sorting/README.md)).

| From | What to try |
|---|---|
| Reference gyro RG1 to RG3 | The gyro and the right stick are set to the July reference's values (tests check the numbers). Does aiming feel like the reference: in Base, with the cursor on, and through the two ramp stages? |
| WASD modifier scaffold WM2 | Assign a key such as Walk to the empty WASD Modifier slot on the left stick's edge. Try a slow, a quick and a held push: are the WASD-only, modifier-only and combined regions where you want them? |
| Temp cursor gyro TC2 | The cursor's entry gives one strong pulse at 200 ms (300 until 90.25) and nothing after. Is one pulse right, and is there any buzzing while the cursor stays on, or on a retried hold? |
| Temp cursor gyro TC8 | Both sticks at about a quarter of their travel end the cursor (radius 4915 on the left, 7209 on the right). Do the two sticks feel alike, and is a quarter the right distance? |
| Menu buttons MB7 | In each Menu Fn layer the eight stick directions type punctuation with a haptic tick. Hold them, change direction, and try the same directions inside a transition: is there unwanted buzzing, or a duplicate key? |
| 90.6 P1 | In a Double Tap window a left-pad swipe types its key directly. Does the swipe feel like Base's, in sensitivity and haptics? |
| 90.33 G1 | The fallback's bump: one strong pulse as the fallback guard comes on, at once since 90.34, and another when a bumper at centre ends it. Is the pulse the right strength? And where on the diagonal should Steering base's four-way stick turn from A or D into the fallback (A51)? (From 90.11 to 90.32 the tuning was the hold exit's warning pulses and its length.) |

## Two that are kept apart

A7 and A8 look like one assumption and were written as one in places. A
Release on a **button**, in a layer added while the button was held, is
established (A7): every Tap Cover works that way. The same on a **stick
edge** has never been isolated (A8). The stick guards, Steering's stick
modifiers rest on A8. Until 90.32 the Entry Guard and the Fallback Hold did
too.
