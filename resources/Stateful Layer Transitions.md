# Stateful layer transitions

**Status:** design agreed with the author on 2026-10-01, and revised in the
plan review the same day (decisions 37 to 46 in the brainstorm record).
**Not built yet.**
Both layouts still carry the earlier `Transition Set 0/1` and the protected
`Steering | Menu …` layers. The decisions and the options that were rejected
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
| Menu Left + RS click | Stateful Cursor Gyro | No |
| Menu Right + RS click | Gamepad | No |
| Menu Left + LS click | Gamepad | No |

That is the full capacity: four gestures. Until a destination is built, its
gesture clears to Base, keeping `Gyro`.

**Inside a stateful layer, every one of the four gestures clears instead.**
It removes the stateful layer and everything above Base except `Gyro`.

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
| Steering's Menu Left Entry Point | `Steering`, no driver held | Transition 2 | Transition 2 |
| Steering's Menu Right Entry Point | `Steering`, no driver held | Transition 2 | Transition 2 |

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
- **Fn delay:** 200 ms with a 250 ms repeating reset (tentative; today 300 and
  350). The reset keeps firing on the held button and restarts the Fn timer,
  so Fn always arrives on a continued hold.
- **Each later stateful layer may need its own pair** of Entry Points like
  Steering's. Decide when it is built.

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
- Both stick edges are empty, so no guard can be added on top of it.
- Once it has landed it stays until the menu button is released, also when
  the stick recentres.

### (3) Transition layers

| Layer | Select (Menu Left) release | Start (Menu Right) release | Built |
|---|---|---|---|
| Transition 0, same-side gestures | Gamepad | Gamepad | With Gamepad |
| Transition 1, cross gestures | Stateful Cursor Gyro | Steering | First |
| Transition 2, clear | Clear, keeping `Gyro` | Clear, keeping `Gyro` | First |

- The layer titles stay `Transition Set 1` (cross) and `Transition Set 0`
  (clear) for now. They get sorted out when Transition 0 arrives with
  Gamepad.
- Two transition layers are enough until Gamepad exists; the same-side
  gestures use the clear until then.
- **Nothing can be entered from a transition.** Every input that would add a
  layer underneath is blocked with an empty binding, and gyro and trackpads
  are disabled. Block, don't replace: the modifier pair no longer scrolls.
  Outputs that add no layer may pass through.
- Both layouts get identical transition layers. The modifier and firing
  pairs are all blocked, so there is nothing to mirror.
- A transition is an Owner for the definition of done: it binds both
  stick-touch releases. Its recovery for a missed release is the next tap of
  either menu button, whose Release ends the transition. It has no
  stick-touch or Select-press recovery.

### (4) The destination

- The commit is one array: remove the transition and whatever the
  destination replaces, then add the stateful layer and its entry guard last.
- At entry the stateful layer has no Release or delayed binding on Start or
  Select. A repeating press that adds its Entry Point, like Base's, is
  allowed (author, 2026-10-01).

## Rules

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
| Modifier 2 clear | Both modifiers together (bumpers in default, triggers in alternative) clear everything to Base, including `Gyro`. No transition. It is the fallback from any state |
| Steering's hold exit | Holding W with no driver exits Steering after 2.5 s, warning from 1 s. To be added for S as well |
| Stateful Cursor Gyro's own clear (not built) | Besides the menu-plus-click clear and the Modifier 2 clear, it can be left the same way Temp Cursor Gyro clears, with both sticks deflected. No transition |
| `Gyro` | Entered and left by the uncovered Modifier 2 release. It doesn't remap the controls that toggle it. The menu-plus-click clear leaves it on |
| Menu stateful layer | Will not use this structure. It stays in the [todos](../todos.md#menu-stateful-layer) as its own design |

## Adding a stateful layer

- [ ] Its gesture is one of the four in the [gesture map](#gesture-map), and
      the map above is updated.
- [ ] The Base Entry Point for that menu side sends the click's Release to
      the right transition, and that transition's menu Release adds the new
      layer. Transition 0 is created if this is Gamepad.
- [ ] It has Entry Points whose click releases both lead to Transition 2, and
      its own menu press adds them.
- [ ] Transition 2 and the Modifier 2 clear both remove it and its helpers.
- [ ] It has no Release or delayed binding on Start or Select at entry. A
      repeating press that adds its Entry Point is allowed.
- [ ] Nothing in it depends on a chord hand-over or a D-pad centre bind.
- [ ] Both layouts are changed.
- [ ] The transition test and the Deck checklist are updated.

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
  left-stick up and down as plain W and S, so Steering's hold-exit clock
  doesn't run during the window.
- The clear happens at the stick click's release, not its press.
- In Transition 1 the two menu buttons lead to different places, so a stray
  tap of the other one commits to the other destination. The first button is
  then still held over Base, and its repeating press starts a fresh menu
  hold (confirmed by the author, 2026-10-01).
- A stick click held from before the menu press counts as part of the
  gesture.
- Modifier 2 can't be reached from inside a transition. The transition ends
  when the menu button is released.

## Not settled

Steering's part below is decided in direction but not built.

- **Steering's left-stick centre detection.** `Steering | LS: Entry Point`,
  the two LS covers, Modifier 0 and 1 and the two Double Tap windows use an
  inverted edge on a D-pad stick, which rule 6 rules out. Direction (author,
  2026-10-01; not built): the same recipe as the stick guards.
  - **A normal, generous outer edge whose Release ends the modifier.** Once
    Modifier 1 is entered by holding north, the edge keeps it in place. The
    player can roll to East and West for A and D and stay in the modifier.
    It ends when the stick comes back to centre and the edge releases.
  - **The edge Release clears the modifier and adds its Double Tap window**,
    which is what the inverted-edge press does today.
  - **The entering direction carries the hold** that applies the Tap Cover
    (author, 2026-10-01, replacing the earlier idea of moving it to the
    edge). North in Modifier 1 and south in Modifier 0 have a chord on Any
    driver with a 250 ms delay that adds the Tap Cover, and the 300 ms
    repeating reset. This is the pattern `L1: Modifier 0` and
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
     The Entry Point stays under a guard, with its Fn delay possibly
     running. If it fired, Fn would land on the guard.
  4. **A delay starts again when a removal exposes it under a held button.**
     When a guard comes off, Fn is expected to follow.

## Tests

None yet, because the structure isn't built. When it is, a test asserts for
both layouts: each Entry Point's click-release targets, each transition's two
menu-release destinations, that the transitions leave no layer-adding input
unblocked, and that the Fn layers and guards bind no stick click. It is
extended each time a stateful layer is added, until all four gestures are
taken.
