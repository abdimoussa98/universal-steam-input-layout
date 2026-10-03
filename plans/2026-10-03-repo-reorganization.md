# Plan: reorganize the repo, one skills directory, a short README

**Status, 2026-10-03:** done, in four commits after `90ed6c8` (the 90.16 to
90.19 work, committed first). The README is 118 lines. Checked at the end:
build audit clean, 627 tests pass, 6 exporter tests pass, the change report
shows no changes, and a rebuild of 90.19 from the edited builders gives the
working layouts byte for byte.

What differs from the plan as written:

- `docs/` has a sixth page, `reading-guide.md`, for the README's annotated list
  of resources and findings.
- `steam_layout/rules.py` did change: its `SOURCES` table names three of the
  moved modules (Part 2).
- The chord-ID table had 22 unknown rows, not six (Part 6).
- The plan left `findings/` as written. But 38 links in 14 records pointed at
  files that moved. The targets of 31 were repointed (the scripts, to `tools/`;
  `traced_stacks.json`; and what went to `archived/`); the text of each link
  is unchanged. Seven links in
  `findings/2026-09-29-steering-design-review/AUDIT.md` point at the deleted
  `.cursor/skills/` files and stay broken: it lists what was read that day.

## Why

The repo root has 26 entries: 12 loose CLI scripts, two parallel skill
directories (`.claude/skills/` and `.cursor/skills/`), a 515-line README that
is really a reference manual, a retired stub, a one-off migration folder from
April and a loose config file. The layering underneath is sound
(`steam_layout/` library, `neptune/` working layouts, `versions/` snapshots,
`findings/` dated records, `archived/`), but nothing says what lives where, and
the command that runs the test suite is written down nowhere.

**Outcome:** one `skills/` directory that belongs to no tool, a `tools/`
directory for the command-line scripts, a README under 150 lines built around
a directory map, the long reference sections moved (not deleted) into `docs/`,
and `resources/` checked for documents that no longer describe the layouts.

**Brevity is a requirement** (author, 2026-10-03). The README has a hard cap of
150 lines. New `docs/` pages use short sentences and tables, and don't restate
the Definition of Done. The existing long documents are not rewritten here;
only their stale pointers are fixed.

## Decisions

The author chose these on 2026-10-03:

| Question | Decision |
|---|---|
| Where the skills live | `skills/` holds the real files; `.claude/skills` becomes a symlink to it, so Claude Code still finds them |
| The two skills that exist only under `.cursor/` | Promote both, rewritten in the style of the other four |
| The 12 scripts at the root | Move them to `tools/` |
| Where the README's long sections go | A new `docs/` folder |
| `resources/` | Audit it; `Layer Reverse Lookup.md` was the author's example of a dead document |

## Baseline, on 90.19

| Check | Result |
|---|---|
| `python3 audit_build.py` | Four passes per layout, "clean", exit 0 |
| The test suite (command below) | 627 tests, all pass, about 5 minutes |
| `node --test tests/test_convert_vdf.mjs` | 6 pass |
| `python3 change_report.py` | "No changes" for both layouts |

```bash
PYTHONPATH=.:tests python3 -m unittest $(ls tests/test_*.py | sed 's#/#.#; s#\.py$##' | tr '\n' ' ')
```

`tests/` has to be on the path because four test modules import a sibling by
its bare name. `python3 -m unittest discover` does not work.

## Step 0: before any move

1. **Commit the 90.16 to 90.19 work.** The reorganization renames files that
   are modified or untracked today; mixing the two makes every rename
   unreviewable.
2. Record the baseline again on the clean tree.

Then four commits, each leaving the suite passing: skills, `tools/`, loose
files and resources, README and `docs/`.

## Target structure

```
├── README.md              # under 150 lines: what it is, quick start, the directory map
├── todos.md
├── docs/                  # new: taken out of the README
│   ├── tools.md           #   every script, the library table, the entry budget, running the tests
│   ├── runtime-ids.md     #   runtime ID numbering and the list-order hazard
│   ├── publishing.md      #   the five-step release workflow
│   ├── file-formats.md    #   JSON and VDF, the exporter
│   └── building.md        #   the generated layouts and the builder chain
├── skills/                # new home: six skills, the real files
├── .claude/
│   ├── settings.local.json
│   └── skills -> ../skills        # symlink
├── tools/                 # new: the 12 scripts, and id_replacement/
├── steam_layout/          # library; traced_stacks.json joins flow_config.json here
├── neptune/               # the two live layout pairs, nothing else
├── versions/neptune/<v>/  # release snapshots
├── resources/             # domain knowledge, 7 documents after the audit
├── plans/  findings/  tests/  archived/
```

`.cursor/` is deleted.

## Part 1: skills

Checked: `.claude/skills/` is the maintained set (frontmatter, rule IDs, last
commit 2026-10-03). Each of the four `.cursor/` copies carries a banner saying
the `.claude` copy wins. Claude Code's documentation says a skill folder may be
a symlink.

1. `git mv .claude/skills skills`, then `ln -s ../skills .claude/skills`.
2. In each moved `SKILL.md`, links are one level shallower:
   `../../../resources/` becomes `../../resources/`.
3. Promote `steam-actionset-delete` and `steam-runtimeid-remap` from
   `.cursor/`, rewritten in the style of the other four (frontmatter, a
   `# Title`, the rule-ID line, the new `tools/` paths). Keep every guardrail:
   the two-pass replacement, the backup file name, "prefer title tokens".
4. `skills/README.md`: the six skills, one line each, and a note on the symlink.
5. `git rm -r .cursor`.
6. `tests/test_rule_registry.py`: three globs of `ROOT / ".claude" / "skills"`
   become `ROOT / "skills"`.
7. `resources/Layer Definition of Done.md`, four links: `../.claude/skills/`
   becomes `../skills/`.
8. Links to `.claude/skills/` inside `findings/` stay. They are dated records,
   and they still resolve through the symlink.

## Part 2: `tools/`

`git mv` the 12 scripts and `id_replacement/` into `tools/`, with an empty
`tools/__init__.py`. Commands become `python3 -m tools.<name>`, run from the
repo root. That is the form the repo already uses
(`python3 -m steam_layout.fixes`, `python3 -m tests.scenario`), and it is
needed because eight of the scripts import `steam_layout`. The exporter becomes
`node tools/convert_vdf.mjs`.

**Inside the moved scripts,** four paths assumed the root:

- `audit_build.py`: `ROOT` becomes `parents[1]`; each audit runs as
  `[sys.executable, "-m", "tools.<module>", ...]`; the printed `rerun:` hint
  changes to match.
- `audit_inheritance.py` and `change_report.py`: `ROOT` becomes `parents[1]`.
- `audit_cleanups.py`: `RULES` becomes
  `parents[1] / "steam_layout" / "flow_config.json"`.

**Everywhere else, five patterns.** The counts are from 90.19. The builder
chain grows by a folder per release, so the search below is the test, not the
counts.

| Pattern | Becomes | Where |
|---|---|---|
| `from audit_x import`, `import audit_x`, and the same for `convert_runtime_ids` | `from tools.audit_x import` | 58 lines in 36 files: 17 builders, 18 tests, `steam_layout/fixes/menu_combo_keys.py` |
| `ROOT / "convert_vdf.mjs"`, in either quote style | `ROOT / "tools" / "convert_vdf.mjs"` | 21 builders and installers in `findings/` |
| A script path given to `subprocess.run`, such as `str(ROOT / "audit_x.py")` | `"-m", "tools.audit_x"` with `cwd=ROOT` | 7 test files, 11 calls |
| `ROOT.glob("audit_*.py")` | `(ROOT / "tools").glob("audit_*.py")` | `tests/test_rule_registry.py`, twice |
| `'../convert_vdf.mjs'` | `'../tools/convert_vdf.mjs'` | `tests/test_convert_vdf.mjs`, twice |

Afterwards this prints nothing:

```bash
grep -rnE "^\s*(from|import) (audit_|convert_runtime_ids|change_report)|/ ['\"](convert_vdf\.mjs|audit_[a-z_]+\.py|change_report\.py)['\"]" \
  tests steam_layout findings tools --include="*.py" | grep -v "['\"]tools['\"] /"
```

Notes:

- **This edits 26 scripts in `findings/`, which are frozen records.** It can't
  be avoided: the installer in `findings/2026-10-03-pad-click-holds/` loads all
  ten builders by file path. The change is the import line and the exporter
  path, nothing else. `archived/README.md` gets one line saying so.
- `steam_layout/rules.py`: the Definition of Done names audits by title
  ("Budget audit"), not by file name, so the parser doesn't change. Its
  `SOURCES` table does: it imports three of the scripts by module name to read
  their `ENFORCES` tables (found while building; the plan first said no change).
- **The manifests keep their hashes.** Each builder's `manifest.json` records a
  SHA-256 of the builder before it. The import edit changes those files, so the
  recorded hashes are of the builders as built. Nothing reads them. A rebuild
  of 90.19 from the edited builders gives the same layouts, byte for byte.
- The next release's builder is made by copying the previous one, so it gets
  the new form. `docs/building.md` says this in one line.

## Part 3: loose files

| File | Goes to | Why |
|---|---|---|
| `traced_stacks.json` | `steam_layout/traced_stacks.json` | Beside `flow_config.json`. Nine references in code (`tools/audit_inheritance.py`, `steam_layout/fixes/window_routes.py`, four test files) and one link in the Definition of Done |
| `manual-testing.md` | `archived/` | A retired stub; its whole body says so |
| `resources/scratch paper/` | `archived/scratch-paper/` | Four empty files and two pasted JSON fragments; nothing live points at them |
| `neptune/empty_0.vdf` | `archived/` | Nothing points at it |
| `.DS_Store` | `git rm --cached` | Tracked although `.gitignore` names it |

`out/` stays: Git ignores it, and `archived/README.md` already says it can be
deleted.

## Part 4: README and `docs/`

Every section that leaves the README is moved whole. What is cut, not moved,
is repetition, and history that `findings/` already holds.

| README at 90.19 (lines) | Goes to |
|---|---|
| 1 to 28: title, install, variants | Stays, tightened |
| 30 to 290: the three editing scripts, six audits, change report, library table | `docs/tools.md` |
| 291 to 337: command entry limit, dead-group prune | `docs/tools.md` |
| 339 to 372: runtime IDs, the list-order hazard | `docs/runtime-ids.md` |
| 374 to 401: the annotated list of resources and findings | One line each in the README; the notes go to `docs/` |
| 403 to 445: publishing | `docs/publishing.md` |
| 447 to 488: file formats, the exporter | `docs/file-formats.md` |
| 490 to 515: the generated layouts, the 90.10 to 90.19 build records | `docs/building.md` |

The new README's line budget:

| Section | Lines |
|---|---|
| What it is, install, the two variants | 20 |
| Quick start: build audit, test suite, export | 15 |
| **The directory map:** one line per entry, saying what belongs there and what doesn't | 55 |
| Where a new file goes | 15 |
| Index of `docs/` and `resources/` | 20 |
| Conventions: run from the root, `-m tools.x`, dated records are frozen | 15 |

Four stale lines are fixed in the rewrite: line 387 lists `Action Sets.md`,
deleted in commit `5517a7f`; line 388 lists `Layer Reverse Lookup.md` (Part 6);
line 379 says Stateful Layer Transitions is "not built yet", and it shipped in
90.10; line 445 names the `.cursor` skills. One thing is added: the test-suite
command.

## Part 5: reference sweep

Update commands and paths in the live documents: the README (35), the skills
(17), `resources/` (8), `plans/` (5), `todos.md` (2) and one docstring in
`steam_layout/`.

The prose in `findings/` (21 commands) and `archived/` stays as written: it
records what was run that day. Extend the two ID checks in
`tests/test_rule_registry.py` to read `docs/*.md`, so rule and assumption IDs
there are checked like those in `resources/`.

## Part 6: resources audit

All ten files, checked against 90.19 (one action set, 75 layers).

| File | Last real change | Verdict |
|---|---|---|
| `Layer Definition of Done.md` | 2026-10-03 | Current |
| `Steam Behaviour Assumptions.md` | 2026-10-03 | Current |
| `Stateful Layer Transitions.md` | 2026-10-03 | Current. The README is what is wrong about it |
| `Layout Vocabulary.md` | 2026-10-03 | Current |
| `Steam Input JSON Structure.md` | 2026-10-03 | Current, with three stale pointers |
| `Cleanup Functions.md` | 2026-10-02 | Keep. A superseded draft whose own header says R127 to R132 win |
| `Neptune Chorded Button Ids.md` | 2025-09-08 | **Keep and correct** |
| `neptune_chord_ids.json`, `.vdf` | 2025-07-31 | Keep. The probe layout that table came from |
| `Layer Reverse Lookup.md` | 2025-07-26 | **Archive** |

- **`Layer Reverse Lookup.md` goes to `archived/`.** Its header says "Layer Ids
  as of 31.0", and it maps the four-set layouts (Base, Gyro, Alt, Gamepad) that
  are already archived. Two earlier audits said the same:
  [the rule inventory](../findings/2026-10-02-rule-inventory/README.md) and
  [the steering design review](../findings/2026-09-29-steering-design-review/AUDIT.md).
  `convert_runtime_ids to-titles` and `duplicate_layer --list` replace it. It
  gets a row in `archived/README.md`.
- **`Neptune Chorded Button Ids.md` is corrected, not archived.** It is the
  only chord-ID table. The
  [exploratory layout audit](../findings/2026-09-27-exploratory-layout-audit/AUDIT.md)
  found 14 and 15 labelled the wrong way round (the layouts bind 14 to Menu
  Right and 15 to Menu Left), and 22 rows were `?`. Done: 14 and 15 are fixed,
  and seven more IDs are filled in from that audit's table and checked against
  90.19 (16, 17, 20, 23, 24, and the mask bits). The buttons the layouts don't
  chord on stay "not known". The header says the layouts use both forms:
  `chord_button` for one button, a mask for several buttons and for stick
  deflection.
- **`Steam Input JSON Structure.md`, lines 1820 and 1863 to 1865,** point at
  the lookup and at `Ramp Up Layers Comparison.md`, which is already in
  `archived/`. Repoint them. Nothing else in that document changes.

## Verification

From the repo root, after each commit:

1. `git status`: every move shows as a rename.
2. The search in Part 2 prints nothing.
3. `python3 -m tools.audit_build`: four passes per layout, "clean", exit 0.
4. The test suite: 627 tests, all pass. It loads all ten builders by path, so
   it covers the import changes.
5. `node --test tests/test_convert_vdf.mjs`: 6 pass.
6. `python3 -m tools.change_report`: "No changes" for both layouts. Nothing
   here edits a layout, so any difference means something went wrong.
7. The exporter path, which no test covers: run
   `findings/2026-10-03-pad-click-holds/build_candidate.py`, then
   `install_neptune.py --deck` in the same folder. Both finish, `git status`
   shows no tracked file changed, and the `deck/` folder it makes is deleted.
8. Each script answers `--help` as `python3 -m tools.<name>`.
9. `.claude/skills/steam-layout-prep/SKILL.md` reads through the symlink, and
   a new Claude Code session lists all six skills.
10. A link check over `README.md`, `docs/`, `skills/` and `resources/`, and a
    search for plain-text mentions of files that moved.
11. `wc -l README.md`: under 150.

## Not in this plan

- **The builder chain stays in `findings/`.** Ten builders load each other by
  path; moving them would break the chain and change the records.
- **No layout JSON or VDF changes, and no version bump.**
- **The long `resources/` documents are not shortened.**
  `Steam Input JSON Structure.md` (1,870 lines) gets three pointer fixes only.
