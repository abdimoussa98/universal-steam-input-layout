# Stick-touch release rule: exceptions and the Transition Set 0 patch (90.6)

**Author rule, 2026-09-30:** every layer binds its stick-touch release cleanup
explicitly. Only cover-type layers may inherit it. See
[Layer Definition of Done §5](../../resources/Layer%20Definition%20of%20Done.md#5-stick-touch-release).

## Static check

Every layer's active LS and RS touch inputs were checked for a release that
removes layers. The check found these layers without one. The author reviewed
each:

| Layer | Missing on | Decision |
|---|---|---|
| Tap Covers, Double Tap Covers, Temp Cursor Gyro, Enter, Backspace, RTP Tap Cover | Both | Cover-type; inheriting is fine |
| `Gyro Off Ramp Up` | Both | Cover-type. Its only delay is the 5 ms RS handoff to `Turning Ramp Up 0`, which isn't a hold to complete |
| `Gyro` | Both | Base stateful layer, always directly on Base; inheriting is fine |
| `LST/RST: Entry Point`, `Tap Cover`, `Temporary Gyro` | Opposite stick | They are what the release removes; no opposite-stick release is needed |
| LST/RST Double Tap | Own stick | Always On; follows its self-first exit instead |
| `Transition Set 0` | Both | **Patched** (below) |

## Transition Set 0

The steering build repurposed `Transition Set 1` as the steering commit
transition. It replaced that layer's touch input with a release-only cleanup
of the side's LST/RST trio ([steering cleanup audit](../2026-09-30-steering-lean/CLEANUP-AUDIT.md)).
`Transition Set 0` kept its pre-steering touch input, which has one empty chord
per menu button plus the repeating guarded recovery. That's three entries,
with no release.

The patch keeps the recovery and adds Transition Set 1's release. To stay within
the three-entry budget, it merges the two empty menu chords into one
multi-button **Any** chord: Menu Left bit 12 + Menu Right bit 14 = `20480`. The
settings match, so the merge is allowed
([chord consolidation](../../resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)).
Base's gyro mask already uses both bits on the Deck. Nothing in the layer has
a delay, so the release has no pending add to complete first.

| Entry | Before | After |
|---|---|---|
| 1 | Chord Menu Left: empty | Chord Any(Menu Left, Menu Right): empty, `interruptable: 0` |
| 2 | Chord Menu Right: empty | Regular Press: repeating guarded recovery (unchanged) |
| 3 | Regular Press: recovery | Release: remove LST/RST `Temporary Gyro`, `Tap Cover`, `Entry Point` |

The LS and RS edges keep their original two-chord guards.

## Tools and checks

- [steam_layout/fixes/transition_set_0.py](../../archived/retired-fixes/transition_set_0.py) applies the patch. It is
  idempotent, works on numeric-ID or title-token files, and runs in the
  `python3 -m steam_layout.fixes` pipeline.
  [install_neptune.py](../2026-09-30-steering-lean/install_neptune.py) runs it,
  so a reinstall keeps it.
- [test_neptune_recovery.py](../../tests/test_neptune_recovery.py) pins the new
  touch shape in both variants.
- Deck gate T1 is in
  [manual testing](../../manual-testing.md#906-chorded-delays-and-dead-group-prune).
  It is untested, including whether the editor shows the merged chord as
  Select + Start with Any.
