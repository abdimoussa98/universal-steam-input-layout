# Plan: intended-flow inheritance checker

Status: built, 2026-10-01 ([record](../findings/2026-10-01-intended-flow-checker/README.md)).
All nine families, both variants, the cover check and the report are done.
Applying the results to cleanup/blocking decisions is the follow-up in §6. It replaces exhaustive runtime reachability as the
prerequisite for routine inheritance and cleanup audits.

## Goal and scope

For each layer, follow its intended layer-addition flows and report:

1. The ordered stacks below it, with the input/transition path producing each.
2. For each relevant button, the nearest inherited binding, its original
   activators/settings, and the layer providing it.
3. Where different flows expose competing non-Base bindings and therefore
   need an explicit clear/block rather than an assumed replacement.

> **Correction, 2026-10-01 (author):** this was a misreading. "More than one inherited keybind
> means block" is not a rule for ordinary layers. It is the last step of the Always On window
> rule: under a layer with an Always On action, if one of the bindings it could inherit is a
> layer command, clear the input when more than one keybind is possible, otherwise override it
> with that keybind. The Window audit checks that. The Flow audit now lists differing inherited
> bindings as information ("varies") and no longer fails on them.

Global above-layer analysis is deferred. Lightweight covers get a separate,
focused check after the lower-stack checker works. This is a read-only audit;
layout edits and a cleanup-list writer are later work.

No numeric clock simulation, solver dependency, exhaustive input interleavings,
or saved search database is required. A delayed add is the successful hold
branch; an early release is the alternate branch. Resets remain recorded in
binding evidence but are not expanded into timer histories. The report describes
intended flows, not all physically reachable stacks.

## 1. Extract and describe intended transitions

Add `steam_layout/flow_model.py` using `Layout`, `entries`, and `layer_ops` from
`steam_layout/model.py`. Preserve actual command execution order and original
JSON evidence. Each transition records its owner, source, input, activator,
entry identity, relevant conditions, and ordered adds/removals.

Recognize normal entry, successful hold, normal release, second press, and
window expiry. Keep guard/chord alternatives distinct. Recoveries, reset-only
removals and repeated retries are not independent normal entry routes. A
normal release that adds a Double Tap window is a real route and must be kept.
A transition containing removal plus addition applies both in execution order.

Derive transitions from the layout rather than hand-writing every path. Use a
small, versioned flow configuration only where intent cannot be inferred from
bindings: family entry points, branch constraints, and deliberate exclusions.
Seed it from the existing documented interaction recipes. Every excluded or
unclassified layer-changing entry must be listed with its reason; never silently
drop it or pretend an arbitrary add graph establishes intended behavior.

Keep the existing user scope: explicit adds/removals only, no action-set
switching, and list legacy hold commands as ignored. Do not migrate them here.

First deliverable: a readable transition inventory for normal modifiers and
one menu family, checked against their documented behavior, before traversal
is generalized to both complete layouts.

## 2. Traverse the logical flows

Add `steam_layout/flow_paths.py`. Start from Base and follow classified intended
transitions. Resolve the effective input in the current ordered stack before
using a transition; an overridden lower binding must not fire. Preserve branch
conditions and owner context so unrelated family branches are not freely mixed.
Include documented persistent-mode contexts and both supported modifier orders.

Reuse ordered operation application where suitable: adding an active layer
leaves its position unchanged; removing then adding moves it to the top.
Record the lower stack whenever the target layer is present, including when a
normal transition changes its lower stack. Keep existing upper layers for
binding lookup without producing a global above-layer catalogue.

Deduplicate equal ordered stacks with equal relevant flow context. Terminate
repeat/cycle edges when they return to an already visited context; keep an
explanatory route reference. Do not enumerate repeated input histories or use
an arbitrary depth cap as a successful completion criterion. If a resource
limit is reached, explicitly report that the declared flows were not covered.

## 3. Resolve inheritance and recommend clear/block

Add `steam_layout/flow_inheritance.py`. Reuse and adapt the static helpers in
`steam_layout/inheritance.py` and `steam_layout/stacks.py`, not `StackSpace`'s
chord-blind, depth-limited search.

For each target/input and each lower stack:

- Walk from the nearest lower layer down to Base; distinguish inherited
  binding, explicit empty block, disabled source, and no binding.
- Retain complete original activators, settings and binding command order.
  Compare normalized definitions, not merely source-layer names.
- Show Base fallback separately. Multiple distinct non-Base inherited bindings
  trigger a clear/block recommendation under the author's policy.
- Also show what the target itself does: inherits, clears, replaces, or disables
  the source. A clear already present is satisfied, not a new missing block.
- Do not conclude that one non-Base binding makes replacement safe. Check all
  relevant branches, including Base fallback, before suggesting any replacement.
  Existing `strip_layer_api`/`blocks_needed` output comparison can help, but must
  not erase differences from the original-binding evidence or override the
  multiple-non-Base-binding clear rule.

Source-mode changes and referenced mode shifts need explicit context. Reuse
static lookup where it applies; identify unsupported lookup cases in the report
rather than silently applying ordinary button semantics. Do not expand this
into analog geometry or timer simulation.

## 4. Produce a usable report

Add `audit_flow_inheritance.py` with proposed usage:

```sh
python3 -m tools.audit_flow_inheritance \
  neptune/single-set-default_hold-gyro_latest.json \
  --layer 'RTP: Double Tap'

python3 -m tools.audit_flow_inheritance \
  neptune/single-set-default_hold-gyro_latest.json --json
```

The default configuration supplies the intended-flow rules; allow `--config`
for another layout's declared exceptions. Make the tool work without `out/`.
Print a concise table plus the paths and original bindings supporting each
finding. JSON includes layout identity, flow-rule identity, target coverage,
unclassified entries and unsupported cases. Distinguish coverage gaps from
inheritance conflicts; neither should be presented as a runtime impossibility.
The proposed CLI and module names are implementation choices, not existing tools.

## 5. Validate and benchmark

Use small fixtures with manually known paths and expected inherited bindings:

- Branching adds and both modifier orders preserve different lower stacks.
- A removal before an add removes the old owner from the resulting stack.
- Re-add versus remove/add ordering, normal releases into windows, and cycles.
- Overridden inputs, explicit empty bindings, disabled sources, Base fallback.
- Same binding from two owners versus two genuinely different bindings.
- Existing clears, unsafe replacements, and unclassified transition reporting.

Then review representative modifier, menu, stick-touch and RTP flows in both
Neptune variants. Pin the exact input hashes used for the benchmark; the old
90.6 research checkpoint is reference material, not the required new target.
Record wall time, peak memory, flow/context counts and classification coverage.
Aim for seconds on routine layouts; measure before promising a runtime. If path
counts explode, inspect unintended branch combinations before adding machinery.

Acceptance: every audited intended route has an explanation; every relevant
layer-changing entry is classified or explicitly accounted for; each finding
links to concrete binding/path evidence; and both variants run without Z3 or
saved search data. Uncovered cases remain visible and prevent a clean audit.

## 6. Follow-up, after the first checker is useful

Add targeted above-layer checks for lightweight covers using their intended
owners and overlays. Then apply the report to cleanup/blocking decisions and
consider integration with `audit_inheritance.py`. Keep automatic layout edits
and cleanup generation separate. Preserve the deprecated research code for
reuse or a specifically justified investigation.

## Work order

- [x] Extract a transition inventory for modifiers and one menu family.
- [x] Implement path traversal and verify those small, known flows.
- [x] Implement binding comparison and clear/block recommendations.
- [x] Add readable/JSON reports and coverage diagnostics.
- [x] Extend intended-flow classification to both layouts; validate and benchmark.
- [x] Add the focused lightweight-cover check afterward.

Related: [todos](../todos.md), [cleanup generator proposal](2026-09-30-cleanup-generator.md),
[deprecated tooling](../findings/2026-09-30-stack-search/ARCHIVE.md).
