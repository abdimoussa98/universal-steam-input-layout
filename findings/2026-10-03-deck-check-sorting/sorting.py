#!/usr/bin/env python3
"""The sorting and the migration of the 137 Deck checks (rule registry plan, phases 11 and 14), as data.

`SORT[(section, check ID)] = (what it becomes, detail)`, and once a check has been
migrated, `WENT[(section, check ID)]` says where it went: the scenario or static
test that replaced it, the assumption it joined, a tuning note, or what made it
obsolete. checks.json holds the original wording of every check, frozen on
2026-10-03, so the record survives the checklist.

    python3 findings/2026-10-03-deck-check-sorting/sorting.py          # rewrite the table in README.md
    python3 findings/2026-10-03-deck-check-sorting/sorting.py --check  # fail if the record and the checklist disagree
"""
from collections import Counter
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KINDS = ("Scenario", "Static", "Assumption", "Tuning", "Obsolete")
S, T, A, U, O = KINDS

SORT = {
    # 90.13: no turn assist in Steering
    ("90.13", "N1"): (S, "St, Gyro: the right-stick edge adds no ramp layer in Steering; the gyro source isn't disabled"),
    ("90.13", "N2"): (S, "B, Tr, St, K: the driver's Release still reaches its layer; no W left down"),
    ("90.13", "N3"): (S, "St, T, Tr, K: a trigger pull inside a Steering window clicks"),
    ("90.13", "N4"): (S, "St, T, Gyro: outside Steering the ramp layers still come and go (same as TR3)"),
    # 90.12: cleanup lists
    ("90.12", "C1"): (S, "B, Miss, St: a stick touch clears a stuck Modifier 2"),
    ("90.12", "C2"): (S, "B, St: with either bumper held, a stick touch clears nothing"),
    ("90.12", "C3"): (S, "B, T, Miss, St: one edge push clears a stuck cursor and its modifier"),
    ("90.12", "C4"): (S, "B, Miss, St: Steering Modifier 2 with one bumper still held"),
    ("90.12", "C5"): (S, "B, T: the rocking sequence; test_modifier_rocking.py already replays it with walk"),
    ("90.12", "C6"): (S, "B, T, K: double tap scrolls, a used bumper doesn't, the quick tap toggles Gyro"),
    ("90.12", "C7"): (S, "B, Miss, St: a stuck modifier, Fn layer and Steering driver each clear"),
    ("90.12", "C8"): (S, "B, St, T, K: the menu hold with a stick guard, and the Fn release"),
    # 90.11: Steering fallback hold
    ("90.11", "F1"): (S, "St, T, Hap: rolling to A or D removes the Fallback Hold, so no exit and no pulse"),
    ("90.11", "F2"): (S, "St, T, K, Hap: W, the pulse, and the exit with its beep at 1.5 s. The pulse strength is a tuning note"),
    ("90.11", "F3"): (S, "St, T: the exit counts from the second push"),
    ("90.11", "F4"): (A, "A16: does a delay's clock start when its layer is added"),
    ("90.11", "F5"): (S, "St, T, K: a diagonal holds two directions"),
    ("90.11", "F6"): (S, "B, St, T: a driver press removes the hold. Whether W returns after the driver's release rests on A11"),
    ("90.11", "F7"): (S, "St, T: the Entry Guard, entered with the stick centred or already up. The second rests on A8"),
    ("90.11", "F8"): (S, "B, St, T, K: a Start tap types Tab and adds nothing over the hold"),
    ("90.11", "F9"): (S, "Desk: F1 and F2 again on the layout with every entry past the third dropped. Rests on A21"),
    ("90.11", "F10"): (S, "B, St, T, K: the menu Entry Point types W on stick up and adds no hold"),
    ("90.11", "F11"): (S, "B, St, T, K: Start and Select type their keys in the Entry Guard"),
    # 90.10: stateful transitions
    ("90.10", "G1"): (A, "A26: do stick inputs inherit through the middle of the stack"),
    ("90.10", "G2"): (A, "A26: the same shape, with the Fn layer over the Entry Point"),
    ("90.10", "G3"): (A, "A8: a stick edge's Release in a layer added with the stick already out. Its last branch is A14"),
    ("90.10", "G4"): (A, "A15: a guard that lands inside the Fn delay cancels it"),
    ("90.10", "G5"): (S, "B, St, T, K: a Start tap with a stick out types one Tab"),
    ("90.10", "G6"): (A, "A14: a delay starts again when a removal exposes it"),
    ("90.10", "T1"): (S, "B, St, K, Hap: the four gestures from Base and from Gyro, with the beep and pulse"),
    ("90.10", "T2"): (S, "B, St, Hap: the four gestures clear Steering and keep Gyro"),
    ("90.10", "T3"): (S, "B, St: letting go of the menu button first cancels"),
    ("90.10", "T4"): (S, "B, St, Miss: a transition left by a missed release ends on the next menu tap"),
    ("90.10", "T5"): (S, "B, St, T, K: guards on and off; rests on A8"),
    ("90.10", "T6"): (S, "B, St, Miss: a stick touch clears a stale guard"),
    ("90.10", "T7"): (S, "B, St, T, K: the accepted gap under the menu Tap Cover"),
    ("90.10", "T8"): (S, "B, T, K: one Backspace before Fn is up; rests on A10"),
    ("90.10", "T9"): (S, "B, St, K: the right stick types nothing while a menu button is held"),
    ("90.10", "T10"): (S, "B, St, Tr, T, K: mouse buttons through a window. Whether a held click is interrupted rests on A11"),
    ("90.10", "D1"): (S, "B, T, K: menu buttons in Steering, with and without a driver"),
    ("90.10", "D2"): (O, "Replaced by 90.11 F1 to F5"),
    ("90.10", "D3"): (S, "B, St, T: the stick modifier holds through a roll to the side"),
    ("90.10", "D4"): (S, "B, St, T, K: stick first, then the driver; rests on A8"),
    ("90.10", "D5"): (S, "B, St, T, K: the stick double tap and its window"),
    ("90.10", "D6"): (S, "B, St, T, K: W and S through the window; rests on A10 and A11"),
    ("90.10", "D7"): (S, "B, St, T, K: the other driver inside the window"),
    ("90.10", "D8"): (S, "B, St, Miss, K: a mapped button uses up the tap; a stuck modifier map clears"),
    ("90.10", "D9"): (S, "The same sequence as 90.11 F7, first half"),
    # 90.9: Enter / Backspace typed by the menu chords
    ("90.9", "K1"): (O, "Replaced by 90.10 T8"),
    ("90.9", "K2"): (S, "B, T, K: Backspace on every press with Fn up, repeating"),
    ("90.9", "K3"): (S, "B, T, K: the accepted stray Escape when the first button is lifted first"),
    ("90.9", "K4"): (S, "B, K: a held Fn key falls through to Base (R138)"),
    ("90.9", "K5"): (T, "Every layer command resolves to a layer after the ID shift: test_fixes already checks it. The fresh load is A33"),
    ("90.9", "M5"): (S, "Pad, T: the right-pad double tap and Circular Scroll"),
    # 90.7: slim steering overlays
    ("90.7", "S1"): (S, "B, St, T, K: a face button inside the stick window"),
    ("90.7", "S2"): (S, "St, T, K: flick, then flick and hold repeats the scroll"),
    ("90.7", "S3"): (S, "B, St, T: lifting the thumb during a stick modifier"),
    ("90.7", "S4"): (S, "B, St, Miss: the driver's recovery through the cover"),
    ("90.7", "S5"): (O, "The protected menu layers were replaced by the stick guards in 90.10 (T5)"),
    ("90.7", "S6"): (S, "Pad, St: no RTP touch mode starts while steering"),
    ("90.7", "S7"): (O, "Turn assist is off in Steering since 90.13 (N1)"),
    ("90.7", "S8"): (O, "Replaced by 90.10 D5"),
    # 90.6: chorded delays and dead-group prune
    ("90.6", "D1"): (T, "The prune removes only dead groups: test_layout_hygiene. Loading without error is A33"),
    ("90.6", "D2/D3"): (T, "RTP: Mouse Buttons' wheel bindings: test_layout_hygiene. The layer is added by hold_layer, which isn't simulated"),
    ("90.6", "D4/D5"): (T, "The prune kept every mode-shift target: test_layout_hygiene and the fix pipeline's fixed point"),
    ("90.6", "C1"): (O, "Replaced by 90.11 F1 to F9. Its pulse timing is a tuning note on F2"),
    ("90.6", "C2"): (S, "The same sequence as 90.11 F7, second half"),
    ("90.6", "C3"): (O, "Replaced by 90.10 D5: the window is an Always On layer now"),
    ("90.6", "C4/C5/S7"): (S, "B, St, T, K: the hold uses up the tap; no scroll at centre after a takeover"),
    ("90.6", "R1"): (S, "B, T, K: double-tap and hold, then a clean release through the cover"),
    ("90.6", "R2"): (A, "A12: the reset restarts an interrupted delay. That each delayed add has its reset is R120"),
    ("90.6", "R3"): (A, "A21: the desktop configuration drops the 4th entry. The reset being last is checked by the Budget audit"),
    ("90.6", "T1"): (O, "The transitions were rebuilt in 90.10 with no stick-touch recovery (T4). The merged chord in the editor is A30"),
    ("90.6", "P1"): (T, "The pads' bindings in every window: test_double_tap_windows. The swipe feel is a tuning note"),
    ("90.6", "B1"): (T, "RTP Double Tap's back buttons and selection: test_double_tap_windows. The trigger part was replaced by 90.10 T10"),
    # Menu buttons
    ("Menu buttons", "MB1"): (S, "B, T, K: a tap types Escape or Tab"),
    ("Menu buttons", "MB2"): (S, "B, T, K: the Fn hold (200 ms since 90.10, not 300) and its silent release"),
    ("Menu buttons", "MB3"): (A, "A12: the reset restarts an interrupted hold"),
    ("Menu buttons", "MB4"): (S, "B, T, K: Enter and Backspace, quickly and with Fn up (same keys as 90.10 T8 and 90.9 K2)"),
    ("Menu buttons", "MB5"): (S, "B, T, K: double tap and hold repeats the key. How many keys a quick double tap sends is a tuning note"),
    ("Menu buttons", "MB6"): (S, "B, St, K: the stick click enters a transition; stick directions type punctuation"),
    ("Menu buttons", "MB7"): (U, "The Fn directions' haptic feel"),
    ("Menu buttons", "MB8"): (S, "B, St, T, K: a thumb lift completes the Fn hold (R123)"),
    ("Menu buttons", "MB9"): (S, "B, St, Miss: a stuck Fn layer clears on the next input"),
    ("Menu buttons", "MB10"): (S, "B, Miss: a stuck Entry Point clears on the other menu button"),
    # Modifier layers
    ("Modifier layers", "ML1"): (S, "B, K: the nav keys in each modifier"),
    ("Modifier layers", "ML2"): (S, "B, K: the same in Gyro"),
    ("Modifier layers", "ML3"): (S, "B, Gyro: Start or Select in a modifier leaves the gyro source alone. Whether that is wanted is a question for the author"),
    ("Modifier layers", "ML4"): (S, "B, T, K: no tap or scroll after a nav chord"),
    # Temp cursor gyro
    ("Temp cursor gyro", "TC1"): (S, "B, T: the cursor lands at 300 ms; its settings are checked by test_neptune_cursor"),
    ("Temp cursor gyro", "TC2"): (U, "The entry pulse's feel; its setting is checked by test_neptune_cursor"),
    ("Temp cursor gyro", "TC3"): (S, "B, St, T: a thumb lift enters the cursor early (R123)"),
    ("Temp cursor gyro", "TC4"): (S, "B, T, K: every cancel input before, at and after 300 ms; rests on A9 and A11"),
    ("Temp cursor gyro", "TC5"): (T, "The two chords and the recovery on each input: test_neptune_cursor. Their order is A32"),
    ("Temp cursor gyro", "TC6"): (S, "B, St, T: a cancel input and a thumb lift together; run in both orders (A32)"),
    ("Temp cursor gyro", "TC7"): (T, "The three entries on each stick edge: test_neptune_cursor and test_neptune_recovery"),
    ("Temp cursor gyro", "TC8"): (S, "B, St: one stick keeps the cursor, both remove it. The physical thresholds are a tuning note"),
    ("Temp cursor gyro", "TC9"): (S, "B, St, Miss: a lost modifier clears its family with the sticks out"),
    ("Temp cursor gyro", "TC10"): (S, "B, Tr, T: both Modifier 2 orders and release orders"),
    ("Temp cursor gyro", "TC11"): (S, "Tr, H: the alternative's repeating Modifier 2 entry over a held trigger (A6)"),
    ("Temp cursor gyro", "TC12"): (S, "B, T: a fresh hold is eligible again; the reset part is A12"),
    ("Temp cursor gyro", "TC13"): (T, "Exactly three entries on each cursor-entry input: test_neptune_cursor"),
    ("Temp cursor gyro", "TC14"): (S, "B, T: no repeated removal after the cursor or a cover has landed (R122)"),
    ("Temp cursor gyro", "TC15"): (T, "Window isolation and ordering: the Window audit and test_neptune_recovery"),
    ("Temp cursor gyro", "TC16"): (T, "RTP Double Tap's blocks: test_neptune_cursor"),
    ("Temp cursor gyro", "TC17"): (A, "A13 and A28: a removal during RTP Entry's delay, and trackball momentum"),
    ("Temp cursor gyro", "TC18"): (A, "A34: do the trackpad's inactive mode-shift targets take effect"),
    # Reference gyro and right-stick tuning
    ("Reference gyro and right-stick tuning", "RG1"): (T, "Base's gyro settings: test_neptune_gyro. The feel is a tuning note"),
    ("Reference gyro and right-stick tuning", "RG2"): (T, "The cursor's and the covers' gyro settings: test_neptune_gyro and test_neptune_cursor. The feel is a tuning note"),
    ("Reference gyro and right-stick tuning", "RG3"): (T, "The right stick's and the ramp stages' settings: test_neptune_gyro. The feel is a tuning note"),
    # Triggers and ramp-up
    ("Triggers and ramp-up", "TR1"): (S, "B, Tr, K: the triggers click; a menu button works with a trigger held"),
    ("Triggers and ramp-up", "TR2"): (T, "Three entries and Any chords on Base's right-stick edge: the Budget audit. What the editor shows is A30"),
    ("Triggers and ramp-up", "TR3"): (S, "St, T, Gyro: the two ramp stages and the way back"),
    ("Triggers and ramp-up", "TR4"): (S, "St, Tr, T, Gyro: a held trigger keeps the gyro on"),
    ("Triggers and ramp-up", "TR5"): (S, "St, Tr, T, K: a pull brings the gyro back. The first click registering is A11"),
    ("Triggers and ramp-up", "TR6"): (S, "B, St, T: a held modifier lets no ramp layer in"),
    ("Triggers and ramp-up", "TR7"): (S, "B, St, T, H: a modifier pressed during ramp-up ends it"),
    ("Triggers and ramp-up", "TR8"): (S, "The same three in Gyro"),
    ("Triggers and ramp-up", "TR9"): (A, "A12: the 300 ms reset restarts the interrupted stage change"),
    ("Triggers and ramp-up", "TR10"): (S, "B, Pad, St: a stuck right pad doesn't block the edge. Trackball momentum is A28"),
    ("Triggers and ramp-up", "TR11"): (S, "B, T: the two-bumper quick tap, and the cover after 200 ms"),
    ("Triggers and ramp-up", "TR12"): (T, "No haptic setting on the right-stick edge entries"),
    # Default trigger reference match
    ("Default trigger reference match", "DT1"): (T, "Base's trigger settings and mouse outputs against the July reference"),
    ("Default trigger reference match", "DT2"): (S, "Tr, St, T, K: pulls in Base, Gyro and both ramp stages"),
    ("Default trigger reference match", "DT3"): (T, "The windows' trigger bindings: test_double_tap_windows and the Window audit"),
    # Left-stick recovery and Transition Sets
    ("Left-stick recovery and Transition Sets", "LR1"): (S, "B, St, Miss: the left-edge cleanup functions. The Transition Set part was replaced in 90.10"),
    # WASD modifier scaffold
    ("WASD modifier scaffold", "WM1"): (T, "Base's left-stick edge entry and its settings"),
    ("WASD modifier scaffold", "WM2"): (U, "The modifier's regions with a key assigned"),
    ("WASD modifier scaffold", "WM3"): (S, "St: which stacks leave Base's left-stick edge exposed"),
    ("WASD modifier scaffold", "WM4"): (T, "The layers that bind the left-stick edge: test_neptune_recovery"),
    ("WASD modifier scaffold", "WM5"): (A, "A11: an output exposed or hidden under a stick that is already out"),
    # Missed releases and cleanup scope
    ("Missed releases and cleanup scope", "MR1"): (S, "B, St, Miss: what each cleanup function clears and leaves; the Cleanup audit checks the lists"),
    ("Missed releases and cleanup scope", "MR2"): (T, "Both Modifier 2 orders are never on the stack together: the Cleanup audit's \"never there\". Its counts are from before 90.12"),
    # Held inputs across layer changes
    ("Held inputs across layer changes", "HI1"): (O, "The stick click is a Release in the Entry Point since 90.10 (G2, T1)"),
    ("Held inputs across layer changes", "HI2"): (S, "B, T, H: the staggered Gyro toggle. What appears after the removal rests on A9"),
    ("Held inputs across layer changes", "HI3"): (S, "Tr, St, H, T: the alternative's Modifier 2 entry without re-pulling (same as TC11)"),
    ("Held inputs across layer changes", "HI4"): (A, "A10 and A11: outputs when a layer is added and when a removal exposes them"),
}


# Where each migrated check went (phase 14). Filled one checklist section at a time.
SCENARIOS_90_11 = "`tests/test_scenarios_90_11.py`"
WENT = {
    ("90.13", "N1"): SCENARIOS_90_11, ("90.13", "N2"): SCENARIOS_90_11, ("90.13", "N3"): SCENARIOS_90_11,
    ("90.13", "N4"): SCENARIOS_90_11,
    **{("90.11", check): SCENARIOS_90_11 for check in ("F1", "F2", "F3", "F5", "F6", "F7", "F8", "F9", "F10", "F11")},
    ("90.11", "F4"): "A16: it is that assumption's Deck procedure",
    **{("90.12", f"C{n}"): "`tests/test_scenarios_90_12.py`" for n in range(1, 9)},
    **{("90.10", check): "`tests/test_scenarios_90_10.py`" for check in
       ("G5", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "D1", "D3", "D4", "D5", "D6", "D7", "D8")},
    ("90.10", "G1"): "A26: it is that assumption's Deck procedure",
    ("90.10", "G2"): "A26: the same question with the Fn layer on top",
    ("90.10", "G3"): "A8: it is that assumption's Deck procedure; its last branch is A14",
    ("90.10", "G4"): "A15: it is that assumption's Deck procedure",
    ("90.10", "G6"): "A14: it is that assumption's Deck procedure",
    ("90.10", "D2"): "Obsolete: replaced by 90.11 F1 to F5",
    ("90.10", "D9"): "Same as 90.11 F7",
    **{("90.9", check): "`tests/test_scenarios_90_6_to_90_9.py`" for check in ("K2", "K3", "K4", "M5")},
    ("90.9", "K1"): "Obsolete: replaced by 90.10 T8",
    ("90.9", "K5"): "`test_fixes.test_overlays_are_gone_and_nothing_references_them`; the fresh load is A33",
}


def checks():
    """[(section, check ID, text)]: every check as it was worded, from checks.json."""
    frozen = json.loads((HERE / "checks.json").read_text(encoding="utf-8"))
    return [(c["section"], c["id"], c["text"]) for c in frozen]


def remaining():
    """{(section, check ID)} still in manual-testing.md, if the file is still there."""
    path, found, section = ROOT / "manual-testing.md", set(), None
    if not path.exists():
        return found
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = re.sub(r":.*", "", line[3:]).strip()
        match = re.match(r"- \[.\] ([A-Z]+[0-9]+(?:/[A-Z]+[0-9]+)*)\b", line)
        if match:
            found.add((section, match.group(1)))
    return found


def table(rows):
    out = ["| Section | Check | It says | Becomes | Notes | Went to |", "|---|---|---|---|---|---|"]
    for section, check, text in rows:
        kind, detail = SORT[(section, check)]
        words = re.sub(r"\s+", " ", re.sub(r"[`*\[\]|]", "", text))
        out.append(f"| {section} | {check} | {words[:70].rstrip()}{'…' if len(words) > 70 else ''} | {kind} | {detail} "
                   f"| {WENT.get((section, check), 'Not migrated yet')} |")
    return "\n".join(out)


def main():
    rows = checks()
    keys = [(section, check) for section, check, _ in rows]
    problems = [f"not sorted: {k}" for k in keys if k not in SORT] + [f"no such check: {k}" for k in SORT if k not in keys]
    problems += [f"listed twice: {k}" for k, n in Counter(keys).items() if n > 1]
    left = remaining()
    problems += [f"migrated, but still in manual-testing.md: {k}" for k in WENT if k in left]
    problems += [f"not migrated, and gone from manual-testing.md: {k}" for k in keys if k not in WENT and k not in left]
    problems += [f"went somewhere, but was never sorted: {k}" for k in WENT if k not in SORT]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    counts = Counter(SORT[k][0] for k in keys)
    print(f"{len(keys)} checks: " + ", ".join(f"{counts[kind]} {kind.lower()}" for kind in KINDS)
          + f"; {len(WENT)} migrated, {len(keys) - len(WENT)} still in manual-testing.md")
    if "--check" not in sys.argv:
        readme = HERE / "README.md"
        text = readme.read_text(encoding="utf-8")
        start, end = "<!-- table:start -->", "<!-- table:end -->"
        text = text[:text.index(start) + len(start)] + "\n" + table(rows) + "\n" + text[text.index(end):]
        readme.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
