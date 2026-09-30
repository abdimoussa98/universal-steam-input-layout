"""The inheritance/blocking audit (resources/Layer Definition of Done.md, section 8).

For each target layer (every Always On layer, plus any named in the config),
every stack it can be on top of comes from `StackSpace`. For each input the
target doesn't define, the topmost lower binding is the effective one; if it
changes layers (directly or through a mode shift) it is a route. Routes need
a block or a recorded decision. See audit_inheritance.py for the CLI.
"""
import copy

from .model import EMPTY, LAYER_COMMAND, MODE_SHIFT, Layout, always_on_layers, bindings, defined, map_title
from .model import entries as model_entries
from .stacks import StackSpace, effective_input

STATUSES = ("allow", "todo")


def changes_layers(layout, activators):
    """Return the reason this binding changes layers, or None."""
    for binding in bindings(activators):
        if LAYER_COMMAND.search(binding):
            return "direct"
        shift = MODE_SHIFT.search(binding)
        if shift:
            group = layout.groups.get(shift.group(2), {})
            if any(LAYER_COMMAND.search(b) for value in group.get("inputs", {}).values()
                   for b in bindings(value.get("activators", {}))):
                return shift.group(0)
    return None


def check_stack(layout, target, stack):
    top = layout.active(target)
    below = [(title, layout.active(title)) for title in stack]
    routes, blocked = [], []
    sources = dict.fromkeys(s for _, groups in below for s in groups)
    for source in sources:
        names = dict.fromkeys(n for _, groups in below for n in groups.get(source, {}).get("inputs", {}))
        for name in names:
            definer = None
            for index in range(len(below) - 1, -1, -1):
                group = below[index][1].get(source)
                if group is None:
                    continue
                if group["mode"] == "disabled":
                    break
                if defined(group, name):
                    definer = index
                    break
            if definer is None:
                continue
            layer, groups = below[definer]
            group = groups[source]
            via = changes_layers(layout, group["inputs"][name]["activators"])
            if not via:
                continue
            row = {"stack": list(stack), "source": source, "input": name, "from_layer": layer,
                   "via": via, "bindings": list(bindings(group["inputs"][name]["activators"]))}
            mine = top.get(source)
            if mine and mine["mode"] == "disabled":
                blocked.append({**row, "kind": "disabled source"})
            elif defined(mine, name):
                own = list(bindings(mine["inputs"][name]["activators"]))
                kind = "cleared" if all(b.startswith(EMPTY) for b in own) else "replaced"
                blocked.append({**row, "kind": kind})
            else:
                above = [g[source] for _, g in below[definer + 1:] if source in g]
                above += [mine] if mine else []
                replaced = any(g["mode"] != group["mode"] for g in above)
                routes.append({**row, "status": "mode_replaced" if replaced else "open"})
    return routes, blocked


def untraced(layout, target, routes):
    """Inputs other layers use for layer commands that `target` leaves open."""
    top = layout.active(target)
    seen = {(r["source"], r["input"]) for r in routes}
    users = {}
    for layer, preset in layout.presets.items():
        if layer == target:
            continue
        for gid, state in preset["group_source_bindings"].items():
            source = state.split(" ", 1)[0]
            mine = top.get(source)
            if mine and mine["mode"] == "disabled":
                continue
            for name, value in layout.groups[gid].get("inputs", {}).items():
                if (source, name) in seen or defined(mine, name):
                    continue
                if any(LAYER_COMMAND.search(b) for b in bindings(value.get("activators", {}))):
                    users.setdefault((source, name), set()).add(layer)
    return [{"source": source, "input": name, "layers": sorted(layers)}
            for (source, name), layers in sorted(users.items())]


def strip_layer_api(activators):
    """The activators without layer commands, mode shifts or empty bindings; None if nothing is left."""
    if not activators:
        return None
    result = {}
    for kind, value in activators.items():
        kept = []
        for entry in value if isinstance(value, list) else [value]:
            binding = entry.get("bindings", {}).get("binding", [])
            actions = [a for a in (binding if isinstance(binding, list) else [binding])
                       if not LAYER_COMMAND.search(a) and not MODE_SHIFT.search(a) and not a.startswith(EMPTY)]
            if actions:
                kept.append({"bindings": {"binding": actions[0] if len(actions) == 1 else actions},
                             "settings": copy.deepcopy(entry.get("settings", {}))})
        if kept:
            result[kind] = kept[0] if len(kept) == 1 else kept
    return result or None


def blocks_needed(layout, stacks, routes):
    """Replace with the underlying output if it's the same in every stack, else clear."""
    result = []
    for source, name in dict.fromkeys((r["source"], r["input"]) for r in routes):
        outputs = [strip_layer_api(effective_input(layout, list(stack), source, name)) for stack in stacks]
        same = outputs[0] is not None and all(o == outputs[0] for o in outputs)
        result.append({"source": source, "input": name, "action": "replace" if same else "clear",
                       "stacks": len(stacks), "activators": outputs[0] if same else None})
    return result


def audit(data, config, depth=5):
    layout = Layout(data)
    variant = "alternative" if "alternative" in layout.cm.get("title", "") else "default"
    mapping = config.get("variants", {}).get(variant, {})
    specs = {map_title(t, mapping): spec for t, spec in config.get("targets", {}).items()}
    for title in always_on_layers(layout):
        specs.setdefault(title, {})
    space = StackSpace.of(layout, depth) if depth else None
    targets = {}
    for title, spec in specs.items():
        layout.active(title)
        decisions = {}
        for decision in spec.get("decisions", []):
            if decision.get("status") not in STATUSES or not decision.get("why"):
                raise ValueError(f"{title}: decision needs status {STATUSES} and a why: {decision}")
            decisions[(decision["source"], decision["input"])] = decision
        declared = [tuple(map_title(t, mapping) for t in s["layers"]) for s in spec.get("stacks", [])]
        derived = space.below(title) if space else {}
        stacks = list(dict.fromkeys(declared + sorted(derived, key=lambda s: (derived[s], s))))
        routes, blocked, used = [], [], set()
        earlier = set()
        for stack in stacks:
            found, stopped = check_stack(layout, title, list(stack))
            if derived.get(stack, 0) < depth or stack in declared:
                earlier |= {(r["source"], r["input"], r["from_layer"]) for r in found}
            blocked += stopped
            for route in found:
                decision = decisions.get((route["source"], route["input"]))
                if decision:
                    used.add((route["source"], route["input"]))
                    route["status"] = "allowed" if decision["status"] == "allow" else "todo"
                    route["why"] = decision["why"]
                routes.append(route)
        stale = [d for key, d in decisions.items() if key not in used]
        final = {(r["source"], r["input"], r["from_layer"]) for r in routes}
        pending = [r for r in routes if r["status"] in ("open", "mode_replaced", "todo")]
        targets[title] = {"stacks": len(stacks), "routes": routes, "blocked": blocked,
                          "saturated": not depth or final == earlier,
                          "blocks_needed": blocks_needed(layout, stacks, pending) if pending else [],
                          "stale_decisions": stale, "untraced": untraced(layout, title, routes)}
    undecided = any(r["status"] in ("open", "mode_replaced") for t in targets.values() for r in t["routes"])
    unsaturated = any(not t["saturated"] for t in targets.values())
    return {"variant": variant, "depth": depth, "targets": targets, "ok": not undecided and not unsaturated}


def entries(data, title):
    """Every binding that adds `title`, with the removals that execute before it."""
    layout = Layout(data)
    owners = {}
    for layer, preset in layout.presets.items():
        for gid, state in preset["group_source_bindings"].items():
            owners.setdefault(gid, (layer, state))
    rows = []
    for group in layout.cm["group"]:
        layer, state = owners.get(group["id"], ("(unreferenced)", ""))
        for name, value in group.get("inputs", {}).items():
            for kind, entry in model_entries(value.get("activators", {})):
                ops = layout.layer_ops(entry)  # execution order
                for index, (op, target) in enumerate(ops):
                    if op == "add_layer" and target == title:
                        rows.append({"layer": layer, "source_state": state, "input": name,
                                     "activation": kind, "settings": entry.get("settings", {}),
                                     "removes_first": [t for o, t in ops[:index] if o == "remove_layer"]})
    return rows
