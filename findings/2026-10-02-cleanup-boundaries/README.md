# Cleanup boundaries: what a cleanup function removes

**Status:** the rule set, 2026-10-02. The author answered every decision the
same day ([answered](#answered-author-2026-10-02)) and approved the fixes. The
Cleanup audit checks these rules and 90.12 applies them
([first run and fix](../2026-10-02-cleanup-audit/README.md)).

The question (author, 2026-10-02): what are the boundaries of a cleanup
function? The working idea was "what's below you that you're responsible for,
and what's above you that you're responsible for", where above means a layer
you apply that removes itself on its own button but has little or no cleanup
of its own.

## Contents

| Section | What it covers |
|---|---|
| [Answer](#answer) | The rules in short, and how well they fit |
| [The one idea behind it](#the-one-idea-behind-it-keeper-and-guard) | Keeper and guard, on the L1 modifier |
| [The rules](#the-rules) | Six rules with examples, revised after the author's answers |
| [Evidence](#evidence) | The measurements, on every snapshot back to the multi-set layouts |
| [Where the layouts differ](#where-the-layouts-differ-from-the-rules) | Five places that don't follow the rules today |
| [The open questions](#how-this-answers-the-open-questions) | What this means for the four questions in Cleanup Functions |
| [Checklist](#checklist-for-a-new-or-changed-layer) | How to apply the rules to a layer |
| [Decisions for the author](#decisions-for-the-author) | Eight answered on 2026-10-02, what they change, and one still open |
| [Method and limits](#method-and-limits) | How it was measured and what it can't see |

## Answer

The author's framing is right, with one condition added to both halves: **the
layer has to be kept alive by the same button the cleanup is guarded by.**

- **Below:** a cleanup removes every layer under it that the same button keeps
  alive. It stops at the first layer that something else keeps alive.
- **Above:** a cleanup removes every layer it put on top that the same button
  keeps alive and that has no cleanup of its own, or only a few. A layer above
  with full cleanup doesn't need you: it removes you, as part of its own
  "below".
- **Never:** a cleanup doesn't remove a layer that another button, a thumb on
  a stick, a timer or a mode keeps alive.

How well this fits the current layouts (90.10, the same in both variants, 261
cleanup functions on 36 of 70 layers):

| | Removed | Left |
|---|---|---|
| Layer below, kept by the same button | 28 | 5 (deliberate, see [differences](#where-the-layouts-differ-from-the-rules)) |
| Layer below, kept by something else | 0 | 17 |
| Layer above, same button, 0 to 4 cleanups of its own | 20 | 0 |
| Layer above, same button, 5 or more cleanups of its own | 0 | 4 |
| Layer above, kept by something else | 10 (all in Steering) | 43 |

In every layout built by hand (the July reference, 90.4 and the four archived
multi-set layouts), no cleanup removes a layer kept by something else: 0 of
418 cases.

## The one idea behind it: keeper and guard

| Term | Meaning | Example |
|---|---|---|
| **Keeper** | What keeps a layer alive. For most layers it's the button whose Release removes the layer (the owner removal) | `L1: Modifier 0`, `L1: Tap Cover` and `L1: Temp Cursor Gyro` all end on the LB Release, so LB is their keeper |
| **Guard** | The buttons whose chords sit beside a cleanup function and suppress it | Every cleanup in `L1: Modifier 0` has a chord with LB |

Other keepers: a thumb on a stick (the `LST` and `RST` layers), a timer (the
Always On windows), a threshold (the ramp layers) and a mode (`Gyro`,
`Steering`).

A cleanup function fires only when its guard buttons are up. That is its
whole evidence: it knows those buttons aren't held, and nothing else. So it
can only speak for layers those buttons keep alive.

Example, `L1: Modifier 0` stuck after a missed release. You press A, LB is
not held, the cleanup fires:

| Layer that can be on the stack | Keeper | Removed? | Why |
|---|---|---|---|
| `L1: Modifier 0`, `Gyro \| L1: Modifier 0` | LB | Yes | The host and its other-mode twin |
| `L1: Tap Cover`, `L1: Temp Cursor Gyro` | LB | Yes | Applied by the modifier, same keeper |
| `R1: Tap Cover` | RB | No | The modifier adds it too (rocking), but RB may still be held |
| `R1: Modifier 1`, `L1!R1: Modifier 2` | RB; both bumpers | No | RB may still be held, and both layers carry full cleanup of their own |
| `L1: Double Tap` | timer | No | A window ends itself |
| `Gyro`, `RST: Entry Point`, `Escape` | mode, thumb, left pad | No | Not LB's |

## The rules

### 1. The guard is the boundary

A cleanup removes only layers whose keeper is inside its guard. The more
buttons the guard has, the more it can remove.

A layer that only exists while another layer's button is held counts as kept
by that button. Steering's left-stick modifiers end when the stick is
released, but they only exist while a driver (W or S) is held, so the
driver's cleanup removes them.

| Host | Guard | Removes |
|---|---|---|
| `L1: Modifier 0` | LB | 4 layers, all LB's |
| `L1!R1: Modifier 2` | LB and RB (either one held suppresses it) | 11 layers: both sides' modifiers, covers and cursors |
| `Menu Left: Fn Layer` | Select and Start on 18 inputs, Select alone on the Start button | 6 layers: itself, both of its Entry Points, both stick guards, the menu Tap Cover |

These are today's lists. [Rule 6](#6-list-only-what-can-be-on-the-stack-with-you)
shortens them: `L1: Modifier 0`'s goes from 4 to 3 and `L1!R1: Modifier 2`'s
from 11 to 6.

### 2. Below: remove down to the first layer you can't speak for

Follow the layers that added you, downward. Remove each one your guard's
buttons keep alive. Stop at Base, a stateful layer, a window, or a layer
another button keeps alive.

- `Menu Left: Fn Layer` removes `Menu Left: Entry Point` (and its Steering
  twin) under it.
- `L1!R1: Modifier 2` removes `L1: Modifier 0` and `R1: Modifier 1`. The
  `Gyro |` variant stops at `Gyro`.
- `L1: Scroll Down` removes nothing below: the layer that added it is the
  `L1: Double Tap` window, and that already removed itself.
- `Steering | R1: W Key` removes the temporary Steering layers and stops at
  `Steering`.

**In one step** (author, 2026-10-02): every layer takes care of itself and
what is below it. A cleanup function doesn't remove only itself and leave the
rest to the layer underneath. A cancellation is different: it has no guard,
also fires while the owner is held, and removes only itself (the cursor's 15
cancel inputs).

The reason for reaching down: a cleanup that removes only itself exposes
another stale layer, and the player needs a second gesture. The author
approved this for the Transition Sets on 2026-09-28
([record](../2026-09-28-left-stick-recovery/CHANGES.md#transition-set-cleanup-depth)).

### 3. Above: remove what you put there that can't clean itself up

A layer above you binds some inputs and leaves the rest alone. On an input it
leaves alone, **your** cleanup is still the one that fires. So if that layer
is stuck, only you can remove it.

- `L1: Tap Cover` binds three inputs. On the other fifteen the modifier's
  cleanup fires, so the modifier removes the cover.
- `L1: Double Tap Cover` binds only LB, so `L1: Scroll Down`'s cleanup removes
  it.
- `Menu Left: Fn Layer` binds every input `Menu Left: Entry Point` has a
  cleanup on. The Entry Point's cleanup can't fire while Fn is on top, so the
  Entry Point doesn't list Fn. Fn's cleanup removes both.

This is the author's test: a layer you apply that has its own owner removal
but no cleanup of its own, or very little. In 90.10, every layer above with
the same keeper and at most 4 cleanups is removed by the layer that applied
it (20 of 20). None with 5 or more is (0 of 4).

### 4. If you bind an input that has a cleanup below, carry it

Steam overrides whole inputs. An overlay that binds an input for its own job
hides whatever cleanup the layer below had on that input. So it carries that
cleanup itself, with the same guard. This is where an overlay's "very little"
cleanup comes from.

| Overlay | Binds | Cleanup it carries |
|---|---|---|
| `L1: Tap Cover` | LB and both stick touches | 2: both stick touches, with the modifier's list plus `Steering \| R1!L1: Modifier 2`, which also adds the cover |
| `L1: Double Tap Cover` | LB | None: it hides no cleanup |
| `L1: Temp Cursor Gyro` | 16 inputs | 2, on the stick edges. The other 15 are cancellations, which remove only the cursor |

Decided on 2026-10-02 and not built: the four Modifier 2 layers bind both
stick touches without carrying the cleanup, and get it.

### 5. What a cleanup never removes

| Kept alive by | Layers | Removed by |
|---|---|---|
| A mode | `Gyro`, `Steering` | Their deliberate exits only (the Modifier 2 quick tap, the menu-plus-click clear) |
| A thumb on a stick | `LST` and `RST` `Entry Point`, `Tap Cover`, `Temporary Gyro` | The stick-touch Release only |
| A timer | The Double Tap windows | Themselves. A cleanup never lists a window: it always clears itself (author, 2026-10-02) |
| Another button | The other side's modifier, cover and cursor | That side's own cleanup |
| Another interaction | Trackpad layers, key layers, ramp layers | Their own exits |

No cleanup function in any single-set snapshot, from the July reference to
90.10, removes a stateful layer or a stick-touch helper.

### 6. List only what can be on the stack with you

**Author, 2026-10-02:** a list doesn't remove a layer that can never be on
the stack at the same time. Unnecessary removals go. This replaces the first
version of this rule, which allowed them.

- **No other-mode twin.** `L1: Modifier 0`'s cleanup doesn't list
  `Gyro | L1: Modifier 0`, and the Gyro variant doesn't list the normal one.
  Checked in both layouts: every binding that turns Gyro on removes all four
  normal modifiers first, every binding that turns it off removes all four
  Gyro modifiers, and neither kind is ever added from the other side. So a
  missed release can't leave the twin behind either.
- **No whole-family list.** `Steering | R1: W Key`'s cleanup doesn't list
  `Steering | L1: S Key`, which is never there with it.
- **A shared layer keeps each layer it can sit on.** `L1: Tap Cover` can be
  on `L1: Modifier 0`, on `Gyro | L1: Modifier 0` or on
  `Steering | R1!L1: Modifier 2`, one at a time. Each can be under it, so
  all three stay in its list. `Menu Left: Fn Layer` keeps both of its Entry
  Points for the same reason.
- **Ordinary releases follow this rule too. A deliberate clear doesn't.**
  Entering a transition and Steering Modifier 2's uncovered release remove
  every layer on purpose and keep their whole lists
  ([examples](#answered-author-2026-10-02)).

How much this is: the cleanup functions of one layout make 1,982 removals,
and 1,016 of them name a layer that is never on the stack with the host (292
are the Gyro or normal twin side, 548 are in Steering's lists, 176 are
others).

**What "never" means has to be checked per removal.** The 1,016 come from
the backward chains, which follow normal sequences without timing. Three
kinds are in there:

| Kind | Example | Drop it? |
|---|---|---|
| Can't be there by construction: another mode, or the other owner | The Gyro twin (292). `Steering \| L1: S Key` in the W Key's list | Yes |
| Not there in a normal sequence, but a timing race could put it there | `Menu Left: Fn Layer` lists the two stick guards and the menu Tap Cover. A guard normally lands before Fn's 200 ms delay ends and cancels it. If both land together, they are on the stack at once | Review each one. 90.10 added these on purpose |
| The chains can't see it | `RTP: Mouse Buttons` on top of `RTP: Circular Scroll`: it is added with `hold_layer`, which the chains don't follow | No, it stays |

## Evidence

One row per layout, from `measure.py summary`. "Expected but left" counts the
cases where a layer can be on the stack with the host, has its keeper inside
the guard, leaves the input alone, and still isn't removed.

| Layout | Cleanup functions | Below, same keeper: removed / left | Below, other keeper: removed / left | Above, same keeper, 0 to 4 cleanups: removed / left | Above, same keeper, 5+ cleanups: removed / left | Above, other keeper: removed / left | Expected but left |
|---|---|---|---|---|---|---|---|
| July reference | 80 | 6 / 5 | 0 / 18 | 12 / 6 | 2 / 0 | 0 / 24 | 110 |
| 90.4 | 207 | 14 / 5 | 0 / 13 | 16 / 6 | 2 / 0 | 0 / 25 | 108 |
| 90.5 | 275 | 40 / 9 | 1 / 22 | 27 / 11 | 6 / 6 | 10 / 29 | 192 |
| 90.7 | 267 | 28 / 7 | 0 / 21 | 22 / 10 | 4 / 4 | 14 / 29 | 192 |
| 90.9 | 267 | 28 / 7 | 0 / 21 | 22 / 8 | 4 / 4 | 14 / 27 | 148 |
| 90.10, both variants | 261 | 28 / 5 | 0 / 17 | 20 / 0 | 0 / 4 | 10 / 43 | 8 |

The four archived multi-set layouts (`measure_multiset.py`) have 250 to 327
cleanup functions each. Every one removes its host, and none removes a layer
with another keeper (0 of 338). Most remove one or two layers. So rule 1 has
always held, and rules 2 and 3 were filled in over time.

**The "expected but left" column lines up with the cleanup problems already
found by hand.** That is the main reason to trust the rule:

| Layout | What the rule flags | What happened to it |
|---|---|---|
| July reference | Transition Sets remove only themselves and leave the menu Entry and Fn layers below | Cleanup audit F7. The author approved the deeper cleanup on 2026-09-28 |
| 90.4 to 90.7 | The Fn layers leave `Menu Right: Enter` and `Menu Left: Backspace` on top | Cleanup audit F1. The two layers were removed in 90.9 |
| 90.5 to 90.9 | The Fn layers leave `Steering \| Menu …: Entry Point` and its Tap Cover below | Noted as "left by mistake, probably" in todos.md on 2026-10-01. Closed in 90.10: the Fn cleanups now remove the Steering Entry Point |
| July to 90.9 | The Fn layers leave a Transition Set that's on top of them | I found no record of this one. Closed in 90.10, where the transitions bind every input |
| 90.10 | Only the cursor's two edge cleanups | Deliberate, see below |

The July figure also has 40 cases among the left-pad key layers, the right-pad
layers and the starred Modifier 2 layers that I didn't trace.

## Where the layouts differ from the rules

Each one now has a decision; see [answered](#answered-author-2026-10-02).

1. **The cursor's two edge cleanups remove only the cursor.** The modifier
   below has the same keeper, so rule 2 says remove it too. This is the
   deliberate "remove yourself, let the layer below finish" pattern
   ([cursor cancellation](../../resources/Steam%20Input%20JSON%20Structure.md#button-overlays-and-inherited-cleanup)).
   It works because the modifier has a repeating cleanup on the same edge.
2. **`RTP: Mouse Buttons`' stick-touch cleanup removes only itself**, although
   `RTP: Circular Scroll` can be under it with the same keeper. Same pattern:
   Circular Scroll's cleanup fires next.
3. **The four Modifier 2 layers bind both stick touches with a Release only.**
   That hides the single modifier's touch cleanup without carrying one (rule
   4). A stuck Modifier 2 is cleaned up by 14 other inputs, but not by
   touching a stick. Definition of Done §5 says a layer that binds a touch
   input includes that input's guarded recovery.
4. **Steering's cleanups list more than the rules need.**
   - Six Steering layers (the two drivers, the two left-stick modifiers and
     the two Modifier 2 layers) each remove the two Steering Double Tap
     windows. No cleanup lists a window in any snapshot up to 90.9. The
     arrays do remove the windows first, as §9 asks, and a window binds every
     input, so in a normal stack these removals can't fire through one.
   - `Steering | R1: W Key`'s cleanup is guarded by RB alone and removes
     `Steering | R1!L1: Modifier 2`, whose keeper is LB. The normal
     `L1!R1: Modifier 2` is guarded by both bumpers instead.
5. **The stick guards' Release removes both Fn layers; their cleanup
   doesn't.** In a normal stack an Fn layer is never there with a guard (the
   guard eats the Fn delay), so the difference has no effect today.

Not a difference, but related: `Menu Left: Escape` and `Menu Right: Tab` bind
9 inputs and have no cleanup function, while `L1: Scroll Down` has 4. The
author accepted that on 2026-09-28 (cleanup audit F2).

## How this answers the open questions

The four [questions for the author](../../resources/Cleanup%20Functions.md#questions-for-the-author)
in Cleanup Functions, with what the measurements suggest. These are proposals
until confirmed.

| Question | Suggested answer | Evidence |
|---|---|---|
| 1. Who belongs to a family: computed or listed? | Computed, by keeper. A layer belongs to the button whose Release removes it, not to whoever adds it | `L1: Tap Cover` is added by `R1: Modifier 1` too, but only LB-guarded cleanups remove it |
| 2. What must a cleanup leave alone? | Everything whose keeper is outside its guard (rule 5) | 0 of 335 in the hand-built layouts |
| 3. Which inputs carry a cleanup? | Observed, not a rule yet: an owner has one on every button-type input it binds, except its own button, cleared inputs and plain outputs. Stick touches vary | `L1: Modifier 0`: 17 of 20 inputs. `L1!R1: Modifier 2`: 14 of 20, no touches. Fn: 19 of 32 |
| 4. Who cleans up a layer two families add? | The side its keeper says. With two keepers, only a cleanup guarded by both | `L1&R1: Tap Cover` (LB and RB) is removed by the Modifier 2 cleanups only |

## Checklist for a new or changed layer

1. **Name its keeper.** Which button's Release removes it? If the answer is a
   thumb, a timer or a mode, no cleanup function ever lists it.
2. **Does it need cleanup functions?** Only on the inputs it binds. An overlay
   that binds one button and hides no cleanup needs none.
3. **Guard:** every button that can validly hold this stack open.
4. **Below:** list each layer under it, down the chain that added it, whose
   keeper is inside the guard. Stop at the first one that isn't.
5. **Above:** list each layer it adds whose keeper is inside the guard and
   that leaves at least one of its cleanup inputs alone.
6. **Other layers' lists:** add the new layer to the cleanup of
   - each layer under it with the same keeper, on the inputs the new layer
     leaves alone (rule 3)
   - each layer that can sit on top of it with the same keeper and has
     cleanup of its own (rule 2)
7. **Check:** `python3 findings/2026-10-02-cleanup-boundaries/measure.py detail <layout>`
   shows "LEFT, expected" for anything steps 4 to 6 missed.

## Decisions for the author

### Answered (author, 2026-10-02)

- **Entering a transition clears the stack first.** Before a Transition Set
  is added, everything below that can be cleared is cleared. 90.10 already
  does this: each of the eight bindings that add a Transition Set removes 69
  of the 70 layers first, `Steering` included, and adds the Transition Set
  last. The one layer left is `Gyro`, by the
  [exception of 2026-10-01](../../resources/Layer%20Definition%20of%20Done.md#11-stateful-layers).
  So a Transition Set has nothing under it to clean up, and needs no cleanup
  function of its own.
- **Modifier 2 gets the cleanup on its stick touches** (was decision 2).
  Decided, not built. It never had one: the four layers bind the touch with a
  Release only in the archived multi-set layout, the July reference, 90.4 and
  90.10, while the single modifiers had the cleanup there in all four. No
  record gives a reason.
- **A cleanup doesn't list a window** (part of decision 4). A window always
  clears itself. Decided, not built: six Steering layers list the two
  Steering windows today.

- **The rule, in the author's words:** every layer takes care of itself and
  what is below it, and of what is above it if it has that responsibility.
  That is rules 2 and 3.
- **A cleanup function cleans up in one step** (was decision 1). The author
  didn't mind two steps and left the choice open; one step is what the rule
  above says, so that is the answer recorded here. Decided, not built.
  - What changes: six bindings per layout. The cursor layers' two edge
    cleanups take the modifier's list (the modifier, its Gyro twin, the Tap
    Cover, the cursor). `RTP: Mouse Buttons`' two stick-touch cleanups also
    remove `RTP: Circular Scroll`. No input gains an entry.
  - Why it's safe: these bindings only fire when the keeper is up (LB, or the
    thumb on the right pad), and then the layer below is stale too.
  - Why it's better: it no longer leans on a binding firing after a removal,
    which is the [unverified held-input rule](../../resources/Layer%20Definition%20of%20Done.md#4-entry),
    and "below, same keeper" becomes a check with no exceptions (33 removed,
    0 left).
  - What stays two steps: the cursor's 15 cancellations (face buttons, D-pad,
    menu buttons, stick clicks, the other bumper). They aren't cleanup
    functions. They have no guard and also fire while LB is held, where
    removing the modifier would be wrong. When the stack is stuck, the first
    press removes the cursor and the modifier's own cleanup on that button
    follows on the repeat.

- **Either bumper protects Steering's Modifier 2 on a stick touch too** (was
  decision 3). Its 12 button cleanups are suppressed while either bumper is
  held; its 2 stick-touch cleanups only by the bumper pressed first. They
  become "either", like the rest. Decided, not built: four bindings per
  layout (triggers in the alternative layout).
  - Normal use doesn't change: with the first bumper held, the cleanup was
    already suppressed.
  - The one case that changes: the first bumper's release was missed and the
    second is still held. A stick touch no longer cleans that up. Letting go
    of the second bumper does.
- **Short lists** (was decision 4). A list names only layers that can be on
  the stack with its host. This is [rule 6](#6-list-only-what-can-be-on-the-stack-with-you).
  Decided, not built.

- **An ordinary release follows rule 6 too; a deliberate clear doesn't.** The
  author: "deliberate clears are different than cleanups", and there is no
  point removing a layer that can't be on the stack. (The second half is how
  I read a dictated sentence; correct it if wrong.) Decided, not built.

  | Kind | Example | Removes today | Can be there | Under rule 6 |
  |---|---|---|---|---|
  | Ordinary release | `L1: Modifier 0`, L1 released | 3: itself, the cursor, the Gyro twin | 2 | Drop the twin |
  | Ordinary release | `L1: Tap Cover`, L1 released | 5: itself, its three possible modifiers, the cursor | 4 | Drop the cursor. The three modifiers stay: the cover can sit on each |
  | Ordinary release | `Steering \| R1: W Key`, R1 released | 13 | 9 | Drop 4: the S Key, the other Modifier 2 order, `R1: Tap Cover`, the Entry Guard |
  | Ordinary release | `Menu Left: Fn Layer`, Select released | 6: itself, both Entry Points, both stick guards, the menu Tap Cover | 3 | Review: the guards and the Tap Cover are the timing-race kind |
  | Modifier 2 quick tap | `L1!R1: Modifier 2`, a bumper released | 13, then Gyro on | 6 | Drop the three Gyro twins and both cursors. Review the other Modifier 2 order |
  | Deliberate clear | Entering a transition | 69 | 22 | Stays at 69 |
  | Deliberate clear | `Steering \| R1!L1: Modifier 2`, L1 released without a cover | 70 | 10 | Stays at 70 |

  Per layout: 58 ordinary releases make 252 removals, 83 of a layer that is
  never there. The 8 Modifier 2 quick taps make 108, 56 never there. The 10
  clears make 692, 532 never there, and keep them all.

  Why a clear is exempt: it is the reset to fall back on when the stack is
  not what it should be, so it must not depend on knowing the stack. It is
  also where "can be there" is least reliable, because the chains put only
  one unrelated layer underneath at a time.

  Not touched: the stick-touch release keeps its fixed three layers per side
  (Definition of Done §5), although 84 of its 314 removals name one that
  can't be there under that host.

### What the answers change

| Change | Where | Size per layout |
|---|---|---|
| Add the guarded cleanup to both stick touches | The four Modifier 2 layers | 8 bindings |
| One step instead of two | Cursor edge cleanups, `RTP: Mouse Buttons` touch cleanups | 6 bindings |
| Either bumper as the guard on stick touches | The two Steering Modifier 2 layers | 4 bindings |
| Take the windows out of cleanup lists | Six Steering layers | Part of the row below |
| Drop removals of layers that can't be there | Every cleanup list | About 1,000 of 1,982 removals |
| The same for ordinary releases and the Modifier 2 quick tap | 66 bindings | Up to 139 of 360 removals |

### Still open

1. **Read the revised [six rules](#the-rules) and confirm or correct them.**
   With that, the [Cleanup audit](../../todos.md#layer-cleanup) can fail on
   three things: a layer the rules expect and the cleanup leaves, a removed
   layer whose keeper is outside the guard, and a removed layer that can
   never be on the stack with the host.

## Method and limits

- [measure.py](measure.py) reads a layout and classifies every cleanup
  function (the Flow model's `recovery` role). The stacks come from the
  backward chains, so "can be below" and "can be above" mean the same as in
  `audit_layer.py`. [measure_multiset.py](measure_multiset.py) does the table
  for the archived layouts without chains.
  ```bash
  python3 findings/2026-10-02-cleanup-boundaries/measure.py summary
  python3 findings/2026-10-02-cleanup-boundaries/measure.py detail neptune/single-set-default_hold-gyro_latest.json
  python3 findings/2026-10-02-cleanup-boundaries/measure.py pairs  <layout>   # every host with what is below and above it
  python3 findings/2026-10-02-cleanup-boundaries/measure.py above  <layout>   # what a layer on top puts on a cleanup input
  ```
- **The keeper is worked out, not declared:** the buttons whose Release
  removes the layer, checked against the guards of its own cleanups. It is
  wrong for layers that only exist inside another layer's hold. Steering's
  left-stick layers end on a stick Release, but only exist while a driver is
  held, so they show up as "kept by something else". Of the 10 such removals
  in 90.10, 6 are these left-stick layers, 2 are the Steering windows and 2
  are the second driver's Modifier 2 ([difference 4](#where-the-layouts-differ-from-the-rules)).
- **Stale stacks aren't modelled.** The chains follow intended flows, so
  "never on the stack with it" means never in a normal stack. A missed
  release can produce stacks the chains don't have, which is what the extra
  removals are for.
- **Chords are ignored when building stacks**, and `hold_layer` isn't
  followed, so `RTP: Mouse Buttons` under `RTP: Circular Scroll` isn't seen
  as a stack.
- Static analysis only. Nothing here was tested on the Deck.
