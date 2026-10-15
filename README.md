# Universal Steam Input Layout

Custom Steam Input controller layouts for the Steam Controller 2 (Ibex, the
base layout), the Steam Deck and the DualSense Edge, built from action layers
on a single action set.

Layers are added and removed with explicit `add_layer` and `remove_layer`
commands, and the layouts never switch action sets. `hold_layer` is used only
where the exceptions register allows it. See the
[runtime rules](resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30)
and the [Layer Definition of Done](resources/Layer%20Definition%20of%20Done.md).

## Install

Download the [latest release](https://github.com/abdimoussa98/universal-steam-input-layout/releases/latest/download/universal-steam-input-layout.zip)
([all releases](https://github.com/abdimoussa98/universal-steam-input-layout/releases)):
one folder per controller. Copy your controller's two `.vdf` files into Steam's
`controller_base/templates/` folder, on the Steam Deck
`/home/deck/.steam/steam/controller_base/templates/`. What changed is in
[CHANGELOG.md](CHANGELOG.md).

## The two variants

| Layout | Triggers | Modifiers |
|---|---|---|
| **Default** | L2/R2 | L1/R1: the bumpers add modifier layers |
| **Alternative** | L1/R1 | L2/R2: the triggers add modifier layers |

- **Default** is the usual shooter scheme: L2/R2 aim and fire, and the bumpers
  switch the other buttons to alternate mappings.
- **Alternative** inverts it, for games where analog trigger control matters less.

## Quick start

Run everything from the repo root.

```bash
python3 -m tools.audit_build          # the gate for every version: four audits, every controller's layouts
python3 -m tools.change_report        # working layouts against their newest snapshots
node tools/convert_vdf.mjs neptune/single-set-default_hold-gyro_latest.json   # JSON to VDF
python3 -m tools.release check neptune   # before tagging a release (docs/publishing.md)

# every Python test (about 46 minutes on this Mac), then the exporter's tests
PYTHONPATH=.:tests python3 -m unittest $(ls tests/test_*.py | sed 's#/#.#; s#\.py$##' | tr '\n' ' ')
node --test tests/test_convert_vdf.mjs
```

The layouts in `neptune/` are **generated**. To change one, change the builder
and install it ([building](docs/building.md)); a hand edit is lost on the next
install.

## Directory map

```
├── README.md
├── CHANGELOG.md           every release, newest first
├── todos.md               the live to-do list, and what is left to check on the Deck
├── ibex/                  Steam Controller 2: the base layout, JSON and VDF. Generated
├── neptune/               Steam Deck: the two working layouts. Generated
├── dse/                   DualSense Edge: the two working layouts. Converted from Ibex
├── versions/<c>/<v>/      one snapshot per controller and version. Never changed once tagged
├── .github/workflows/     the release pipeline: a pushed tag publishes the bundle
├── tools/                 the command-line scripts: audits, converters, editors
├── steam_layout/          the library behind the tools, and the fix pipeline
├── tests/                 unit tests, and press-by-press scenario tests
├── skills/                agent skills: the steps of an edit, in order
├── docs/                  how to work in this repo
├── resources/             what is true of Steam Input and of these layouts
├── plans/                 dated plans, each with a status line
├── findings/              dated records: audits, investigations, and every build
└── archived/              deprecated code and documents, kept for reference
```

| Directory | What belongs there | What doesn't |
|---|---|---|
| `ibex/`, `neptune/`, `dse/` | Each controller's two working layouts, `<stem>_latest.json` and `.vdf` ([controllers](resources/Controllers.md)) | Hand edits, candidates, backups |
| `versions/` | `<controller>/<version>/`: the JSON and VDF of a version, with the version in the file name | Edits to a tagged snapshot |
| `tools/` | A script someone runs: `python3 -m tools.<name>`. [Reference](docs/tools.md) | Logic that two scripts share: that goes in `steam_layout/` |
| `steam_layout/` | Importable code, the fixes in `fixes/`, the chain engine's source in `engine/`, and the two config files: `flow_config.json` (rules and the exceptions register) and `traced_stacks.json` | Scripts with a command line |
| `tests/` | `test_*.py`, `test_scenarios_<release>.py`, and `scenario.py`, the gesture helpers | One-off scripts for an investigation: those stay with their finding |
| `skills/` | One folder per skill, each a `SKILL.md`. `.claude/skills` and `.agents/skills` symlink here for Claude Code and Codex | Rules: a skill restates a rule beside its ID, the rule itself is in `resources/` |
| `docs/` | How the repo works: tools, formats, publishing, building | Facts about Steam or the layouts |
| `resources/` | Rules, assumptions, vocabulary, the JSON format | Anything dated: that is a finding |
| `plans/` | `<date>-<slug>.md`, written before the work | Results |
| `findings/` | `<date>-<slug>/`, written during and after. Each build's builder and installer live here too | Later rewrites: a record stays as written |
| `archived/` | What nothing uses any more, with a row in its README | Anything a tool, test or builder still loads |

`out/` and `.venv/` are local and ignored by Git.

## Where a new file goes

| You have | Put it in |
|---|---|
| A new release | A new build folder under `findings/`, a snapshot under `versions/<controller>/<v>/` for each controller that changed, `tests/test_scenarios_<v>.py`, and a CHANGELOG section |
| A check that should run on every build | `steam_layout/` for the logic, `tools/audit_*.py` for the command, a rule row in the Definition of Done |
| A fix the installer should apply | `steam_layout/fixes/`, and the pipeline list in its `__init__.py` |
| A rule, or an accepted exception to one | `resources/Layer Definition of Done.md`; the exception in `steam_layout/flow_config.json` |
| Something Steam does that the layout relies on | A row in `resources/Steam Behaviour Assumptions.md` |
| A plan, or the record of an investigation | `plans/<date>-<slug>.md`, or `findings/<date>-<slug>/` |

## Documentation

| Page | Read it for |
|---|---|
| [docs/tools.md](docs/tools.md) | Every script, the library's modules, and how to run the tests |
| [docs/building.md](docs/building.md) | How the layouts are generated, and the chain of builders |
| [docs/publishing.md](docs/publishing.md) | The steps of a release, the tags and the release pipeline |
| [docs/file-formats.md](docs/file-formats.md) | JSON and VDF, and the exporter |
| [docs/runtime-ids.md](docs/runtime-ids.md) | How Steam numbers sets and layers, and the list-order hazard |
| [docs/reading-guide.md](docs/reading-guide.md) | What each document in `resources/` covers, and the findings worth reading first |
| [skills/README.md](skills/README.md) | The six skills |
| [archived/README.md](archived/README.md) | What was retired, when and why |

## Conventions

- **Run from the repo root.** The tools are modules (`python3 -m tools.<name>`),
  and the tests import them that way.
- **Edit layouts as titles.** `python3 -m tools.convert_runtime_ids to-titles`
  turns numeric runtime IDs into `{{Base::Title}}` tokens; `to-ids` turns them
  back before export ([runtime IDs](docs/runtime-ids.md)).
- **Rules have IDs.** R101 and up are rules, A1 and up are assumptions about
  Steam. A test checks that every ID named in the README, `docs/`,
  `resources/`, the skills and the code exists.
- **Dated records are frozen.** A plan or a finding says what was known and run
  that day. Paths and commands in them are as they were then; the scripts were
  at the repo root until 2026-10-03.
- **Every changed layout ships with its VDF, a version bump and a snapshot**
  ([publishing](docs/publishing.md)). Each controller has its own version;
  pushing a tag `<controller>-v<version>` publishes it.
