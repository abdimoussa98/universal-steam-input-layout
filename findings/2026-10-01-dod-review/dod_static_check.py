"""Mechanical Definition of Done checks used by the 2026-10-01 review (sections 1, 5, 6, 9).

Usage, from the repo root: PYTHONPATH=. python3 findings/2026-10-01-dod-review/dod_static_check.py default|alternative
Section 1 types are matched by title pattern, which is exactly the gap the review describes.
"""
import json, sys, re
from steam_layout.model import Layout, defined, entries, always_on_layers
from steam_layout.flow_model import Inventory
v = sys.argv[1]
lay = Layout(json.load(open(f"neptune/single-set-{v}_hold-gyro_latest.json")))
inv = Inventory.of(lay)
L, R = ("L1", "R1") if v == "default" else ("L2", "R2")
TYPES = [
 ("Stateful", lambda t: t in ("Gyro", "Steering")),
 ("Always On window", lambda t: t in set(always_on_layers(lay))),
 ("Chorded window", lambda t: t.startswith("Steering | LS") and t.endswith("Double Tap")),
 ("Stick-touch helper", lambda t: re.match(r"(LST|RST): (Entry Point|Tap Cover|Temporary Gyro)$", t)),
 ("Overlay", lambda t: t.endswith(("Tap Cover", "Double Tap Cover", "Temp Cursor Gyro")) or t in ("Menu Right: Enter", "Menu Left: Backspace")),
 ("Ramp or threshold", lambda t: "Ramp Up" in t),
 ("Owner", lambda t: re.search(r"Modifier [012]|Fn Layer|Menu (Left|Right): Entry Point|Scroll (Up|Down)|Transition Set|W Key|S Key|RTP: (Entry Point|Circular Scroll|Mouse Buttons)|LTP: Arrow Keys", t)),
]
types = {}
for t in lay.presets:
    if t == lay.base: continue
    hit = [n for n, f in TYPES if f(t)]
    types[t] = hit
print("§1 untyped:", sorted(t for t, h in types.items() if not h))
print("§1 multi-typed:", sorted((t, h) for t, h in types.items() if len(h) > 1))
# §5 touch release on both sticks
TRIO = {"joystick": "LST", "right_joystick": "RST"}
covers = {t for t, h in types.items() if "Overlay" in h} | {"Gyro Off Ramp Up"}
miss = []
for t in lay.presets:
    if t in (lay.base, "Gyro") or t in covers: continue
    if types.get(t) and "Stick-touch helper" in types[t]: continue
    for src, pre in TRIO.items():
        g = lay.active(t).get(src)
        acts = g["inputs"].get("touch", {}).get("activators", {}) if g else {}
        rel = acts.get("release")
        ops = [x for _, e in entries({"r": rel}) for x in lay.layer_ops(e)] if rel else []
        rem = {x for o, x in ops if o == "remove_layer"}
        if not {f"{pre}: Entry Point", f"{pre}: Tap Cover", f"{pre}: Temporary Gyro"} <= rem:
            miss.append((t, src))
print("§5 missing side release:", len(miss), miss[:12])
# §6 delayed add has scoped reset
bad = []
for t in inv.transitions:
    if t.role != "hold" or not any(o == "add_layer" for o, _ in t.ops) or t.control[1] == "always_on_action": continue
    target = [x for o, x in t.ops if o == "add_layer"][-1]
    sibs = [s for s in inv.transitions if s.layer == t.layer and s.control == t.control and s.role == "reset"]
    ok = [s for s in sibs if s.ops == (("remove_layer", target),)]
    d = int(dict(t.settings).get("delay_start", 0))
    rr = [int(dict(s.settings).get("repeat_rate", 0) or 0) for s in ok]
    if not ok or not all(r > d for r in rr):
        bad.append((t.layer, f"{t.source}/{t.input}", t.activator, d, target, rr))
print("§6 delayed adds without a scoped longer reset:", len(bad))
for b in bad: print("    ", b)
# §9 AO windows: adders add last; window transitions remove self first
ao = set(always_on_layers(lay))
viol = []
for t in inv.transitions:
    for w in ao:
        if ("add_layer", w) in t.ops and t.ops[-1] != ("add_layer", w): viol.append(("adds not last", t.describe()[:90]))
    if t.layer in ao and any(o == "add_layer" for o, _ in t.ops) and t.ops[0] != ("remove_layer", t.layer): viol.append(("not self-first", t.describe()[:90]))
print("§9 violations:", viol)
