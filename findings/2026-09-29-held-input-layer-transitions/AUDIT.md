# Held inputs across layer changes: add vs. remove

Date: 2026-09-29. This is a static audit of both Neptune layouts (working tree on
`neptune-trigger-rampup-port`, HEAD `50758b3` plus the uncommitted cursor-gyro
edits). **No layout was changed.** The rule below is the layout author's runtime
observation. The JSON is consistent with it everywhere I looked, but I did not
reproduce it on a Deck.

Follow-up: F1's two missing alternative repeats are now fixed in JSON by the
[cursor self-removal implementation](../../plans/2026-09-29-cursor-self-removal.md)
and covered by regression tests; Deck validation remains pending. The audit and
inventory below describe the pre-fix snapshot, including its original cursor
inheritance. Current cursor overlays remove themselves to expose the repeating
parent transition.

## Summary

**Your understanding holds up.** Steam treats an input that is already held
differently depending on whether a layer was just added or just removed:

1. **Add:** a layer added while an input is held does **not** fire its
   immediate layer command on that input. From the new layer's point of view,
   nothing was pressed.
2. **Delay and repeat still fire:** on that same newly added layer, an
   activator with a Fire Start Delay fires once the delay elapses, and one
   with Hold to Repeat fires on its next interval. This is why the delayed
   Soft Presses in the ramp-up flow need no repeat.
3. **Remove:** a layer removed while an input is held **does** fire the newly
   exposed lower binding on that input, as if the input had just been pressed.

"Immediate" means a Regular Press, chord, or Soft Press with no Fire Start Delay
and no Hold to Repeat. "Layer command" means `add_layer`, `remove_layer`, or
`hold_layer`.

The layouts are built around this rule, mostly without saying so:

- **All 19 delayed layer applies per layout sit on the input that was just
  pressed to add their layer, and none of them repeat.** The 5 ms delay in
  `Gyro Off Ramp Up` exists for one reason: the stick is already past the
  threshold when that layer appears, so a zero-delay Soft Press would never
  fire. The earlier delayed-apply audit couldn't explain the 5 ms; this rule
  does.
- **Every repeating layer add outside Base is explained by rule 1:**
  Gyro's modifier entry, Mod 0/1 → Mod 2 entry, and Fn stick-click → Transition Set.
  Base's repeating entries are not; Base is never added, so they are backups
  for rule 3.
- **Every threshold exit that removes layers repeats** (five per layout),
  because its condition can already be true when its layer is added.
- **The menu Entry → Fn transitions add the Enter/Backspace overlay themselves**,
  even though Fn has its own chord that adds it. That chord can't fire on the
  already-held button (rule 1).
- **Ramp-up's modifier exits, Gyro Off Ramp Up's firing-control exit, and
  stale-menu recovery rely on rule 3.** The removal lets the same press reach
  the exposed binding.

I found no binding that contradicts the rule. Findings:

- **F1:** in the alternative layout, `R2: Modifier 1` and `Gyro | R2: Modifier 1`
  lack the Hold to Repeat that the other three Mod 2 entry pairs have. Under
  rule 1, R2 → L2 Mod 2 entry fails when LT is already pulled as R2's layer
  appears. This predates September; the archived export has it too.
- **F2:** three passages in the structure doc said the opposite of rule 3 or left
  it open. They now link to the new section.
- **F3:** the rule's scope is still open for key and mouse outputs, and for how
  the regular Mod 2 → Gyro toggle resolves while one bumper is still held.
  Deck checks are listed [below](#deck-checks).

## The rule, with the layout evidence

| Change while the input is held | Top binding on that input afterward | Fires? | Where the layout depends on it |
|---|---|---|---|
| Layer added | Immediate layer command | **No** | Menu Entry → Fn adds the overlay explicitly; repeats on Gyro entry, Mod 2 entry, and Fn click |
| Layer added | Fire Start Delay (any length) | Yes, after the delay | All 19 delayed applies, including the 5 ms ramp handoff |
| Layer added | Hold to Repeat | Yes, on the next interval | Gyro 50 ms entry, Mod 2 entry chord, Fn click chord, threshold exits |
| Layer added | Release activator | Yes, on release (a new event) | Every modifier, entry, and overlay release exit |
| Layer removed | Newly exposed lower binding | **Yes** | Ramp modifier exits, firing-control exit, stale-entry and guarded recovery pass-through |

### How this fits the other timer observations

Three earlier author observations are already documented:

- Layer removals reset Fire Start Delay timers, even when the removal comes from
  a different input ([Blocking to Protect Layer Timers](../../resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers)).
- A repeating removal restarts a delayed apply that got stuck after an
  interruption ([Interrupted Delayed Layer Applies](../../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies)).
- Stick-touch releases apply their pending target *before* removing helpers so
  the removals can't postpone it ([Complete Delayed Applies on Stick-Touch Release](../../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release)).

Taken with rule 3, they point the same way: **a removal makes Steam re-evaluate
held inputs, and an add doesn't.** The new layer inherits "already held" and
waits for a new press, a delay, or a repeat tick. A removal re-arms what it
touches: exposed bindings fire and delay timers restart.

This is a working model, not a verified description of Steam's internals. It
can't be a literal re-press of every binding. The 250 ms Mod 2 reset removes a
layer from its own Regular Press, and if that re-pressed the same activator, it
would loop every frame instead of letting the 200 ms apply finish.

## Walkthrough: the ramp-up flow

Default layout. Each row notes which input is held and why the activator fires.

| Step | What happens | Why it fires, or why the setting is there |
|---|---|---|
| 0 | Thumb touches RS: Base touch adds `RST: Entry Point` (its 150 ms chord later adds `RST: Tap Cover`). Neither defines RS edge. | Fresh touch. The 150 ms chord fires on the already-touched stick (rule 2). |
| 1 | RS reaches full deflection. Base RS edge Regular Press (radius 32767) adds `Gyro Off Ramp Up`; gyro is disabled. | Fresh press on Base. |
| 2 | `Gyro Off Ramp Up` owns RS edge. The stick is **already** past 29031 when it appears. Its Soft Press 29031 with **5 ms delay** adds `Turning Ramp Up 0`. | A zero-delay Soft Press would miss the held stick (rule 1). The 5 ms delay makes it fire (rule 2). |
| 2a | Same layer: inverted Soft Press 25807, **Hold to Repeat**, removes itself. | Only needed if the stick is already back inside when the layer appears. Repeat makes that case fire. |
| 3 | `Turning Ramp Up 0` owns RS edge (sensitivity 150). Soft Press 29031 with **250 ms delay** adds `Turning Ramp Up 1`. No repeat. | Rule 2, the case you called out. |
| 3a | Same layer: Regular Press repeating every 300 ms removes `Turning Ramp Up 1`. | Delayed-apply reset; a different purpose. It stops once Ramp 1 owns the edge. |
| 3b | Same layer: inverted Soft Press 29031, repeating, removes all three ramp layers. | If `Turning Ramp Up 0` arrives from the 5 ms handoff while the stick is already coming back, this exit is already true. Only the repeat fires it (rule 1). |
| 4 | `Turning Ramp Up 1` owns RS edge (sensitivity 200). Its only edge activator is inverted Soft Press 25807, repeating, which removes all three. | Same reasoning as 3b. |
| 5 | Stick drops inside 25807: all ramp layers removed. Base RS edge is exposed, but the stick is below 32767, so nothing fires. Gyro is back. | Rule 3 would fire the Base edge if the stick were still at full deflection. It isn't. |

Branches:

- **Firing control held first.** Base's Any chord (LT/RT full or soft pull)
  interrupts the Regular Press and adds `Turning Ramp Up 0` directly, so gyro
  stays on. Then steps 3–5.
- **Firing control pulled mid-ramp.** Ramp 0/1 have empty trigger groups, so
  the pull reaches `Gyro Off Ramp Up`'s trigger Regular Press (repeating,
  uninterruptible), which removes that layer. That exposes Base's mouse button
  under the held trigger, so the first click still registers (rule 3, applied
  to a mouse output; see F3). The repeat covers `Gyro Off Ramp Up` being added
  while a trigger is already down, where rule 1 would otherwise skip it.
- **Modifier pressed mid-ramp.** The top ramp layer's LB/RB Regular Press
  removes all three ramp layers and does nothing else (`empty_binding`). With
  LB still held, Base's (or Gyro's) LB entry is exposed and fires by rule 3,
  adding the right modifier variant. Their 50 ms repeat is a backup. Base's
  RS-edge LB/RB chord (empty, uninterruptible) then keeps the exposed edge
  from restarting ramp-up while the modifier is held. The port plan credited
  the repeat for this re-entry. By rule 3 the removal alone is enough.
- **Alternative layout.** The roles are swapped. Ramp layers block the soft pull
  (`edge` → empty) and exit on full pull (`click` → remove all three, repeating).
  The full pull exposes Base's trigger `edge`, which is still held, so
  `L2/R2: Modifier` enters by rule 3.
  `Gyro Off Ramp Up`'s bumper removal repeats for the same reason as the
  default's trigger removal.

## Inventory: which layer adds repeat, and why

Counts are per layout (default / alternative).

### Repeating adds (19 / 17)

| Add | Layer added? | Rule that needs the repeat |
|---|---|---|
| Base: Start/Select entry, LB/RB (alt LT/RT) entry at 50 ms, LS/RS touch, RTP touch, RS edge (both) — 9 / 9 | Never (Base is the action set) | None. Base bindings come back only through removals, which fire them by rule 3. Keep the repeats as a backup |
| Gyro: LB/RB (alt LT/RT) → `Gyro \| … Modifier`, 50 ms — 2 / 2 | Yes, by the regular Mod 2 release, often while the other modifier is still held | **Rule 1.** Gyro arrives over a held modifier, so its entry can fire only on a repeat tick |
| Mod 0/1 second modifier → Mod 2 (plus tap covers), regular and Gyro — 4 / **2** | Yes, the first modifier layer can appear while the second is already held (both pressed together, or a ramp exit exposing both) | **Rule 1.** The alternative's R2 side lacks it (F1) |
| Menu Fn stick click → Transition Set — 4 / 4 | Yes, Menu Entry's own click chord adds Fn while the click is held | **Rule 1.** Without the repeat, one held click stops at Fn; it would take a second click to reach the Transition Set |

### Delayed adds (19 / 19): no repeat needed to fire

Each parent below is added by a press of the same input that carries its
delayed apply, so the input is always held when the delay starts:

| Parent (added by) | Delayed target | Delay |
|---|---|---|
| Both Menu Entry Points (menu button) | Own Fn Layer | 300 |
| Four single modifiers, regular/Gyro (modifier press) | Own Temp Cursor Gyro | 300 |
| Four Mod 2 variants (second modifier) | Combined Tap Cover | 200 |
| `Turning Ramp Up 0` (stick already at edge) | `Turning Ramp Up 1` | 250 |
| `Gyro Off Ramp Up` (stick already at edge) | `Turning Ramp Up 0` | 5 |
| LST / RST / RTP Entry Point (touch) | Own Tap Cover | 150 |
| Two scroll layers (second modifier press in Double Tap) | Own Double Tap Cover | 150 |
| Menu Left: Escape / Menu Right: Tab (second menu press in Double Tap) | Own Double Tap Cover | 150 |

Eleven of these also have a separate repeating reset. That fixes interrupted
applies, a different problem from firing on a held input.

### Immediate adds that don't repeat

None of these rely on a new layer firing an immediate layer command on an
already-held input:

- **Release-triggered adds** (Double Tap windows, touch-release completion adds).
  A release is a new event.
- **Double Tap second presses** (Scroll Down/Up, Escape/Tab, LST/RST Temporary
  Gyro + Entry, Circular Scroll). The window was added on release, so the
  second press is fresh.
- **Chords that add an overlay while sending output** (nav keys, face buttons,
  clicks). The press is fresh. The overlay doesn't redefine that input, so it
  falls through to the chord that just fired.
- **Menu Entry → other menu button** adds the overlay and Fn in one array. The
  press is fresh, and the array adds the overlay itself because Fn's own chord for it
  can't fire on the held button. These are the only two places per layout
  where a newly added layer has an immediate layer command on the held input.
  They are handled this way on purpose.

### Repeating removals

| Kind | Why it repeats |
|---|---|
| Threshold exits: `Gyro Off Ramp Up` 25807, `Turning Ramp Up 0` 29031, `Turning Ramp Up 1` 25807, `LTP: Arrow Keys` and `RTP: Mouse Buttons` click release — all inverted Soft Presses, 5 / 5 | **Rule 1:** the exit condition can already be true when the layer appears. That is realistic for the ramp handoffs; the trackpad-click exits share the shape as a safeguard. The Base LS-edge WASD scaffold is also inverted but has no repeat. That's correct: it sends no layer command and Base is never added |
| `Gyro Off Ramp Up` firing-control removal (default triggers, alternative bumpers) | Rule 1: the layer can appear while a firing control is already down |
| Ramp modifier exits (default LB/RB, alternative trigger click) | Mostly a backup. The press that triggers them is normally fresh |
| Guarded recovery (all of them) | Convention: retry while the recovery input stays eligible. Rule 3 already cascades a single press through stacked stale layers. The repeat also covers an input that was held before the guard dropped |
| Delayed-apply resets (11) | Restart an interrupted apply. They don't handle held inputs |

## Where the layout relies on rule 3

- **Ramp modifier exits** (above): the modifier enters on the same press that ends
  ramp-up.
- **Firing control during `Gyro Off Ramp Up`:** the first click registers.
- **Stale Menu Entry:** pressing the other menu button clears the stale entry,
  then Base's entry for that button fires, so it "works normally" on the same
  press. This is the existing manual check under *Stuck entry layer*.
- **Guarded recovery in general:** clearing a stale layer exposes the input's
  normal action, which fires on the same press.
- **Double Tap expiry:** a bumper or stick edge held through the window fires
  its Base binding when the window removes itself, for example the RS edge
  resuming ramp-up after `L1: Double Tap` expires.

The flip side: any new removal fires the exposed binding of every input
the user is still holding. When you add a removal, trace what it exposes on
held inputs, not just what it clears.

## Findings

### F1. Alternative R2 → Mod 2 entry doesn't repeat

| Layer (alternative) | Group | Input | `hold_repeats` | Source |
|---|---|---|---|---|
| `L2: Modifier 0` | 257 | RT `edge` chord → L2!R2 Mod 2 | `"1"` | [line 3354](../../neptune/single-set-alternative_hold-gyro_latest.json#L3354) |
| `R2: Modifier 1` | 258 | LT `edge` chord → R2!L2 Mod 2 | **missing** | [line 3398](../../neptune/single-set-alternative_hold-gyro_latest.json#L3398) |
| `Gyro \| L2: Modifier 0` | 12923 | RT `edge` chord | `"1"` | [line 13559](../../neptune/single-set-alternative_hold-gyro_latest.json#L13559) |
| `Gyro \| R2: Modifier 1` | 12940 | LT `edge` chord | **missing** | [line 14191](../../neptune/single-set-alternative_hold-gyro_latest.json#L14191) |

All four default counterparts repeat: `L1: Modifier 0` [line 15949](../../neptune/single-set-default_hold-gyro_latest.json#L15949),
`R1: Modifier 1` [line 16051](../../neptune/single-set-default_hold-gyro_latest.json#L16051),
and the Gyro variants at [18740](../../neptune/single-set-default_hold-gyro_latest.json#L18740)
and [18842](../../neptune/single-set-default_hold-gyro_latest.json#L18842).
The archived alternative export has the same gap, so this is old, not a
September regression.

Failure case under rule 1: both triggers are soft-pulled during ramp-up, where
the ramp layers block the soft pull. Then one trigger is fully pulled. The
removal exposes both Base trigger entries at once (rule 3). If `R2: Modifier 1`
lands on top, its LT chord can't fire for the LT that is already pulled, so
Mod 2 needs a re-pull. Pulling both triggers at nearly the same moment is a
second case.

**Recommendation, not applied:** add `hold_repeats: "1"` (no explicit rate,
matching the other three pairs) to both chords. The entry count doesn't
change. The repeat stops once Mod 2 owns LT `edge`. Confirm on the Deck with
the F1 check below.

### F2. Documentation said the opposite of rule 3

Three passages in [Steam Input JSON Structure](../../resources/Steam%20Input%20JSON%20Structure.md)
now point to the new [held-input section](../../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes):

- *How Binding Overlay Works*, step 3: "Do not assume the triggering event is replayed
  into a newly exposed cleanup."
- *Inheritance Review*, step 3: "Static inspection does not prove … that the same
  gesture fires a newly exposed binding."
- *Stick-Edge Cleanup*: "the same gesture is not guaranteed to run both cleanup
  and the newly exposed action."

Historical plans and findings were left as written. The port plan says the
repeating entry performs ramp re-entry; rule 3 makes the removal enough on its own.

### F3. Open scope questions

1. **Key and mouse outputs on add.** You scoped rule 1 to layer commands.
   Four overlays depend on outputs firing on the press that adds their layer:
   `Menu Left: Backspace`, `Menu Right: Enter`, `Menu Left: Escape`, and
   `Menu Right: Tab` send their key from a Regular Press on the same held
   menu button. If outputs followed rule 1, the first Backspace/Enter and
   double-tap-hold Escape/Tab would be missing. These checks are still
   unchecked in manual testing.
2. **Mouse output on remove.** The firing control during `Gyro Off Ramp Up`
   applies rule 3 to a mouse button. Also still unchecked.
3. **Regular Mod 2 release while one modifier is still held.** The release array
   removes 13 layers, then adds Gyro (with beep and notification). Rule 3 fires
   the exposed Base modifier entry. Rule 1 holds back Gyro's entry until its
   50 ms repeat tick. What happens depends on whether Steam re-checks the held
   bumper before or after the `add_layer Gyro` in the same array:
   - After: only `Gyro | L1: Modifier 0` appears.
   - Before: the regular `L1: Modifier 0` also appears, under Gyro.

   Either way, releasing that bumper later goes through a modifier release, which
   adds `L1: Double Tap` and scrolls after 50 ms. The Gyro → regular toggle
   (removing Gyro) exposes Base's entry directly. That scroll may already be
   familiar and accepted; it follows from the rules, so it is listed as a
   check, not a defect.

## Deck checks

Added to [manual testing](../../manual-testing.md#held-inputs-across-layer-changes).
A disposable minimal layout separates the rule from this layout's other logic:

1. Base: A Regular Press → `add_layer X 0 1` (notification on). X: B Regular Press
   → `add_layer Y 0 1`. Hold B, then press A. **Rule 1 predicts Y does not appear.**
2. Repeat step 1 with a 5 ms Fire Start Delay on X's B. **Rule 2 predicts Y appears.**
   Repeat with Hold to Repeat instead of the delay: Y appears after one interval.
3. X: B Regular Press → `remove_layer X`. Base: B has a second binding that adds Y.
   Enter X, hold B. **Rule 3 predicts Y appears from the exposed Base binding.**
4. Scope: replace X's B with `key_press` and step 1's hold. Does the key fire?
   (F3.1.)

Then in the real layouts: one held stick click from Menu Entry reaches a
Transition Set; the staggered Mod 2 release; the alternative's F1 scenario;
and the existing first-click and Enter/Backspace checks.

## Reproduce

```sh
tmp=$(mktemp -d)
python3 convert_runtime_ids.py to-titles neptune/single-set-default_hold-gyro_latest.json --output "$tmp/default.json"
python3 convert_runtime_ids.py to-titles neptune/single-set-alternative_hold-gyro_latest.json --output "$tmp/alternative.json"
python3 findings/2026-09-29-held-input-layer-transitions/build_inventory.py "$tmp/default.json"
python3 findings/2026-09-29-held-input-layer-transitions/build_inventory.py "$tmp/alternative.json"
```

Section A of the output lists every layer added while its own input is held,
and classifies the new layer's bindings on that input. In each layout the only
immediate layer commands are the two Menu Entry → Fn cases described above.
Section B lists the repeating adds (19 / 17).

Key sources (default unless noted): `Gyro Off Ramp Up` 5 ms apply
[line 19374](../../neptune/single-set-default_hold-gyro_latest.json#L19374)
(alternative [19628](../../neptune/single-set-alternative_hold-gyro_latest.json#L19628));
`Turning Ramp Up 0` edge [3624](../../neptune/single-set-default_hold-gyro_latest.json#L3624);
Base RS edge [818](../../neptune/single-set-default_hold-gyro_latest.json#L818);
Gyro LB entry [19290](../../neptune/single-set-default_hold-gyro_latest.json#L19290);
Menu Left Entry → Fn + Enter [17309](../../neptune/single-set-default_hold-gyro_latest.json#L17309);
Menu Left Fn LS/RS click → Transition Set [6435](../../neptune/single-set-default_hold-gyro_latest.json#L6435) /
[11043](../../neptune/single-set-default_hold-gyro_latest.json#L11043);
ramp LB exit [16225](../../neptune/single-set-default_hold-gyro_latest.json#L16225);
`Gyro Off Ramp Up` LT removal [15522](../../neptune/single-set-default_hold-gyro_latest.json#L15522);
L1!R1 Mod 2 RB release [16487](../../neptune/single-set-default_hold-gyro_latest.json#L16487).
Line numbers refer to the current working-tree files and will drift with edits.
