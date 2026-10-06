"""Dump layers of the July reference layout: every group of a layer, active or not, with its binds.

Read-only. Run from the repository root; the first argument is a source filter or "-":

    python3 findings/2026-10-04-july-stick-clears/dump.py - "Split Stick" "Split Stick Fallback"
"""
import json, sys, re
sys.path.insert(0, '.')
from steam_layout.model import Layout, entries, actions
L = Layout(json.load(open('findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json')))
ids = {str(i + 1): L.titles[k] for i, k in enumerate(L.order)}
def show(a):
    return re.sub(r'(add_layer|remove_layer|hold_layer) (\d+)', lambda m: f"{m.group(1)} [{ids.get(m.group(2), m.group(2))}]", a.replace('controller_action ', '')).replace(', , ', '')
def dump(title, sources=()):
    print('==', title)
    for gid, state in L.presets[title]['group_source_bindings'].items():
        source, _, rest = state.partition(' ')
        if sources and source not in sources: continue
        g = L.groups[gid]
        print(f'  [{source}] ({rest}) mode {g.get("mode")} {g.get("settings") or {}}')
        for name, slot in g.get('inputs', {}).items():
            acts = slot.get('activators', {})
            if not acts: print(f'    {name}: empty'); continue
            for kind, e in entries(acts):
                ex = [show(x) for x in reversed(actions(e))]
                print(f'    {name} {kind} {e.get("settings") or {}}: ' + ' ; '.join(ex))
if __name__ == '__main__':
    srcs = tuple(sys.argv[1].split(',')) if sys.argv[1] != '-' else ()
    for t in sys.argv[2:]: dump(t, srcs)
