"""After a stick window is closed by the other driver: ways to make Modifier 2 come for certain.

    PYTHONPATH=.:tests python3 findings/2026-10-11-owner-release-audit/window_fix.py <scratch dir>

`<scratch dir>` holds the trial layouts of plan_candidate.py after the fix pipeline. Three versions are written
beside them (never into `neptune/`) and compared with 90.56:

    as answered     the plan as it is: the window's chord only removes the window, and Modifier 2 comes from the W
                    or S layer's entry, a repeating chord with seven sub-commands that is uncovered under the
                    second driver
    split entry     that entry becomes two chords on the same chord button, the shape the plain modifiers' command
                    binds already have: one that does not repeat, with the six removes and the add, for a fresh
                    press; and one that repeats every 50 ms with a single command, the add. To stay at three
                    entries the other driver's Release goes (six removes)
    window adds it  the window's chord removes the window and adds Modifier 2 in the same bind (the plan's first
                    version of part 2)

Each runs on two simulators. "as it is" is the press simulator. "strict" builds in the author's report of
2026-10-10 and the slow reading of A9: a bind uncovered under a held button waits for its repeat, and a
repeating Chorded Press with more than one sub-command never runs its commands on a repeat. On each: the
two-driver plan's 640-gesture sweep, and one gesture (first driver held, the stick flicked, the second driver
pressed 20 ms into the window and held, then A).
"""
import contextlib
import copy
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

from steam_layout.model import TARGET, Layout, actions, entries, map_title
from steam_layout.simulator import Simulator
import scenario
from scenario import Pad
import first_driver as base

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "findings/2026-10-11-two-drivers-in-steering"
WINDOWS = ("Steering | LS Up: Double Tap", "Steering | LS Down: Double Tap")
VERSIONS = ("90.56", "as answered", "split entry", "window adds it")
PLAIN = Simulator


class Strict(Simulator):
    """The author's report of 2026-10-10 built in, with the slow reading of A9."""

    def __init__(self, layout, start=None, **options):
        options["exposed_fires"] = False
        super().__init__(layout, start, **options)

    def _fire(self, key, act):
        entry = act.entry
        repeat = self._repeat(entry)
        if entry.kind == "chord" and repeat is not None and not act.first \
                and len(entry.ops) + len(entry.outputs) + len(entry.taps) > 1:
            act.due = self.now + repeat                       # a repeat of a chord with several sub-commands: nothing
            return
        return super()._fire(key, act)


def versions(out, variant):
    name = (lambda title: map_title(title, base.RENAME)) if variant == "alternative" else (lambda title: title)
    button = lambda driver: scenario.BUTTONS[scenario.ROLES[variant][driver]]
    answered = json.loads((out / f"{variant}.json").read_text(encoding="utf-8"))
    found = {"90.56": scenario.layout_data(variant), "as answered": answered}

    split = copy.deepcopy(answered)
    layout = Layout(split)
    for host, (first, second, _, driver, _) in base.MOD2.items():
        source, inp = button(second)
        value = layout.active(name(driver))[source]["inputs"][inp]
        entry = value["activators"]["chord"]
        once = copy.deepcopy(entry)
        for key in ("hold_repeats", "repeat_rate"):
            once["settings"].pop(key, None)
        again = copy.deepcopy(entry)
        again["bindings"]["binding"] = next(a for a in actions(entry) if TARGET.search(a).group(1) == "add_layer")
        value["activators"] = {"Full_Press": value["activators"]["Full_Press"], "chord": [once, again]}
    found["split entry"] = split

    adds = copy.deepcopy(answered)
    layout = Layout(adds)
    for window in WINDOWS:
        for host, (first, second, _, driver, _) in base.MOD2.items():
            source, inp = button(second)
            chord = layout.active(name(window))[source]["inputs"][inp]["activators"]["chord"]
            number = layout.order.index(next(k for k, t in layout.titles.items() if t == name(host))) + 1
            chord["bindings"]["binding"] = [f"controller_action add_layer {number} 0 0, , ", *actions(chord)]
    found["window adds it"] = adds
    return found


def sweep(matrix, variant, data):
    matrix.DATA[variant] = data
    shown = io.StringIO()
    with contextlib.redirect_stdout(shown):
        matrix.main(variant)
    text = shown.getvalue()
    total = int(re.search(r"(\d+) flags", text).group(1))
    return total, re.findall(r"^ +(\d+)  (.+)$", text, flags=re.M)


def gesture(variant, data, first, second):
    pad = Pad(variant, data=data)
    pad.enter_steering().lift("LS").wait(300)
    pad.hold(first).wait(500).flick("LS", "up").wait(20).mark().hold(second).wait(400)
    typed = pad.typed()
    modifier = any(": Modifier 2" in title for title in pad.names())
    pad.mark().tap("A")
    return f"Modifier 2 {'on' if modifier else 'NOT on'}; the second driver typed {typed or 'nothing'}; A types {pad.typed()}"


def main():
    out = Path(sys.argv[1])
    spec = importlib.util.spec_from_file_location("two_driver_matrix", PLAN / "matrix.py")
    matrix = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matrix)
    built = {variant: versions(out, variant) for variant in scenario.VARIANTS}
    for variant in scenario.VARIANTS:
        for version in VERSIONS[2:]:
            path = out / f"{variant}-{version.replace(' ', '-')}.json"
            path.write_text(json.dumps(built[variant][version], indent="\t") + "\n", encoding="utf-8")
    for label, simulator in (("as it is", PLAIN), ("strict", Strict)):
        scenario.Simulator = simulator
        print(f"\nThe simulator {label}:")
        for version in VERSIONS:
            flags, seen = {}, {}
            results = set()
            for variant in scenario.VARIANTS:
                total, rows = sweep(matrix, variant, built[variant][version])
                flags[variant] = total
                seen[variant] = rows
                for first, second in (("R1", "L1"), ("L1", "R1")):
                    results.add(gesture(variant, built[variant][version], first, second)
                                .replace("'S'", "its key").replace("'W'", "its key"))
            print(f"  {version}: sweep flags {flags['default']} and {flags['alternative']} (default, alternative)")
            for count, what in seen["default"]:
                print(f"        {count}  {what}")
            for result in sorted(results):
                print(f"      in a window: {result}")
    scenario.Simulator = PLAIN



if __name__ == "__main__":
    main()
