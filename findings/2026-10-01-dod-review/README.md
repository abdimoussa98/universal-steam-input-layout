# Review: Layer Definition of Done and Cleanup Functions

Reviewed 2026-10-01 against the 90.8 layouts (updated for 90.9 where the
menu overlays were removed), the two new audit tools and
today's author decisions. Goal: what must be decided or written down before
[Layer Definition of Done](../../resources/Layer%20Definition%20of%20Done.md)
(**DoD**) and [Cleanup Functions](../../resources/Cleanup%20Functions.md)
(**CF**) can be the source of truth for "a layer is done", and audited by
script. Nothing was changed in either document.

**Short version:** the DoD's mechanics are solid; §2, §3 and §9 can be checked
mechanically today, and 90.8 passes them. What blocks "source of truth" status:
- both documents are still marked draft;
- cleanup scope (DoD §7) depends on CF's four unanswered questions, so it
  can't be audited;
- some layers fit no type, and the cover-type list is a judgment call;
- §8 states two different blocking rules;
- a handful of rules have layers that break them with no recorded exception.

Evidence for the mechanical results: [dod_static_check.py](dod_static_check.py),
run on both variants (identical results).

## A. Decisions only you can make

Ordered by how much they block auditing.

### A1. Cleanup Functions' four open questions (blocks DoD §7)

Without them, no tool can say whether a cleanup removes the right layers.

| Question | What exists today | Suggested answer |
|---|---|---|
| Q1 Family membership: computed, listed, or by prefix? | The flow checker already lists families by hand in [flow_config.json](../../steam_layout/flow_config.json), but as *flows*, not as cleanup scopes | (a) list by hand, in one data file shared by the flow checker and the future cleanup generator |
| Q2 Survivors | CF has a "my guess" table for `L1: Modifier 0` | Confirm or correct the table, then state the general rule: live owners, persistent modes, stick-touch helpers, other families |
| Q3 Which inputs host cleanup functions | Ranges from 0 to 19 inputs per layer, with no rule | A rule per layer type, or "keep each layer's current host list" |
| Q4 Who removes a layer two families add | Open | The menu example is gone: `Menu Left: Backspace` and `Menu Right: Enter` were removed in 90.9, because the menu whose button is held owns the combo. That leaves the modifier covers: confirm whether `L1: Tap Cover`, which both sides apply under rocking, belongs to the side its name says or to whichever side applied it |

### A2. Layer types missing or ambiguous (DoD §1)

Seven layers fit no type in either variant. Two fit two types.

| Layer(s) | Problem | Suggestion |
|---|---|---|
| `Escape`, `Enter`, `Tab`, `Backspace` (left-pad key layers) | No type | New type "pad key layer": removed by the pad's touch release |
| `Menu Left: Escape`, `Menu Right: Tab`, and arguably `L1: Scroll Down` / `R1: Scroll Up` | "Second-press layer" exists in the §6 recipe but not in §1 (Scroll is listed as Owner) | New type "second-press layer" with its cleanup scope |
| `Steering \| LS: Entry Point` | Disposable entry guard; called "Overlay" only in my steering audit | Add it as an example under Overlay, or create a "guard" type |
| `LST/RST: Tap Cover` | Named like a cover, typed as a stick-touch helper; §5 says "the Tap Covers" are cover-type | State that these two are stick-touch helpers, not covers (the flow rules already exclude them) |
| `Gyro Off Ramp Up` | §1 calls it "Ramp or threshold"; §5 lists it as cover-type | Pick one, or say a ramp layer can also be cover-type |

### A3. A written definition of cover-type (DoD §5)

§5 says cover-type "is a judgment call". The list now exists twice: in DoD §5
and in `flow_config.json` (`covers`), where the checker treats covers
differently. Suggested definition, which the checker can test:

> only ever added directly on its owner; defines only the controls it changes
> and inherits the rest; removed by its own exit or with its owner's family.

Then keep the list in one place, and have the other point to it.

### A4. Delayed adds with no reset and no recorded exception (DoD §6)

§6 says every delayed add needs a scoped reset or a recorded exception. Three
have neither (both variants):

| Parent / input | Delay → target | Status |
|---|---|---|
| `LST: Entry Point` / LS touch | 150 ms → `LST: Tap Cover` | The [reset audit](../2026-09-28-delayed-apply-reset-audit/AUDIT.md) proposed a 200 ms reset "next", never decided |
| `RST: Entry Point` / RS touch | 150 ms → `RST: Tap Cover` | Same |
| `Gyro Off Ramp Up` / RS edge (Soft Press) | 5 ms → `Turning Ramp Up 0` | §5 explains it's a threshold handoff, but §6 doesn't list it as an exception |

`RTP: Entry Point` (150 ms, no reset) is the one documented exception.

### A5. §8 states two blocking rules

- **"When to block"**: inheritance is the default; block only while something
  must not be disturbed (Always On, pending delay, owner held, menu).
- **"How to check it"**: if any stack would put a layer command under an open
  input, block it "for its whole lifetime".

Read literally, the second rule blocks everywhere, including overlays that
should inherit their owner. The flow checker meanwhile uses a third rule:

| Situation | Flow checker's rule |
|---|---|
| Two or more distinct non-Base bindings | Recommend clear/block |
| One non-Base binding, Base on other flows | "Review" |

None of this is in the DoD. Decide:
1. Which rule is the DoD rule. Suggestion: the "When to block" table decides
   *whether* to block; the trace decides *what* (clear vs replace).
2. Whether "review" findings need action. There are 42 of them in default 90.8.
3. That `allow`/`todo` decisions (in `traced_stacks.json` and `flow_config.json`)
   are the official way to accept an exception.

### A6. Tap consumption is missing from the §6 recipe

The recipe covers hold → target and release → window → second press → cover.
It doesn't cover the **Tap Cover**: a hold past the threshold, or any mapped
action during the hold, *uses up* the tap, so the release doesn't open a
Double Tap window. The modifiers depend on this (`L1: Tap Cover`), and so does
steering (`LS: Tap Cover`). Add it as a recipe step, with its checks.

### A7. Conventions that aren't written down

Each was applied consistently by hand or by builders, but there's no rule to
audit against:

| Convention | Today |
|---|---|
| Chord form | Legacy `chord_button` (several IDs still unknown in the [chord ID table](../../resources/Neptune%20Chorded%20Button%20Ids.md)) vs modern `gyro_ratchet_button_mask` with any/all. Which for new layers? |
| `interruptable` | `0` on resets, cancels, output chords; default on guarded recoveries. Not stated as a rule |
| Haptics | `haptic_intensity: 0` on cleanup releases, 3 on warnings and holds, 1–2 on pad keys |
| Gyro twins | Modifiers have `Gyro \| …` versions, menus don't. When does a layer need one? |
| Alternative-layout mirroring | §2 says only "L1/R1 become L2/R2". The controls differ too: bumpers become trigger edges, chord IDs 1/2 become 7/8, mask bits differ. Needs a mapping table |
| Title naming | `L1: …`, `Gyro \| …`, `L1!R1` (order), `L1&R1` (both), `Steering \| control: function`. Tools rely on it (the variant regex, families by prefix) but it isn't documented |

### A8. Runtime assumptions the rules rest on

DoD's "Open questions: None" isn't accurate. These unverified behaviors shape
the rules and should be listed, each with its Deck check:

| Assumption | Used by |
|---|---|
| A removal that exposes a binding on a held input: does it fire? | §4, and the 90.8 M1 check (Select held after Backspace is removed) |
| The stuck-delay mechanism and the reset that fixes it | §6 |
| A cleared input is saved as `empty_binding` | §8 |
| Sticks inherit through the middle of the stack (2022 report says no) | §8; still in todos |
| Steam's desktop configuration drops entries after the third | §3 |

## B. Fixes to the text (no decision needed)

1. **Status lines.** DoD: "draft for author review, 2026-09-30". CF: "draft…
   proposal until confirmed". Update once A1–A5 are settled.
2. **DoD §10 Ship it** lists only the budget and inheritance audits. Add
   `audit_flow_inheritance.py` (clean on 90.8).
3. **CF "Computing a scope"** still uses `StackSpace` (deprecated for routine
   use) and its 9,471-stack example. Point it at the flow checker's per-layer
   lower stacks.
4. **CF finding F1** ("Menu Fn recovery never removes Menu Right: Enter") is
   moot since 90.9 removed both overlay layers. Done in the CF text on 2026-10-01.
5. **CF kinds table** is missing kinds that exist in the layouts:
   - stick-center exit: a repeating removal on an inverted edge (steering);
   - clear-to-Base quick exit (the Mod 2 exception in DoD §1);
   - commit and abort (Transition Set 1);
   - leaving a mode into another family (Start/Select from Steering);
   - ramp threshold exits;
   - removing an overlay with its menu's family (the new fix).

   Also, "Cancellation" says "removes only itself", but the ramp cancels on
   the bumpers remove the whole ramp family.
6. **DoD §5 exceptions list** should name the LST/RST windows' own-stick
   release. It's explained in the prose above the list, but the list is what
   an audit reads.
7. **DoD §6 reset pairs** list 150/200 to 300/350 but not steering's 5/50.
   State whether 5/50 fits the "+50 convention" or is its own case.
8. **DoD §9 "Current coverage"** is a hand-written snapshot dated 2026-09-30.
   Replace it with "run the audit", or regenerate it.

## C. Making it auditable and faster to build with

1. **One rule → check map.** Today:

   | DoD section | Checked by | Gap |
   |---|---|---|
   | §1 type | nothing | needs A2, plus per-layer type data |
   | §2 placement | apply-skill pre-flight, budget audit | none |
   | §3 activators | `audit_command_budget.py` | none |
   | §4 entry over held input | nothing mechanical | hard to check statically; Deck only |
   | §5 touch release | steering tests only; the 2026-09-30 check was one-off | make the static check permanent |
   | §6 resets / recipe | steering tests only | make the static check permanent (A4) |
   | §7 cleanup scope | nothing | needs A1 |
   | §8 blocking | `audit_inheritance.py` (windows), `audit_flow_inheritance.py` (all layers) | the rule itself (A5) |
   | §9 Always On order | blocking audit, flow checker | none (90.8 passes) |

2. **A per-layer "card" as data.** Every layer gets: type, family/owner,
   entries, exits, timers with resets, touch behavior, what it blocks, and
   exceptions with reasons. Families and covers already live in
   `flow_config.json`; extending that file (or a sibling `layers.json`) gives:
   - one place to answer A1–A3;
   - the cleanup generator's input;
   - a checklist for a new layer: fill in its card, then the audits compare
     the bindings against it.

3. **One `audit_layer_dod.py`** that runs every mechanical check above per
   layer and reports by DoD section. The review script here is a starting
   point.

## Verified passing on 90.8 (both variants)

- §2: list order matches `Preset_` order, preset blocks and IDs are
  consistent, no duplicate titles, no unresolved tokens.
- §3: budget audit passes; no banned activators.
- §5: every non-cover layer binds both stick-touch releases, except the
  documented LST/RST window case.
- §6: every delayed add has a scoped, longer reset, except the four in A4.
- §8/§9: `audit_inheritance.py` and `audit_flow_inheritance.py` are clean; Always On
  windows are added last and remove themselves first everywhere.
