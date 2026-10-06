# Stateful layer transitions

**Status:** design agreed with the author on 2026-10-01, and revised in the
plan reviews the same day (decisions 37 to 46 in the brainstorm record).
**Built in 90.10** for both layouts
([build record](../findings/2026-10-01-stateful-transitions/README.md)).
`Cursor Gyro` was added in 90.21
([build record](../findings/2026-10-03-cursor-gyro/README.md)) and `Gamepad`
in 90.22 ([build record](../findings/2026-10-03-gamepad/README.md)), so all
four gestures are taken.
**Rests on two assumptions that aren't verified:** A26 and A8 in
[Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md), the two [Deck gates](#steerings-left-stick-and-the-deck-gates) below. The decisions and the options that were rejected
are in the [brainstorm record](../plans/2026-10-01-stateful-layer-transitions.md),
and the build steps are in the
[implementation plan](../plans/2026-10-01-stateful-transitions-implementation.md).

This is the structure every stateful layer enters and leaves through. A new
stateful layer has to fit it; see [the checklist](#adding-a-stateful-layer)
and [Layer Definition of Done §11](Layer%20Definition%20of%20Done.md#11-stateful-layers).

## Purpose

A stateful layer remaps buttons the player is holding to reach it. The
transition makes sure the two controls of the gesture, a menu button and a
stick click, are **both released before the stateful layer is live**, and the
same on the way out. Otherwise the new layer sees a held button and sends an
input the player never meant.

Only those two controls count. Any other button the player happens to hold is
out of scope.

## Gesture map

| Gesture | Destination | Built |
|---|---|---|
| Menu Right + LS click | Steering | Yes |
| Menu Left + RS click | `Cursor Gyro`, with `Gyro` underneath | Yes, 90.21 |
| Menu Right + RS click | `Gamepad` | Yes, 90.22 |
| Menu Left + LS click | `Gamepad` | Yes, 90.22 |

That is the full capacity: four gestures, all taken since 90.22.

**Inside a stateful layer, every one of the four gestures clears instead.**
It removes the stateful layer and everything above Base except `Gyro`.
`Gamepad` does it without Entry Points: see [exceptions](#exceptions).

## The flow

```
Base: menu button press
  └─ Menu Entry Point ................... (1) holds the stick-click binds
       ├─ stick out ──► LS / RS Stick Guard    (2) no Fn while a stick is out
       │                └─ held past the delay, or thumb lifted ──► menu Tap Cover
       ├─ held past the Fn delay ──► Fn Layer  (inherits the click binds)
       └─ stick click RELEASE ──► clear the menu layers, add the Transition
            └─ Transition ............... (3) blocks every layer entry
                 └─ menu button RELEASE ► remove the Transition,
                                          add the destination (4)
```

The stick click is released first and the menu button second. Both are up at
the commit, in a fixed order, with nothing to count. Every step uses
behaviour that is already established: a Release fires on a layer that was
added over a held button.

Letting go of the menu button first cancels. No transition is added, and the
menu release is an ordinary one.

## The layers

### (1) Menu Entry Points

They hold the transition binds, so the layer that adds an Entry Point decides
where the clicks lead.

| Entry Point | Added by | LS click release | RS click release |
|---|---|---|---|
| `Menu Left: Entry Point` | Base, `Gyro` | Transition 0 | Transition 1 |
| `Menu Right: Entry Point` | Base, `Gyro` | Transition 1 | Transition 0 |
| `Stateful \| Menu Left: Entry Point` | `Steering` with no driver held, `Cursor Gyro` | Transition 2 | Transition 2 |
| `Stateful \| Menu Right: Entry Point` | `Steering` with no driver held, `Cursor Gyro` | Transition 2 | Transition 2 |

- **Both sticks are D-pads in every Entry Point.** The right stick copies the
  left stick's setup with empty directions, so it is dead while a menu button
  is held. This is what lets the Fn layers inherit the click binds: a
  different source mode would block the inheritance.
- **The click binds are Release activators.** Binding them replaces the whole
  input, so Base's Q and E don't fire with a menu button held.
- **The Fn layers bind no stick click.** They inherit both from the Entry
  Point underneath.
- **The other menu button only adds Fn** (author, 2026-10-01). Backspace and
  Enter are typed by the Fn layers alone, as before the menu split. The
  Entry Point's own key from 90.9 goes away.
- **Since 90.28 that is two pairs of Fn layers.** Under Base's Entry Points
  the Fn layer's bind for the other menu button adds the chorded chain's
  Entry Point on every press: a tap types Enter or Backspace from the chain's
  window, a double tap and hold holds it, and a 200 ms hold enters
  `Menu Keys`. The `Stateful |` Entry Points add their own copies,
  `Stateful | Menu Left: Fn Layer` and `Stateful | Menu Right: Fn Layer`,
  which type the key at once, as this paragraph describes
  ([record](../findings/2026-10-04-menu-chain-and-window-pads/README.md)).
- **Fn delay:** 200 ms with a 250 ms repeating reset (tentative; 300 and 350
  until 90.9). The reset keeps firing on the held button and restarts the Fn
  timer, so Fn always arrives on a continued hold.
- **Stateful layers share one pair** (author, 2026-10-03). `Cursor Gyro`
  reuses Steering's two Entry Points, renamed `Stateful | …` in 90.21. They
  differ from Base's in the click targets and in typing W and S on stick up
  and down.

### (2) Stick guards

Two layers, split by stick, shared by both menu sides and every Entry Point:
`Menu Buttons: Left Stick Guard` and `Menu Buttons: Right Stick Guard`. With
the one menu Tap Cover they replace the protected
`Steering | Menu …: Entry Point` and `… Tap Cover` layers.

**A guard behaves like the Entry Point for the menu button that is held**
(author, 2026-10-01). The only difference is what the hold brings in: the
menu Tap Cover where the Entry Point would bring in Fn.

| | Left-stick guard | Right-stick guard |
|---|---|---|
| Added by | Entry Point's LS edge, repeating | Entry Point's RS edge, repeating |
| Own stick | Normal outer edge; its **Release** removes this guard | Same |
| Other stick | Unbound, inherits the Entry Point's edge | Same |
| Stick clicks | Unbound, inherits the transition binds | Same |
| Menu button release | Opens that button's Double Tap window, as in the Entry Point | Same |
| Menu button held 200 ms | Adds the menu Tap Cover, with the 250 ms repeating reset | Same |
| Stick touch release | Adds the menu Tap Cover, then clears that stick's trio | Same |
| Stick touch, no menu button held | The recovery: removes both guards, the menu Tap Cover and the Entry Points | Same |

- Both menu buttons have the same three binds, so one guard serves both menu
  sides.
- The guards stack. With both sticks out both are up, and releasing a stick
  removes only its guard.
- When the last guard comes off before the Tap Cover has landed, the player
  is back in the Entry Point, and Fn follows through the repeating reset.
- Both sticks use the D-pad edge radius (4915 today: engages near 25% of
  travel, releases near 5%). Guard and Entry Point use the same radius.

**The menu Tap Cover** is one layer for both menu sides, built like
`L1&R1: Tap Cover`:

- Either menu button: the press does nothing, and the release cleans up (the
  cover, both guards, the Entry Points). No key and no window.
- It binds both stick edges, so no guard can be added on top of it: an empty
  block until 90.23, and its cleanup function since 90.24 (R170).
- Both stick touches are its own since 90.23: the guards' recovery and chord,
  and a Release that clears that stick's trio. Before that it inherited them
  from the guard, and a pad layer between the two lost the right-thumb lift
  ([record](../findings/2026-10-04-tap-cover-stick-touches/README.md)).
- Once it has landed it stays until the menu button is released, also when
  the stick recentres.

### (3) Transition layers

| Layer | Select (Menu Left) release | Start (Menu Right) release | Built |
|---|---|---|---|
| `Transition Set 0`, same-side gestures | `Gamepad` | `Gamepad` | 90.22 |
| `Transition Set 1`, cross gestures | `Gyro`, then `Cursor Gyro` | Steering | 90.10; Select since 90.21 |
| `Transition Set 2`, clear | Clear, keeping `Gyro` | Clear, keeping `Gyro` | 90.10 |

- The titles follow these numbers since 90.22. From 90.10 to 90.21 the clear
  had the title `Transition Set 0`; it kept its place in the layer list, so
  no runtime ID moved, and the same-side transition was appended.
- `Transition Set 0` is a copy of `Transition Set 1`. Only the two menu
  Releases differ.
- **Nothing can be entered from a transition.** Every input that would add a
  layer underneath is bound in the transition, and gyro and trackpads are
  disabled. Until 90.23 those inputs were empty blocks. Since 90.24 each holds
  the transition's cleanup function (R169 to R171): an empty chord with either
  menu button, beside a repeating removal of the transition. With a menu
  button held, which is the only valid state, the input still does nothing.
  The modifier pair no longer scrolls. Outputs that add no layer may pass
  through.
- Both layouts get identical transition layers. The modifier and firing
  pairs all hold that cleanup, so there is nothing to mirror.
- A transition is an Owner for the definition of done: it binds both
  stick-touch releases. Its recovery for a missed release is the next stick
  touch, stick push, bumper press or trigger pull, which removes it, or the
  next tap of either menu button, whose Release commits it. From 90.10 to
  90.23 only the menu tap ended it.

### (4) The destination

- The commit is one array: remove the transition and whatever the
  destination replaces, then add the stateful layer last. Until 90.32
  Steering's commit also added its Entry Guard; since 90.33 Steering's own up
  and down bring the fallback guard in, at entry too.
  `Cursor Gyro`'s commit adds `Gyro` first, so the layer always sits on it;
  if `Gyro` is already on, that add does nothing.
- **Every transition beeps and gives a high haptic pulse on its menu
  release** (author, 2026-10-02), whether it enters a stateful layer or
  clears. The Release has `haptic_intensity` 3, and one layer command
  carries the beep flag: the stateful layer's `add_layer`, or the
  transition's own `remove_layer` when nothing is added. No on-screen
  notification: the command ends in `0 1`, the name flag and then the beep
  flag (A49). Until 90.28 the layouts wrote `1 0`, which shows the name and
  doesn't beep.
- At entry the stateful layer has no Release or delayed binding on Start or
  Select. A repeating press that adds its Entry Point, like Base's, is
  allowed (author, 2026-10-01).

## Rules

Their registry rows are R157 to R163 in the
[Layer Definition of Done §11](Layer%20Definition%20of%20Done.md#11-stateful-layers):
rule 1 here is R157, rule 3 is R160, rule 4 is R158, and rule 6 is R111 and
R112.

1. **Every stateful layer is entered and left through a transition**, apart
   from the exceptions below. Stateful layers never add each other directly.
   A stateful layer may have an extra exit of its own, but it always keeps
   the menu-plus-click clear and the Modifier 2 clear.
2. **Only the gesture's two controls have to be released.**
3. **No layer can be entered from a transition.**
4. **Inside a stateful layer, any menu button plus any stick click clears.**
5. **Menu buttons inside Steering:**
   - No driver held: Steering's own Entry Points, with the normal menu flow.
     Steering stays underneath.
   - W or S driver held: Start is Tab and Select is Escape. Plain keys, no
     menu flow.
   - Steering Modifier 0 to 2: the same keys as the normal Modifier 0 to 2.
6. **Don't build on these**
   ([runtime rules](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)):
   - a chord handing over to another activator when the chord button is
     released (chords latch)
   - an inverted edge of a D-pad stick adding or removing a layer. One that
     only sends output is fine

## Exceptions

| Exception | What it does |
|---|---|
| Modifier 2 clear | Both modifiers together (bumpers in default, triggers in alternative) clear everything to Base, including `Gyro`. No transition. It is the fallback from any state. In Steering's fallback guard the pair are the Gyro modifiers, so since 90.33 the `Gyro \| … Modifier 2` quick tap removes `Steering` and the guard too, with the beep |
| Steering's fallback guard (90.33) | Not an exit. With no driver held, stick up or down adds `Steering \| LS: Fallback Guard` with a strong pulse: at once since 90.34, after 100 ms in 90.33. Since 90.34 Steering base reads the left stick four ways, so a diagonal counts as one direction, and leaves both stick edges open, so turn assist runs there and in the guard and is off only while a driver is held ([record](../findings/2026-10-05-steering-four-way-and-open-edges/README.md)). Since 90.35 the two swap places: the bind that adds the guard removes `Steering`, and each bind that removes the guard adds `Steering` first, because the guard's eight-way stick did not take effect over the four-way one on the Deck. The guard carries `Steering`'s Start, Select and right pad itself ([record](../findings/2026-10-06-steering-fallback-swap/README.md)). It types W and S and stays when the stick is let go. In it, each of the modifier pair adds its Gyro modifier while the left stick is out, and removes the guard, with a pulse, when the stick is at centre; the button then drives. Start and Select are Steering's own, so the menu-plus-click clear works from there. The author's design of 2026-10-04 and 2026-10-05, after the July layout ([record](../findings/2026-10-05-steering-fallback-guard/README.md)). From 90.11 to 90.32 the fallback was an exit: holding W or S for a time and letting go left Steering ([90.31 record](../findings/2026-10-04-fallback-window/README.md), [90.11 record](../findings/2026-10-02-steering-fallback-hold/README.md)) |
| `Cursor Gyro`'s both-sticks exit | Pushing both sticks out about a quarter removes `Cursor Gyro` and nothing else; `Gyro` stays. No transition. It is only in `Cursor Gyro`: a layer on top that binds the stick edges (a held modifier, a held menu button, a window) answers instead, and the exit follows when that layer goes if the sticks are still out (author, 2026-10-03) |
| `Cursor Gyro`'s entry | Its commit also adds `Gyro`. Leaving by the menu-plus-click clear or by both sticks therefore ends in `Gyro`, also when the player came from Base |
| `Gamepad` and the Modifier 2 clear | The Modifier 2 quick tap does not leave `Gamepad`: the bumpers and triggers are gamepad buttons there (author, 2026-10-03). The one way out is a menu button held plus a stick click |
| `Gamepad`'s exit | It has no Entry Points. Each stick click has a chord on Start or Select being held that runs the Entry Points' clear list and adds `Transition Set 2`. So the clear is entered at the click's **press**. The menu button's Release in the transition ends it as usual. If the menu button is let go before the click, Base is live under a held click and may type one Q or E (A11) |
| `Gamepad`'s Start and Select | They use Steam's own Double Press and Long Press, the one exception to R108 (author, 2026-10-03): a tap sends the button after the Double Press time, a double press holds it, a hold sends nothing. It is safe only because `Gamepad` is closed: it binds every input, so no layer can be added over it (R168). Rests on A43 to A45 |
| `Gyro` | Entered and left by the uncovered Modifier 2 release. It doesn't remap the controls that toggle it. The menu-plus-click clear leaves it on |
| `Menu Keys`, the menu stateful layer (90.25) | Doesn't use this structure. Both menu buttons held for 200 ms enter it, from Base or `Gyro`, through a chorded Entry Point that the Fn layer adds on every press of the second button (90.28); both sticks out, or a stick out plus a face button or D-pad direction, leave it. Only its menu-plus-click exit goes through the clear transition, by a chord on the stick clicks as in `Gamepad` ([record](../findings/2026-10-04-pad-bumps-and-menu-keys/README.md)) |

## Adding a stateful layer

All four gestures are taken since 90.22, so a new stateful layer has to
replace one. The list is kept for that.

- [ ] Its gesture is one of the four in the [gesture map](#gesture-map), and
      the map above is updated.
- [ ] The Base Entry Point for that menu side sends the click's Release to
      the right transition, and that transition's menu Release adds the new
      layer.
- [ ] It has Entry Points whose click releases both lead to Transition 2, and
      its own menu press adds them.
- [ ] Transition 2 and the Modifier 2 clear both remove it and its helpers.
- [ ] It has no Release or delayed binding on Start or Select at entry. A
      repeating press that adds its Entry Point is allowed.
- [ ] Nothing in it depends on a chord hand-over or a D-pad centre bind.
- [ ] Both layouts are changed.
- [ ] Its commit beeps and pulses like every other transition release: the
      beep flag on its `add_layer` (`0 1`, A49) and `haptic_intensity` 3 on
      the Release.
- [ ] The transition test and the scenario tests are updated
      ([definition of done](Layer%20Definition%20of%20Done.md#10-ship-it), R154 and R165).

## Accepted consequences

- The camera is dead while a menu button is held.
- With a stick out, Fn can't be reached. A quick menu tap still types Tab or
  Escape through the Double Tap window; a 200 ms hold or a thumb lift makes
  the release silent.
- With a stick out and one menu button held, a bump of the other one types
  its key, because a guard binds both menu buttons the same way.
- Under the menu Tap Cover, a bump of the other menu button removes the
  cover while the first button is still held. It returns within about
  200 ms; a release inside that gap types its key.
- Steering can sit under the two menu Double Tap windows. They bind
  left-stick up and down as plain W and S, so no fallback guard comes on
  during the window.
- The clear happens at the stick click's release, not its press. `Gamepad`
  is the exception: its exit chord fires at the press.
- In `Gamepad` a single Start or Select tap arrives late by the Double Press
  time (200 ms). The pad clicks send Select and Start at once.
- In Transition 1 the two menu buttons lead to different places, so a stray
  tap of the other one commits to the other destination. The first button is
  then still held over Base, and its repeating press starts a fresh menu
  hold (confirmed by the author, 2026-10-01).
- A stick click held from before the menu press counts as part of the
  gesture.
- Modifier 2 can't be reached from inside a transition. The transition ends
  when the menu button is released.

## Steering's left stick and the Deck gates

Steering's part below is built in 90.10. The Deck gates at the end of this
section are still open: they are assumptions A26 and A8 in
[Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md), which holds the procedure for each.

- **Steering's left-stick centre detection.** `Steering | LS: Entry Point`,
  the two LS covers, Modifier 0 and 1 and the two Double Tap windows use an
  inverted edge on a D-pad stick until 90.9, which rule 6 rules out. Since
  90.10 (author, 2026-10-01) they use the same recipe as the stick guards.
  - **A normal, generous outer edge whose Release ends the modifier.** Once
    Modifier 1 is entered by holding north, the edge keeps it in place. The
    player can roll to East and West for A and D and stay in the modifier.
    It ends when the stick comes back to centre and the edge releases.
  - **The edge Release clears the modifier and adds its Double Tap window**,
    which is what the inverted-edge press does today.
  - **The entering direction carries the hold** that applies the Tap Cover
    (author, 2026-10-01, replacing the earlier idea of moving it to the
    edge). North in Modifier 1 and south in Modifier 0 have a chord on Any
    driver with a 200 ms delay that adds the Tap Cover, and the 250 ms
    repeating reset (250 and 300 until 90.25). This is the pattern `L1: Modifier 0` and
    `R1: Modifier 1` use. The edge has only its Release.
  - **Left and right keep A and D and add the Tap Cover in the same bind.**
    Rolling sideways uses up the tap at once, so there is no wait for the
    hold, and the modifier stays.
  - **The Tap Cover is only ever added from inside Modifier 0 or 1.** The
    driver press in `Steering` adds the W or S layer alone, and entering or
    leaving Modifier 2 adds no `LS: Tap Cover`. So the cover is always added
    with the stick out, and its edge Release can always remove it.
  - **The W and S layers add the modifier with a repeating bind** on stick
    up and down, replacing the 5 ms delayed add and its reset. A stick that
    is already held when the driver goes down enters the modifier at once.
  - **The opposite direction only cleans up.** South in Modifier 1 removes
    Modifier 1 and nothing else, and the reverse. It never adds the other
    modifier itself (author rule). The player is back on the W or S layer,
    and Modifier 0 comes from that layer's own bind.
  - **Every cleanup in Modifier 0 and 1 is guarded by two All-chords**
    (author rule): left-stick deflection plus the left driver, and left-stick
    deflection plus the right driver. The drivers are the bumpers in the
    default layout and the triggers in the alternative. The modifier is valid
    only while the stick is out and a driver is held, so the repeating
    cleanup fires only when neither chord matches. Whether the guards are
    interruptible is undecided.
  - Budget: two guard chords plus the repeating cleanup are three entries.
    Today's Steering modifiers spend two chords on the key and on adding the
    Tap Cover; those have identical settings, so each guard chord can carry
    both in one array.
  - This replaces the earlier idea of ending on the direction's own Release,
    which dropped the modifier on every roll to the side.
  - It changes one row of the steering behaviour matrix: Up to sideways no
    longer removes Modifier 1.
  - It rests on gate 2 below, because the modifier is added while the stick
    is already out.
  - **The two `Steering | LS …: Double Tap` windows become Always On
    windows** (author, 2026-10-01), like the bumper ones. A second press in
    the same direction adds the repeating-scroll cover, as today. The
    timeout, which sends the single scroll and removes the window, moves to
    an Always On action. Today it is a delayed chord on an inverted edge at
    full radius, read while the stick is at centre; that was an oversight in
    the first build. The windows then follow
    [Definition of Done §9](Layer%20Definition%20of%20Done.md#9-always-on-layers),
    and the Always On windows go from seven to nine.
  - **What a Steering window binds** (author, 2026-10-01). It binds all of
    this itself, so nothing that changes layers is inherited:
    - its own direction removes the window first and adds the Double Tap
      Cover
    - the opposite direction only removes the window; the other modifier
      then comes from the W or S layer's own bind
    - left and right are plain A and D, and the window stays
    - both drivers send W and S, and each Release removes the window first
      and then the family. `Steering` stays. There are no chords, so
      Modifier 2 can't be entered during the window
  - **`LS: Double Tap Cover` ending adds no Tap Cover,** like
    `L1: Double Tap Cover`.
- **Since 90.33 there is no Entry Guard.** `Steering | LS: Fallback Guard`
  took its place and is added by `Steering`'s own up and down, not by the
  entry. The points below are the 90.10 design.
- **`Steering | LS: Entry Point` stays** (author, 2026-10-01). Only the
  Steering entry adds it, and it has nothing to do with Modifier 0 and 1,
  which are entered straight from the W and S layers. Its job: W carried
  into Steering on the stick would start the hold exit clock at once, so the
  layer rebinds the stick as plain WASD with no clock until the stick
  recentres or a driver is pressed.
  - It is renamed `Steering | LS: Entry Guard` (author, 2026-10-01); the old
    name read like an entry point for the modifiers.
  - It ends on an inverted edge today, so it moves to the edge Release like
    the modifiers and depends on gate 2. If Steering is entered with the
    stick centred, the edge isn't out, so the layer stays until the first
    push and return or a driver press.
- **Deck gates.** Two behaviours have never been tested on their own. The
  guards rely on both; the Steering recipe above relies on the second. The
  author expects both to hold, and the implementation plan assumes they do:
  1. **A stick input inherited from the middle of the stack.** Under a guard
     the stack is Base, Entry Point, guard. The click bind is in the Entry
     Point and the guard doesn't bind the click. A
     [2022 community report](https://steamcommunity.com/app/353370/discussions/0/3468361193665969286/)
     says sticks take inputs only from the top layer and Base. If so, a click
     under a guard would send Base's Q and never reach the transition. The
     Fn layer over an Entry Point has the same shape.
  2. **An edge Release in a layer added while the stick was already out.**
     The guard is added because the stick is out, and its only edge bind is
     a Release. If the Release needs the layer to have seen the push, the
     guard never comes off until the menu button is released.
- **Two more behaviours are relied on and untested in isolation:**
  1. **A key output on an input held when its layer was added.** Fn's
     Backspace and Enter need it once the Entry Points stop typing the key,
     and so do W and S in a Steering window. The author's experience is that
     it works; the held-input rule covers the layer API only
     ([scope note](Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes)).
  2. **A key output after a removal exposes it under a held input.** W and S
     need it when a Steering window times out.
  3. **A running delay doesn't fire once another layer binds its input.**
     Established (author, 2026-10-01): the layer that binds the button eats
     the delayed action. So a guard that lands inside the Fn delay cancels
     it, and Fn can't land on a guard. The Entry Point's edge chord repeats
     every 50 ms so the guard lands in time when a stick is already out.
  4. **A delay starts again when a removal exposes it under a held button.**
     When a guard comes off, Fn is expected to follow. The same holds for a
     guard's Tap Cover delay after a second guard on top of it comes off.

## Tests

[test_gamepad.py](../tests/test_gamepad.py) asserts, on the 90.22 build, all
four gestures, the three transitions and their feedback, `Gamepad`'s map,
its native menu activators, its exit chord, and that it is closed (R168).
[test_cursor_gyro.py](../tests/test_cursor_gyro.py) asserts `Cursor Gyro`'s
binds, its entry, its three exits and the renamed Entry Points on the 90.21
build. [test_stateful_transitions.py](../tests/test_stateful_transitions.py) asserts
for both layouts: each Entry Point's click-release targets, each transition's
two menu-release destinations, that the transitions leave no layer-adding
input unblocked, that the Fn layers and guards bind no stick click, the
guards' and the Tap Cover's binds, and Steering's left-stick recipe and
windows, on the 90.10 build. The later builds have their own test files,
above.
