# Testing

Tests protect saved layout contracts, conversion rules, audit behavior and
simulated input sequences. They do not establish how Steam schedules a binding
on a physical controller. Keep that distinction, and the rule and assumption
IDs, when adding or reorganizing a check.

The [Definition of Done](../resources/Layer%20Definition%20of%20Done.md)
defines the required checks. [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md)
records what the simulator assumes. [Building](building.md) identifies current
builders and conversion sources; [publishing](publishing.md) defines release
validation and immutable tagged snapshots. Dated findings retain their own
historical sources and commands.

## Running tests

Run commands from the repository root:

```bash
python3 -m tests.runner
python3 -m unittest discover -s tests -t .
python3 -m tests.scenario
```

For a quick, partial check, run `python3 -m unittest discover -s tests/unit -t .`.
To retain full-run outcomes and timings, run
`python3 -m tests.runner --evidence /tmp/test-run.json`. The runner assigns a
unique run ID unless one is supplied. The artifact records collection, manifest
preparation, execution and revalidation time, plus per-module time including
class/module setup and teardown. Peak Python RSS excludes native child
processes; it is measured after test execution, before artifact serialization.

The full runner coordinates the Python suite, scenario evidence and both Node
test files. Unfiltered Python discovery runs the Python suite and its coverage
finalization. Filename filters such as `-p test_native.py` and test-name filters
such as `-k selected` run only their matching tests, without the whole-suite
coverage gate. The default patterns `test*.py` and `test_*.py` retain that gate
when no test-name filter is supplied. `tests.scenario` lists scenario rules and assumptions and can
produce a release report. A focused `python3 -m unittest <module-or-test-id>`
run checks its selection; it does not establish complete scenario coverage.

Use the release tool's shard selection in CI, as documented in
[publishing](publishing.md). Shards must partition the active tests exactly
once and merge their scenario evidence before the coverage gate. An incomplete
or failed shard cannot supply a successful whole-suite report. Keep the actual
CLI, exporter dependency and native compiler checks: missing prerequisites
must not silently turn required tests into skips.

`archived/` and `overlay/` are outside this suite's discovery. The Python
profile-export tests under `tests/` remain included; the separate overlay
application and its workflow have their own validation.

## Pattern for a test

State these five things in the module or class documentation and the coverage
inventory:

| Part | What to state |
|---|---|
| Contract | Behavior, exact configuration, error or rule protected. |
| Source | Synthetic layout, current controller/variant, exact frozen path/release, separate candidate, or actual builder/converter output. |
| Cases | Controller, variant, transformation stage, starting stack, held inputs, event order/times, assumptions, desktop mode, seeds and engine options. |
| Observation | The report, inventory, chain result or trace produced once for that exact case. |
| Assertions | Named checks with enough context to locate a failure: controller, release, variant, input, rule and options. |

Use one execution for related assertions about the same behavior. For example,
the modifier-rocking tests walk a sequence once and check its intermediate
stacks, the layer answering each input, final cleanup and cover ordering.
Separate test methods may read one class observation when their contracts have
different names. Use `subTest` for independent cases and prerequisites before
indexing a report or trace.

Do not replace exact outputs, stored order, witnesses, paths, finding reasons
or exit statuses with a general `ok` check. Two sequences that end on the same
stack can protect different behavior. Preserve both when their starts,
intermediate states, timing or options differ.

Directories identify responsibility rather than execution cost:

| Area | Responsibility |
|---|---|
| `tests/support/` | Source preparation, toy builders, shared expectations and execution evidence. No discovered test classes. |
| `tests/unit/` | Small synthetic model, audit and simulator cases. |
| `tests/contracts/` | Current-layout invariants with an explicit controller/variant matrix. |
| `tests/releases/` | Frozen shapes and deltas, independent builder/conversion reproduction. |
| `tests/scenarios/` | Input sequences with stable release labels, rules and assumption metadata; separate candidate sources remain separate. |
| `tests/integration/` | Real commands, reports, native parity, release repositories and profile exports. |
| `tests/node/` | VDF exporter and steering observer tests. |

Use canonical package imports. Shared helpers belong in support, not in a test
module imported through a bare sibling name. Preserve old checker references
through the test-reference resolver when moving or splitting a module; update
live documentation, without rewriting a dated finding's claims. A compatibility
module must not re-export `TestCase` classes and discover them a second time.

The [migration ledger](../tests/test-map.csv) maps all 1,407 original case IDs
to their current owners, preserving scenario labels and expected failures.
Keep these baseline rows when moving a check again; new tests are collected
normally and do not need invented legacy IDs. The
[file inventory](../plans/2026-10-15-test-inventory.csv) records current paths,
source boundaries and controller scope. `tests.support.discovery.resolve_tests`
resolves legacy checker references, including checks split across modules.

## Sources and controller scope

Ibex is the built base. Neptune and DSE are converted from the Ibex release
named in their changelog, which need not be the newest source snapshot. Both
variants matter. Numeric release names are local to a controller: DSE 1.0 and
Ibex 1.0 are different sources.

R156/R177 have independent obligations: build current Ibex and compare its
saved output; convert each current derived layout from its named source and
compare its saved output. Historical Neptune builders through 90.74 keep their
own reproduction checks. R152 runs the fix pipeline again on all six working
layouts to prove a fixed point. Reuse does not replace these executions.

Some examples of existing fixture boundaries:

| Checks | Source and cases |
|---|---|
| Neptune cursor, recovery, gyro and held-input contracts | Current Neptune default/alternative; raw numeric and readable forms, duplicate-key detection and runtime-ID roundtrip. Gyro tuning also compares the July reference. |
| Controller registry | All three controllers and both variants; directory/header identity, gyro style and controller-local snapshot ownership. |
| Conversion rules | Independent small synthetic layouts for each rule, including absent/moved chord controls and wrong-source failures. |
| Whole-pad transformation | Frozen Ibex 1.0 default after only the whole-pad step; this is not the final DSE conversion. |
| Conversion integration | C1 current provenance; C2 real CLI audit on Ibex/DSE; C3 independently sourced Neptune 90.74 roundtrip; C5 final DSE versus source pad models, both variants. |
| Python profile exporter | Frozen Ibex 1.0 default only. Share its read-only export; execute altered inputs and the determinism rerun independently. |
| 90.61 static shapes | Frozen 90.58 versus the 90.61 candidate, plus distinct frozen 90.64 shape checks. |
| 90.62 static shapes | Current modifier contracts and a separate 90.61/90.62/90.64 historical comparison. |
| 90.69 and 90.70 cleanup checks | Frozen off-line 90.69 trial; current 90.70-descendant contracts; separate frozen 90.68 → 90.70 delta. |

The 90.39 fallback-window candidate uses its own source and rules. It must not
become current merely because of its version number. Frozen sources in
findings and snapshots under `versions/` retain their original purposes.

DSE lacks stick touch and the right pad. Its CTP layers, physical grip mapping,
mute input and Gyro/Base distinction need their own cases. Rules and declared
stacks are adapted through the controller-specific exception view. An absent
input makes a particular rule inapplicable; it does not justify skipping an
unrelated contract.

The DSE E1–E8 scenarios cover 60 gesture cells across both variants: swipes,
ring and centre clicks, key-layer handoff with both A9 outcomes, mute, Gyro and
Base starts, four physical grips, and three missed-release types recovered by
either stick. The historical C4 Ibex/partial-Edge experiment is recorded in
[the build finding](../findings/2026-10-15-ibex-base/README.md); it is not a
regular full-suite gate or a test of the final DSE layout.

## Reusing preparation and observations

Use bounded, in-process test fixtures. `tests.support.sources.load_json`
returns a private copy and keys parsing by the resolved path, exact bytes and
parser mode. Re-reading a changed file therefore prepares its new content.
The Neptune bundle also retains raw bytes as text, the numeric source,
readable source, conversion count, lookup and group/preset indexes. Callers
receive private copies, including aliases between the prepared views.

Read-only projections may be shared within a class. Mutation, cleanup fixes
and comparison normalization use private copies. In particular, stripping
release title/description or gyro-style fields must not alter a source used
by another test. A saved candidate cannot be both the expected value and the
supposed independently generated actual value.

| Observation | Identity required for reuse |
|---|---|
| Parsed source | Exact path/content, controller, variant, source kind, release and parsing/normalization mode. |
| Conversion stage | Source Ibex release/content, target controller/profile and version, variant, rules and exact processing stage. |
| Backward chains | Layout, arrival allowance, contexts and foreign-arrival behavior. |
| Native result | Tables and exit table, extras, landings, path policy, threads, memory limit and batch settings. Keep pairs and the invocation's walk summary together. |
| Audit report | Analysis identity, effective controller-specific rules/declared stacks, filters, changed-layer set and baseline. |
| Gesture trace | Source and target controller, release/candidate stage, start/held state, events/times, assumption options, desktop mode, seed and instrumentation. |

Keep dictionary and list order in fingerprints. `Chains.of(layout)` can reuse
an existing layout's analysis, but `Inventory.of(layout)` deliberately reads
current mutable groups on every call. Do not introduce a production cache to
make a fixture faster. Prepare an inventory once at the test boundary only
when its layout remains unchanged.

Different mutations, configurations and native options are different cases.
Keep independent reference implementations, fresh-process checks, fixed-point
passes, deterministic reruns, progress/memory-stop tests and timing checks.
Never accept an unfinished walk as complete coverage or reduce the specified
extra-press depth, samples, seeds or landing checks to make a run quicker.
Conversion's structural reach graph, scenario reach and backward-chain/native
reach are different observations and are not interchangeable.

## Scenario evidence and completeness

Scenario metadata, execution, reach accumulation and report rendering are
separate responsibilities. The full suite executes each selected case once
and records its outcome and reach; finalization checks the required case
selection before using that evidence. Nonempty reach is not proof that all
required cases ran.

Keep current, frozen, candidate and controller-specific reach separate. A
frozen Neptune case remains Neptune when the default scenario controller is
Ibex. Explicit DSE cases must not satisfy Neptune coverage. Record every
assumption combination, including expected failures and unexpected successes;
do not count a partially executed failed case as successful coverage.

Each gesture gets a fresh simulator, event queue, held-input state, log and
reach accumulator. Share immutable input sequences and source preparation,
not a running simulator or a mutated common prefix. Retain the special
Steering-entry gesture and settling behavior when selecting an initial stack.

R165's automated reach check establishes that changed layers occur on the
stack. Human review still checks held inputs, presses inside layers and missed
releases. A simulator pass does not verify an unconfirmed Steam assumption.

## Changing the suite

Before and after a reorganization, record the collected identities, fixture
hashes, outcomes, rule/assumption links, matrices and reach. Every original
assertion obligation needs an owner even if test-method counts change. Keep
the inventory and live checker references synchronized with moves and splits.

Measure imports, setup, test bodies and subprocesses separately; shared setup
can dominate a short-looking test. Compare fresh runs on the same stable tree
and machine, record native compilation separately, and report peak memory.
CI shard weights need updating when work moves from a method to a shared
fixture or the coverage finalizer.

Run affected groups independently and in another order after introducing
sharing. Demonstrate representative negative cases still fail. Then complete
the full gate: no lost controller/variant/assumption cells, no reduced bounds,
no extra skips or expected failures, valid reports and references, and no
unexplained memory regression. A focused timing result is not a full-suite
speedup claim.
