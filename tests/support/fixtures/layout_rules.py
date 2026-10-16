"""Static checks for rules that nothing checked before (rule registry plan, phase 15).

Each asks what the layouts hold, with no presses. The rule is named beside the test, and the test is named
under that rule's "Checked by" in resources/Layer Definition of Done.md.
"""


import json


import re


import unittest


from steam_layout import changes, exceptions


from steam_layout.cleanups import Cleanups


from steam_layout.model import Layout, bindings, entries, map_title


from tests.scenario import RENAME, VARIANTS, layout_data


LEGACY_HOLDS = {"LTP: Arrow Keys", "RTP: Mouse Buttons", "LTP: Middle Click", "RTP: Middle Click"}   # R101's entry in the register


__all__ = ['Cleanups', 'LEGACY_HOLDS', 'Layout', 'RENAME', 'VARIANTS', 'bindings', 'changes', 'entries', 'exceptions', 'json', 'layout_data', 'map_title', 're', 'unittest']
