# Derived stacks under the Double Tap windows, and the blocks they need (90.6)

**Author rule, 2026-09-30:** think about the lifecycle of the moment a Double
Tap window is added. Trace every stack it can land on, and ask whether any of
them would ever have a layer API call under an input the window leaves open.
If one would, the window blocks that input for its lifetime:
- **replace** it with the underlying bind when that bind is always the same
  (for example always E, or always middle mouse)
- **clear** it otherwise, because the window is applied in more than one
  context and a hard-coded bind would be wrong in some of them

## How the stacks are derived

[audit_inheritance.py](../../audit_inheritance.py) starts from Base and
applies every effective binding's layer commands. It respects bottom-to-top
order, whole-input overrides and disabled sources, and it ignores chord
conditions, so missed releases and stale stacks are included. It goes up to
5 input events.

| Depth (events) | Stacks (default) | Stacks under L1 Double Tap | Routes under the windows |
|---:|---:|---:|---|
| 3 | 2,458 | 11 | trigger edges; RTP touch (allowed) |
| 4 | 21,288 | 85 | + RTP back buttons |
| 5 | 157,674 | 532 | no change (saturated) |

The number of stacks keeps growing, but the set of routes stops at depth 4,
and the audit fails if depth 5 adds a route depth 4 didn't. The search takes
about 3.6 s per layout. Hand-traced stacks (the earlier `traced_stacks.json`)
missed all of these routes.

## Routes found and blocks applied

| Window | Input | Layer API underneath | Underlying bind across stacks | Block |
|---|---|---|---|---|
| All seven (default) | `left_trigger` / `right_trigger` edge | `Gyro Off Ramp Up` removes itself | left or right mouse in most stacks, nothing under Gyro Off Ramp Up | clear (**replaced with the mouse button since 90.10**: a stack with only a layer command adds no keybind; [record](../2026-10-01-stateful-transitions/README.md#what-the-fix-pipeline-derived)) |
| RTP Double Tap (both) | right pad `touch` | Base adds `RTP: Entry Point` | nothing but the layer command | **allowed** (see below) |
| RTP Double Tap (both) | four back buttons | the Fn layers (hold a menu button, quick-tap the right pad) | Ctrl from Base, menu-held chords from Fn | clear |

Alternative's triggers are modifiers with their own window blocks, so only the
RTP routes apply there. Every block is a clear, because none of the underlying
binds is the same in every stack.
[steam_layout/fixes/window_routes.py](../../steam_layout/fixes/window_routes.py) applies the recommendations
(18 in default, 4 in alternative). It's idempotent, runs last in the `python3 -m steam_layout.fixes` pipeline, and
[install_neptune.py](../2026-09-30-steering-lean/install_neptune.py) runs it
last.

**RTP Double Tap's touch is allowed (author, 2026-09-30).** The window's
dpad-mode right pad is its own second-tap selection. A second tap in the north
or south region transitions to Circular Scroll, and a tap anywhere else leaves
the window and stays in mouse mode. It's a unique edge case, so no touch bind
is added, and the `allow` decision with this reason is in
[traced_stacks.json](../../traced_stacks.json). An earlier version cleared
touch there; that clear was removed.

**Not blocked:** stick clicks, face buttons and D-pad. No derived stack puts a
layer command under them in a window, so they stay inherited. `--untraced`
still lists which layers use them for layer commands elsewhere.

## Tests

- [test_audit_inheritance.py](../../tests/test_audit_inheritance.py) covers:
  - the explorer: parent removal, contexts, overrides, disabled sources, no
    reordering, hold layers, mode shifts, the depth limit
  - saturation, and replace versus clear
  - the working layouts: all seven windows audited, saturated, and with no
    undecided route
- [test_double_tap_windows.py](../../tests/test_double_tap_windows.py) pins
  the back-button and trigger-edge clears. It also checks that RTP Double Tap
  keeps its dpad pad with no touch bind and that the `allow` decision is
  recorded.
