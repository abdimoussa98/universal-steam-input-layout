#!/usr/bin/env python3
"""Inventory blocking and Always On ordering without editing the layouts.

Requires default.json / alternative.json title copies made by the repository's
to-titles command. Reuses the preceding cleanup audit's pointer/owner extractor.
"""
import argparse
import collections
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('cleanup_audit', HERE.parent / '2026-09-28-neptune-cleanup-audit/build_inventory.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)
sys.path.insert(0, str(ROOT))
from audit_command_budget import audit_layout, unique_object
from convert_runtime_ids import generate_lookup, titles_to_ids

def empty(b):
    return b.startswith('controller_action empty_binding')

def pure(e):
    return bool(e['bindings']) and all(empty(b) for b in e['bindings'])

def tags(e, entries):
    result=[]
    peers=cleanup.siblings(e, entries)
    if pure(e):
        result.append('conditional empty' if e['activation']=='chord' else 'release empty' if e['activation']=='release' else 'press empty')
    elif any(empty(b) for b in e['bindings']):
        result.append('mixed empty + real commands')
    if e['activation']=='Full_Press' and e['removes'] and e['settings'].get('interruptable')!='0' and any(p['activation']=='chord' for p in peers):
        result.append('cleanup protected by sibling chord')
    if e['activation']=='chord' and any(p['activation']=='Full_Press' and p['removes'] and p['settings'].get('interruptable')!='0' for p in peers):
        result.append('held-state guard')
    if e['commands']:
        result.append('ordered layer operations')
    elif e['bindings'] and not any(empty(b) for b in e['bindings']):
        result.append('output/mode replacement candidate')
    if e['input']=='always_on_action': result.append('Always On')
    return result

def cell(s):
    return str(s).replace('|','\\|').replace('\n','<br>')

def location(e):
    return f'[g{e["group_id"]} {e["input"]} {e["activation"]}[{e["index"]}]](../../{e["file"]}#L{e["line"]})'

def write_csv(path, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        w.writeheader();w.writerows(rows)

def generate(reports, readable_dir):
    all_entries=[];all_groups=[];summaries=[]
    for r in reports:
        entries=r['entries']
        filename=r['file'];raw=(ROOT/filename).read_text()
        cm=json.loads((readable_dir/(r['variant']+'.json')).read_text())['controller_mappings']
        lines=cleanup.pointer_lines(raw)
        by_group={g['id']:g for g in cm['group']}
        timed={o['layer'] for e in entries if e['input']=='always_on_action' and e['status']=='active' for o in e['owners'] if o['state']=='active'}
        active=[e for e in entries if e['status']=='active']
        pure_active=[e for e in active if pure(e)]
        summary=dict(variant=r['variant'],file=filename,sha256=r['sha256'],
            entries=len(entries),empty_entries_by_status=dict(collections.Counter(e['status'] for e in entries if any(empty(b) for b in e['bindings']))),
            active_pure_empty_by_activation=dict(collections.Counter(e['activation'] for e in pure_active)),
            active_mixed_empty_entries=sum(any(empty(b) for b in e['bindings']) and not pure(e) for e in active),
            active_guarded_cleanup_entries=sum('cleanup protected by sibling chord' in tags(e,entries) for e in active),
            disabled_sources=collections.Counter(),always_on_layers=[],layers=[])
        group_lines={}
        for gi,g in enumerate(cm['group']):
            os=r['group_owners'].get(g['id'],[])
            ms=[o for e in entries if e['group_id']==g['id'] for o in e['mode_shift_owners']]
            status='active' if any(o['state']=='active' for o in os) else 'mode_shift' if ms else 'inactive' if os else 'unreferenced'
            line=lines[f'/controller_mappings/group/{gi}'];group_lines[g['id']]=line
            all_groups.append(dict(variant=r['variant'],group=g['id'],status=status,mode=g['mode'],owners=json.dumps(os),
                settings=json.dumps(g.get('settings',{})),inputs=json.dumps(list(g.get('inputs',{}))),file=filename,line=line))
            if g['mode']=='disabled':
                summary['disabled_sources'].update(o['source'] for o in os if o['state']=='active')
        for e in entries:
            all_entries.append(dict(variant=r['variant'],id=e['id'],status=e['status'],group=e['group_id'],mode=e['mode'],
                owners=json.dumps(e['owners'],ensure_ascii=False),mode_shift_contexts=json.dumps(e['mode_shift_owners'],ensure_ascii=False),input=e['input'],activation=e['activation'],bank=e['bank'],
                classifications=json.dumps(tags(e,entries)),settings=json.dumps(e['settings']),
                bindings_storage_order=json.dumps(e['bindings'],ensure_ascii=False),
                siblings=json.dumps([dict(activation=p['activation'],settings=p['settings'],bindings=p['bindings']) for p in cleanup.siblings(e,entries)],ensure_ascii=False),
                file=filename,line=e['line'],json_pointer=e['pointer']))
        doc=[f'# {r["variant"].title()} 90.2: blocking in every layer','',
             f'Source: [{filename}](../../{filename}); SHA-256 `{r["sha256"]}`.','',
             'Read [AUDIT.md](AUDIT.md) for the purpose of each blocking family and the author\'s historical crash workaround. This catalog records every active source and activator, including ordinary outputs and the layers with zero explicit empties. It does not classify all ordinary outputs as intentional blocks. All inactive/unreferenced/conditional entries and source settings are in the CSV inventories.','',
             '**Types:** pure empties suppress an input/event; chord guards protect cleanup from firing during valid holds; mixed arrays still execute their real actions; output/mode replacements may intercept lower layer changes. A group with mode `disabled` is a source block; a group with no explicit inputs is not counted as one. The CSV contains complete payloads and sibling activators.','',
             '**Inheritance limit:** active source membership and explicit input replacement are structural evidence. They do not prove how every possible stale stack and cross-mode inherited input behaves on the Deck.','']
        for rid,(preset,title) in enumerate(r['layers'].items(),1):
            local=[e for e in active if cleanup.owned(e,title)]
            gs=[(by_group[gid],o) for gid,os in r['group_owners'].items() for o in os if o['layer']==title and o['state']=='active']
            counts=collections.Counter(e['activation'] for e in local if pure(e))
            info=dict(title=title,runtime_id=rid,preset=preset,pure_empty_by_activation=dict(counts),
                mixed_empty_entries=sum(any(empty(b) for b in e['bindings']) and not pure(e) for e in local),
                guarded_cleanup_entries=sum('cleanup protected by sibling chord' in tags(e,entries) for e in local),
                disabled_sources=[o['source'] for g,o in gs if g['mode']=='disabled'],always_on=title in timed)
            summary['layers'].append(info)
            doc.extend([f'## {rid}. {title}','',
                f'Pure empty entries by activation: `{json.dumps(dict(counts))}`. Mixed entries containing empty subcommands: **{info["mixed_empty_entries"]}**. Chord-protected cleanup entries: **{info["guarded_cleanup_entries"]}**. Always On owner: **{"yes" if title in timed else "no"}**.','',
                '| Active source | Group / mode | Explicit inputs | Source settings |','|---|---|---|---|'])
            for g,o in gs:
                doc.append(f'| {o["source"]} | [g{g["id"]}](../../{filename}#L{group_lines[g["id"]]}) / **{g["mode"]}** | {cell(", ".join(g.get("inputs",{})) or "none explicitly defined")} | `{cell(json.dumps(g.get("settings",{})))}` |')
            doc.extend(['','| Exact activator | Classification | Settings | Binding payload in storage order |','|---|---|---|---|'])
            for e in local:
                payload='; '.join(e['bindings']).replace('controller_action ','').replace('{{Base::','').replace('}}','').replace(' 0 0, , ','').replace(', , ','')
                doc.append(f'| {location(e)} | {cell("; ".join(tags(e,entries)))} | `{cell(json.dumps(e["settings"]))}` | {cell(payload)} |')
            if not local:doc.append('| — | No explicit input activators; inspect source settings above and inherited behavior | — | — |')
            doc.append('')
            conditional=[e for e in entries if any(o['layer']==title for o in e['mode_shift_owners'])]
            if conditional:
                doc.extend(['**Conditional mode-shift bindings** (not the default active mode):','',
                    '| Exact activator | Classification | Settings | Payload |','|---|---|---|---|'])
                for e in conditional:
                    doc.append(f'| {location(e)} | {cell("; ".join(tags(e,entries)))} | `{cell(json.dumps(e["settings"]))}` | {cell("; ".join(e["bindings"]))} |')
                doc.append('')
            if title in timed:
                mutations=[e for e in local if e['commands']]
                incoming=[e for e in active if title in e['adds']]
                check=dict(title=title,timer_entries=[e['id'] for e in local if e['input']=='always_on_action'],
                    entries=[],exits=[],base_routes=[])
                for e in incoming:
                    # Stronger than just command sorting: add must be the last
                    # executing subcommand in the complete stored array.
                    passed=e['bindings'][0].startswith('controller_action add_layer {{Base::'+title+'}}')
                    check['entries'].append(dict(id=e['id'],line=e['line'],pass_add_last=passed,execution_order=list(reversed(e['bindings']))))
                for e in mutations:
                    passed=e['bindings'][-1].startswith('controller_action remove_layer {{Base::'+title+'}}')
                    check['exits'].append(dict(id=e['id'],line=e['line'],pass_self_first=passed,execution_order=list(reversed(e['bindings']))))
                # Identify whether the timed layer intercepts each Base input
                # with direct add/remove/hold behavior. Mode changes are recorded
                # as a review boundary, not automatically counted as full proof.
                for e in active:
                    if not e['commands'] or not cleanup.owned(e,'Base'):continue
                    source=next(o['source'] for o in e['owners'] if o['state']=='active')
                    matching=[g for g,o in gs if o['source']==source]
                    own=[x for x in local if x['group_id'] in {g['id'] for g in matching} and x['input']==e['input']]
                    status='no explicit interception found'
                    if any(g['mode']=='disabled' for g in matching):status='source disabled'
                    elif own:status='input explicitly redefined'
                    elif any(g['mode']!=e['mode'] for g in matching):status='source mode replaced; runtime inheritance check'
                    check['base_routes'].append(dict(base_entry=e['id'],source=source,input=e['input'],status=status,
                        own_entries=[x['id'] for x in own],groups=[g['id'] for g in matching]))
                summary['always_on_layers'].append(check)
                doc.extend(['**Always On ordering:** '+str(len(incoming))+' incoming bindings add this layer last; '+str(len(mutations))+' directly owned layer-changing bindings remove it first. Exact execution sequences are in `blocking-summary.json`.','',
                    '| Base layer-changing route | Interception in this layer |','|---|---|'])
                for route in check['base_routes']:
                    doc.append(f'| {route["source"]} / {route["input"]} (`{route["base_entry"]}`) | {route["status"]}; groups {", ".join(route["groups"])} |')
                doc.append('')
        summary['disabled_sources']=dict(summary['disabled_sources'])
        summaries.append(summary)
        (HERE/(r['variant']+'-layers.md')).write_text('\n'.join(doc).rstrip('\n')+'\n')
    write_csv(HERE/'activator-inventory.csv',all_entries)
    write_csv(HERE/'source-inventory.csv',all_groups)
    (HERE/'blocking-summary.json').write_text(json.dumps(summaries,indent=2,ensure_ascii=False)+'\n')
    return summaries

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--readable-dir',type=Path,required=True)
    args=p.parse_args();cleanup.TEMP=str(args.readable_dir)
    for variant in ('default','alternative'):
        raw=(ROOT/f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text()
        data=json.loads(raw,object_pairs_hook=unique_object);cm=data['controller_mappings']
        assert cm['title'].endswith('90.2')
        keys=[int(k.split('_')[1]) for k in cm['action_layers']];assert keys==sorted(keys)
        assert [p['name'] for p in cm['preset']]==list(cm['actions'])+list(cm['action_layers'])
        assert [p['id'] for p in cm['preset']]==[str(i) for i in range(len(cm['preset']))]
        lookup=generate_lookup(data);assert len(lookup['id_to_title'])==len(lookup['title_to_id'])
        restored,count=titles_to_ids((args.readable_dir/(variant+'.json')).read_text(),lookup)
        assert restored==raw and count==1437
        assert not audit_layout(data)['violations']
    reports=[cleanup.extract(v) for v in ('default','alternative')]
    summaries=generate(reports,args.readable_dir)
    for s in summaries:
        timed=s['always_on_layers'];incoming=[e for t in timed for e in t['entries']];outgoing=[e for t in timed for e in t['exits']]
        assert all(e['pass_add_last'] for e in incoming)
        assert all(e['pass_self_first'] for e in outgoing)
        print(s['variant'],len(timed),'Always On layers;',len(incoming),'add-last entries;',len(outgoing),'self-first mutation entries; ordering PASS')

if __name__=='__main__':main()
