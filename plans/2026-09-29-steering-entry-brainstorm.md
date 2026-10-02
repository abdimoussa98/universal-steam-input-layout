# Steering brainstorm — current agreed behavior

Updated 2026-09-30. [Implementation plan](2026-09-29-steering-implementation-plan.md)
· [Candidate exports](../findings/2026-09-30-steering-lean/README.md)
· [Visual overview](steering-overview.html) · [Steering todo](../todos.md#steering)

This revision replaces the earlier both-controls-released rearm rule, Mod 2
tap/double recognition and separate directional entry/repeat helpers. The
[previous brainstorm](2026-09-30-steering-entry-brainstorm.previous.md) preserves
historical discussion and matrix rows; conflicting older policies are superseded.

Steering remains stateful action layers within Base, not another action set.
The implemented inventory is **16 added layers**, with no new Always On actions.
No modifier bank is built into a W/S owner.

## Transition matrix for review and implementation

| Situation | Behavior |
|---|---|
| Either stick deflected before/during menu entry | Since 90.10: a stick guard lands on the Entry Point, so no Fn while a stick is out. A tap still types Tab/Escape through the Double Tap window; a 200 ms hold or a thumb lift makes the release silent |
| Deliberate menu stick click | Since 90.10: the click's Release clears and adds the transition; Right Menu + LS click selects steering, and the menu release commits. Inside Steering every menu + click gesture clears, keeping Gyro |
| Start / Select inside Steering | Since 90.10: no driver held, Steering's own Entry Points and Steering stays; driver held, Tab / Escape; modifier maps, their keys |
| Enter with carried WASD | Disposable protection, no exit clock; ends at LS center or driving-control press |
| Right driver / left driver | W / S, R1/L1 Default and R2/L2 Alternative |
| Opposite pressed while driving | Ordered Modifier 2, no opposing movement output |
| Dominant released with opposite still held | Clear old branch; held opposite takes over W/S with old gesture history consumed |
| Dominant released without opposite held | WASD fallback; carried W starts fresh exit clock |
| Normal fresh Up / Down | Modifier 1 / 0; eligible short return to actual center scrolls once |
| Normal hold or modified action | Consume tap through shared cover until true center |
| Up→sideways | Since 90.10: A/D and the Tap Cover; Modifier 1 stays until the stick returns to center |
| Up→Down without center | Since 90.10: remove Modifier 1 only; the W or S layer's repeating bind then adds Modifier 0. Under the Tap Cover nothing changes until center. Inverse for Down→Up |
| Opposite direction inside a Double Tap window | Since 90.10: removes the window and drops the pending scroll; the W or S layer then adds the other modifier |
| Sideways inside a Double Tap window | Since 90.10: plain A/D; the window stays |
| Same-direction double and second hold | Shared normal repeat cover, Base face buttons; no final release tick |
| Repeat reversal/sideways/center | Stop repeat and consume; no unintended opposite tick |
| Modifier 2 Up/Down | Immediate simple scroll, repeat while held; no tap/double/long-hold recognition |
| Modifier 2 faces during scroll | Modifier 2 mappings remain, independent of scroll |
| Uncovered Mod 2 opposite release | Clear all layers to Base, including Gyro |
| Opposite held 200 ms or mapped action/thumb release | Apply existing opposite-side single Tap Cover |
| Covered opposite release | Since 90.10: back to the owner layer with no Tap Cover; a held stick enters its modifier at once |
| Fallback W or S 1 / 2.5 seconds | Repeated warning / whole-steering exit with beep and vibration (S since 90.10) |
| W released or owner acquired | Stop warning and cancel clock; next fallback hold starts fresh |
| Mapped button held across changed mapping | Old output ends, replacement waits fresh press; unchanged output survives — native gate |
| Existing AO window / overlay interruption | Preserve self-first isolation/recovery; no stale owner, key, wheel or delayed work |

Normal single-scroll timing is 150 ms pending-window expiry or early resolution.
Normal hold consumption is 250 ms; repeats are 50 ms. Shared normal repeat has a
5 ms initial delay used for cancellation during reversal. These native bindings
need Deck checks, particularly shared cover reassertion and reversed-tick
cancellation. See [acceptance](../findings/2026-09-30-steering-lean/ACCEPTANCE.md).
