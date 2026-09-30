# Steering documentation and design review

Date: 2026-09-29. Scope: the repository's findings and documentation, the current
steering proposal, and relevant bindings in both current Neptune layouts.
**Outcome: the proposal needs native proof and additional helper definitions;
it is not a verified executable seven-layer design.** The
[implementation plan](../../plans/2026-09-29-steering-implementation-plan.md)
turns the findings into binding work packages and acceptance gates.

## Coverage and authority

Reviewed the 56 documentation files present at the start of this review:
19,739 lines including generated catalogs, the HTML proposal, historical notes,
scratch notes and both local skill directories. Narrative documents were read;
large generated catalogs were exhaustively parsed and their layer families,
scopes and supporting inventories reviewed. Four scratch files are empty.
The complete file ledger is below. This is not a claim that every byte of every
historical JSON/VDF was dynamically tested.

Supporting structured review covered the 2,004 blocking-activator rows, 1,061
source rows, 992 cleanup-lifecycle rows, 1,224 September command-budget rows,
related audit summaries, current relevant input groups, and the July steering
reference. Generated September inventories describe their recorded revisions;
the later repeat, edge, cursor and held-input fixes supersede parts of them.
`versions/` contains JSON/VDF snapshots, not additional documentation.

Authority for this plan: current user requirements, current documented layout
rules, current working JSON, then historical implementation evidence. The
31.0 layer lookup, old scratch mode shifts and July Split Stick are references,
not current runtime IDs or behavior. “Post-fix” in July means the order repair,
not that steering was completed or validated.

## Current baseline and checks

| Check | Default | Alternative |
|---|---|---|
| Title release suffix | 90.4 | 90.4 |
| Action sets / action layers | 1 / 55 | 1 / 55 |
| Groups / audited inputs | 549 / 661 | 552 / 697 |
| Full command budget | PASS, max 3, zero violations | PASS, max 3, zero violations |
| Layer order, preset order, sequential preset IDs | PASS | PASS |
| Unique titles | PASS | PASS |
| Readable conversion in scratch | 1,813 references converted | 1,813 references converted |

Working JSON SHA-256 at inspection:

- Default: `2489201cdf3e1641fcf2f1fb7ff24ee19e45889b7f38e47b19fa9a3d300fee95`
- Alternative: `087fbbdf230f99139626b65e790b9a3b5021c55bb0122d0cad2fcd5813b2dbe3`

`python3 -m unittest discover -s tests -p 'test_*.py'`: **33 passed**.
`node --test tests/test_convert_vdf.mjs`: **6 passed**. Both read-only
`audit_command_budget.py` runs passed. Preflight and title conversions above
left the working layout JSON/VDFs unchanged.

The prior HTML checks (89 model cases, including ordered and simultaneous input
sequences, plus browser interaction checks) establish consistency of that model.
They do **not** execute Steam's activators, inherited inputs, haptics or Always On
rules. Existing layout tests also do not prove new steering behavior.

## Findings that affect implementation

### R1. A shared timed window can lose dominant-owner identity

In Mod 2 both driving controls are held. The same release is dominant cleanup
in one owner stack and bank restoration in the other. A shared Always On
window must intercept that release so it can remove itself first, but current
held-button conditions alone do not identify the owner underneath. Inheriting
the lower owner release changes other layers too early. Removing just the
window and relying on lower release replay is unverified; listing all possible
window removals can remove an unrelated layer before the actual timed owner.

**Plan change:** initially budget owner-specific timed windows; reserve separate
normal/Mod 2 and up/down definitions until complete input tables justify merges.
Share maps and generation templates immediately. See
[Always On ordering](../../resources/Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround)
and [held-input limits](../2026-09-29-held-input-layer-transitions/AUDIT.md).

### R2. Unrelated removals may starve the five-second fallback timer

The three-entry candidate (W, delayed warning, delayed exit) fits the command
limit, but that does not establish timing correctness. The documented removal
behavior can restart Fire Start Delay. Fallback can inherit touch, trackpad,
ramp, gyro and menu mutations; a face-only timer test misses these routes.

**Plan change:** native timer probe T4 exercises every allowed mutation during
continuous W and the already-held transition back to fallback. If the clock
is disturbed, explicitly isolate it or choose a different proven mechanism.
Do not add repeating removals to generate haptics or silently suppress useful
controls. Sources: [timer blocking](../../resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers),
[Base inherited routes](../2026-09-28-neptune-blocking-audit/AUDIT.md).

### R3. Layer-command observations do not prove key handoffs

Immediate layer commands do not fire merely because their layer appears over
a held input; delayed/repeating commands do. Output-on-add/remove and release
replay remain unverified. This affects W→W continuity, W→S exclusivity, fallback
re-entry, a held Mod 2 face output across helper changes, and changed mappings.

**Plan change:** T1/T6 choose the actual output site and suppression mechanism.
A global input blocker cannot independently rearm several held face/D-pad/click
buttons while preserving unaffected outputs. Count any per-input state it needs.
Source: [held-input rule](../../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes).

### R4. Simulator sample priority is not native activator ordering

Bottom-to-top ordering only orders subcommands in one binding array. It does
not order separate press, release, delayed or Always On activators. Exact timer
ties, simultaneous driving presses, opposite+stick entry, and a face press
coincident with context change remain desired policies.

**Plan change:** test before selecting native arbitration; do not translate
JavaScript epochs or transactions into imaginary Steam state. Source:
[binding execution order](../../resources/Steam%20Input%20JSON%20Structure.md#binding-execution-order).

### R5. Protected menu has several automatic Fn paths

Current Right Entry has a delayed Fn add, early Fn completion on both stick-touch
releases, and an other-menu chord that adds Fn. Its owner input already has
three entries. Deleting only the delayed add leaves automatic Fn reachable.

**Plan change:** replace the complete protected owner/touch/other-menu lifecycles;
detect late deflection on existing stick inputs, not a fourth owner entry.
Latch protection and prevent repeating selectors from reopening normal entry.
The current normal Base self-chord is uninterruptible; keeping it unchanged
beside a new protected chord risks both routes applying. The plan prototypes
an interruptible normal Regular Press against an uninterruptible protected
chord. Existing Fn also records no automatic-versus-deliberate provenance;
any rule depending on that distinction needs explicit state or a commit policy.
Source: [touch-release completion](../../resources/Steam%20Input%20JSON%20Structure.md#complete-delayed-applies-on-stick-touch-release),
current default groups 13044–13046 and left-side counterparts.

### R6. Historical steering commitment is absent in current layouts

Current Transition Set 1 menu releases (group 1247) are empty. July group 356
committed Split Stick on Right Menu release. Current Fn also has independent
switch click aliases/mode shifts as well as source click→Transition bindings.

**Plan change:** wire commitment explicitly, consume its menu tap and retire
Fn mode-shift/click ancestry. Preserve guard selection for carried movement;
test held click so punctuation/Q cannot replace steering movement. Sources:
[July findings](../2026-07-11-layer-order-swap/FINDINGS.md), current groups
1320, 1330, 1247 and mode-shift targets 12900/12910.

### R7. Existing modifiers and scroll helpers contain incompatible lifecycle

Mod 0/1 carry cursor timers, repeating cover hooks and family recovery. Mod 2
uncovered releases toggle Gyro. Base Scroll uses driving controls, releases
through Double Tap, and later adds a Double Tap Cover. That release path may
not satisfy steering's no-extra-final-tick contract for a short second stroke.

**Plan change:** extract output payloads; construct steering lifecycles. Existing
Base windows emit at 50 ms and expire at 150 ms, unlike the demo's deferred
single. Prototype actual wheel counts rather than declare identical semantics.
Sources: [cursor inheritance](../2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md),
[delayed-apply inventory](../2026-09-28-delayed-apply-reset-audit/INVENTORY.md).

### R8. New steering stacks invalidate old inheritance exclusions

RTP Double Tap can coexist above a modifier/cursor and needed explicit mapped
input blocks. Other old windows were excluded based on their then-current
entry paths. Steering adds new routes, selectors and held repeats; old exclusions
must be retraced. Inactive-marked trackpad mode shifts remain a runtime question.

**Plan change:** produce an effective-input manifest for every new layer/window,
including foreign windows, pending activators and stale stacks. Output-only Mod 2
keys may continue during its timed window only after mutators are replaced or
blocked. Source: [window coexistence review](../2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md).

### R9. Center, vertical release and selector deflection differ

LS up→side ends W but must not count as full center for the entry/gesture guard.
The Base edge is the WASD modifier scaffold, not a ready-made center detector.
Radial edge, direction deadzone and chord-selector deflection are distinct;
Alternative soft/full trigger transitions also need explicit treatment.

**Plan change:** T2 measures native thresholds/hysteresis and documents displaced
edge behavior. Do not equate old radius values with proven neutral detection.
Source: [threshold review](../2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md#edge-threshold-verification).

### R10. Recovery and delay resets have different owners and scopes

Guarded cleanup is interruptible and repeating; delayed-reset removals are
deliberately uninterruptible. Touch-release completion may intentionally add
before removing stick helpers. RTP touch excludes the periodic reset to preserve
trackball momentum. These are distinct mechanisms, not inconsistent cleanup.

**Plan change:** retain the distinctions; no blanket reset or family-removal
normalization. Every helper needs a named recovery owner, valid survivors and
ordered exits. Sources: [repeat changes](../2026-09-28-repeating-recovery/CHANGES.md),
[cleanup audit](../2026-09-28-neptune-cleanup-audit/AUDIT.md),
[delayed-apply audit](../2026-09-28-delayed-apply-reset-audit/AUDIT.md).

### R11. Test and release workflows must grow with the feature

`test_neptune_recovery.py` currently asserts exactly seven Always On layers.
Adding windows must extend its expected set and all ordering checks, not remove
the assertion or claim the old suite covers new inherited routes. A diagnostic
runtime result must record a fresh Deck load separately from static tests.

Follow current description/version, sibling VDF and per-version snapshot rules
when implementing. Older publication wording and fixed ID mappings are historical.
This planning-only task needs no layout version bump or export.

### R12. One documentation status overstated native validation

The held-input follow-up's completion bullets said the alternative repeat fix
was checked on Deck, while its status table, implementation paragraph and audit
said pending. No confirming result was found.

**Corrected:** the [follow-up](../../plans/2026-09-29-held-input-rule-followups.md)
now states JSON/static validation completed and Deck/output checks pending.
The rest of the historical findings retain their revision context.

## Limits and next implementation slice

These findings are design risks and proof gaps, not claims of reproduced bugs
in the current 90.4 controller files. No steering binding change was made by
this review. The next slice is a small native ownership/neutral/window/clock
harness, followed by one complete owner-aware Up gesture in normal and Mod 2
contexts. The implementation plan names the input tables, ordering constraints,
test extensions and gates before mirroring or full integration.

## Documentation coverage ledger

The ledger describes the initial 56-file scope; this audit and the new
implementation plan are outputs of the review. Existing proposal text was also
read and checked against the current user requirements. Generated inventories
were parsed exhaustively rather than treated as current runtime evidence.

| Document | Initial lines | Review type |
|---|---:|---|
| [.claude/skills/steam-binding-order/SKILL.md](../../.claude/skills/steam-binding-order/SKILL.md) | 70 | Local workflow/instruction reference |
| [.claude/skills/steam-layer-duplicate/SKILL.md](../../.claude/skills/steam-layer-duplicate/SKILL.md) | 86 | Local workflow/instruction reference |
| [.claude/skills/steam-layout-apply/SKILL.md](../../.claude/skills/steam-layout-apply/SKILL.md) | 138 | Local workflow/instruction reference |
| [.claude/skills/steam-layout-prep/SKILL.md](../../.claude/skills/steam-layout-prep/SKILL.md) | 101 | Local workflow/instruction reference |
| [.cursor/skills/README.md](../../.cursor/skills/README.md) | 16 | Local workflow/instruction reference |
| [.cursor/skills/steam-actionset-delete/SKILL.md](../../.cursor/skills/steam-actionset-delete/SKILL.md) | 34 | Local workflow/instruction reference |
| [.cursor/skills/steam-binding-order/SKILL.md](../../.cursor/skills/steam-binding-order/SKILL.md) | 35 | Local workflow/instruction reference |
| [.cursor/skills/steam-layer-duplicate/SKILL.md](../../.cursor/skills/steam-layer-duplicate/SKILL.md) | 35 | Local workflow/instruction reference |
| [.cursor/skills/steam-layout-apply/SKILL.md](../../.cursor/skills/steam-layout-apply/SKILL.md) | 72 | Local workflow/instruction reference |
| [.cursor/skills/steam-layout-prep/SKILL.md](../../.cursor/skills/steam-layout-prep/SKILL.md) | 54 | Local workflow/instruction reference |
| [.cursor/skills/steam-runtimeid-remap/SKILL.md](../../.cursor/skills/steam-runtimeid-remap/SKILL.md) | 38 | Local workflow/instruction reference |
| [README.md](../../README.md) | 294 | Full narrative/reference review |
| [archived/Ramp Up Layers Comparison.md](../../archived/Ramp%20Up%20Layers%20Comparison.md) | 151 | Full narrative/reference review |
| [findings/2026-07-11-layer-order-swap/FINDINGS.md](../../findings/2026-07-11-layer-order-swap/FINDINGS.md) | 175 | Full narrative/reference review |
| [findings/2026-09-27-exploratory-layout-audit/AUDIT.md](../../findings/2026-09-27-exploratory-layout-audit/AUDIT.md) | 268 | Full narrative/reference review |
| [findings/2026-09-27-neptune-command-budget/AUDIT.md](../../findings/2026-09-27-neptune-command-budget/AUDIT.md) | 185 | Full narrative/reference review |
| [findings/2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md](../../findings/2026-09-27-neptune-command-budget/CHORD_SELECTOR_VERIFICATION.md) | 87 | Full narrative/reference review |
| [findings/2026-09-27-neptune-command-budget/IMPLEMENTATION.md](../../findings/2026-09-27-neptune-command-budget/IMPLEMENTATION.md) | 99 | Full narrative/reference review |
| [findings/2026-09-27-r1-tap-cover/FINDINGS.md](../../findings/2026-09-27-r1-tap-cover/FINDINGS.md) | 91 | Full narrative/reference review |
| [findings/2026-09-27-rtp-entry-ramp-up/FINDINGS.md](../../findings/2026-09-27-rtp-entry-ramp-up/FINDINGS.md) | 81 | Full narrative/reference review |
| [findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md](../../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md) | 294 | Full narrative/reference review |
| [findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md](../../findings/2026-09-28-delayed-apply-reset-audit/INVENTORY.md) | 97 | Full narrative/reference review |
| [findings/2026-09-28-left-stick-recovery/CHANGES.md](../../findings/2026-09-28-left-stick-recovery/CHANGES.md) | 158 | Full narrative/reference review |
| [findings/2026-09-28-neptune-blocking-audit/AUDIT.md](../../findings/2026-09-28-neptune-blocking-audit/AUDIT.md) | 308 | Full narrative/reference review |
| [findings/2026-09-28-neptune-blocking-audit/alternative-layers.md](../../findings/2026-09-28-neptune-blocking-audit/alternative-layers.md) | 1958 | Exhaustive generated catalog and supporting inventory review |
| [findings/2026-09-28-neptune-blocking-audit/default-layers.md](../../findings/2026-09-28-neptune-blocking-audit/default-layers.md) | 1922 | Exhaustive generated catalog and supporting inventory review |
| [findings/2026-09-28-neptune-cleanup-audit/AUDIT.md](../../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) | 494 | Full narrative/reference review |
| [findings/2026-09-28-neptune-cleanup-audit/alternative-layers.md](../../findings/2026-09-28-neptune-cleanup-audit/alternative-layers.md) | 2626 | Exhaustive generated catalog and supporting inventory review |
| [findings/2026-09-28-neptune-cleanup-audit/default-layers.md](../../findings/2026-09-28-neptune-cleanup-audit/default-layers.md) | 2626 | Exhaustive generated catalog and supporting inventory review |
| [findings/2026-09-28-repeating-recovery/CHANGES.md](../../findings/2026-09-28-repeating-recovery/CHANGES.md) | 66 | Full narrative/reference review |
| [findings/2026-09-29-held-input-layer-transitions/AUDIT.md](../../findings/2026-09-29-held-input-layer-transitions/AUDIT.md) | 398 | Full narrative/reference review |
| [findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md](../../findings/2026-09-29-temp-cursor-gyro/IMPLEMENTATION.md) | 352 | Full narrative/reference review |
| [findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md](../../findings/2026-09-29-temp-cursor-gyro/SELF-REMOVAL-INHERITANCE.md) | 105 | Full narrative/reference review |
| [id_replacement/README_replace_layer_ids.md](../../id_replacement/README_replace_layer_ids.md) | 125 | Full narrative/reference review |
| [id_replacement/SUMMARY.md](../../id_replacement/SUMMARY.md) | 128 | Full narrative/reference review |
| [manual-testing.md](../../manual-testing.md) | 226 | Full narrative/reference review |
| [plans/2026-09-27-neptune-command-budget.md](../../plans/2026-09-27-neptune-command-budget.md) | 156 | Full narrative/reference review |
| [plans/2026-09-27-neptune-gyro-shifts-navkeys.md](../../plans/2026-09-27-neptune-gyro-shifts-navkeys.md) | 168 | Full narrative/reference review |
| [plans/2026-09-27-neptune-trigger-rampup-port.md](../../plans/2026-09-27-neptune-trigger-rampup-port.md) | 172 | Full narrative/reference review |
| [plans/2026-09-27-split-menu-entry-point.md](../../plans/2026-09-27-split-menu-entry-point.md) | 251 | Full narrative/reference review |
| [plans/2026-09-29-cursor-self-removal.md](../../plans/2026-09-29-cursor-self-removal.md) | 236 | Full narrative/reference review |
| [plans/2026-09-29-held-input-rule-followups.md](../../plans/2026-09-29-held-input-rule-followups.md) | 181 | Full narrative/reference review |
| [plans/2026-09-29-steering-entry-brainstorm.md](../../plans/2026-09-29-steering-entry-brainstorm.md) | 716 | Full narrative/reference review |
| [plans/2026-09-29-temp-cursor-gyro.md](../../plans/2026-09-29-temp-cursor-gyro.md) | 423 | Full narrative/reference review |
| [plans/steering-overview.html](../../plans/steering-overview.html) | 492 | Proposal text and interaction model reviewed |
| [resources/Layer Reverse Lookup.md](../../resources/Layer%20Reverse%20Lookup.md) | 712 | Legacy lookup; full table parsed, not current IDs |
| [resources/Layout Vocabulary.md](../../resources/Layout%20Vocabulary.md) | 72 | Full narrative/reference review |
| [resources/Neptune Chorded Button Ids.md](../../resources/Neptune%20Chorded%20Button%20Ids.md) | 63 | Full narrative/reference review |
| [resources/Steam Input JSON Structure.md](../../resources/Steam%20Input%20JSON%20Structure.md) | 1557 | Full narrative/reference review |
| [resources/scratch paper/LST.md](../../resources/scratch%20paper/LST.md) | 195 | Full narrative/reference review |
| [resources/scratch paper/RST.md](../../resources/scratch%20paper/RST.md) | 195 | Full narrative/reference review |
| [resources/scratch paper/all.md](../../resources/scratch%20paper/all.md) | 0 | Empty file; confirmed |
| [resources/scratch paper/alt.md](../../resources/scratch%20paper/alt.md) | 0 | Empty file; confirmed |
| [resources/scratch paper/base.md](../../resources/scratch%20paper/base.md) | 0 | Empty file; confirmed |
| [resources/scratch paper/gyro.md](../../resources/scratch%20paper/gyro.md) | 0 | Empty file; confirmed |
| [todos.md](../../todos.md) | 157 | Full narrative/reference review |
