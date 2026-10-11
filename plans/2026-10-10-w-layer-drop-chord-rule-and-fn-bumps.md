# Plan: the W layer drop, the Steering stick edges, and the Fn hold bumps

**Status, 2026-10-10:** parts 1, 3, 4 and 6 are built as **90.53** on the
author's "implement the plan"
([record](../findings/2026-10-10-steering-entry-and-edge-chords/README.md)).
Part 5, the Fn hold bumps, is set aside by the author and not built. Part 7
is a note. Nothing has run on the Deck. One thing was built differently from
the text below: the entry chord of part 1 needs the driver and the deflect,
both, on the author's answer of the same day (see part 1). The text below is
the plan as discussed; the leads in it are from reading the bindings and are
not diagnoses.

The scroll fault's cause was found by the author on the Deck after this plan:
the hold timer owned by the stick's direction. The lead in part 1 about the
entry chord was wrong. See
[stick-hold-timer-on-the-driver](2026-10-10-stick-hold-timer-on-the-driver.md),
built in the same release.

## Terms

- **Driver:** R1 for W and L1 for S in `Steering` (R2 and L2 in the
  alternative).
- **W layer:** `Steering | R1: W Key`, which `Steering` adds while R1 is held.
  `Steering | L1: S Key` is its twin.
- **Stick modifier:** `Steering | LS Up: Modifier 1` or
  `Steering | LS Down: Modifier 0`.
- **Hold marker:** `Steering | LS: Tap Cover`.
- **Ring:** the left stick's outer edge input. Its **radius** is how far out
  the stick must be for the ring to be pressed.
- **Sub-command:** one command inside an activator's binding list. A chord
  with `add_layer A` and `remove_layer B` has two. A second activator on the
  same input is not a sub-command.
- **Unstated haptic:** an activator with no `haptic_intensity` setting, so
  Steam's default decides.
- **Guard pattern:** what the ring carries in `Steering | LS: Entry Guard`,
  described in part 6.

## 1. The W layer drops while the driver is held

**Fault (author).** Holding a driver in `Steering` and flicking the left stick
sometimes removes the W layer (or the S layer). With the driver still down,
stick up or down then reaches `Steering`'s own exit and clears the stateful
layer. That must never happen while a driver is held.

**Lead.** In the W and S layers, stick up, down, ring and touch each carry a
plain repeating Regular Press that removes the layer. The only thing holding
it back is a chord on the held driver interrupting it. One missed interrupt
during a flick gives the fault. Not reproduced.

The ring is the first suspect among the four: in these layers it is pressed
at radius 13276, the same travel at which up and down start, so every flick
crosses it and starts the press and its guard again. See part 6.

### A second lead, and the scroll that works once

The older fault, still open: with a driver held, a deflect scrolls once and
then not again; W stays held; pressing the driver again doesn't help; a
deflect to the rim can leave `Steering` (author, on 90.50 and 90.51). One
bind would give all of that and the W layer drop above.

**The bind.** Up and down in the W and S layers, the entry of the stick's
sequence. Each holds two entries: the cleanup press that removes the W layer,
and a chord on the driver, repeating every 50 ms, that adds the stick
modifier. The chord is also the cleanup's only guard.

**What may go wrong.** A chord stays latched until the input it is bound to
is released (A17, verified). Here that input is up, and the chord's button is
the driver, which stays held through every deflect. On the first deflect the
chord adds the stick modifier, which takes up over. Up's release is then
answered by the modifier, not by the W layer. If the W layer's chord never
sees it, it is still latched and has nothing left to start it again.

| What you see | How it follows |
| --- | --- |
| The first deflect scrolls | The chord fires for the first time |
| Later deflects don't | The chord no longer fires, so no stick modifier is added and no window opens |
| W stays held | The cleanup press is no longer interrupted and removes the W layer; `Steering` adds it again within 50 ms |
| A deflect to the rim leaves `Steering` | In that 50 ms gap `Steering`'s own exit is uncovered with the stick at the rim |
| Pressing the driver again doesn't help | Only if a latched chord outlives its layer being removed and added. Not known |

**Why 90.51 and 90.52 would not have fixed it.** 90.51 took a cleanup off the
stick modifier. 90.52 put every step of the sequence on the bumper lifecycle
except this one: its record says "Entry: unchanged". In the bumper lifecycle
the entry is a self-chord in Base and L1 carries no cleanup. Here the entry
is a chord on another button that is never released, beside a cleanup.

**Unverified.** The simulator starts the chord again on every deflect, so it
scrolls every time on every release. A check that tells this lead from the
timer and the window: after the scroll has stopped, hold up and press a
button that the stick modifier retypes. The W layer's key means the modifier
was never added, which is this lead. The modifier's key means the entry works
and the fault is later in the sequence.

**Decided (author, 2026-10-10: "yes").** Mirror the entry too: in the W and S
layers, up and down add the stick modifier with a self-chord on the stick's
deflect, repeating, and carry no cleanup. The layer only exists while its
driver is held, so the add still needs the driver. Recovery without a driver
is the ring's inverted chord of part 6.

**Built differently (author, 2026-10-10).** "The layer only exists while its
driver is held" is wrong after a missed driver release. With the chord on the
deflect alone, a stuck W layer and the stick held up, a face button's cleanup
removed the stick modifier and the entry added it again, without end. Asked,
the author chose the chord on the driver and the deflect, both. No cleanup on
up and down, as decided.

## 2. Repeating chords with more than one sub-command (called out, no rule)

**Author, 2026-10-10:** a repeating Chorded Press with more than one
sub-command does not fire its repeat. This is a call-out, not a rule: no rule
ID, no audit check. The one change it asks for is part 3.

For reference, 16 chords have that shape today: Start and Select in Base and
in `Steering`, the other bumper in the four base and `Gyro` modifiers, the
other menu button in the four menu Entry Points, both bumpers in the Entry
Guard, and the other bumper in the W and S layers (13 sub-commands each).

## 3. No right pad clears in the Steering modifier layers

**Requirement (author, repeated).** No `RTP:` layer removes while in the
Steering modifier layers: the two stick modifiers and the two Modifier 2
layers.

**Change.** 12 binds lose their `RTP:` removes and keep the rest:

| Layer | Bind | `RTP:` removes of its sub-commands |
| --- | --- | --- |
| Each stick modifier | its own direction's 200 ms chord | 3 of 4 |
| Each stick modifier | left stick touch Release | 3 of 7 |
| Each stick modifier | right stick touch Release | 3 of 7 |
| Each Modifier 2 layer | the bumper's 200 ms chord | 6 of 7 |
| Each Modifier 2 layer | left stick touch Release | 6 of 10 |
| Each Modifier 2 layer | right stick touch Release | 6 of 10 |

**Left as they are (my call, say if not):**

- The Modifier 2 bumper Release in both Modifier 2 layers. It is the full
  clear to Base (R159, 88 removes); taking the 7 `RTP:` removes out would
  leave right pad layers on after a clear.
- The right pad's touch Release in the two Double Tap windows. They are not
  modifier layers.

## 4. Drop the hold marker add on A and D

**Change (author).** In the two stick modifiers, stick left and right send A
or D and also add the hold marker. On a four-way D-pad they can't be reached
without releasing up or down, which already opens the window. The four binds
keep only the key.

**Stays (author):** the stick-click chords in the stick modifiers keep their
hold marker add. A stick can be clicked while W is held.

## 5. More than one bump on the Fn layer hold

**Fault (author).** Holding a menu button gives more than one haptic bump.

**Lead.** From Base, three binds run on the held button before the Fn layer
owns it. Only the third states a bump:

1. Base's repeating chord that adds the Entry Point: unstated haptic.
2. The Entry Point's repeating reset of the Fn layer (every 250 ms): unstated
   haptic.
3. The Entry Point's 200 ms chord that adds the Fn layer: Low.

An unstated haptic on a pad layer command pulsed on the Deck before, and the
pads have a test for it
(`test_quiet_resets_and_beeps.test_every_layer_command_on_a_pad_states_its_haptic`).
The menu buttons have no such test. With both menu buttons held, the Entry
Point's chord on the second button repeats at Low.

**Observation (author, 2026-10-10):** sometimes one bump, sometimes two,
sometimes three. The author suspects the repeats.

**Reading.** The count changing from hold to hold points at the two repeating
binds, in one of two ways. Which one is not known.

| | A. A repeat pulses by itself | B. A repeat undoes the Fn layer |
| --- | --- | --- |
| What happens | The Entry Point's reset repeats every 250 ms and the Fn layer is due at 200 ms: a 50 ms margin. A thumb on a pad or stick during the hold postpones the 200 ms (on the simulator the Fn layer lands at 210 to 450 ms, up to about a second with the right pad), so one or more repeats fire first. Each has an unstated haptic | The reset keeps repeating after the Fn layer has landed and removes it. The 200 ms chord starts over and adds it again, with its Low bump, every time |
| When the extra bumps come | Before the Fn layer is on, within the first half second or so | For as long as the button is held, about one each quarter to half second |
| The Fn layer | Late, but stays | Drops out briefly between bumps |
| Fix | Haptic Off on the reset and on Base's chord | The reset must not act once the Fn layer is on; haptic Off alone would not stop the bumps |

A third source, apart from the repeats: Steam's text says an activator's
haptic pulses on activation and on deactivation, so the one Low bump may come
again as the button lets go.

**Change.** State haptic Off on every menu-button layer command except the
one bump, and extend the test from the pads to the menu buttons. That settles
A. B needs the Deck answer first (open questions).

## 6. The ring in the Steering layers: copy the guard pattern

**Author, 2026-10-10:** the ring binds throughout the Steering layers don't
make sense as they are. The one that does is the Entry Guard's. Copy that
pattern to the others; the ring binds stay. Also: the Steering layers aren't
using the default for the ring, so audit the left stick in every Steering
layer.

*Corrected the same day: the first version of this part proposed taking the
ring binds off. The author never asked for that.*

### The guard pattern

On the ring of `Steering | LS: Entry Guard`:

- A **Chorded Press on either driver with Invert Activation**, repeating, not
  interruptible, haptic Off, with one sub-command: it removes the Entry Guard
  itself.
- A **Release**, haptic Off, that removes the Entry Guard itself.
- The group states no radius (Steam's default, near the rim) and is not
  inverted.

**How an inverted chord works (author, 2026-10-10; corrected the same day).**
It acts while **no** chord button is held. Steam's own text for the setting,
read from the client on this Mac: "Fires when this input is released while no
chord button is pressed. Pressing this input releases it." So on the ring it
runs while no driver is held and the stick is short of the rim, and stops
when a driver is pressed or the stick reaches the rim. It is a cleanup in one
bind: to use the layer a driver has to be held, and without one the layer
clears itself.

### Audit: the left stick's ring in every Steering layer

Default layout. The alternative is the same with L2 and R2 as the drivers.

| Layer | Ring radius | Four-way stated | On the ring |
| --- | --- | --- | --- |
| Base, for comparison | 21700, inverted | no | Soft Press: the WASD modifier |
| `Steering` | default | yes | nothing bound |
| Entry Guard | default | yes | the guard pattern |
| W layer, S layer | 13276 | no | Repeating press removes the two scroll layers, the Double Tap Cover, the hold marker, both stick modifiers and itself. Guard chord: its own driver |
| The two stick modifiers | 13276 | no | Repeating press removes the hold marker, itself, the W layer and the S layer. Guard chord: either driver |
| Hold marker | 13276 | no | Repeating press removes the S layer, the W layer, both stick modifiers and itself. Guard chord: either driver |
| `Steering \| LS: Double Tap Cover` | 13276 | no | Repeating press removes the S layer, the W layer and itself. Guard chord: either driver |
| The two scroll layers | 13276 | no | Repeating press removes the S layer, the W layer, the Double Tap Cover and itself. Guard chord: either driver |
| The two Double Tap windows | 13276 | no | Empty block |
| The two Modifier 2 layers | default | no | Repeating press removes the bumper's Tap Cover, itself, and the W or S layer. Guard chord: either driver |

What the audit shows:

1. **Ten of the fourteen layers state 13276; four use the default.** 13276 is
   also the D-pad deadzone, so in those ten the ring is pressed at the same
   travel at which up and down start.
2. **Where 13276 came from.**

   | Releases | Radius in the Steering layers | Why |
   | --- | --- | --- |
   | 90.10 to 90.30 | 4915 | The ring's Release meant "back at centre" and ended the stick modifier |
   | 90.31 to 90.48 | default | The author's decision of 2026-10-04: "It should just be the default" |
   | 90.49 to 90.51 | 13276 in eight layers | So that a partial flick would press the ring, whose Release ended the stick modifier (A55) |
   | 90.52 | 13276 in ten layers | The two new scroll layers took it. But since 90.52 the stick modifier ends on its direction's own Release, not the ring's |

   So the reason for 13276 went away in 90.52. Today nothing in these ten
   layers ends on the ring's Release; the radius only decides where the ring's
   repeating press starts.
3. **None of the ten has a Release on the ring.** The Entry Guard is the only
   Steering layer where the ring is a real exit.
4. **Shape.** The ten layers and the Modifier 2 layers use two binds that
   race: a plain press that removes, and a chord with an empty binding that
   has to interrupt it. The guard pattern has no such race.
5. **Reach.** Eight of those layers remove the W and S layers from above. In
   the guard pattern a layer removes only itself.
6. **Four-way.** Only `Steering` and the Entry Guard state the four-way
   layout. The other twelve state none; whether they take the four-way of the
   layer under them is open (A51). Part 4's reasoning rests on the stick
   modifiers being four-way.

### Decided: the radius (author, 2026-10-10)

"Copy the value from the cursor edge gyro temp layers." `L1: Temp Cursor
Gyro` and `R1: Temp Cursor Gyro` state no radius on either stick, in both
variants: Steam's default, near the rim. So the ten layers lose their 13276
and all fourteen Steering layers are on the default, as from 90.31 to 90.48.

### What is wrong in the repo today

The first two versions of this part had the inverted chord backwards, as
"runs while a driver is held". So do three things in the repo:

| Where | What it says | What it should say |
| --- | --- | --- |
| [90.44 note](../resources/Stateful%20Layer%20Transitions.md#9044-entry-guard-inward-exit-and-stateful-preservation) | The Entry Guard's chord repeats "while either driver is held"; without a driver, a centred entry protects the first push | It repeats while no driver is held |
| A54 | A repeating chord "on either driver" on an inverted edge | The same correction |
| `steam_layout/simulator.py` | An inverted chord needs its chord button held and its input released | Its input released and no chord button held |

The author's [observations of 2026-10-07](../resources/Steam%20Behaviour%20Assumptions.md#inverted-chorded-press-in-action-layers)
were right all along: on at layer load, off when the chorded button is
pressed. They also say that a chord button shuts the bind off until the owner
is pressed again or the layer loads again, that Remove Layer doesn't restart
it, and that a Release at the same moment or a very fast add and remove can
stop it.

**Consequence for the Entry Guard, to check on the Deck:** entering `Steering`
with no driver held and the stick short of the rim, the guard removes itself
at once. The scenario tests that say otherwise rest on the simulator's model.

### The change

On the ring of each layer below, the plain repeating press and its empty
guard chord become one inverted chord: repeating, not interruptible, haptic
Off, on the same drivers as today's guard, with today's list. The lists stay
because they were worked out for the same case, no driver held (R127 to
R132).

| Layer | Chord buttons | The ring removes |
| --- | --- | --- |
| `Steering \| R1: W Key` | R1 | the two scroll layers, the Double Tap Cover, the hold marker, both stick modifiers, itself |
| `Steering \| L1: S Key` | L1 | the same, with itself |
| `Steering \| LS Up: Modifier 1`, `Steering \| LS Down: Modifier 0` | either driver | the hold marker, itself, the W layer, the S layer |
| `Steering \| LS: Tap Cover` (hold marker) | either driver | the S layer, the W layer, both stick modifiers, itself |
| `Steering \| LS Up: Scroll Up`, `Steering \| LS Down: Scroll Down` | either driver | the S layer, the W layer, the Double Tap Cover, itself |
| `Steering \| LS: Double Tap Cover` | either driver | the S layer, the W layer, itself |
| `Steering \| R1!L1: Modifier 2`, `Steering \| L1!R1: Modifier 2` | either driver | the bumper's Tap Cover, itself, the W or S layer |

Unchanged: the Entry Guard, `Steering` (nothing bound) and the two Double Tap
windows (empty block; a window clears itself).

Press by press, in the W layer:

- **R1 held, any flick:** the chord is off, because its chord button is held.
  Nothing on the ring can remove the W layer. This is the race of part 1 gone
  from the ring.
- **R1 not held and the W layer still on** (a Release that never fired): the
  chord runs as soon as the stick is short of the rim, and clears the list.

**The Release is not copied (my call, say if not).** In the Entry Guard it is
the layer's own exit. With the default radius a ring Release fires when the
stick leaves the rim, not when it is back at centre: push up to the rim, ease
back while still holding up, and it would end the stick modifier mid-hold.

**Not in this part:** the same press-and-guard shape on the stick touches.
Up and down in the W and S layers are in part 1.

**Rules to update with it:** R133 (the cleanup shape) and R111's register
(inverted edges on a D-pad stick) get these binds named, and the Cleanup audit
has to read an inverted chord as a cleanup with its guard.

## 7. Trackpad clicks (noted, not in scope)

**Author, 2026-10-10:** still weird interrupts or behaviour on the trackpad
clicks. Noted here only; to be described and looked at later.

## Open questions

No decision is open. Set aside (author, 2026-10-10): whether a repeating
chord with more than one sub-command fires once. The lists of part 6 stay as
they are; the check is in `todos.md`.

Observations from the Deck:

1. Part 5: do the extra bumps keep coming the longer a menu button is held,
   or are they all over within the first half second? One menu button or
   both? Was a thumb on a pad or a stick?
2. Part 1, the check that tells the entry from the timer and the window:
   after the scroll has stopped, hold up and press a button the stick
   modifier retypes. Which key comes?
3. Part 1: does the W drop happen with both drivers, and on a flick through
   the centre or around the rim?
