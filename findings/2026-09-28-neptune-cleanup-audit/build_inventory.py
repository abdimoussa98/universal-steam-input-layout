#!/usr/bin/env python3
"""Build the cleanup audit evidence from title-form copies; never edit layouts."""
import json, re, hashlib, collections, bisect, csv, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMP = None

def pointer_lines(raw):
    decoder = json.JSONDecoder()
    starts = [0] + [m.end() for m in re.finditer('\n', raw)]
    result = {}
    def ws(pos):
        return re.compile(r'\s*').match(raw, pos).end()
    def walk(pos, path):
        pos = ws(pos)
        result[path] = bisect.bisect_right(starts, pos)
        if raw[pos] == '{':
            pos = ws(pos + 1)
            while raw[pos] != '}':
                key, pos = decoder.raw_decode(raw, pos)
                pos = ws(pos)
                assert raw[pos] == ':'
                pos = ws(walk(pos + 1, path + '/' + key.replace('~','~0').replace('/','~1')))
                if raw[pos] == ',': pos = ws(pos + 1)
                else: assert raw[pos] == '}'
            return pos + 1
        if raw[pos] == '[':
            pos, i = ws(pos + 1), 0
            while raw[pos] != ']':
                pos = ws(walk(pos, path + '/' + str(i)))
                i += 1
                if raw[pos] == ',': pos = ws(pos + 1)
                else: assert raw[pos] == ']'
            return pos + 1
        _, pos = decoder.raw_decode(raw, pos)
        return pos
    assert ws(walk(0,'')) == len(raw)
    return result

def extract(variant):
    filename = f'neptune/single-set-{variant}_hold-gyro_latest.json'
    raw = (ROOT / filename).read_text()
    original = json.loads(raw)
    data = json.loads(Path(TEMP,variant+'.json').read_text())
    cm = data['controller_mappings']
    lines = pointer_lines(raw)
    groups = {g['id']: g for g in cm['group']}
    names = {k:v['title'] for k,v in {**cm['actions'],**cm['action_layers']}.items()}
    owners = collections.defaultdict(list)
    for p in cm['preset']:
        for gid, source_state in p.get('group_source_bindings',{}).items():
            source, state = source_state.rsplit(' ',1)
            owners[gid].append(dict(layer=names[p['name']], preset=p['name'],source=source,state=state))
    entries=[]
    for gi,g in enumerate(cm['group']):
        for inp, val in g.get('inputs',{}).items():
            for bank in ('activators','disabled_activators'):
                for kind, values in val.get(bank,{}).items():
                    for ei,e in enumerate(values if isinstance(values,list) else [values]):
                        pointer=f'/controller_mappings/group/{gi}/inputs/{inp}/{bank}/{kind}'
                        if isinstance(values,list): pointer+=f'/{ei}'
                        bs=e.get('bindings',{}).get('binding',[])
                        bs=bs if isinstance(bs,list) else [bs]
                        commands=[]
                        for bi,b in enumerate(bs):
                            m=re.search(r'controller_action (add_layer|remove_layer|hold_layer|CHANGE_PRESET) \{\{(.*?)\}\}(.*)',b)
                            if m: commands.append(dict(operation=m[1],target=m[2].removeprefix('Base::'),suffix=m[3],array_index=bi))
                        entries.append(dict(id=f'{variant[0].upper()}:{g["id"]}:{inp}:{bank}:{kind}:{ei}',variant=variant,file=filename,
                            group_id=g['id'],group_index=gi,mode=g['mode'],input=inp,bank=bank,activation=kind,index=ei,
                            pointer=pointer,line=lines[pointer],settings=e.get('settings',{}),group_settings=g.get('settings',{}),
                            bindings=bs,commands=commands,owners=owners[g['id']],mode_shift_owners=[]))
    # Conditional mode shifts: propagate only from enabled entries in active owners.
    for _ in range(len(groups)):
        changed=False
        for e in entries:
            if e['bank']!='activators': continue
            contexts=[o for o in e['owners'] if o['state']=='active']+e['mode_shift_owners']
            for b in e['bindings']:
                m=re.match(r'mode_shift (\S+) (\d+)',b)
                if not m: continue
                assert m[2] in groups
                for o in contexts:
                    context=dict(layer=o['layer'],preset=o['preset'],source=m[1],state='mode_shift',via=e['id'])
                    for target in entries:
                        if target['group_id']==m[2] and context not in target['mode_shift_owners']:
                            target['mode_shift_owners'].append(context);changed=True
        if not changed: break
    for e in entries:
        e['status']='active' if any(o['state']=='active' for o in e['owners']) else 'mode_shift' if e['mode_shift_owners'] else 'inactive' if e['owners'] else 'unreferenced'
        e['removes']=[c['target'] for c in e['commands'] if c['operation']=='remove_layer']
        e['adds']=[c['target'] for c in e['commands'] if c['operation']=='add_layer']
        e['holds']=[c['target'] for c in e['commands'] if c['operation']=='hold_layer']
    assert sum(len(e['removes']) for e in entries)==raw.count('controller_action remove_layer ')
    assert sum(len(e['commands']) for e in entries)==len(re.findall(r'controller_action (?:add_layer|remove_layer|hold_layer|CHANGE_PRESET) ',raw))
    return dict(variant=variant,file=filename,sha256=hashlib.sha256(raw.encode()).hexdigest(),layers=names,entries=entries,
                groups_total=len(groups),group_owners={k:v for k,v in owners.items() if v})

def active_owners(e):
    return [o for o in e['owners'] if o['state'] == 'active'] + e['mode_shift_owners']

def siblings(e, entries):
    return [s for s in entries if s['group_id'] == e['group_id'] and s['input'] == e['input']
            and s['bank'] == e['bank'] and s['id'] != e['id']]

def kind(e, entries):
    if e['input'] == 'always_on_action': return 'timed self-removal'
    if e['activation'] == 'release': return 'release'
    if e['settings'].get('edge_binding_invert') == '1': return 'inverted threshold'
    if e['settings'].get('repeat_rate') in ('250','300','350'): return 'delayed-apply reset'
    if any(s['activation'] == 'chord' for s in siblings(e, entries)): return 'press beside chord'
    if e['adds']: return 'second-press transition'
    if e['removes'] == ['RTP: Double Tap']: return 'cancel tap window'
    return 'contextual press'

def scope(e, owner):
    if set(e['removes']) == {owner}: return 'self only'
    if owner in e['removes']: return 'self + related'
    return 'other layers only'

def md(s):
    return str(s).replace('|', '\\|').replace('\n', '<br>')

def ref(e):
    return f'[g{e["group_id"]} {e["input"]} {e["activation"]}[{e["index"]}]](../../{e["file"]}#L{e["line"]})'

def owned(e, title, state='active'):
    return any(o['layer'] == title and o['state'] == state for o in e['owners'])

def generate(reports, destination):
    summaries=[]
    inventory=[]
    for r in reports:
        entries=r['entries']
        clean=[e for e in entries if e['removes']]
        live=[e for e in clean if e['status'] == 'active']
        summary={k:r[k] for k in ('variant','file','sha256','groups_total')}
        summary.update(
            action_sets=1, layer_count=len(r['layers'])-1,
            active_groups=sum(any(o['state']=='active' for o in owners) for owners in r['group_owners'].values()),
            unreferenced_groups=r['groups_total']-len(r['group_owners']),
            mode_shift_groups=sorted({e['group_id'] for e in entries if e['mode_shift_owners']},key=int),
            command_entries=len(entries), cleanup_entries=len(clean),
            cleanup_entries_by_status=dict(collections.Counter(e['status'] for e in clean)),
            removal_subcommands=sum(len(e['removes']) for e in clean),
            active_removal_subcommands=sum(len(e['removes']) for e in live),
            active_cleanup_types=dict(collections.Counter(kind(e,entries) for e in live)),
            active_cleanup_scopes=dict(collections.Counter(scope(e,active_owners(e)[0]['layer']) for e in live)),
            disabled_entries=sum(e['bank']=='disabled_activators' for e in entries),
            layers=[])
        for e in entries:
            if not e['commands']: continue
            inventory.append(dict(
                variant=r['variant'],id=e['id'],status=e['status'],group=e['group_id'],mode=e['mode'],
                owners=json.dumps(e['owners'],ensure_ascii=False),input=e['input'],activation=e['activation'],
                bank=e['bank'],cleanup_type=kind(e,entries) if e['removes'] else '',
                removes=json.dumps(e['removes'],ensure_ascii=False),adds=json.dumps(e['adds'],ensure_ascii=False),
                holds=json.dumps(e['holds'],ensure_ascii=False),settings=json.dumps(e['settings']),
                group_settings=json.dumps(e['group_settings']),
                bindings_in_storage_order=json.dumps(e['bindings'],ensure_ascii=False),
                siblings=json.dumps([dict(activation=s['activation'],settings=s['settings'],bindings=s['bindings'])
                                     for s in siblings(e,entries)],ensure_ascii=False),
                file=e['file'],line=e['line'],json_pointer=e['pointer']))
        doc=[f'# {r["variant"].title()} 90.2: every layer and cleanup', '',
             f'Source: [{r["file"]}](../../{r["file"]}). SHA-256: `{r["sha256"]}`.', '',
             'See [AUDIT.md](AUDIT.md) for interpretation, gaps, and the consistency proposal. This catalog is generated by `build_inventory.py`.', '',
             'Every cleanup in active groups appears below. Dormant definitions have their own appendix. Incoming entry/removal counts count command entries, not subcommands. Entries owned by an active group are candidates whenever that layer is active; this is not proof that a layer above it leaves the input exposed.', '',
             'Within each pattern, targets and bindings retain JSON storage order; subcommands execute in reverse according to the repository rule. `Settings {}` means omitted settings, not explicit defaults. Guard columns show sibling chord settings, not a proven Boolean condition. See the CSV for complete sibling outputs, other activators, raw bindings, group settings, and JSON pointers.', '',
             'Layer numbers below are runtime IDs; Base is 1. Alternative L2/R2 names correspond to default L1/R1 modifier roles.', '']
        for runtime_id,(preset,title) in enumerate(r['layers'].items(),1):
            local=[e for e in live if owned(e,title)]
            dormant=[e for e in clean if owned(e,title,'inactive')]
            incoming=[e for e in entries if e['status'] in ('active','mode_shift') and title in e['adds']+e['holds']]
            exits=[e for e in live if title in e['removes']]
            own_exits=[e for e in exits if owned(e,title)]
            info=dict(title=title,preset=preset,runtime_id=runtime_id,
                      local_active_cleanup_entries=len(local),local_dormant_cleanup_entries=len(dormant),
                      incoming_add_or_hold_entries=len(incoming),incoming_explicit_remove_entries=len(exits),
                      removal_activation_types=dict(collections.Counter(e['activation'] for e in exits)),
                      local_cleanup_ids=[e['id'] for e in local],incoming_entry_ids=[e['id'] for e in incoming],
                      incoming_removal_ids=[e['id'] for e in exits])
            summary['layers'].append(info)
            doc.extend([f'## {runtime_id}. {title}', '',
                        f'Preset `{preset}`. Active cleanup entries owned here: **{len(local)}**; dormant: **{len(dormant)}**. Incoming add/hold entries: **{len(incoming)}**; explicit removal entries anywhere active: **{len(exits)}**.', ''])
            if incoming:
                doc.extend(['**How it is entered:**',''])
                groups=collections.defaultdict(list)
                for e in incoming:
                    own=', '.join(o['layer'] for o in active_owners(e))
                    op='hold_layer' if title in e['holds'] else 'add_layer'
                    groups[(own,op,json.dumps(e['settings'],sort_keys=True))].append(e)
                for (own,op,settings),es in groups.items():
                    doc.append(f'- {own}: `{op}`, settings `{settings}` — '+', '.join(ref(e) for e in es)+'.')
                doc.append('')
            else:
                doc.extend(['Base is the action set, not a removable layer.' if title=='Base' else 'No enabled add/hold reference found.', ''])
            if exits:
                external=collections.Counter(o['layer'] for e in exits for o in active_owners(e) if o['layer']!=title)
                doc.extend([f'**How it is removed:** {len(own_exits)} command entries owned here; external removal entries by owner: '+
                            (', '.join(f'{n} ({count})' for n,count in external.items()) or 'none')+'.', ''])
                if all(e['activation']=='release' for e in exits):
                    doc.extend(['**Release-only explicit removal:** no active press, threshold, or timer targets this layer. For Gyro this is an intentional mode toggle; see the audit for the temporary-layer gaps.', ''])
            clusters=collections.defaultdict(list)
            for e in local:
                clusters[json.dumps(e['bindings'],ensure_ascii=False)].append(e)
            for i,(bs,es) in enumerate(clusters.items(),1):
                e=es[0]
                doc.extend([f'### Cleanup pattern {i}: {scope(e,title)}', '',
                            '**Removes:** '+', '.join('`'+s+'`' for s in e['removes'])+'.', ''])
                if e['adds'] or e['holds']:
                    doc.extend(['**Also applies:** '+', '.join('`'+s+'`' for s in e['adds']+e['holds'])+'.',
                                '**Full storage order:**', '', '```json',json.dumps(e['bindings'],indent=2,ensure_ascii=False),'```',''])
                doc.extend(['| Source / exact location | Type | Activator settings | Sibling chord settings |', '|---|---|---|---|'])
                for e in es:
                    source=', '.join(o['source'] for o in e['owners'] if o['layer']==title and o['state']=='active')
                    guards=[s['settings'] for s in siblings(e,entries) if s['activation']=='chord']
                    doc.append(f'| {md(source)} / {ref(e)} | {kind(e,entries)} | `{md(json.dumps(e["settings"]))}` | `{md(json.dumps(guards))}` |')
                doc.append('')
            if not local: doc.extend(['No explicit cleanup command in this layer\'s active groups.',''])
        doc.extend(['## Dormant cleanup definitions', '',
                    'These are inactive alternate groups, not backup exits available in the current presets. No mode-shift target or unreferenced group contains an explicit cleanup.', '',
                    '| Owner | Location | Targets | Settings |','|---|---|---|---|'])
        for e in clean:
            if e['status']=='active':continue
            doc.append('| '+md(', '.join(o['layer'] for o in e['owners']))+' | '+ref(e)+' | '+md(', '.join(e['removes']))+' | `'+md(json.dumps(e['settings']))+'` |')
        (destination/(r['variant']+'-layers.md')).write_text('\n'.join(doc)+'\n')
        summaries.append(summary)
    with (destination/'lifecycle-inventory.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(inventory[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(inventory)
    (destination/'audit-summary.json').write_text(json.dumps(summaries,indent=2,ensure_ascii=False)+'\n')
    print('Generated',len(inventory),'lifecycle command-entry rows,',sum(bool(json.loads(row['removes'])) for row in inventory),'with explicit removals.')
    return summaries

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readable-dir',required=True,type=Path,help='Contains default.json and alternative.json made by convert_runtime_ids.py to-titles --output')
    args=parser.parse_args()
    TEMP=str(args.readable_dir)
    sys.path.insert(0,str(ROOT))
    from convert_runtime_ids import generate_lookup, titles_to_ids
    from audit_command_budget import audit_layout, unique_object
    for variant in ('default','alternative'):
        path=ROOT/f'neptune/single-set-{variant}_hold-gyro_latest.json'
        raw=path.read_text()
        data=json.loads(raw,object_pairs_hook=unique_object)
        cm=data['controller_mappings']
        keys=[int(k.split('_')[1]) for k in cm['action_layers']]
        assert keys==sorted(keys)
        assert [p['name'] for p in cm['preset']]==list(cm['actions'])+list(cm['action_layers'])
        assert [p['id'] for p in cm['preset']]==[str(i) for i in range(len(cm['preset']))]
        lookup=generate_lookup(data)
        assert len(lookup['id_to_title'])==len(lookup['title_to_id'])
        restored,count=titles_to_ids((args.readable_dir/(variant+'.json')).read_text(),lookup)
        assert restored==raw and count==1437, 'Readable copy must match the current source exactly'
        assert not audit_layout(data)['violations']
    reports=[extract(v) for v in ('default','alternative')]
    generate(reports,Path(__file__).resolve().parent)
