# The first driver hands over, and 264 removes fewer (90.57)

Built on 2026-10-12 from the **90.56** snapshot, both layouts, on the author's
word: "yes now start building". 90 layers in each layout. Nothing here has run
on the Deck.

It builds parts 1, 3, 4 and 6 of the
[plan](../../plans/2026-10-11-two-drivers-in-steering.md). The evidence is in
two audits of 90.56: [both drivers held](../2026-10-11-two-drivers-in-steering/README.md)
and [the owner releases](../2026-10-11-owner-release-audit/README.md).

## Terms

- **Driver:** R1 for W and L1 for S inside `Steering` (the triggers' soft pull
  in the alternative layout). The **W layer** is `Steering | R1: W Key`, the
  **S layer** its twin.
- **First driver, second driver:** the one held first, and the one pressed
  while it is held. `Steering | R1!L1: Modifier 2` is R1 first.
- **Bare `Steering`:** `Steering` itself is the top layer that answers the
  stick. It answers a stick at the rim with its exit.

## Why

The author, on 90.56:

1. R1 held for W, L1 pressed for Modifier 2. Letting go of R1 with the stick
   up or down ended `Steering`, although L1 was held (2026-10-11).
2. "its insane how many removals exist there": the second bumper's Release in
   the two Steering Modifier 2 layers had 88 removes (2026-10-11).
3. "I don't want to be cleared out of steering in mod 2" (2026-10-12).
4. "remember i still want to reduce unnecessay removals" (2026-10-12).

## The changes

[Default](single-set-default_hold-gyro_latest-changes.txt) and
[alternative](single-set-alternative_hold-gyro_latest-changes.txt): 9 layers
changed in each.

### 1. The first driver hands over

Each Steering Modifier 2 layer now binds its first driver:

| Entry | What it does |
|---|---|
| Regular Press, not interruptible | The first driver's key: W in `R1!L1`, S in `L1!R1` |
| Release | Adds the second driver's layer, then removes the Modifier 2 layer and the first driver's layer |

The add is stored last, so it runs first: `Steering` is never bare inside the
array. In the alternative layout each Modifier 2 layer gets a trigger group
for the first driver, with the settings of the W or S layer's group.

### 2. The second driver removes the Modifier 2 layer, and nothing else

| Bind in a Steering Modifier 2 layer | 90.56 | 90.57 |
|---|---|---|
| The second driver, Chorded Press, 200 ms | Added the cover, with a low bump | Gone |
| The second driver, Regular Press repeating at 250 ms | The timer's reset | Gone |
| The second driver, Release | 88 removes | One: the Modifier 2 layer |
| The twelve command binds and the two stick touch Releases | Added the cover first | No add of the cover |

The cover is `L1: Tap Cover` or `R1: Tap Cover`. Both keep their binds for the
plain modifiers; no Steering layer names them any more, and they name no
Steering layer.

### 3. Fewer removes

| Where, per layout | 90.56 | 90.57 |
|---|---|---|
| The second driver's Release in the two Steering Modifier 2 layers | 176 | 2 |
| Their two resets | 2 | 0 |
| The cover in their 32 cleanup functions | 32 | 0 |
| The cover in the W and S layers' Releases and Modifier 2 entries, and in `Steering`'s exit | 10 | 0 |
| A Steering Modifier 2 layer in the two covers' lists | 6 | 0 |
| Layers that answer the same driver, in three binds of the W and of the S layer | 16 | 0 |
| Seven layers that are never there, in each of the four Gyro Modifier 2 Releases | 28 | 0 |
| New: the first driver's Release | 0 | 4 |
| **Every remove in the default layout** | **4,277** | **4,013** |

The alternative layout goes from 4,347 to 4,083. The builder's own changes
make 222 of the 264 and the fix pipeline 42 (the `cleanup_lists` step, R132).

- **The sixteen.** The W and S layers' two driver Releases and their
  Modifier 2 entry named the two stick windows, and the Releases named the
  Modifier 2 layer. Each of those binds the same driver, so it answers the
  driver whenever it is on and the bind underneath does not run.
- **The 28.** Each Gyro Modifier 2 Release named `Steering`, its Entry Guard,
  the two plain modifiers, the two plain Modifier 2 layers and the other Gyro
  Modifier 2 layer. The author asked for that on 2026-10-04 for the Steering
  fallback, which went in 90.42. None was on the stack in 953 firings on
  12,000 random walks, and the Cleanup audit calls all seven "never there".

### Left as they are

- **The two stick windows** (author, 2026-10-12: "just dont touch the window
  for now and have it remove itself as today"). The second driver pressed
  inside one still types its key until the window closes itself, with
  Modifier 2 after; a driver let go inside one still removes both driver
  layers.
- **The right pad's window** (author: "leave it"). `RTP: Double Tap` answers a
  driver's Release and names no Steering layer.
- `Steering`'s exit, Base's Modifier 2 layers, the rocking order of the plain
  modifiers, the stick modifiers and scroll layers.

## What you would feel

- Hold R1, then L1, and let go of R1: you are on S at once, wherever the
  stick is. `Steering` stays.
- A tap and a hold of the second bumper end the same way: Modifier 2 goes and
  you are on the first bumper's layer. `Gyro` stays as it was, W or S is not
  let go, a held pad click stays down, and at the rim `Steering` stays.
- No bump 200 ms after the second bumper goes down.
- Outside `Steering` nothing changes: both bumpers and a quick release still
  toggle `Gyro` with one beep, also inside `Cursor Gyro`.
- After a release missed in the Steam menu, or answered by the right pad's
  window, a W or S layer can be left on. It types nothing and goes when a
  thumb touches a stick.

## Rules, the register and the tests

- **R174 (new, author 2026-10-12):** inside `Steering`, letting go of one
  driver never leaves `Steering` bare under the other. The stick windows are
  its to-do in the register.
- **R132, tightened (author 2026-10-12):** a list names only layers that can
  be on the stack when its bind fires. The audit checks only the first half
  (on the stack with the host); the second is applied bind by bind, and has a
  to-do.
- **R159, reworded:** the Modifier 2 quick tap toggles `Gyro` and removes no
  other stateful layer. The author's note on `Cursor Gyro` is in its row, the
  register and the transitions doc.
- **A4, A10, A11, A37** list the Steering Modifier 2 layers: the first
  driver's key lands on a held driver at entry and is handed back at exit.
- **The register.** The two R132 entries that kept the Gyro Modifier 2 lists
  were to be deleted. The frozen builders of 90.43 to 90.56 read the same
  register and rebuild a different layout without them, and no layer tells
  90.57 from 90.56. So a kept removal can now end at a release: the entries
  carry `"until": "90.56"` (`steam_layout/cleanups.py`, `exceptions.py`, the
  `cleanup_lists` fix; tests in `test_cleanups` and `test_exceptions`).
- **Tests.** New: `tests/test_scenarios_90_57.py`, eleven scenarios and six
  shape tests. On the 90.56 build (`frozen`): 90.16 X3, 90.17 S1 and
  90.44 S4, which state the old clear, and two shape tests of its lists.
  Rewritten for what holds now: 90.14 P12, 90.26 H3, 90.33 L2, 90.43 B2,
  90.44 E3 and S1, and three shape tests (`test_fn_feedback_steering_clear`,
  `test_neptune_cursor`, `test_steering_touch_windows`).

## Validation

- **Build audit:** clean on both layouts (Budget, Window, Flow, Cleanup),
  on the candidates and on the installed layouts. Its only stale register
  decisions are the two that 90.56 already had.
- **Pre-flight:** layer order, preset blocks and preset ids OK, no duplicate
  titles, no unresolved token.
- **The builder against the trial.** Its layouts equal, bind for bind, the
  trial layouts the plan was checked on before the build.
- **Scenarios:** `tests/test_scenarios_90_57.py`, 17 tests, pass. Among them
  the 640-gesture sweep of the first audit on both layouts: no flag outside a
  stick window state; inside one, only the three that the windows are known
  for.
- **Full suite:** 1,212 tests in 106 modules, all pass, with the same 25
  expected failures as before the build.
- **Is anything left on?** The 90.56 snapshot and the installed layouts
  played the same 23,595 random walks, half with one release in ten missed.
  After everything is let go a layer is left on in 40 of 5,796 walks against
  29 (default, no release missed), and 232 of 5,799 against 189 with releases
  missed. After a thumb on each stick: none, on either, in every run. The
  difference is traced in the
  [owner release audit, section 10](../2026-10-11-owner-release-audit/README.md#10-with-fewer-removes-is-anything-left-on).
- **Unverified assumptions:** 48, listed with what rests on each in
  [unverified-assumptions.txt](unverified-assumptions.txt). This build adds
  none. It rests more on A10 and A37: the first driver's key changes hands
  when Modifier 2 lands on it and when it leaves.

## On the Deck

Everything above is the simulator's. With a key tester open, in `Steering`:

1. Hold R1, then L1. Push the stick up to the rim and let go of R1: S is
   down and `Steering` stays. This is the reported fault.
2. Rock the bumpers: R1, L1, R1 up, R1 down, L1 up, L1 down. W or S follows
   the bumper that is held. Watch the held key as the other bumper goes down
   and up: a blink means A37 does not hold there.
3. Hold R1 and tap L1 a few times, then hold L1 for a second and let go: each
   time you are back on W with no bump, and `Gyro` is as it was.
4. Hold R1 and L1 and press A: the Modifier 2 key types.
5. Hold R1, click and hold the right pad, tap L1: the mouse button stays
   down.
6. The window check, which decides whether the stick windows need a fix:
   hold R1, flick the stick, press and hold L1 as the stick comes back (an S
   shows you were inside the window), wait half a second, press A. M means
   Modifier 2 came after the window. F means it did not.
7. Outside `Steering`: hold both bumpers and let one go quickly. `Gyro`
   toggles with one beep, as before.
