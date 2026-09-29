# Neptune 90.2 blocking and Always On isolation audit

Date: 2026-09-28. Both latest Neptune layouts were audited in title form. No JSON
or VDF was edited. This supplements the [cleanup audit](../2026-09-28-neptune-cleanup-audit/AUDIT.md)
with the author's explanation of the blocking design and historical crash.
Recorded hashes, counts, and source-line references describe the original audit
inputs. Subsequent changes include the [repeat convention](../2026-09-28-repeating-recovery/CHANGES.md)
and [LS-edge recovery](../2026-09-28-left-stick-recovery/CHANGES.md), including
seven new explicit LS-edge blocks in the Double Tap windows. The historical
inventory below predates those changes; the Always On ordered boundaries remain
unchanged and are checked again by the recovery regression tests.

**Blocking protects layer lifetimes as well as input behavior.** The layouts
prevent unrelated layer operations from resetting delayed applies or disturbing
short-lived Always On layers. Their precise subcommand order is part of the
workaround: finish cleanup before entering a timed layer; leave it before
executing any other layer changes.

**Both variants pass the directly configured Always On ordering checks:**
seven timed layers, 13 active entries that add the timed layer last, and 30
directly owned layer-changing entries that remove it first. No violation was
found in those arrays. This is not a runtime claim about every possible stack
or whether the historical crash still occurs in the current Steam client.

## Evidence and scope

- [Default: blocking in every layer](default-layers.md) and
  [alternative: blocking in every layer](alternative-layers.md): all 53 layers
  plus Base, active source modes, every active activator, conditions, payloads,
  source locations, and conditional mode-shift definitions.
- [Activator inventory](activator-inventory.csv): **2,004 entries**, including
  active, inactive, conditional mode-shift, and unreferenced groups. Complete
  bindings, sibling activators, settings, ownership, and JSON pointers.
- [Source inventory](source-inventory.csv): **1,061 groups**, including source
  settings and groups with no explicit input activators. This captures disabled
  trackpads/gyro that an empty-binding search alone would miss.
- [Summary and execution-order evidence](blocking-summary.json): hashes,
  per-layer counts, every Always On entry/exit in actual execution order, and
  the structural coverage of Base's layer-changing routes.
- [Builder](build_inventory.py): regenerates these files from verified
  `default.json` and `alternative.json` title copies. It reuses the cleanup
  audit's source-pointer and group-ownership extractor.

| Count | Default | Alternative |
|---|---:|---:|
| Pure empty Regular Press entries in active groups | 78 | 66 |
| Pure empty chord entries in active groups | 132 | 132 |
| Pure empty release entries in active groups | 4 | 4 |
| **Total pure empty entries in active groups** | **214** | **202** |
| Mixed entries containing empty subcommands and real actions | 12 | 12 |
| Entries containing empties in inactive groups | 14 | 14 |
| Entries containing empties in conditional mode-shift groups | 12 | 12 |
| Entries containing empties in unreferenced groups | 2 | 2 |
| Active disabled source groups | 32 | 32 |
| Disabled sources: gyro / left pad / right pad | 15 / 9 / 8 | 15 / 9 / 8 |
| Chord-protected Regular Press cleanup entries | 185 | 185 |
| Always On command entries / owning layers | 11 / 7 | 11 / 7 |

These are different measurements, not disjoint categories to sum. A chord can
both be an empty binding and protect a sibling cleanup. The 12 mixed entries
still execute real actions; they are not twelve wholly blocked inputs.
All inputs remain within the three-GUI-command-entry limit.

## The two timing problems and the solution

### Fire Start Delay resets

The author reports that removals can reset Fire Start Delay timers. The existing
repeating-removal workaround deliberately uses that effect to restart an
interrupted apply. The same effect is undesirable when an unrelated cleanup
disturbs a timer that should complete. Additions can also replace the input
that owns a pending action.

Therefore, the layouts block unrelated layer operations during protected
interactions. This does not establish that every removal resets every timer
globally, or explain Steam's internal implementation. Preserve the observed
behavior and the targeted exception: four Mod 2 resets at 250 ms, the ramp
reset at 300 ms, and the two menu-entry resets at 350 ms are intentional.
RTP's 150 ms touch-to-cover apply retains the separate momentum exception.

### Historical Always On crash

The author reports a severe historical crash when other layer additions or
removals occurred while a layer containing Always On actions remained active.
The solution was to isolate those layers and carefully order their boundaries.
The original client build, date, and exact crash mechanism were not supplied.

**Current fix status: unknown.** Public-source searches did not establish a
Valve fix for this exact behavior, and no crash reproduction was run. Generic
Steam Input crash fixes or unrelated Always On changes would not establish that
this case is fixed. The observation is attributed to the author, and the
workaround remains an explicit layout constraint.

The contract is:

1. Before entry, complete other layer operations, then add the Always On layer.
2. While that layer remains active, suppress unrelated add/remove/hold routes.
3. Its expiry removes only itself.
4. A permitted early exit removes that Always On layer **first**, then performs
   other removals or additions. It need not wait for the timeout to expire.

This isolates **layer changes**, not all gameplay output. The Double Tap layers
retain permitted key, wheel, mouse, and inherited movement behavior. Four of
the seven windows also use Always On to send their tap output after 50 ms.

## Exact execution order already implemented

The [binding-order skill](../../.claude/skills/steam-binding-order/SKILL.md)
defines subcommand execution bottom to top. Ordering below is **execution
order**, not JSON storage order.

| Boundary | Existing example | Execution sequence |
|---|---|---|
| Enter a timed window | L1 Modifier 0 release | Remove Gyro L1 modifier → remove regular L1 modifier → add L1 Double Tap |
| Expire | L1 Double Tap Always On after 150 ms | Remove L1 Double Tap only |
| Complete a second press | L1 Double Tap on L1 | Remove L1 Double Tap → add L1 Scroll Down |
| Cross-gesture cancellation | L1 Double Tap on RS touch release | Remove L1 Double Tap → remove RST Entry Point → remove RST Tap Cover → remove RST Temporary Gyro |
| Stick second touch | RST Double Tap on RS touch | Remove RST Double Tap → add RST Entry Point → add RST Temporary Gyro |
| Trackpad selection | RTP Double Tap north/south | Remove RTP Double Tap → add RTP Circular Scroll |

The current exit exception is thus **self first**, not self last. A generic
cleanup-list sort or a rule saying “always remove the owner after its children”
would break the intended protection. Independent activators on the same input
are not ordered by this array rule; keep the boundary operations together in
the existing command entry.

The seven windows are:

| Timed layer, default / alternative | Expiry | Additional Always On output | Incoming entries | Layer-changing entries owned here |
|---|---:|---|---:|---:|
| L1 / L2: Double Tap | 150 ms | Scroll down after 50 ms | 3 | 4 |
| R1 / R2: Double Tap | 150 ms | Scroll up after 50 ms | 3 | 4 |
| LST: Double Tap | 200 ms | None | 1 | 3 |
| RST: Double Tap | 200 ms | None | 1 | 3 |
| RTP: Double Tap | 150 ms | None | 1 | 8 |
| Menu Left: Double Tap | 150 ms | Escape after 50 ms | 2 | 4 |
| Menu Right: Double Tap | 150 ms | Tab after 50 ms | 2 | 4 |
| **Total** | | | **13** | **30** |

The 30 include seven timeout removals and 23 early exits/cancellations. Every
one has self-removal as the first executing subcommand. No directly owned
command changes another layer while retaining its timed owner. The single
dormant RTP Double Tap transition in group 1025 also removes self first; it is
not an active path. No other dormant timed-window entry was found.

**Double Tap Covers are not timed windows:** they contain no Always On input.
They suppress the tap/reopen behavior on release and have a different lifetime.

## Types of blocking in use

| Type | What it protects | Examples |
|---|---|---|
| Explicit press suppression | Prevents the covered input's ordinary layer-changing action | Double Tap/menu/transition RS edge; menu buttons during unrelated windows; selected trigger full-pull slots |
| Conditional empty chord | Holds a block only while an owner or selector is held | Modifier RS edge/touch; RTP-entry edge while RTP is touched; Base ramp selection while a modifier is held |
| Real-output chord protecting cleanup | Keeps stale-state cleanup from firing during a valid hold | Modifier keys and Fn keys versus their sibling Regular Press removal |
| Alternative chord branch suppression | Prevents the wrong held modifier branch from acting | Mod 2 has real output for its first-owner chord and an empty chord for the other side; both suppress fallback cleanup |
| Click/deflection suppression | Avoids another action while a click or menu interaction owns the stick | Fn stick directions have empty stick-click chords; conditional Fn mode shifts have their own empty click/edge/touch definitions |
| Disabled source | Removes an entire input source's operation in that layer | Pads in Double Tap/Transition layers; gyro in menu layers and Gyro Off Ramp Up |
| Output replacement | Allows useful output while withholding layer entry | Scroll output in place of a modifier-adding bumper/trigger during Double Tap; alternative bumpers retain mouse buttons |
| Release interception | Suppresses tap, window reopening, or underlying release behavior | Tap Covers; Double Tap Covers; Transition Sets' explicit empty menu releases; Enter/Backspace key-layer releases |
| Gyro output gating | Restricts gyro output through source settings, separately from layer-management blocking | Base's All selector; Gyro and its modifier variants' Any selectors; LST/RST Temporary Gyro touch selectors |
| Ordered self-exit | Makes a layer transition permissible by ending the protected lifetime first | All seven Double Tap layers |

An active group whose mode is `disabled` is not the same as a group marked
`inactive` in preset bindings. An empty input dictionary does not prove an
intentional block. A mixed array such as `remove_layer ...; empty_binding` still
removes layers. The catalogs and inventories preserve these distinctions.

## Blocking strategy in every layer family

This table covers all 53 layers plus Base; the catalogs split each into its own
section with exact input locations. Default L1/R1 modifier-family names map to
alternative L2/R2. “Empties” counts pure empty activators per layer, D/A.

| Layer(s) | Empties D/A | Implemented strategy |
|---|---:|---|
| Base | 2/2 | Explicit LS edge blank; modifier-held RS edge chord blocks the ordinary ramp route. Gyro uses its separate All gate. |
| Turning Ramp Up 0 and 1 | 0/2 each | Modifier exit consumes the event with removal + empty output; alternative additionally blocks soft pull while full pull exits. These mixed removals are not pure blocks. |
| Single modifiers, regular and Gyro (4) | 5/3 each | Owner-held RS edge/touch and LS touch empties protect the gesture and suppress fallback. Real-output chords protect other recovery inputs. Default full-pull slots are blanked. |
| Mod 2, both orders, regular and Gyro (4) | 16/16 each | Dual-owner guard branches, wrong-side empty chord on face/D-pad/menu/click inputs, guarded RS edge, full-pull suppression. The deliberate cover-reset binding stays uninterruptible. |
| Gyro | 0/0 | Changes gyro gating and modifier entry selection; no explicit empty input entries. |
| LST/RST Temporary Gyro (2) | 0/0 each | Own touch-release lifecycle replacement and gyro selector. Does not broadly silence inputs. |
| Gyro Off Ramp Up | 0/0 | Active gyro-disabled source. Firing input restores gyro by removing this layer; RS thresholds control its lifetime. |
| LTP Arrow Keys; RTP Mouse Buttons; RTP Circular Scroll (3) | 2/2 each | Pad-touch chords suppress cleanup on either stick's touch while the pad owns the interaction. |
| Modifier Scroll Down/Up (2) | 5/3 each | Owner-held edge/touch blocks; delayed cover and release replacement; ordinary scrolling remains allowed. |
| Escape, Tab, Backspace, Enter without Menu prefix (4) | 2/2 each | LTP-touch guarded stick-touch cleanup; key output remains active. |
| Menu Left Escape / Menu Right Tab (2) | 4/4 each | RS edge, other menu button, and full-pull slots blocked; gyro disabled. Key output and delayed cover remain allowed. |
| Menu Left Backspace / Menu Right Enter (2) | 0/0 each | Dedicated key output/release replaces that button's lower lifecycle; gyro disabled. |
| Menu Left/Right Fn (2) | 14/14 each | Chords protect family cleanup; empty menu-held edge and stick-click directional chords; firing-role suppression; gyro disabled. Conditional mode shifts add further blocks. One mixed helper-entry chord per layer is not a pure block. |
| LST/RST Entry Point (2) | 0/0 each | Touch lifecycle is replaced with delayed-cover and release-to-window behavior. Empty source dictionaries are not counted as blocks. |
| RTP Entry Point | 1/1 | RTP-touch chord intentionally blocks RS edge; without RTP touch, the separate cleanup can clear the entry/cover. |
| Menu Left/Right Entry Point (2) | 5/5 each | Own-menu-held RS edge and stick touches block unrelated actions; full-pull suppression; gyro disabled. The Fn reset is intentionally allowed; two mixed entry chords still apply real layers. |
| Modifier Double Tap (2) | 5/3 each | Both pads disabled; menu/RS edge blocked; modifier input becomes output or self-first transition. Timeout and 50 ms scroll output remain. |
| LST/RST Double Tap (2) | 5/5 each | Both pads disabled; menu/RS edge/full-pull slots blocked. Second touch leaves the window before applying the gyro/entry pair. |
| RTP Double Tap | 5/5 | Left pad disabled; right pad replaced with selection D-pad; menu/RS edge/full-pull slots blocked. Pad selection/cancellation removes self first. |
| Menu Left/Right Double Tap (2) | 4/4 each | Both pads and gyro disabled; RS edge, opposite menu button, and full-pull slots blocked. Own menu button performs self-first completion. |
| Single-modifier Tap Covers (2) | 0/0 each | Release replaces the parent's Double Tap-producing release with family cleanup. No Always On action. |
| Combined-modifier Tap Cover | 0/0 | Release suppresses the uncovered Mod 2 Gyro toggle, while clearing the released-side family. Two mixed empty/removal arrays remain real cleanup. |
| LST/RST Tap Covers (2) | 0/0 each | Release removes cover + entry and suppresses the entry layer's Double Tap creation. |
| RTP Tap Cover | 0/0 | Same release suppression for RTP; does not add the repeating-removal workaround to the touch timer. |
| Modifier Double Tap Covers (2) | 0/0 each | Release suppresses reopening the Double Tap window, removing scroll + cover; scroll output stays available. |
| Menu Left/Right Double Tap Covers (2) | 0/0 each | Same prevention of window reopening for menu hold keys; gyro disabled. |
| Transition Sets 0/1 (2) | 12/12 each | Pads/gyro disabled; stick clicks and selected full-pull inputs blank; menu releases explicitly empty; held-menu chords block edge/touch cleanup until released. |

### Why the variants have different empty counts

This is a physical-input difference, not evidence that alternative lost the
Always On boundary protection. Alternative removes two default full-pull blanks
from each of four single modifiers, two scroll layers, and two modifier Double
Tap layers (16 fewer), while its two ramp stages add two partial-pull blanks
each (4 more). Net: **12 fewer active pure empty entries**. Direct ordered
Double Tap layer changes still match after the role swap.

## Inherited-route review and remaining uncertainty

Each timed layer was checked against the **15 Base command entries that directly
add/remove/hold layers**. Six windows explicitly redefine the relevant inputs
or disable their source: eight routes are redefined and seven are covered by
disabled pads. This includes Base's pad key-helper and hold-layer entries, not
only the obvious menu/modifier/ramp entries.

RTP Double Tap is intentionally different. Eight Base routes have explicit
input replacements and five are covered by its disabled left pad. Its right
pad changes from Base's `absolute_mouse` group 562 to `dpad` group 1298. Base's
pad `click` hold-layer and `touch` entry-layer paths have no explicit matching
click/touch activator in that new group, so these **two routes depend on the
source-mode replacement**. The saved structure supports the intended isolation;
the audit does not call this a demonstrated leak or proven crash. Confirm on
the target client that the old click/touch layer bindings do not survive that
replacement during the short window.

Other previously active layers can also exist below a timed layer. A direct
ordering check is not a simulation of every such stack. The layouts clean their
ordinary parent state before entering the window, but tests should include
missed-release stacks and mode shifts. The active layer with an input does not
necessarily own every other input, and an omitted input is not blanket isolation.

## Consequences for cleanup changes

The author subsequently clarified that the menu helpers/hold keys/covers in
cleanup findings F1/F2 should remain lightweight overlays of an existing stack.
They inherit unrelated inputs and rely on the underlying stack's recovery;
needing another related-button press for a residual cover is an acceptable
tradeoff. Their release-only cleanup is therefore not, by itself, a repair task.
Do not add independent stick-edge cleanup to every cover. The author confirmed
the existing menu overrides are intentional: all six menu layers in F1/F2 disable
gyro, and Menu Left: Escape / Menu Right: Tab block RS edge. Start/Select menu
interactions are not used during gameplay, so WASD modifiers and ramp-up need
not remain available there. This resolves the design review; preserve those
overrides while keeping local cleanup and inherited recovery.
The [main cleanup examples](../../resources/Steam%20Input%20JSON%20Structure.md#cleanup-scopes-and-concrete-examples)
and `todos.md` now preserve this distinction and the accepted current-branch /
released-side cleanup scopes.

The earlier cleanup audit's release-only and missing-target observations remain
facts, but they are not permission to add removal commands to every blank slot.
The consistency contract must include the **protected timing state**:

- Limit edge cleanup to layers that need that recovery: it displaces the inherited
  LS WASD modifier or RS ramp-up. Ramp-up's add/remove API constraints explain more
  frequent RS blocking; do not infer that LS must match every RS override. See
  [the edge-cleanup tradeoff](../../resources/Steam%20Input%20JSON%20Structure.md#stick-edge-cleanup-and-inherited-actions).
- Preserve intentional blocks while the owner/timer should remain active.
- For a new recovery action inside an Always On layer, remove that timed owner
  first in the same entry, then perform the broader cleanup or transition.
- At an entry boundary, finish all other layer operations before adding the
  timed layer. Do not split the sequence across independent activators.
- Keep tap suppression, gyro gating, and stale-state recovery as distinct jobs.
- Preserve the 30 non-Always-On touch-release arrays that currently add a cover
  or Fn layer before their stick cleanup; they are separate from the verified
  Double Tap entry/exit ordering. This audit does not reorder either category.

The behavior and author attribution are now documented in
[Steam Input JSON Structure](../../resources/Steam%20Input%20JSON%20Structure.md#blocking-to-protect-layer-timers),
linked from README, and added to both Claude and Cursor binding-order/prep
skills. The cleanup audit now links this constraint prominently.
The binding-order skill also corrects its stale RTP copy/paste warning and makes
new-layer cleanup updates conditional on scope and protected timing states.

## Validation

Both sources pass preset-order checks, unique-title checks, exact numeric/title
round-trip with 1,437 references, and the full three-entry command budget. The
builder scans all input definitions and source groups, records literal stored
binding order, and checks the complete first/last subcommand at each timed
boundary. It preserves source hashes and writes only audit artifacts.
An independent scan of numeric IDs confirms the reported empty/source counts
and all 13 entry / 30 exit sequences. Every CSV payload was reconciled to its
source entry; both catalogs cover all 54 titles. At the initial audit, both JSON
and VDF pairs were byte-identical to HEAD; subsequent JSON description-only edits
do not change these binding findings. Local documentation links and skill frontmatter pass
validation.

For a future fresh-load Deck check, verify unrelated menu/modifier presses,
both pads, RS edge, and opposite-stick touches during each 150/200 ms window;
the intended second press and timeout; interrupted delayed applies; and the
RTP click/touch source-mode boundary. Include both variants and normal Gyro
states. Observe that only the intended self-first exit changes other layers.
Current crash status and exact client scheduling remain unverified.

Regenerate after making title-form copies with `convert_runtime_ids.py to-titles
--output`, named `default.json` and `alternative.json`:

```bash
python3 findings/2026-09-28-neptune-blocking-audit/build_inventory.py --readable-dir /path/to/readable-copies
```

No layout repairs, version bump, VDF export, or commit was performed.
