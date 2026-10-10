# 90.45 — Right-stick sensitivity

The requested progression is applied to both default and alternative layouts:

| Layer | Sensitivity before | Sensitivity after | Vertical scale after | Configured vertical target |
|---|---:|---:|---:|---:|
| Base | 100 | 150 | 100% default | 150 |
| Turning Ramp Up 0 | 150 | 200 | 75% | 150 |
| Turning Ramp Up 1 | 200 | 250 | 60% | 150 |

The follow-up request asks for vertical/horizontal ratios to be recalculated
after the sensitivity change. The selected default interpretation holds the
configured vertical target at Base's 150 while horizontal speed increases:
`vertical scale = 100 × Base sensitivity / ramp sensitivity`.
Thus `200 × 0.75 = 150` and `250 × 0.60 = 150`. Horizontal scale stays
at its existing default. This replaces the old explicit vertical scales 80
and 67; their historical derivation is not documented, so this record does
not claim to reproduce an established old formula.

[Valve's source-mode documentation](https://partner.steamgames.com/doc/features/steam_controller/input_source_modes?l=english)
describes vertical scale as the ratio between vertical and horizontal motion.
The local Steam UI's Joystick Mouse controls separately expose sensitivity
and vertical/horizontal scales. These calculations use configured sensitivity
units, not a measurement of native pointer speed or a game's camera response.

Curves, deadzones, bindings,
feedback, activation thresholds and timing remain unchanged. Gyro Off Ramp Up
continues to inherit sensitivity. Higher same-mode layers inherit the nearest
lower sensitivity unless they explicitly override it; disabled sources and
other stick modes retain their behavior. No layer command or timer boundary
changes, and all 88 action-layer slots remain stable.

The builder extends frozen 90.44. This installation used `--from-working`
after verifying the complete live input equals its previously validated frozen
90.44 candidate. Reversing three sensitivity fields and two vertical scales restores that
input exactly; the fix pipeline is a no-op. The concise variant descriptions
were reviewed and retained, and both release titles become 90.45.

```bash
python3 findings/2026-10-10-right-stick-sensitivity/build_candidate.py
python3 findings/2026-10-10-right-stick-sensitivity/build_candidate.py --install
```

The [change report](change-report.txt) shows only the intended settings in
three source groups per variant. [Validation](validation.json) passes eleven existing
tests: the updated sensitivity contract and ten trigger/ramp scenarios.
All three changed layers have [scenario coverage](scenario-coverage.txt).
The [build audit](build-audit.txt) records Budget, Window, Flow and Cleanup
for both variants. Native stick speed/feel is not modeled by those scenarios;
the settings check verifies the saved numeric values.

Final JSON/VDF integrity and backups are recorded in
[snapshot-manifest.json](snapshot-manifest.json).
