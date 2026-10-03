# Second-press cover resets as a last, 4th entry (90.6)

**Author decision, 2026-09-30.** A successful double tap lands on a
second-press layer, where holding the button adds that layer's Double Tap Cover
after 150 ms. That delayed add had no stuck-delay reset, because the input
already had three entries. It now has the standard reset as a **4th entry,
placed last**.

| Layout | Layer | Input |
|---|---|---|
| Default | `L1: Scroll Down` / `R1: Scroll Up` | Left / right bumper |
| Alternative | `L2: Scroll Down` / `R2: Scroll Up` | Left / right trigger soft pull (`edge`) |
| Both | `Menu Left: Escape` / `Menu Right: Tab` | Select / Start |

## The change

The existing entries are unchanged. The new entry is a Regular Press that
removes **only** that layer's Double Tap Cover, with `hold_repeats: 1`,
`repeat_rate: 200` (delay + 50 ms) and `interruptable: 0`. That is the
[interrupted-apply pattern](../../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies).
Each cover overrides the same input, so the reset stops once the cover is
applied.

**Why it's last.** Steam's desktop configuration drops every entry after the
third ([budget origin](../../resources/Steam%20Input%20JSON%20Structure.md#command-entry-budget)).
The reset is the least important entry, so it must be the one desktop drops.
The JSON form keeps repeated activator types together as one list, so the
Regular Press list moves to the end:

| Position | Before | After |
|---|---|---|
| 1 | Regular Press: output (key or wheel) | Release: back into the Double Tap window |
| 2 | Release | Chord: add the cover after 150 ms |
| 3 | Chord | Regular Press: output (unchanged) |
| 4 | — | **Regular Press: reset** |

On desktop the reset is lost, and the other three entries work exactly as
before. The exported VDF was parsed to confirm this order.

## Tools and checks

- [steam_layout/fixes/cover_resets.py](../../steam_layout/fixes/cover_resets.py) applies the change. It is
  idempotent, works on numeric-ID or title-token files, and runs in the
  `python3 -m steam_layout.fixes` pipeline. It
  must find exactly four layers per layout.
  [install_neptune.py](../2026-09-30-steering-lean/install_neptune.py) runs it
  after the RTP fix and the prune, so a reinstall keeps the change.
- `audit_command_budget.py` allows only this shape as `allowed_fourth`: four
  entries, with the last one being a repeating, non-interruptible removal of
  the same input's chorded-delay target. Any other overflow still fails.
- [test_layout_hygiene.py](../../tests/test_layout_hygiene.py) pins these eight
  inputs, their order and their settings.
  [test_audit_command_budget.py](../../tests/test_audit_command_budget.py)
  covers the rejected shapes.
- Both installed files match the pre-install layout plus this fix, byte for
  byte, and title-form and numeric edits produce identical output.

## Deck checks (untested)

See [manual testing](../../archived/manual-testing.md#906-chorded-delays-and-dead-group-prune), gates R1–R3.
