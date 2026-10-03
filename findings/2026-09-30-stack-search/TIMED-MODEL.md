# Timed layer replay

**Deprecated for routine audits (2026-09-30):** exhaustive stack search and
timed proof tooling are retained for reference, reuse and targeted investigations.
The replacement is an intended-flow inheritance checker, still to be built.
See the [decision, next steps and preserved checkpoint](ARCHIVE.md).
Historical commands below may reference disposable files under `out/`.


Implemented 2026-09-30. The new Python runtime replays explicit presses,
releases, analog samples and elapsed milliseconds. It keeps separate clocks
for activators and retains every resulting command-order branch. This is a
working reference simulator under the contract below. A persistent exhaustive
search explores its finite clock/analog quotient, and the timed fact audit
combines replayed witnesses with checked inductive exclusions.
Exclusions require either independently checked graph closure or validated
inductive invariants of the timed envelope. The model is not certified as an
exact description of Steam.

**The tools and checked 90.6 checkpoint are implemented; the all-facts
classification remains incomplete.** Read the current
[summary](../../out/stack_search/timed-facts/default-summary.json),
[full audit](../../out/stack_search/timed-facts/default-audit.json), and
[certificate](../../out/stack_search/timed-facts/default-certificate.json).
The checkpoint records **11,491 witnessed, 31,644 excluded and 3,769
unresolved** alternatives out of 46,904.

**Production scope: the default 90.6 layout.** The author chose to finish
this original input after the mutable `latest` file advanced to 90.7. Every
layout command below uses the tracked [90.6 JSON](../../versions/neptune/90.6/single-set-default_hold-gyro_90.6.json).
It matches the frozen copy `out/stack_search/timed-facts/layout-default-90.6.json`
and the recorded certificate's canonical layout SHA-256:
`cab4cde6228baff341546bf78a9d977ad6c87756529a2e55c79f7229e5114377`.
The newer 90.7 layout is not covered by these witnesses, counts or certificates.

The author's clarification is incorporated: removals restart the discussed
timer, which waits another 300 ms rather than being cancelled. The runtime
uses each entry's configured delay, so this does **not** turn every delay into
300 ms. Legacy `hold_layer` commands can be explicitly omitted for this work.
The project uses explicit layer adds/removals and one structural Base action
set; action-set switching is excluded.

## Run a trace

The checked-in [example trace](timed-example.json) holds Menu Left for 300 ms:

```json
[
  {"press": ["switch", "button_menu"]},
  {"wait_ms": 300},
  {"release": ["switch", "button_menu"]}
]
```

Then run:

```sh
python3 -m steam_layout.timed_trace \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  findings/2026-09-30-stack-search/timed-example.json \
  --ignore-hold-bindings \
  --default-repeat-ms 50
```

**The author accepted 50 ms for this analysis. It is not a claimed Steam default.**
It supplies the interval only for entries with `hold_repeats: "1"` and no
`repeat_rate`; explicitly configured intervals take precedence. Omitting the
option when such entries exist causes an informative error. Choosing another
value can change a replay and changes its recorded model identity.

`--ignore-hold-bindings` omits only the legacy hold commands from the scenario.
Their entries still participate in input overriding and chord guards, and
other commands in those entries remain. The report records five omitted
commands for each 90.6 Neptune variant. Neither the flag nor replay edits
the layout files.

The command writes JSON containing initial states, each event's resulting
states and transitions between them, final branch count, scenario settings,
the runtime contract, and layout/model/implementation hashes. State snapshots show elapsed
time, the complete layer stack, held controls, analog samples, individual
activator deadlines and active mode shifts. Invalid traces or unsupported
features produce an error and exit status 2.

## Events and Python API

Each trace event contains exactly one operation:

| Event | Meaning |
|---|---|
| `{"press": ["source", "input"]}` | Activate a logical input at the current time |
| `{"release": ["source", "input"]}` | Release a held control at the current time |
| `{"wait_ms": 100}` | Advance 100 integer milliseconds, processing every deadline reached |
| `{"analog": {"control": ["joystick", "edge"], "value": "27000"}}` | Supply a logical threshold coordinate at the current time |

Analog coordinates use the **0 through 32767** scale, not normalized 0–1
values. They are not controller sensor readings: a positive sample also marks
that logical input held, while zero releases it. An `edge` press asserts an
edge activation after source processing. Decimal strings preserve exact
comparison values. Controls use
the layout's source/input names. Switch-bank pad-touch and stick-click aliases
map to their corresponding physical pad/stick controls. Physical checks retain
the thumb-location restrictions and require touch before dependent pad/stick
inputs, and trigger edge before full click when those controls are present.

- [`timed_spec.py`](../../archived/exhaustive-stack-search/steam_layout/timed_spec.py) provides
  `TimedSpec(layout, ignore_hold_bindings=False, default_repeat_ms=None)` and
  immutable `EntrySpec` records. They preserve numeric delays, repeat intervals,
  chord selectors, thresholds, inversion, full settings, ordered layer
  operations and mode-shift targets. Stable entry IDs distinguish separate
  activators; fingerprints include the complete serialized entry, including
  non-layer outputs, plus source/input/kind.
- [`timed_model.py`](../../archived/exhaustive-stack-search/steam_layout/timed_model.py) provides
  `TimedModel(layout, *, ignore_hold_bindings=False, default_repeat_ms=None)`.
  `start()` returns a set of initial `TimedState` values. `press(state, control)`,
  `release(state, control)`, `analog(state, control, value)` and
  `wait(state, milliseconds)` each return a set of successor states.
  `snapshot(state)` returns a JSON-compatible view; `semantics` exposes the
  current contract and scenario choices.
- [`timed_trace.py`](../../archived/exhaustive-stack-search/steam_layout/timed_trace.py) provides
  `parse_trace(trace)` and `replay(model, trace, *, layout_data, options=None)`
  as well as the CLI. Replay follows all branches and records edges between
  successive event snapshots rather than arbitrarily choosing one outcome.

Active normal groups and recursively referenced mode-shift groups are parsed.
A mode-shift command supplies its target source directly, so shift-only inputs
are retained even without an inactive preset binding. Unknown activator kinds,
chord selectors, malformed timing values and dangling targets fail explicitly.

## Timing contract

Separate activators have separate deadlines. If a press starts entries delayed
by 100 and 500 ms, the first is due at t=100 and the second at t=500. Advancing
to t=499 cannot fire the second entry. These clocks replace the old model's
single nondeterministic “later” event.

For the confirmed restart example, a 300 ms timer started at t=0 and restarted
at t=200 is next due at **t=500**. It is neither due at its original t=300 nor
permanently cancelled.

The current simulator makes the following additional policies explicit:

1. **Removal scope:** any executed removal resets every pending start delay,
   including when the removed target is absent. A completed delayed add is
   rearmed when its own target is removed. The full configured start delay is
   counted from the removal time, provided the entry remains eligible.
   This global reset scope is an implementation policy extending beyond the
   author's confirmed restart example; online evidence does not prove every
   case covered by it.
2. **Repeats:** ordinary repeat clocks keep their scheduled intervals. They
   are not all restarted merely because another layer was removed. A delayed
   one-shot add rearmed by removal follows its start delay again. Once a
   delayed repeating entry has fired, removing its target preserves the
   repeat deadline.
3. **Layer transitions while held:** an identical activator fingerprint
   preserves its existing clock across a binding-owner change. A newly exposed
   held binding starts its configured delay; a repeating entry without a start
   delay waits one repeat interval. A newly exposed immediate, non-repeating
   command is suppressed until a qualifying activation occurs.
4. **Release ownership:** release activators are selected from the control's
   current effective binding at release time. The simulator does not invent
   release actions from a previous owner that has been overridden.
5. **Concurrent commands:** entries due together are selected from one snapshot
   and executed as an atomic batch, considering every order of those entries.
   Within an entry, binding-array commands execute bottom to top. Binding
   eligibility is refreshed after the batch. Reaching a deadline with `wait`
   processes the timer before the next separately supplied physical event.

Base cannot be removed. Adding an already-active layer leaves its position
unchanged; removing and adding it places it on top. Always On activators use
the same clock scheduling rather than an arbitrary untimed firing event.

## Mode shifts and thresholds

A fired mode shift remains attached to the physical control that activated it
until that control is released or its chord condition ends, including across
binding-owner changes. A shifted group replaces its complete target source;
an input absent from the shifted group does not fall through to the unshifted
group. Multiple active shifts are resolved using their activation order.

Soft Press entries with an explicit threshold require an analog sample.
Normal thresholds use `magnitude > threshold`; inverted thresholds use
`magnitude <= threshold`. The equality rule is an explicit model assumption,
not a measured Steam boundary. A missing numeric threshold is not inferred
from group settings. Digital inverted click inputs can instead represent the
click being released. Group-specific analog processing and controller sensor
behavior are not reproduced. In particular, `analog(edge, 1)` can activate
ordinary edge bindings in this contract; it does not establish that a tiny
physical deflection activates the saved layout's outer ring.

[`source_geometry.py`](../../archived/exhaustive-stack-search/steam_layout/source_geometry.py) separately
resolves explicitly saved source settings and their defining layers. For
example, Base RST has ring radius 32767 and deadzones 3280/32000. Sensitivity
overlays preserve inherited geometry. The helper requires explicit defaults
for missing ring settings and an equality policy at the boundary. It is not
silently inserted into the runtime: doing so would change its event alphabet,
analog quotient, witnesses and proof identity. Valve documents
[ring radius and inversion](https://partner.steamgames.com/doc/features/steam_controller/input_source_modes)
and [layer setting inheritance](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers),
but these pages do not settle every numeric boundary or Soft Press interaction.

## Fact completeness without exhausting the graph

The three requested answers are finite projections of the full ordered stack:
layers below/above X, and each raw input's inherited owner and original
activators. The default 90.6 layout has **46,904 catalogue alternatives**
across 72 layers including Base. An above relation reuses the corresponding
below fact, so it is not counted twice in the global catalogue.

The timed fact audit combines two independent forms of evidence:

1. **Concrete witnesses:** `timed_facts.py` records complete timed states and
   parent events. Every retained edge must replay through `TimedModel`.
   `timed_discover.py` samples additional traces and can import a matching
   timed-search database. Its time, step and branch budgets only limit witness
   discovery; stopping never proves an exclusion.
2. **Inductive exclusions:** `timed_envelope.py` keeps the full ordered stack,
   held controls and threshold predicates while allowing additional timer
   firings and mode-shift histories. Each command batch selects entries from
   one snapshot and retains their possible execution orders.
   `timed_phase_envelope.py` strengthens this upper bound with consequences of
   the runtime's timer and press phases. `timed_progress_envelope.py` adds
   restrictions on what a faster repeater must do before a delayed entry can
   fire. `timed_elapsed_envelope.py` separates elapsed repeats from immediate
   one-shots, and `timed_analog_envelope.py` preserves the mandatory first batch
   after a positive analog sample. `timed_proof.py` uses this
   `TimedAnalogEnvelope` production compiler
   and checks candidate invariants over the larger system until a fixed point,
   then independently validates initialization and preservation. Symbolic
   batch projections reduce checking cost; they do not replace the stack with
   pair-based search states. `timed_predicates.py` adds family disjunctions
   (at least one listed layer must be below X or between an ordered pair) and exact catalogue-fact
   exclusions. `TimedProof.refine` checks additional hypotheses while retaining
   a verified baseline; suggested hypotheses never count as proof by themselves.

`timed_audit.py` classifies every alternative as `proven` (a replayed witness),
`excluded` (checked induction), or `possible` (still unresolved).
**A report is complete for this model when no alternative remains possible.**
This does not require enumerating or closing the entire timed state graph.
It also does not certify physical realizability beyond the logical-input
contract above. An unobserved fact is never excluded merely because discovery
stopped or a solver timed out.

Per-layer completeness includes both below and above relations, including
above facts whose catalogue target is another layer. Full-report counts use
unique fact IDs; summing per-layer counts would count shared relations again.
JSON retains all excluded alternatives, original inherited activators and
witness node/trace IDs. A report for selected layers also records
`global_complete_for_model` for the whole catalogue.

### Runtime-derived batch restrictions

The production compiler retains the full stack and each batch's entry order.
It inherits six phase rules from
[`TimedPhaseEnvelope`](../../archived/exhaustive-stack-search/steam_layout/timed_phase_envelope.py), extended
to positive analog first batches as described below:

1. A positive-start-delay entry cannot share a due batch with a zero-start,
   nonrepeating entry. Existing due activations advance before execution and
   refresh; newly created or reset positive delays lie strictly in the future.
2. An unconditional zero-start, nonrepeating Full Press fires only on its own
   rising edge. Every occurrence of its fingerprint must be unconditional:
   either uninterruptible, or in a complete binding with no chord activators.
   Always On is exempt. Checking the whole fingerprint family includes normal
   and mode-shift bindings. The production analog compiler handles both press
   and positive-analog rising edges, including controls with Soft Press entries.
3. A delayed one-shot D cannot fire while a repeating remover R is eligible
   when both fingerprints occur exactly once, they have the same numeric
   owner, R has zero start delay, D's delay exceeds R's period, and no mode
   shift targets R's source. R's removals keep resetting D; at batch selection,
   whenever both timers are pending, D's deadline is strictly later. R's eligibility remains
   in the guard even if a projection omits R's layer operations.
4. The first batch after a physical press can select another control's entry
   only if that entry was previously ineligible. Already eligible entries
   retain completed or future activations: the press advances no time and
   preserves the existing layer stack and latched shifts. Eligible own-control
   entries with zero start delay remain mandatory.
5. A zero-start, nonrepeating chord with a non-Always On control fires only
   in the first press or positive-analog batch. A modifier's press or analog
   rise may activate a chord on an already held control. Releases cannot make the
   positive held/chord condition true, and later binding exposure suppresses
   immediate firing.
6. Every zero-start entry that becomes eligible in the first press or
   positive-analog snapshot must fire in that batch, including another
   control's newly activated chord.
   The binding lookup is unchanged, so it was already bound. Its previous
   ineligibility rules out an existing activation, and the unchanged raw-input
   binding prevents an activation transferring from another owner. Refresh
   therefore creates a deadline at the current instant.

These rules start from reachable states whose previous due timers have been
drained. Alias matching uses canonical physical controls. A rising analog
sample on a control with no Soft Press is represented by the corresponding
press transition. The standalone phase component conservatively exempts
controls with Soft Press occurrences from its press-only rules; the production
analog component handles their positive samples directly and removes that
global exemption. Actual Soft Press entries and Always On entries keep their
automatic-activation exceptions. The compiler still permits additional timing histories; remaining alternatives
need witnesses or further checked exclusions before completeness is claimed.

### Ordered-owner progress restriction

[`TimedProgressEnvelope`](../../archived/exhaustive-stack-search/steam_layout/timed_progress_envelope.py)
adds the following restriction on automatic batches and is inherited by the
production compiler. All five compiler files are included in the certificate's
algorithm identity. These refinements
strengthen the symbolic upper bound; **they do not change `TimedModel`.**

Let D be a delayed, nonrepeating entry and R a zero-start repeater with period
P. D's start delay must be **strictly greater than P**, and every occurrence
of both fingerprints must have a numeric layer owner. D's raw source must
have no mode shifts. R's source must also have no mode shifts, unless the
physical exception below applies.

Under those structural conditions, D cannot fire in a snapshot where all of
the following hold:

- R is eligible.
- **Every present owner of D's entire fingerprint family** is at or above
  R's selected owner in the stack. Checking only the currently bound D owner
  would miss timers transferred from an older, lower owner.
- R contains any removal command, **or** at least one target added by R is
  currently absent. An absent-target removal still counts as a removal.

At batch selection, while these conditions hold and D is pending, D's
deadline is later than R's. R has at most P milliseconds remaining. When R
fires, its removal resets D, or its additions make every added target present.
Making an added target absent again requires a removal, which resets D.
A newly eligible R in an already selected binding fires immediately. Exposing
a new R binding requires a removal or adding R's owner; an aged D's earlier
owner then lies below R and makes the all-owner condition false. Transferring
D's clock to another owner preserves that earlier owner until a removal
resets the clock. R's eligibility and absent-target checks remain in the guard
even when a projection omits R's layer operations.

The physical exception permits a shifted R source only when **every shift
origin** is incompatible with keeping D's and R's own controls held together.
This exception excludes actual Soft Press entries and Always On inputs.
A non-Soft entry remains eligible for the exception even if another activator
on its control is Soft Press: the non-Soft entry still requires its own control
to be held. The compatibility check canonicalizes aliases and supplies required stick/pad touches and
trigger edges before checking conflicts, so a missing prerequisite cannot be
mistaken for physical incompatibility. An aged D and held R cannot coexist
with any such latched shift origin; ending a shift therefore cannot expose R
while preserving an aged D. These exemptions apply to the physical exception;
the unshifted-source case does not require physical incompatibility.

### Elapsed-repeat batches

[`TimedElapsedEnvelope`](../../archived/exhaustive-stack-search/steam_layout/timed_elapsed_envelope.py) extends
the phase and progress restrictions. Repeating versions of the qualifying
unconditional Full Press and positive-chord families can first fire immediately
on a press or positive sample. A binding exposed later while held waits one
repeat interval; a transferred activation preserves its existing deadline.
Their automatic firings therefore require elapsed time and cannot share a
batch with a newly created zero-delay, nonrepeating activation. The runtime
advances every previously due timer before commands execute and refresh creates
new activations. Their first physical/analog batch can still contain both.

Full Press repeats remain restricted to their own control in the first press
batch; chords can be activated by another control. Complete fingerprint-family
checks prevent a conditional Full Press copy from transferring an immediate
release-unblock activation into a supposedly elapsed-only family. Soft Press
and Always On activators keep their automatic exceptions.

### Positive analog first batches

[`TimedAnalogEnvelope`](../../archived/exhaustive-stack-search/steam_layout/timed_analog_envelope.py) is the
production compiler. It exposes five stable transition families:
`press`, `release`, `analog_positive`, `analog_zero`, and `automatic`.

A positive sample increases or preserves held membership, so existing positive
chord conditions cannot end a latched mode shift. Before the first batch, the
stack and binding choices are unchanged. The compiler executes **exactly the
zero-delay entries that are eligible after the sample and were ineligible
before it**, together in every possible command order. This includes threshold
crossings while a control remains held, raw aliases, and newly activated chords
on other controls. Already eligible activations remain completed or scheduled
for a future deadline.

A zero sample retains the mandatory release-command prefix. Inverted Soft
Press activators may become eligible there and are allowed to fire in a later
automatic batch. Layer-effect projections retain the complete pre-state
eligibility conditions and preserve all relevant command orders. This compiler
changes neither the concrete timed runtime nor the logical-input geometry
contract.

### Discover, compact and check

Run these commands from the repository root. The proof stage uses the optional
Z3 dependency; discovery and replay do not require it.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-proof.txt

.venv/bin/python -m steam_layout.timed_discover \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-discovery.sqlite \
  --ignore-hold-bindings --default-repeat-ms 50 \
  --seconds 120 --max-steps 10000 --seed 0 \
  --summary out/stack_search/timed-facts/default-discovery-summary.json
```

An existing archive resumes automatically after its recorded edges are checked.
`--import-search out/stack_search/default-timed.sqlite` can add witnesses from
a matching timed search. The Python `discover_from_untimed` helper can also
try old search traces as suggestions, but accepts only newly replayed timed
states; an old stack or HeldModel proof is never imported as timed evidence.

Compaction keeps the ancestors needed for all witnessed facts in a separate
archive. Choose a fresh destination; the discovery archive remains available
for further exploration. The example uses `regenerated-*` outputs to preserve
the saved checkpoint. A fresh `timed_audit run` infers primitive invariants;
it does not load the saved proof's additional checked families and may produce
a weaker baseline. To retain and extend that proof, use
[`timed_refine`](#refine-an-existing-certificate).

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from steam_layout.timed_facts import FactCatalogue
from steam_layout.timed_discover import compact_archive

layout = Layout(json.loads(Path("versions/neptune/90.6/single-set-default_hold-gyro_90.6.json").read_text()))
model = TimedModel(layout, ignore_hold_bindings=True, default_repeat_ms=50)
compact_archive(model, FactCatalogue(model),
                "out/stack_search/timed-facts/default-discovery.sqlite",
                "out/stack_search/timed-facts/regenerated-evidence.sqlite")
PY

.venv/bin/python -m steam_layout.timed_audit run \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/regenerated-evidence.sqlite \
  out/stack_search/timed-facts/regenerated-certificate.json \
  out/stack_search/timed-facts/regenerated-audit.json \
  --ignore-hold-bindings --default-repeat-ms 50
```

Inspect the saved checked checkpoint independently of that regeneration:

```sh
.venv/bin/python -m steam_layout.timed_audit show \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-evidence.sqlite \
  out/stack_search/timed-facts/default-certificate.json \
  'L1: Double Tap' --json \
  --ignore-hold-bindings --default-repeat-ms 50
```

`run --layer NAME` limits the output layers; it does not weaken induction.
Exit 0 means a report was produced, not that it is complete: inspect
`complete_for_model` and the unresolved count. `--timeout-ms` bounds individual
solver calls (default 10000); unknown induction checks discard unproved
candidates, and unknown fact queries leave alternatives possible.

Certificates contain invariant hypotheses, the full quotient identity, and
hashes of the proof, all five envelope compilers, batch, invariant, predicate and
fact implementations.
`show` reloads and checks every archived edge, rejects mismatched identities,
and independently reruns certificate validation before using exclusions.
Serialized `verified` flags are not trusted. Validation can be reused within
one process while the identity and invariant set are unchanged.
Typed predicate payloads preserve family members. Fact-exclusion payloads
identify a catalogue alternative; loading restores its raw-input aliases and
defining layers from the layout instead of accepting supplied definer context.

**Production status remains incomplete for default 90.6.** The current
[summary and readable layer reports](README.md#checked-current-checkpoint)
accompany the matching certificate and full audit. There are **11,491 witnessed,
31,644 excluded and 3,769 unresolved** alternatives, with
`complete_for_model: false`. The certificate's **901 invariants passed 3,409
independent validation checks** using all five event families.
The final regression suite
passed **531 tests in 106.323 seconds**
([log](../../out/stack_search/timed-final-tests.log)).

The historical timed baseline in
[`default-base-report.json`](../../out/stack_search/timed-facts/default-base-report.json)
classifies **10,245 alternatives as witnessed, 24,207 as excluded, and 12,452
as unresolved**. Its evidence archive, `default-orphan-witness.sqlite`, retains
7,241 nodes. The matching `default-base-certificate.json` contains 1,373
compacted invariants (from 3,223 primitive invariants and 11 family
disjunctions), independently verified by 4,021 checks. The full 430-test suite
passed in 106 seconds at this baseline. A [compact summary and four layer
reports](README.md#historical-timed-baseline) preserve the earlier result for
review; they are extracted from the validated report without another solver
run. This measurement predates the phase and progress compilers. Its saved
`default-base-certificate.json` has the old algorithm hash, so current tools
correctly reject it. Use `timed_audit run` above to generate a certificate for
the current compiler when generating a new baseline. The current checkpoint
uses the phase, progress, elapsed-repeat and analog refinements described above.

### Seek witnesses for selected facts

[`timed_seek.py`](../../archived/exhaustive-stack-search/steam_layout/timed_seek.py) searches for concrete traces
for selected catalogue alternatives. Targets are JSON rows `[kind, x, y, j]`,
either in a list or an object with `facts` and optional text `scope`. `kind` is
`below` or `inherit`; `below` uses `j=-1`. All indices are checked against the
chosen layout, and inheritance definitions come from its catalogue.

```sh
.venv/bin/python -m steam_layout.timed_seek \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-unresolved.json \
  out/stack_search/timed-facts/default-targeted-witness.sqlite \
  --input-archive out/stack_search/timed-facts/default-evidence.sqlite \
  --seconds 120 --per-target-seconds 0.2 \
  --ignore-hold-bindings --default-repeat-ms 50
```

Supply `--seconds`, `--max-events`, or both. The command checks the input
archive, retains all command-order outcomes of sampled events, and writes a
compact archive plus `OUTPUT.sqlite.summary.json`. Each requested fact is
reported as `witnessed` or `unresolved`; exhausting the search budget proves
no exclusion, and `complete_for_model` remains false. Equivalent inheritance
predicates share a search. `--per-target-events`, `--max-frontier` and
`--seed-limit` control exploration size.

The output can equal `--input-archive` for an atomic replacement after replay
and compaction. Layout and target files cannot be output destinations; the
summary must have a separate path from all inputs and the output archive.

### Minimize a checked certificate

[`timed_minimize.py`](../../archived/exhaustive-stack-search/steam_layout/timed_minimize.py) removes predicates
that follow from the remaining conjunction under the symbolic state domain.
It independently validates both the input certificate and the reduced output:

```sh
.venv/bin/python -m steam_layout.timed_minimize \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-certificate.json \
  out/stack_search/timed-facts/default-minimized-certificate.json \
  --ignore-hold-bindings --default-repeat-ms 50 \
  --timeout-ms 10000 --minimize-timeout-ms 100
```

Unknown entailment checks retain their predicate. The smaller conjunction
preserves the same logical bounds; it can reduce later validation work.
The lower-level `minimize_hypotheses` helper only preserves logical equivalence
and never turns unvalidated hypotheses into a checked proof.

### Mine conditional family hypotheses

[`timed_between.py`](../../archived/exhaustive-stack-search/steam_layout/timed_between.py) suggests a small
family of binding owners that appears between a witnessed ordered pair. For
an unresolved inheritance alternative, a proved `RequiresBetweenAny(X, Y,
members)` excludes ownership by Y when every member defines that raw input:
at least one of those bindings must override Y before reaching X.

The miner replays the archive and accepts the same strict target rows as
`timed_seek`. It only considers pairs actually seen together, then finds one
minimum-size sampled cover per distinct target formula. The following uses
the saved phase5 diagnostic targets solely to select hypotheses:

```sh
.venv/bin/python -m steam_layout.timed_between \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-phase4-seek-witness.sqlite \
  out/stack_search/timed-facts/default-phase5-unresolved.json \
  out/stack_search/timed-facts/default-between-hypotheses.json \
  --ignore-hold-bindings --default-repeat-ms 50 --max-members 5
```

The result is explicitly **unvalidated**, regardless of sample coverage or
search exhaustion. `--max-search-nodes` and `--seconds` limit suggestion
work; they cannot establish exclusions. Pass the output through
`timed_refine --family-hypotheses` to check it. The separate `timed_mine`
command proposes unconditional `RequiresBelowAny` families from lower-stack
prefixes, using positional arguments `LAYOUT ARCHIVE OUTPUT` and the same
model and search-budget options.

### Refine an existing certificate

[`timed_refine.py`](../../archived/exhaustive-stack-search/steam_layout/timed_refine.py) replays a matching
witness archive, independently checks the baseline certificate, and recomputes
which alternatives remain unresolved. It proposes one `FactExclusion` for each
distinct unresolved formula, sharing hypotheses across raw inputs with the
same defining layers. It then checks those hypotheses against the preserved
baseline and independently validates the combined result before saving a new
certificate. The report still classifies every original catalogue alternative.

Use the current `default-certificate.json` and its compact 90.6 evidence archive.
This reuses a
matching checked proof; the historical `default-base-certificate.json` is not
a compatible input to the current compiler:

```sh
.venv/bin/python -m steam_layout.timed_refine \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/timed-facts/default-evidence.sqlite \
  out/stack_search/timed-facts/default-certificate.json \
  out/stack_search/timed-facts/default-next-certificate.json \
  out/stack_search/timed-facts/default-next-report.json \
  --ignore-hold-bindings --default-repeat-ms 50 \
  --timeout-ms 10000 --refine-timeout-ms 1000 \
  --family-hypotheses out/stack_search/timed-facts/below-family-hypotheses.json \
  --checkpoint out/stack_search/timed-facts/default-next-hypotheses.json
```

The optional family file contains `{"candidates": [...]}` with serialized
`RequiresBelowAny` or `RequiresBetweenAny` hypotheses. These are checked suggestions, not trusted
exclusions. The optional checkpoint saves the fixed-point hypotheses and
statistics **before independent validation** for manual recovery. It is marked
unvalidated and cannot be loaded as a certificate. Validation failure produces
no new certificate or report.

`--layer 'L1: Double Tap'` limits generated fact hypotheses to that layer's
below, above and inheritance questions; repeat it for more layers. Explicit
family hypotheses are still checked. **The saved report always covers the
full catalogue.** Its `complete_for_model` and `global_complete_for_model`
refer to that global report. The `refinement.selected_complete_for_model`
field, also printed by the CLI, describes only the selected questions.

`--timeout-ms` controls individual validation and fact-query calls;
`--refine-timeout-ms` can use a different limit for candidate induction and
otherwise defaults to the same value. Unknown induction checks discard
unproved hypotheses. Exit 0 means validated outputs were written, not that
the report has no unresolved alternatives. This command requires the optional
solver dependency from `requirements-proof.txt`.

## Reachability search and proof checks

The timed runtime now has a separate SQLite reachability engine. It explores
**all integer-millisecond event sequences**, without an event-depth or elapsed
time cap. This precision belongs to the runtime contract; it does not establish
coverage of fractional-time events or Steam frame scheduling. Resource budgets stop with an explicit open frontier and can be
raised on resume. They do not turn unobserved behavior into an exclusion.

```sh
# New search; the state limit is a resource budget, not a completeness claim.
python3 -m steam_layout.timed_search run \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/default-timed.sqlite \
  --ignore-hold-bindings --default-repeat-ms 50 --max-states 25000

# Continue the same graph under exactly the same runtime/scenario.
python3 -m steam_layout.timed_search run \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/default-timed.sqlite \
  --ignore-hold-bindings --default-repeat-ms 50 --resume --max-states 50000

# The original three questions: layers below/above X, and inherited raw bindings.
python3 -m steam_layout.timed_search show \
  versions/neptune/90.6/single-set-default_hold-gyro_90.6.json \
  out/stack_search/default-timed.sqlite 'L1: Double Tap' \
  --ignore-hold-bindings --default-repeat-ms 50
```

`witness LAYOUT DATABASE STATE_ID` replays a stored witness and returns a JSON
trace, combining consecutive millisecond waits. `check LAYOUT DATABASE`
independently verifies a completed graph. Both commands require the same
`--ignore-hold-bindings` / `--default-repeat-ms` choices as the search.
`show --json` includes full activators, witness IDs and the proof certificate
when available. No solver dependency is required by these timed commands.

The finite quotient removes only distinctions that do not affect this model:

- Normalize absolute time to zero and keep **every remaining deadline**.
  Pending timers advance one millisecond at a time, so an input can still
  occur at every integer instant between distinct deadlines.
- For each physical control, collect Soft Press thresholds from every layer
  and referenced shift group. Zero is separate; a positive interval `(a, b]`
  uses its upper boundary as representative. All strict `>` / inverted `<=`
  comparisons therefore keep their truth values. Missing samples remain
  distinct from explicit zero. Samples on controls without any Soft Press
  entry are redundant with held state and can be removed.
- Preserve the entire ordered layer stack, held controls, activation stages,
  fired flags and ordered mode shifts. This is not the earlier top-K or
  layer-pair approximation.

Each remaining clock is bounded by a configured delay or repeat interval.
There are finitely many control/analog states, layer orders, activations and
mode shifts. Thus the quotient is finite even though elapsed wall time and
event count are unbounded. This does **not** promise that a large layout's
reachable graph is small enough to finish in practical time.

An expansion commits every new successor and its parent's expanded flag in
one transaction. If the state budget would be exceeded, that entire expansion
stays pending. Runtime errors and interrupts also preserve an open frontier.
`--max-seconds` is checked between complete expansions, not inside a command
batch. Model, layout, quotient-code and format identity must match on resume;
existing databases are never overwritten by a new run.

A completed graph is checked independently before a report excludes anything:

1. It must contain every initial state.
2. Every stored state must have a replayable path from an initial state.
3. Recomputing every possible successor must stay inside the stored set.

These are reachability and inductive-closure checks over the versioned timed
model. Merely setting database rows to expanded cannot create a valid proof.
For partial searches, `proven` requires a replayed timed witness and every
unobserved static alternative stays `possible`. In `timed_search` reports,
`complete_for_model` requires both an exhausted frontier and a verified closure
certificate. The separate `timed_audit` route above can instead complete the
finite fact catalogue through checked induction and witnesses. Inheritance
remains the raw binding below X, even with another layer above X; it does not
assert which chord fires or substitute an active shifted source's commands.

The implementation is split into `timed_search.py` (quotient, exploration,
witness/closure verification and CLI), `timed_store.py` (durable graph and
parent traces), and `timed_report.py` (the three layer projections).

### Exact relevance reduction

`timed_reduction.py` supplies `ReducedTimedQuotient(model)`, a separate
`TimedQuotient` subclass usable with the same `TimedStore`, `run_search`,
`WitnessVerifier` and `verify_closure` APIs. It preserves full ordered-stack
reachability while removing irrelevant controls, irrelevant analog distinctions
and unused fired flags, and canonicalizing independent mode shifts. Chord
dependencies and required touch/edge parents are retained. Remaining clocks
still advance one millisecond at a time.

Its identity includes the full reference quotient, reduction implementation and
reduced event alphabet. Existing full-quotient databases are unchanged and
cannot be resumed as reduced databases. A trace containing discarded controls
must first replay through the full `reference` quotient; the resulting states
can then be projected with `normalize`. These reductions are specific to the
current runtime contract and would need review if source geometry began
affecting ordinary edge activators.

## Scope and validation

This work does not implement Steam `hold_layer` ownership, action-set switching,
output-key lifetimes, nonzero `delay_end`, or delayed release activators.
Nonzero end delays and delayed/repeating release activators are rejected when
constructing the runtime. Unsupported settings on layer/shift commands or chord
guards also fail explicitly. Output-only commands
remain in fingerprints and guards but are not emitted to a controller or game.

The existing `HeldModel`, compiled search database, symbolic transitions and
Houdini proofs remain separate. Their witnesses and exclusions do not become
timed-runtime evidence by replaying this CLI. The timed engine supports
exhaustive finite-state closure and a separate symbolic envelope. The envelope
retains the full ordered stack and held controls while admitting additional
timer firings and mode-shift histories. Every real timed event has a path
through this larger system. Its inductive exclusions therefore bound the
timed model; its possible states are not witnesses. Successful trace replay
establishes one sequence, while a verified closed graph establishes all
reachable states under this contract.
Neither establishes correspondence to hardware. The [online evidence](ONLINE-EVIDENCE.md)
supports specific documented behaviors; it is not a proof of the entire
runtime contract above.

Validation recorded at the initial timed-search milestone (before the later
fact discovery, induction and relevance-reduction modules):

- Full regression suite: **311 tests passed** (including 105 timed tests),
  using `.venv/bin/python -m unittest discover -s tests`.

- 22 search/quotient tests, 20 persistent-store tests and 12 report tests pass,
  including interrupted/resumed search, exact clock and analog reductions,
  transactional budget rollback, stale identity rejection, forged-completion
  rejection, witness replay and all four search CLI commands.
- 23 runtime tests pass, covering separate deadlines, restart scope, repeat
  continuity, held binding replacement, all 24 orders of four simultaneous
  commands, shifts, thresholds, physical release and zero-time cycle detection.
- 20 parser tests pass, covering exact timing, command order, validation,
  fingerprints, hold omission, selector controls, mode-shift discovery and
  both 90.6 layout variants.
- 8 trace/CLI tests pass, covering exact deadlines, branch preservation,
  input validation and evidence identity.
- The Menu Left example passed on both 90.6 variants with explicit repeat
  assumptions of 50 and 900 ms. Each run opens Entry Point at t=0, adds Fn at
  t=300, then returns to Base on release, with five recorded hold omissions.
  Matching this example at two intervals does not establish equivalence for
  every other trace.

Measured search results on 2026-09-30:

- A small three-layer fixture with a 3 ms delayed add closes at **5 states /
  8 edges**. Independent checking verifies initialization, every retained
  witness and transition closure. Its Late-layer report has 2 witnessed
  facts, no unresolved facts and 4 exclusions.
- The default 90.6 layout resumed successfully from a 2,499-state resource stop
  to **25,000 states** (2,586 expanded, 22,414 pending). That resumed run took
  about 9.3 seconds. It remains incomplete. L1 Double Tap has 38 witnessed
  projection facts and 495 unresolved alternatives, with **no exclusions**.
  These counts use the explicit 50 ms assumed repeat default and omitted
  hold commands; they cannot be compared as the same model as older proofs.

Generated reports and databases are under `out/stack_search/`: default
90.6 uses `default-timed.sqlite`, `default-timed-summary.json`, and
`default-timed-l1-report.json`; the closed fixture is in `timed-proof-example/`.
The full regression log is `timed-search-tests.log`.

Run the focused suites with:

```sh
python3 -m unittest discover -s tests -p 'test_timed_*.py' -v
```
