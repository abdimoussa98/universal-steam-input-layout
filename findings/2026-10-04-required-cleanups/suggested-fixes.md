# Suggested fixes for the required cleanups on 90.23

**Status, 2026-10-04:** the author made the five decisions at the end, and the
fixes are built as 90.24 ([record](README.md#what-9024-changed)). The rest of
this page is as it was written for the decisions, when every fix had been
tried on scratch copies of the 90.23 layouts with [trial_fixes.py](trial_fixes.py).

The rules and the check: [README.md](README.md). Select is Menu Left and Start
is Menu Right.

## What the audit reports

`python3 -m tools.audit_cleanups neptune/single-set-default_hold-gyro_latest.json`
fails on 174 inputs (196 in the alternative layout):

| Check | Default | Alternative |
|---|---|---|
| Touch without cleanup (R169) | 48 | 48 |
| Edge without cleanup (R170) | 42 | 42 |
| Button without cleanup (R171) | 84 | 106 |

## The seven shapes

Each input gets one of these, by what it holds today. The cleanup is always a
Regular Press with Hold to Repeat, interruptible, that removes the layer's
cleanup list. The guard is one chord, Any, not interruptible.

| The input holds today | It becomes | Entries | Inputs, default | Alternative |
|---|---|---|---|---|
| Nothing, a stick touch | The stick-touch Release (that side's three helpers), a guard, the cleanup | 3 | 22 | 22 |
| Nothing, a stick edge | A guard and the cleanup. The group states its edge radius and "not inverted" (R111) | 2 | 10 | 10 |
| Only a Release | A guard and the cleanup beside it | 3 | 24 | 24 |
| The owner's chord already | The cleanup beside it. The chord is the guard | 2 or 3 | 16 | 16 |
| An empty block | A guard and the cleanup | 2 | 36 | 44 |
| An empty block that covers nothing | A guard and the cleanup (decision 1). The first trial deleted these | 2 | 38 | 18 |
| A Regular Press with an output (a key, scroll, or the Steering hand-over) | The output moves into the guard chord. The cleanup is the Regular Press | 2 or 3 | 28 | 62 |

No input ends above three entries (R109): 116 end at two and 58 at three in the
default layout, 138 and 58 in the alternative.

The stick-touch Release on a cover only removes that side's three helpers. It
adds nothing: on every cover the owner's Release adds the cover itself.

## The guard for each layer

| Layers | Guard |
|---|---|
| A layer that already has cleanup functions | The same buttons as those |
| `Menu Left: Escape`, `Menu Right: Tab` and their Double Tap Covers | Select, or Start |
| The four menu Entry Points | Their menu button. The chord is already on the touches and the edges |
| Both Fn layers | Start or Select, as **one** Any chord. Their other cleanups use two chords, which would make four entries beside the Release |
| The three transitions, the two stick guards, `Menu Buttons: Tap Cover` | Start or Select (mask 20480, Any) |
| `L1: Double Tap Cover`, `R1: Double Tap Cover`, the two Temp Cursor layers | L1, or R1 |
| `L1&R1: Tap Cover` | L1 or R1 |
| `RTP: Entry Point`, `RTP: Tap Cover` | A thumb on the right pad |
| The Steering stick modifiers, `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover` | Either driver |
| The Steering stick modifiers' right-stick edge | A driver held and the left stick out: their two existing chords |
| `Steering \| LS: Entry Guard`, `Steering \| LS: Fallback Hold` | The left stick out (mask bit 30) |

## The fixes, group by group

| Group | Inputs that change | Notes |
|---|---|---|
| The four menu Entry Points | Both touches, both edges, L1 and R1, the full-pull blocks | On an edge the cleanup sits beside "add the stick guard". Scroll on L1 and R1 moves into the guard chord |
| `Menu Left: Escape`, `Menu Right: Tab` | Both touches, both edges, the other menu button, L1 and R1, the full-pull blocks | The left edge is new. The right edge's block becomes a cleanup, which still keeps ramp-up out (R142). The list is the layer and its Double Tap Cover |
| Their two Double Tap Covers | Both touches, both edges | New groups on both sticks |
| Both Fn layers | Both touches, both trigger pulls | One Any chord, as above |
| The three transitions | Both touches, both edges, L1, R1, both trigger pulls, the full-pull blocks | A stick touch or push with no menu button held now clears a stuck transition. Since 90.10 only the next menu tap did |
| The two stick guards | Their own stick's edge | Release, guard, cleanup: three entries |
| `Menu Buttons: Tap Cover` | Both edges | The same guard and list as its touches |
| `RTP: Entry Point`, `RTP: Tap Cover` | Both touches | The cover gets new groups on both sticks (decision 2) |
| `L1&R1: Tap Cover`, `L1: Double Tap Cover`, `R1: Double Tap Cover` | Both touches | New groups on both sticks |
| The two Temp Cursor layers | Both touches | Their groups exist |
| `L1: Scroll Down`, `R1: Scroll Up` | Start, Select, the other bumper, the full-pull blocks | The three keys move into the guard chord |
| The eight modifiers | The full-pull blocks in the default layout. In the alternative layout the two bumpers, which are retyped there | |
| The two Steering stick modifiers | Left edge, right edge | Left: the Release stays. Right: the two "driver and left stick out" chords, three entries |
| The two Steering Modifier 2 layers | Both edges | The blocks become cleanups |
| `Steering \| R1: W Key`, `Steering \| L1: S Key` | Both edges, Start, Select, the other driver | Tab and Escape move into the guard chord. The other driver is decision 3 |
| `Steering \| LS: Tap Cover`, `Steering \| LS: Double Tap Cover` | Both touches, the left edge | A new right-stick group. The left edge is decision 4 |
| `Steering \| LS: Entry Guard`, `Steering \| LS: Fallback Hold` | Both touches, the right edge, Start, Select | With the left stick centred, a Start press removes the layer and does not type Tab (author, 2026-10-04) |

Two things the fixes pull in:

- **The two Steering stick windows type Tab and Escape themselves.** They
  inherit Start and Select from the W and S layers. Those inputs now hold a
  cleanup, which is a layer command, and a window may not inherit one (R140).
  Four inputs.
- **15 new stick groups**, in Base's mode for that stick, so the directions
  still come through: six on the left stick and nine on the right. They are
  the shape `L1: Tap Cover` has today.

## What the trial showed

Scratch copies of both layouts, the fix pipeline's `cleanup_lists` step, then
the four audits against the 90.23 snapshot:

| | 90.23 | With the fixes |
|---|---|---|
| Required cleanups missing | 174 and 196 | 0 and 0 |
| Budget audit | pass | pass |
| Window audit | pass | pass, with the four window inputs above |
| The six list checks (R127 to R132) | pass | pass, after 28 and 38 list edits by `cleanup_lists` |
| Hidden exits (R136) | 0 | 0 |
| Exits to review (R136) | 0 | 5, all `RTP: Tap Cover` (decision 2) |
| Flow audit, inputs to review (R139) | 0 | 4 and 12, all on the stick guards (decision 5) |

The trial ran the audits. It did not run the scenario tests, which read the
installed layouts: the press sequences are for the build.

## Decisions for the author

1. **The full-pull blocks that cover nothing.** 38 in the default layout and
   18 in the alternative.
   - **Decided (author, 2026-10-04): keep them.** Each gets a guard and a
     cleanup, like any other block. The trial passes the same way
     (`--keep-blocks`); the stick guards then inherit four more inputs to read
     in the default layout. Whether they can be deleted is a
     [to-do](../../todos.md#investigations).
   - Not chosen: deleting them. Nothing under them binds the full pull.

2. **`RTP: Tap Cover` and the right stick.** To bind the right-stick touch the
   cover needs a right-stick group, in mouse mode. When it lands over a menu
   Entry Point or the right stick guard, whose right stick is in D-pad mode,
   it hides their right-stick click and edge (A2). The audit lists five such
   pairs to review.
   - **Decided (author, 2026-10-04): accept the five pairs.** The right thumb
     is on the pad, so it can't be on the right stick. A stale cover removes
     itself the moment the right stick is touched, through the new cleanup.
   - **Called out by the author:** the hidden click is the one the Fn layer
     inherits from the Entry Point to start a transition. So a menu button
     plus the right-stick click starts no transition while the cover is over
     the Entry Point (scenario 90.24 K6).
   - Not chosen: an exception to R169 for the cover's right-stick touch.

3. **The other driver in the Steering W and S layers.** It holds a Regular
   Press that hands over to the other driver, and a Release. A guard and a
   cleanup beside them would make four entries.
   - **Decided (author, 2026-10-04): the hand-over becomes the guard chord.**
     The hand-over is the bind that adds the Steering Modifier 2 layer. With
     this layer's driver held, pressing the other driver adds it as before;
     the cleanup is the Regular Press. Three entries. This is what the trial
     did.
   - It changes the activator of the hand-over, which is timing-sensitive, so
     the build runs the scenario tests for rocking between the drivers.
   - Not chosen: an exception to R171 for those two inputs.

4. **The left edge of the two Steering stick covers.** Their own Release is
   there, and the left stick keeps them on, as it does the Entry Guard.
   - **Decided (author, 2026-10-04): a guard on either driver** and the
     cleanup, as for the stick modifiers. This is what the trial did.
   - Not chosen: an exception, as for the Entry Guard and the Fallback Hold.

5. **The stick guards inherit L1 and R1 from the Entry Point under them.** In
   the alternative layout also the triggers. After the fixes that input
   differs between Base's Entry Points and the `Stateful` ones: the same
   scroll, a different cleanup list. The Flow audit asks for it to be read.
   - **Decided (author, 2026-10-04): the guards keep inheriting it.** It is
     accepted in the register with the build, as the guards' inherited stick
     clicks are today. The entry isn't added yet: until the Entry Points
     change it would match nothing and be reported as stale.

## Not suggested

- **Leaving the covers to inherit the touch cleanup.** It works in today's
  stacks, but the author decided every cover has its own (2026-10-04), and it
  is how the menu Tap Cover gap went unseen until 90.23.
- **A cleanup on a stick-touch helper's own stick.** The thumb is both the
  keeper and the input, so it could never fire.

## What applying it takes

- A new version (90.24) from a builder, with its change report and snapshot.
- The five decisions above, and a register entry for each accepted one.
- R116's text: a cover no longer inherits the stick-touch Releases.
- Scenario tests for the changed layers (R165): a stuck layer cleared from a
  touch, an edge and a button in each group, and the hand-over between the
  Steering drivers.
