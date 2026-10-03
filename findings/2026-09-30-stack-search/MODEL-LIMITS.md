# What the stack proofs establish

Follow-up: [online documentation and reports](ONLINE-EVIDENCE.md) establish
several basic rules and narrow the remaining hardware checks. They do not
yet supply a complete runtime specification.

The search engines and invariant checker analyze `HeldModel`, an untimed
transition system. A witnessed fact is reachable in that model. An inductive
exclusion holds for all of its finite event sequences, without a search-depth
cap. Neither result establishes the corresponding claim about Steam runtime
behavior. Agreement between the Python, C++, and symbolic implementations
checks their consistency; it does not supply independent hardware evidence.

The distinction matters because the current model can both add behaviors and
omit behaviors. It has not been established as either an upper or a lower
bound on Steam. Consequently, model witnesses alone do not prove hardware
reachability, and model exclusions alone do not prove hardware impossibility.
The findings below describe code behavior reproduced on 2026-09-30. They are
not claims that the corresponding hardware experiments have been completed.

## Project scope clarification (2026-09-30)

The author prohibits `hold_layer` and action-set switching; held interactions
must use explicit adds/removals. Overridden hold bindings and competing Steam
hold owners are therefore not questions for the intended design. Five legacy
`hold_layer` commands remain in each current variant, so their model limitation
still affects analysis of those files until migration. See
[runtime rules](../../resources/Layout%20Vocabulary.md#runtime-rules-author-confirmed-2026-09-30).
The author also confirms that the discussed removal resets the timer: restart
and wait 300 ms, not cancellation. The current Boolean-delay model cannot
represent that observation.

The separate [timed runtime](TIMED-MODEL.md) now implements numeric delays,
restart/repeat scheduling, mode-shift lifetimes and analog eligibility for
explicit event traces. A resumable exhaustive search now explores a finite
quotient of that runtime, with independent witness and closure verification.
It retains explicit policies for unsettled interactions.
The omissions below still apply to `HeldModel`, the C++ engines and their
symbolic proofs; the new simulator does not retroactively repair that evidence.

## Reproduced gaps

| Area | Current behavior and consequence | Code |
|---|---|---|
| Delays and repeats | Every nonzero delay becomes one Boolean. A hold event fires all eligible delayed/repeating entries together; numeric delay order and intervening button events are lost. Delay-only entries can fire again on later hold events. | [`HeldModel._entry`, lines 169–176](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L169), [`_selected`, lines 223–242](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L223), [`fire`, lines 249–262](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L249) |
| Analog thresholds | `activation_threshold` and `edge_binding_invert` are not represented. Inverted and non-inverted Soft Press entries use the same press/hold selection rules. | [`_entry`, line 169](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L169) |
| Mode shifts | A shifted input is retained only if it already occurs in the ordinary input universe. A control with only a mode-shift command is not necessarily tracked as held. Shift activity is recomputed from the held control's current binding, and shifted inputs are modeled as whole taps. | [`SearchModel.__init__`, line 25](../../archived/exhaustive-stack-search/steam_layout/search_model.py#L25), [`HeldModel.__init__`, lines 102–135](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L102), [`shifted`, line 265](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L265), [`successors`, line 299](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L299) |
| Hold ownership | Every `hold_layer` target appearing anywhere on a control is removed when that control releases, whether that hold command actually fired or another control owns a hold. The state contains no active hold-ownership record. | [`HeldModel.__init__`, lines 123–131](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L123), [`fire`, lines 260–261](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L260) |
| Unsupported activators and chords | An unknown activator kind defaults to Regular Press. An unknown chord condition is treated as satisfied when firing, but unsatisfied when deciding whether it blocks Regular Press. That is a fixed combined behavior, not a branch over both possible chord conditions. | [`_entry`, line 171](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L171), [`satisfied`, lines 179–187](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L179) |
| Concurrent entries | All entry orders are considered only when at most three entries have layer operations. With more than three, only their serialized order is considered. | [`fire`, line 255](../../archived/exhaustive-stack-search/steam_layout/held_model.py#L255), [matching C++ rule](../../archived/exhaustive-stack-search/tools/stack_search/rules.hpp#L325) |

The default layout is affected by the analog omission: it has inverted
Soft Press cleanup entries in `Gyro Off Ramp Up`, `Turning Ramp Up 0`,
`Turning Ramp Up 1`, `LTP: Arrow Keys`, and `RTP: Mouse Buttons`. It also has
six referenced mode-shift groups and one unknown chord-condition key shared
by two entries. Its active bindings do not currently have more than three
layer-changing entries, and their activator kinds are all in the model's
recognized set. Those last two gaps matter when the layout is extended.

### Tiny delay example

Suppose one held button has two independent Regular Press entries:

```text
100 ms: add Early
500 ms: add Late
```

The ordinary intended timing interpretation includes `Base, Early` between
the two deadlines. Exhaustive `HeldModel` search instead produces these
distinct stacks:

```text
Base
Base, Early, Late
Base, Late, Early
```

It never produces `Base, Early`: both delayed entries run in the same hold
event, in either order. This is why removing concrete time cannot presently
be described as a conservative approximation. This small reproducer uses
the existing test fixture helpers and performs no hardware experiment:

```bash
PYTHONPATH=tests python3 - <<'PY'
from test_audit_inheritance import build, add
from steam_layout.model import Layout
from steam_layout.held_model import HeldModel, explore

entries = [
    {"bindings": {"binding": add(name)}, "settings": {"delay_start": delay}}
    for name, delay in (("Early", "100"), ("Late", "500"))
]
data = build({
    "Base": {"switch": ("switches", {"left_bumper": {"Full_Press": entries}})},
    "Early": {}, "Late": {},
})
model = HeldModel(Layout(data))
for stack in sorted({model.names_of(state[0]) for state in explore(model)}):
    print(", ".join(stack))
PY
```

Two other minimal reproductions are useful regression cases:

- Give Base's LB only `mode_shift joystick 90`; put north's `add H` only in
  group 90. The current model omits north from its control universe, does not
  hold LB, and never reaches H.
- Give RB `hold_layer H` only in an inactive layer. Add H through an ordinary
  Base command and press/release Base's unrelated RB binding. The current
  model removes H on RB release even though that hold command never fired.

## Interpreting inheritance and witnesses

A known stack determines the model's **binding owner and serialized
activators**, using its per-input lookup and disabled-source rule. It does
not determine which chord or timed entry actually fires, nor active mode
shifts; those require additional state. Source-mode changes also need a
runtime contract beyond per-input lookup; the existing inheritance audit
already treats some of those cases as `mode_replaced`.

The layer report examines bindings below X whenever X is present, including
stacks with layers above X. This answers what X can inherit structurally.
A layer above X may still override the effective input for the whole stack.
The report does not assert that the listed lower command fires at that
moment. A disabled source below X and an entirely unbound input are distinct
results.

Evidence requires an ordinary held search with missed releases disabled,
matching exported `model.txt` bytes, and present state artifacts. This
rejects many stale-layout and incompatible-search mistakes. Every witness
retained for a reported fact is then replayed from Base through the current
`HeldModel.successors`, and its final stack must match its `stacks.tsv` row.
Common verified prefixes are reused. An invalid event or ancestor prevents
the fact from being reported. Explicit witness retrieval also requires this
replay; sampled candidate seeds do not, because induction independently
checks every surviving candidate.

Existing searches do not record a transition-semantics version or
implementation hash. Replay supplies the current-model certificate for
retained positive facts even when a semantics-only implementation change
leaves the export unchanged. Versioning and regenerating searches would
still reject outdated files earlier and improve the usefulness of candidate
seeds. The replay establishes no additional correspondence to hardware.

`possible` means the current inductive facts did not exclude a relation.
It includes solver timeouts and does not mean a witness exists.
`complete_for_model` concerns the report's finite relation/value questions,
not a complete enumeration of stacks or proof of Steam behavior. The
candidate vocabulary may be too weak to settle true facts. Runtime and
remaining uncertainty must be measured on the actual layout; the Houdini
method does not itself guarantee a fast or complete answer.

## Work needed for Steam-level claims

1. Specify and test the runtime event contract: timer origins and deadlines,
   repeats, release selection after a layer change, simultaneous entries,
   mode-shift activation and analog thresholds. Migrate the remaining forbidden
   hold commands instead of specifying competing Steam hold owners.
   Record Deck observations separately from assumed rules.
2. Extend the state and transitions to retain the distinctions that affect
   these observations. Timers need a justified finite abstraction or another
   timed verification method; changing positive delays into booleans is
   insufficient. Include shifted-only controls and explicit layer-lifetime behavior.
3. Keep regression cases for each omission, and check both directions of
   correspondence where claiming exactness. If using a conservative upper
   bound instead, establish that every admitted hardware transition is
   covered before interpreting an exclusion as a hardware guarantee.
4. Version the transition semantics in exported searches and regenerate old
   evidence. Preserve current-model replay of every retained fact witness;
   add hardware replay for claims intended to establish real reachability.
5. Measure the default layout's proof run and report unresolved facts. Add
   stronger invariant templates where counterexamples show they are needed;
   a completed fixed point is not a promise that all real questions close.
