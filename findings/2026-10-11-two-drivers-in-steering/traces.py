"""The reported two-driver gestures in `Steering`, press by press, on the press simulator.

    PYTHONPATH=.:tests python3 findings/2026-10-11-two-drivers-in-steering/traces.py [variant] [layout.json]

Without a layout file it reads the working layout.
"""
import json
import sys

from scenario import Pad

SHOWN = ("press", "release", "add", "remove", "down", "up", "handover", "tap", "beep")
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "default"
DATA = None
if len(sys.argv) > 2:
    with open(sys.argv[2], encoding="utf-8") as handle:
        DATA = json.load(handle)


def start():
    pad = Pad(VARIANT, data=DATA)
    pad.enter_steering().lift("LS").wait(300)
    return pad


def show(title, pad, since):
    print(f"\n{title}")
    start_ms, last, ticks = pad.sim.log[since][0], None, 0
    for ms, what, detail in pad.sim.log[since:]:
        if what not in SHOWN:
            continue
        if what == "tap":
            ticks += 1
            if last == (what, detail):                       # one line per run of wheel steps
                continue
        last = (what, detail)
        print(f"  {ms - start_ms:5d} ms  {what:8s} {detail}")
    print(f"  stack: {' > '.join(pad.names())}   keys down: {pad.down() or 'none'}   wheel steps: {ticks}")


def main():
    pad = start().hold("R1").wait(500)
    since = len(pad.sim.log)
    pad.hold("L1").wait(300).push("LS", "up").wait(200).let_go("R1").wait(300)
    show("T1. R1 held, L1 pressed (Modifier 2), stick up, R1 let go", pad, since)
    since = len(pad.sim.log)
    pad.recentre("LS").wait(300).let_go("L1").wait(300)
    show("    ... stick back to centre, then L1 let go", pad, since)

    pad = start().hold("R1").wait(500).flick("LS", "up").wait(20)
    since = len(pad.sim.log)
    pad.hold("L1").wait(300)
    show("T2. R1 held, stick tapped up (its window open for 20 ms), L1 pressed and held", pad, since)
    since = len(pad.sim.log)
    pad.let_go("L1").wait(300)
    show("    ... L1 let go", pad, since)

    pad = start().hold("R1").wait(500).push("LS", "up").wait(400)
    since = len(pad.sim.log)
    pad.tap("L1", 100).wait(300)
    show("T3. R1 held, stick held up, L1 tapped for 100 ms (the Modifier 2 quick tap)", pad, since)

    pad = start().hold("R1").wait(500)
    since = len(pad.sim.log)
    pad.hold("L1").wait(300).let_go("R1").wait(200).hold("R1").wait(300).let_go("L1").wait(200).let_go("R1").wait(300)
    show("T4. Rocking with the stick at centre: R1, L1, R1 up, R1 down, L1 up, R1 up", pad, since)

    pad = start().hold("L1").wait(500).flick("LS", "down").wait(20)
    since = len(pad.sim.log)
    pad.hold("R1").wait(100).let_go("L1").wait(300)
    show("T5. L1 held, stick tapped down (window), R1 pressed, L1 let go after 100 ms", pad, since)

    pad = start().hold("R1").wait(500).hold("L1").wait(300).miss("L1").wait(100)
    since = len(pad.sim.log)
    pad.let_go("R1").wait(300)
    show("T6. R1 held, L1 pressed, L1's release missed (Steam menu open), R1 let go", pad, since)
    since = len(pad.sim.log)
    pad.touch("LS").wait(100)
    show("    ... then a thumb on the left stick", pad, since)


if __name__ == "__main__":
    main()
