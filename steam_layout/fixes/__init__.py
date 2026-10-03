"""Idempotent post-install fixes for the Neptune layouts, as one ordered pipeline.

The steering install rebuilds `neptune/*_latest.json` from a frozen source, so
every fix made since then must be re-applied in order. Each fix is idempotent:
the working layouts are a fixed point of the pipeline, which the tests check.

    python3 -m steam_layout.fixes neptune/*_latest.json            # apply, write
    python3 -m steam_layout.fixes neptune/*_latest.json --dry-run  # report only

After a real run, regenerate the VDFs (`node convert_vdf.mjs <json>`) and follow
the steam-layout-apply skill.

| Fix | What it does | Record |
|---|---|---|
| rtp_scroll | RTP scroll Long Press -> chorded delay | findings/2026-09-30-dead-group-prune |
| dead_groups | prune plain-inactive slots and unreferenced groups | findings/2026-09-30-dead-group-prune |
| cover_resets | 4th-entry cover resets on the second-press layers | findings/2026-09-30-second-press-cover-reset |
| menu_combo_keys | Backspace/Enter typed by the menu chords; the two overlay layers removed | findings/2026-10-01-intended-flow-checker |
| window_pads | trackpads off the layer API in Double Tap windows | findings/2026-09-30-double-tap-pad-blocks |
| window_routes | block derived layer-API routes under the windows | findings/2026-09-30-derived-window-blocks |

`window_routes` runs last because it audits the layout the others produce.

Retired: `transition_set_0` (2026-10-01, now in archived/retired-fixes/). The
stateful transitions build writes both transition layers whole, with their
stick-touch releases.
"""
from . import cover_resets, dead_groups, menu_combo_keys, rtp_scroll, window_pads, window_routes

PIPELINE = [
    ("rtp_scroll", rtp_scroll.fix),
    ("dead_groups", dead_groups.prune),
    ("cover_resets", cover_resets.fix),
    ("menu_combo_keys", menu_combo_keys.fix),
    ("window_pads", window_pads.fix),
    ("window_routes", window_routes.fix),
]


def apply_all(data, only=None):
    """Apply the pipeline to `data` in place; returns {fix name: report}."""
    return {name: fix(data) for name, fix in PIPELINE if only is None or name in only}
