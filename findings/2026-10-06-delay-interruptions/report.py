#!/usr/bin/env python3
"""Turn interruptions.json (from audit.py) into the tables: one section per delay.

    python3 findings/2026-10-06-delay-interruptions/report.py              # writes INVENTORY-<layout>.md
    python3 findings/2026-10-06-delay-interruptions/report.py --summary    # also prints the counts the README quotes

A row groups the lines that share who fires them, what they do to the delay, whether they can
fire, and the layer the binding is in. Its "since" lists every first version found in the group.
Removals that name neither the host nor the target are folded into one row per kind.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = ["owner release", "owner rest", "owner press", "partner release", "partner rest", "partner press",
         "other press", "other release", "other rest", "timer"]
EFFECTS = ["host removed", "host stays", "target lands", "covered", "restart"]
# The commits before the first snapshot, as the tables call them. README.md has the dates.
LABELS = {"85.8 (5eae4dc)": "85.8 Feb", "85.8 (4c351cd)": "85.8 port", "85.8 (a4c2fe5)": "85.8 menu split",
          "90.0 (c85d8ac)": "90.0", "90.1 (7cee48d)": "90.1", "90.2 (2fee9ee)": "90.2", "90.3 (171f3f5)": "90.3"}
FAMILIES = [("Modifier hold, to the cursor", ["L1: Modifier 0", "R1: Modifier 1", "Gyro | L1: Modifier 0", "Gyro | R1: Modifier 1"]),
            ("Modifier 2, to the combined Tap Cover", ["L1!R1: Modifier 2", "R1!L1: Modifier 2", "Gyro | L1!R1: Modifier 2", "Gyro | R1!L1: Modifier 2"]),
            ("Second press held, to its Double Tap Cover", ["L1: Scroll Down", "R1: Scroll Up", "Menu Left: Escape", "Menu Right: Tab"]),
            ("The menu chain's second press, to its Double Tap Cover", ["Menu Left!Right: Enter", "Menu Right!Left: Backspace"]),
            ("Menu Entry Point, to the Fn layer", ["Menu Left: Entry Point", "Menu Right: Entry Point",
                                                    "Stateful | Menu Left: Entry Point", "Stateful | Menu Right: Entry Point"]),
            ("Stick guard, to the menu Tap Cover", ["Menu Buttons: Left Stick Guard", "Menu Buttons: Right Stick Guard"]),
            ("Menu chain, to Menu Keys", ["Menu Left!Right: Entry Point", "Menu Right!Left: Entry Point"]),
            ("Stick touch, to its Tap Cover", ["LST: Entry Point", "RST: Entry Point"]),
            ("Right pad touch, to its Tap Cover", ["RTP: Entry Point"]),
            ("Ramp, first stage (5 ms)", ["Gyro Off Ramp Up"]),
            ("Ramp, second stage", ["Turning Ramp Up 0"]),
            ("Steering stick modifier, to its Tap Cover", ["Steering | LS Down: Modifier 0", "Steering | LS Up: Modifier 1"]),
            ("Steering Modifier 2, to a Tap Cover", ["Steering | R1!L1: Modifier 2", "Steering | L1!R1: Modifier 2"]),
            ("Left pad click hand-over (5 ms)", ["LTP: Click Entry Point"]),
            ("Right pad click hand-over (5 ms)", ["RTP: Click Entry Point"]),
            ("Delayed scroll on the right pad's ring", ["RTP: Mouse Buttons"]),
            ("Delayed scroll on Steering's stick (5 ms)", ["Steering | LS: Double Tap Cover"])]
KINDS = {"Full_Press": "Regular Press", "chord": "Chorded Press", "release": "Release", "Soft_Press": "Soft Press",
         "none": "nothing bound", "": "", "Start_Press": "Start Press", "Long_Press": "Long Press",
         "Double_Press": "Double Press"}


def code(title):
    return f"`{title}`"


def listed(names, limit=14):
    names = sorted(names)
    return ", ".join(names[:limit]) + (f" and {len(names) - limit} more" if len(names) > limit else "")


def who(trigger, inputs, timer=False):
    actor, how = (trigger.split() + [""])[:2]
    if trigger == "timer":
        return "A window's timer runs out"
    names = listed(inputs)
    tail = {"owner": " (its own input)", "partner": " (its chord button)", "other": ""}[actor]
    if timer and actor == "owner":
        tail = " (the window's own button)"
    if how == "release":
        return f"{names} let go{tail}"
    if how == "rest":
        return f"{names} at rest, inverted bind{tail}"
    return f"{names} {'held: another entry on it' if actor == 'owner' and not timer else 'pressed'}{tail}"


def what(line):
    effect, layer = line["effect"], line["effect_layer"]
    if effect == "host removed":
        if layer:
            return f"**Host removed**; {code(layer)} lands on the input"
        left = [d for d in line["detail"] if d != "nothing"]
        return "**Host removed**" + (f"; then {listed(code(d) for d in left)} answers the input" if left else "; nothing answers the input")
    if effect == "host stays":
        return "**Host stays**: the delay is dropped, nothing else changes"
    if effect == "target lands":
        return f"**Target lands** by this route: {code(layer)}"
    if effect == "covered":
        return f"**Covered** by {code(layer)}"
    if layer == "target":
        return "**Restart**: removes the delay's target" + (", and keeps firing" if "keeps firing" in line["detail"] else "")
    return "**Restart**: an unrelated removal" + (", and keeps firing" if "keeps firing" in line["detail"] else "")


def fires(line):
    gate, detail = line["gate"], line["gate_detail"]
    rate = f", every {line['rate']} ms" if line.get("repeats") and line.get("rate") else \
        ", repeating" if line.get("repeats") else ""
    if gate == "fires":
        return "Yes" + rate
    if gate == "needs":
        return f"Only with {detail} held too" + rate
    if gate == "held back":
        return f"No: held back while {detail} is held (A27)"
    if gate == "unless":
        return f"Only while {detail or 'the guard button of the layer it is in'} is not held" + rate
    return "Depends on which chord button is held"


def label(version):
    return LABELS.get(version, version)


def since(lines, default):
    """Every first version in the group, the commonest first; with the inputs when the group is split."""
    found = defaultdict(set)
    for line in lines:
        gaps = ", ".join(" to ".join(label(v) for v in gap.split(" to ")) for gap in line.get("gaps", "").split(", ") if gap)
        found[label(line.get("since", "")) + (f", not in {gaps}" if gaps else "")].update(line["inputs"])
    parts = []
    for version, inputs in sorted(found.items(), key=lambda kv: -len(kv[1])):
        parts.append(version + (f" ({listed(inputs, 6)})" if len(found) > 1 else ""))
    text = "; ".join(parts)
    if default:
        july = {bool(line.get("july")) for line in lines}
        text += " · July: " + ("yes" if july == {True} else "no" if july == {False} else "in part")
    return text


def loose(line):
    """A removal that names neither the host nor the target: folded into one row per kind."""
    return line["effect"] == "restart" and line["effect_layer"] == "other"


def rows(delay, default, folded=True):
    """The table rows of one delay. `folded=False` leaves the unrelated removals out."""
    groups = defaultdict(list)
    for line in delay["interruptions"]:
        fold = loose(line)
        if fold and not folded:
            continue
        key = (ORDER.index(line["trigger"]), EFFECTS.index(line["effect"]), line["effect_layer"],
               "keeps firing" in line["detail"], line.get("rate") or 0, line["gate"], line["gate_detail"],
               "" if fold else line["layer"], "" if fold else line["kind"],
               tuple(line["detail"]) if line["effect"] == "host removed" and not line["effect_layer"] else ())
        groups[key].append(line)
    timer = delay["input"] == "timer"
    for key in sorted(groups):
        lines = groups[key]
        first = lines[0]
        inputs = {i for line in lines for i in line["inputs"]}
        if loose(first):
            layers = sorted({line["layer"] for line in lines})
            where = f"{len(layers)} layer{'s' if len(layers) > 1 else ''}: " + listed((code(t) for t in layers), 8)
        else:
            where = ("Host" if first["layer"] == delay["layer"] else code(first["layer"])) + \
                (f", {KINDS.get(first['kind'], first['kind'])}" if first["kind"] else "")
        yield [who(first["trigger"], inputs, timer), what(first), where, fires(first), since(lines, default)]


def history(delay, default):
    parts = []
    for version, ms, does in delay.get("changes", []):
        parts.append(f"{label(version)}: {ms} ms, {listed(code(t) for t in does) if does else 'removes itself'}")
    text = "History: " + "; then ".join(parts) + "." if parts else ""
    if delay.get("gaps"):
        text += f" Not in {delay['gaps']}."
    if default:
        july = delay.get("july")
        text += (f" July reference: {july[0]} ms, {listed(code(t) for t in july[1]) if july[1] else 'removes itself'}."
                 if july else " Not in the July reference.")
    return text


def gone(delay):
    """Rows for the lines this delay had in an older version and has no more."""
    groups = defaultdict(set)
    for line in delay.get("gone", []):
        shown = dict(line, inputs=[line["input"]], detail=[], repeats=False)
        key = (ORDER.index(line["trigger"]), what(shown), line["layer"], line["kind"], fires(shown), line["first"], line["last"])
        groups[key].add(line["input"])
    timer = delay["input"] == "timer"
    for (order, effect, layer, kind, gate, first, last), inputs in sorted(groups.items()):
        where = ("Host" if layer == delay["layer"] else code(layer)) + (f", {KINDS.get(kind, kind)}" if kind else "")
        span = label(first) if first == last else f"{label(first)} to {label(last)}"
        yield [who(ORDER[order], inputs, timer), effect, where, gate, span]


def table(head, body):
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return lines + ["| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in body]


def section(delay, default):
    does = {"add": "adds " + listed(code(t) for t in delay["targets"]),
            "exit": "removes its own layer" + (f" and sends {listed(delay['outputs'])}" if delay["outputs"] else ""),
            "output": "sends " + listed(delay["outputs"])}[delay["role"]]
    head = f"### {code(delay['layer'])}: {delay['input']}, {delay['ms']} ms, {does}\n\n"
    facts = [history(delay, default)]
    if delay["input"] != "timer":
        held = " or ".join(" + ".join(h) for h in delay["held"])
        resets = ", ".join(f"{i} every {r} ms" if r else f"{i}, no rate stated" for i, r in delay["resets"])
        if delay["role"] == "add":
            facts.append(f"Held while it is pending: {held}. Reset (R120): {resets or 'none'}.")
        else:
            facts.append(f"Held while it is pending: {held}.")
    facts.append(f"Pending on {delay['pending_stacks']} of the stacks the chains reach.")
    text = head + " ".join(f for f in facts if f) + "\n\n"
    text += "\n".join(table(["Interrupted by", "What it does to the delay", "Binding in", "Can it fire?", "Since"],
                            rows(delay, default))) + "\n"
    old = list(gone(delay))
    if old:
        text += "\nCame and went:\n\n" + "\n".join(table(["Interrupted by", "What it did", "Binding in", "Could it fire?",
                                                            "Versions"], old)) + "\n"
    return text


def inventory(variant, found):
    default = variant == "default"
    lines = [f"# Delay interruptions: the {variant} layout, {found['version']}", "",
             "Generated by [report.py](report.py) from [interruptions.json](interruptions.json). "
             "What the columns mean, and what was found: [README.md](README.md).", ""]
    kinds = [("Holds that add a layer", lambda d: d["input"] != "timer" and d["role"] == "add" and d["ms"] > 5),
             ("The 5 ms hand-overs", lambda d: d["input"] != "timer" and d["role"] == "add" and d["ms"] <= 5),
             ("Delayed outputs on a held input", lambda d: d["input"] != "timer" and d["role"] == "output"),
             ("Window timers", lambda d: d["input"] == "timer")]
    for title, keep in kinds:
        chosen = [d for d in found["delays"] if keep(d)]
        lines += [f"## {title} ({len(chosen)})", ""]
        lines += [section(d, default) for d in chosen]
    if found.get("retired"):
        lines += ["## Delays that are gone", "",
                  "A delay some version had and 90.36 has not. The value and the action are those of its last version.", ""]
        lines += table(["Layer", "Input", "Delay", "When it ended", "Versions"],
                       [[code(r["layer"]), r["input"], f"{r['ms']} ms",
                         {"add": "added " + listed(code(t) for t in r["does"]), "exit": "removed its own layer",
                          "output": "sent " + (listed(r["does"]) or "a haptic or nothing")}[r["role"]],
                         label(r["first"]) if r["first"] == r["last"] else f"{label(r['first'])} to {label(r['last'])}"]
                        for r in found["retired"]])
        lines.append("")
    if found.get("july_only"):
        lines += ["Delays the July reference has and no Neptune version had under that name: "
                  + "; ".join(found["july_only"]) + ".", ""]
    return "\n".join(lines)


def shape(delay):
    """What a delay's lines look like with the names taken out: mirrored delays have the same shape."""
    found = Counter()
    for line in delay["interruptions"]:
        if not loose(line):
            where = "host" if line["layer"] == delay["layer"] else "other"
            found[(line["trigger"], line["effect"], line["gate"], where)] += len(line["inputs"])
    return found


def families(found, rename=lambda title: title):
    """[(family, [delays])] for the held delays, and a check that each family's members have one shape."""
    by_layer = defaultdict(list)
    for delay in found["delays"]:
        if delay["input"] != "timer":
            by_layer[delay["layer"]].append(delay)
    result = []
    for title, layers in FAMILIES:
        members = [d for layer in layers for d in by_layer.pop(rename(layer), [])]
        result.append((title, members, len({tuple(sorted(shape(d).items())) for d in members}) == 1))
    if by_layer:
        raise SystemExit(f"held delays outside every family: {sorted(by_layer)}")
    return result


def digest(found):
    """One family at a time: its members, and the first member's rows without the unrelated removals."""
    out = []
    for title, members, same in families(found):
        first = members[0]
        out.append(f"\n## {title}: {len(members)} delay{'s' if len(members) > 1 else ''}, "
                   f"{'one shape' if same else 'SHAPES DIFFER'}")
        out.append("   members: " + "; ".join(f"{d['layer']} / {d['input']} {d['ms']} ms" for d in members))
        out.append("   " + history(first, True) + f" resets: {first['resets']}")
        for row in rows(first, True, folded=False):
            out.append("   - " + " | ".join(row))
        unrelated = [line for line in first["interruptions"] if loose(line)]
        keeps = sorted({(line["layer"], line["rate"]) for line in unrelated if "keeps firing" in line["detail"]})
        out.append(f"   unrelated removals: {len({line['layer'] for line in unrelated})} layers; keeps firing: {keeps}")
    return "\n".join(out)


def summary(result):
    """The counts the README quotes."""
    out = []
    for variant, found in result.items():
        delays = found["delays"]
        held = [d for d in delays if d["input"] != "timer"]
        out.append(f"== {variant} {found['version']}: {len(delays)} delays ({len(held)} on a held input, "
                   f"{len(delays) - len(held)} window timers), {sum(len(d['interruptions']) for d in delays)} lines")
        cells = defaultdict(set)
        for d in held:
            for line in d["interruptions"]:
                actor = line["trigger"].split()[0]
                effect = line["effect"] + (" " + line["effect_layer"] if line["effect"] == "restart" else "")
                where = "" if effect.startswith(("restart", "host stays")) or actor == "owner" else \
                    " (host's own bind)" if line["layer"] == d["layer"] else " (another layer's bind)"
                gate = "held back" if line["gate"] == "held back" else "can fire"
                cells[(actor, effect + where, gate)].add((d["layer"], d["input"]))
        out.append("   delays with at least one such line, of the held ones:")
        for key, members in sorted(cells.items()):
            out.append("   " + " | ".join(f"{k:38}" if i == 1 else f"{k:9}" for i, k in enumerate(key)) + f" {len(members)}")
        order = []
        for d in delays:
            for version, _, _ in d.get("changes", []):
                order.append(version)
        first = Counter(d.get("since", "") for d in delays)
        lines, close = Counter(), Counter()
        for d in delays:
            for line in d["interruptions"]:
                lines[line.get("since", "")] += 1
                close[line.get("since", "")] += not loose(line)
        versions = sorted(lines, key=version_key)
        out.append("   first version: delays that came with it / lines that came with it (of those, lines that name the "
                   "host, the target or a cover)")
        out += [f"      {label(v):18} {first.get(v, 0):3} / {lines[v]:4} ({close[v]})" for v in versions]
        out.append("   families: " + "; ".join(f"{t} ({len(m)}{'' if same else ', shapes differ'})" for t, m, same in
                                                 families(found, (lambda t: t) if variant == "default" else alternative)))
    return "\n".join(out)


def version_key(version):
    """Sort "85.8 (5eae4dc)", "90.2 (50758b3)" and "90.10" in the order they came."""
    commits = ["5eae4dc", "4c351cd", "3f84c06", "a4c2fe5", "c85d8ac", "7cee48d", "2fee9ee", "16de85e", "ebc55bc",
               "52494a0", "619cb34", "f5f811f", "c820d22", "50758b3", "5bf46a7", "171f3f5"]
    number, _, commit = version.partition(" (")
    major, minor = (int(n) for n in number.split("."))
    return (major, minor, commits.index(commit.rstrip(")")) if commit else 0)


def alternative(title):
    """A default-layout title as the alternative layout names it."""
    import re
    return re.sub(r"(?<![A-Za-z0-9])([LR])1(?![0-9])", r"\g<1>2", title)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--summary", action="store_true", help="print the counts the README quotes")
    parser.add_argument("--digest", action="store_true", help="print each family's first delay, default layout")
    args = parser.parse_args()
    result = json.loads((HERE / "interruptions.json").read_text(encoding="utf-8"))
    for variant, found in result.items():
        (HERE / f"INVENTORY-{variant}.md").write_text(inventory(variant, found), encoding="utf-8")
    if args.summary:
        print(summary(result))
    if args.digest:
        print(digest(result["default"]))


if __name__ == "__main__":
    main()
