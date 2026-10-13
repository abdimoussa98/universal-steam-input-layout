# The layer list in a new order (90.64)

Built on 2026-10-12 from the **90.63** snapshot, both layouts, on the author's
word: "reorder all the layers keep the initial order ramp up 0, ramp up 1.
then the stateful base layers: gyro, steering, cursor gyro, menu, gamepad.
then the other layer still separate by the parent statful layers, so all the
base then gyro, so on so forth. Within that group of stateful leftover
layers, i want you to determine the order yourself". 90 layers in each
layout. Nothing here has run on the Deck.

No bind, setting or group changed. 88 of the 90 layers moved; the two ramp
layers kept places 1 and 2. Removes are unchanged: 2,885 and 2,943.

## The order

Default-layout titles; the alternative layout has L2 and R2 for L1 and R1.

| Places | Group | Layers |
|---|---|---|
| 1 to 2 | The ramp | `Turning Ramp Up 0`, `Turning Ramp Up 1` |
| 3 to 7 | The stateful layers | `Gyro`, `Steering`, `Cursor Gyro`, `Menu Keys`, `Gamepad` |
| 8 to 22 | Base: the bumpers | The two modifiers, the two Modifier 2 layers, the three Tap Covers, the two Temp Cursor Gyro layers, the two Double Taps, `L1: Scroll Down`, `R1: Scroll Up`, the two Double Tap Covers |
| 23 to 31 | Base: the sticks | `Gyro Off Ramp Up`, then for both sticks: Entry Point, Tap Cover, Double Tap, Temporary Gyro |
| 32 to 41 | Base: the trackpads | The right pad's Entry Point, Tap Cover, Double Tap and `RTP: Circular Scroll`; the two Click Entry Points, `LTP: Arrow Keys`, `RTP: Mouse Buttons`, the two Middle Click layers |
| 42 to 45 | Base: the held keys | `Escape`, `Tab`, `Backspace`, `Enter` |
| 46 to 66 | Base: the menu buttons | The two Entry Points, the three `Menu Buttons` guard layers, the two Fn Layers, the two Double Taps, `Menu Left: Escape`, `Menu Right: Tab`, the two Double Tap Covers, then the four `Menu Left!Right` and the four `Menu Right!Left` layers |
| 67 to 69 | Base: the transitions | `Transition Set 0`, `1`, `2` |
| 70 to 73 | Gyro | The two Gyro modifiers and the two Gyro Modifier 2 layers |
| 74 to 86 | Steering | `Steering \| LS: Entry Guard`, the W and S layers, the two Modifier 2 layers, the two stick modifiers, the Tap Cover, the two Double Taps, the two scroll layers, the Double Tap Cover |
| 87 to 90 | Steering and Cursor Gyro | The two `Stateful \| Menu` Entry Points and the two `Stateful \| Menu` Fn Layers |

The full list, with each layer's old place, is in the
[default](default-build-report.json) and
[alternative](alternative-build-report.json) build reports.

## The choices that were mine

- **Inside a group:** by input, and for one input in the order its gesture
  runs: Entry Point, Tap Cover, Double Tap, what the double tap gives,
  Double Tap Cover. Left before right, as the titles already pair them.
- **A layer's parent is the stateful layer it is entered from.** A layer
  entered from Base is in the Base group even when it also works over
  `Gyro`: the Temporary Gyro layers, the Temp Cursor Gyro layers, `Gyro Off
  Ramp Up`.
- **`Cursor Gyro`, `Menu Keys` and `Gamepad` have no group.** No layer is
  theirs alone.
- **The four `Stateful | Menu` layers** are added from `Steering` and from
  `Cursor Gyro`, so they are a last group of their own.
- **The three Transition Sets** are entered from the menu buttons, so they
  close the Base group, numbered 0, 1, 2.

## How it was done

In `{{Base::Title}}` form: `action_layers` and the preset blocks are put in
the new order, the existing `Preset_` numbers are handed out again in
ascending order, and the preset ids run from 0 (R104). Every layer command
is then converted to the new positions.

The builder stops unless every layer, read by title, is bind for bind what
it was on 90.63, the groups are untouched, the numbers convert back to the
same titles, and the fix pipeline changes nothing.

R103 (a new layer is appended, so no position shifts) still holds for new
layers. This build moves positions on purpose; its row says so.

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup).
- **Pre-flight:** both VDFs exported and verified against their JSON; the
  snapshot equals the installed files.
- **New tests,** [`tests/test_layer_order_90_64.py`](../../tests/test_layer_order_90_64.py),
  five: the first seven layers; the rest in one run per parent; the working
  layout has the builder's order; the `Preset_` keys, blocks and ids follow
  the list; every layer is bind for bind what it was on 90.63.
- **Unverified assumptions:** 49, in
  [unverified-assumptions.txt](unverified-assumptions.txt). 395 scenarios.
- **Random walks, the whole log compared** with 90.63 ([`proof.py`](proof.py),
  [`proof.txt`](proof.txt)): 24,000 walks a layout, half with one release
  in ten missed. No log differs in either layout, at either rate.
- **Full suite:** 1,257 tests in 111 modules, with the same 25 expected
  failures. A first run failed in four modules. Three compared layer
  positions or raw layer numbers with an older build
  (`test_steering_entry_quiet_drivers`, `test_steering_entry_feedback`,
  `test_scenarios_90_52`); they now compare by title. The fourth was the
  5-second limit in `test_audit_inheritance`, missed while other runs shared
  the machine. All four pass on a rerun.

## What it rests on

- **A22:** Steam can resolve layer numbers by `Preset_` key order on a fresh
  load. The keys and the list agree here, as R104 asks.
- **Positions mean nothing to Steam beyond naming a layer.** The stack
  follows the order layers are added in, not the list. Every build so far
  has relied on that.

## On the Deck

Check first that the configurator's title shows `:: 90.64`, after a fresh
load of the layout.

1. The layer list in the editor shows the order above.
2. One gesture from each group lands where it should: hold L1 (scroll),
   rest a thumb on a stick, click the right pad, hold Start for the Fn
   layer, enter `Gyro` and `Steering`, hold R1 in `Steering` for W.
