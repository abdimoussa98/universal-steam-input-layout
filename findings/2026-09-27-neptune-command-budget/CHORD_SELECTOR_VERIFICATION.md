# Verification of the multi-button chord fields

Date: 2026-09-27. Verified both Neptune 90.2 JSONs before commit.
**The current fields and masks are correct. No binding changes were needed.**

## Why a chord uses a field named `gyro_ratchet_button_mask`

Valve developer **aubreyh** explains that the newer chord selector reuses the
gyro button picker and migrates legacy `chord_button` values to
`gyro_ratchet_button_mask`. This is the expected serialized field for a modern
chord, despite the gyro-specific name. See the [developer's March 13 explanation](https://steamcommunity.com/groups/SteamClientBeta/discussions/0/796712326821607594/)
and the account's [Valve Employee badge](https://steamcommunity.com/profiles/76561199089249923).

These are selector settings under `inputs.edge.activators.chord[].settings`.
They select which held buttons qualify the chord; the chord's binding still
determines the action. Using the mask here does not itself enable or disable gyro.

## Direct verification in the installed Steam UI

Read-only inspection of the installed client found the chord settings schema
in `steamui/chunk~2dcc5aaf7.js`:

```js
{key:d.Rs,id:"Chord_ChordButton",visualizerType:"ActivatorButtonChordMask"}
{key:d.Cp,id:"Chord_AnyOrAll",choices:$e}
```

The same module defines:

```js
$e=[{id:"GyroRequireAny",value:0},{id:"GyroRequireAll",value:1}]
```

The gyro picker uses the same `d.Rs` and `d.Cp` setting keys. The client's
English localization labels `Chord_AnyOrAll` as **Require Any/All Chord Buttons**,
`GyroRequireAny` as **Any**, and `GyroRequireAll` as **All**. The native
`steamclient.dylib` also contains the serialized setting names
`gyro_ratchet_button_mask` and `gyro_ratchet_button_requireany_or_all`.

Thus `gyro_ratchet_button_requireany_or_all: "0"` selects **Any**; `"1"`
selects **All**. This is now independently corroborated by the Steam UI schema,
rather than relying only on the July layout's inferred behavior.

Installed source path:

`/Users/abdi/Library/Application Support/Steam/Steam.AppBundle/Steam/Contents/MacOS/steamui/chunk~2dcc5aaf7.js`

SHA-256: `5b4db9a7e27b0d92254fdfc1babfe942027e507a82560b8a64e8ccc090bd6aeb`.
The nearby localization file is `localization/steamui_english-json.js`.
The minified schema entries are at character offsets 10072628 and 10072704;
the Any/All choice list is at 10007791. These locations identify this installed
bundle only and may move after a Steam update.

## Exact button masks

The same UI bundle explicitly declares these `k_eGamepadButtonBitMask_*` indices:

| Button | Bit index | Value |
|---|---:|---:|
| Right trigger full pull | 0 | 1 |
| Left trigger full pull | 1 | 2 |
| Right bumper | 2 | 4 |
| Left bumper | 3 | 8 |
| Right trigger soft pull | 24 | 16,777,216 |
| Left trigger soft pull | 25 | 33,554,432 |

Further indices from the same table, checked 2026-09-30 (bits 32 and above
also exist, for example back grips 41/42 and macros 32–39):

| Button | Bit index | Value |
|---|---:|---:|
| North / West / East / South face | 4 / 6 / 5 / 7 | 16 / 64 / 32 / 128 |
| D-pad up / right / left / down | 8 / 9 / 10 / 11 | 256 / 512 / 1024 / 2048 |
| Back (View) / Guide / Start (Options) | 12 / 13 / 14 | 4096 / 8192 / 16384 |
| Back grip left lower / right lower | 15 / 16 | 32768 / 65536 |
| Left / right pad clicked | 17 / 18 | 131072 / 262144 |
| Left / right pad touch (cap sense) | 19 / 20 | 524288 / 1048576 |
| Left / right stick click | 22 / 26 | 4194304 / 67108864 |
| Left / right stick deflection | 30 / 31 | 1073741824 / 2147483648 |

The steering chorded delays use LS deflection (bit 30), and the RTP scroll
repeat uses right-pad touch (bit 20).

- Either bumper: `4 | 8 = 12`.
- Either trigger, soft or full pull: `1 | 2 | 16777216 | 33554432 = 50331651`.

The earlier inferred decode table assigned soft-pull bits 24/25 to left/right
instead of right/left. That table is corrected. Both consolidation masks include
both soft-pull bits, so the correction does not change either layout or the
combined-selector equivalence result.

| Current Base edge chord | Default mask | Alternative mask |
|---|---|---|
| Add Turning Ramp Up 0 while trigger role is held | `50331651` | `12` |
| Empty binding while modifier role is held | `12` | `50331651` |

All four chord objects have explicit **Any** (`"0"`), with no leftover
`chord_button` in those replacement objects. Default matches the July reference's
two masks; alternative swaps them to match its bumper/trigger role reversal.
Both full-layout command-budget checks still pass.

This verifies the serialization, option values, and selected buttons. Fresh-load
Deck tests of interruption priority and layered runtime behavior remain pending,
as listed in the [implementation record](IMPLEMENTATION.md).
