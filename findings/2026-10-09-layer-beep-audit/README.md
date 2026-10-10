# Layer add/remove beep audit

Investigation of both live **90.42** layouts and their VDF exports, 2026-10-09.
No layout, export, simulator, or haptic setting was changed. The Entry Guard,
driver/modifier cleanup, and deferred two-bumper gesture fixes remain unimplemented.

**Gyro-off has three beep-enabled removals in one Release entry; Gyro-on has
one beep-enabled add.** This is the clearest configuration-level candidate for
the reported duplicate sound. It does not establish how many sounds Steam
actually plays: two of those removals normally target layers that are absent.

## Base ↔ Gyro

| Gesture | Beep requests, in execution order | Requests affecting present/new layers in the ordinary trace |
|---|---|---:|
| Quick two-driver toggle from Base | Add `Gyro` | 1 of 1 |
| Quick two-driver toggle from Gyro | Remove `Steering \| LS: Fallback Guard`; remove `Steering`; remove `Gyro` | 1 of 3 |

The extra flags live in **both `Gyro` Modifier 2 layers**, on both driver
Release entries: four affected entries per layout. Default uses L1/R1;
alternative uses L2/R2. Default group IDs are `12950` and `12961`; alternative
group IDs are `12948`, `12949`, `12959`, and `12960`.

The ordinary quick-toggle traces request all three at the **first physical
driver release**, regardless of which driver was pressed or released first.
The second release adds no beep request. This does not resolve the separate
Steering two-bumper release-order bug.

`Gyro` uses flags `1 1` (name and beep); the other two removals use `0 1`
(beep only). Binding arrays execute bottom to top; the table gives runtime
order. Name display is a separate setting from the beep.

These extra flags predate the recent Fn/Steering changes:

- **90.33** extended Gyro Modifier 2 cleanup with a beeping Steering removal:
  [builder](../2026-10-05-steering-fallback-guard/build_candidate.py).
- **90.35** also enabled the Fallback Guard removal's beep:
  [builder](../2026-10-06-steering-fallback-swap/build_candidate.py).
  Its rationale explicitly assumes an absent-layer removal stays silent.
- **90.42** left those cleanup flags intact while making Fallback Guard dormant.
  No current binding adds that guard. Its removal still requests a beep.

The native sound behavior is unresolved. The repository describes the flag
as “beep when it changes,” but there is no confirmed Deck result here for
an already-absent removal. The simulator logs flagged commands even when
they do not change the stack. Consequently **three simulated beep requests
are not proof of three audible beeps**, or proof of the user's exact double
beep. If Steam suppresses every no-op removal, the clean Gyro-off trace has
only one effective beep-bearing change.

No clean current route was found with two of these flagged targets present
when Gyro Modifier 2 releases. Steering overrides the driver inputs, and
its normal entry clears the previous modifiers. Cursor Gyro cancellation
also reaches the Gyro-off path with Steering and Fallback Guard absent.
An artificially stale stack could differ; it is not evidence that such a
stack caused the reported sound.

## Complete inventory

Every stored add/remove command was inspected, including inactive groups,
disabled activator banks, and group references. Legacy `hold_layer` commands
were also counted. JSON and VDF command inventories were compared.

| Per layout | Default | Alternative |
|---|---:|---:|
| Add commands | 398 | 398 |
| Remove commands | 4,275 | 4,345 |
| Hold commands | 4 | 4 |
| Commands requesting a beep | 38 | 38 |
| Activator entries containing those requests | 30 | 30 |

All layer commands are in normal activator banks of active groups. The five
inactive-only groups in each layout contain none; there are no layer commands
in disabled banks or unreferenced groups.

| Beep-bearing binding family, per layout | Entries | Beep requests in the saved commands |
|---|---:|---:|
| Ordinary Modifier 2 releases: add Gyro | 4 | 4 |
| Gyro Modifier 2 releases: clear to Base | 4 | **12** |
| Transition menu releases | 6 | 6 |
| Steering full up/down exits | 2 | 2 |
| Cursor Gyro two-stick exits | 2 | 2 |
| Menu Keys entries | 2 | 2 |
| Menu Keys button and two-stick exits | 10 | 10 |
| **Total** | **30** | **38** |

Only the four Gyro Modifier 2 Release entries contain multiple beep flags.
Cursor Gyro entry silently adds Gyro and then beeps on adding Cursor Gyro.
Menu Keys entry silently removes Gyro and then beeps on adding Menu Keys.
Those are coherent single-feedback transitions.

All **16 Fn adds per layout are silent**, as intended since 90.41. Ordinary
driver/modifier additions, repeated helper cleanups, touch helpers, turn-assist
layer changes, and all four `hold_layer` commands are also silent.

Steering's repeating full-up/down clear requests one beep on removing Steering.
In the clean modeled traces, holding either direction for 500 ms produces
one request: the first clear removes the layer that owns the repeating action.
This does not rule out another beep if another interaction re-enters Steering.

## Other findings

**Steering's two Modifier 2 full-clear Release entries have no beep at all.**
They remove Steering, Gyro, and their helpers silently. This behavior dates
to the [original Steering builder](../2026-09-30-steering-lean/build_candidate.py)
and is inconsistent with the current R161 expectation that a stateful layer's
own exit beeps. No explicit exception documenting intentional silence was found.
This is separate from the deferred release-order correction.

**Some written Fn guidance is stale.** The feedback table in
[Steam Input JSON Structure](../../resources/Steam%20Input%20JSON%20Structure.md)
and the Fn-based probes under A49, A50, and A52 in
[Steam Behaviour Assumptions](../../resources/Steam%20Behaviour%20Assumptions.md)
still expect Fn beeps. The current policy beside R161 in
[Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md)
correctly records Fn silence. These documents were not edited by this audit.

## Proposed scope for a later correction

1. In the four **Gyro Modifier 2 Release entries**, keep the beep on removing
   Gyro and silence the Steering/Fallback Guard cleanup removals. Preserve
   every removal and its execution order.
2. Treat **Steering Modifier 2 exit feedback** separately: if bringing it into
   line with R161, beep only on the actual Steering removal in each of its two
   full-clear entries. This does not require changing the gesture's release
   conditions or implementing the deferred symmetry fix.
3. Keep Fn, temporary layers, and ordinary cleanup commands silent. Correct
   the stale Fn documentation when the feedback change is implemented.
4. Check one audible beep per successful toggle on the Deck, in both driver
   press/release orders, from Base, Gyro, and Cursor Gyro. Check Steering's
   exit separately. The device check distinguishes native no-op suppression
   from repeated activations or audio behavior the model cannot reproduce.

This proposal changes beep flags only, needs **no new layers**, and leaves
haptics outside its scope. It has not been applied.

## Evidence and reproduction

- [Static audit script](static_audit.py) and [full static inventory](static_inventory.json)
  retain every beep entry's exact source path, flags, and command execution
  order, as well as the silent Steering exits.
- [Runtime probe](probe.py) and [results](results.json): **264 cases**, exercising
  **all 30 beep-enabled entries in each variant**. Ordinary quick toggles,
  longer holds, stick/pad touches, menu transitions, stateful exits, and turn
  assist were covered. Every exact per-command request count matched the
  simulator log; no target-name bookkeeping collision inflated these counts.
- [Boundary probe](boundary_probe.py) and [results](boundary-results.json):
  **160 additional toggles** across release gaps of 0, 1, 49, 50, and 51 ms,
  both driver press/release orders, both variants, and both A9 held-input
  assumptions. Results remain one request on / three off, all at the first
  release. **40 Gyro → Steering entry cases** holding neither, either, or both
  drivers added no Gyro Modifier 2 layer. Total runtime cases: **464**.
- Both layouts pass preflight and the command-budget audit. The live JSONs
  and VDFs remain byte-identical to the saved 90.42 release manifest.

The probe observes raw command flags before calling the unchanged simulator.
It records whether each target was present and whether the command changed
the modeled stack. It does not model audible mixing/coalescing, native
same-frame release batching, or analog distances. Results describe tested
sequences, not an exhaustive proof of all possible layer stacks.

Run from the repository root:

```sh
python3 findings/2026-10-09-layer-beep-audit/static_audit.py --output findings/2026-10-09-layer-beep-audit/static_inventory.json
python3 findings/2026-10-09-layer-beep-audit/probe.py
python3 findings/2026-10-09-layer-beep-audit/boundary_probe.py
```
