# Rule registry and an automated definition of done

**Status, 2026-10-02:** in progress. The author said to implement it on
2026-10-02, slowly, one step at a time, with nothing breaking. Reviewed against
the repo the same day; the review's changes and the author's answers are
folded in (see [Decisions](#decisions)).

| Phase | State |
|---|---|
| 1. Inventory | Done: [findings/2026-10-02-rule-inventory](../findings/2026-10-02-rule-inventory/README.md) |
| 2 to 5 | Not started |
| Parts B and C | Not started; each waits for the author's review of the part before it |

**Baseline:** commits `601b61b` (archive) and `1fa38ac` (90.11 to 90.13, the
Cleanup audit, the hidden-exit prototype). The working layouts are 90.13, the
build audit is clean and the 321 tests pass.

## Why

The layout's rules are enforced in five ways (audits, the fix pipeline, tests,
builder guards, Deck checks) and written down in many places. Nothing ties a
rule to what checks it. On 2026-10-02 that caused real problems:

- **Rules are scattered and go stale.** "Keeper" is defined only in a findings
  README. The 09-30 Lean builder still says Steering keeps turn assist, which
  stopped being true in 90.13.
- **Information nobody reads.** The Flow audit's "varies" entries pointed
  straight at the Fallback Hold bug, but they don't fail anything.
- **Fixes change things nobody decided.** In 90.13 the `window_routes` fix
  dropped binds from the Steering stick Double Tap windows. It was harmless,
  and it was only noticed by diffing.
- **Exceptions are scattered:** in prototype code, in
  `steam_layout/flow_config.json`, in to-dos.
- **Tests pin counts, not rules.** At least 11 assertions pin a
  release-specific number ("71 layers", "69 targets") and break on every
  release without catching anything. `grep -rn "assertEqual(len(" tests/`
  finds 59 length checks; many of those are legitimate.
- **Deck checks pile up unrun.** `manual-testing.md` holds 137 checks in 17
  sections and none is ticked. The runtime facts the layout depends on came
  from the author playing, not from the checklist.

## Two words this plan depends on

- **Rule:** what our layout must do. Example: a layer may not cover the exit
  of the layer it sits on unless it removes that layer there.
- **Assumption:** what we believe Steam does. Example: a layer added over a
  stick that is already held still gets that stick's Release. Some are
  verified on the Deck, some aren't. A rule can rest on assumptions.

## The goals

**1. One rule list.** Every rule has:

| Field | Example |
|---|---|
| ID | R12 |
| One plain-English statement | A layer that can land on top of another may not cover an exit on what keeps the lower layer alive, unless it removes the lower layer there |
| One example from the layout | `L1: Modifier 0` under `RTP: Double Tap`: let go of L1 inside the window and the modifier stays on |
| Decided by, and when | Author, 2026-10-02 |
| Checked by | An audit check, a fix, a unit test or a scenario test, by name |
| Rests on | The Steam assumptions it depends on, by ID |
| Exceptions | Touchpad pairs, with a reason and a to-do |

**2. A fully automated definition of done (author, 2026-10-02).** No Deck
checks in it. Everything it asks for is checked by a script that runs against
the layout. Two things make that possible:

- **Scenario tests:** press-by-press tests ("hold the stick up, tap Start, let
  go: which layer gets the Release, what is on the stack, which keys are down")
  run by a press simulator against both working layouts.
- **An assumptions document:** what the tools assume Steam does, one entry
  each, verified or not, with what depends on it. The Deck is used only to
  settle an assumption, once (again after a Steam update), never per layer or
  per release. When an assumption is settled, the simulator and the tests
  that rest on it follow.

**Done on an unverified assumption (author, 2026-10-02).** A layer whose
scenario tests pass is done, even when they rest on a Steam behaviour nobody
has checked on the Deck. The release record names each unverified assumption
the release rests on. Example: the Fallback Hold relies on the stick's Release
firing in a layer that was added while the stick was already held up (Deck gate
G3, never run); its release record would say so. This is how 90.10 to 90.13
shipped.

## Ground rules for every step

"Nothing breaking" means each step ends with all of these, and is its own
commit:

1. `python3 audit_build.py` is clean.
2. `python3 -m unittest discover -s tests` and `node --test tests/*.mjs` pass
   (321 and 8 tests at the baseline).
3. The working layouts are byte-identical to the 90.13 snapshot, JSON and VDF.
   The file names differ, so the check is:

   ```sh
   for v in default alternative; do for e in json vdf; do
     cmp neptune/single-set-${v}_hold-gyro_latest.$e \
         versions/neptune/90.13/single-set-${v}_hold-gyro_90.13.$e
   done; done
   ```

   No step in this plan changes a layout. A layout bug found along the way
   becomes its own release, outside this plan, and the baseline moves to that
   release.
4. Docs and code change in the same commit when they describe the same thing.
5. No Deck check is deleted until its replacement exists: a scenario test, a
   static test, an assumption entry, or a recorded reason it is obsolete.
6. The author reviews at the end of each part before the next one starts.

## Order of the parts (author, 2026-10-02)

Part A (the rules), then Part B (cleanup), then Part C (automated testing).
Part B fixes the incidents listed under "Why" and needs only Part A. Part C is
the largest and least certain part, so it goes last.

## Part A. The rules

### Phase 1. Inventory (read-only)

List every rule and every Steam assumption wherever it lives today, without
changing anything:

| Where | What's there |
|---|---|
| `resources/Layer Definition of Done.md` (593 lines) | The checklist, by section |
| `resources/Steam Input JSON Structure.md` (1,802 lines) | Rules mixed with explanations of Steam behaviour, and the held-input rules |
| `resources/Cleanup Functions.md`, `Stateful Layer Transitions.md`, `Layout Vocabulary.md`, `Layer Reverse Lookup.md` | Definitions and design rules |
| The four skills in `.claude/skills/` | Restated rules (three entries per input, banned activators, execution order) |
| `.cursor/skills/` | A second, older copy of those skills (found by the inventory) |
| Findings READMEs and plans | Decided rules (the six cleanup rules, the keeper rule, the temporary-guard rule) and listed assumptions and Deck gates |
| `todos.md` | Decisions recorded inside to-dos |
| `steam_layout/flow_config.json`, `traced_stacks.json` | Accepted exceptions |
| The audits and fixes (`audit_*.py`, `steam_layout/*.py`, `steam_layout/fixes/`) | What each check enforces, and exemptions written into the code (deliberate clears, the stick-touch trio, `hold_layer` left out) |
| The tests | Rules that exist only as an assertion, and the rule each updated test cites |
| The four builders' comments | Rules as they stood when each was frozen |
| `manual-testing.md` | 137 Deck checks, many of them assumptions in disguise |
| My memory notes (outside the repo) | About 20 notes; several are rules or Steam facts (chords latch, held inputs, temporary guards) |

Each statement is sorted as a rule or an assumption (see the definitions
above). Some docs call a Steam fact a rule; for example "a source in a
different mode blocks inheritance" is an assumption, verified by the author.

Output: `findings/<date>-rule-inventory/README.md` with two tables. Rules:
statement, every place it appears, decided by and when, what checks it today,
flags for duplicates, conflicts and stale text. Assumptions: statement,
verified or not and by whom, where it is written, which rules rest on it.

### Phase 2. The registry document

The rule list lives in the Layer Definition of Done (decision 1). Each rule
there gets an ID (decision 2) and its fields, in one fixed table shape that a
test can read. The first commit of this phase fixes that shape and adds the
test that reads it; rules are filled in after.

Other docs keep their explanations but point at rule IDs instead of restating
the rule. The skills are the exception: an agent needs the rule in front of
it, so a skill keeps a one-line statement next to the ID, and a test checks
that the ID exists. My memory notes are treated the same way (decision 3).

An exemption written into a check (deliberate clears, the stick-touch trio,
`hold_layer` left out) is part of the rule: it goes in the rule's statement as
a clause, with who decided it. It is not an exception (phase 4).

"Rests on" stays empty until phase 10 gives the assumptions their IDs.

Add the missing terms to the Vocabulary: exit, keeper, cover, pair.

Also in this phase, as rules with IDs: the three entries proposed on
2026-10-02 (the hidden-exit rule in §7, the temporary-guard row in §8's "When
to block" table, the Vocabulary terms).

Docs only, plus the two tests.

### Phase 3. Tie the code to the IDs (no behaviour change)

- Each audit check and each fix declares the rule IDs it enforces.
- Audit output prints the ID next to each finding.
- A consistency test, in both directions: every check names a rule that
  exists, and every rule's "Checked by" matches what the code declares or the
  rule is on a "not checked yet" list. Part C works that list down; phase 15
  makes it empty or explicitly accepted.

One audit per commit. Tests that read audit output change with it.

### Phase 4. One exceptions register

An **exception** is one accepted finding: a place where the layout breaks a
rule and the author accepted it, with a to-do that ends it.

Move every exception into one file, extending `flow_config.json`: rule ID,
scope, reason, decided by and when, and the to-do that ends it. Today there
are four shapes in two files (`decisions`, `covers.allow` and `cleanups.keep`
in `flow_config.json`, and `targets` in `traced_stacks.json`) and one entry in
all: the accepted decision for the two Steering stick modifiers. The touchpad
exception moves here from the prototype. One entry can cover several inputs
with one reason, as the existing decision does.

A test fails on an exception with no reason; the audits already report
exceptions that no longer match anything.

### Phase 5. Tests that check rules, not counts

First classify the 59 length checks:

- a count that is the rule itself (three entries per input, say);
- a count on a frozen snapshot or a made-up layout, which never changes;
- a release-specific count on the working layouts.

Replace only the third kind (at least 11), one file per commit. Each
replacement must still fail on the mistake the count was catching, or the
count is deleted when another assertion already catches it. Examples:

- `tests/test_fixes.py` checks "71 layers" on the line after it checks that
  the two removed overlay layers are gone. The count adds nothing and goes.
- `tests/test_flow_inheritance.py` pins "69 targets". It becomes "every layer
  is a target except the two `hold_layer` ones", computed from the layout.

**End of part A: author review.**

## Part B. Cleanup

### Phase 6. A change report between two releases

A standalone script diffs two layout files by layer and input (before and
after) and writes the result into the release's findings folder. Run it on the
last snapshot in `versions/neptune/` and the working layout. It isn't built
into `install_neptune.py`: there are three of those, one per build folder, and
a hand edit never goes through them.

§10 gains a line: read it before shipping. Unit tests on tiny made-up layouts.

### Phase 7. The hidden-exit check (needs author approval)

Move the prototype into the Cleanup audit as a seventh check, using the
registry's rule ID and the exceptions register. Only after the author approves
building it. The touchpad fixes stay a separate to-do.

A **pair** is a lower layer plus a layer that can sit on top of it and covers
one of its exits (example: `Tab` under `L1: Double Tap`). On 90.13 the
prototype reports 0 findings outside the touchpad exception, 68 touchpad pairs
and 2 information pairs. The touchpad exception enters the register as one
entry in the same commit as the check, so the build audit stays clean.

### Phase 8. Information that nobody reads

Three outputs fail nothing today:

- **varies** (Flow audit): a layer inherits an input, and two or more
  different bindings from layers above Base can reach it.
- **review** (Flow audit): a layer inherits one such binding on some stacks
  and Base's binding, or nothing, on others.
- The hidden-exit check's Information list.

**Decided (author, 2026-10-02): on a changed layer, each entry fails the
build until it is fixed or accepted** with a reason in the exceptions
register (decision 4).

- **Changed** means the change report (phase 6) lists the layer, or the layer
  is new, compared with the last snapshot. An entry is in scope when its
  target layer changed or a layer that provides one of its bindings changed.
  At the 90.13 baseline nothing is changed, so the build audit stays clean
  when this lands.
- **Accepting isn't blocking.** Inheritance stays the default for an ordinary
  layer. The acceptance records that the entry was read, and why it is fine.
- **Cost, measured on 90.13 (default):** 94 "varies" entries, 82 of them on
  cover layers and 12 on six other layers (the two stick guards, the two
  Steering stick modifiers, the two Fn layers). 57 "review" entries, 17 on
  cover layers and 40 on 22 other layers, two to four each. The alternative
  has 92 and 53.
- **Cover layers (proposed in review, not yet the author's):** a cover
  inherits its owner, so different bindings below it are expected, and the
  cover check already judges it. Their entries are accepted by that rule as
  one register entry, not one by one. Without this, changing one Tap Cover
  brings 15 to 18 failures.

### Phase 9. Stale text

Fix what the inventory flagged as stale. Frozen builders aren't edited: their
hashes are recorded in later manifests. The registry notes where a frozen
builder's comment no longer holds.

**End of part B: author review.**

## Part C. Automated testing instead of Deck checks

### Phase 10. The assumptions document

A new document (decision 5) where each Steam assumption gets:

| Field | Example |
|---|---|
| ID | A3 |
| Statement | A layer added over an input that is already held doesn't fire its immediate layer command on that input; its delays and repeats still fire |
| Status | Verified by the author, 2026-09-29 / unverified / refuted |
| The layout | Relies on it / must work either way |
| How to verify on the Deck | One short procedure |
| What rests on it | Rule IDs, simulator behaviours, scenario tests |

"Must work either way" marks an unverified assumption the layout doesn't lean
on. Example: held-input rule 3 (removing a layer fires the exposed binding on
a held input). Every layer command that needs it also repeats, so the layout
works whether rule 3 holds or not.

Seeded from the inventory. Known entries include:

- **Verified by the author:** held-input rules 1 and 2, which cover layer
  commands only; a layer that binds a button mid-delay eats the delay; chords
  latch until the bound button is released; a normal outer-edge Release is
  reliable on a D-pad stick, an inverted centre bind isn't; the desktop
  configuration drops entries after the third; re-adding an active layer
  doesn't move it; Long and Double Press misbehave with layers; a fresh VDF
  load can swap layers when the list order and the Preset numbers disagree; a
  source in a different mode blocks inheritance.
- **Unverified:** removing a layer fires the exposed binding on a held input
  (held-input rule 3); a key output fires on an input that is already held
  when its layer is added (the author's experience, not tested on its own); a
  delay's clock starts when its layer is added, not at the physical press; a
  stick edge's Release fires in a layer added while the stick was already out
  (stick guards, Fallback Hold; the same on a button is established); a delay
  starts again when a removal exposes it under a held button; analog sticks
  inherit through the middle of the stack.
- **From the archived replay's timing contract**
  (`findings/2026-09-30-stack-search/TIMED-MODEL.md`, five policies), to be
  sorted the same way. Two aren't listed above: a repeat keeps its schedule
  when another layer is removed, and entries due at the same moment run as one
  batch.

Then fill in each rule's "Rests on". Docs only, plus a test that every
assumption ID named elsewhere exists. Memory notes that hold a Steam fact keep
a one-line statement next to its ID.

### Phase 11. Sort the 137 Deck checks (read-only)

This comes before the simulator because it decides what the simulator has to
model.

First give every check an identity. 62 of the 137 have no ID (everything from
"Menu buttons" down), and eight IDs are used twice (C1 to C4, D1, D2, D4, T1:
C1 is the Modifier 2 stick touch in 90.12 and the fallback pulses in 90.6).
Number the unlabelled ones without changing their wording, and identify each
check by section plus ID.

Then sort each check:

| Becomes | When | Example |
|---|---|---|
| A scenario test | It asks which layer gets an input, what is on the stack, or which keys are down | 90.11 F8, 90.13 N2, 90.10 T5 |
| A static test on the layout | It asks what a binding or a setting is, with no presses | "each cursor-entry input has exactly three entries", "precision speed 750" |
| An assumption entry | It really tests what Steam does; duplicates merge into one entry | 90.10 G3, 90.11 F4 |
| A tuning note | It is about feel (a 1.5 s exit, pulse strength); kept in the assumptions document as a list to try, not a gate | 90.6 C1's pulse timing |
| Obsolete | A later release replaced the behaviour; recorded with that release | 90.10 D2 (replaced by F1 to F5) |

For each scenario test, list what the simulator must model to run it. The
freshest checks already need more than buttons and stacks: rolling the stick
from up to A (F1), pulses and the beep (F1, F2), turn assist and gyro (N1,
N4), the desktop configuration (F9). What won't be modelled is re-sorted as an
assumption or a tuning note.

Output: `findings/<date>-deck-check-sorting/README.md`, one row per check,
which later becomes the migration record. `manual-testing.md` changes only by
gaining IDs.

### Phase 12. The press simulator

`walk` in `steam_layout/stacks.py` replays presses and releases and tracks the
stack. It fires the topmost layer's binding for an input. It doesn't track
which buttons are held, doesn't choose between a chord and a Regular Press,
has no time, delays or repeats, and doesn't log key output. The modifier
rocking tests use it.

**Step 0: read the archived replay and record what is reused.**
`archived/exhaustive-stack-search/steam_layout/` holds `timed_spec.py`,
`timed_model.py` and `timed_trace.py`, archived in `601b61b`. They replay
press, release, wait and analog events with a clock per activator, delays,
repeats, removals restarting delays, chord selectors and mode shifts. They
have no key-output log and predate the author's 2026-10-01 facts (chords
latch, an override eats a delay). Two earlier plans ruled out numeric clock
simulation (the 09-30 cleanup generator, the 10-01 intended flow). That was
for the audits and the exhaustive search. This simulator replays one scripted
sequence and searches nothing; the audits stay untimed.

Then build in small steps, to the scope phase 11 set. Each modelled behaviour
names the assumption ID it relies on, and gets unit tests on tiny made-up
layouts:

1. Held buttons, and choosing the activator from them: chord or Regular Press,
   Any or All masks. Chord settings are already decoded by `chord_condition`
   in `steam_layout/flow_model.py` (legacy `chord_button` IDs and masks); the
   simulator reuses it.
2. An output log: which keys and mouse buttons are down after each step.
3. The held-input rules: what fires when a layer lands on, or leaves, an input
   that is held.
4. Time: an event clock for `delay_start`, repeats, Always On timeouts, a
   delay eaten by an override, and removals restarting delays.

The simulator is a new entry point next to `walk`. `walk` keeps its signature,
and the modifier rocking tests pass unchanged at every step. As a cross-check,
the rocking sequences replayed in the simulator give the same stacks as `walk`.

Unverified assumptions (decision 7): one the layout relies on is modelled as
stated, and the test report lists the scenarios that rest on it. One the
layout must work either way under is run both ways, and both must pass.

### Phase 13. The scenario test suite

Small Python helpers (`hold`, `press`, `release`, `wait`, `expect_stack`,
`expect_keys`) inside the test suite (decision 6), run against both working
layouts. Each scenario names the rule IDs it checks and the assumption IDs it
rests on. Start with the freshest checks that phase 11 sorted as scenarios,
from 90.11's F1 to F11 and 90.13's N1 to N4. Example, F8:

> Hold the stick up with no driver; tap Start. Expect: Tab typed once, W still
> down, no menu layer on the stack, the Fallback Hold still on top.

The test report lists every scenario that rests on an unverified assumption.
That list is what the release record carries (goal 2).

### Phase 14. Migrate the 137 Deck checks

One `manual-testing.md` section per commit (17 sections), following the
sorting from phase 11. Each check becomes a scenario test, a static test, an
assumption entry, a tuning note or an obsolete record.

The migration record maps every check, by section plus ID, to where it went,
so nothing is lost quietly. At the end `manual-testing.md` is retired; the
assumptions document carries the Deck procedures.

### Phase 15. The definition of done becomes automated

- Every Deck mention in the definition of done goes: the contents table, the
  held-input note in §4, §10 Ship it ("A Deck section is added to
  manual-testing.md", "what the Deck checks are for"), §11's "Deck validation
  is pending" and "Test and Deck checklist", and the open-questions note.
- §10 gains: scenario tests cover the new layer's press sequences, every new
  Steam assumption is in the assumptions document with what rests on it, and
  the release record lists the unverified assumptions the release rests on.
- §10 keeps a line on what the checks don't prove: scenario tests cover the
  sequences that are written down, not every interleaving or timer race.
- Each rule's "Checked by" names an audit check, a fix or a test. A rule with
  nothing to check it is a to-do for a test, listed in one place.
- The `steam-layout-apply` skill and the README stop pointing at Deck
  sections.

**End of part C: author review.**

## Not in this plan

- Folding the four builders (09-29 baseline, 09-30 Lean, 10-01 Stateful,
  10-02 Fallback Hold) into one. It needs its own plan, with "the output is
  byte-identical" as its acceptance test.
- Driving real Steam automatically (injected controller input, reading keys
  back). Unproven here and a project of its own.

## Decisions

Decided by the author on 2026-10-02:

- **Decision 1. Where the rule list lives.** The Layer Definition of Done
  itself, with IDs and fields added, in one fixed table shape that a test can
  read.
- **Decision 4. The "needs review" list.** Failing: on a changed layer, each
  entry fails the build until it is fixed or accepted with a reason (phase 8).
- **Decision 8. Order.** Part A (rules), Part B (cleanup), Part C (automated
  testing).
- **Decision 9. Done on an unverified assumption.** Done, and listed in the
  release record (goal 2).

Settled in the review, not yet confirmed by the author:

- **Decision 2. ID scheme.** `R` plus a number for rules (R12), `A` plus a
  number for assumptions (A3). No section number in the ID, because sections
  move (phase 15 rewrites §10 and §11). Never reused or renumbered; a retired
  entry keeps its ID, marked retired.
- **Decision 3. Memory notes.** Rules and Steam facts that live only in my
  memory notes move into the repo. The note keeps a one-line statement and its
  how-to-apply next to the ID, for the same reason a skill does.
- **Decision 5. The assumptions document.** A new
  `resources/Steam Behaviour Assumptions.md` that replaces
  `manual-testing.md` at the end of phase 14.
- **Decision 6. How scenario tests are written.** Small Python helpers inside
  the test suite, so they run with the other tests and need no new tooling.
- **Decision 7. Unverified assumptions in the simulator.** Relied on: modelled
  as stated and listed. Must work either way: run both ways (phase 12).
- **Decision 10. Cover layers in the "needs review" list.** Accepted by the
  cover rule as one entry (phase 8).
