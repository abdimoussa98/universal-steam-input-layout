# Stuck RTP entry layer blocks right-stick ramp-up

Date: 2026-09-27. Compared the active bindings in the [Neptune layout](../../neptune/single-set-default_hold-gyro_latest.json) and [July snapshot](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json), using readable layer targets and accounting for device-specific chord encoding. No layout was modified and no independent runtime reproduction was performed.

The July snapshot contains the fix the author recalls: **`RTP: Entry Point` changes its right-stick edge from an unconditional empty binding to cleanup guarded by RTP touch.** Its own description is “fix ramp up being disabled due to stuck rtp entry layer.” The reusable lesson is also recorded in [Steam Input JSON Structure](../../resources/Steam%20Input%20JSON%20Structure.md#empty-bindings-and-stuck-layer-cleanup).

| Right-stick edge in `RTP: Entry Point` | Neptune | July |
|---|---|---|
| Active group | `1163` | `204` |
| RTP still touched | Empty binding | Empty binding through an RTP-touch chord |
| RTP no longer touched | Still empty; no edge cleanup | Remove `RTP: Tap Cover` and `RTP: Entry Point` |
| Removal repeats | No removal | `hold_repeats: "1"`; no explicit `repeat_rate` |

Neptune's `right_joystick active` group `1163`, `inputs.edge`, is at lines 10104–10112:

```json
{
  "activators": {
    "Full_Press": {
      "bindings": {
        "binding": "controller_action empty_binding, , "
      }
    }
  }
}
```

An explicit empty binding consumes that input instead of exposing the lower layer's binding. If `RTP: Entry Point` remains applied after the trackpad interaction, pushing the right stick to the outer edge therefore cannot reach the lower ramp-up command through this path.

July's group `204`, `inputs.edge`, at lines 7709–7732 replaces it with:

```json
{
  "activators": {
    "chord": {
      "bindings": {
        "binding": "controller_action empty_binding, , "
      },
      "settings": {
        "gyro_ratchet_button_mask": "1048576",
        "interruptable": "0"
      }
    },
    "Full_Press": {
      "bindings": {
        "binding": [
          "controller_action remove_layer {{Base::RTP: Entry Point}} 0 0, , ",
          "controller_action remove_layer {{Base::RTP: Tap Cover}} 0 0, , "
        ]
      },
      "settings": {
        "hold_repeats": "1"
      }
    }
  }
}
```

Mask `1048576` means **right-trackpad touch**, corresponding to Neptune `chord_button: "17"`. While RTP is touched, the chord retains the intentional empty edge action. Once RTP is no longer touched, the Regular Press provides cleanup. Following this repo's binding-array execution rule, the bottom entry removes the tap cover first and the top entry removes the entry layer last. Neither command directly applies a ramp-up layer; they clear the override so the underlying edge behavior can become available again.

The R1 connection is supported by the surrounding bindings, with an important limit on what can be inferred:

1. **R1 does not replace the active right-trackpad input.** July's regular and starred R1 modifiers have no RTP group; Neptune's corresponding RTP groups are inactive. In this path, the Base trackpad-touch binding remains available and applies `RTP: Entry Point` (July group `59`, Neptune `562`).
2. **R1 has its own right-stick edge cleanup.** With R1 held, an R1 chord makes the edge empty. With R1 no longer held, a repeating Regular Press removes both R1 modifier variants and `R1: Tap Cover` (July groups `19` / `266`; Neptune `217` / `12934`). This edge binding is unchanged between the layouts after normalization.
3. **An RTP entry override can hide that R1 edge cleanup as well as the underlying ramp-up action.** If an R1 modifier remains underneath, July's RTP cleanup can expose the R1 cleanup, which can then expose the normal ramp-up path. This explains how the symptom could look like being stuck in R1.

The confirmed blocker named by the snapshot and addressed by the changed binding is **`RTP: Entry Point`**. Its cleanup does not directly remove R1. The exact R1/RTP press-and-release order that originally left the entry layer active is not established by the saved JSON. Both layouts already have normal RTP release cleanup; this fix adds another exit when using the stick after leaving the pad, rather than proving why the ordinary release failed.

The lower ramp-up commands also changed elsewhere between these layouts. Neptune's Base edge applies `Turning Ramp Up 0` plus `Gyro Off`, with a separate gyro variant. July's Base edge applies `Gyro Off Ramp Up`, or `Turning Ramp Up 0` when a trigger chord is active. July explicitly suppresses that Base edge action while either bumper is held. Therefore, failure to enter ramp-up while still holding R1 or touching RTP can be intentional; the stale-layer case concerns failure after those conditions have ended.

This fix respects the earlier [RTP trackball-momentum exception](../2026-09-27-r1-tap-cover/FINDINGS.md). It is **stick-edge cleanup after RTP touch ends**, not the 250 ms repeating-removal workaround alongside a delayed trackpad-touch apply. There is no new repeating removal on RTP touch and no explicit interval on this edge cleanup. The unchanged 150 ms `RTP: Tap Cover` apply remains in the entry layer.

Static verification:

- Compared only active groups, resolving runtime IDs through the existing list order and normalizing chord encoding and renamed gyro layers.
- The right-stick `edge` change above is the **only semantic difference across all active groups in `RTP: Entry Point`**.
- All active groups in `RTP: Tap Cover` and `RTP: Double Tap` compare equal after normalization.
- Both regular and gyro R1 modifiers retain the same right-stick edge cleanup.
- July's pre-fix and post-fix snapshots have identical input groups. This RTP behavior was already present before the separate July layer-order correction; “post-fix” is the snapshot containing both changes, not evidence that reordering layers introduced this cleanup.

For a future runtime regression check, exercise R1 → RTP touch → release both → stick edge in both release orders, and observe the active layers. Confirm that stale RTP entry/cover state clears before ramp-up resumes, while holding RTP or R1 continues to suppress the edge action intentionally. These are proposed checks, not reported test results.
