"""90.43 static contracts that binary-input scenarios cannot establish."""


import json


import re


import unittest


from steam_layout.model import Layout, actions, entries


from tests.scenario import Pad, VARIANTS, layout_data


GUARD = 'Steering | LS: Entry Guard'


OLD_GUARD = 'Steering | LS: Fallback Guard'


COMMAND = re.compile(r'controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|\d+) (\d+) (\d+)')


FN = {f'{prefix}Menu {side}: Fn Layer' for prefix in ('', 'Stateful | ') for side in ('Left', 'Right')}


def commands(layout, entry):
    return [(match.group(1), layout.resolve(match.group(2)), match.group(3), match.group(4))
            for action in reversed(actions(entry)) if (match := COMMAND.search(action))]


__all__ = [name for name in globals() if not name.startswith("__")]
