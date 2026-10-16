"""Bounded source preparation for tests; callers always own the returned dictionaries.

Paths and exact bytes identify a source. Reading again notices changed files, while
parsing and title conversion are reused only for the same content and parser mode.
No audit, builder, conversion, fix pipeline or simulator result is cached here.
"""
import copy
from functools import lru_cache
import json
from pathlib import Path

from tools.audit_command_budget import unique_object
from tools.convert_runtime_ids import generate_lookup, ids_to_titles

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=16)
def _parsed(path, raw, strict):
    return json.loads(raw, object_pairs_hook=unique_object if strict else None)


def load_json(path, *, strict=False):
    """A private copy of a JSON source, preserving stored order and parser behavior."""
    path = Path(path).resolve()
    return copy.deepcopy(_parsed(str(path), path.read_bytes(), strict))


@lru_cache(maxsize=4)
def _neptune_bundle(path, raw):
    original = _parsed(path, raw, True)
    text = raw.decode("utf-8")
    lookup = generate_lookup(original)
    readable, count = ids_to_titles(text, lookup)
    cm = json.loads(readable)["controller_mappings"]
    names = {key: value["title"] for key, value in {**cm["actions"], **cm["action_layers"]}.items()}
    return dict(raw=text, original=original, readable=readable, count=count, lookup=lookup, cm=cm,
                groups={group["id"]: group for group in cm["group"]},
                presets={names[preset["name"]]: preset for preset in cm["preset"]})


def neptune_bundle(path):
    """Private numeric/readable views for Neptune contracts, with duplicate keys rejected."""
    path = Path(path).resolve()
    return copy.deepcopy(_neptune_bundle(str(path), path.read_bytes()))


def without_release_text(data):
    """A private comparison copy; preserve every field and stored order except install text."""
    result = copy.deepcopy(data)
    for field in ("title", "description"):
        result["controller_mappings"].pop(field)
    return result
