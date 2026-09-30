# Stack search: the three questions and what we tried

**Status:** paused 2026-09-30. Tools built and tested; no approach yet gives
answers that are both definite and realistic. Pick up at [Next step](#next-step).

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
one thumb per place, delays, repeats, `hold_layer`), no depth or event cap.

For a **known stack** all three are exact and instant from the layout JSON
(`StackDB.values(stack)`). The hard part is knowing **every stack that can
happen**.

## Model decisions (author-confirmed)

- Re-adding an active layer does not move it (ABC + add A stays ABC); remove
  then add puts it on top. Confirmed on the Deck and in Valve's docs.
- Missed releases (Steam menu open while releasing) are **left out**: cleanup
  functions exist to recover from them. `--missed` turns them back on.
- Hand model: each thumb is in one place (left: stick, pad, D-pad or Menu Left;
  right: stick, pad, face buttons or Menu Right). Any combination of face
  buttons, D-pad, bumpers with triggers, and back buttons is allowed.
- A pad chord means "thumb on the pad" (touch). An input stays held in the model
  only when its timing matters: a chord checks it, or it has a release entry, a
  `hold_layer`, or a delayed or repeating layer command. Everything else is a
  press-and-release.
- Releasing a button removes the layer its `hold_layer` holds.

## What we tried

Default layout, `neptune/single-set-default_hold-gyro_latest.json`, 72 layers.
"Events" are button presses, releases, holds, taps and Always On timers.

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

## Next step

**Prove invariants instead of enumerating states** (the Houdini method from
program verification):

1. Candidate facts come from the search: everything it never saw, such as "Y is
   never below X" or "X present means button b is held".
2. A fact is proven if it holds at the start and **no single entry in the
   layout can break it**, assuming the other candidate facts hold. Failing
   candidates are dropped and the check repeats until nothing changes. This is
   a check per entry: seconds, no event cap, and it keeps held buttons and
   cleanups (they appear in the facts).
3. Proven facts are definitely impossible. What's left is either real (search
   deeper for a button sequence) or needs a stronger fact.

Then build the helper: `python3 -m steam_layout.stackdb show "LAYER"` listing
below/above layers and every inherited input with its value, each marked
*proven* or *possible*, derived at run time.

Risk: some true facts may need more than "layer pairs" or "layer implies
button held" to prove; those stay on an open list.

## Tools

| Piece | What it does |
|---|---|
| `steam_layout/held_model.py` | Realistic model (`HeldModel`); `TopModel` for the top-K bound |
| `tools/stack_search/rules.hpp` | The same rules in C++, shared by both engines |
| `tools/stack_search/stack_search.cpp` | In-memory exhaustive search (`--held`, `--missed`, `--top K`, `--memory-limit`) |
| `tools/stack_search/stack_search_disk.cpp` | Disk-backed search (`--memory`, `--disk-limit`, `--resume`) |
| `steam_layout/stackdb.py` | Runs the engines; SQLite store; `values`, `moment`, `inheritance`, `inherited_values`, `witness`, `sql` |
| `tests/test_held_model.py`, `test_stack_search*.py`, `test_top_model.py` | Engines agree exactly with the Python reference; soundness of `TopModel` |
| [scripts/](scripts/) | The analyses behind rows 8–12 (read `out/stack_search/default-held`) |

Regenerate the data the scripts read (about 2 minutes, stops at 12 GB):

```bash
python3 -m steam_layout.stackdb run neptune/single-set-default_hold-gyro_latest.json \
    out/stack_search/default-held --held --threads 14 --memory-limit 12
python3 findings/2026-09-30-stack-search/scripts/rule.py
```
