# Plan: split Menu Buttons: Entry Point into Menu Left / Menu Right entry layers

- **Date:** 2026-09-27
- **Status:** Execution steps 1–4 done on 2026-09-27. Both `neptune/*.json` files are edited and pass the static checks. Waiting on step 5 (VDF conversion and in-game testing on the Deck).
- **Result:**
  - **New layers (runtime ID, key):**
    - Menu Right: Entry Point: 27, `Preset_1000083`
    - Menu Left: Backspace: 43, `Preset_1000132`
    - Menu Right: Enter: 44, `Preset_1000133`
  - **Existing layers:** every runtime ID after 26 shifts up. The only existing key that changes is Transition Set 0's, from `Preset_1000132` to `Preset_1000134`.
  - **New groups:** 13042–13051 in the default and 13039–13048 in the alternative.
- **Deviation from the outline below:** each combo layer also has a disabled `gyro` group, as `Menu Right: Tab` does. That keeps the gyro off if the other menu button is released first. That's the one moment the combo layer sits directly on Base, and today the re-added entry layer keeps the gyro off there too.

## Context

This comes from the Bugs section of `todos.md`: "Split menu entry layer into separate Menu Left / Menu Right layers." It also folds in:

- "Fix tap cover / menu entry bug (start delay interrupt)" for the menu buttons (decision 5)
- a fix for a stray Tab / Escape after the Enter / Backspace combos (decision 6)

Today a single layer, `Menu Buttons: Entry Point`, runs the press / hold / release logic for both Start and Select. Every other menu layer already comes in Left / Right pairs. This doc traces the current lifecycle in both Neptune layouts and proposes the split.

**Names:**

- **Select** is Menu Left: `button_menu`, chord 15.
- **Start** is Menu Right: `button_escape`, chord 14.
- The existing layers follow this pattern. The Left layers bind Select and send Escape; the Right layers bind Start and send Tab.

**One rule the design relies on:** the topmost layer that binds an input owns that input. That's how the Fn layer "covers" the release: once it's on top, the Entry Point's release binding can't fire.

**Source:** the current `neptune/*.json` (commit `3f84c06`), read in title form. Both files share this logic, and the differences are noted where they matter.

## How it works today

### One button's lifecycle

This shows Select. Start is identical, with Tab and the Right layers.

```
Select pressed ─► Base adds Menu Buttons: Entry Point (self-chord, repeats while held)
 │
 ├─ still held at 300 ms ─► adds Menu Left: Fn Layer on top
 │     └─ Select released ─► removes Fn + Entry Point (nothing is sent)
 │
 └─ released before 300 ms ─► Entry Point swaps itself for Menu Left: Double Tap
       ├─ 50 ms later: Escape
       ├─ 150 ms later: Double Tap removes itself
       └─ Select pressed again within the 150 ms ─► Menu Left: Escape (Escape on press)
             ├─ released ─► back to Double Tap (Escape again 50 ms later)
             └─ held 150 ms ─► adds Menu Left: Double Tap Cover
                                (Escape held; releasing clears both layers)
```

### Everything else the shared Entry Point does

| While the Entry Point is active | Binding | Result |
|---|---|---|
| Hold Select, press Start | Start chorded with Select: add Menu Left: Fn now | Fn's Start chord sends **Enter** |
| Hold Start, press Select | Select chorded with Start: add Menu Right: Fn now | Fn's Select chord sends **Backspace** |
| RS or LS click with a menu button held | add that side's Fn layer now | The Fn layer's stick-click chords then open Transition Set 0 (RS) / 1 (LS) |
| Touch a stick with a menu button held | touch chords: empty | Blocks RST / LST: Entry Point |
| Lift your thumb off a stick (touch release) | stick cleanup + add **Menu Left**: Fn, whichever button is held | See problem 2 |
| RS to the edge with no menu button held | remove both Fn layers and the Entry Point | Stuck-layer cleanup. The alternative adds them instead (problem 3) |
| Bumpers / triggers | Default: bumpers scroll, trigger clicks are blocked. Alternative: triggers scroll, bumpers are mouse buttons | |
| Gyro | `disabled` | |

### The Fn layers (the hold result and the tap cover)

`Menu Left: Fn Layer` and `Menu Right: Fn Layer` are the same except for which menu button their own chords use.

- **F-keys and modifiers:** F1–F12 are on the face buttons, D-pad, bumpers, and triggers. Right Ctrl / Alt / Shift and Win are on the back buttons. These work with either menu button held.
- **Punctuation:** the stick directions type punctuation, but only while the layer's own menu button is held.
- **Stick clicks:** with the layer's own button held, they open the Transition Sets and mode-shift the stick into a punctuation D-pad.
- **Cleanup:** pressing any of these inputs with no menu button held removes the Fn layer and the Entry Point, and the press passes through to the layer below.

### Problems with one shared layer

1. **One layer for two buttons.** Whichever button is pressed first adds the Entry Point, and every exit removes all of it. Nothing records which button opened it.
2. **Lifting your thumb off a stick (touch release) is hard-wired to the Left side.**
   - It adds Menu Left: Fn even while Start is the button being held.
   - For Select, that covers the release, so the tap is cancelled.
   - For Start, by the bindings:
     - Menu Left: Fn's own Start cleanup removes it and the Entry Point immediately.
     - Base then re-adds the Entry Point because Start is still held, which restarts Start's 300 ms timer.
   - So the same action behaves differently depending on the side.
3. **Alternative only: the RS-edge cleanup adds instead of removes.** With no menu button held, RS to the edge repeatedly *adds* both Fn layers and the Entry Point, where the default removes them. A stuck Entry Point gets worse instead of clearing.
4. **Enter / Backspace can be followed by a stray Tab / Escape.** Take the Enter combo:
   1. Hold Select and press Start: Enter is sent.
   2. Lift **Select first**. That removes the Left layers while Start is still down.
   3. Base's Start binding repeats while the button is held, so it re-opens Start's entry layer, as if Start had just been pressed.
   4. Releasing Start within 300 ms counts as a quick tap and sends **Tab**.

   The mirror sends **Escape** after Backspace, which can close a dialog.

Also found while tracing. The split doesn't change these, but they're worth checking on the Deck:

- **A double tap may send the key three times.** By the bindings, a quick double tap sends Escape three times:
  - once from the first tap's Double Tap layer
  - once on the second press
  - once when the second release re-enters Double Tap

  Tab works the same way.
- **The 300 ms delayed chords are interruptable** (the default). R1's delayed tap-cover chord sets Interruptable Off ([finding](../findings/2026-09-27-r1-tap-cover/FINDINGS.md)). Decision 5 adds the repeating-removal reset and leaves this setting as it is.

## Proposed rewrite

### Layers

- **Rename** `Menu Buttons: Entry Point` to **`Menu Left: Entry Point`**. It keeps its slot and key.
- **Insert** **`Menu Right: Entry Point`** directly after it (decision 1).
- **Insert** **`Menu Left: Backspace`** and **`Menu Right: Enter`** directly after `Menu Right: Tab` (decision 6).
- **Runtime IDs and keys:** every layer after an insertion moves up in runtime ID, and the `Preset_` keys get renumbered to match the list order, as in the port.
- **Base:** Select's chord adds Menu Left: Entry Point, and Start's chord adds Menu Right: Entry Point.
- **Fn layer cleanups:**
  - Menu Left: Fn Layer's cleanups remove Menu Left: Entry Point. That's 22 references, 2 of them in dormant groups.
  - Menu Right: Fn Layer's cleanups remove Menu Right: Entry Point. That's 20 references.
- Nothing else references the entry layer.

### Menu Left: Entry Point

| Input | Binding | Compared with today |
|---|---|---|
| Select release | add Menu Left: Double Tap, remove Menu Left: Entry Point | Same |
| Select self-chord, 300 ms delay | add Menu Left: Fn Layer | Same |
| Select press, repeating every 350 ms, Interruptable Off | remove Menu Left: Fn Layer | **New**: start-delay reset (decision 5) |
| Start chorded with Select | add Menu Left: Fn Layer, then Menu Right: Enter on top | **Also adds Menu Right: Enter** (decision 6) |
| Start press (repeating) | remove Menu Left: Entry Point | **New**: stuck-layer cleanup (decision 4) |
| RS / LS click chorded with Select | add Menu Left: Fn Layer | Start's copies move to Menu Right |
| RS edge chorded with Select | empty | Start's copy moves to Menu Right |
| RS edge press (repeating) | remove Menu Left: Fn Layer and Menu Left: Entry Point | Now clears only its own side; the alternative is fixed |
| RS / LS touch chorded with Select | empty | Start's copies move to Menu Right |
| RS / LS touch release | stick cleanup + add Menu Left: Fn Layer | Same, in today's order: the add stays at the bottom of the array (decision 3) |
| Bumpers, triggers, gyro | unchanged | Same |

### Menu Right: Entry Point

This is the same table with these swaps: Select ↔ Start, Left ↔ Right, Escape ↔ Tab, and Enter ↔ Backspace.

That includes the stick touch release. It clears the same RST / LST layers and adds **Menu Right**: Fn Layer, in today's binding order (decision 3). So the Right side no longer borrows the Left Fn layer, which fixes problem 2.

### Enter / Backspace layers (decision 6)

The Enter and Backspace keys move out of the Fn layers' chords into their own layers. These are built like `Menu Right: Tab` and `Menu Left: Escape`.

**`Menu Right: Enter`** binds only Start:

- **Start press** (Interruptable Off) sends Enter, held while Start is held, the same way Tab does.
- **Start release** removes the layer and sends nothing else.

Nothing else is bound. So the Fn layer underneath keeps its F-keys, and it still owns Select's release.

**`Menu Left: Backspace`** is the mirror: it binds only Select, sends Backspace, and removes itself on release.

**What adds them:**

| Where | Today | New |
|---|---|---|
| Menu Left: Fn Layer, Start chorded with Select | `key_press RETURN` | add Menu Right: Enter |
| Menu Left: Entry Point, Start chorded with Select (before 300 ms) | add Menu Left: Fn Layer | add Menu Left: Fn Layer, then Menu Right: Enter on top |
| Menu Right: Fn Layer, Select chorded with Start | `key_press BACKSPACE` | add Menu Left: Backspace |
| Menu Right: Entry Point, Select chorded with Start (before 300 ms) | add Menu Right: Fn Layer | add Menu Right: Fn Layer, then Menu Left: Backspace on top |

**Why this fixes problem 4:** the new layer owns the second button until it's released. So after lifting Select first, Base can't re-open Start's entry layer, and releasing in either order sends nothing extra.

**What still works:**

- **Repeated combos:** each Start press while holding Select adds the layer again, so repeated Enters still work.
- **Adding the layer directly on the early path:** the entry layers add it themselves before 300 ms. That path no longer depends on the Fn layer's chord firing for a button that's already down.

### Start-delay reset (decision 5)

This uses the same pattern as the two-bumper tap covers and Turning Ramp Up 0.

- **The binding:** on the input that carries the delayed apply, a press repeats and removes the layer being applied. Menu Left removes Menu Left: Fn Layer, and Menu Right removes Menu Right: Fn Layer.
- **Why it works:** each repeated removal restarts the delay, so a hold whose apply was interrupted can still bring up the Fn layer.
- **When it stops:** once the Fn layer is up, it owns that button, so the repetition stops.
- **Interval:** every existing use repeats at the delay plus 50 ms (200 → 250, 250 → 300), so the 300 ms hold gets **350 ms**.

### What changes in play

- **Holding a menu button recovers after an interrupted 300 ms apply** (decision 5).
- **Enter / Backspace** no longer risk a stray Tab / Escape, whichever finger lifts first (decision 6).
- **A stuck entry layer no longer swallows the other menu button.** It clears, and the press opens that button's own entry layer (decision 4).
- **The alternative's RS-edge cleanup** now removes the layers instead of adding them.
- **Lifting a thumb off a stick while holding Start** now brings up Menu Right: Fn, the way Select already brings up Menu Left: Fn. Releasing Start afterwards sends nothing. Today it restarts Start's timer instead, so a quick release can still send Tab (decision 3).
- **Everything else is unchanged:** taps, holds, double taps, stick clicks, Transition Sets, scroll, and gyro off.

## Decisions (settled 2026-09-27)

1. **Placement:** directly after Menu Left: Entry Point.
2. **Both buttons held:** keep today's logic.
3. **Stick touch release** (lifting a thumb off a stick): clear the same RST / LST layers as today (Temporary Gyro, Tap Cover, Entry Point) and add the side's own Fn layer. Keep today's binding order: the add stays at the bottom of the array. Stick deflection / edge is separate and follows the tables above.
4. **Stuck-layer cleanup for the other menu button:** yes.
5. **Start-delay bug:** folded in as a 350 ms repeating removal of each side's own Fn layer.
6. **Enter / Backspace release order:** move the keys into `Menu Right: Enter` and `Menu Left: Backspace`, placed after Menu Right: Tab.

## Execution outline

This follows the same pipeline as the previous two plans.

1. Run the pre-flight check, then `to-titles` into a scratchpad copy.
2. Run a one-off edit script with assertions. It:
   - renames the layer and all its tokens
   - copies the 6 live groups to new group IDs for Menu Right: Entry Point (the dormant `button_diamond` group isn't copied)
   - trims each side, and adds the start-delay reset and the other-button cleanup
   - points each stick touch release at the side's own Fn layer, keeping today's binding order
   - builds `Menu Right: Enter` and `Menu Left: Backspace` (one `switch` group each, plus a disabled `gyro` group; see Status)
   - rewires the four combo chords
   - retargets Base and the Menu Right Fn cleanups
   - fixes the alternative's RS edge

   Some group IDs here differ between the two files, so the script finds groups by layer and source, as before.
3. Insert the three new layers at their places in the list, then renumber the `Preset_` keys and the preset IDs.
4. Run `to-ids`, the leftover-token grep, the pre-flight check, and the round trip.
5. Copy the results over `neptune/*.json`. Then you convert to VDF and test on the Deck.

## Verification

**Static:**

- The pre-flight check and the token round trip are clean.
- `Menu Buttons: Entry Point` appears nowhere, and there are 53 layers.
- **Semantic diff:** only these change:
  - Base (Start / Select)
  - the entry layers and the two Fn layers
  - the two new Enter / Backspace layers
- **Mirrors:**
  - Menu Right: Entry Point equals Menu Left: Entry Point with the sides swapped.
  - Menu Left: Backspace mirrors Menu Right: Enter.
- `key_press RETURN` / `BACKSPACE` appear only in the new layers.

**In-game (both variants):**

1. Tapping Select sends Escape, and tapping Start sends Tab.
2. Holding either for 300 ms brings up its Fn layer. The F-keys work, and releasing sends nothing.
3. **Start-delay reset:** reproduce the interrupted hold you've seen, then keep holding or hold again. The Fn layer comes up.
4. **Enter / Backspace:**
   - Select → Start sends Enter, and Start → Select sends Backspace. Check this both quickly (before 300 ms) and after the Fn layer is up.
   - Releasing in either order sends nothing extra.
   - Holding the second button repeats the key.
   - Tapping it again while holding the first sends it again.
5. Double tap and hold: the key repeats, and releasing stops it.
6. A menu button + stick click opens a Transition Set, and the stick punctuation works.
7. **Stuck entry layer:** the other menu button still works, and RS to the edge clears the layer. In the alternative, it no longer adds layers.
8. Start / Select inside the modifier layers still give the nav keys.
9. **Stick touch release:** hold Start, touch a stick and lift off, then release Start. Menu Right: Fn comes up, and no Tab is sent. Select does the same with Menu Left: Fn, and no Escape is sent.

## Related todos (not in this plan)

- **Menu refactor:** the Menu stateful set, and Temp cursor gyro.
- **Move gamepad layer** → Menu Right + RS click / Menu Left + LS click (the Transition Sets).
