#!/usr/bin/env python3
"""One gesture per class of interruption, replayed on the press simulator (default layout).

    python3 findings/2026-10-06-delay-interruptions/check.py

Each line says when the delay's target lands, or that it never does, and what took the input.
The simulator models the assumptions as stated (A12 to A16), so this checks the audit's classes
against the simulator, not against Steam.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from scenario import Pad                                                # noqa: E402


def landed(pad, title):
    """When `title` was added, in ms from the start, or None."""
    times = [ms for ms, what, detail in pad.sim.log if what == "add" and detail == title]
    return times[0] if times else None


def show(label, pad, title, note=""):
    at = landed(pad, title)
    print(f"{label:62} {title}: {'never' if at is None else f'at {at} ms'}{'  ' + note if note else ''}")
    print(f"{'':62} stack: {' > '.join(pad.sim.stack)}")


def main():
    cursor, fn = "L1: Temp Cursor Gyro", "Menu Left: Fn Layer"

    pad = Pad("default").hold("LB").wait(400)
    show("1. hold LB, nothing else", pad, cursor)

    pad = Pad("default").hold("LB").wait(100).let_go("LB").wait(400)
    show("2. own input let go at 100 ms (host removed)", pad, cursor)

    pad = Pad("default").touch("RS").wait(300).hold("LB").wait(100).lift("RS").wait(400)
    show("3. thumb lifts off the right stick at 100 ms (target lands)", pad, cursor, "(LB pressed at 300)")

    pad = Pad("default").hold("LB").wait(100).tap("A").wait(400)
    show("4. A tapped at 100 ms (covered by the host's own cover)", pad, cursor)

    pad = Pad("default").hold("LB").wait(50).touch("RP").wait(50).lift("RP").wait(600)
    show("5. right pad tapped at 50 to 100 ms (covered by a window)", pad, cursor, "(A14: the delay comes back as the window ends)")

    pad = Pad("default").hold("LB").wait(100).press_pad("RP", "centre").wait(600)
    show("6. right pad clicked at 100 ms and held (unrelated removals)", pad, cursor, "(A13: each removal restarts it)")

    pad = Pad("default", any_removal_resets=False).hold("LB").wait(100).press_pad("RP", "centre").wait(600)
    show("6b. the same, if only the target's removal restarts it", pad, cursor, "(A13 false)")

    pad = Pad("default").hold("LB").wait(100).click_pad("RP", "centre", ms=60).wait(600)
    show("6c. right pad clicked at 100 ms and let go at 160 ms", pad, cursor, "(the pad's window covers LB, as in 5)")

    pad = Pad("default").hold("Select").wait(400)
    show("7. hold Select, nothing else", pad, fn)

    pad = Pad("default").touch("LS").wait(300).hold("Select").wait(400)
    show("8. thumb resting on the left stick, then hold Select", pad, fn, "(Select pressed at 300)")

    pad = Pad("default").hold("Select").wait(100).push("LS", "up").wait(400)
    show("9. left stick pushed out at 100 ms (covered by the stick guard)", pad, fn)

    pad = Pad("default").hold("Select").wait(100).hold("LB").wait(400)
    show("10. LB pressed at 100 ms with Select held", pad, fn)

    pad = Pad("default").push("RS").wait(100).hold("Select").wait(600)
    show("11. right stick out, Select at 100 ms (ramp delay covered)", pad, "Turning Ramp Up 1")


if __name__ == "__main__":
    main()
