# The 137 Deck checks, sorted

**Status, 2026-10-03:** read-only sorting, phase 11 of the
[rule registry plan](../../plans/2026-10-02-rule-registry.md). No check was
deleted or reworded. `manual-testing.md` changed in one way only: the 62
checks that had no ID got one.

## Why sort before building the simulator

The plan replaces Deck checks with tests a script can run. What a check
becomes decides what the press simulator has to model, so the sorting comes
first.

## Identity

A check is named by **section plus ID**, for example "90.12 C1". Eight IDs
are used in two sections (C1 to C4, D1, D2, D4, T1), so the ID alone isn't
enough. The 62 unlabelled checks, everything from "Menu buttons" down, were
numbered with a two-letter prefix per section: MB, ML, TC, RG, TR, DT, LR, WM,
MR, HI.

## What a check becomes

| Becomes | When | Count |
|---|---|---|
| **Scenario** test | It asks which layer gets an input, what is on the stack, or which keys are down | 90 |
| **Static** test | It asks what a binding or a setting is, with no presses. Most already exist as tests | 21 |
| **Assumption** entry | It really tests what Steam does. It joins an entry in [Steam Behaviour Assumptions](../../resources/Steam%20Behaviour%20Assumptions.md) as that entry's Deck procedure | 14 |
| **Tuning** note | It is about feel | 3 |
| **Obsolete** | A later release replaced the behaviour | 9 |

Many checks have a second part. A scenario can end in a feel question ("the
pulse strength"), or rest on an unverified assumption ("whether W comes
back"). The last column says where that part goes. Five scenario checks
repeat another one (N4, 90.10 D9, 90.6 C2, MB4, HI3); they are marked "same".

By section, as scenario, static, assumption, tuning, obsolete:

| Section | Checks | Sc | St | As | Tu | Ob |
|---|---|---|---|---|---|---|
| 90.13 | 4 | 4 | | | | |
| 90.12 | 8 | 8 | | | | |
| 90.11 | 11 | 10 | | 1 | | |
| 90.10 | 25 | 19 | | 5 | | 1 |
| 90.9 | 6 | 4 | 1 | | | 1 |
| 90.7 | 8 | 5 | | | | 3 |
| 90.6 | 13 | 3 | 5 | 2 | | 3 |
| Menu buttons | 10 | 8 | | 1 | 1 | |
| Modifier layers | 4 | 4 | | | | |
| Temp cursor gyro | 18 | 10 | 5 | 2 | 1 | |
| Reference gyro and right-stick tuning | 3 | | 3 | | | |
| Triggers and ramp-up | 12 | 9 | 2 | 1 | | |
| Default trigger reference match | 3 | 1 | 2 | | | |
| Left-stick recovery and Transition Sets | 1 | 1 | | | | |
| WASD modifier scaffold | 5 | 1 | 2 | 1 | 1 | |
| Missed releases and cleanup scope | 2 | 1 | 1 | | | |
| Held inputs across layer changes | 4 | 2 | | 1 | | 1 |
| **Total** | **137** | **90** | **21** | **14** | **3** | **9** |

## What the simulator has to model

Each scenario row lists what it needs, by these codes. The count is how many
of the 90 scenario checks need it.

| Code | What | Needed by |
|---|---|---|
| B | Buttons held and released; which activator answers: a chord (Any or All) or a Regular Press | 68 |
| St | A stick as inputs: its directions, its outer edge, its click and its touch. Rolling from one direction to another | 59 |
| T | Time: start delays, Hold to Repeat, Always On timeouts, a delay eaten by an override, a reset restarting a delay | 56 |
| K | A log of key and mouse output: what is down, what was typed | 42 |
| Miss | A missed release: the button is up but the layout never saw the Release | 13 |
| Tr | A trigger's soft pull and full pull as two inputs | 10 |
| Gyro | Whether the gyro source is disabled on the stack | 5 |
| Hap | Haptic pulses and beeps, as logged events | 4 |
| H | The held-input rules: what fires when a layer lands on, or leaves, a held input | 4 |
| Pad | A trackpad's touch, click and swipe directions as inputs | 3 |
| Desk | The desktop configuration: every entry past the third dropped | 1 |

The plan's phase 12 listed four steps: held buttons and chords, the output
log, the held-input rules, and time. The sorting adds sticks, missed
releases, triggers and pads as inputs, and three small ones (gyro disabled,
haptics, desktop).

**Not modelled, and what that moves:**

- **How far a stick or trigger is.** A stick is in or out, a trigger is not
  pulled, soft-pulled or fully pulled. Physical thresholds are tuning notes
  (TC8, WM2).
- **`hold_layer`.** The layout isn't meant to use it (R101). The one check that
  needs it, 90.6 D2/D3, is a static test.
- **Mode shifts.** The checks about them are static tests (90.6 D4/D5) or an
  assumption (TC18).
- **Gyro motion, sensitivity and feel.** Settings are static tests; feel is a
  tuning note.

## New assumptions the sorting found

- **A33:** Steam loads an exported VDF as written. Behind "both variants load
  without error" (90.6 D1) and every "load fresh" instruction.
- **A34:** a trackpad's `inactive modeshift` target takes effect when its mode
  shift fires (TC18).

## The table

Generated from [sorting.py](sorting.py), which fails if a check is missing or
listed twice (`python3 findings/2026-10-03-deck-check-sorting/sorting.py --check`).
It becomes the migration record in phase 14.

<!-- table:start -->
| Section | Check | It says | Becomes | Where it goes, or what the simulator needs |
|---|---|---|---|---|
| 90.13 | N1 | in Steering, push the right stick fully out and hold, with and without… | Scenario | St, Gyro: the right-stick edge adds no ramp layer in Steering; the gyro source isn't disabled |
| 90.13 | N2 | hold R1, hold a trigger (firing), push the right stick out, let go of… | Scenario | B, Tr, St, K: the driver's Release still reaches its layer; no W left down |
| 90.13 | N3 | in a Steering stick Double Tap window (flick the left stick while driv… | Scenario | St, T, Tr, K: a trigger pull inside a Steering window clicks |
| 90.13 | N4 | outside Steering, turn assist and gyro-off-while-turning work as befor… | Scenario | St, T, Gyro: outside Steering the ramp layers still come and go (same as TR3) |
| 90.12 | C1 | (Modifier 2, stick touch): hold L1 then R1, miss both releases, touch… | Scenario | B, Miss, St: a stick touch clears a stuck Modifier 2 |
| 90.12 | C2 | (Modifier 2 held, stick touch): hold L1 and R1 and rest a thumb on eac… | Scenario | B, St: with either bumper held, a stick touch clears nothing |
| 90.12 | C3 | (cursor, one step): hold L1 for 300 ms (cursor), miss the release, pus… | Scenario | B, T, Miss, St: one edge push clears a stuck cursor and its modifier |
| 90.12 | C4 | (Steering Modifier 2): in Steering hold R1 then L1, miss R1's release… | Scenario | B, Miss, St: Steering Modifier 2 with one bumper still held |
| 90.12 | C5 | (rocking): hold L1, add R1, wait 200 ms, let go of L1, press L1 again,… | Scenario | B, T: the rocking sequence; test_modifier_rocking.py already replays it with walk |
| 90.12 | C6 | (taps): tap L1 twice quickly: scroll down. Hold L1 and press A, let go… | Scenario | B, T, K: double tap scrolls, a used bumper doesn't, the quick tap toggles Gyro |
| 90.12 | C7 | (stuck, still clears): miss the release of L1 alone, of Start's Fn lay… | Scenario | B, Miss, St: a stuck modifier, Fn layer and Steering driver each clear |
| 90.12 | C8 | (menu): hold Start, push a stick (guard), release: Tab or the window a… | Scenario | B, St, T, K: the menu hold with a stick guard, and the Fn release |
| 90.11 | F1 | (the fix): hold the left stick up for about 1 s, roll to A or D withou… | Scenario | St, T, Hap: rolling to A or D removes the Fallback Hold, so no exit and no pulse |
| 90.11 | F2 | (exit): hold the left stick up: W, pulses from the start, and Steering… | Scenario | St, T, K, Hap: W, the pulse, and the exit with its beep at 1.5 s. The pulse strength is a tuning note |
| 90.11 | F3 | (early release): hold up for 1 s, recentre, hold up again: the exit co… | Scenario | St, T: the exit counts from the second push |
| 90.11 | F4 | (after A or D): hold A for 3 s, roll up and hold: the exit comes about… | Assumption | A16: does a delay's clock start when its layer is added |
| 90.11 | F5 | (diagonal): hold up-left: W and A together, pulses carry on, exit at 1… | Scenario | St, T, K: a diagonal holds two directions |
| 90.11 | F6 | (driver): hold up, press R1 before 1.5 s: the pulses stop, no exit, an… | Scenario | B, St, T: a driver press removes the hold. Whether W returns after the driver's release rests on A11 |
| 90.11 | F7 | (entry): enter Steering with the stick centred, push up and hold: W wi… | Scenario | St, T: the Entry Guard, entered with the stick centred or already up. The second rests on A8 |
| 90.11 | F8 | (menu while holding up): hold up, tap Start: one Tab, W carries on, an… | Scenario | B, St, T, K: a Start tap types Tab and adds nothing over the hold |
| 90.11 | F10 | (menu held, then push up): hold Start with the stick centred, push up… | Scenario | B, St, T, K: the menu Entry Point types W on stick up and adds no hold |
| 90.11 | F11 | (Entry Guard): enter Steering and leave the stick centred: Start and S… | Scenario | B, St, T, K: Start and Select type their keys in the Entry Guard |
| 90.11 | F9 | (desktop): apply the layout to the desktop configuration and repeat F1… | Scenario | Desk: F1 and F2 again on the layout with every entry past the third dropped. Rests on A21 |
| 90.10 | G1 | (gate 1, stick inheritance from the middle of the stack): hold the lef… | Assumption | A26: do stick inputs inherit through the middle of the stack |
| 90.10 | G2 | (gate 1, Fn): hold Start past 200 ms so Fn is up, click and release th… | Assumption | A26: the same shape, with the Fn layer over the Entry Point |
| 90.10 | G3 | (gate 2, edge Release in a layer added with the stick already out): ho… | Assumption | A8: a stick edge's Release in a layer added with the stick already out. Its last branch is A14 |
| 90.10 | G4 | (stick already out): hold the left stick north, then hold Start for 50… | Assumption | A15: a guard that lands inside the Fn delay cancels it |
| 90.10 | G5 | (tap with a stick out): hold the left stick north, tap Start: one Tab | Scenario | B, St, T, K: a Start tap with a stick out types one Tab |
| 90.10 | G6 | (eaten delay comes back): push both sticks out while holding Start, re… | Assumption | A14: a delay starts again when a removal exposes it |
| 90.10 | T1 | each gesture from Base and from Gyro: Start + LS click enters Steering… | Scenario | B, St, K, Hap: the four gestures from Base and from Gyro, with the beep and pulse |
| 90.10 | T2 | (clear): in Steering, each of the four gestures leaves it, with the be… | Scenario | B, St, Hap: the four gestures clear Steering and keep Gyro |
| 90.10 | T3 | (cancel): hold Start, click and hold the left stick, release Start fir… | Scenario | B, St: letting go of the menu button first cancels |
| 90.10 | T4 | (missed release): in each transition, release the menu button while th… | Scenario | B, St, Miss: a transition left by a missed release ends on the next menu tap |
| 90.10 | T5 | (guards): guard on and off for each stick, and both together; with a g… | Scenario | B, St, T, K: guards on and off; rests on A8 |
| 90.10 | T6 | (stale guard): with a stick out, release the menu button while the Ste… | Scenario | B, St, Miss: a stick touch clears a stale guard |
| 90.10 | T7 | (accepted): under the menu Tap Cover, bump the other menu button: the… | Scenario | B, St, T, K: the accepted gap under the menu Tap Cover |
| 90.10 | T8 | (K1 reworded): hold Start, press Select before Fn is up: exactly one B… | Scenario | B, T, K: one Backspace before Fn is up; rests on A10 |
| 90.10 | T9 | the camera stick is dead while a menu button is held, and comes back o… | Scenario | B, St, K: the right stick types nothing while a menu button is held |
| 90.10 | T10 | (mouse buttons through a window): tap L1, or flick the left stick whil… | Scenario | B, St, Tr, T, K: mouse buttons through a window. Whether a held click is interrupted rests on A11 |
| 90.10 | D1 | (menu): with no driver held, tap Start: one Tab and Steering stays; ho… | Scenario | B, T, K: menu buttons in Steering, with and without a driver |
| 90.10 | D2 | (hold exit): replaced by F1 to F5 in 90.11 | Obsolete | Replaced by 90.11 F1 to F5 |
| 90.10 | D3 | (modifier and roll): hold R1, hold the left stick up: the R1 modifier… | Scenario | B, St, T: the stick modifier holds through a roll to the side |
| 90.10 | D4 | (stick first): hold the left stick up, then press R1: the modifier map… | Scenario | B, St, T, K: stick first, then the driver; rests on A8 |
| 90.10 | D5 | (double taps): flick up and back: one scroll about 150 ms after centre… | Scenario | B, St, T, K: the stick double tap and its window |
| 90.10 | D6 | (W and S through the window): hold a driver, flick the stick once: W o… | Scenario | B, St, T, K: W and S through the window; rests on A10 and A11 |
| 90.10 | D7 | (other driver in the window): flick the stick, bump the other driver i… | Scenario | B, St, T, K: the other driver inside the window |
| 90.10 | D8 | (mapped buttons): in a modifier map, press a face button: its key, and… | Scenario | B, St, Miss, K: a mapped button uses up the tap; a stuck modifier map clears |
| 90.10 | D9 | (entry with the stick centred): enter Steering with the stick centred,… | Scenario | The same sequence as 90.11 F7, first half |
| 90.9 | K1 | (early path): hold Start and press Select within 300 ms, before Fn is… | Obsolete | Replaced by 90.10 T8 |
| 90.9 | K2 | with Fn up (hold Start past 300 ms), Select types Backspace on every p… | Scenario | B, T, K: Backspace on every press with Fn up, repeating |
| 90.9 | K3 | (accepted): hold Start, press and keep holding Select, lift Start firs… | Scenario | B, T, K: the accepted stray Escape when the first button is lifted first |
| 90.9 | K4 | other Fn keys behave the same way (hold Start, hold LB for F10, lift S… | Scenario | B, K: a held Fn key falls through to Base (R138) |
| 90.9 | K5 | every layer still does what it did: spot-check a modifier, Mod 2, both… | Static | Every layer command resolves to a layer after the ID shift: test_fixes already checks it. The fresh load is A33 |
| 90.9 | M5 | RTP double tap: tap the right pad, tap again north or south within 150… | Scenario | Pad, T: the right-pad double tap and Circular Scroll |
| 90.7 | S1 | drive, flick LS up to center, press A within 150 ms: F fires once, one… | Scenario | B, St, T, K: a face button inside the stick window |
| 90.7 | S2 | flick, then flick and hold: repeat scroll; releasing stops it; the nex… | Scenario | St, T, K: flick, then flick and hold repeats the scroll |
| 90.7 | S3 | hold LS up past 250 ms, lift the left thumb, put it back: LST layers c… | Scenario | B, St, T: lifting the thumb during a stick modifier |
| 90.7 | S4 | hold LS up past 250 ms, release the driver while the Steam menu is ope… | Scenario | B, St, Miss: the driver's recovery through the cover |
| 90.7 | S5 | protected menu entry (Start with a stick deflected), hold past 300 ms,… | Obsolete | The protected menu layers were replaced by the stick guards in 90.10 (T5) |
| 90.7 | S6 | while steering, tap and touch the right pad: the cursor moves and pad… | Scenario | Pad, St: no RTP touch mode starts while steering |
| 90.7 | S7 | while steering, turn assist (RS past the ramp threshold) works while j… | Obsolete | Turn assist is off in Steering since 90.13 (N1) |
| 90.7 | S8 | flick LS up to center, then push sideways within 150 ms: one scroll fi… | Obsolete | Replaced by 90.10 D5 |
| 90.6 | D1 | both variants load without error; every layer's sources look the same… | Static | The prune removes only dead groups: test_layout_hygiene. Loading without error is A33 |
| 90.6 | D2/D3 | right pad clicked, tap up/down gives one wheel tick; hold repeats from… | Static | RTP: Mouse Buttons' wheel bindings: test_layout_hygiene. The layer is added by hold_layer, which isn't simulated |
| 90.6 | D4/D5 | Base dpad/face and Menu Fn stick mode shifts unchanged; stick double-t… | Static | The prune kept every mode-shift target: test_layout_hygiene and the fix pipeline's fixed point |
| 90.6 | C1 | steering fallback, hold LS up: warning pulses from 1 s, exit with one… | Obsolete | Replaced by 90.11 F1 to F9. Its pulse timing is a tuning note on F2 |
| 90.6 | C2 | enter Steering with W held for more than 3 s: no warning or exit until… | Scenario | The same sequence as 90.11 F7, second half |
| 90.6 | C3 | short flick to center scrolls once about 150 ms after center; flick-fl… | Obsolete | Replaced by 90.10 D5: the window is an Always On layer now |
| 90.6 | C4/C5/S7 | holding down/up past 250 ms consumes the tap and keeps the modifier ma… | Scenario | B, St, T, K: the hold uses up the tap; no scroll at centre after a takeover |
| 90.6 | R1 | second-press cover. Double-tap Select and hold past 150 ms: Escape hol… | Scenario | B, T, K: double-tap and hold, then a clean release through the cover |
| 90.6 | R2 | interrupt that hold (release before 150 ms, then double-tap-hold again… | Assumption | A12: the reset restarts an interrupted delay. That each delayed add has its reset is R120 |
| 90.6 | R3 | apply either layout to the desktop configuration; those four inputs sh… | Assumption | A21: the desktop configuration drops the 4th entry. The reset being last is checked by the Budget audit |
| 90.6 | T1 | Transition Set 0 (Fn + RS click). While either menu button is held, to… | Obsolete | The transitions were rebuilt in 90.10 with no stick-touch recovery (T4). The merged chord in the editor is A30 |
| 90.6 | P1 | during any Double Tap window (within 150 ms of a tap), a left-pad swip… | Static | The pads' bindings in every window: test_double_tap_windows. The swipe feel is a tuning note |
| 90.6 | B1 | derived window blocks. Default only: push RS past the ramp threshold (… | Static | RTP Double Tap's back buttons and selection: test_double_tap_windows. The trigger part was replaced by 90.10 T10 |
| Menu buttons | MB1 | Tapping Select sends Escape, and tapping Start sends Tab | Scenario | B, T, K: a tap types Escape or Tab |
| Menu buttons | MB2 | Holding either for 300 ms brings up its Fn layer, and the F-keys work | Scenario | B, T, K: the Fn hold (200 ms since 90.10, not 300) and its silent release |
| Menu buttons | MB3 | Start-delay reset: after an interrupted hold, keep holding or hold aga… | Assumption | A12: the reset restarts an interrupted hold |
| Menu buttons | MB4 | Enter / Backspace: Select → Start sends Enter, and Start → Select send… | Scenario | B, T, K: Enter and Backspace, quickly and with Fn up (same keys as 90.10 T8 and 90.9 K2) |
| Menu buttons | MB5 | Double tap and hold repeats Escape / Tab, and releasing stops it | Scenario | B, T, K: double tap and hold repeats the key. How many keys a quick double tap sends is a tuning note |
| Menu buttons | MB6 | Menu button + stick click opens a Transition Set, and with the menu bu… | Scenario | B, St, K: the stick click enters a transition; stick directions type punctuation |
| Menu buttons | MB7 | In each Menu Fn layer, its eight directional keybinds (four LS + four… | Tuning | The Fn directions' haptic feel |
| Menu buttons | MB8 | Stick touch release: hold Start, touch a stick and lift off, then rele… | Scenario | B, St, T, K: a thumb lift completes the Fn hold (R123) |
| Menu buttons | MB9 | Steam button recovery: | Scenario | B, St, Miss: a stuck Fn layer clears on the next input |
| Menu buttons | MB10 | Stuck entry layer (for example, the Steam button within 300 ms of a me… | Scenario | B, Miss: a stuck Entry Point clears on the other menu button |
| Modifier layers | ML1 | Nav keys with Start / Select: LB gives Insert / Delete, RB gives Home… | Scenario | B, K: the nav keys in each modifier |
| Modifier layers | ML2 | The same nav keys in Gyro mode | Scenario | B, K: the same in Gyro |
| Modifier layers | ML3 | Holding Start or Select in any modifier layer, in Base or Gyro mode, d… | Scenario | B, Gyro: Start or Select in a modifier leaves the gyro source alone. Whether that is wanted is a question for the author |
| Modifier layers | ML4 | After a nav chord, releasing the modifier doesn't fire its tap / scrol… | Scenario | B, T, K: no tap or scroll after a nav chord |
| Temp cursor gyro | TC1 | Hold the primary modifier for 300 ms: its Temp Cursor Gyro overlay app… | Scenario | B, T: the cursor lands at 300 ms; its settings are checked by test_neptune_cursor |
| Temp cursor gyro | TC2 | The 300 ms hold entry gives one high-intensity haptic pulse. Keep hold… | Tuning | The entry pulse's feel; its setting is checked by test_neptune_cursor |
| Temp cursor gyro | TC3 | Before 300 ms, lift either thumb: cursor applies immediately, then onl… | Scenario | B, St, T: a thumb lift enters the cursor early (R123) |
| Temp cursor gyro | TC4 | Check every ordinary face/D-pad/click input, Start/Select, and opposit… | Scenario | B, T, K: every cancel input before, at and after 300 ms; rests on A9 and A11 |
| Temp cursor gyro | TC5 | Check the twelve ordinary inputs in all four regular/Gyro owners: outp… | Static | The two chords and the recovery on each input: test_neptune_cursor. Their order is A32 |
| Temp cursor gyro | TC6 | Trigger a normal-cover input and thumb release together near the 300 m… | Scenario | B, St, T: a cancel input and a thumb lift together; run in both orders (A32) |
| Temp cursor gyro | TC7 | Confirm each single-modifier edge has three entries: interruptible own… | Static | The three entries on each stick edge: test_neptune_cursor and test_neptune_recovery |
| Temp cursor gyro | TC8 | One stick alone preserves cursor; both sticks around 25% should overri… | Scenario | B, St: one stick keeps the cursor, both remove it. The physical thresholds are a tuning note |
| Temp cursor gyro | TC9 | Release/lose the modifier while sticks stay deflected: recovery clears… | Scenario | B, St, Miss: a lost modifier clears its family with the sticks out |
| Temp cursor gyro | TC10 | Test both Mod 2 orders and release orders, including alternative parti… | Scenario | B, Tr, T: both Modifier 2 orders and release orders |
| Temp cursor gyro | TC11 | Alternative R2 regular/Gyro → L2 now repeats its Mod 2 entry. With LT… | Scenario | Tr, H: the alternative's repeating Modifier 2 entry over a held trigger (A6) |
| Temp cursor gyro | TC12 | Fresh modifier holds become eligible for cursor again. A short primary | Scenario | B, T: a fresh hold is eligible again; the reset part is A12 |
| Temp cursor gyro | TC13 | Confirm each cursor-entry primary input has exactly three entries: rel… | Static | Exactly three entries on each cursor-entry input: test_neptune_cursor |
| Temp cursor gyro | TC14 | Keep holding for several 350 ms intervals after cursor entry, early | Scenario | B, T: no repeated removal after the cursor or a cover has landed (R122) |
| Temp cursor gyro | TC15 | Hold/move/touch inputs across all seven Double Tap windows and menu/Fn… | Static | Window isolation and ordering: the Window audit and test_neptune_recovery |
| Temp cursor gyro | TC16 | During a modifier hold, quickly touch/release RTP, before and after cu… | Static | RTP Double Tap's blocks: test_neptune_cursor |
| Temp cursor gyro | TC17 | Cancel cursor during RTP Entry's 150 ms wait: check the touch/trackbal… | Assumption | A13 and A28: a removal during RTP Entry's delay, and trackball momentum |
| Temp cursor gyro | TC18 | First verify whether touching either trackpad actually activates face/… | Assumption | A34: do the trackpad's inactive mode-shift targets take effect |
| Reference gyro and right-stick tuning | RG1 | Base gyro matches the July reference's feel and settings: natural sens… | Static | Base's gyro settings: test_neptune_gyro. The feel is a tuning note |
| Reference gyro and right-stick tuning | RG2 | In regular and Gyro modifier holds, cursor response is 750/0/1/5 and r… | Static | The cursor's and the covers' gyro settings: test_neptune_gyro and test_neptune_cursor. The feel is a tuning note |
| Reference gyro and right-stick tuning | RG3 | Base right stick retains its reference settings and feel. Ramp 0 chang… | Static | The right stick's and the ramp stages' settings: test_neptune_gyro. The feel is a tuning note |
| Triggers and ramp-up | TR1 | LT / RT fire left / right click, and Start / Select work while a trigg… | Scenario | B, Tr, K: the triggers click; a menu button works with a trigger held |
| Triggers and ramp-up | TR2 | In the Deck GUI, Base's right-stick outer edge shows three command ent… | Static | Three entries and Any chords on Base's right-stick edge: the Budget audit. What the editor shows is A30 |
| Triggers and ramp-up | TR3 | RS to the edge with nothing held: | Scenario | St, T, Gyro: the two ramp stages and the way back |
| Triggers and ramp-up | TR4 | RS to the edge while holding a trigger keeps the gyro on during ramp-u… | Scenario | St, Tr, T, Gyro: a held trigger keeps the gyro on |
| Triggers and ramp-up | TR5 | Pulling a trigger after the gyro turns off, in both stages, brings the… | Scenario | St, Tr, T, K: a pull brings the gyro back. The first click registering is A11 |
| Triggers and ramp-up | TR6 | Holding a modifier on the way to the edge lets no ramp-up or gyro-off… | Scenario | B, St, T: a held modifier lets no ramp layer in |
| Triggers and ramp-up | TR7 | Pressing a modifier during ramp-up ends ramp-up and enters the right m… | Scenario | B, St, T, H: a modifier pressed during ramp-up ends it |
| Triggers and ramp-up | TR8 | The edge / trigger / modifier checks above work the same in Gyro mode | Scenario | The same three in Gyro |
| Triggers and ramp-up | TR9 | Interrupting the 250 ms stage change, recentering and retrying still r… | Assumption | A12: the 300 ms reset restarts the interrupted stage change |
| Triggers and ramp-up | TR10 | Stuck right trackpad: | Scenario | B, Pad, St: a stuck right pad doesn't block the edge. Trackball momentum is A28 |
| Triggers and ramp-up | TR11 | Two-bumper tap cover: | Scenario | B, T: the two-bumper quick tap, and the cover after 200 ms |
| Triggers and ramp-up | TR12 | No new haptic pulse when RS hits the edge | Static | No haptic setting on the right-stick edge entries |
| Default trigger reference match | DT1 | Load the default layout fresh and confirm both Base triggers match the… | Static | Base's trigger settings and mouse outputs against the July reference |
| Default trigger reference match | DT2 | Check partial/full pulls, quick pulls, held firing, and release in Bas… | Scenario | Tr, St, T, K: pulls in Base, Gyro and both ramp stages |
| Default trigger reference match | DT3 | Check inherited trigger behavior through modifier/cover layers, menu F… | Static | The windows' trigger bindings: test_double_tap_windows and the Window audit |
| Left-stick recovery and Transition Sets | LR1 | Validate the new LS-edge recovery and Transition Set depth on the Deck… | Scenario | B, St, Miss: the left-edge cleanup functions. The Transition Set part was replaced in 90.10 |
| WASD modifier scaffold | WM1 | Base left stick shows one empty Soft Press command named WASD Modifier… | Static | Base's left-stick edge entry and its settings |
| WASD modifier scaffold | WM2 | With a test modifier assigned, check slow deflection, quick deflection… | Tuning | The modifier's regions with a key assigned |
| WASD modifier scaffold | WM3 | Verify inherited modifier behavior in Base, Gyro, ramp stages, stick-t… | Scenario | St: which stacks leave Base's left-stick edge exposed |
| WASD modifier scaffold | WM4 | Verify the modifier is displaced by the 16 LS-edge recovery layers (in… | Static | The layers that bind the left-stick edge: test_neptune_recovery |
| WASD modifier scaffold | WM5 | Enter and leave those overrides while the stick is already deflected,… | Assumption | A11: an output exposed or hidden under a stick that is already out |
| Missed releases and cleanup scope | MR1 | Validate recovery on the Deck after missed releases, in both layouts | Scenario | B, St, Miss: what each cleanup function clears and leaves; the Cleanup audit checks the lists |
| Missed releases and cleanup scope | MR2 | Verify whether interrupted transitions can leave both Mod 2 press orde… | Static | Both Modifier 2 orders are never on the stack together: the Cleanup audit's "never there". Its counts are from before 90.12 |
| Held inputs across layer changes | HI1 | One held stick click from Menu Left / Right Entry (before 300 ms) goes… | Obsolete | The stick click is a Release in the Entry Point since 90.10 (G2, T1) |
| Held inputs across layer changes | HI2 | Staggered Gyro toggle: hold LB, press RB, then release RB about 100 ms… | Scenario | B, T, H: the staggered Gyro toggle. What appears after the removal rests on A9 |
| Held inputs across layer changes | HI3 | Alternative only: soft-pull both triggers during ramp-up, then fully p… | Scenario | Tr, St, H, T: the alternative's Modifier 2 entry without re-pulling (same as TC11) |
| Held inputs across layer changes | HI4 | Output scope: the existing first-click check (a trigger pulled during… | Assumption | A10 and A11: outputs when a layer is added and when a removal exposes them |
<!-- table:end -->
