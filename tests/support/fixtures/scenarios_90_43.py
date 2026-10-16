"""90.43 entry protection, driver ownership during recovery, and layer beeps."""


import unittest


from tests.scenario import DIRECTIONS, ScenarioCase, scenario, old_inverted_chord


GUARD = 'Steering | LS: Entry Guard'


DRIVERS = {'R1': 'Steering | R1: W Key', 'L1': 'Steering | L1: S Key'}


MODIFIERS = {'up': 'Steering | LS Up: Modifier 1', 'down': 'Steering | LS Down: Modifier 0'}


RAMP = ('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1')


def home(gyro):
    return ('Base', 'Gyro') if gyro else ('Base',)


def enter(pad):
    return pad.enter_steering(settle=False)


def both_home_states(case):
    for gyro in (False, True):
        for pad in case.each(start=home(gyro)):
            yield gyro, pad


def both_armed_states(case):
    for gyro, pad in both_home_states(case):
        pad.enter_steering().mark()
        yield gyro, pad


__all__ = [name for name in globals() if not name.startswith("__")]
