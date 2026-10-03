# Brainstorm: steering behavior and deflection-safe entry

Updated 2026-09-30. **Behavior contract retained; lean candidate generated.**
The [implemented lean candidate](../../findings/2026-09-30-steering-lean/README.md)
adds **25 layers with zero new Always On actions**; nine safety helpers remain
beyond the conditional 16-layer target. Native verification is pending.
The [lean plan](../../plans/2026-09-29-steering-implementation-plan.md) targets **16 added
layers with no new Always On actions**, subject to complete binding and native
proof. The [existing 36-layer candidate](../../findings/2026-09-29-steering-implementation/README.md)
remains unchanged. The user reports it looked good on their Deck; individual
acceptance cases and the tested build/variant are not yet recorded.
Linked from the [Steering todo](../../todos.md#steering). Read the short
[interactive overview](../../plans/steering-overview.html) for the behavior; its model is
not Steam Input validation.

The [previous plan](2026-09-29-steering-implementation-plan.baseline.md) preserves
the audit-era architecture. Its owner-specific Always On windows are no longer
mandatory: ordinary-input windows can inherit cleanup from W/S owners if their
timing and lifecycle pass the lean plan's gates. The
[documentation review](../../findings/2026-09-29-steering-design-review/AUDIT.md)
remains historical evidence, especially for inheritance and timer hazards.

**Steering is a stateful layer:** it persists after a driving control is released
and owns temporary entry, driving, modifier, and gesture helpers. Everything
uses action layers inside the existing action set. Action-set switching remains
excluded because the author reports buggy behavior with action sets.

This revision replaces bank cycling, tap/double-tap/hold bank selection, and the
ten-layer directional-bank proposal. **No modifier mapping is built into either
driving owner.** Stick direction and the opposite control select separate,
momentary banks. Older todo wording and the historical layout do not constrain
these requirements.

## What is confirmed, proposed, and unproven

- **Confirmed:** protected menu entry; Menu Right + LS click for steering;
  disposable WASD entry protection; right = W and left = S; LS up = Mod 1,
  LS down = Mod 0, opposite held = Mod 2; Base button mappings when driving
  without a selector; normal Mod 0/1 scroll tap/hold/double-deflection behavior;
  Mod 2 may also use layer-based tap/double flows, with exhaustive edge-case
  review rather than an instruction to remove those flows;
  dominant-release cleanup to fallback; five-second fallback-W exit with
  repeated vibration beginning at 2.5 seconds; releasing W cancels the warning
  and restarts the timing on the next hold.
- **Recommended interaction policies:** Mod 2 has priority and restores the
  current LS bank on release; handoffs consume pending scroll gestures; Mod 2
  uses a separate tap/hold/double gesture context, gated by recognized center
  and a fresh deflection, while keeping Mod 2 button mappings; first press owns
  driving; exact simultaneous presses acquire neither owner;
  both controls must be released before rearming after a held-opposite cleanup;
  input cancellation wins an exact timer tie. The detailed rules below make
  those choices reviewable rather than silently treating them as requirements.
- **Unproven implementation:** the lean 16-definition target, shared ordinary
  windows/repeat cover, consumed-state reuse and removal of dedicated Rearm.
  The complete binding tables must account for every remembered state. Retain
  a minimal extra helper if sharing cannot preserve the behavior below.

## Menu entry stays protected

| Current context | Input / condition | Intended result |
|---|---|---|
| Base | Menu button pressed, both sticks centered | Enter its normal menu entry |
| Base | Menu button pressed, either stick deflected | Enter its alternate protected entry directly |
| Normal menu entry | Either stick deflects while the menu button is held | Transfer to alternate entry; start a fresh Tab/Escape tap window |
| Alternate entry | Release its menu button within the fresh tap window | Tab for Menu Right; Escape for Menu Left |
| Alternate entry | Tap-cover condition occurs | Apply an ordinary silent cover; never automatically apply Fn |
| Alternate entry | Deliberate stick click while menu button is held | Explicit Fn/stateful-layer transition remains available |
| Menu Right interaction | LS click | Select steering entry; exact commit wiring remains open |

Both menu buttons need this protection. Either stick is sufficient, whether it
was already deflected or moves during normal entry. Restarting the tap window
means restoring release eligibility, not emitting Tab/Escape at transfer.
Continued deflection or an entry repeat must not restart that window repeatedly.
No menu timing values are selected here.

Recommended: alternate entry remains selected until the menu interaction ends,
even if the sticks center. Returning to normal mid-hold would reintroduce the
accidental Fn path. Block inherited automatic Fn routes, including stick-touch
release and any two-menu-button route; the deliberate stick-click exception
stays available. Once a deliberate steering transition is committed, consume
the originating menu tap so the later menu release cannot also emit Tab.
The lean plan adds no retrospective cancellation after Fn entry and preserves
deliberate Fn. Simultaneous menu buttons and existing Enter/Backspace/double-tap
paths still need a wiring review. Touch, deflection, and click are separate inputs.

The suggested Base implementation selects the normal or protected path with
existing chords/repeats. Existing normal entry bindings detect later deflection.
Protected-entry selection must beat normal repeats and cancel pending automatic
Fn application. This selection needs no dedicated detector layer.

## Steering states and outputs

| State | Movement and buttons | Exit timing |
|---|---|---|
| Protected entry | WASD and normal controls; no driving owner or modifier bank | Disabled, however long W remains held |
| Fallback | WASD and normal controls | Continuous fallback W warns at 2.5 s and exits at 5 s |
| W owner | Right control holds W; LS vertical movement becomes modifier/scroll input | Disabled |
| S owner | Left control holds S; LS vertical movement becomes modifier/scroll input | Disabled |

Default uses **R1 = W / L1 = S**. Alternative uses **R2 = W / L2 = S**.
The **dominant control** is the one that acquired the active W/S owner. Pressing
the opposite control never adds the opposite movement key and never transfers
ownership while the dominant control remains held.

W and S are exclusive. Entering S while fallback LS-up was outputting W must
end fallback W before S takes over; entering W from fallback S is symmetric.
For a W-to-W handoff, preserve the logical held output without a synthetic key
press if Steam permits it. Do not assume two sources for the same key can be
removed in any order without producing a release. This needs a runtime check.

**Recommended:** LS supplies the vertical selectors and retains A/D laterally;
RS retains its existing role. In fallback, any diagonal that still outputs W
counts as continuous W. Moving to left/right without W cancels the exit hold;
full stick centering is not required to cancel it. The disposable guard has a
different boundary: it ends when **LS centers**, not merely when LS leaves up.
Stick thresholds and hysteresis need to distinguish those events reliably.

### Disposable entry protection

If steering is entered with LS deflected, apply one untimed entry guard over
fallback. WASD stays usable, including an already-held W. No warning or exit
timer runs under the guard. Retire it at **the first of LS centering or a
steering-control press**. It never returns during that steering session.

LS-only selection is recommended because this guard protects carried movement.
Either-stick deflection continues to select the protected **menu** flow; those
are different decisions. RS-only deflection should not leave a steering guard
waiting for an LS-center event that has already occurred. This LS-only choice
is a proposal; the retirement events were explicitly confirmed by the author.

If a steering control consumes the guard while LS is up/down, enter its owner
and select the corresponding bank immediately. That inherited deflection is a
**consumed gesture**: it cannot emit a scroll when released or become the first
half of a double-deflection. New scroll gestures require recognized neutral
and a fresh deflection. Time under the guard never contributes to fallback's
later exit timer.

### Driving and momentary bank selection

| While W or S is owned | Effective button mappings | Movement |
|---|---|---|
| LS neutral, opposite released | Base mappings; no Mod layer | Keep the owned W or S |
| LS up, opposite released | Separate **Mod 1** | Keep the owned W or S |
| LS down, opposite released | Separate **Mod 0** | Keep the owned W or S |
| Opposite control held, any LS position | Separate **Mod 2**, including during its scroll repeat | Keep the owned W or S; never add its opposite |
| Direction in normal double-deflection scroll-repeat mode, opposite released | Proposed Base mappings; suspend Mod 0/1 | Keep the owned W or S while the wheel repeats |

The bank is available as soon as the selector engages; a hold is not required
before a face-button combination works. A plain driving owner has no built-in
bank. Entering an owner with a selector already held can therefore apply a bank
immediately without contradicting the absence of a default bank.

Recommended effective-bank rule: **Mod 2 > current LS up/down > no bank**.
During normal double-deflection repeat, suspend the direction bank so Base
buttons remain available, following the Base scroll-helper approach. Mod 2
scroll repeat instead keeps Mod 2 mappings available throughout. Only one bank
is active at a time. Releasing the opposite control recomputes
from the **current** LS position, not the position when Mod 2 began. For
example, hold LS-up for Mod 1, hold opposite for Mod 2, move LS-down, then
release opposite: return to Mod 0. Do not keep hidden Mod 0/1 layers underneath
Mod 2 or require recentering just to restore the proper key map.

Every Mod 2 boundary cancels the outgoing interaction's pending output. Entering
Mod 2 cancels normal scroll taps, double-deflection history, and repeat helpers;
leaving it cancels Mod 2 taps, double history, and repeat. Restoring Mod 0/1 while
LS is still deflected restores only the bank, never a new deflection, tap, or double press. Recognized
center and a fresh deflection rearm normal scrolling. The opposite control is
only a bank selector during driving: its own press/release has no wheel output,
tap/double path, gyro toggle, or Base modifier-release side effect.

### Mod 2 has its own tap/hold/double scroll context

The author explicitly allows tap/double flows implemented with layers. The
requirement is to inspect their transitions and bug risks carefully, not to
eliminate those mechanisms. **Recommended behavior:** while the opposite
control is held, use a separate LS gesture context:

| Fresh gesture while Mod 2 is held | Scroll behavior | Button mappings |
|---|---|---|
| Short up/down deflection, then recognized center | One scroll in that direction, following the selected single/double arbitration | Mod 2 throughout |
| Long direction hold | Consume the release scroll; no wheel from holding alone | Mod 2 throughout |
| Same-direction double-deflection, second held | Repeating scroll until vertical release or cancellation; no final release tick | Mod 2 throughout, including repeat |
| Face/D-pad/click action during any phase | Recommended independent of LS scrolling: do not consume its pending tap, double window, hold tracking, or repeat | Use Mod 2; preserve the normal held-output handoff rules |

Mod 2 face use is independent because LS is no longer selecting the modifier
bank in this context. This is a recommendation, not a newly confirmed user
choice. It differs from normal Mod 0/1, where using a modified action consumes
the scroll tap. A long LS hold remains silent on release even if a Mod 2 action
was used. A short eligible LS stroke may still scroll while that action is
used. Repeating scroll must not expose Base buttons or remove Mod 2 merely
because the existing Base repeat helper normally does so. A Mod 2 face action
between the first and second taps must neither flush the pending single early
nor prevent a valid double. A face already held before a new LS direction also
must not consume that gesture. Adding/removing a gesture helper alone must not
release or replay a held face output whose Mod 2 mapping is unchanged.

Apply a neutral gate so entering Mod 2 cannot reinterpret a carried Mod 1/0
stroke as a new scroll gesture:

- **LS already up/down/sideways on Mod 2 entry:** discard normal gesture state;
  no new scroll gesture starts. Recognize center first, then require a fresh
  up/down deflection. Releasing the carried direction emits no wheel.
- **LS already recognized centered on entry:** a later fresh direction can
  start a Mod 2 gesture. A pending normal single/double window is still cleared.
- **Opposite press and LS deflection in the same input sample:** recommend
  treating the direction as carried, regardless of callback ordering. Require
  center and another deflection; processing two sampled events in a convenient
  order must not invent an intentional fresh stroke.
- **During a Mod 2 hold/repeat:** losing the vertical direction ends it. A direct
  reversal or sideways movement without recognized center consumes the stroke;
  center rearms before another direction can begin. A/D changes that preserve
  the same vertical direction do not restart hold duration or repeat cadence.
- **Rapid opposite release/repress while LS remains deflected:** every entry
  remains disarmed until center; no old hold, pending single, double candidate,
  or repeat may resume. Repeated layer selection commands are not new gestures.

Keep normal and Mod 2 histories separate. A first tap completed in normal
Mod 0/1 cannot combine with a second in Mod 2, nor vice versa. Even two Mod 2
taps separated by releasing and repressing the opposite control belong to
different contexts and cannot form a double. Every entry creates a fresh Mod 2
interaction; every exit cancels all pending output from that interaction.

On opposite release, stop Mod 2 pending taps/repeat before restoring the current
LS bank. If LS is still up/down, restore Mod 1/0 as a consumed gesture; its later
release emits nothing and supplies no double history. If centered, restore Base
mappings with no bank; any pending Mod 2 single is cancelled. A new centered-to-
direction gesture then follows the normal Mod 0/1 rules. No cross-context
restoration may replay a held face/D-pad/click output either.

Dominant release or whole-context cleanup wins over bank restoration and scroll
output: clear the entire branch, then return to fallback or exit as appropriate.
Under the recommended input-first timing policy, opposite release, vertical
release during repeat, direct reversal, or dominant release in the same sample
as a repeat deadline cancels that tick. Mod 2 entry similarly cancels a normal
pending tap/repeat due in that sample; Mod 2 exit cancels its pending single due
in that sample. No cancelled callback can resume when a layer exposes its input.

Single/double arbitration must be consistent within each context. The HTML's
deferred-single illustration can retain a completed tap until the double window
closes. Exact equality at the hold/double threshold, a new direction at the
single deadline, and activator callback ordering require explicit Deck checks;
no native Steam ordering guarantee is established here. Exact windows, center
dwell, directional hysteresis, and the extra gesture/helper cost remain open.
Normal Mod 0/1 behavior below and menu/steering entry remain intact.

### Normal LS vertical gestures reuse the Base modifier interaction

The intent is the Base bumper/trigger **tap/hold/scroll interaction**, not the
entire existing modifier layer lifecycle or its temporary cursor-gyro entry.

| Gesture during driving, without Mod 2 | Behavior |
|---|---|
| Quick deflect and release | Scroll once: up or down according to direction |
| Hold direction | Keep Mod 1/0 available; consume the release scroll |
| Use a modified face button, D-pad, stick click, or other modified mapping | Consume the release scroll immediately, including a fast combination |
| Double-deflect the same direction and hold the second | Repeat that scroll direction until vertical release, a cancelling handoff, or cleanup |
| Opposite direction for the second deflection | It is not a same-direction double press |

Use the established Base gesture thresholds/windows where they fit. Exact
values, repeat cadence, and first-tap emission policy must be read from and
validated against those bindings; HTML timing is only an illustration. A
double-deflection must not accidentally add a third scroll on final release.
Entering repeat consumes its release tap. Recommended: repeat suspends Mod 0/1
and exposes Base buttons; those buttons can be used without cancelling repeat.
Vertical release, direct direction change, or owner/context cleanup stops the
repeat. Mod 2 cancels this normal repeat and uses its separate gesture
context above; releasing Mod 2 with LS still deflected restores the direction bank
as a consumed gesture and never automatically resumes normal repeat.

In the HTML's deferred-single illustration, a completed tap has already returned
through recognized center. A subsequent different direction, sideways movement,
or Base face press emits that pending single once and ends double eligibility;
it does not silently discard valid scrolling. Mod 2 and owner/context cleanup
still cancel pending output. This emission policy is illustrative until the
Base timing implementation is selected.

A direct up-to-down crossover changes the bank immediately. If no stable
neutral was recognized, cancel the old gesture and treat the new direction as
consumed until neutral. Moving sideways without recognized center also consumes
the stroke; vertical release alone is insufficient to emit a tap or arm a
double-deflection. With recognized neutral, the old gesture ends normally and
the new direction starts its own interaction. Only a same-direction second
deflection within the same driving hold/session can form a double press.
Threshold chatter must not manufacture wheel taps, repeated bank applies, or
double presses. Exact neutral dwell/hysteresis is still to be specified.

### Dominant release and held inputs

Releasing the dominant control, from any bank or scroll state, must:

1. Cancel that driving interaction's delayed applies, pending taps, double-press
   windows, normal/Mod 2 scroll repeat, Mod 2 neutral-gate state, and queued
   bank restoration.
2. End its W/S output and remove the owner, every steering bank, and associated
   gesture helpers, including helpers that are not expected to be active.
3. Return to Steering fallback with the entry guard still consumed. A currently
   deflected stick immediately supplies fallback WASD. If it supplies W, start
   a **fresh** five-second exit hold and a fresh 2.5-second warning delay.

Recommended: a still-held opposite control cannot immediately become the new
owner. If it remains held at dominant release, block acquisition by **either**
control until neither is held; only a subsequent fresh
press can own driving. Repressing the old dominant while the opposite remains
held does not bypass that gate. Releases during rearm are silent: no Base
scroll or gyro toggle. This prevents unintended W-to-S handoff and stops
inherited repeating Base entry from rebuilding the old stack. If both controls
were sampled down simultaneously with no prior owner, remain in fallback and
require both to be released before acquisition rearms. A simultaneous press
also consumes an entry guard, even though it acquires neither owner. Distinct
press events use the first observed press as owner. These rearm policies may
require additional memory/helpers and are not free in the seven-layer budget.

Bank changes must also handle a held face/D-pad/click input. Recommended: end
an old output whose mapping changes, suppress its replacement until a fresh
physical press, and preserve unaffected held outputs. Never leave the old key
stuck, fire a second mapped action solely because a bank appeared, or replay a
held face action when Mod 2 restores Mod 1. The eventual release must clean up
the output that actually began. This policy requires validation and may cost
helpers; key-output replay is not established by the layer-command rules.

### Fallback exit and warning

Only **continuous W supplied by ordinary fallback** starts this timer.

| Elapsed eligible W | Result |
|---|---|
| 0 to under 2.5 s | Normal fallback movement; silent |
| 2.5 s to under 5 s | Repeat vibration while fallback W remains eligible |
| 5 s | Exit Steering and all owned helpers; emit the existing requested beep and exit vibration once |

Releasing W before exit cancels both thresholds, the repeating warning, and
queued feedback. The next hold starts at zero. Pressing a steering control at
any time before exit does the same cleanup and transfers to its owner; the
owner never inherits elapsed exit time, even if it also outputs W. A preheld
LS direction selects Mod 1/0 on that transfer as a consumed gesture.

Returning to fallback with LS-up still held starts a fresh timer immediately.
This is a context transition, so it does not require a physical W release or
new LS deflection. Its press-detection and restart behavior must be designed
explicitly for Steam rather than assumed from newly exposed bindings.

Recommended sampled-input priority: whole-state exit and dominant release win
first; then resolve eligible ownership/bank context changes, then fresh stick
and mapped-button input, then timers. A **dominant release plus a fresh opposite
press in one sample** means cleanup/fallback and blocking new ownership until
both controls are released, not an order-dependent W/S transfer. If the same
sample also changes LS, carry its final direction as consumed in the new
context. If a fresh mapped action's context/mapping changes in that sample,
suppress it until release/repress; an already-held output whose mapping remains
unchanged can continue. Opposite release cancels pending wheel output even if
face input changes in that same sample. UI clicks arriving separately are
ordered events and do not establish this native frame-level priority.

For timer boundaries, resolve those input/context changes first, then evaluate
whether a deadline still belongs to an eligible fallback hold. Thus a W release or valid steering press in the same
sample as 2.5 s or 5 s cancels that event. Once the five-second exit has already
completed, later input follows the outside Base layout and cannot resurrect the
old session. Exit leaves ordinary outside movement available; it releases
steering-owned outputs, not every globally held key.

## Transition matrix for review and implementation

IDs below identify proposed acceptance scenarios. Unless stated as confirmed
above, an edge-case resolution is a recommended policy to validate. Run each
applicable scenario with both W/S owners and both controller variants.

| ID | Starting condition and event | Required or recommended resulting behavior |
|---|---|---|
| M1 | Menu press with LS, RS, or both already deflected | Protected entry immediately; no automatic Fn |
| M2 | Normal entry; deflection arrives near Fn deadline | Cancel pending automatic Fn; alternate entry wins; fresh tap window once |
| M3 | Protected entry; stick centers, deflects again, or an entry repeat fires | Keep protection; do not keep restarting the tap window |
| M4 | Protected entry; touch release, other menu press, or long hold | No accidental Fn; ordinary covers only; two-menu key behavior still needs wiring review |
| M5 | Protected entry; deliberate LS click with Menu Right held | Reach steering; consume the originating menu tap on commitment; no stray Tab |
| E1 | Enter with LS-up; hold for more than 5 s | Guard preserves W/WASD; no warning or exit |
| E2 | Guard; LS centers | Consume guard; fallback active; no timer until W is output |
| E3 | Guard; LS-up and left steering press | Consume guard; end fallback W; acquire S + Mod 1; no W+S and no pending scroll |
| E4 | Enter with RS-only deflection and LS neutral | Protected menu flow; proposed ordinary steering fallback without guard |
| E5 | Guard active; both steering controls pressed in one sample | Consume guard; acquire neither owner; start fresh fallback W timing if applicable; require both controls released to rearm |
| F1 | Fallback W at 2.4 s; acquire W or S | Cancel exit/warning timing; drive immediately; LS-up selects Mod 1 as consumed |
| F2 | Fallback W at 4.9 s with warning active; acquire W or S | Stop warning immediately, cancel five-second exit, then drive |
| F3 | Fallback W warning active; W released or W direction lost | Stop warning; cancel exit and reset elapsed time |
| F4 | Fallback W; change up to up-left without losing W | Timer continues; no false reset from A/D |
| F5 | W release or valid owner acquisition at exactly a timer deadline | Input cancellation wins before feedback or exit evaluation |
| F6 | Fallback W reaches 5 s with no cancellation | Whole steering cleanup, one beep/exit vibration, no queued warning afterward |
| F7 | Just after steering has exited, a steering control is pressed | Outside Base behavior; expired callbacks cannot rebuild steering |
| D1 | Owner active, no selectors | Base button maps; no built-in or selected Mod bank |
| D2 | Owner active; fresh LS-up/down | Mod 1/0 immediately; arm direction gesture if eligible |
| D3 | Mod 1 active; opposite pressed | Replace with Mod 2; preserve owned movement; consume pending tap/repeat |
| D4 | Mod 2 active; opposite released with LS still up | Restore Mod 1 immediately; no wheel output or synthetic deflection |
| D5 | Mod 2 active; LS up→down→opposite released | Restore current Mod 0; no obsolete Mod 1 or queued scroll |
| D6 | Mod 2 active; LS centers before opposite release | Keep Mod 2 until release, then no bank |
| D7 | Both driving controls arrive in exactly one sample | Proposed no owner; remain fallback; both releases rearm acquisition |
| D8 | Dominant released with opposite still held | Clear branch, fallback; both controls must become released before a fresh press can acquire either owner |
| D9 | Both driving controls released together | One cleanup to fallback; no intermediate bank restore or scroll |
| D10 | Dominant released while LS-up | Fallback W begins a fresh exit timer; guard stays consumed |
| D11 | Default steering owner + opposite bumper also matches planned global L1+R1 cleanup | Steering Mod 2 wins; do not accidentally invoke the global exit chord |
| D12 | Enter Mod 2 with LS already up/down/sideways | Keep Mod 2; cancel normal gestures; carried stroke cannot scroll; require center then fresh direction |
| D13 | Enter Mod 2 while centered; later make a short up/down stroke | New Mod 2 gesture; one eligible single scroll through its own arbitration; keep Mod 2 buttons |
| D14 | Opposite press and LS deflection sampled together | Treat as carried deflection; no new gesture; require center and fresh direction |
| D15 | Mod 2 gesture pending/held/repeating; face/D-pad/click used | Recommended independent: use Mod 2 mapping without consuming or resetting the LS interaction |
| D16 | Mod 2 repeat active; LS centers | Stop repeat; no release tick; later direction starts another Mod 2 interaction |
| D17 | Mod 2 hold/repeat; reverse or move sideways without recognized center | End old hold/repeat; consume stroke; require center before new gesture |
| D18 | Mod 2 hold/repeat; add/remove A/D while vertical direction stays unchanged | Continue hold duration/repeat cadence and Mod 2; no duplicate deflection |
| D19 | Mod 2 repeat/hold active; opposite released while LS deflected | Cancel Mod 2 interaction; restore current Mod 1/0 consumed; later LS release emits nothing |
| D20 | Opposite rapidly toggled with LS still deflected | No resumed hold, tap, double history, or repeat; each entry requires center |
| D21 | Opposite/vertical/dominant release or reversal exactly at repeat deadline | Cancellation wins; no extra wheel tick or callback resurrection |
| D22 | Enter Mod 2 exactly when normal pending tap/repeat is due | Cancel normal output first; never feed it into Mod 2 history |
| D23 | Dominant released during Mod 2 repeat with opposite held | Clear all scrolling/Mod 2; fallback; fresh W timer if LS-up; both controls released before ownership rearms |
| D24 | Same-direction double-deflection entirely within one Mod 2 hold | Repeat after eligible second deflection; keep Mod 2 mappings; no final release tick |
| D25 | Mod 2 interaction active; whole-state exit or external cleanup | Cancel taps/repeat/history/neutral gate; fresh session cannot revive old output |
| D26 | Normal completed first tap, then Mod 2 entry and second deflection | No cross-context double; clear normal pending output; assess second only in new Mod 2 context |
| D27 | Mod 2 completed first tap, then opposite release and normal second deflection | Cancel Mod 2 pending output/history; no cross-context double |
| D28 | Mod 2 first tap, opposite released/repressed while centered, then second tap | New Mod 2 context; it cannot complete the previous context's double |
| D29 | Long Mod 2 direction hold with or without face use | Silent on release; Mod 2 stays active until opposite release |
| D30 | Mod 2 pending single due at the exact opposite-release deadline | Context cancellation wins; no late wheel output in normal mapping |
| D31 | Mod 2 second deflection opposite to first, with recognized center between | Not a double; settle any completed single under chosen arbitration and start the new direction independently |
| D32 | Mod 2 direction/face event exactly at hold/double threshold | Preserve context and mapping; verify selected threshold equality and native activator ordering before implementation |
| D33 | Mod 2 pending first tap; face action; valid same-direction second tap | Face neither flushes nor consumes pending single; valid double remains possible |
| D34 | Face already held in Mod 2; new LS gesture or gesture-helper transition | Do not consume LS gesture or replay/release an unchanged held face output |
| D35 | Dominant release plus fresh opposite press in one sample | Cleanup to fallback; quarantine ownership until both controls released; no event-order handoff |
| D36 | Context change plus fresh direction or mapped-button press in one sample | Carry direction consumed; suppress ambiguous fresh mapped action until release/repress; unchanged held mapping continues |
| D37 | Opposite release + pending wheel deadline + face change in one sample | Cancel wheel first; no stale Mod 2 action/tick after context restoration |
| G1 | Fresh short LS-up/down; return through recognized center without modified action | One scroll; no stuck bank or extra release output |
| G2 | Fresh direction; modified action used before hold threshold | Action uses its bank; release scroll consumed |
| G3 | Direction held beyond hold threshold, no action used | Bank remains; release sends no scroll |
| G4 | Same-direction double-deflection; second held | Proposed suspend Mod 0/1 for usable Base buttons; repeat until vertical release/cancellation; no additional final release tick |
| G5 | Repeat active; opposite pressed, owner released, or whole-state exit | Stop repeat and clear scheduled ticks immediately |
| G6 | Repeat cancelled by Mod 2; Mod 2 later released with LS still deflected | Restore direction bank as consumed; never auto-resume repeat |
| G7 | Direct up→down or sideways without recognized neutral | Switch/remove bank according to direction; cancel old gesture; no tap/double eligibility until neutral |
| G8 | Preheld LS selects a bank after guard/fallback→owner or Mod 2 release | Bank works immediately; no synthetic tap/double history |
| G9 | Mod 2 held while LS moves | Only its gated gesture context runs; normal Mod 0/1 histories/helpers stay inactive; release restores only current bank |
| H1 | Face/D-pad/click held across a bank change | End changed old mapping; proposed fresh press required for new mapping; no stuck/replayed key |
| H2 | Repeating bank reconciliation while desired bank is already active | Idempotent; no remove/add churn, gesture reset, or timer restart |
| H3 | Dominant release exposes Base modifier entry, or old dominant is repressed while opposite stays held | Steering's both-controls-released rearm gate blocks ownership and Base release side effects |
| X1 | Whole-state exit, external state transition, or recovery cleanup mid-gesture | Clear owned stack, W/S ownership, pending gestures, warning and exit timing; no resurrection |
| X2 | New steering session after X1 | Clean gesture/rearm/timer state; select entry guard afresh from current LS state |
| A1 | Add a timed Always On double window | Complete other entry mutations first; add that window last; never overlap another Always On window |
| A2 | Window active above Steering + W/S + Mod 2 | Keep lower stack immutable; allow proven output-only W/S and Mod 2 face outputs; block/replace every inherited mutation |
| A3 | Window timeout | Remove only that window; permitted wheel output may fire; do not restore a bank or remove an owner on timeout |
| A4 | Opposite released during window | Remove window first in same binding entry, then remove Mod 2/gesture helpers and restore current bank consumed |
| A5 | Dominant released during window | Remove window first, then clear branch and enter fallback; no inherited cleanup can run ahead of self-removal |
| A6 | Second deflection during Mod 2 double window | Remove window first, then enter repeat while keeping Mod 2 map and owner intact |
| A7 | Face used during Mod 2 window | Output-only action preserves double timing; inherited cover/cursor/selector mutations must be blocked or replaced |
| A8 | Foreign window such as RTP Double Tap already active | That window must self-exit before any steering window/layer mutation; no add-new-then-remove-old sequence |
| A9 | Lower delayed/repeating activator was pending before window entry | Verify it is cancelled or gated; an installed override alone does not prove it cannot mutate the stack later |
| A10 | Stale/missed-release or mode-shift stack exposes recovery under a window | Trace actual effective binding; block mutations or self-exit first; ordinary omitted input is not isolation |

Rows A1–A10 describe **Always On** windows: apply them to the historical
candidate, existing foreign windows, or an explicitly justified AO fallback.
Lean ordinary-input windows use S3/S10 in the implementation plan instead;
their presence does not impose AO self-first isolation on inherited owner cleanup.

## Smallest useful architecture to prototype

The [lean implementation plan](../../plans/2026-09-29-steering-implementation-plan.md) is the
current architecture authority. Its layer-title table uses `Steering | control: function`
like the Gyro family, with required separate W-owner and S-owner Modifier 2 layers. It follows the earlier
[trigger/ramp-up removal](../../plans/2026-09-27-neptune-trigger-rampup-port.md) and
[Base selector consolidation](../../plans/2026-09-27-neptune-command-budget.md): put selection
in existing inputs and inherit unchanged behavior instead of allocating a layer
for each control combination.

| Family | Added definitions | Purpose |
|---|---:|---|
| Steering + disposable guard | 2 | Persistent fallback and one-time untimed WASD |
| W/S owners | 2 | Regular movement output and release cleanup inherited by every helper |
| Mod 0/1 | 2 | Separate maps and their own Down/Up lifecycle; other direction and A/D inherited |
| Mod 2 owner variants | 2 | Required separate W-owner and S-owner lifecycles; shared output payloads |
| Normal LS Tap Cover | 1 | Shared consumed state, retained until true center |
| Up/Down Double Windows | 2 | Ordinary-input pending-single/double timing and direction memory |
| Shared Double/Repeat Cover | 1 | Repeat phase, provided direction and context remain distinguishable |
| Protected menus + silent covers | 4 | One protected entry and ordinary silent cover per menu side |
| **Target** | **16** | No new Always On actions; not a proven minimum |

W/S dominant inputs have Regular Press W/S plus Release Press removing the
whole temporary steering family. Upper layers omit those inputs so cleanup
inherits. The release preserves Steering fallback and persistent unrelated
state. No modifier map is built into either owner.

Mod 0 overrides Down and Mod 1 overrides Up; a release in the outgoing bank must
not remove the newly selected bank. Whole-input override rules still apply:
a silent cover that overrides direction also hides its selector unless that
selector is explicitly rebuilt. Source/mode settings must support the intended
A/D and opposite-direction inheritance.

Shared windows should no longer need owner identity because they contain no
Always On action: W/S owners supply release behavior below. Prototype timing on
recognized center. A directional release alone is not center. The first
completed stroke's direction must survive until pending-single/double resolution.
A shared repeat cover likewise needs original direction memory so direct reversal
cannot emit a stray tick. Keep two directional repeat helpers if one cannot do it.

Normal and Mod 2 contexts clear each other's outgoing history. Reusing a normal
consumed cover in Mod 2 must not apply Mod 0/1. Mod 2 face actions remain independent
of its gesture. Held-opposite rearm and changed-held-output suppression also
need explicit native proof before their dedicated memory can disappear.

Menu protection remains before/during entry; no new rule retrospectively cancels
already-entered Fn based on inferred provenance. Keep deliberate Fn routes.
Existing menu Double Tap Covers are not silent: reuse them in their established
double flow, not as replacements for the two new silent covers.

Fallback W retains the baseline three-entry approach: normal W, repeating
warning from 2.5 seconds, exit at 5 seconds. Validate cancellation, restart on
held-stick fallback exposure and coexistence with pad/RS/ramp/gyro mutations.
Do not turn warning pulses into layer churn that resets the exit clock.

Count all required helpers and maximum active depth. The plan explicitly allows
a justified extra helper rather than weakening true-center, rearm, timing or
held-output safeguards to force the target.

## Concrete Always On window plan

**Historical baseline / contingency only.** The lean plan replaces these new
windows with ordinary-input timing. The rules below still apply to existing
Base/menu/RTP Always On windows and to any explicitly justified AO fallback;
they do not require owner-specific windows in the lean architecture.

Follow the repository's [Always On isolation rule](../../resources/Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround)
and [inheritance review](../../resources/Steam%20Input%20JSON%20Structure.md#inheritance-review-for-binding-changes).
The reported historical crash is not claimed to reproduce on every current
client, but its ordering/isolation contract remains required here. Its rule
that normal key/mouse/movement outputs may continue is important: **a timed
window does not require disabling W/S or all Mod 2 face buttons**.

A candidate Mod 2 double window can sit above an **immutable Steering + one
W/S owner + Mod 2** stack. Those lower layers remain applied and output-only
bindings may continue. While the window exists, no other layer may be added or
removed, whether by its own input, an inherited input, a held repeat, delayed
apply, source mode shift, recovery chord, or stale upper/lower stack. A window
must explicitly block or replace those routes. A merely omitted input is not a
block, and a lower owner-held chord is not a general isolation guarantee.
Even a repeat that re-adds an already-active bank, or removes an apparently
absent helper, must be stopped here. Calling it idempotent does not exempt a
layer command from Always On isolation.

| Transition / input | Required execution order and output policy |
|---|---|
| Enter double window | Resolve normal-versus-Mod 2 gesture context and complete other entry mutations; add timed window **last** |
| Timed window remains active | Keep Steering/owner/Mod 2 applied and unchanged; output-only movement and mapped keys can remain usable |
| Window timeout | Remove **only itself**; any permitted wheel output is an ordinary output, not permission to restore banks or clean owners |
| Second deflection | Remove window **first**, then apply the appropriate repeat helper; Mod 2 repeat must keep Mod 2 mappings |
| Opposite released | Remove window **first**, then remove Mod 2/its gesture helpers, then restore current Mod 0/1 consumed or no bank |
| Dominant released | Remove window **first**, then clear driving/bank/gesture branch and establish fallback/fresh eligible W timing |
| Menu/touch/pad/edge recovery or external transition | Block unrelated mutations, or implement an explicit early exit that removes the window **first** before all remaining changes |
| Another Always On window is active | Existing window must self-exit before any new layer changes; never add a new timed window and then remove the old one |

**First means runtime execution, within the same binding entry.** Subcommand
arrays execute bottom-to-top, so a window self-removal belongs before the
other operations in execution order, not merely somewhere in the array. Keep
the three-entry limit while preserving this ordering. Timeout self-removal is
not a general allowance to remove any active helper from an Always On binding.

The active-window input audit must include both physical owner controls,
LS directions and outer edge, RS edge, face/D-pad/stick clicks, menu buttons,
stick touches, trackpad click/touch/release, modifier selector repeats, normal
tap-cover/cursor additions, global cleanup, and mode-shift targets. In
particular, a Mod 2 face button stays available only if its inherited binding
is proven output-only or is replaced by the equivalent output-only binding in
the window. It must not also add a normal cover, remove a cursor helper, or
flush a pending single. Helper-only transitions must preserve an already-held
unchanged Mod 2 output rather than replaying it.

Foreign Always On helpers such as RTP Double Tap need the same review. Do not
assume a steering helper can safely coexist with one merely because the normal
entry route does not mention it. Block a route that would create overlap, or
provide the currently active window with a self-first exit before subsequent
entry changes. Each new or reused window must also address pending lower
activators: static overrides do not prove a delayed apply or held repeat that
started earlier is cancelled. Check those transitions on a fresh Deck load,
including missed releases and plausible stale stacks.

Sharing a gesture-window definition between W and S is desirable only if it can
distinguish the correct owner, preserve the proper key map, and order every
manual exit correctly. Owner-specific cleanup discrimination, immutable-window
input replacements, and Mod 2 versus normal repeat behavior can require more
helper definitions in an AO architecture. The lean plan counts ordinary gesture
helpers in its 16 target and separately lists state that may require additions. Acceptance cases A1–A10 above make this review concrete.

## Implementation constraints and runtime questions

- Treat transitions as a logical transaction: cancel obsolete callbacks and
  output ownership, perform required removals, then establish the destination.
  Steam cannot be assumed to perform a simulator's transaction atomically.
  Arrays execute bottom-to-top; place removals/applies accordingly and test
  transient W/S exclusivity and inherited binding exposure.
- Do not generate W/S from an Always On owner while changing banks above it.
  The repository's [Always On isolation rule](../../resources/Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround)
  applies. Any reused timed Always On helper must remove itself before other
  layer mutations; add it only after its entry changes are complete.
- Immediate layer commands on already-held inputs do not fire merely because
  a layer was added. Held-input removals and key/mouse output handoff are still
  unverified. Use the [held-input contract](../../resources/Steam%20Input%20JSON%20Structure.md#held-inputs-across-layer-changes)
  to design delayed/repeating reconciliation, not as proof that every press,
  release, or timer will replay correctly.
- Reconciliation must be owner guarded and idempotent: apply only the desired
  bank, clear obsolete banks, and do nothing when the bank is already correct.
  Repeated selection must not restart a hold, recreate a consumed scroll tap,
  or resurrect a cleaned-up owner. The needed activators and command budget
  are still to be established.
- Interrupted delayed applies can require reset removals. A repeating reset
  for gesture state must not reset fallback exit timing or continuously destroy
  the currently intended bank. Verify warning cancellation and a fresh second
  attempt after every interruption path.
- Shared banks inherit from the remaining active stack; they do not inherit
  only from Base. Trace group settings, empty bindings, mode shifts, face/D-pad
  outputs, touch/click paths, A/D movement, gyro/ramp-up, and global recovery.
  Preserve useful behavior without importing Base's modifier entry or release
  side effects on steering controls.
- The [global stateful cleanup todo](../../todos.md#global-stateful-behavior) uses
  L1 + R1. In Default steering those same controls express owner + Mod 2:
  steering must mask that global chord or every Mod 2 interaction could exit.
  Recommend reserving both steering controls for this flow while Steering is
  active, including fallback tie/rearm handling. Alternative needs a role-aware
  review because its physical bumpers are different from its R2/L2 steering
  controls; its unrelated global/firing chord policy remains open.
- Alternative trigger ownership needs explicit activation/release thresholds.
  Crossing soft/full pull stages must not create two presses, duplicate Mod 2,
  or leave a partially held control permanently rearm-blocked. Apply equivalent
  neutral/hysteresis reasoning to LS direction and menu deflection.
- Every whole-state exit and any future external state transition must clear
  this family's timers, warnings, scroll repeat and owned outputs. Preserve
  unrelated stateful layers only according to their actual coexistence rules;
  coexistence with gyro/menu/gamepad is still a design question, not permission
  to globally remove them.
- Input and timer boundaries need Deck checks at 2.5 s/5 s, plus repeated
  entry/exit, same-key handoff, opposite-direction handoff, threshold jitter,
  same-sample presses/releases, held face buttons, and warning cancellation.
  Documentation/simulator checks validate the proposal's consistency only.

## Historical implementation reference

The author supplied the July
[MOST_RECENT_LAYOUT.post-fix.json](../../findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json)
as a partially implemented, partially broken reference. It was inspected
statically on 2026-09-29. The requirements above remain authoritative; the
snapshot has not been runtime-validated for this design. Its “post-fix” label
refers to the [layer-order repair](../../findings/2026-07-11-layer-order-swap/FINDINGS.md),
not to completion or repair of steering behavior.

The historical name is **Split Stick**, implemented as four layers under Base:

| Layer / preset | Relevant saved behavior | Use for this brainstorm |
|---|---|---|
| `Split Stick` / `Preset_1000055` | Switch group **383** repeatedly adds the S helper from L1 and W helper from R1. LS group **410** adds fallback from up/down with a 100 ms delay and a repeating 150 ms removal/reset | The right = W / left = S assignment matches the chosen controls. The fallback-entry delay/reset is an example to inspect, not the requested five-second exit |
| `Split Stick Fallback` / `Preset_1000056` | Active LS group **407** supplies W/S on up/down; Base supplies A/D. Switch group **390** either removes fallback or enters existing starred Mod 0/1 layers through LS-deflection-qualified chords | Useful separation of movement fallback from steering controls. The old modifier routing does not establish the new handoff when entry protection is discarded |
| `Split Stick: W Key` / `Preset_1000059` | Switch group **426** sends W through Always On, removes this helper on R1 release, and adds `*R1!L1: Modifier 2` on L1 press | Separates W ownership from the opposite control's key-access role, but does not implement the new LS Mod 0/1 gesture contract |
| `Split Stick: S Key` / `Preset_1000060` | Switch group **431** sends S through Always On, removes this helper on L1 release, and adds `*L1!R1: Modifier 2` on R1 press | Symmetric S ownership; the new gesture and cleanup contract is absent |

Useful concepts are the separate movement fallback, direction ownership, and
opposite-control access to other keybinds. Four named steering layers are not
the complete dependency count: the old design also enters existing modifier
and helper layers. This reference therefore does not prove that the requested
design fits in four layers.

The historical entry route already uses Menu Right + LS click: menu-entry
LS group **203** applies `Menu Right: Fn Layer`; that Fn layer's LS group
**253** repeatedly adds `Transition Set 1`; its switch group **356** commits
entry to `Split Stick` on **Menu Right release**. This is useful wiring to
inspect, but the release-to-commit detail is not yet a decision for the new
design, and the route does not supply the requested alternate menu flow or
protected steering entry.

Specific limits to account for before adapting any bindings:

- **Entry protection and timeout:** the four steering presets contain no
  dedicated disposable entry guard, 2.5-second repeated warning, or five-second
  fallback-W exit from steering and all its owned layers.
  Those remain new behavior to design.
- **Scrolling is unresolved in the snapshot:** both bumpers in group 383 issue
  mode shifts to LS group **408** (up/down scrolling) and **409** (up/down empty
  blocks, A/D, and other stick bindings) on the same press. Active W/S helper
  groups **441/442** also explicitly block LS up/down. These overlapping paths
  need a deliberate replacement; the presence of a scroll binding is not proof
  that it wins at runtime.
- **Saved inactive experiments:** groups **386**, **391**, **396**, and
  **402–404** retain older fallback/scroll/centering approaches. Ordinary
  inactive groups are not the active implementation. Groups marked
  `inactive modeshift` need their actual mode-shift callers traced; that marker
  alone does not establish runtime behavior.
- **Always On:** W/S helpers add Mod 2 while their own Always On output remains
  active. This conflicts with the current
  [Always On isolation rule](../../resources/Steam%20Input%20JSON%20Structure.md#always-on-layer-isolation-and-the-historical-crash-workaround).
  Reusing continuous W/S output needs a design compatible with bank changes;
  this static conflict is not a diagnosis of the author's historical breakage.
- **Command budget:** each bumper in active group 383 has four command entries
  (one layer addition and three mode shifts), exceeding today's three-entry
  limit. The old binding cannot be copied unchanged under that constraint.
- **Existing Mod 2 side effects:** groups **360/361** can remove Gyro, Split
  Stick, and fallback on bumper release, but those cleanup arrays omit the W/S
  helpers. This is a concrete reason to design steering-specific bank ownership
  and whole-family cleanup instead of assuming existing Mod 2 is a neutral
  key bank. Residual helper behavior still depends on the runtime stack.
- **Other old behavior:** W's left-trackpad click swaps to the S helper, and
  S's left-trackpad touch release removes S (groups **427/432**). These are
  historical mechanisms, not newly selected requirements.

## Remaining native checks for the lean prototype

- Menu tap-window duration and ordinary-cover behavior; both-menu combinations;
  coexistence with other stateful layers. The lean plan keeps menu-release
  commitment and limits new automatic-Fn protection to before/during entry.
- LS-only guard selection, A/D inheritance during driving, stable-neutral and
  trigger thresholds, and the proposed tie/rearm/held-mapped-input policies.
- Exact Base scroll tap/hold/double/repeat settings, whether first-tap output is
  immediate or deferred during double recognition, and corresponding feedback.
  The gesture contract is chosen; these timing/wiring details are not.
- Confirm the proposed Mod 2 tap/hold/double behavior, independent face use,
  preserved Mod 2 mappings during repeat, and center-before-fresh-deflection
  gate. Layer-based flows are allowed; native helper count and transition safety
  still need concrete binding and runtime validation.
- Warning pulse cadence/intensity and the final exit beep/vibration pattern.
  Only the 2.5-second warning start and five-second exit thresholds are fixed.
- Concrete activators, command budget, gesture/rearm/helper count, and results
  of the transition matrix on the Deck. No controller JSON/VDF is changed by
  this brainstorming revision.

Additional references: the [earlier menu split](../../plans/2026-09-27-split-menu-entry-point.md)
and [layout vocabulary](../../resources/Layout%20Vocabulary.md). Earlier plans and
historical bindings are evidence to inspect, not implementations of this contract.
