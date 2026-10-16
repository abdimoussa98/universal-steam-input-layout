"""90.44: inward Entry Guard recovery, quiet drivers and retained stateful layers."""


import unittest


from tests.scenario import ScenarioCase, scenario


from tests.support.fixtures.scenarios_90_43 import DRIVERS, GUARD, MODIFIERS, home


from tests.support.fixtures.steering_entry_quiet_drivers import gyro_settings


ORDERS = (('L1', 'R1'), ('R1', 'L1'))


CURSOR = 'Cursor Gyro'


def enter_with_drivers(pad, drivers):
    pad.hold('Start').click('LS')
    for driver in drivers:
        pad.hold(driver)
    return pad.mark().let_go('Start')


def toggle(pad, first, second, released, gap=30):
    last = second if released == first else first
    return pad.hold(first).wait(30).hold(second).wait(30).let_go(released).wait(gap).let_go(last).wait(400)


__all__ = [name for name in globals() if not name.startswith("__")]
