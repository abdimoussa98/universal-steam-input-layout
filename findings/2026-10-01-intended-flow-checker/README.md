# Intended-flow inheritance checker

Built 2026-10-01 from the [implementation plan](../../plans/2026-10-01-intended-flow-inheritance.md);
every work-order item is done. Read-only; the layout changes below were made
separately, from [author decisions](#author-decisions-2026-10-01) on its first
findings. Both Neptune variants are fully covered: every layer is in a
declared family except the two reached only by legacy `hold_layer`, which are
listed as out of scope. **Both variants are clean as of 90.9.**

> **Correction, 2026-10-01 (author):** this was a misreading. "More than one inherited keybind
> means block" is not a rule for ordinary layers. It is the last step of the Always On window
> rule: under a layer with an Always On action, if one of the bindings it could inherit is a
> layer command, clear the input when more than one keybind is possible, otherwise override it
> with that keybind. The Window audit checks that. The Flow audit now lists differing inherited
> bindings as information ("varies") and no longer fails on them.
>
> Below, "conflict" is the old name for "varies". The counts and decisions
> recorded here are from before the correction.
>
> **Deprecated, 2026-10-01:** the family walk this record describes
> (`flow_paths.py`, `flow_covers.py`, the `families` rules) is no longer used.
> `audit_flow_inheritance.py` now runs on backward chains, with the cover
> results checked to be identical on the 90.9 layouts
> ([record](../2026-10-01-backward-chain-stacks/README.md#deprecated)).

```sh
python3 audit_flow_inheritance.py neptune/single-set-default_hold-gyro_latest.json
python3 audit_flow_inheritance.py <layout> --layer 'L1: Tap Cover'          # paths, bindings, layers above
python3 audit_flow_inheritance.py <layout> --inventory --family steering   # classified transitions
python3 audit_flow_inheritance.py <layout> --json
```

Exit 0 means clean; 1 means open findings or coverage gaps; 2 means invalid input.

## Pieces

| File | Plan § | Does |
|---|---|---|
| [`steam_layout/flow_model.py`](../../steam_layout/flow_model.py) | 1 | Classifies every layer-changing entry. Followed: entry, second-press, hold, release, expiry, removal, cancel, center. Listed with a reason, not followed: reset, recovery, legacy-hold, mode-shift. Also the mode-aware input lookup |
| [`steam_layout/flow_config.json`](../../steam_layout/flow_config.json) | 1 | What bindings can't say: nine families with their contexts (and which context layers are live), starting controls, controls held at the start or held only for chords, exclusions at family boundaries, the cover list, and decisions |
| [`steam_layout/flow_paths.py`](../../archived/depth-search-and-family-walk/steam_layout/flow_paths.py) | 2 | Walks (ordered stack, held controls) states; resolves the effective input per stack; checks chords against held controls |
| [`steam_layout/flow_inheritance.py`](../../steam_layout/flow_inheritance.py) | 3 | Nearest lower definition per input and lower stack; normalized comparison; conflict / review / replaced / satisfied |
| [`steam_layout/flow_covers.py`](../../archived/depth-search-and-family-walk/steam_layout/flow_covers.py) | 6 | Cover check: owners from the flows, then outlives owners, below its owner, intervening layer; layers above each cover for review |
| [`audit_flow_inheritance.py`](../../tools/audit_flow_inheritance.py) | 4 | Text and JSON report; coverage gaps, inheritance findings and cover findings kept separate |
| [`tests/test_flow_inheritance.py`](../../tests/test_flow_inheritance.py) | 5 | 23 fixture tests with hand-known paths and bindings, 3 on both Neptune variants |

## Families

| Family | Starts from | Reaches |
|---|---|---|
| modifiers | Base / Gyro, the two modifier controls | 19 modifier layers and Gyro (the L1+R1 toggle) |
| menu_left, menu_right | Base / Gyro, Select or Start | Entry, Fn, window, Escape/Tab, covers, the protected steering entries, both Transition Sets |
| steering | the Transition Set 1 commit: Base (+Gyro) > Steering > LS Entry Point, live | the 12 in-mode steering layers and the reused L1/R1 Tap Covers |
| left_stick_touch, right_stick_touch | Base / Gyro, the stick's touch | Entry Point, Tap Cover, Double Tap, Temporary Gyro |
| right_pad | Base / Gyro, right pad touch | Entry Point, Tap Cover, Double Tap, Circular Scroll |
| left_pad_keys | Base / Gyro, left pad swipes | Escape, Enter, Tab, Backspace |
| ramps | Base / Gyro, RS edge, a trigger held for the direct ramp | Gyro Off Ramp Up, Turning Ramp Up 0/1 |

Family boundaries are explicit exclusions with reasons: the Transition Set 1
commit (the steering family starts there), and Start/Select leaving steering
(the menu families start there).

## Rules worth knowing

- **A source-mode change blocks inheritance** (author rule, 2026-10-01). The
  first group for a source, walking down from the top (or the target's own
  group), sets the mode; a lower group in a different mode stops the lookup.
  Applied when firing inputs and when comparing inherited bindings. Documented
  in [Layer Definition of Done §8](../../resources/Layer%20Definition%20of%20Done.md#a-source-mode-change-blocks-inheritance).
- **Family scope.** A restricted context layer (Base, Gyro) fires only on the
  family's declared controls. Layers the flow adds, and live context layers,
  fire on all their inputs.
- **Held controls.** A control is held across steps only if the family's
  reachable layers time it (a release or hold entry) or a chord checks it;
  everything else is a tap. A delayed entry is the successful hold; a release
  without it is the early-release branch. Resets aren't expanded into timers.
  A stick points one way: at most one direction per stick is held.
- **Deflection chords** (mask bits 30/31) are satisfied by any direction or the
  edge of that stick: an over-approximation where the edge is inverted.
- **Center exits.** A repeating removal on an inverted stick edge
  (`edge_binding_invert` 1) is the stick returning to center: a lifecycle exit,
  followed, not a stale-state recovery.
- **No depth cap.** Visited states end cycles; `--max-states` is a resource
  limit that marks a family not covered.
- **Covers** inherit their owner by design, so their inheritance findings are
  context; the cover check judges them. A cover's owner is the layer directly
  below it right after each add (a window that removes itself hands the cover
  to the layer under it).
- **Decisions** (`decisions` and `covers.allow` in the flow rules) accept a
  finding with a reason; accepted findings stay listed. A decision that no
  longer matches anything is reported as stale.

## Validation against documented behavior

| Documented | Found (both variants) |
|---|---|
| Modifier recipe: tap → window → Scroll → Double Tap Cover; both Mod 2 orders; Temp Cursor by hold or thumb lift | The 19 modifier layers plus Gyro; `L1&R1: Tap Cover` on four lower stacks (two orders × Base/Gyro) |
| Menu recipe, Start/Select overlays, protected steering entry | Both menu families reach all their layers and both Transition Sets |
| Steering after commit: owners, takeover, banks, chorded windows, covers | All 12 in-mode layers, plus the reused L1/R1 Tap Covers |
| Covers sit on their owner and leave with it | Every cover clean (the two menu overlays that weren't were removed in 90.9) |
| Steering helpers inherit the active owner's driver controls | Reported as conflicts under the author's rule; recorded as `allow` citing the steering README and its pinning test |

Inheritance of non-cover layers, summed over the families' lower stacks
(default, 90.9): 27 replaced, 16 satisfied, 42 review, 8 conflicts (all with a
recorded decision).

## Author decisions, 2026-10-01

The first full run (90.7) left three open items; the author decided all three.

1. **A source-mode change blocks inheritance.** The run had 43 "unsupported"
   inputs per variant inheriting through a layer that binds the source in a
   different mode: the key layers' single-button left pad, the Transition Sets'
   mouse right stick over the Fn dpad, and RTP's pads. The rule settles all of
   them as blocked. It also removed the apparent `RTP: Entry Point` over
   `RTP: Double Tap` conflict: the window's dpad-mode pad doesn't inherit Base's
   mouse-mode `touch`, so a second touch never adds the Entry Point inside the
   window. `audit_inheritance.py` now reports such cases as blocked
   (`mode replaced`), and the RTP window's `touch` allow in `traced_stacks.json`
   was retired.
2. **The opposite-button overlays are removed (90.9).** `Menu Left: Backspace`
   (Select while Start's menu is open) outlived its owner when Start was
   released with Select still held, by design: the
   [split-menu plan](../../plans/2026-09-27-split-menu-entry-point.md) added
   it so the still-held Select couldn't fall through to Base, open Menu Left
   and send a stray Escape. But pressing Start again put `Menu Right: Entry
   Point` above it; that layer binds Select without a release, so the overlay's
   own release was hidden and the next Select press typed a stray Backspace.
   `Menu Right: Enter` mirrored this.

   The author's decision: the menu whose button is held owns the combo, like
   every other Fn key (hold LB for F10, lift Start, and LB becomes the L1
   modifier). So the layers aren't needed. The fix
   [`menu_combo_keys`](../../steam_layout/fixes/menu_combo_keys.py) makes the
   menu chords type the key directly (the Entry Point's early chord adds Fn,
   then the key; the Fn chord is its pre-split `key_press`), drops every
   removal of the two layers, and deletes them: 69 layers per variant.
   **Accepted cost:** lift the first button first, then release the second
   within 300 ms, and it sends Escape (after Backspace) or Tab (after Enter).
3. **90.8 was an intermediate build.** It kept the layers but removed them
   with their menu's family, which protected nothing and reintroduced the
   stray Escape/Tab. 90.9 replaces it; the 90.8 snapshot is kept, untested.
   The fix runs in the install pipeline, so a steering reinstall keeps it.
   Deck checks K1–K5 are in [manual testing](../../archived/manual-testing.md).

## Benchmark

Inputs: default `e04e681abd012cce…`, alternative `dcd8abbe519f1964…` (90.9),
flow rules v4 `e9c06efe1c4c8340…`. macOS, Python 3.9, full CLI run with JSON.

| Variant | Wall | Peak memory | States (modifiers, menu L/R, steering, LST/RST, RTP, LTP keys, ramps) |
|---|---:|---:|---|
| Default | 0.69 s | 22 MB | 992, 640 / 832, 1,832, 20 / 20, 64, 80, 960 |
| Alternative | 0.75 s | 24 MB | 992, 640 / 832, 1,832, 20 / 20, 64, 80, 3,072 |

All 763 layer-changing entries per layout classify (767 before the two layers were removed). Not followed, per variant:
271 recoveries, 25 resets, 8 family-boundary exclusions, and 1 legacy hold on
a family layer. Earlier reductions that kept the search small: tracking only
the controls a family's reachable layers time or check (menus fell from about
54,000 states), and one direction per stick (steering fell from 7,584 to
1,832). The mode rule then removed inputs that no longer fire across a mode
change (menus to 2,144 / 2,528, left-pad keys from 1,040 to 80), and removing
the two overlays shrank the menus again (640 / 832).

## Limits

- Intended flows only, not every runtime interleaving: no missed releases,
  numeric timers or analog geometry beyond one direction per stick. Entries
  firing together run in serialized order.
- Deflection chords over-approximate on inverted edges; diagonals aren't
  modelled.
- Mode-shift groups that change layers would be reported as unsupported
  (none do today).
