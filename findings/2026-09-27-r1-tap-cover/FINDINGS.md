# R1 and L1&R1 tap-cover delayed apply: comparison and interruption research

Date: 2026-09-27. Evidence includes static comparison, public-source research, and the layout author's runtime observations supplied during review. No independent Steam runtime reproduction was performed in this investigation, and neither source layout was edited.

The reusable behavior and RTP exception are also documented in [Steam Input JSON Structure: Interrupted Delayed Layer Applies](../../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies). This finding retains the detailed comparison and evidence.

July adds **250 ms repeating removal of `L1&R1: Tap Cover`** in `*L1!R1: Modifier 2` and `*R1!L1: Modifier 2`. These bindings are absent from Neptune's corresponding `(Gyro)` layers. **The layout author reports that repeated removal resets the Fire Start Delay, allowing the delayed apply to trigger again after an earlier apply was interrupted.** This explains the workaround's purpose and observed effect; the JSON establishes where and how it is configured.

| July layer | Input carrying the removal | Active group | Added activator |
|---|---|---|---|
| `*L1!R1: Modifier 2` | R1 / `right_bumper` | `360` | Regular Press: remove `L1&R1: Tap Cover`; Hold to Repeat On; Repeat Rate 250 ms; Interruptable Off |
| `*R1!L1: Modifier 2` | L1 / `left_bumper` | `361` | Same |

In the July source, the first removal is at lines 17153–17161, and the mirrored removal is at lines 17298–17306. Their settings are exactly `hold_repeats: "1"`, `repeat_rate: "250"`, `interruptable: "0"`.

Each sits alongside a chord on the same input that applies `L1&R1: Tap Cover` with `delay_start: "200"`. The R1 input's chord requires L1 (`gyro_ratchet_button_mask: "8"`); the L1 input's chord requires R1 (`"4"`). The repeating removal itself is a Regular Press, with no chord requirement and no explicit start delay. Interruptable Off prevents the chord from suppressing that Regular Press through ordinary activator interruption rules; actual scheduling across layer replacement still requires runtime observation.

Neptune groups `12950` and `12961` contain the release cleanup and 200 ms apply chord, but **no `Full_Press` activator on these respective bumper inputs**. The regular, unstarred two-bumper layers in July also lack this added removal. Thus this particular change was made only in the starred/gyro variants. The configured removal interval is 250 ms, 50 ms longer than the apply delay. The author identifies the delay reset as the reason the workaround fixes interrupted applies; the choice of that exact interval has not been separately explained. Do not infer from the settings alone that a repeating command keeps executing after another layer overrides its input.

**RTP trackpad exception:** the author deliberately did **not** apply this recurring delayed-apply reset workaround to the RTP trackpad layers, recalling that repeated layer removal interfered with **trackball momentum**. Preserve that exception when extending the bumper fix: restarting start delays is useful for recovering the interrupted apply, but recurring layer removal was unsuitable for the trackpad's momentum behavior.

The files support the distinction: `RTP: Entry Point` applies `RTP: Tap Cover` from its right-trackpad `touch.chord` with a **150 ms** start delay (July group `176`; Neptune group `1032`), without the corresponding periodic tap-cover-removal activator on that touch input. This does not mean all repeated removals are absent from RTP-related layers. Separate cleanup bindings exist, such as joystick-touch removals in `RTP: Mouse Buttons` / `RTP: Circular Scroll`, and July's right-stick-edge cleanup of `RTP: Entry Point` and `RTP: Tap Cover`. Those are distinct from adding the recurring reset workaround to the delayed trackpad-touch apply.

The separate [stuck RTP entry / ramp-up finding](../2026-09-27-rtp-entry-ramp-up/FINDINGS.md) traces that stick-edge cleanup and how an RTP override could also hide R1 cleanup. It runs when using the stick without RTP touch, preserving the trackpad exception described here.

For the separate single-bumper path, the R1 button chord that applies `R1: Tap Cover` is semantically unchanged between the two requested layouts. Both use **R1 chorded with R1 itself**, a **300 ms Fire Start Delay**, and **Interruptable Off**. Neither enables Hold to Repeat on this delayed apply. There is no new reset or retry binding on that specific command in the July snapshot.

Sources compared:

- [July post-fix snapshot](../2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json), revision 14001, `controller_triton`.
- [Neptune layout](../../neptune/single-set-default_hold-gyro_latest.json), revision 12896, `controller_neptune`.

Used the project [steam-layout-prep](../../.claude/skills/steam-layout-prep/SKILL.md) and [steam-binding-order](../../.claude/skills/steam-binding-order/SKILL.md) skills. Converted Neptune to readable titles in a temporary file with `convert_runtime_ids.py to-titles --output`, preserving its existing list order. Resolved presets to their active switch groups rather than comparing arbitrary text matches.

| Setting / location | Neptune | July post-fix |
|---|---|---|
| Layer | `R1: Modifier 1` | `R1: Modifier 1` |
| Active switch group | `160` | `313` |
| Input / activator | `right_bumper.activators.chord` | Same |
| Target | `add_layer 24` → `Base::R1: Tap Cover` | `add_layer {{Base::R1: Tap Cover}}` |
| Chord condition | `chord_button: "2"` = R1 | `gyro_ratchet_button_mask: "4"` = R1 |
| Fire Start Delay | `delay_start: "300"` | Same |
| Interruptable | `"0"` | Same |
| Hold to Repeat / Repeat Rate | Neither explicitly set here | Neither explicitly set here |

The chord encodings differ by controller, not by the required button. See the paired mappings in the [existing audit appendix](../2026-09-27-exploratory-layout-audit/AUDIT.md#appendix-chord-and-mask-decoding).

Exact source locations:

- Neptune regular R1 chord: lines 16538–16545; July: lines 14318–14325.
- Neptune gyro variant, `(Gyro) R1: Modifier 1`, group `12931`: lines 19495–19502; July `*R1: Modifier 1`, group `359`: lines 16980–16987.
- Neptune tap-cover R1 release, group `781`: lines 17682–17697; July group `332`: lines 15295–15310.

After translating IDs/chord encodings and mapping `(Gyro) R1:` to `*R1:`, the **entire R1 input object** compares equal in all three places: regular modifier, gyro modifier, and tap cover.

The intended flow is apparent from the bindings:

1. Base/Gyro R1 applies the corresponding R1 modifier.
2. Inside the modifier, the delayed R1 chord applies the tap cover.
3. Without the cover, R1 release removes both modifier variants and enters `R1: Double Tap`; that layer contains the scroll-up/tap handling.
4. With the cover, R1 release instead removes the cover and both modifier variants, omitting the double-tap/scroll path.

The cover therefore suppresses the tap behavior after a hold or another modifier action has applied it. The self-chord explicitly requires R1 to be held. This single-bumper binding is separate from the author's identified repeating-removal workaround in the two-bumper layers.

Another nearby change is in the **Base and Gyro entry chords**, which apply the modifier rather than the tap cover. Both already had `hold_repeats: "1"` in Neptune. July adds an explicit `repeat_rate: "50"`:

- Base: Neptune lines 16029–16042; July lines 14044–14058.
- Gyro: Neptune lines 19916–19929; July lines 17366–17380.

After normalization, this added repeat rate is the only difference in those two R1 input objects. Neptune's omitted repeat rate was not interpreted as a known numeric default. Repeating modifier entry could help recover entry after another layer disappears; that is an inference about intent, not proof of a fix for the separate delayed cover command.

Also, the entire `controller_mappings.group` array is identical between the July **pre-fix** and **post-fix** snapshots. “Post-fix” refers to the [layer ordering correction](../2026-07-11-layer-order-swap/FINDINGS.md), not an R1 timing fix. The current [todos.md](../../todos.md) still lists both the start-delay interruption issue and tap covers failing to re-add at lines 67–68.

Public research supports distinguishing ordinary activator interruption from a layer replacing the binding that owns a pending delay:

- Valve describes Fire Start Delay as delaying activation, and Interruptable as governing interactions with other activators. Its documentation does not promise that turning Interruptable off preserves or resets a delayed command across layer replacement. A chord is a regular-style activation with an additional held-button requirement. [Valve: Activators](https://partner.steamgames.com/doc/features/steam_controller/activators)
- Valve states that applying an already-active layer has no effect and does not move it to the top of the stack. Repeatedly applying the modifier is therefore not evidence that its delayed cover activator is being reset. [Valve: Action Set Layers](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers)
- A firsthand December 5, 2024 report describes a related failure: interrupting a Double Press sequence with a layer change causes the next attempt to require three presses. The author reproduced it on Deck and Windows. This resembles failure to reset activator state, but concerns Double Press, not this delayed chord, and does not establish an identical root cause. [Steam Client Beta report](https://steamcommunity.com/groups/SteamClientBeta/discussions/0/4630359652384738093/)
- A firsthand October 2022 thread reports intermittent layer-entry failures. The author's eventual workaround combined switching action sets, explicit entry/exit commands, and turbo on entry. It is relevant to the repeat-entry pattern, but does not verify a fix for delayed tap-cover application. [Action Layer sometimes fails to enter](https://steamcommunity.com/app/353370/discussions/0/3468361193665969286/)

No exact public reproduction or Valve-confirmed fix for “interrupt a delayed apply, then the next press fails” was found in this research. The layout author's runtime observation supplies the explanation used here: repeated removal resets the start delay and fixes the interrupted-apply behavior. The underlying Steam implementation and behavior on current client versions were not independently verified. The trackball-momentum conflict is likewise recorded as the author's observed reason for excluding RTP from this workaround.

A focused runtime check for independent reproduction or future regression testing would distinguish the cases:

1. In a disposable minimal layout, reproduce Base → R1 modifier → delayed tap cover, retaining release cleanup but omitting unrelated double-tap and gyro logic. Use a layer notification to observe cover entry.
2. Establish that a normal R1 hold applies the cover, and separately test releasing R1 before 300 ms.
3. Add a test layer that overrides R1 with an empty binding. Apply it during the 300 ms window, release R1 while it is active, remove it, and then press/hold R1 again. Test removing the modifier during the delay as a separate case.
4. Record whether the next press enters the modifier but misses the cover. This separates modifier-entry failure from delayed-cover failure.
5. As a diagnostic variant only, replace the delayed chord with a 300 ms Long Press and zero Fire Start Delay. This tests a different timing mechanism; it is not a verified workaround and its behavior on layer entry must also be checked.

Pre-flight results were recorded without changing either source: July has aligned layer/preset order but duplicate unrelated `DEPRECATED` titles; Neptune has unsorted layer keys, matching preset blocks, sequential preset IDs, and unique titles. No title-to-ID conversion, structural normalization, or export was attempted.
