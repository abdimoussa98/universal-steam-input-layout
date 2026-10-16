"""The rule registry: the rule tables in resources/Layer Definition of Done.md (steam_layout/rules.py)."""


from pathlib import Path


import re


import subprocess


import sys


import tempfile


import unittest


from steam_layout import rules


from steam_layout.fixes import PIPELINE


from tests.support.discovery import resolve_tests


ROOT = Path(__file__).resolve().parents[3]


HEAD = "| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |\n|---|---|---|---|---|---|---|\n"


def row(rule_id="R101", checked="Not checked yet", rests="—", statement="Do the thing"):
    return f"| {rule_id} | {statement} | `A` on `B` | Author, 2026-10-02 | {checked} | {rests} | None |\n"


def read(text):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "registry.md"
        path.write_text(text, encoding="utf-8")
        return rules.load(path)


AHEAD = ("| ID | Assumption | Status | The layout | How to verify on the Deck | What rests on it |\n"
         "|---|---|---|---|---|---|\n")


def arow(assumption_id="A1", status="Verified by the author, 2026-09-29", layout="Relies on it", rests="R113, R115"):
    return f"| {assumption_id} | Steam does the thing | {status} | {layout} | Hold a button, add a layer | {rests} |\n"


__all__ = ['AHEAD', 'HEAD', 'PIPELINE', 'Path', 'ROOT', 'arow', 're', 'read', 'resolve_tests', 'row', 'rules', 'subprocess', 'sys', 'tempfile', 'unittest']
