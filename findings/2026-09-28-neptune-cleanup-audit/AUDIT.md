# Neptune 90.2 cleanup audit

Date: 2026-09-28. Both requested layouts were audited without editing either JSON
or VDF. The audited snapshot matches the 90.2 release (`2fee9ee`); the surrounding
documentation includes the subsequent stuck-layer notes (`5e82567`). Source
SHA-256 hashes are recorded in the catalogs and machine-readable summary.
Later documentation work observed description-only edits to both JSON files.
Their binding data still matches this snapshot; the recorded hashes describe
the original audit inputs, before those metadata edits.

**The existing strategy is layered, local recovery, not a global reset.** Normal
release removes the state associated with the gesture; other inputs provide
chord-guarded recovery when the owning button is no longer held. Some exits remove
only the current layer and expose another layer's recovery. Others clear a named
family of layers in one command entry. Timers, pressure/edge thresholds, and
delayed-apply resets are separate mechanisms. These differences often serve a
purpose and should not all become one large removal list.

**The two variants have matching cleanup target structures after mapping the
modifier roles.** Shared review areas include release-only stick-touch families,
unequal stick-edge recovery coverage, and differences between partial and
broader family cleanup. Release-only menu covers/helpers are an intentional
lightweight design, not automatically missing recovery implementations.

This is a static audit. The missing references and configured scopes below are
verified; event propagation after layer removal, Steam-menu recovery, competing
activator timing, and trackball behavior require fresh-load Deck tests.

**Author clarification after this audit:** blocking also protects Fire Start Delay
timers and isolates Always On layers from a historical crash involving other
layer additions/removals. The [blocking audit](../2026-09-28-neptune-blocking-audit/AUDIT.md)
and [documented contract](../../resources/Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround)
qualify all recovery proposals below. Do not replace blocks with broad cleanup
without tracing the protected lifetime. Add an Always On layer last; remove it
first before any other layer changes on exit. All existing Double Tap entry/exit
arrays satisfy that ordering. This requirement is separate from the 30 non-Always-On
mixed touch-release arrays discussed in F6, which were not changed.

**Further author clarification:** the menu helpers/hold keys/covers discussed in
F1/F2 are intended to overlay an existing stack, intercept only their related
button/action, and inherit unrelated behavior. The underlying stack owns its
recovery. A residual lightweight cover requiring another related-button press
is acceptable; do not add independent edge cleanup to every cover. The author
also confirmed that menu interactions do not need simultaneous gameplay: all
six discussed menu layers intentionally disable gyro, and Escape/Tab intentionally
block RS edge. WASD modifiers and ramp-up need not remain available in menu
context. Preserve these overrides and the local cleanup design.

## Complete evidence

- [Default: all 53 layers plus Base](default-layers.md): entry sources, every
  active cleanup pattern, exact input/group locations, settings, sibling chord
  settings, incoming removal counts, and dormant definitions.
- [Alternative: all 53 layers plus Base](alternative-layers.md): the same complete
  catalog using its actual L2/R2 titles and physical inputs.
- [Lifecycle inventory](lifecycle-inventory.csv): **992 command-entry rows**,
  including all **678 cleanup entries** and all remaining add/hold entries.
  Includes JSON pointers, source line numbers, complete binding order, settings,
  group settings, and sibling activators. Filter `removes != []` for cleanups.
- [Summary and reverse indexes](audit-summary.json): exact counts, hashes, and
  each layer's incoming entry/removal IDs.
- [Evidence builder](build_inventory.py): read-only with respect to the layouts;
  regenerates the catalogs, CSV, and summary from verified title-form copies.

An entry is one activator object, not one `remove_layer` string. The same entry
can remove twelve layers and still consume only one GUI command entry. All
enabled and disabled banks, all groups, and conditional mode-shift targets were
scanned. Dormant definitions are not counted as current recovery paths.

| Coverage, per variant | Default | Alternative |
|---|---:|---:|
| Action sets / layers | 1 / 53 | 1 / 53 |
| Groups / input definitions | 531 / 594 | 530 / 630 |
| Groups directly marked active | 319 | 319 |
| Groups without a preset reference | 50 | 50 |
| Conditional mode-shift target groups | 6 | 6 |
| All GUI command entries | 984 | 1,020 |
| Entries containing explicit removal | **339** | **339** |
| Of those, in active / inactive groups | **328 / 11** | **328 / 11** |
| Removal subcommands, all / active groups | 1,208 / 1,191 | 1,208 / 1,191 |
| Cleanup entries in mode-shift-only / unreferenced groups | 0 / 0 | 0 / 0 |
| Disabled entries | 0 | 0 |
| Maximum GUI entries on any input | 3 | 3 |

The six mode-shift targets are groups 1039, 1043, 1290, 1291, 12900, and 12910.
All 53 layers have at least one active explicit removal reference somewhere.
That does **not** establish a usable missed-release recovery path for each one.

## What counts as cleanup here

The primary unit is an activator containing `controller_action remove_layer`.
The audit also traced `add_layer` and `hold_layer` to explain entry and ordinary
lifetime. There are five enabled `hold_layer` entries and one dormant copy in
each file, targeting LTP: Arrow Keys or RTP: Mouse Buttons. Held lifetime is
distinct from an explicit fallback; both trackpad modes also define inverse
pressure cleanup and guarded stick-touch recovery.

The local [binding-order skill](../../.claude/skills/steam-binding-order/SKILL.md)
defines array execution as bottom to top. That rule applies to subcommands in
one entry, not scheduling between activators. The
[layout-prep skill](../../.claude/skills/steam-layout-prep/SKILL.md) requires
readable title copies and correct preset order. Both were followed before
examining targets.

The documentation's [stuck-layer explanation](../../resources/Steam%20Input%20JSON%20Structure.md#stuck-layers-and-why-there-is-so-much-cleanup)
records the author's observation that releases can be missed while the Steam
menu is open. This audit uses that as the failure scenario, not as a newly
reproduced client bug. Valve documents that layers overlay existing bindings
and an already-active layer is not promoted by reapplying it. Consequently,
repeating `add_layer` alone is not a stack reset.
[Valve: Action Set Layers](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers).

Valve also distinguishes release, chord, and regular activators and describes
interruption between activators. The saved sibling chord plus interruptible
Regular Press is evidence of the intended guard; it does not prove all timing
outcomes on a specific client.
[Valve: Activators](https://partner.steamgames.com/doc/features/steam_controller/activators).

## Two independent classifications: trigger and scope

The maintained [cleanup scope examples](../../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples)
now document lightweight inherited recovery, nine-target Mod 2 branch cleanup,
and eight-target released-side cleanup, incorporating the author's clarifications.

For consistency, describe both **when cleanup fires** and **what it clears**.
“Self cleanup” describes scope; “release cleanup” describes a trigger. One
binding can be both. A delayed-apply reset removes another layer but is not
missed-release recovery.

### Triggers already implemented

These categories partition the 328 cleanup entries in active groups in each file.

| Trigger/purpose | Entries | Existing examples and meaning |
|---|---:|---|
| Regular Press beside a chord | 185 | Modifier, Fn, trackpad, scroll, entry, and transition recovery. The held owner normally enables a real output or empty chord; when absent, the Regular Press can clear stale state. Repetition is used selectively. |
| Release | 107 | Remove the released gesture's state; sometimes also open a double-tap window or apply a cover/Fn layer. These are not all pure exits. |
| Inverted threshold | 5 | Ramp stages 0/1, Gyro Off Ramp Up, LTP: Arrow Keys, RTP: Mouse Buttons. Clean up after stick magnitude or pad pressure drops below the configured condition. |
| Delayed-apply reset | 7 | Four regular/gyro Mod 2 variants: remove combined tap cover every 250 ms; Ramp Up 0: remove stage 1 every 300 ms; two menu entry layers: remove their Fn layer every 350 ms. These use `interruptable: "0"` intentionally. |
| Timed self-removal | 7 | All seven Double Tap windows. LST/RST expire after 200 ms; modifier, menu, and RTP windows after 150 ms. |
| Second-press transition | 8 | Consume a Double Tap window and apply its next mode. RTP north and south are separate entries. |
| Tap-window cancellation | 3 | RTP Double Tap east, west, and edge remove the window without applying Circular Scroll. |
| Contextual press | 6 | Four modifier-button exits from ramp stages, plus two firing-button exits from Gyro Off Ramp Up. These intentionally clean up during normal use. |

**The guard rule is specific to stale-state recovery.** It should not forbid
the reset, transition, or deliberate cancellation bindings from firing while
buttons are held. In particular, do not turn the seven uninterruptible reset
entries into interruptible fallbacks just to make settings uniform.

### Removal scopes already implemented

Mechanically, 58 active cleanup entries remove only their owning layer, 211
remove their owner plus other layers, and 59 remove only other layers. The
semantic scopes inside those groups are:

| Scope | Existing implementation | Why it is different |
|---|---|---|
| Self only | Double Tap timer; Enter/Backspace release; Transition Set recovery; firing-button cleanup in Gyro Off Ramp Up | Ends a small state or exposes the layer underneath. The safety of the overall exit depends on what remains. |
| Parent/child pair | Fn + its entry; RTP entry + tap cover; scroll + double-tap cover; stick cover + entry | Clears a small local branch without disturbing unrelated modes. |
| Single-modifier family | Regular modifier + its Gyro variant + its tap cover | Defensive variant cleanup, while leaving persistent Gyro itself intact. |
| Current Mod 2 branch | Current order's regular/Gyro Mod 2 + both single-modifier families + three covers: **9 layers** | Does not remove the opposite-order Mod 2 pair. |
| Whole modifier family | All eight regular/Gyro modifier layers + three tap covers: **11 layers** | Used by uncovered Mod 2 release. The normal variant then enables Gyro; the Gyro variant additionally removes Gyro, for **12 removals**. This is a mode transition. |
| Released-side modifier family | Combined cover release: both Mod 2 orders/variants + released side's single modifier variants/cover + combined cover: **8 layers** | Intentionally preserves the other side's single-modifier family if it is still held. |
| Ramp family | Ramp Up 0 + Ramp Up 1 + Gyro Off Ramp Up | Ends turning assistance and restores the underlying gyro state. |
| Other gesture's family | RST or LST Temporary Gyro + Tap Cover + Entry Point, on stick-touch release in another layer | Cleans a covered input's lifecycle; may also apply the current layer's cover or Fn mode. |
| Reset target only | The pending Fn, combined-cover, or next-ramp layer | Restarts delayed application; intentionally leaves the layer owning the timer active. |

“Whole stack” should therefore mean **a named interaction's stack**, not every
active layer. Neither file has a universal clear-all cleanup. Persistent Gyro
is removed only by the four deliberate Gyro Mod 2 release entries.

## Where the strategy is implemented

Default names are used below. In alternative, substitute L2/R2 for the L1/R1
modifier, scroll, double-tap, and cover names. All other names stay the same.
Counts are cleanup entries owned in active groups, per layer; the linked catalogs
enumerate every exact binding and every external removal source.

| Layers | Entries per layer | Strategy and current coverage |
|---|---:|---|
| Base; Gyro | 0; 0 | Entry/state layers. Base is not removable; persistent Gyro has external deliberate toggle-off paths. |
| Turning Ramp Up 0; Turning Ramp Up 1 | 6; 5 | Inward-edge and modifier-button family exits; stick-touch family cleanup; stage 0 also resets its delayed stage-1 apply. |
| L1: Modifier 0; R1: Modifier 1; both Gyro counterparts | 19 each | Sixteen guarded recovery entries clear the single-modifier family; own release opens Double Tap; two stick releases clear the stick family and apply the modifier cover. |
| L1!R1: Modifier 2; R1!L1: Modifier 2; both Gyro counterparts | 18 each | Thirteen guarded 9-layer branch cleanups; two 11/12-layer mode-changing releases; two stick releases; one combined-cover delay reset. |
| LST: Temporary Gyro; RST: Temporary Gyro | 1 each | Own touch release removes temporary gyro + entry. Many external stick-release lists also remove them; their direct opposite-stick press fallbacks are inactive. |
| Gyro Off Ramp Up | 3 | Firing buttons and inward edge remove only this layer. Ramp layers perform the broader family exit. |
| LTP: Arrow Keys; RTP: Mouse Buttons | 5 each | Pressure exit and two guarded stick touches remove self; two stick releases remove the respective stick families. |
| RTP: Circular Scroll | 5 | Pad release or guarded stick touch removes scroll + mouse-buttons mode; stick releases remove stick families. |
| L1: Scroll Down; R1: Scroll Up | 6 each | Three guarded scroll/cover recoveries; own release removes scroll and opens Double Tap; two stick releases apply Double Tap Cover after accounting for stick state. |
| Escape; Tab; Backspace; Enter (without Menu prefix) | 5 each | LTP release and two guarded stick touches remove self; two stick releases clear stick families. These have more recovery coverage than the Menu-prefixed key layers. |
| Menu Left: Escape; Menu Right: Tab | 3 each | Own release opens a Double Tap window; two stick releases clear stick state and add a cover. **No active non-release removal targets either layer.** |
| Menu Left: Backspace; Menu Right: Enter | 1 each | Only their own menu-button release removes them. No external removal references. |
| Menu Left: Fn Layer; Menu Right: Fn Layer | 22 each | Nineteen guarded family-recovery entries, own menu release, two stick-family releases. Both stick edges have recovery. Enter/Backspace are absent from these lists. |
| LST: Entry Point; RST: Entry Point | 1 each | Own touch release removes entry and opens Double Tap. External removal is also release-only. |
| RTP: Entry Point | 4 | Own release opens Double Tap; guarded RS edge clears RTP entry + cover; two stick releases clear stick state and apply RTP cover. |
| Menu Left: Entry Point; Menu Right: Entry Point | 6 each | RS edge clears Fn + entry; other menu button clears entry; own release opens Double Tap; own held-button press resets Fn delay; two stick releases enter Fn. |
| L1: Double Tap; R1: Double Tap | 4 each | Timer, second press to scroll, and two cross-gesture release exits. |
| LST: Double Tap; RST: Double Tap | 3 each | Timer, second touch to temporary gyro + entry, opposite-stick release cancellation. |
| RTP: Double Tap | 8 | Timer, north/south transition to circular scroll, east/west/edge cancellation, two stick-release exits. |
| Menu Left: Double Tap; Menu Right: Double Tap | 4 each | Timer, second menu press to Escape/Tab hold mode, two stick-release exits. |
| L1: Tap Cover; R1: Tap Cover | 1 each | Own release clears the single-modifier family; inherited modifier fallback also explicitly removes the cover. |
| L1&R1: Tap Cover | 2 | Released-side 8-layer cleanup, preserving the other single-modifier family and persistent Gyro. |
| LST: Tap Cover; RST: Tap Cover | 1 each | Touch release clears cover + entry; external removals also require release. |
| RTP: Tap Cover | 1 | Touch release clears cover + entry; inherited RTP-entry RS-edge fallback also targets it. |
| L1: Double Tap Cover; R1: Double Tap Cover | 1 each | Own release clears scroll + cover; three inherited scroll-layer fallbacks also clear both. |
| Menu Left: Double Tap Cover; Menu Right: Double Tap Cover | 1 each | Own release clears Escape/Tab + cover. **No external removal references.** |
| Transition Set 0; Transition Set 1 | 3 each | Guarded LS touch, RS touch, and RS edge remove self only. Underlying menu family must then recover separately. |

## Findings and consistency decisions

### F1. Enter/Backspace are missing from menu-family recovery

Confirmed in both files. Each has two entry sources (the opposite menu's entry
and Fn layer) but only one removal source: its own release. The Fn/entry cleanup
can remove the lower menu family while leaving the key layer active.

Evidence: default [Backspace](../../neptune/single-set-default_hold-gyro_latest.json#L18421)
and [Enter](../../neptune/single-set-default_hold-gyro_latest.json#L18462);
alternative [Backspace](../../neptune/single-set-alternative_hold-gyro_latest.json#L18693)
and [Enter](../../neptune/single-set-alternative_hold-gyro_latest.json#L18734).

This records the target omission behind the existing todo, not proof that the
helper needs its own cleanup infrastructure. Following the author's lightweight
cover clarification, do not automatically expand recovery merely because the
helper can survive a parent removal. Preserve intentional menu gyro suppression
and verify the existing local exit. If parent cleanup is later deliberately
expanded, the relationship is Menu Left
entry/Fn → Menu Right: Enter, and Menu Right entry/Fn → Menu Left: Backspace.
Add those targets only to recovery conditions that establish the relevant menu
buttons are no longer held. **Do not blindly add them to the Fn owner's release:**
the second menu button may still be held, and dropping its key layer early can
restore the stray Tab/Escape behavior the split was designed to prevent.

The guards themselves need review before widening a list: Fn stick-edge/face
recovery has chords for **both** menu buttons, while each entry layer's RS edge
guards only its **own** menu button. The opposite-menu-button fallback also has
only the owning button's chord. Therefore, appending Enter/Backspace to every
existing menu cleanup is not sufficient to establish safe eligibility. Protect
the helper's still-held button as well, and account for which layer owns the input.

### F2. Four older menu tap/hold layers also use release-only cleanup

`Menu Left: Escape`, `Menu Right: Tab`, and their two Double Tap Covers have no
active non-release removal reference. Escape/Tab can be removed by their own
release or their cover's release; each cover can only remove itself on release.
Their stick-touch releases clean the stick family and **add** the menu cover;
they do not recover the stuck menu key family.

The key layers also place an unconditional empty binding on RS edge. For example,
[default group 1169](../../neptune/single-set-default_hold-gyro_latest.json#L9568)
and [alternative group 1169](../../neptune/single-set-alternative_hold-gyro_latest.json#L10229)
can continue to mask the underlying edge behavior. Adding a lower-layer recovery
alone would not fix that path. The author confirmed this is intentional during
menu use, when gameplay ramp-up is unnecessary. It is not a reason to expand
release-only cleanup or remove the edge block.

The corresponding modifier scroll/Double Tap Cover families have guarded
RS-edge and stick-touch exits, but their broader recovery is not a requirement
for these lightweight menu overlays. Preserve local release cleanup and review
the inherited behavior and existing blockers before proposing any new exits.

### F3. The six stick-touch lifecycle layers depend entirely on releases

LST/RST **Temporary Gyro, Entry Point, and Tap Cover** have many incoming removal
references (33 or 35 each), but every active one is a release activator. A large
reference count therefore overstates their recovery coverage after a missed
release. Touching and releasing again can provide a new exit; merely pressing
an unrelated control does not have an active explicit fallback to clear them.

Opposite-stick touch fallbacks exist in groups **731/732**, but both groups are
inactive. Two other inactive cleanup copies, **12985/13027**, remove RST Temporary
Gyro from Gyro and Gyro Off Ramp Up. These are not current safety nets. See the
dormant appendices in both catalogs.

If these families receive press-based recovery, guard on the original stick's
touch being absent and decide whether to clear all three members. The current
normal releases are deliberately narrower: Temporary Gyro removes itself +
entry; Tap Cover removes itself + entry. Do not add an unconditional removal
while that stick is still intentionally touched.

### F4. Right-stick edge recovery has broader coverage than left-stick recovery

**15 non-ramp layers** define RS-edge cleanup without an LS-edge counterpart:
all eight modifier variants, both modifier scroll layers, RTP Entry Point,
both menu entry layers, and both Transition Sets. Their active LS groups contain
no edge cleanup. Many do have LS touch/click paths, so this is a difference in
which gesture recovers, not total absence of LS recovery.

Both Fn layers already cover both stick edges. The three ramp-related layers
also have RS-only threshold cleanup, but that is expected for right-stick
turning and should not be mechanically mirrored onto movement.

**Author clarification: these are review candidates, not mandatory additions.**
Edge cleanup replaces the inherited LS WASD modifier or RS ramp-up while that
layer owns the edge. Ramp-up is more often blocked because it uses the layer
add/remove API and inherits its timer/ordering constraints. This asymmetry can
be intentional. Add LS or RS edge cleanup only where the recovery need justifies
the displaced action; consider existing inherited/touch/click/button exits first.
Where an addition is warranted, match the appropriate guards and family scope.
See [the maintained design rule](../../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions).

### F5. Mod 2 recovery is branch cleanup, not the full modifier family

The 13 fallback entries in each regular/Gyro Mod 2 variant remove nine layers.
They include the current order's regular/Gyro pair but omit the opposite-order
Mod 2 pair. The release path removes both orders, for eleven modifier/cover
layers, plus an intentional Gyro state change.

The nine-layer list is sufficient for the ordinary current-order branch. Its
targets are the current order's two regular/Gyro layers, four single-modifier
layers, and three tap covers. The omitted pair is exactly:

| Fallback owner, either regular or Gyro variant | Pair not removed |
|---|---|
| L1!R1: Modifier 2 | R1!L1: Modifier 2 and Gyro \| R1!L1: Modifier 2 |
| R1!L1: Modifier 2 | L1!R1: Modifier 2 and Gyro \| L1!R1: Modifier 2 |

Alternative has the same relationship with L2/R2 names. Each of the four Mod 2
variants has one active entry path, from its first-held single modifier when
the other modifier is pressed; that entry adds only its corresponding order.
This supports an intentional current-branch interpretation, although the
original reason for choosing nine targets is not established by static data.
The two sibling chords guard fallback while either modifier is held. Persistent
Gyro is deliberately absent from fallback targets.

**Recommendation after review: retain the nine-layer scope.** Check whether
interrupted transitions can actually leave both orders active before proposing
an eleven-layer fallback. If both coexist, clearing one branch could expose the
other's cleanup and require another gesture; this has not been demonstrated.
Broader removal is a separate behavior change, particularly given timer-reset
side effects. Do not copy the release path's Gyro toggle into recovery.

Conversely, the combined tap cover's eight-layer release list is intentionally
partial: it preserves the still-held opposite modifier. Making that list match
the eleven-layer whole-family scope would discard that intentional survivor.

### F6. Thirty mixed bindings execute their add before their removals

Each file has **30 active touch-release entries** stored as removals followed
by an add. Under the repository's reverse-array rule, the add executes first.
They clear the RST/LST family and apply a cover or Fn layer. All other active
mixed add/remove entries use add-after-removal storage order.

The 30 are: two stick releases in each of eight modifier variants (16), two
modifier scroll layers (4), two menu entry layers (4), RTP Entry Point (2), and
Menu Left: Escape / Menu Right: Tab (4).

This differs from the skill's usual cleanup-then-add guideline, but the
[menu-split plan, decision 3](../../plans/2026-09-27-split-menu-entry-point.md#decisions-settled-2026-09-27)
explicitly preserves the current menu ordering. The added layer is not one of
the removed stick targets. There is no established defect from ordering alone.
Document these as retained behavior; any normalization should be a separate
reviewed behavior change with tests, not an automatic audit fix.

### F7. Transition Sets intentionally rely on cleanup in stages

Their three fallback entries remove **only the Transition Set**. They do not
clear either menu entry/Fn family. Both menu-button releases are empty in these
layers, so a release while the Transition Set owns those inputs is not the
underlying Fn release cleanup.

With no menu held, stick touch/RS edge can remove the Transition Set, exposing
the lower menu family; its next eligible fallback can then clear it. This is
a coherent self-removal strategy, but the audit cannot promise that the same
physical event runs both layers' cleanups. Test the whole recovery sequence,
including whether a second gesture is needed. Do not describe the first removal
as an entire-stack reset.

The RTP Entry Point → modifier → Base recovery is similar: RTP's edge cleanup
removes RTP entry/cover, not the modifier or ramp layers directly. It exposes
lower bindings whose own eligibility still applies.

### F8. A historical copy/paste warning is stale for these files

The binding-order skill originally cited RTP Mouse Buttons removing LTP Arrow
Keys as a current copy/paste example. **The current active inverse-pressure entry removes RTP
Mouse Buttons correctly**, in group 242 in both variants. Its two stick-touch
fallbacks also target itself. Do not report the historical example as a current
layout defect. The follow-up blocking audit corrected that warning in the skill;
its general advice to inspect copied targets remains valid.

### Differences between default and alternative

The cleanup-entry multiset matches after normalizing modifier layer titles,
grouping by owner, active/inactive state, activation type, and ordered removal
and add targets. A second comparison paired **all 328 active entries** by owner,
input role, activation type, and complete ordered binding payload; all matched.
There is no cleanup target drift between variants under those comparisons.
Physical controls still differ, and this is not byte equality:

- Default modifiers use bumpers; alternative uses trigger soft-pull ownership.
  During ramp-up, alternative uses full-pull `click` to exit and keeps the
  existing partial-pull empty override.
- Sixteen cleanup entries differ by an explicit zero haptic setting versus
  omission. This does not change the target list; it is not proof of equal
  feedback defaults on every client.
- The sibling chord that enters the second modifier from the right single
  modifier has Hold to Repeat in default and omits it in alternative, in both
  normal and Gyro variants. The associated fallback's targets/settings agree;
  entry retry behavior is an adjacent difference to test, not a removal defect.

## Consistency proposal

Use one policy for a given **purpose and interaction family**, while retaining
different policies for different jobs:

1. **Normal release:** clear the released gesture's owned state, preserve any
   still-held independent gesture, and explicitly specify any next tap window.
2. **Stale-state recovery:** establish that all relevant owners are absent, clear
   the named transient family including its covers/helpers, and preserve
   persistent modes such as Gyro. Check that a higher layer does not mask the
   recovery input.
3. **Self-removing child:** document which parent remains, its recovery path,
   and whether another gesture may be needed. Do not call this full-stack cleanup.
4. **Delayed-apply reset:** target only the pending child, retain the repeat
   interval and interruption settings, and keep it distinct from recovery.
5. **Cross-gesture release:** list the stick-family removals and any new cover/Fn
   separately; document the 30 retained add-first arrays rather than silently
   claiming every mixed array cleans before applying.
6. **Protected timing state:** preserve blocks that keep unrelated layer changes
   from disturbing a timer. Finish other cleanup before adding an Always On
   layer; remove that layer first before any other layer changes on an exit.
   Its timeout is self-only. A proposed fallback must respect these boundaries.

For each family, keep a small explicit contract: owner condition, ordinary exit,
recovery inputs, exact targets, intentional survivors, covering layers, and
protected timers.
Compare regular/Gyro variants and left/right counterparts against that contract.
Adding a new helper should require checking every recovery list that promises
to clear its family. The three-entry limit still applies to GUI command entries;
additional removal subcommands do not consume another entry.

Following the author's priorities and cover clarification, start with F4's
selective edge-cleanup review and its required blocking protections, then F3's stick-family
recovery. For F1/F2, retain the confirmed menu gyro/edge overrides and lightweight
local exits; runtime exit checks remain separate from the settled design decision.
For F5, retain current-branch scope unless overlapping orders are demonstrated.
Before choosing a repair, trace the timer/blocking
contract; a blank input alone does not justify another removal. Preserve the
RTP delayed-touch exception: its 150 ms
cover apply must not acquire the repeating-removal workaround that the author
found harmful to trackball momentum. Existing stick-edge recovery and other
RTP cleanups serve different purposes.

No layout repairs were made. The initial cleanup audit changed no skills; the
follow-up blocking audit added the isolation contract and corrected the stale
copy/paste warning in the editing guidance.

## Verification and runtime acceptance

Static checks passed for both files: ascending preset keys, matching preset
block order, sequential IDs, unique titles, 1,437 resolved runtime references,
byte-identical title→ID readback, and the full three-command-entry audit.
The inventory's removal counts reconcile with every raw `remove_layer`
occurrence. It also accounts for every add/hold occurrence and checks all
referenced layer targets through the conversion round-trip.
All 992 inventory pointers and their full binding payloads were independently
resolved against the readable source copies. All 185 guarded fallbacks per
variant leave `interruptable` omitted/default; none explicitly disables it.

Useful Deck tests for the future repair, in each variant:

- For every temporary family, miss release via the Steam menu, then try RS edge,
  LS edge, stick touch, click, face button, and the opposite menu input separately.
  Record which action restores ordinary control and which layers remain.
- Repeat while the original owner is still held: guarded recovery must not
  destroy valid output. Distinguish this from intentionally active resets.
- Exercise Enter/Backspace in both press/release orders, including interrupted
  holds; preserving the still-held second button must prevent stray Tab/Escape.
- Test menu Escape/Tab double-tap-and-hold, their covers, and the unconditional
  edge blockers after a missed release.
- Test combined modifiers in both orders, one button remaining held, and Gyro
  both enabled and disabled. Recovery should preserve persistent Gyro; deliberate
  uncovered release should still toggle it.
- Observe Transition Set and RTP-entry cleanup in stages. Do not assume removing
  an overlay replays that same press in the newly exposed layer.
- Interrupt each delayed apply, then retry. Preserve the 200/250, 250/300, and
  300/350 ms apply/reset relationships, and the RTP trackball exception.

To regenerate evidence, first run the skill preflight checks, then create
`default.json` and `alternative.json` with `convert_runtime_ids.py to-titles
--output` in a temporary directory. Pass that directory to:

```bash
python3 findings/2026-09-28-neptune-cleanup-audit/build_inventory.py --readable-dir /path/to/readable-copies
```

The builder verifies those copies against the current numeric layouts before
writing only this audit's generated artifacts. The narrative above is reviewed
analysis, not generated proof of runtime behavior.
