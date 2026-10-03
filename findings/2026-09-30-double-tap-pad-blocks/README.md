# Double Tap windows: trackpads off the layer API (90.6)

**Author direction, 2026-09-30:** both trackpads must be blocked from the
layer API during the seven Always On Double Tap windows. Where there's an
obvious use, replace the layer with the direct key bind.

## Before and after

| Pad input | Base | Window before | Window after |
|---|---|---|---|
| Left swipe back (`dpad_west`) | add `Escape` key layer | disabled source | `key_press ESCAPE` |
| Left swipe forward (`dpad_east`) | add `Enter` key layer | disabled source | `key_press RETURN` |
| Left swipe up (`dpad_north`) | add `Tab` key layer | disabled source | `key_press TAB` |
| Left swipe down (`dpad_south`) | add `Backspace` key layer | disabled source | `key_press BACKSPACE` |
| Left click | hold `LTP: Arrow Keys` | disabled source | cleared |
| Left touch | (the key layers' own touch-release cleanup) | disabled source | cleared |
| Right pad mode, six windows | mouse (`absolute_mouse`) | disabled source | mouse, settings `layer: "1"` only (inherits Base's feel) |
| Right click, six windows | hold `RTP: Mouse Buttons` | disabled source | cleared |
| Right touch, six windows | add `RTP: Entry Point` | disabled source | cleared |
| Right click, RTP Double Tap | hold `RTP: Mouse Buttons` | not defined (dpad mode) | cleared |
| Right touch, RTP Double Tap | add `RTP: Entry Point` | not defined (dpad mode) | not bound: an `allow` exception |

The window's left pad copies Base's swipe group: mode `2dscroll`, sensitivity
`50`, and haptic intensity `1` on the swipes. The keys come from the key layers
that Base adds. One difference: a key layer holds its key until the finger
leaves the pad, while the direct bind holds it only while the swipe direction
is held. Each window has its own pad group, so no group IDs changed.

**Right pad (author, 2026-09-30):** the cursor keeps moving during the
window. In the six windows that used to disable the pad, it's now the mouse
with only click and touch cleared. Its settings are just `layer: "1"`, so
friction, acceleration and haptics come from Base, following the repo's
rule of keeping tuning in Base. The derived-stack audit found no new layer-API
route through the pad.

**RTP Double Tap** keeps its dpad-mode selection pad. A second tap north or
south goes to Circular Scroll, and anywhere else stays in mouse mode. Touch
isn't bound there; it's an `allow` decision in
[traced_stacks.json](../../steam_layout/traced_stacks.json).

## Tools and checks

- [steam_layout/fixes/window_pads.py](../../steam_layout/fixes/window_pads.py) applies the change. It is
  idempotent, works on numeric-ID or title-token files, and runs in the
  `python3 -m steam_layout.fixes` pipeline.
  [install_neptune.py](../2026-09-30-steering-lean/install_neptune.py) runs it.
- [test_double_tap_windows.py](../../tests/test_double_tap_windows.py)
  requires, in both variants:
  - the swipe keys, with click and touch cleared and no layer commands on the
    left pad
  - a right pad that stays the mouse, with click and touch cleared, except
    RTP Double Tap's dpad selection pad, with click cleared
  - every window's stick-touch release removing the window first, then the
    side trio
- [audit_inheritance.py](../../tools/audit_inheritance.py) now blocks the right-pad
  `click` route and passes both layouts.
- Deck gate P1 is in [manual testing](../../archived/manual-testing.md#906-chorded-delays-and-dead-group-prune).
