# Plan: recognize, check and regenerate cleanup functions

**Status:** proposed, 2026-09-30. It depends on the author confirming the
definitions in [Cleanup Functions](../resources/Cleanup%20Functions.md),
especially interaction families and survivors. Nothing here has been built.

## Intended-flow inheritance audit (author-approved)

Updated 2026-09-30: build this read-only checker first. The detailed
[implementation plan](2026-10-01-intended-flow-inheritance.md) now tracks that work. Exhaustive stack search,
numeric timer simulation and inductive completeness are deprecated as prerequisites
for routine cleanup audits. Retain their implementation for reuse and targeted
investigations; see the [research archive](../findings/2026-09-30-stack-search/ARCHIVE.md).

1. Follow the intended logical paths of explicit layer additions from Base,
   preserving ordered stacks, relevant button/chord guards and explicit removals
   in each transition. Do not turn the add graph into unrestricted combinations.
2. For each layer and relevant input, inspect its ordered lower stack on each
   intended path. Report the nearest binding owner and original activators,
   including explicit blocks and Base fallback.
3. Compare distinct non-Base inherited bindings across paths. If more than one
   occurs, recommend an explicit clear/block rather than assuming replacement
   works on every path. Identical binding/activator definitions from different
   owners are not automatically different bindings. Keep Base fallback visible.

   > **Correction, 2026-10-01 (author):** this was a misreading. "More than one inherited keybind
   > means block" is not a rule for ordinary layers. It is the last step of the Always On window
   > rule: under a layer with an Always On action, if one of the bindings it could inherit is a
   > layer command, clear the input when more than one keybind is possible, otherwise override it
   > with that keybind. The Window audit checks that. The Flow audit now lists differing inherited
   > bindings as information ("varies") and no longer fails on them.

4. Defer above-layer checks to a separate pass for lightweight covers and other
   specifically identified exceptions. Do not gate the lower-layer audit on
   solving every possible upper-layer relationship.
5. Report the paths and bindings behind each recommendation. Benchmark both
   variants, then use the results to review cleanup and blocking. No layout
   mutations are part of the initial checker.

The scope is intended additive flows, not a proof over every possible runtime
interleaving. Timer edge cases can be investigated separately when a concrete
finding needs them. Built and benchmarked 2026-10-01
([record](../findings/2026-10-01-intended-flow-checker/README.md)).
The older candidate-based cleanup writer below remains a later proposal;
its co-active approximation is not a substitute for the intended-path checker.

## Goal

After changing the stack (a new layer, a new overlay, a changed transition),
run one script that:
1. recognizes every layer-removing binding as one of the defined kinds
2. computes what each **cleanup function** and **owner release** should remove
3. reports the differences, and with `--write` updates the removal lists in
   place

## Building blocks already in place

- `steam_layout.model`: bindings in execution order, and activator entries.
- `steam_layout.stacks.StackSpace`: `when_effective(host, source, input)` and
  `co_active(...)`, which give the candidate layers for any binding.
- `steam_layout.fixes`: the idempotent pipeline, with a fixed-point test, that
  a writer can join.
- The existing tests pin today's recovery shapes, and the regenerated lists
  must still pass them.

## Steps

1. **Recognizer.** Add `steam_layout/cleanups.py`, which classifies each
   activator that removes layers into the kinds in *Cleanup Functions*, using
   shape only (trigger, activation type, settings, order). Report anything
   unclassified.
   - Test: every current removal classifies, in both variants.
2. **Families.** Compute each owner's family: the owners, plus the dependents
   that only the family's bindings add. Apply declared overrides for shared
   dependents.
   - Test: the families match today's documented scopes (single modifier,
     current Mod 2 branch, menu Entry/Fn, Transition Sets).
3. **Scope checker.** Add a read-only `audit_cleanups.py`. For each cleanup
   function and owner release, the expected scope is co-active candidates ∩
   family − survivors, and it is compared with the current list. Report
   *missing* entries (for example F1: Menu Right: Enter) and *extra* entries.
   Then fix, or record a decision, like `traced_stacks.json` does.
4. **Writer** (`--write`, and a pipeline fix):
   - updates only the removal subcommands of those two kinds
   - never touches guards, settings, activation types or other kinds
   - keeps kept removals in their current positions (the author's keep-order
     rule)
   - puts new removals where they run **before** any add in the same array
   - leaves Always On windows untouched
   - flags any new removal of a layer that has a pending delay, because
     removals can reset timers
   - idempotent: the working layouts stay a fixed point
5. **Docs and tests:** link from Definition of Done §7; add the checker to
   the ship checklist and the apply skill.

## Risks

- **Candidates are over-approximated,** because chord conditions are ignored.
  The family filter keeps scopes tight, and survivors are explicit.
- **Timers:** an added removal can reset a pending delay
  ([Blocking to Protect Layer Timers](../resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers)).
  The writer flags these rather than applying them silently.
- **Order:** some arrays deliberately run an add first (touch-release
  completion), and the writer doesn't touch those kinds.

## Open questions

See [Cleanup Functions → Questions for the author](../resources/Cleanup%20Functions.md#questions-for-the-author).
