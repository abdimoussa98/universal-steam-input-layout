"""90.44 contracts: exact cleanup exclusions, explicit silence and inherited response."""


import copy


import functools


import importlib.util


import json


import unittest


from steam_layout.controllers import without_gyro_style


from steam_layout.model import Layout, actions, entries


from tests.scenario import ROOT, Pad, VARIANTS, frozen_layout_data, layout_data


from tests.support.fixtures.steering_entry_feedback import GUARD, commands


from tools.convert_runtime_ids import generate_lookup, ids_to_titles


def by_title(data):
    """The layout with its layer commands written by title, so two builds compare whatever their layer order (90.64)."""
    data = json.loads(data) if isinstance(data, str) else data
    text, _ = ids_to_titles(json.dumps(data), generate_lookup(data))
    return json.loads(text)


@functools.lru_cache(maxsize=None)
def previous(variant):
    path = ROOT / 'findings/2026-10-09-steering-entry-and-feedback/build_candidate.py'
    spec = importlib.util.spec_from_file_location('quiet_drivers_previous', path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    data, _ = builder.build(variant)
    return Layout(by_title(data))


def activators(layout, title):
    for source, group in layout.active(title).items():
        for name, slot in group.get('inputs', {}).items():
            for bank in ('activators', 'disabled_activators'):
                for index, (kind, entry) in enumerate(entries(slot.get(bank) or {})):
                    yield (source, name, bank, kind, index), entry


def without_haptic(entry):
    result = copy.deepcopy(entry)
    result.get('settings', {}).pop('haptic_intensity', None)
    if not result.get('settings'):
        result.pop('settings', None)
    return result


SCROLLS = ('Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down')     # the two stick scroll layers, since 90.52


def without_scroll_layers(layout, entry):
    """The entry without the removals of the two stick scroll layers, which the cover's removal lists have had since 90.52."""
    entry = copy.deepcopy(entry)
    binding = entry.get('bindings', {}).get('binding')
    if isinstance(binding, list):
        entry['bindings']['binding'] = [action for action in binding if not any(
            op == 'remove_layer' and target in SCROLLS for op, target in layout.layer_ops({'bindings': {'binding': action}}))]
    return entry


def without_right_pad(layout, entry):
    """(settings, commands) of an entry without its right pad removals. Since 90.53 the Steering modifier
    layers remove no right pad layer outside the clear to Base (author, 2026-10-10)."""
    kept = [action for action in actions(entry) if not any(
        op == 'remove_layer' and target.startswith('RTP:') for op, target in layout.layer_ops({'bindings': {'binding': action}}))]
    return entry.get('settings', {}), kept


def gyro_settings(layout, stack):
    """The same-mode property inheritance promised by the layout, not a sensor model."""
    settings, mode = {}, None
    for title in stack:
        group = layout.active(title).get('gyro')
        if group:
            if group['mode'] != mode:
                settings = {}
            mode = group['mode']
            settings.update(group.get('settings', {}))
    return mode, settings


__all__ = [name for name in globals() if not name.startswith("__")]
