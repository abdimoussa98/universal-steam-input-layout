"""The stack-search rules, exported for the compiled engine (tools/stack_search).

The rules are the same as `steam_layout.stacks.StackSpace`:

- For every input, the layer that fires it is the topmost layer in the stack
  that binds it. A `disabled` source stops the lookup and fires nothing.
- Each activator entry of that binding can fire (chord conditions are not
  checked, so missed releases and stale stacks are included). Its layer
  commands run in execution order (binding arrays run bottom to top).
- Removing a layer takes it out; adding a layer that's already present does
  nothing (Valve's documented behavior, confirmed on the Deck), otherwise it
  goes on top. Base is never removed.
- Mode-shift group entries fire with the entry that shifts to them.
- A `hold_layer` target can be released at any time.

`SearchModel.successors` is a small Python reference used by the tests. The
engine reads the text file that `write` produces.
"""
from .model import MODE_SHIFT, TARGET, actions, entries

ADD, REMOVE = "a", "r"


class SearchModel:
    def __init__(self, layout):
        self.layout = layout
        self.layer_names = list(layout.presets)  # the action set (Base) comes first
        self.index = {t: n for n, t in enumerate(self.layer_names)}
        names, blocked = {}, {}
        for title in self.layer_names:
            for source, group in layout.active(title).items():
                if group["mode"] == "disabled":
                    blocked.setdefault(title, set()).add(source)
                for name in group.get("inputs", {}):
                    names.setdefault(source, set()).add(name)
        for sources in blocked.values():
            for source in sources:
                names.setdefault(source, set())
        self.inputs = sorted((s, n) for s, ns in names.items() for n in ns)
        self.input_index = {j: n for n, j in enumerate(self.inputs)}
        self.binds = {}   # layer id -> {input id}
        self.blocks = {}  # layer id -> {input id}
        self.events = []  # {"layer", "input", "label", "ops": [(op, layer id)]}
        self.fires = {}   # (layer id, input id) -> [event ids]
        for title in self.layer_names:
            lid = self.index[title]
            for source, group in layout.active(title).items():
                if group["mode"] == "disabled":
                    self.blocks.setdefault(lid, set()).update(
                        self.input_index[j] for j in self.inputs if j[0] == source)
                    continue
                for name, value in group.get("inputs", {}).items():
                    acts = value.get("activators")
                    if not acts:
                        continue
                    jid = self.input_index[(source, name)]
                    self.binds.setdefault(lid, set()).add(jid)
                    for kind, entry in entries(acts):
                        self._event(lid, jid, f"{title} {source}/{name} {kind}", layout.layer_ops(entry))
                        for gid in [m.group(2) for a in actions(entry) if (m := MODE_SHIFT.search(a))]:
                            for shifted, value2 in layout.groups.get(gid, {}).get("inputs", {}).items():
                                for kind2, entry2 in entries(value2.get("activators", {})):
                                    self._event(lid, jid, f"{title} {source}/{name} {kind} -> mode shift {shifted} {kind2}",
                                                layout.layer_ops(entry2))
        self.hold_names = sorted({layout.resolve(m.group(2)) for g in layout.cm["group"]
                                  for v in g.get("inputs", {}).values()
                                  for _, e in entries(v.get("activators", {})) for a in actions(e)
                                  if (m := TARGET.search(a)) and m.group(1) == "hold_layer"})
        self.hold_events = {}
        for title in self.hold_names:
            self.hold_events[self.index[title]] = len(self.events)
            self.events.append({"layer": self.index[title], "input": -1, "label": f"release hold layer {title}",
                                "ops": [(REMOVE, self.index[title])]})

    def _event(self, lid, jid, label, ops):
        if not ops:
            return
        self.fires.setdefault((lid, jid), []).append(len(self.events))
        self.events.append({"layer": lid, "input": jid, "label": label,
                            "ops": [(REMOVE if op == "remove_layer" else ADD, self.index[t]) for op, t in ops]})

    # -- helpers for the Python reference -----------------------------------
    def ids_of(self, stack):
        return tuple(self.index[t] for t in stack)

    def names_of(self, stack):
        return tuple(self.layer_names[i] for i in stack)

    def apply(self, stack, ops):
        result = list(stack)
        for op, target in ops:
            if op == REMOVE:
                if target in result and target != 0:
                    result.remove(target)
            elif target not in result:
                result.append(target)
        return tuple(result)

    def successors(self, stack):
        """{(next stack, event id)} for one stack of layer ids (bottom first)."""
        found = set()
        candidates = set()
        for lid in stack:
            candidates |= self.binds.get(lid, set()) | self.blocks.get(lid, set())
        for jid in candidates:
            for lid in reversed(stack):
                if jid in self.blocks.get(lid, set()):
                    break
                if jid in self.binds.get(lid, set()):
                    for event in self.fires.get((lid, jid), []):
                        found.add((self.apply(stack, self.events[event]["ops"]), event))
                    break
        for lid, event in self.hold_events.items():
            if lid in stack:
                found.add((self.apply(stack, self.events[event]["ops"]), event))
        return found

    # -- export ----------------------------------------------------------------
    def write(self, path):
        lines = [f"layers {len(self.layer_names)}"]
        lines += [f"layer {n} {t}" for n, t in enumerate(self.layer_names)]
        lines.append(f"inputs {len(self.inputs)}")
        lines += [f"input {n} {s} {name}" for n, (s, name) in enumerate(self.inputs)]
        lines += [f"bind {lid} {jid}" for lid, js in sorted(self.binds.items()) for jid in sorted(js)]
        lines += [f"block {lid} {jid}" for lid, js in sorted(self.blocks.items()) for jid in sorted(js)]
        lines.append(f"events {len(self.events)}")
        for n, e in enumerate(self.events):
            ops = " ".join(f"{op} {t}" for op, t in e["ops"])
            lines.append(f"event {n} {e['layer']} {e['input']} {len(e['ops'])} {ops} | {e['label']}")
        lines.append("end")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
