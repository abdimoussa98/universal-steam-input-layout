#!/usr/bin/env python3
"""Why a pad's outer ring gives no bump on 90.50, and why a stick tap doesn't scroll in Steering.

Read-only. It reads the frozen snapshots of 90.48 to 90.50 and writes nothing.
The candidate is an in-memory edit of 90.50, not a builder.

    python3 findings/2026-10-10-pad-ring-bump-and-stick-tap/probe.py

The press simulator holds a control or doesn't: it knows no stick distance, no
pad pressure and no haptic motor. What it shows is which binding answers.
"""
import collections
import copy
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from steam_layout.model import Layout, entries, map_title  # noqa: E402
from steam_layout.simulator import Simulator  # noqa: E402
from tests.scenario import RENAME, Pad  # noqa: E402

VARIANTS = ("default", "alternative")
J, RJ, RP = "joystick", "right_joystick", "right_trackpad"
OVERRIDE = {"0": "Off", "1": "Low", "2": "Medium", "3": "High", "5": "Use Activator Settings", None: "not stated"}
RING = (("LTP: Arrow Keys", "left_trackpad"), ("RTP: Mouse Buttons", "right_trackpad"))
CENTRE = (("LTP: Middle Click", "left_trackpad"), ("RTP: Middle Click", "right_trackpad"))
MODIFIERS = (("Steering | LS Up: Modifier 1", "Steering | LS Up: Double Tap"),
             ("Steering | LS Down: Modifier 0", "Steering | LS Down: Double Tap"))
HELPERS = ("LST: Temporary Gyro", "LST: Tap Cover", "LST: Entry Point")        # stored order: the array runs bottom to top


def snapshot(variant, version):
    return json.loads((ROOT / f"versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json").read_text())


def title(variant, text):
    return map_title(text, RENAME) if variant == "alternative" else text


def candidate(variant):
    """90.50 with the plan's two changes, in memory."""
    data = copy.deepcopy(snapshot(variant, "90.50"))
    layout = Layout(data)
    for layer, source in RING:
        group = layout.active(layer)[source]
        group["settings"]["haptic_intensity_override"] = "5"
        group["inputs"]["edge"]["activators"]["Full_Press"].setdefault("settings", {})["haptic_intensity"] = "0"
    for modifier, _ in MODIFIERS:
        release = layout.active(title(variant, modifier))[J]["inputs"]["touch"]["activators"]["release"]
        release["bindings"]["binding"] = [
            f"controller_action remove_layer {layout.order.index(layout.presets[helper]['name']) + 1} 0 0, , " for helper in HELPERS]
    return data


# --- the pads ----------------------------------------------------------------------------------

def haptic(entry):
    return (entry.get("settings") or {}).get("haptic_intensity", "not stated")


def pads():
    print("Pad clicks: what asks for a bump, per release (the two layouts agree)\n")
    for version in ("90.48", "90.49", "90.50"):
        rows = []
        for variant in VARIANTS:
            layout = Layout(snapshot(variant, version))
            row = {}
            for pad in ("left_trackpad", "right_trackpad"):
                row[f"Base, {pad} click add"] = haptic(layout.active("Base")[pad]["inputs"]["click"]["activators"]["Soft_Press"])
            for layer, source in CENTRE:
                row[f"{layer}, output"] = haptic(layout.active(layer)[source]["inputs"]["click"]["activators"]["Full_Press"])
            for layer, source in RING:
                group = layout.active(layer)[source]
                row[f"{layer}, D-pad override"] = OVERRIDE[group["settings"].get("haptic_intensity_override")]
                row[f"{layer}, direction outputs"] = "/".join(sorted({
                    haptic(group["inputs"][f"dpad_{d}"]["activators"]["Full_Press"]) for d in ("north", "south", "east", "west")}))
            rows.append(row)
        assert rows[0] == rows[1], version
        print(f"  {version}")
        for key, value in rows[0].items():
            print(f"    {key:38s} {value}")
    print()


# --- the stick tap -----------------------------------------------------------------------------

SURROUNDINGS = {"nothing else": [],
                "right thumb resting on its stick": [("press", (RJ, "touch")), ("wait", 300)],
                "right thumb resting on its pad": [("press", (RP, "touch")), ("wait", 300)]}
ORDERS = ("the thumb stays on", "the thumb stays on, ring before direction",
          "the thumb lands, taps and leaves before the stick is back",
          "a resting thumb taps and leaves before the stick is back", "the thumb leaves after the stick is back")


def push(order, direction):
    """One 60 ms push of the left stick. `(J, 'edge')` is the outer ring."""
    touch, way, ring = (J, "touch"), (J, direction), (J, "edge")
    out = [("press", way), ("press", ring)] if order != ORDERS[1] else [("press", ring), ("press", way)]
    back = [("release", way), ("release", ring)]
    if order in ORDERS[:2]:
        return [("press", touch), ("wait", 300), *out, ("wait", 60), *back, ("wait", 400)]
    if order == ORDERS[2]:
        return [("press", touch), *out, ("wait", 60), ("release", touch), ("wait", 10), *back, ("wait", 400)]
    if order == ORDERS[3]:
        return [("press", touch), ("wait", 300), *out, ("wait", 60), ("release", touch), ("wait", 10), *back, ("wait", 400)]
    return [("press", touch), ("wait", 300), *out, ("wait", 60), *back, ("wait", 20), ("release", touch), ("wait", 400)]


def play(pad, steps):
    for what, value in steps:
        {"press": pad.sim.press, "release": pad.sim.release, "wait": pad.wait, "hold": pad.hold}[what](value)
    return pad


def wheel(pad):
    return [output for output in pad.typed() if output.startswith("mouse_wheel")]


def sweep(label, layouts):
    """Every push, on both layouts. A push passes with exactly one wheel step in its direction."""
    passed = collections.OrderedDict((order, [0, 0]) for order in ORDERS)
    for variant in VARIANTS:
        for start, driver, (direction, step), around, order, thumb_first, exposed, reverse in itertools.product(
                (("Base", "Steering"), ("Base", "Gyro", "Steering")), ("R1", "L1"),
                (("dpad_north", "SCROLL_UP"), ("dpad_south", "SCROLL_DOWN")), SURROUNDINGS, ORDERS,
                (False, True), (True, False), (False, True)):
            steps = push(order, direction)
            if thumb_first and steps[1] != ("wait", 300):
                continue                                  # the thumb lands with the tap: it can't be there first
            if thumb_first:
                steps = [steps[0], ("wait", 300), ("hold", driver), ("wait", 100), *steps[2:]]
            else:
                steps = [("hold", driver), ("wait", 100), *steps]
            pad = Pad(variant, start=start, data=layouts[variant], exposed_fires=exposed, reverse_ties=reverse)
            play(pad.mark(), SURROUNDINGS[around] + steps)
            passed[order][0] += wheel(pad) == [f"mouse_wheel {step}"]
            passed[order][1] += 1
    print(f"  {label}: {sum(n for _, n in passed.values())} pushes")
    for order, (good, count) in passed.items():
        print(f"    {good:4d} of {count:4d} scroll once   {order}")


def other_thumb(label, layouts):
    """The right thumb leaves its own stick during the push: the hold marker is completed (R123)."""
    steps = [("hold", "R1"), ("press", (J, "touch")), ("press", (RJ, "touch")), ("wait", 300), ("press", (J, "dpad_north")),
             ("press", (J, "edge")), ("wait", 60), ("release", (RJ, "touch")), ("wait", 10), ("release", (J, "dpad_north")),
             ("release", (J, "edge")), ("wait", 400)]
    found = {len(wheel(play(Pad(variant, start=("Base", "Steering"), data=layouts[variant]).mark(), steps))) for variant in VARIANTS}
    print(f"  {label}: the right thumb leaves its stick during the push: wheel steps {sorted(found)}")


def lost_release(layouts):
    """Four pushes in a row if the ring's Release never reaches a modifier that landed with the ring already out.

    Modelled by leaving the ring out of a push whose modifier isn't on yet. The next push starts with the
    modifier on, so its ring is pressed inside the modifier and its Release fires.
    """
    found = set()
    for variant in VARIANTS:
        pad = Pad(variant, start=("Base", "Steering"), data=layouts[variant])
        play(pad, [("hold", "R1"), ("press", (J, "touch")), ("wait", 300)])
        steps = []
        for _ in range(4):
            on = pad.has("Steering | LS Up: Modifier 1")
            pad.mark()
            play(pad, [("press", (J, "dpad_north")), *([("press", (J, "edge"))] if on else []), ("wait", 60),
                       ("release", (J, "dpad_north")), *([("release", (J, "edge"))] if on else []), ("wait", 400)])
            steps.append(len(wheel(pad)))
        found.add(tuple(steps))
    print(f"  wheel steps of four pushes in a row, the thumb on the stick: {sorted(found)}")


# --- "it only happens once" ----------------------------------------------------------------------

class GuardsStayOff(Simulator):
    """The press simulator with one assumption turned off: a chord does not start when a removal exposes
    its binding under an input that is held (A36, for exposure). A what-if, not a claim about Steam."""

    def _establish(self, control, phase, mode):
        if mode != "exposed":
            return super()._establish(control, phase, mode)
        held, self.held = self.held, set()                # no chord button reads as held: no chord starts
        try:
            super()._establish(control, phase, mode)
        finally:
            self.held = held


def delayed_guards(layout):
    """Inputs whose cleanup function is held back only by chords that have a start delay."""
    found = []
    for layer in layout.presets:
        for source, group in layout.active(layer).items():
            for name, node in group.get("inputs", {}).items():
                listed = list(entries(node.get("activators", {})))
                cleanups = [e for kind, e in listed if kind == "Full_Press" and (e.get("settings") or {}).get("interruptable") != "0"
                            and any(op == "remove_layer" for op, _ in layout.layer_ops(e))]
                delays = [int((e.get("settings") or {}).get("delay_start") or 0) for kind, e in listed if kind == "chord"]
                if cleanups and delays and all(delays):
                    found.append(f"{layer}, {source}/{name}: the guard waits {'/'.join(map(str, delays))} ms")
    return found


def what_if(variant, data, start=("Base", "Steering"), exposed=True):
    pad = Pad(variant, start=start, data=data, exposed_fires=exposed)
    pad.sim = GuardsStayOff(pad.layout, start=tuple(pad.stack), exposed_fires=exposed)
    return pad


def once(layouts):
    """Deflects in one driver hold with the thumb staying on the stick, under the what-if."""
    tap = [("press", (J, "dpad_north")), ("press", (J, "edge")), ("wait", 60), ("release", (J, "edge")),
           ("release", (J, "dpad_north")), ("wait", 600)]
    rows = collections.OrderedDict()
    for variant, resting, again, exposed in itertools.product(VARIANTS, (True, False), (False, True), (True, False)):
        pad = what_if(variant, layouts[variant], exposed=exposed)
        play(pad, [("hold", "R1"), *([("press", (J, "touch"))] if resting else []), ("wait", 300)])
        steps = [len(wheel(play(pad.mark(), tap)))]
        left = "on" if pad.has("Steering | R1: W Key") else "gone"
        for _ in range(3):
            if again:                                       # the driver let go and pressed again before each deflect
                pad.let_go("R1").wait(100).hold("R1").wait(100)
            steps.append(len(wheel(play(pad.mark(), tap))))
        key = ("a thumb resting on the stick" if resting else "no thumb on a stick as the window closes",
               "the driver let go and pressed again each time" if again else "the driver held throughout")
        rows.setdefault(key, set()).add((tuple(steps), left))
    for (thumb, driver), results in rows.items():
        for steps, left in sorted(results):
            print(f"    {thumb:40s} {driver:46s} wheel steps {steps}; the W layer is {left} after the first one")


def releases():
    """Four deflects, a thumb resting, the driver held: every live snapshot from 90.38 on, as it is and with the what-if."""
    tap = [("press", (J, "dpad_north")), ("press", (J, "edge")), ("wait", 60), ("release", (J, "edge")),
           ("release", (J, "dpad_north")), ("wait", 600)]
    for version in ("90.38", "90.40", "90.41", "90.42", "90.43", "90.44", "90.45", "90.46", "90.47", "90.48", "90.49", "90.50"):
        found = {"as it is": set(), "with the what-if": set()}
        for variant, exposed, reverse in itertools.product(VARIANTS, (True, False), (False, True)):
            data = snapshot(variant, version)
            for model in found:
                pad = Pad(variant, start=("Base", "Steering"), data=data, exposed_fires=exposed, reverse_ties=reverse)
                if model != "as it is":
                    pad.sim = GuardsStayOff(pad.layout, start=tuple(pad.stack), exposed_fires=exposed, reverse_ties=reverse)
                play(pad, [("hold", "R1"), ("press", (J, "touch")), ("wait", 300)])
                found[model].add(tuple(len(wheel(play(pad.mark(), tap))) for _ in range(4)))
        print(f"    {version}: " + "; ".join(f"{model} {sorted(steps)}" for model, steps in found.items()))


def everyday(layouts):
    """The same what-if outside Steering: thumbs resting, L1 held past the cursor's 200 ms, then A."""
    for model in ("as the simulator has it", "with the what-if"):
        found = set()
        for variant, exposed in itertools.product(VARIANTS, (True, False)):
            pad = Pad(variant, data=layouts[variant], exposed_fires=exposed) if model.startswith("as") else \
                what_if(variant, layouts[variant], start=None, exposed=exposed)
            play(pad, [("press", (J, "touch")), ("press", (RJ, "touch")), ("wait", 400), ("hold", "L1"), ("wait", 300)])
            pad.mark().tap("A", 60).wait(300)
            found.add((tuple(pad.typed()), "on" if pad.has("L1: Modifier 0") else "gone"))
        print(f"    {model:24s} " + "; ".join(f"A types {list(keys)}, the modifier is {state}" for keys, state in sorted(found)))


def main():
    pads()
    print("Stick taps in Steering, a driver held (press simulator, both layouts)\n")
    versions = {version: {variant: snapshot(variant, version) for variant in VARIANTS} for version in ("90.48", "90.50")}
    versions["candidate"] = {variant: candidate(variant) for variant in VARIANTS}
    for label, layouts in versions.items():
        sweep(label, layouts)
    print()
    for label in ("90.50", "candidate"):
        other_thumb(label, versions[label])
    print("\nIf the ring's Release is lost when the modifier lands with the ring already out (A8 false), on 90.50:")
    lost_release(versions["90.50"])
    print("\nIf a guard's chord does not start when a removal uncovers it under a held input (A36 false for exposure):")
    versions.update({version: {variant: snapshot(variant, version) for variant in VARIANTS} for version in ("90.45", "90.46")})
    for label in ("90.45", "90.46", "90.50", "candidate"):
        print(f"  {label}: four deflects in a row")
        once(versions[label])
    print("  wheel steps of four deflects, a thumb resting, the driver held, per release")
    releases()
    print("  90.50, outside Steering: thumbs resting, L1 held 300 ms, then A")
    everyday(versions["90.50"])
    print("\nCleanup functions whose only guard is a chord with a start delay (the two layouts agree):")
    for version in ("90.42", "90.50"):
        found = [delayed_guards(Layout(snapshot(variant, version))) for variant in VARIANTS]
        assert len(found[0]) == len(found[1])
        print(f"  {version}: {len(found[0])}")
        for line in found[0]:
            print(f"    {line}")


if __name__ == "__main__":
    main()
