# Steering scroll and trackpad-click audit — 90.48

Read-only investigation of both committed 90.48 layouts, 2026-10-10.
No layout, exported VDF, version, or binding has been changed. The user's
specific failing gesture and affected pad were asked about and remain
unconfirmed at the time of this report.

The probe characterizes **384 steering sequences and 192 click sequences**.
All characterization assertions pass; this means the reported behavior was
reproduced, not that the behavior is desirable. Sources and SHA-256 hashes,
full input/output traces, and configured feedback sources are in
[results.json](results.json); counts and limitations are in
[summary.json](summary.json).

## Steering scrolling

The left-stick path is:

1. Hold either driver: Steering adds W or S.
2. Up/down adds `Steering | LS Up: Modifier 1` or
   `Steering | LS Down: Modifier 0` from the direction input.
3. Returning from the **outer edge** removes that modifier and adds its
   Double Tap window.
4. After 150 ms, that window removes itself and emits one wheel step.
   A second push in the same direction instead adds `Steering | LS: Double
   Tap Cover`, whose directional chord scrolls repeatedly while a driver
   remains held (5 ms start delay, 50 ms repeat in the configuration).

| Gesture, with a driver held | Result in the model |
|---|---|
| Full flick, return to center, keep both thumbs resting | One wheel step after the window |
| Direction pressed and released without reaching the outer edge | No wheel step; Mod 0/1 remains on the stack after the stick direction is released |
| First direction held 300 ms, then centered | No wheel step; the 200 ms Tap Cover suppresses the tap |
| Full flick, then same direction held after a 50 ms gap | Repeating wheel output (six steps during the 300 ms hold in the model) |
| Full flick, then lift left thumb during the window | No step; LS touch Release removes the window before its output |
| Full flick, then lift right thumb during the window | No step; RS touch Release also removes that window before its output |

The shallow-flick problem comes from **direction-based entry versus
edge-based exit**. These are not the same threshold. The steering groups
state deadzone 13276 and omit an outer-ring radius. The model can demonstrate
a direction without an edge; it cannot measure the actual Deck radius.
Assumption A50 records the default as near the rim, rather than inherited
from Base. The [90.31 release record](../2026-10-04-fallback-window/README.md#2-the-outer-ring-radius)
explicitly documents this consequence when the small radii were removed:
short-of-rim movement leaves the map active until driver release. This is
an existing behavior, not a newly introduced 90.48 change.

The thumb-release cancellations are explicit local bindings in **both
Steering LS Double Tap windows**. Both stick-touch Releases remove the
active window and their touch helper family; neither completes its pending
wheel output. The usual full-flick scenario tests keep thumbs resting, so
they do not establish that a flick followed by a thumb lift scrolls.

A single long hold suppressing the scroll is the current intended tap/hold
split. Continuous scroll currently requires a second push; whether that
matches the user's desired gesture still needs clarification.

## Trackpad click haptics

The 90.41 change lowered intensity; it did not collapse feedback sources.
Current settings in both variants are:

| Owner | Configured source |
|---|---|
| Base, LP/RP click | Low feedback when adding the Click Entry Point |
| LTP/RTP Click Entry Point | Routing activators and D-pad mode feedback Off |
| LTP/RTP Middle Click | Low feedback on Caps Lock / Middle Mouse output |
| LTP Arrow Keys | Low on all four arrow outputs **and** Low D-pad mode override |
| RTP Mouse Buttons | Low on Back/Forward outputs **and** Low D-pad mode override |
| RTP Mouse Buttons, up/down wheel | Activator feedback Off, but the same D-pad mode override remains Low |

Thus a simple center click has two configured feedback sources. Outer
clicks can also involve mode feedback. These are settings, not a claim
that every source produces a separate physical pulse on the Deck.
The [earlier click investigation](../2026-10-03-pad-click-exits/README.md#haptics)
records the two-source design and a previous report of three or four bumps.

### A second click-entry bump during Steering Mod 0/1

This is also a layer-lifecycle issue, not just intensity settings:

- Start an LS modifier, then click and keep holding the right pad before
  its delayed Tap Cover completes.
- The modifier's Tap Cover add also removes `RTP: Entry Point`,
  `RTP: Tap Cover`, `RTP: Circular Scroll`, **and all three RTP click layers**.
- If exposing a held click fires Base's add (A9 true), the click layer is
  rebuilt and Base requests its Low entry bump again. In the representative
  Mod 1 trace, bumps occur at 30 ms and 230 ms while the click stays held.
- If exposed held inputs do not fire (A9 false), the click layer is removed
  and is not restored in the probe. That can also interrupt the held click
  output; it is not an acceptable alternative interpretation of a fixed path.

**12 of 192 click cases** produce two explicit entry-bump events: both
variants, Mod 0 or Mod 1 before their cover, three right-pad click locations,
and A9 true. Base, armed Steering, W/S alone, left-pad clicks, and clicks
started after the cover produce one modeled entry bump. Physical output and
mode feedback can add sensation beyond that modeled event count.

The simulator does not emit output-activator haptics when their layer lands
on a held input, and does not simulate mode-level haptics. Therefore the
previous click tests' assertion of one logged bump did **not** prove one
physical bump. This limitation is already noted in scenario 90.16 X5.

## Proposed repair scope

1. **Steering W/S, Mod 0/1, and LS covers/windows:** align the normal edge's
   activation range with modifier entry, or explicitly redesign the exit
   condition. An explicit radius at the movement deadzone is a candidate
   to validate on the Deck. Do not blindly add north/south Releases: the
   current design intentionally permits rolling from north/south to A/D
   while retaining the modifier. Keep the stateful full-deflection clear
   and Entry Guard protection separate from this change.
2. **Both Steering LS Double Tap windows:** decide whether lifting either
   thumb should complete the pending single scroll or preserve its timer.
   Keep Always On self-removal first on any early exit and preserve helper
   cleanup; do not introduce unrelated layer removals while the window runs.
3. **Mod 0/1 Tap Cover handoff:** audit why it clears the entire RTP click
   family, then preserve valid held clicks through completion. Simply
   silencing their re-entry bumps would leave the output interruption.
4. **Pad feedback owners:** choose one explicit click-feedback source, then
   disable the duplicate output/mode sources. Keeping Base's immediate Low
   bump is the least timing-dependent candidate for ordinary clicks; paths
   such as Circular Scroll's currently silent click entry need consistent
   treatment. Preserve recovery repeats and click outputs.

These are proposed changes, not installed fixes. No new layer or longer
timer is needed for the feedback cleanup. The exact scroll behavior should
be confirmed before changing the existing tap/hold and roll contracts.

## Reproduce

```bash
python3 findings/2026-10-10-steering-scroll-and-pad-click-audit/probe.py
```

The script validates preset/layer order and unique titles, converts IDs to
title tokens in memory, and tests both held-input exposure outcomes and
both same-time ordering outcomes for scrolling. Analog thresholds,
physical haptic counts, and native timing still need device verification.
