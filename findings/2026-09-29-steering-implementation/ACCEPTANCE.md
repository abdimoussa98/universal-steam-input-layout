# Candidate acceptance — device results pending

Use the [observer](../2026-09-29-steering-native-probes/observer.html) and copy the
[run metadata template](../2026-09-29-steering-native-probes/RESULTS.md#run-metadata-copy-per-run).
Record each candidate's numeric JSON hash from `manifest.json`. Run both variants,
both owners and both directions. No row below is a device pass yet.

| Gate | Candidate procedure | Required observation | Status |
|---|---|---|---|
| S1 | Enter centered, acquire right W then left S separately; repeat with LS up/down/diagonal already held; release dominant | Correct key edges, no W+S overlap or stuck output; carried W continuity measured | UNTESTED |
| S2 | Enter with LS deflected and keep W beyond 5 s; center, then begin a new fallback W hold; repeat with driving acquisition before center | Guard survives first hold; retirement is one-time; subsequent hold warns/exits; physical center threshold recorded | UNTESTED |
| S3 | Short Up/Down → center → second same direction; release dominant or opposite at different points in the 150 ms window | Exact active window exits before other mutations; no final release scroll, no unrelated layer resurrection | UNTESTED |
| S4 | Hold fallback W past 5 s; repeat while touching/releasing pads, crossing RS ramp edges, changing gyro and using permitted controls | 2.5/5 s deadlines do not drift; W release/owner entry cancels; owner release with LS up starts fresh | UNTESTED |
| S5 | Observe and record warning pulses and final exit feedback; cancel just after warning and retry | Repeated vibration stops on cancellation; beep/vibration once on exit; no keyboard marker substituted in candidate | UNTESTED |
| S6 | Hold A through Normal Up → Mod2 → Normal Down → center; repeat with two mapped inputs, D-pad/click/menu keys | Changed old key releases, replacement waits for fresh press, unchanged Mod2 hold survives helper/window changes | UNTESTED |
| S7 | Near-simultaneous both driving presses; opposite+LS; dominant release+opposite press; face+center; W release near 5 s | No transient forbidden output or stale branch; record order uncertainty rather than claim exact ties from hand timing | UNTESTED |
| S8 | Menu with either stick already deflected; later partial deflection near 300 ms; short/long release; explicit Fn then deflect; next centered menu hold | No automatic Fn leak, protected tap timer restarts once, explicit Fn survives, subsequent automatic Fn remains functional | UNTESTED |
| S8 commit | Right Menu + LS click with LS touch/edge held; release Right Menu; repeat through deliberate Fn; try Left Menu abort and other-menu held | One steering entry, WASD carried, no Tab/Q/punctuation leak or lingering mode shift; no stick-recovery race | UNTESTED |
| S8 re-entry | Open menu from fallback/centered drive or normal repeat, then select steering again; press menu keys while each bank is selected | Ordered steering exit before actual menu entry; bank-selected menu keys preserve Insert/Delete, Home/End, Page Up/Down | UNTESTED |
| S9 | Open Steam overlay during Guard, drive, each gesture phase and fallback warning; release controls there and return | No stuck key, owner or warning; active window expires/self-exits before recovery; no delayed Fn/stroke resurrection | UNTESTED |
| S10 | Run separate native comparison: short, long, double, reversal, action consumption, carried/context entry | Determine whether native activators can replace stroke/window helpers without violating semantics | UNTESTED |

## Modifier and scroll sequences

- Own W, fresh LS Up, A: H. Release to center: no scroll because the action
  consumed the stroke. Repeat Down: G, no release scroll.
- Own W, Up held; opposite press; A: M. Move Down while opposite held; opposite
  release: G bank becomes available, but that carried stroke cannot scroll.
- Own either direction; Mod2 active; short fresh Up, center, A during the double
  window, then fresh Up held: M remains available and scroll repeats. A does not
  consume Mod2's gesture. No normal and Mod2 taps may form a double together.
- Normal same-direction double and second hold: Base face mapping while repeating.
  Mod2 double and hold: Mod2 mapping while repeating. Release produces no extra tick.
- During warning, acquire W/S: warning stops. Release dominant with LS still up:
  start a new fallback clock even if opposite remains held in Rearm.
- Release dominant while opposite remains held, then repress dominant before
  opposite releases: neither may acquire. After both released, a fresh press works.

## Local evidence already recorded

- 54 Python tests and 8 Node tests passed after candidate wiring.
- Both candidate VDF exports verify serialized keys, values and order.
- Full command budgets pass; runtime references round-trip with no unresolved
  tokens; one action set and sequential appended presets are retained.
- Eight new windows pass exact-self-first exit, add-last entry, timeout-only-self
  and inherited mutation-input coverage checks.
- Command-array traces cover both owners/variants through Normal → Mod2 → repeat
  → current-direction restoration → dominant release. These execute the encoded
  arrays; they do not emulate Steam's scheduling or output reference counting.
- Working Neptune JSON hashes remain the reviewed 90.4 hashes. Candidate copies
  have separate titles/hashes and no release version bump or upload.

A failing S6 requires explicit per-input rearm memory unless another native
mechanism passes; a failing S4 requires a proven clock/isolation change. Neither
failure is permission to relax the user's output or timing requirements. Use
[the plan's failure branches](../../plans/2026-09-29-steering-implementation-plan.md#decisions-and-failure-branches).
