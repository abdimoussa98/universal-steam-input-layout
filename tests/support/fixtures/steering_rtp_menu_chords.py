"""90.38 generated configuration, ordering, and narrow inverted-edge exception.

The contracts were last written against 90.42. 90.43 replaced `Steering | LS: Fallback Guard` with
`Steering | LS: Entry Guard`, and the tests below name the Entry Guard where the requirement still holds.
"""


import copy


import importlib.util


import json


from pathlib import Path


import unittest


from steam_layout import controllers


from steam_layout.model import Layout, entries


from tools.audit_command_budget import audit_layout


from tests.support.sources import without_release_text


ROOT = Path(__file__).resolve().parents[3]


ENTRY_GUARD = 'Steering | LS: Entry Guard'


STATEFUL_MENU = ('Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point')


FN_STEERING_CLEAR = ROOT / 'findings/2026-10-09-fn-haptics-and-steering-clear'          # the 90.42 build


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def release_builder(version, controller_type='controller_neptune'):
    """The builder of the findings folder whose stored build carries this version for this controller, newest folder
    first."""
    for folder in sorted(ROOT.glob('findings/*'), reverse=True):
        stored, script = folder / 'default-candidate.json', folder / 'build_candidate.py'
        if not (stored.exists() and script.exists()):
            continue
        mappings = json.loads(stored.read_text())['controller_mappings']
        if mappings['title'].endswith(f' :: {version}') and mappings.get('controller_type') == controller_type:
            return module(script, 'release_build')
    return None


build = module(ROOT / 'findings/2026-10-08-steering-rtp-and-menu-chords/build_candidate.py', 'steering_rtp_build')


__all__ = ['ENTRY_GUARD', 'FN_STEERING_CLEAR', 'Layout', 'Path', 'ROOT', 'STATEFUL_MENU', 'audit_layout', 'build', 'controllers', 'copy', 'entries', 'importlib', 'json', 'module', 'release_builder', 'unittest', 'without_release_text']
