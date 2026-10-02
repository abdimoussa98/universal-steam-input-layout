# Stack search: the three questions and what we tried

**Deprecated for routine audits (2026-09-30):** exhaustive stack search and
timed proof tooling are retained for reference, reuse and targeted investigations.
The replacement is an intended-flow inheritance checker (built 2026-10-01).
The three questions below are now answered per layer by backward chains
([record](../2026-10-01-backward-chain-stacks/README.md), `audit_layer.py`).
On 2026-10-01 the depth-limited `StackSpace` search and the intended-flow
family walk were deprecated too; every audit now builds its stacks from
those chains.
See the [decision, next steps and preserved checkpoint](ARCHIVE.md).
Historical commands below may reference disposable files under `out/`.


**Tools implemented and checked; complete analysis of default 90.6 remains
incomplete.** The timed runtime,
witness discovery, full-stack symbolic envelope, inductive checker and
`timed_audit` report/CLI are implemented. They can answer the three questions
without enumerating every reachable state: every catalogue alternative must
have either a replayed timed witness or a checked inductive exclusion.
The current checkpoint covers **46,904 alternatives**: **11,491 witnessed,
31,644 excluded and 3,769 unresolved**. The
[summary](../../out/stack_search/timed-facts/default-summary.json),
[full audit](../../out/stack_search/timed-facts/default-audit.json), and
[checked certificate](../../out/stack_search/timed-facts/default-certificate.json)
retain the distinction between witnessed, excluded and unresolved facts.
The current compiler combines phase, progress, elapsed-repeat and
[atomic analog rules](TIMED-MODEL.md#positive-analog-first-batches).

The author chose to finish the original [90.6 layout](../../versions/neptune/90.6/single-set-default_hold-gyro_90.6.json)
after the mutable `latest` file advanced to 90.7. The versioned file matches
the frozen input and certificate's layout identity; [the canonical hash is recorded
here](TIMED-MODEL.md). **These timed results do not cover 90.7.**

The [timed contract](TIMED-MODEL.md) tracks separate delays, removal-driven
restarts, repeats, held mode shifts and logical threshold coordinates. It
omits legacy hold commands for this analysis and uses the author's accepted
50 ms fallback for omitted repeat intervals. The original requirement of
complete answers faithful to Steam hardware is stronger than completeness for
this declared model; source processing and other assumptions remain explicit.
See [the current audit](#current-timed-fact-audit) and
[model limits](MODEL-LIMITS.md).

**Historical HeldModel result:** [4,720 invariants in 226 seconds](PROOF-RESULTS.md),
with no solver timeouts. L1 Double Tap's possible lower layers fell from 70 to
23 (19 witnessed, 4 unresolved). Those results and the older experiments below
use the untimed model; their witnesses and exclusions are not timed evidence.

## Why

This tooling exists to audit and extend the layout programmatically:

- audit today's cleanup functions and the blocks/replaces that fix inheritance
  bugs, against [Cleanup Functions](../../resources/Cleanup%20Functions.md) and
  [Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md)
  (§7 Cleanup, §8 Inheritance and blocking);
- use that to clean up the layout, and to add layers reliably later
  ([cleanup generator plan](../../plans/2026-09-30-cleanup-generator.md)).

## The three questions

For any layer X (and at any given moment):

1. **What is inherited:** which inputs fall through X to a layer below it.
2. **What each inherited input does:** its value, a keybind or a layer API
   call, and which layer it comes from.
3. **What is below and above X:** every layer that can be under it, and every
   layer that can be added on top of it.

"Definite" means: everything listed can really happen, and nothing that can
happen is missing. "Realistic" means: real button presses (held buttons, chords,
one thumb per place, delays, repeats, explicit layer adds/removals), no depth or event cap.

For a **known stack**, binding owners and serialized activators can be read
directly from the layout JSON (`StackDB.values(stack)`). Which activator fires
also depends on held controls, timing and mode shifts. The reachability problem
is determining which of those owners and layer relationships occur in any
reachable stack. A complete set of answers does not require explicitly listing
every stack if witnesses and checked exclusions cover every alternative.

## Model decisions (author-confirmed)

- Re-adding an active layer does not move it (ABC + add A stays ABC); remove
  then add puts it on top. Confirmed on the Deck and in Valve's docs.
- Missed releases (Steam menu open while releasing) are **left out**: cleanup
  functions exist to recover from them. `--missed` turns them back on.
- Hand model: each thumb is in one place (left: stick, pad, D-pad or Menu Left;
  right: stick, pad, face buttons or Menu Right). Any combination of face
  buttons, D-pad, bumpers with triggers, and back buttons is allowed.
- A pad chord means "thumb on the pad" (touch). The timed model keeps explicit
  held controls. The historical HeldModel optimized other inputs into taps and
  retained generic `hold_layer` support; that legacy implementation is not the
  current runtime contract.
- Author clarification (2026-09-30): never use `hold_layer` or action-set
  switching; holds use explicit adds/removals. The old model's automatic
  `hold_layer` release rule is an implementation assumption, not an
  author-confirmed runtime requirement. Five legacy commands remain in each
  90.6 variant; see [runtime rules](../../resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).
- The removal/reset timer restarts and waits 300 ms in the discussed case,
  rather than being cancelled. The new timed replay models this rule;
  `HeldModel` and its proof engine still omit numeric timing.
- The author accepted a 50 ms repeat interval where the layout omits one for
  this analysis. Explicitly configured intervals take precedence. This is an
  analysis choice, not a claim about Steam's built-in default.

## Current timed fact audit

[`timed_facts.py`](../../steam_layout/timed_facts.py) catalogues every alternative
and stores replayable witnesses. [`timed_discover.py`](../../steam_layout/timed_discover.py)
finds additional witnesses under resource budgets; those budgets never prove
absence. The symbolic envelope and timed induction provide the independent
upper bound. `timed_audit` reports the three answers with X anywhere in the
full ordered stack, including when another layer is above it.

To inspect the saved checkpoint, use its matching evidence and certificate:

```sh
.venv/bin/python -m steam_layout.timed_audit show \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-evidence.sqlite \
  out/stack_search/timed-facts/default-certificate.json \
  'L1: Double Tap' --json \
  --ignore-hold-bindings --default-repeat-ms 50
```

See [the discovery, compaction and proof commands](TIMED-MODEL.md#discover-compact-and-check)
to collect more witnesses or generate a fresh baseline.
A fresh `timed_audit run` infers primitive invariants and can be weaker than
the saved checked proof. Its example writes separate `regenerated-*` outputs;
`timed_refine` retains the checked baseline when adding hypotheses.

`proven` means a concrete timed witness; `excluded` means independently checked
induction; `possible` remains unresolved. `complete_for_model` is true only
when every alternative in the requested report is witnessed or excluded.
This criterion can finish without exhausting the timed graph. JSON preserves
all excluded alternatives, original activators and witness traces. Loading a
certificate checks its model/code identity and reruns induction validation;
a saved `verified` flag is not sufficient. None of these labels establishes
hardware equivalence outside the [declared timed contract](TIMED-MODEL.md).

### Checked current checkpoint

The current default 90.6
[summary](../../out/stack_search/timed-facts/default-summary.json),
[full audit](../../out/stack_search/timed-facts/default-audit.json), and
[certificate](../../out/stack_search/timed-facts/default-certificate.json)
use the production `TimedAnalogEnvelope` and matching
[`default-evidence.sqlite`](../../out/stack_search/timed-facts/default-evidence.sqlite).
This is a checked checkpoint, **not a complete classification**.
Its **901 invariants passed 3,409 independent validation checks**. Across the
full catalogue, **11,491 alternatives are witnessed, 31,644 excluded and
3,769 unresolved**; `complete_for_model` is false.
The final full regression suite passed **531 tests in 106.323 seconds**
([log](../../out/stack_search/timed-final-tests.log)).

Readable per-layer reports and their matching JSON are in
[`default-layers`](../../out/stack_search/timed-facts/default-layers).
They retain below/above alternatives, raw inherited activators, exclusions and
witness references. Unresolved alternatives need another concrete timed
witness or an additional independently checked exclusion.

| Current layer report | Witnessed alternatives | Excluded | Unresolved |
|---|---:|---:|---:|
| [L1 Double Tap](../../out/stack_search/timed-facts/default-layers/l1-double-tap.txt) | 88 | 373 | 72 |
| [LST Double Tap](../../out/stack_search/timed-facts/default-layers/lst-double-tap.txt) | 113 | 411 | 9 |
| [RTP Double Tap](../../out/stack_search/timed-facts/default-layers/rtp-double-tap.txt) | 135 | 111 | 21 |
| [Steering LS Down Double Tap](../../out/stack_search/timed-facts/default-layers/steering-ls-down-double-tap.txt) | 99 | 490 | 21 |

These are query alternatives, not stack counts. Above relations reuse other
layers' below facts, so per-layer counts must not be summed into a global total.

### Historical timed baseline

The default 90.6 [compact summary](../../out/stack_search/timed-facts/default-base-summary.json)
is extracted from [the full baseline report](../../out/stack_search/timed-facts/default-base-report.json)
and its [checked certificate](../../out/stack_search/timed-facts/default-base-certificate.json).
That historical checkpoint recorded **10,245 witnessed, 24,207 excluded and
12,452 unresolved** alternatives.
The proof retained 3,223 primitive invariants plus 11 checked family
disjunctions, then removed redundant predicates to leave 1,373. These are timed
results, separate from the historical HeldModel measurements below. This
baseline predates `TimedPhaseEnvelope`; its certificate has the old algorithm
hash and is correctly rejected by current tools. Its counts are retained as a
historical measurement, separate from the current checked checkpoint above.

| Layer report | Witnessed alternatives | Excluded | Unresolved |
|---|---:|---:|---:|
| [L1 Double Tap](../../out/stack_search/timed-facts/default-base-layers/l1-double-tap.txt) | 85 | 218 | 230 |
| [LST Double Tap](../../out/stack_search/timed-facts/default-base-layers/lst-double-tap.txt) | 66 | 391 | 76 |
| [RTP Double Tap](../../out/stack_search/timed-facts/default-base-layers/rtp-double-tap.txt) | 123 | 105 | 39 |
| [Steering LS Down Double Tap](../../out/stack_search/timed-facts/default-base-layers/steering-ls-down-double-tap.txt) | 66 | 111 | 433 |

Each row includes below, above and raw-inheritance alternatives; these counts
are not numbers of stacks. Matching JSON files retain excluded alternatives,
original activators and the referenced witness traces. The full 430-test suite
passed in 106 seconds at this historical baseline.

## Historical untimed experiments

Default layout, `neptune/single-set-default_hold-gyro_latest.json`, 72 layers.
The measurements in this section predate the timed runtime. "Events" are
button presses, releases, holds, taps and Always On timers in the older models.

| # | Approach | Result |
|---|---|---|
| 1 | Python stack search (`StackSpace`), depth 5 | Fast, but depth-capped: misses anything deeper |
| 2 | Chord-blind exhaustive search (C++) | 114M states at 9 events, still ×4 per event: never finishes |
| 3 | Realistic held-button search (C++, in memory) | Exact through 10 events (186M states, 3.5M distinct stacks) before 12 GB; ×3 per event |
| 4 | Drop missed releases | Barely helped: 66M states at 10 events |
| 5 | Fix which inputs stay held (pad touch only; `hold_layer` release) | Correct, not smaller: 82M at 10 events. Most states hold 5–9 inputs |
| 6 | Disk-backed search (`--disk`, resumable) | Works, same counts. Estimates: 11 events ~5 min / 13 GB, 12 ~50 min / 40 GB, 13 ~5 h / 115 GB |
| 7 | Do answers converge? | L1/R1 Double Tap stable from 6 events, Menu Left from 7. RTP Double Tap, Menu Right and Steering still new at 10 |
| 8 | Sample of 11-event stacks | 535k new stacks: 81% a known stack plus one layer, 19% reorders. Only **31** add new facts (152), mostly Steering and Turning Ramp Up |
| 9 | Split into independent groups | Adds split into 10 groups (main 50 layers, RTP, LST, RST, ramps, 5 swipes), but cleanups and stick-touch releases tie them all together |
| 10 | Reuse (summaries keyed by what's below) | (X, profile below) has only **38,761** keys, but the exact key barely compresses (3.96M of 4.15M): cleanups reach ~32 layers below any layer, so deep order always matters |
| 11 | Top-K model (top K in order, rest as a set; `--top K`) | Doesn't finish: K=1 still 134M states at 10 events. Growth is ~300 held-button combinations per set of active layers, not order |
| 12 | Per-layer rule ("Y can be below X if Y can be active when something adds X") | Instant and never missed a proven fact, but far too loose (table below) |
| 13 | Full-stack symbolic events + Houdini induction | 4,720 invariants in 226 seconds, no event cap or solver timeouts; much tighter bounds, some facts still unresolved ([results](PROOF-RESULTS.md)) |

Per-layer rule against the search (layers below X):

| Layer | Proven by search | Rule: possible |
|---|---:|---:|
| L1 Double Tap | 19 | 70 |
| LST Double Tap | 7 | 57 |
| RTP Double Tap | 46 | 69 |
| Steering LS Down Double Tap | 4 | 59 |
| L1: Modifier 0 | 20 | 48 |

Rejected by the author: pair-based search as the main answer, depth caps, and
keeping missed releases.

## What we learned

- The growth is combinations of independent activity (which buttons are held
  × which layers are active), not stack order. Almost none of it changes an
  answer: the answers themselves are small (about 39k facts).
- Brute force gives **proven** answers (each with the button sequence that
  reaches it) but can't prove that nothing is missing.
- A cheap bound gives **nothing missing** but is too loose without the
  author's own invariants ("Modifier 0 exists only while LB is held",
  "LB release cleans up the L1 family").

Layout finding waiting on a decision: RTP Double Tap inherits LB, RB, both menu
buttons (~33–35 different layers each) and both trigger edges (both Fn layers)
depending on the stack. By §8 ("replace only if identical in every stack") they
should be cleared. Not applied.

<a id="the-helper"></a>

## Historical HeldModel helper

Install the optional solver in a local environment, then use a matching held
search as concrete evidence:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-proof.txt
.venv/bin/python -m steam_layout.stackdb show 'L1: Double Tap' \
    --search out/stack_search/default-held
```

`--layout PATH` selects another layout; the default is the default Neptune
JSON. `--json` includes witness IDs, full activators, the surviving invariants,
excluded alternatives and proof statistics. Use `StackDB.witness(id)` to read
a trace; every reported fact's trace has already been replayed against the
current model. `--search` is optional, but without concrete evidence reachable facts
remain `possible`. An incompatible or stale search is rejected.

Exit 0 means the report was generated; inspect `complete_for_model` before
treating it as a complete audit. Exit 2 reports invalid input or incompatible
evidence. Python callers can reuse a completed `InvariantProof` across
`layer_report(proof, title, evidence)` calls for several layers.

The three answers are derived for X **anywhere in the stack**, including when
another layer is above X. Inputs defined or disabled by X are not inherited.
For each remaining input, the report identifies its topmost lower binding,
disabled source, or absence of a binding, and retains the original activators.
An upper layer can still override the whole stack's effective input.

- **proven:** a concrete event sequence reaches the fact in `HeldModel`.
- **possible:** the inductive bound cannot exclude the fact; it may be unreal.
- **excluded:** impossible under the surviving inductive invariants in
  `HeldModel` (listed in JSON, omitted from the ordinary possibilities).
- **complete_for_model:** every alternative left in this report has a witness.
  This does not certify hardware behavior or enumerate every stack.

There is no event or stack-depth cap on the proof. `--timeout-ms` limits each
solver call (default 10000); unknown induction checks discard affected
candidates, and unknown query checks retain possibilities. Timeouts can lose
precision but never produce a proof. The full fixed point must finish before
any exclusion is used. Candidate seeding from incomplete search is safe because
every retained candidate is independently checked by induction.

The symbolic state includes the **entire ordered stack and all held controls**.
Pair-shaped candidate facts are predicates over that state, not the previously
rejected pair-based reachability search. Each transition is a whole event:
entry selection, all its commands and automatic hold release stay together.

The optional dependency is [Z3](https://github.com/Z3Prover/z3). The inference
algorithm follows [Houdini's candidate elimination](https://www.microsoft.com/en-us/research/publication/explainhoudini-making-houdini-inference-transparent/).

## Remaining work

Both the historical HeldModel checker and the separate **timed-envelope
inductive checker** are implemented:

1. Candidate facts come from the search: everything it never saw, such as "Y is
   never below X" or "X present means button b is held".
2. A fact is proven if it holds at the start and **no complete event can break
   it**, assuming the other candidate facts hold. Failing candidates are
   dropped and every event is rechecked until a full pass removes nothing.
   This retains held buttons and cleanups, with no event cap. Checking each
   layout entry in isolation would be incorrect for atomic multi-entry events.
3. Proven facts are definitely impossible. What's left is either real (search
   deeper for a button sequence) or needs a stronger fact.

The tools and checked checkpoint are implemented. Complete answers for every
layer still require resolving each remaining alternative through another
timed witness or a stronger independently checked invariant.
The source-geometry and other runtime assumptions remain a separate scope
question; mathematical completeness for the declared contract does not settle
them.
The original estimate of "seconds" was a proposal, not a benchmark; there is
no general speed guarantee for these solver checks.

Risk: some true facts may need more than "layer pairs" or "layer implies
button held" to prove; those stay on an open list.

## Tools

| Piece | What it does |
|---|---|
| `steam_layout/timed_spec.py`, `timed_model.py`, `timed_trace.py` | Numeric runtime specifications, immutable timed states and JSON event replay ([contract](TIMED-MODEL.md)) |
| `steam_layout/timed_search.py`, `timed_store.py`, `timed_report.py` | Resumable timed reachability, witness replay, closure certificates and the three layer queries |
| `steam_layout/timed_facts.py`, `timed_discover.py` | Finite query alternatives, replayed witness forests, budgeted discovery and archive compaction |
| `steam_layout/timed_envelope.py`, `symbolic_batch.py`, `timed_proof.py` | Full-stack timed upper bound, atomic symbolic batches and checked inductive exclusions |
| `steam_layout/timed_phase_envelope.py` | Six runtime-derived restrictions on press and timer batches, included in certificate identity ([rules](TIMED-MODEL.md#runtime-derived-batch-restrictions)) |
| `steam_layout/timed_progress_envelope.py` | Ordered-owner restriction relating repeaters and delayed entries; included in certificate identity ([rule](TIMED-MODEL.md#ordered-owner-progress-restriction)) |
| `steam_layout/timed_elapsed_envelope.py` | Separate elapsed repeats from newly activated one-shots ([rule](TIMED-MODEL.md#elapsed-repeat-batches)) |
| `steam_layout/timed_analog_envelope.py` | Production compiler with all preceding rules and atomic positive-analog first batches; five transition families ([rules](TIMED-MODEL.md#positive-analog-first-batches)) |
| `steam_layout/timed_predicates.py` | Additional induction hypotheses: a family below a layer, a family between an ordered pair, or a specific impossible catalogue fact |
| `steam_layout/timed_mine.py`, `timed_between.py` | Replay-backed sample mining of small family hypotheses; suggestions require independent induction ([usage](TIMED-MODEL.md#mine-conditional-family-hypotheses)) |
| `steam_layout/timed_audit.py` | `run` / `show`: identity-bound certificates and three-question reports combining timed witnesses with induction |
| `steam_layout/timed_refine.py` | Extend a checked baseline with exact fact hypotheses; optional family candidates and unvalidated recovery checkpoints ([usage](TIMED-MODEL.md#refine-an-existing-certificate)) |
| `steam_layout/timed_minimize.py` | Reduce a checked certificate to an equivalent subset and independently validate it again ([usage](TIMED-MODEL.md#minimize-a-checked-certificate)) |
| `steam_layout/timed_reduction.py` | Exact relevance quotient for ordered-stack reachability; separate from the unchanged full-quotient databases |
| `steam_layout/source_geometry.py` | Explicit saved/inherited source settings and boundary candidates; separate from runtime sensor interpretation |
| `steam_layout/held_model.py` | Realistic model (`HeldModel`); `TopModel` for the top-K bound |
| `tools/stack_search/rules.hpp` | The same rules in C++, shared by both engines |
| `tools/stack_search/stack_search.cpp` | In-memory exhaustive search (`--held`, `--missed`, `--top K`, `--memory-limit`) |
| `tools/stack_search/stack_search_disk.cpp` | Disk-backed search (`--memory`, `--disk-limit`, `--resume`) |
| `steam_layout/stackdb.py` | Runs the engines; SQLite store; `values`, `moment`, `inheritance`, `inherited_values`, `witness`, `sql` |
| `steam_layout/symbolic.py` | Complete ordered-stack, held-control event formulas matching `HeldModel` |
| `steam_layout/invariants.py` | Candidate generation and sound fixed-point induction; unknown checks remain unproven |
| `steam_layout/stack_evidence.py` | Matching search evidence; all-stack inheritance and concrete witnesses |
| `steam_layout/stack_report.py` | `stackdb show`: combines witnessed facts with inductive bounds |
| `tests/test_held_model.py`, `test_stack_search*.py`, `test_top_model.py` | Engines agree exactly with the Python reference; soundness of `TopModel` |
| `tests/test_symbolic.py`, `test_invariants.py`, `test_stack_evidence.py` | Differential event tests, induction fixed point/unknown handling, evidence and inheritance checks |
| [scripts/](scripts/) | The analyses behind rows 8–12 (read `out/stack_search/default-held`) |

Regenerate the data the scripts read (about 2 minutes, stops at 12 GB):

```bash
python3 -m steam_layout.stackdb run neptune/single-set-default_hold-gyro_latest.json \
    out/stack_search/default-held --held --threads 14 --memory-limit 12
python3 findings/2026-09-30-stack-search/scripts/rule.py
```
