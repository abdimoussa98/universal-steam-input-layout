"""The stick-touch binds of the menu Entry Points, through every saved version.

Read-only. Run from the repository root:

    python3 findings/2026-10-06-menu-entry-point-stick-touches/history.py

Prints both stick touches of every menu Entry Point for the July layout and each snapshot under
versions/neptune/, and only where they differ from the version before. Entries are in the order
they are stored, which is the order the Steam editor lists them; inside an entry the commands are
in the order they run.
"""
import json,sys,re,glob,os
sys.path.insert(0,'.')
from steam_layout.model import Layout, entries, actions
def brief(L, ids, kind, e):
    st=e.get('settings') or {}
    keys=[k for k in ('chord_button','gyro_ratchet_button_mask','hold_repeats','repeat_rate','delay_start','interruptable') if k in st]
    cmds=[re.sub(r'controller_action (\w+) (\d+|\{\{Base::.+?\}\}) \d \d.*', lambda m: f"{m.group(1)[:3]} {ids.get(m.group(2), m.group(2)).replace('{{Base::','').replace('}}','')}", a).replace('controller_action ','').replace(', , ','') for a in reversed(actions(e))]
    return f"{kind}({','.join(f'{k}={st[k]}' for k in keys)}): " + ' ; '.join(cmds)
def show(path, label, want=lambda t: 'Menu' in t and 'Entry Point' in t and '!' not in t):
    L=Layout(json.load(open(path)))
    ids={str(i + 1): L.titles[k] for i, k in enumerate(L.order)}
    out=[]
    for t in L.presets:
        if not want(t): continue
        for src in ('joystick','right_joystick'):
            g=L.active(t).get(src)
            slot=(g or {}).get('inputs',{}).get('touch')
            if not slot: out.append((t,src,'-- no touch bind --')); continue
            out.append((t,src,' || '.join(brief(L,ids,k,e) for k,e in entries(slot.get('activators',{})))))
    return out
if __name__=='__main__':
    prev=None
    vers=sorted(os.listdir('versions/neptune'), key=lambda v: [int(x) for x in v.split('.')])
    paths=[('July','findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json')]+[(v,f'versions/neptune/{v}/single-set-default_hold-gyro_{v}.json') for v in vers]
    for label,p in paths:
        cur=show(p,label)
        if cur!=prev:
            print('=====',label)
            for t,src,line in cur: print(f'  {t} | {src}.touch\n      {line[:520]}')
        prev=cur
