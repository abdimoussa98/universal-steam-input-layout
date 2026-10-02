# Layer definition of done

**Status:** draft for author review, 2026-09-30.

A layer is done when every section below holds for both variants (default and
alternative). Each section gives the rule in a few bullets and then links to the
full explanation. The linked docs are the source of truth.

## Contents

| # | Section | What it covers |
|---|---|---|
| 1 | [Layer type](#1-layer-type) | What kind of layer this is, which decides how much its cleanup removes |
| 2 | [Placement](#2-placement) | Where it goes in the file so other layers' IDs don't shift |
| 3 | [Activators](#3-activators) | Which Steam activators are allowed, and the three-entry limit |
| 4 | [Entry](#4-entry) | Whether it still works when a button is already held |
| 5 | [Stick-touch release](#5-stick-touch-release) | Lifting a thumb must clear that side's LST or RST layers |
| 6 | [Hold, tap and double tap](#6-hold-tap-and-double-tap) | **The recipe** for chorded delay + repeating reset + release → Double Tap → Double Tap Cover, the stuck-delay bug it works around, and how touch release fits in. Required whenever a layer adds a delay or a double tap |
| 7 | [Cleanup](#7-cleanup) | Normal exit, recovery from stuck layers, and which other layers must remove this one |
| 8 | [Inheritance and blocking](#8-inheritance-and-blocking) | What a layer picks up from the layers below it, when to block that, and what a block looks like |
| 9 | [Always On layers](#9-always-on-layers) | Ordering rules for the Double Tap windows. What they block comes from §8 |
| 10 | [Ship it](#10-ship-it) | Audits, tests, Deck checks and publishing |
| 11 | [Stateful layers](#11-stateful-layers) | A stateful layer is entered and left through the transition structure. Only for stateful layers |
| – | [Open questions](#open-questions) | Decisions for the author |

Main references: [Steam Input JSON Structure](Steam%20Input%20JSON%20Structure.md)
(**JSON Structure** below) and [Layout Vocabulary](Layout%20Vocabulary.md).

---

## 1. Layer type

Choose the layer's type first. The type sets how much its cleanup removes.
The author accepted these types on 2026-09-30, and more may be added later.

| Type | Examples | What its cleanup removes |
|---|---|---|
| Stateful | `Gyro`, `Steering` | Removed only by its own deliberate exit. Other layers' cleanup never removes it. See [§11](#11-stateful-layers) |
| Owner | Modifiers, Menu Entry and Fn layers, the two menu stick guards, Scroll, Transition Sets, trackpad modes | Its family or current branch, plus every overlay it applied |
| Overlay | Tap Covers, Double Tap Covers, Temp Cursor Gyro | Itself, or a local pair. The owner handles recovery when it gets stuck |
| Stick-touch helper | `LST` or `RST` `Entry Point`, `Tap Cover` and `Temporary Gyro` | Every layer removes it when the thumb lifts off that stick ([§5](#5-stick-touch-release)) |
| Always On window | The nine Double Tap layers, including `Steering \| LS Up/Down: Double Tap` since 90.10 | Only itself ([§9](#9-always-on-layers)) |
| Ramp or threshold | `Turning Ramp Up 0/1`, `Gyro Off Ramp Up` | Itself and the ramp family, through repeating threshold exits |

**Exception (author, 2026-09-30):** the quick opposite-modifier tap in every
Modifier 2 layer (`Gyro | …` and `Steering | …`) is a deliberate "clear to
Base" gesture. It removes every layer, including the stateful `Gyro` and
`Steering`.

See: [Vocabulary](Layout%20Vocabulary.md#terms) ·
[Cleanup scopes](Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) ·
[Steering per-layer exits](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md#per-layer-exit-review)

## 2. Placement

- Use explicit `add_layer` / `remove_layer` for every lifetime; never
  `hold_layer`. Never switch action sets (`CHANGE_PRESET`); modes are layers
  within Base. See [runtime rules and existing conflicts](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).

- Append the layer to the **end** of `action_layers` as `Preset_<max+1>`, so
  no existing runtime ID shifts.
- Keep the list order the same as the `Preset_` numeric order. Otherwise a
  fresh load can swap layers.
- Give it a unique title, and edit in `{{Base::Title}}` token form.
- Mirror it into the alternative layout, where L1/R1 become L2/R2.

See: [layout-prep skill](../.claude/skills/steam-layout-prep/SKILL.md) ·
[layer-duplicate skill](../.claude/skills/steam-layer-duplicate/SKILL.md) ·
[layer-order swap](../findings/2026-07-11-layer-order-swap/FINDINGS.md)

## 3. Activators

- Use only **Regular, Chorded, Start, Release and Soft Press**. Never use Long
  Press or Double Press. Build a hold as a chorded delay and a multi-tap as a
  layer window.
- Each input can have **at most three command entries**. Subcommands inside an
  entry don't count toward the three. The limit exists because Steam's desktop
  configuration drops every entry after the third. The only exception is a
  delayed-apply reset as a 4th entry, and it must be **last** so it's the one
  that gets dropped.
- Subcommand arrays run **bottom to top**.
- **On a D-pad-mode stick, an inverted edge never adds or removes a layer**
  (author rule, 2026-10-01). It isn't caught reliably there. Use a normal
  outer edge and its Release. An inverted edge that only sends output, such
  as a walk bind or the WASD modifier, is fine. Mouse-mode sticks aren't
  affected; the ramp-up's Soft Press exits work.
  - The Budget audit fails on it since 90.10 (`inverted_edges`). Steering's
    left-stick layers were the only violators and now end on the edge's
    Release.
- **Chords latch** (author's test, 2026-10-01). A bind can't hand over from a
  chord to another activator when the chord button is released; it stays in
  the chord until its own button is released.

See: [Allowed activators](Steam%20Input%20JSON%20Structure.md#allowed-activation-types) ·
[Entry budget](Steam%20Input%20JSON%20Structure.md#command-entry-budget) ·
[Execution order](Steam%20Input%20JSON%20Structure.md#binding-execution-order) ·
[binding-order skill](../.claude/skills/steam-binding-order/SKILL.md)

## 4. Entry

- When a layer is added, its immediate layer command **doesn't fire on an
  input that's already held**. Give that command Hold to Repeat, or add the next
  layer in the same array.
- **This rule covers the layer API only** (author, 2026-10-01): `add_layer`,
  `remove_layer` and `hold_layer`. It doesn't cover key or mouse outputs. The
  author's experience is that an output does fire on an already-held input
  when its layer is added; this hasn't been tested on the Deck in isolation.
- Delayed applies do fire on a held input. Keep short delays such as the 5 ms
  delay.
- Anything that must fire after a removal needs Hold to Repeat. How removals
  affect held inputs is unverified.

See: [Held inputs](Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes) ·
[Held-input audit](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)

## 5. Stick-touch release

**Author rule, 2026-09-30: every layer binds this explicitly. Only cover-type
layers may inherit it.** A cover-type layer is a lightweight layer that is only
ever added on top of another layer. There's no strict definition yet; it's a
judgment call. Current cover-type layers:
- the Tap Covers and the Double Tap Covers, including the steering
  `LS: Tap Cover` and `LS: Double Tap Cover` (since 90.7) and
  `Menu Buttons: Tap Cover` (since 90.10). The two menu stick guards are not
  covers: they bind both stick touches with their own recovery
- Temp Cursor Gyro
- `Gyro Off Ramp Up`. Its only delay is a 5 ms right-stick handoff to
  `Turning Ramp Up 0`, which is a threshold handoff rather than a hold, so a
  thumb release has nothing to complete.

**Always On windows bind it too, but remove themselves first.** Each Double
Tap window's touch release removes the window, then that side's trio (the
self-removal is stored last, so it runs first). The LST/RST windows' own stick
has no release: touching it again is the second-touch transition, which also
removes the window first ([§9](#9-always-on-layers)).

- **LS touch release** removes `LST: Entry Point`, `LST: Tap Cover` and
  `LST: Temporary Gyro`. **RS touch release** removes the same three RST layers.
- Each release clears only its own side. It never removes `Gyro`, the other
  stick's layers, or an owner that's still valid.
- Defining any activator on a stick's touch input **replaces the whole
  inherited input**, so include that input's guarded recovery as well.
- Every other layer defines both touch inputs itself, even if a trace suggests
  inheritance would work. That includes stateful layers, owners, helpers and
  ramp layers.
- **Other accepted exceptions** (author, 2026-09-30):
  - `Gyro` is the base stateful layer and always sits directly on Base, so it
    inherits Base's touch inputs.
  - `LST/RST: Entry Point`, `Tap Cover` and `Temporary Gyro` are the layers
    that the release removes. They need a release only on their own stick,
    not the opposite one.
- A static check on 2026-09-30 found every other layer compliant after
  [`Transition Set 0` was patched](../findings/2026-09-30-touch-release-rule/README.md).

See: [Touch-release rule](Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release) ·
[Steering cleanup audit](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md#findings-and-changes)

## 6. Hold, tap and double tap

This section is one concept. The chorded delay, the repeating reset, the
release into a Double Tap window, the Double Tap Cover, and the stick-touch
release all belong to the same recipe. **Any layer that adds a delay or a
double tap must implement the whole recipe, or record which part it leaves
out and why.** Recorded so far: the steering double tap
([deviations](../findings/2026-09-30-steering-lean/README.md#recipe-deviations-dod-6)).

### The bug it works around: the stuck delay

If a delayed `add_layer` is interrupted before its delay finishes, it can fail
to fire on the **next** entry. The hold then silently stops working. The
author observed that a **repeated `remove_layer` of the same target restarts
the delay**, so the add fires again. This is the author's runtime observation,
not a confirmed Steam internal. On 2026-09-30 the author clarified the
reset outcome: restart and wait 300 ms in the discussed case, not cancellation.
Other configured delay values remain distinct.
([Interrupted applies](Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies) ·
[R1 tap-cover findings](../findings/2026-09-27-r1-tap-cover/FINDINGS.md))

### The recipe, using Menu Left as the example

These are the actual default-layout bindings. The modifiers follow the same
shape: L1 → `L1: Double Tap` → `L1: Scroll Down` → `L1: Double Tap Cover`.

```
Base: Select press
  └─ Menu Left: Entry Point ............ (1) parent: tap or hold?
       ├─ hold 200 ms ──► Menu Left: Fn Layer          (hold result)
       └─ release ──────► Menu Left: Double Tap ....... (2) Always On window, 150 ms
            ├─ timeout ──► window removes itself        (single tap)
            └─ 2nd press ► Menu Left: Escape .......... (3) second-press layer
                 ├─ hold 150 ms ► Menu Left: Double Tap Cover  (4) cover
                 │                 └─ release ► remove Escape + cover (done)
                 └─ release ──► Menu Left: Double Tap again (tap chain)
```

**(1) Parent layer.** The primary button uses three entries:

| Entry | Settings | Does |
|---|---|---|
| Chord (hold) | `delay_start: 200` | Adds the hold target, `Menu Left: Fn Layer` |
| Regular Press (**reset**) | `hold_repeats: 1`, `repeat_rate: 250`, `interruptable: 0` | Removes **only** that same target, which restarts a stuck delay |
| Release (tap) | — | Removes the parent, then adds `Menu Left: Double Tap` **last** |

Both stick-touch releases in the parent **complete the pending hold first**
(add `Fn Layer`, last in storage), then clear the LST or RST trio. So a thumb
lift finishes the hold early instead of resetting its timer. See [§5](#5-stick-touch-release).

**(2) Double Tap window.** It's an Always On layer, so all of [§9](#9-always-on-layers)
applies:

- It times out by removing only itself after 150 ms (200 ms for LST and RST).
- It can send a delayed single-tap output. Menu Left sends Escape at 50 ms.
- A second press removes the window **first**, then adds the second-press
  layer.
- Every other layer change is blocked while it's active.

**(3) Second-press layer.** The button holds or repeats its output (the
Escape key, or the scroll wheel for modifiers). A 150 ms chord adds the Double
Tap Cover, and a 200 ms repeating reset protects it. The reset is a **4th
entry, placed last**; see the
[change record](../findings/2026-09-30-second-press-cover-reset/README.md).
Release goes back into a Double Tap window, which is what lets rapid taps
chain. Its touch releases add the cover first, then clear the trio.

**(4) Double Tap Cover.** It keeps the output, and its release cleans up
without opening another window. It has no Always On action.

### Checks for this recipe

- [ ] **Reset present.** Every delayed `add_layer` has a Regular Press on the
      same input in the parent that removes only that target, with
      `hold_repeats: 1` and `interruptable: 0`. If there's no reset, record the
      exception. The known deliberate exception is RTP touch, because the
      reset breaks trackball momentum. If the input is already full, add the
      reset as a **last** 4th entry ([§3](#3-activators)).

      See the [reset coverage table](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md#coverage-at-a-glance).
- [ ] **Reset interval is longer than the delay**, so a healthy apply lands
      before the first reset. The current pairs are 150/200, 200/250, 250/300
      and 300/350. The +50 ms spacing is a convention, not a proven formula.
- [ ] **The hold target overrides the parent's primary input.** That is what
      stops the reset from removing the target once it has been applied. The
      reset must never strip a cover that has already been applied.
      ([cursor follow-up](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up))
- [ ] **The release adds the window last**, and the window's second press
      removes the window first ([§9](#9-always-on-layers)).
- [ ] **Touch releases complete the pending add**, then clear the trio. Once the
      add completes, covers get cleanup-only touch releases so a thumb lift
      can't re-add the parent's target.
- [ ] **The cover's release doesn't reopen the window.**
- [ ] **A delayed apply needs no repeat** to fire over a held input. Keep short
      delays such as 5 ms ([Held inputs](Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes)).

### Other delays

- **Output, haptic, exit timer or direction-dependent routing:** don't complete
  these on thumb release. Direction routing keeps its direction condition.
- **Any pending timer:** block unrelated layer changes while it's pending,
  because removals reset timers.

See: [Complete delayed applies](Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release) ·
[Blocking for timers](Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) ·
[Reset audit](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md) ·
[Steering delay handling](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md#delay-classification-and-ordering)

## 7. Cleanup

- **Normal exit:** it fits the layer's type ([§1](#1-layer-type)) and removes
  only the state it owns.
- **Stuck-layer recovery (owners only):** put an owner-held chord and an
  interruptible, repeating Regular Press removal on the inputs likely to be
  used next. Guard against every valid owner. Remove the family and the
  overlays it applied.
- **Stick edges:** add edge cleanup only where it's needed. Using the LS edge
  costs the WASD modifier, and using the RS edge costs ramp-up.
- **Other layers' cleanup lists:** add the new layer's removal only where that
  list's scope covers it. Overlays go into their owner's recovery, and family
  members go into their family's exits. Never add it to the other side's lists
  or to a persistent mode's lists.
- **Inheritance and blocking** have their own section, [§8](#8-inheritance-and-blocking).

See: [Cleanup Functions](Cleanup%20Functions.md) (draft definitions of every kind) ·
[Stuck layers](Steam%20Input%20JSON%20Structure.md#stuck-layers-and-why-there-is-so-much-cleanup) ·
[Guarded recovery](Steam%20Input%20JSON%20Structure.md#guarded-recovery-binding-shape) ·
[Overlay ownership](Steam%20Input%20JSON%20Structure.md#overlay-cleanup-ownership) ·
[Stick edges](Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions) ·
[Cleanup audit](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md)

## 8. Inheritance and blocking

Steam overrides **whole inputs**. Any input a layer doesn't define comes from
whatever is below it. That can be any layer, including a stale one left behind
by a missed release, not only the usual parent. So a layer inherits more than
its JSON shows, and a change to a lower layer reaches upper layers whose JSON
never changed.

### When to block

Inheritance is the default, and usually it's what we want. Overlays inherit
their owner's recovery and gameplay output. Block only while something must
not be disturbed:

| While… | Block | Because |
|---|---|---|
| An Always On layer is active | Every inherited layer command | Historical crash ([§9](#9-always-on-layers)) |
| A delayed add is pending | Inherited removals that could reset its timer | Removals restart delays ([§6](#6-hold-tap-and-double-tap)) |
| A valid owner is held | The owner's own stale-state recovery, using a guard chord | Recovery would tear down a live interaction ([§7](#7-cleanup)) |
| A menu interaction is active | Gameplay routes such as gyro and RS edge | The author's deliberate menu suppression |

### What a block looks like

**Author rule, 2026-09-30: clear first, and replace only where the context
makes it obvious.**

- **Block only the routes that change layers.** Target an inherited input only
  if its binding contains `add_layer`, `remove_layer` or `hold_layer`, directly
  or through a mode shift. Key, mouse and movement output pass through.
- **Default: clear the input.** That means the GUI's cleared binding, which is
  assumed to be saved as `controller_action empty_binding`. When in doubt,
  clear.
- **Replace when there's an obvious contextual use.** Give the input a static
  output with no layer command. For example, the modifier Double Tap windows
  replace the bumper, which normally adds a layer, with the scroll wheel, so
  the button stays useful during the short window.
- **Never block with a removal.** A `remove_layer` is itself a layer change. It
  resets timers, and inside an Always On layer it's exactly what's forbidden.
- **Other block shapes:**
  - a conditional empty chord blocks only while its selector is held
  - a disabled source quiets the whole trackpad or gyro, including its output
  - a group in a different source mode blocks the whole source
    ([below](#a-source-mode-change-blocks-inheritance))
- **Watch the whole-input override.** Clearing or replacing an input drops
  *all* of its inherited activators. Record what's lost; for example, blocking
  LS edge loses the WASD modifier.
- **These are not blocks:**
  - an omitted input
  - an empty `inputs` object
  - an `inactive` group
  - an `empty_binding` inside an array that also has real actions
- **Existing empty bindings may be protecting a timer.** Find out what one
  protects before you replace it.

### A source-mode change blocks inheritance

**Author rule, 2026-10-01: inputs don't inherit between modes.** When a layer
binds a source in a different mode from the layers below it (for example a
`dpad` trackpad over Base's `absolute_mouse` pad), none of that source's
lower inputs carry over, including inputs the upper group leaves unbound. The
mode change is itself the block; no extra clear is needed.

Example: the RTP Double Tap window's right pad is in `dpad` mode and binds no
`touch`. Base's mouse-mode `touch` (which adds `RTP: Entry Point`) does not
fire inside the window, so a second touch only fires the window's own regions.

Both [audit_inheritance.py](../audit_inheritance.py) (blocked kind
`mode replaced`) and [audit_flow_inheritance.py](../audit_flow_inheritance.py)
apply this rule.

### How to check it

**Author rule, 2026-09-30, restated by the author on 2026-10-01. It applies
to a layer with an Always On action, and to no other layer:**

1. Trace every stack the layer can be applied on.
2. For each input the layer leaves open, look at the bindings it could
   inherit from those stacks.
3. If one of them is a layer command, the layer must handle that input for
   its whole lifetime.
4. How:
   - **Clear** it if more than one keybind is possible underneath. A
     hard-coded replacement would be wrong in some stack.
   - **Replace** it with the keybind if there is only one, for example always
     E or always middle mouse.
   - **A stack whose binding is only a layer command adds no keybind**
     (author, 2026-10-01). Under `Gyro Off Ramp Up` a trigger soft pull only
     removes that layer, so the one keybind is Base's mouse button and the
     window keeps it. Until 90.9 the audit counted that stack as a second,
     empty keybind and cleared the input.
   - If no stack gives a keybind, clear it.

If none of the bindings it could inherit is a layer command, the input is
left alone, even when the keybinds differ between stacks. An ordinary layer
inherits by default; it is never required to block an input because the
layers below would give it different bindings.

The **Window audit** ([audit_inheritance.py](../audit_inheritance.py)) checks
this rule. The **Flow audit**
([audit_flow_inheritance.py](../audit_flow_inheritance.py)) runs the cover
check ([§5](#5-stick-touch-release)), checks that a chain reaches every
layer, and lists inherited bindings that differ between stacks as
information. Until 2026-10-01 it failed on those for every layer, which
misread step 4 as a rule of its own. Both audits build their stacks from the
same backward chains and run in the build audit ([§10](#10-ship-it)):

```bash
python3 audit_inheritance.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_inheritance.py <layout> --entries "Menu Left: Double Tap"   # who adds it, what they remove first
python3 audit_layer.py <layout> --layer "Menu Left: Fn Layer"             # below, above, inherited, exits
```

For one layer, [audit_layer.py](../audit_layer.py) prints what can be below
and above it, each inherited input with the layer it comes from, and what
each of its exits removes against what can be present. The exits lists are
for review against [§7](#7-cleanup); they aren't a check.

1. **It builds the stacks backwards** (since 2026-10-01,
   [chains.py](../steam_layout/chains.py)). It starts at the layer and asks
   which bindings add it, then which add those layers, back to Base. Each
   chain gives one stack, and applies the whole binding, so a parent that
   removes itself isn't underneath.
   - A step only counts if its layer answers that input on the stack so far.
   - Between two steps a cover may lift (a removal-only binding), and one
     other layer may arrive.
   - **Bystanders:** any other layer stays underneath if it leaves the
     chain's inputs alone and the chain doesn't remove it. This is how
     `Gyro Off Ramp Up` ends up under a bumper window.
   - There is no depth cap and no config, so the Steering layers are reached
     like any other. Every Always On layer is audited automatically.
   - Chords are ignored (author, 2026-10-01): every adding binding is
     followed. That can add a stack that can't happen, never drop one that
     can. Missed releases, `hold_layer` and three families overlapping are
     not covered.
2. **A window no stack reaches fails** as "not checked". Each open route is
   printed with the bindings that built its stack. `--depth 5` adds the older
   depth-limited search as a comparison; it is off by default and deprecated.
3. **It finds the routes.** For each input the layer doesn't define, the
   topmost lower binding in each stack is the effective one. If it changes
   layers, directly or through a mode shift, that's a route. Inputs the layer
   clears, replaces or disables count as blocked.
4. **It recommends the block.** `blocks_needed` says replace (with the exact
   activators) or clear, following the rule above.
   [window_routes.py](../steam_layout/fixes/window_routes.py)
   applies the recommendations to the Always On windows during the install.
5. **Exceptions go in [traced_stacks.json](../traced_stacks.json):** `allow`
   with a reason, or `todo` while it awaits the author. The file can also add
   stacks the search can't reach. An undecided `open` route fails the check.
   A different source mode above the definer is a block, not a route
   ([below](#a-source-mode-change-blocks-inheritance)).
6. **The test enforces it.** [test_audit_inheritance.py](../tests/test_audit_inheritance.py)
   fails when a change opens an undecided route or breaks saturation in the
   working layouts.

See: [Inheritance review](Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) ·
[Blocking for timers](Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) ·
[Blocking audit: types](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#types-of-blocking-in-use) ·
[Blocking audit: inherited routes](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#inherited-route-review-and-remaining-uncertainty) ·
[Cursor self-removal inheritance](../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md)

## 9. Always On layers

This section applies to any layer with an `always_on_action`, which currently
means the nine Double Tap windows.

1. **Entry:** make every other layer change first, and add the Always On layer
   **last**.
2. **While it's active:** block every inherited layer command, as described in
   [§8](#8-inheritance-and-blocking).
3. **Timeout:** remove only this layer.
4. **Early exit:** remove this layer **first**, then make the other changes.

**Trackpads (author, 2026-09-30):** both pads stay off the layer API during
every window.
- **Left pad:** the swipes send their keys directly: back is Escape, forward is
  Enter, up is Tab, down is Backspace. They don't add the key layers. Click
  and touch are cleared.
- **Right pad:** stays the mouse, so the cursor keeps moving. Click and touch
  are cleared, and the mouse feel inherits from Base. RTP Double Tap keeps its
  own D-pad selection pad, with `click` cleared and no touch bind (see below).

See the [change record](../findings/2026-09-30-double-tap-pad-blocks/README.md).

**Current coverage of rule 2** (derived stacks, depth 5, 2026-09-30): there
are no open routes in any of the seven windows in either layout. The derived
stacks found routes that the earlier hand-traced stacks missed. Most are now
cleared, and one is a deliberate exception
([change record](../findings/2026-09-30-derived-window-blocks/README.md)):
- **Trigger edges, all nine default windows:** `Gyro Off Ramp Up` can sit
  under any window, and its edge removes it. The only keybind underneath is
  Base's left or right mouse button, so since 90.10 the edge is replaced
  with it. It was cleared from 90.6 to 90.9.
- **Right-pad `touch`, RTP Double Tap: blocked by the mode change** (author,
  2026-10-01). The window's D-pad-mode pad is its own second-tap selection: a
  second tap north or south goes to Circular Scroll, and anywhere else leaves
  the window and stays in mouse mode. Base's mouse-mode touch doesn't inherit
  into the dpad-mode pad ([mode rule](#a-source-mode-change-blocks-inheritance)),
  so no touch bind is needed. The former `allow` decision was retired.
- **The four back buttons, RTP Double Tap:** the Fn layers can be underneath
  if you hold a menu button and quick-tap the right pad.
- **Since 90.10** ([record](../findings/2026-10-01-stateful-transitions/README.md)):
  - **Left-stick up and down, the two menu windows:** Steering can sit under
    them, and its hold-exit clock would show through. Both are replaced with
    plain W and S.
  - **The two Steering windows** bind the stick and both drivers themselves.
    Derived on top, because a ramp layer can be added while in Steering: in
    the default layout the trigger edges keep the mouse buttons; in the
    alternative the bumpers keep the mouse buttons and the trigger clicks,
    which have no keybind underneath, are cleared.

**Stick clicks, face buttons and D-pad:** the derived stacks never put a layer
command under them in a window, so they stay inherited. `--untraced` still
lists which layers use them for layer commands, for review.

See: [Always On isolation](Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround) ·
[LS-edge blocks](../findings/2026-09-28-left-stick-recovery/CHANGES.md#always-on-isolation) ·
[Cursor blocks](../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md#all-seven-always-on-windows)

## 10. Ship it

- [ ] **The build audit is clean, on every version.** `python3 audit_build.py`
      runs the three audits below on both variants and exits 0 only when all
      pass. No version ships with a failing line.

      | Audit | Script | Clean means |
      |---|---|---|
      | Budget audit | `audit_command_budget.py` | Three entries per input, no banned activators, and no layer command on an inverted D-pad stick edge ([§3](#3-activators)) |
      | Window audit | `audit_inheritance.py` | No undecided layer command under an Always On window ([§8](#8-inheritance-and-blocking), [§9](#9-always-on-layers)) |
      | Flow audit | `audit_flow_inheritance.py` | A chain of adding bindings reaches every layer, and no cover finding is open ([§5](#5-stick-touch-release), [§8](#8-inheritance-and-blocking)) |

      What a clean build audit doesn't prove: it follows the intended flows,
      not every runtime interleaving, missed release or timer race. Those are
      what the Deck checks are for.
- [ ] **A new layer needs no declaration.** The audits pick it up from the
      layout. If no binding adds it, the Flow audit reports it as a coverage
      gap. Only two things go in
      [flow_config.json](../steam_layout/flow_config.json): a cover whose
      title doesn't end in a cover suffix, and an accepted cover finding or
      unsupported lookup, with a reason. A decision that no longer matches
      anything is reported as stale.
- [ ] The tests pass, and a new invariant gets a new test.
- [ ] The change is recorded in `findings/<date>-<slug>/`.
- [ ] A Deck section is added to [manual-testing.md](../manual-testing.md). It
      covers an input held across the change, a press inside the layer, and a
      release missed while the Steam menu is open.
- [ ] The [layout-apply skill](../.claude/skills/steam-layout-apply/SKILL.md)
      has run: description, version bump, `to-ids`, VDF export and snapshot.

## 11. Stateful layers

This section applies only when a stateful layer is added or changed. The
structure is in [Stateful Layer Transitions](Stateful%20Layer%20Transitions.md).
It was agreed on 2026-10-01 and is built since 90.10; Deck validation is
pending.

The check is whether the transitions behave as that document says.
[test_stateful_transitions.py](../tests/test_stateful_transitions.py) asserts
it on the generated layouts, and is extended with every new stateful layer
until all four gestures are taken.

- [ ] **Gesture.** The layer is entered by one of the four menu-plus-stick-click
      gestures, and the gesture map is updated.
- [ ] **Entry.** The Base Entry Point sends that click's Release to the right
      transition, and the transition's menu Release adds the layer.
- [ ] **Transition feedback.** Every menu Release in a transition beeps and
      gives a high haptic pulse (author, 2026-10-02), entering or clearing:
      `haptic_intensity` 3 on the Release, and the beep flag on the stateful
      layer's `add_layer`, or on the transition's own removal when nothing
      is added. No on-screen notification.
- [ ] **Exit.** Inside the layer, every one of the four gestures leads to the
      clear transition. The layer has Entry Points for that, added by its own
      menu press.
- [ ] **Fallback.** The Modifier 2 clear removes the layer and its helpers.
- [ ] **Clean entry.** At entry the layer has no Release or delayed binding on
      Start or Select. A repeating press that adds its Entry Point, like
      Base's, is allowed (author, 2026-10-01).
- [ ] **No layer is entered from a transition.** Every layer-adding input
      underneath is blocked with an empty binding.
- [ ] **Recipes.** Nothing depends on a chord handing over when the chord
      button is released, or on an inverted edge of a D-pad stick adding or
      removing a layer ([§3](#3-activators)).
- [ ] **Test and Deck checklist** are updated for the new layer.

**Exceptions (author, 2026-10-01):**
- `Gyro` is toggled by the Modifier 2 release and is left on by the clear.
- The Modifier 2 clear and Steering's W/S hold exit skip the transition.
- Stateful Cursor Gyro will also clear the way Temp Cursor Gyro does. An extra
  exit like these is allowed; the menu-plus-click clear and the Modifier 2
  clear are never dropped.
- The planned Menu stateful layer won't use this structure.

See: [Stateful Layer Transitions](Stateful%20Layer%20Transitions.md) ·
[brainstorm record](../plans/2026-10-01-stateful-layer-transitions.md) ·
[runtime rules](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)

## Open questions

None. Deck validation is tracked in [manual testing](../manual-testing.md).
