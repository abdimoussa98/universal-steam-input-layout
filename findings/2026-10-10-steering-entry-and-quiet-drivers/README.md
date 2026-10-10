# 90.44 — Steering entry, quiet drivers and stateful cleanup

Implements the [approved plan](../../plans/2026-10-10-entry-guard-edge-and-quiet-drivers.md)
on both variants, extending 90.43. Both live JSON/VDF pairs are finalized,
validated and backed up under `versions/neptune/90.44/`.

## Result by layer

| Layer or path | Change |
|---|---|
| `Steering \| LS: Entry Guard` | Adds the old fallback-style inward edge chord: either driver held removes only Guard, silently. Default selects L1/R1; alternative selects L2/R2. The source stays non-inverted; the original direction/outer-edge Releases and driver/menu handoffs remain. Centered entry without a driver still protects the first push. |
| Steering W/S layers and their four incoming entries | Every W/S-owned activator is explicitly Off, along with each W/S LS D-pad mode override and the parent entry feedback. Outputs, repeats and cleanup order are unchanged. |
| Steering Modifiers 0/1 | Their LS-edge Releases and following 150 ms Double Tap completion are explicitly Off. Their recovery fixes and scroll behavior remain. |
| Both Steering Modifier 2 layers | The existing broad Release clear retains Steering and Cursor Gyro. Other cleanup targets remain, including Gyro. The former Steering-removal beep disappears with that command. |
| Both Gyro Modifier 2 layers | Both driver Releases retain Cursor Gyro. The ordinary Gyro toggle and its single beep remain. |
| Base and turning ramps | No sensitivity edit was needed: the complete active right-stick settings already match the July reference and remain identical. |

There are still **88 action layers**. Entry Guard keeps runtime slot **65**;
no layer or preset was inserted, renamed or reordered. Per variant, six Release
entries across four Modifier 2 layers lose Cursor Gyro removal; two of those
also lose Steering removal. There are 54 activator haptic-field changes and two
W/S mode overrides. Already-Off W/S activators remain Off.

Fn adds retain their Low bump. Steering's full up/down clear retains Soft Press
threshold `29031`, 50 ms repeat, one Steering beep and one Low bump. It remains
an independent exit: a full direction still held when Modifier 2 clears can
expose it and clear Steering. Cursor Gyro's deliberate both-stick and menu
exits also remain. This release does not implement the deferred two-driver
release-order redesign or add its proposed covers.

Haptic changes follow ownership. Other layers that override W/S inputs keep
their own feedback, including non-completion actions inside Double Tap windows.
See the [inheritance review](inheritance-review.md) for affected stacks,
intentional timer blocks and retained Cursor response with Gyro on or off.

## Build and evidence

```bash
python3 findings/2026-10-10-steering-entry-and-quiet-drivers/build_candidate.py
python3 findings/2026-10-10-steering-entry-and-quiet-drivers/build_candidate.py --install
python3 findings/2026-10-10-steering-entry-and-quiet-drivers/validate.py
python3 -m tools.audit_build
```

The [component](followup.py) edits only title-form data. Its builder requires
the complete fix pipeline to be an exact no-op, preserving the requested
cleanup exclusions. Both full frozen-chain builds match the installed JSONs
byte for byte; [rebuild verification](rebuild-verification.json) also compares
their reports with builds from the verified live 90.43 inputs.

The [change report](change-report.txt) contains exactly twelve changed layers
per variant. The [build audit](build-audit.txt) passes Budget, Window, Flow and
Cleanup for both variants. The [feedback and sensitivity inventory](feedback-and-sensitivity.json)
finds 30 beep-bearing entries, each with one beep flag, and exact July-reference
right-stick settings in Base and all three ramp layers.

| Final verification | Result |
|---|---|
| [Final validation summary](final-validation.json) | 293 distinct scenario methods and 254 regression methods verified across the full and targeted runs below. |
| [Full run](validation.log) | 289 of 293 scenarios and 247 of 248 regressions passed initially; all five outdated expectations/registry omissions were corrected and their follow-ups passed. |
| [Legacy scenario follow-up](targeted-legacy-results.json) | Four older live tests now require Steering to survive; pad cleanup, 5 ms timing, held-click re-entry and final released-output checks still pass. |
| [Rule registry follow-up](registry-followup.log) | 28 checks pass after listing the new R111 scenarios in the rule's Checked by column. An accidentally broader rerun was interrupted before this focused run. |
| [Exact preservation tests](targeted-static.log) | Six new contracts plus six existing feedback tests pass against fresh frozen-90.43 builds. The six existing tests overlap the full regression run. |
| [Held release orders](held-release-orders-scenarios.log) | Two extended scenarios pass 192 combinations; [held-direction cleanup](held-mod2-scenario.log) passes 64 combinations. |
| [Changed-layer coverage](scenario-coverage.txt) | All twelve changed layers in each variant are reached; recorded before the new backups. |
| [VDF exports](export-verification.json) | Both serializers verify keys, values and order; JSON/VDF metadata and ordered layer commands/flags match. |
| [Version backups](snapshot-manifest.json) | All four JSON/VDF backups match their live files byte for byte. |

The [initial validation counts](validation.json) are retained rather than
rewritten as a clean first run. The four legacy scenario failures expected
Steering removal, which this release intentionally deletes. The single
regression failure was the missing R111 scenario declaration, now corrected.
No layout changes were needed for these follow-ups. Earlier new-test fixture
corrections are recorded in [targeted-scenarios.json](targeted-scenarios.json).

Ready to load: [default VDF](../../neptune/single-set-default_hold-gyro_latest.vdf)
and [alternative VDF](../../neptune/single-set-alternative_hold-gyro_latest.vdf).
The concise descriptions were reviewed and retained; both titles are 90.44.
The [unverified assumptions](unverified-assumptions.txt) remain device checks.

## Fresh-load checks on the Deck

1. Enter Steering centered without a driver, then push and release: the first
   movement remains protected. Repeat with full up/down already held on entry.
2. Enter with both drivers held and LS deflected, then center LS: only Guard
   leaves, silently. Check both bumpers in default and both soft/full trigger
   pulls in alternative. Also check each single-driver handoff.
3. Hold W/S, use up/down Modifiers 0/1, then center: the driver feedback,
   modifier release and automatic wheel completion should be quiet. Check the
   separate Fn bump and intentional full-deflection clear feedback.
4. Quick-release the second driver from Steering Modifier 2: Steering remains
   and the clear is silent. Test with LS centered separately from a full held
   direction, which can expose Steering's independent stick clear.
5. From Cursor Gyro, toggle Gyro off and on in both driver press/release orders:
   Cursor stays, each Gyro toggle beeps once, and its response remains intact.
   Check deliberate both-stick and menu exits afterward.

The simulator checks modeled bindings and stacks. It cannot establish native
inward D-pad edge delivery (A19/A54), physical Soft Press distance, actual
gyro motion, or audible/tactile feedback. The release records those assumptions
separately from automated results.
