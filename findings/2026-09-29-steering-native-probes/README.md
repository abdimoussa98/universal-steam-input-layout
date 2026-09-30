# Steering native probes: first implementation slice

Status: **generated and statically checked; no Deck results yet**. These are
standalone diagnostic layouts, not the production steering feature. Start with
[the existing held-input rule-test](../2026-09-29-held-input-layer-transitions/AUDIT.md#deck-checks).
Then use this slice to select a movement-output site and verify neutral/rearm
behavior before building dependent gesture layers.

## Files and build

Run from the repository root:

```sh
python3 findings/2026-09-29-steering-native-probes/build_probes.py --vdf
python3 -m unittest discover -s tests -p 'test_steering_probes.py'
```

Each of the eight candidates has readable title-token JSON, numeric JSON and a
verified VDF export. `build-manifest.json` records numeric JSON hashes. Generation
reads current Base LS movement settings from each working layout; it does not
edit either working layout. Rebuilding after Base changes can change these hashes.

| File stem | What it tests |
|---|---|
| `default-owner` / `alternative-owner` | Ordinary W/S output attached to owner input after its layer is added over the held control |
| `default-entry` / `alternative-entry` | W/S output attached to the same entry binding that adds the owner; owner input then outputs nothing |
| `default-long-clock` / `alternative-long-clock` | Native Long Press comparison: same F9/F10 markers and B stressor, using hold time instead of Fire Start Delay |
| `default-clock` / `alternative-clock` | Three-entry W clock: W, repeating F9 after 2.5 seconds, F10 plus exit after 5 seconds |

The clock uses **keyboard markers, not implemented haptic feedback**. It tests
S4's timing candidate only, not S5 sound/vibration or full coexistence. B removes
an absent diagnostic layer every 100 ms to probe whether unrelated removals
restart the clock. That is an intentional timer stressor, not production behavior.

## Load and observe

1. Select a diagnostic VDF for a dedicated test application through your existing
   local Steam import workflow. Freshly load it and confirm its title. Never use
   visible layer names as the only output evidence.
2. Open [observer.html](observer.html) in the test application/browser receiving
   that application's Steam layout. A browser launched outside that context may
   receive the desktop layout instead; verify F-key markers before testing.
3. Enter a run label, start recording, and keep the capture panel focused.
   Browser/OS shortcuts may intercept some keys despite `preventDefault`; verify
   F1–F6/F9/F10 delivery first. Stop before clicking elsewhere, then download JSON.
4. Record client/OS/controller version, build hash, load procedure and results in
   [RESULTS.md](RESULTS.md). All device rows start UNTESTED. The logger does not
   observe internal activator order, full layer stacks or controller sampling.

## Controls and expected movement cases

- Right Menu: enter Steering + Entry Guard from Base. This is **temporary direct
  harness entry**, not the final Right Menu + LS click menu flow. Already inside
  the harness it is blocked, so it cannot restart a guard or reorder an owner.
- Left Menu: clear the diagnostic family to Base. All these probes are untimed
  ordinary layers, with no Always On windows requiring a window-specific reset.
- D-pad Right: F1 Base, F2 Steering, F3 Guard, F4 W Owner, F5 S Owner, F6 Rearm.
  Querying the marker reports only the effective D-pad binding at that instant.
- Default R1 drives W, L1 drives S. Alternative R2 drives W, L2 drives S using
  the existing trigger `edge` source. Exercise both shallow and full travel.
- The opposite control is blocked in an owner: no Mod 2 yet, and no opposing
  W/S output. LS vertical is blocked while driving; A/D remains available.
- Dominant release removes its owner then adds Rearm. Both controls must be
  released before another owner can engage. Rearm includes candidate guarded
  release handling plus repeating stick/center recovery; neither is native-proven.
- Guard preserves WASD and retires on LS center or driving acquisition. Its
  inverted edge radius is 6553 (nominal 20%; static hysteresis estimate ~10% on,
  ~30% off). Calibrate the actual physical threshold; do not call this measured.
- Rearm center radius 17000 overlaps the WASD direction region so a neutral/
  direction sensing gap is not intentionally built in. Test diagonals, partial
  travel, already-neutral entry and both-control release orders.

For each movement candidate: hold LS up before entry; enter centered; acquire W
and S fresh; acquire while LS up/down/diagonal; press opposite while driving;
release dominant with opposite held; release opposite and acquire again; hold
both near-simultaneously. Record every W/S edge, any gap, overlap or stuck output.
Try reset while moving and while driving. Repeat after opening Steam overlay,
releasing there and returning. A stuck owner after a missed release is a recorded
failure: this first slice has no production stale-owner recovery yet.

For the clock: Right Menu enters Steering without Guard. LS up holds W; F9
should start near 2500 ms and repeat at 250 ms; F10 should mark expiry near
5000 ms. Base still outputs WASD after expiry, so W may remain held until LS is
released. Release at roughly 2.4, 2.6 and 4.9 seconds and retry. Compare an
uninterrupted hold with B held before and during the warning. Log delivered
keyboard repeats separately from browser/OS auto-repeat; the F9 cadence is not
proof of a vibration cadence. D-pad Right reports F1/F2 (F3 is the unused
Clock Disturbance layer and should never appear). Driving acquisition and
return-to-fallback clock tests await the selected movement path.

## Binding and inheritance manifest

Every source is explicitly built in a minimal action set; no production menu,
trackpad, gyro, ramp, Fn, touch or mode-shift hooks are imported. This deliberately
isolates the probes; it does not validate production coexistence.

| Layer/input | Entries | Output / mutations / inheritance |
|---|---:|---|
| Base LS directions | 1 each | Copied WASD key settings; touch/click/Walk scaffold excluded |
| Base Right Menu | 1 | Add Steering, then Guard; clock adds Steering only |
| Every Left Menu | 1 | Reverse binding array executes top-family removals before Steering |
| Steering/Guard driving control | 1 | Remove Guard, add corresponding owner; entry candidate also sends W/S |
| Owner dominant | 2 | Ordinary output (or explicit no-op); release removes owner then adds Rearm |
| Owner opposite | 1 | Explicit no-op; no opposing key or modifier |
| Owner LS vertical / lateral | 1 each | Explicit vertical no-op / A,D payload |
| Guard inverted LS edge | 1 | Repeating Guard self-removal; no timer |
| Rearm controls | 2 | Release removal + held-any uninterruptible no-op chord; interruption is under test |
| Rearm LS directions | 3 | Uninterruptible WASD output, interruptible repeating self-removal, held-any uninterruptible guard |
| Rearm inverted edge | 2 | Interruptible repeating self-removal + held-any guard |
| Every D-pad Right | 1 | Unique F-key; no layer mutation |
| Clock LS up | 3 | W, delayed repeating F9, delayed F10 + self-removal |
| Clock B | 1 | Repeating removal of absent Clock Disturbance, intentionally tests timer interference |

There are five movement helpers plus Base, or two clock helpers plus Base.
These are diagnostic counts, not a forecast of the final steering layer count.
Arrays execute bottom-to-top; no assertion is made about separate activator order.

## Next integration boundary

Record S1/S2 results before selecting either movement-output candidate. The
entry candidate may lose its output when its input is overridden; the owner
candidate may fail to acquire a key when added over a held input. That comparison
is the purpose of the exports. Neither is declared the winner by static tests.

S10 native gesture comparison, owner-aware windows if necessary, full timer
coexistence, haptic feedback, mapped-hold suppression and protected-menu
integration remain pending. Keep the main layouts unchanged until their relevant
proof gates pass. The [implementation plan](../../plans/2026-09-29-steering-implementation-plan.md)
contains the failure branches and subsequent sequence.

## Implementation continuation

The [complete candidate exports](../2026-09-29-steering-implementation/README.md)
now wire protected entry, direction banks, explicit gesture windows and actual
haptic/exit bindings. Use these small probes first to resolve their native
assumptions. `build_native_gestures.py` also generates the no-Always-On
`native-gestures.vdf` comparison; its controls and acceptance cases are in the
candidate handoff. These files do not turn earlier untested rows into passes.
