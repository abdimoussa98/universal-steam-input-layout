# Steam Input JSON Configuration Structure

This document describes the structure and relationships within Steam Input controller configuration files (JSON format converted from VDF).
For player-facing names of the hold and second-hold paths, see
[timed gestures](Layout%20Vocabulary.md#timed-gestures). Layer titles such as
`Tap Cover` and `Double Tap Cover` remain exact technical identifiers here.

**References:**
- [Steam Input Action Sets & Layers Overview](https://partner.steamgames.com/doc/features/steam_controller/iga_file)
- [Action Set Layers Behavior (overlay/stacking)](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers)

## Current project policy

**Rules: R101, R102** (Layer Definition of Done [§2](Layer%20Definition%20of%20Done.md#2-placement)). This section explains them; the rule text is there.

The API descriptions below include historical and generic format capabilities.
Current layouts must use explicit `add_layer` / `remove_layer`, never
`hold_layer` or action-set switching (`CHANGE_PRESET`). See the
[author-confirmed runtime rules and migration conflicts](Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).

## Overview

Steam Input configurations define how a controller's physical inputs map to game actions. The JSON structure contains several interconnected sections that work together to define a complete controller layout.

## Top-Level Structure

```json
{
  "controller_mappings": {
    "version": "3",
    "revision": "...",
    "title": "...",
    "description": "...",
    "controller_type": "controller_neptune",
    "actions": { ... },
    "action_layers": { ... },
    "localization": { ... },
    "group": [ ... ],
    "preset": [ ... ]
  }
}
```

---

## Section Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        controller_mappings                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐         parent_set_name         ┌──────────────┐  │
│  │   actions    │◄────────────────────────────────│action_layers │  │
│  │ (Action Sets)│                                 │   (Layers)   │  │
│  └──────┬───────┘                                 └──────┬───────┘  │
│         │                                                │          │
│         │ Preset_ID (key)                               │ Preset_ID │
│         │                                                │          │
│         ▼                                                ▼          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                         preset[]                             │   │
│  │  (Contains controller bindings for each Action Set/Layer)   │   │
│  │  - "name" field matches Preset_ID from actions/action_layers│   │
│  └──────────────────────────────┬──────────────────────────────┘   │
│                                 │                                   │
│                                 │ group_source_bindings             │
│                                 │ (IDs reference groups)            │
│                                 ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                          group[]                             │   │
│  │  (Defines input modes and actual key/button bindings)       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Section Descriptions

### 1. `actions` (Action Sets)

Action Sets are the top-level containers for controller configurations. A controller can switch between different Action Sets based on game context (e.g., on-foot vs. driving).

**Structure:**
```json
"actions": {
  "Preset_1000001": {
    "title": "Base",
    "legacy_set": "1"
  },
  "Preset_1000014": {
    "title": "Gyro",
    "legacy_set": "1"
  }
}
```

**Key Points:**
- The **key** (e.g., `"Preset_1000001"`) is the unique identifier for the Action Set
- `title` is the human-readable name displayed in Steam Input
- This key is referenced by:
  - Action Layers via `parent_set_name`
  - Presets via `name`

---

### 2. `action_layers` (Layers)

Action Layers are modifiers that overlay on top of Action Sets. When a layer is active, its bindings temporarily replace or supplement the parent Action Set's bindings.

**Structure:**
```json
"action_layers": {
  "Preset_1000006": {
    "title": "L2",
    "legacy_set": "1",
    "set_layer": "1",
    "parent_set_name": "Preset_1000001"
  }
}
```

**Key Points:**
- The **key** (e.g., `"Preset_1000006"`) is the unique identifier for the layer
- `title` is the human-readable name
- `set_layer`: Always `"1"` to indicate this is a layer (not a set)
- **`parent_set_name`**: References the Action Set this layer belongs to
  - Example: `"Preset_1000001"` links to the "Base" Action Set

**Relationship:** Each Action Layer **must** have a `parent_set_name` that matches a key in the `actions` block.

---

### 3. `preset[]` (Preset Bindings)

Presets contain the actual controller binding configurations for both Action Sets and Action Layers. Every Action Set and Action Layer has a corresponding entry in the preset array.

**Structure:**
```json
"preset": [
  {
    "id": "0",
    "name": "Preset_1000001",
    "group_source_bindings": {
      "10": "switch active",
      "11": "button_diamond active",
      "12": "joystick active",
      "126": "gyro inactive"
    }
  }
]
```

**Key Points:**
- `id`: Numeric identifier within the preset array
- **`name`**: Matches the Preset_ID key from either `actions` or `action_layers`
  - Action Set preset: `"name": "Preset_1000001"` → matches `actions["Preset_1000001"]`
  - Layer preset: `"name": "Preset_1000006"` → matches `action_layers["Preset_1000006"]`
- **`group_source_bindings`**: Maps group IDs to input sources and states
  - The **numeric key** (e.g., `"10"`, `"126"`) is the Group ID
  - The **value** specifies the input source and state (e.g., `"switch active"`, `"gyro inactive"`)

**Relationship:** The `name` field connects a preset entry to its corresponding Action Set or Action Layer definition.

---

### 4. `group[]` (Input Groups)

Groups define the actual input configurations—what physical inputs do and how they behave. They contain the key bindings, activators, and input settings.

**Structure:**
```json
"group": [
  {
    "id": "0",
    "mode": "four_buttons",
    "name": "",
    "description": "",
    "inputs": {
      "button_a": {
        "activators": {
          "Full_Press": {
            "bindings": {
              "binding": "key_press SPACE, Jump, , "
            }
          }
        }
      },
      "button_b": { ... },
      "button_x": { ... },
      "button_y": { ... }
    },
    "settings": {
      "button_size": "17994",
      "button_dist": "19994"
    }
  }
]
```

**Key Points:**
- **`id`**: Unique identifier referenced by `preset[].group_source_bindings`
- `mode`: Input type (e.g., `"four_buttons"`, `"dpad"`, `"absolute_mouse"`, `"joystick"`, `"gyro"`)
- `inputs`: Contains the actual button/input definitions
  - Each input has `activators` defining what happens on press/release
  - `binding` format: `"key_press KEY, Label, , "`
- `settings`: Mode-specific configuration options

#### Allowed Activation Types

**Rule: R108** (Layer Definition of Done [§3](Layer%20Definition%20of%20Done.md#3-activators)). This section explains it; the rule text is there.

**Hard requirement for this repository: use only these activation types.**
The layout author reports that Steam's Long Press and Double Press activators
misbehave when combined with the action layers this layout depends on. Build
every hold threshold and multi-tap gesture from the allowed types and layers.

| Steam GUI name | JSON key under `activators` | Allowed |
|---|---|---|
| Regular Press | `Full_Press` | Yes |
| Chorded Press | `chord` | Yes |
| Start Press | `Start_Press` | Yes |
| Release Press | `release` | Yes |
| Soft Press | `Soft_Press` | Yes |
| Long Press | `Long_Press` | **No** |
| Double Press | `Double_Press` | **No** |

The rule covers every group, including inactive sources, mode-shift targets and
unreferenced groups, because a dormant activator becomes live when its source
is enabled or its group is reattached.

**One exception (author, 2026-10-03, since 90.22):** Start and Select in the
`Gamepad` layer each have a Regular Press, a Double Press and a Long Press.
`Gamepad` binds every input, so no layer can be added over it (R168), and the
bug is with layers. The exception is one entry in the exceptions register,
which the Budget audit reads; anywhere else the two types still fail. It rests
on A43 and A44, which are not verified. Timing settings on allowed activators,
such as `delay_start`, `hold_repeats` and `repeat_rate`, are fine.

Replacements:

- **Hold threshold (instead of Long Press):** a chorded delay, which is a
  `chord` with `delay_start`. The chord condition can be a button or stick
  deflection. In the modern mask, LS deflection is bit 30 (`1073741824`); see
  the [guarded recovery example](#guarded-recovery-binding-shape). A stick
  direction can't be a chord button, so chord a direction on its stick's
  deflection. When the delayed action adds a layer, pair it with the same
  input's repeating removal. The existing pattern is the Mod 2 opposite cover:
  chord `delay_start 200` adds the cover, and Regular Press `hold_repeats` at
  250 ms removes it. See [Interrupted Delayed Layer Applies](#interrupted-delayed-layer-applies).
- **Multi-tap (instead of Double Press):** a layer-based window, as the
  existing Double Tap and Double Tap Cover layers do. The first press or
  release adds a window layer; a second press inside the window acts, and the
  window's own timed exit ends it.

**Enforced.** `audit_command_budget.py` fails (exit 1) on any `Long_Press` or
`Double_Press`, in enabled or disabled banks of any group, and reports
unreferenced groups and plain-inactive slots. The `steam-layout-apply`
pre-flight already requires exit 0. Release 90.6 removed the last violations:

- Steering's six Long Press timers became chorded delays
  ([plan](../plans/2026-09-30-steering-chorded-delays.md)).
- `RTP: Mouse Buttons` scroll repeat became a chord on right-pad touch.
- The four inactive stick-touch Double Press groups were pruned with the other
  dead groups ([plan](../plans/2026-09-30-banned-activators-and-dead-groups.md),
  [record](../findings/2026-09-30-dead-group-prune/README.md)).

#### Command Entry Budget

**Rule: R109** (Layer Definition of Done [§3](Layer%20Definition%20of%20Done.md#3-activators)). This section explains it; the rule text is there.

**Hard requirement for this repository: at most three GUI command entries per
input.** The layout author confirmed on 2026-09-27 that subcommands are allowed
inside those entries. This records the required design constraint, not a claim
about an independently measured limit in every Steam client version.

**Where the limit comes from (author, 2026-09-30):** it comes from applying a
layout to the **desktop** configuration in Steam Input. There, every command
entry after the third on an input disappears. The editor doesn't show it, and
it doesn't fire. The limit keeps the layouts working on desktop. This is a
Steam bug the author may report. Recheck it periodically, and relax the rule
if Valve fixes it (tracked in [todos](../todos.md)).

**One allowed exception: a delayed-apply reset as a last, 4th entry.** Because
desktop drops entries in order, a 4th entry is acceptable only when it is the
least important one and sits **last**. The only case is the
[interrupted-apply reset](#interrupted-delayed-layer-applies): a Regular Press
that removes the target of the same input's chorded delay, with Hold to Repeat
and `interruptable: "0"`. On desktop the reset is lost and everything else
keeps working. Since 90.6 this applies to the four second-press layers,
`Menu Left: Escape`, `Menu Right: Tab` and the two modifier Scroll layers. Each
one's Regular Press list goes last, so the reset is the 4th entry in VDF order;
see the [change record](../findings/2026-09-30-second-press-cover-reset/README.md).
`audit_command_budget.py` reports these as `allowed_fourth`. Any other shape,
including a reset that isn't last, is still a violation.

Count objects under `group[].inputs.<input>.activators`, across **all** activation
types. A singleton object counts as one; a list contributes its number of objects.
For example, one `Full_Press` plus six `chord` objects is **seven**, even though
there are only two activation-type keys. One `Full_Press` plus two chord objects
is **three**. Each of those objects can have a string or an array in
`bindings.binding`; the array's actions are subcommands sharing that one entry.
Do not count or truncate those actions as separate GUI command entries.

The budget applies separately to each input (button, edge, click, touch, trigger
pull, etc.) in each group; do not sum inherited/layered definitions or different
inputs together. Audit active groups, dormant groups, mode-shift targets, and
unreferenced groups. Check disabled activator banks separately before restoring
them; disabling overflow is not a repair.

Run `python3 -m tools.audit_command_budget path/to/layout.json` before finalizing.
It is read-only and supports numeric IDs and title tokens. Exit 0 is required;
exit 1 reports violations, exit 2 reports invalid input. `--json` emits every
input's counts and every violation's activators, bindings, settings, and path.

**Multi-button chord consolidation:** combine commands only when the output and
all non-selector settings match. A single modern chord can select several
buttons with `gyro_ratchet_button_mask`; use
`gyro_ratchet_button_requireany_or_all: "0"` for **Any**, or `"1"` for **All**.
The Any/All values are independently verified in the installed Steam chord UI
schema; see the [selector verification](../findings/2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md).
Confirm the imported selections in the target client's GUI. Preserve
delays, thresholds, repeat settings, and `interruptable`. Different activation
conditions cannot be represented by dumping all outputs into one unconditional
subcommand array.

Legacy `chord_button` values are selector IDs, **not bit positions or bitmasks**.
Do not OR those IDs together. Decode actual button masks first. Nor is the modern
selector exclusive to Triton: Valve's [March 9, 2026 client update](https://steamcommunity.com/games/593110/announcements/detail/524243918833846834)
introduced a multiple-button selector for chord activators; the [Deck release
notes](https://www.steamdeck.com/en/news/?p=26) also record that change (news page
pagination can move). This does not substitute for a fresh-load test of the exact
mask on the target controller.

See the [90.1 audit](../findings/2026-09-27-neptune-command-budget/AUDIT.md) and
[three-entry ramp-up plan](../plans/2026-09-27-neptune-command-budget.md) for the
specific masks, the alternative variant's swapped roles, and regression checks.

#### Binding Execution Order

**Rule: R110** (Layer Definition of Done [§3](Layer%20Definition%20of%20Done.md#3-activators)). This section explains it; the rule text is there.

**IMPORTANT:** When a binding contains an array of `controller_action` commands, they execute **from bottom to top** (reverse order).
The array below is subcommands within **one** GUI command entry; it does not
violate the three-entry budget. This execution-order rule does not specify
priority or timing between separate activator objects.

```json
"binding": [
    "controller_action add_layer {{Base::L2}} 0 0, , ",           // Executes LAST
    "controller_action remove_layer {{Base::Gyro Off}} 0 0, , ",  // Executes 4th
    "controller_action remove_layer {{Base::Turning Ramp Up 0}} 0 0, , ",  // Executes 3rd
    "controller_action remove_layer {{Base::Turning Ramp Up 1}} 0 0, , ",  // Executes 2nd
    "controller_action remove_layer {{Base::(Gyro) Turning Ramp Up 0}} 0 0, , ",  // Executes 1st
    "controller_action remove_layer {{Base::(Gyro) Turning Ramp Up 1}} 0 0, , "   // Executes FIRST
]
```

**Why this matters:**
- The **final state** is determined by the **top** binding executing last
- For the usual cleanup-then-apply transition, place `add_layer` commands at the
  **top** and `remove_layer` commands **below** them so cleanup executes first
- Some stick-touch releases intentionally **complete a delayed apply before
  removal can reset its timer**; preserve the opposite order on those paths
  ([documented exception](#complete-delayed-applies-on-stick-touch-release))
- Always On entry/exit ordering remains mandatory: add the timed layer last;
  remove it first before changing other layers

#### Interrupted Delayed Layer Applies

**Rules: R120, R121** (Layer Definition of Done [§6](Layer%20Definition%20of%20Done.md#6-hold-tap-and-double-tap)). This section explains them; the rule text is there.

The layout author observed a Steam Input bug where interrupting an `add_layer` command
before its Fire Start Delay completes can prevent the command from firing on the next
press. **Repeated `remove_layer` commands have restarted the delay and recovered the
apply in observed cases.** The author reports on 2026-10-09 that removal does not reliably
reset every timer, can accelerate held repeats, and that a following delay can appear
to fire immediately during rapid or simultaneous add/remove transitions, notably the
cursor-driver add. The exact triggers remain unresolved. See
[Delay Timers and Repeat Rates](Delay%20Timers%20and%20Repeat%20Rates.md): delays and
repeat intervals must not carry mission-critical behavior.

The July layout implements this with two separate activators on the same bumper input:
a **Button Chord** that applies `L1&R1: Tap Cover` after **200 ms**, and a **Regular Press**
that removes that cover with a **250 ms** repeat interval.

| Activator field | Value | Purpose |
|---|---|---|
| `chord.bindings.binding` | `controller_action add_layer {{Base::L1&R1: Tap Cover}} 0 0, , ` | Apply the cover |
| `chord.settings.delay_start` | `"200"` | Fire Start Delay in milliseconds |
| `Full_Press.bindings.binding` | `controller_action remove_layer {{Base::L1&R1: Tap Cover}} 0 0, , ` | Remove the cover to reset the delayed apply |
| `Full_Press.settings.hold_repeats` | `"1"` | Enable Hold to Repeat |
| `Full_Press.settings.repeat_rate` | `"250"` | Repeat interval in milliseconds |
| `Full_Press.settings.interruptable` | `"0"` | Keep the removal activator from being suppressed by the chord |

These paths are relative to an input's `activators` object. The removal has no chord
requirement or explicit start delay. This uses independently configured activators;
the bottom-to-top rule above applies to commands within a `binding` array, not the timing
of these two activators.

In the July snapshot, the pattern appears on **R1 in `*L1!R1: Modifier 2`** (chord
requires L1) and **L1 in `*R1!L1: Modifier 2`** (chord requires R1), but not the
unstarred variants. It was absent from the earlier Neptune export; the September
port added it to all four Neptune Mod 2 layers, regular and gyro. The single-modifier
cursor follow-up adds the same pattern to all four regular/Gyro parents per layout:
their primary input applies its own Temp Cursor Gyro after 300 ms and removes only
that cursor target every 350 ms (200 and 250 since 90.26). Both cursor and normal overlays replace the complete
primary input to retire the apply/reset pair. The reset must never remove the normal
cover and reopen cursor eligibility. See the [follow-up and inheritance checks](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#delayed-apply-reset-follow-up).
The 200/250 ms values describe the configured implementation, not a guaranteed
ordering of the delayed add and the next removal on the Deck.

**Since 90.26** (author, 2026-10-04) no hold delay is over 200 ms, and every reset still repeats
at its delay plus 50 ms (R121): 200/250 for the modifiers, the Fn layers, the stick guards, the
Steering modifiers and `Menu Keys`; 150/200 for the second-press covers and the Tap Covers of
the stick and pad Entry Points. The ramp-up layers keep 250/300. The 5 ms outer ring bind of
the two Click Entry Points has its reset on the pad's touch, every 55 ms. The audit of every
delayed add, and what a shorter or longer margin costs, are in
[the build record](../findings/2026-10-04-standard-delays/README.md).

**RTP trackpad exception, until 90.24:** the author deliberately left this workaround out
of the RTP trackpad layers because repeated layer removal interfered with **trackball
momentum** (A28). RTP's delayed touch binding applied `RTP: Tap Cover` after 150 ms without
a corresponding repeating removal on that input. **Since 90.25 it has the reset** (author,
2026-10-04), as have the two stick Entry Points: a Regular Press that removes only the Tap
Cover every 200 ms. On a normal touch it fires once, as the Entry Point lands on the thumb
(A6), and not again: the cover lands at 150 ms, before the first repeat (A48). The author
felt that one fire on the Deck as a pulse at every touch, kept the reset, and since 90.29
all three state `haptic_intensity` 0
([record](../findings/2026-10-04-quiet-resets-and-beeps/README.md)). **Since 90.30 the reset
is off all three again, for now** (author, 2026-10-04): the author thinks the repeated
removal stopped the menu buttons while a thumb was on a stick
([record](../findings/2026-10-04-window-releases-and-tap-cover-resets/README.md)).
Other repeated cleanup bindings in RTP-related layers serve separate purposes.

See the [R1 and L1&R1 tap-cover findings](../findings/2026-09-27-r1-tap-cover/FINDINGS.md)
for exact groups, source locations, the Neptune comparison, and supporting research.

The original [delayed-apply reset audit](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md)
recorded seven of nineteen delayed-add paths per layout with the reset. The cursor
follow-up raises current coverage to **eleven of nineteen**. The original audit
distinguishes the confirmed RTP exception from undocumented omissions and
proposed extensions; a missing reset is not by itself a reproduced failure.
Don't couple a reset to wheel or key output timing to extend coverage. Keep the
reset on the parent that owns the pending apply, not inside the overlay or an
Always On window.

**90.6 adds the four second-press layers** (`Menu Left: Escape`,
`Menu Right: Tab`, `L1/R1: Scroll Down/Up`), which bring coverage to fifteen
of nineteen (these counts are from 90.6 and haven't been recounted; 90.10
added delayed adds with their resets, for the stick guards and Steering's
modifiers). After an accepted double tap, these layers add their Double Tap
Cover after 150 ms. The author chose a 200 ms reset as a **4th entry, placed
last**; this is the only allowed exception to the
[command entry budget](#command-entry-budget). See the
[change record](../findings/2026-09-30-second-press-cover-reset/README.md).

#### Complete Delayed Applies on Stick-Touch Release

**90.38 RTP extension (author, 2026-10-08):** Steering permits RTP entry
outside windows. Its six pending Steering/Stateful applies and their
existing stick-touch completion entries add the target before cleaning
non-window RTP helpers. The binding order and affected owners are in the
[release record](../findings/2026-10-08-steering-rtp-and-menu-chords/README.md#rtp-access-and-timed-completion).
This does not remove an Always On RTP window after another layer change;
window isolation and self-first exits still apply.


**Rules: R116, R117, R123, R125** (Layer Definition of Done [§5](Layer%20Definition%20of%20Done.md#5-stick-touch-release) and [§6](Layer%20Definition%20of%20Done.md#6-hold-tap-and-double-tap)). This section explains them; the rule text is there.

**Author-confirmed cleanup rule, 2026-09-30:** every layer must **explicitly**
bind the appropriate stick-touch **release** cleanup. Only cover-type layers,
which are only ever added on top of another layer (the Tap Covers, the Double
Tap Covers, Temp Cursor Gyro and `Gyro Off Ramp Up`), may
inherit it. A trace
showing that inheritance would work is not enough for any other layer. The
accepted exceptions (`Gyro Off Ramp Up` as cover-type, `Gyro` as the base
stateful layer, and the LST/RST helpers on the opposite stick) are listed in
the [Layer Definition of Done](Layer%20Definition%20of%20Done.md#5-stick-touch-release).
LS thumb release removes `LST: Entry Point`, `LST: Tap Cover` and
`LST: Temporary Gyro`; RS thumb release removes the corresponding `RST` trio.
This is capacitive touch release, not stick click or cardinal-direction release.
Keep the scope side-local; do not remove persistent `Gyro`, the other stick's
helpers, or a valid driving owner as part of this ordinary release cleanup.

For a pending **layer transition**, complete its matching delayed add first in
execution order, then remove the stick helper trio. Stored arrays execute
bottom-to-top, so the add is last in storage. Completed covers override this
with cleanup-only release to avoid reopening the parent transition. Audit the
entire touch input when overriding it: release-only overrides also hide lower
Regular/chord stale-state recovery. Preserve the applicable recovery guards and
the three-entry budget.

This does not mean firing delayed wheel/key output, haptic warning, exit timers,
or both possible direction selectors on thumb release. Direction-dependent
routing must keep its direction condition; it has no unconditional target to
complete. Always On Double Tap windows also bind the release, but they remove
themselves **first** and then the side's trio; they never complete an early
apply. The LST/RST windows' own stick has no release, because touching it again
is the self-first second-touch transition. See the
[16-layer steering cleanup audit](../findings/2026-09-30-steering-lean/CLEANUP-AUDIT.md)
for the per-layer application of this rule.

**Author-confirmed intent, 2026-09-29:** certain layers deliberately apply the
target of a pending delayed transition when a thumb leaves either stick, before
removing that stick's helper layers. The removals can reset start-delay timers.
Completing the apply first avoids postponing it while still clearing LST/RST
state. This is an early-completion path, not an input intended to cancel the
delayed transition. It does not wait for the rest of the hold delay.

For example, in default `L1: Modifier 0`, the primary hold currently applies
`L1: Temp Cursor Gyro` after 200 ms. Its RS touch release contains this stored array:

```json
"binding": [
    "controller_action remove_layer {{Base::RST: Temporary Gyro}} 0 0, , ",
    "controller_action remove_layer {{Base::RST: Tap Cover}} 0 0, , ",
    "controller_action remove_layer {{Base::RST: Entry Point}} 0 0, , ",
    "controller_action add_layer {{Base::L1: Temp Cursor Gyro}} 0 0, , "
]
```

Execution is **apply L1 cursor overlay → remove RST Entry → remove RST cover → remove RST
Temporary Gyro**. The LS release uses the corresponding LST family. The
alternative layout uses its L2/R2 modifier owners. The add is last in storage
because it must run first; do not sort these into the usual remove-before-add
order. All four subcommands share one Release Press entry.

The [cleanup audit's F6 inventory](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md#f6-thirty-mixed-bindings-execute-their-add-before-their-removals)
records thirty active non-Always-On touch-release arrays per layout with this
ordering, including modifiers and Menu Entry → Fn transitions. Preserve their
individual targets and guards; the shared ordering does not make their cleanup
scopes interchangeable.

When changing one of these delayed transitions:

- Update its touch-release completion target alongside the primary delayed
  target. Limit the release removals to the corresponding stick's helper family;
  keep held-owner protection and stale-state recovery as separate activators.
  A sibling owner chord guarding Regular Press does not establish that Release
  Press is guarded; trace missed-owner and already-touched input transitions.
- Trace the input inherited by the target overlay and any overriding cover.
  Once the transition is completed or intentionally superseded, give those
  inputs cleanup-only release behavior where needed so a thumb lift cannot
  re-add the old target or defeat the override. Preserve the appropriate
  owner-guarded, repeating recovery and the three-entry command budget.
- Keep unnecessary removals out of a valid pending hold. This pattern completes
  an apply before necessary cleanup; the [periodic reset workaround](#interrupted-delayed-layer-applies)
  deliberately restarts an interrupted apply. They solve different problems.
- Preserve Always On isolation. This exception does **not** permit another
  layer change while a timed Always On layer remains active. Its self-first
  exit/add-last entry rules take precedence.

The [Temp Cursor Gyro implementation](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md) uses this
pattern explicitly: the primary delay and both touch releases apply the
cursor overlay; normal Tap Covers replace touch inputs with guarded
recovery and LST/RST removal only. Start/Select, the opposite modifier, and the
other normal-cover inputs remain overrides, even before 200 ms. Cursor overlays
omit both stick-touch inputs, deliberately inheriting the parent's completion
and helper cleanup; adding the already-active cursor does not establish a new
hold. Normal covers keep their cleanup-only replacements so a thumb lift cannot
reactivate cursor after cancellation. The saved bindings implement this lifecycle,
and the scenario tests replay it ([test_scenarios_cursor.py](../tests/scenarios/neptune/test_scenarios_cursor.py)).
What Steam does when two of these fall in the same moment is not verified
(A13 and A32 in [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md)).

#### Blocking to Protect Layer Timers

**Rule: R126** (Layer Definition of Done [§6](Layer%20Definition%20of%20Done.md#6-hold-tap-and-double-tap)). This section explains it; the rule text is there.

Blocking is part of the layout's state management. The author reports that layer
removals can reset Fire Start Delay timers, but not consistently, and can make held
repeats faster. Repeating removal has recovered interrupted applies in observed
cases; it does not guarantee a restart or a full new wait. Rapid or simultaneous
add/remove transitions can also make a following delay appear to fire immediately
([timing observations](Delay%20Timers%20and%20Repeat%20Rates.md)). Unrelated additions can change
which layer owns the input. Do not add broad cleanup or repeated layer commands
to an apparently unused input without checking the timing state it protects.

The layouts use several distinct forms of blocking:

- **Explicit empty binding:** suppress the lower action for the configured
  input/event. An empty chord can block only while its selector is held.
- **Chord protection:** the valid held-button action, either a real output or
  an empty binding, interrupts the Regular Press cleanup on that input.
- **Disabled source mode:** an active group with `mode: "disabled"` disables
  that source, such as a trackpad or gyro. This is different from an `inactive`
  alternate group, which is not currently applied.
- **Replacement output or release:** a scroll/key/mouse action replaces a
  lower layer-changing action; a cover's release replaces a tap-producing exit.
- **Ordered exit:** remove a protected timed layer before executing any other
  layer changes. This permits a controlled transition rather than an unrelated
  mutation while that timed layer remains active.

An `empty_binding` subcommand inside an array containing real actions does not
cancel the rest of the array. Likewise, an empty `inputs` object, an omitted
binding, or an inactive group is not evidence of an explicit input block.
Layer/source inheritance and the currently exposed input must be considered.

#### Always-On Layer Isolation and the Historical Crash Workaround

**Rules: R140, R146 to R149** (Layer Definition of Done [§8](Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking) and [§9](Layer%20Definition%20of%20Done.md#9-always-on-layers)). This section explains them; the rule text is there.

**Author-reported historical bug, documented 2026-09-28:** adding or removing
other layers while a layer with an Always On binding remained active caused
severe crashes. The affected client build/date and exact internal cause are not
known. The bug may have been fixed; no matching Valve fix or current runtime
reproduction was confirmed in this audit. The isolation and ordering below
remain requirements of these layouts, not claims that every current Steam
client still crashes.

The workaround isolates the short-lived Double Tap layers:

1. **Before entry, finish other layer changes; add the Always On layer last.**
2. **While it is active, block unrelated layer additions/removals**, including
   inherited routes. Normal key/mouse/movement output need not be disabled.
3. **On timeout, remove only that timed layer.**
4. **For an early exit, remove the timed layer first**, then remove other
   layers or add the next layer. Self-removal is the permitted exception; it
   must execute before the other layer operations, not merely appear somewhere
   in the same array.

Arrays execute bottom to top. These are actual default-layout patterns, shown
with readable titles (alternative uses L2/R2 modifier names):

**Entry from L1 Modifier 0 release:**

```json
[
  "controller_action add_layer {{Base::L1: Double Tap}} 0 0, , ",
  "controller_action remove_layer {{Base::L1: Modifier 0}} 0 0, , ",
  "controller_action remove_layer {{Base::Gyro | L1: Modifier 0}} 0 0, , "
]
```

Execution: remove the Gyro modifier, remove the regular modifier, then add
Double Tap. Never move that timed-layer addition below the other operations.

**Second-press exit from L1 Double Tap:**

```json
[
  "controller_action add_layer {{Base::L1: Scroll Down}} 0 0, , ",
  "controller_action remove_layer {{Base::L1: Double Tap}} 0 0, , "
]
```

Execution: remove Double Tap first, then add Scroll Down. Cross-gesture exits
follow the same rule: their Double Tap self-removal is at the bottom, before
the stored RST/LST cleanup subcommands execute. Do not sort these lists by
layer ID, name, or a blanket self-last cleanup convention.

There are **seven Always On layers** in each 90.2 layout: the two modifier Double
Tap layers, LST/RST/RTP Double Tap, and Menu Left/Right Double Tap. LST/RST time
out after 200 ms; the other five after 150 ms. The two modifier and two menu
windows also send a scroll/key output after 50 ms. Those outputs are not layer
mutations. **Double Tap Covers are separate layers and have no Always On bind.** Since
90.10 there are nine: `Steering | LS Up: Double Tap` and `Steering | LS Down:
Double Tap` time out after 150 ms and send their single scroll in the same
entry as the self-removal, so a second push or the opposite direction can
drop it.

The [blocking audit](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md)
of 2026-09-28 checked every layer of the 90.2 layouts: all 13 entry bindings
added the timed layer last, and all 30 layer-changing bindings in a window
removed it first. Today `tests/contracts/neptune/test_neptune_recovery.py` checks the same for
every window on every run. Since 90.6 every window's left pad swipes straight to the Escape,
Enter, Tab and Backspace keys, with no layer command, and clears click and
touch. The right pad stays the mouse (Base's mode, settings inherited) with
click and touch cleared, except in RTP Double Tap. That window keeps its
dpad-mode pad for the intended selection, with self-removal before Circular
Scroll, and clears `click` ([change record](../findings/2026-09-30-double-tap-pad-blocks/README.md)). `audit_inheritance.py` derives every stack a
window can be applied on and blocks any remaining layer command underneath,
for example the default trigger edges under `Gyro Off Ramp Up` and RTP Double
Tap's back buttons ([derived blocks](../findings/2026-09-30-derived-window-blocks/README.md)).
RTP Double Tap's right-pad touch needs no block: the window's pad is in
`dpad` mode, and a different source mode stops Base's mouse-mode touch from
being inherited (the earlier `allow` decision was retired on 2026-10-01).
Menu inputs, RS edge, and modifier routes are explicitly blocked or replaced.
This validates configured ordering, not arbitrary stale-stack inheritance or
the absence of a crash on a current client.

**Cleanup audits must preserve these protections.** An empty binding is not
automatically a missing cleanup. Classify the reason for the block first. If a
new recovery exit is needed inside an Always On layer, remove that layer first
in the same entry, then perform the recovery. The RTP trackball-momentum
exception to repeating delayed-apply resets ended with 90.25.

**Common Group Modes:**

| Mode | Description |
|------|-------------|
| `four_buttons` | Face buttons (A, B, X, Y) |
| `dpad` | Directional pad |
| `joystick` | Analog stick |
| `absolute_mouse` | Mouse movement |
| `gyro` | Gyroscope/motion controls |
| `trigger` | Analog triggers (L2/R2) |
| `switch` | Digital buttons (bumpers, menu, etc.) |

---

## Relationship Summary

### Action Sets → Presets
```
actions["Preset_1000001"]  ←→  preset[].name == "Preset_1000001"
       (Action Set)                    (Preset Entry)
```

### Action Layers → Action Sets
```
action_layers["Preset_1000006"].parent_set_name == "Preset_1000001"
              (Layer)                                (Parent Set)
```

### Action Layers → Presets
```
action_layers["Preset_1000006"]  ←→  preset[].name == "Preset_1000006"
              (Layer)                        (Preset Entry)
```

### Presets → Groups
```
preset[].group_source_bindings = {
  "10": "switch active",    // → group[] where id == "10"
  "11": "button_diamond active"  // → group[] where id == "11"
}
```

---

## How Binding Overlay Works

1. **Action Set Activated**: When entering an Action Set (e.g., "Base"), the controller loads all bindings from its corresponding preset entry.

2. **Layer Applied**: When a layer is activated:
   - The layer's preset entry is loaded
   - Bindings from the layer **overlay** (replace) the exposed lower bindings
   - Unchanged inputs can inherit from the remaining layer stack, not just the Base set
   - Source settings and mode replacements also matter: an active `disabled` gyro
     group overrides gyro even when it has no explicit input activators
   - **A different source mode blocks inheritance** (author rule, 2026-10-01).
     When a layer binds a source in a different mode from the layers below, none
     of that source's lower inputs carry over, even ones the upper group leaves
     unbound. Example: the RTP Double Tap window's `dpad` pad doesn't inherit
     Base's mouse-mode `touch`. See
     [Layer Definition of Done §8](Layer%20Definition%20of%20Done.md#a-source-mode-change-blocks-inheritance).
   - **Re-adding a layer that's already active does nothing.** It isn't
     promoted: a stack A B C (bottom to top) stays A B C when A is added again.
     The only way to move a layer to the top is to remove it and then add it.
     This is Valve's documented behavior
     ([Action Set Layers](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers))
     and was confirmed by the author on the Deck on 2026-09-30.
     `steam_layout.stacks` models it this way, and Mod 2 rocking depends on it
     ([Rocking Between Modifiers](#rocking-between-modifiers-0-1-and-2)).
   - **Unverified:** a 2022 community report says analog sticks inherit only
     from the top layer and the base action set, skipping the middle of the
     stack ([source](https://steamcommunity.com/app/353370/discussions/0/3468361193665969286/),
     on 360 controllers). The tools assume normal inheritance for sticks. The
     check is tracked in [todos](../todos.md).

3. **Layer Deactivated**: Removing the layer exposes the remaining stack's bindings,
   or the parent Action Set when no lower layer overrides that input. Adding a
   layer over a held input does not fire its immediate layer commands. Whether
   removing one fires the exposed binding on a held input is unverified, so
   these layouts back it with Hold to Repeat; see [Held Inputs Across Layer Changes](#held-inputs-across-layer-changes).

**Example Flow:**
```
Base Set (Preset_1000001) active:
  - A button = Space (Jump)

L2 Layer (Preset_1000006) activated:
  - L2 layer groups overlay onto Base
  - Modified inputs take effect

L2 released:
  - Reverts to Base Set bindings
```

### Held Inputs Across Layer Changes

**Rules: R113 to R115** (Layer Definition of Done [§4](Layer%20Definition%20of%20Done.md#4-entry)). This section explains them; the rule text is there.
What Steam is assumed to do here is A5 to A11 and A15 in
[Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md), each with its status.

**Documented 2026-09-29 from the author's runtime experience.** A layer added
over an input that is already held treats that input as already pressed:

| Layer **added** while the input is held | Fires on that held input? |
|---|---|
| Immediate layer command: Regular Press, chord, or Soft Press with no Fire Start Delay and no Hold to Repeat | **No.** The press happened before the layer existed |
| Activator with a Fire Start Delay | Yes, once the delay elapses |
| Activator with Hold to Repeat | Yes, at once: a repeating action always triggers (author, 2026-10-04). Until then this said "on its next repeat interval" |
| Release activator | Yes, on release |

A layer command is `add_layer`, `remove_layer`, or `hold_layer`.

These observations describe activation on a held input, not stable scheduling
through later layer changes. The author reports disrupted repeat intervals and
premature delays during some transitions; see
[Delay Timers and Repeat Rates](Delay%20Timers%20and%20Repeat%20Rates.md).

**Unverified: a layer removed while the input is held.** The author expects the
newly exposed lower binding to fire as if the input had just been pressed, but
this hasn't been isolated. In these layouts, every layer command that a removal
is expected to expose on a held input also has Hold to Repeat. That includes
Base's entries, Gyro's modifier entry, and the cursor parents' cover and Mod 2
chords. Repetition is the existing retry mechanism for the unverified exposure
case; it does not guarantee an exact firing time or an unaffected held-repeat
interaction. Until this is confirmed:

- Keep those repeats.
- Give any new layer command that must fire after a removal Hold to Repeat.
- Still trace what each new removal exposes on held inputs, since it may fire
  immediately.

[`rule-test.vdf`](../findings/2026-09-29-held-input-layer-transitions/rule-test.vdf)'s
T4 can settle it later.

**Scope (author, 2026-10-01): the rule covers the Steam layer API only.** It
was reported for layer commands. It says nothing about key and mouse outputs,
so don't use it to argue that an output can't fire on an input that is already
held.

- **Outputs when a layer is added:** the author's experience is that they do
  fire. Before the menu split, the Entry Point's opposite-button chord only
  added Fn, and Fn's own chord typed Backspace / Enter for the button that was
  already down. **Reported, never verified in isolation (A10).** The Escape / Tab
  second-press layers and Steering's W / S layers rely on the same thing.
- **Outputs when a removal exposes them:** unverified (A11). The first click after a
  trigger removes `Gyro Off Ramp Up`, and keys exposed by cursor self-removal,
  rely on it.

Each has one procedure in [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md).

How these layouts use it:

- **A delayed apply needs no repeat to fire on the held input that just added
  its parent.** All 19 delayed applies per layout have this shape. The 5 ms delay
  in `Gyro Off Ramp Up` exists only for this: the stick is already past its
  threshold when the layer appears, so a zero-delay Soft Press would never fire.
  Don't remove "too short to matter" delays or add repeats to delayed applies
  without checking this.
- **When a new layer must act immediately on a held input**, either add the next
  layer in the same binding array, or give the new layer's activator Hold to Repeat:
  - Array: Mod 0/1 → Mod 2 entry adds the covers and Mod 2 in one array.
    In 90.9 the Menu Entry's opposite-button chord also added Fn and then
    typed Enter / Backspace itself (until 90.8 it added an overlay layer
    instead of the key). The reason given at the time, that Fn's own chord
    can't fire for a button that is already down, stretched this rule to an
    output; see the scope note above. **Reverted in 90.10** (author,
    2026-10-01): the Entry Point's chord only adds Fn, and Fn's chord types
    the key, as it did before the split.
  - Repeat: Gyro's 50 ms modifier entry after a Mod 2 release, Mod 0/1 → Mod 2
    entry, the Menu Entry Points' stick-edge chord that adds a stick guard
    (50 ms, so the guard lands inside the 200 ms Fn delay when a stick is
    already out), and the Steering W and S layers' modifier add.
- **A layer that binds a button while a delay is running on that button eats
  the delayed action** (author, 2026-10-01). The stick guards rely on it: a
  guard that lands inside the Entry Point's Fn delay cancels it. Whether the
  delay comes back when the covering layer is removed rests on the repeating
  reset and is unverified.
- **An exit whose condition can already be true when its layer is added needs
  Hold to Repeat.** Examples: the ramp layers' inverted thresholds, the trackpad-
  click hold exits, and `Gyro Off Ramp Up`'s firing-control removal.
- **Re-entry after a removal is carried by repeats.** These all re-enter through
  a repeating entry on the input that is still held:
  - Ramp modifier exits clear ramp-up, then the Base/Gyro modifier entry
    re-enters on its repeat (how soon after a removal exposes it is A9).
  - Guarded recovery clears the stale layer, then the input's normal action follows.
  - A Double Tap expiry exposes the Base action under a held input.

  Removal pass-through may fire them sooner (see above).
- **Base is never added.** Its bindings return only through removals, so its
  repeating entries (menu, modifier, stick/trackpad touch, RS edge) are the
  retry mechanism for the unverified removal case. The regression tests protect
  their presence, not Steam's actual repeat schedule.

The earlier timer observations suggested that removals restart Fire Start Delay
timers. Later observations do not support a dependable restart rule: some delays
reset, held repeats can accelerate, and a following delay can appear immediate
after a rapid add/remove transition. Re-evaluation of held inputs after a removal
remains a hypothesis (A18); it does not explain all these timing effects. See
[Delay Timers and Repeat Rates](Delay%20Timers%20and%20Repeat%20Rates.md).

See the [held-input audit](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md)
for the ramp-up walkthrough, per-layout inventory, the alternative layout's
former missing R2 → Mod 2 repeat, and the open questions. The
[regression tests](../tests/contracts/neptune/test_neptune_held_inputs.py) protect the delays and
repeats listed here. The staggered Gyro toggle is a scenario test (HI2 in
[test_scenarios_triggers_and_recovery.py](../tests/scenarios/neptune/test_scenarios_triggers_and_recovery.py)),
and what Steam does with a held input is A5 to A11 in
[Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md).

### Gyro Settings Inheritance

**Rule: R143** (Layer Definition of Done [§8](Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)). This section explains it; the rule text is there.

Keep the normal gyro response in Base. Ordinary layers inherit the exposed lower
stack's settings; do not copy a complete Base gyro group into every layer. Follow
the [July reference](../findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json)
and distinguish these intentional exceptions:

- **Activation layers:** persistent Gyro, the Gyro modifier variants, and LST/RST
  Temporary Gyro specify only `layer: "1"` and the activation selector/Any-All
  fields they change. They inherit sensitivity, calibration, and response.
- **Response overlays:** Temp Cursor Gyro specifies only its four response/haptic
  overrides. Cancellation removes that cursor layer, exposing the response below.
  Normal modifier Tap Covers and regular Mod 0/1 parents have no active gyro
  source; neither duplicates response settings. The cover prevents cursor re-entry
  for the rest of the hold by replacing the primary and stick-touch lifecycles.
- **Disabled contexts:** preserve active `disabled` gyro sources in menu,
  transition, and Gyro Off layers. These are deliberate source replacements,
  not missing inheritance. Dormant `inactive` groups are a separate category.

In the current Neptune layouts, normal precision/haptic/bump/threshold is
300/0/5/0; cursor is 750/0/1/5. Both inherit Base natural sensitivity 300,
rotation calibration 3853, vertical ratio 200, conversion style 4, and speed
deadzone 0. When tuning Base, trace overlapping activation/profile layers and
preserve cursor's deliberate response overrides. There is no normal-cover copy
to synchronize. Do not overwrite activation gates while importing response values. The [reference-tuning record](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#reference-tuning-and-gyro-inheritance-follow-up)
lists exact settings and pending runtime checks.

### Cursor Cancellation and Repeating Cover Chords

**Rule: R135** (Layer Definition of Done [§7](Layer%20Definition%20of%20Done.md#7-cleanup)). This section explains it; the rule text is there.

Each regular/Gyro Mod 0/1 parent splits its twelve ordinary cancellation inputs
(face buttons, D-pad directions, stick clicks, and Start/Select) into exactly
three GUI command entries:

| Entry | Action | Interruption and repeat |
|---|---|---|
| Owner-held output chord | Original key/mouse output only | Uninterruptible (`interruptable: "0"`); retain the output's existing repeat behavior |
| Same-owner cover chord | Add only the owner's normal Tap Cover | Uninterruptible; Hold to Repeat; no start delay or haptic feedback |
| Regular Press recovery | Existing modifier-family removal | Interruptible; Hold to Repeat; suppressed by the valid owner chords |

Both chords use the same owner selector. The separate repeat retries a layer
addition without repeating a key or mouse action that was not previously
repeating. This is 48 split inputs per layout. The opposite-modifier transition
keeps its own repeating Mod 2 path; the owner primary still uses its three
entries for release, 200 ms cursor apply, and the independent 250 ms reset.

Temp Cursor Gyro replaces those twelve inputs and the opposite modifier with
uninterruptible, repeating Regular Press removals of **only itself**. These
local cancellation entries contain no key output, cover addition, or Mod 2
selection. Removing cursor exposes the actual regular/Gyro parent, which
provides the original output and repeating cover/transition. This follows the
author's [held-input rule](#held-inputs-across-layer-changes); output delivery,
release, and same-selector chord arbitration are not verified (A10, A11 and
A27 in [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md)).
Do not claim chord-list order preserves the old combined array's add-before-key
execution order.

Both stick edges retain a different three-entry shape: an interruptible empty
owner guard, an uninterruptible repeating All chord requiring owner plus the
opposing stick's deflection, and interruptible repeating recovery. The parent
All chord adds the normal cover; the cursor All chord removes only cursor.
Cursor's lost-owner edge recovery also removes only itself and exposes the
parent's family recovery. One stick alone while its owner is held does not
cancel cursor. Keep the empty edge guard interruptible; the requirement that
both output/cover chords are uninterruptible does not change that guard.

Cursor inherits the parent's LS/RS touch inputs and geometry. Normal Tap Covers
keep cleanup-only touch replacements and inherit gyro response. Both overlays
retain their primary release exit, whose family cleanup is intentionally broader
than a cursor cancellation's self-only removal. See the
[implementation record](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md)
for affected stacks and validation.

### Inheritance Review for Binding Changes

**Rules: R139, R140** (Layer Definition of Done [§8](Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)). This section explains them; the rule text is there.

**Review a binding change in the stacks that can expose it, not only in the
layer that defines it.** Adding or changing a lower binding can change upper
layers whose JSON is untouched. Deleting an override can expose a lower action
that was previously blocked. Source modes, mode shifts, and settings such as
edge geometry can change that exposure too.

For each changed input or source:

1. **Trace the lower behavior and the upper layers that can inherit it.** Follow
   actual layer entry/exit paths and application order, including button
   overlays, timed windows, and plausible stale or overlapping stacks after a
   missed release. GUI/preset list order is not proof of the runtime stack.
   Include any mode-shift path that can expose the changed input. Do not assume
   an upper layer can inherit only from Base or from its usual entry layer.
2. **Resolve the effective input at each relevant boundary.** Check active
   source groups, mode replacements, settings, and explicit input bindings.
   Distinguish intentional inheritance, unconditional blocks, conditional
   chords, and replacement actions. An omitted input, empty `inputs` object,
   or inactive alternate group does not establish a block. A chord guard only
   protects its held condition; it cannot guarantee isolation once that owner
   is released or the stack is stale.
3. **Check entry, active time, and exit.** Ask what happens if the input starts
   during the upper layer and if it is already held, repeating, or waiting on
   Fire Start Delay when that layer is added or removed. Look for inherited
   additions/removals that could disturb a timer, hidden recovery, lost movement
   modifiers, or a newly exposed action after exit. Static inspection does not
   prove that installing a block cancels an already pending activator. Per the
   [held-input rule](#held-inputs-across-layer-changes), a newly added layer's
   immediate layer command doesn't fire on a held input. A newly exposed binding
   may fire after a removal, but that's unverified; rely on Hold to Repeat
   where it must fire.
4. **Choose the behavior deliberately.** Keep inheritance where the upper
   layer should share the lower action. Add a narrowly scoped explicit block
   where that action must be unavailable. If an Always On window needs an
   early recovery exit, remove that timed layer first in the same command entry
   before any other layer changes; otherwise keep those changes blocked.
   Preserve add-last entry and self-first exit ordering. Ordinary button
   overlays should continue inheriting useful owner recovery where intended;
   this review does not require blocking every overlay or disabling a whole
   source to protect one input.
5. **Record and verify the affected stacks.** Run `audit_inheritance.py`,
   which derives every stack from the layout's own transitions; see the
   [Layer Definition of Done §8](Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking).
   State the changed lower action,
   upper layer(s), intended inheritance/block/exit, and displaced behavior.
   Check both layout variants, the three-command limit, and relevant ordering
   and timer invariants. Record unresolved runtime questions and test the input
   both already held across a transition and first activated inside it on a
   fresh Deck load.

**Concrete example — LS-edge recovery and Double Tap windows:** the
[LS-edge change](../findings/2026-09-28-left-stick-recovery/CHANGES.md#always-on-isolation)
added guarded removals to fourteen lower layers. All seven Always On Double
Tap windows omitted LS edge, leaving a route for lower recovery to be inherited
in an overlapping or stale stack. The lower held-owner guards were insufficient
as a general isolation guarantee: recovery becomes eligible when those owners
are no longer held, while the timed window may still be active.

Each window therefore received an explicit empty LS-edge Regular Press:
left/right modifier, LST/RST/RTP, and Menu Left/Right Double Tap. These blocks
preserve the timed layer's isolation without issuing another removal. They
temporarily displace the inherited edge modifier and leave directional movement
unchanged. Double Tap Covers are separate overlays without Always On bindings;
they do not automatically need the same block. The
[regression checks](../tests/contracts/neptune/test_neptune_recovery.py) verify these seven
configured blocks and entry/exit ordering. Pending-activator behavior and
current-client crash behavior still require runtime evidence.

**Concrete example — cursor cancellation beneath RTP Double Tap:** Base's RTP
touch can be inherited through a single modifier and its cursor overlay. A quick
RTP release removes RTP Entry and adds RTP Double Tap, leaving the modifier/cursor
below the Always On window. The new repeating face, D-pad, and stick-click
mutations therefore require explicit empty replacements in RTP Double Tap:
four face inputs, four physical D-pad directions, and both stick clicks. These
ten blocks temporarily suppress the corresponding inherited outputs. Existing
menu/owner replacements, stick-edge blocks, and self-first touch/pad exits remain.

The other six windows were traced separately. Modifier releases clear their
regular/Gyro owner and cursor before adding their Double Tap window; scroll
entry goes through that cleared window. Single modifiers and their overlays
replace the Base LST/RST and menu entry inputs, while menu/scroll contexts
replace modifier entry with ordinary outputs. No additional coexistence path
for the new single-modifier repeats was found in those normal transitions, so
this change does not add ten blanket blocks to every window. This is a traced
configuration result, not proof about arbitrary stale stacks.

RTP Double Tap still relies on its `absolute_mouse` → `dpad` source replacement
to suppress Base's RTP click/touch layer actions, as recorded in the
[blocking audit](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md#inherited-route-review-and-remaining-uncertainty).
The inactive-marked trackpad mode-shift targets contain only key outputs;
whether they become effective in these stacks is assumption A34.
RTP Entry and Circular Scroll have no Always On action and keep useful modifier
inheritance. What a cursor cancellation does to RTP Entry's pending delay is
assumption A13 (both in [Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md));
this change does not add a repeating reset to the author's RTP touch exception.

### Stuck Layers and Why There Is So Much Cleanup

**How a layer gets stuck.** Most layers are removed when the button that opened them is
released. The layout author has observed that this release can be missed:

1. A layer stack is active.
2. You press the **Steam button**.
3. You let go of the buttons while the Steam menu is open.
4. You close the Steam menu.

The layout never saw the releases, so the layers are still active even though no button
is held.

For example:

1. Hold Start until `Menu Right: Fn Layer` is up.
2. Press the Steam button, let go of everything, and close the Steam menu.

The whole stack is still active: `Menu Right: Entry Point` and `Menu Right: Fn Layer`,
although Start is no longer held. The next face-button or stick press runs the Fn
layer's guarded recovery instead of its normal action.

**Recovery belongs to the interaction that owns the stack.** Modifier, Fn, and
entry layers provide backup exits on likely next inputs: sticks, face buttons,
or the other menu button. Overlays can keep a narrow release exit and
inherit the underlying recovery instead of duplicating it. A residual cover
requiring another related-button press was previously accepted; review invalid
residual covers under the [owning-layer responsibility](#cover-cleanup-ownership).
Menu layers deliberately restrict gameplay controls. See
[cleanup scopes and examples](#cleanup-scopes-and-concrete-examples).
After the [cursor-overlay additions](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md)
of 2026-09-29, each layout had 390 activators in active groups that explicitly
removed layers. That count is from then; 90.12 shortened the lists (R132).

#### Guarded Recovery Binding Shape

**Rule: R133** (Layer Definition of Done [§7](Layer%20Definition%20of%20Done.md#7-cleanup)). This section explains it; the rule text is there.

**Stored order (R133, since 90.36):** on an input with a cleanup function the
activator types are stored as `Full_Press`, then `chord`, then `release`. It
is the order the editor lists them in. Whether Steam's behaviour depends on it
is not known (A52); the author asked for one order everywhere on 2026-10-06.

Use **guarded recovery binding** for the fallback that clears stale state when
the button/touch owning an interaction is no longer held. This is the cleanup
shape to preserve when adding LS-edge recovery. Not every `remove_layer` in the
layout is this type of cleanup.

Most of these backup exits follow one pattern, on one input:

- **A chord with the button (or stick touch) that normally holds the layer open.** In
  normal use that button is held, so the chord fires. It sends the layer's real output,
  or an empty binding.
- **A Regular Press that removes the layer and its related layers,** with Hold to
  Repeat on every guarded recovery input. It keeps the default Interruptable setting, so the chord suppresses it during
  normal use. It only fires when the button isn't held, which is exactly the stuck case.

`L1: Modifier 0`'s right stick shows the pattern on three inputs:

| Input | Chord with LB (normal use) | Regular Press (LB not held, so stuck) |
|---|---|---|
| RS edge | empty binding; stronger LB + LS-deflected chord repeatedly adds normal cover | remove `L1: Modifier 0`, `L1: Tap Cover` and `L1: Temp Cursor Gyro` (Hold to Repeat) |
| RS touch | empty binding | the same removal (Hold to Repeat) |
| RS click | separate uninterruptible chords for middle mouse and repeating `L1: Tap Cover` addition | the same removal (Hold to Repeat) |

The Fn layers do the same on almost every input. For example, in `Menu Left: Fn Layer`:

- A chorded with a menu button sends F3.
- A pressed with no menu button held removes `Menu Left: Fn Layer` and `Menu Left: Entry Point`.

**Required structure for guarded recovery:**

1. Put the owner-held **Button Chord** and the cleanup **Regular Press** on the
   same recovery input. The chord sends the intended held action or an explicit
   empty binding. Holding its selector alone does not activate the recovery
   input; both input eligibility and the selector condition matter.
2. Keep the cleanup Regular Press **interruptible**, so the active chord
   suppresses it. Current guarded fallbacks omit `interruptable`, retaining
   the default; do not set `interruptable: "0"` on their removal entry.
   An empty chord is still a guard, not an invitation to delete it.
3. On **every guarded recovery input**, use **Hold to Repeat** on the removal
   (`hold_repeats: "1"`), including buttons, clicks, touches, and edges. This retries while
   the recovery input remains eligible and no protecting chord is active; it
   is not a background timer running just because the layer exists. Preserve
   the existing repeat-rate settings; do not infer a client-default interval.
4. Protect every valid held owner. Mod 2 uses two chord guards, so **either**
   held modifier suppresses recovery. Preserve those guards, or use an
   equivalent Any selector only when their outputs/settings match; All would
   change the condition. Count the guards and fallback toward the three-entry
   limit. Keep the related removal targets as subcommands in one entry.
5. Remove the state owned by that recovery, including invalid dependent covers,
   while preserving valid held interactions and persistent modes. Check that
   this lower-layer fallback cannot run through a protected Always On window.

With the recovery input active, the intended behavior is:

| Owner chord condition | Chord action | Regular Press cleanup |
|---|---|---|
| Any protecting owner is held | Held action or empty binding | Suppressed |
| No protecting owner is held | Inactive | Runs and repeats while the recovery input remains eligible |

This is **activator interruption**, not execution order based on which command
appears above another in the GUI/JSON. Bottom-to-top execution applies only to
subcommands inside one `binding` array; it does not sequence the chord and
Regular Press against each other.

For example, the existing default L1 modifier's RS-edge input has this shape
(readable title form):

```json
{
  "edge": {
    "activators": {
      "chord": [{
        "bindings": {
          "binding": "controller_action empty_binding, , "
        },
        "settings": {
          "chord_button": "1"
        }
      }, {
        "bindings": {
          "binding": "controller_action add_layer {{Base::L1: Tap Cover}} 0 0, , "
        },
        "settings": {
          "gyro_ratchet_button_mask": "1073741832",
          "gyro_ratchet_button_requireany_or_all": "1",
          "interruptable": "0",
          "hold_repeats": "1"
        }
      }],
      "Full_Press": {
        "bindings": {
          "binding": [
            "controller_action remove_layer {{Base::L1: Modifier 0}} 0 0, , ",
            "controller_action remove_layer {{Base::L1: Temp Cursor Gyro}} 0 0, , ",
            "controller_action remove_layer {{Base::L1: Tap Cover}} 0 0, , "
          ]
        },
        "settings": {
          "hold_repeats": "1"
        }
      }
    }
  }
}
```

This example has three GUI entries and three removal subcommands (four until
90.11, with the `Gyro |` twin, which R132 dropped). The empty
owner guard is interruptible; the stronger owner-plus-opposing-stick chord is
uninterruptible and repeating. Both require LB, so moving both sticks without LB cannot add
a cover or suppress recovery. The cleanup retains default Interruptable and
Hold to Repeat. The opposite chord uses All; its mask is LB bit 3 plus LS
deflection bit 30. Chord arbitration still needs a runtime check, not a claim
based on JSON list order. Other recovery inputs retain their existing guards.

**Convention standardized, 2026-09-28:** all 207 active guarded Regular Press
removals per layout at the time (265 cleanup functions in 90.13) enable Hold to Repeat, including stick clicks and
Scroll Down/Up stick-touch recovery. The six dormant guarded entries also
repeat. The [separate repeat change](../findings/2026-09-28-repeating-recovery/CHANGES.md)
enabled repeat on 104 of the original 185 active entries without changing their
guards or targets. The subsequent [LS-edge work](../findings/2026-09-28-left-stick-recovery/CHANGES.md)
added fourteen guarded recoveries and expanded Transition Set scope as approved.
The initial cursor implementation added eight touch recoveries. Its self-removal
follow-up retains the four normal-cover touch recoveries and replaces the four
cursor touch recoveries with four guarded cursor-edge recoveries. Cursor now
inherits the parent's touch input. These are saved-configuration checks, not a
new Steam runtime test.

**Other lifecycle removals have different shapes:**

- **Stick touch release:** many layers clear `RST` / `LST: Temporary Gyro`, `Tap Cover`
  and `Entry Point` when a thumb leaves a stick.
- **Cursor cancellation:** face/D-pad/menu/click/opposite-modifier inputs use an
  uninterruptible repeating removal of cursor alone. Their purpose is to expose
  the lower held action; they are not owner-guarded family recovery.
- **Timed self-removal:** the double-tap windows remove themselves from `always_on_action`
  after a start delay, for example 150 ms in `Menu Left: Double Tap`.
- **Delayed-apply resets:** repeating removals that restart an interrupted Fire Start Delay.
  Their Regular Press deliberately sets `interruptable: "0"` so a same-input
  chord does not suppress the reset. Do not apply the guarded-recovery setting
  to them. These solve a different problem; see
  [Interrupted Delayed Layer Applies](#interrupted-delayed-layer-applies).
- **Threshold exits and deliberate transitions:** ramp threshold/firing exits
  and Double Tap second-press transitions have their own activation conditions.
  An unguarded removal in one of these paths is not automatically a missing guard.

**When you add or change a layer:**

- **Review inherited effects in both directions.** Trace the lower bindings
  this layer exposes and the upper layers that can inherit its changes. Follow
  the [inheritance review](#inheritance-review-for-binding-changes), including
  timed windows and stale stacks, before treating the edit as local.
- **Identify who owns recovery.** For a stack-owning layer, trace an eligible fallback
  and the overlays that might hide it. For a button overlay, check its local exit
  and inherited behavior before adding independent cleanup inputs.
- **Choose the scope for that exit.** Remove only the state that exit owns. Review
  related cleanup lists against their promised scope; a new layer does not require
  adding its removal everywhere. Self-only, current-branch, released-side, and full
  family exits are all valid for different purposes.
- **Guard stale-state recovery during valid holds.** This rule does not forbid normal
  releases, deliberate transitions, timed expiry, or delayed-apply resets. For example,
  the combined Tap Cover's release removes only the released side, so the modifier
  that is still held stays valid.
- **Preserve protected timing states.** Empty bindings can hide lower cleanup, but
  some blocks deliberately protect timers or Always On layers. Trace their purpose
  before replacing them. Keep Always On entry add-last and exit remove-self-first.
- **Reserve stick-edge cleanup for layers that need it.** It replaces the inherited
  edge action: the LS WASD modifier or RS ramp-up. Weigh that loss against the
  recovery need before adding or mirroring an edge binding.

### Stick-Edge Cleanup and Inherited Actions

**Rules: R170, R142** (Layer Definition of Done [§7](Layer%20Definition%20of%20Done.md#7-cleanup) and [§8](Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)). This section explains them; the rule text is there.

**Which layers need one is R170 since 2026-10-04.** A layer that binds or
blocks a stick's edge has a cleanup function on that edge, and a layer that
binds or blocks a face button, a D-pad direction, Start, Select or a back
button has one on both. It replaces R134, "only where the layer needs one",
which left that to judgment. The cost below is why the rule stops there: the
layers that let ramp-up through (the stick-touch helpers, the pad layers,
`Gyro` and the single Tap Covers) bind none of those inputs and stay outside
it.

**Adding an edge fallback consumes an input that otherwise serves the
inherited layout.** It is not a free extra recovery path.

| Edge overridden by cleanup | Inherited behavior displaced while that override owns the input |
|---|---|
| Left stick | The user's WASD modifier, such as Walk, when configured in the Base edge slot; the default slot is empty. This concerns the modifier action, not all WASD movement. |
| Right stick | The lower ramp-up / gyro-off entry logic and its conditions. |

A held-owner chord protects the layer from premature cleanup, but its empty or
replacement binding still owns that edge; it does not restore the inherited
WASD modifier or ramp-up action. Removing the layer exposes lower behavior again.
If the RS edge is still held, ramp-up re-enters through Base's repeating entry.
The LS WASD modifier is a non-repeating output, with no such backup. Whether the
removal alone fires either one on the same gesture is unverified; see
[Held Inputs Across Layer Changes](#held-inputs-across-layer-changes).

The author intentionally accepts more restrictions on ramp-up: it uses layer
add/remove commands and delayed transitions, so it carries the timer-reset,
ordering, and protected-layer constraints documented above. RS ramp-up is thus
blocked or overridden by cleanup more often. This does not justify copying each
RS cleanup onto LS and losing the WASD modifier in all of those layers.

Menu layers are an intentional exception to preserving gameplay availability:
the author does not use Start/Select menu interactions while playing. WASD
modifiers and ramp-up need not remain available there, and gyro suppression is
intentional. Preserve those context-specific overrides; the selective-edge rule
still applies to gameplay layers where the inherited action is useful.

For each proposed edge cleanup, identify the stuck state it must recover, check
whether an existing inherited/touch/click/button exit is sufficient, and record
which inherited action will become unavailable. Add or mirror the edge only
where that tradeoff is needed. Keep overlays minimal and preserve
intentional timer blocks. Left/right consistency means matching recovery scope
and guards **where appropriate**, not equal edge-cleanup coverage everywhere.

The cleanup audit's fifteen RS-only non-ramp layers were a **review list**.
After review, the author selected fourteen for LS recovery: all eight modifier
variants, both menu entries, both scroll layers, and both Transition Sets.
RTP Entry Point remains outside this pass. The two Fn layers already implement
both edges; ramp-stage threshold exits remain specific to right-stick turning.
See the [implementation and tradeoffs](../findings/2026-09-28-left-stick-recovery/CHANGES.md).

The original fourteen LS additions used the Fn outer-edge region (`21000`,
inversion off). The cursor change moves the four single-modifier LS/RS pairs
to LS `4915` / RS `7209`, inversion off, accounting for the modes' different
hysteresis to target roughly 25% engagement; earlier recovery
when the owner is absent is accepted. The other ten LS groups retain `21000`.
Movement settings are preserved; physical thresholds and the opposing-stick
selector still need Deck verification. See the [threshold evidence](../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#edge-threshold-verification).
Every Always On Double
Tap window (seven then, nine since 90.10) explicitly blocks LS edge so it cannot inherit the new lower
recovery. The blocks contain no layer operations; timeout and ordered exits are
unchanged. These temporary blocks also displace the inherited edge modifier.

### User-Defined WASD Modifier Scaffold

Both Neptune layouts use the Base left-stick setup from
[the July reference](../findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json),
with its `KEYPAD_ASTERISK` action replaced by
`controller_action empty_binding, WASD Modifier, , `. The GUI label is
**WASD Modifier**. The user can assign a modifier such as
Walk to this slot in the GUI. The shipped scaffold sends no modifier key.

The edge has one `Soft_Press` entry with the reference's settings:
`soft_press_sytle: "2"`, `activation_threshold: "26610"`,
`edge_binding_invert: "1"`, `interruptable: "0"`, and
`haptic_intensity: "0"`. Preserve the exported spelling `soft_press_sytle`.
The source has inner-ring radius `21700`, inversion `1`, movement deadzone
`13276`, `requires_click: "0"`, and analog-emulation duty cycle `50`.
W/A/S/D remain Regular Press bindings and use the reference's
`interruptable: "0"`; Q click and stick-touch entry are unchanged.

This is an output scaffold, not a guarded cleanup: it adds or removes no
layers and needs no repeating removal. The user's chosen modifier, deflection,
and preferred Soft Press style determine the useful movement/modifier behavior.
How WASD-only, modifier-only and combined pushes behave after assigning a key
is a [tuning note](Steam%20Behaviour%20Assumptions.md#tuning-notes) (WM2); the
empty slot alone cannot demonstrate modifier output.

**Scaffold inheritance review:** this scaffold change modified only Base's LS
group. Upper layers without an explicit LS-edge binding can inherit the exposed lower
edge; that may be Base's scaffold or another layer's recovery. The 16 layers
with explicit LS-edge recovery retain their own outer geometry (`4915` for
single modifiers, `21000` for the other recovery layers,
inversion off). Every Always On Double Tap window retains its explicit
empty edge block, and the two menu Fn LS mode-shift groups also explicitly
block the edge. Those overrides intentionally displace the modifier. No upper
bindings or layer-mutation order changed in the scaffold update. Inherited source settings can still
affect contexts without their own settings. Which stacks leave Base's edge
exposed, and which displace it, is a scenario test (WM3 in
[test_scenarios_triggers_and_recovery.py](../tests/scenarios/neptune/test_scenarios_triggers_and_recovery.py)).
What a removal exposes under a stick that is already out is assumption A11,
and the feel of the modifier is a tuning note, both in
[Steam Behaviour Assumptions](Steam%20Behaviour%20Assumptions.md#tuning-notes).

### Cleanup Scopes and Concrete Examples

**Rules: R127 to R132** (Layer Definition of Done [§7](Layer%20Definition%20of%20Done.md#7-cleanup)). This section explains them; the rule text is there.

Describe a cleanup by both **when it fires** and **what it removes**. A release
can remove one layer or a family; a guarded fallback does not inherently mean
clear every active layer. A "stack cleanup" here means a named interaction's
stack, never a universal clear-all. The following examples describe the current
90.13 layouts. The scopes are the author's of 2026-09-28; the numbers are
since 90.12, when the cleanup rules shortened every list to the layers that can be
on the stack with its host (R132).

| Scope | Concrete example | State intentionally left alone |
|---|---|---|
| Self only | A Double Tap window removes itself on timeout; a Temp Cursor Gyro cancellation removes only the cursor | The underlying stack and unrelated interactions |
| Local pair | Menu Left: Double Tap Cover release removes itself and Menu Left: Escape; the right-side pair is Double Tap Cover + Tab | Other families; no global cleanup |
| Single-modifier family | Either L1 overlay's release removes itself and the regular and Gyro L1 modifier (it can sit on either); the modifier's cleanup function removes the modifier and L1: Tap Cover. Until 90.57 it also named L1: Temp Cursor Gyro, which binds those inputs as cancels and so answers them itself (R132); on a stick touch it names only the modifier since 90.58, because the cover binds both touches | R1's family and persistent Gyro |
| Current Mod 2 branch | Either L1!R1 regular/Gyro cleanup function removes six layers: that Mod 2, the two single modifiers of its mode, and the three covers. On a stick touch it leaves out L1&R1: Tap Cover since 90.58: that cover binds both touches | The opposite-order R1!L1 pair and persistent Gyro |
| Released side | L1&R1: Tap Cover on L1 release removes eight layers | R1's single-modifier family, which may still be held, and persistent Gyro |
| Whole modifier family plus mode change | Uncovered Mod 2 release removes six layers and deliberately enables or disables persistent Gyro | Unrelated interaction families |
| Transition (since 90.10) | A Transition Set's menu Release removes the transition. It has no cleanup function: a missed release is recovered by the next tap of either menu button. The binding that enters it first clears every layer that can be on the stack there, never Gyro (R163; every layer but Gyro until 90.57) | Persistent Gyro |
| Timed self-exit | Double Tap expiry removes its timed owner only | Other stacks; an early transition removes the timed owner first before changing them |

In alternative, replace L1/R1 modifier-family names with L2/R2. The Menu Left /
Menu Right names and their Select / Start roles do not change.

<a id="lightweight-covers-and-inherited-cleanup"></a>

#### Button Overlays and Inherited Cleanup

**Rules: R138, R142** (Layer Definition of Done [§7](Layer%20Definition%20of%20Done.md#7-cleanup) and [§8](Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking)). This section explains them; the rule text is there.

The [vocabulary](Layout%20Vocabulary.md) calls a layer with one button/action
responsibility a **button overlay**, or **overlay** for short. Combined covers
are overlays spanning two linked buttons. These layers are applied **on
top of an existing interaction stack**. They override the related button/action
and inherit unrelated behavior, including the lower stack's recovery. Repeating
all of the parent's cleanup inputs in each overlay would duplicate its recovery.
Release-only cleanup is not, by itself, evidence of a missing fallback.

**Removed in 90.9 (author, 2026-10-01):** `Menu Left: Backspace` and
`Menu Right: Enter` used to be the example here. They held the second menu
button after the first was released, so it couldn't fall through to Base. The
author decided the menu whose button is held owns the combo, like every other
Fn key: the menu chords now type Backspace / Enter directly, and a still-held
second button falls through to Base when the first is released. The accepted
cost is a stray Escape / Tab if that second button is then released within
300 ms ([record](../findings/2026-10-01-intended-flow-checker/README.md#author-decisions-2026-10-01)).

`L1: Tap Cover` inherits the modifier's edge/click recovery, which removes
the modifier and both overlays. Its explicit touch replacements
preserve guarded recovery but remove only LST/RST helpers on thumb release;
this blocks the lower cursor-add release after cancellation. It has no gyro
source and keeps the owner's ordinary outputs and repeating cover chords.

`L1: Temp Cursor Gyro` instead inherits both touch inputs, including cursor
completion before helper cleanup. Its cancellation inputs repeatedly remove
only itself, exposing the parent's output, repeating cover/Mod 2 transition,
or family recovery. Its two guarded edge exits also remove only cursor; stick
geometry and movement settings remain inherited. Both overlays replace the
primary input with their family-release exit, stopping the 200/250 ms apply/reset
pair. These narrow cancellation responsibilities do not replace the modifier's
broader responsibility for both overlays. Menu Double Tap Covers keep a local
pair exit with Escape/Tab; neither cover has Always On.

**Menu gameplay suppression is intentional, confirmed by the author.** These
layers serve Start/Select menu interactions, not simultaneous gameplay. WASD
modifiers and ramp-up do not need to remain available in that context. The four
menu layers discussed here (Escape, Tab and the two Menu Double
Tap Covers) have active disabled gyro groups; Escape/Tab also explicitly block
RS edge. Preserve those overrides. An overlay has local cleanup and inherited
bindings; that does not require passing through every gameplay function.
After a missed release, use the existing local exit and underlying stack's
recovery; do not add broad cover cleanup just to remove these intended blocks.
See the [blocking audit](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md).

<a id="cover-cleanup-ownership"></a>

#### Overlay Cleanup Ownership

**Rule: R129** (Layer Definition of Done [§7](Layer%20Definition%20of%20Done.md#7-cleanup)). This section explains it; the rule text is there.

Use **button overlay** for a layer with one button/action responsibility and
**owning layer** for a layer that applies it; see [definitions and examples](Layout%20Vocabulary.md).
This describes cleanup responsibility, not GUI ordering or the JSON action-set
parent. A shared overlay can have multiple owning layers.

**A layer that applies an overlay owns responsibility for recovering
that overlay. Its stale-state cleanup must include it when the covered
interaction is no longer valid.** The overlay can keep its local release exit and
inherit broader recovery; it does not need to duplicate the owner's fallback
bindings. The overlay's limited responsibility does not exempt the owning
layer from cleaning it up.

For example, the L1 modifier's recovery removes the modifier,
`L1: Tap Cover` and `L1: Temp Cursor Gyro`. The scroll layer similarly recovers itself
and its `Double Tap Cover`. Apply the same ownership review wherever a layer
adds a cover or helper following this overlay design.

Preserve shared covers or helpers whose interaction is still valid, including
a still-held opposite button. Record the guard or survivor explicitly. This
rule concerns stale-state recovery; it does not broaden every normal release,
delayed-apply reset, or timed expiry into a stack removal. Always On isolation
and execution ordering still apply. The author approved deeper recovery for
Transition Sets in the [LS-edge change](../findings/2026-09-28-left-stick-recovery/CHANGES.md#transition-set-cleanup-depth).
Other extensions to cleanup depth and missing owning-layer targets remain
review/implementation work.

#### Mod 2 Current-Branch Cleanup

Each regular/Gyro Mod 2 variant has sixteen cleanup functions, guarded by
either bumper, with the same six-layer list. For `L1!R1: Modifier 2`:

- `L1!R1: Modifier 2` itself.
- `L1: Modifier 0` and `R1: Modifier 1`, the two single modifiers under it.
- `L1: Tap Cover`, `R1: Tap Cover` and `L1&R1: Tap Cover`, the three covers.

`Gyro | L1!R1: Modifier 2` lists the `Gyro |` modifiers instead. Until 90.11
the list had eleven targets: both modes' modifiers and the two cursor
overlays as well. 90.12 dropped the ones that can never be on the stack with
the host (R132).

The opposite-order pair is deliberately outside the cleanup scope:

| Fallback in either regular/Gyro variant of | Pair not targeted |
|---|---|
| L1!R1: Modifier 2 | R1!L1: Modifier 2 and Gyro \| R1!L1: Modifier 2 |
| R1!L1: Modifier 2 | L1!R1: Modifier 2 and Gyro \| L1!R1: Modifier 2 |

The entry paths support this interpretation: pressing R1 from the L1 modifier
adds the L1!R1 branch; pressing L1 from the R1 modifier adds the R1!L1 branch.
Each entry adds only its corresponding Mod 2 order. The regular/Gyro entry
variants preserve that relationship, as do alternative's L2/R2 variants.
Sibling chords suppress fallback while either modifier remains held. The
fallback does not toggle or remove persistent `Gyro`.

The review decision is to **retain current-branch recovery**. The scope went
from nine targets to eleven with the cursor overlays, and to six in 90.12;
it still excludes the opposite Mod 2 order. Check for an interrupted sequence that leaves
both orders active before broadening it. If both remain, one fallback could
expose the other's recovery and require another gesture; that is not yet a
demonstrated failure. Additional removals can disturb timers, so widening the
list is a behavior change, not harmless normalization.

#### Combined Tap Cover: Preserve the Still-Held Side

`L1&R1: Tap Cover` has a different purpose. On **L1 release**, it removes:

- Both Mod 2 orders in regular/Gyro form — four layers.
- L1's regular/Gyro single modifier and L1: Tap Cover — three layers.
- The combined L1&R1: Tap Cover itself — one layer.

That is eight removals (nine until 90.11, with L1: Temp Cursor Gyro, which can't be
on the stack with the combined cover). It leaves R1's regular/Gyro single modifier, R1: Tap
Cover, and R1: Temp Cursor Gyro untouched so the still-held R1 interaction can continue. R1 release is
the mirror. This does not apply every survivor; it simply avoids removing them.
Persistent Gyro is also preserved.

By comparison, **uncovered Mod 2 release** removes six layers (that Mod 2, its
mode's two single modifiers and the three covers; thirteen until 90.11) and
intentionally changes Gyro state: the regular variant adds Gyro,
and the Gyro variant removes it as a seventh removal. Do not copy that wider
release list or its Gyro toggle into the combined cover or guarded fallback.

#### Rocking Between Modifiers 0, 1 and 2

**Author-confirmed purpose, 2026-09-30, re-confirmed 2026-10-02.** You can
*rock* between the modifiers to type fast: hold both bumpers for Mod 2, let go
of one and you're on the other side's single modifier, press it again and
you're straight back in Mod 2. You never pass through Base, you never wait out
a Double Tap window, and you **never get an accidental scroll**. The author
calls the add order behind this very sensitive: it depends on **stack order**
and on the **execution order** inside each array. Don't normalize either one.

**The one rule behind it.** A release fires on the topmost layer that binds
that bumper. A Double Tap window, and so a scroll, only opens from a single
modifier's own release, and that only happens when the modifier is the top
binder, meaning you tapped the bumper without using it. Every way of using a
bumper puts a layer with a clean release above its modifier first:

| You | Goes on top of the modifier | Its release |
|---|---|---|
| Tap the bumper and let go | Nothing | The modifier's: opens the window. A second tap inside 150 ms scrolls |
| Press any button with the bumper held | Its Tap Cover | Clean exit, no window |
| Hold the bumper 200 ms | Temp Cursor Gyro | Clean exit, no window |
| Press the other bumper too | Both covers, then Mod 2 | See the walkthrough |

The walkthrough uses the default layout; alternative is the same on the L2/R2
trigger soft pulls, and with Gyro on the modifiers and Mod 2 are the `Gyro |`
layers while the covers are shared. Stacks are bottom to top.

| Step | Input | Binding that fires | Stack after |
|---|---|---|---|
| 1 | Hold L1 | Base LB chord adds `L1: Modifier 0` | Base, L1 Mod 0 |
| 2 | Hold R1 too | L1 Mod 0's RB chord adds, in execution order: `L1: Tap Cover`, `R1: Modifier 1`, `R1: Tap Cover`, `L1!R1: Modifier 2` | Base, L1 Mod 0, L1 Tap Cover, R1 Mod 1, R1 Tap Cover, L1!R1 Mod 2 |
| 3 | Keep both held 200 ms | Mod 2's delayed RB chord (chord with LB) adds `L1&R1: Tap Cover`, with the 250 ms reset | … , L1!R1 Mod 2, L1&R1 Tap Cover |
| 4 | Let go of L1 | The combined cover is the top LB binder. Its LB release removes itself, the left side (modifier, Gyro twin, Tap Cover, cursor) and both Mod 2 orders | Base, R1 Mod 1, R1 Tap Cover |
| 5 | Press L1 again | R1's cover doesn't bind LB, so R1 Mod 1 answers. Its LB chord re-adds `R1: Tap Cover` (already there, so it doesn't move), then `L1: Modifier 0`, `L1: Tap Cover`, `R1!L1: Modifier 2` | Base, R1 Mod 1, R1 Tap Cover, L1 Mod 0, L1 Tap Cover, R1!L1 Mod 2 |
| 6 | Keep both held 200 ms | R1!L1's delayed chord is on **L1**, the side pressed second | … , R1!L1 Mod 2, L1&R1 Tap Cover |
| 7 | Let go of R1 | The combined cover's RB release removes the right side and both orders | Base, L1 Mod 0, L1 Tap Cover |
| 8 | Let go of L1 | `L1: Tap Cover` is the top LB binder: clean exit, no window | Base |

What makes it work:

- **Each side's cover sits above its modifier.** The entry chord adds the
  first side's cover, then the second modifier, then its cover, then Mod 2
  last. If a cover were added before its modifier, the modifier would end up
  on top, its release would open the Double Tap window, and pressing that
  bumper again quickly would scroll.
- **Re-adding an active layer doesn't move it.** In step 5, R1 Mod 1's chord
  re-adds `R1: Tap Cover`, which stays where it is. Only the new layers go on
  top. The re-add is there for the case where R1 was pressed first and not
  used yet: it puts R1's cover above R1's modifier before L1's layers go on.
- **The combined cover's release removes only the released side.** The held
  side's modifier, its Tap Cover and its cursor survive, and so does
  persistent Gyro. That is why an owner release can have a narrower scope
  than a cleanup function. Its lists remove **both** Mod 2 orders, because the
  combined cover can sit on either; keep both there.

**Two timing rules:**

- **Be in Mod 2 for 200 ms before rocking.** Until the combined cover lands,
  letting go of **either** bumper fires Mod 2's own release: the quick tap,
  which clears every modifier and toggles Gyro.
- **The 200 ms runs on the bumper pressed second**, as a delayed chord with
  the first bumper, protected by a 250 ms repeating reset on the same button.

**Tests.** [test_modifier_rocking.py](../tests/contracts/neptune/test_modifier_rocking.py)
replays every sequence above with `steam_layout.stacks.walk`, on both layouts,
with Gyro off and on: the double tap that scrolls, the used bumper and the
cursor that don't, the exact add order of both Mod 2 entries, the quick tap
inside 200 ms, rocking in both directions and back and forth, and the
combined cover's lists. It checks that no window opens during rocking and that
each cover stays above its modifier. Swapping two adds in the entry chord
fails eight of its tests.

These scopes remain subject to the [Always On ordering contract](#always-on-layer-isolation-and-the-historical-crash-workaround)
and the three-command-entry limit. Subcommand arrays can contain all the listed
removals within one GUI entry. See the [cleanup audit](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md)
for exact activators, targets, source locations, and other scope examples.

### Empty Bindings and Stuck Layer Cleanup

An explicit `controller_action empty_binding` overrides the lower binding for that input;
it does not mean “inherit.” A layer left active after its intended interaction can therefore
block both normal actions and cleanup bindings in layers underneath it.

The RTP ramp-up fix illustrates this. The earlier Neptune export assigned an unconditional
empty binding to `RTP: Entry Point`'s right-stick edge. If the entry layer remains active, that override
blocks the lower ramp-up action. It can also hide R1's edge cleanup if an R1 modifier
remains underneath.

The July layout uses two cases, also carried into Neptune by the September port:

- **RTP touched:** a chord keeps the empty binding, preserving intentional suppression.
- **RTP no longer touched:** a Regular Press removes `RTP: Tap Cover` and `RTP: Entry Point`,
  exposing the lower edge bindings. It has `hold_repeats: "1"` with no explicit repeat rate.

This cleanup provides another exit if the normal trackpad-release cleanup leaves stale
state. It does not directly apply ramp-up or remove R1. R1's existing cleanup can run once
exposed, and the Base ramp-up binding remains subject to its own conditions.

This is stick-edge cleanup after leaving the trackpad. It preserves the
[RTP exception to the delayed-apply workaround](#interrupted-delayed-layer-applies), which
held until 90.24: no periodic removal was added to the trackpad-touch apply path, where the
author observed interference with trackball momentum.

See the [stuck RTP entry / ramp-up findings](../findings/2026-09-27-rtp-entry-ramp-up/FINDINGS.md)
for the exact bindings, the R1 interaction, and the limits of the static diagnosis.

---

## group_source_bindings States

The value in `group_source_bindings` contains the source and state:

| State | Meaning |
|-------|---------|
| `active` | Group is enabled and processing input |
| `inactive` | Group is disabled |
| `modeshift` | Group activates during mode shift conditions |
| `inactive modeshift` | Group disabled but available for mode shift |

**Format:** `"[source] [state]"` or `"[source] [state] [modifier]"`

Examples:
- `"switch active"` - Switch input group, always active
- `"gyro inactive"` - Gyro group, disabled
- `"button_diamond inactive modeshift"` - Face buttons available for mode shift

---

## File Format Notes

- This JSON format is converted from Valve's VDF (Valve Data Format)
- VDF is a key-value format similar to JSON but with different syntax
- The numeric string IDs (e.g., `"Preset_1000001"`) are auto-generated by Steam
- Preset IDs are roughly sequential based on creation order

---

## Limits the Steam editor sets

The author, 2026-10-04, reading the Steam editor. A value written to a layout
file has to be one the editor could set. What Steam does with a value outside
its range is not known: it may raise or lower it to the nearest end.

| Setting | In the file | Range in the editor | What the layouts hold |
|---|---|---|---|
| Fire Start Delay, Repeat Rate | `delay_start`, `repeat_rate` | Up to 1000 ms | Nothing over 1000 since 90.31. Until 90.30, 1500 and 1550 in `Steering \| LS: Fallback Hold` |
| D-pad Outer Ring Command Radius | `edge_binding_radius` on a D-pad group | 10,000 to 32,000 | 21000 and 21700, inside the range. Until 90.30 also 4915, on the left stick in 34 layers and on the right stick in 7, since the cursor work of 2026-09-29: below the range. Those groups state no radius since 90.31 |
| Directional Pad Layout | `layout` on a D-pad group | Four choices: 0 Radial Without Overlap (four-way), 1 Radial With Overlap (eight-way), 2 Analog Emulation, 3 Cross Gate. The numbers are the Steam client's (read 2026-10-05) | Not stated on most left-stick groups, which then get eight-way (A51). 0 in the Fn layers since the July layout and in `Steering` since 90.34; 1 in the historical Steering fallback guard; restored Entry Guard matches Steering at 0 since 90.43. On the Deck a group that states 1 over a lower layer's group that states 0 stayed four-way (author, 2026-10-06), so since 90.35 the guard replaces `Steering` and is never over it |
| Outer Ring Command Radius on a mouse-mode stick | `edge_binding_radius` on a `joystick_mouse` group | Not read yet | 32767 in Base. Until 90.30 also 7209 in 21 layers; they state no radius since 90.31 |
| Soft Press Threshold | `activation_threshold` | The editor showed the author 0 to 20,000. Assumed to be the editor's own scale: the value in the file is taken to run like the outer ring's, 10,000 to 32,000 (author, 2026-10-04) | 23000, 24996, 25807, 26610 and 29031: ten Soft Presses, all inside that assumed range and all above 20,000. Six are the author's own, from the July layout, and turn assist runs on them |

Looked up on 2026-10-04:

- **Online:** nothing states these ranges. Valve's Steam Input pages, the
  Steam Controller forums and the community guides describe the settings
  without their limits.
- **The installed Steam client:** its settings carry a value, a default, a
  minimum and a maximum. Three have a maximum of 1000: two with a minimum and
  default of 0, and one with a default of 100 and a minimum of 10. That fits
  the start delay, the end delay and the repeat rate, and it would make the
  default repeat rate 100 ms (A35). They were found by their numbers, not by
  name, so this is a match and not a proof. No setting with a range of 10,000
  to 32,000 turned up that way.

**The Soft Press range is an assumption.** The author saw 0 to 20,000 on the
Soft Press Threshold slider, and every threshold in the layouts is above
that. So what the slider shows and what the file holds are taken to be two
scales, and the file's is assumed to match the outer ring's. Nothing confirms
it; read the slider against a known value in the file to settle it.

**The outer ring radius is not an assumption.** It can't go under 10,000 on a
D-pad, and the 4915 in the layouts is wrong (author).

Fixed in 90.31 ([record](../findings/2026-10-04-fallback-window/README.md)): the
fallback's 1500 and 1550 are gone, and no stick group states 4915 or 7209. R173
keeps it that way. Since 90.33 no delay or repeat rate is over 300 ms: the fallback's 1000 ms
window of 90.31 and 90.32 is deleted.

## Quick Reference Table

| Section | Contains | References |
|---------|----------|------------|
| `actions` | Action Set definitions | — |
| `action_layers` | Layer definitions | `actions` via `parent_set_name` |
| `preset[]` | Binding configurations | `actions`/`action_layers` via `name`, `group[]` via `group_source_bindings` |
| `group[]` | Input modes & bindings | Referenced by `preset[]` via ID |

---

---

## Runtime IDs for controller_action Commands

**CRITICAL:** Steam Input generates runtime IDs for action sets and layers based on their **order of appearance** in the JSON structure. These IDs are used in `controller_action` binding commands.

### ID Assignment Rules

1. **Action Sets** are numbered **first**, starting at **1**
2. **Action Layers** are numbered **after** all action sets
3. IDs are assigned based on the **order they appear** in the `actions` and `action_layers` blocks

### ⚠️ CAVEAT: Steam's loader may use Preset numeric key order instead (found 2026-07-11)

**Rule: R104** (Layer Definition of Done [§2](Layer%20Definition%20of%20Done.md#2-placement)). This section explains it; the rule text is there.

The "order of appearance" rule above describes how the GUI/session writes runtime IDs. On a
**fresh VDF load**, Steam has been observed resolving the same positional runtime IDs against
the **`Preset_10000XX` numeric key order** instead. The two orderings normally coincide, but
can diverge — e.g. after reordering layers in the Steam GUI (in-session everything is
handle-based, so nothing looks wrong until the next reload). When they diverge, every binding
whose runtime ID falls in the divergent range silently retargets to a different layer.

Diagnostic signature: `action_layers` keys not in ascending numeric order, with the swapped
layers being exactly the out-of-order entries. Fix: reorder `action_layers` + matching
`preset` blocks into numeric key order (resequencing preset `id` fields) so both
interpretations agree — do this while bindings are in `{{title}}` token form so intent is
preserved. Case study: `findings/2026-07-11-layer-order-swap/FINDINGS.md`.

### Example ID Assignment

Given this structure:

```json
"actions": {
  "Preset_1000001": { "title": "Base" },      // Runtime ID: 1
  "Preset_1000014": { "title": "Gyro" },      // Runtime ID: 2
  "Preset_1000021": { "title": "Steering" },  // Runtime ID: 3
  "Preset_1000028": { "title": "Gamepad" }    // Runtime ID: 4
},
"action_layers": {
  "Preset_1000006": {                         // Runtime ID: 5
    "title": "L2",
    "parent_set_name": "Preset_1000001"
  },
  "Preset_1000007": {                         // Runtime ID: 6
    "title": "R2",
    "parent_set_name": "Preset_1000001"
  }
}
```

**ID Mapping:**
- `Preset_1000001` (Base) → ID **1**
- `Preset_1000014` (Gyro) → ID **2**
- `Preset_1000021` (Steering) → ID **3**
- `Preset_1000028` (Gamepad) → ID **4**
- `Preset_1000006` (L2 Layer) → ID **5**
- `Preset_1000007` (R2 Layer) → ID **6**

### controller_action Command Syntax

**General format:**
```
controller_action COMMAND RUNTIME_ID NAME BEEP, LABEL,
```

| Parameter | Description |
|-----------|-------------|
| `COMMAND` | The action: `CHANGE_PRESET`, `add_layer`, `remove_layer`, `hold_layer` |
| `RUNTIME_ID` | Numeric ID of the action set or layer (see ID Assignment Rules above) |
| `NAME` | `1` = show the layer's or set's name on screen when it changes, `0` = don't |
| `BEEP` | `1` = beep when it changes, `0` = silent |
| `LABEL` | Optional display label (usually empty) |

**The order of the two flags (A49).** Until 90.28 this section had them the other
way round: the beep first. The Steam client's own message for the command lists
`display` and then `beep`, and its dialog shows "Display name when changed" above
"Beep when changed" (read from the installed client on 2026-10-04). On the Deck the
author heard no beep from any command written `1 0`. The layouts wrote `1 0` for
"beep, no name" from 90.10 to 90.28; 90.29 moved all of them to `0 1`
([record](../findings/2026-10-04-quiet-resets-and-beeps/README.md)).

### controller_action Command Examples

**Change to Base action set (name and beep):**
```
controller_action CHANGE_PRESET 1 1 1, ,
                                ↑ ↑ ↑
                                │ │ └─ Beep
                                │ └─── Show the name
                                └───── Runtime ID 1 = Base
```

**Add or remove a layer silently:**
```
controller_action add_layer 5 0 0, ,
controller_action remove_layer 5 0 0, ,
                               ↑ ↑ ↑
                               │ │ └─ No beep
                               │ └─── No name
                               └───── Runtime ID 5 = L2 Layer (Preset_1000006)
```

**Remove the Gyro layer with the name and the beep** (the Modifier 2 toggle):
```
controller_action remove_layer 2 1 1, ,
```

**Enter a stateful layer with the beep and no name** (R161):
```
controller_action add_layer 88 0 1, ,
                            ↑↑ ↑ ↑
                            ││ │ └─ Beep
                            ││ └─── No name
                            └┴───── Runtime ID 88 = Menu Keys
```

**Hold a layer while pressed (silent):**
```
controller_action hold_layer 13 0 0, ,
```

### When to Use the Name and the Beep

| Scenario | Name | Beep | Rationale |
|----------|------|------|-----------|
| Frequent layer changes (triggers, modifiers, covers, cleanups) | `0` | `0` | Too frequent to announce |
| The `Gyro` toggle | `1` | `1` | The author's own, since the July layout |
| Entering or leaving a stateful layer through a transition, or by its own exit (R161) | `0` | `1` | The author, 2026-10-02: a beep and no on-screen notification |
| The Fn layers' adds | `0` | `0` | Silent since 90.41; their Low haptic bump remains |
| Temporary layers (`hold_layer`) | `0` | `0` | Too frequent to announce |

### ⚠️ CRITICAL WARNING: ID Shift on Deletion

**Rule: R103** (Layer Definition of Done [§2](Layer%20Definition%20of%20Done.md#2-placement)). This section explains it; the rule text is there.

**If you delete an action set or action layer, ALL subsequent IDs will shift down by one.**

**Example - Before deletion:**
```
Base (Preset_1000001) → ID 1
Gyro (Preset_1000014) → ID 2
Alt (Preset_1000021) → ID 3
L2 Layer (Preset_1000006) → ID 4
R2 Layer (Preset_1000007) → ID 5
```

**After deleting "Gyro" (ID 2):**
```
Base (Preset_1000001) → ID 1
Alt (Preset_1000021) → ID 2  ← SHIFTED from 3
L2 Layer (Preset_1000006) → ID 3  ← SHIFTED from 4
R2 Layer (Preset_1000007) → ID 4  ← SHIFTED from 5
```

**Consequences:**
- All `controller_action` commands referencing IDs ≥ the deleted item **must be updated**
- Bindings like `"controller_action add_layer 5 0 0"` would now reference a different (or non-existent) layer
- **Always recalculate all runtime IDs** after adding or removing action sets/layers

### Best Practices

1. **Never hardcode runtime IDs** - Calculate them dynamically based on current order
2. **Count carefully** - Action sets come first (starting at 1), then layers
3. **Revalidate after modifications** - Any structural change affects all downstream IDs
4. **Read IDs as titles** - `python3 -m tools.convert_runtime_ids to-titles` shows every ID as `{{Base::Title}}`, and `python3 -m tools.duplicate_layer <layout> --list` prints the current ID table. The old hand-kept table, `Layer Reverse Lookup.md`, is in `archived/`: it maps release 31.0

---

---

## Action Sets Quick Reference

| Preset ID | Title |
|-----------|-------|
| `Preset_1000001` | Base |
| `Preset_1000014` | Gyro |
| `Preset_1000021` | Alt |
| `Preset_1000028` | Gamepad |

---

## Runtime ID Calculation Algorithm

```python
def calculate_runtime_id(preset_name, actions_dict, action_layers_dict):
    """Calculate the runtime ID for a given Preset_* identifier."""
    position = 1
    
    # Check action sets first
    for action_key in actions_dict.keys():
        if action_key == preset_name:
            return position
        position += 1
    
    # Check action layers next
    for layer_key in action_layers_dict.keys():
        if layer_key == preset_name:
            return position
        position += 1
    
    return None  # Not found
```

---

## See Also

- [Neptune Chorded Button Ids](Neptune%20Chorded%20Button%20Ids.md) - Chord button ID reference for Steam Deck
- [Runtime IDs](../docs/runtime-ids.md) - how the IDs are numbered, and the list-order hazard
- In `archived/`, for the older multi-set layouts: [Layer Reverse Lookup](../archived/Layer%20Reverse%20Lookup.md) (layer IDs as of release 31.0) and [Ramp Up Layers Comparison](../archived/Ramp%20Up%20Layers%20Comparison.md)
