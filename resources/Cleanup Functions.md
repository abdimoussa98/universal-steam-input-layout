# Cleanup functions

**Status:** written as a draft on 2026-09-30. Its four open questions were
answered by the cleanup rules on 2026-10-02, which are R127 to R132 in the
[Layer Definition of Done §7](Layer%20Definition%20of%20Done.md#7-cleanup);
where this page and those rules differ, the rules are right. The kinds and
terms below still describe the layout.

This page defines every kind of binding that removes layers, so that a
script can recognize them, check them, and eventually regenerate them (see
the [cleanup generator plan](../plans/2026-09-30-cleanup-generator.md)). It
separates an **owner release**, the normal way out of an interaction, from a
**cleanup function**, the backup that fixes stale state.

## Contents

| Section | What it covers |
|---|---|
| [Terms](#terms) | Interaction family, owner, dependent, host, trigger, scope, survivor |
| [The kinds](#the-kinds) | Every kind of layer-removing binding and its required shape |
| [Owner release vs cleanup function](#owner-release-vs-cleanup-function) | The difference, side by side |
| [Order matters](#order-matters) | Why stack order and execution order decide what a release does |
| [Computing a scope](#computing-a-scope) | How the layer report finds the candidates and the family filters them |
| [Questions for the author](#questions-for-the-author) | What needs defining before the generator is built |

## Terms

| Term | Definition (draft) | Example |
|---|---|---|
| **Interaction family** | An interaction's owner layers plus its dependents. It's the unit a cleanup's scope is written in | The L1 family: `L1: Modifier 0`, `Gyro \| L1: Modifier 0`, `L1: Tap Cover`, `L1: Temp Cursor Gyro` |
| **Owner** | A layer that exists because a button or touch is held, and applies the family's other layers ([vocabulary](Layout%20Vocabulary.md#terms)) | `L1: Modifier 0` and its Gyro variant |
| **Dependent** | A layer that only the family's own bindings add: covers, overlays, cursor, helpers | `L1: Tap Cover` |
| **Host** | The layer whose input carries the binding | Guarded recovery on `L1: Modifier 0`'s RS edge |
| **Trigger** | When the binding fires: the input, the activation type and the condition | Regular Press on RS edge while LB is *not* held |
| **Scope** | Which layers it removes, named by rule rather than by list | "the L1 family", "the current Mod 2 branch", "self only" |
| **Survivor** | A layer the scope deliberately leaves, with a reason | The still-held R1 side; persistent `Gyro`; unrelated families |

Existing scope names and examples are in
[Cleanup Scopes](Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples).
The trigger-by-scope classification is from the
[cleanup audit](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md#two-independent-classifications-trigger-and-scope).

## The kinds

Each kind has a required shape, so a script can recognize it. The rules for
what each may remove are R127 to R135 in the
[Layer Definition of Done §7](Layer%20Definition%20of%20Done.md#7-cleanup);
the stick-touch release is R116 to R118 and R123, the reset R120 to R122, and
the timed self-exit and transition R146 to R148.

| Kind | Trigger | Shape | Scope | Reference |
|---|---|---|---|---|
| **Owner release** | Owner's primary button released | Release entry. The array removes the family, then adds any next layer (a Double Tap window) **last** | One of: the whole family, the current Mod 2 branch, or only the **released side** (rocking). It can be narrower than the cleanup function's scope | [Lifecycle exit](Layout%20Vocabulary.md#terms), [Combined Tap Cover](Steam%20Input%20JSON%20Structure.md#combined-tap-cover-preserve-the-still-held-side) |
| **Cleanup function** (guarded recovery) | A likely next input pressed while **no owner is held** | An empty or real-output chord guard for each valid owner, plus an **interruptible** Regular Press with **Hold to Repeat** that removes the scope | The owner's family and every dependent it applied, minus survivors | [Guarded Recovery Binding Shape](Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape), [Overlay ownership](Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership) |
| **Stick-touch release** | Thumb leaves a stick | Release entry. It completes a pending add first (last in storage), then removes that side's LST/RST trio | Side-local trio; Always On windows remove themselves first | [Definition of Done §5](Layer%20Definition%20of%20Done.md#5-stick-touch-release) |
| **Delayed-apply reset** | Primary button held | Regular Press, `interruptable: 0`, Hold to Repeat at delay + 50 ms | Only the pending delayed target. This is timer maintenance, not cleanup | [§6](Layer%20Definition%20of%20Done.md#6-hold-tap-and-double-tap) |
| **Timed self-exit** | `always_on_action` after its delay | Always On entry | Only itself | [Always On isolation](Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround) |
| **Transition** | Second press, threshold crossing, or a deliberate move | Removes the source layer(s) first, then adds the next layer last | The layer(s) being left | [cleanup audit triggers](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md#triggers-already-implemented) |
| **Cancellation** | Any listed input during an overlay | Uninterruptible, repeating Regular Press that removes **only itself**, exposing the parent | Self only | [Cursor cancellation](Steam%20Input%20JSON%20Structure.md#cursor-cancellation-and-repeating-cover-chords) |

A recognizer needs only the shape: trigger, activation type, settings and
order. With the stacks from the backward chains
([`layer_report`](../steam_layout/layer_report.py)), each kind's scope can be
checked and computed.

## Owner release vs cleanup function

| | Owner release | Cleanup function |
|---|---|---|
| Purpose | The normal way out | A backup exit when the release was missed (Steam menu) |
| Fires when | The owner button is released | A likely next input is pressed and **no** owner is held |
| Guard | None: it *is* the owner's input | One chord per valid owner suppresses it |
| Repeat | No | Hold to Repeat (required) |
| Interruptible | Default | Default (the guard must be able to suppress it) |
| Can add a layer | Yes, last (window, next state) | No |
| Scope | Depends on the gesture. For example, the combined cover's release removes only the released side, so you can rock between modifiers | The family and every dependent it applied |
| Where it lives | Owner's primary input | Owner and stack-owning layers, on the likely next inputs; overlays inherit it |

Both use the same scope question: which of the family's layers can be active
when this fires? That's why the stack helper serves both.

## Order matters

**Author, 2026-09-30:** what a release does depends on the **current stack
order** (which layer is topmost for that input) and on the **execution order**
inside the array that built the stack. Mod 2 rocking is the main example:
- When you let go of one side of Mod 2, only that side is removed.
- The held side's Tap Cover sits directly above its modifier, so letting go
  of that side later exits cleanly, without a Double Tap window.
- Pressing the released side again goes straight back to Mod 2.

This relies on:
- the entry chord adding the covers in a specific order
- a re-add of an active layer leaving it where it is

See the step-by-step walkthrough in
[Rocking Between Modifiers](Steam%20Input%20JSON%20Structure.md#rocking-between-modifiers-0-1-and-2).
`steam_layout.stacks.walk` replays any sequence like it, and
[test_modifier_rocking.py](../tests/test_modifier_rocking.py) pins the rocking sequence in both
layouts. A generator must never reorder these arrays or change which layer
ends up on top.

## Computing a scope

The layer report answers the first half. For each binding of a layer that
removes layers, its Exits section lists what the binding removes that can be
present, what can be present and is left, and what it removes that is never
there:

```bash
python3 -m tools.audit_layer neptune/single-set-default_hold-gyro_latest.json --layer "L1: Modifier 0"
```

The candidates are not the scope, though. Measured with the older
depth-limited search (now in [archived/](../archived/README.md)), `L1:
Modifier 0`'s RS edge fired in 9,471 stacks, and 20 layers could be present.
Most of them belong to other interactions: stick helpers, RTP layers and the
key layers.
The scope is:

> **scope = co-active candidates ∩ the host's family − survivors**

So the family is the definition that matters most. Two early results already
show the value:

- `Menu Left: Fn Layer`'s RS-edge recovery could find `Menu Right: Enter` active
  and never removed it: finding F1 in the
  [cleanup audit](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md#f1-enterbackspace-are-missing-from-menu-family-recovery).
  It is moot since 90.9, which removed both overlay layers.
- Overlays that override the host's input, such as the cursor on LB, correctly
  drop out of the owner release's candidates. Their own local exit handles
  them.

## Questions for the author

**Answered:**
- **Owner release scope vs cleanup scope (was question 2):** they are not
  always the same. An owner release can deliberately remove less. The
  combined cover's release removes only the released side, so you can rock
  between Mod 0, 1 and 2 ([Order matters](#order-matters)). The scope of each
  owner release has to be stated per gesture.

**The four questions below were answered by the cleanup rules (author,
2026-10-02),** in the
[cleanup boundaries findings](../findings/2026-10-02-cleanup-boundaries/README.md#how-this-answers-the-open-questions).
The Cleanup audit (`audit_cleanups.py`) checks them since 90.12.

1. **Who belongs to a family: computed, or listed by hand?**
   A computed rule could be "a layer belongs to the L1 family if only L1's
   layers ever add it". Here is what that gives today:

   | Layer | Added by | Computed rule says |
   |---|---|---|
   | `L1: Temp Cursor Gyro` | `L1: Modifier 0` and its Gyro variant only | L1 family ✓ |
   | `L1: Tap Cover` | L1 Mod 0 **and R1 Mod 1** (step 5 of rocking), plus Steering's R1!L1 Mod 2 | not only L1, so the rule fails |
   | `L1&R1: Tap Cover` | all four Mod 2 layers | the Mod 2 family, shared by both sides |

   So a purely computed rule breaks on exactly the layers that make rocking
   work. The options:
   - **(a)** list each family by hand
   - **(b)** compute it, with a hand-written override list (for example "L1
     Tap Cover belongs to L1 even though R1 adds it")
   - **(c)** name it by prefix: every `L1: …` layer is L1's

2. **What must a cleanup leave alone (survivors)?**
   When `L1: Modifier 0`'s RS-edge recovery fires (no L1 held), up to 20
   layers can be active. Some examples, with what I think should happen:

   | Could be active | Remove? (my guess) |
   |---|---|
   | `L1: Tap Cover`, `L1: Temp Cursor Gyro` | yes: L1's own dependents |
   | `R1: Modifier 1`, `R1: Tap Cover` (R1 still held) | no: a live interaction |
   | `Gyro` | no: persistent mode |
   | `RST: Entry Point` (thumb on the right stick) | no: only the stick-touch release removes stick helpers |
   | `Escape` key layer, `RTP: Entry Point` | no: another family |

   Is that right? Are there other survivors?

3. **Which inputs should host cleanup functions?**
   Today it varies a lot by layer:

   | Layer | Guarded-recovery inputs |
   |---|---|
   | `L1: Modifier 0` | 17: face buttons, D-pad, both menu buttons, RB, both stick clicks, touches and edges |
   | `L1!R1: Modifier 2` | 14: face buttons, D-pad, both menu buttons, stick clicks and edges (no touches) |
   | `Menu Left: Fn Layer` | 19: face buttons, D-pad, trigger clicks, bumpers, back buttons, Start, both stick edges |
   | `L1: Scroll Down`, `Transition Set 0` | 4: both stick touches and edges |
   | `L1: Tap Cover` | 2: stick touches only (inherits the rest from its owner) |
   | `Menu Left: Escape` | 0: relies on its release and the menu stack below |

   Should there be a rule per layer type (owner, Fn, scroll, transition,
   overlay), or should the generator keep each layer's current host list and
   only fix what's removed?

4. **Who cleans up a layer that two families add?**
   `L1&R1: Tap Cover` is added by all four Mod 2 layers. `L1: Tap Cover` is
   added by both single modifiers because of rocking. When L1's recovery
   fires with R1 still held, should it remove `L1: Tap Cover` (yes: it's the
   left side's) and leave `R1: Tap Cover` (the held side's)? In other words,
   does a shared layer belong to the side its name says, whoever added it?
