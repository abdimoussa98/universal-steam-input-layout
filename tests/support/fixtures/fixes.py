"""The post-install fix pipeline (steam_layout.fixes)."""


import copy


import json


from pathlib import Path


import subprocess


import sys


import tempfile


import unittest


from steam_layout import controllers


from steam_layout.fixes import PIPELINE, apply_all


ROOT = Path(__file__).resolve().parents[3]


def load(variant):
    return json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text())


__all__ = ['PIPELINE', 'Path', 'ROOT', 'apply_all', 'controllers', 'copy', 'json', 'load', 'subprocess', 'sys', 'tempfile', 'unittest']
