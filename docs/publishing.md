# Publishing layout changes

Every time a changed layout is published, **revalidate its description and bump
its release version**. Apply this before committing a layout update, exporting
it for delivery, or publishing it to Steam:

1. Require a **concise, accurate** `controller_mappings.description`: a short
   overview of the main features and essential default/alternative controls.
   Keep detailed gestures, timing, tuning, and implementation notes in repository
   documentation. Read the full description against the final layout and correct
   stale claims or control mappings; retain wording that is already concise and
   accurate.
2. Increment the release suffix in `controller_mappings.title`, such as `90.2`
   to `90.3`, from the last published release. Use one bump for the release batch,
   including its follow-up edits and export; align both variants when released
   together. This is separate from schema `version`, export `revision`, and runtime
   layer IDs, which must not be changed for a release bump.
3. Complete command-budget, ordering, reference, and relevant regression checks.
   **Always regenerate the sibling VDF after every successful, validated JSON
   edit, in the same task.** This includes settings, bindings, title/version, and
   description changes. Export the final metadata with the layout so JSON and
   VDF agree; no separate export request or permission is needed. This standing
   instruction supersedes the earlier preference to leave VDFs to the user.
   Only a newer explicit instruction for the task can opt out. If conversion
   fails, report the blocker; do not claim the edit is complete. Local VDF export
   does not authorize a commit or Steam upload.
4. **Save a version snapshot after the export.** Copy each variant's final JSON
   and VDF into `versions/neptune/<version>/`, with `_latest` in the filename
   replaced by the version, such as
   `versions/neptune/90.4/single-set-default_hold-gyro_90.4.vdf`. `neptune/`
   remains the live working copy. Follow-up edits in the same release batch
   refresh that version's snapshot; snapshots of other versions are never
   changed. The `steam-layout-apply` skill has the copy command.
5. Write the change's press sequences as scenario tests, and list the
   assumptions that aren't verified in the release's record:
   `python3 -m tests.scenario --out findings/<date>-<slug>/`
   ([Definition of Done §10](../resources/Layer%20Definition%20of%20Done.md#10-ship-it),
   R165 to R167). Committing JSON is not evidence of a successful Steam
   upload, and a passing scenario is not evidence of what Steam does: an
   assumption's status in
   [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md)
   says that.

Read-only audits and documentation-only changes do not publish a changed layout.
The [steam-layout-apply](../skills/steam-layout-apply/SKILL.md) skill enforces this workflow.
