"""Steering flick completion and final-output feedback for pad clicks."""


import unittest


from steam_layout.model import Layout


from tests.scenario import ScenarioCase, frozen_layout_data, layout_data, scenario


WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')


SCROLL_OWNERS = (
    'Steering | R1: W Key', 'Steering | L1: S Key',
    'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
    'Steering | LS: Tap Cover', *WINDOWS, 'Steering | LS: Double Tap Cover',
)


__all__ = ['Layout', 'SCROLL_OWNERS', 'ScenarioCase', 'WINDOWS', 'frozen_layout_data', 'layout_data', 'scenario', 'unittest']
