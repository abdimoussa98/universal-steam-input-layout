"""The order of the entries on every stick input that has a cleanup function and a guard.

Read-only. Run from the repository root, with the versions to survey:

    python3 findings/2026-10-06-menu-entry-point-stick-touches/order.py 90.23 90.24 90.35

A cleanup function is a repeating Regular Press that only removes layers; the guard is the chord
beside it. For each stick input (touch, edge, click) it prints the stored order of the entry
types and how many inputs and layers have it.
"""
import json,sys,collections
sys.path.insert(0,'.')
from steam_layout.model import Layout, entries
def survey(path):
    L=Layout(json.load(open(path)))
    pat=collections.defaultdict(list)
    for t in L.presets:
        for src in ('joystick','right_joystick'):
            g=L.active(t).get(src) or {}
            for name in ('touch','edge','click'):
                slot=g.get('inputs',{}).get(name)
                if not slot: continue
                es=list(entries(slot.get('activators',{})))
                kinds=[k for k,_ in es]
                cleanup=any(k=='Full_Press' and (e.get('settings') or {}).get('hold_repeats')=='1' and L.layer_ops(e) and all(op=='remove_layer' for op,_ in L.layer_ops(e)) for k,e in es)
                if cleanup and 'chord' in kinds:
                    pat[(name,tuple(kinds))].append((t,src))
    return pat
if __name__=='__main__':
    for v in sys.argv[1:]:
        p=f'versions/neptune/{v}/single-set-default_hold-gyro_{v}.json'
        pat=survey(p)
        print('=====',v, sum(len(x) for x in pat.values()), 'stick inputs with a cleanup function and a guard')
        for (name,kinds),where in sorted(pat.items(), key=lambda kv:(kv[0][0],-len(kv[1]))):
            layers=sorted({t for t,_ in where})
            print(f'  {name:<6} {" > ".join(kinds):<44} {len(where):>3} inputs in {len(layers):>2} layers' + ('' if len(layers)>8 else ': '+', '.join(layers)))
