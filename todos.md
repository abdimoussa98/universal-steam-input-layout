# Todo:

The Deck checklist was retired on 2026-10-03, and this list was re-sorted the
same day. Press-by-press checks are scenario tests (`python3 -m tests.scenario`).
What is left for the Deck is in [the next section](#on-the-deck-the-unverified-assumptions).
A "validate on Deck" item whose checks became tests is closed below, with where
each check went ([migration record](findings/2026-10-03-deck-check-sorting/README.md)).
None of them was run on the Deck: a layer whose tests pass but rest on an
unverified assumption is done, and listed (author, 2026-10-02).

Reviewed 2026-10-01 against release 90.9 (69 layers per layout). Every version
has to pass the build audit, `python3 -m tools.audit_build`
([definition of done §10](resources/Layer%20Definition%20of%20Done.md#10-ship-it)).

Terminology: use **stateful layer** for a persistent action layer and refer to
its supporting layers separately. This replaces the earlier “stateful set”
wording. These features use layers throughout; action-set switching is excluded
because the author reports buggy behavior with Steam action sets.

## Steering exit and Fn feedback (2026-10-09)

- [x] **Implemented 90.48, 2026-10-10:** normal/Gyro two-driver hold haptics Off; Steering driver entries add W/S only, without redundant Guard removal. Guard's atomic handoff is retained pending the separate follow-up below. No new delays or layers. Both JSON/VDF pairs exported and backed up; 315 scenarios, 83 distinct regression methods and all four audits pass. [Release record](findings/2026-10-10-quiet-gyro-and-guard-handoff/README.md).

- [ ] **Guard ownership follow-up, 2026-10-10:** the requested remove-only Entry Guard exposes Steering's held up/down clear before W/S can acquire. Preserve its atomic handoff until a broader clear design avoids this race without relying on timer ordering. Direct-split probes failed 224/256 simulator cases; the 100 ms workaround was rejected against the author's recorded timer observations. [Investigation and candidate record](findings/2026-10-10-quiet-gyro-and-guard-handoff/README.md).

- [x] **Implemented 90.47, 2026-10-10:** silent normal/Gyro Temp Cursor adds; Steering inherits LST/RST after Entry Guard; both touch Double Tap windows explicitly output W/S on LS up/down and block the inherited Steering clear. Existing driver/menu window restrictions remain. No new layers. Both JSON/VDF pairs and version backups are saved; [release record](findings/2026-10-10-quiet-cursor-and-steering-touch/README.md).
- [x] **Implemented 90.44, 2026-10-10:** the old-style inverted Any-driver chord silently removes only Entry Guard; W/S-owned feedback, Modifier 0/1 edge Releases and their automatic Double Tap completion are explicitly Off. Both Steering Modifier 2 release clears retain Steering; six releases across the four Gyro/Steering Modifier 2 layers retain Cursor Gyro. Other cleanup targets and the ordinary Gyro toggle remain. The two Steering-clear beeps leave with their removed commands. Base/Ramp Up right-stick settings remain identical to the requested July reference. Both JSON/VDF pairs are validated, exported and backed up: [release record](findings/2026-10-10-steering-entry-and-quiet-drivers/README.md); [approved plan](plans/2026-10-10-entry-guard-edge-and-quiet-drivers.md).
- [x] Implemented the author's narrower follow-up in **90.42**, both live layouts: `Steering` base left-stick up/down directly clears the Steering family, retaining the `Soft_Press` threshold `29031`, and every Fn-layer apply gets a Low haptic bump. JSON/VDF exports and version backups are saved; no layers were added. See the [release record](findings/2026-10-09-fn-haptics-and-steering-clear/README.md) and [updated plan](plans/2026-10-09-steering-fallback-recovery.md). The earlier proposal to retain fallback entry with separate feedback is superseded.
- [x] Implemented the approved **90.43** [entry guard plan](plans/2026-10-09-steering-entry-guard.md): reused the dormant fallback slot, protected held/first movement, preserved valid W/S owners during Modifier 0/1 recovery, prevented stale driver/modifier re-add loops, and applied the [beep audit corrections](findings/2026-10-09-layer-beep-audit/README.md). The full-deflection clear remains after the guard disarms; no new layers or changes to the deferred two-driver release-order behavior. Both JSON/VDF exports and version backups are saved; [validation and release record](findings/2026-10-09-steering-entry-and-feedback/README.md).
- [ ] **Deferred by the author, 2026-10-09:** revisit two-driver release-order and held-driver recovery. The [retained proposal](plans/2026-10-09-steering-fallback-recovery.md#4-make-steering-quick-clears-symmetric-without-breaking-holds) proposed two dedicated Steering Tap Covers and symmetric stateful clearing. The 2026-10-10 request now preserves Steering through both Steering Modifier 2 release clears, so that old exit goal must be reconsidered before resuming it. Do not add the proposed layers in the current change. Recheck both-held entry, missed-release recovery, and the proposed broader Gyro Modifier 2 clear when resuming this work.
- [ ] On a fresh **90.44** Deck load, verify held-stick and centered-first-push protection, the driver-conditioned inward Guard exit, quiet W/S and Modifier 0/1 releases, Steering/Cursor persistence through the changed Modifier 2 releases, and one audible Base/Gyro toggle beep. Check the armed near-rim up/down clear and Fn's intended bump too. Follow the [release checks](findings/2026-10-10-steering-entry-and-quiet-drivers/README.md#fresh-load-checks-on-the-deck); automated checks do not establish native input delivery, the physical threshold or feedback.

## Menu chords and Steering fallback follow-up

- [x] Build the [2026-10-07 plan](plans/2026-10-07-menu-chords-and-steering-fallback.md): **90.38**, both variants ([record](findings/2026-10-08-steering-rtp-and-menu-chords/README.md)). Repeating menu entry chords, RTP access in Steering/fallback with window restrictions, delayed targets before RTP cleanup, near-rim `29031` directional Soft Presses with strong feedback, and the inverted repeating fallback edge chord.
- [ ] On a fresh Deck load, verify the current near-rim directional threshold (A53), silent right-pad touch and Low entry bump. Numeric thresholds and physical feedback are not established by the simulator. The inverted fallback edge became dormant in 90.42; 90.44 reuses its activator pattern for Entry Guard's driver-conditioned self-removal, so A54 needs verification on that current binding.
- [ ] **Deferred with fallback recovery:** decide whether a restored fallback return must also work through Gyro modifier/cover edge overrides. Historical 90.38 implements the local fallback chord; frozen scenario S2 records that these higher bindings still take precedence. Frozen scenario S3 covers the additive fallback-under-Steering stack.

## Deferred delay tests and the menu entry issue

- [ ] Verify the Base menu self-chords on a fresh Deck load. The [July comparison and 90.37 change](findings/2026-10-06-menu-base-chords/README.md) restore repeating, uninterruptible Start/Select chords in both layouts. This is the current candidate cause/workaround for Fn not appearing while a thumb rests on a stick; causation is unverified. Compare with 90.36 using both menu buttons and both sticks.
- [ ] Resume the [delay test layout and scenario sheet](plans/2026-10-06-delay-test-layout.md) later. Deferred by the author on 2026-10-06 while the menu activator difference is investigated. Keep the [delay audit](findings/2026-10-06-delay-interruptions/README.md), historical fault, proposed slow/real-speed rigs and scenarios; nothing is built. Existing delay fixes remain.
- [ ] If gyro still differs on the Deck, identify the active stack and triggering gesture. Base, Gyro and all four Gyro Modifier 0–2 active settings already match July in both variants; the [comparison](findings/2026-10-06-menu-base-chords/README.md#the-active-gyro-masks-and-settings-already-match) records the older gyro mode shifts and current response overlays separately.

## On the Deck: the unverified assumptions

The Deck is used to settle an assumption, once, and again after a Steam update
that could change it. Each has one procedure in its row of
[Steam Behaviour Assumptions](resources/Steam%20Behaviour%20Assumptions.md).
What rests on each one, [as of 90.32](findings/2026-10-04-fallback-window-replacements/unverified-assumptions.txt);
`python3 -m tests.scenario` prints the current list.

The layout relies on these twenty. If one is false, something is broken.
A40 and A41 came with 90.14, and the pad clicks rest on them. A43, A44 and A45
came with 90.22, and `Gamepad` rests on them. A46 and A48 came with 90.25; nothing rests on A46 since the touch bump went in
90.27, or on A48 since the Tap Cover resets went in 90.30. A49 came with 90.29:
every beep rests on it. A51 came with 90.34: Steering base's four-way stick rests on it.

- [ ] A8: A stick edge's Release fires in a layer that was added while the stick was already out (unverified; rests on it: 5 scenarios; R111)
- [ ] A10: A key or mouse output fires on an input that is already held when its layer is added (reported by the author; rests on it: 38 scenarios; R138)
- [ ] A11: A key or mouse output fires when a removal exposes it under an input that is held (unverified; rests on it: 9 scenarios)
- [ ] A13: Any `remove_layer` can reset a running start delay; an `add_layer` doesn't (reported by the author; rests on it: 4 scenarios; R123, R126, R141)
- [ ] A14: A delay starts again when a removal exposes it under a button that is held (unverified; rests on it: 4 scenarios)
- [ ] A16: A delay's clock starts when its layer is added, not at the physical press (unverified; rests on it: 14 scenarios)
- [ ] A26: Stick inputs inherit through the middle of the stack like any other input (unverified; rests on it: R140)
- [ ] A27: An active chord suppresses an interruptible Regular Press on the same input. How two chords on one input are ordered is not known (reported; rests on it: 10 scenarios; R133, R135)
- [ ] A33: Steam loads an exported VDF as written: the same layers, groups and bindings as the JSON it was made from (reported; rests on it: R151)
- [ ] A34: A group marked `inactive modeshift` takes effect only while a `mode_shift` binding that targets it is held (unverified)
- [ ] A36: A chord is decided when its binding starts answering a held input: at the press, or when its layer lands or is exposed. Pressing the chord button afterwards doesn't start it (unverified; rests on it: 12 scenarios)
- [ ] A38: A stick group that doesn't state `edge_binding_invert` has a normal edge. It doesn't take the inverted setting of the group it replaces in a lower layer (unverified; rests on it: 2 scenarios; R111)
- [ ] A40: A Soft Press on a pad's outer ring reads the thumb's distance from the centre, on the scale of the D-pad deadzone and the outer ring radius, and an inverted one fires reliably on a D-pad-mode pad (unverified; rests on it: 13 scenarios). If it is false, a pad click may send nothing
- [ ] A41: A D-pad group that inverts its outer ring and states no radius uses a radius of about 24996 of 32767 (unverified; rests on it: 9 scenarios). Read the slider on 90.13's `RTP: Mouse Buttons`; a different number goes into `CENTRE_RADIUS` in the 90.14 builder
- [ ] A43: On a button with an interruptible Regular Press, a Double Press and a Long Press, a tap sends the Regular Press once after the Double Press time, a hold sends only the Long Press, and a second press sends only the Double Press (unverified; rests on it: 2 scenarios; R108's exception, R168)
- [ ] A44: Long Press and Double Press behave in a layer that no other layer is added over (unverified; rests on it: 1 scenario; R108's exception, R168)
- [ ] A45: A chord reads a button as held while that button carries Long Press and Double Press activators (unverified; rests on it: 3 scenarios)
- [ ] A49: A layer command's two flags are the on-screen name and then the beep (unverified on the Deck; read from the Steam client, 2026-10-04; rests on it: R161 and every beep). Hold Select and Start: `Menu Keys` comes on with a beep and no name on screen
- [ ] A50: A stick group that states no outer ring radius uses Steam's default, near the rim, and not the radius of the group it replaces (unverified; rests on it: the 62 stick groups that stated 4915 or 7209 until 90.30)
- [ ] A51: A D-pad group's `layout` 0 is four-way (Radial Without Overlap) and 1 is eight-way; a layer's group does not change the layout of a four-way group under it (reported by the author on the Deck, 2026-10-06; rests on it: Steering base's four-way left stick, and the swap of 90.35). Open: whether a layer that states no layout takes the four-way of the layer under it

The layout is built to work either way under these thirteen. Settling one takes a
branch out of the tests:

- [ ] A9: Removing a layer fires the exposed layer command on an input that is held (held-input rule 3) (unverified; rests on it: 28 scenarios; R114)
- [ ] A18: A `remove_layer` call makes Steam re-evaluate held inputs (unverified)
- [ ] A24: Adding or removing another layer while a layer with an Always On action is active caused crashes (reported by the author; rests on it: R140, R146, R147, R148, R149)
- [ ] A31: A repeating activator keeps its schedule when another layer is removed (unverified; rests on it: R114)
- [ ] A32: When two separate activators on one input are due at the same moment, their order is not fixed. Inside one activator the array still runs bottom to top (unverified; rests on it: 1 scenario)
- [ ] A35: Hold to Repeat with no stated rate repeats at one fixed default interval (unverified; rests on it: 1 scenario)
- [ ] A37: When the layer that answers a held input changes and the new binding sends the same key, the key stays down with no release in between (unverified; rests on it: 2 scenarios)
- [ ] A39: An active Soft Press that is not interruptible suppresses an interruptible Soft Press on the same input (unverified). Nothing rests on it since 90.16; 90.14 and 90.15 did
- [ ] A42: A layer held with `hold_layer` is taken off when the activator that holds it is no longer active, also when `add_layer` put it on first and the layer holds itself (unverified; rests on it: 4 scenarios)
- [ ] A46: A Soft Press on a pad's outer ring is read on a touch alone, with no click, when the pad's D-pad doesn't require a click (unverified; nothing rests on it since 90.27). The pad touch bump of 90.25 and 90.26 relied on it; check it first if the bump comes back ([how it was built](findings/2026-10-04-pad-touch-bump/README.md))
- [ ] A47: A pad in directional swipe mode gives no touch Release (reported by the author; nothing rests on it since 90.27). `LTP: Entry Point` of 90.25 and 90.26 bound one anyway
- [ ] A48: On a normal touch the right pad's Tap Cover reset fires once and not again, and that one removal leaves the trackball glide alone (reported by the author, 2026-10-04). Nothing rests on it since 90.30: the reset is off the three Entry Points
- [ ] A52: The stored order of an input's entries can change what Steam does: a Release between a Regular Press and its guard can stop the guard from interrupting it (unverified; the author's suspicion, 2026-10-06; R133). Since 90.36 every cleanup input has one order

## Rules without a check

- [ ] Ten rules have no check and eighteen have one that covers only part: `python3 -m steam_layout.rules` lists them. Each is a to-do for a test
- [ ] Decide R116 for four layers, so it can be checked. The rule lets only a cover-type layer inherit a stick-touch Release. `Gyro Off Ramp Up` and `Steering | LS: Fallback Hold` bind neither stick's touch Release, and `LST: Double Tap` and `RST: Double Tap` bind only the other stick's. Are they exceptions, or findings?

## The pad window's Releases, the fallback's edge, the Tap Cover resets off (90.30)

- [x] Build [the plan](plans/2026-10-04-window-releases-and-tap-cover-resets.md) (author, 2026-10-04): built as **90.30** ([record](findings/2026-10-04-window-releases-and-tap-cover-resets/README.md) · scenarios [W1 to T2](tests/test_scenarios_90_30.py)). Five layers change. Not run on the Deck
  - Part 1: in `RTP: Double Tap`, Start, Select, L1 and R1 get a Release that removes the window and then that button pair's layers. On the simulator 304 of 304 cases of a button let go inside the window leave a layer on today, and none with the prototype
  - Part 2: the outer edge's Release comes off `Steering | LS: Fallback Hold`; up and down keep theirs
  - Part 3: the Tap Cover delay fix comes off `RTP: Entry Point`, `RST: Entry Point` and `LST: Entry Point`, for now. The author thinks the stick ones are behind the menu buttons doing nothing while a thumb is on a stick
  - Declined by the author: taking the 90.24 cleanup binds out of the Fallback Hold
  - [ ] For the author: whether the Click Entry Points' delay fix (90.26) should go too
  - [ ] On the Deck, in [this order](findings/2026-10-04-window-releases-and-tap-cover-resets/README.md#on-the-deck-in-this-order): the menu buttons with a thumb on a stick (the test of part 3), the pad window, the fallback, the Tap Covers

## One order for the entries of a cleanup input (90.36)

- [x] Build the author's decision of 2026-10-06: built as **90.36** ([record](findings/2026-10-06-cleanup-entry-order/README.md)). No bind changes. Not run on the Deck
  - Every input with a cleanup function stores its Regular Press, then its guard, then its Release (R133). 121 inputs per layout were stored otherwise: the stick touches of the four menu Entry Points (Release in the middle, since 90.24), of the two Scroll layers (Release first), and 109 inputs with the guard first
  - The author's suspicion (A52): with the Release between them the guard did not interrupt the Regular Press, so the Fn layer never came while a thumb was on a stick, seen on a first load
  - [ ] On the Deck: load it fresh, rest a thumb on a stick, hold Select for a second: the Fn beep at 200 ms. Then the modifiers as usual: 109 of the reordered inputs had worked with the guard first

## `Steering` and its fallback guard swap places (90.35)

- [x] Build the author's design of 2026-10-06: built as **90.35** ([record](findings/2026-10-06-steering-fallback-swap/README.md) · scenarios [S1 to S6](tests/test_scenarios_90_35.py)). 88 layers. Not run on the Deck
  - On the Deck with 90.34 the guard's eight-way left stick did not take effect over `Steering`'s four-way one (A51). Now the bind that adds the guard removes `Steering`, and each bind that removes the guard adds `Steering` first: a bumper at centre, and a thumb put on either stick with the left stick at centre
  - The guard carries `Steering`'s Start, Select and right pad itself, and the Gyro Modifier 2 quick tap beeps on the guard's removal too
  - Added on my own: a driver's press in `Steering` removes the three ramp layers before it adds its layer. One left under the driver's layer kept the gyro off until the driver was let go (possible since 90.34 inside 5 ms, and with the swap whenever `Steering` is handed back over a ramp stage)
  - [ ] On the Deck, in [this order](findings/2026-10-06-steering-fallback-swap/README.md#on-the-deck-in-this-order): W and A together in the fallback, a bumper at centre, the clear, both bumpers
  - [ ] On the Deck, open: while a driver is held, is the left stick four-way too? The drivers' layers and the stick modifiers sit over the four-way `Steering` and state no layout

## Steering base: open edges, a four-way stick, the fallback at once (90.34)

- [x] Build the author's design of 2026-10-05: built as **90.34** ([record](findings/2026-10-05-steering-four-way-and-open-edges/README.md) · scenarios [E1 to E3](tests/test_scenarios_90_34.py)). 88 layers. Not run on the Deck
  - `Steering` no longer blocks the stick edges, so turn assist runs in Steering base and in the fallback guard; it is off only while a driver is held. This reverses 90.13 for Steering base
  - `Steering`'s left stick is four-way; the fallback guard states eight-way. Up and down add the guard at once with a repeating press, so the order of stick and driver decides
  - In the alternative layout a soft trigger pull does not drive while the right stick is ramping: the ramp stages block it, as in Base, and the full pull ends them
  - The fix pipeline wrote the firing buttons' mouse buttons into the two Steering stick windows (gone again in 90.35), and in the alternative layout blocked a trigger's full pull in the two modifier windows (R140)
  - [ ] On the Deck, in [this order](findings/2026-10-05-steering-four-way-and-open-edges/README.md#on-the-deck-in-this-order): the pulse and W at once, the diagonal (A51), stick first and driver first, turn assist with and without a driver

## The fallback as a layer the stick brings in and the bumpers take out (90.33)

- [x] Build [the plan](plans/2026-10-04-steering-fallback-layer.md) (author's design, 2026-10-04 and 2026-10-05, after the July layout): built as **90.33** ([record](findings/2026-10-05-steering-fallback-guard/README.md) · scenarios [G1 to C2](tests/test_scenarios_90_33.py)). It walks back the fallback window of 90.31 and 90.32. Two layers fewer: 88. Not run on the Deck
  - `Steering`'s up and down add `Steering | LS: Fallback Guard` after 100 ms (at once since 90.34), with a strong pulse. It types W and S and stays when the stick is let go. A bumper pressed with the stick out adds its Gyro modifier; pressed with the stick at centre it ends the guard, with a pulse, and drives
  - The Gyro Modifier 2 quick tap also removes `Steering`, the guard and the Base modifiers, so both bumpers end in Base from the fallback too. Leaving `Steering` by holding the stick is gone
  - The Entry Guard became the fallback guard; the Fallback Hold and its window are deleted, and entering `Steering` adds no guard
  - Differs from the plan: after a bumper or menu hold with the stick let go, the simulator removes the guard (its cleanup function answers the thumb resting at centre). The Deck may keep it; the next bumper at centre drives either way
  - The exceptions register can scope an entry to a build (`where`): the frozen builders read the same register
  - [ ] On the Deck, in [this order](findings/2026-10-05-steering-fallback-guard/README.md#on-the-deck-in-this-order): the pulse and W, a bumper at centre, a bumper with the stick up, both bumpers with `Gyro` on and off, the clear, the driver and the stick together, entering with the stick held
  - [ ] For the author to check after trying it: a thumb put back on either stick at centre ends the guard (R169)

## The fallback's second in a window, the outer ring, the Entry Guard (90.31)

- [x] Build [the plan](plans/2026-10-04-fallback-window.md) (author's design, 2026-10-04): built as **90.31** ([record](findings/2026-10-04-fallback-window/README.md) · scenarios [F1 to G1](archived/fallback-window/tests/test_scenarios_90_31.py), retired with 90.33). One layer added: 90. Not run on the Deck
  - `Steering`'s up and down add the Fallback Hold and, on top, a new window that types W and S and removes itself after 1000 ms. The Fallback Hold underneath then types W and S, and its Release on up and down clears the Steering layers: hold for a second, then let go, to leave
  - Inside the second, letting up or down go or the edge letting go removes the window and then the Fallback Hold; `Steering` stays. A driver or a menu button removes only the window, and the Fallback Hold then clears the Steering layers, as it does for them after the second. Its cleanup binds (stick touches, the right stick's edge) clear the Steering layers too, held back while the left stick is out. The pulse is on up and down in the window
  - The author answered the plan's four points on 2026-10-04
  - Part 2 of the plan (author, 2026-10-04): the outer ring radius is fixed in all thirteen Steering layers. No timer is left in the fallback but the window's
  - Decided (author, 2026-10-04): Steam's default radius, stated as not inverted, in every Steering layer and the new window
  - Part 3 of the plan (author approved, 2026-10-04): the same radius fix in every other layer that states 4915 or 7209; the Entry Guard's four directions get a Release that removes it; the stick modifiers are left as they are
  - [x] Walked back in 90.33 before it ran on the Deck. Left from its Deck list: Fn with a thumb on a stick (A50), which 90.33 keeps
  - [x] Inside the window the drivers and the menu buttons take replacements and change no layer (author, 2026-10-04): built as **90.32** ([record](findings/2026-10-04-fallback-window-replacements/README.md) · scenarios [R1 to R4](archived/fallback-window/tests/test_scenarios_90_32.py), retired with 90.33). Start and Select type Tab and Escape, the drivers scroll. A button still held when the second ends is answered by the Fallback Hold and leaves Steering at that moment

## Investigations

- [ ] The menu Entry Points' stick-touch binds (author, 2026-10-06: "some oddities"): [audit](findings/2026-10-06-menu-entry-point-stick-touches/README.md), nothing changed. Their order (Regular Press, Release, guard) is unique to the four Entry Points; 56 other layers have Regular Press, guard, Release. It dates from 90.24, which put the new cleanup function in front of July's Release and guard; the split of 2026-09-27 did not cause it. The simulator shows nothing odd
  - [x] The author's answer (2026-10-06): on a first load, with a thumb on a stick and a menu button held, Fn never applied. Built as 90.36: the common order, on every cleanup input
  - [ ] Offered, not built: write the Entry Points' guard as the button mask, if 90.36 does not cure it
- [ ] Steam caps a delay and a repeat rate at 1000 ms (author, 2026-10-04). The fallback hold's exit is written as 1500 ms and its delay fix as 1550 ms; no other value in the layouts is over 1000
  - The author's numbers, for later: the exit at 950 ms and its delay fix at 1000 ms (the usual + 50)
  - Replaced the same day by [the fallback window plan](plans/2026-10-04-fallback-window.md): the timer becomes a window's 1000 ms, with no delay fix
  - My reading, not checked: if Steam caps both at 1000 today, the exit and its delay fix come due at the same moment, and the delay fix restarts the exit. That alone could make the exit unreliable
- [ ] The outer edge radius in the Steering layers (author, 2026-10-04: "why are they being set? It should just be the default"). All thirteen Steering layers set the left stick's outer edge to radius 4915, not inverted; 21 other layers do too
  - Where it came from: the Temp Cursor Gyro work of 2026-09-29 picked 4915 so that, with the D-pad stick's hysteresis, the edge comes on near 25% of travel and lets go near 5%. Steering took it on 2026-10-01 as the modifiers' pattern ([plan](plans/2026-10-01-stateful-transitions-implementation.md)). The numbers are calculated from Steam's code, never measured on the Deck
  - What it is for: the edge's Release means "the stick is back at centre". The stick modifiers and the Entry Guard end on it, and the 90.24 cleanup functions on the edge fire from 25% of travel
  - The risk the plan named: a stick that rests above 5% never lets the edge go, so layers that end on its Release stay on
  - The author, 2026-10-04: in the Steam editor the D-pad's Outer Ring Command Radius goes from 10,000 to 32,000, so 4915 is below what the editor can set (and so is the right stick's 7209, in 21 layers). The value was calculated on 2026-09-29 and never checked against the editor's range. The editor shows these layers at the lowest setting, which suggests Steam raises the value to 10,000; with the same hysteresis that is on near 40% and off near 20%, not 25% and 5%. Not confirmed
  - Also read in the Steam client, 2026-10-04: a haptic setting on an activator pulses "on activation and deactivation", so a pad click's strong pulses can come on the release as well
  - The July layout states no radius outside Base and the Fn layers, ends no layer on an edge's Release, and its fallback is two keys and a bumper exit ([reading](findings/2026-10-04-july-stick-clears/README.md))
  - The Steering layers are part 2 of [the fallback window plan](plans/2026-10-04-fallback-window.md). The limits are recorded in [Steam Input JSON Structure](resources/Steam%20Input%20JSON%20Structure.md#limits-the-steam-editor-sets)
  - [x] Decide with the author: the other 21 layers on the left stick, and the right stick's 7209. Decided 2026-10-04: the default radius there too, part 3 of the plan
  - Soft Press thresholds (author, 2026-10-04): the slider showed 0 to 20,000, yet all ten in the layouts are above 20,000. Assumed: the slider has its own scale, and the file's value runs like the outer ring's, 10,000 to 32,000. Nothing to fix there
- [ ] The Steering fallback hold is unreliable on the Deck (author, 90.29, 2026-10-04): up and down sometimes dead with no pulses, and the exit can't be relied on ([findings](findings/2026-10-04-fallback-hold-on-the-deck/README.md))
  - Suspect: the four cleanup binds 90.24 gave `Steering | LS: Fallback Hold`. Each removes the layer unless Steam sees the left stick as out, a stick-deflection chord nothing has checked. With that chord missed as the layer lands, the simulator has the layer added and removed about 20 times a second: no W, no pulse, no exit. On 90.23 the same miss costs only the exit
  - Also on the simulator, on 90.23 as well: a right-thumb lift from its stick during the hold moves the exit from 1.5 s to 3.05 s (A13, then the hold's own reset)
  - [ ] On the Deck: load the 90.23 snapshot and try the hold. Reliable there means the 90.24 binds are the cause
  - Declined (author, 2026-10-04): the four binds stay. What the author asked for is the edge Release off, part 2 of [the plan](plans/2026-10-04-window-releases-and-tap-cover-resets.md). Open: whether the exit should survive a right-thumb lift
- [x] Block the delay fix on `RTP: Entry Point` (author, 2026-10-04: "make a note to block the delay fix only on the rtp entry point"). Confirmed later the same day and widened: it comes off the pad's and both sticks' Entry Points, for now. It is part 3 of [the plan](plans/2026-10-04-window-releases-and-tap-cover-resets.md)
- [ ] Stick touches and the menu buttons (author, on the Deck with 90.29, 2026-10-04): "the menubuttons weren't working when touching them", and after the thumbs came off, "immediately beeping as if the fn layer was applied" ([findings](findings/2026-10-04-stick-touch-and-menu-buttons/README.md))
  - On the simulator three things stop a menu button near a stick: the stick guards (a stick past 15% of its travel holds Fn off), a stick's Double Tap window (Start and Select are dead for 200 ms after a short touch, and after the right stick is pushed and let go), and the thumb-lift entry (Fn at once, silent)
  - The simulator never gives an Fn beep sooner than 200 ms after the press. If the Deck did, the candidates are A14 and A16 (the delay under a guard counts from the press) and A12
  - Reproduced on the simulator (author's third observation, 2026-10-04): a menu button let go inside `RTP: Double Tap`, the 150 ms after a short right-pad touch, loses its Release, so its Entry Point and Fn layer stay on and the next press is in the Fn layer at once. A modifier does the same. It is the touchpad exception to R136, set aside on 2026-10-02; a fix in the 90.28 pattern is proposed in the findings, not built: in `RTP: Double Tap`, Start, Select and the two bumpers get a Release that removes the window and then that button's own layers. Waiting for the author's approval
  - The author's candidate (2026-10-04): the stick Entry Points' delay fix. By the layout the Tap Cover and the menu Entry Point cover it, and on the simulator it fires once per touch. It is the cause only if Steam keeps a repeat running after a layer covers its input, which nothing here has checked
  - [ ] The author's answers: tap or hold, touched or moved, and whether the beep came during the hold or on a later press
  - [ ] Whether the pad's pulse on 90.28 came once per touch or every 200 ms while the thumb rested; or a trial copy of 90.29 without the two stick resets
- [ ] Why do 19 layers block the trigger's full pull, and can those blocks go? (author, 2026-10-04)
  - What they are: an empty binding on `left_trigger/click` and `right_trigger/click` in the eight modifiers, the two scroll layers, `Menu Left: Escape`, `Menu Right: Tab`, the four menu Entry Points and the three transitions. 38 inputs in the default layout
  - What the Cleanup audit says: in the default layout every one covers nothing. Neither Base nor any layer the chains put under them binds the full pull. In the alternative layout 18 cover nothing, and 8 (in `Menu Left: Escape`, `Menu Right: Tab` and Base's two menu Entry Points) cover the two Turning Ramp Up layers, which bind the full pull there
  - My guess, not checked: they are left from when the full pull added the old trigger layers
  - The author's decision for now: keep them, and give each a guard and a cleanup under R171 ([suggested fixes](findings/2026-10-04-required-cleanups/suggested-fixes.md), decision 1). If they can go, that is 38 inputs with nothing on them instead of two entries each
  - To find out: when each block was added (the version snapshots), and whether a stack the chains don't model puts a full-pull binding under one
- [ ] Could an inverted chord replace the empty guard chord, to free entries under the three-entry rule (R109)? (author, 2026-10-03)
  - The feature: the Steam beta of September 2026 adds **Invert Activation** to the Chorded Press. In the file it is `edge_binding_invert` on the chord, the key the inverted Soft Press uses. Seen in the client installed on the Mac (build of 2026-09-25); not yet in any layout here
  - What it would save: a cleanup function (R133) spends two entries, an empty chord with the owner's button plus the repeating cleanup. One inverted chord, "clean up when the owner's button is not held", would do both. Per layout 140 inputs have that shape, with 152 empty guard chords, and 135 of those inputs are at three entries. A freed entry is what the layers on top of `Cursor Gyro` lack to carry its exit ([plan](plans/2026-10-03-cursor-gyro-and-gamepad.md#decisions))
  - The doubt: Steam describes it as "Fires when this input is released while no chord button is pressed. Pressing this input releases it." That inverts the bound input too, so it would fire on the Release, not on a press with the chord button up. If so it can't replace a guard
  - Deck check to settle it: on one button put an inverted chord with LB that types a key. Press the button without LB: does the key type on the press, on the Release, or while the button is up? It becomes an assumption row when something is built on it
  - If it works: the Cleanup audit, the simulator and R133 read a guard as the chords beside the cleanup, so all three change with it. The layout would also need the beta client until the feature reaches stable
- [ ] Investigate the Tap Cover reset on the stick Entry Points (author, 2026-10-04). Should `LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point` get it, and what does it cost? The recommendation below is not the author's
  - Built in 90.25 on all three (author, 2026-10-04; [record](findings/2026-10-04-pad-bumps-and-menu-keys/README.md#5-the-tap-cover-reset)). This to-do stays open for the Deck checks below, which are how the change is verified. The pad's reset reverses R120's old exception; if the glide breaks, it comes out again (A48)
  - The reset is R120's repeating removal: beside a delayed add, a Regular Press on the same input that removes only that layer, every delay + 50 ms. Three delayed adds have none: the 150 ms add of the Tap Cover on the touch of these three layers
  - Recommended: add it to `LST: Entry Point` and `RST: Entry Point`, every 200 ms. R120 asks for it on every delayed add and records no exception for the sticks. The touch has two entries, so it is the third (R109)
  - Recommended: leave `RTP: Entry Point` without it. That is R120's one exception: a repeated removal on the right pad's touch broke trackball momentum (A28, the author's observation, not rechecked). Changing it starts with a Deck check: add the reset, flick the cursor, see whether it still glides
  - Checked on a copy of 90.23 with the reset on two and on all three: the Budget, Window and Flow audits pass and the Cleanup audit's output is unchanged. Nothing removes a Tap Cover without its Entry Point (69 removals for each stick, 23 for the pad), so the reset stays silent on a normal touch: the cover lands at 150 ms and takes the input over before the first tick at 200 ms
  - What it would fix: a delayed add that was interrupted can fail on the next touch (A12). The cover then never lands, the Release after a long rest opens the Double Tap window, and a quick lift and re-touch counts as a double tap: `LST: Temporary Gyro` or `RST: Temporary Gyro` comes on unasked. No such failure is recorded for the sticks
  - Downside: it takes the last free entry on those two touch inputs. Nothing is waiting for it; the stick-touch helpers are left out of the required cleanups (R169)
  - Downside: thumbs rest on the sticks most of the time, far longer than a button that has a reset is held. If a cover is late, the reset ticks every 200 ms until it lands, and each tick is a removal that can restart a delay running somewhere else (A13). Example: L1's 300 ms cursor apply is pending, the stick's reset ticks, and the 300 ms start again from that tick. This is timing, so no audit sees it
  - Downside: a cover that failed lands at 350 ms, not 150. Without the reset it doesn't land at all
  - Downside for the pad only: A28, above
  - Deck check, is there a failure to fix: touch a stick for under 150 ms and lift. After a second, rest the thumb on it for a second, lift, and touch again at once. If Temporary Gyro comes on, the cover didn't land
  - Deck check, the cross-talk: with the reset added, hold L1 and count how often the cursor apply comes later than 300 ms while a thumb settles on a stick
  - Deck check, the pad (A28), first: with the reset on, flick the cursor and see whether it still glides
  - Then: keep or take out each reset by what the checks show, and bring R120's exception and A28 in line

## Brainstormed ideas

- [x] Implement brainstormed ideas (author, 2026-10-03 and 2026-10-04): built as **90.25**, one release ([record](findings/2026-10-04-pad-bumps-and-menu-keys/README.md) · [plan](plans/2026-10-04-pad-bumps-and-menu-layer.md) · scenarios [P1 to K7](tests/test_scenarios_90_25.py)). Twelve new layers, 78 to 90 per layout. Not run on the Deck
  - Part 1: a low bump on touch where a click would be the centre click: `RTP: Touch Entry Point` and `LTP: Touch Entry Point`, hand-over layers; Base's left pad is a D-pad and the swipes are in `LTP: Entry Point`
  - Part 2: `RTP: Middle Click` is a mouse pad, so the cursor moves while middle mouse is held
  - Part 3: `Menu Keys`: both menu buttons held for 150 ms, from Base or `Gyro`. A chorded tap types Enter or Backspace, a double tap and hold holds it: two chains of four layers
  - Part 4: five extra presses by default in the hidden-exit check
  - Part 5: the Tap Cover reset on `LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point`
  - [ ] Confirm what the build did differently from the plan ([list](findings/2026-10-04-pad-bumps-and-menu-keys/README.md#what-differs-from-the-plan)): `Menu Keys` without Entry Points (an R158 exception); the stick touches off in `Menu Keys`. Two others are settled: the hand-over layer on the left pad went with the bump in 90.27, and the chain running only on the first press of a hold was fixed in 90.28
  - [ ] Confirm the inherited inputs accepted while building: two R139 entries and two R136 entries in the exceptions register, all for the chorded menu layers. The other six R139 entries were for the pad bump and went with it in 90.27
  - [ ] On the Deck, in [this order](findings/2026-10-04-pad-bumps-and-menu-keys/README.md#on-the-deck-in-this-order), without the steps for the bump, which went in 90.27: the glide (A48), the chorded menu, `Menu Keys`' exits
  - [ ] A pad touch during a hold that is still counting postpones it, on the simulator: in 90.25 the cursor response at 700 ms where it was 300, the Fn layer at 450 where it was 200 ([table](findings/2026-10-04-pad-bumps-and-menu-keys/README.md#what-it-costs)); since 90.26, with every hold at 200 ms, 210 to 450 ms, and up to about a second with the right pad ([table](findings/2026-10-04-standard-delays/README.md#what-the-margin-does)). It rests on A13. Check on the Deck whether holds feel late with a thumb landing on a pad

## The silent Tap Cover resets and the beep flag (90.29)

- [x] The pulse at every touch of the right pad (author, on the Deck with 90.28, 2026-10-04): built as **90.29** ([record](findings/2026-10-04-quiet-resets-and-beeps/README.md) · scenarios [Q1 and Q2](tests/test_scenarios_90_29.py))
  - It was the Tap Cover reset on `RTP: Entry Point`'s touch: a repeating bind, so it fires as the layer lands on the thumb, and it stated no haptic. The reset stays (author) and states `haptic_intensity` 0, on the two stick Entry Points as well
  - [x] On the Deck: touch the right pad: no pulse. Closed without a run: the reset is off since 90.30
- [x] No beep entering `Menu Keys` (author, on the Deck with 90.28, 2026-10-04): the beep is the second flag of a layer command, and the layouts had set the first, which shows the layer's name (A49). All 22 commands written `1 0` are `0 1`: both adds of `Menu Keys`, its ten exits, the transitions' six menu Releases, Steering's 1.5 s exit and `Cursor Gyro`'s both-sticks exit
  - This repo's documentation had the two flags the wrong way round since February 2026. The Steam client's message for the command lists `display`, then `beep`
  - [ ] On the Deck: hold Select and Start: a beep and the strong pulse as `Menu Keys` comes on. If the beep comes and the pulse doesn't, the pulse is a separate fault: the hold bind has `haptic_intensity` 3, as the transitions' Releases have
  - [ ] On the Deck: enter and leave `Steering`, `Cursor Gyro` and `Gamepad`: a beep each time, and no name on screen

## The menu chain on every press, and the windows' right-pad touch (90.28)

- [x] The chorded menu chain runs on every press (author, 2026-10-04, after finding on the Deck that 90.26 "just fires enter"): built as **90.28** ([record](findings/2026-10-04-menu-chain-and-window-pads/README.md) · scenarios [M1 to W4](tests/test_scenarios_90_28.py)). 87 layers to 89. Not run on the Deck
  - The Fn layers' bind for the other menu button adds the chain's Entry Point, where it typed Enter or Backspace. The first button's hold and the stick-touch Releases add the Fn layer alone again
  - `Steering` and `Cursor Gyro` keep the key at once: the `Stateful |` Entry Points add their own copies, `Stateful | Menu Left: Fn Layer` and `Stateful | Menu Right: Fn Layer`
  - What was wrong in 90.25 to 90.27: the chain's Entry Point was added once per hold and removed itself on its first Release, so only the first press went through the chain. My change to the author's design, listed then as a deviation
  - [ ] On the Deck: hold Select, tap Start three times (Enter each time), then hold Start (`Menu Keys`); a quick press of both; the same in Steering (Enter at once, no `Menu Keys`) ([order](findings/2026-10-04-menu-chain-and-window-pads/README.md#on-the-deck-in-this-order))
- [x] In a Double Tap window the right pad's touch follows the stick touches (author, 2026-10-04): a Release that removes the window and `RTP: Entry Point`, `RTP: Tap Cover`, `RTP: Circular Scroll`, where it was an empty press. `RTP: Double Tap` is left out. The known replacements for the pads are one list now, rule R172
  - In the two stick windows and the two Steering windows the fix pipeline keeps only the window's own removal: the pad's layers can't be under them
  - [ ] On the Deck: rest a thumb on the right pad, tap L1, lift at once, touch again: the cursor moves and a click works

## The pad touch bump comes out (90.27)

- [x] Take the pad touch bump out (author, 2026-10-04): built as **90.27** ([record](findings/2026-10-04-pad-bump-removal/README.md) · [how the bump was built](findings/2026-10-04-pad-touch-bump/README.md) · scenarios [B1 to B4](tests/test_scenarios_90_27.py)). 90 layers to 87. Not run on the Deck
  - `RTP: Touch Entry Point`, `LTP: Touch Entry Point` and `LTP: Entry Point` are gone. Base's pads are those of 90.24: the right pad's touch adds `RTP: Entry Point` and its click adds `RTP: Click Entry Point`; the left pad is the swipe pad with its click
  - Kept: `RTP: Middle Click` as a mouse pad, the Tap Cover resets, the Click Entry Points' reset, `Menu Keys`, the 200 ms hold delays
  - A left-pad touch no longer postpones a hold. A right-pad touch still can, through the Tap Cover reset on `RTP: Entry Point` alone, if a reset's repeat that removes nothing restarts other delays
  - [x] Decide on the Deck whether that reset stays: it stays (author, 2026-10-04, after running 90.28). It fires once per touch and pulsed; silent since 90.29 (A48 and the [Tap Cover reset investigation](#investigations))
  - [x] The two things that were waiting here, the windows' right-pad touch and the `Menu Keys` chain, are built as 90.28 (above)

## Hold delays and the pad layers' ring binds (90.26)

- [x] Standardize the hold delays and give the pad clicks' outer bind a reset (author, 2026-10-04): built as **90.26** ([record](findings/2026-10-04-standard-delays/README.md) · scenarios [H1 to P2](tests/test_scenarios_90_26.py)). Twelve layers change. Not run on the Deck
  - Every hold delay over 200 ms is 200 ms: the bumper Modifier 0 and 1 (300), the Steering Modifier 0 and 1 (250). Both menu buttons into `Menu Keys`: 200, not 150
  - Every reset repeats at its delay + 50 ms, as before (R121). A first build had + 5; the author took it back the same day ([why](findings/2026-10-04-standard-delays/README.md#three-margins-with-every-hold-at-200-ms))
  - The second-press covers and the touches stay at 150 ms; the ramp-up layers are untouched
  - `RTP: Click Entry Point` and `LTP: Click Entry Point`: a reset for the 5 ms outer ring bind, on the pad's touch, every 55 ms (R120)
  - `RTP: Touch Entry Point` and `LTP: Touch Entry Point`: the outer bind starts at the inner one's threshold, 24996, with no delay. Gone with the layers in 90.27
  - [x] The R139 entry accepted while building (the right pad's ring under nine layers) is gone: with Base's click back in 90.27 the Flow audit has no finding there
  - [ ] On the Deck: the clicks, the holds and a right-pad touch during a hold ([order](findings/2026-10-04-standard-delays/README.md#on-the-deck-in-this-order), without its first step: the touch layers went in 90.27)

## Next: allowed activators and cleanup (90.6)

Implemented in 90.6 ([chorded delays](plans/2026-09-30-steering-chorded-delays.md),
[banned activators and dead groups](plans/2026-09-30-banned-activators-and-dead-groups.md)).
The audit now fails on Long/Double Press. The Deck gates below were re-sorted on 2026-10-03; none was run.

- [x] Validate steering chorded delays on Deck (gates C1–C5): fallback warning/exit, entry carry, window clock from layer add, consume + 300 ms reset, reset never strips the cover — **closed 2026-10-03 without a Deck run**
  - Where the gates went: C4 and C5 are one scenario test ([90.6 C4/C5/S7](tests/test_scenarios_90_6_to_90_9.py)) and C2 is 90.11 F7's. C1 and C3 are obsolete, replaced by 90.11 F1 to F9 and by 90.10 D5. They rest on A8 and A16
  - 90.11 replaces the fallback gate (C1) with [F1 to F9](tests/test_scenarios_90_11.py)
  - The [transition build](#stateful-layer-transitions) replaces the window clock (C3) with an Always On action. The consume hold stays on the direction but is chorded on Any driver instead of stick deflection. Those gates then need rewriting; the fallback warning/exit gate stays and gains S
- [x] Validate the prune and RTP chord on Deck (gates D1–D5): fresh load, RTP tap/hold scroll, RTP edges, mode shifts, temporary gyro — **closed 2026-10-03 without a Deck run**
  - Where the gates went: static tests (`test_layout_hygiene.test_no_unreferenced_groups_or_plain_inactive_slots`, `test_layout_hygiene.test_rtp_scroll_repeat_is_a_touch_chorded_delay`, `test_fixes.test_working_layouts_are_a_fixed_point`). That the file loads as written is A33
- [x] Validate the second-press cover resets (gates R1–R3), including that desktop drops only the 4th entry ([record](findings/2026-09-30-second-press-cover-reset/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gates went: R1 is a scenario test ([90.6 R1](tests/test_scenarios_90_6_to_90_9.py), rests on A10). R2 is A12 and R3 is A21, both verified by the author
- [x] Validate Transition Set 0's new stick-touch release on Deck (gate T1) ([record](findings/2026-09-30-touch-release-rule/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gate went: obsolete. The transitions were rebuilt in 90.10 (scenario 90.10 T4), and what the editor shows for the merged chord is A30, verified
  - Goes away with the [transition build](#stateful-layer-transitions), which drops the transition's chord-guarded stick-touch recovery. Only worth running if that build is delayed
- [x] Validate the derived Double Tap window blocks on Deck (gate B1) ([record](findings/2026-09-30-derived-window-blocks/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gate went: a static test (`test_double_tap_windows.test_rtp_double_tap_keeps_its_touch_selection_and_clears_the_fn_back_buttons`). Its trigger part is scenario 90.10 T10, which rests on A37
- [x] Validate the Double Tap window pads on Deck (gate P1) ([record](findings/2026-09-30-double-tap-pad-blocks/README.md)) — **closed 2026-10-03 without a Deck run**
  - Where the gate went: two static tests (`test_double_tap_windows.test_left_pad_swipes_send_keys_without_the_layer_api`, `test_double_tap_windows.test_right_pad_stays_the_mouse_with_its_click_cleared_and_a_touch_release`). The swipe feel is a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes)
- [ ] Deck check: do stick inputs (edge, click, touch, directions) inherit through the middle of the stack, or only from the top layer and Base? Put three layers up where only the middle one binds LS click. A 2022 community report says sticks skip the middle ([JSON Structure](resources/Steam%20Input%20JSON%20Structure.md#how-binding-overlay-works)). If true, the inheritance tools must model it
  - Assumption A26, listed [above](#on-the-deck-the-unverified-assumptions)
  - This is gate 1 of the [transition build](#stateful-layer-transitions): the stick guards and Fn layers inherit the stick clicks from the Entry Point. The author expects it to hold and the plan assumes it does ([test steps](resources/Stateful%20Layer%20Transitions.md#steerings-left-stick-and-the-deck-gates))
- [x] Build the intended-flow inheritance checker ([implementation plan](plans/2026-10-01-intended-flow-inheritance.md)) instead of resuming exhaustive stack/timer proofs ([record](findings/2026-10-01-intended-flow-checker/README.md))
  - Follow intended explicit layer-addition paths from Base; retain stack order, input/chord conditions and removals within each transition
  - For each relevant button, report the nearest inherited binding and original activators on each path
  - When paths expose multiple distinct non-Base bindings, recommend explicit clear/block; compare actual bindings and activators, not just owner names. Do not assume replacement is safe
    - Corrected 2026-10-01 (author): this misread the rule. Clear-or-override only applies under an Always On layer with an inherited layer command ([§8](resources/Layer%20Definition%20of%20Done.md#how-to-check-it)). The Flow audit now lists these as "varies" and doesn't fail on them
  - Handle above-layer interactions separately for lightweight covers; do not make global above-layer reachability a prerequisite
  - Benchmark the checker on both variants and audit cleanup functions/blocks against the project docs. Scope is intended flows, not every runtime interleaving
- [x] `RTP: Entry Point` over `RTP: Double Tap`: resolved by the author's mode rule; a source-mode change blocks inheritance, so the window's dpad pad never inherits Base's touch ([decisions](findings/2026-10-01-intended-flow-checker/README.md#author-decisions-2026-10-01))
- [x] Opposite-button overlays: removed in 90.9. The menu chords type Backspace / Enter directly (fix `menu_combo_keys`); the stray Escape / Tab when the first button is lifted first is accepted
  - The [transition build](#stateful-layer-transitions) takes the key back out of the Entry Points: their chord only adds Fn, and Fn types Backspace / Enter, as before the split (author, 2026-10-01)
- [x] Inheritance across a source-mode change: author rule, it blocks; documented in [Layer Definition of Done §8](resources/Layer%20Definition%20of%20Done.md#a-source-mode-change-blocks-inheritance)
- [ ] Use the Flow audit's per-layer reports to review cleanup lists and blocks (plan [§6](plans/2026-10-01-intended-flow-inheritance.md#6-follow-up-after-the-first-checker-is-useful))
  - Blocks are covered by the Window audit, which checks the one blocking rule: under an Always On layer, an inherited layer command must be cleared or overridden. Cleanup lists are not checked by any audit; see the Cleanup audit under [Layer cleanup](#layer-cleanup)
  - The per-layer report is now `audit_layer.py` (2026-10-01)
- [x] Name the audits and add one gate for every version: `audit_build.py` runs the Budget, Window and Flow audits on both layouts. In [definition of done §10](resources/Layer%20Definition%20of%20Done.md#10-ship-it) and the layout-apply skill (2026-10-01)
- [x] Deprecate the exhaustive stack/timed-proof audit as the default workflow; preserve code, tests and a compact research checkpoint for reuse, moved to [archived/](archived/README.md) on 2026-10-02 ([archive](findings/2026-09-30-stack-search/ARCHIVE.md))
- [x] Deprecate the depth-limited stack search and the family walk; every audit builds its stacks from backward chains (2026-10-01, [record](findings/2026-10-01-backward-chain-stacks/README.md#deprecated))
  - `flow_config.json` no longer declares families: a new layer needs no entry. Code and tests of both older searches are kept in [archived/](archived/README.md) since 2026-10-02, with comparisons frozen at 90.9
- [ ] Decide RTP Double Tap's LB and RB: their inherited values change with the stack, so §8 says clear ([finding](findings/2026-09-30-stack-search/README.md#what-we-learned))
  - At 90.9 the menu buttons and both trigger stages are cleared in that window. LB and RB are replaced with the scroll wheel, like the other windows. What's left to decide is whether that replacement stays or becomes a clear
- [ ] Periodically recheck whether Steam's desktop configuration still drops entries after the third; consider filing a Valve bug report (assumption A21). If it's fixed, revisit the [command entry budget](resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)

## Done

- [x] Make L1&R1: Tap Cover interruptable (in R1!L1, L1!R1, R2!L2, and L2!R2 layers)

## Stateful layer transitions

Agreed design, built in 90.10. Its 25 Deck checks became 19 scenario tests, 5 assumption procedures (A8, A14, A15, A26) and 1 obsolete check on 2026-10-03; none was run. The scenarios rest on A8, A9, A10, A11, A14, A16, A27 and A37 ([build record](findings/2026-10-01-stateful-transitions/README.md) · [scenario tests](tests/test_scenarios_90_10.py) · [implementation plan](plans/2026-10-01-stateful-transitions-implementation.md)): [Stateful Layer Transitions](resources/Stateful%20Layer%20Transitions.md) · [brainstorm record](plans/2026-10-01-stateful-layer-transitions.md) · [definition of done §11](resources/Layer%20Definition%20of%20Done.md#11-stateful-layers)

- [x] Build the transition structure in both layouts (90.10; [implementation plan](plans/2026-10-01-stateful-transitions-implementation.md); assumes both Deck gates pass: A26 and A8)
  - Entry Points: both sticks as D-pads, stick-click Release binds, Fn layers inherit the clicks, Fn delay 200 ms / reset 250 ms. The other menu button only adds Fn; Backspace / Enter are typed by Fn alone
  - Two stick guards split by stick and one shared menu Tap Cover, replacing the four protected `Steering | Menu …` layers (one new layer, 70 in total). A guard's menu release still opens the Double Tap window; the hold or a thumb lift applies the Tap Cover
  - Transition 1 (Select release clears for now, Start release enters Steering) and Transition 2 (clear, keeping Gyro); everything layer-adding blocked with empty bindings
  - Steering's own Entry Points; W/S driver layers send Tab / Escape on Start / Select; the plain menu press no longer drops Steering
  - Add the 2.5 s hold exit for S
- [x] Add `tests/test_stateful_transitions.py` (90.10). Extend it with every new stateful layer until all four gestures are taken
- [x] Rework Steering's left-stick centre detection (90.10): the inverted edge on a D-pad stick isn't reliable (seven layer groups; [list](plans/2026-10-01-stateful-layer-transitions.md#9-recentre-detection-decision-19))
  - Built as the author directed (2026-10-01): the stick-guard recipe. A normal, generous outer edge holds Modifier 0 / 1 and its Release cleans up, so rolling to A / D keeps the modifier. The entering direction carries the 250 ms hold that adds the Tap Cover (Any-driver chord, like the L1 / R1 modifiers); left and right add the Tap Cover with A / D; the opposite direction only cleans up; mapped-button cleanups are guarded by two All-chords, left-stick deflection plus each driver. The Tap Cover is never added by a driver press ([details](resources/Stateful%20Layer%20Transitions.md#steerings-left-stick-and-the-deck-gates))
  - Depends on the edge-Release Deck check below (A8)
  - Rebuild the two `Steering | LS …: Double Tap` windows as Always On windows; their 150 ms timeout rides on an inverted edge today (an oversight in the first build). Seven Always On windows become nine, under [definition of done §9](resources/Layer%20Definition%20of%20Done.md#9-always-on-layers). They bind the drivers themselves (W and S, Release removes the window first, then the family) and inherit nothing that changes layers
- [x] Add an audit check for the new rule in [definition of done §3](resources/Layer%20Definition%20of%20Done.md#3-activators): no layer command on an inverted edge of a D-pad-mode stick. Added in 90.10 as `inverted_edges` in the Budget audit
- [ ] Deck check for the stick guards: an edge Release fires in a guard that was added while the stick was already out. The mid-stack stick inheritance check above is a gate for the guards too ([both explained](resources/Stateful%20Layer%20Transitions.md#steerings-left-stick-and-the-deck-gates))
  - Assumptions A8 and A26, listed [above](#on-the-deck-the-unverified-assumptions)
- [ ] Deck check: does a `remove_layer` call re-evaluate held inputs, the way it restarts delays? (author's hypothesis, with the [chord latch](resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30))
  - Assumption A18. The layout works either way

## Gamepad layer

- [x] Gamepad layer on Menu Right + RS click / Menu Left + LS click: built in 90.22 as `Gamepad` ([record](findings/2026-10-03-gamepad/README.md) · [plan](plans/2026-10-03-cursor-gyro-and-gamepad.md) · scenarios [G1 to G7](tests/test_scenarios_90_22.py)). Not run on the Deck
  - Note: requires same-side input (claw style); not frequent, so acceptable tradeoff
  - Enters through `Transition Set 0`, created with this layer. The clear was renamed `Transition Set 2`
  - Out: Start or Select held plus a stick click. Not the Modifier 2 quick tap (author, 2026-10-03)
  - Start and Select use Steam's own Double Press and Long Press, the one exception to R108, because nothing can be added over `Gamepad` (R168)
  - [ ] On the Deck first: A43, A44 and A45 (the tap, the double press and the hold; and the exit chord). `Gamepad` relies on all three and none is verified. The fallback for A43 and A44 needs no layer: Start and Select on the pad clicks alone
  - [ ] Confirm the choices made while building: the exit fires at the click's press (R158 exception); the Long Press at entry (R162 exception); the grip map L4 L3, L5 B, R4 A, R5 Y from the archived set; the pad clicks as Select and Start

## Steering

[Sixteen-layer candidates](findings/2026-09-30-steering-lean/README.md) are generated for both variants: **16 additions, 71 total at the time, no new Always On actions**. Saves nine against the prior lean build. Installed in both working layouts as release 90.5; the original 36-layer candidate remains unchanged. Completion awaits [native acceptance](findings/2026-09-30-steering-lean/ACCEPTANCE.md). The layouts have 69 layers since 90.9 removed the two menu overlays.

**The [transition build](#stateful-layer-transitions) changes several behaviours listed below** (author decisions, 2026-10-01). Validating them on the Deck before that build tests behaviour that is about to change:
- Protected menu entry is replaced by the stick guards and one menu Tap Cover, and the commit is stick click released first, then the menu button.
- A plain Start or Select press no longer leaves Steering, so Steering can sit under the two menu Double Tap windows. With a driver held they send Tab and Escape.
- A driver press no longer adds `Steering | LS: Tap Cover`; a stick already held enters the modifier at once.
- Sideways keeps Modifier 0 / 1; the stick's edge Release ends it. The opposite direction only cleans up.
- The two Double Tap windows become Always On windows, so "no new Always On actions" no longer holds.
- The hold exit also applies to S. `Steering | LS: Entry Point` is renamed `Steering | LS: Entry Guard`.

Since 2026-10-03 Steering's press sequences are scenario tests (90.7 S, 90.10 D, 90.11 F and 90.13 N). The four "validate" items below predate them and haven't been matched against the scenarios one by one, so they stay open.

- [ ] Validate protected menu entry and disposable WASD entry on Deck
  - Right Menu + LS click, release menu to commit; either-stick deflection blocks automatic Fn during entry; deliberate clicks remain
  - Guard ends at LS center or driving press; initial carried W has no timeout
- [ ] Validate W/S ownership and held-opposite takeover
  - Right R1/R2 owns W, left L1/L2 owns S; no built-in bank
  - Dominant release clears old modifiers/gestures; a held opposite takes over. No Rearm layer
- [ ] Validate consolidated normal modifiers and scrolling
  - Mod 0/1 own Down/Up gesture state; actual center qualifies tap; sideways removes silently; reversal before 250 ms selects the other bank consumed
  - Shared normal Tap Cover, two Double Tap windows, one shared Double Tap Cover
  - Tap Cover (90.6): up/down do nothing, center removes Mod 0, Mod 1, then the cover; verify repeat reversal cancels the delayed opposite tick
- [ ] Validate simple Modifier 2 scrolling
  - Two ordered Modifier 2 variants; Up/Down wheel immediately and repeat while held; no Mod 2 gesture helpers
  - Uncovered opposite release clears all layers to Base; 200 ms hold/action coverage uses existing opposite-side single Tap Covers with the existing 250 ms reset
  - Covers preserve W/S and normal covered release behavior; opposite release restores consumed normal mapping without dropping the owner
  - Existing combined Tap Cover remains unchanged to preserve W/S inputs; face outputs remain independent
- [x] Move the fallback exit timer into `Steering | LS: Fallback Hold` (90.11, author 2026-10-02): the timer ran on while the stick was on A or D. `Steering`'s stick up and down only add the layer; the layer types W or S, exits at 1.5 s and leaves on Release; its edge pulses from the start and carries the reset ([record](findings/2026-10-02-steering-fallback-hold/README.md); 71 layers)
  - Nothing is added over the Fallback Hold or the Entry Guard (author): Start and Select type Tab and Escape there; Steering's Entry Points type W and S on stick up and down instead of inheriting the add
- [x] Audit check for a hidden exit (built 2026-10-02 as the Cleanup audit's seventh check, rule R136): a layer that can be added over another binds an input whose Release is that layer's exit, without carrying it (the 90.11 menu-tap case). Prototype and 90.12 results in [findings/2026-10-02-hidden-exit](findings/2026-10-02-hidden-exit/README.md); goes in the cleanup audit as a seventh check
  - Touchpad pairs are an exception for now (author, 2026-10-02; next item). On 90.13, 2 pairs remain, both passing: the menu Tap Cover over a stick guard (its menu Release still removes the guard). The 4 turn-assist pairs over the driver layers were fixed in 90.13 by blocking the right-stick edge in `Steering` (author). (A first run also listed 8 modifier pairs; that was a prototype bug, corrected)
  - Decided (author, 2026-10-02): a cleanup function removing the layer later is not a pass. The prototype uses the keeper rule: 0 findings outside the touchpad exception
- [x] The menu second-press layers inherited the Fallback Hold add (found 2026-10-03 by the 90.14 review; present since 90.11; fixed in 90.15). In Steering, a double-tap-and-hold of Select or Start with the left stick pushed up or down put `Steering | LS: Fallback Hold` over `Menu Left: Escape` or `Menu Right: Tab`, which took the menu button's Release and left the layer on. Both layers now type W and S on stick up and down, as Steering's Entry Points and the menu windows do ([record](findings/2026-10-03-menu-second-press-keys/README.md); scenarios [M1 to M4](tests/test_scenarios_90_15.py))
  - [x] The hidden-exit check missed it, and now counts landings (2026-10-03): any adding binding that answers on a stack the chains visited puts its layer on top of that whole stack. It finds the four pairs on 90.13 and 90.14 and none on 90.15 ([record](findings/2026-10-03-menu-second-press-keys/README.md#why-the-hidden-exit-check-missed-it))
- [x] The hidden-exit check reads the chain walk with six extra presses (author, 2026-10-04): every layer of every stack tested, by a compiled engine (`steam_layout/native.py`, `steam_layout/engine/chain_engine.cpp`); the audit needs a C++ compiler. The capped walk and the first engines of 2026-10-03 are archived ([record](findings/2026-10-03-simultaneous-cap/README.md))
- [x] **The menu Tap Cover loses a right-thumb lift** (found 2026-10-03; present since 90.10; fixed in 90.23, 2026-10-04: the cover binds both stick touches itself, the author's choice of fix A; [record](findings/2026-10-04-tap-cover-stick-touches/README.md)). `Menu Buttons: Tap Cover` directly over a pad layer that keeps the right stick in mouse mode leaves the right-stick touch unanswered, so `RST: Entry Point`, `RST: Tap Cover` or `RST: Temporary Gyro` stays on: 12 pairs on 90.22, none on 90.23. The build audit failed on them, with no exception (author, 2026-10-04) ([the fixes that were weighed](findings/2026-10-03-simultaneous-cap/suggested-fixes.md))
  - Not settled, and no longer needed for this: whether a person can hold that stack at all (four thumb controls for two thumbs)
  - On the Deck: the gesture of scenario 90.23 C1 would also confirm A2 on a stick; it was verified on a pad
- [ ] **Touchpad exception to the hidden-exit rule: address it** (author, 2026-10-02). For now every pair where either layer is a touchpad layer (`Tab`, `Escape`, `Backspace`, `Enter`, `RTP: Entry Point`, `RTP: Circular Scroll`, `RTP: Double Tap`) or the covered exit is a trackpad input is set aside, not a finding. Under the keeper rule (a pair counts only if it covers an exit on what keeps the lower layer alive; a later cleanup doesn't count), that is 68 pairs in 90.13 (99 in 90.16: 31 more windows over the six pad click layers, whose touch Release is new there): 40 windows over pad layers and 28 `RTP: Double Tap` over button layers. 26 more (pad layers over the menu hold) are information: no stuck layer, but they block the right-stick click transition gesture ([list](findings/2026-10-02-hidden-exit/README.md#touchpad-exception))
  - Worst first: the 12 pairs where the lower layer has no cleanup function. `RTP: Double Tap` over `Menu Left: Escape`, `Menu Right: Tab`, the four Double Tap Covers, `L1&R1: Tap Cover` and `Menu Buttons: Tap Cover`; the L1, R1, Menu Left and Menu Right windows over `RTP: Tap Cover`. Example: double-tap and hold Select, tap the right pad, let go of Select inside the window: `Menu Left: Escape` stays on
  - Windows can't carry the exit without breaking their isolation, so the choice is a cleanup function on the lower layer or stopping the window from landing
  - Then the 25 mode blocks: the left-pad and RTP layers keep the right stick in mouse mode, which blocks the menu Entry Points' right-stick click Release and the right stick guard's edge Release
  - [ ] Confirm the five choices made while building, first the reset on the edge instead of a 4th entry on up and down ([list](findings/2026-10-02-steering-fallback-hold/README.md#choices-made-while-building))
- [x] Validate the fallback exit, held outputs and recovery ([F1 to F11](tests/test_scenarios_90_11.py)) — **closed 2026-10-03 without a Deck run**
  - Where the checks went: ten are scenario tests, and F4 is A16's procedure. They rest on A8, A9, A10 and A16
  - W or S pulses from the start and exits at 1.5 seconds; rolling to A or D, a release or a driver press cancels; the next hold starts fresh
  - Native timers, feedback, changed-held-output suppression and foreign Always On isolation remain acceptance gates
- [Implementation plan](plans/2026-09-29-steering-implementation-plan.md) · [Behavior matrix](plans/2026-09-29-steering-entry-brainstorm.md) · [Visual overview](plans/steering-overview.html)

## Menu stateful layer

- [x] Add menu stateful layer: built in 90.25 as `Menu Keys` ([record](findings/2026-10-04-pad-bumps-and-menu-keys/README.md) · [plan](plans/2026-10-04-pad-bumps-and-menu-layer.md#3-the-menu-stateful-layer-menu-keys) · scenarios [M1 to K7](tests/test_scenarios_90_25.py)). Not run on the Deck
  - It doesn't go through the [stateful transition structure](resources/Stateful%20Layer%20Transitions.md#exceptions) (author, 2026-10-01)
  - Enter: hold Select and Start for 150 ms, from Base or `Gyro`; `Gyro` goes off, with the beep and the strong pulse
  - Exit: both sticks out; a stick out plus a face button or a D-pad direction (the press then counts as Base's); a menu button held plus a stick click
  - Inputs: the D-pad is the arrow keys; A, B, X, Y are Enter, Escape, Backspace, Tab. The modifiers, Start, Select and the stick touches do nothing; everything else is Base's
  - With one menu button held, a tap of the other types Enter or Backspace and a double tap and hold holds it

## Cursor gyro

- [ ] Deck check: does `L1: Temp Cursor Gyro` / `R1: Temp Cursor Gyro` pick up Base's inverted left-stick edge?
  - Their left-stick group doesn't state `edge_binding_invert`, their edge removes the layer, and Base's left-stick edge is inverted. The inverted-edge audit check only counts a layer whose own group says inverted (author, 2026-10-01; [plan](plans/2026-10-01-stateful-transitions-implementation.md#step-6-steerings-left-stick)), so these two pass it either way
  - Assumption A38 since 2026-10-03. The two cursor scenarios that push both sticks (TC8, TC9) rest on it
  - If they do pick it up, they break the rule in [Definition of Done §3](resources/Layer%20Definition%20of%20Done.md#3-activators) and need an explicit setting
- [x] Cursor gyro (stateful): built in 90.21 as `Cursor Gyro` ([record](findings/2026-10-03-cursor-gyro/README.md) · [plan](plans/2026-10-03-cursor-gyro-and-gamepad.md) · scenarios [C1 to C9](tests/test_scenarios_90_21.py)). Not run on the Deck
  - In: Select plus the right-stick click, through `Transition Set 1`. The entry also adds `Gyro` underneath (author, 2026-10-03)
  - Out: any menu button plus any stick click (ends in `Gyro`), the Modifier 2 quick tap (ends in Base), and both sticks pushed out (ends in `Gyro`)
  - The both-sticks exit is only in `Cursor Gyro`; nothing on top carries it (author, 2026-10-03). Wider versions were discussed and dropped: a stick plus a button, and carrying the exit in the windows or the modifiers
  - It reuses Steering's Entry Points, renamed `Stateful | Menu Left: Entry Point` and `Stateful | Menu Right: Entry Point`
  - [ ] Confirm the R139 exception written while building: the `Stateful` Entry Points' right-pad touch differs between `Cursor Gyro` (Base's `RTP: Entry Point`) and `Steering` (cleared)
- [x] Temp cursor gyro
  - 90.4: high haptic pulse on the initial 300 ms hold entry only, in all regular/Gyro owners. Touch-release entry stays silent and ongoing gyro vibration remains off
  - Implemented in both JSON layouts: delayed Mod 0/1 holds apply owner-specific cursor overlays in regular/Gyro variants (L1/R1 default, L2/R2 alternative). See the [implementation and inheritance review](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md), [current design](plans/2026-09-29-cursor-self-removal.md), and the [scenario tests](tests/test_scenarios_cursor.py)
  - Apply Gated Gyro's response/haptic properties after 300 ms: precision 750, haptic intensity 0, haptic bump 1, movement threshold 5. Cursor self-removal exposes normal 300/0/5/0; normal covers inherit gyro. Natural sensitivity remains inherited at 300, and existing activation gates are preserved
  - Base gyro follows the July reference (rotation 3853, precision 300, conversion style 4, speed deadzone 0). Gyro/LST/RST sources retain activation-only overrides; only cursor overlays supply the temporary response. See [exact settings and inheritance policy](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#reference-tuning-and-gyro-inheritance-follow-up) and the [tuning notes](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (RG1 to RG3)
  - Either stick-touch release completes that apply early, before LST/RST cleanup can reset its delay; see [the documented pattern](resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release)
  - Regular face/D-pad/click inputs, Start/Select, the opposite modifier, and both sticks deflected about 25% apply the normal cover until the next modifier hold. Whether trackpad-held face/D-pad mode shifts bypass that behavior remains unverified; see the check below. An override before 300 ms prevents cursor entry; normal covers replace touch inputs with guarded recovery and LST/RST removals, never cursor additions
  - Three entries per edge: interruptible owner guard, uninterruptible owner-plus-opposing-stick override, and repeating recovery. LS radius 4915 / RS 7209 account for different hysteresis to target ~25% engagement; earlier cleanup when the owner is absent is accepted. Physical/selector thresholds and chord priority remain Deck checks: the travel is a tuning note (TC2), and the chord priority is A27
  - Extended owner-family cleanup for cursor overlays while preserving outputs, opposite held owners, and Always On isolation. A follow-up adds the missing 350 ms reset to each 300 ms cursor-entry parent; both overlay types replace that input to stop the apply/reset pair
- [x] Replace cursor property restoration with repeating cursor self-removal
  - [Implementation plan](plans/2026-09-29-cursor-self-removal.md): split 48 ordinary modifier inputs per layout into output and repeating cover-add chords, both uninterruptible, plus existing interruptible repeating cleanup; keep three entries per input
  - Cursor cancellation removes only itself; normal Tap Covers inherit gyro and retain cleanup-only touch releases. Cursor layers inherit LS/RS touches. Preserve the owner's 300 ms apply / 350 ms reset, repeating opposite-modifier transitions, and separate repeating dual-stick paths
  - Fixed the two missing alternative Mod 2 repeats from held-input F1. RTP Double Tap now explicitly blocks face/D-pad/stick-click inputs above a modifier/cursor; existing timer boundaries stay intact. See the [per-window inheritance review](findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)
  - Static tests and reference checks pass. The press sequences are [scenario tests](tests/test_scenarios_cursor.py) since 2026-10-03, resting on A9, A11, A32, A35 and A38. Not run on the Deck: both same-selector chords (A27), held-output handoff (A10, A11), interrupted timers (A13) and RTP's brief output blocking
- [ ] Verify whether trackpad-held face/D-pad mode shifts activate under modifiers and bypass Temp Cursor Gyro overrides (assumption A34)
  - Both layouts mark target groups 1039/1043 as `inactive modeshift`. Enabled Base trackpad-touch commands reference them, but those references alone do not establish whether Steam activates them under the modifier stack. The earlier review overstated this as a confirmed behavior gap
  - First reproduce the behavior on the Deck, before and after the 300 ms cursor apply. Only consider a fix if these groups actually take effect and bypass the normal Tap Cover; otherwise close this concern without changing bindings
  - If confirmed, consider modifier-specific mode-shift bindings that preserve existing key outputs and apply the owning normal cover. Trace inheritance through regular/Gyro owners, overlays, and Double Tap windows, including held inputs across transitions; preserve the three-command limit and Always On isolation
  - See the [corrected review note](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#stick-edges-and-inheritance) and A34's procedure

## Ramp up / triggers

- [x] Copy reference Base and ramp-up right-stick settings into both layouts
  - Base and Gyro Off Ramp Up already match. Turning Ramp Up 0 now uses sensitivity/vertical scale 150/80; Turning Ramp Up 1 uses 200/67. Bindings, modifier sensitivity 75, and local cleanup thresholds are preserved; the feel is a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (RG1, RG3)

- [x] Remove dedicated trigger layers and the old layer-based chorded ramp-up arrangement
  - Confirmed in both layouts: dedicated trigger layers are gone. Base still intentionally uses grouped Any chords to select or suppress ramp-up; this does not mean removing every ramp-up chord
- [x] Move ramp up gyro on / off entry selection to Base
  - Base RS edge adds Gyro Off Ramp Up normally, or Turning Ramp Up 0 directly while a firing control is held. Modifier-held input suppresses entry. Firing controls are L2/R2 in default and L1/R1 in alternative
- [x] Have firing controls remove Gyro Off Ramp Up during ramp-up
  - Gyro Off Ramp Up owns repeating, uninterruptible removal on default trigger pulls / alternative bumpers. Turning Ramp Up 0/1 leave those firing inputs unoverridden, inheriting the removal while Gyro Off Ramp Up remains below them
  - Verified from both JSON layouts on 2026-09-28; this is configuration verification, not a fresh Deck runtime test
- [x] Match default trigger configuration to the July reference (clarified scope of the hip-fire TODO; alternative excluded)
  - Both Base trigger groups now match the reference's bindings and settings, retaining their own group IDs. Removed only the explicit `adaptive_threshold: "0"` settings; no Soft Press/hip-fire activator was added, since the reference triggers do not use one
  - Reference: [MOST_RECENT_LAYOUT.post-fix.json](findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json). The checks are static tests (`test_static_checks.test_the_defaults_base_triggers_match_the_july_reference`) and one scenario (DT2 in [test_scenarios_triggers_and_recovery.py](tests/test_scenarios_triggers_and_recovery.py)); a fresh load is A33

## Trackpads

- [x] Decide a pad click once, through a Click Entry Point (90.14, author 2026-10-02 and 2026-10-03): the centre and the D-pad buttons were live in one layer, and a click near their boundary could send both. A click now adds `LTP: Click Entry Point` or `RTP: Click Entry Point`, whose two repeating Soft Presses on the pad's edge add `LTP: Middle Click` / `RTP: Middle Click` (centre, uninterruptible) or the D-pad layer (outer, interruptible). The five `hold_layer` commands are gone ([record](findings/2026-10-03-pad-middle-click/README.md); 75 layers)
  - The ranges are the sizes of 90.13: the outer one is the D-pad deadzone (23000), the centre one the default outer ring radius, taken as 24996 (A41)
  - The Click Entry Point has no haptics; the click's pulse on Base and the outputs' pulses are unchanged
  - [ ] Confirm the choices made while building ([list](findings/2026-10-03-pad-middle-click/README.md#choices-made-while-building)): the layer names, the 50 ms repeat, the eleven inherited inputs accepted under R139, and the Window audit's time limit
  - [ ] On the Deck, in this order: A10 for a pad click, A40, A41, then a very short click ([P7](tests/test_scenarios_90_14.py))
- [x] More exits and quieter haptics after the first Deck run (90.16, author 2026-10-03): on 90.14 and 90.15 pad click layers got stuck and a click gave three or four bumps. Every pad click layer now also ends on the click's Release and when the thumb lifts; Base adds the Click Entry Point with a silent repeat as well; both Soft Presses are uninterruptible and the outer one has a 5 ms delay; the Click Entry Point's pad states its haptic override as off ([record](findings/2026-10-03-pad-click-exits/README.md))
  - [x] Haptics: right on the Deck in 90.16 (author, 2026-10-03)
- [x] Pad click layers moved by Soft Presses only (90.17, author 2026-10-03, after playing 90.16): the click's Release is gone from all six pad click layers, because it fires at the full-click threshold and everything else here is a Soft Press; the outer add repeats again, with its 5 ms delay; the left pad's centre is Caps Lock ([record](findings/2026-10-03-pad-click-soft-press-only/README.md))
  - [ ] On the Deck: are layers still stuck? The author reports there are still issues without `hold_layer`; which ones isn't recorded yet. If they stay, the pad clicks go back to `hold_layer` (R101 would need its exception again). How 90.13 did it is in the [record](findings/2026-10-03-pad-click-soft-press-only/README.md#how-9013-did-it-with-hold_layer)
- [x] The Click Entry Point hands over (90.18, author 2026-10-03): each of its two Soft Presses removes it and then adds the chosen layer, and its own Soft Press removal on the click is gone, so it binds no click. The chosen layers no longer name it ([record](findings/2026-10-03-pad-click-handoff/README.md))
  - [ ] On the Deck: a click shorter than the hand-over (5 ms at the rim, 50 ms at the centre) leaves the Click Entry Point on until the hand-over fires or the thumb lifts. With no thumb on the pad, it only ends if an inverted Soft Press counts as true there (A40)
- [x] The final pad click layers hold themselves (90.19, author 2026-10-03, after playing 90.18: it works, but the haptics repeat while a click is held): `LTP: Arrow Keys`, `RTP: Mouse Buttons` and the two Middle Click layers have the 90.13 self-hold on the click's Soft Press, with the inverted repeating removal as the backup; the Click Entry Point adds the layer first and then removes itself. R101 has its exception back, as a decision ([record](findings/2026-10-03-pad-click-holds/README.md))
  - [x] On the Deck: 90.19 works and looks good (author, 2026-10-03). Nothing more was said about the repeating haptics of 90.18
  - [ ] A42: does the self-hold take the layer off? On the simulator it never fires in an ordinary click, because the layer lands on a pad that is already pressed (A5); the backup removal does the work
- [x] One add on Base's pad clicks (90.20, author 2026-10-03): each pad click had two Soft Presses adding the Click Entry Point, the second one silent and repeating every 50 ms since 90.16. The repeating one is gone; the first, with the bump and no repeat, is kept ([record](findings/2026-10-03-base-pad-click-one-add/README.md))
  - [ ] The author asked to keep "the one repeating at 100". That one has Hold to Repeat off; 100 is what Steam shows for an unset rate. Confirm that one add per press, with no repeat, is what is wanted
  - [x] Where the two ranges overlap, the middle click wins (author, 2026-10-04): a repeating action always triggers, so the centre Soft Press fires as the Click Entry Point lands, before the outer one's 5 ms delay (A6). Until then the simulator made the centre one wait for its 50 ms repeat, and sent the D-pad button there
- [x] A bump on touch, and the middle click as a mouse (90.25, author 2026-10-03 and 2026-10-04): a pad's touch adds a hand-over layer that reads the thumb once, bumps low inside the centre, and adds the pad's Entry Point. The click's add moved from Base to the Entry Points; `Steering` binds its own. `RTP: Middle Click`'s pad is a mouse ([record](findings/2026-10-04-pad-bumps-and-menu-keys/README.md))
  - The hand-over's two binds are the Click Entry Point's own: the inner one repeats and bumps, the outer one has the 5 ms delay (author, 2026-10-04). The click's add in the Entry Points repeats. So the bump and the click agree at every spot
  - [x] The bump came out in 90.27 (author, 2026-10-04: "I don't like the new trackpad changes"). The middle click as a mouse stays. [How the bump was built](findings/2026-10-04-pad-touch-bump/README.md), in case it comes back

## Sticks

- [x] Add left-stick edge cleanup only where needed, matching appropriate right-stick recovery
  - Implemented in both layouts: all eight modifier variants, both Menu Entry Points, both scroll layers, and both Transition Sets; see [scope, guards, and validation](findings/2026-09-28-left-stick-recovery/CHANGES.md). RTP Entry Point remains excluded; Fn layers already cover both edges
  - LS recovery matches each RS owner/family scope, with Hold to Repeat and default Interruptable. With cursor overlays included, single modifiers remove four targets and Mod 2 removes its eleven-target branch; menu entries and scroll layers remove their own pairs. Persistent Gyro remains intact
  - Author-approved Transition Set depth: LS/RS touch and edge all remove the current Transition Set first, then both Menu Entry/Fn families, only when neither menu button is held. Invalid menu-overlay recovery remains the separate ownership review
  - Added explicit LS-edge empty blocks in all seven Double Tap windows to prevent inherited layer mutations while Always On is active; existing timers and self-first/add-last boundaries remain intact
  - Originally used Fn's LS outer region (radius 21000, inversion off). The cursor change moves the four single-modifier pairs to LS radius 4915 / RS 7209; the other ten selected LS layers retain 21000. WASD directions are unchanged; the inherited WASD modifier remains displaced while these layers own the edge. See [the accepted tradeoff](resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions)
- [x] Add WASD modifier scaffold (user-defined)
  - Both layouts use the July reference's Base left-stick Soft Press setup, with an explicit empty binding in place of `KEYPAD_ASTERISK`; the user chooses the modifier key
  - Copied the reference's thresholds, style, inner-ring settings, and noninterruptible WASD presses. The empty scaffold sends no modifier; WASD-only, modifier-only, and combined behavior after assigning a key are a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (WM2)
  - Existing LS-edge recovery and Double Tap blocks still override this slot. See [configuration and inheritance](resources/Steam%20Input%20JSON%20Structure.md#user-defined-wasd-modifier-scaffold)
- [x] Add haptics to Fn stick-direction key selection
  - Both Menu Fn layers in both layouts: `haptic_intensity: "2"` on their eight directional keybinds (four LS + four RS), totaling 16 entries per layout
  - Separate mode-shift bindings, cleanup, empty guards, touch/click actions, and timer ordering are unchanged. Upper layers can inherit the Fn directional feedback; the feel is a [tuning note](resources/Steam%20Behaviour%20Assumptions.md#tuning-notes) (MB7)

## Global stateful behavior

- [ ] L1 + R1 clears all stateful layers
  - Author rule, 2026-10-01: the Modifier 2 clear (both bumpers in default, both triggers in alternative) always clears everything to Base, including Gyro. It is the fallback from any state and the one exit that never uses a transition ([structure](resources/Stateful%20Layer%20Transitions.md#exceptions)). Every new stateful layer must be removed by it ([definition of done §11](resources/Layer%20Definition%20of%20Done.md#11-stateful-layers))
  - 90.41 audit: Steering's uncovered second-driver release clears every layer, but releasing the first driver first retains Steering. Gyro Modifier 2 removes its 15-target list and can leave missed-release helpers. The [broader fix](plans/2026-10-09-steering-fallback-recovery.md) is deferred by the author on 2026-10-09; the current up/down Steering exit does not change these Mod 2 paths
  - Settled with Gamepad in 90.22 (author, 2026-10-03): the Modifier 2 quick tap does not leave `Gamepad`, whose bumpers and triggers are gamepad buttons. It is a recorded exception to R159
  - `Cursor Gyro` (90.21) follows the rule: the two `Gyro | … Modifier 2` releases remove it

## Bugs

- [x] Fix menu-entry start-delay interruption
  - Both Menu Entry → Fn paths apply after 300 ms and have a repeating 350 ms reset with Interruptable Off. Implemented in both layouts; The sequences are [scenario tests](tests/test_scenarios_menu_and_modifiers.py); that the reset restarts an interrupted delay is A12 (MB3)
- [x] Fix combined tap covers not properly re-adding after interrupt
  - All four Mod 2 variants per layout (both press orders, regular and Gyro) apply the combined Tap Cover after 200 ms and reset it every 250 ms with Interruptable Off. The sequences are [scenario tests](tests/test_scenarios_triggers_and_recovery.py); that the reset restarts an interrupted stage change is A12 (TR9)
- [x] Add delayed-apply reset to all four Temp Cursor Gyro entry parents per layout
  - Corrects the omission from the initial cursor implementation: the owning primary input removes only its Temp Cursor Gyro overlay every 350 ms with Hold to Repeat On and Interruptable Off, alongside the existing 300 ms apply and release exit
  - Both the cursor overlay and normal Tap Cover replace the complete primary input, stopping the reset after cursor entry or override. The reset never removes the normal cover or clears the owner stack. All seven Double Tap windows explicitly replace the primary controls; see [scope and isolation](findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up) and the [scenario tests](tests/test_scenarios_cursor.py)
- [x] Split menu entry layer into separate Menu Left / Menu Right layers
  - Both layouts have distinct Menu Left: Entry Point and Menu Right: Entry Point layers and their own Fn paths
- [x] Review extending the delayed-apply reset to additional tap-cover paths: since 90.25 every delayed add has its reset, the three Entry Points' Tap Cover included
  - Decided 2026-10-04 (author): the reset goes on all three Entry Points, the pad's included ([plan, part 5](plans/2026-10-04-pad-bumps-and-menu-layer.md#5-the-tap-cover-reset-on-the-three-entry-points)). The downsides and the Deck checks are under [Investigations](#investigations)
  - At 90.9, 21 of 24 delayed-add paths per layout have a reset (static count, 2026-10-01). The three without are LST Entry → Tap Cover, RST Entry → Tap Cover, and RTP Entry → Tap Cover, which is the deliberate exclusion below. The completed fixes above do not imply every delayed apply needs a reset
  - [Binding inventory](findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md) and [proposed follow-up work](findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#proposed-todo-split-and-validation); missing resets are not proof of runtime failures
  - Remaining proposed additions: LST/RST Entry → Tap Cover per layout. The four single-modifier paths now target Temp Cursor Gyro and have their resets. Keep resets in the parent owning the pending apply; preserve overlays and the three-command limit
  - Preserve the author-confirmed RTP touch exclusion for trackball momentum. The four scroll/menu-key Double Tap Cover paths got their resets in 90.6 as a last 4th entry ([record](findings/2026-09-30-second-press-cover-reset/README.md))
  - Keep the 5 ms Gyro Off → Turning Ramp Up 0 delay. It lets the apply fire on the already-held stick under the [held-input rule](resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes), and `tests/test_neptune_held_inputs.py` protects it
- [ ] Run the held-input real-layout checks and act on the results; see the [follow-up plan](plans/2026-09-29-held-input-rule-followups.md)
  - Done: F1 (the alternative R2 → Mod 2 repeats) and the [held-input regression tests](tests/test_neptune_held_inputs.py), including Base's covering repeats
  - Exported: [rule-test.vdf](findings/2026-09-29-held-input-layer-transitions/rule-test.vdf) and both Neptune VDFs using `convert_vdf.mjs`; static export checks pass
  - Pending on the Deck: A10 and A11, the key and mouse output scope (F3.1/F3.2). The staggered Gyro toggle (F3.3) is a scenario test since 2026-10-03, run both ways under A9 (HI2 in [test_scenarios_triggers_and_recovery.py](tests/test_scenarios_triggers_and_recovery.py))
  - Not scheduled: rule 3 (a removal firing the exposed layer command, A9) stays unverified. The layouts back it with repeats; run the optional T4 in `rule-test.vdf` before ever removing a Base repeat
- [x] Confirm menu helper/cover overrides are intentional within the overlay design
  - Keep Backspace / Enter, Escape / Tab, and the two Menu Double Tap Covers local to their button/action; the underlying stack owns recovery. Release-only exits remain valid; review invalid residual helpers in the owner's recovery instead of automatically adding independent edge cleanup to each overlay
  - Author confirmed: Start/Select menu interactions are not used during gameplay. Preserve disabled gyro in all six layers and the Escape / Tab RS-edge blocks; WASD modifiers and ramp-up are not required in menu context
  - Superseded 2026-10-01: the Enter / Backspace layers were removed in 90.9, so the still-held second menu button now falls through to Base
  - Background: [button overlays and inherited cleanup](resources/Steam%20Input%20JSON%20Structure.md#button-overlays-and-inherited-cleanup), [vocabulary](resources/Layout%20Vocabulary.md), and both audits

## Layer cleanup

- [x] **Build the required cleanups (R169 to R171).** Built 2026-10-04 as **90.24** ([record](findings/2026-10-04-required-cleanups/README.md)). Every layer has a cleanup function on both stick touches, the stick edges and every button it retypes or blocks: 174 inputs in the default layout and 196 in the alternative. The rules were enforced first, with 90.23 failing the Cleanup audit on purpose
  - The author's five decisions (2026-10-04): the full-pull blocks that cover nothing stay and get a cleanup; `RTP: Tap Cover` gets its right-stick group, and the five exits it covers are accepted; in the Steering W and S layers the bind that adds the Modifier 2 layer moved into the guard chord; the two Steering stick covers' left edge is guarded by either driver; the stick guards keep inheriting L1 and R1
  - Called out by the author: with the right pad touched first and a menu button pressed before `RTP: Tap Cover` lands, the right-stick click starts no transition while the thumb stays on the pad (scenario 90.24 K6)
  - Four behaviours changed, each with a scenario: a stuck transition ends on a stick or a bumper; `Steering | LS: Entry Guard` only lasts while the left stick is out; the click under `RTP: Tap Cover`; a stale menu cover under a held right pad clears one step later than on 90.23
- [ ] On the Deck, 90.24: enter Steering with the left stick centred and check the first push (the Entry Guard removes itself about 100 ms after it lands, which rests on A6); rock between the Steering drivers (the bind that adds the Modifier 2 layer is a chord now, A17 and A36)
- [x] Complete the static [cleanup audit](findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) and [blocking audit](findings/2026-09-28-neptune-blocking-audit/AUDIT.md) for both layouts, including all layers, entry/exit references, dormant groups, and Always On ordering
- [x] Document per-layer cleanup and blocking, with [concrete scope examples](resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) and guidance in the editing skills
- [x] Enable Hold to Repeat on every guarded recovery removal in both layouts; see the [separate change record](findings/2026-09-28-repeating-recovery/CHANGES.md). Static validation passed; a missed release and the recovery after it are scenario tests (MR1 in [test_scenarios_triggers_and_recovery.py](tests/test_scenarios_triggers_and_recovery.py), and the missed-release scenarios of each release)
- [x] Build the **Cleanup audit** and add it to the build audit as the fourth audit (90.12)
  - **Built 2026-10-02, tests first:** `audit_cleanups.py` on `steam_layout/cleanups.py`, six checks, stacks from the backward chains ([plan](plans/2026-10-02-cleanup-audit.md)). Not in the build audit yet
  - **First run:** 190 findings per layout, the same in both variants ([fix list](findings/2026-10-02-cleanup-audit/README.md)). Open for the author: the cursor group (recommended: drop), Fn and the stick guards, the other Modifier 2 order, and four new Steering findings
  - **Done in 90.12:** the `cleanup_lists` fix-pipeline step resolves every finding; both layouts are clean and the audit is the fourth gate of `audit_build.py`. C1 to C8 are scenario tests since 2026-10-03 ([test_scenarios_90_12.py](tests/test_scenarios_90_12.py))
  - The gap (2026-10-01): the build audit validates blocks and inheritance, but nothing checks that a cleanup function or an owner release removes the right layers. A list can miss a layer, remove a survivor, or a new layer can be removed by nothing. Today only the Flow audit's cover check and hand-written tests such as `test_neptune_recovery.py` touch this
  - Read-only checker first (`audit_cleanups.py`, steps 1 to 3 of the [cleanup generator plan](plans/2026-09-30-cleanup-generator.md)); no automatic rewriting of lists
  - **The raw lists exist (2026-10-01):** `python3 -m tools.audit_layer <layout> --layer TITLE` prints, for each binding of a layer that removes layers, what it removes that is present, what is present and left, what it removes that is never present, and which layers above intercept it. It is a report, not a check; it passes and fails nothing ([record](findings/2026-10-01-backward-chain-stacks/README.md#the-per-layer-report))
  - Base the audit on those lists. They use the backward chains (`steam_layout/chains.py`) in the view that sees overlaps between families
  - Was blocked on the author's review of the exits lists; answered on 2026-10-02 by the cleanup rules. The tool can see what an exit leaves behind, but not whether that is wrong. "Present, not removed" holds both kinds:
    - left on purpose: `Gyro`, a ramp layer or a stick-touch helper under `Menu Right: Fn Layer`. They belong to something else
    - left by mistake, probably: the Fn layer's 19 recovery bindings leave `Steering | Menu Right: Entry Point` and its Tap Cover, which its release does remove
    - and "removed, never present" may be clutter or a safety net: `L1: Modifier 0`'s release removes `Gyro | L1: Modifier 0`, which is never on the stack with it
  - The review is the same decision as the four open questions in [Cleanup Functions](resources/Cleanup%20Functions.md#questions-for-the-author) (who belongs to a family, what a cleanup must leave alone, which inputs host cleanup functions, who cleans up a layer two families add). Looking at the lists for a few layers is a concrete way to answer them
  - **A rule set to review (2026-10-02):** a cleanup removes the layers below and above it that the same button keeps alive, and nothing another button, a thumb, a timer or a mode keeps alive. Measured on every snapshot; five decisions are open for the author ([findings](findings/2026-10-02-cleanup-boundaries/README.md#decisions-for-the-author))
  - Without those answers a failing check would flag hundreds of correct things or miss the real ones, as the misread blocking rule did ([correction](findings/2026-10-01-backward-chain-stacks/README.md#the-flow-audit-on-chain-stacks))
  - Best done before or with the [transition build](#stateful-layer-transitions), which rewrites many removal lists
- [x] Add the guarded cleanup to both stick touches of the four Modifier 2 layers (author, 2026-10-02: "should have cleanup on its stick touches as well"). They bind the touch with a Release only, which hides the single modifier's touch cleanup ([finding](findings/2026-10-02-cleanup-boundaries/README.md#where-the-layouts-differ-from-the-rules))
- [x] Make the two-step cleanups one step (author's rule, 2026-10-02: every layer takes care of itself and below): the cursor layers' two edge cleanups take the modifier's list, and `RTP: Mouse Buttons`' two stick-touch cleanups also remove `RTP: Circular Scroll`. The cursor's 15 cancellations stay as they are ([record](findings/2026-10-02-cleanup-boundaries/README.md#answered-author-2026-10-02))
- [x] Guard the two stick-touch cleanups of both Steering Modifier 2 layers with either bumper, like their 12 button cleanups (author, 2026-10-02). Today only the bumper pressed first suppresses them
- [x] Shorten every cleanup list to the layers that can be on the stack with its host (author, 2026-10-02: no Gyro twin in a normal layer's list or the reverse, no whole-family lists; "I want to reduce unnecessary layer removals"). About 1,000 of 1,982 removals per layout. Ordinary releases and the Modifier 2 quick tap follow the same rule (up to 139 of 360 removals); deliberate clears and the stick-touch trio keep their lists. Check each against the chains first; `RTP: Mouse Buttons` under `RTP: Circular Scroll` is a known false "never", and the Fn layers' stick guards are a timing-race case to review ([rule 6](findings/2026-10-02-cleanup-boundaries/README.md#6-list-only-what-can-be-on-the-stack-with-you))
- [x] Take the two Steering Double Tap windows out of the six Steering cleanup lists (author, 2026-10-02: a cleanup doesn't list a window; it always clears itself)
- [ ] Review owning-layer recovery against the [overlay cleanup ownership rule](resources/Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership)
  - The Cleanup audit above would check this mechanically. The menu Enter / Backspace overlays named below were removed in 90.9
  - Each layer applying an overlay is responsible for removing it during stale-state recovery when that interaction is no longer valid; retain the overlay's local exit and inherited recovery
  - Trace shared owners and still-held buttons before extending target lists. Review the menu Entry/Fn helpers that currently rely on another related-button press after parent recovery; preserve valid held helpers and normal release behavior

## Carried over

- [x] Make Base gyro activation require LS/RS deflect, LS/RS touch, Select, and Start together, replacing the Start/Select gyro mode shifts
  - Verified in both layouts on 2026-09-29: active Base gyro group 576 uses mask `211109453778944` with `gyro_ratchet_button_requireany_or_all: "1"` (All six inputs)
  - The Start/Select gyro mode shifts are removed. Remaining mode-shift definitions cover trackpad-touch navigation and menu Fn stick punctuation and were preserved by that refactor. Trackpad mode-shift activation under modifiers remains the separate verification item above
  - Implementation: [gyro mode-shift removal plan](plans/2026-09-27-neptune-gyro-shifts-navkeys.md). The runtime checks are scenario tests (ML1 to ML4 in [test_scenarios_menu_and_modifiers.py](tests/test_scenarios_menu_and_modifiers.py)); other gyro layers retain their own activation rules
- [ ] Handle cursor gyro layer (may be covered by [Cursor gyro above](#cursor-gyro))
- [ ] Clear all unnecessary layers on action set swap
  - Likely obsolete: action sets are never switched ([runtime rules](resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)), and the transitions' clear covers the layer case. Kept open by the author (2026-10-01)
- [ ] Add temp gyro to both right and left stick touch
  - Looks done: `LST: Temporary Gyro` and `RST: Temporary Gyro` exist in both layouts, reached by the second stick touch. Kept open by the author (2026-10-01)
