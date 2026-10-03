# Backward chains: what can be below a layer

Status: built on 2026-10-01 ([chains.py](../../steam_layout/chains.py)).
Every audit now builds its stacks from it: the Window audit, `window_routes`,
the Flow audit and the per-layer report (`audit_layer.py`). The two older
searches are [deprecated](#deprecated). Measuring the Flow audit on chain
stacks also exposed a misread rule, now corrected
([details](#the-flow-audit-on-chain-stacks)). Steps and status are in the
[plan](../../plans/2026-10-01-backward-chain-audit.md).
The sections below record the prototype; [Built](#built) has the final
numbers.

The author's idea, 2026-10-01: don't calculate every stack. Start at a layer,
ask who adds it, then who adds that layer, back to Base, and look at the
bindings on the way. The [prototype](prototype.py) does that and adds two
small steps. On both working layouts it finds the same inputs as the two
existing searches together, in about 0.02 s for all 69 layers.

## Result

Checked on the seven Always On windows and the two Steering Double Tap
windows, in both layouts. "Same inputs" means the set of inputs that have a
layer command somewhere beneath the window.

| Method | Time per layout | Depth cap | Reaches Steering windows | Finds two families overlapping |
|---|---|---|---|---|
| Depth-5 search (`StackSpace`) | 3.3 s | 5 inputs | No | Yes |
| Intended-flow walk | 0.6 s | None | Yes | No |
| Backward chains (this) | 0.02 s | None | Yes | Yes |

- **All nine windows, both layouts:** the chains find every input the
  depth-5 search finds, every input the flow walk finds, and nothing that
  neither of them finds.
- **Stacks under `L1: Double Tap`:** 30, against 530 from the depth-5 search.
- **Every layer, default layout:** for 65 of 69 layers the chains contain
  every stack the flow walk has. The four exceptions and the two layers the
  chains never reach are under [Limits](#limits).

## The algorithm

There are three parts. The example is `L1: Double Tap` in the default layout.

### 1. The chain: who adds this layer

- Find every binding that adds the layer. Here: the L1 release in
  `L1: Modifier 0`.
- Apply that whole binding to get the stack afterwards. It removes
  `L1: Modifier 0`, `Gyro | L1: Modifier 0` and `L1: Temp Cursor Gyro`, then
  adds the window. So the modifier is not under the window; what was under
  the modifier is.
- Repeat for the layer that held the binding: `L1: Modifier 0` is added by
  Base's L1 press. Base ends the chain.
- A step only counts if its layer is the one that answers that input on the
  stack so far. If the previous step put a cover or a Modifier 2 on top, and
  that layer binds the input, the step is intercepted and the chain is
  dropped.
- Recovery and reset bindings are not followed. They only fire on stale
  layers.

### 2. Settle: removals between two adds

Between two adds, the stack can shrink through a removal-only binding. The
case that needs it: a Steering driver press adds the W Key layer and
`Steering | LS: Tap Cover` together. The cover binds stick up, so the next
chain step (stick up adds Modifier 1) is intercepted until the cover lifts at
stick centre. The settle step applies such removals, so both stacks are
tried. Only removals are applied here; adds are only ever followed along the
chain.

### 3. The bystander check: layers that added nothing

A layer can be on the stack without being in the chain. Push the right stick
(`Gyro Off Ramp Up` is added), then tap L1: the ramp layer is under the
window, but the chain is only window, modifier, Base.

For every other layer, replay the chain on top of that layer's own chain
stack. The layer stays under the window if both hold:

1. **No step is intercepted.** The layer doesn't bind any input the chain
   uses. Otherwise that press fires the layer's own binding and the window is
   never added.
2. **No step removes it.**

| Layer | Binds L1 | Removed by the chain | Under `L1: Double Tap` |
|---|---|---|---|
| `Gyro Off Ramp Up` | No | No | Yes |
| `Menu Right: Fn Layer` | Yes, L1 is F10 | – | No |
| `L1: Temp Cursor Gyro` | – | Yes | No |

The ramp layer's trigger edge is a `remove_layer`, so the window has to block
the trigger edges. It does.

## The three questions

These are the questions from the
[stack search record](../2026-09-30-stack-search/README.md#the-three-questions).
For any layer X:

| Question | How the chains answer it |
|---|---|
| 1. What is inherited | For each stack under X, every input X doesn't bind resolves to the nearest layer below that binds it. The existing checks already do this from a list of stacks (`check_stack`, `inspect_target`); only the source of the stacks changes |
| 2. What each inherited input does, and from which layer | The same lookup gives the layer and its binding. Each stack carries its reason: the chain of bindings that built it, or the bystander's name |
| 3. What can be below X, and above X | Below: the layers in X's stacks. Above: every layer Z that has X in one of its stacks. One pass over all layers gives both |

Checked on three layers in the default layout:

| Layer | Below (examples) | Above (examples) |
|---|---|---|
| `L1: Modifier 0` | `R1: Modifier 1`, `Gyro Off Ramp Up`, the stick-touch helpers | `L1: Temp Cursor Gyro`, `L1: Tap Cover`, both `Modifier 2` layers |
| `Menu Right: Fn Layer` | Both Menu Right Entry Points, `Gyro`, the ramp layers | Both Transition Sets, the right-pad layers |
| `Steering \| LS Up: Modifier 1` | `Steering`, the W and S Key layers, `Gyro` | `Steering \| LS: Tap Cover` |

### Cleanup

"What must my exit remove" is questions 1 to 3 combined with the layer types
in [Definition of Done §1](../../resources/Layer%20Definition%20of%20Done.md#1-layer-type):

- **Above me:** overlays I added. The exit removes them.
- **Below me, from my own chain:** my parents. The exit removes them if they
  are my family (`Menu Right: Fn Layer` removes its Entry Point).
- **Bystanders:** another owner's layers or a stateful layer. Never removed;
  they only matter for blocking.

The prototype also showed a fourth group: layers an exit removes that are
never present with it, such as `Gyro | L1: Modifier 0` in
`L1: Modifier 0`'s exit. These are defensive removals of a sibling variant.

## Variants that were tried

| Variant | Outcome |
|---|---|
| Chain with no interception test | Found everything, but added a false stack: `R1: Modifier 1` under `L1: Double Tap`, through a step that `Modifier 2` intercepts |
| Interception test, no settle step | Exact on the seven windows, but found no stack for the Steering windows |
| Interception test with settle | Exact on all nine windows. This is the prototype |
| Every pair of families walked together | Same answers as depth-5, but 92 s, and one pair hit the 300,000-state limit |
| Other families' stacks placed below with no check | 0.5 s, missed nothing, flagged many false routes |
| Replaying the flow walk's path over other families' stacks | 0.5 s, exact on five windows. Missed the ramp layer under the menu windows, because the path changes when the stick is out |

## Limits

- **Missed releases are out of scope.** A missed release is a button release
  Steam never sees, for example while the Steam menu is open, which leaves a
  layer on the stack with nobody holding its button. The chains follow
  intended adds only, and skip recovery bindings.
- **Chords and held buttons are ignored**, by the author's decision
  (2026-10-01). A chain follows an adder whether or not its chord could be
  satisfied at that moment. This can add a stack that can't happen, never
  drop one that can.
- **One bystander at a time, arriving before the chain starts.** A layer that
  arrives in the middle of the chain is not modelled. This is the cause of
  the four exceptions: `Transition Set 0`, `Transition Set 1` and the two Fn
  layers lack the flow stacks where a `Steering | Menu …: Tap Cover` landed
  on its Entry Point before the next step. A fix was measured; see
  [Fixing the limits](#fixing-the-limits).
- **`hold_layer` is not followed.** `LTP: Arrow Keys` and
  `RTP: Mouse Buttons` are only added that way, so the chains never reach
  them.
- **The comparison is on inputs, not stacks,** for nine layers, on today's
  two layouts.
- **Nothing here was tested on the Deck.** It is a model of the bindings.

## Fixing the limits

Measured with [prototype_limits.py](prototype_limits.py) on 2026-10-01. The
author ruled `hold_layer` out of scope.

| Fix | Time, all 69 layers | Outcome |
|---|---|---|
| None (the prototype above) | 0.04 s | Four layers lack flow stacks |
| One mid-chain arrival | 4.3 s | Every flow stack is found. Seven windows still exact. New inputs under the two Steering windows |
| Two bystanders | 1.8 s | No change on any of the nine windows |
| Held-button tracking for chords | 1.2 s, or 72 s with arrivals | Removed no false stack, and lost a real result on the menu windows |

- **Mid-chain arrival works.** Between two chain steps, try every binding
  that adds a layer and that fires on the stack at that point, once per
  chain. This recovers the Tap Cover under the Fn layers and Transition
  Sets.
  - It also reports inputs under the two Steering windows that neither
    existing search can see: the trigger edges and left-pad touch in the
    default layout, the trigger clicks and left bumper in the alternative.
    These look like a ramp layer or a left-pad key layer added while already
    in Steering. They have not been traced one by one.
  - Cost: stacks go from about 1,900 to about 118,000 across all layers.
    Computing only the layers asked for, or limiting arrivals to bindings
    that carry a layer command the target leaves open, should cut this; not
    measured.
- **Two bystanders add nothing today.** Keep one in the tool, and keep the
  two-bystander comparison as a test.
- **Held-button tracking is the wrong fix for chords.** It makes "which
  buttons are held" part of every state, which is what made the earlier
  searches explode: chain states went from 122 to 13,795, and to 294,000
  with arrivals. There is also no false stack for it to remove today. The
  lost menu-window result was not traced; it may be the rule or the
  prototype keeping one path per stack.

## Built

The module follows the prototype, with two differences: the walk is breadth
first to a fixed point, so loops are handled and each stack's reason is a
shortest chain; and mid-chain arrivals are on (one per chain).

| | Depth-5 search (before) | Chains (now) |
|---|---|---|
| Window audit, per layout | 3.3 s | 0.55 s |
| Stacks checked under the seven windows | 4,285 | 5,090 |
| Reaches the Steering windows | No | Yes |
| Config needed for a new window | A family in `flow_config.json` or within five inputs | None |

Checked by tests in [test_chains.py](../../tests/test_chains.py), on both
layouts:

- the seven Always On windows: the same inputs as the depth-5 search and
  the flow walk together
- every stack the flow walk finds is also found by chains, for every layer
  except the two `hold_layer` ones
- two bystanders find no input that one doesn't
- the Window audit runs in under one second

The build audit is clean on both layouts and the fix pipeline changes
nothing, so no window gained or lost a block.

### Under the Steering windows

Chains report inputs under the two Steering Double Tap windows that neither
older search can see. Each was traced with the reasons the tool records. All
come from a layer Base adds while `Steering` is already on, because
`Steering` leaves those inputs to Base:

| Layout | Input | Layer underneath | How it gets there |
|---|---|---|---|
| Default | Trigger edges | `Gyro Off Ramp Up` | Push the right stick in Steering, then drive and flick the left stick |
| Alternative | Trigger clicks | `Turning Ramp Up 0` | Push the right stick with a driver held |
| Alternative | Both bumpers | `Gyro Off Ramp Up` | As the default case |
| Both | Left-pad touch | `Escape`, `Enter`, `Tab`, `Backspace` | Swipe the left pad in Steering |

- **The ramp cases look real.** The right thumb holds the stick out while
  the left hand drives. The seven existing windows already clear these same
  inputs for this reason.
- **The left-pad case needs the left thumb on the pad and the left stick at
  once**, which one thumb can't do. The tool has no model of that.
  `window_pads` clears the left pad in every Always On window anyway.
- **None of these fail today**, because the Steering windows aren't Always
  On yet. When the stateful transitions build makes them Always On,
  `window_routes` will ask for these blocks.

### The per-layer report

`python3 audit_layer.py <layout> --layer TITLE` prints the three questions
and the exits lists for one layer, in about two seconds. On
`Menu Right: Fn Layer` in the default layout it shows, for example:

- its release removes both Entry Point variants and the Steering menu Tap
  Cover, all of which can be present
- its 19 recovery bindings remove only itself and the normal Entry Point, so
  the Steering Entry Point and its Tap Cover are present and left

The second point is the kind of thing the lists are for. Whether it needs a
fix is the author's call; the stateful transitions plan already extends
those recoveries.

### The Flow audit on chain stacks

Measured with [flow_audit_on_chains.py](flow_audit_on_chains.py): the Flow
audit's comparison, run on chain stacks in place of its own family walk. It
counts inputs a non-cover layer inherits whose binding differs between
stacks.

| Stacks used | Inputs with differing inherited bindings | Time |
|---|---|---|
| Family walk | 8 | 0.6 s |
| A layer's own chains, no arrivals, no bystanders | 38 | under 0.1 s |
| Chains with arrivals and bystanders | 296 (default), 294 (alternative) | 12 s |

At the time these were called "conflicts" and failed the Flow audit, so the
jump from 8 to 296 looked like 288 new problems. It wasn't.

**The rule had been misread** (author, 2026-10-01). "More than one inherited
keybind means block" is the last step of the Always On window rule, not a
rule for ordinary layers:

1. The layer has an Always On action.
2. One of the bindings it could inherit on an open input is a layer command.
3. Then clear the input if more than one keybind is possible, otherwise
   override it with that keybind.

The Flow audit had applied step 3 to every layer without steps 1 and 2.
Checked against the real rule, none of the 296 is a failure:

- 290 are on layers with no Always On action.
- 6 are on `RTP: Double Tap`, and none of those is a layer command.

What changed:

- The Flow audit lists these as "varies", for information, and no longer
  fails on them. It still fails on cover findings and coverage gaps.
- [Definition of Done §8](../../resources/Layer%20Definition%20of%20Done.md#how-to-check-it)
  states the rule as the steps above.
- The Window audit, which already implemented the real rule, is unchanged.

After that correction the Flow audit moved to chains as well; see
[Deprecated](#deprecated).

## Deprecated

Decision: the author, 2026-10-01. Two older ways of finding stacks are no
longer used by any audit. Their code and tests are kept, as with the earlier
[stack search archive](../2026-09-30-stack-search/ARCHIVE.md).

**Moved on 2026-10-02:** both are in
[archived/depth-search-and-family-walk/](../../archived/README.md), with the
90.9 comparison tests and family rules. `audit_inheritance.py --depth` and
the `depth` and `chains` arguments of the audit are gone. The two prototype
scripts in this folder import the archived modules, so they only run at the
commit named in that README. The "Where" column below gives the old paths.

| Deprecated | Where | Replaced by | Why |
|---|---|---|---|
| Depth-limited search | `StackSpace` and `explore` in `steam_layout/stacks.py`; `audit_inheritance.py --depth N` | `chains.py`, the default view | It can't reach layers more than five inputs from Base, and took 3.3 s |
| Family walk | `steam_layout/flow_paths.py`, `flow_covers.py`, and the `families` section of `flow_config.json` | `chains.py`, the family view, and `covers.py` | It needed a family declared for every layer, and couldn't see overlaps between families |

**The family view.** The cover check judges a cover with its own family. On
chains that takes two settings, which `covers.family_view` applies:

- chains may start from each context in the rules: Base, and Base with `Gyro`
- only a layer the chain itself added may arrive mid-chain, not one that Base
  or a context layer adds

**How the replacement was checked**, on the frozen 90.9 layouts with the
family rules of that day (`tests/data/flow_families_90.9.json`):

- all 15 covers in both layouts: the same owners, the same findings and the
  same layers above ([test_covers.py](../../tests/test_covers.py))
- the seven Always On windows: the same inputs as both older searches
  together ([test_chains.py](../../tests/test_chains.py))
- every stack the family walk found is also found by chains

These comparisons are frozen at 90.9 on purpose. They record that the switch
was sound and are not meant to follow later layouts, which the old searches
would not handle.

**What changed for the Flow audit:**

| | Before | Now |
|---|---|---|
| Time per layout | 0.7 s | 0.1 s |
| Rules needed for a new layer | A family | None |
| Coverage gap | A layer outside every family | A layer no chain reaches |
| `flow_config.json` | Families, covers, decisions | Contexts, covers, decisions |

**What is still usable from the old code:** `walk` / `fire` in `stacks.py`
replay one concrete input sequence. `apply_ops`, `definer` and the transition
inventory in `flow_model.py` are not deprecated; the chains are built on them.

## Reproduce

```bash
python3 findings/2026-10-01-backward-chain-stacks/prototype.py default
python3 findings/2026-10-01-backward-chain-stacks/prototype.py alternative
```

Each run takes about 4 s, nearly all of it the depth-5 search it compares
against. Both prototypes read the frozen 90.9 layouts and family rules.
