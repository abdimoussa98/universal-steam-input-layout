# Steering implementation plan audit

Date: 2026-09-29. Scope: the [steering implementation plan](../../plans/2026-09-29-steering-implementation-plan.md),
checked against the [brainstorm contract](../../plans/2026-09-29-steering-entry-brainstorm.md),
the [design review](../2026-09-29-steering-design-review/AUDIT.md), both 90.4
working JSONs (read through title-token copies in scratch), the July reference
and the installed Steam UI bundle. **No layout, plan or test file was changed.**

## Review follow-up

The implementation plan now incorporates the actions below, using S1–S10 gate
labels, a native-gesture comparison before window allocation, explicit failure
branches and a defined diagnostic handoff. Findings describe the audited plan
revision; implementation and device results remain pending. This follow-up also
qualifies proposed fixes that the original audit did not establish.

## Verdict

The plan's baseline facts are accurate, and as a risk register it is thorough.
It is not yet executable as an implementation plan:

1. It misses or understates five concrete interactions in the current layout
   (H1–H5). Three of them can be resolved statically now, without the Deck.
2. Several acceptance targets (exact-sample ties, exact deadlines) cannot be
   produced by hand. The plan never says how key edges and wheel ticks are observed.
3. No gate has a failure branch. The user decisions it depends on are not listed
   in one place.
4. The next work item, the diagnostic harness, is specified only by its file
   pattern. The existing rule-test layout is already built and answers two of
   the plan's open questions, but it is not scheduled.

## Verified as stated

| Plan claim | Result |
|---|---|
| Both files 90.4, 1 set, 55 layers; 549 / 552 groups | Match |
| Review hashes (default `2489201c…`, alternative `087fbbdf…`) | Match; working JSON unchanged since the review |
| 33 unittest + 6 node tests pass; both budget audits PASS, max 3 | Re-run: match |
| Max `Preset_1000155`; max group 13071 (default) / 13072 (alternative) | Match |
| Runtime IDs 1, 19/20, 30, 34/35, 36/37, 51/52, 56; default groups 10, 12, 871, 13044–13046, 1161/1162, 1320/1330/1331, 1247/1260/1261, 893/897, 901/905, 951/955 | Match |
| Alternative menu group IDs differ | True: its Menu Right Entry uses 13041/13043/13044, and its 13044 is the LS group, not the switch group |
| Menu Right Entry owner input is full (release, 300 ms Fn chord, 350 ms repeating reset) | Match; Menu Left mirrors it |
| Base group 10 is the only binding that adds the menu entry layers | True in both variants, so the selector change is correctly scoped |
| Transition Set 1 menu releases are empty | Match |
| Base Double Tap: wheel at 50 ms, self-removal at 150 ms; cover cadence 50 ms; Scroll releases back into Double Tap until the 150 ms cover | Match |
| HTML: 150 ms deferred single, 100 ms repeat | Match |
| `test_neptune_recovery.py` asserts exactly seven Always On layers | Match (line 154) |
| 7 + 4 + 8 = 19 | Correct |
| Either-stick mask `3221225472` | **Correct, now verified**: see [Mask verification](#mask-verification). The exploratory audit's decode table still marks both bits "inferred" |

## Findings

**High:** executing the plan as written would give a wrong or unreliable layout.
**Medium:** a gap that will cost rework. **Low:** clarity only.

### H1. The commit can race Transition Set 1's own stick recoveries

The plan commits steering on Menu Right release in Transition Set 1
([P4.5](../../plans/2026-09-29-steering-implementation-plan.md#L247)). It also
says to "preserve its recovery ancestry" ([baseline table](../../plans/2026-09-29-steering-implementation-plan.md#L57)).
Transition Set 1's LS touch, LS edge, RS touch and RS edge each carry a repeating
Regular Press that removes every menu layer **and Transition Set 1 itself**
(groups 1260/1261). Only the empty chord-14/15 entries block them, and only
while a menu button is held.

At the commit instant Menu Right is released, so that block lifts in the same
moment the release fires. The thumb is normally still on LS, because it has just
clicked. In the guarded case LS is also deflected past the edge. If a recovery
runs before the release binding, the commit's layer is gone. The user lands in
Base with no steering.

July had only the LS touch recovery, and it removed only Transition Set 1. The
current layout adds an LS edge recovery. That recovery fires in exactly the
carried-movement case the guard exists for. By held-input rule 1, Transition
Set 1 was added over a held touch, so the competing event is a repeat tick
rather than a fresh press. This is a potential ordering failure, not a
reproduced device result; a few successful manual tries would not exclude it.

**Change:** name the race in P4.5 and in T8. Probe it with the thumb resting on
LS and with LS at full tilt, over many repetitions. Prototype one of these
mitigations:

- (a) **Commit on the LS click** (the brainstorm's open alternative). Steering or
  the Guard must then own Menu Right until it is released. Otherwise Base's
  repeating self-chord, now exposed, re-adds Menu Right Entry while the button
  is still held.
- (b) **Gate recovery and commitment exclusively.** Replace competing recovery
  routes with explicit state/conditions. A short start delay alone does not
  establish priority: it may already have elapsed while the input was held.
  Any timing-based candidate still needs native evidence.

### H2. Same-sample and exact-deadline targets cannot be produced by hand

T7 and parts of T4 require events in "exactly one sample" or at exactly
2.5 s / 5 s. So do matrix rows D7, D21, D30, D35–D37, E5 and F5. Controller
input is sampled every few milliseconds. A person cannot produce a same-sample
pair or hit a deadline on demand, so these rows can neither pass nor fail
deliberately.

The plan also never says how "observed key edges/wheel counts"
([delivery](../../plans/2026-09-29-steering-implementation-plan.md#L319)) are
recorded. W+S overlap, a stuck key and an extra wheel tick are not visible from
layer names or in-game movement.

**Change:**

- **Order independence:** restate every tie policy as an order-independence
  requirement. For each pair of activators that can coincide, show statically
  that both orders have safe intermediate key/wheel outputs and layer mutations,
  as well as acceptable final states. A stray tick, W+S overlap or mutation
  inside an Always On window is a failure even if cleanup reaches the right state.
- **Near-boundary tests:** test natively only near the boundaries (for example
  ±100 ms). Repeat and record observed timing uncertainty. These trials can
  expose ordering failures but cannot prove their absence or certify exact ties.
- **Named observer:** use a timestamped keydown/keyup/wheel logger on the Deck,
  such as a small browser page added as a non-Steam game with the test layout.
  This observes application-delivered events, not native activator scheduling.
  Exact-sample evidence requires controlled input and a documented sampling path.

### H3. LS vertical has no budget row, and quieting it conflicts with map-only banks

The [P1 budget table](../../plans/2026-09-29-steering-implementation-plan.md#L160)
omits the hardest input: LS up/down while driving. The brainstorm keeps the
selector in the owner ("keep selectors and cleanup in owners"; a bank "must not
… hide the owner's selector"). Under that rule, this one input needs:

- **A delayed or repeating selector:** rule 1 stops an immediate add when LS is
  already held at owner entry.
- **Release handling** for tap and double.
- **Delayed hold-threshold consumption.**
- **A repeating reset,** if that consumption is a delayed `add_layer`. This is
  the documented reset for an interrupted delayed apply.

That straightforward decomposition needs four entries unless some are merged
or moved. It is not a proof that every owner-based architecture needs four;
write actual activator tables before claiming a minimum layer count.

A repeating selector also keeps re-adding Mod 1. Under Mod 2 it could restore or reorder Mod 1 unless
blocked. Re-adding a non-top active layer is itself unverified (M6); even an
apparent no-op is not acceptable during an isolated Always On window.

The repo's established solution is to have **the added layer override its own
selector input**. Base's bumper chords repeat `add_layer` every 50 ms, and the
modifier layer overrides the bumper, so the repeats go silent. Applied here,
the Mod 0/1 banks would own LS vertical and the gesture lifecycle. That
contradicts the map-only rule and changes what "3 banks" means.

**Change:** count this input statically, now. Before P2, choose between two
structures:

- banks own LS vertical, or
- the owner keeps the selector, with extra helpers.

Then update the architecture table. P2.3's "quiet the selector" depends on this
choice.

### H4. Guard selection on release has no demonstrated native mechanism

P4.5 enters "Steering plus the guard selected from current LS state" on Menu
Right **release**. Neither layout contains a chorded `release` (0 of 123 in each
file). In these files, a chord is the only activator form that depends on
another input. The plan therefore has no demonstrated conditional-release
mechanism. Absence from these exports does not prove Steam cannot support one.

Two candidates to prototype:

- **Always add the Guard.** It then retires through a center detector that must
  also fire when LS is **already** centered at add time, which rule 1 says needs
  a delay or repeat. This makes T2's center detector a prerequisite for P4, not
  only for gestures.
- **Use a marker layer.** Deflection inside Transition Set 1 sets it. This costs
  one definition.

The layout already has a concrete T2 candidate: an inverted LS edge
(`edge_binding_invert: "1"`, used by Base's WASD scaffold and RTP: Mouse
Buttons) with a radius below the 13276 dpad deadzone. The native ±10% LS `dpad`
hysteresis is derived from [native-code analysis](../2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#edge-threshold-verification).
These are static calculations, not physical Deck measurements.
A group has only one LS edge, though, so this displaces the WASD Modifier
scaffold in every layer that uses it. That is a user decision, not only an item
to record.

### H5. Bank payloads are owner-gated chords bundled with recovery and consumption

"Extract key/mouse payloads only" ([P2.1](../../plans/2026-09-29-steering-implementation-plan.md#L176))
understates what the source looks like. Every Base modifier face input has
three entries:

- an interruptible repeating **recovery removal**
- an **owner-chord output**, for example `R1: Modifier 1` A: chord RB →
  `key_press H`
- an **owner-chord cover add**

In `L1!R1: Modifier 2`, the output and the tap-consumption change share a single
binding: chord LB → `key_press M` + add `L1&R1: Tap Cover`. The gate is also
what makes a stale bank harmless: once the owner is released, the output chord
goes inactive and the recovery runs.

P2.1 excludes "cover mutations", yet P2.3 requires a modified action to consume
the stroke. Each steering bank input therefore needs a replacement hook. For
each bank, specify:

- **The activator shape** of each input.
- **The output gate:** driving control held (Default either-bumper mask `12`,
  Alternative trigger bits), and/or LS deflection bit 30 for Mod 0/1. A chord
  cannot select a stick direction.
- **The consumption hook.**
- **Stale-bank recovery.**

Both driving controls are held during valid Mod 2, but an either-control gate
remains true after dominant release while the opposite remains held. Establish
dominant validity and ordered cleanup explicitly; that mask alone cannot make
a stale bank harmless. A shared three-bank design remains a candidate, subject
to complete lifecycle tables, rather than a proven payload-only solution.

### M1. Run the existing rule-test first, and rename the gates

Held-input rule 3 is unverified: it says removing a layer fires the exposed
binding on a held input. So is key-output scope on add/remove. The plan leans on
both:

- fallback W and a fresh timer after dominant release (D10)
- Mod 1/0 restoration when the opposite control is released with LS held (D4/D5)
- W output under the Guard after commit
- W→W continuity (T1)

[`rule-test.vdf`](../2026-09-29-held-input-layer-transitions/rule-test.vdf) is
already built. Its T4 probes rule 3 for layer commands, and it includes a
key-output layer. Running it is cheap, but it is currently unscheduled. Run it
before building the steering harness, and feed the result into T1, T4 and T6.

The plan's T1–T9 also collide with rule-test's own T-numbering. The memory index
also refers to "the optional T4" for rule 3. Rename the steering gates, for
example to S1–S9.

### M2. Protection must engage at or below the movement threshold

The guard and the protected menu exist to protect carried WASD. WASD engages at
the 13276 dpad deadzone (about 40%). P4.3 would detect late deflection with the
menu-entry LS edges, which sit at radius 21000. With ±10% hysteresis they engage
near 74% and release near 54%. The threshold behind the AxisDeflection chord bit
is unmeasured. As a result:

- a partial tilt that moves the player will not trigger the transfer
- Base's chord and the entry edges may disagree about "deflected"

Add a threshold-alignment requirement to P4 and T8. Changing those edge radii
also moves the entry layers' existing stale-recovery trigger.

### M3. The transfer interrupts a pending delayed Fn add; test the next press

A late-deflection transfer removes normal Entry while its 300 ms delayed Fn add
may still be pending. That is the documented
[interrupted delayed apply](../../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies)
bug class, and its symptom shows up on the **next** press. It also raises the
question of whether removing the layer cancels the pending add at all
(brainstorm A9).

T8 tests deflection near the deadline but not what happens afterwards. Add both
checks:

- no Fn arrives at 300 ms after the transfer
- a later ordinary centered hold still gets Fn at about 300 ms

### M4. No failure branches; decisions and recommendations are mixed

Each gate states a pass condition. For T1, T3 and T4, a failure only says to
design something different. These three gates decide the architecture, so each
needs at least one named fallback and the user decision it would trigger:

- **T1:** compare entry-input versus owner-input output sites. Accepting a W
  gap changes the contract and requires a behavior decision if neither works.
- **T4:** identify resetting mutations and prototype scoped isolation or a
  separate ordinary-input clock. A separate layer is not proof of timer
  independence; an Always On timeout may only self-remove, not exit the family.
- **T3:** repair exact isolation/exit routes or compare a proven native gesture
  mechanism. Fewer windows alone do not resolve owner-aware exit failures.

"Decisions carried into implementation" also includes items the brainstorm
labels as recommendations: LS-only guard, commit on release, independent Mod 2
face use, and the tie and rearm policies. Add one **open decisions** list,
grouped by the work package each decision blocks:

- commit on release vs. commit on click (H1)
- how the guard is selected (H4)
- displacing the WASD Modifier scaffold (H4)
- RS ramp-up while driving (M5)
- re-entry and exit behavior (M6)
- first-tap policy
- tie and rearm policies

### M5. Inherited Base RS ramp entry is suppressed while driving

Base's RS edge has an uninterruptible empty chord for "modifier role held"
(Default mask `12`, Alternative `50331651`). Steering's driving controls *are*
the modifier-role controls. So while driving, the inherited RS edge never adds
Gyro Off Ramp Up, in either variant. The brainstorm says "RS retains its
existing role". Already-active ramp layers may retain their own behavior;
this finding concerns Base entry, not every ramp lifecycle. Decide what that means:

- Base's no-modifier RS behavior, which needs an override, or
- this inherited suppression.

### M6. Re-entering from inside steering, and `add_layer` on an active layer

Nothing in the plan has Steering override the menu buttons, so Base's selector
stays reachable during steering. The manifest has no row for opening a menu
while steering, or for selecting steering again while Steering is active. In
that case the commit would re-add Steering, which is already active but now sits
below the menu layers. It would also add a Guard over whatever owner or bank is
present.

No doc establishes what `add_layer` does to an already-active layer that is
**not on top**: nothing, or a move to the top. If it moves Steering above an
owner, Steering's bindings would hide the owner's. The answer also matters for
any repeating selector that runs underneath a helper.

**Change:** add a probe for this behavior. Decide what menu→steering does inside
steering: blocked, exit, or restart.

### M7. The plan ignores an existing native directional-scroll precedent

`RTP: Mouse Buttons` (group 242) already scrolls natively on dpad directions.
An uninterruptible Regular Press sends one tick, and a 150 ms `Long_Press` with
Hold to Repeat keeps scrolling. The layouts also use `Double_Press`.

The existing example does not demonstrate action-consumed taps or cancellation
across contexts, and ordinary long-hold repeat contradicts steering hold semantics.
Nevertheless, an interruptible Regular Press plus
`Long_Press` plus a repeating `Double_Press` might cover part of tap/hold/double
without Always On windows. The plan reserves eight new Always On windows, which
would take the current seven to fifteen. Before committing to that, add one
probe of native activators on an LS direction inside a layer. Include whether
their state resets across layer changes. Either way, add group 242 to the
reference table.

### Low

- **L1.** P2 omits the brainstorm's G4 rule that normal repeat suspends
  Mod 0/1 and exposes Base buttons.
- **L2.** "Audit dormant/mode-shift groups as well" is redundant.
  `audit_command_budget.py` already scans every group, inactive ones included.
- **L3.** The first slice names file types but no harness content. Specify its
  layers, bindings, probe keys, observer (H2) and result-sheet template, as the
  rule-test did.
- **L4.** Much of the plan is phrased as prohibitions and disclaimers. Rewriting
  each work package as "build X; it passes when Y" would make it executable in
  a later session.

## Mask verification

This was a read-only check of the installed client's `steamui/chunk~2dcc5aaf7.js`.
It is the same bundle as the September
[selector verification](../2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md),
with an unchanged SHA-256 (`5b4db9a7e27b0d92254fdfc1babfe942027e507a82560b8a64e8ccc090bd6aeb`).

- It declares `k_eGamepadButtonBitMask_AxisDeflectionLeftStick=30` at byte
  offset 9524806, and `k_eGamepadButtonBitMask_AxisDeflectionRightStick=31`.
  So `(1<<30)|(1<<31) = 3221225472`.
- The same enum puts `ButtonBackOrView` at 12 (Menu Left) and
  `ButtonStartOrOptions` at 14 (Menu Right), which matches the decode table.

This verifies which bits are which. It does not measure the deflection
threshold behind those bits (see M2).

## Suggested order

1. **Static work, now:** the H3 count, the H5 activator shapes, the H4 guard
   mechanism, the H2 order-independence analysis and the M4 decisions list.
2. **Run the existing rule-test (M1).**
3. **Build the harness** with the renamed gates, including probes for H1, M3,
   M6 and M7.
4. **Then P1→P5** as the plan describes.
