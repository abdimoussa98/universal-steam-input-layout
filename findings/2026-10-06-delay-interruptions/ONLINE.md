# What is written about start delays and layers

**Status:** a web search on 2026-10-06, asked for by the author after the
[audit](README.md): "look online for how steam input delays and layer
interactions and any issues that could be caused by these". Nothing in the
layouts, the rules or the assumptions table changed. The checks at the end are
proposals.

Three kinds of source, kept apart:

- **Valve**: the installed Steam client's own setting descriptions (read from
  `steamui_english-json.js` on this Mac), the Steamworks pages, and the client
  update of 2017-10-11 that introduced layers.
- **Reports**: forum and GitHub posts by users. Each is one person's setup on
  one client version. Valve answered two of them.
- **My reading**: marked as such.

## What Valve says

| Subject | Valve's words | Where |
|---|---|---|
| Fire Start Delay | "The activator will wait for this period of time after the button has been pressed before activating. This delay will offset the entire period the button is held, so if no end delay is set, the total period of time the button is held will be the same, just delayed." | Client, `ControllerBinding_FullPress_StartDelay_Description`; the Steamworks Activators page has the first sentence |
| Interruptible | "Interruptable activators can be paused or stopped by other activators. For example, a Long Press activator can interrupt a Full Press activator so the Full Press only fires if the Long Press doesn't." On: "Long Press, Double Press, etc. will cause it to wait for their conditions to be met". Off: "ignore other activators and always activate/deactivate as if it were alone." | Client. The same text is on Regular Press and on Release Press |
| Chorded Press | "Button Chord Activator activates when the both the button owning the activator and the chorded button are pressed." Nothing about it stopping a Regular Press | Client |
| Layers, order | "Activating an action set layer that is already active will have no effect", and "will not change its order in the stack". "Deactivating an action set layer, and then activating it, will set it to the top of the stack." | Steamworks, Action Set Layers |
| Layers, re-applying | "Just because you can re-apply action set layers every frame doesn't mean you should, especially if you're using more than one layer." No reason given | Steamworks, Action Set Layers |
| A held output across a layer change | "if the same action/output is bound across the boundaries of these sets, rather than being un-pressed and immediately pressed on this transition, it will continue to be held if bound to a pressed button in both sets." | Client update, 2017-10-11 |
| An activator's state across a layer change | "Activators which have matching Activators across action set/layer/mode shift boundaries will also carry over state, so if the same activator exists across these boundaries, a 'long press' which has been pressed but not yet activated will maintain timing information." | Client update, 2017-10-11 |
| A layer command on a held input | "Action set/layer activation binding now fires on the activation, rather than deactivation of the input it's attached to." "Prevention of feedback loops is now handled automatically, buttons which share action set changes on the same input will not fire when entering the new set/layer." | Client update, 2017-10-11 |
| Interruption is per input | "Fixed activators from different inputs being able to interrupt each other" | Client update, 2017-10-11 |

Valve says nothing, anywhere I found, about what happens to a start delay that
is still running when its layer is removed or covered, about a removal
restarting a delay, or about a chord interrupting a Regular Press.

## What users report

| When | Report | Valve |
|---|---|---|
| 2018-01 | A Hold Layer whose button is rebound inside the layer never comes off | SDalton: the Hold binding "is no longer present because it's being rebound" |
| 2019-05 | Spamming a Hold Layer button leaves the layer on: "the release is not always captured". Still there in the October 2019 beta | None |
| 2020-10 | A chord bypasses a Regular Press on the same button, but not a Release Press (cybin). In the same thread: layers get "finicky" when added and removed quickly | None |
| 2021-05 | Leaving a layer while another digital button is held sends a release of that button, and clears toggles. Fixed for that user with Fire End Delay | None |
| 2021-06 | After a client update, chorded presses on face buttons and the D-pad were ignored altogether | austinp_valve fixed it in the next day's beta |
| 2021-08 | Pressing a Hold Layer button cancels another input that is held, until the layer is let go. A mode shift doesn't (GitHub 7983, open) | None |
| 2022-03 | Hold Layer on a trackpad click never comes off; the same on R1 works (Deck) | None |
| 2022-05 | A Hold Layer inside layer A, when another layer removes A: the hold "cannot be released", and an Always On turbo bind fires with nothing held | None |
| 2022-09 | Triggers in a layer forget what they inherit after a client restart or a layout load (GitHub 8786, open) | None |
| 2022-10 | A Hold Layer "sometimes fail[s] to enter". Fixed for that user with an explicit enter command on a Regular Press with turbo, and the exit on the Release | None |
| 2024-07, 08 | ugafan: "The command to hold the layer should not have a fire start delay." In another thread a delay of about 200 ms on a Change Action Set command, as its own entry and not a sub-command, did work | None |
| 2024-10 | "If an action layer shift is input, regardless of Fire Start Delay setting, the action layer will fire automatically" (Wyppo, no replies) | None |
| 2024-11 | A layout with a custom layer loads with the layer "stuck on by default" until the layout is switched away and back (Deadlock forum) | None |
| 2025-02 | Each set or layer change re-sends a press of a key that is held, when the two sides bind it differently (Deck) | None |
| 2026-09 | Layer references going stale after copying, exporting or restarting (GitHub 13624, open) | None |

Fixed by Valve, from release notes: a crash on a trigger set to Disabled in a
layer (2022-09). The beta of 2026-10-05 has no change to layers or activators.

## What it means for the layouts

1. **A start delay is a shift, not a hold threshold** (Valve). By that text a
   50 ms tap with a 200 ms delay still fires, 200 ms late. Valve's threshold
   is Long Press, which R108 bans. The layouts get "tap does nothing" another
   way: the own input's Release removes the host. That holds for 35 of the 39
   delays in the audit.
   - My reading: for the 4 where the host stays (`RTP: Mouse Buttons`' two
     ring scrolls and the two Steering stick modifiers), Valve's text predicts
     the delayed action still fires after an early let-go. The simulator drops
     it. One of the two is wrong.
   - My reading: what Steam does with a shifted press whose layer has gone is
     the undocumented part, and A12 is the author's observation of it.
2. **State carries over to a matching activator** (Valve). A covering layer
   whose activator on that input matches may keep the timing instead of
   starting again. A16 says the clock starts when the layer is added, and is
   unverified. The stick guards are the case: their Select and Start carry the
   same 200 ms chord as the Entry Point they land over. Valve doesn't say what
   "matching" means.
3. **A5 has a Valve sentence behind it.** "Buttons which share action set
   changes on the same input will not fire when entering". My reading: as
   written it covers an input that has a layer command on both sides. A layer
   command landing on an input whose old binding was a key isn't clearly
   covered. The cleanups repeat, so R113 doesn't depend on it.
4. **A10 and A11 have a report behind them.** The 2025 report shows a held
   key re-sent in both directions of a change. The 2021 report shows a release
   on leaving a layer. A37 has Valve's sentence, for the same output bound on
   both sides.
5. **The guard rests on unwritten behaviour.** That an active chord stops an
   interruptible Regular Press (A27) is in no Valve text; one user states it,
   and adds that a Release is not stopped. All 367 held-back cleanups in the
   audit depend on it. Chords broke once with a client update, in June 2021.
6. **The repeating adds are a known remedy.** One user fixed a layer that
   failed to enter with turbo on the entry command, which is what R113 and
   R114 do. Valve's
   one caution is about re-applying layers every frame through the API.
7. **Hold Layer is the common factor in the stuck-layer reports.** That
   supports R101. The trackpad-click report is the four pad click layers' own
   case (A42); their inverted Soft Press is the fallback.
8. **A first load can be wrong by itself.** Three reports (2022-09, 2024-11,
   2026-09) describe layers or triggers in a bad state right after a load or a
   restart. My reading: the "first load, Fn never came" symptom behind A52 may
   not be about stored order at all.

## Checks this suggests

Not added to the assumptions table or the to-do list.

| Check | How | What it settles |
|---|---|---|
| Is the delay a shift? | Test layout: one button, Regular Press, a key, Fire Start Delay 500 ms. Tap it | The key typed half a second later: Valve's text holds, and the simulator's "let go drops the delay" is wrong where the host stays |
| Does a tap leave a press behind? | Tap LB. Is the cursor's pulse felt 200 ms later, or the cursor on with nothing held? | Whether a shifted press fires in a layer that is gone |
| Does a matching activator keep the timing? | Hold Select 150 ms, push the left stick out, let go of Select 100 ms later | Escape typed: the guard's delay started again (A16); the simulator gives this. No Escape: the timing carried over (Valve, 2017) |

## Not found, or not read

- No source on a delay restarting after a removal (A13, A14), on a default
  Hold to Repeat rate (A35), or on the order of two activators due at once
  (A32).
- A Reddit thread from February 2023, "Something broke: interruptible actions
  don't trigger", could not be opened.

## Sources

- Valve: [Activators](https://partner.steamgames.com/doc/features/steam_controller/activators),
  [Action Set Layers](https://partner.steamgames.com/doc/features/steam_controller/action_set_layers),
  [client update of 2017-10-11](https://store.steampowered.com/oldnews/33500),
  [Deck client beta of 2022-09-27](https://steamdeckhq.com/news/steam-deck-client-beta-update-input-improvements/),
  [client beta of 2026-10-05](https://www.gamingonlinux.com/2026/10/steam-client-beta-october-5th-brings-fixes-for-older-cpus-and-more-steam-input-adjustments/)
- Community reference: [Steam Input Wiki, chapter 4](https://github.com/SteamInputWiki/SteamInputWiki/blob/main/chapter-4/changing_things_up.md),
  [Steam Deck Controller Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2804823261)
- Reports, in the table's order:
  [2018-01](https://steamcommunity.com/app/353370/discussions/1/1621726179575997225/),
  [2019-05](https://steamcommunity.com/app/353370/discussions/1/1652169858530682256/),
  [2020-10](https://steamcommunity.com/app/353370/discussions/0/3014556944200392295/),
  [2021-05](https://steamcommunity.com/app/353370/discussions/0/3117032860247421217/),
  [2021-06](https://steamcommunity.com/app/353370/discussions/1/3118160027748150164/),
  [2021-08](https://github.com/ValveSoftware/steam-for-linux/issues/7983),
  [2022-03](https://steamcommunity.com/app/1675200/discussions/1/5764050278033878598/),
  [2022-05](https://steamcommunity.com/app/353370/discussions/1/4417479689929271737/),
  [2022-09](https://github.com/ValveSoftware/steam-for-linux/issues/8786),
  [2022-10](https://steamcommunity.com/app/353370/discussions/0/3468361193665969286/),
  [2024-07](https://steamcommunity.com/app/353370/discussions/0/4511002532254606954),
  [2024-08](https://steamcommunity.com/app/1675200/discussions/0/4425436537576825579),
  [2024-10](https://steamcommunity.com/groups/bigpicture/discussions/1/4694531508754516495/),
  [2024-11](https://forums.playdeadlock.com/threads/steam-input-breaks-after-launching-into-game-with-a-controller-layout-that-uses-a-custom-action-set-layer-21-nov-2024-patch.47913/),
  [2025-02](https://steamcommunity.com/app/1675200/discussions/1/599644215836716771/),
  [2026-09](https://github.com/ValveSoftware/steam-for-linux/issues/13624)

The forum pages were read through a summarising fetch. The quotes from the
client were read directly; the others are as the fetch returned them.
