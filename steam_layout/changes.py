"""What differs between two layouts, by layer and input.

Every live group of every layer is compared: a source's active group and its
mode-shift targets (plain-inactive slots are dead and left out). For each one
the mode, the settings and every input's activators are compared. A layer
command is compared by the title it targets, and a mode shift by the group it
leads to, so a runtime ID or group ID that shifted is not a change.

    report = diff(before, after)        # two layout dicts
    report["added"], report["removed"]  # layer titles
    report["layers"]                    # {title: [change, ...]} for layers in both
    changed_layers(report)              # titles that are new or changed
    text(report, "90.12", "90.13")      # the report as text

A change is {"source", "input", "what", "before", "after"}. `input` is None for
a change to the group itself. `what` is one of: binding, input added, input
removed, mode, settings, source added, source removed. Bindings are shown one
line per entry, commands in execution order (arrays run bottom to top).

The command line is change_report.py. Plan: plans/2026-10-02-rule-registry.md, phase 6.
"""
import json
from pathlib import Path
import re

from .model import MODE_SHIFT, TARGET, Layout, actions, entries

VERSIONS = Path(__file__).resolve().parent.parent / "versions" / "neptune"
SHIFT = " mode shift"


def slots(layout, title):
    """{label: group} for the layer's live groups: `joystick`, `joystick mode shift`, ..."""
    found, ids = {}, {}
    for gid, state in layout.presets[title]["group_source_bindings"].items():
        source, _, rest = state.partition(" ")
        if rest != "active" and "modeshift" not in rest:
            continue
        label = source + (SHIFT if "modeshift" in rest else "")
        number = 2
        while label in found:
            label = f"{source}{SHIFT} {number}"
            number += 1
        found[label], ids[gid] = layout.groups[gid], label
    return found, ids


def command(layout, binding, ids):
    """One binding string with its layer named by title and its mode-shift target by slot."""
    target = TARGET.search(binding)
    if target:
        binding = binding.replace(target.group(2), "{" + layout.resolve(target.group(2)) + "}", 1)
    shift = MODE_SHIFT.search(binding)
    if shift:
        binding = binding.replace(shift.group(0), f"mode_shift {shift.group(1)} {{{ids.get(shift.group(2), 'group ' + shift.group(2))}}}", 1)
    return binding


def normal(layout, activators, ids):
    """Activators in a form that compares equal across layouts: [(kind, settings, commands in storage order)]."""
    return [[kind, entry.get("settings") or {}, [command(layout, b, ids) for b in actions(entry)]]
            for kind, entry in entries(activators or {})]


def lines(rows, prefix=""):
    """One readable line per entry of `normal` output."""
    result = []
    for kind, settings, commands in rows:
        shown = []
        for c in reversed(commands):                 # execution order
            head, _, rest = c.partition(",")
            head = re.sub(r"^controller_action ", "", head)
            head = re.sub(r"\{(.+)\}", r"\1", head)
            head = re.sub(r" 0 0$", "", head)
            label = rest.split(",")[0].strip()
            shown.append(head + (f" [{label}]" if label else ""))
        options = ",".join(f"{k}={v}" for k, v in sorted(settings.items()))
        result.append(f"{prefix}{kind}{'(' + options + ')' if options else ''}: {' ; '.join(shown)}")
    return result


def describe(layout, value, ids):
    """(comparable form, readable lines) of one input."""
    live = normal(layout, value.get("activators"), ids)
    off = normal(layout, value.get("disabled_activators"), ids)
    return (live, off), lines(live) + lines(off, "disabled ")


def group_changes(a, b, label, ga, gb, ids_a, ids_b):
    rows = []

    def row(name, what, before, after):
        rows.append({"source": label, "input": name, "what": what, "before": before, "after": after})

    if ga.get("mode") != gb.get("mode"):
        row(None, "mode", ga.get("mode"), gb.get("mode"))
    sa, sb = ga.get("settings") or {}, gb.get("settings") or {}
    keys = sorted(k for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))
    if keys:
        row(None, "settings", {k: sa.get(k) for k in keys}, {k: sb.get(k) for k in keys})
    ia, ib = ga.get("inputs") or {}, gb.get("inputs") or {}
    for name in list(ia) + [n for n in ib if n not in ia]:
        before = describe(a, ia[name], ids_a) if name in ia else None
        after = describe(b, ib[name], ids_b) if name in ib else None
        if before is None:
            row(name, "input added", None, after[1])
        elif after is None:
            row(name, "input removed", before[1], None)
        elif before[0] != after[0]:
            row(name, "binding", before[1], after[1])
    return rows


def whole(layout, group, ids):
    """Every input of a group as readable lines, for a source that was added or removed."""
    return {name: describe(layout, value, ids)[1] for name, value in (group.get("inputs") or {}).items()}


def diff(before, after):
    """The change report for two layout dicts."""
    a, b = Layout(before), Layout(after)
    report = {"title": {"before": a.cm.get("title"), "after": b.cm.get("title")},
              "count": {"before": len(a.presets) - 1, "after": len(b.presets) - 1},
              "added": [t for t in b.presets if t not in a.presets],
              "removed": [t for t in a.presets if t not in b.presets], "layers": {}}
    for title in b.presets:
        if title not in a.presets:
            continue
        (sa, ids_a), (sb, ids_b) = slots(a, title), slots(b, title)
        rows = []
        for label in list(sa) + [s for s in sb if s not in sa]:
            if label not in sb:
                rows.append({"source": label, "input": None, "what": "source removed",
                             "before": whole(a, sa[label], ids_a), "after": None})
            elif label not in sa:
                rows.append({"source": label, "input": None, "what": "source added",
                             "before": None, "after": whole(b, sb[label], ids_b)})
            else:
                rows += group_changes(a, b, label, sa[label], sb[label], ids_a, ids_b)
        if rows:
            report["layers"][title] = rows
    return report


def changed_layers(report):
    """The layers that are new or changed."""
    return set(report["layers"]) | set(report["added"])


def text(report, before_name, after_name):
    """The report as text."""
    out = [f"Changes from {before_name} to {after_name}",
           f"Layers: {report['count']['before']} -> {report['count']['after']}"
           f" (added: {', '.join(report['added']) or 'none'}; removed: {', '.join(report['removed']) or 'none'})"]
    if not report["layers"] and not report["added"] and not report["removed"]:
        return "\n".join(out + ["No changes."])

    def show(side, value, indent="    "):
        if value is None:
            return
        if isinstance(value, dict) and all(isinstance(v, list) for v in value.values()):   # a whole source
            for name, shown in value.items():
                out.extend(f"{indent}{side} {name}: {line}" for line in shown or ["(no binding)"])
        elif isinstance(value, list):
            out.extend(f"{indent}{side} {line}" for line in value or ["(no binding)"])
        else:
            out.append(f"{indent}{side} {json.dumps(value, sort_keys=True)}")

    total = 0
    for title, rows in report["layers"].items():
        out.append(f"\n== {title}")
        for c in rows:
            total += 1
            where = c["source"] + (f"/{c['input']}" if c["input"] else "")
            out.append(f"  {where}: {c['what']}")
            show("before:", c["before"])
            show("after: ", c["after"])
    layers = len(report["layers"])
    out.append(f"\n{layers} layer{'' if layers == 1 else 's'} changed, {total} change{'' if total == 1 else 's'}")
    return "\n".join(out)


def version(name):
    """The release number in a snapshot's file or folder name, as a tuple: 90.10 -> (90, 10)."""
    match = re.search(r"(\d+(?:\.\d+)+)(?:\.json)?$", name)
    return tuple(int(part) for part in match.group(1).split(".")) if match else ()


def newest_snapshot(working_name, versions=VERSIONS):
    """The newest snapshot of a working layout (`..._latest.json`), or None."""
    stem = Path(working_name).name.replace("_latest.json", "")
    found = [path for folder in Path(versions).iterdir() if folder.is_dir() and version(folder.name)
             for path in [folder / f"{stem}_{folder.name}.json"] if path.exists()]
    return max(found, key=lambda path: version(path.parent.name)) if found else None
