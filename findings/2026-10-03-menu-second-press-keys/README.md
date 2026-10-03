# Menu second-press layers type W and S (90.15)

**Status, 2026-10-03:** built and installed in `neptune/` as **90.15**, with the
snapshot in `versions/neptune/90.15/`. Device status: **untested**. The build
audit is clean and the tests pass. 90.15 is 90.14 plus four bindings.

## The gap

Found on 2026-10-03 by the inherited-input review of 90.14 (R139), present
since 90.11, reproduced on the press simulator on 90.13 and 90.14.

In Steering: double-tap and hold Select or Start, push the left stick up or
down, let go of the menu button.

1. The double tap puts `Menu Left: Escape` or `Menu Right: Tab` on the stack.
   Those two layers left the left stick's up and down open.
2. In Steering, the binding underneath is Steering's repeating add of
   `Steering | LS: Fallback Hold`. The hold landed on top.
3. The hold types Tab and Escape on Start and Select, so it answered the menu
   button. The second-press layer's Release never fired, and the layer stayed
   on after the stick was back at centre.

## The fix (author, 2026-10-03)

Both layers bind left stick up and down to Base's W and S.

| Layer | Input | Before | 90.15 |
|---|---|---|---|
| `Menu Left: Escape`, `Menu Right: Tab` | left stick up | not bound | Regular Press, W, Interruptible off |
| | left stick down | not bound | Regular Press, S, Interruptible off |

- It is the bind Steering's Entry Points got in 90.11 and the two menu Double
  Tap windows have had since 90.10. Every layer of the menu gesture now has it.
- Every stack under the two layers gives W or S, so this replaces the input
  and blocks nothing (R141).
- The two menu Double Tap Covers sit on these layers and inherit the binds.
- Outside Steering nothing changes: Base types the same W and S there.

One thing does change in Steering: while the second press is held, stick up or
down no longer starts the 1.5 s exit. It starts when the menu button goes up
(scenario M2). Steering's Entry Points already behave that way.

The change report against 90.14
([default](single-set-default_hold-gyro_latest-changes.txt),
[alternative](single-set-alternative_hold-gyro_latest-changes.txt)) has two
layers and four changes per layout, all decided here. The R139 `todo` entry in
the exceptions register is gone.

## Why the hidden-exit check missed it

R136 says a layer that can land on top of another may not cover an exit on
what keeps the lower layer alive. The Fallback Hold over `Menu Left: Escape`
is exactly that, and the Cleanup audit passed 90.11 to 90.14.

The reason is how the check asks "which layers can be on top of this one".

- The backward chains build a layer's stacks from **its own chain**: who adds
  it, who adds that layer, back to Base. The Fallback Hold's chain is Base,
  the transition, `Steering`, the hold. `Menu Left: Escape` is not in it.
- A second way puts one **bystander** underneath: another layer's whole stack
  first, then the chain replayed on top. That doesn't work here either. The
  hold's chain starts by entering Steering, and that can't be replayed on a
  stack that already has the menu layer on it.
- The walk does visit the stuck stack. When it stands on
  `Base > Steering > Menu Left: Escape`, it tries every adding binding that
  answers there, finds Steering's stick-up bind, and records
  `Base > Steering > Menu Left: Escape > Steering | LS: Fallback Hold`. Such a
  stack is called an **arrival**: a layer that came in through a binding of a
  layer lower in the stack, not through the layer the chain is following.
- Arrivals are only used as places the chain's next step could start from.
  `above()`, which the hidden-exit check reads, is built from own chains and
  bystanders. It never looks at the arrival stacks, so it did not count the
  hold as being on top of the menu layer.

An earlier explanation in the conversation said the chains never build this
stack because only one arrival is allowed per chain. That was wrong: one
arrival is enough here, and the stack is visited. The check doesn't read it.

### The fix to the check (author, 2026-10-03: "fix it")

The hidden-exit check now counts **landings**: for every stack the walk
visited, every adding binding that answers there, whichever layer of the stack
it belongs to. The resulting stack gets the check's own test. It asks "what
can land on this stack next", one binding at a time, on stacks that are
already known. It adds no depth and no search.

- `Chains.landings()` in `steam_layout/chains.py` lists them.
- `Cleanups.covered_exits()` in `steam_layout/cleanups.py` reads them next to
  `above()`. Only the hidden-exit check uses them. `above()` itself is
  unchanged: it also feeds the "left above" and "hidden cleanup" checks, and
  the `cleanup_lists` fix writes lists from those, so widening it there would
  have changed bindings.

Results, both variants:

| Layout | Findings before | Findings now | Cleanup audit time |
|---|---|---|---|
| 90.13 | 0 | 4 | not measured before |
| 90.14 | 0 | 4 | 6.8 s to about 7.1 s |
| 90.15 | 0 | 0 | 6.8 s to about 7.1 s |

The four findings are this gap and nothing else: the Fallback Hold over
`Menu Left: Escape`, `Menu Right: Tab` and their two Double Tap Covers. Each
finding shows the stack and ends its path with the landing, for example
`landing: Steering joystick/dpad_north Full_Press#0: +Steering | LS: Fallback Hold`.
[arrival_prototype.py](arrival_prototype.py) was the read-only trial
([output](arrival-prototype.txt), taken before the change).

**One more change came with it: who a mode block is charged to.** With
landings counted, 13 pairs appeared as information where a menu layer landed
above a pad click layer. The pad layer keeps the right stick in mouse mode,
and that is what blocks the menu Entry Point's right-stick click Release; the
check named the menu layer on top instead, because the lookup reports the top
layer of a source. The pair now names the first layer above that changed the
mode. Effects:

- Those 13 fold into pairs the touchpad exception already holds.
- On 90.14 and 90.15 the exception's pairs on a keeper go from 77 to 71:
  `RTP: Click Entry Point` covers the pad-touch Release of the three layers
  under it, and `RTP: Mouse Buttons` and `RTP: Middle Click` above it no
  longer count a second time. 90.13 keeps its 68 and 26.

Tests, in `tests/test_cleanups.py`:

- A made-up layout where a layer lands through a lower layer's binding, with
  the three ways it is fine (it leaves the exit alone, it can't land, it
  removes the lower layer there).
- A made-up layout for the mode block.
- The 90.13 snapshot now expects the four pairs, and the working layouts
  expect none.

What it still does not see: a layer that needs two or more bindings after a
visited stack before it covers an exit, where the chains don't follow the
first of them. No such case is known.

## Scenarios and tests

- `tests/test_scenarios_90_15.py`, M1 to M4: the gesture with both buttons and
  both directions, run both ways for A9; the exit waiting for the menu button;
  the same gesture outside Steering; a missed menu Release.
- `tests/test_menu_second_press_keys.py`: the four binds, that nothing else
  changed against 90.14, and that no layer a menu button keeps alive leaves
  stick up or down to Steering.
- M4 records what is unchanged: the second-press layers have no cleanup
  function, so a Release missed while the Steam menu is open leaves the layer
  on until the button is tapped again.

## Files

- `build_candidate.py`: the builder. It extends the 10-03 pad click builder,
  which stays frozen.
- `install_neptune.py`, `*-menu-second-press-keys.json`, `manifest.json`,
  `neptune-installation.json`: as in the earlier builds.
- `single-set-*-changes.txt`: the change report against 90.14 (R164).
- `unverified-assumptions.txt`: 22 assumptions that aren't verified; 54 of the
  103 scenarios rest on one (R167).
- `arrival_prototype.py`, `arrival-prototype.txt`: the read-only trial of the check change, before it was built.
