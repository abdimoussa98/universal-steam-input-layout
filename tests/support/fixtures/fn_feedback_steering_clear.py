"""90.42: Fn feedback and the full-deflection exit from Steering."""


import re


import unittest


from steam_layout.model import Layout, actions, always_on_layers, entries


from tests.scenario import VARIANTS, frozen_layout_data, layout_data


FN = {f'{prefix}Menu {side}: Fn Layer'
      for prefix in ('', 'Stateful | ') for side in ('Left', 'Right')}


ADD = re.compile(r'controller_action add_layer (\{\{.+?\}\}|\d+) (\d+) (\d+)')


REMOVE = re.compile(r'controller_action remove_layer (\{\{.+?\}\}|\d+) (\d+) (\d+)')


def steering_family(layout):
    return {title for title in layout.presets
            if title == 'Steering' or title.startswith('Steering | ')}


__all__ = ['ADD', 'FN', 'Layout', 'REMOVE', 'VARIANTS', 'actions', 'always_on_layers', 'entries', 'frozen_layout_data', 'layout_data', 're', 'steering_family', 'unittest']
