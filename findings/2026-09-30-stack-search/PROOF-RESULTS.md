# Invariant checker results — 2026-09-30

The helper now runs to an inductive fixed point without enumerating all states.
It substantially tightens the earlier rule, but does **not** yet settle every
fact. All results below are relative to `HeldModel`; its [runtime gaps](MODEL-LIMITS.md)
remain a separate obstacle to answers that are both complete and realistic.

## Measured run

Default Neptune layout, Python 3.9.6, Z3 5.1.0, 10,000 ms per solver call:

- 6,860 initial candidate invariants; 4,720 survived induction.
- Four rounds; 2,783 solver checks; 1,090 previously proved checks reused by
  their assumption dependencies.
- 1,619 complete event branches share 659 distinct symbolic updates.
- Induction took **226.041 seconds**. This excludes subsequent evidence scans
  and report queries. The proof was reused for all four layer reports.
- **No induction or query timeouts.** Remaining uncertainty in these reports
  was not caused by a solver timeout.
- Search evidence came from `out/stack_search/default-held`: 186,339,683
  states, complete through 10 events. That depth limits only the available
  positive witnesses; the inductive exclusions have no event/depth limit.
- Every reported positive witness was replayed from Base through the current
  Python reference, including its final stack.

Layers below X, **excluding Base** to match the earlier comparison:

| Layer | Witnessed | Earlier rule upper bound | New inductive upper bound | Still unresolved |
|---|---:|---:|---:|---:|
| L1: Double Tap | 19 | 70 | 23 | 4 |
| LST: Double Tap | 7 | 57 | 10 | 3 |
| RTP: Double Tap | 46 | 69 | 49 | 3 |
| L1: Modifier 0 | 20 | 48 | 21 | 1 |

The upper bound includes the witnessed facts. Across each report's below,
above and inherited-value alternatives (including Base where applicable):

| Layer | Witnessed facts | Unresolved facts | Excluded alternatives | Complete for model |
|---|---:|---:|---:|---|
| L1: Double Tap | 62 | 25 | 446 | No |
| LST: Double Tap | 42 | 23 | 468 | No |
| RTP: Double Tap | 117 | 20 | 130 | No |
| L1: Modifier 0 | 97 | 5 | 337 | No |

Exclusions include structural constraints (such as Base never being above a
layer) as well as the learned invariants. Rows are different projected
questions; they are not counts of unique reachable stacks.

## The remaining L1 Double Tap questions

The four unconfirmed lower layers are `R1: Modifier 1`,
`Gyro | R1: Modifier 1`, `L1: Tap Cover`, and `R1: Tap Cover`.
The only unconfirmed upper layer is `R1: Tap Cover`.

Twenty unresolved inherited-value alternatives come from the first two lower
layers: four face buttons, four D-pad directions and both stick clicks, with
two possible owners apiece. These are **open reachability questions**. They
need stronger invariant predicates or concrete witnesses. More of the same exhaustive enumeration is
not required to establish the exclusions already proved.

Retaining order predicates alongside coexistence exclusions mattered. With
only the stronger coexistence guesses for pairs never seen together, the L1
report had 137 unresolved alternatives. Keeping the weaker ordering guesses
reduced that to 25. Raising the solver allowance from 1,000 to 10,000 ms
eliminated timeouts and retained more global invariants, but did not close the
remaining 25 L1 alternatives. The default is now 10,000 ms.

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-proof.txt
.venv/bin/python -m steam_layout.stackdb show 'L1: Double Tap' \
    --search out/stack_search/default-held --json
```

Use the README's search command if that evidence directory is absent.
The full local reports from this run are `out/stack_search/proof-verified-0.json`
(L1 Double Tap), `-1.json` (LST Double Tap), `-2.json` (RTP Double Tap), and
`-4.json` (L1 Modifier 0). These generated files are ignored by Git. Their
summary is `out/stack_search/proof-verified-summary.json`.

Input identity:

```text
layout SHA-256
2243bf4c978360051a19a53ff1ca9217a58263c5624990886f4565f4e78308c0
exported model.txt SHA-256
bd00098ae388a7b2e36191effbf6e3339a2408587d07c9fcfe23679b7241a970
```

Validation: **206 Python tests passed**, including symbolic/reference
comparison on arbitrary valid small states, complete small-layout reports,
induction dependency removal, unknown handling, and corrupted-witness rejection.
The invariant and CLI suites also passed after setting the final default
solver allowance. `git diff --check` passed.

The next work is to investigate the small remaining fact lists and repair the
runtime-model omissions. A stronger proof of the current model alone cannot
repair its missing timing, analog and hold-ownership distinctions.
