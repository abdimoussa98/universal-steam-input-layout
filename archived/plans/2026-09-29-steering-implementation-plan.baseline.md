# Steering: concrete implementation plan

Date: 2026-09-29. **Status: full Default/Alternative candidate bindings generated;
static validation passes; native acceptance remains open.** The
[implementation handoff](../../findings/2026-09-29-steering-implementation/README.md)
contains complete candidate exports, source generator, exact layer count and
remaining device limitations. Working Neptune layouts have not been replaced.


This implements the [steering interaction contract](../../plans/2026-09-29-steering-entry-brainstorm.md)
using action layers within Base. The [review record](../../findings/2026-09-29-steering-design-review/AUDIT.md)
lists the documentation inspected, current-layout checks, and findings that
changed this plan. The [HTML](../../plans/steering-overview.html) illustrates intended behavior;
its JavaScript is not an implementation of Steam activators or a proof of their
ordering. A static audit cannot establish absence of runtime bugs.

## Contract and provisional implementation choices

- Keep either-stick-protected menu entry and explicit stick-click transitions.
  Right Menu + LS click selects steering. **Proposed commit:** release Right
  Menu through the existing Transition Set 1, consuming its Tab interaction.
  This chooses the historical commit pattern; it is not already wired in 90.4.
- Steering fallback preserves WASD. An entry guard protects carried LS movement
  until LS centers or a steering control is pressed; it never returns within
  that session. LS-only guard selection remains the recommended interpretation.
- Default R1 owns W and L1 owns S; Alternative R2 owns W and L2 owns S. The
  opposite control selects Mod 2 without reversing movement. Releasing the
  dominant clears driving, banks and gestures to fallback.
- No bank is built into an owner. Normal LS up/down select separate Mod 1/0.
  Mod 2 overrides the direction bank and restores the current direction on exit.
- Normal direction gestures provide tap/hold/double scrolling. Mod 2 has its
  own gesture history and retains Mod 2 keys during repeat. Keep the proposed
  independent Mod 2 face/scroll interaction; do not import Base gyro toggles.
- Fallback W warns at 2.5 seconds and exits at 5 seconds. W release cancels both;
  valid driving acquisition cancels them before taking ownership. Returning
  to fallback with W already held starts a fresh attempt.
- Preserve the recommended consumed-stroke, rearm and held-output policies as
  acceptance targets. Same-sample priority and suppression of changed held
  mappings are **not native capabilities already demonstrated by the simulator**.
  Resolve gates below before promising them in a delivered layout.

## Reviewed baseline and editing boundary

Both working files are **90.4**, one action set and 55 action layers. Default has
549 groups; Alternative has 552. Their order, preset ordering/sequential IDs,
unique titles and three-entry budgets pass. Baseline hashes and test results
are recorded in the review. Recheck them before applying future changes because
the workspace also contains unrelated ongoing work.

The implementation will resolve sources by `(layer title, source, input)`, edit
title-token form, append new definitions, and allocate fresh preset/group IDs.
Current maxima are `Preset_1000155` and group 13071/13072, but **recompute them**
at generation time. Runtime IDs below identify this inspected baseline only.

| Existing binding | Baseline location | Planned use |
|---|---|---|
| Base | runtime 1, switch group 10 | Replace menu selection predicates; preserve other Base controls and established repeats |
| Menu Left / Right Entry | runtime 34/35; default switches 871/13044 | Detect later deflection through stick inputs; owner input already uses all three entries |
| Menu-entry stick groups | default LS 1162/13046; RS 1161/13045 | Protected transfer and removal of automatic Fn routes; preserve intended menu gyro suppression |
| Menu Right Fn | runtime 30; LS 1330, RS 1331, switch 1320 | Preserve explicit LS-click selection; retire click aliases and mode shifts at commitment |
| Transition Set 1 | runtime 56; switch 1247, LS 1260, RS 1261 | Prototype release commitment with exclusive recovery gating; current stick recoveries compete with release, so do not inherit them unchanged |
| Base movement | LS group 12 | Reuse WASD payload/settings and A/D inheritance; do not mistake its edge scaffold for a center detector |
| Base modifier banks | resolve Mod 0/1/2 by title in each variant | Extract output payloads; rebuild ownership gates, consumption and recovery explicitly; exclude Base cursor/gyro/cover lifecycle |
| RTP: Mouse Buttons | group 242, directional Regular Press + 150 ms repeating Long Press | Native gesture comparison only; ordinary long-hold repeat does not match steering hold semantics |
| Base Double Tap | runtime 36/37; switches 893/897 | Reference for add-last/self-first timing, not a layer to enter unchanged |
| Base Scroll / Double Tap Cover | runtime 19/20 and 51/52; default switches 901/905 and 951/955 | Reference wheel/release behavior; LS and steering cleanup require new bindings |

Alternative menu group IDs differ. Never port edits by blindly copying default
group numbers. Default and Alternative share semantic roles through a variant
table, including the swapped firing controls and their ramp-up behavior.

## Architecture and the layer budget

The table below preserves the allocation used to plan implementation. The
[implemented breakdown](../../findings/2026-09-29-steering-implementation/README.md#layer-count-and-reuse)
is now 36 new definitions; do not treat the earlier 19-definition subtotal as
the completed count. The native comparison is generated, but has no device result.
The complete candidate therefore uses the explicit layered path pending comparison.

Reuse **maps and generated binding templates** first. Sharing a template removes
maintenance duplication; it does not reduce the number of Steam layer definitions.

| Family | Initial definitions / allocation rule | Lifetime and responsibility |
|---|---|---|
| Steering | 1 | Stateful membership, ordinary fallback, owned-family recovery |
| Steering: Entry Guard | 1 | Untimed carried WASD; one-time retirement |
| Steering: W / S | 2 | Store dominant identity, own movement and bank transitions |
| Steering: Mod 0 / 1 / 2 | 3 | Shared maps plus LS lifecycle overrides that silence lower selectors; inherit dominant cleanup; Mod 2 face use independent |
| Menu Left/Right: Protected Entry / Silent Cover | 4 | Protected menu lifecycles; no automatic Fn |
| Steering: `{W,S}` / `{Normal,Mod2}` / `{Up,Down}` Double Window | **Conditional reserve of 8 after native gesture probe** | An Always On window must know its actual owner and exact self-removal target |
| Tap-consumed / neutral gate | Explicit candidate families, count after first-direction binding proof | Distinguish fresh, long/used and carried strokes; block cross-context tap history |
| Scroll repeat and release cover | Explicit candidate families, count after first-direction binding proof | Stop on release, prevent final release tick; retain Mod 2 where selected |
| Both-controls rearm | Explicit latch mechanism to prove | Block stale opposite ownership until neither driving control is held |
| Fn entry provenance, if needed | Explicit policy/state decision before menu integration | Existing Fn does not distinguish deliberate click from automatic entry |
| Changed-held-output suppression | Allocate only if native output behavior needs it | Independent rearm for affected physical inputs; no blanket blocker that loses unrelated holds |
| Fallback timing protection | Result of timer gate S4 | Prevent unrelated mutations from starving warning/exit without silently changing required controls |

The first five rows are the earlier **7 steering + 4 menu** subtotal. First test native directional activators (S10). If they cannot preserve the contract, reserving
eight timed windows makes **19 named candidate definitions before the remaining
helpers**; this is neither a complete count nor a lower bound. It is an explicit
fallback allocation, not a commitment to implement eight windows. Count native-gesture consumption/rearm helpers too when comparing alternatives.

**Why timed windows start owner-specific:** with both controls held, a physical
release can mean dominant cleanup or opposite-bank restoration. One generic
window cannot infer which owner is underneath from those held buttons alone.
It also cannot inherit an owner release that changes layers before removing
the active Always On window. Removing all possible windows is not a substitute:
an unrelated removal might execute before removal of the actual active window.
Removing only the window and expecting the lower release event to replay is
unverified. Keep owner-specific windows unless an explicit smaller dispatcher
protocol passes the same tests.

Normal/Mod 2 windows may later merge per owner/direction if every output,
gesture boundary, release and inherited route remains correct. Do not assume
that physical chords encode arbitrary layer-presence predicates. Up/down
windows retain the first tap's direction while LS is centered; merging them
needs a demonstrated replacement for that memory.

Untimed helpers can inherit owner recovery when their overrides do not hide it.
Any helper that overrides both driving controls needs the same ownership review.
Do not multiply every helper across all dimensions by default; construct its
complete input table, then merge only identical lifecycle behavior. Record new
definitions, maximum active stack, and command entries separately.

## First milestone: native contract probes

First run the existing [held-input rule-test](../../findings/2026-09-29-held-input-layer-transitions/AUDIT.md#deck-checks), especially its T4 removal exposure and key-output probes. Record results rather than treating the existence of the harness as evidence. Steering gates use S1–S10 to avoid its T-numbering.

Build a small diagnostic harness before integrating the whole feature. Follow
the existing held-input `rule-test` pattern: human-readable JSON, numeric JSON,
VDF, a build script, and a result sheet identifying Steam/client/controller
version and fresh-load procedure. Keep diagnostics separate from delivery
layouts. Use explicit test bindings, not assumptions carried from the HTML.

| Gate | Concrete probe | Pass condition / consequence |
|---|---|---|
| S1 — movement ownership | Add an ordinary W/S owner over an already-held driving control; compare owner-input output with output attached to the entry input; exercise W→W, W→S, S→W, held diagonals and dominant release | Exactly the intended key remains held, no stuck output or W+S overlap, and fallback resumes correctly. Select the proven output site; reject July's Always On W/S pattern |
| S2 — neutral and fresh input | Enter with LS up/down/sideways; move up→side, up→down, through center, and along diagonals; repeat with radial/selector thresholds near their boundaries | Distinguish loss of W, vertical release and true LS center. Carried stroke never emits a tap. Identify native detector/settings and any displaced LS-edge action |
| S3 — owner-aware timed window | Test one Up window for each W/S owner in normal and Mod 2 contexts. Hold both controls and release each in turn; test window timeout and second stroke | Correct active window removes first in the same entry; dominant clears branch, opposite restores current bank; no dependency on replaying lower release events |
| S4 — fallback clock | Hold fallback W past 5 seconds while independently exercising each legal touch/pad/RS/ramp/menu/gyro route and stale recovery; enter fallback with W already held; interrupt/retry at 2.4/2.5/4.9/5 seconds | Continuous eligible W retains its clock despite unrelated activity. Release/owner acquisition cancels immediately, return starts fresh. If removals reset it, design explicit isolation or a different proven clock before integration |
| S5 — feedback | Use a haptic-only candidate without layer mutation for delayed repeating warning; test release, owner transfer and full exit. Test exit feedback flag separately | Repeated vibration begins at 2.5 seconds and stops on cancellation; exit beep/vibration occurs once. Confirm actual sound/haptic behavior on Deck; do not infer both from a field name |
| S6 — mapped holds | Hold each face/D-pad/click output through bank changes and unchanged Mod 2 gesture helpers; include two mapped controls held simultaneously and trackpad mode shifts | Old changed outputs release; no synthetic replacement/replay; unchanged outputs continue. If independent suppression needs extra memory, enumerate its cost before selecting it |
| S7 — overlapping activators | Exercise simultaneous driving presses, dominant release+fresh opposite press, opposite+LS entry, timer+release and face+context change at boundaries | Require safe key/wheel/mutation traces in either event order, including transient states; use near-boundary device trials as supporting evidence. Array reversal is not evidence for ordering separate activators. A failed exact-tie policy requires a concrete native arbitration mechanism or an explicit behavior decision |
| S8 — menu protection | Enter with either stick already deflected; deflect during normal entry near Fn deadlines; release thumb touch, press the other menu button, hold/click LS through commit | No automatic Fn leak; fresh Tab/Escape eligibility exactly once; explicit click entry survives; no Tab/Q/punctuation or lingering Fn mode shift after commit |
| S9 — interruption/recovery | Open Steam overlay during each phase, release controls there, return; cancel a delayed apply before expiry and retry; add a foreign timed-window attempt | No stuck owner, delayed resurrection or overlapping Always On windows. Every added blocking override must also address already-pending lower activators |
| S10 — native direction gestures | Compare LS Regular/Long/Double Press with layered windows; fresh and carried entry, action consumption, reversal, both context handoffs, repeat release | Short release scrolls once; normal hold/use scrolls zero; second held stroke repeats without final tick; normal repeat exposes Base, Mod 2 repeat retains Mod 2; no history survives context cancellation |

These are **required implementation evidence**, not a request to relax user
requirements. All controller wiring can be drafted and checked statically, but
do not mark a dependent native mechanism complete before its result exists.
No delay/repeat should be removed merely because one happy-path test passes.

## Binding work packages

### P1. Persistent membership, guarded entry and movement

1. Create Steering, Entry Guard, W and S with unique titles and fresh groups;
   append them without reordering existing definitions. Use a temporary explicit
   harness entry while the protected menu path is under construction.
2. Copy Base WASD/A/D outputs with their existing uninterruptible settings.
   Override only the inputs/settings needed for ownership, center sensing and
   timing. Record any displaced LS Walk scaffold or RS ramp action.
3. Implement the S1-selected ordinary W/S output route. Primary release clears
   the complete steering driving/gesture family and exposes fallback. Opposite
   input is exclusively a Mod 2 selector while driving, with no Base scroll or
   gyro side effect. Do not use a persistent Always On owner.
4. Prototype always adding Entry Guard at a fresh steering commit, then retiring it when centered or on driving acquisition. This avoids an unproven conditional release activator. Centered entry may transiently contain the guard, but must not suppress a subsequent fresh exit hold. Implement one-time retirement from S2. A neutral
   condition that is already true on entry must have a proven delayed/repeating
   path where required; an immediate layer command will not fire on a held input.
5. Implement ownership rearm as actual native state. Stale Base repeating entry
   must be blocked during quarantine. Release-only cleanup without a rearm
   mechanism does not satisfy the held-opposite policy.

Candidate input budgets to resolve into actual activator objects:

| Input / context | Entries to account for | Constraint |
|---|---|---|
| Fallback LS up | W output; delayed repeated warning; delayed family exit | 3 already; no fourth reset slot. S4/S5 decide whether this candidate survives |
| Guard LS up | Untimed W output | No inherited warning/exit; center detection is a separate input/source problem |
| Dominant in an untimed owner | Ordinary movement output, release cleanup, any required recovery | At most 3; preserve output continuity selected by S1 |
| Opposite in an untimed owner | Mod 2 entry, release/restoration, any required recovery | At most 3; added-over-held and removal exposure must be explicit |
| Owner LS up/down | One delayed/repeating selector; upper bank replaces the complete direction input | Bank must silence selector, including under Mod 2; no remove/reapply loop |
| Mod 0/1 LS direction | Native Regular/Long/Double candidate, maximum 3; or release + hold-consume + delayed-apply reset candidate, maximum 3 | Separate alternatives, never six entries; consumption/freshness helpers must override the complete input and preserve A/D |
| Normal bank face/D-pad/click | Gated output + consumption hook + recovery, maximum 3 | Specify dominant validity and current stroke; original Base cover is not the hook |
| Mod 2 bank face/D-pad/click | Gated output + recovery if needed, maximum 3 | No normal consumption; either-control-held alone cannot establish dominant validity |
| Owner release inside a timed window | Exact window self-removal followed by semantic cleanup | Window owns this route; do not defer it to inherited release replay |

The table is a command allocation, not fictitious executable Steam syntax.
Every row must become a real input/activator table with conditions, interruption,
delay, repeat, feedback and ordered subcommands before it is counted as wired.

### P2. Shared maps and one complete normal Up gesture

1. Extract Base/Mod 0/1/2 key and mouse payloads into steering-specific groups.
   Preserve output repeats only where the source output already repeats.
   Exclude Base cursor delayed applies, cover mutations, gyro toggles and family
   removals. Rebuild output gates, steering consumption hooks and stale recovery
   as separate budgeted activators. An either-control gate remains true after
   dominant release with opposite held: it is not sufficient owner validity.
   Preserve sparse Base gyro inheritance under the selected context.
2. Implement immediate Mod 1 selection on fresh LS-up. Entering an owner with
   LS already up selects the map with tap consumed. Restore carried direction
   after Mod 2 through a proven held-input route, not a synthetic press assumption.
3. Provide distinct fresh/consumed stroke behavior and a real center gate.
   A modified action consumes a normal stroke; direct reversal without center
   consumes it. Quiet the selector when its intended state is already installed:
   a repeating remove/reapply loop can reset timers and is forbidden under an
   Always On window even when its apparent end state is unchanged.
4. Run S10 first. If native gesture activators meet all acceptance cases with fewer total helpers, use them. Otherwise wire the owner-specific Up Double Window. Its first-tap direction and owner
   must remain known after LS centers. On second Up, remove that exact window
   first, then enter repeat. On timeout, remove only itself.
5. Normal repeat removes Mod 0/1 and exposes Base face buttons; Mod 2 repeat retains Mod 2. Build repeat and release suppression so both an early second release and a
   long second hold have **no extra final release tick**. Existing Base Scroll
   starts with a release-to-Double-Tap path and only later applies a cover; it
   cannot be copied if that creates an unwanted release tick in this contract.
6. Finish all owner/gesture exits and the input-resolution manifest below;
   count actual definitions and command entries. Only then mirror Down with
   Mod 0 and the opposite wheel output.

**Timing must be chosen from the native reference, not copied from the demo.**
Current Base Double Tap emits one scroll at 50 ms and removes itself at 150 ms.
Its repeat cover specifies a 50 ms wheel cadence. The HTML uses an illustrative
150 ms deferred single and 100 ms repeat. Neither file proves first-output,
double-window equality or second-release behavior for LS. Prototype the existing
Base timing first, record total ticks for quick/long second strokes, and select
the final values/first-tap policy explicitly before mirroring. Use a dedicated
tap-consumption delay only if its reset/lifecycle satisfies the three-entry
budget; do not import the 300 ms cursor action itself.

### P3. Mod 2 scrolling and bank handoffs

1. Opposite press tears down normal gesture state before selecting Mod 2.
   If a timed window is active, its own early-exit binding removes itself first.
   A carried or simultaneous LS deflection starts consumed until center.
2. Use the S10-selected gesture mechanism. If windows are necessary, use owner-specific Mod 2 Up/Down windows initially. Their independent
   tap/double history cannot survive a Mod 2 exit and re-entry. Normal and Mod 2
   first taps never combine into one double.
3. Keep Mod 2 applied during its window and repeat. Its face/D-pad/click routes
   are output-only there and leave the scroll clock/history alone. Helper
   transitions must not release or replay an unchanged held Mod 2 output.
4. Opposite release removes the active timed window first, clears that gesture
   family and Mod 2, then exposes/restores the current LS bank as consumed.
   Dominant release removes the window first and clears the entire branch.
   Stale work from either history must not run after the transition.
5. Exercise both ownership orders and the Alternative soft/full trigger stages.
   No inherited Base Mod 2 cover, gyro-toggle release or global L1+R1 cleanup may
   reinterpret steering's owner+opposite pair.

### P4. Protected menu entry and real commitment

1. Resolve Menu Left as `button_menu`, Menu Right as `button_escape`. Base's
   existing self-chords use legacy selector 15/14 respectively. Use verified
   multi-button **Any** semantics for either-stick deflection (candidate mask
   `3221225472`, verified in the installed UI enum); do not OR legacy selector IDs. Selector identity does not establish its threshold.
2. Prototype a two-entry Base selector: **interruptible repeating Regular Press**
   for normal entry, plus an **uninterruptible Any-deflection chord** for protected
   entry. Do not retain the current uninterruptible self-chord unchanged beside
   a new chord: both could apply their entries. Demonstrate interruption priority and
   that the normal repeat cannot reinstate normal entry after protection latches.
3. Detect later deflection on existing normal-entry stick inputs. Their owner
   switch input is already full (release, 300 ms Fn apply, 350 ms Fn reset).
   Preserve its budget rather than append a fourth activator. Align protection
   onset at or below movement onset. Current LS edge radius 21000 engages near
   74% by native-code calculation versus WASD deadzone 13276 (~40%); it cannot
   be reused unchanged. Calibrate both sticks and the chord selector on device.
   Record changes to the same edge's stale-recovery threshold. After transfer,
   check both no late Fn add and a subsequent centered hold getting Fn normally.
4. Add protected entry and silent cover per side. Replace the complete owner,
   stick-touch release and other-menu inputs that otherwise add Fn. Existing
   touch release completes Fn early; replacing only the delayed Fn add leaks.
   Preserve explicit stick-click routes. Repeated deflection must not re-add
   the protected entry or restart its fresh tap window.
5. Route selected steering through Transition Set 1. Implement Right Menu release
   commitment explicitly; current releases there are empty. Clear the originating
   menu/Fn/transition and invalid overlays, stop their click aliases/mode shifts,
   then enter Steering plus Entry Guard with the S2 center-retirement route.
   Transition Set 1 LS/RS touch and edge repeats currently remove the transition
   when the menu guard lifts. Replace those routes with an exclusive commit/
   recovery protocol before wiring release; a short delay does not guarantee
   priority because it may have elapsed while held. If this cannot pass S8,
   prototype click commitment with menu-release suppression instead. Do not
   emit Tab or replay LS click as Base Q. Preserve any independently held menu
   overlay only where its actual interaction remains valid.
6. Recommended re-entry policy: opening a menu from steering performs an ordered
   whole-steering exit before normal/protected menu entry. Remove an active
   window first; consume Tab when subsequently selecting steering. This makes
   reselection a new session rather than re-adding an active Steering or
   restarting its guard over an owner. Implement only after tracing held W and
   other-menu behavior. Probe active non-top `add_layer` separately for all
   remaining repeating selectors; do not rely on it being a no-op.
7. Include automatic Fn from two-menu routes, already-active Fn, simultaneous
   menu buttons, and touch-release-at-transfer in S8. If the existing Fn was
   entered deliberately, preserve that intentional route. Current automatic and
   deliberate entry share the same Fn definition, which records no provenance.
   Distinguishing them requires an explicit marker/helper or a defined commit
   policy; account for that state rather than assume it already exists. Do not
   invent a blanket Fn-removal rule that destroys intended explicit entry.

### P5. Fallback warning, exit and coexistence

1. Implement the S4/S5-selected clock and output path. If the simple three-entry
   LS-up candidate passes, keep it. If inherited removals starve it, list the
   exact offending bindings and choose a proven isolated clock/override design.
   Do not silently disable RS, gyro or trackpad behavior to make the timer pass.
2. Ordinary face input alone is insufficient coverage. Include LS/RS touch
   release, RTP entry/cover/Double Tap, trackpad keys, RS ramp thresholds and
   firing removal, menus, gyro transitions and stale recovery during W.
3. Make each allowed external transition a deliberate continuation, cancellation
   or whole-steering exit. Retire any active timed window first. Preserve
   unrelated persistent Gyro according to the chosen inheritance policy; do
   not copy Base Mod 2's intentional gyro toggle into steering cleanup.
4. Add recovery for missed releases, including Steam-overlay interruption.
   Guarded recovery remains interruptible and repeating with correct owner
   protection. Keep it out of timed windows unless the window self-exits first.

## Required input-resolution manifest

Produce a row for every new/changed layer and each input below, in both variants.
Record the effective source/group, owning binding, intended output, all mutations,
guard, interruption/repeat/delay, exit scope, displaced inherited action, and
pending-activator behavior. A blank input object or inactive group is not a block.

| Stack / phase | Inputs that must be resolved |
|---|---|
| Base → normal/protected Menu → Fn → Transition → Steering | Both menu buttons; switch click aliases; LS/RS click/touch/edge; Fn mode-shift targets; already-held controls |
| Steering / Guard / owner / bank | LS four directions and center sensing; both driving controls and Alternative trigger stages; face/D-pad/clicks; Base repeats exposed by cleanup |
| Always On window above owner/bank | Every source capable of mutation: both owners, both stick edges/touches/clicks, menus, all face/D-pad inputs, trackpad click/touch/release, firing controls, global recovery, source/mode-shift targets |
| Repeat / consumed / rearm helper | Release visibility, inherited owner recovery, map continuity, direction changes, held opposite and fresh-entry suppression |
| Fallback W with timer active | Every permitted touch/pad/ramp/menu/gyro mutation and pending delayed/reset path |
| Stale or foreign-window combinations | Missing releases, RTP Double Tap, existing seven Always On windows, pending lower activators and exposed Base entry repeats |

For each timed window prove: add last; immutable lower stack; output-only keys
where allowed; timeout self-only; exact self-removal first on early exit. Do not
remove absent helpers ahead of the active window. Prevent overlapping Always On
windows at their entry routes; do not try to repair overlap by adding another.

## Static checks, native acceptance and delivery

Extend tests from the current passing baseline instead of weakening them:

- Add `tests/test_neptune_steering.py` for resolved targets, unique definitions,
  all owner-specific transitions, complete family scopes, no W/S Always On,
  modifier payload equivalence, absence of Base gyro/cursor lifecycles, and
  neutral/rearm/helper reachability.
- Extend `test_neptune_recovery.py`'s expected Always On set (currently exactly
  seven) with the new explicit titles. Preserve checks for the original seven;
  add entry/add-last and every actual self-first exit plus effective inherited
  mutation isolation. Counting windows alone is not an isolation test.
- Preserve held-input and cursor tests; add coverage for changed selector and
  overlay exposure. Test delayed resets separately from key/wheel outputs.
- Run `python3 -m unittest discover -s tests -p 'test_*.py'`,
  `node --test tests/test_convert_vdf.mjs`, and both full-layout
  `audit_command_budget.py` checks. Audit dormant/mode-shift groups as well.
- Validate fresh unique IDs, matching preset order, active and mode-shift group
  references, title-token round-trip and no unresolved targets. Diff unaffected
  output maps, gyro/ramp settings and outside-steering menu behavior.
- Run S1–S10 and the brainstorm transition matrix on a **fresh Deck load**, for
  both variants and both owners. Record observed key edges/wheel counts and
  feedback, not only visible layer names. Boundary checks use repeated near-deadline trials; record
  observed timestamps and uncertainty. Exact-sample claims require controlled
  input scheduling and evidence of the native sampling path, not hand timing
  or the simulator clock. Classify every failure and re-run affected scenarios after fixes.

Only after the relevant checks pass, refresh the actual delivered description,
bump the release suffix once from the then-current published baseline, regenerate
both sibling VDFs, verify JSON/VDF equivalence, and save matching JSON/VDF
snapshots under `versions/neptune/<version>/`. Recheck the current title instead
of assuming a fixed next version. Keep pending native checks explicit in any
prototype handoff; local export/snapshot does not authorize commit or upload.

## Decisions and failure branches

These defaults allow the isolated prototype to proceed; they are not additional
user-confirmed requirements. Do not relax the stated contract to make a gate pass.

| Decision | Prototype choice / blocked integration |
|---|---|
| Commit | Try release commitment with exclusive recovery gating; click commitment plus held-menu suppression is the alternative if S8 fails |
| Guard | Always add on fresh session; S2 center retirement makes protection effective only for carried LS movement; no re-add within a session |
| Map architecture | Banks may override LS gesture inputs to silence selectors. Keep dominant identity/movement/cleanup in owners. No built-in bank |
| LS scaffold | Prototype center sensing on inverted LS edge with explicit settings; retain A/D. Document displaced Walk behavior; do not silently remove it from delivery |
| RS | Preserve existing modifier-held suppression of Base ramp entry for the prototype. Test already-active ramp layers separately; this does not mean all ramp behavior stops |
| Re-entry | Recommended menu opening exits steering before menu entry; validate output continuity and timed-window exit in S8 before integration |
| Gesture semantics | Keep independent Mod 2 face use, carried-stroke consumption, both-controls rearm and changed-held-output policy from the brainstorm as prototype targets |
| First tap | Start with existing native reference timing; record tick traces for single/double strokes before freezing delivery timing |

| Failed gate | Required next implementation step |
|---|---|
| S1 movement continuity | Compare entry-input and owner-input output sites in isolation. If neither works, stop movement integration and present measured alternatives; a W gap is a behavior change, not a default fallback |
| S2 neutral | Calibrate inverted edge including hysteresis and already-centered entry. If it cannot distinguish required states, prototype explicit neutral memory and count it; preserve displaced scaffold through a compatible route or document the decision |
| S3 window isolation | Identify the inherited or pending mutation, replace that exact input, and repeat both owner-release paths. If isolation cannot fit, try S10's native mechanism or an explicit dispatcher. Fewer windows alone do not fix isolation |
| S4 clock | Enumerate resetting removals, then prototype scoped isolation or a separate ordinary-input clock. A new layer is not proof of independence. An Always On timer may only self-remove on timeout, so cannot directly perform whole-family exit |
| S5 feedback | Isolate supported haptic/repeat fields and output site; retain the 2.5/5-second contract. Record unavailable feedback as a blocker rather than substituting silently |
| S6 mapped holds | Enumerate affected input memories and measure helper cost; prototype independent rearm. Do not accept synthetic remapping or blanket loss of unrelated holds |
| S7 ordering | Redesign with mutually exclusive state/gates and compare every intermediate output/mutation trace. If the requested tie policy is not expressible, record the exact conflicting traces and behavior decision before integration |
| S8 entry | Resolve recovery exclusion, threshold alignment, pending Fn and re-entry separately. Compare click commitment only with held-menu suppression and no leaked Tab/Q |
| S9 interruption | Add scoped recovery without breaking active-window isolation, including pending lower activators; re-run the failing interruption and normal route |
| S10 native gestures | Reject any candidate that leaks taps/history, repeats on an ordinary hold, or loses Mod 2 keys. Use explicit layered gestures and count all helpers; no automatic eight-window allocation |

## First actionable implementation slice

**Implemented:** the [first probes](../../findings/2026-09-29-steering-native-probes/README.md),
[native gesture comparison](../../findings/2026-09-29-steering-native-probes/native-gestures.vdf),
and [complete candidate layouts](../../findings/2026-09-29-steering-implementation/README.md)
are generated. The candidate has 30 steering and 6 menu definitions (36 added,
91 total), with shared maps/consumption/repeats and no separate Mod2 routing
layers. The following sequence remains the device-validation order, rather than
an indication that all these files still need to be built. Candidate haptic
bindings are wired; actual feedback and native output suppression are unverified.


Create `findings/2026-09-29-steering-native-probes/` with a generator,
`observer.html`, `RESULTS.md`, and generated title-token JSON, numeric JSON and
VDF per probe. Use separate selectable diagnostic layouts rather than layering
unrelated tests together. Reuse the existing rule-test's title resolution and
conversion tooling; never modify its established controls to fit this harness.

Build in this order:

1. **Existing rule-test:** run its documented controls on Deck. Record T4
   layer-command exposure plus key-output add/removal results. These feed S1/S6;
   they do not establish every steering transition.
2. **Movement/neutral probe (S1/S2):** Base, Steering, Guard, W, S and an explicit
   rearm candidate. Right Menu selects fresh Steering+Guard for this diagnostic;
   Left Menu resets through a defined family cleanup. LS retains WASD in
   fallback/Guard, R1 owns W and L1 owns S (variant swaps to R2/L2). D-pad Right
   emits a unique per-layer F-key marker without mutation. Exercise both held
   entry and fresh presses, neutral, diagonals and dominant release with opposite
   held. Do not add scrolling or exit timers yet.
3. **Native gesture comparison (S10):** retain the proven ownership path; add
   Mod 1 and Mod 2, initially Up only. Compare native Regular/Long/Double
   activators with explicit consumed/neutral helpers. A sends H in Mod 1,
   M in Mod 2 and the Base payload when unmodified. Log first/second stroke
   wheel ticks, normal action consumption, normal repeat exposing Base, Mod 2
   repeat preserving M, and history cancellation on opposite press/release.
4. **Window alternative (S3), only if needed:** build W/S × normal/Mod 2 Up
   windows with self-first exits. Block every inherited mutation, including
   reset: Left Menu removes the actual window first, then its family. Add Down
   only after Up passes. Count this route against the native candidate including
   consumption, repeat, rearm and output-suppression helpers.
5. **Clock/feedback probe (S4/S5):** separate fallback layout with W output,
   warning and exit candidates. Test plain holds, release/retry, driving
   acquisition, and owner release with LS still up. Then copy the actual
   permitted touch/ramp/menu/pad mutation routes one at a time to identify
   resets. The initial isolated timer passing does not pass coexistence.
6. **Entry/overlap integration (S7/S8/S9):** add protected menu and commit only
   after the above tables exist. Probe transition recovery, pending Fn then
   next press, partial deflection, both menus, menu-from-steering, active non-top
   layer re-add, Steam-overlay missed releases and foreign timed-window entry.

The observer records monotonic timestamps, keydown/keyup with repeat flags,
currently held keys, wheel delta/count, blur/focus and a downloadable JSON trace.
Keep it focused and prevent browser navigation/scroll shortcuts where possible.
It measures application-delivered events, not internal Steam activator order or
controller samples. F-key markers identify the effective binding at the instant
queried; they do not reconstruct the full stack. Record sound/vibration manually
with the event trace reference. Lost focus invalidates continuity conclusions.

Each result row contains: probe/build hash; Steam/OS/controller version; variant;
fresh-load steps; initial stack and held controls; ordered input sequence;
expected key/wheel/feedback trace; actual trace file; observations; pass/fail/
unverified; failure branch; next retest. Do not pre-fill results as passing.

For potentially coincident events, enumerate **both callback orders and all
intermediate outputs and mutations**, not only final layers. Include dominant
release/opposite press, opposite/direction, face/context switch, W release/exit,
and window timeout/second stroke. Check no W+S overlap, no stray tick, no stale
reapplication and no foreign mutation while an Always On window is active.
Manual trials bracket deadlines repeatedly; they cannot certify exact ties.
Any controlled-input test must document whether it exercises the same Steam
sampling path. Unresolved ordering keeps that integration gate open.

The first handoff is the generated diagnostic layouts, complete binding-budget
and inheritance tables, observer and unfilled device result sheet. It is ready
for device testing, not a production release. After relevant gates pass, mirror
Down, finish P1–P5 in both variants, freeze the measured helper count and perform
the full delivery checks above.
