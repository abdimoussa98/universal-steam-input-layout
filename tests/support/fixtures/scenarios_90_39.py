"""90.39 candidate scenarios; explicit candidate data, separate from live coverage.

F1–F9/G1 and R1–R4 preserve the archived 90.31/90.32 gestures. Other
scenarios exercise later fixes against the restored fallback window.
"""


import itertools


import json


from pathlib import Path


import unittest


from steam_layout.simulator import desktop


from tests.scenario import Pad, ScenarioCase as LiveScenarioCase, SWITCHES, data_fingerprint, scenario


ROOT = Path(__file__).resolve().parents[3]


HERE = ROOT / 'findings/2026-10-09-fallback-window-backport'


CANDIDATE_REACHED = {}


_candidates = {}


def candidate(variant):
    if variant not in _candidates:
        _candidates[variant] = json.loads((HERE / f'single-set-{variant}-fallback-window_hold-gyro_90.39.json').read_text())
    return _candidates[variant]


class ScenarioCase(LiveScenarioCase):
    fixture_kind = 'candidate'
    fixture_controller = 'neptune'
    fixture_version = '90.39'

    def each(self, start=None, variants=('default', 'alternative'), desktop_configuration=False, **options):
        meta = getattr(getattr(self, self._testMethodName), 'scenario', None)
        names = [SWITCHES[a][0] for a in (meta.either if meta else ())]
        ways = [SWITCHES[a][1] for a in (meta.either if meta else ())]
        for variant in variants:
            for way in itertools.product(*ways):
                data = candidate(variant)
                source_data = data
                data_fingerprint(source_data)
                if desktop_configuration:
                    data = desktop(data)
                chosen = {**options, **dict(zip(names, way))}
                pad = Pad(variant, start=None if start == 'steering' else start, data=data, **chosen)
                if start == 'steering':
                    pad.enter_steering()
                self._pad = pad
                try:
                    yield pad.mark()
                finally:
                    self.record_cell(pad, source_data, kind='candidate', controller='neptune', version='90.39',
                                     desktop_configuration=desktop_configuration, start=start)
                    CANDIDATE_REACHED.setdefault(variant, set()).update(pad.reached())


WINDOW, HOLD, GUARD = "Steering | LS: Fallback Window", "Steering | LS: Fallback Hold", "Steering | LS: Entry Guard"


NORTH, SOUTH = ("joystick", "dpad_north"), ("joystick", "dpad_south")


BOTH = (("up", "W", NORTH), ("down", "S", SOUTH))


def left_steering(pad):
    return pad.lacks("Steering", HOLD, WINDOW)


WINDOW, HOLD = "Steering | LS: Fallback Window", "Steering | LS: Fallback Hold"


TAPS = (("Start", "TAB"), ("Select", "ESCAPE"), ("R1", "mouse_wheel SCROLL_UP"), ("L1", "mouse_wheel SCROLL_DOWN"))


__all__ = [name for name in globals() if not name.startswith("__")]
