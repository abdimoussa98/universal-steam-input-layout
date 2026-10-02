"""The inheritance/blocking audit (resources/Layer Definition of Done.md, section 8).

For each target layer (every Always On layer, plus any named in the config),
the stacks beneath it come from the backward chains (chains.py: who adds the
layer, back to the action set, plus bystanders; no depth cap and no config)
and from any stacks the config declares. `depth` adds the older chord-blind,
depth-limited search (`StackSpace`, deprecated 2026-10-01) as a comparison. For each input
the target doesn't define, the topmost lower binding is the effective one; if
it changes layers (directly or through a mode shift) it is a route. Routes
need a block or a recorded decision, and each carries the reason its stack
exists. A target no stack reaches isn't checked, which fails the audit. See
audit_inheritance.py for the CLI.
"""
import copy

from .chains import Chains
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


def layer_command_inputs(layout):
    """{(group id, input): how it changes layers} for every active group input that does, cached on the layout."""
    if "_layer_command_inputs" not in layout.__dict__:
        found = {}
        for title in layout.presets:
            for group in layout.active(title).values():
                for name, value in group.get("inputs", {}).items():
                    via = changes_layers(layout, value.get("activators", {}))
                    if via:
                        found[(group["id"], name)] = via
        layout.__dict__["_layer_command_inputs"] = found
        layout.__dict__["_layer_command_names"] = {
            (source, name) for title in layout.presets for source, group in layout.active(title).items()
            for name in group.get("inputs", {}) if (group["id"], name) in found}
    return layout.__dict__["_layer_command_inputs"], layout.__dict__["_layer_command_names"]


def _bindings(layout, group, name):
    """The input's binding strings; one shared list per group input (rows repeat it across many stacks)."""
    cache = layout.__dict__.setdefault("_input_bindings", {})
    key = (group["id"], name)
    if key not in cache:
        cache[key] = list(bindings(group["inputs"][name]["activators"]))
    return cache[key]


def check_stack(layout, target, stack):
    top = layout.active(target)
    below = [(title, layout.active(title)) for title in stack]
    routes, blocked = [], []
    changing, hot = layer_command_inputs(layout)
    sources = dict.fromkeys(s for _, groups in below for s in groups)
    for source in sources:
        names = dict.fromkeys(n for _, groups in below for n in groups.get(source, {}).get("inputs", {}))
        for name in names:
            if (source, name) not in hot:
                continue   # no layer anywhere changes layers on this input, so no definer can
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
            via = changing.get((group["id"], name))
            if not via:
                continue
            row = {"stack": list(stack), "source": source, "input": name, "from_layer": layer,
                   "via": via, "bindings": _bindings(layout, group, name)}
            mine = top.get(source)
            above = [g[source] for _, g in below[definer + 1:] if source in g]
            above += [mine] if mine else []
            if mine and mine["mode"] == "disabled":
                blocked.append({**row, "kind": "disabled source"})
            elif any(g["mode"] != group["mode"] for g in above):
                # A different source mode at or above the definer blocks inheritance
                # (author, 2026-10-01): the lower mode's inputs don't carry over.
                blocked.append({**row, "kind": "mode replaced"})
            elif defined(mine, name):
                own = _bindings(layout, mine, name)
                kind = "cleared" if all(b.startswith(EMPTY) for b in own) else "replaced"
                blocked.append({**row, "kind": kind})
            else:
                routes.append({**row, "status": "open"})
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
                kept.append({"bindings": {"binding": actions[0] if len(actions) == 1 else actions}})
                if entry.get("settings"):   # the builders never write an empty settings block
                    kept[-1]["settings"] = copy.deepcopy(entry["settings"])
        if kept:
            result[kind] = kept[0] if len(kept) == 1 else kept
    return result or None


def blocks_needed(layout, stacks, routes):
    """Replace with the underlying keybind if only one is possible across the stacks, else clear.

    A stack whose binding is only a layer command adds no keybind (author, 2026-10-01): under
    Gyro Off Ramp Up a trigger soft pull only removes that layer, so the one keybind is Base's
    mouse button and the window replaces the input with it. If no stack gives a keybind, clear.
    """
    result = []
    for source, name in dict.fromkeys((r["source"], r["input"]) for r in routes):
        outputs = [o for stack in stacks
                   if (o := strip_layer_api(effective_input(layout, list(stack), source, name))) is not None]
        same = bool(outputs) and all(o == outputs[0] for o in outputs)
        result.append({"source": source, "input": name, "action": "replace" if same else "clear",
                       "stacks": len(stacks), "activators": outputs[0] if same else None})
    return result


def audit(data, config, depth=0, chains=True):
    """`depth` > 0 adds the depth-limited search; `chains=False` leaves only it and the declared stacks."""
    layout = Layout(data)
    variant = "alternative" if "alternative" in layout.cm.get("title", "") else "default"
    mapping = config.get("variants", {}).get(variant, {})
    specs = {map_title(t, mapping): spec for t, spec in config.get("targets", {}).items()}
    for title in always_on_layers(layout):
        specs.setdefault(title, {})
    space = StackSpace.of(layout, depth) if depth else None
    lineage = Chains.of(layout) if chains else None
    targets = {}
    for title, spec in specs.items():
        layout.active(title)
        decisions = {}
        for decision in spec.get("decisions", []):
            if decision.get("status") not in STATUSES or not decision.get("why"):
                raise ValueError(f"{title}: decision needs status {STATUSES} and a why: {decision}")
            decisions[(decision["source"], decision["input"])] = decision
        declared = [tuple(map_title(t, mapping) for t in s["layers"]) for s in spec.get("stacks", [])]
        chained = lineage.below(title) if lineage else {}
        derived = space.below(title) if space else {}
        stacks = list(dict.fromkeys(declared + list(chained) + sorted(derived, key=lambda s: (derived[s], s))))
        routes, blocked, used = [], [], set()
        earlier = set()
        for stack in stacks:
            found, stopped = check_stack(layout, title, list(stack))
            if derived.get(stack, 0) < depth or stack in declared or stack in chained:
                earlier |= {(r["source"], r["input"], r["from_layer"]) for r in found}
            blocked += stopped
            for route in found:
                decision = decisions.get((route["source"], route["input"]))
                if decision:
                    used.add((route["source"], route["input"]))
                    route["status"] = "allowed" if decision["status"] == "allow" else "todo"
                    route["why"] = decision["why"]
                route["reason"] = reason(stack, declared, chained, derived)
                routes.append(route)
        stale = [d for key, d in decisions.items() if key not in used]
        final = {(r["source"], r["input"], r["from_layer"]) for r in routes}
        pending = [r for r in routes if r["status"] in ("open", "todo")]
        targets[title] = {"stacks": len(stacks), "chain_stacks": len(chained), "checked": bool(stacks),
                          "routes": routes, "blocked": blocked,
                          "saturated": not depth or final == earlier,
                          "blocks_needed": blocks_needed(layout, stacks, pending) if pending else [],
                          "stale_decisions": stale, "untraced": untraced(layout, title, routes)}
    undecided = any(r["status"] == "open" for t in targets.values() for r in t["routes"])
    unsaturated = any(not t["saturated"] for t in targets.values())
    unchecked = any(not t["checked"] for t in targets.values())
    return {"variant": variant, "depth": depth, "targets": targets,
            "ok": not undecided and not unsaturated and not unchecked}


def reason(stack, declared, chained, derived):
    """Why a stack is checked: the bindings that built it, or which other source supplied it."""
    if stack in declared:
        return ["declared in the config"]
    if stack in chained:
        why = chained[stack]
        return why.describe() + ([f"bystander: {why.bystander}"] if why.bystander else [])
    return [f"depth search, {derived[stack]} input(s) from the action set"]


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
