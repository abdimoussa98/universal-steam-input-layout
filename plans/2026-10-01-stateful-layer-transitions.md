# Brainstorm: stateful layer transitions

Status: design agreed, 2026-10-01, after thirteen rounds with the author.
Nothing here is implemented and no layout was changed. **The clean
description is [Stateful Layer Transitions](../resources/Stateful%20Layer%20Transitions.md);**
this file is the record of the decisions, the facts about today's layouts
and the options that were rejected. Sections 3 and 4 describe the layouts as
they were at release 90.8; the 90.9 change that removed the menu overlays
isn't reflected. Related:
[vocabulary](../resources/Layout%20Vocabulary.md)
· [definition of done](../resources/Layer%20Definition%20of%20Done.md)
· [held-input rules](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)

Scope: the stateful layers that exist today, `Gyro` and `Steering`. Cursor
Gyro, Gamepad and Menu modes are not designed here (author, 2026-10-01). The
rules should still hold when those are added.

## 1. Purpose

A stateful layer remaps buttons the player is already holding to reach it. The
transition layer exists so that **no control used for the gesture is still
held when the stateful layer becomes live**, and the same on the way out.
Otherwise the new layer sees a held button and can send an input the player
never meant.

Two things follow:

- The transition **clears first**. As soon as the gesture is complete (menu
  button held, stick clicked), the source interaction is removed and every
  input is blanked.
- The transition **commits last**. The destination is added only after the
  gesture controls are released.

## 2. Decisions so far (author, 2026-10-01)

1. **Entry and exit both go through a transition.** The gesture is a menu
   button plus a stick click, for entering a stateful layer and for leaving
   it. The exit side isn't built yet.
2. **Two exits skip the transition.**
   - **Modifier 2.** Both modifiers together always clear everything to Base.
     That is both bumpers in the default layout and both triggers in the
     alternative. It is the fallback from any state.
   - **Steering's hold exit.** Holding W with no driver exits Steering after
     2.5 s, with the warning from 1 s. It stays, because Steering should be
     easy to leave. It must also work on **S**, for reversing. Today only W
     has it.
3. **Only the gesture controls have to be released.** The menu button and the
   stick click that opened the transition must both be up when it ends. Any
   other button the player happens to hold is out of scope.
4. **No layer can be entered from a transition.** While a transition is
   active, no input may add another layer. Every input that would add one
   underneath is blocked.
5. **Block, don't replace.** The wheel on the modifier pair was a replacement
   whose purpose was to hide the modifier entry. To keep it simple these
   become empty bindings.
6. **Both layouts get the same treatment.** See §4.
7. **Don't design for modes that don't exist yet.**
8. **Exit is one simple rule.** Inside a stateful layer, any menu button plus
   any stick click clears it: same side, opposite side, either stick. It
   needs no extra layer and no per-combination routing.
9. **`Gyro` is excluded from the exit rule.** Menu plus stick click never
   removes `Gyro`; with only `Gyro` on, Menu Right + LS click still enters
   Steering above it. The clear keeps `Gyro` for now, and only Modifier 2
   removes it (confirmed in round eleven).
10. **Menu buttons inside Steering:**
    - **No driver held:** the normal Menu Entry Point flow, the same as
      outside Steering. Steering stays underneath.
    - **W or S driver held:** Start is Tab and Select is Escape. Plain keys,
      nothing inherited, no menu flow.
    - **Steering Modifier 0 to 2:** the same Start and Select keys as the
      normal Modifier 0 to 2.
11. **No back-out inside a transition.** The Select-press cancel in
    `Transition Set 1` goes. Let go, land in Steering, and leave with any
    menu plus stick click.
12. **When a stick recentres, its guard comes off and the player is back in
    the Entry Point they were in** (restated in round nine, after decision
    18 was withdrawn).
13. **The Entry Points own the transition clicks, and both their sticks are
    D-pads.** The right stick changes from mouse mode to `dpad` with empty
    directions, copying the left stick's setup. The click on each stick is
    the transition bind. The Fn layers stop binding the stick clicks and
    inherit them, which works because the modes now match. The camera is dead
    while a menu button is down; that is accepted, because nobody aims with
    the right stick while tapping Tab or Escape.
14. **Fn delay drops from 300 ms to 200 ms** (tentative, to be tuned). Tab and
    Escape need a quicker tap, and Fn arrives sooner.
15. **Decision 13 applies to every Entry Point, whenever a menu button is
    held**, not only under the guard. The Entry Point holds the transition
    binds and everything above it inherits them.
16. **Two more Entry Points for stateful layers.** The Base pair sends the
    clicks to the entry transition; the stateful pair sends them to the
    clear. That is how the destination changes with where the player is.
17. **The stick guards are reusable.** A guard never binds the stick clicks,
    so the same guard works over every Entry Point.
18. *(Withdrawn.)* Recentring clears the whole menu family.
19. **Never detect a recentre with an inverted edge bind on a D-pad-mode
    stick.** The repeating centre bind isn't caught reliably there. The
    ramp-up's Soft Press centre clearing works, but only on a mouse-mode
    stick.
20. *(Withdrawn after the author's manual test.)* Detecting a recentre with
    a deflection chord on the owner button, backed by a repeating removal.
    It doesn't work.
21. **Split the guard by stick, not by menu side.** There is a left-stick
    guard and a right-stick guard, mirror images of each other. An Entry
    Point's stick edge adds that stick's guard. The guard binds a normal
    outer edge on its own stick, and the **Release** of that edge removes
    only that guard. Edge release is reliable on a D-pad stick. The guard
    leaves the other stick alone, so the other stick's edge is inherited
    from the Entry Point and the two guards can stack.
    **Approved as the approach (round ten).**
22. **The Entry Point's repeating reset brings Fn back after a guard comes
    off.** The reset (350 ms today, 250 ms with decision 14) keeps firing on
    the held menu button and restarts the delayed Fn timer, so Fn always
    arrives on a continued hold, and its haptic bump confirms it. The exposed
    Fn timer is therefore not a risk for the guard recipe.
23. *(Replaced by decision 26.)* Two transition layers in total.
24. **Steering needs its own pair of Entry Points**, whose clicks lead to the
    clear. Each later stateful layer may need its own pair as well. Not
    designed now, only noted.
25. **Chords latch (author's manual test).** Once a chorded activator is
    active, releasing the chord button doesn't re-evaluate it. The input
    stays in the chord until the button the chord is bound to is released.
    So a bind can't hand over from a chord to a Regular Press when the chord
    button goes up. Hypothesis, not yet tested: a `remove_layer` call
    re-evaluates held inputs, the same way it restarts delays, because any
    change to the stack seems to re-evaluate everything.
26. **Gesture map and its encoding (author, round twelve).**
    - Menu Right + RS click and Menu Left + LS click lead to Gamepad.
    - Menu Left + RS click leads to stateful Cursor Gyro.
    - Menu Right + LS click leads to Steering.
    - The Entry Points hold these binds, and the click adds the transition
      on its **Release**. By the time the transition is up the stick click
      is already released, and only the menu button is left to let go.
    - The transition commits on the **menu button's Release**, and which
      menu button it is picks the destination.
    - Three transition layers: 0 for the same-side gestures, 1 for the
      cross gestures, 2 for the clear. See §6.
27. **Unbuilt destinations clear.** Until Gamepad and Cursor Gyro exist,
    their gestures clear to Base, keeping `Gyro`.
28. **Two transition layers now, a third with Gamepad.**
29. **The structure is documented and checked.** It lives in
    [Stateful Layer Transitions](../resources/Stateful%20Layer%20Transitions.md)
    and in the definition of done (§11), which every new stateful layer has
    to pass. A test takes over once the structure is built, and is extended
    with each stateful layer until all four gestures are taken.
30. **The Menu stateful layer is an exception.** It won't go through the
    transitions; it stays in the todos.
31. **Stateful Cursor Gyro has three exits.** The menu-plus-click clear, the
    Modifier 2 clear, and its own clear built the way Temp Cursor Gyro
    clears (both sticks deflected). The third skips the transition and is an
    exception like Steering's hold exit. In general a stateful layer may add
    an exit of its own but always keeps the first two.
32. *(Replaced by decision 33.)* End Steering's Modifier 0 and 1 on the
    Release of their own direction.
33. **Steering's Modifier 0 and 1 use the stick-guard recipe** (not built).
    A normal, generous outer edge holds the modifier and its Release cleans
    up, so the player can roll to A and D inside it. The entering direction
    is blocked. The opposite direction only cleans up; it never adds the
    other modifier. Every cleanup is guarded by two All-chords: left-stick
    deflection plus the left driver, and plus the right driver (bumpers in
    default, triggers in alternative).
    Details and open points are in
    [Stateful Layer Transitions](../resources/Stateful%20Layer%20Transitions.md#not-settled).
34. **Edge binds in Steering's Modifier 0 and 1** (clarified). The edge
    Release clears the modifier and adds its Double Tap window. The edge
    also carries the hold that applies the Tap Cover. A second press in the
    window's direction adds the repeating-scroll cover. The windows' timeout
    is settled by decision 35.
35. **The Steering Double Tap windows become Always On windows**, as the
    author originally intended. The inverted-edge timeout was an oversight.
36. **Definition of done rule:** on a D-pad-mode stick an inverted edge never
    adds or removes a layer. Output-only uses such as a walk bind or the WASD
    modifier are fine.

## 3. What the layouts do today

Checked in both Neptune JSON files. This differs from the author's
recollection in four places.

| Topic | Recollection | In the JSON |
|---|---|---|
| Numbering | 0 = Menu Left, 1 = Menu Right | 0 = **RS click**, 1 = **LS click**. Both Fn layers reach both |
| Clear on click | Menu family cleared when the stick clicks | Not cleared. `Transition Set 0` leaves Entry/Fn underneath. `Transition Set 1` clears everything only at commit |
| Commit | On stick release | On **Start release** (`Transition Set 1` → `Steering` + `Steering \| LS: Entry Point`). Stick click is an empty Regular Press with no release |
| Menu button in the transition | No bind | `Transition Set 0`: Start/Select release are empty. `Transition Set 1`: Start release commits, Select press cancels |

Other facts that matter:

- `Transition Set 0` has no commit. It only has the guarded recovery: stick
  touch or edge removes it and both menu families when neither menu button is
  held.
- `Transition Set 1` reached from Menu Left can't commit on Select. The player
  has to press and release Start.
- The commit doesn't wait for the stick. Releasing Start while LS is still
  clicked enters Steering with the click held.
- **Steering has two exits that skip the transition**, besides Modifier 2:
  - Any Start or Select press removes the whole Steering family and adds that
    side's Menu Entry Point. This is in `Steering` and in both W/S driver
    layers. Decision 10 replaces it.
  - Holding W with no driver exits after 2.5 s, with a warning from 1 s.
- **Steering's Modifier 0 to 2 already match the normal ones** on Start and
  Select: Insert / Delete, Home / End, Page Up / Page Down.
- **Base's stick clicks are Q and E**, on the stick groups' `click` input.
- **Modifier 2 can't be reached inside a transition.** The modifier controls
  are bound to the wheel there, so Base's modifier entry is hidden.
- `Gyro` is entered by the uncovered Modifier 2 release from Base and left by
  the same gesture. It never passes through a transition.

## 4. The transition in both layouts

The two layouts swap the modifier pair and the firing pair. Today each
transition mirrors that swap:

| Control | Default today | Alternative today |
|---|---|---|
| Bumpers | Wheel down / up | Left / right mouse button |
| Trigger soft pull (edge) | Not bound, so Base's mouse buttons show through | Wheel down / up |
| Trigger full pull (click) | Empty, with haptic | Empty, with haptic |

So in both layouts the modifier pair scrolls and the firing pair clicks the
mouse while a transition is up.

With decision 5, all three rows become empty bindings in both layouts. The
transition layers are then **identical in the default and the alternative**,
which removes the mirroring work for these layers.

**Decision 4 already holds against Base and `Gyro`.** A static check of both
layouts on 2026-10-01 found no input in Base or `Gyro` that adds a layer and
is left unbound by either Transition Set. Start, Select, the modifier pair,
both stick touches and edges are all overridden, and gyro and both trackpads
are disabled. What still passes through is output only, not layer entry:

- Face buttons, D-pad and the four back grips send their Base keys.
- In the default layout the trigger soft pull sends Base's mouse buttons
  until it is blanked.
- Base's trackpad-touch mode shifts aren't overridden, but both trackpads are
  disabled in the transition.

The check covered Base and `Gyro` only. `Transition Set 0` also sits on the
menu Entry and Fn layers today; clearing them on the click (rule 3) removes
that case.

**Consequence for Modifier 2:** the fallback isn't reachable from inside a
transition, since reaching it means adding the modifier layers. The
transition is momentary. It ends when the two gesture controls are released,
and its guarded recovery covers a missed release.

## 5. Proposed rules

1. **Every stateful entry and exit goes through a transition**, except the
   Modifier 2 clear and Steering's W/S hold exit (decisions 1 and 2).
   Stateful layers never add each other directly.
2. **`Gyro` stays on Modifier 2.** From Base the uncovered Modifier 2 release
   adds `Gyro`. From `Gyro` or `Steering` it clears to Base. `Gyro` doesn't
   remap the controls that toggle it, so it has nothing to protect.
3. **Clear on entry to the transition, then block.** The binding that adds
   the transition also removes the menu family, its overlays and every
   transient layer. The transition then blocks every input that could add a
   layer, with empty bindings and disabled gyro and trackpads (decisions 4
   and 5).
4. **The destination goes live when the gesture controls are released**:
   stick click first, then the menu button (§6).
5. **Destination discipline.** At entry a stateful layer has no Release,
   delayed or repeating binding on a gesture control. Those are the cases the
   held-input rule doesn't make safe. `Steering | LS: Entry Point` is the
   existing pattern for anything else that must be guarded at entry.
6. **A transition is an Owner** for the definition of done. It binds both
   stick-touch releases, has a guarded recovery in case a release is missed,
   and takes its removal lists from the cleanup generator.

## 6. How the transition ends (decision 26)

The stick click's **Release** in the Entry Point adds the transition. The
menu button's **Release** in the transition commits. Both gesture controls
are up at the commit, in a fixed order, with no counting.

**Entry Point binds (Base pair, also used over `Gyro`):**

| Entry Point | LS click release | RS click release |
|---|---|---|
| `Menu Left: Entry Point` | Transition 0 | Transition 1 |
| `Menu Right: Entry Point` | Transition 1 | Transition 0 |

**Steering's pair of Entry Points:** both click releases add Transition 2.

**Transition layers:**

| Layer | Select (Menu Left) release | Start (Menu Right) release |
|---|---|---|
| Transition 0, same side | Gamepad | Gamepad |
| Transition 1, cross | Stateful Cursor Gyro | Steering |
| Transition 2, clear | Clear, keeping `Gyro` | Clear, keeping `Gyro` |

Why this is better than the earlier proposals:

- **Every step is established behaviour.** A Release fires on a layer added
  over a held button, as today's Start commit and Fn's Select release do.
  Nothing depends on a layer exposed by a removal, so the manual test asked
  for earlier isn't needed.
- **Two layers encode four gestures**, because the held menu button carries
  half the information.
- **No chords, timers or centre binds.**

Consequences:

- **Three transition layers once Gamepad exists.** Today only Steering is
  built, so Transition 1 and the clear are enough and the count stays at two.
  The third arrives with Gamepad.
- **The clear happens at the click's release, not its press.** Between the
  two, the Entry Point is unchanged. If the click is held past the Fn delay,
  Fn arrives and inherits the click bind, so the release still works.
- **Menu button released first cancels.** The click release then lands on
  Base and no transition is added. The menu release is an ordinary one:
  silent once Fn has arrived, Tab or Escape inside the Fn delay.
- **In Transition 1 the two menu buttons differ.** A stray tap of the other
  one commits to the other destination. Transitions 0 and 2 are symmetric.
- **A click held from before the menu press counts.** Its Release fires in
  the Entry Point like any other. With the earlier press chord it didn't.
- **Binding Release on the click replaces the whole input**, so Base's Q and
  E don't fire while a menu button is held.
- **Unbuilt destinations.** Until Gamepad and Cursor Gyro exist, their
  commits clear to Base, keeping `Gyro` (proposed default).

Withdrawn: the two stacked covers that counted releases, the per-destination
transition with a shared guard, ending on one release with the other control
still down, and the chord-guarded touch clock (chords latch, decision 25).

## 7. Where the stick click lives (author proposal, 2026-10-01)

**Proposal:** one transition layer that always clears every layer to Base.
The four menu Entry Points bind the stick clicks themselves: the click clears
everything and adds the transition. The Fn layers stop binding the click and
inherit it from the Entry Point underneath. The clear list is generated and
checked with the audit tooling.

**What the Entry Points do with a click today** (both layouts):

| Entry Point | LS click | RS click |
|---|---|---|
| `Menu Left: Entry Point` | Add Menu Left Fn | Add Menu Left Fn |
| `Menu Right: Entry Point` | Add `Transition Set 1` | Add Menu Right Fn |
| `Steering \| Menu Left: Entry Point` | Add Menu Left Fn | Add Menu Left Fn |
| `Steering \| Menu Right: Entry Point` | Add `Transition Set 1` | Add Menu Right Fn |

Two of the eight already go straight to a transition; that is the Steering
entry. The other six add Fn and rely on Fn's repeating click chord to reach a
Transition Set on the same held click. The proposal makes all eight work like
the two.

**What it buys:**

- The clear happens at the click (its Release, by decision 26), not after a
  hop through Fn.
- The Entry → Fn → Transition Set chain goes away, and with it Fn's four
  repeating click chords and the two click mode-shift groups per Fn layer.
- No new layer for the transitions until Gamepad is built (§6).

**Catches, and where they stand:**

1. **RS click through Fn: solved by decision 13.** Fn binds the right stick
   in `dpad` mode and the Entry Points bound it in `joystick_mouse` mode, and
   a different source mode blocks inheritance. With both Entry Point sticks
   as D-pads the modes match and Fn inherits both clicks.
   - Consequence: with the stick guard up, the camera stays dead until the
     menu button is released or the stick recentres, not only for the Fn
     delay.
   - Fn inheriting a stick input from the Entry Point is inheritance from the
     middle of the stack. The unverified report that sticks skip the middle
     is still a tracked todo. The layouts already depend on the same thing
     where the cursor overlays inherit stick touches.
   - Fn's switch-group stick-click mode shifts go, since the click now clears
     Fn.
2. **The Entry Point can't tell where the player came from: solved by
   decision 16.** There are two Entry Points per side, and the layer that
   adds one picks it. Base adds the Base pair; a stateful layer adds the
   stateful pair.
3. **Click before menu button.** With the click bound on Release (decision
   26) this order now counts: the Release fires in the Entry Point even when
   the click was already down.

**Click routing with decision 16:**

| Entry Point | Where the clicks lead |
|---|---|
| Base pair (also used over `Gyro`) | The gesture map in decision 26 |
| Steering's pair (added by Steering) | The clear, keeping `Gyro` |

**Layer tally for the menu and transition part:**

| | Today | Proposed |
|---|---|---|
| Base Entry Points | 2 | 2 |
| Second pair of Entry Points | 2 (protected, stick out) | 2 (stateful) |
| Stick-out handling | 2 Tap Covers | 2 guards, one per stick |
| Transitions | 2 | 2 now, 3 once Gamepad exists (§6) |
| Total | 8 | 8 |

The four existing `Steering | Menu …` layers can be repurposed in place: the
two protected Entry Points become the stateful pair and the two Tap Covers
become the guards. No runtime ID shifts and the layer total is unchanged. This
holds until the third transition is added with Gamepad.

Superseded: the earlier options for this catch (fixed destinations, the layer
underneath owning the click, an exit overlay).

**Timer change (decision 14).** Each Entry Point has two values, in both
layouts: the 300 ms Fire Start Delay that adds Fn and the 350 ms repeating
reset. Moving to 200 ms means 200 and 250, keeping the 50 ms gap. Tests pin
the current values.

## 8. Stick guards instead of protected Entry Points (decisions 17 and 21)

**What the protected flow does today** (per menu side, two layers:
`Steering | Menu …: Entry Point` and `Steering | Menu …: Tap Cover`; the
names say Steering, but Base adds them):

- **Entered** when a stick is already past the edge as the menu button goes
  down (a deflection chord in Base), or passes it during the normal Entry
  Point (repeating edge chord, which swaps the Entry Point out).
- **Tap** sends Tab or Escape on release. There is no double-tap window.
- **Button down 300 ms** adds the Tap Cover, so the release is silent.
- **No Fn timer.** Stick clicks still work.
- **Recentring does nothing.** It stays protected until the menu button is
  released.

**The two guards:**

| | Left-stick guard | Right-stick guard |
|---|---|---|
| Added by | Entry Point's LS edge, repeating | Entry Point's RS edge, repeating |
| Own stick | Outer edge, not inverted; Release removes this guard | Same |
| Other stick | Unbound: inherits the Entry Point's edge | Same |
| Stick clicks | Unbound: inherits the transition binds | Same |
| Menu buttons | Bound, so the Fn timer underneath is hidden; release only cleans up, no key | Same |

- **Two layers serve everything.** The guards are split by stick, so the
  same pair works for Menu Left and Menu Right and over all four Entry
  Points.
- **The Entry Point adds them both ways.** Its edge bind repeats, so it fires
  for a stick that was already out when the Entry Point was added and for one
  that goes out later. Base's deflection chord on Start and Select is no
  longer needed.
- **They stack.** With both sticks out both guards are up. Releasing one
  stick removes one guard. If that stick goes out again, the Entry Point's
  edge bind is exposed for it and adds its guard back.
- **Edge radius.** On a D-pad stick radius 4915 engages near 25% of travel
  and releases near 5%, by the documented hysteresis. So the Release fires
  when the stick is practically centred. The right stick is a D-pad in the
  Entry Points now, so it takes 4915 as well, not its mouse-mode 7209. Guard
  and Entry Point must use the same radius, or the guard may not see the
  edge as held when it is added. If a resting stick sits above 5%, raise the
  radius.

**What the recipe leans on:**

1. **Release fires for an edge that was already out when the guard was
   added.** Established for buttons and for stick touch; not isolated for a
   stick edge.
2. **Fn after the last guard comes off: covered by decision 22.** The Entry
   Point's repeating reset restarts the Fn timer on the held button.
3. **Stick inheritance from the middle of the stack.** Under a guard the
   stick clicks come from the Entry Point, which is neither the top layer nor
   Base. The unverified report that sticks skip the middle is a tracked
   todo, and it becomes a gate for this design.
4. **The other menu button.** The guards serve both sides, so they bind both
   menu buttons the same way. A stray tap of the other one runs the cleanup
   release and clears the menu flow while the owner is still held. Base's
   repeating entry then adds the Entry Point back.

## 9. Recentre detection (decision 19)

**Where a recentre is detected today:**

| Where | Stick and mode | How | Status |
|---|---|---|---|
| Ramp-up exits (`Gyro Off Ramp Up`, `Turning Ramp Up 0/1`) | RS, mouse | Repeating Soft Press | Works, keep |
| `Steering \| LS: Entry Point` | LS, D-pad | Inverted edge, repeating, removes itself | Ruled out by decision 19 |
| `Steering \| LS: Tap Cover`, `LS: Double Tap Cover` | LS, D-pad | Inverted edge, repeating cleanup | Ruled out |
| `Steering \| LS Down: Modifier 0`, `LS Up: Modifier 1` | LS, D-pad | Inverted edge opens the Double Tap window | Ruled out |
| `Steering \| LS Up/Down: Double Tap` | LS, D-pad | Inverted edge, chorded 150 ms | Ruled out |

Every Steering row uses an inverted outer-ring bind at radius 6553 (about
20%) on a D-pad stick whose dead zone is 13276 (about 40%). Steering's
native acceptance is still pending. Steering is set aside for now (author,
round nine); these rows are the list to come back to.

**Recipes for a D-pad stick:**

| Recipe | Status |
|---|---|
| Inverted edge with a repeating bind | Doesn't work (decision 19) |
| Deflection chord on the owner button, with a repeating removal | Doesn't work (decision 20, manual test) |
| Normal outer edge, Release activator | Reliable per the author; used by the guards (decision 21) |

Still on the deflection chord: Base's protected-entry chord on Start and
Select, which the guards replace, and Steering's W exit clock.

## 10. Open questions

None from the author's side. Both of round twelve's questions are settled
(decisions 27 and 28).

Deferred with Steering: how `Steering | LS: Entry Point` and the Steering
modifier helpers detect the left stick's centre (§9). Steering's W exit clock
uses a deflection chord; decision 25 doesn't break it, because releasing W
releases the bound input.

Settled:

- The 2.5 s hold exit stays and extends to S (decision 2). The exit gesture
  is any menu button plus any stick click (decision 8).
- Other buttons held through the gesture are out of scope (decision 3).
- Modifier 2 isn't reachable inside a transition (decision 4, §4).
- `Gyro` is excluded from the exit rule (decision 9).
- Steering survives a plain menu press (decision 10).
- No back-out inside a transition (decision 11).
- The guards' menu buttons never send a key. A recentre removes only that
  stick's guard, detected by the outer edge's Release (decisions 12, 21).
- Entry Points own the clicks with both sticks as D-pads, and Fn inherits
  them (decisions 13 and 15). A second pair of Entry Points serves stateful
  layers, and the guards are reusable (decisions 16 and 17). The Fn delay moves to 200 ms, tentatively (decision 14).
- Clearing the menu family on the click also ends the Fn stick punctuation on
  that stick. Nothing is lost, because the same punctuation is available in
  the Fn layer without clicking.

## 11. Next steps (not started)

- Build it: [implementation plan](2026-10-01-stateful-transitions-implementation.md).
- Manual Deck tests for the guard recipe: items 1 and 3 in §8.
- Add the transition test once the structure is built.
- Come back to Steering's left-stick centre detection (§9).

All tracked in [todos](../todos.md#stateful-layer-transitions).

## 12. Plan review (author, 2026-10-01)

The author reviewed the implementation plan the same day. These decisions
continue the numbering in §2 and replace the earlier ones named. The binds
are in the [implementation plan](2026-10-01-stateful-transitions-implementation.md#review-decisions-author-2026-10-01).

37. **Steering's `LS: Tap Cover` follows the L1 and R1 pattern.** It is added
    only inside Modifier 0 and 1: by the entering direction (Any-driver
    chord, 250 ms, with the 300 ms reset), by left and right together with A
    and D, and by a mapped button. Never by a driver press, and not when
    entering or leaving Modifier 2. *Replaces the edge-carried hold and the
    blocked entering direction in decisions 33 and 34.*
38. **The W and S layers add Modifier 1 and 0 with a repeating bind.**
39. **The Steering Double Tap windows bind everything themselves.** Own
    direction to the Double Tap Cover; the opposite direction only removes
    the window; left and right are plain A and D; both drivers send W and S
    and their Release removes the window first, then the family, leaving
    `Steering`. No chords and nothing inherited. *Completes decision 35.*
40. **Steering may sit under the two menu Double Tap windows,** which bind
    left-stick up and down as plain W and S. *Drops the 90.6 rule that
    Steering never reaches an Always On window.*
41. **The menu buttons keep their repeating presses in `Steering`.** The
    clean-entry rule is reworded to allow a repeating Entry Point add.
42. **The Entry Points only add Fn; Backspace and Enter live in Fn alone.**
    The Entry Point's own key was a leftover of the 90.9 overlay removal.
    The held-input rule covers the layer API only, not key outputs.
43. **A bump of the other menu button in a transition is accepted** (the
    consequence already listed under decision 26).
44. **Two stick guards and one menu Tap Cover.** A guard behaves like the
    Entry Point for the held menu button, except that the hold brings in the
    Tap Cover where the Entry Point brings in Fn. Its menu release still
    opens the Double Tap window, and a thumb lift applies the Tap Cover and
    clears that stick's trio. One Tap Cover serves both menu sides, like
    `L1&R1: Tap Cover`. One new layer, 70 in total. *Replaces the guard's
    "release only cleans up, no key" in decision 21 and §8, and the matching
    line in §10.*
45. **With a stick out, a bump of the other menu button types its key.**
    Accepted; the alternatives (a fourth bind, or disabling the same-side
    button) were considered and dropped.
46. **Soft pull stays on at full pull,** so the alternative layout's
    All-chords use the soft-pull bits alone, as its existing chords do.
