# Steering exits after stick modifier recovery

Investigation of both live **90.42** layouts, 2026-10-09. No layout or export
was changed. The Entry Guard proposal and dual-bumper fix remain unimplemented.

There is a reproducible failure in the runtime model while the driving button
stays held: a stick-modifier cleanup removes the valid W/S driver along with
the modifier. Before the driver's repeating entry restores it, a new full
up/down push can reach Steering's full clear. This depends on the supported
timing case where exposing a held layer-add binding does not immediately run
its command (A9 false). It establishes a configuration weakness; it does not
establish which native Steam event caused the author's observed dropout.

## Reproduction

1. Enter Steering and hold either driving button: R1/L1 in default, R2/L2 in
   alternative. Keep it held throughout.
2. Make a shallow left-stick up/down push, enough to enter Modifier 1/0 but
   not enough to activate the outer-edge input.
3. Return the left stick to center. Modifier 1/0 remains: its direction has
   no Release action, and the outer edge was never activated/released.
4. Push the right stick far enough to activate its edge. The modifier's
   recovery guard requires both left-stick deflection and a driver. With the
   left stick centered, that guard is false even though the driver is held.
5. The fallback cleanup removes the modifier/cover **and both W/S owners**.
   Steering base is now exposed. In the A9-false simulation the driver entry
   waits for its configured 50 ms repeat to apply the driver again.
6. Push the left stick fully up/down inside that gap. Steering's Soft Press
   clears its family with a Low bump and beep. The driving button has never
   been released.

The next full push is a new physical direction event, so its clear does not
need a missed chord or a missed release. A9-true re-entry closes the gap at
once in the simulator; that timing difference explains why a basic hold test
can pass while the more specific sequence fails.

## Bindings responsible

`Steering | LS Up: Modifier 1` and `Steering | LS Down: Modifier 0` enter
through the W/S layer's repeating direction binding. Each modifier's normal
exit is on `joystick/edge` Release. Both lack a direction Release exit.

The problematic `right_joystick/edge` has:

- An interruptible, repeating Regular Press removing both W/S driver layers,
  the current modifier and `Steering | LS: Tap Cover`.
- Two interrupting chords: **left stick deflected AND left driver**, or
  **left stick deflected AND right driver**.

This treats an inactive stick modifier as if its driving owner were also
invalid. The same cleanup structure occurs on 13 inputs in each modifier:
four face buttons, four D-pad buttons, both menu buttons, both stick clicks,
and the right-stick edge. That is 26 affected fallback entries per variant.
The left-stick edge and both stick touches use different, driver-only guards.

The right-stick groups are `13258/13259` in default and `13265/13266` in
alternative. The LS Tap Cover does not override the right-stick edge, so the
same recovery remains reachable after the 200 ms hold consumes the tap.

None of the W/S owners, LS Modifier 0/1, LS covers or directional Double Tap
windows directly removes `Steering`. The final removal comes from Steering
base's up/down Soft Press: threshold `29031`, repeat `50 ms`, Low feedback,
and the beep on Steering's removal.

## Probe results

The read-only [probe](probe.py) records layout hashes, preflight results,
case results and event traces in [results.json](results.json).

| Cases | Result |
|---|---|
| 512 ordinary held-driver cases, including full stick pushes, rolls, releases, windows and touch/camera activity | No Steering exits |
| 2,880 partial-push recovery cases across both variants, drivers, directions, hold durations and timing options | 960 Steering exits, all with A9 false and the new push before 50 ms |
| New-push gaps of 50, 51 or 100 ms; every A9-true recovery case | No Steering exits |
| 16 cases that actually release the driver while the stick remains fully up/down | Steering exits through the same exposed base clear |

The timing sweep includes 1–300 ms initial holds, crossing the 200 ms Tap
Cover threshold, and both simultaneous-activator orderings. It does not
inject a failed guard into these cases. The numerical gap is a simulator
result based on the configured repeat; native Steam scheduling is not a
measured 50 ms guarantee.

An additional [in-memory diagnostic](scope-isolation.json) removed only the
W/S-owner removals from the two modifiers' right-stick-edge fallback. All
16 checked held-driver cases then remained in Steering, while four
no-driver stale-owner cases still recovered through the exposed owner's own
cleanup. This diagnostic did not alter a saved layout and is not full
validation of a proposed fix.

Existing general gesture tests tend to call `Pad.push`, which activates both
the direction and outer edge, then `recentre`, which releases both. The
partial excursion used here deliberately activates/releases only the
direction. Future regression coverage needs that distinction.

## Recommended correction

Separate **cancelling the stick modifier** from **removing its W/S owner**.
Centering the left stick should allow a modifier/cover cleanup while a held
driving button keeps its W/S layer. Review all 26 affected fallback entries
and the cleanup generator's ownership rules, then test stale-owner recovery
as well as legitimate held-owner preservation. Do not merely change the
generated JSON: the builder/fix pipeline must preserve the correction.

The proposed Entry Guard protects initial Steering entry. It would not cover
this later recovery gap unless its role were deliberately expanded. Also
keep actual driver release distinct: the current full clear will run if that
release exposes base under an already-full up/down direction.

Adding an empty driver chord beside the current base clear is not a verified
fix: the Soft Press is explicitly uninterruptible, and the documented chord
suppression behavior concerns Regular Press. Preserve the intended full
clear while fixing the overly broad recovery first.

Native checks should distinguish the shallow-push/recenter/right-stick-edge
sequence from an exit with uninterrupted full deflection. The latter was not
reproduced by the ordinary probes; missed guard recognition or different
stick inheritance remains a hypothesis for that case. Relevant assumptions
are A9, A26, A36, A50 and A53 in
[Steam Behaviour Assumptions](../../resources/Steam%20Behaviour%20Assumptions.md).
