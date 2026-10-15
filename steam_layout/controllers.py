"""The controllers this repo has layouts for, in one place.

Ibex, the Steam Controller 2, is the base layout (R177): every layout change is made on it, and
the Steam Deck's and the DualSense Edge's layouts are converted from an Ibex release by their
rules (steam_layout/convert.py). Each controller has a working directory with one
`<stem>_latest.json` and `.vdf` per variant, and its snapshots under `versions/<name>/<version>/`.

    controllers.BASE                                  # the Ibex entry
    controllers.get("dse").controller_type            # "controller_ps5_edge"
    controllers.get("neptune").working_json("default")
    controllers.for_name("dse_single-set-default_hold-gyro_latest.json").name     # "dse"
    controllers.for_type("controller_neptune").name                              # "neptune"
    controllers.with_layouts()                        # the ones whose directory has working layouts

The header values are what Steam writes for each controller: `controller_caps` from Steam's
own exports (the Deck from the working layouts, the Steam Controller 2 from the exploratory
layout of findings/2026-07-11-layer-order-swap/, the DualSense Edge from archived/dse/).

Plan: plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 1.
"""
from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ("default", "alternative")
# gyro_to_2d_conversion_style, "3DOF to 2D Conversion Style" in Steam's editor (read from the Steam client, 2026-10-15)
GYRO_STYLES = {0: "Yaw", 1: "Roll", 2: "Yaw + Roll", 3: "Local Space", 4: "Player Space", 5: "World Space",
               6: "Laser Pointer"}
GYRO_STYLE = "gyro_to_2d_conversion_style"
STICK_TOUCHES = (("joystick", "touch"), ("right_joystick", "touch"))

_DESCRIPTION = ("WASD movement, gyro aiming, right-stick turn assist, and circular trackpad scrolling. "
                "{fire}: mouse buttons; {mods}: modifiers. Includes Fn controls, Steering, Cursor Gyro, "
                "and Gamepad modes.")
_EDGE_DESCRIPTION = ("WASD movement, gyro aiming, right-stick turn assist, and touchpad swipes for Escape, "
                     "Enter, Tab and Backspace. {fire}: mouse buttons; {mods}: modifiers; mute: middle mouse. "
                     "Includes Fn controls, Steering, Cursor Gyro, and Gamepad modes.")
_ROLES = {"default": {"fire": "L2/R2", "mods": "L1/R1"}, "alternative": {"fire": "L1/R1", "mods": "L2/R2"}}


def _per_variant(text):
    return {variant: text.format(**_ROLES[variant]) for variant in VARIANTS}


@dataclass(frozen=True)
class Controller:
    """One controller: where its files are, what Steam calls it, and how Ibex converts to it."""
    name: str                     # the directory, and the first word of a release tag (`neptune-v90.75`)
    label: str                    # what the controller is called
    controller_type: str          # controller_mappings.controller_type
    controller_caps: str          # controller_mappings.controller_caps, as Steam exports it for this controller
    prefix: str                   # the start of every file stem: "ibex_", "dse_"; "" for the Deck (R177's stems)
    gyro_style: int               # gyro_to_2d_conversion_style in every gyro-to-mouse group (Part 3 of the plan)
    descriptions: dict            # variant -> controller_mappings.description
    urls: dict                    # variant -> controller_mappings.url (a Steam Workshop item, or empty)
    base: bool = False            # the base layout (R177); every other one is a conversion of it
    absent: frozenset = frozenset()          # (source, input) the controller lacks or the author left out (R178)
    absent_sources: frozenset = frozenset()  # sources it lacks: every bind on them is absent (R178)
    swaps: tuple = ()             # ((source, input), (source, input)): inputs that trade places (R181)
    whole_pad: bool = False       # the left pad's role goes to the whole touchpad, center_trackpad (R183); the
                                  # two pad-touch switches stay: on the Edge they are the touchpad's halves
    mute: str = ""                # the input of the mute button, bound in Base (R184)
    always_gyro: bool = False     # the gyro enable masks come off (R185)
    first_version: str = "1.0"    # the version of a controller's first layout (Ibex's and the Edge's own lines)
    built_until: str = ""         # the last version built directly, before the base layout (R177)

    @property
    def directory(self):
        return ROOT / self.name

    @property
    def versions(self):
        return ROOT / "versions" / self.name

    def stem(self, variant):
        return f"{self.prefix}single-set-{variant}_hold-gyro"

    def working_json(self, variant):
        return self.directory / f"{self.stem(variant)}_latest.json"

    def working_vdf(self, variant):
        return self.directory / f"{self.stem(variant)}_latest.vdf"

    def snapshot(self, variant, version, suffix=".json"):
        """`versions/<name>/<version>/<stem>_<version>.json` (or `.vdf`)."""
        return self.versions / version / f"{self.stem(variant)}_{version}{suffix}"

    def working(self):
        """The working layouts that exist, as paths, in variant order."""
        return [path for variant in VARIANTS for path in [self.working_json(variant)] if path.exists()]

    def has_layouts(self):
        return bool(self.working())

    def lacks(self, source, name):
        """True if a bind on (source, input) can never fire on this controller (R178)."""
        return source in self.absent_sources or (source, name) in self.absent

    def variant_of(self, path):
        """The variant a working layout or snapshot of this controller is, from its file name."""
        name = Path(path).name
        for variant in VARIANTS:
            if name.startswith(self.stem(variant) + "_"):
                return variant
        raise ValueError(f"{name} is no layout of {self.name}")


IBEX = Controller(
    name="ibex", label="Steam Controller 2", controller_type="controller_triton", controller_caps="1096859647",
    prefix="ibex_", gyro_style=4, descriptions=_per_variant(_DESCRIPTION), urls={v: "" for v in VARIANTS},
    base=True)
NEPTUNE = Controller(
    name="neptune", label="Steam Deck", controller_type="controller_neptune", controller_caps="23117823",
    prefix="", gyro_style=2, descriptions=_per_variant(_DESCRIPTION),
    urls={"default": "workshop://3660206238", "alternative": "workshop://3660203920"}, built_until="90.74")
DSE = Controller(
    name="dse", label="DualSense Edge", controller_type="controller_ps5_edge", controller_caps="852975615",
    prefix="dse_", gyro_style=4, descriptions=_per_variant(_EDGE_DESCRIPTION), urls={v: "" for v in VARIANTS},
    absent=frozenset(STICK_TOUCHES), absent_sources=frozenset({"right_trackpad"}),
    swaps=((("switch", "button_back_left_upper"), ("switch", "button_back_left")),
           (("switch", "button_back_right_upper"), ("switch", "button_back_right"))),
    whole_pad=True, mute="button_capture", always_gyro=True)

CONTROLLERS = (IBEX, NEPTUNE, DSE)
BASE = IBEX
_BY_NAME = {controller.name: controller for controller in CONTROLLERS}
_BY_TYPE = {controller.controller_type: controller for controller in CONTROLLERS}


def get(name):
    """The controller of a directory name: "ibex", "neptune" or "dse"."""
    if name not in _BY_NAME:
        raise ValueError(f"unknown controller {name!r}: one of {', '.join(_BY_NAME)}")
    return _BY_NAME[name]


def for_type(controller_type):
    """The controller of a `controller_type`, or None."""
    return _BY_TYPE.get(controller_type)


def of_layout(data):
    """The controller a layout dict is for, by its `controller_type`, or None."""
    return for_type(data.get("controller_mappings", {}).get("controller_type"))


def for_name(name):
    """The controller a working layout or snapshot file name belongs to: the one whose stem prefix starts
    it, else the Deck, whose stems have none."""
    name = Path(name).name
    for controller in CONTROLLERS:
        if controller.prefix and name.startswith(controller.prefix):
            return controller
    return NEPTUNE


def for_path(path):
    """The controller of a file under a controller directory or its versions folder, else by its name."""
    parts = Path(path).resolve().parts
    for controller in CONTROLLERS:
        for top in (controller.directory, controller.versions):
            if parts[:len(top.parts)] == top.parts:
                return controller
    return for_name(path)


def with_layouts():
    """The controllers whose directory has working layouts, base first."""
    return [controller for controller in CONTROLLERS if controller.has_layouts()]


def working_layouts():
    """Every working layout of every controller, base first."""
    return [path for controller in with_layouts() for path in controller.working()]


def without_gyro_style(value):
    """`value`, a group's settings or anything holding them, with every gyro style left out: for comparing a layout
    with one from before each controller stated its own style in every gyro group (R177, R179, R180)."""
    if isinstance(value, dict):
        return {key: without_gyro_style(item) for key, item in value.items() if key != GYRO_STYLE}
    if isinstance(value, list):
        return [without_gyro_style(item) for item in value]
    return value


VERSION = re.compile(r"^\d+(\.\d+)+$")


def version_key(text):
    """A version as a tuple that orders by number: "90.10" -> (90, 10), higher than "90.9"."""
    if not VERSION.match(text or ""):
        raise ValueError(f"not a version: {text!r}")
    return tuple(int(part) for part in text.split("."))


def title_version(title):
    """The version at the end of a layout title: `single-set-default :: always-gyro :: 90.74` -> "90.74"."""
    return title.rsplit(" :: ", 1)[-1]


def next_version(text):
    """The version after this one: "90.74" -> "90.75", "1.0" -> "1.1"."""
    parts = list(version_key(text))
    parts[-1] += 1
    return ".".join(str(part) for part in parts)
