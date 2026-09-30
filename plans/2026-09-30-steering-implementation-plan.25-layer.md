# Steering implementation plan — lean revision

Updated 2026-09-30. **Lean candidates generated; native acceptance pending.**
The [implementation handoff](../findings/2026-09-30-steering-lean/README.md) contains
both variants: **25 added definitions, 80 total, no new Always On actions**.
The design target below remains 16; nine explicit state helpers were retained
under the failure branches rather than removing their safety behavior.

The existing [36-layer candidate](../findings/2026-09-29-steering-implementation/README.md)
remains unchanged as the comparison baseline. The user reports that it looked
good when tested on their Deck. That is useful positive feedback; the tested
export, variant, client build and individual edge cases have not been recorded,
so it does not mark every acceptance gate passed. The
[previous plan](2026-09-29-steering-implementation-plan.baseline.md) preserves the
original architecture and audit context.

The [brainstorm and transition matrix](2026-09-29-steering-entry-brainstorm.md)
remain the behavior contract; the [short overview](steering-overview.html) shows
that behavior. This revision replaces the old mandatory owner/context/direction
window allocation. Keep the baseline's behavior while moving cleanup into the
owners, directional state into the banks, and timing onto ordinary inputs.

## Implemented consolidation and deviations

The separate [lean generator and exports](../findings/2026-09-30-steering-lean/README.md)
implement inherited two-entry W/S cleanup, two required ordered Modifier 2
variants, shared gesture state between W/S, ordinary-input windows and four
prefixed menu helpers. Explicit Fn routing is preserved; automatic-Fn copies
are removed. Existing working layouts and the 36-layer comparison are unchanged.

The target's conditional merges retain these nine extra definitions: four
normal/Mod 2 directional Entry Points (true-center history), two extra Mod 2
Double Tap windows (face-action independence), a second directional Double Tap
Cover (repeat reversal), one Mod 2 Tap Cover (consumption isolation), and Rearm.
All children use `Steering | …` names; full titles are in the generated manifest.
The original naming/budget table below is the target, not the actual manifest.

The ordinary 150 ms clock uses a widened inverted stick edge after true-center
entry, preventing the center-to-direction deadzone gap from freezing eligibility.
It uses Long Press; added-over-held start and stability remain native gates.
Single scroll now occurs at 150 ms expiry (or early resolution), instead of the
baseline's 50 ms output/150 ms expiry. This avoids double emission without an
extra “already emitted” state. Same-direction second hold repeats at 50 ms.

68 Python and 8 Node tests pass, including 14 new binding tests; VDF keys,
values/order and runtime references round-trip. These are static results, not
native timer/held-output acceptance. See the
[lean acceptance checklist](../findings/2026-09-30-steering-lean/ACCEPTANCE.md).

## Contract and provisional implementation choices

- Everything remains layers inside the existing Base action set. Steering is
  persistent membership; releasing its driving owner returns to fallback.
- Preserve Right Menu + LS click selection and the baseline's menu-release
  commitment. Consume the menu tap and retire transition click aliases/mode
  shifts without Tab, Q or punctuation leakage or a competing recovery exit.
- Either stick deflected before/during menu entry selects protected entry.
  Transfer restarts Tab/Escape eligibility once; centering does not switch back
  mid-hold. Block automatic Fn routes, including touch/two-menu routes, while
  preserving deliberate stick clicks.
- Initial disposable protection preserves carried WASD without timeout. It ends
  at the first LS center or driving-control press and cannot return this session.
- Right R1 (Default) / R2 (Alternative) owns W; left L1 / L2 owns S. First owner
  wins; the opposite control selects Mod 2, never the opposing movement key.
- Owners contain no modifier map. Centered normal driving uses Base buttons;
  LS Up selects Mod 1, Down selects Mod 0. Mod 2 takes priority. Opposite release
  restores the current direction's bank, with the carried gesture consumed.
- Fresh short direction → center scrolls once; long hold or a normal modified
  action consumes release scroll. Same-direction double/second hold repeats,
  without a final release tick. Normal repeat exposes Base buttons.
- Preserve the proposed independent Mod 2 gesture context: its face actions do
  not consume scrolling; its repeat retains Mod 2. Entry/exit clears outgoing
  tap, double and repeat history. Carried deflection must center before scrolling.
- Dominant release clears the complete temporary steering family, leaving
  Steering fallback and unrelated persistent state. The guard stays retired.
- Preserve proposed rearm/tie rules: a held opposite cannot acquire after owner
  release; both controls must release before reacquisition. An exact simultaneous
  fresh pair acquires neither. Native scheduling must substantiate these rules.
- A changed held mapping releases the old output and waits for a fresh physical
  press before the new output. Unchanged mappings continue. Do not silently
  weaken this target if native handoff cannot provide it.
- Fallback W warns repeatedly at 2.5 seconds and exits Steering at 5 seconds
  with beep/vibration. W release or driving acquisition cancels both. Returning
  to fallback with LS Up starts fresh timing, even with the opposite held.

## Architecture and the layer budget

| Added definitions | Count | Responsibility and reuse |
|---|---:|---|
| Steering + disposable Entry Guard | 2 | Persistent fallback/timer; temporary untimed WASD override |
| W owner + S owner | 2 | Regular W/S, opposite selector, inherited release cleanup |
| Mod 0 + Mod 1 | 2 | Button maps and their own Down/Up gesture lifecycle; other direction inherited |
| Mod 2 owner variants | 2 | Required W-owner and S-owner variants; share output payloads, retain distinct control lifecycles |
| Normal LS Tap Cover | 1 | Consume normal scroll while preserving current bank selection; shared Up/Down |
| Up + Down Double Window | 2 | Remember first direction after true center; ordinary-input timing, shared across owners and compatible contexts |
| LS Double/Repeat Cover | 1 | Shared repeat phase, conditional on preserving original direction and context without another helper |
| Protected Menu Left/Right + silent tap covers | 4 | Deflected entry and fresh silent-cover lifecycle; reuse existing double-tap covers only in their existing role |
| **Target total** | **16** | **12 steering + 4 menu; 71 total on the reviewed 55-layer source** |

This allocation replaces eight Stroke definitions with bank/cover state, eight
owner/context-specific Always On windows with two ordinary windows, four repeat
layers with one proposed shared cover, and two automatic-Fn copies with existing
Fn definitions. It also attempts to absorb consumed/rearm state. Those last
merges are conditional: every required bit of memory must appear in a binding
or a counted layer, not only in the HTML model.

**Keep the smallest demonstrably correct result.** Two Mod 2 variants are required
by the user, one per owner. Share their payloads in the generator, not their
runtime definitions. Do not force the target by dropping center detection,
consumed state, release cleanup or rearm. A justified extra
helper is preferable to a regression in the working candidate.

### Layer titles: match the existing Gyro family

Use `Steering | <control>: <function>` for child layers, matching existing
`Gyro | L1: Modifier 0` titles. Keep the membership layer named `Steering`, just
as the existing membership layer is `Gyro`. Use `Modifier`, `Entry Point`,
`Double Tap`, `Tap Cover` and `Double Tap Cover` in titles rather than the
planning shorthand “bank,” “window,” or “owner.” `LS` here means stick direction,
not `LST` (stick touch).

| Role | Default title | Alternative title |
|---|---|---|
| Membership/fallback | `Steering` | Same |
| Disposable entry | `Steering | LS: Entry Point` | Same |
| W owner | `Steering | R1: W` | `Steering | R2: W` |
| S owner | `Steering | L1: S` | `Steering | L2: S` |
| Down bank | `Steering | LS Down: Modifier 0` | Same |
| Up bank | `Steering | LS Up: Modifier 1` | Same |
| Mod 2, right/W owner then left | `Steering | R1!L1: Modifier 2` | `Steering | R2!L2: Modifier 2` |
| Mod 2, left/S owner then right | `Steering | L1!R1: Modifier 2` | `Steering | L2!R2: Modifier 2` |
| Shared normal consumed cover | `Steering | LS: Tap Cover` | Same |
| Up pending window | `Steering | LS Up: Double Tap` | Same |
| Down pending window | `Steering | LS Down: Double Tap` | Same |
| Shared repeat cover | `Steering | LS: Double Tap Cover` | Same |
| Protected left menu entry | `Steering | Menu Left: Entry Point` | Same |
| Protected right menu entry | `Steering | Menu Right: Entry Point` | Same |
| Silent left menu cover | `Steering | Menu Left: Tap Cover` | Same |
| Silent right menu cover | `Steering | Menu Right: Tap Cover` | Same |

The two ordered `!` titles follow the existing modifier-family convention.
Menu helpers use the Steering namespace but are active before Steering membership;
namespace alone must not determine which layers remain applied at commitment.
The generated cleanup registry must enumerate both Mod 2 variants explicitly.
These are target titles; the current manifest lists additional retained helpers
and two directional Double Tap Covers. Preserve historical baseline export names.

### Ownership and cleanup

Each owner has two entries on its dominant input: **Regular Press W/S** and
**Release Press cleanup**. W/S is held by the regular entry; releasing it ends
that output. The release entry removes all steering banks, covers, windows,
repeat helpers, any entry guard and both owners, leaving Steering applied.
Generate this family from one registry so adding a helper cannot omit cleanup.
Remove upper helpers before the owner in executed order (arrays run bottom to
top); separately verify key release and newly exposed fallback behavior.

Every upper helper must omit the dominant input entirely so both entries inherit.
An empty binding is not a reliable blocker, and a Release-only override hides
the lower Regular Press as well. Shared helpers should omit both driver inputs;
the W/S owner interprets the opposite input and owns its context teardown.
Opposite release clears only modifier/gesture context, keeps its owner, and
restores the current directional bank consumed. Dominant release takes priority
when both controls release/change together; command-array ordering alone does
not establish priority between separate native activators.

This generic teardown is safe only without a live Always On window above it.
Existing menu/RTP/Base windows must use their own self-first exits before any
steering transition. Removing arbitrary windows somewhere inside a blanket
cleanup array does not satisfy the Always On rule.

### Sparse maps and shared covers

Mod 0 overrides Down; Mod 1 overrides Up. Leave the other direction and A/D
inherited where source/mode inheritance actually supports it. Direction changes
clear the previous bank before applying the current one. An outgoing direction's
release must not erase the newly selected opposite bank.

Normal modified actions consume the stroke via the shared Tap Cover. A cover
that overrides Up/Down must reproduce any selector lifecycle it hides; a silent
release alone would hide the lower selector. Keep consumption until recognized
center, including Up → sideways and direct Up → Down. Do not infer center from
a single direction's release.

Mod 2 suppresses normal bank selection but preserves A/D and inherited dominant
cleanup. Its fresh tap/hold/double flow is independent of face actions. A shared
cover must not carry normal-bank add commands into Mod 2. If conditional routing
cannot fit with correct native behavior, allocate a separate consumed helper
and count it. Merely duplicating Mod 2 by owner does not solve gesture history.

### Ordinary windows instead of Always On

Prototype the Up/Down pending windows on the recognized-center input: when added
while centered, an ordinary delayed/Long Press binding emits the pending single
at the chosen deadline and expires the window. Preserve the baseline's deferred
single/double timing initially; inspect actual export settings rather than
retuning interaction during consolidation. Layer-added-over-held delayed behavior
is documented; timer start, cancellation, movement away from center, and native
key/wheel behavior still require a complete-path probe.

A second same-direction fresh deflection enters repeat. A different direction,
sideways movement or normal Base action after a completed first tap resolves
that pending single and ends double eligibility. Context teardown instead
cancels the pending single. Mod 2 face actions leave its window intact. A native
Regular/Long/Double trio already uses all three entries: it cannot accept a
fourth immediate bank selector, and changing layers may reset native history.
The existing native comparison is evidence to test, not an integrated solution.

### State that sharing must actually preserve

| Required distinction | First allocation to try | Failure condition / smallest fallback |
|---|---|---|
| Up/Down before center vs eligible first tap after center | Directional bank + recognized-center transition into directional window | Direction release cannot start a window; retain direction memory or add a minimal phase helper |
| Long/used/carried stroke vs fresh stroke | Shared Tap Cover; context-gated Mod 2 consumption | If reuse restores a normal bank in Mod 2, keep a separate Mod 2 consumed helper |
| Original repeat direction vs current reversed direction | Keep directional window as memory while shared repeat cover changes phase, with its timeout/output disabled | If repeat hides no safe phase distinction, use separate Up/Down repeat helpers; no reversed or late wheel tick |
| Normal repeat Base keys vs Mod 2 repeat Mod 2 keys | Sparse repeat cover inherits underlying context; remove Mod 0/1 on normal repeat | No hard-coded map in shared repeat; no delayed normal-bank resurrection |
| Both released vs opposite still held after owner cleanup | Existing owner/acquisition gates and physical release history | If exposed held input can reacquire, retain one Rearm helper until a native replacement passes |
| Unchanged held mapping vs changed output | Native inheritance/handoff with explicit gates where possible | Add only the required per-input suppression memory if native behavior fails |

These are blocking design checks, not assertions that one cover already solves
all phases. Write the full input tables before accepting any merger.

## Menu entry: four new helpers

Reuse the existing normal entries, Fn layers, transitions and double-tap covers.
Add protected entry and silent ordinary cover per menu side. Existing Menu
Double Tap Covers emit Escape/Tab and are **not silent covers**; reuse them only
for the established double flow, retaining its Always On isolation.

Original protection concerns deflection before/during entry. It does not require
new provenance memory that retrospectively cancels an already-entered automatic
Fn while preserving deliberate Fn. The lean plan therefore makes no new
post-entry cancellation rule: explicit Fn survives later deflection. Prevent
pending automatic application during normal→protected transfer, including
near-deadline, touch-release and two-menu routes.

Do not blanket-retarget Fn references: the baseline generator also redirects
normal-entry deliberate clicks to automatic-Fn copies. Lean wiring must send
explicit clicks directly to the intended existing Fn/transition, and test both
normal and protected paths. This is a targeted correction, not permission to
change the baseline files in this planning revision.

Use existing Base chord/repeat selection, with protected entry stable until menu
release. Align either-stick detection with actual movement/mouse activation;
old high edge thresholds miss partial deflection. Preserve fresh release
eligibility exactly once on transfer, and cancel delayed Fn without poisoning
the next centered menu hold. The baseline's provisional thresholds must be
measured on Deck, not described as physical measurements.

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

## Required input-resolution manifest

For every reachable stack in both variants, list effective source/mode/input,
all activators and their settings, inherited owner, command execution order,
held-input behavior on add/removal, and layer mutations. Count every GUI entry,
including dormant/mode-shift entries; arrays may contain multiple subcommands.

| Input | Proposed budget / required proof |
|---|---|
| Dominant driver in all gesture phases | Regular W/S + Release cleanup = 2; neither hidden by upper helpers |
| Opposite driver | Owner-specific context entry/exit and only justified recovery, at most 3; never opposing movement |
| Fallback LS Up | Regular W + 2.5 s repeating haptic + 5 s exit = 3; retain baseline Long Press approach unless evidence requires change |
| Mod 0 Down / Mod 1 Up | Selector/hold-consume/release lifecycle at most 3; true-center validation is separate, never a fourth direction entry |
| Shared cover Up/Down | Selection and silent lifecycle at most 3; consumed latch survives noncentral release/reversal |
| Pending-window center | Pending output/expiry within 3; added-over-held start and leaving-center resolution traced |
| Pending-window directions | Same/different-direction routing within 3; carried input cannot become a second tap |
| Shared repeat directions | Repeat, stop and required phase routing within 3; original direction remains identifiable |
| Normal bank mapped controls | Output plus consumption/recovery within 3; Base payloads reused without their unrelated lifecycle |
| Mod 2 mapped controls | Output/recovery within 3; no normal tap consumption and no repeat cadence reset |
| Menu inputs/edges/touches | All existing entries count; prove mixed source-mode inheritance instead of assuming it |

Audit LS click/edge/touch, RS click/edge/touch, both menu buttons, D-pad, face
buttons, triggers, bumpers, pads and gyro across all phases. Preserve ordinary
RS/pad/ramp behavior and persistent Gyro; do not disable unrelated controls to
make timer tests pass. Default's L1+R1 pair means owner + Mod 2 while steering,
not the planned global pair-exit chord. Alternative trigger soft/full thresholds
must be handled independently: an All mask combining all four bits is not a
valid generic both-triggers condition.

## Binding work packages

1. **Freeze and identify the comparison.** Record source/candidate manifest
   hashes, client build and variant. Keep current generator/exports intact;
   create a separate lean generator/output directory. Preserve existing semantic
   tests; add checks for zero new Always On actions and inherited owner cleanup.
2. **Owners, membership and guard.** Implement the two-entry owners and generated
   cleanup family, guard retirement and fallback clocks first. Test carried W,
   S acquisition, dominant release with LS Up, opposite held and simultaneous
   presses before removing Rearm. No new ownership while a release gate is closed.
3. **One complete normal Up path.** Fold stroke state into Mod 1; implement shared
   Tap Cover and ordinary Up window, then repeat. Demonstrate true-center
   eligibility, action consumption, sideways movement, reversal and pending
   cancellation with all input budgets. Establish timing without Always On
   before copying the pattern to Down and the other owner.
4. **Mod 2 and sharing.** Build both required owner-specific Mod 2 variants;
   keep W/S movement and dominant cleanup in owners. Test entry/exit in every
   phase, current-direction consumed restoration, face independence and held
   output handoff. Share windows/repeat only after full effective bindings prove
   compatible. Split helpers minimally if the state-allocation table fails.
5. **Four-helper menu integration.** Preserve release commitment and fix explicit
   Fn routing. Exercise both sticks, partial deflection, pending Fn deadlines,
   touch/two-menu paths and existing double flow without overlapping AO windows.
6. **Consolidation and acceptance.** Remove redundant baseline roles one at a
   time in the separate candidate, run the complete matrix against both variants,
   report actual definitions/maximum active stack, and compare against baseline.
   Only promote after evidence; a lower definition count alone proves neither
   correctness nor better Steam Input performance.

## First milestone: native contract probes

Existing [probes](../findings/2026-09-29-steering-native-probes/README.md) and
[observer](../findings/2026-09-29-steering-native-probes/observer.html) remain useful.
The HTML state model demonstrates policy; it cannot prove native scheduling.

| Gate | Required lean comparison |
|---|---|
| S1 — movement | Both owners/variants; acquire over held Up/Down/diagonals; no W+S overlap, stuck output or unintended handoff gap |
| S2 — guard/center | Initial W beyond 5 s protected; center or driver ends guard once; distinguish direction release, sideways and true center |
| S3 — ordinary window | Add over centered input, single expiry, same-direction double, different direction/sideways/action, owner/opposite release; exact wheel counts and no stale timeout |
| S4 — fallback clock | 2.5/5 s under RS/pad/ramp/gyro changes; acquisition cancels; dominant release with LS Up starts fresh even during held-opposite rearm |
| S5 — feedback | Repeated warning stops at W release/acquisition/exit; fresh hold restarts; final beep/vibration once |
| S6 — held mappings | One/two buttons, D-pad/click/menu keys across banks/covers/window/repeat; changed output releases, replacement waits, unchanged output survives |
| S7 — overlap | Both drivers, opposite+direction, owner release+opposite press, face+center, release near timer; record event order uncertainty and reject forbidden transient outputs |
| S8 — menu | Either-stick partial deflection before/during entry, deadline/touch/two-menu races, explicit clicks in both routes, fresh next centered Fn; no tap/click leakage on commit |
| S9 — interruption | Overlay/focus loss and return during guard, every gesture phase and warning; released controls cannot leave stale owner, key, wheel, warning or delayed add |
| S10 — integrated gesture | Shared normal/Mod 2 windows/repeat with actual bank selectors and 3-entry limit; native isolated activator success alone is insufficient |

Replay the full brainstorm matrix. Especially: Up Mod 1 → opposite → Down →
opposite release; opposite re-press without center; dominant release during
pending single/repeat; repeat reversal without center; warning → S → release
with LS Up; release both controls at nearly the same time. Context cancellation
must win over outgoing output; separately ordered arrays do not prove exact
same-sample races. Record near-deadline tests and any limitations honestly.

## Decisions and failure branches

| Failure | Required response |
|---|---|
| Ordinary center clock cannot preserve single/double semantics | Keep the baseline working path while testing a minimal ordinary phase helper; no silent conversion to long-hold repeat |
| No safe ordinary-clock solution | Reconsider a narrowly scoped AO window with full self-first/isolation binding tables; revise layer count rather than reuse generic owner teardown beneath it |
| Shared repeat loses original direction | Use two directional repeat helpers or retain safe directional memory; never emit a reversed tick before cleanup |
| Shared cover loses consumed/context state | Retain the smallest separate consumed helper; prohibit normal bank actions in Mod 2 |
| Held opposite reacquires | Retain Rearm and test all release orders, including dominant repress before opposite release |
| Held mapped output changes incorrectly | Add necessary suppression memory; reduced count cannot override S6 |
| Fallback clock drifts with unrelated layer changes | Preserve baseline while proving timer/isolation alternative; do not disable normal controls or extend the five-second contract |
| Protected-entry timer/Fn cancellation fails | Repair routes and delayed-reset scope; preserve explicit Fn; add state only for the defined entry protection contract |
| Feedback or interruption leaves work active | Block promotion; fix cancellation and repeat complete exit/re-entry sequences |
| Count exceeds 16 | Document exact memory/input constraint and revised count; retain behavior rather than conceal helpers |

## Static checks, native acceptance and delivery

- Resolve by semantic title/source/input; allocate IDs dynamically and retain one
  Base set, sequential appended presets, unique titles and valid mode-shift refs.
- Run existing conversion, layout and steering tests plus meaningful lean
  invariants: three entries/input, no new AO, complete family cleanup, inherited
  dominant entries, no Mod 0/1 selector beneath active Mod 2/repeat, separate
  gesture histories, correct pending/repeat cancellation and preserved source data.
- Emit readable/numeric JSON, VDF, binding-resolution tables and manifest hashes
  for both variants. Round-trip VDF and inspect serialized order, not just counts.
- Compare output traces and native acceptance against the unchanged baseline;
  retain the full behavior matrix rather than trimming tests to the new structure.
- Report device results per build/hash/variant and case. Existing local tests and
  the user's encouraging Deck report are baseline evidence, not lean validation.
- Do not overwrite working layouts, upload, bump release versions or mark the
  todo complete as part of this planning revision. Implementation produces a
  separately reviewable candidate first.
