# Lean steering candidates — 16 layers

Updated 2026-09-30 with the user's simplified modifier/ownership rules.
**16 added layers, 71 total, zero new Always On actions.** This saves nine
layers against the previous lean candidate and twenty against the original 36.
Both required Modifier 2 variants use `Steering | …` titles.

- [Default VDF](default-steering-lean.vdf) / [Alternative VDF](alternative-steering-lean.vdf)
- [Default readable JSON](default-steering-lean.readable.json) / [Alternative readable JSON](alternative-steering-lean.readable.json)
- [Hashes and complete layer titles](manifest.json)
- [Default input manifest](default-bindings.json) / [Alternative input manifest](alternative-bindings.json)
- [Device acceptance](ACCEPTANCE.md)

Applied to both working Neptune JSON/VDF pairs on 2026-09-30 at the user’s request.
The original 36-layer candidate exports remain unchanged. Previous Neptune files
are preserved in `pre-steering/neptune/`; see [installation hashes](neptune-installation.json).
These exports replace the earlier 25-layer lean candidates at these paths;
record the new manifest hash when testing. Native acceptance is pending.

## Implemented changes

- No Rearm layer. Dominant release clears the temporary steering family. A
  still-held opposite control acquires its W/S owner through fallback's 50 ms
  repeating acquisition route; if neither is held, ordinary fallback continues.
  Both-held acquisition is blocked until an owner can be selected without the
  opposite held. Takeover clears old modifiers/gesture history and starts with
  the Tap Cover: a stick already held gives no modifier map until it returns to
  center (see [Simplified Tap Cover](#simplified-tap-cover-906)).
- Modifier 2 Up/Down is a direct wheel bind with 50 ms hold repeat. It has no
  tap, double-tap, long-hold or consumed helpers. Its face mappings remain
  independent. After coverage, opposite release retains its owner and exposes
  the Tap Cover underneath, so a held stick does nothing until center.
  A short opposite tap instead clears all layers to Base.
- Modifier 0/1 themselves retain fresh Down/Up gesture state. Their cardinal
  release does not remove the map; true center removes it and opens the matching
  double window. Sideways removes it silently; reversal replaces it with the
  other bank plus the shared consumed cover. Hold or modified action consumes
  scrolling. No separate directional Entry Point layers remain.
- One `Steering | LS: Double Tap Cover` handles both normal repeat directions.
  Direction release, center or sideways removes the cover and consumes further
  scrolling until center. Wheel output has a 5 ms start delay so reversal
  cleanup can cancel the newly entered opposite direction before its tick.
- The existing four protected-menu helpers, disposable initial entry, two
  movement owners, two ordered Modifier 2 maps and fallback feedback remain.

## Exact added layer families

| Family | Count |
|---|---:|
| Steering + LS Entry Point | 2 |
| Right W Key / left S Key owners | 2 |
| LS Down Modifier 0 / LS Up Modifier 1 | 2 |
| Right!Left / Left!Right Modifier 2 | 2 |
| LS Tap Cover | 1 |
| Existing opposite-side single Tap Covers | 0 new |
| LS Up / Down Double Tap | 2 |
| LS Double Tap Cover | 1 |
| Protected Menu Left/Right Entry Points and Tap Covers | 4 |
| **Total** | **16** |

The two steering-only covers were removed in favor of existing opposite-side
single covers. The saving against the 25-layer candidate is nine.
Default uses R1/L1 names; Alternative uses R2/L2. Membership is `Steering`, like
`Gyro`; all children are prefixed `Steering | `.

## Normal gesture timing and native gates

Normal long-hold consumption is 250 ms. A single scroll resolves at the end of
the 150 ms double window, or sooner on a different direction/sideways/normal
mapped action. The window clock is a chorded delay on the widened inverted
stick edge after true-center entry, chorded on either driver; no new Always On
timer is added. See [Chorded delays (90.6)](#chorded-delays-906). A second
same-direction deflection starts the shared repeat cover, with a 5 ms initial
delay and 50 ms repeat. Modifier 2 has immediate ordinary wheel output and
50 ms hold repeat, with no gesture recognition.

Two consolidation assumptions specifically require Deck proof:

1. ~~**Consumed-cover priority/idempotence.**~~ Removed in 90.6. Valve documents
   that re-adding an active layer does not move it to the top, so the old
   cover routing could leave a bank above the cover. The cover no longer adds
   banks; see [Simplified Tap Cover](#simplified-tap-cover-906).
2. **Shared-repeat reversal cancellation.** Removing the cover on old-direction
   release must cancel the new direction's delayed wheel output. The 5 ms delay
   is a guard, not proof of callback ordering/cancellation in Steam.

Other native gates remain: movement handoff, held mapped-output suppression,
added-over-held chorded-delay timing, timer stability, warning/beep delivery,
menu thresholds/Fn cancellation and foreign-window/overlay recovery. No claim
of bug-free runtime behavior or device acceptance is made. Failed gates block
promotion; preserve the original candidate while fixing the failing path.

## Build and local validation

```sh
python3 findings/2026-09-30-steering-lean/build_candidate.py --vdf
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_convert_vdf.mjs tests/test_steering_observer.mjs
```

The generator reuses the baseline source/serialization helpers in
an isolated module per variant, appends fresh IDs, checks the three-entry input
budget, rejects new Always On inputs and verifies runtime-reference roundtrips.
Builders now read the frozen pre-steering input, so regeneration cannot ingest
the installed steering layers. Both VDF exports verify keys, values and order.
The lean suite has 26 tests of
actual bindings and ordered command arrays; those tests do not emulate Steam.

## Touch cleanup follow-up

All 16 new layers now have explicit LS/RST-side thumb-release cleanup. Normal
Modifier 0/1 and protected menu entries first apply their delayed cover, then
remove local stick helpers; completed covers remain cleanup-only. Owner/menu
recovery guards and three-entry budgets are preserved. See the
[per-layer cleanup audit](CLEANUP-AUDIT.md) and the
[repository rule](../../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release).

## Reused single-side Mod 2 tap covers

Fallback warning remains **1 second**, exit **2.5 seconds**. The count returns
to **16 additions / 71 total** by removing the two steering-only tap covers.

| Steering movement owner | Default cover reused | Alternative cover reused |
|---|---|---|
| W Key (right held) | L1: Tap Cover | L2: Tap Cover |
| S Key (left held) | R1: Tap Cover | R2: Tap Cover |

These single-side covers override only the opposite driver. The dominant
Regular W/S and its release cleanup therefore inherit from W Key/S Key unchanged.
The **combined** L1&R1/L2&R2 Tap Cover remains unchanged and is not used here.

The Mod 2 opposite input retains the existing 200 ms delayed cover / 250 ms
reset pattern. A short uncovered **opposite** release clears all layers to Base;
a long hold, mapped action or thumb release applies the corresponding existing
single cover. Dominant release always uses ordinary steering cleanup and permits
held-opposite takeover, even before coverage; this preserves the user's earlier
owner-release rule without overriding the dominant input.

Reuse also needs a change to state placement: Mod 2 entry clears old gesture
history, places the normal consumed cover **below** Mod 2, then applies its map.
Mod 2 overrides that cover's direction handlers while active. Existing single
cover releases now append removal of only the corresponding Steering Modifier 2 layer to their original side-local
cleanup; removing Mod 2 exposes the already-installed consumed state with the
original owner intact. No shared release adds any steering layer, so ordinary
Base/Gyro use cannot create a stray steering cover. Side-specific guarded touch
recovery gets the same additional removals; original touch releases and guards
are preserved. Owner/full steering teardown also clears both reused covers.

Covered opposite release keeps W/S continuously; no fallback reacquisition gap
is introduced. Mode maps and simple repeat scrolling inherit unchanged. Native
checks must confirm buried consumed selectors are cancelled/hidden on Mod 2
entry and restore only after exit, as well as cover timing and held-output
continuity. Source tables and 22 lean tests verify binding structure/order,
not native scheduling. Full validation: **76 Python and 8 Node tests**.

## Interrupted delayed applies

Every new Fire Start Delay layer apply has a scoped repeating removal on the
same owning input: W/S Up/Down selectors use 5/50 ms, protected menu covers
300/350 ms, and Mod 2 covers 200/250 ms. Applying the target overrides the whole
input and stops its parent reset. The LS Tap Cover has no delayed apply and,
since 90.6, no routing at all. No additional layers are needed.

## Chorded delays (90.6)

Long Press is banned repo-wide ([rule](../../resources/Steam%20Input%20JSON%20Structure.md#allowed-activation-types)),
so all six steering timers are now chorded delays: a `chord` with `delay_start`
and a modern mask (`gyro_ratchet_button_mask`, Any). Timings are unchanged.

| Layer / input | Chord condition | Delay | Action | Reset |
|---|---|---|---|---|
| `Steering` / LS up | LS deflection (bit 30) | 1000 ms, repeat 250, haptic 3 | Warning pulse | none (no layer add) |
| `Steering` / LS up | LS deflection | 2500 ms, haptic 3 | Full exit with beep | none |
| `LS Down: Modifier 0` / down, `LS Up: Modifier 1` / up | LS deflection | 250 ms | Add `LS: Tap Cover` | Regular Press removal, repeat 300 |
| `LS Up/Down: Double Tap` / edge | Either driver (Default `12`, Alternative `50331651`) | 150 ms | Wheel tick, remove window | none |

The Mod 0/1 reset follows the interrupted-delay rule (delay + 50 ms). The cover
it applies is added fresh, so it lands on top, overrides the input and hides
the reset. The window clock is chorded on the drivers
because it runs at center, where LS deflection is false.

The builder also deletes the groups it replaces (66 Default / 64 Alternative)
and refuses any Long or Double Press in steering layers. `LS: Entry Point` still
overrides LS up, so W carried through entry starts no clock.

Install with `install_neptune.py` after building. It carries the working
title and description forward, applies the RTP scroll fix and prunes dead
groups (see [dead-group prune](../2026-09-30-dead-group-prune/README.md)), then
exports the VDF and refreshes [installation hashes](neptune-installation.json):

```sh
python3 findings/2026-09-30-steering-lean/build_candidate.py --vdf
python3 findings/2026-09-30-steering-lean/install_neptune.py --version 90.6
```

Deck gates C1–C5 are in [ACCEPTANCE](ACCEPTANCE.md#chorded-delays-906).

## Simplified Tap Cover (90.6)

The first 90.6 build kept the old cover routing: every 50 ms the cover added
the current bank and then re-added itself. Valve documents that applying an
already-active layer has no effect and does not move it to the top
([r1-tap-cover findings](../2026-09-27-r1-tap-cover/FINDINGS.md), [cleanup audit](../2026-09-28-neptune-cleanup-audit/AUDIT.md)).
So whenever the cover was already active (reversing after the tap was used up,
acquiring a driver with the stick held, leaving Mod 2 with the stick held),
the bank landed above the cover, took over center and opened a double-tap
window: a phantom scroll. The test helper had modelled re-add as "move to top"
and hid this.

The author's design, now implemented, for stick up (stick down is the mirror):

1. In `R1: W Key` / `L1: S Key`, stick up applies `LS Up: Modifier 1` (5 ms
   delayed apply with its 50 ms reset).
2. In Modifier 1, holding up runs a chord on LS deflection that applies
   `LS: Tap Cover` after 250 ms, with the repeating Regular Press removal of the
   cover below it (interrupted-delay reset, 300 ms).
3. Released to center before that, Modifier 1's center removes Mod 0/1 and
   applies the `LS Up: Double Tap` window.
4. In the Tap Cover, holding up or down does nothing (empty bindings, which
   also hide the bank's delayed apply and reset). Center overrides the bank's
   center and removes Mod 0, Mod 1, then the Tap Cover, in that order.

The cover never adds a modifier, so it is only ever added fresh, on top of the
bank it covers. Behavior change: after a driver takeover or a Mod 2 exit with
the stick still held, the stick gives no modifier map until it returns to
center and is pushed again. The test helper now follows Valve's rule, and a new
test fails any binding that adds a bank while an active cover could be left
below it.
