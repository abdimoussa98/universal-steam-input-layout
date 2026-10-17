# Publishing layout changes

A change is built on Ibex, the base layout, and converted to the other
controllers ([building](building.md), R177). Each controller has its own
version and its own releases: a release is a version with a Git tag
`<controller>-v<version>`, such as `neptune-v90.75`, and pushing the tag
publishes it. Apply these steps before committing a layout update, exporting it
for delivery, or publishing it:

1. Require a **concise, accurate** `controller_mappings.description` for each
   controller: a short overview of the main features and essential
   default/alternative controls. The descriptions are in the registry,
   [controllers.py](../steam_layout/controllers.py), from where the builder and
   `tools.convert` write them. Keep detailed gestures, timing, tuning, and
   implementation notes in repository documentation. Read each description
   against its final layout and correct stale claims or control mappings.
2. **Each controller that changed gets its next version** at the end of
   `controller_mappings.title`, such as `90.74` to `90.75`, one per release
   batch, the same in both variants. Ibex's builder writes Ibex's;
   `python3 -m tools.convert <controller>` writes the next one for the Deck and
   the Edge. A controller whose layout did not change keeps its version. The
   version is separate from the schema `version`, the export `revision` and the
   runtime layer IDs, which a release never changes. Versions compare as
   numbers: 90.10 is higher than 90.9.
3. Complete the build audit, ordering, reference and regression checks.
   **Always regenerate the sibling VDF after every successful, validated JSON
   edit, in the same task.** This includes settings, bindings, title/version and
   description changes. No separate export request or permission is needed. If
   conversion fails, report the blocker; do not claim the edit is complete.
   Local VDF export does not authorize a commit or a Steam upload.
4. **Save the snapshot after the export**, for each controller that changed:
   `python3 -m tools.release snapshot <controller>` copies each variant's JSON
   and VDF into `versions/<controller>/<version>/`, with `_latest` in the file
   name replaced by the version, such as
   `versions/neptune/90.75/single-set-default_hold-gyro_90.75.vdf`. The
   working directory stays the live copy. Until the version is tagged, a
   follow-up edit in the same batch refreshes its snapshot. **A tagged snapshot
   never changes**: a fix after the tag is a new version, and the tool refuses
   to overwrite one.
5. Write the change's press sequences as scenario tests, and list the
   assumptions that aren't verified in the release's record:
   `python3 -m tests.scenario --out findings/<date>-<slug>/`
   ([Definition of Done §10](../resources/Layer%20Definition%20of%20Done.md#10-ship-it),
   R165 to R167). A passing scenario is not evidence of what Steam does: an
   assumption's status in
   [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md)
   says that. The author tests on the device; a trial ends here and is never
   tagged.
6. Add a section to [CHANGELOG.md](../CHANGELOG.md), newest first, headed
   `## <controller> <version>`, with a short summary and a link to the findings
   record that built it. A conversion's section names the Ibex release it is
   made from: `From ibex 1.0.`
7. `python3 -m tools.release check <controller>` passes for each controller
   being released: titles, snapshot, a fresh export of each VDF, the version
   above the latest release, the CHANGELOG section, released snapshots
   unchanged, and a conversion equal to what `tools.convert` makes from its
   Ibex release.
8. Commit and push `main`, then tag each controller the change releases and
   push the tags in the same step. **Every push to `main` that carries a new
   version is tagged** (author, 2026-10-17): a version on `main` without its
   tag is not done. An Ibex change usually releases all three, and the tags
   can go together:

   ```bash
   git tag ibex-v1.1 && git tag neptune-v90.77 && git tag dse-v1.1
   git push origin main ibex-v1.1 neptune-v90.77 dse-v1.1
   ```

## What the workflow does

[release.yml](../.github/workflows/release.yml) runs on every pushed
`*-v*` tag, and by hand (Actions, Release, Run workflow) to retry. Each run
publishes every release tag that has no GitHub Release yet, oldest first, so
tags pushed together are all published even when GitHub cancels a waiting
run. A tag must be on `main`. For each tagged commit it runs the Python tests
in four parallel parts, both Node files and the build audit. Each Python part
uploads its assigned case outcomes and scenario evidence. A dependent job
requires all four parts from the same commit/run/attempt, rejects missing, duplicate,
stale or unsuccessful records, and checks changed-layer reach separately for
Neptune and DSE. Publication depends on that finalizer as well as every test
and audit job. Checkouts retain tags/history for ancestry and snapshot tests.
See [testing](testing.md) for local and focused commands.

To retry a failed run, choose **Re-run all jobs**, or start a new **Run
workflow**. Evidence artifacts are isolated by attempt, and all four Python
parts must finish in that attempt. Rerunning only failed jobs does not supply
a complete set of evidence for the new attempt and cannot pass the finalizer.

The workflow loads `tools/test_compat.py` from its own commit so it can also
publish older tags that predate the organized suite. At those tags it runs
the tag's original four unittest shards and both original Node files, and
requires four successful completion records for that exact commit/run/attempt and
module partition. These explicitly legacy records cannot satisfy the new
scenario-evidence gate. Tags containing `tests.runner` use the full protocol
described above.

For each tag it runs
`tools.release check --tagged`, then `tools.release bundle`, and creates the
GitHub Release with the bundle and the CHANGELOG section as its notes.

The bundle is one zip, `universal-steam-input-layout.zip`: one folder per
controller with its latest release's two VDFs, and `RELEASE.md`. Every release
carries every controller's latest, so this link always downloads the newest:
<https://github.com/abdimoussa98/universal-steam-input-layout/releases/latest/download/universal-steam-input-layout.zip>.

The workflow never writes a VDF or a snapshot, never judges a description and
never uploads anything to Steam. A tagged release is not evidence of a Steam
upload.

Read-only audits and documentation-only changes do not publish a changed
layout. The [steam-layout-apply](../skills/steam-layout-apply/SKILL.md) skill
enforces this workflow.
