# All guarded recovery removals repeat

Date: 2026-09-28. Applies to both Neptune 90.2 layouts. This change is committed
separately from the pending cleanup-audit documentation and vocabulary work.

## Convention and behavior

Every **guarded recovery binding** uses Hold to Repeat on its Regular Press
removal. When an input remains active after its protecting chord is no longer
active, recovery can retry rather than relying on a new press. The owner-held
chord still suppresses the cleanup during valid use because the removal keeps
the default Interruptable setting.

This convention concerns stale-state recovery. It does not turn release exits,
Always On expiry, threshold exits, deliberate transitions, or delayed-apply
resets into the same operation. Their conditions and timing remain intact.

## Exact change

Added only `settings.hold_repeats: "1"` to **104 existing removal entries per
layout**. Every changed entry previously had no settings and contains only
`remove_layer` subcommands. No key, mouse, or layer-add action was made repeating.

| Existing recovery family | Default / alternative | Entries changed per layout |
|---|---|---:|
| Four single modifiers, regular and Gyro | L1/R1 / L2/R2 | 13 each; 52 total |
| Four Mod 2 variants, both orders and Gyro | L1!R1 and R1!L1 / L2!R2 and R2!L2 | 12 each; 48 total |
| Two scroll layers, both stick-touch inputs | L1 Scroll Down and R1 Scroll Up / L2 Scroll Down and R2 Scroll Up | 2 each; 4 total |
| **Total** | | **104** |

Each file now has **185 active guarded recovery entries, all repeating**,
instead of 81 repeating and 104 without repeat. Its six dormant guarded
recovery entries already repeated and are unchanged. No extra command entry,
new LS-edge binding, new cleanup target, or new chord guard was added.

Bindings and their order, interruption settings, repeat-rate settings,
delayed-apply resets, Always On boundaries, source geometry, movement output,
layer/preset ordering, metadata/version, and VDFs are unchanged. No explicit
repeat rate was introduced; this follows the existing recovery convention
without assuming a value for the Steam client's default interval.

## Verification

- Ran the prep skill's ordering/unique-title checks and actual `to-titles`
  conversion before editing temporary copies, then finalized with `to-ids`.
  All 1,437 references per layout round-trip exactly.
- Verified structurally that undoing only the 104 new settings in each file
  reproduces its complete original JSON data. This also verifies all guards,
  targets, other activators, and Always On entry/exit sequences are unchanged.
- Scanned every group and activator bank: all 191 guarded removal entries per
  layout have Hold to Repeat, including the six dormant entries.
- Both complete command-budget checks pass; maximum remains three entries per
  input. No unresolved title references remain.
- Verified both VDFs still match the pre-change commit.

Deck validation remains: hold a recovery input while the owner chord is held
and confirm no cleanup, then release the owner and confirm recovery can repeat;
also test interrupted holds, both Mod 2 orders, Gyro variants, and both stick
touches in the scroll layers. Check protected Double Tap windows and inherited
routes on the target client. Static validation does not establish runtime
interruption or repeat scheduling.

| Source | SHA-256 before | SHA-256 after |
|---|---|---|
| [Default](../../neptune/single-set-default_hold-gyro_latest.json) | `acc224322b6937903dd8cfb1477bd54d0dc93213fc9bb2db03e7364372880c48` | `73acd6d0879d66ef54500dedc0e03fef25e211e027ff95cf76ea84a0a03ce492` |
| [Alternative](../../neptune/single-set-alternative_hold-gyro_latest.json) | `b3ea92487b475c8f790531caf73f93a297dc3f50bea47eaad9babefca0c1aac6` | `435ac1acbdae6ca6dcbb4994ef83572e888893cc09098b303502e6574ad2d522` |
