---
name: steam-layout-apply
description: Finalize an edited Steam Input layout for loading into Steam. Runs pre-flight checks, converts {{Base::Title}} tokens back to numeric runtime IDs with convert_runtime_ids.py to-ids, confirms nothing was left unresolved, exports VDF with convert_vdf.mjs, and saves a per-version backup copy under versions/neptune/. Use this whenever edits to a layout JSON in this repo are finished and it needs to go back into Steam, or when the user asks to run to-ids, finalize, export, produce a VDF, or back up a layout version.
---

# Finalize a layout for Steam

Rule IDs (R108 and so on) point at the [Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md#rule-tables), which holds each rule's full text, example and check.

## Required completion: JSON and VDF together

Standing user instruction: after successfully editing and validating a layout
JSON, **always regenerate its sibling VDF in the same task**. Run the exporter
below without asking for separate permission. This includes settings, bindings,
title/version, and description edits. Do not stop at JSON completion or leave
conversion to the user. This supersedes the earlier leave-VDFs-to-the-user
preference; only a newer explicit instruction for the current task can opt out.
If export fails, report the blocker and keep the task incomplete rather than
claiming the layout is ready. Exporting a local VDF does not authorize a commit
or an upload to Steam.

**All work is on `main`** (author, 2026-10-03). Don't create a branch or a
worktree for a release, also when an agent's own default says to branch before
committing. When the author asks for a commit, it goes on `main`.

## Required publication metadata

**R151.** Every publication of a changed layout must include a reviewed description and
a version bump. Before committing layout changes, exporting for delivery, or
publishing to Steam, follow [Publishing layout changes](../../docs/publishing.md):

- Read the complete `controller_mappings.description` against the final layout.
  Correct stale behavior, control mappings, tuning, and implemented/planned status;
  keep an accurate description if no wording needs changing.
- Increment the release version in `controller_mappings.title` from the last
  published revision (for example `90.2` → `90.3`). Bump once per release batch,
  not once per edit or converter run; keep jointly released variants aligned.
- Do not use the schema `version`, export `revision`, or runtime IDs as the
  release version. Preserve these unrelated fields.
- Export only after metadata and validation are final, so JSON/VDF titles and
  descriptions match. Always regenerate the sibling VDF after the validated JSON
  edit. A JSON update alone is not a completed layout edit or Steam publication.

## Required version snapshot

Standing user instruction: after the JSON is validated, the VDF is regenerated,
and the description and version are final, **save a copy of the layout under
`versions/neptune/<version>/`** in the same task, without asking. `neptune/`
stays the live working copy; every edit still goes there. The snapshot is the
final step of a completed layout edit (step 4, item 2 below).

- `<version>` is the release suffix of `controller_mappings.title` (the part
  after the last ` :: `, such as `90.4`). Copy each variant's JSON and VDF,
  replacing `_latest` in the filename with `_<version>`, for example
  `versions/neptune/90.4/single-set-default_hold-gyro_90.4.json`.
- Follow-up edits in the same release batch refresh that version's snapshot.
  Never edit, overwrite, or delete a snapshot for any other version. If the
  current version was already published, bump the title first (see above)
  rather than overwriting its published snapshot.
- Snapshot files are backups. Don't edit them, and don't point tools or tests at
  them. Saving a snapshot does not authorize a commit or an upload to Steam.

## 1. Run the pre-flight check

**R164.** Read the change report first: `python3 -m tools.change_report --out findings/<date>-<slug>/`
lists what differs from the newest snapshot, by layer and input, and saves it
with the release's record. Every change in it should be one somebody decided;
a fix can change a binding on its own.

For binding, source, or layer-transition changes, confirm the
[inheritance review](../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes)
records affected upper layers, intended inheritance/blocks, and protected timer
entry/exit behavior. Numeric-reference and command-budget checks do not verify
effective inherited behavior. Write the held-across-transition and newly activated
input cases as scenario tests (below). When reporting, keep three things apart:
what a static check shows, what a scenario shows on the simulator, and what
Steam was seen to do (an assumption's status).

**R165 to R167.** The press sequences of a new or changed layer are scenario
tests in `tests/test_scenarios_*.py`: an input held across the change, a press
inside the layer, and a release missed while the Steam menu is open
([how to write one](../../tests/scenario.py)). The tests fail while a layer
that changed since the newest snapshot is on the stack in no scenario, so run
them before saving the snapshot. A Steam behaviour the change depends on gets a
row in [Steam Behaviour Assumptions](../../resources/Steam%20Behaviour%20Assumptions.md),
and the scenario names it. Then
`python3 -m tests.scenario --out findings/<date>-<slug>/` writes
`unverified-assumptions.txt` into the release's record: every assumption that
isn't verified, with the rules and scenarios resting on it. A layer whose tests
pass but rest on one of those is done, and listed.

**R150.** Run the build audit first: `python3 -m tools.audit_build`. It runs the Budget audit,
the Window audit, the Flow audit and the Cleanup audit on both working layouts and must exit
**0** before any version is finalized
([Layer Definition of Done §10](../../resources/Layer%20Definition%20of%20Done.md#10-ship-it)).
The paragraphs below describe the individual audits it runs.

The Budget audit (R108, R109, R111) is `python3 -m tools.audit_command_budget path/to/layout.json`. It must exit **0**
before finalizing a layout for Steam. It also fails on any Long Press or Double
Press, which are banned (see `steam-binding-order`). The limit is **three GUI command entries per
input**, across activator types; `binding` array subcommands do not consume extra
entries. The checker includes inactive/unreferenced groups and checks disabled
banks separately. Resolve failures using `steam-binding-order`; do not truncate
cleanup subcommands to make a count pass. Read-only audits may report failures
without changing the layout.

The Window audit (R140) is `python3 -m tools.audit_inheritance path/to/layout.json`. It must also exit
**0**. It derives every stack each Always On layer can be applied on and fails
on any undecided layer command underneath, or on a window no stack reaches. Apply
its `blocks_needed` (replace only if the underlying output is identical in
every stack, otherwise clear). The install runs
`steam_layout.fixes` pipeline, which does
this (`python3 -m steam_layout.fixes <layout> --dry-run` shows what it would change). See
[Layer Definition of Done §8](../../resources/Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking).

The Flow audit (R144, R145) is `python3 -m tools.audit_flow_inheritance path/to/layout.json`. It
must exit **0**: a chain of adding bindings reaches every layer, and no cover
finding is open. A new or renamed layer needs no declaration; only a cover
whose title doesn't end in a cover suffix, or an accepted finding as an entry
in the exceptions register with its reason, goes in `steam_layout/flow_config.json`. An inherited binding that
differs between stacks fails it on a layer that changed since the newest snapshot (R139): fix it, or accept it
in the register with a reason. The Cleanup audit does the same for a covered side exit (R136).

The Cleanup audit (R127 to R132) is `python3 -m tools.audit_cleanups path/to/layout.json`. It must
exit **0**: every cleanup function and release follows the six cleanup rules
(Layer Definition of Done §7). The `cleanup_lists` step of the fix pipeline
resolves its findings (`python3 -m steam_layout.fixes <layout> --dry-run`
shows what it would change). A removal kept on purpose is an exception to
R132 in the exceptions register (`steam_layout/flow_config.json`), with its reason.

The same command checks the required cleanups (R169 to R171): a cleanup function
on both stick touches, on the stick edges, and on every button the layer retypes
or blocks. No fix resolves these. Add the cleanup function in the builder, or
record the input as an exception to that rule in the register, with the
author's reason.

```bash
python3 - path/to/layout.json <<'EOF'
import json, sys, collections
cm = json.load(open(sys.argv[1]))["controller_mappings"]
order = list(cm["actions"]) + list(cm["action_layers"])
keys = [int(k.split("_")[1]) for k in cm["action_layers"]]
dups = [t for t, n in collections.Counter(v["title"] for v in cm["action_layers"].values()).items() if n > 1]
print("layer order:  ", "OK" if keys == sorted(keys) else "OUT OF ORDER (list order != Preset_ numeric order)")
print("preset blocks:", "OK" if [p["name"] for p in cm["preset"]] == order else "MISMATCH (not in actions + layers order)")
print("preset ids:   ", "OK" if [p["id"] for p in cm["preset"]] == [str(i) for i in range(len(cm["preset"]))] else "not sequential 0..N")
print("dup titles:   ", dups or "none")
EOF
```

Continue only if every line is `OK` and `dup titles` is `none` (R104, R105):

- **Out of order or mismatched:** the generated IDs could be resolved against the wrong ordering on a fresh load, which silently swaps layers. Normalize first, while the file is still in title form. The procedure is in the `steam-layout-prep` skill and `findings/2026-07-11-layer-order-swap/FINDINGS.md`.
- **Duplicate titles:** every duplicate token becomes the ID of the *last* layer with that title. `to-ids` gives no warning about this. Stop and tell the user. The fix is to rename the layers, and then work out which `{{Base::<title>}}` tokens belong to which layer.

## 2. Convert titles to IDs

```bash
python3 -m tools.convert_runtime_ids to-ids path/to/layout.json                                   # in place
python3 -m tools.convert_runtime_ids to-ids path/to/layout.json --output path/to/layout_final.json
```

The script prints `Warning: Could not find runtime ID for '<title>'` for any token that doesn't match a current `Parent::Title`. The usual cause is a renamed layer. Those tokens stay in the file unchanged.

## 3. Verify nothing is left unresolved

```bash
grep -c 'controller_action [A-Za-z_]* {{' path/to/layout_final.json   # must print 0
```

## 4. Hand off for Steam

1. **JSON → VDF:** run `node tools/convert_vdf.mjs path/to/layout_final.json`. This writes/replaces the sibling `.vdf` using the installed `pfwobcke.vscode-vdf` serializer and verifies keys, values, repeated bindings, and order before writing. Use `-o path/to/output.vdf` for a different destination. See `docs/file-formats.md` for requirements and extension discovery. The agent can complete this export directly.
2. **Save the version snapshot:** once every exported variant has its final description and version, copy each one into `versions/neptune/<version>/` (see [Required version snapshot](#required-version-snapshot)):

   ```bash
   for json in neptune/*_latest.json; do
     v=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["controller_mappings"]["title"].rsplit(" :: ", 1)[-1])' "$json")
     [[ "$v" =~ ^[0-9]+(\.[0-9]+)+$ ]] || { echo "unexpected version '$v' in $json"; break; }
     mkdir -p "versions/neptune/$v"
     for src in "$json" "${json%.json}.vdf"; do
       dst="versions/neptune/$v/$(basename "${src/_latest/_$v}")"
       cp "$src" "$dst" && cmp "$src" "$dst" && echo "saved $dst"
     done
   done
   ```

   Expect one `saved` line for each JSON and VDF. Run it from the repo root, and only after every variant is exported. It copies every `neptune/*_latest.json` and its sibling VDF, so a variant with a stale VDF would be snapshotted stale.
3. **Test on a fresh load:** the user loads the layout and spot-checks the binds on any layers that were added, renamed, or reordered. Checking in the live editing session isn't enough, because there layers are resolved by handle and swaps don't show up.
4. **Return to editing:** to keep working, run `to-titles` again (see `steam-layout-prep`).

## Guardrails

- `to-ids` only checks that tokens resolve. It doesn't check that each bind targets the layer you intended, so review `add_layer` / `remove_layer` targets in title form before converting.
- If you renamed a set or layer, every token for it must use the new `Parent::Title` exactly.
- Don't reorder `actions` / `action_layers` after converting to IDs.

## References

- Converter: `convert_runtime_ids.py`
- Runtime ID rules and the load-order caveat: `docs/runtime-ids.md`, `resources/Steam Input JSON Structure.md`
