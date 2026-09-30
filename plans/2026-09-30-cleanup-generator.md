# Plan: recognize, check and regenerate cleanup functions

**Status:** proposed, 2026-09-30. It depends on the author confirming the
definitions in [Cleanup Functions](../resources/Cleanup%20Functions.md),
especially interaction families and survivors. Nothing here has been built.

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
