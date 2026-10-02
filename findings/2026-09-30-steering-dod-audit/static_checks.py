"""Static Definition-of-Done checks for the steering layers (sections 2, 3, 5, 6, 9).

Usage: python3 static_checks.py <variant> <layout in title form> <pre-steering layout>
Make the title-form copy with convert_runtime_ids.py to-titles -o.
"""
import json,sys,re
v=sys.argv[1]; d=json.load(open(sys.argv[2]))['controller_mappings']
pre=json.load(open(sys.argv[3]))['controller_mappings']
L=d['action_layers']; keys=list(L)
presets={p['name']:p for p in d['preset']}; G={g['id']:g for g in d['group']}
by={l['title']:k for k,l in L.items()}; by['Base']=list(d['actions'])[0]
steer=[k for k in keys if L[k]['title'].startswith('Steering')]
print('## §2 placement')
nums=[int(k.split('_')[1]) for k in keys]
print(' list order == Preset_ order:', nums==sorted(nums))
premax=max(int(k.split('_')[1]) for k in pre['action_layers'])
print(' pre-steering max', premax, 'steering presets', [k for k in steer][:2],'..', 'all appended:', all(int(k.split('_')[1])>premax for k in steer))
titles=[l['title'] for l in L.values()]; print(' unique titles:', len(titles)==len(set(titles)))
def src(t):
    p=presets[by[t]]
    return {b.split()[0]:G[g] for g,b in p['group_source_bindings'].items() if b.endswith(' active')}
def ents(bd):
    for k,it in bd.get('activators',{}).items():
        for e in (it if isinstance(it,list) else [it]): yield k,e
def cmds(e):
    b=e['bindings']['binding']; b=b if isinstance(b,list) else [b]; return list(reversed(b))  # execution order
bad=[]
for k in steer:
    s=json.dumps(src(L[k]['title']))
    if 'hold_layer' in s or 'CHANGE_PRESET' in s: bad.append(L[k]['title'])
print(' hold_layer/CHANGE_PRESET in steering:', bad or 'none')
print('## §9 Always On'); print(' steering layers with always_on_action:', [L[k]['title'] for k in steer if any('always_on_action' in g.get('inputs',{}) for g in src(L[k]['title']).values())] or 'none')
print('## §3 activators'); acts=set()
for k in steer:
    for g in src(L[k]['title']).values():
        for n,bd in g.get('inputs',{}).items():
            for kind,e in ents(bd): acts.add(kind)
print(' activator kinds used:', sorted(acts))
print('## §5 touch release')
trio={'joystick':['LST: Entry Point','LST: Tap Cover','LST: Temporary Gyro'],'right_joystick':['RST: Entry Point','RST: Tap Cover','RST: Temporary Gyro']}
def ops(cl): 
    out=[]
    for c in cl:
        m=re.search(r'(add|remove)_layer \{\{Base::(.*?)\}\}',c)
        if m: out.append(('+' if m[1]=='add' else '-')+m[2])
        elif 'empty_binding' not in c: out.append(c.split(',')[0])
    return out
for k in steer:
    t=L[k]['title']; ss=src(t); row=[]
    for s in ('joystick','right_joystick'):
        bd=ss.get(s,{}).get('inputs',{}).get('touch')
        if not bd: row.append(f'{s}: INHERITS'); continue
        rel=[cmds(e) for kind,e in ents(bd) if kind=='release']
        kinds=sorted(kind for kind,_ in ents(bd))
        r=ops(rel[0]) if rel else None
        ok = r is not None and [x for x in r if x.startswith('-')]==['-'+x for x in trio[s]]
        row.append(f"{s}: {kinds} release={r} {'OK' if ok else 'CHECK'}")
    print(' ',t); [print('     ',x) for x in row]
print('## §6 delayed applies and resets')
for k in steer:
    t=L[k]['title']
    for s,g in src(t).items():
        for n,bd in g.get('inputs',{}).items():
            E=list(ents(bd))
            for kind,e in E:
                st=e.get('settings',{})
                adds=[x[1:] for x in ops(cmds(e)) if x.startswith('+')]
                if 'delay_start' in st and adds:
                    tgt=adds[-1]; D=int(st['delay_start'])
                    resets=[(k2,e2) for k2,e2 in E if k2=='Full_Press' and e2 is not e and e2.get('settings',{}).get('hold_repeats')=='1' and ops(cmds(e2))==['-'+tgt]]
                    rr=[int(e2['settings'].get('repeat_rate','0') or 0) for _,e2 in resets]
                    intr=[e2['settings'].get('interruptable') for _,e2 in resets]
                    tsrc=src(tgt) if tgt in by else {}
                    overrides = n in tsrc.get(s,{}).get('inputs',{})
                    print(f'  {t} [{s}] {n} {kind} delay={D} adds={adds} reset_rate={rr} interruptable={intr} target_overrides_input={overrides}')
