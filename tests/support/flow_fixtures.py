"""Fresh flow fixtures; entry commands are supplied in execution order.

Unlike ``layouts.build``, ``fixture`` accepts complete source specs, uses zero-based
group IDs and returns a Layout. Preserve those differences for mutation tests.
"""
from steam_layout.model import Layout
from tests.support.layouts import EMPTY, add, remove as rem


def entry(*commands, **settings):
    """Commands in execution order (stored bottom to top)."""
    e = {"bindings": {"binding": list(reversed(commands)) if len(commands) > 1 else commands[0]}}
    if settings:
        e["settings"] = {k: str(v) for k, v in settings.items()}
    return e


def inp(**activators):
    return {"activators": activators}


def fixture(layers):
    """layers: {title: {source: {"mode": ..., "inputs": {...}}}}; the first title is the action set."""
    cm = {"title": "fixture", "actions": {}, "action_layers": {}, "preset": [], "group": []}
    for n, (title, sources) in enumerate(layers.items()):
        key = f"Preset_{1000001 + n}"
        (cm["actions"] if n == 0 else cm["action_layers"])[key] = {"title": title}
        bindings = {}
        for source, spec in sources.items():
            gid = str(len(cm["group"]))
            cm["group"].append({"id": gid, "mode": spec.get("mode", "switches"),
                                "inputs": spec.get("inputs", {}), "settings": {}})
            bindings[gid] = source + " active"
        cm["preset"].append({"id": str(n), "name": key, "group_source_bindings": bindings})
    return Layout({"controller_mappings": cm})


def switches(**inputs):
    return {"switch": {"mode": "switches", "inputs": inputs}}


def cover_layout():
    """An owner (A) that applies a cover and a second overlay (Mid), and releases into a window (W)."""
    return fixture({
        "Base": switches(left_bumper=inp(chord=entry(add("A"), chord_button=1))),
        "A": {"switch": {"mode": "switches", "inputs": {
            "left_bumper": inp(release=entry(rem("A"), add("W")))}},
            "button_diamond": {"mode": "four_buttons", "inputs": {
                "button_a": inp(chord=entry(add("Cover"), chord_button=1)),
                "button_b": inp(chord=entry(add("Mid"), chord_button=1))}}},
        "Mid": {"button_diamond": {"mode": "four_buttons", "inputs": {"button_y": inp(Full_Press=entry("key_press Y, , "))}}},
        # The cover only changes the release: it removes the owner, then itself.
        "Cover": switches(left_bumper=inp(release=entry(rem("A"), rem("Cover")))),
        "W": switches(always_on_action=inp(Full_Press=entry(rem("W"), delay_start=150)))})
