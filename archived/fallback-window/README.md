# The fallback window's scenario tests (90.31 and 90.32)

Retired on 2026-10-05, when 90.33 deleted `Steering | LS: Fallback Window`
and `Steering | LS: Fallback Hold`. The scenario tests run on the working
layouts, so these two files can't run any more. They are kept as the record of
what the window did.

- [tests/test_scenarios_90_31.py](tests/test_scenarios_90_31.py): F1 to F9 and
  G1 ([record](../../findings/2026-10-04-fallback-window/README.md)).
- [tests/test_scenarios_90_32.py](tests/test_scenarios_90_32.py): R1 to R4
  ([record](../../findings/2026-10-04-fallback-window-replacements/README.md)).

The static tests of both builds still run: `tests/test_fallback_window.py` and
`tests/test_fallback_window_replacements.py` build with the frozen builders.
The fallback's scenarios since 90.33 are in `tests/test_scenarios_90_33.py`.
