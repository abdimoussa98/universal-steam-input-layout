# Steam Input JSON Configuration Structure

This document describes the structure and relationships within Steam Input controller configuration files (JSON format converted from VDF).

**References:**
- [Steam Input Action Sets & Layers Overview](https://partner.steamgames.com/doc/features/steam_controller/iga_file)
- [Action Set Layers Behavior (overlay/stacking)](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers)

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

#### Command Entry Budget

**Hard requirement for this repository: at most three GUI command entries per
input.** The layout author confirmed on 2026-09-27 that subcommands are allowed
inside those entries. This records the required design constraint, not a claim
about an independently measured limit in every Steam client version.

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

Run `python3 audit_command_budget.py path/to/layout.json` before finalizing.
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
- For layer management, place `add_layer` commands at the **top** so they apply after all cleanup/removal operations
- Place `remove_layer` cleanup commands **below** the primary action
- This ensures a clean state before the main layer is added

#### Interrupted Delayed Layer Applies

The layout author observed a Steam Input bug where interrupting an `add_layer` command
before its Fire Start Delay completes can prevent the command from firing on the next
press. **Repeated `remove_layer` commands reset the start delay and allow the delayed apply
to trigger again.** This is the author's observed workaround; the exact Steam internals
were not independently verified.

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
port added it to all four Neptune Mod 2 layers, regular and gyro. The separate single-bumper
`R1: Tap Cover` apply still uses a 300 ms delay without this added repeating removal.
The 200/250 ms values describe this implementation, not a general timing formula.

**RTP trackpad exception:** the author deliberately left this workaround out of the RTP
trackpad layers because repeated layer removal interfered with **trackball momentum**.
Preserve that exception when copying the bumper fix. RTP's delayed touch binding applies
`RTP: Tap Cover` after 150 ms without a corresponding repeating removal on that input.
Other repeated cleanup bindings in RTP-related layers serve separate purposes; their
presence does not mean this workaround was applied to the trackpad-touch path.

See the [R1 and L1&R1 tap-cover findings](../findings/2026-09-27-r1-tap-cover/FINDINGS.md)
for exact groups, source locations, the Neptune comparison, and supporting research.

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
   - Bindings from the layer **overlay** (replace) the parent Action Set's bindings
   - Only the inputs defined in the layer's groups are affected
   - Inputs not defined in the layer retain the parent set's behavior

3. **Layer Deactivated**: When the layer is released, the controller reverts to the parent Action Set's bindings.

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
[RTP exception to the delayed-apply workaround](#interrupted-delayed-layer-applies): no
periodic removal was added to the trackpad-touch apply path, where the author observed
interference with trackball momentum.

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
controller_action COMMAND RUNTIME_ID BEEP NOTIFICATION, LABEL,
```

| Parameter | Description |
|-----------|-------------|
| `COMMAND` | The action: `CHANGE_PRESET`, `add_layer`, `remove_layer`, `hold_layer` |
| `RUNTIME_ID` | Numeric ID of the action set or layer (see ID Assignment Rules above) |
| `BEEP` | `1` = play haptic/beep feedback on trigger, `0` = silent |
| `NOTIFICATION` | `1` = show on-screen notification, `0` = no notification |
| `LABEL` | Optional display label (usually empty) |

### controller_action Command Examples

**Change to Base action set (with beep and notification):**
```
controller_action CHANGE_PRESET 1 1 1, ,
                                ↑ ↑ ↑
                                │ │ └─ Show notification
                                │ └─── Play beep
                                └───── Runtime ID 1 = Base
```

**Add/activate L2 layer (silent, no notification):**
```
controller_action add_layer 5 0 0, ,
                            ↑ ↑ ↑
                            │ │ └─ No notification
                            │ └─── No beep
                            └───── Runtime ID 5 = L2 Layer (Preset_1000006)
```

**Remove L2 layer (silent, no notification):**
```
controller_action remove_layer 5 0 0, ,
                               ↑ ↑ ↑
                               │ │ └─ No notification
                               │ └─── No beep
                               └───── Runtime ID 5 = L2 Layer
```

**Remove Gyro layer with feedback (beep and notification):**
```
controller_action remove_layer 2 1 1, ,
                               ↑ ↑ ↑
                               │ │ └─ Show notification
                               │ └─── Play beep
                               └───── Runtime ID 2 = Gyro layer
```

**Hold layer while pressed (silent):**
```
controller_action hold_layer 13 0 0, ,
                             ↑↑ ↑ ↑
                             ││ │ └─ No notification
                             ││ └─── No beep
                             │└───── Runtime ID 13 = Layer held while button pressed
                             └────── 
```

**Add a later layer (silent):**
```
controller_action add_layer 32 0 0, ,
                            ↑↑ ↑ ↑
                            ││ │ └─ No notification
                            ││ └─── No beep
                            │└───── Runtime ID 32 = 32nd total item
                            └────── 
```

### When to Use Beep/Notification

| Scenario | Beep | Notification | Rationale |
|----------|------|--------------|-----------|
| Frequent layer toggles (triggers, modifiers) | `0` | `0` | Avoid spam during gameplay |
| Mode switches (Base ↔ Gyro ↔ Gamepad) | `1` | `1` | User should know mode changed |
| Debug/testing | `1` | `1` | Helps verify bindings work |
| Temporary layers (hold_layer) | `0` | `0` | Too frequent to notify |

### ⚠️ CRITICAL WARNING: ID Shift on Deletion

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
4. **Use Layer Reverse Lookup.md** - Cross-reference with the ID mapping documentation

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

- `Layer Reverse Lookup.md` - Complete mapping of layer IDs to names and parents
- `Neptune Chorded Button Ids.md` - Chord button ID reference for Steam Deck
- `Ramp Up Layers Comparison.md` - Comparison of turning/ramp up layer configurations
