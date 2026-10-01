# Online evidence for runtime semantics

Researched 2026-09-30. This narrows the hardware questions in
[MODEL-LIMITS.md](MODEL-LIMITS.md); it does not change the model or certify
the existing proofs against Steam. Official documentation describes intended
behavior. Dated release notes and reproducible user reports have narrower
version/configuration scope.

## Author clarification after this research (2026-09-30)

The intended design never uses Steam's `hold_layer` API (too buggy) or
switches action sets. Layer lifetimes use explicit adds/removals. Questions
about overridden hold bindings and competing hold owners are retired from the
intended-design checklist. The reports below remain historical context only;
[current files still need five hold-command migrations per variant](../../resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).

For the discussed removal/reset behavior, the author confirms that the timer
restarts and waits 300 ms, rather than being cancelled. This observation takes
precedence over speculation from historical release notes; it does not turn
all configured delay values into 300 ms.

## Answers available online

| Question | Evidence | Consequence for this project |
|---|---|---|
| Do distinct delays have distinct deadlines? | Valve describes a delay before activation and a separate delay after release. A hands-on guide demonstrates three commands triggered at 0, 250 and 500 ms from one press. [Valve activators](https://partner.steamgames.com/doc/features/steam_controller/activators?l=english), [guide, command timing](https://steamcommunity.com/sharedfiles/filedetails/?id=2804823261). | Model inference: retain individual pending deadlines; grouping all delayed entries into one event loses intermediate states. Layer-changing commands can alter subsequent eligibility, which these basic examples do not settle. |
| Must a layer change reset every timer? | Valve's October 11, 2017 update documented state transfer for matching activators across sets, layers and mode shifts, including an unfinished long press retaining its elapsed time. It also documented preservation of matching held outputs. [Official release notes](https://store.steampowered.com/oldnews/33500). | A universal reset rule would exceed this evidence. The exact matching criteria, current delay-specific behavior and the repository's observed removal/reset cases still need reconciliation. This historical note does not override those Deck observations. |
| Does entering a layer always fire its commands on an already-held input? | The same official update describes suppression of action-set/layer changes on entry to avoid feedback. [Official release notes](https://store.steampowered.com/oldnews/33500). | This supports distinguishing entry suppression from ordinary output continuity. It is not a full specification of reactivation after removal, delayed applies, or repeat scheduling. |
| How does a normal mode shift end? | Valve specifies a temporary input-mode change while the designated button is held, followed by restoration on release. [Mode shifting](https://partner.steamgames.com/doc/features/steam_controller/mode_shifting?l=english). | Shift-only controls and the shift's active lifetime belong in the state model. Basic mode-shift behavior does not need to be rediscovered on hardware. |
| What does ring inversion mean? | Valve specifies activation outside the configured radius normally, and inside it when inverted. [Input source modes](https://partner.steamgames.com/doc/features/steam_controller/input_source_modes?l=english). | Inversion must affect eligibility. The precise JSON-field mapping, boundary equality, and reevaluation across layer changes are separate questions. |
| Are trigger thresholds meaningful state? | Valve documents analog pull and threshold-emulated digital click. A hands-on guide demonstrates the different simple-threshold, hair-trigger and hip-fire behaviors. [Valve input sources](https://partner.steamgames.com/doc/features/steam_controller/input_source?l=english), [guide, triggers](https://steamcommunity.com/sharedfiles/filedetails/?id=2804823261). | Select the actual layout's threshold style and represent the relevant analog regions; a universal edge/click Boolean rule is insufficient for every style. |

## Hold-layer releases: useful reports, incomplete specification

A January 2018 report provides a configuration and reproduction in which a
layer remains active after release. A respondent identifies replacement of
the originating hold binding in the added layer as the problem. This is
evidence for that configuration, not a current universal ownership rule.
The Valve employee reply in that thread explains opening configuration links;
it does **not** confirm the respondent's semantic explanation.
[Original report](https://steamcommunity.com/app/353370/discussions/1/1621726179575997225/).

A separate August 2024 report includes a build number, configuration and steps
for a held-layer touch-menu problem. Valve acknowledged a forthcoming fix,
and the reporter confirmed the fix the next day. This demonstrates why old
reports must retain their version context.
[Report and Valve response](https://steamcommunity.com/groups/SteamClientBeta/discussions/0/4428813423382815447/).

I did not find a complete authoritative rule covering two controls holding
the same layer, replacement of a hold binding while held, or the interaction
between explicit add/remove commands and an outstanding hold. Therefore the
model's global per-control target-removal rule remains unverified.

## Smaller remaining hardware checklist

1. With restart rather than cancellation settled for the discussed case,
   compare timer continuity for an unchanged inherited activator, an overridden
   activator and an activator exposed by removal. Include unrelated removals
   and removal of an absent layer where the current layout depends on them.
2. Test the already-held input exposed by layer removal, and inverted-threshold
   cleanup when a layer appears while its threshold condition is already true.

Record the client build with those observations. The online evidence already
supports correcting the basic timing, inversion and mode-shift omissions;
the list above is for interactions still not established by the reviewed sources.
