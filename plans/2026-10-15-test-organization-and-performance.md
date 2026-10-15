# Plan for test organization and performance

**Status, 2026-10-15: proposed.** This review covers the current working tree,
including the pending 90.71–90.74 work. No test, layout, builder or production
code has been changed. The accompanying [file inventory](2026-10-15-test-inventory.csv)
accounts for every active test file and the archived test files.

Organize tests by what they prove, make their fixture source explicit, and
compute each expensive observation once for all assertions that examine it.
Keep independent calculations where the comparison itself is the test.
Start with duplicate execution and shared preparation; moving files alone
will not make the suite faster.

## Existing documentation governs the change

| Existing source | Requirement for this enhancement |
|---|---|
| [Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md), especially §10 | Preserve R150's four audits, R152's fixed-point check, R154's invariants, R156's current-builder comparison, and the scenario and assumption checks R165–R167. Exact test names in “Checked by” are executable references. |
| [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md) and [publishing](../docs/publishing.md) | Preserve `rests`, `either`, both variants, assumption combinations, and release reports. Simulator success does not verify Steam behavior. |
| [README](../README.md), [tools](../docs/tools.md#running-the-tests), [building](../docs/building.md) | The existing convention is flat `tests/test_*.py`, release-named scenario files, `unittest`, and explicit Node commands. Changing paths and discovery requires updating these instructions together. |
| [Fourteen stale tests](2026-10-11-the-fourteen-stale-tests.md) | Its completed status corrects its original proposal: R156 stays on the working layout and matching builder. Historical assertions remain separately covered. Rewritten checks were demonstrated to fail on broken inputs. |
| [Repository reorganization](2026-10-03-repo-reorganization.md) and [reading guide](../docs/reading-guide.md) | Put durable instructions in `docs/`, keep the README short, and preserve dated records in `findings/`. |
| [Archive policy](../archived/README.md) and [retired fallback scenarios](../archived/fallback-window/README.md) | Archived tests remain historical records, outside active discovery. The frozen static tests of 90.31/90.32 remain active. |
| [Controller directories and release pipeline proposal](2026-10-15-controller-dirs-and-release-pipeline.md) | Coordinate fixture loading with that separate proposal. Do not delete snapshots, change storage, introduce controller ports or implement its release workflow here. |

Historical fixture sources are not interchangeable. Some established engine
regressions read `versions/neptune/`; newer frozen behavior tests read findings
candidates or execute frozen builders. Retain each test's existing source and
purpose. In particular, 90.39 is a separate candidate with local rules, and
trial versions are not automatically the live lineage.

## Inventory and evidence

The active Python suite has **121 files, 1,333 authored test methods and
1,333 collected test instances**. There are **two Node files with eight tests**.
The Python files contain 22,443 lines, excluding the scenario support module.
The inventory divides the review into:

| Area | Files | Python methods |
|---|---:|---:|
| Release and feature scenario modules | 58 | 527 |
| Scenario registry and 90.64 layer-order checks | 2 | 20 |
| Core engines, audits, tools and registry checks | 19 | 429 |
| Feature contracts, historical builders and probes | 42 | 357 |
| Total active Python | 121 | 1,333 |

Of the 527 methods in scenario modules, **441 have scenario metadata and 86
are ordinary static, delta or walk tests**. Of the decorated methods, 102
explicitly name a frozen release; 30 use the separate 90.39 candidate harness.
Module names and decorator defaults alone therefore cannot determine fixture
ownership. Several modules mix live checks, frozen checks and exact historical
diffs. The migration must classify individual checks before splitting them.

There are also **44 archived Python test files**: 35 exhaustive-search files,
five depth-search/family-walk files, two capped-walk/old-engine files and two
retired fallback scenario files. They are accounted for but are not active
coverage to migrate or silently reactivate.

Validation performed for this plan:

- Collection of all 121 Python modules found 1,333 test instances.
- Both Node files passed: eight tests, approximately 0.29 seconds.
- A focused run of `test_native`, `test_audit_inheritance.NeptuneLayoutTests`,
  `test_audit_build`, `test_audit_command_budget` and `test_rule_registry`
  passed all 62 tests in **23.298 seconds**, including import/setup overhead.
- The two current Window report tests took **3.380 and 3.359 seconds** in
  their bodies. They independently audit the same two variants/configuration.
- The native Python-reference comparison took **6.899 seconds**. Its separate
  algorithms are intentional coverage, not redundant work to remove.
- A full run was started and interrupted after several minutes, during
  `test_cleanups.FixedSnapshotTests.test_the_audit_is_clean_after_the_fix`, inside
  `cleanup_lists.fix` → `Cleanups.present` → backward-chain replay. There is
  **no completed full-suite baseline or full-suite pass from this review**.

These are local observations, not portable performance targets. The “701 tests
in a little over five minutes” in `docs/tools.md` is dated 2026-10-04; the
later stale-tests plan describes a roughly 40-minute suite. Measure the
current full run before making a total speedup claim.

The focused run used Python 3.9.6; Node was v26.7.0. Reproduce its selection
from the repository root with:

```bash
PYTHONPATH=.:tests python3 -m unittest tests.test_native tests.test_audit_inheritance.NeptuneLayoutTests tests.test_audit_build tests.test_audit_command_budget tests.test_rule_registry
node --test tests/test_convert_vdf.mjs tests/test_steering_observer.mjs
```

## Documented test pattern

Add `docs/testing.md` as the durable home for the following pattern. Link it
from the README, reading guide and tools guide, and update the Definition of
Done's test-path instructions when discovery changes.

Each test module or class declares:

1. **Contract:** the behavior, invariant or rule it protects.
2. **Fixture:** synthetic, current controller/variant, exact frozen source,
   separately named candidate, or actual builder output. Declare rules and
   baseline where relevant; a release in the filename is not enough.
3. **Execution matrix:** variants, initial stack, input sequence, timing,
   desktop transformation, assumption switches, seeds and engine options.
4. **Observation:** the report, chain analysis, native result or simulator
   trace whose cost is paid once for that exact case.
5. **Assertions:** focused named checks of that observation, with variant,
   release, rule, input and option labels in failures.

Prefer separate test methods reading a shared class/module observation when
they protect separately named contracts. Within one behavioral case, group
related assertions after one execution. Use labeled `subTest` blocks for
independent observations so one failed assertion does not hide all the rest.
Keep prerequisite checks explicit before indexing a report or trace.

Existing examples worth documenting:

- `test_cleanups.SnapshotTests` prepares historical audit reports once and
  exposes them to nine checks; `test_required_cleanups.SnapshotTests` similarly
  shares reports across six checks.
- `test_modifier_rocking` walks one concrete sequence and checks intermediate
  stacks, resolving owners, final cleanup and cover ordering.
- `test_steering_touch_windows` checks both report success and exact blocked
  contexts from one report. Its deliberately broken layouts are separate cases.

Do not replace exact keys, output order, stored command order, paths or failure
reasons with a generic `ok` assertion. Do not merge different gestures simply
because they finish on the same stack.

### Proposed directory structure

Keep `unittest` and Node's existing test runner. Introduce explicit packages
and canonical imports; a framework migration is unnecessary for these gains.

```text
tests/
  support/                  # fixture loaders, toy builders, observations, IDs
  unit/                     # small synthetic model, audit and simulator cases
  contracts/neptune/        # invariants of the current working layouts
  releases/neptune/         # frozen shapes, exact deltas, builder reproduction
  scenarios/neptune/        # press sequences; retain test_scenarios_90_<n> names
  scenarios/candidates/     # separate 90.39 source/rules and similar experiments
  integration/              # CLI, native parity, reports, registry integrity
  node/                     # exporter and observer tests
```

Directories express responsibility, not cost. Some current contracts and
historical checks are expensive; some integration tests are tiny. Keep
synthetic engine cases separate from the real-layout native parity cases.
Split mixed modules by class/check only after recording their old identities.
The inventory names intended homes rather than treating every file as an
indivisible move.

Release scenario labels such as `90.74 F1` remain stable, as do rule IDs,
assumption IDs and frozen-source metadata. Retaining release-based filenames
preserves the established link to build records. Current structural contracts
get descriptive feature names; exact historical diffs stay under releases.

## Performance work in priority order

### 1. Execute scenarios once and collect their evidence

`tests/scenario.py:reached()` builds a second suite with
`loadTestsFromModule` for every scenario module. It executes all **527**
methods, including the 86 non-scenario tests, using a private `TestResult`.
The normal suite then executes those modules too. The registry's reach setup
and release-list test can trigger this hidden run. `_ran` prevents another
private run; it does not account for execution by the outer test runner.

Separate metadata discovery, scenario execution, reach accumulation and report
rendering. A full-suite runner should execute each selected scenario once,
record its outcome and reach, then run the R165 coverage finalizer. Registry
and report-format unit tests should consume explicit records instead of
launching the whole scenario suite as setup.

Preserve standalone `python3 -m tests.scenario` and targeted registry checks:
when they need reach evidence, explicitly execute the complete required
scenario selection once. Never infer completeness from a nonempty `REACHED`
dictionary. Track expected IDs, completed outcomes and fixture identity;
missing cases and unexpected failures must surface. Preserve expected-failure
behavior explicitly rather than letting an ignored result imply success.

Live, frozen and candidate reach records must remain separate. Keep the
90.39 harness's candidate rules/source isolated. A cached or partial run from
another fixture must never satisfy the live R165 check. The existing R165
automated check only establishes layer reach: human review still checks held
inputs, presses inside a layer and missed releases.

This removes redundant executions, not scenarios, seeds, input combinations or
assertions. Regular static and walk checks still run once in their own group.

### 2. Reuse exact reports and native results

| Current repetition | Change | Coverage to retain |
|---|---|---|
| `test_audit_inheritance` runs the same live Window audit in the undecided-route and window-coverage tests | Prepare one report per variant/configuration; retain separately named assertions | All windows, exact contexts, both variants; fresh runs for timing, changed config and mutated layouts |
| `test_cleanups.found()` calls the audit again whenever a test wants another projection | Compute one local report; use pure selectors for finding pairs/details/status | Finding reason, inputs, path and overall status; new report for every different mutation/config |
| Native snapshot path replay and historical tap-cover tests each call `covered_exits(3)` | Share decoded pairs together with that invocation's `walked` summary | Every path replay, minimal stack/cost and the specific regression pair |
| Native thread comparison and batch/path comparison each create the same default raw baseline | Share that default result | Execute `threads=1`, no paths, small batches and their combination independently; keep wrapper checks and Python-reference runs |
| Hygiene and some CLI tests rerun the same check only to inspect another field/output line | Share the exact report or captured process result | Keep real exit-code, invalid-input, write-protection and option tests |
| Static scenario checks repeatedly scan identical inventories (`90_69`, `90_70`, `90_61`, `90_62`) | Prepare rows/partitions once per exact source and variant | Exact counts, inside/outside-Steering assertions and historical delta checks |

Begin at existing API boundaries. Sharing raw native output and decoded
cleanup pairs through one new abstraction is a later step if needed; do not
bypass `covered_exits` wrapper coverage just to reduce subprocesses.

### 3. Share fixture preparation without sharing mutable test state

- Extract toy builders and helper functions from `test_audit_inheritance`,
  `test_chains`, `test_flow_inheritance`, `test_cleanups` and feature test modules
  into `tests/support/`. Preserve whether helper arguments mean execution
  order or stored order.
- Centralize the Neptune loader used by cursor, gyro, recovery and held-input
  tests. Preserve its duplicate-key detection (`unique_object`), numeric and
  readable forms, reference lookup and ordering.
- Share read-only window inventories, reference projections and historical
  builder products across consumers where their inputs and processing stage
  match. Keep a real builder execution for reproducibility; a saved candidate
  must not become both the expected and actual value.
- Historical builders already often build once per class. Measure their
  recursive construction and fix passes separately from test bodies. Do not
  remove repeated pipeline calls until proving they serve the same stage;
  mutation-stage and fixed-point checks intentionally run again.
- In `ScenarioCase.each`, an explicit `start` currently constructs a default
  `Pad` and then replaces it with another `Pad`. Select the start first so only
  one simulator is constructed. Preserve the special `start="steering"`
  entry gesture and its settling behavior.
- Cache 90.39 candidate loading and parsed fixture preparation where safe.
  Always create a fresh simulator, event queue, held-input state, log and reach
  accumulator for every gesture/matrix cell.

R156 currently removes title/description from mappings in place before its
ordered comparison. Convert that normalization to copies before sharing any
loader output. Likewise, mutation and fix tests must receive private raw data
and fresh analyses; `Layout` exposes the underlying mutable dictionaries.

### 4. Define reuse boundaries explicitly

Use bounded, in-process fixtures first. Retaining graphs for every historical
version can consume substantial memory. Do not add a persistent disk cache
in the initial implementation.

| Observation | Identity required for reuse |
|---|---|
| Source data | Controller, variant, live/frozen/candidate/builder source, exact source path/version/content, transformation and processing stage |
| Parsed layout/inventory | Source identity and parser/inventory semantics; immutable input throughout its lifetime |
| Backward chains | Layout identity, arrival allowance, contexts and foreign-arrival behavior |
| Native result | Tables and exit table, extras, landings, paths policy including `PATHS_UP_TO`, threads, memory limit and batch settings |
| Audit report | Relevant analysis identity plus effective rules/exception register, filters, changed-layer set and baseline |
| Recorded gesture | Exact fixture, start/held state, event order/times, assumption options, desktop transformation, seed and instrumentation |

Preserve dictionary/list order in fingerprints. Sorting JSON keys would erase
ordering that some tests explicitly protect. Live files must be refreshed in
a new run; if they change during a run, fail or invalidate the fixture rather
than silently mixing revisions.

`Chains.of(layout)` already caches on a `Layout` object. Repeatedly constructing
a new layout loses that benefit. **`Inventory.of(layout)` is not cached**:
`test_flow_inheritance` deliberately changes a group and calls it again to
observe different roles. Do not add unconditional memoization to that API.

`Cleanups` holds mutable configuration and caches; `covered_exits()` runs the
engine on every call and overwrites `walked`. Retain the pairs and summary as
one observation. Family cover chains use contexts and
`foreign_arrivals=False`, unlike general chains. They must stay distinct.

Bypass reuse for fresh-process/CLI behavior, compiler availability, progress
callbacks, memory-stop behavior, explicit timing, mutation, idempotence and
engine-option comparisons. An unsettled/memory-limited result must never be
accepted as a complete walk. Preserve default five-extra-press hidden-exit
coverage, all landing checks and the independent Python oracle.

The 90.58 frozen equivalence samples and live R163 clear samples are different
work: they use different sources, seeds and instrumentation. Keep all 120
equivalence walks and 240 live clear walks per variant, the bumper-sequence
matrix, and exact log comparisons. Share preparation only. Common gesture
prefixes may be shared as immutable inputs, not as mutable simulator state.
Keep 90.57's 1,280 gesture cells and the 25 individually identified
`old_inverted_chord` expected-failure scenarios; grouping must not hide an
unexpected success or change the assertion at which an expected failure ends.

### 5. Consider algorithm changes and parallelism only after measurement

An inverse index for repeated `Chains.above()` lookups is a possible later
production improvement. It requires reference tests preserving stacks,
witness/path selection and ordering; it is not necessary for the initial test
reorganization. Similarly, native engines already use threads: parallel test
workers can oversubscribe CPUs, duplicate expensive caches and multiply peak
memory. Benchmark bounded worker counts only after redundant work is removed.

## Discovery and documentation migration

Moves have dependencies beyond imports:

- The current Python shell command lists only flat files; scenario discovery
  also uses a flat glob. Add one canonical discovery mechanism, rooted only
  in active `tests/`, and make scenario/report consumers use it.
- Add package initializers and normalize bare sibling imports. Extract helpers
  before moving their test owners. Do not use compatibility modules that
  re-export `TestCase` classes into discovery and execute them twice.
- `steam_layout.rules.checkers()` accepts short test module/method references;
  registry tests resolve them to `tests/<module>.py`. The retired checklist's
  sorting record contains the same references. Introduce a resolver for stable
  test references, with explicit old-to-new mappings for splits/renames,
  rejecting missing or ambiguous targets. Keep historical prose intact.
- Make rule/assumption source scans recursive so nested tests and shared
  support remain checked. Keep existing parser and documentation-integrity
  tests, and update live “Checked by” references when names change.
- Include both Node files in the full-suite entry point. Preserve the
  exporter dependency and native compiler requirements; absence must not
  become a silent skip. Preserve fresh observer VM state.
- Retain `tests.scenario` as a working report entry point even if its
  implementation moves into support.

Document a single full command, a focused module command, and an optional
fast subset. For example, a new `python3 -m tests.run` may coordinate Python,
scenario finalization and Node; its implementation must return nonzero for
failures in any part. A fast subset is convenience, not the release gate.
Use one ordered Python suite builder from both that runner and the `tests`
package's `load_tests` hook. Verify that
`python3 -m unittest discover -s tests -t .` executes the same Python selection
and R165 finalizer, with no hidden
scenario rerun. Explicit module selections remain focused runs and must not
claim complete-suite coverage; a focused reach-check invocation explicitly
requests the required scenario selection. Update README, tools, building,
reading guide, publishing and
Definition of Done together, plus any skill commands that reference old paths.

## Implementation sequence and acceptance

1. **Baseline and coverage ledger.** Complete a fresh-process full run on a
   stable tree before changing tests. Save environment, fixture hashes,
   collected IDs, outcomes including expected failures, scenario labels,
   variants/options/seeds, rule/assumption links, and live/frozen/candidate
   reach. Time imports, class/module preparation, bodies and subprocesses;
   count chain/native invocations by exact analysis key. Record peak memory.
   Treat existing failures as baseline findings, not a reason to weaken checks.
2. **Pattern and support.** Write `docs/testing.md`; extract helpers and
   normalize imports without moving tests or changing expectations. Add
   coverage-ledger entries for shared observation ownership. Keep existing
   commands valid through this phase.
3. **Remove duplicate execution.** Separate scenario metadata/reporting from
   execution and integrate finalization. Verify standalone CLI, full suite,
   focused registry run, partial run, failed/expected-failed scenario, and
   frozen/candidate exclusion from live reach.
4. **Reuse measured observations.** Start with duplicate Window reports,
   cleanup report selectors and native baselines. Then share fixture loading,
   remove discarded `Pad` construction and reuse historical preparation.
   Keep independent test names when a class fixture suffices.
5. **Move by responsibility.** Introduce recursive discovery and stable
   reference resolution, then move one group at a time. Split mixed files
   with an explicit old-check → new-check mapping. Update documentation and
   the inventory as each group moves.
6. **Prove equivalence and measure.** Run the full suite in a fresh process,
   then compare against step 1. Investigate every missing ID/matrix cell or
   changed expected-failure status. Reproduce representative checks with
   deliberately broken input and verify they still fail. Run affected groups
   alone and in reversed/shuffled order to expose leaked shared state.

Completion requires:

- Every original assertion obligation has a mapped owner, even if method
  counts change. All 441 scenario labels and their sources/assumption matrices
  remain accounted for; newly added tests extend the ledger.
- Both variants, all specified option combinations, timing boundaries,
  seeds, negative cases, stored-order checks, CLI behaviors and Node tests
  remain covered. No new skip, expected failure or reduced walk bound is used
  to obtain a green/faster suite.
- R156 still compares current files with independently generated current
  output; historical reproducibility and R152's second pipeline pass remain.
- Documentation references resolve, nested tests are discovered exactly once,
  archive tests remain excluded, and standalone scenario reports remain valid.
- Equivalent read-only observations run once per exact key where intended;
  mutation, reference and option-diversity cases still execute independently.
- Full-suite wall time improves with no unexplained peak-memory regression.
  Compare fresh-process runs on the same inputs/machine and record native
  compilation separately; use repeated runs to distinguish noise. Set a
  numerical time target only after the complete baseline exists.

The first implementation slice should therefore be the coverage ledger,
testing guide and helper extraction, followed by the scenario execution fix
and the measured Window report reuse. Layout changes and release publication
are outside this enhancement.
