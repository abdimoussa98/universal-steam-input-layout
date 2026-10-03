"""Make every cleanup function and release follow the six cleanup rules.

The Cleanup audit (audit_cleanups.py, steam_layout/cleanups.py) finds what is
wrong; this fix resolves exactly those findings, so the two can't drift apart:

    guard mismatch     the odd cleanup's either-button chord gets the layer's full guard
    left below/above   the missing layers are added to the cleanup's list
    outside the guard  the removal is dropped
    never there        the removal is dropped (cleanup functions and releases;
                       deliberate clears and the stick-touch trio are exempt)
    hidden cleanup     the hiding layer carries the cleanup on that input: one chord
                       with either of its guard buttons, beside a repeating removal of
                       the list its other cleanups use

Rules and decisions: findings/2026-10-02-cleanup-boundaries/README.md and
findings/2026-10-02-cleanup-audit/README.md. A removal kept by an exception to
R132 in the exceptions register (steam_layout/flow_config.json) is never dropped.

It only removes entries from removal lists or adds removals and cleanup
entries. It never touches an add or the order of the entries it keeps, so the
modifier rocking (tests/test_modifier_rocking.py) is unchanged. Idempotent;
works with numeric IDs or title tokens.
"""
from collections import Counter
import json
from pathlib import Path

from ..cleanups import BUTTONS, Cleanups, kept, name, run
from ..exceptions import load_config
from ..flow_model import BITS
from ..model import EMPTY, TARGET, Layout, actions, entries

RULES = Path(__file__).resolve().parents[1] / "flow_config.json"


def chord_mask(buttons):
    """The chord mask whose bits are exactly these buttons (a trigger's edge and click both count)."""
    mask = 0
    for bit, controls in BITS.items():
        if isinstance(controls, list) and controls and all(BUTTONS.get(c) in buttons for c in controls):
            mask |= 1 << bit
    return mask


def entry_of(layout, t):
    activators = layout.active(t.layer)[t.source]["inputs"][t.input]["activators"]
    return list(entries(activators))[t.index][1]


def set_binding(entry, commands):
    entry.setdefault("bindings", {})["binding"] = commands[0] if len(commands) == 1 else commands


def removal(layout, title, like):
    """A remove_layer command for `title`, in the same reference style as `like`."""
    if "{{" in like:
        ref = "{{%s::%s}}" % (layout.base, title)
    else:
        key = next(k for k, v in layout.titles.items() if v == title)
        ref = str(layout.order.index(key) + 1)
    return f"controller_action remove_layer {ref} 0 0, , "


def _guards(layout, c, keep):
    """Give a cleanup whose guard is narrower than its layer's the layer's full guard."""
    changed = []
    for host in c.layers:
        found = list(c.cleanups(host))
        everywhere = frozenset().union(*[g for _, g, _ in found]) if found else frozenset()
        for t, guard, _ in found:
            expected = everywhere - {name(t.control)}
            if guard == expected:
                continue
            activators = layout.active(host)[t.source]["inputs"][t.input]["activators"]
            chords = [e for kind, e in entries(activators) if kind == "chord"]
            settings = chords[0].get("settings", {}) if len(chords) == 1 else {}
            if len(chords) != 1 or "gyro_ratchet_button_mask" not in settings \
                    or not all(a.startswith(EMPTY) for a in actions(chords[0])):
                raise ValueError(f"{host} {name(t.control)}: guard mismatch on an input without one empty mask chord")
            settings["gyro_ratchet_button_mask"] = str(chord_mask(expected))
            settings["gyro_ratchet_button_requireany_or_all"] = "0"
            changed.append(f"{host} / {name(t.control)}: guard {'+'.join(sorted(expected))}")
    return changed


def _missing(layout, c, keep):
    """Add the layers a cleanup leaves below or above it. They run after the layers it already removes."""
    changed = []
    for host in c.layers:
        if not c.reached(host):
            continue
        for t, guard, removed in c.cleanups(host):
            missing = sorted({target for target, _ in c.left(host, t, guard, removed)}, key=list(layout.presets).index)
            if not missing:
                continue
            entry = entry_of(layout, t)
            commands = actions(entry)
            set_binding(entry, [removal(layout, x, commands[0]) for x in reversed(missing)] + commands)
            changed.append(f"{host} / {name(t.control)}: adds {', '.join(missing)}")
    return changed


def _unneeded(layout, c, keep):
    """Drop the removals that are outside the guard or of a layer that is never there."""
    changed = []
    for host in c.layers:
        if not c.reached(host):
            continue
        for t in c.inv.by_layer(host):
            drop = {target for target in c.unneeded(host, t) if (host, target) not in keep}
            if not drop:
                continue
            entry = entry_of(layout, t)
            commands = actions(entry)
            left = [a for a in commands
                    if not ((m := TARGET.search(a)) and m.group(1) == "remove_layer" and layout.resolve(m.group(2)) in drop)]
            if not left:
                raise ValueError(f"{t.describe()}: dropping {sorted(drop)} would leave nothing")
            set_binding(entry, left)
            changed.append(f"{host} / {name(t.control)} {t.activator}: drops {', '.join(sorted(drop))}")
    return changed


def _hidden(layout, c, keep):
    """Let a layer that hides a cleanup below carry its own cleanup on that input."""
    todo = {}
    for host in c.layers:
        if not c.reached(host):
            continue
        for t, guard, _ in c.cleanups(host):
            for upper in c.hiding(host, t, guard):
                todo.setdefault((upper, t.source, t.input), t)
    changed = []
    for (upper, source, inp), t in sorted(todo.items()):
        own = list(c.cleanups(upper))
        if not own:
            raise ValueError(f"{upper} hides a cleanup on {source}/{inp} and has no cleanup to copy")
        scope = Counter(removed for _, _, removed in own).most_common(1)[0][0]
        model = next(x for x, _, removed in own if removed == scope)
        guard = frozenset().union(*[g for _, g, _ in own]) - {name(t.control)}
        activators = layout.active(upper)[source]["inputs"][inp]["activators"]
        if set(activators) & {"Full_Press", "chord"} or sum(1 for _ in entries(activators)) > 1:
            raise ValueError(f"{upper} {source}/{inp}: no room for a cleanup next to {list(activators)}")
        cleanup = {"bindings": {"binding": list(actions(entry_of(layout, model)))}, "settings": {"hold_repeats": "1"}}
        set_binding(cleanup, actions(cleanup))
        chord = {"bindings": {"binding": EMPTY + ", , "},
                 "settings": {"gyro_ratchet_button_mask": str(chord_mask(guard)),
                              "gyro_ratchet_button_requireany_or_all": "0", "interruptable": "0"}}
        layout.active(upper)[source]["inputs"][inp]["activators"] = {"Full_Press": cleanup, "chord": chord, **activators}
        changed.append(f"{upper} / {name((source, inp))}: carries its cleanup (guard {'+'.join(sorted(guard))})")
    return changed


def fix(data, config=None):
    """Resolve every Cleanup audit finding in place. Returns what changed and what is left.

    The stacks are built once. Every edit here is to a list the backward chains don't follow (a cleanup
    function) or drops a layer that is never on the stack at that point, so the stacks stay valid.
    """
    config = load_config(RULES) if config is None else config
    first, stacks = run(data, config)
    if first["ok"]:
        return {"changed": [], "remaining": 0}     # already clean: the usual case in the pipeline
    variant = "alternative" if "alternative" in data["controller_mappings"].get("title", "") else "default"
    keep = kept(config, variant)
    changed = []
    for phase in (_guards, _missing, _unneeded, _hidden):
        layout = Layout(data)
        changed += phase(layout, Cleanups(layout, stacks), keep)
    return {"changed": changed, "remaining": len(run(data, config, stacks=stacks)[0]["findings"])}
