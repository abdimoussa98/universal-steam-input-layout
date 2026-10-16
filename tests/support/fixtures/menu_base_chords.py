"""Reference comparison and generated-layout contract for 90.37."""


import copy


import importlib.util


import json


from pathlib import Path


import unittest


from steam_layout.controllers import without_gyro_style


from steam_layout.model import Layout, map_title


ROOT = Path(__file__).resolve().parents[3]


spec = importlib.util.spec_from_file_location(
    'menu_base_chords', ROOT / 'findings/2026-10-06-menu-base-chords/build_candidate.py')


build = importlib.util.module_from_spec(spec)


spec.loader.exec_module(build)


__all__ = ['Layout', 'Path', 'ROOT', 'build', 'copy', 'importlib', 'json', 'map_title', 'spec', 'unittest', 'without_gyro_style']
