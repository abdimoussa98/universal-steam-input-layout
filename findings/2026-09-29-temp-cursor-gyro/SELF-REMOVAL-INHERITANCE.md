# Cursor self-removal: inherited bindings and timer protection

Implemented in both Neptune JSON layouts on 2026-09-29. This is a static trace
of the [self-removal change](../../plans/2026-09-29-cursor-self-removal.md),
starting from fresh preflight and actual `to-titles` copies of the working
files. It supplements the [implementation record](IMPLEMENTATION.md). It does
not establish current Steam runtime behavior or safety for every possible stale
stack. Default's modifier owners are L1/R1; alternative uses L2/R2.

## The changed lower inputs

Four regular/Gyro single-modifier parents each split twelve inputs into an
uninterruptible output chord, an uninterruptible repeating normal-cover chord,
and existing interruptible repeating family recovery. The twelve inputs are
four face buttons, four physical D-pad directions, LS/RS click, Start, and Select.
Their dual-stick cover chords also repeat. Both opposite-modifier transitions
repeat, including the two formerly missing alternative Mod 1 settings.

Each cursor overlay now replaces those twelve inputs plus the opposite modifier
with repeating, uninterruptible self-removal only. Its two stick edges have
owner guards, repeating dual-stick self-removal, and repeating self-only recovery.
The cursor inherits the parent's touch inputs; the normal cover replaces them
with cleanup-only inputs. Both overlays replace the owner's full primary input
with release-only family cleanup, retiring the parent's 300/350 ms apply/reset.
The normal cover inherits gyro settings after cursor removes itself.

An upper layer that omits these inputs can expose either the cursor's removal
or the parent's cover addition. An empty source dictionary is not a block.

## All seven Always On windows

| Window | Entry/stack trace | Protection and decision |
|---|---|---|
| Left modifier Double Tap | The owning regular/Gyro modifier release removes that owner's regular/Gyro pair and cursor before adding the window. Entry via Scroll Down follows the same cleared interaction. | Existing primary/opposite/menu replacements, edge blocks, touch self-first exits, and disabled pads remain. No demonstrated normal path leaves a single modifier/cursor underneath; no new face/D-pad/click blocks. |
| Right modifier Double Tap | Mirror of the left: release clears the right owner and cursor before the timed addition; Scroll Up entry follows that cleared interaction. | Same decision and existing protections as the left window. |
| LST Double Tap | Only LST Entry's touch release applies it. Single modifiers replace Base's LST-entry-producing touch input; cursor inherits that replacement and the normal cover replaces it with cleanup only. If LST Entry predates the modifier, the upper modifier's touch input replaces its release-to-window path. | Existing second-touch self-first exit, opposite-touch self-first cleanup, edges, menu/modifier replacements, and disabled pads remain. No additional normal modifier/cursor coexistence path found. |
| RST Double Tap | Mirror of LST: single-modifier touch replacement prevents a new RST Entry above it and supersedes an older entry's release path. | Same decision as LST; preserve second-touch and opposite-touch exit ordering. |
| **RTP Double Tap** | Base RTP touch is still inherited through a modifier/cursor. RTP Entry's quick release removes only RTP Entry, then adds this window. The modifier and optional cursor can remain below it. RTP Entry may also predate the modifier because the modifier does not replace RTP touch. | **Add ten explicit blocks:** four face inputs, four physical D-pad directions, LS click, RS click. Existing menu/owner replacements, edge blocks, touch self-first exits, and pad-selection exits remain. |
| Menu Left Double Tap | Its entry points are Menu Left Entry release and Menu Left Escape release. Single modifiers/cursor intercept Select with their own output/cancellation/cover logic, preventing Base's Menu Left Entry addition. Menu contexts replace physical modifier entry with outputs. | Existing menu self-first exit, edge/touch protection, and disabled pads/gyro remain. No demonstrated normal modifier/cursor coexistence path; no new face/D-pad/click blocks. |
| Menu Right Double Tap | Mirror of Menu Left, using Start, Menu Right Entry, and Tab. | Same decision as Menu Left. |

A missed-owner single modifier exposes its existing repeating family cleanup on
these touch/menu/opposite-modifier inputs before the newly exposed Base binding
can begin the unrelated gesture. This supports the normal-path exclusions;
it is not an assertion that an arbitrary malformed stack can never contain
another modifier below one of the six unchanged windows.

### Exact RTP additions

All ten inputs use one explicit `empty_binding` Regular Press, matching the
existing edge-block shape. They deliberately suppress inherited key/click output for this
150 ms protected window; they do not remove cursor or add a cover while Always
On remains active.

| Source/input | Default group | Alternative group |
|---|---|---|
| `button_diamond`: `button_a`, `button_b`, `button_x`, `button_y` | 13070 | 13071 |
| `dpad`: `dpad_north`, `dpad_south`, `dpad_east`, `dpad_west` | 13071 | 13072 |
| `joystick`: `click` | 1024 | 1024 |
| `right_joystick`: `click` | 1023 | 1023 |

Existing group 989 replaces menu and bumper inputs. Alternative additionally
replaces the modifier trigger edges in groups 987/988. Groups 1023/1024 retain
their edge blocks and touch releases that remove RTP Double Tap **before**
LST/RST cleanup. Group 1298 retains its right-pad north/south self-first exits
to Circular Scroll and east/west/edge self-only exits. No timer or output delay
was changed, and no new early-exit behavior was introduced.

## Other upper layers

| Context | Exposure and decision |
|---|---|
| Normal single-modifier Tap Cover | Deliberately inherits the parent's split chords and dual-edge repeats. Re-adding the already active cover maintains the hold's latch; the primary replacement and cleanup-only touch inputs prevent cursor re-entry. No Always On. |
| Temp Cursor Gyro | Explicit cancellation replaces parent inputs until self-removal; inherited touches deliberately complete cursor before helper cleanup. Local edges inherit parent geometry/movement. Parent owns broad stale-family cleanup. |
| Mod 2, both orders and Gyro variants | Replaces all twelve split inputs, owner/opposite-modifier inputs, stick touches, and both edges. Its own guards, delayed combined cover, reset, and release scopes remain. Lower single-owner repeats are not exposed on those inputs. |
| Combined modifier Tap Cover | Replaces the two owner lifecycles and inherits Mod 2's ordinary inputs. Retains the released-side cleanup, preserving the other held family. |
| Modifier Scroll Down/Up | Replaces owner/opposite/menu inputs, touches, and both edges. Face/D-pad/click inputs are omitted, but normal entry is the modifier Double Tap self-first transition after owner/cursor cleanup; no normal single-modifier repeat stack was found below scroll. |
| Menu Entry points and menu key overlays | Partial input replacement is intentional. Their normal entry is intercepted while a modifier/cursor is active, and menu contexts replace modifier entry with outputs. Do not describe omitted face/D-pad inputs as blocks. |
| Menu Fn layers | Explicitly replace the twelve ordinary inputs, both edges/touches, and modifier entry controls. Fn stick-click mode-shift targets contain keys and explicit edge/click/touch empties, with no layer commands. |
| Transition Sets 0/1 | Explicit owner/menu replacements and stick-click/edge/touch protection; face/D-pad can inherit from their menu/Fn stack. Normal menu entry excludes single-modifier/cursor coexistence. Preserve existing transition-family recovery and disabled pads/gyro. |
| RTP Entry, Tap Cover, and Circular Scroll | Can coexist with modifier/cursor and deliberately inherit ordinary cancellation inputs. They have no Always On. Their local touch/pad behavior remains; cursor removal or cover addition is permitted here. RTP Entry's eventual quick-release path is why RTP Double Tap needs the ten blocks. |

## Limits and manual checks

- RTP Double Tap changes the right pad from Base's `absolute_mouse` group 562
  to `dpad` group 1298. It still relies on that source-mode replacement to stop
  Base's omitted RTP `click` hold-layer and `touch` entry-layer actions. This is
  the pre-existing [blocking-audit caveat](../2026-09-28-neptune-blocking-audit/AUDIT.md#inherited-route-review-and-remaining-uncertainty),
  not a newly demonstrated leak or a runtime guarantee from the ten blocks.
- Base switch group 10 references the inactive-marked trackpad-touch mode-shift
  targets 1039/1043. Those targets contain only keys, so they introduce no layer
  mutation into the timed-window trace. Their actual activation/precedence under
  modifiers and blocks remains unverified; retain the separate mode-shift
  follow-up rather than reporting a confirmed bypass.
- Under the author's timer rule, removing cursor while RTP Entry's 150 ms apply
  is pending could restart that unrelated delay. Check interrupted holds and
  quick releases on Deck. Do not add a repeating reset to the RTP touch path;
  its trackball-momentum exclusion remains intentional.
- Test affected inputs already held across window entry as well as newly
  pressed within it. Static replacement does not prove cancellation of an
  activator that was already pending. Confirm key/mouse delivery and release
  when cursor self-removal exposes both uninterruptible parent chords.

See [manual testing](../../archived/manual-testing.md) for the fresh-load checks. No VDF
export or Steam client runtime test is represented by this audit.
