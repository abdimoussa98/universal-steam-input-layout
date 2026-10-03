"""Press-by-press scenario tests: readable gestures over the press simulator, on the working layouts.

A scenario is one Deck check written as a test: hold this, tap that, wait, and then
say which layers are on the stack and which keys went down.

    class FallbackHold(ScenarioCase):
        @scenario("90.11 F8", rules=("R137",), rests=("A16",))
        def test_a_start_tap_types_tab_and_adds_nothing(self):
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(100)
                pad.tap("Start")
                self.assertEqual(pad.typed_since_mark(), ["TAB"])

`scenario(check, rules, rests, either)` records which Deck check the test replaces, the
rules it checks and the Steam assumptions its outcome rests on. `self.each()` runs the
body on both layouts, and once per way of every assumption named in `either` (the ones
the layout must work either way under: A9, A32).

    python3 -m tests.scenario      # the scenarios, and which rest on an unverified assumption

Names. Buttons: Start, Select, A, B, X, Y, Up, Down, Left, Right, LB, RB, and the back
buttons. L1 and R1 are the modifier buttons: the bumpers in the default layout, the
triggers' soft pull in the alternative. LF and RF are the firing buttons: the triggers'
soft pull in the default, the bumpers in the alternative. Sticks are LS and RS, pads LP
and RP. A layer title is written with the default layout's names; `pad.title()` and the
expectations turn L1 and R1 into L2 and R2 for the alternative.

Plan: plans/2026-10-02-rule-registry.md, phases 13 and 14.
"""
from collections import namedtuple
import itertools
import json
from pathlib import Path
import unittest

from steam_layout.model import Layout, map_title
from steam_layout.simulator import Simulator, desktop, typed

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("default", "alternative")
BUTTONS = {"Start": ("switch", "button_escape"), "Select": ("switch", "button_menu"),
           "LB": ("switch", "left_bumper"), "RB": ("switch", "right_bumper"),
           "A": ("button_diamond", "button_a"), "B": ("button_diamond", "button_b"),
           "X": ("button_diamond", "button_x"), "Y": ("button_diamond", "button_y"),
           "Up": ("dpad", "dpad_north"), "Down": ("dpad", "dpad_south"),
           "Left": ("dpad", "dpad_west"), "Right": ("dpad", "dpad_east"),
           "LT": ("left_trigger", "edge"), "RT": ("right_trigger", "edge"),
           "LT full": ("left_trigger", "click"), "RT full": ("right_trigger", "click"),
           "L4": ("switch", "button_back_left_upper"), "L5": ("switch", "button_back_left"),
           "R4": ("switch", "button_back_right_upper"), "R5": ("switch", "button_back_right")}
ROLES = {"default": {"L1": "LB", "R1": "RB", "LF": "LT", "RF": "RT"},
         "alternative": {"L1": "LT", "R1": "RT", "LF": "LB", "RF": "RB"}}
SOURCES = {"LS": "joystick", "RS": "right_joystick", "LP": "left_trackpad", "RP": "right_trackpad"}
DIRECTIONS = {"up": "dpad_north", "down": "dpad_south", "left": "dpad_west", "right": "dpad_east"}
SWITCHES = {"A9": ("exposed_fires", (True, False)), "A32": ("reverse_ties", (False, True))}   # the either-way assumptions
RENAME = {"L1": "L2", "R1": "R2"}

Meta = namedtuple("Meta", "check name rules rests either")
SCENARIOS = []
_layouts = {}


def scenario(check, rules=(), rests=(), either=()):
    """Mark a test as the scenario for a Deck check (section plus ID, as in the sorting)."""
    def mark(function):
        function.scenario = Meta(check, function.__qualname__, tuple(rules), tuple(rests) + tuple(either), tuple(either))
        SCENARIOS.append(function.scenario)
        return function
    return mark


def layout_data(variant):
    if variant not in _layouts:
        path = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
        _layouts[variant] = json.loads(path.read_text(encoding="utf-8"))
    return _layouts[variant]


class Pad:
    """The controller in a scenario: gestures by name, on one layout."""

    def __init__(self, variant, start=None, data=None, **options):
        self.variant, self.options = variant, options
        self.layout = Layout(data or layout_data(variant))
        self.sim = Simulator(self.layout, start=tuple(self.title(t) for t in start) if start else None, **options)
        self._mark = 0

    def __repr__(self):
        return f"{self.variant}{' ' + str(self.options) if self.options else ''}"

    # --- names -----------------------------------------------------------------------------

    def title(self, title):
        """A layer title written with the default layout's names, as this layout names it."""
        return map_title(title, RENAME) if self.variant == "alternative" else title

    def control(self, name):
        name = ROLES[self.variant].get(name, name)
        if name in BUTTONS:
            return BUTTONS[name]
        stick, _, part = name.partition(" ")
        return (SOURCES[stick], part)          # "LS click", "RP touch"

    # --- gestures ---------------------------------------------------------------------------

    def hold(self, *names):
        for name in names:
            self.sim.press(self.control(name))
        return self

    def let_go(self, *names):
        for name in names:
            self.sim.release(self.control(name))
        return self

    def tap(self, name, ms=30):
        self.hold(name).wait(ms)
        return self.let_go(name)

    def miss(self, *names):
        """Let go while the Steam menu is open: the layout never sees the release (A25)."""
        for name in names:
            self.sim.lose(self.control(name))
        return self

    def wait(self, ms):
        self.sim.wait(ms)
        return self

    def _held(self, stick, part):
        return (SOURCES[stick], part) in self.sim.held

    def touch(self, stick):
        if not self._held(stick, "touch"):
            self.sim.press((SOURCES[stick], "touch"))
        return self

    def push(self, stick, direction=None):
        """Push a stick out: the thumb on it, the direction (on a D-pad stick), and the outer edge."""
        self.touch(stick)
        if direction:
            self.sim.press((SOURCES[stick], DIRECTIONS[direction]))
        if not self._held(stick, "edge"):
            self.sim.press((SOURCES[stick], "edge"))
        return self

    def roll(self, stick, direction):
        """Move a stick that is out to another direction without passing through centre."""
        self.sim.press((SOURCES[stick], DIRECTIONS[direction]))
        for part in DIRECTIONS.values():
            if part != DIRECTIONS[direction] and self._held(stick, part):
                self.sim.release((SOURCES[stick], part))
        return self

    def recentre(self, stick):
        for part in (*DIRECTIONS.values(), "edge"):
            if self._held(stick, part):
                self.sim.release((SOURCES[stick], part))
        return self

    def lift(self, stick):
        self.recentre(stick)
        if self._held(stick, "touch"):
            self.sim.release((SOURCES[stick], "touch"))
        return self

    def flick(self, stick, direction, ms=60):
        return self.push(stick, direction).wait(ms).recentre(stick)

    def click(self, stick, ms=30):
        self.touch(stick)
        self.sim.press((SOURCES[stick], "click"))
        self.wait(ms)
        self.sim.release((SOURCES[stick], "click"))
        return self

    def enter_steering(self, settle=True):
        """Start plus left-stick click, the click released first. `settle` moves the stick out and back
        once, which ends the Entry Guard."""
        self.hold("Start").click("LS").let_go("Start")
        if settle:
            self.flick("LS", "left").wait(300)
        return self

    # --- reading ----------------------------------------------------------------------------

    @property
    def stack(self):
        return self.sim.stack

    @property
    def top(self):
        return self.sim.stack[-1]

    def has(self, *titles):
        return all(self.title(t) in self.sim.stack for t in titles)

    def lacks(self, *titles):
        return not any(self.title(t) in self.sim.stack for t in titles)

    def layers(self, *titles):
        """A stack written with default names, for comparing with `stack`."""
        return tuple(self.title(t) for t in titles)

    def down(self):
        return self.sim.down()

    def mark(self):
        """Remember this moment; `typed()` and `seen()` then report only what came after."""
        self._mark = len(self.sim.log)
        return self

    def typed(self):
        """What was typed since the mark: keys, mouse buttons and wheel steps, in order."""
        return typed(self.sim.log[self._mark:])

    def seen(self, *kinds):
        return [(what, detail) for _, what, detail in self.sim.log[self._mark:] if what in kinds]

    def gyro_off(self):
        return self.sim.gyro_disabled()


class ScenarioCase(unittest.TestCase):
    """Runs a scenario on both layouts, once per way of each assumption it names in `either`."""
    _pad = None

    def _formatMessage(self, msg, standardMsg):
        """Say which layout and which way of an assumption a failed expectation was on."""
        where = f" [on {self._pad!r} at {self._pad.sim.now} ms, stack {self._pad.stack}]" if self._pad else ""
        return super()._formatMessage(msg, standardMsg) + where

    def each(self, start=None, variants=VARIANTS, desktop_configuration=False, **options):
        meta = getattr(getattr(self, self._testMethodName), "scenario", None)
        names = [SWITCHES[a][0] for a in (meta.either if meta else ())]
        ways = [SWITCHES[a][1] for a in (meta.either if meta else ())]
        for variant in variants:
            for way in itertools.product(*ways):
                chosen = {**options, **dict(zip(names, way))}
                data = desktop(layout_data(variant)) if desktop_configuration else None
                pad = Pad(variant, data=data, **chosen)
                if start == "steering":
                    pad.enter_steering()
                elif start:
                    pad = Pad(variant, start=start, data=data, **chosen)
                self._pad = pad
                yield pad.mark()


def report():
    """The scenarios, and which of them rest on an assumption that isn't verified."""
    from steam_layout import rules
    for path in sorted((ROOT / "tests").glob("test_scenarios_*.py")):
        __import__(f"tests.{path.stem}")
    assumptions = rules.load_assumptions()
    lines = [f"{len(SCENARIOS)} scenarios for {len({m.check for m in SCENARIOS})} Deck checks"]
    resting = {}
    for meta in SCENARIOS:
        for assumption in meta.rests:
            if not assumptions[assumption].verified:
                resting.setdefault(assumption, []).append(meta)
    lines.append(f"\nResting on an assumption that isn't verified: "
                 f"{len({m.name for found in resting.values() for m in found})}")
    for assumption in sorted(resting, key=lambda a: int(a[1:])):
        entry = assumptions[assumption]
        way = "run both ways" if assumption in SWITCHES else entry.layout.lower()
        lines.append(f"\n{assumption} ({entry.status.split(':')[0].split(',')[0].lower()}; {way}): {entry.statement}")
        lines.extend(f"  {meta.check}  {meta.name}" for meta in resting[assumption])
    return "\n".join(lines)


if __name__ == "__main__":
    from tests.scenario import report as registered      # the test files register with the imported module
    print(registered())
