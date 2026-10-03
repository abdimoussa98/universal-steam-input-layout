"""The exceptions register: every accepted finding, in one list.

An exception is one place where the layout breaks a rule and that is accepted,
or is a known gap that still has to end. They all live under `exceptions` in
steam_layout/flow_config.json:

    {"rule": "R139",                     the rule it is an exception to (resources/Layer Definition of Done.md)
     "scope": {...},                     what it covers; the shape depends on the rule, see below
     "status": "allow" or "todo",        accepted for good, or a gap that a to-do will close
     "why": "...",                       the reason
     "decided": "Author, 2026-10-02",    who decided it, and when
     "todo": "todos.md: ..." or null}    the to-do that ends it; required when the status is "todo"

Scope, by rule:

    R139, R145   {"layers": [...], "inputs": [...]}                      the Flow audit's inherited inputs
                 (`inputs` may be {"default": [...], "alternative": [...]})
    R144         {"cover": "...", "checks": [...]}                        the cover check
    R132         {"layers": [...], "removes": [...]}                      a removal the Cleanup audit keeps
    R140         {"target": "...", "source": "...", "input": "..."}       a route the Window audit allows
    R136         {"kind": "touchpad"}                                     the hidden-exit pairs set aside
    other rules  any object, for example {"note": "..."}: a record that no audit reads

The audits still read the sections they always read. `expand` fills
`decisions`, `covers.allow`, `cleanups.keep` and `cleanups.touchpad_exits` from the register, and `window`
adds the R140 entries to the Window audit's stacks config, so one entry format
serves all four. Titles use default-layout names, as everywhere in this file.
"""
import copy
import json
from pathlib import Path

from .rules import RULE_ID

REGISTER = Path(__file__).with_name("flow_config.json")
STATUSES = ("allow", "todo")
FIELDS = ("rule", "scope", "status", "why", "decided", "todo")
FLOW = ("R139", "R145")
SCOPES = {"R139": ("layers", "inputs"), "R145": ("layers", "inputs"), "R144": ("cover", "checks"),
          "R132": ("layers", "removes"), "R140": ("target", "source", "input"), "R136": ("kind",)}


def check(entries):
    """The entries, unchanged, once each has every field and a scope that fits its rule."""
    for entry in entries:
        missing = [field for field in FIELDS if field not in entry]
        if missing:
            raise ValueError(f"an exception needs {', '.join(missing)}: {entry}")
        if not RULE_ID.fullmatch(entry["rule"] or ""):
            raise ValueError(f"an exception needs a rule ID: {entry}")
        if entry["status"] not in STATUSES:
            raise ValueError(f"an exception's status is one of {STATUSES}: {entry}")
        if not entry["why"] or not entry["decided"]:
            raise ValueError(f"an exception needs a why and who decided it: {entry}")
        if entry["status"] == "todo" and not entry["todo"]:
            raise ValueError(f"an exception with status todo names the to-do that ends it: {entry}")
        scope = entry["scope"]
        if not scope or any(key not in scope for key in SCOPES.get(entry["rule"], ())):
            raise ValueError(f"{entry['rule']}: the scope needs {SCOPES.get(entry['rule'], 'something')}: {entry}")
    return entries


def load(path=None):
    """The register's entries, checked."""
    return check(json.loads(Path(path or REGISTER).read_text(encoding="utf-8")).get("exceptions", []))


def of(entries, rule):
    """The entries for one rule."""
    return [entry for entry in entries if entry["rule"] == rule]


def expand(config):
    """A copy of `config` with the sections the audits read filled in from its `exceptions`."""
    config = copy.deepcopy(config)
    for entry in check(config.get("exceptions", [])):
        scope, rule = entry["scope"], entry["rule"]
        if rule in FLOW:
            config.setdefault("decisions", []).append(
                {"layers": scope["layers"], "inputs": scope["inputs"], "status": entry["status"], "why": entry["why"]})
        elif rule == "R144":
            config.setdefault("covers", {}).setdefault("allow", []).append(
                {"cover": scope["cover"], "checks": scope["checks"], "reason": entry["why"]})
        elif rule == "R132":
            config.setdefault("cleanups", {}).setdefault("keep", []).append(
                {"layers": scope["layers"], "removes": scope["removes"], "why": entry["why"]})
        elif rule == "R136" and scope["kind"] == "touchpad":
            config.setdefault("cleanups", {})["touchpad_exits"] = entry["why"]
    return config


def load_config(path=None):
    """The rules file with its exceptions expanded: what the Flow, cover and Cleanup audits read."""
    return expand(json.loads(Path(path or REGISTER).read_text(encoding="utf-8")))


def window(stacks_config, entries):
    """A copy of the Window audit's stacks config with the register's R140 routes as its decisions."""
    config = copy.deepcopy(stacks_config)
    for entry in of(check(entries), "R140"):
        scope = entry["scope"]
        config.setdefault("targets", {}).setdefault(scope["target"], {}).setdefault("decisions", []).append(
            {"source": scope["source"], "input": scope["input"], "status": entry["status"], "why": entry["why"]})
    return config
