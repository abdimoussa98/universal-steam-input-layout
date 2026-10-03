# Plan: replace the stack searches with backward chains

Status: built on 2026-10-01, with tests first. Step 7 ended differently from
the plan: it exposed a misread rule, which the author corrected. See
[Progress](#progress).
Evidence and the algorithm:
[backward chains finding](../findings/2026-10-01-backward-chain-stacks/README.md)
and its [prototype](../findings/2026-10-01-backward-chain-stacks/prototype.py).

## Progress

| Step | State |
|---|---|
| 1 Chains | Done. [chains.py](../steam_layout/chains.py), [test_chains.py](../tests/test_chains.py) |
| 2 Settle | Done, with all four removal roles |
| 3 Bystander check | Done |
| 3b Mid-chain arrivals | Done, one per chain. The Window audit takes about 0.55 s per layout |
| 4 Parity | Done. Exact on the seven windows in both layouts; the Steering extras are traced and recorded in the test |
| 5 Window audit and `window_routes` | Done. Build audit clean, fix pipeline unchanged, 610 tests pass |
| 6 Per-layer report and cleanup lists | Done. [audit_layer.py](../tools/audit_layer.py), [layer_report.py](../steam_layout/layer_report.py), [test_layer_report.py](../tests/test_layer_report.py). About two seconds per layer |
| 7 Flow audit | Done, with a different outcome. On chain stacks the count of inputs with differing inherited bindings went from 8 to 296. The author then clarified that "more than one inherited keybind means block" only applies under an Always On layer with an inherited layer command. The Flow audit now lists these as "varies" and doesn't fail on them; it keeps its family walk for the cover check and coverage ([details](../findings/2026-10-01-backward-chain-stacks/README.md#the-flow-audit-on-chain-stacks)) |
| 9 Deprecation (added by the author, 2026-10-01) | Done. The depth-limited search and the family walk are deprecated; the Flow audit runs on chains with identical cover results on the 90.9 layouts, and `flow_config.json` no longer has families ([record](../findings/2026-10-01-backward-chain-stacks/README.md#deprecated)) |
| 8 Docs | Done: README, Definition of Done §8, `traced_stacks.json`, the stack search record, the stateful transitions plan, the finding |

What changed from the plan as written:

- The walk is a breadth-first fixed point, not a recursion with a loop
  guard. Loops are followed, and each stack's reason is a shortest chain.
- `audit()` gained `chains=True` so the depth-search tests can run that
  source alone (`chains=False`).
- The planned test "a recovery or reset binding that adds a layer is not
  followed" was dropped: those roles are removal-only by definition. A
  `hold_layer` test took its place.
- A layer that one binding can add is explained as an arrival before the
  first step, not as a bystander. The bystander check is what finds layers
  that need two or more bindings, such as a Fn layer on its Entry Point.
- The exits lists gained a fourth list, "intercepted by": a layer above that
  binds the exit's own input, so the exit can't fire while it is on top. In
  the text output, exits with the same removals and lists are shown once.
- "Above" works out the stacks of every layer, so the report takes about two
  seconds, not under one.

What is left:

- the author's review of the exits lists against
  [Cleanup Functions](../resources/Cleanup%20Functions.md), before any
  cleanup check is made to fail
- deleting the deprecated code, if the author ever wants that. It is kept
  for now, with its tests and the frozen 90.9 comparisons

## Goal

One source of stacks for every audit: the backward chains. It answers the
three questions (what is inherited, what each inherited input does and from
where, what can be below and above a layer) for any layer, with a reason for
each answer. The target is under one second per layout for the Window audit;
the prototype with mid-chain arrivals takes 4.3 s for all 69 layers, so the
target still has to be met (step 3b).

It replaces, in this order:

1. the depth-5 search (`StackSpace`) in the Window audit and in
   `window_routes`
2. the flow stacks added to the Window audit on 2026-10-01
3. the flow walk as the Flow audit's stack source, if step 7 shows it can

The checks themselves stay: `check_stack`, `blocks_needed`,
`inspect_target` and the cover check all take a list of stacks today.

## Decisions needed from the author

Each has the default this plan assumes.

| Decision | Default |
|---|---|
| Missed releases | Out of scope. The stack search record already rejects keeping them |
| How many things at once | The layer's own chain plus one bystander. Three overlapping families are not checked |
| The depth-5 search after step 5 | Decided 2026-10-01: deprecated now. Kept as an opt-in comparison (`--depth 5`) |
| The flow walk and the `families` in `flow_config.json` | Decided 2026-10-01: deprecated. The Flow audit runs on chains; `flow_config.json` keeps contexts, covers and decisions |
| Mid-chain arrivals | In, one per chain (step 3b). It was measured to recover every flow stack |

## Decided

**Chords are ignored** (author, 2026-10-01). A chain follows every binding
that adds a layer, as if its chord could fire.

- It never misses a real stack through a chord, because the real binding is
  always among the ones followed.
- It can include a stack that can't happen, for example a chord that needs
  Start held right after a step that released Start. The cost is an unneeded
  block in a window; nothing unsafe gets through.
- Tracking held buttons was measured and rejected: chain states went from
  122 to 13,795, and to 294,000 with arrivals
  ([results](../findings/2026-10-01-backward-chain-stacks/README.md#fixing-the-limits)).
- If a parity test ever shows a false stack, add a rule for that one chord,
  checked along the chain, with no held buttons stored in the state.

**`hold_layer` is not followed** (author, 2026-10-01). `LTP: Arrow Keys` and
`RTP: Mouse Buttons` are reported as not reached.

## Scope

**In:** a new module and its tests, the Window audit, `window_routes`, a
per-layer report for the three questions, a report-only cleanup check, docs.

**Out:** any layout change, `hold_layer` and mode-shift modelling, timing,
Deck testing, the deprecated timed tooling.

## Method

Test first at every step: write the tests, watch them fail, then write the
code. No step needs a long run. The slowest test is the parity comparison,
which runs the depth-5 search once per layout (about 3 s each).

## Step 1: chains on tiny layouts

New module `steam_layout/chains.py`, new test file `tests/test_chains.py`.
The tests build small layouts with the `build` helper already in
[test_audit_inheritance.py](../tests/test_audit_inheritance.py).

Tests to write first:

- a layer added by Base has one stack under it: Base
- a parent that removes itself in the adding binding is not under the layer
- a parent that stays is under the layer
- layers added earlier in the same binding sit below the later ones
- two bindings that add the same layer give two stacks
- a step whose input is bound by a layer on top is intercepted, and the
  chain is dropped
- a recovery or reset binding that adds a layer is not followed
- a loop (A adds B, B adds A) ends
- a disabled source, or a group in a different source mode, stops the lookup
  (use `flow_model.resolve`, which already applies the mode rule)
- every stack comes with its reason: the bindings that built it

Then the code: the adder index, the chain walk, the interception test.

## Step 2: settle

Tests first:

- a cover added with its owner blocks the next step; a removal-only binding
  that lifts the cover lets the step fire, and both stacks are returned
- a binding that also adds a layer is never applied by the settle step
- a recovery removal is never applied

Then the code. Settle with the `center`, `removal`, `cancel` and `release`
roles. The prototype needs only `center` today and gave the same result with
all four. But `center` means a repeating removal on an inverted stick edge,
and the [stateful transitions plan](2026-10-01-stateful-transitions-implementation.md)
replaces those with an edge Release. With `center` alone, the Steering
windows would lose their stacks after that build.

Add one more test for that: a cover lifted by an edge Release lets the next
step fire.

## Step 3: the bystander check

Tests first:

- the three-button example: a layer that binds only button 2 is under a
  window entered with button 1
- a layer that binds the chain's input is not under the window
- a layer the chain removes is not under the window
- a bystander brings its own parent (a Fn layer brings its Entry Point)
- the reason names the bystander

Then the code: replay the chain over each other layer's chain stack.

## Step 3b: a layer that arrives mid-chain

Tests first:

- an Entry Point adds its Tap Cover on a hold, then adds a Fn layer on a
  click: the cover is under the Fn layer
- an arrival that binds the next chain input intercepts it, and that chain
  is dropped
- at most one arrival per chain
- the reason names the arriving binding

Then the code: between two chain steps, try each binding that adds a layer
and fires on the stack at that point.

This is the costly step: the prototype went from 0.04 s to 4.3 s for all 69
layers. Before the switch-over, add a test that the Window audit stays under
one second per layout, and cut the work to meet it: compute only the layers
asked for, and only try arrivals that could matter to the target.

## Step 4: parity on the working layouts

A test class that guards the switch-over. For both layouts:

- for each of the seven Always On windows, the inputs with a layer command
  beneath, from chains, equal those from the depth-5 search and the flow
  walk together
- for the two Steering Double Tap windows, chains find every input the flow
  walk finds. The extra inputs chains report there are listed in the test,
  each with its traced stack (see below)
- every window has at least one stack

And for every layer:

- the chains contain every flow stack. The only exceptions are
  `LTP: Arrow Keys` and `RTP: Mouse Buttons`, which are added by
  `hold_layer` and are out of scope.
- two bystanders give the same inputs as one on every window. This guards
  the "one bystander" default.

With arrivals on, the two Steering Double Tap windows report inputs neither
old search can see (trigger edges and left-pad touch in the default layout).
Trace each one before step 5 and record whether it is a real stack. They are
not failures today, because those windows are not Always On yet.

## Step 5: the Window audit and `window_routes` use chains

Tests first, in `test_audit_inheritance.py` and `test_fixes.py`:

- `audit()` checks a window three inputs deep with no `flows` and no depth
- a window no chain reaches is "not checked" and fails
- each route carries the reason for its stack
- the working layouts pass, with all seven windows checked
- `window_routes` clears a route found only through a bystander
- the fix pipeline leaves the working layouts unchanged

Then the code:

- `audit()` takes its stacks from chains. `depth` defaults to 0.
- The `flows` argument and `--flows` option from 2026-10-01 are removed; the
  tests written for them are rewritten against chains.
- `saturated` only applies when `--depth` is given.
- `audit_inheritance.py` prints the reason with each open route.

After this step the Window audit should take well under a second per layout.

## Step 6: the three questions for any layer

New CLI, `audit_layer.py <layout> --layer TITLE`, read-only.

Tests first:

- below: the layers under it, each with a reason
- above: every layer that has it in one of its stacks
- inherited inputs: for each, the providing layer and its binding
- a layer the chains never reach is reported as such, not as "nothing below"

Then a cleanup section in the same report, report-only. For each exit
binding of the layer, three lists:

- present and removed
- present and not removed (a parent or bystander that isn't this layer's to
  clean, or a missing removal: the layer type decides)
- removed and never present (a defensive removal)

No failing check is added for cleanup in this plan. The lists need the
author's review against
[Cleanup Functions](../resources/Cleanup%20Functions.md) first.

## Step 7: the Flow audit

Measure before deciding. Run the Flow audit's comparison (`inspect_target`)
on chain stacks for every layer and compare its findings with today's.

- If the findings match, or differ only by new bystander cases the author
  accepts, switch the Flow audit to chains and retire the flow walk and the
  `families` section.
- If they differ in ways that need chords or held buttons, keep the flow
  walk for the Flow audit and say so in the docs.

More findings are likely: chain stacks include bystanders, and the Flow
audit reports competing bindings.

## Step 8: docs and the other plan

- [Definition of Done §8](../resources/Layer%20Definition%20of%20Done.md#8-inheritance-and-blocking):
  "How to check it" describes chains, and the depth and saturation text
  moves to a note on the opt-in comparison.
- `traced_stacks.json` and `flow_config.json` notes.
- [Stack search record](../findings/2026-09-30-stack-search/README.md): one
  line pointing here.
- [Stateful transitions plan](2026-10-01-stateful-transitions-implementation.md):
  the line about covering nine Always On windows becomes "covered by chains;
  the two Steering windows need no config".
- A change record in `findings/`.

## Order

Steps 1 to 4, including 3b, add code and tests and change no existing
behaviour. Step 5 is the switch-over and depends on step 4 being green. Steps 6 and 7 are
independent of each other. Step 8 follows whatever was built.

## Done when

- `python3 -m tools.audit_build` is clean on both layouts with no depth search and
  no flow stacks in the Window audit.
- The parity tests pass, with every exception listed and explained.
- The full test suite passes.
- A new Always On window needs no entry in any config to be checked.

## Risks

- **Parity is measured on today's layouts.** A future layout could need
  chords or a mid-chain bystander. The parity tests stay until the depth
  search is removed, so a disagreement shows up as a failing test.
- **Ignoring chords can add false stacks.** The interception test removed
  the one found so far. If another appears, it is over-reporting (an
  unneeded block), not a missed route.
- **One bystander at a time** can miss a route that needs three families
  overlapping. Two bystanders were measured and changed nothing on the nine
  windows; step 4 keeps that comparison as a test.
- **Arrivals cost time.** If the one-second target in step 3b can't be met,
  the fallback is to compute arrivals only for the Window audit's targets.
