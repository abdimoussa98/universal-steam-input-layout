# Steering fallback hold (90.11)

**Status, 2026-10-02:** built and installed in `neptune/` as **90.11**, with the
snapshot in `versions/neptune/90.11/`. Device status: **untested**. The Deck
checks are first in [manual-testing.md](../../manual-testing.md#9011-steering-fallback-hold).

**90.12 carries all of it.** 90.12 is this build plus the fix pipeline's new
`cleanup_lists` step ([cleanup audit](../2026-10-02-cleanup-audit/README.md)).
Checked on 2026-10-02: `test_working_layouts_are_this_build` rebuilds this
builder, runs the current pipeline and matches 90.12 exactly, all 11 Fallback
Hold tests pass, and both descriptions keep the fallback and menu sentences.
Rebuilds keep going through this folder's `install_neptune.py`; the pipeline
step is applied there.

**Since 90.14 the working layouts are a later build.**
[findings/2026-10-03-pad-middle-click](../2026-10-03-pad-middle-click/README.md)
extends this builder, and rebuilds go through that folder's
`install_neptune.py`. This builder stays frozen.

## 90.13: no turn assist in Steering

Author, 2026-10-02: "just block it in the steering base". `Steering` binds the
right-stick edge as an empty Regular Press, and every Steering layer inherits
it or binds its own. Before, Base's edge started turn assist, and its
either-trigger chord could add `Turning Ramp Up 0` with a driver held. The ramp
layers bind both bumpers, so letting go of R1 there went to the ramp layer
instead of `Steering | R1: W Key` (the hidden-exit prototype's only open case).

- Turn assist is off everywhere in Steering, fallback included.
- `Gyro Off Ramp Up` isn't added either, so the gyro stays on while the right
  stick turns the camera in Steering.
- The fix pipeline no longer writes the trigger mouse buttons (default) or the
  bumper mouse buttons and trigger-click blocks (alternative) into the two
  Steering stick Double Tap windows. They only cut a route to the ramp layers;
  the windows now inherit the same mouse buttons from Base.
- Both descriptions say turn assist is off while steering.

Released as 90.13 on top of 90.12 (90.12's snapshot untouched).

A comment that no longer holds: the frozen 09-30 Lean builder
(`findings/2026-09-30-steering-lean/build_candidate.py`, line 423) still says
Steering and the W and S layers keep turn assist. Since 90.13 they don't. The
builder is frozen (later manifests record its hash), so the comment stays.

## The problem

In 90.10 Steering's fallback timers (warning from 1 s, exit at 2.5 s) sat in
the `Steering` layer on stick up and stick down. On the Deck the author found
the timer still running while the stick was on A or D.

## The design (author, 2026-10-02)

One layer is added, `Steering | LS: Fallback Hold`. It is on only while the
stick is up or down with no driver held.

| Layer | Input | Entry | Does |
|---|---|---|---|
| `Steering` | stick up, stick down | Regular Press, repeats every 50 ms | Adds the Fallback Hold. No key and no timer |
| Fallback Hold | stick up, stick down | Regular Press | W or S |
| | | Chord on left-stick deflection, 1500 ms | Removes the Fallback Hold, the steering branch and `Steering`, with the beep and a strong pulse |
| | | Release | Removes the Fallback Hold |
| Fallback Hold | edge | Chord on left-stick deflection, 5 ms, repeats every 250 ms | Empty binding with a strong pulse |
| | | Regular Press, repeats every 1550 ms | Removes `Steering \| LS: Entry Guard` (the reset) |
| | | Release | Removes the Fallback Hold |
| Fallback Hold, `Steering \| LS: Entry Guard` | Start, Select | Regular Press | Tab, Escape (the driver layers' binds) |
| `Steering \| Menu Left/Right: Entry Point` | stick up, stick down | Regular Press | W, S |

- **Nothing lands on top (author, 2026-10-02).** No layer is added over the
  Fallback Hold or the Entry Guard; the only thing that happens there is
  removals. Start and Select type Tab and Escape, so no menu layer can come
  in and hide their Releases. A driver press removes either layer before it
  adds its own. Losing Fn and the leave gesture in the Entry Guard doesn't
  matter: it's a temporary guard, and the stick gets recentred.
- **Menu layers don't inherit the Fallback Hold.** Steering's Entry Points
  type W and S on stick up and down. Before, they inherited `Steering`'s add,
  so pushing up with a menu button held put the Fallback Hold on top of the
  menu layers and its timer could leave Steering mid-menu. Every stack under
  them gives W or S, so it is a replace, not a block. The stick guards and
  the menu Tap Cover inherit it from the Entry Point under them.
- **Rolling to A or D.** Up or down lets go, the Release removes the layer and
  the pending exit goes with it. A and D come from `Steering`, which has no
  timer. On a diagonal, up or down is still held, so W or S and the timer
  carry on.
- **The pulse.** It starts with the layer and runs until the layer leaves. The
  1 s warning delay is gone.
- **The reset.** A repeated `remove_layer` restarts a stuck delay
  ([Definition of Done §6](../../resources/Layer%20Definition%20of%20Done.md#6-hold-tap-and-double-tap)).
  The Entry Guard is never on the stack while the Fallback Hold is exposed, so
  the removal changes nothing else. At 1550 ms it comes after a healthy exit.
- **Everything else is inherited.** The layer has one group, the left stick,
  with three inputs. Left, right, click and touch come from `Steering`.

## Choices made while building

The author described the layer by voice. These points were filled in and
should be confirmed:

1. **The reset and the pulse are on the edge, not on up and down.** Up and
   down already hold three entries (key, exit, Release), which is the cap. The
   author offered the edge for the pulse; the reset went there for the same
   reason. The edge is out for as long as the layer is on. The alternative is
   the reset as a last 4th entry on up and down, which needs the Budget
   audit's exception widened: today it only allows a reset whose target is
   the layer the same input's delay adds.
2. **The Release on up and down is kept** from the author's first description.
   It is what ends the timer on A and D.
3. **The pulse is a 5 ms chorded delay**, not an immediate bind. The edge is
   already held when the layer is added, and a delay still fires over a held
   input.
4. **The edge has a Release that removes the layer.** A backstop for any up
   or down Release a layer above might hide.
5. **A driver press removes the Fallback Hold**, next to the Entry Guard, so
   it is never under a W or S layer. The layer is in the whole-layout clears
   (transition entry, Modifier 2 quick tap) and nowhere else.

## Fixed in the same release: a menu tap stranded the layer

The first 90.11 build let Start and Select through to `Steering`. With the
stick up in fallback, a menu tap went Entry Point, stick guard, then the
150 ms menu Double Tap window, which binds stick up, down and the edge.
Recentring inside the window meant no Release reached the Fallback Hold, and
the next push to A or D pulsed until centre. The Flow audit listed both paths
as "varies", which is information, not a failure. Start and Select now type
Tab and Escape in the layer, so the chain can't start.

Other layers the guard and the hold inherit adds from (the right-stick turn
assist, the trackpad layers) bind only left-stick touch, so they can't hide a
Release here.

### Audit check, measured and not built

"Fail when a layer that isn't a window inherits a bind that adds a layer"
hits 207 inherited adds on 30 layers in the default, nearly all intended
(the left-pad layers inherit the L1 and R1 modifiers, for example). It is too
broad to fail on. The narrower case is the one that bit here: a layer that can
be added over another one binds an input whose Release is that layer's exit,
without carrying the exit. That belongs with the cleanup audit, which doesn't
model missed releases yet.

## Files

| File | What it is |
|---|---|
| [build_candidate.py](build_candidate.py) | The builder. `FallbackHold` extends the frozen 10-01 `Stateful` builder |
| [install_neptune.py](install_neptune.py) | Runs the fix pipeline and installs into `neptune/` |
| `default-…` / `alternative-fallback-hold.json` | Builder output before the fix pipeline, with `.readable.json` in title form |
| [manifest.json](manifest.json) | Hashes, new layers and timing |
| [neptune-installation.json](neptune-installation.json) | Hashes of the installed files |

```bash
python3 findings/2026-10-02-steering-fallback-hold/build_candidate.py
python3 findings/2026-10-02-steering-fallback-hold/install_neptune.py --version 90.11
python3 audit_build.py
python3 -m unittest discover -s tests
```

The working layouts are generated. A hand edit in `neptune/` is lost on the
next install, and `test_working_layouts_are_this_build`
(`tests/test_steering_fallback_hold.py`) fails on it.

## What changed from 90.10

71 layers (70 in 90.10). The new layer is appended, so no runtime ID shifts.
Per variant:

- `Steering`: stick up and stick down.
- `Steering`: the two driver presses also remove the Fallback Hold.
- `Steering | LS: Entry Guard`: Start and Select type Tab and Escape.
- `Steering | Menu Left/Right: Entry Point`: stick up and down type W and S.
- Ten whole-layout clear lists gain one removal: the eight Entry Point stick
  clicks and the two Modifier 2 quick taps.
- The description: the fallback sentence now says the pulse starts at once
  and the exit is at 1.5 s, and the menu sentence says when Start and Select
  type Tab and Escape.

Verified: the build audit is clean on both variants and the 302 tests pass.
Nothing has run on the Deck.
