"""Fresh toy layout constructors shared by engine, audit and simulator tests.

``act`` and ``stored_release`` accept the binding in stored JSON order and preserve
its settings. ``on``, ``press`` and ``release`` accept commands in execution order,
reverse arrays for Steam's bottom-to-top execution, and stringify settings. Keep
these APIs distinct: their fixture shapes and ordering are intentional.
"""

EMPTY = "controller_action empty_binding, , "
SW = "switches"


def act(binding, **settings):
    """Regular Press with the binding already in stored JSON order."""
    return {"Full_Press": {"bindings": {"binding": binding}, "settings": settings}}


def add(title):
    return f"controller_action add_layer {{{{Base::{title}}}}} 0 0, , "


def remove(title):
    return f"controller_action remove_layer {{{{Base::{title}}}}} 0 0, , "


def build(layers, modeshift=None):
    """layers: {title: {source: (mode, {input: activators})}}; the first title is the action set."""
    cm = {"title": "single-set-default :: test :: 1", "actions": {}, "action_layers": {},
          "preset": [], "group": []}
    gid = 0
    for index, (title, sources) in enumerate(layers.items()):
        key = f"Preset_{1000001 + index}"
        (cm["actions"] if index == 0 else cm["action_layers"])[key] = {"title": title}
        bindings = {}
        for source, (mode, inputs) in sources.items():
            gid += 1
            cm["group"].append({"id": str(gid), "mode": mode,
                                "inputs": {name: {"activators": a} for name, a in inputs.items()}})
            bindings[str(gid)] = f"{source} active"
        cm["preset"].append({"id": str(index), "name": key, "group_source_bindings": bindings})
    for group_id, (source, mode, inputs) in (modeshift or {}).items():
        cm["group"].append({"id": group_id, "mode": mode,
                            "inputs": {name: {"activators": a} for name, a in inputs.items()}})
        cm["preset"][0]["group_source_bindings"][group_id] = f"{source} inactive modeshift"
    return {"controller_mappings": cm}


def stored_release(binding):
    """Release Press with the binding already in stored JSON order."""
    return {"release": {"bindings": {"binding": binding}}}


def on(kind, *commands, **settings):
    """One activator entry; commands in execution order (stored bottom to top)."""
    stored = list(reversed(commands)) if len(commands) > 1 else commands[0]
    return {kind: {"bindings": {"binding": stored}, "settings": {k: str(v) for k, v in settings.items()}}}


def press(*commands, **settings):
    return on("Full_Press", *commands, **settings)


def release(*commands, **settings):
    return on("release", *commands, **settings)


def deep_window():
    """Win is three inputs from Base (a, b, x); Owner's button_y stays open under it."""
    return build({"Base": {"switch": ("switches", {"button_a": act(add("Mode"))})},
                  "Mode": {"switch": ("switches", {"button_b": act(add("Owner"))})},
                  "Owner": {"switch": ("switches", {"button_x": act(add("Win")), "button_y": act(remove("Owner"))})},
                  "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")), "button_a": act(EMPTY),
                                                  "button_b": act(EMPTY), "button_x": act(EMPTY)})}})


def bystander_window():
    """Button 1 enters L70, whose button 4 adds the window. Buttons 3 then 5 build EP > L60, which only
    binds button 2, so it stays under the window. It takes two bindings to build, so it can't be a single
    layer arriving mid-chain: the chain has to be replayed on top of it."""
    return build({"Base": {"switch": ("switches", {"button_1": act(add("L70")), "button_3": act(add("EP"))})},
                  "EP": {"switch": ("switches", {"button_5": act(add("L60"))})},
                  "L60": {"switch": ("switches", {"button_2": act(remove("L60"))})},
                  "L70": {"switch": ("switches", {"button_4": act([add("Win"), remove("L70")])})},
                  "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                  "button_1": act(EMPTY), "button_3": act(EMPTY),
                                                  "button_4": act(EMPTY), "button_5": act(EMPTY)})}})
