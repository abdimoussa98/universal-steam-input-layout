# Manual testing (Deck)

Implementation work is tracked in [todos.md](todos.md). Unchecked items below remain pending runtime validation.

- Covers every release from 90.6 to 90.13, newest first, and below them the
  areas from before 90.6 that were never run (menu buttons, modifiers, cursor
  gyro, triggers and ramp-up, recovery, held inputs)
- Nothing here has been run on the Deck
- Load both VDFs fresh, not in the live editing session, and run every check on both layouts
- Written for the default. In the alternative, swap LB / RB ↔ LT / RT: the bumpers fire, and the soft-pull triggers are the modifiers
- If a bind applies the wrong layer, suspect the load-order swap (`findings/2026-07-11-layer-order-swap/`)

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
