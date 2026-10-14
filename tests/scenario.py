"""Press-by-press scenario tests: readable gestures over the press simulator, on the working layouts.

A scenario is one press sequence written as a test: hold this, tap that, wait, and then
say which layers are on the stack and which keys went down.

    class FallbackHold(ScenarioCase):
        @scenario("90.11 F8", rules=("R137",), rests=("A16",))
        def test_a_start_tap_types_tab_and_adds_nothing(self):
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(100)
                pad.tap("Start")
                self.assertEqual(pad.typed_since_mark(), ["TAB"])

`scenario(label, rules, rests, either)` records the scenario's label, the rules it checks
and the Steam assumptions its outcome rests on. The label is the release and a number
(`90.14 S1`); a scenario that replaced a check of the retired Deck checklist carries that
check's section and ID. `self.each()` runs the body on both layouts, and once per way of
every assumption named in `either` (the ones the layout must work either way under: A9, A32, A42).

    python3 -m tests.scenario           # the assumptions that aren't verified, and what rests on each
    python3 -m tests.scenario R133      # the scenarios that check a rule
    python3 -m tests.scenario --out findings/<date>-<slug>/    # also write unverified-assumptions.txt there

The first form also says which layers no scenario puts on the stack. A layer that is new or
changed since the newest snapshot has to be on the stack in at least one scenario (R165,
`uncovered`).

Retired interactions may specify `frozen="90.41"` on their scenario. Those
run the named frozen builder and record reach separately; they cannot satisfy
the working layout's coverage requirement. The assumption report labels them.

Names. Buttons: Start, Select, A, B, X, Y, Up, Down, Left, Right, LB, RB, and the back
buttons. L1 and R1 are the modifier buttons: the bumpers in the default layout, the
triggers' soft pull in the alternative. LF and RF are the firing buttons: the triggers'
soft pull in the default, the bumpers in the alternative. Sticks are LS and RS, pads LP
and RP. A pad click is `press_pad(pad, where)`: "centre", a direction for the outer part, or
"ring left" for the ring where the two ranges overlap (A39). A layer title is written with the default layout's names; `pad.title()` and the
expectations turn L1 and R1 into L2 and R2 for the alternative.

Plan: plans/2026-10-02-rule-registry.md, phases 13 to 15.
"""
import argparse
from collections import namedtuple
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

from steam_layout import changes
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
SWITCHES = {"A9": ("exposed_fires", (True, False)), "A32": ("reverse_ties", (False, True)),
            "A42": ("hold_releases", (True, False))}                                             # the either-way assumptions
RENAME = {"L1": "L2", "R1": "R2"}
BACK = {new: old for old, new in RENAME.items()}

Meta = namedtuple("Meta", "check name rules rests either frozen", defaults=(None,))
SCENARIOS = []
REACHED = {}                                 # layout -> the layers a scenario has put on the stack so far
FROZEN_REACHED = {}                          # (version, layout) -> historical reach, never live coverage
RELEASE_LIST = "unverified-assumptions.txt"
_layouts = {}
_frozen_layouts = {}
_ran = []


def scenario(check, rules=(), rests=(), either=(), frozen=None):
    """Mark a test as a scenario: its label, the rules it checks and the assumptions its outcome rests on."""
    def mark(function):
        function.scenario = Meta(check, function.__qualname__, tuple(rules), tuple(rests) + tuple(either), tuple(either), frozen)
        if function.scenario not in SCENARIOS:               # a test file can be imported under two names
            SCENARIOS.append(function.scenario)
        return function
    return mark


def old_inverted_chord(function):
    """Mark a scenario written to the reading of an inverted chord that A61 replaced.

    Until 90.52 the simulator ran a chord with Invert Activation while a chord button was held. It runs while
    none is. On the corrected simulator `Steering | LS: Entry Guard` leaves at once after a centred entry with
    no driver held, and the Fallback Guard of the frozen 90.33 to 90.41 builds hands back to `Steering` at
    once, so these scenarios no longer hold. The author, 2026-10-11: the guard is only meant to protect a
    stick held at entry; a first push after a centred entry is not meant to be guarded. They stay as the
    record of what was believed, as expected failures. 90.53 G1 to G3 state what the guard does.
    """
    return unittest.expectedFailure(function)


def layout_path(variant):
    return ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"


def layout_data(variant):
    if variant not in _layouts:
        _layouts[variant] = json.loads(layout_path(variant).read_text(encoding="utf-8"))
    return _layouts[variant]


def frozen_layout_data(variant, version):
    """Load a retired interaction from its frozen builder or validated candidate."""
    builders = {'90.41': 'findings/2026-10-09-low-haptics-and-silent-fn/build_candidate.py',
                '90.42': 'findings/2026-10-09-fn-haptics-and-steering-clear/build_candidate.py'}
    candidates = {'90.48': 'findings/2026-10-10-quiet-gyro-and-guard-handoff',
                  '90.49': 'findings/2026-10-10-steering-scroll-and-pad-click-fix',
                  '90.51': 'findings/2026-10-10-ring-bump-and-modifier-direction',
                  '90.53': 'findings/2026-10-10-steering-entry-and-edge-chords',
                  '90.54': 'findings/2026-10-11-hold-timer-on-the-edge',
                  '90.55': 'findings/2026-10-11-edge-soft-press-timers',
                  '90.56': 'findings/2026-10-11-edge-cleanup-press-and-guard',
                  '90.57': 'findings/2026-10-12-driver-handover-and-fewer-removes',
                  '90.58': 'findings/2026-10-12-removes-that-never-take-a-layer-off',
                  '90.61': 'findings/2026-10-12-inverted-chord-on-the-steering-left-edge',
                  '90.62': 'findings/2026-10-12-steering-rocking-like-the-bumper-modifiers',
                  '90.63': 'findings/2026-10-12-inverted-ring-on-the-steering-left-edge',
                  '90.64': 'findings/2026-10-12-layer-order',
                  '90.65': 'findings/2026-10-13-steering-left-edge-press-and-guard',
                  '90.66': 'findings/2026-10-13-steering-mode-shift-on-the-drivers',
                  '90.67': 'findings/2026-10-13-entry-guard-before-the-left-edge-cleanup',
                  '90.68': 'findings/2026-10-13-entry-guard-adds-the-driver-layer-first',
                  '90.69': 'findings/2026-10-13-steering-cleanup-presses-without-repeat',
                  '90.70': 'findings/2026-10-13-entry-guard-in-every-steering-cleanup'}
    key = version, variant
    if key not in _frozen_layouts:
        if version in candidates:
            path = ROOT / candidates[version] / f'{variant}-candidate.json'
            _frozen_layouts[key] = json.loads(path.read_text(encoding='utf-8'))
        else:
            spec = importlib.util.spec_from_file_location('scenario_frozen_' + version.replace('.', '_'),
                                                          ROOT / builders[version])
            builder = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(builder)
            _frozen_layouts[key], _ = builder.build(variant)
    return _frozen_layouts[key]


class Pad:
    """The controller in a scenario: gestures by name, on one layout."""

    def __init__(self, variant, start=None, data=None, **options):
        self.variant, self.options = variant, options
        self.layout = Layout(data or layout_data(variant))
        self.sim = Simulator(self.layout, start=tuple(self.title(t) for t in start) if start else None, **options)
        self._mark, self._began = 0, tuple(self.sim.stack)

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
        """Move a stick that is out to another direction; the outer edge stays out.

        To a neighbouring direction the stick passes through the diagonal, so both are held for a moment.
        Opposite directions can't be held together: the old one lets go before the new one presses.
        """
        new = DIRECTIONS[direction]
        old = [part for part in DIRECTIONS.values() if part != new and self._held(stick, part)]
        opposite = {"dpad_north": "dpad_south", "dpad_south": "dpad_north", "dpad_west": "dpad_east", "dpad_east": "dpad_west"}
        for part in old:
            if opposite[part] == new:
                self.sim.release((SOURCES[stick], part))
        self.sim.press((SOURCES[stick], new))
        for part in old:
            if opposite[part] != new:
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

    def press_pad(self, pad, where="centre", rest=True):
        """Click a pad and keep it down: the thumb on it at `where`, then the click.

        "centre" is inside the centre range only. A direction ("left") is the outer part, past the D-pad
        deadzone. "ring left" is the ring where the centre and outer ranges overlap, on that side (A39).
        The direction goes down after the click: Base's left pad uses the same input names for its
        swipes, and a click isn't a swipe.

        Since 90.25 a touch runs a hand-over first; since 90.26 it is done as the thumb lands, wherever
        that is. The thumb rests until it is done; `rest=False` clicks at the moment of the touch.
        """
        source = SOURCES[pad]
        ring, direction = (where.split() + [None])[:2] if where.startswith("ring") else (None, where)
        if direction != "centre" and not self._held(pad, "edge"):
            (self.sim.press_between if ring else self.sim.press)((source, "edge"))
        self.touch(pad)
        for _ in range(100 if rest else 0):
            if not any(title.endswith(": Touch Entry Point") for title in self.sim.stack):
                break
            self.wait(1)
        self.sim.press((source, "click"))
        if direction != "centre":
            self.sim.press((source, DIRECTIONS[direction]))
        return self

    def slide_pad(self, pad, where):
        """Move the thumb on a pad that is clicked: to "centre", or out to a direction."""
        source = SOURCES[pad]
        self.recentre(pad)
        if where != "centre":
            self.sim.press((source, "edge"))
            self.sim.press((source, DIRECTIONS[where]))
        return self

    def let_go_pad(self, pad, lift=True):
        """Stop pressing a pad; `lift` also takes the thumb off it. The direction lets go before the click,
        so that it isn't left held over Base's swipe of the same name."""
        source = SOURCES[pad]
        for part in DIRECTIONS.values():
            if self._held(pad, part):
                self.sim.release((source, part))
        self.sim.release((source, "click"))
        return self.lift(pad) if lift else self

    def click_pad(self, pad, where="centre", ms=120, rest=True):
        return self.press_pad(pad, where, rest).wait(ms).let_go_pad(pad)

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
        """The top layer, by its default-layout name (L1 and R1 also in the alternative)."""
        return self.names()[-1]

    def names(self):
        """The stack by default-layout names, so one expectation serves both layouts."""
        return tuple(map_title(t, BACK) if self.variant == "alternative" else t for t in self.sim.stack)

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

    def reached(self):
        """Every layer that has been on the stack in this scenario."""
        return set(self._began) | {title for _, what, title in self.sim.log if what == "add"}


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
                frozen = meta.frozen if meta else None
                data = frozen_layout_data(variant, frozen) if frozen else layout_data(variant)
                if desktop_configuration:
                    data = desktop(data)
                pad = Pad(variant, data=data, **chosen)
                if start == "steering":
                    # A settled baseline has no thumb held by its entry gesture.
                    # Since 90.47 a resting thumb legitimately owns LST helpers.
                    # Tests of that state use enter_steering() or touch() explicitly.
                    pad.enter_steering().lift("LS").wait(300)
                elif start:
                    pad = Pad(variant, start=start, data=data, **chosen)
                self._pad = pad
                try:
                    yield pad.mark()
                finally:
                    if frozen:
                        FROZEN_REACHED.setdefault((frozen, variant), set()).update(pad.reached())
                    else:
                        REACHED.setdefault(variant, set()).update(pad.reached())


def modules():
    """Every scenario test file, imported (which registers its scenarios)."""
    return [__import__(f"tests.{path.stem}", fromlist=["*"]) for path in sorted((ROOT / "tests").glob("test_scenarios_*.py"))]


def for_rule(rule_id):
    """The scenarios that name a rule."""
    modules()
    return [meta for meta in SCENARIOS if rule_id in meta.rules]


def reached():
    """{layout: the layers some scenario puts on the stack}. Runs every scenario test once."""
    if not _ran:
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules())
        suite.run(unittest.TestResult())             # a failure here shows when the tests themselves run
        _ran.append(True)
    return REACHED


def uncovered(variant, baseline=None):
    """The layers changed since the newest snapshot (or since `baseline`) that no scenario puts on the stack (R165)."""
    changed = changes.changed_since(layout_data(variant), changes.baseline_for(layout_path(variant), baseline))
    return sorted(changed - reached().get(variant, set()))


def report():
    """Every assumption that isn't verified, with the rules and the scenarios that rest on it."""
    from steam_layout import rules
    modules()
    assumptions, registry = rules.load_assumptions(), rules.load()
    waiting = [entry for entry in assumptions.values() if not entry.verified]
    resting = {entry.id: [meta for meta in SCENARIOS if entry.id in meta.rests] for entry in waiting}
    lines = [f"{len(SCENARIOS)} scenarios",
             f"Resting on an assumption that isn't verified: {len({m.name for found in resting.values() for m in found})}",
             f"Assumptions that aren't verified: {len(waiting)}"]
    for entry in waiting:
        way = "run both ways" if entry.id in SWITCHES else entry.layout.lower()
        lines.append(f"\n{entry.id} ({entry.status.split(':')[0].split(',')[0].lower()}; {way}): {entry.statement}")
        ruled = [rule.id for rule in registry.values() if entry.id in rule.rests_on]
        if ruled:
            lines.append("  Rules: " + ", ".join(ruled))
        lines.extend(f"  {meta.check}  {meta.name}" + (f" [frozen {meta.frozen}]" if meta.frozen else "")
                     for meta in resting[entry.id])
        if not ruled and not resting[entry.id]:
            lines.append("  No rule and no scenario rests on it")
    return "\n".join(lines)


def coverage():
    """Which layers no scenario puts on the stack, and which of those changed since the newest snapshot."""
    lines = []
    for variant in VARIANTS:
        titles = set(Layout(layout_data(variant)).titles.values())
        missing = sorted(titles - reached().get(variant, set()))
        lines.append(f"\n{variant}: {len(titles) - len(missing)} of {len(titles)} layers are on the stack in a scenario")
        lines.extend(f"  never: {title}" for title in missing)
        changed = uncovered(variant)
        lines.append("  Changed since the newest snapshot and in no scenario (R165): " + (", ".join(changed) or "none"))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="The scenario tests: what rests on an unverified assumption, and what they reach.")
    parser.add_argument("rule", nargs="?", help="a rule ID: list the scenarios that check it")
    parser.add_argument("--out", type=Path, help=f"folder of the release's record: write {RELEASE_LIST} there")
    args = parser.parse_args(argv)
    if args.rule:
        found = for_rule(args.rule)
        print(f"{len(found)} scenarios check {args.rule}")
        for meta in found:
            print(f"  {meta.check}  {meta.name}" + (f" [frozen {meta.frozen}]" if meta.frozen else ""))
        return 0
    shown = report()
    print(shown)
    print(coverage())
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / RELEASE_LIST).write_text(shown + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys
    from tests import scenario as registered             # the test files register with the imported module
    sys.exit(registered.main())
