# Extra presses in the hidden-exit check

**Status, 2026-10-04:** built. The Cleanup audit's hidden-exit check reads the
chain walk with **6 extra presses**, done by one compiled engine. The build
audit **failed on 90.22** on the 12 pairs below, on purpose: the author wanted
no exception. **90.23 fixed them** the same day
([record](../2026-10-04-tap-cover-stick-touches/README.md)), and the build
audit is clean again.

## Where it ended

Decided by the author on 2026-10-03 and 2026-10-04:

- **A cap on extra presses, not on layers.** "The chain is more accurate than
  the walk." The check follows one layer's chain, as the other audits do, and
  allows six extra presses (arrivals) along it where they allow one.
- **Six is the default.** `--extras K` changes it, from 0 to 14.
- **One engine.** [chain_engine.cpp](../../steam_layout/engine/chain_engine.cpp),
  run by [native.py](../../steam_layout/native.py). The capped walk, the first
  engine and the old check are in
  [archived/capped-walk-and-first-engines](../../archived/capped-walk-and-first-engines/README.md).
- **A C++ compiler is required.** Without one the audit stops with a message.
  It does not fall back to another check.
- **No exception for 90.22.** The audit failed until the layout was fixed, in
  90.23.

What the check does now:

| Step | What |
|---|---|
| Walk | One layer's chain back to Base, with up to six extra presses, to a fixed point |
| Test | Every layer of every stack: is each exit on its keeper answered by that layer, or by one that removes it there? |
| Landing | The same test on every stack one more adding binding past a walked stack |
| Report | For each pair, the smallest stack that shows it, and the bindings that build it with the fewest extra presses |

On 90.22 that is 7,728,211 stacks in about 20 s and 2 GB for one layout. The
Cleanup audit as a whole takes about 27 s for one layout (7.5 s before).
`cleanup_lists` asks for the audit without the exit checks, so the fix
pipeline is as fast as before and needs no compiler.

Checked ([tests/test_native.py](../../tests/test_native.py)):

- The engine gives the same stacks and the same pairs as `chains.py` walked
  with the same number of arrivals, at 0, 1 and 2 on the 90.20 snapshot.
- Every path replays in Python: each binding fires where the path says, and
  the last one leaves the pair's stack.
- One thread and every thread give the same result, paths included.
- Keeping paths or not, and taking the waiting states in small batches,
  change nothing else.
- On both working layouts, 6 extra presses reports every exit the old check
  reported, and more.

The rest of this record is how it got there, in the order it happened. The
sections on the capped walk describe code that is now archived.

## The question

The author asked why the stack walk (the backward chains,
[chains.py](../../steam_layout/chains.py)) only goes "one layer deep", and
whether it could go on without a limit.

- The chain itself has no limit. Three extras around it are limited to one:
  one arrival, one bystander, one landing.
- This record measures what happens when those limits are lifted, and what
  the author decided.

## Terms

| Term | Meaning | Example |
|---|---|---|
| Press | One binding that fires and changes the stack | Select in Base adds `Menu Left: Entry Point` |
| Layers on at once | The layers in a stack, Base not counted | `Base > RST: Entry Point > Menu Left: Entry Point` has two |
| Settled | No press on any stack builds a new stack. The walk is complete | |
| Pair | One lower layer plus one layer that covers one of its exits (R136) | `Menu Left: Entry Point` over `RST: Entry Point` |
| Would fail | A pair on a keeper's exit that no exception sets aside | |

## Without a limit it does not settle

From Base, every followed binding on every stack, in every order. Run on the
90.22 default layout until the author stopped it.

| Presses from Base | Stacks first built by that press |
|---|---|
| 6 | 133,358 |
| 7 | 416,140 |
| 8 | 1,130,913 |
| 9 | 2,720,163 |
| 10 | 5,858,284 |
| 11 | 11,415,202 |
| 12 | 20,256,942 |

- Stopped during the 13th press: 71,472,161 stacks, 966 s, 6.1 GB.
- Each press still built more than the one before, about 1.8 times more at
  the end.
- The 71 million stacks hold only 554,173 distinct sets of layers. The rest
  is the same layers in another order.
- The longest stack had 15 layers on at once.

## With a cap on layers at once it settles

The same walk, but a stack with more than N layers on at once is not built.

| N | Stacks | Presses to settle | Time | Memory | Would fail | Touchpad pairs |
|---|---|---|---|---|---|---|
| 4 | 47,352 | 13 | 1 s | 0.1 GB | 0 | 8 |
| 5 | 243,395 | 14 | 3 s | 0.2 GB | 2 | 8 |
| 6 | 1,108,547 | 15 | 17 s | 0.3 GB | 6 | 8 |
| 7 | 4,176,461 | 16 | 67 s | 0.6 GB | 8 | 8 |
| 8 | 13,283,970 | 17 | 232 s | 1.6 GB | 12 | 8 |
| 10 | 80,430,057 | 20 | 40 minutes | 7.0 GB | 12 | 8 |

- Each extra layer costs about four times more, and the factor falls slowly:
  5.1, 4.6, 3.8, 3.2.
- At 8 layers the walk has every pair the unlimited run found in 12 presses.
- Rows 4 to 8 are from [measure_walk.py](measure_walk.py). Row 10 is the
  Cleanup audit itself with `--walk 10`, which also keeps where each stack
  came from.
- From 8 to 10 layers nothing new is found: the same 12 pairs and the same 8
  touchpad pairs.

## The first cap: 10 layers on at once (replaced)

Decided by the author, 2026-10-03, and replaced the same day by a cap on
presses: at most 10 layers on at once.

- **Basis.** Four fingers add layers in the default layout: the left thumb
  (18 inputs: left stick, left pad, D-pad, Select), the right thumb (13:
  right stick, right pad, face buttons, Start), and LB and RB. One thumb on a
  stick fires up to four inputs. My estimate was eight to ten layer-adding
  bindings in play at once.
- **The estimate is rough.** On 90.22 the chain stacks already reach 12
  layers on at once: 1,866 of 149,087 stacks have more than 10. The largest
  is `Base > Gyro > Cursor Gyro > LST: Entry Point > Gyro | L1: Modifier 0 >
  L1: Tap Cover > Gyro | R1: Modifier 1 > R1: Tap Cover > Gyro | L1!R1:
  Modifier 2 > L1&R1: Tap Cover > RTP: Circular Scroll > LTP: Click Entry
  Point > RTP: Mouse Buttons`.
- **So the cap is not applied to the chain stacks.** Applying it there would
  only drop those 1,866 stacks. It is the limit of the walk, where a limit is
  needed for the walk to finish.

## What was built on 2026-10-03 (archived since)

- **[walk.py](../../archived/capped-walk-and-first-engines/steam_layout/walk.py):** `Walk(layout, max_layers).run()`.
  It follows the same bindings as the chains, keeps every stack in memory with
  the stack it came from, and gives a shortest path for any stack.
  `MAX_SIMULTANEOUS` is 10.
- **The Cleanup audit's hidden-exit check** takes `walk=N`
  (`Cleanups.walked_exits`): it reads every layer of every stack of the walk,
  not the chain stacks. The exceptions and the report are the same.
- **Command line:** `python3 -m tools.audit_cleanups <layout> --walk [N]`,
  N from 1 to 10, default 10, and `--extras K` for the chain walk with K
  extra presses. `--python` keeps `--walk` out of the engine. `--memory GB`
  stops the walk; the audit then fails as not finished.
- **[native.py](../../steam_layout/native.py)** builds the engine with
  `clang++` on first use, into `steam_layout/engine/build/` (ignored by git),
  and falls back to Python when there is no compiler.
- **`chains.py`** takes `workers`; the default is one process, so the other
  audits run as before.
- **Tests:** `tests/test_walk.py` (18) and `tests/test_native.py` (12). The walk's lookup is checked
  against `flow_model.resolve` on the 90.20 snapshot, and a made-up layout
  has a cover two landings away that the chain check can't see.
- **Not changed:** `audit_build` runs the Cleanup audit without the walk, as
  before. The Window and Flow audits and the layer report still read the
  chain stacks.

## What the walk finds on 90.22

Twelve pairs would fail, all one gap: `Menu Buttons: Tap Cover` directly over
a pad layer that keeps the right stick in mouse mode. The Tap Cover is in
D-pad mode and binds only the edge, so nobody answers the right-stick touch
and the thumb lift is lost.

| Upper | Lower | Layers on at once |
|---|---|---|
| `Menu Left: Entry Point`, `Menu Right: Entry Point` | `RST: Entry Point` | 5 |
| | `RST: Tap Cover`, `RST: Temporary Gyro` | 6 |
| `Stateful \| Menu Left: Entry Point`, `Stateful \| Menu Right: Entry Point` | `RST: Entry Point` | 7 |
| | `RST: Tap Cover`, `RST: Temporary Gyro` | 8 |

- The audit names the menu Entry Point because it is the first layer above
  that changes the right stick's mode. The printed stack shows the Tap Cover
  on top.
- Seven layers can sit directly under the Tap Cover in mouse mode:
  `RTP: Entry Point`, `RTP: Click Entry Point`, `LTP: Click Entry Point`,
  `Escape`, `Enter`, `Tab`, `Backspace`. Five of them have been there since
  90.10.
- On the press simulator (90.20, A13 as assumed): right thumb on the stick,
  hold Select or Start, push the left stick, touch the right pad, lift the
  right thumb. `Base > RST: Entry Point` is left behind, in both layouts.
- Eight more pairs fall under the touchpad exception: the two Steering stick
  Double Tap windows over `LTP: Arrow Keys`, `LTP: Middle Click`,
  `RTP: Middle Click` and `RTP: Mouse Buttons`.

## Why the chain check misses it

Measured on 90.20, before the walk was built.

- The chains do build the stack: it is one of 11,604 stacks under the Tap
  Cover (one arrival plus a bystander). In 3,448 of them nobody answers the
  right-stick touch.
- `Chains.above()` keeps one example stack per pair, and the hidden-exit
  check tests only that one. It is a good one.
- Testing every chain stack (about 153,000, 2.4 s per layout) finds the six
  pairs of 90.20. Firing one more binding on every chain stack finds the
  eight touchpad pairs. Neither change was built; the walk covers both up to
  its cap.
- A trial of the layout fix on scratch copies: the Tap Cover gets the guards'
  two stick-touch inputs, without the add of itself. The six pairs go away,
  the other audits pass, and the simulator ends on `Base`. It makes two
  information pairs (the Tap Cover over each stick guard's edge exit) fail as
  "exit to review", because the Tap Cover counts as changed.

## Making it faster

Asked by the author the same day: every core first, then a compiled language.
All times are for the 90.22 default layout on a 14-core machine.

**The capped walk** (layers on at once):

| N | Stacks | Python, one core | Python, every core | Compiled engine |
|---|---|---|---|---|
| 6 | 1,108,547 | 17 s | 6 s | 0.4 s |
| 7 | 4,176,461 | 67 s | 20 s | 1.6 s |
| 8 | 13,283,970 | 232 s | 71 s | 6 s |
| 9 | 35,728,702 | not run | not run | 9 s, 2 GB |
| 10 | 80,430,057 | 40 minutes | 9 minutes, 9 GB | 25 s, 4 GB |

**The chain walk with extra presses** (arrivals per chain, no bystander),
every stack tested, and every stack one landing past it:

| Extra presses | Stacks | Python, one core | Python, every core | Compiled engine | Would fail |
|---|---|---|---|---|---|
| 1 (the audits) | 3,383 | 1 s | | 0.04 s | 0 |
| 2 | 31,111 | 12 s | 2 s | 0.1 s | 4 |
| 3 | 185,013 | 140 s | 35 s | 0.5 s | 10 |
| 4 | 784,861 | 36 minutes | 6 minutes 50 s | 2.7 s | 12 |
| 5 | 2,684,100 | not run | not run | 10 s, 1.2 GB | 12 |
| 6 | 7,728,211 | not run | not run | 36 s, 4.6 GB | 12 |

- **Every core, in Python,** is about 3.5 to 5 times faster on 14 cores. One
  process keeps the table of known stacks and merges what the others find,
  and that part doesn't split.
- **The compiled engine** ([walk_engine.cpp](../../archived/capped-walk-and-first-engines/steam_layout/engine/walk_engine.cpp))
  is 40 to 100 times faster than Python on one core. Every thread inserts
  into one table split into 4,096 parts, so nothing waits on a single
  process. A stack is 16 bytes.
- **Same results.** At 3, 4 and 5 layers the engine and the Python walk give
  the same number of stacks, the same pairs with the same exits and the same
  shortest path lengths. At 0, 1 and 2 extra presses the engine's chain mode
  has the same stacks and pairs as `chains.py`. The Python chain walk on every
  core gives the same stacks in the same order, with the same reasons, as on
  one. `tests/test_native.py` keeps the engine and Python in step.
- **Merging orders that can't matter** was measured and dropped: only 13% of
  layer pairs are free of each other (most share a stick touch, R116), and
  the walk at 6 layers shrinks 1.8 times.
- **Extra presses keep multiplying.** Each one costs about four to five times
  more in the engine. Seven would need about 17 GB. From 4 on nothing new is
  found.

## Eight extra presses: the chain engine

On 2026-10-03 the author chose the chain walk with a cap on presses over the
walk with a cap on layers ("the chain is more accurate than the walk"), and
asked how far the press count can go, ideally to 8. The first engine keeps 84
bytes for every state and would need about 47 GB for that.
[chain_engine.cpp](../../steam_layout/engine/chain_engine.cpp) is a second
engine for the chain walk only.

| Extra presses | States | Stacks | Time | Memory at peak | Would fail |
|---|---|---|---|---|---|
| 5 | 11,277,677 | 2,684,100 | 3.5 s | 1.5 GB | 12 |
| 6 | 40,106,537 | 7,728,211 | 15 s | not measured | 12 |
| 7 | 122,873,089 | 19,035,805 | 48 s | 6.5 GB | 12 |
| 8 | 329,696,719 | 40,275,669 | 8 minutes 15 s | 10.9 GB | 12 |

What it does differently:

- **A state is (stack, the layer the chain is on).** The number of extra
  presses used is not part of it. The walk goes by cost, cheapest first, so
  each state is met once, at its lowest cost. At 6 extra presses that is 40.1
  million states, where the first engine has 54.6 million.
- **The table is filled one part at a time.** It is split into 16,384 parts by
  the stack's hash. Threads first sort new states into one queue per part;
  then each part is filled by a single thread. The part being worked on fits
  in the processor's cache, and no lock guards it.
- **A stack is tested once,** when its first state is met. There are about
  eight states per stack at 8 extra presses.
- **A state takes 18 bytes.** With paths it also keeps the state and binding
  it came from, 20 bytes more. Up to 6 extra presses one run keeps the paths.
  Past that the walk runs without them, to fit in memory, and each pair's
  stack and path come from a second run at 6. A pair that only shows with
  more extra presses would keep its stack and say that no path was kept;
  there is none today.
- **The same result on every run.** With paths, the states to expand and the
  queue of each part are put in one order first, so which state a stack
  "came from" does not depend on which thread got there first.

Checked:

- At 0 to 6 extra presses both engines give the same number of stacks, the
  same pairs with the same exits and the same longest stack. Its state count
  equals the first engine's count of distinct (stack, layer) states.
- One thread and 14 give the same result.
- From 4 to 8 extra presses nothing new is found: 183 pairs, of which 12
  would fail and 8 more fall under the touchpad exception.

Limits:

- **Nine extra presses** would be about 800 million states and over 20 GB.
  It does not fit this machine (24 GB).
- **Eight is slow for its size:** four times more time per state than seven.
  It runs close to the machine's free memory.

Why the first engine stopped gaining past four threads (measured on this
machine, an Apple M4 Pro with 10 fast and 4 slow cores):

- The threads stay busy. The same 9-layer walk costs 35 s of processor time
  on 4 threads and 62 s on 8.
- Two separate engines with 4 threads each, sharing nothing, each took 15.3 s
  where one alone took 9.5 s. So the limit is the machine's memory under
  random lookups in a table of gigabytes, not the locks and not the language.
  A Rust version would do the same lookups.
- A lighter lock, asking memory for a slot ahead of time, and a lock-free
  check for known stacks were tried on scratch copies. Together the first two
  gave 1.5 times; the third gave nothing. They are not in the repo.

## The run at 10

`python3 -m tools.audit_cleanups versions/neptune/90.22/single-set-default_hold-gyro_90.22.json --walk 10`
on 2026-10-03: 80,430,057 stacks, settled after 20 presses, 2,377 s and a
peak of 7.0 GB. It fails on the 12 pairs above. The exceptions set aside 109
pairs on a keeper's exit (101 in the chain check) and 62 on another exit.

## Open

- **The gap is fixed in 90.23** (author's choice of fix A in
  [suggested-fixes.md](suggested-fixes.md)): the menu Tap Cover binds both
  stick touches itself. Not open any more.
- **Hands.** The stacks above need a menu button, the left stick, a pad and
  the right thumb on its stick: four thumb controls for two thumbs. Whether a
  person can produce that is for the author to say. The fix does not depend
  on the answer.
- **Nine extra presses** do not fit this machine.

## Files

- `measure_walk.py`: the read-only trial the first numbers come from, before anything was built. It may not run
  against today's code.
- `suggested-fixes.md`: what to change in the layout for the 12 pairs.
  `python3 findings/2026-10-03-simultaneous-cap/measure_walk.py <layout> <GB> - <N>`.
