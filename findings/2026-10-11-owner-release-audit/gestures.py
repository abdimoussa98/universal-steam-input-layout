"""The two-driver gestures inside `Steering`, press by press, on the press simulator.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/gestures.py
"""
from scenario import Pad

SHOWN = ("press", "release", "add", "remove", "down", "up", "handover", "tap", "beep")


def show(title, pad, since, before=None):
    print(f"\n{title}")
    if before:
        print(f"  stack before: {' > '.join(before)}")
    for ms, what, detail in pad.sim.log[since:]:
        if what in SHOWN:
            print(f"  {ms - pad.sim.log[since][0]:5d} ms  {what:8s} {detail}")
    print(f"  stack: {' > '.join(pad.names())}")
    print(f"  keys down: {pad.down() or 'none'}")


def start(gyro=False, **options):
    pad = Pad("default", **options)
    if gyro:
        pad.hold("L1").wait(20).hold("R1").wait(40).let_go("R1").wait(20).let_go("L1").wait(400)
    pad.enter_steering().lift("LS").wait(300)
    return pad


def main():
    for exposed in (True, False):
        way = f"(a bind exposed under a held button fires {'at once' if exposed else 'on its next repeat'}, A9)"
        pad = start(exposed_fires=exposed)
        pad.hold("R1").wait(500)
        since = len(pad.sim.log)
        pad.hold("L1").wait(60).let_go("L1").wait(300)
        show(f"1. R1 held (W), L1 tapped for 60 ms {way}", pad, since)

    pad = start()
    pad.hold("R1").wait(500)
    since = len(pad.sim.log)
    pad.hold("L1").wait(300).let_go("L1").wait(300)
    show("2. R1 held (W), L1 held 300 ms and let go: the cover's Release answers", pad, since)

    pad = start()
    pad.hold("R1").wait(500)
    since = len(pad.sim.log)
    pad.hold("L1").wait(60).let_go("R1").wait(300)
    show("3. R1 held (W), L1 pressed, R1 let go first: the W layer's own Release answers", pad, since)

    pad = start(gyro=True)
    pad.hold("R1").wait(500)
    since = len(pad.sim.log)
    pad.hold("L1").wait(60).let_go("L1").wait(300)
    show("4. As 1, with Gyro on under Steering", pad, since)

    pad = start()
    pad.touch("RP").wait(300).touch("LS").wait(50).touch("RS").wait(50)
    pad.hold("R1").wait(500)
    since, before = len(pad.sim.log), pad.names()
    pad.hold("L1").wait(60).let_go("L1").wait(300)
    show("5. As 1, with thumbs resting on the right pad and both sticks before R1", pad, since, before)

    pad = start()
    pad.hold("R1").wait(300).touch("LS").wait(300).touch("RS").wait(300)
    since, before = len(pad.sim.log), pad.names()
    pad.hold("L1").wait(60).let_go("L1").wait(300)
    show("6. As 1, with thumbs resting on both sticks after R1", pad, since, before)

    pad = start()
    pad.press_pad("LP", "centre").wait(300).hold("R1").wait(300)
    since, before = len(pad.sim.log), pad.names()
    pad.hold("L1").wait(60).let_go("L1").wait(300)
    show("7. As 1, with the left pad clicked and held before R1", pad, since, before)


if __name__ == "__main__":
    main()
