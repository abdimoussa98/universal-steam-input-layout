# Reading guide

Where the knowledge is. `resources/` holds what stays true across releases;
`findings/` holds dated records, one folder per investigation or build.

## `resources/`

| Document | What is in it |
|---|---|
| [Layer Definition of Done](../resources/Layer%20Definition%20of%20Done.md) | The one list of the layout's rules, each with its ID, example and check |
| [Steam Behaviour Assumptions](../resources/Steam%20Behaviour%20Assumptions.md) | What the rules and tools assume Steam does, each with its status and a Deck procedure |
| [Delay Timers and Repeat Rates](../resources/Delay%20Timers%20and%20Repeat%20Rates.md) | Layer removals accelerating held repeats, inconsistent delay resets, and immediate firing after rapid add/remove transitions; why timing must not carry mission-critical behavior |
| [Layout Vocabulary](../resources/Layout%20Vocabulary.md) | Button overlays, owning layers, interaction stacks, and recovery terminology |
| [Stateful Layer Transitions](../resources/Stateful%20Layer%20Transitions.md) | The menu-plus-stick-click gesture map, Entry Points, stick guards and transition layers every stateful layer goes through. Built in 90.10 |
| [Cleanup Functions](../resources/Cleanup%20Functions.md) | The kinds of cleanup and their terms. A draft; where it differs from R127 to R132, the rules are right |
| [Steam Input JSON Structure](../resources/Steam%20Input%20JSON%20Structure.md) | JSON format, binding execution order, and the sections below |
| [Neptune Chorded Button Ids](../resources/Neptune%20Chorded%20Button%20Ids.md) | The `chord_button` ID and mask bit of each Deck button. `neptune_chord_ids.json` and `.vdf` are its probe layout |

The [inverted Chorded Press observations](../resources/Steam%20Behaviour%20Assumptions.md#inverted-chorded-press-in-action-layers)
cover owner/chorded-button differences, activation on layer load, the
Remove Layer limitation, and timing edge cases for a possible cleanup mechanism.

Sections of Steam Input JSON Structure worth knowing by name:

- [Interrupted delayed layer applies](../resources/Steam%20Input%20JSON%20Structure.md#interrupted-delayed-layer-applies) - including the repeating-removal workaround and the RTP trackball-momentum exception that held until 90.24
- [Stuck layers and why there is so much cleanup](../resources/Steam%20Input%20JSON%20Structure.md#stuck-layers-and-why-there-is-so-much-cleanup) - how the Steam button leaves layers active with no button held, and the chord-guarded cleanup pattern that recovers from it
- [Cleanup scopes and concrete examples](../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples) - overlays and inherited recovery, nine-layer Mod 2 branch cleanup, and eight-layer combined-cover cleanup that preserves the still-held side
- [Stick-edge cleanup and inherited actions](../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions) - why edge recovery is selective: LS overrides the WASD modifier, RS overrides ramp-up
- [Inheritance review for binding changes](../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes) - trace effects through upper layers, protected timers, and stale stacks; the seven Double Tap LS-edge blocks are the worked example
- [Timer blocking and the Always On crash workaround](../resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers) - why unrelated layer changes are blocked, and why timed layers must be added last and removed first

## `findings/`: comparisons and runtime observations

| Record | What it shows |
|---|---|
| [R1 and L1&R1 tap-cover findings](../findings/2026-09-27-r1-tap-cover/FINDINGS.md) | The tap covers |
| [Stuck RTP entry layer blocking right-stick ramp-up](../findings/2026-09-27-rtp-entry-ramp-up/FINDINGS.md) | The stuck entry layer |
| [Delayed-apply reset coverage audit](../findings/2026-09-28-delayed-apply-reset-audit/AUDIT.md) | Every delayed apply in both Neptune layouts, intentional exclusions, and proposed extensions within the three-command limit |
| [Delays, and what interrupts them](../findings/2026-10-06-delay-interruptions/README.md) | Every start delay of 90.36 with what can interrupt it: its own input or another, removing its layer, landing its target, covering it or restarting it, and the version each came in |
| [Guarded recovery repeat convention](../findings/2026-09-28-repeating-recovery/CHANGES.md) | The separate change enabling Hold to Repeat on every guarded recovery removal |
| [Selected LS-edge recovery](../findings/2026-09-28-left-stick-recovery/CHANGES.md) | Fourteen recovery layers, seven timed-window blocks, and the approved Transition Set cleanup depth in both layouts |
| [Complete Neptune cleanup audit](../findings/2026-09-28-neptune-cleanup-audit/AUDIT.md) and [per-layer blocking audit](../findings/2026-09-28-neptune-blocking-audit/AUDIT.md) | Every cleanup and every block, per layer |
| [Held inputs across layer changes](../findings/2026-09-29-held-input-layer-transitions/AUDIT.md) | Why adding a layer over a held input doesn't fire its layer commands (removal pass-through is unverified and backed by repeats), the ramp-up walkthrough, and which repeats and short delays exist because of it |

The build records, one per release, are listed in [building](building.md).
The deprecated tooling and its records are in [archived/](../archived/README.md).
