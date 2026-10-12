"""Every bind that adds or removes a pad click layer, with the guard chord beside it.

    python3 findings/2026-10-11-pad-click-audit/binds.py [default|alternative]
"""
import sys, json
sys.path.insert(0, '.')
from collections import defaultdict
from tools.convert_runtime_ids import generate_lookup, ids_to_titles


def load(variant):
    numeric = json.load(open(f'neptune/single-set-{variant}_hold-gyro_latest.json'))
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


from steam_layout.model import Layout, entries, actions, EMPTY
from steam_layout.flow_model import chord_condition

variant = sys.argv[1] if len(sys.argv) > 1 else 'default'
L = Layout(load(variant))
ENTRY = [t for t in L.presets if t.endswith(': Click Entry Point')]
FINAL = [t for t in L.presets if t in ('LTP: Arrow Keys', 'RTP: Mouse Buttons', 'LTP: Middle Click', 'RTP: Middle Click')]
CLICK = ENTRY + FINAL

def chord_label(e):
    try:
        return chord_condition(e.get('settings') or {}).label
    except Exception as error:
        return f'?{error}'

rows = defaultdict(list)       # (ops signature) -> [(layer, source, input, kind, guard, repeat)]
for title in L.presets:
    for source, group in L.active(title).items():
        for name, value in (group.get('inputs') or {}).items():
            found = list(entries(value.get('activators', {})))
            guards = [chord_label(e) for kind, e in found if kind == 'chord' and actions(e) == [EMPTY + ', , ']
                      and (e.get('settings') or {}).get('interruptable') == '0']
            for kind, e in found:
                ops = L.layer_ops(e)
                hit = [(op, t) for op, t in ops if t in CLICK]
                if not hit:
                    continue
                s = e.get('settings') or {}
                how = kind + (' inverted' if s.get('edge_binding_invert') == '1' else '') + (' repeat' if s.get('hold_repeats') == '1' else '') \
                      + (f' delay {s["delay_start"]}' if s.get('delay_start') else '') + (' chord on ' + chord_label(e) if kind == 'chord' else '')
                guard = guards[0] if guards and kind == 'Full_Press' and s.get('interruptable') != '0' else None
                rows[title].append((source, name, how, guard, tuple(hit), len(ops)))

print('click layers:', CLICK)
for title, found in rows.items():
    print(f'\n{title}')
    for source, name, how, guard, hit, n in found:
        adds = [t for op, t in hit if op != 'remove_layer']
        removes = [t for op, t in hit if op == 'remove_layer']
        print(f'   {source}/{name:22} {how:34} guard: {guard or "-":28} '
              + (f'ADD {adds} ' if adds else '') + (f'removes {[t.replace(": Click Entry Point", ": CEP") for t in removes]} of {n} commands' if removes else ''))
