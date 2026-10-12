"""Decision 3, replayed: menu layers left on by a release missed in the Steam menu, and what clears them.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/menu_stale.py

In memory only, on the layouts as they are ("today") and on cover_timer.py's "no cover" version (decisions
1, 2 and 4: the second driver's Release removes the Modifier 2 layer and nothing else).

The start of every run: in `Steering`, Start held, the left stick pushed left for 300 ms, then the Steam
menu, where Start and the stick are let go unseen (A25). `Stateful | Menu Right: Entry Point`,
`Menu Buttons: Left Stick Guard` and `Menu Buttons: Tap Cover` are left on. Then one more gesture, and
which layers are still on above `Steering`. Both layouts, both ways of A9.
"""
import scenario
from scenario import Pad
import first_driver as base
import cover_timer as cover

GESTURES = {
    "nothing": lambda p: p,
    "touch the left stick": lambda p: p.touch("LS").wait(300).lift("LS").wait(300),
    "touch the right stick": lambda p: p.touch("RS").wait(300).lift("RS").wait(300),
    "tap Start": lambda p: p.tap("Start").wait(400),
    "tap Select": lambda p: p.tap("Select").wait(400),
    "tap A": lambda p: p.tap("A").wait(300),
    "tap R1": lambda p: p.tap("R1").wait(300),
    "hold R1, tap L1, let go of R1": lambda p: p.hold("R1").wait(300).hold("L1").wait(60).let_go("L1").wait(100).let_go("R1").wait(300),
    "the same with a thumb resting on the left stick": lambda p: p.hold("R1").wait(300).touch("LS").wait(300).hold("L1").wait(60)
    .let_go("L1").wait(100).let_go("R1").wait(300).lift("LS").wait(300),
}


def stale(variant, data, exposed):
    pad = base.steering(Pad(variant, data=data, exposed_fires=exposed))
    pad.hold("Start").wait(50).push("LS", "left").wait(300)
    return pad.miss("Start", "LS dpad_west", "LS edge", "LS touch").wait(500)


def main():
    for version in ("today", "no cover"):
        print(f"\n{version}")
        for name, gesture in GESTURES.items():
            seen = set()
            for variant in scenario.VARIANTS:
                data = scenario.layout_data(variant) if version == "today" else cover.build(variant, version)
                for exposed in (True, False):
                    pad = gesture(stale(variant, data, exposed))
                    seen.add(", ".join(t for t in pad.names()[2:] if t.startswith(("Menu", "Stateful"))) or "nothing")
            print(f"  {name}: left on: {' | '.join(sorted(seen))}")


if __name__ == "__main__":
    main()
