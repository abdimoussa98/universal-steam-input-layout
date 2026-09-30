# Native results — unfilled

No Deck trials have been run by this implementation session. Static validation
is recorded separately and is not a device pass.

## Run metadata (copy per run)

- Probe stem and numeric JSON SHA-256 from `build-manifest.json`:
- Steam version/channel, OS and controller/firmware:
- Variant and fresh-load/import procedure:
- Application and confirmation the correct layout is active:
- Observer trace filename; focus remained valid:
- Initial stack, physical inputs already held, ordered action sequence:
- Expected key/wheel/feedback trace:
- Actual delivered trace, timing uncertainty, sound/haptic observation:
- Result: UNTESTED / PASS / FAIL / UNVERIFIED:
- Failure branch, proposed correction, retest:

## Required first-slice trials

Repeat movement rows for owner-output and entry-output candidates, both variants.
Clock rows apply to both clock exports. Record individual trials, not just an
aggregate checkmark.

| Case | Expected / evidence sought | Status |
|---|---|---|
| Existing rule-test T4 and key-output add/removal | Record native exposure behavior before choosing output site | UNTESTED |
| S1 fresh W and S acquisition | Exactly one intended movement key; release leaves no stuck key | UNTESTED |
| S1 carried LS up, down and diagonals | Measure W→W continuity and W↔S transitions; no W+S overlap | UNTESTED |
| S1 opposite held then dominant release | No opposing key during drive; return to WASD and quarantine; subsequent clean acquisition | UNTESTED |
| S2 centered and deflected entry | Guard retires at center or acquisition; cannot re-enter within session | UNTESTED |
| S2 partial travel and direct reversal | Calibrate center hysteresis and inspect marker; no premature retirement from carried movement | UNTESTED |
| S2 rearm with both controls held/released in either order | No new owner until both released; no dead region preventing recovery | UNTESTED |
| S7 near-simultaneous acquisition and release/press | Save traces; no claim of exact-sample priority from manual trial | UNTESTED |
| Alternative shallow/full trigger stages | No duplicate ownership, early release or opposing output | UNTESTED |
| S4 plain 5-second W hold | F9 begins near 2.5 s; F10 near 5 s; F1 after exit | UNTESTED |
| S4 release before/after warning and retry | No late F9/F10; new hold has fresh timing | UNTESTED |
| S4 B held before/during warning | Determine whether absent removals reset either delayed activator | UNTESTED |
| Reset while held; Steam-overlay release interruption | Record stuck outputs/owners and recovery behavior | UNTESTED |

S3/S5/S6/S8/S9 full coverage and S10 gestures require later probes/integration;
these rows do not mark those gates passed.

## Static validation recorded 2026-09-29

- 39 Python unit tests passed, including six new probe invariant tests.
- Six converter tests and two observer event-recording tests passed.
- All six VDF exports passed the converter's key/value/order verification.
- All twelve readable/numeric layout JSONs passed the three-entry budget audit.
- No Always On actions are introduced by these diagnostic layouts.
- Both working Neptune JSON hashes match the plan-audit baseline.
- Observer event logic was tested with a DOM stub; browser rendering, native
  key delivery, trigger/center thresholds, haptics and Steam scheduling remain
  unverified on the Deck.

## Additional generated probes

`default-long-clock` and `alternative-long-clock` compare native Long Press
2500/5000 ms timing with the earlier Fire Start Delay candidates. Repeat the
plain hold, release/retry and B-removal-stressor rows with both forms; native
results remain UNTESTED. `native-gestures.vdf` adds the no-window gesture
comparison described in the complete candidate handoff.
