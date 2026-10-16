# Plan for test organization and performance

**Status, 2026-10-15: implemented and locally validated.**
The implementation is based on commit `c54b909e` plus the pending controller,
vocabulary and Python profile-export work present at the start. The original
suite was copied to an isolated directory before changes for comparison.
See the implementation record below and [testing guide](../docs/testing.md)
for the current commands. The proposal sections retain the baseline rationale.

**Scope:** exclude the `overlay/` directory, packaging and platform validation,
as requested. Python tests under `tests/`, including `test_overlay_profile.py`,
remain in scope. Its external workflow only receives the Python test path
updates required by the move.

Organize tests by what they prove, make their fixture source explicit, and
compute each expensive observation once for all assertions that examine it.
Keep independent calculations where the comparison itself is the test.
Start with duplicate execution and shared preparation; moving files alone
will not make the suite faster. Preserve controller, variant and conversion
stage as separate coverage dimensions.

## What changed since the first proposal

| Controller | Current version | Generation and coverage |
|---|---|---|
| Ibex | 1.0 | Base layout; independently rebuilt by the R156 test. Player Space gyro. |
| Neptune | 90.75 | Converted from the Ibex release named in its changelog; C1 checks reproduction and C3 checks the historical round trip. Yaw + Roll gyro. Neptune builders through 90.74 remain historical fixtures. |
| DualSense Edge (`dse`) | 1.0 | Converted from the named Ibex release; no stick touch, swapped grips, one whole touchpad and mute binding. C1/C5 and scenarios E1–E8 protect the conversion. Gyro mode is always on; Base retains its enable condition. |

Each has default and alternative variants: six working layouts. Registry and
conversion coverage does not establish physical-device compatibility, nor
does it mean every Neptune scenario runs unchanged on the Edge.

The release tool, four Python CI shards and all-controller audit job already
exist. JSON and VDF snapshots remain under `versions/<controller>/<version>/`;
there is no snapshot-deletion or Git-backed JSON-cache migration to perform.
Versions remain per-controller numbers such as `90.75` and `1.0`.

The pending Python profile exporter tests under `tests/` cover **Ibex 1.0
default only**. Keep that fixture scope explicit when organizing them;
controller registry membership does not extend their coverage to other layouts.

## Existing documentation governs the change

| Existing source | Requirement for this enhancement |
|---|---|
| [Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md), especially §10 and §12 | Preserve R150's four audits, R152's fixed-point check on all six layouts, R156/R177's builder and conversion checks, R165–R167, and conversion rules R178–R185. Exact “Checked by” references must still resolve. |
| [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md) and [publishing](../docs/publishing.md) | Preserve `rests`, `either`, both variants, assumption combinations, and release reports. Simulator success does not verify Steam behavior. |
| [README](../README.md), [tools](../docs/tools.md#running-the-tests), [building](../docs/building.md) | The existing convention is flat `tests/test_*.py`, release-named scenario files, `unittest`, and explicit Node commands. Changing paths and discovery requires updating these instructions together. |
| [Fourteen stale tests](2026-10-11-the-fourteen-stale-tests.md) | Its completed status corrects its original proposal: R156 stays on the working layout and matching builder. Historical assertions remain separately covered. Rewritten checks were demonstrated to fail on broken inputs. |
| [Repository reorganization](2026-10-03-repo-reorganization.md) and [reading guide](../docs/reading-guide.md) | Put durable instructions in `docs/`, keep the README short, and preserve dated records in `findings/`. |
| [Archive policy](../archived/README.md) and [retired fallback scenarios](../archived/fallback-window/README.md) | Archived tests remain historical records, outside active discovery. The frozen static tests of 90.31/90.32 remain active. |
| [Implemented controller and release plan](2026-10-15-controller-dirs-and-release-pipeline.md), [controller reference](../resources/Controllers.md), [build record](../findings/2026-10-15-ibex-base/README.md) | Follow the status and implementation corrections, including retained JSON snapshots, Ibex as base, DSE's whole-pad switches, and Base's gyro exclusion. Preserve recorded C4 evidence as historical evidence, not an active test gate. |
| [Release workflow](../.github/workflows/release.yml), [release tool](../tools/release.py), [publishing](../docs/publishing.md) | Integrate discovery with existing shards and tag/history checks. Preserve snapshot immutability after tagging, numeric version order, reproducible bundles and conversion provenance. |
| [Timed-gesture vocabulary](2026-10-15-timed-gesture-vocabulary.md) and [Layout Vocabulary](../resources/Layout%20Vocabulary.md) | Keep “Hold / Tap, then hold” distinct from a single Tap. Preserve exact technical identifiers and timing expectations when moving tests. |

Historical fixture sources are not interchangeable. Some established engine
regressions read `versions/neptune/`; newer frozen behavior tests read findings
candidates or execute frozen builders. Retain each test's existing source and
purpose. In particular, 90.39 is a separate candidate with local rules, and
trial versions are not automatically the live lineage.

## Pre-implementation inventory and evidence

At the pre-implementation baseline, the tracked Python suite had **125 files and 1,398 test methods**. Including
the pending Python profile exporter tests, the review collected **126 files
and 1,407 test instances**. There are **two Node files with eight tests**.
These totals and the inventory exclude `overlay/`.

| Area | Files | Python methods |
|---|---:|---:|
| Release and feature scenario modules, including DSE | 59 | 535 |
| Scenario registry and 90.64 layer-order checks | 2 | 20 |
| Core engines, audits, tools and registry checks | 19 | 433 |
| Feature contracts, historical builders and probes | 42 | 357 |
| New controller, conversion and release modules | 3 | 53 |
| Pending Python profile exporter | 1 | 9 |
| Total Python in this working tree | 126 | 1,407 |

Of the 535 methods in scenario modules, **449 have scenario metadata and 86
are ordinary static, delta or walk tests**. Of the decorated methods, 102
explicitly name a frozen release; 30 use the separate 90.39 candidate harness.
The remaining 317 are 309 default-controller scenarios and eight explicit DSE
scenarios. Four controller-aware exception tests were also added to the
existing exception module. Counts and pending file status must be refreshed
when the other session finishes.
Module names and decorator defaults alone therefore cannot determine fixture
ownership. Several modules mix live checks, frozen checks and exact historical
diffs. The migration must classify individual checks before splitting them.

There are also **44 archived Python test files**: 35 exhaustive-search files,
five depth-search/family-walk files, two capped-walk/old-engine files and two
retired fallback scenario files. They are accounted for but are not active
coverage to migrate or silently reactivate.

Current evidence is different from the original review. [The tools guide](../docs/tools.md#running-the-tests)
now records **1,398 tests in about 48 minutes** on this Mac. `tools.release.SLOW`
contains measured module costs for balancing four CI shards, including 573 s
for the scenario registry, 191 s for each of two builder-heavy modules, 174 s
for cleanups and 88 s for conversions. These are existing reported measurements,
not a new complete run performed for this revision.

The original review's 62-test timing and interrupted full run predate these
changes. Its duplicate Window report measurement remains a useful candidate
for profiling, not a current performance baseline. Re-measure against the
expanded suite and retain fixture/setup time in the totals.

For this revision, all 1,407 Python instances collected successfully and both
Node files passed all eight tests (about 0.31 s). The focused Python selection
below passed **97 tests in 87.310 s**, with no failures, errors or skips,
including the C2 CLI audits. No new full Python run was performed for this
revision. Reproduce the focused selection from the repository root:

```bash
PYTHONPATH=.:tests python3 -m unittest tests.test_controllers tests.test_convert tests.test_release tests.test_scenarios_dse_1_0 tests.test_overlay_profile tests.test_exceptions
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
3. **Execution matrix:** controller and variant, conversion stage, initial
   stack, input sequence, timing, desktop transformation, assumption switches,
   seeds and engine options.
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

### Directory structure

Keep `unittest` and Node's existing runner. Introduce explicit Python packages
and canonical imports.

```text
tests/
  support/                  # fixture loaders, toy builders, observations, IDs
  unit/                     # small synthetic model, audit and simulator cases
  contracts/shared/         # explicitly applicable controller/variant matrices
  contracts/{ibex,neptune,dse}/ # controller-specific invariants
  releases/{ibex,neptune,dse}/  # frozen shapes, deltas, builder/conversion checks
  scenarios/shared/         # only gestures with declared capability requirements
  scenarios/{ibex,neptune,dse}/ # retain release labels and historical provenance
  scenarios/candidates/     # separate 90.39 source/rules and similar experiments
  integration/              # CLI, native parity, reports, registry integrity
  integration/release/      # scratch Git repositories, tags and bundles
  integration/profiles/     # Python profile-export checks
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

## Controller and release contracts to preserve

| Checks | Required coverage and source boundary |
|---|---|
| `test_controllers` (11) | Registry identity, six working files, controller-specific headers/gyro styles, numeric version ordering and snapshot ownership. |
| `test_convert` (20) | Synthetic rules; frozen Ibex whole-pad intermediate stage; current C1 reproduction from the changelog's Ibex source; C2 real CLI audits on Ibex/DSE; C3 independent Neptune 90.74 round trip; C5 exact CTP model comparison; final DSE structure/gyro/mute. |
| `test_scenarios_dse_1_0` (8) | E1–E8: swipes, ring/centre clicks, key-layer handoff, mute, gyro/Base distinction, physical grips and missed-release recovery on both sticks. Preserve 60 yielded gesture cells, including both A9 outcomes in E4. |
| `test_exceptions` (four added checks) | Controller-specific exception and traced-stack views, renamed CTP inputs, absent-input applicability and Neptune-era expiry. |
| Existing current checks | R156 independently builds Ibex; C1 independently converts Neptune/DSE. R152 now runs the fix pipeline again on all six files. `test_changes` checks six default CLI reports; `test_layout_rules` still has Neptune-specific snapshot checks. |
| `test_release` (22) | Exact JSON/VDF/snapshot bytes, fresh export, version/tag ancestry and changelog, named Ibex conversion source, tagged immutability versus untagged refresh, deterministic bundles, pending tags, shard partition and real-repository integrity. |

Do not replace these with a single “all controllers pass” check. Retain the
wrong-source and absent-chord mutations, exact layer/reference ordering,
independent expected files, CLI exit/output assertions and repeated executions
that prove determinism or fixed-point behavior. Whole-pad conversion tests
protect an intermediate stage; C3 removes style fields from private comparison
copies. Neither can safely consume a mutable shared final-conversion result.

The [C4 record](../findings/2026-10-15-ibex-base/README.md#the-decks-scenarios-on-the-other-layouts-c4)
is outside the active suite. It compared Ibex and an **intermediate** Edge
conversion retaining two pads, not the final DSE product. Do not promote its
reported 53 stick-touch-dependent failures to blanket skips. A future Ibex
scenario gate should explicitly select applicable cases and record replacements
for unavailable controls, such as DSE E8's stick-edge recovery. That would be
an additional gate, distinct from preserving the existing default Neptune
scenarios and eight DSE scenarios.

## Performance work in priority order

### 1. Execute scenarios once and collect their evidence

`tests/scenario.py:reached()` builds a second suite with
`loadTestsFromModule` for every scenario module. It executes all **535**
methods, including the 86 non-scenario tests, using a private `TestResult`.
The normal suite then executes those modules too. The registry's reach setup
and release-list test can trigger this hidden run. `_ran` prevents another
private run; it does not account for execution by the outer test runner.
CI's registry shard therefore also repeats work assigned to other shards.

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

Live, frozen and candidate reach records must remain separate **per controller**.
Today `SCENARIO_CONTROLLER` selects the default at import time, live JSON is
already cached by `(controller, variant)`, and explicit DSE scenarios record
reach separately. `coverage()` and `uncovered()` still check only the default
controller; the decorator metadata itself has no controller field. Replace
mixed string/tuple reach keys with resolved execution identities. Record source
controller/release as well as target controller, variant, stage, options and
outcome. Frozen Neptune sources remain Neptune when an Ibex pass is selected.

Keep the 90.39 harness's candidate rules/source isolated. A cached or partial
run from another fixture must never satisfy the live R165 check. Extend the
finalizer to explicitly selected controller matrices and baselines, including
DSE, rather than crediting DSE reach to Neptune or silently ignoring it. During
migration, use explicit execution context or fresh processes for controller
passes; changing the environment after importing `scenario` is insufficient.
The existing R165 automated check only establishes layer reach: human review still checks held
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
| New controller tests repeatedly parse six live files and C5/structural/gyro checks rebuild readable DSE layouts | Share read-only source bundles and final-layout projections per controller/variant | Preserve independent C1 conversion, intermediate whole-pad tests, copied C3 normalization and the fresh C2 subprocess |
| Python profile exporter checks reuse the same pinned Ibex source | Share a read-only baseline export for assertions on that exact source | Keep the real repeated export for determinism, source-derived timing, unsupported-binding and altered-source/schema cases |

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
Resolve builders by controller type and version, not version alone: Ibex and
DSE both use 1.0. Conversion fixtures also identify the named Ibex snapshot,
target profile/version, variant, transformation stage and fix/rule state.

### 4. Define reuse boundaries explicitly

Use bounded, in-process fixtures first. Retaining graphs for every historical
version can consume substantial memory. Do not add a persistent disk cache
in the initial implementation.

| Observation | Identity required for reuse |
|---|---|
| Source data | Source and target controller, variant, live/frozen/candidate/builder/conversion source, exact source path/version/content, registry profile, transformation and processing stage |
| Parsed layout/inventory | Source identity and parser/inventory semantics; immutable input throughout its lifetime |
| Backward chains | Layout identity, arrival allowance, contexts and foreign-arrival behavior |
| Native result | Tables and exit table, extras, landings, paths policy including `PATHS_UP_TO`, threads, memory limit and batch settings |
| Audit report | Relevant analysis identity plus effective controller-specific exception/traced-stack views, filters, changed-layer set and baseline |
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

The same exception-register bytes now produce different effective views via
`exceptions.for_layout()` and `stacks_for_layout()`. Include those views in
report identity; DSE's absent-input applicability is not a broad audit skip.
`convert.reachable()` follows a structural add/hold graph, which is distinct
from scenario reach, backward-chain feasibility and native exit walks.

Keep release scratch repositories private to each test. Their HEAD, tags,
branches, changelog, snapshots and patched root change during a test. Avoid
caching these stateful checks; layout/version/path alone is insufficient.
Latest-snapshot lookup also depends on current directory contents, while
latest released version depends on reachable tags. Preserve real repeat ZIP
builds and fresh exporter calls, since their reproducibility is under test.

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
The existing four CI shards are retained; this caution concerns adding more
parallelism or changing how threaded native runs are scheduled within them.

## Discovery, sharding and documentation migration

Use one canonical recursive manifest for active Python tests, shared by local
collection, scenario selection and `tools.release.test_modules()/shard()`.
Do not import test modules just to calculate release shards. Exclude archives
and `overlay/`. Keep Node selection explicit in the validation matrix, separate
from Python modules passed to `unittest`.

Before moving files:

- Add Python package initializers, extract helpers and normalize bare sibling
  imports. Do not re-export `TestCase` classes through compatibility modules
  that discovery could execute twice. Keep `tests.scenario` as the report CLI.
- Update the rule/checklist reference resolver and recursive rule/assumption
  scans. Preserve old-check → new-check mappings for split modules, reject
  ambiguous targets, and retain historical prose unchanged.
- Migrate the release sharder and its partition test to the same manifest.
  Use canonical identities for timing weights when basenames cease to be
  unique. Refresh `SLOW` after splitting modules/removing hidden runs; its
  current registry weight includes duplicate scenario execution.
- Update `.github/workflows/release.yml` with the new runner, including both
  Node files. Preserve Python 3.9, Node 26, the pinned exporter/checksum,
  compiler requirements and the all-controller audit job.
- Ensure the test checkout has the tags/history needed by repository integrity
  tests. The current test job omits `fetch-depth: 0`, unlike plan/publish jobs;
  tag-based checks must not pass vacuously on missing history.
- Carry forward the existing conditional skip in the Python release exporter
  test when Node/the extension is unavailable. Record it in the environment
  baseline; the mandatory Node exporter lane must still run with dependencies
  installed. Do not turn missing dependencies into additional silent skips.

### One execution per selected case across four shards

Prefer **per-shard evidence plus one finalizer**, preserving the existing four
balanced Python jobs. The normal runner records scenario execution rather than
having registry tests start another suite:

1. Generate the complete selected-case manifest for the commit and controller
   matrix, then assign each case/module to exactly one shard.
2. Each shard emits a structured record of assigned/completed cases, outcomes,
   resolved fixture/configuration hashes, controller/variant/stage, assumption
   options and reach. Include commit and run identity; bind records to the
   expected manifest. Expected failures retain their individually identified
   status and the documented reach policy.
3. A dependent finalizer validates complete, unique evidence before evaluating
   per-controller R165 coverage and producing the release assumption report.
   Missing shards/cases, duplicates, stale or mixed fixtures, unexpected
   failures/successes and incompatible manifests fail the gate. A failed shard
   cannot be repaired by a report that merely contains enough reached layers.
4. Publishing depends on that finalizer as well as existing audit/export checks.
   Test report formatting and registry integrity with explicit fixture records;
   they must not launch the full scenario suite as setup.

The single-process full command uses the same manifest and finalizer in
memory. A `tests` package `load_tests` hook should give ordinary recursive
Python discovery the same Python selection/finalization. Focused module runs
are explicitly partial; a standalone reach/report invocation requests its
complete selection once. Until this design is implemented, keep existing
commands working rather than claiming a cache alone fixes CI duplication.

Document the local full Python/Node gate, focused commands and the optional
fast subset. Clearly distinguish full-suite validation from partial selections.

Update README, tools, building, publishing, reading guide, Definition of Done,
release sharder/tests and release workflow together with the relevant moves. Also update skill commands that reference moved paths. Add
`docs/testing.md` without duplicating controller rules or changing recorded
Steam assumptions.

## Implementation sequence and acceptance

1. **Baseline and coverage ledger.** Complete a fresh-process full run on a
   stable tree before changing tests; first refresh the pending Python test
   inventory. Save environment, fixture hashes, collected IDs, outcomes including
   expected failures, scenario labels, controller/variant/stage/options/seeds,
   rule/assumption links and live/frozen/candidate reach. Keep reported 1,398-test results,
   this review's focused results and new full-run measurements distinct.
   Time imports, class/module preparation, bodies and subprocesses;
   count chain/native invocations by exact analysis key. Record peak memory.
   Treat existing failures as baseline findings, not a reason to weaken checks.
2. **Pattern and support.** Write `docs/testing.md`; extract helpers and
   normalize imports without moving tests or changing expectations. Add
   coverage-ledger entries for shared observation ownership. Keep existing
   commands valid through this phase.
3. **Remove duplicate execution.** Separate scenario metadata/reporting from
   execution and integrate controller-aware finalization locally and across
   four CI shards. Verify standalone CLI, full suite,
   focused registry run, partial run, failed/expected-failed scenario, and
   frozen/candidate exclusion from live reach, DSE separation, and missing,
   stale, duplicate or failed shard evidence. Validate tags/history availability.
4. **Reuse measured observations.** Start with duplicate Window reports,
   cleanup report selectors and native baselines. Then share fixture loading,
   remove discarded `Pad` construction and reuse historical/conversion
   preparation, including the Python profile export baseline where measured.
   Keep independent test names when a class fixture suffices.
5. **Move by responsibility.** Introduce recursive discovery and stable
   reference resolution, then move one group at a time. Split mixed files
   with an explicit old-check → new-check mapping. Migrate sharder discovery
   and measured weights at the same time. Update documentation and the
   inventory as each group moves.
6. **Prove equivalence and measure.** Run the full suite in a fresh process,
   then compare against step 1. Investigate every missing ID/matrix cell or
   changed expected-failure status. Reproduce representative checks with
   deliberately broken input and verify they still fail. Run affected groups
   alone and in reversed/shuffled order to expose leaked shared state. Compare
   full serial outcomes with merged shard outcomes.

Completion requires:

- Every original assertion obligation has a mapped owner, even if method
  counts change. All 449 scenario labels and their sources/assumption matrices
  remain accounted for; newly added tests extend the ledger.
- All six working layouts, both variants, all specified option combinations,
  timing boundaries, seeds, negative cases, stored-order checks, CLI behaviors and Node tests
  remain covered, as do conversion stages and release history. No new skip,
  expected failure or reduced walk bound is used to obtain a green/faster suite.
- R156 still checks Ibex's actual builder and C1 checks Neptune/DSE against the
  changelog-selected Ibex release; historical Neptune reproduction and all six
  layouts' R152 second pipeline passes remain. No cache substitutes expected
  saved output for independent generation.
- Documentation references resolve, nested tests are discovered exactly once,
  archive tests remain excluded, and standalone scenario reports remain valid.
  Shards partition execution rather than merely module names; their validated
  evidence is required before release publication.
- Equivalent read-only observations run once per exact key where intended;
  mutation, reference and option-diversity cases still execute independently.
- Full-suite wall time improves with no unexplained peak-memory regression.
  Compare fresh-process runs on the same inputs/machine and record native
  compilation separately; use repeated runs to distinguish noise. Set a
  numerical time target only after the complete baseline exists.

## Implementation record

The active suite now contains **193 Python modules and 1,457 test methods**:
all 1,407 baseline cases plus 50 infrastructure checks. The two Node files
still contain eight tests. The 449 scenario labels, including 25 expected
failures, retain their mapped owners. The updated
[inventory](2026-10-15-test-inventory.csv) includes these files, 44 archived
Python files and the historical C4 record. [tests/test-map.csv](../tests/test-map.csv)
records every original case and its current identity.

Implemented:

- Explicit packages separate unit, current contracts, frozen releases,
  scenarios, integration and Node checks. Mixed modules are split by source
  and purpose; shared helper namespaces live under `tests/support/`.
- Recursive discovery, checker-reference resolution and release sharding use
  canonical module names. Active documentation, dated executable probes and
  skill commands resolve the new paths. The durable pattern is in
  [docs/testing.md](../docs/testing.md).
- Scenario metadata and reach queries no longer execute hidden suites. Normal
  runs record each selected case and its cells once. Full discovery and the
  explicit runner finalize the same evidence; focused discovery stays partial.
- Evidence binds source hashes, tags, commit, run and case assignment, and
  separates current/frozen/candidate sources, controllers, variants, stages
  and assumptions. Missing, stale, duplicate, failed and unexpected-success
  records fail; setup/teardown errors and skipped subtests cannot pass the gate.
- Four CI Python shards and the all-controller audit remain. A dependent
  finalizer gates publishing; both Node files run. A workflow-owned adapter
  retains validation of older unpublished tags without claiming modern
  scenario evidence for those tags.
- Source parsing returns private copies, keyed by exact bytes and parser mode.
  Shared Window/cleanup reports, native baseline observations, static
  inventories and profile preparation retain separate assertion methods.
  Native pairs stay paired with their own walk summary. Independent builders,
  conversions, mutations, option comparisons and determinism reruns remain.

The focused 11-case observation sample reduced Window audits from four to
two, cleanup audits from eleven to five, and native walks from eight to six
in the direct native sample. The six avoided cleanup audits also avoided
six native invocations. An illustrative warm run fell from 11.918 s to
7.521 s; this is not a whole-suite measurement. Walk depths, seeds, sample
counts, assertions, expected failures and simulator assumptions are unchanged.

Focused validation includes 433 checks across unit/shared/DSE/registry/release
areas, a separate 37-check migration/scenario/helper pass, all eight Node
checks, 54 scenario-runner/registry/DSE checks, and the legacy-adapter tests.
Fixture isolation and reverse-order groups pass. Collection finds each of the
1,407 original cases exactly once, with the same 449 labels and 25 expected
failures. Python source also compiles using Python 3.9 grammar.
The real standalone scenario CLI passed all 449 cases in 300.224 s with the
same 25 expected failures and wrote its release assumption report. Neptune
reached all 91 layers in each variant; DSE retained 19 of 75 in each variant.
No changed layer was uncovered. DSE's existing targeted scenarios are not
claimed to cover its other 56 layers. C1/C2/C3 passed again after removing
unused setup from the split conversion modules (three checks, 82.757 s).
The complete baseline and updated suite both finished successfully. All 1,407
mapped outcomes match exactly; the 50 added checks pass. Neither run has
failures, errors, skips or unexpected successes. Both retain 25 expected
failures. The full updated runner also passed all eight Node tests and its
coverage finalizer. A second process independently finalized the saved evidence.

| Local measurement | Baseline | Updated |
|---|---:|---:|
| Python cases | 1,407 | 1,457 |
| Python execution | 2,815.842 s (46m 56s) | 2,284.575 s (38m 05s) |
| Peak Python RSS | 1,397,424,128 bytes | 1,468,284,928 bytes |

The observed execution reduction is **531.267 s (18.9%)**. This is one local
sample pair on macOS arm64/Python 3.9.6, not a controlled benchmark: the
baseline overlapped development checks and standalone scenario validation;
the final updated run was serial. Both used the same already-built native
binary, so compilation was not measured. Peak RSS excludes native children
and later artifact serialization. It increased **67.58 MiB (5.1%)**. The new
runner retains execution evidence and bounded source caches; separate probes
measured about 24.80 MiB for the decoded evidence graph and 19.24 MiB for two
current Neptune source bundles. Those probes demonstrate retention costs,
but do not attribute the full-run high-water increase or prove an exact sum.
There is no measured memory improvement; controlled repeat profiling remains
necessary before making a stronger performance or memory claim.

The evidence contains 449 scenarios and 11,902 gesture cells, including all
60 DSE cells. The full-run reach matches the standalone result above. Splitting
the actual serial records into four documents and finalizing their union also
passed; this tests the merger with real results, not four independent CI runs.
Measured module durations, including fixture setup/teardown, now seed all 193
release shard weights. Projected shard times from those serial measurements
are 571.97, 573.57, 571.56 and 567.48 s; shared preparation can repeat across
workers, so these are not measured parallel durations. GitHub Actions itself
and publication were not run.

The compact [validation record](2026-10-15-test-validation.json) preserves the
environment, input fingerprints, exact counts, timings and comparison limits.
The full-run fingerprints precede the final timing-weight refresh, workflow
artifact naming/reference updates and documentation edits. Focused checks
validate those follow-up changes. CI artifact names include the run attempt;
retrying test or coverage jobs requires **Re-run all jobs** so evidence from
different attempts cannot be mixed.
The final fast unit command passed 365 checks in 2.219 s; 51 runner, migration,
legacy-adapter, profile-export and partition checks passed in 0.387 s after
the weight and workflow updates. Both workflow files parse, and current test
sources compile using Python 3.9 grammar.

The runner also releases completed successful test objects during execution,
so shared preparation does not introduce retention of every per-test fixture.
Weak-reference regressions cover CLI/shard/standalone/discovery ownership,
one-pass iterators and external callers that retain their own test lists.

No layout JSON/VDF, controller mapping, simulator engine or published artifact
is changed by this enhancement. The `overlay/` application is excluded as
requested; its Python profile-export contract remains active. The external
overlay workflow points to that test's new path without changing its platform
commands.
