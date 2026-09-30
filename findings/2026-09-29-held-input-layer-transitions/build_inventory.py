"""Held-input inventory for a title-form Steam Input layout JSON.

Section A lists every press-type activator that adds a layer while its own
input is necessarily held, then classifies what the new layer binds on that
same input (release, delayed, repeating, immediate layer command, output).
Section B lists every repeating layer add. Section C lists non-repeating,
non-delayed press-type adds.

Read-only. Usage (after convert_runtime_ids.py to-titles --output):

    python3 findings/2026-09-29-held-input-layer-transitions/build_inventory.py readable.json
"""
import collections
import json
import re
import sys

PRESS = {"Full_Press", "chord", "Soft_Press", "Long_Press", "Double_Press", "start_press"}
LAYER_CMD = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) \{\{Base::(.+?)\}\}")


def as_list(value):
    return value if isinstance(value, list) else [value]


def load(path):
    cm = json.load(open(path))["controller_mappings"]
    groups = {g["id"]: g for g in cm["group"]}
    names = {**{k: v["title"] for k, v in cm["actions"].items()},
             **{k: v["title"] for k, v in cm["action_layers"].items()}}
    layers = collections.defaultdict(lambda: collections.defaultdict(list))
    for preset in cm["preset"]:
        title = names[preset["name"]]
        for gid, state in preset["group_source_bindings"].items():
            if "inactive" in state or "modeshift" in state:
                continue
            source = state.split()[0]
            for inp, spec in (groups[gid].get("inputs") or {}).items():
                for atype, entries in (spec.get("activators") or {}).items():
                    for entry in as_list(entries):
                        bindings = as_list(entry.get("bindings", {}).get("binding", ""))
                        layers[title][(source, inp)].append((atype, entry.get("settings") or {}, bindings))
    return layers


def ops(bindings):
    out = []
    for b in bindings:
        m = LAYER_CMD.search(b)
        if m:
            out.append((m.group(1), m.group(2)))
        elif "empty_binding" in b:
            out.append(("empty", ""))
        else:
            out.append(("out", b.split(",")[0].strip()))
    return out


def describe(atype, st):
    bits = [atype]
    for key, label in (("delay_start", "delay"), ("repeat_rate", "rate"), ("activation_threshold", "thr"),
                       ("chord_button", "chord"), ("gyro_ratchet_button_mask", "mask")):
        if key in st:
            bits.append(f"{label}={st[key]}")
    if st.get("hold_repeats") == "1":
        bits.append("REPEAT")
    if st.get("edge_binding_invert") == "1":
        bits.append("inverted")
    if st.get("interruptable") == "0":
        bits.append("unint")
    return " ".join(bits)


def classify(atype, st, o):
    layer_cmd = any(k in ("add_layer", "remove_layer", "hold_layer") for k, _ in o)
    suffix = " layer-cmd" if layer_cmd else " output"
    if atype == "release":
        return "release (new event)"
    if int(st.get("delay_start", "0") or 0) > 0:
        return "DELAYED" + suffix
    if st.get("hold_repeats") == "1":
        return "REPEATING" + suffix
    if all(k == "empty" for k, _ in o):
        return "empty block"
    return "IMMEDIATE" + suffix


def execution(o):
    return ", ".join(f"{k} {t}".strip() for k, t in reversed(o))


def main(path):
    layers = load(path)
    print(f"# {path}\n")
    print("## A. Layer added while its adding input is held -> new layer's binding on that input\n")
    for layer, inputs in layers.items():
        for (source, inp), entries in inputs.items():
            for atype, st, bindings in entries:
                if atype not in PRESS:
                    continue
                for kind, target in ops(bindings):
                    if kind != "add_layer":
                        continue
                    print(f"- [{layer}] {source}.{inp} ({describe(atype, st)}) -> add [{target}]")
                    child = layers.get(target, {}).get((source, inp))
                    if not child:
                        print(f"      new layer does not override {source}.{inp}; it falls through")
                        continue
                    for c_type, c_st, c_bind in child:
                        o = ops(c_bind)
                        print(f"      {classify(c_type, c_st, o):22s} | {describe(c_type, c_st):45s} | {execution(o)}")

    print("\n## B. Repeating layer adds\n")
    for layer, inputs in layers.items():
        for (source, inp), entries in inputs.items():
            for atype, st, bindings in entries:
                o = ops(bindings)
                if st.get("hold_repeats") == "1" and any(k in ("add_layer", "hold_layer") for k, _ in o):
                    print(f"- [{layer}] {source}.{inp} {describe(atype, st)} | {execution(o)}")

    print("\n## C. Non-repeating, non-delayed press-type layer adds\n")
    for layer, inputs in layers.items():
        for (source, inp), entries in inputs.items():
            for atype, st, bindings in entries:
                o = ops(bindings)
                if (atype in PRESS and st.get("hold_repeats") != "1"
                        and int(st.get("delay_start", "0") or 0) == 0
                        and any(k in ("add_layer", "hold_layer") for k, _ in o)):
                    print(f"- [{layer}] {source}.{inp} {describe(atype, st)} | {execution(o)}")


if __name__ == "__main__":
    main(sys.argv[1])
