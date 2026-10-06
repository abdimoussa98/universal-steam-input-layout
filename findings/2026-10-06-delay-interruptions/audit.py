#!/usr/bin/env python3
"""Every start delay in a layout, and every binding that can interrupt it while it is pending.

A delay is one activator entry with Fire Start Delay. It is pending from the moment its binding
starts answering its input until the delay runs out. This script lists, for each delay, every
other entry that can fire in that time and what that does to the delay:

    host removed     the layer the delay is in leaves the stack
    target lands     another entry adds the layer the delay was going to add, and it takes the input
    covered          another layer lands and takes the input (A15)
    restart          a remove_layer fires and nothing else changes: the delay starts again (A12, A13)

and who fires it: the delay's own input, a button its chord needs, another input, or a timer,
and whether it can fire while the delay's own buttons are held (`gate`).
Each line also gets the version it first appeared in, from the snapshots in versions/neptune/
and the commits before 90.4, and whether the July reference has it (default layout only).
What was found: README.md.

    python3 findings/2026-10-06-delay-interruptions/audit.py            # both layouts, with history
    python3 findings/2026-10-06-delay-interruptions/audit.py --no-history
    python3 findings/2026-10-06-delay-interruptions/audit.py --layer "Menu Left: Entry Point"

It writes interruptions.json beside itself, and nothing else; report.py turns that into the tables.
The stacks are the backward chains (steam_layout/chains.py), with one extra press. It reads no
timing: an entry that can fire on a stack where the delay is pending is listed, whether or not
the gesture is likely. It stops if the working layouts are not the newest snapshot.
"""
import argparse
from collections import defaultdict, namedtuple
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from steam_layout.chains import Chains                                  # noqa: E402
from steam_layout.flow_model import chord_condition                     # noqa: E402
from steam_layout.model import EMPTY, TARGET, Layout, actions, defined, entries   # noqa: E402
from steam_layout.stacks import apply_ops                               # noqa: E402

ALWAYS_ON = ("switch", "always_on_action")
VARIANTS = ("default", "alternative")
JULY = ROOT / "findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json"
# The commits before the first snapshot (90.4), oldest first. Several carry one version number.
COMMITS = ("5eae4dc", "4c351cd", "3f84c06", "a4c2fe5", "c85d8ac", "7cee48d", "2fee9ee", "16de85e", "ebc55bc",
           "52494a0", "619cb34", "f5f811f", "c820d22", "50758b3", "5bf46a7", "171f3f5")

NAMES = {("switch", "button_escape"): "Start", ("switch", "button_menu"): "Select",
         ("switch", "left_bumper"): "LB", ("switch", "right_bumper"): "RB",
         ("button_diamond", "button_a"): "A", ("button_diamond", "button_b"): "B",
         ("button_diamond", "button_x"): "X", ("button_diamond", "button_y"): "Y",
         ("dpad", "dpad_north"): "Up", ("dpad", "dpad_south"): "Down",
         ("dpad", "dpad_west"): "Left", ("dpad", "dpad_east"): "Right",
         ("left_trigger", "edge"): "LT", ("right_trigger", "edge"): "RT",
         ("left_trigger", "click"): "LT full", ("right_trigger", "click"): "RT full",
         ("switch", "button_back_left_upper"): "L4", ("switch", "button_back_left"): "L5",
         ("switch", "button_back_right_upper"): "R4", ("switch", "button_back_right"): "R5",
         ALWAYS_ON: "timer"}
SOURCES = {"joystick": "LS", "right_joystick": "RS", "left_trackpad": "LP", "right_trackpad": "RP"}
PARTS = {"dpad_north": "up", "dpad_south": "down", "dpad_west": "left", "dpad_east": "right"}

Entry = namedtuple("Entry", "layer control kind index settings ops outputs condition inverted delay repeats rate")


def name(control):
    """A control as the scenario tests name it: LB, Start, "LS touch", "RP up"."""
    if control in NAMES:
        return NAMES[control]
    source, part = control
    return f"{SOURCES.get(source, source)} {PARTS.get(part, part)}"


class Reader:
    """A layout's entries and stacks, and which layer answers an input on a stack."""

    def __init__(self, layout):
        self.layout = layout
        self.base = layout.base
        self.stacks = Chains(layout).stacks()                # {stack: Why}
        self._entries, self._answers, self._names = {}, {}, {}

    def entries(self, layer, control):
        key = (layer, control)
        if key not in self._entries:
            source, part = control
            group = self.layout.active(layer)[source]
            group_inverted = part == "edge" and (group.get("settings") or {}).get("edge_binding_invert") == "1"
            found = []
            for index, (kind, raw) in enumerate(entries(group["inputs"][part].get("activators", {}))):
                settings = raw.get("settings") or {}
                outputs = tuple(a.split(",")[0].strip() for a in reversed(actions(raw))
                                if not TARGET.search(a) and not a.startswith(EMPTY) and a.strip(" ,"))
                rate = settings.get("repeat_rate")
                found.append(Entry(layer, control, kind, index, settings, tuple(self.layout.layer_ops(raw)), outputs,
                                   chord_condition(settings) if kind == "chord" else None,
                                   group_inverted or settings.get("edge_binding_invert") == "1",
                                   int(settings.get("delay_start") or 0), settings.get("hold_repeats") == "1",
                                   int(rate) if rate else None))
            self._entries[key] = found
        return self._entries[key]

    def answers(self, stack, source):
        """{input: layer} for one source: the layer whose binding answers each input on this stack.

        The same lookup as flow_model.resolve: the topmost group sets the mode, a group in another
        mode or a disabled one stops the lookup.
        """
        active = self.layout.active
        projection = tuple(t for t in stack if source in active(t))
        key = (source, projection)
        if key not in self._answers:
            found, mode = {}, None
            for title in reversed(projection):
                group = active(title)[source]
                if group["mode"] == "disabled":
                    break
                mode = mode or group["mode"]
                if group["mode"] != mode:
                    break
                for part in group.get("inputs", {}):
                    if part not in found and defined(group, part):
                        found[part] = title
            self._answers[key] = found
        return self._answers[key]

    def answer(self, stack, control):
        return self.answers(stack, control[0]).get(control[1])

    def sources(self, stack):
        key = frozenset(stack)
        if key not in self._names:
            self._names[key] = sorted({source for title in stack for source in self.layout.active(title)})
        return self._names[key]

    def delays(self):
        """Every entry with a start delay, in layer order."""
        found = []
        for layer in self.layout.presets:
            for source, group in self.layout.active(layer).items():
                if group["mode"] == "disabled":
                    continue
                for part in group.get("inputs", {}):
                    if defined(group, part):
                        found += [e for e in self.entries(layer, (source, part)) if e.delay]
        return found


def role(entry):
    """What a delayed entry does when the delay ends: "add", "exit" (it only removes) or "output"."""
    if any(op != "remove_layer" for op, _ in entry.ops):
        return "add"
    return "exit" if entry.ops else "output"


def targets(entry):
    return tuple(title for op, title in entry.ops if op != "remove_layer")


def held_sets(entry):
    """The sets of controls that are held while this delay is pending: one per way its chord can be met.

    A delay on LB chorded with LB itself needs only LB. One on RB chorded with LB needs both. One
    chorded with "LB or RB" gives two sets. An Always On delay needs nothing held.
    """
    if entry.control == ALWAYS_ON:
        return [frozenset()]
    own = frozenset([entry.control])
    condition = entry.condition
    if condition is None or not condition.known or condition.satisfied(own):
        return [own]
    if condition.mode == "all":
        return [own | {c for group in condition.groups for c in group}]
    return [own | set(group) for group in condition.groups]


def partners(entry):
    """The other buttons the delay's chord needs: letting one go is not letting go of the delay's own input."""
    return frozenset().union(*held_sets(entry)) - {entry.control}


def group_name(group):
    """One button of a chord: LB, "LT" for a trigger's two stages, "LS out" for a stick off centre."""
    source = group[0][0]
    if len(group) > 2 and all(c[0] == source for c in group):
        return f"{SOURCES.get(source, source)} out"
    return name(group[0])


def missing(condition, held):
    """The buttons a chord still needs, given what is held: "LS out and LB", or "LB or RB"."""
    if not condition.known:
        return condition.label
    lacking = [group_name(g) for g in condition.groups if not any(c in held for c in g)]
    return (" and " if condition.mode == "all" else " or ").join(lacking)


def gate(reader, entry, held):
    """Whether `entry` can fire while `held` is held: (verdict, detail).

    fires        nothing holds it back
    needs        a chord whose buttons aren't all among the held ones: it fires only with those held too
    held back    an interruptible press, and a chord on the same input is met by the held buttons (A27)
    unless       an interruptible press guarded by other buttons: it fires only while none of them is held.
                 This is another interaction's cleanup function, which fires when that layer is left over
    """
    if entry.kind == "release":
        return "fires", ""
    now = held if entry.inverted else held | {entry.control}       # an inverted entry is live while the input rests
    if entry.kind == "chord":
        if entry.condition.known and entry.condition.satisfied(now):
            return "fires", ""
        return "needs", missing(entry.condition, now)
    if entry.settings.get("interruptable") == "0":
        return "fires", ""
    chords = [e for e in reader.entries(entry.layer, entry.control)
              if e.kind == "chord" and e.inverted == entry.inverted and e.condition.known]
    met = [e for e in chords if e.condition.satisfied(now)]
    if met:
        guards = {group_name(g) for e in met for g in e.condition.groups if any(c in now for c in g)}
        return "held back", " or ".join(sorted(guards))
    if chords:
        return "unless", " or ".join(sorted({group_name(g) for e in chords for g in e.condition.groups}))
    return "fires", ""


def trigger(delay, entry):
    """Who fires `entry`, seen from the delay: its own input, a chord partner, another input or a timer."""
    if entry.control == ALWAYS_ON:
        return "timer"
    who = "owner" if entry.control == delay.control else \
        "partner" if entry.control in partners(delay) else "other"
    how = "release" if entry.kind == "release" else "rest" if entry.inverted else "press"
    return f"{who} {how}"


def blocker(reader, stack, source):
    """The layer that stops the lookup of a source on this stack: a disabled group, or the topmost group when
    a group under it is in another mode (flow_model.resolve)."""
    layers = [t for t in reversed(stack) if source in reader.layout.active(t)]
    for title in layers:
        if reader.layout.active(title)[source]["mode"] == "disabled":
            return title
    return layers[0] if layers else ""


def effect(reader, delay, stack, entry):
    """What `entry` does to `delay` when it fires on `stack`: ((class, layer), detail), or None for nothing.

    class           layer                                           detail
    host removed    the layer the same entry puts on the input      the layer that answers the input afterwards
    target lands    the delay's target, now answering the input
    covered         the other layer that now answers the input
    restart         "target" or "other": what the removal names     "keeps firing" if the entry repeats and still answers
    host stays      (the delay's own Release, nothing else changed)

    For the delay's own Release the delay is over either way; the class says what is left for the next press.
    """
    after = apply_ops(stack, entry.ops, reader.base)
    now = reader.answer(after, delay.control)
    if delay.layer not in after:
        top = now or blocker(reader, after, delay.control[0])      # a layer in another mode takes the source whole
        landed = top if top and top not in stack else ""
        return ("host removed", landed), "" if landed else (now or "nothing")
    if now != delay.layer:
        covering = now or blocker(reader, after, delay.control[0])
        return ("target lands" if covering in targets(delay) else "covered", covering), ""
    if trigger(delay, entry) in ("owner release", "owner rest"):
        return ("host stays", ""), ""
    removed = {title for op, title in entry.ops if op == "remove_layer"}
    if removed:
        again = entry.repeats and reader.answer(after, entry.control) == entry.layer
        return ("restart", "target" if removed & set(targets(delay)) else "other"), "keeps firing" if again else ""
    return None


def reduced(reader, stack, delay, entry):
    """The part of `stack` that decides the effect: layers with the delay's source, and the ones the entry names."""
    named = {title for _, title in entry.ops} | {delay.layer}
    active = reader.layout.active
    return tuple(t for t in stack if t in named or delay.control[0] in active(t))


def audit(layout, only=None):
    """[{delay, slot, pending, interruptions}] for a layout. `only` keeps one host layer."""
    reader = Reader(layout)
    found, counts = [], defaultdict(int)
    for delay in reader.delays():
        if only and delay.layer != only:
            continue
        counts[(delay.layer, delay.control, role(delay))] += 1
        slot = (delay.layer, delay.control, role(delay), counts[(delay.layer, delay.control, role(delay))])
        pending = [s for s in reader.stacks if delay.layer in s and reader.answer(s, delay.control) == delay.layer]
        sets = held_sets(delay)
        records, cache = {}, {}
        for stack in pending:
            for source in reader.sources(stack):
                for part, layer in reader.answers(stack, source).items():
                    for entry in reader.entries(layer, (source, part)):
                        if not entry.ops or entry == delay:
                            continue
                        key = (entry.layer, entry.control, entry.index, reduced(reader, stack, delay, entry))
                        if key not in cache:
                            cache[key] = effect(reader, delay, stack, entry)
                        if cache[key] is None:
                            continue
                        what, detail = cache[key]
                        gates = {gate(reader, entry, held) for held in sets}
                        verdict = gates.pop() if len(gates) == 1 else ("depends", "which chord button is held")
                        once = what == ("restart", "other") and detail != "keeps firing"
                        # a removal that names neither the host nor the target and fires once costs one restart:
                        # those are kept per layer, not per input
                        record = (trigger(delay, entry), entry.layer, None if once else entry.control,
                                  "" if once else entry.kind, what, (verdict[0], "") if once else verdict)
                        seen = records.setdefault(record, {"stack": stack, "entry": entry, "count": 0, "where": set(),
                                                           "detail": set(), "inputs": set()})
                        seen["count"] += 1
                        seen["detail"].add(detail)
                        seen["inputs"].add(name(entry.control))
                        seen["where"].add("host" if layer == delay.layer else
                                          "above" if stack.index(layer) > stack.index(delay.layer) else "below")
                        if len(stack) < len(seen["stack"]):
                            seen["stack"] = stack
        if delay.control != ALWAYS_ON and pending and not any(r[0] in ("owner release", "owner rest") for r in records):
            records[("owner release", delay.layer, delay.control, "none", ("host stays", ""), ("fires", ""))] = \
                {"stack": min(pending, key=len), "entry": None, "count": len(pending), "where": {"host"}, "detail": {""},
                 "inputs": {name(delay.control)}}
        found.append({"delay": delay, "slot": slot, "pending": pending, "records": records, "reader": reader})
    return found


# --- history ---------------------------------------------------------------------------------

def timeline(variant):
    """[(label, loader)] oldest first: the commits before 90.4, then every snapshot."""
    path = f"neptune/single-set-{variant}_hold-gyro_latest.json"
    points = []
    for commit in COMMITS:
        def load(commit=commit):
            return json.loads(subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True,
                                             capture_output=True, text=True).stdout)
        points.append((commit, load))
    snapshots = sorted((p for p in (ROOT / "versions/neptune").iterdir() if p.is_dir()),
                       key=lambda p: tuple(int(n) for n in p.name.split(".")))
    for folder in snapshots:
        file = folder / f"single-set-{variant}_hold-gyro_{folder.name}.json"
        points.append((folder.name, lambda file=file: json.loads(file.read_text(encoding="utf-8"))))
    return points


RENAMED = {"Steering | Menu Left: Entry Point": "Stateful | Menu Left: Entry Point",
           "Steering | Menu Right: Entry Point": "Stateful | Menu Right: Entry Point"}
SPLIT = {"button_menu": "Menu Left: Entry Point", "button_escape": "Menu Right: Entry Point"}


def today(title, control=None):
    """An older layout's layer title as the layer is called now.

    `(Gyro) X` (until 90.0) and the July reference's `*X` are `Gyro | X`. The one menu Entry Point
    (until a4c2fe5) is the left or the right one by its button. The Steering menu Entry Points
    became the stateful ones in 90.21.
    """
    for prefix in ("(Gyro) ", "*"):
        if title.startswith(prefix):
            return "Gyro | " + title[len(prefix):]
    if title == "Menu Buttons: Entry Point" and control:
        return SPLIT.get(control[1], title)
    return RENAMED.get(title, title)


def keys(found):
    """The comparable facts of one audit, under today's titles: {slot: (ms, targets)} and the record keys."""
    slots, records = {}, set()
    for r in found:
        delay, slot = r["delay"], r["slot"]
        slot = (today(slot[0], slot[1]),) + slot[1:]
        slots[slot] = (delay.delay, tuple(today(t) for t in targets(delay)) or delay.outputs)
        for how, layer, control, kind, (what, which), verdict in r["records"]:
            # an entry in the one menu Entry Point is in the left one for Select's delay and the right one for Start's
            layers = {today(layer, control), today(layer, slot[1])} - {"Menu Buttons: Entry Point"} or {layer}
            for title in layers:
                records.add((slot, how, title, control, kind, (what, today(which)), verdict))
    return slots, records


def since(present, labels):
    """(the first label where it is present, the runs of labels after that where it is missing)."""
    first = present.index(True)
    gaps, run = [], []
    for label, there in list(zip(labels, present))[first:]:
        if not there:
            run.append(label)
        elif run:
            gaps.append(run[0] if len(run) == 1 else f"{run[0]} to {run[-1]}")
            run = []
    return labels[first], ", ".join(gaps)


def versions_of(variant):
    """{commit: the version its layout states} for the commits before 90.4."""
    path = f"neptune/single-set-{variant}_hold-gyro_latest.json"
    found = {}
    for commit in COMMITS:
        text = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        found[commit] = json.loads(text)["controller_mappings"]["title"].rsplit(":: ", 1)[-1].strip()
    return found


# --- output ------------------------------------------------------------------------------------

def describe_ops(ops, limit=6):
    text = [("+" if op == "add_layer" else "-" if op == "remove_layer" else "hold ") + title for op, title in ops]
    return " ; ".join(text[:limit]) + (f" ; and {len(text) - limit} more" if len(text) > limit else "")


def as_json(found, history=None, july=None):
    result = []
    for r in found:
        delay, slot = r["delay"], r["slot"]
        resets = []
        if delay.control != ALWAYS_ON and targets(delay):
            for source, group in r["reader"].layout.active(delay.layer).items():
                for part in group.get("inputs", {}) if group["mode"] != "disabled" else ():
                    if defined(group, part):
                        resets += [e for e in r["reader"].entries(delay.layer, (source, part))
                                   if e.repeats and e.ops and e.kind != "release" and not e.delay
                                   and all(op == "remove_layer" for op, _ in e.ops)
                                   and {t for _, t in e.ops} <= set(targets(delay))]
        item = {"layer": delay.layer, "input": name(delay.control), "control": list(delay.control), "kind": delay.kind,
                "ms": delay.delay, "role": slot[2], "targets": list(targets(delay)), "outputs": list(delay.outputs),
                "does": describe_ops(delay.ops) or " ; ".join(delay.outputs),
                "chord": delay.condition.label if delay.condition else "",
                "held": [sorted(name(c) for c in held) for held in held_sets(delay)],
                "resets": [[name(e.control), e.rate] for e in resets], "pending_stacks": len(r["pending"]),
                "interruptions": []}
        if history:
            item["since"], item["gaps"], item["changes"] = history["slots"][slot]
        if july is not None:
            item["july"] = july[0].get(slot)
        if history:
            item["gone"] = [{"trigger": how, "layer": layer, "input": name(control), "kind": kind, "effect": what[0],
                             "effect_layer": what[1], "gate": verdict[0], "gate_detail": verdict[1], "first": first, "last": last}
                            for how, layer, control, kind, what, verdict, first, last in history["gone"].get(slot, [])]
        for record, seen in sorted(r["records"].items(), key=lambda kv: (kv[0][0], kv[0][4], kv[0][1], kv[0][2] or ())):
            how, layer, control, kind, what, verdict = record
            stack, entry, count = seen["stack"], seen["entry"], seen["count"]
            one = control is not None
            line = {"trigger": how, "layer": layer, "where": sorted(seen["where"]), "inputs": sorted(seen["inputs"]),
                    "kind": kind, "effect": what[0], "effect_layer": what[1], "detail": sorted(d for d in seen["detail"] if d),
                    "gate": verdict[0], "gate_detail": verdict[1],
                    "repeats": bool(one and entry and entry.repeats), "rate": entry.rate if one and entry else None,
                    "does": (describe_ops(entry.ops) if entry else "nothing is bound") if one else "",
                    "stacks": count, "example": " > ".join(stack)}
            if history:
                line["since"], line["gaps"] = history["records"][(slot,) + record]
            if july is not None:
                line["july"] = ((slot,) + record) in july[1]
            item["interruptions"].append(line)
        result.append(item)
    return result


def with_history(variant, found):
    """{"slots": {slot: (since, gaps, changes)}, "records": {key: (since, gaps)}} for the newest layout."""
    points = timeline(variant)
    stated = versions_of(variant)
    labels = [f"{stated[label]} ({label})" if label in stated else label for label, _ in points]
    facts = []
    for label, load in points:
        facts.append(keys(audit(Layout(load()))))
        print(f"  {variant} {label}: {len(facts[-1][0])} delays, {len(facts[-1][1])} interruptions", file=sys.stderr)
    slots, records = keys(found)
    if facts[-1] != (slots, records):
        raise SystemExit(f"{variant}: the working layout is not the newest snapshot; snapshot it first")
    history = {"slots": {}, "records": {}}
    for slot in slots:
        first, gaps = since([slot in f[0] for f in facts], labels)
        changes, last = [], None
        for label, (known, _) in zip(labels, facts):
            if slot in known and known[slot] != last:
                last = known[slot]
                changes.append([label, last[0], list(last[1])])
        history["slots"][slot] = (first, gaps, changes)
    for record in records:
        history["records"][record] = since([record in f[1] for f in facts], labels)
    # what came and went: lines of a delay that is still here, and delays that are not
    history["gone"], history["retired"] = defaultdict(list), []
    for record in sorted(set().union(*(f[1] for f in facts)) - records, key=repr):
        present = [record in f[1] for f in facts]
        last = len(present) - 1 - present[::-1].index(True)
        if record[0] in slots and record[3] is not None:               # not the folded unrelated removals
            history["gone"][record[0]].append(record[1:] + (labels[present.index(True)], labels[last]))
    for slot in sorted(set().union(*(f[0] for f in facts)) - set(slots), key=repr):
        present = [slot in f[0] for f in facts]
        last = len(present) - 1 - present[::-1].index(True)
        ms, does = facts[last][0][slot]
        history["retired"].append({"layer": slot[0], "input": name(slot[1]), "role": slot[2], "ms": ms, "does": list(does),
                                   "first": labels[present.index(True)], "last": labels[last]})
    return history


def dump(result):
    """The result as JSON with one interruption per line, so that a rerun gives a readable diff."""
    out = ["{"]
    for v, (variant, found) in enumerate(result.items()):
        head = {k: value for k, value in found.items() if k != "delays"}
        out.append(f' {json.dumps(variant)}: {json.dumps(head)[:-1]}, "delays": [')
        for d, delay in enumerate(found["delays"]):
            head = {k: value for k, value in delay.items() if k != "interruptions"}
            out.append(f"  {json.dumps(head)[:-1]}, \"interruptions\": [")
            lines = [json.dumps(line) for line in delay["interruptions"]]
            out += [f"   {line}{',' if i < len(lines) - 1 else ''}" for i, line in enumerate(lines)]
            out.append("  ]}" + ("," if d < len(found["delays"]) - 1 else ""))
        out.append(" ]}" + ("," if v < len(result) - 1 else ""))
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--no-history", action="store_true", help="skip the older versions: no 'since' column")
    parser.add_argument("--layer", help="print one host layer's delays, from the default layout, and write nothing")
    args = parser.parse_args()
    result = {}
    for variant in VARIANTS:
        data = json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text(encoding="utf-8"))
        layout = Layout(data)
        if args.layer:
            if variant == "default":
                print(json.dumps(as_json(audit(layout, args.layer)), indent=1))
            continue
        found = audit(layout)
        history = None if args.no_history else with_history(variant, found)
        july = keys(audit(Layout(json.loads(JULY.read_text(encoding="utf-8"))))) if variant == "default" else None
        result[variant] = {"version": data["controller_mappings"]["title"].rsplit(":: ", 1)[-1].strip(),
                           "retired": history["retired"] if history else [],
                           "july_only": sorted(f"{slot[0]}: {name(slot[1])}, {ms} ms, {', '.join(does) or 'removes itself'}"
                                               for slot, (ms, does) in july[0].items() if slot not in keys(found)[0]) if july else [],
                           "delays": as_json(found, history, july)}
    if args.layer:
        return
    (HERE / "interruptions.json").write_text(dump(result), encoding="utf-8")
    for variant, found in result.items():
        lines = sum(len(d["interruptions"]) for d in found["delays"])
        print(f"{variant} {found['version']}: {len(found['delays'])} delays, {lines} interruptions")


if __name__ == "__main__":
    main()
