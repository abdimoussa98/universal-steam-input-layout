"""Read a Steam Input layout JSON: layers, active groups and bindings.

Works with numeric runtime IDs or readable `{{Base::Title}}` tokens.
"""
import re

LAYER_COMMAND = re.compile(r"controller_action (add_layer|remove_layer|hold_layer)\b")
MODE_SHIFT = re.compile(r"mode_shift (\S+) (\d+)")
TARGET = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|\d+)")
TOKEN = re.compile(r"\{\{(?:[^:}]+::)?(.+?)\}\}")
EMPTY = "controller_action empty_binding"


def map_title(title, mapping):
    """Rename default-layout titles for a variant, for example {"L1": "L2", "R1": "R2"}."""
    for old, new in mapping.items():
        title = re.sub(rf"(?<![A-Za-z0-9]){re.escape(old)}(?![0-9])", new, title)
    return title


def entries(activators):
    """Every activator entry as (activation type, entry), in serialized order."""
    for kind, value in activators.items():
        for entry in value if isinstance(value, list) else [value]:
            yield kind, entry


def actions(entry):
    """An entry's binding strings, in storage order."""
    binding = entry.get("bindings", {}).get("binding", [])
    return binding if isinstance(binding, list) else [binding]


def bindings(activators):
    """Every binding string of every activator entry."""
    for _, entry in entries(activators):
        yield from actions(entry)


def defined(group, name):
    """True if the group gives this input at least one activator (an empty object doesn't count)."""
    return bool(group and group.get("inputs", {}).get(name, {}).get("activators"))


class Layout:
    """Titles, presets and groups of one layout, with per-layer active groups cached."""

    def __init__(self, data):
        cm = data["controller_mappings"]
        self.cm = cm
        self.groups = {g["id"]: g for g in cm["group"]}
        self.order = list(cm["actions"]) + list(cm["action_layers"])
        self.titles = {key: value["title"] for section in ("actions", "action_layers")
                       for key, value in cm[section].items()}
        self.presets = {self.titles[p["name"]]: p for p in cm["preset"]}
        self.base = self.titles[self.order[0]]
        self._active = {}

    def active(self, title):
        """{source: group} for the layer's active (non-mode-shift) groups."""
        if title not in self.presets:
            raise ValueError(f"unknown layer: {title}")
        if title in self._active:
            return self._active[title]
        result = self._active[title] = {}
        for gid, state in self.presets[title]["group_source_bindings"].items():
            source, _, rest = state.partition(" ")
            if rest == "active":
                result[source] = self.groups[gid]
        return result

    def resolve(self, ref):
        """A command's layer reference (token or runtime ID) as a title."""
        match = TOKEN.fullmatch(ref)
        return match.group(1) if match else self.titles[self.order[int(ref) - 1]]

    def layer_ops(self, entry):
        """An entry's layer commands as (op, title), in execution order (arrays run bottom to top)."""
        return [(m.group(1), self.resolve(m.group(2))) for a in reversed(actions(entry)) if (m := TARGET.search(a))]


def always_on_layers(layout):
    return [title for title in layout.presets
            if any(defined(g, "always_on_action") for g in layout.active(title).values())]
