# Interrupted delayed applies: coverage and recommended scope

Date: 2026-09-28. Audited the default and alternative Neptune 90.2 JSON layouts at
`16de85e`. **No layout, VDF, version, or TODO status was changed.** This is a static
audit with proposed follow-up work, not a new Steam/Deck runtime test.

**Both layouts have the same coverage: 19 delayed layer-add paths each, with the
reset present on 7 and absent on 12.** Of those 12, only the RTP touch path has an
explicitly documented author decision to exclude this workaround. The other
omissions are not evidence of intentional exclusion or of a reproduced bug.

My recommendation per layout: keep the existing 7; propose adding it to 4
single-modifier paths and 2 stick-touch entry paths; preserve the RTP exception;
defer the 4 scroll/menu-key paths until a behavior-preserving design fits the
three-command limit; leave the 5 ms gyro handoff unchanged unless it fails.

## What this fix is, and what was audited

The author observed that interrupting a delayed `add_layer` can leave a later
apply unable to fire. The workaround is a **separate Regular Press on the same
input that repeatedly removes only the layer being applied**, with a repeat
interval longer than its apply delay and Interruptable Off. This restarts the
pending apply according to the author's observations. See the
[documented mechanism and RTP exception](../../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies).

For example, Menu Left: Entry Point applies its Fn layer after 300 ms and has
a separate removal every 350 ms. The intended stopping condition is that the
Fn layer replaces that input once applied. The files show that replacement;
they cannot prove the current client's scheduling or cancellation behavior.

This is different from release cleanup, an inverse stick-threshold exit,
unrelated repeating cleanup, or an Always On expiry timer. `interruptable: "0"`
on an apply is also not evidence that it has the separate reset.

Using the [prep](../../.claude/skills/steam-layout-prep/SKILL.md) and
[binding-order](../../.claude/skills/steam-binding-order/SKILL.md) skills, the audit:

- Used the actual `to-titles` converter on temporary copies before inspecting
  bindings. Both title copies restore byte-for-byte to the numeric sources,
  resolving **1,437 references per file**.
- Checked all 53 layers plus Base, active/inactive/unreferenced groups,
  mode-shift reachability, and disabled activator banks. A recursive raw-JSON
  scan accounts for every positive `delay_start`, including checking for any
  outside the extracted activators.
- Found **30 positive Fire Start Delay entries per file**: 19 layer additions,
  7 Always On self-removals, and 4 Always On key/wheel outputs. All 30 belong to
  active groups; none are dormant or mode-shift-only definitions.
- Inspected each delayed add's other entries, chord/threshold settings, target,
  repeat settings, GUI entry count, and the child's replacement of the same input.
- Confirmed both files pass the three-entry budget and layer/preset ordering
  checks. Default has 984 GUI entries across 531 groups; alternative has 1,020
  across 530. No bank exceeds three entries on an input.

The [complete inventory](INVENTORY.md) links every delayed entry and matching
reset to its source line in each layout. [inventory.json](inventory.json)
preserves source hashes, exact settings, bindings in storage order, JSON
pointers, same-input siblings, and child replacements. Source hashes identify
the current description-inclusive files, rather than older audit snapshots.

## Coverage at a glance

Counts below are **per layout**. Default uses L1/R1 modifiers; alternative uses
L2/R2. “Gyro” includes the matching `Gyro | …` parent variants, not another cover.
Times are milliseconds. A missing reset is a structural observation, not a
runtime failure claim.

| Parent → delayed target | Paths | Apply / reset | Present? | Recommendation |
|---|---:|---|---|---|
| Both Modifier 2 orders, regular + Gyro → combined Tap Cover | 4 | 200 / 250 | Yes | Keep |
| Menu Left / Right: Entry Point → own Fn Layer | 2 | 300 / 350 | Yes | Keep |
| Turning Ramp Up 0 → Turning Ramp Up 1 | 1 | 250 / 300 | Yes | Keep |
| Left / right single modifier, regular + Gyro → own Tap Cover | 4 | 300 / absent | No | Propose adding a 350 ms reset first |
| LST / RST: Entry Point → own Tap Cover | 2 | 150 / absent | No | Propose adding a 200 ms reset next, with touch/gyro checks |
| RTP: Entry Point → RTP: Tap Cover | 1 | 150 / absent | Intentionally absent | Preserve the momentum exception |
| Modifier Scroll Down / Up → own Double Tap Cover | 2 | 150 / absent | No; intent undocumented | Defer; already three entries with repeating wheel output |
| Menu Left: Escape / Menu Right: Tab → own Double Tap Cover | 2 | 150 / absent | No; intent undocumented | Defer; already three entries with held-key output |
| Gyro Off Ramp Up → Turning Ramp Up 0 | 1 | 5 / absent | No; intent undocumented | Keep unchanged unless this handoff fails |

## Already applied: keep these seven paths

### Four combined-modifier paths

The default parents are `L1!R1: Modifier 2`, `R1!L1: Modifier 2`, and both
`Gyro | …` versions. Alternative has the corresponding L2/R2 names. Each
applies the combined Tap Cover after 200 ms and removes only that cover on a
250 ms repeating Regular Press. The reset uses `hold_repeats: "1"` and
`interruptable: "0"`, without an explicit start delay or chord requirement.

It is on the **second modifier's input**, alongside the apply chord and release
transition. Each input uses all three entries. This was added to all four
variants by `4c351cd`, before the menu refactor; see the
[port plan](../../plans/2026-09-27-neptune-trigger-rampup-port.md).

### Two menu-entry paths

`Menu Left: Entry Point` / Select (`button_menu`) and
`Menu Right: Entry Point` / Start (`button_escape`) apply their own Fn layer
after 300 ms and remove only that Fn layer every 350 ms. Each also has its
release transition, so the input has three entries.

These are the two resets added by the menu refactor, `a4c2fe5`, explicitly
addressing interrupted menu entry. See
[decision 5](../../plans/2026-09-27-split-menu-entry-point.md#start-delay-reset-decision-5).
The separate Escape/Tab-to-Double-Tap-Cover paths below did **not** receive it.

### Turning Ramp Up 0

The right-stick edge has a 250 ms Soft Press apply of Turning Ramp Up 1 and
a 300 ms repeating Regular Press removal of that same layer. Its third entry
is inverse-threshold cleanup of the ramp stack. That inverse cleanup is not
the delayed-apply reset; the dedicated Regular Press is. Preserve both roles.
This pattern was also part of the [port](../../plans/2026-09-27-neptune-trigger-rampup-port.md).

For all seven paths, the target layer defines the same input/source, providing
the intended override after the apply. Retain current apply settings: the
combined-modifier and menu chords omit `interruptable`, while the ramp apply
sets it to `"0"`. The reset has its own explicit interruption setting.

## Where I recommend extending it

### First: all four single-modifier parents

- Default: `L1: Modifier 0`, `R1: Modifier 1`, `Gyro | L1: Modifier 0`,
  `Gyro | R1: Modifier 1`, on their respective bumper.
- Alternative: the corresponding L2/R2 parents, on the relevant trigger `edge`.

Each has a 300 ms chord applying its own Tap Cover and a release transition,
with **two entries and no ordinary press output** on that input. A dedicated
350 ms reset therefore fits as entry three without sharing the timing of a
key, wheel, or mouse action. The target single cover already replaces the
same input with its release cleanup.

This is the closest missing counterpart to the existing combined-modifier
fix. I recommend adding it as the first extension, then validating interrupted
hold/retry behavior on the Deck. No documented exclusion was found. An apply
with Interruptable Off still does not supply this reset/retry mechanism.

### Next: LST and RST entry parents

`LST: Entry Point` / left-stick touch and `RST: Entry Point` / right-stick
touch each have a 150 ms Tap Cover apply and a release transition. Again,
there are **two entries and no ordinary press output** on that input. A
200 ms repeating removal of only the respective Tap Cover fits as entry three.

I recommend these as the next extension, checking touch/release, double tap,
Temporary Gyro, and holding the stick deflected. The same-input replacement
exists in each cover. There is no documented stick-touch exclusion; the RTP
trackball-momentum exception should not automatically be extended to sticks.
Static similarity alone does not establish that these paths currently fail.

### Conditions for either extension

Put the reset in the **parent that owns the pending apply**, on the same
input. It should remove only that delayed child, without removing the parent
or clearing a stack. Use a separate `Full_Press` with Hold to Repeat On and
Interruptable Off. Keep the existing chord, release behavior, and delay intact.
The suggested 350/200 ms values follow the spacing of existing uses; they are
trial settings, not a universal “delay plus 50” requirement proven by Steam.

Do not put a repeating reset inside the cover. Covers remain lightweight,
inherit their stack's recovery, and retain their local release exits. This
proposal addresses entry/re-entry, not a reason to add broad cleanup or new
stick-edge overrides to them.

Before accepting an implementation, confirm the repeat stops when the child
owns the input and does not leak through protected Always On windows. Existing
blocking and timed-layer entry/exit order must remain intact. Do not solve
entry-budget pressure by sharing settings that need different timing.

## Exclusions and deferred paths

### Confirmed intentional exclusion: RTP touch

`RTP: Entry Point` applies `RTP: Tap Cover` after 150 ms from trackpad touch.
It has room for another entry, but **the author deliberately excluded the
repeating-removal workaround because it interfered with trackball momentum**.
Keep it excluded. The separate right-stick-edge stale-RTP cleanup is not this
touch-path reset, and is not a contradiction. See the
[documented exception](../../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies).

This is the only absent delayed-add reset in these files for which the reviewed
documentation records an explicit author decision. The following choices are
my recommendations, not retrospectively attributed design decisions.

### Defer: modifier Scroll Down / Up

Default L1: Scroll Down / R1: Scroll Up, and alternative L2: Scroll Down /
R2: Scroll Up, already have three entries: repeating wheel output, the
150 ms cover-apply chord, and a release transition.

A fourth reset is prohibited. Putting the removal into the wheel entry's
binding array would fit numerically but couple the reset to wheel timing.
That output has Hold to Repeat enabled and **no explicit `repeat_rate`**;
this audit does not assume the client's default. A cadence shorter than the
apply delay could repeatedly restart it; setting that entry to 200 ms could
change scrolling speed. Array execution order cannot give subcommands
independent repeat intervals.

Exclude a mechanical retrofit for now. If interrupted re-entry is reproduced,
design and test a solution that preserves wheel rate, initial output, release,
and three entries. Preserve the lightweight Double Tap Cover itself.

### Defer: Menu Left: Escape / Menu Right: Tab

These also already use three entries: Regular Press Escape/Tab, a 150 ms
Double Tap Cover apply, and a release transition. The key entry does **not**
enable Hold to Repeat. Adding removal as a subcommand without changing its
settings would not reproduce the periodic reset; enabling repeat would change
the entry's key behavior and needs its own validation. Do not assume a held
key and a repeating key activator behave identically.

Exclude a mechanical retrofit until a failure justifies a design preserving
key-down/up behavior, any game/OS key repeat, release, and the three-entry cap.
This is separate from the already-fixed Menu Entry → Fn path. The author's
intentional menu gyro suppression and edge blocking remain valid, but they
do not establish an intentional exception to this delayed-apply fix.

### Leave unchanged pending evidence: Gyro Off Ramp Up

Its right-stick Soft Press applies Turning Ramp Up 0 after **5 ms**, with
Interruptable Off. The other entry repeatedly removes Gyro Off Ramp Up below
the inverse threshold; it does not target the pending child and is not the
same reset pattern. A third entry would fit, but this is a short analog
threshold handoff with its own exit, rather than a long held-cover delay.

I recommend leaving it unchanged unless this specific handoff stalls after an
interruption. Five milliseconds does not prove immunity, and the JSON does
not document a deliberate omission. Avoid introducing a new rapid layer-removal
loop merely for uniformity; if a failure appears, evaluate it separately from
the existing 250/300 ms Turning Ramp Up 0 → 1 stage.

### Outside the fix's scope: Always On and intrinsic activator timers

Per layout, seven Double Tap windows have delayed self-removal: LST/RST at
200 ms; left/right modifier, RTP, and Menu Left/Right at 150 ms. Four of those
windows also emit wheel or Escape/Tab output after 50 ms. These **eleven
delayed entries do not apply a layer**, so they are not missing apply resets.

Preserve their isolation: finish other changes before adding the timed layer;
block unrelated mutations while active; remove the timed owner first on an
early exit. Its own timed expiry removes only itself. Do not insert repeating
layer operations into an Always On window. Double Tap **Covers** are separate
layers and do not have these Always On timers.

The inventory also records two active Long Press wheel-output entries and
four dormant Double Press layer-add entries per file. Their
`long_press_time` / `double_tap_time` values are intrinsic activator timing,
not a configured Fire Start Delay. They are not additional unprotected delayed
applies within this workaround's scope. No dormant bindings should be enabled
or changed to increase this fix's coverage. Immediate adds and `hold_layer`
bindings likewise do not call for a blanket reset.

## Proposed TODO split and validation

Keep implementation coverage separate from runtime acceptance:

1. **Implemented:** both Menu Entry → Fn resets; all four combined-modifier
   resets; Turning Ramp Up 0 → 1 reset, in both layouts. The menu refactor
   supplied the two menu resets, not all seven.
2. **Proposed additions:** four single-modifier resets first, then two stick-touch
   resets per layout, using the existing spare third entry.
3. **Explicit exception:** RTP touch stays excluded for momentum.
4. **Deferred:** scroll/menu-key Double Tap Cover applies need a reproduced
   failure and a design preserving their output timing within three entries.
5. **Monitor:** the 5 ms Gyro Off → Turning Ramp Up 0 handoff.
6. **Deck acceptance still needed:** reproduce an interrupted delayed apply,
   keep holding and try a fresh hold, confirm the intended child applies and
   stays applied without repeated removal after input replacement. Also test
   ordinary short tap, long hold/release, second tap, both modifier orders and
   Gyro variants, partial/full trigger pulls on alternative, and stick
   Temporary Gyro interactions. Verify no new layer operations occur while a
   protected Always On window is active. Check wheel/key output and RTP
   momentum remain unchanged.

The two existing broad bug TODOs should not both be marked globally complete
from static coverage alone. Missing reset entries do not prove every absent
path needs one; documented exceptions and deferred designs are valid outcomes.
This audit proposes the split without changing the TODO checkboxes.

## Reproduce the inventory

From the repository root, create temporary readable copies with the prep skill's
converter, then pass their directory to the inventory builder:

```sh
audit_tmp=$(mktemp -d)
python3 convert_runtime_ids.py to-titles neptune/single-set-default_hold-gyro_latest.json --output "$audit_tmp/default.json"
python3 convert_runtime_ids.py to-titles neptune/single-set-alternative_hold-gyro_latest.json --output "$audit_tmp/alternative.json"
python3 findings/2026-09-28-delayed-apply-reset-audit/build_inventory.py --readable-dir "$audit_tmp"
```

The builder checks preflight ordering, round-trip fidelity, the command budget,
and raw delay-key coverage. It regenerates only `INVENTORY.md` and
`inventory.json`; the interpretation in this report is reviewed manually.
