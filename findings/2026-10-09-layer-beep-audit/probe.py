#!/usr/bin/env python3
"""Read-only 90.42 beep-request audit, independent of audible Steam behavior.

The companion dropout probe supplies only preflight/title conversion. This
observer records exact raw per-command flags before calling the unchanged
Simulator._run; it does not replace commands or activation conditions.
Run this file to regenerate the adjacent results.json from working 90.42.
"""
import importlib.util,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tests.scenario import Pad
from steam_layout.simulator import Simulator,COMMAND
from steam_layout.model import actions,entries,TARGET
spec=importlib.util.spec_from_file_location('dropout_probe',ROOT/'findings/2026-10-09-steering-modifier-dropout/probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
DATA,PREFLIGHT=m.load_layouts()
class Observed(Simulator):
 def __init__(self,*a,**kw): self.commands=[];self.execution=0;super().__init__(*a,**kw)
 def _run(self,entry,act=None,tap=False,commands=True):
  if commands:
   source,name=entry.control
   raw=list(entries(self.layout.active(entry.layer)[source]['inputs'][name].get('activators',{})))[entry.index][1]
   stack=list(self.stack);self.execution+=1
   entry_beeps=any((found:=COMMAND.search(command)) and found.group(4)=='1' for command in actions(raw))
   for command_index,command in enumerate(reversed(actions(raw))):
    found=COMMAND.search(command)
    if not found: continue
    op=found.group(1);title=self.layout.resolve(TARGET.search(command).group(2));present=title in stack
    changed=(present and title!=self.base) if op=='remove_layer' else not present
    self.commands.append({'ms':self.now,'execution':self.execution,'layer':entry.layer,'control':list(entry.control),'activator':entry.kind,'entry_index':entry.index,'command_index':command_index,'entry_has_beep_request':entry_beeps,'command':command,'op':op,'target':title,'was_present':present,'changed':changed,'beep_requested':found.group(4)=='1','display_name_requested':found.group(3)=='1'})
    if changed:
     if op=='remove_layer': stack.remove(title)
     else: stack.append(title)
  return super()._run(entry,act,tap,commands)

def fresh(v,start,**options):
 p=Pad(v,data=DATA[v],start=start,**options);p.sim=Observed(p.layout,start=p.layers(*start),**options);return p

def report(p,label,params):
 req=[x for x in p.sim.commands if x['beep_requested']]
 return {'variant':p.variant,'label':label,**params,'beep_request_count':len(req),'beep_requests_on_changed_targets':sum(x['changed'] for x in req),'requests':req,'sim_beeps':[x for x in p.sim.log if x[1]=='beep'],'final':p.stack,'gyro_disabled':p.gyro_off(),'events':[x for x in p.sim.log if x[1] in ('press','release','add','remove','beep')],'commands':[x for x in p.sim.commands if x['entry_has_beep_request'] or x['target']=='Gyro']}

def begin_observation(p):
 """Exclude a real entry gesture's feedback when measuring a subsequent exit."""
 p.sim.commands.clear();p.sim.log.clear();return p
def main():
 CASES=[]
 for v,start,first,release_first,dwell,touch in itertools.product(('default','alternative'),(('Base',),('Base','Gyro')),('L1','R1'),('first','second'),(30,300),(None,'LS','RS','RP')):
  p=fresh(v,start)
  if touch:p.touch(touch).wait(300)
  second='R1' if first=='L1' else 'L1';a,b=(first,second) if release_first=='first' else (second,first)
  p.hold(first).wait(30).hold(second).wait(dwell).let_go(a).wait(30).let_go(b).wait(400)
  if touch:p.lift(touch).wait(400)
  CASES.append(report(p,'two_driver_toggle',dict(start=start,press_first=first,release_first=release_first,overlap_ms=dwell,touch=touch)))
 for v,start,button,dwell in itertools.product(('default','alternative'),(('Base',),('Base','Gyro')),('L1','R1'),(30,300,600)):
  p=fresh(v,start).tap(button,dwell).wait(400)
  CASES.append(report(p,'single_driver',dict(start=start,button=button,hold_ms=dwell)))
 for v,start,menu,stick in itertools.product(('default','alternative'),(('Base',),('Base','Gyro'),('Base','Steering'),('Base','Gyro','Steering'),('Base','Gyro','Cursor Gyro')),('Start','Select'),('LS','RS')):
  p=fresh(v,start).hold(menu).click(stick).let_go(menu).lift(stick).wait(400)
  CASES.append(report(p,'menu_stick_transition',dict(start=start,menu=menu,stick=stick)))
 for v,start,first in itertools.product(('default','alternative'),(('Base',),('Base','Gyro')),('Start','Select')):
  second='Select' if first=='Start' else 'Start'
  p=fresh(v,start).hold(first).wait(30).hold(second).wait(300).let_go(second).let_go(first).wait(400)
  CASES.append(report(p,'menu_keys_entry',dict(start=start,first=first)))
 for v,start,stick in itertools.product(('default','alternative'),(('Base',),('Base','Gyro')),('LS','RS')):
  p=fresh(v,start).touch(stick).wait(300).lift(stick).wait(300)
  CASES.append(report(p,'single_stick_touch',dict(start=start,stick=stick)))
 for v,start in itertools.product(('default','alternative'),(('Base',),('Base','Gyro'))):
  p=fresh(v,start).push('RS').wait(600).lift('RS').wait(300)
  CASES.append(report(p,'turn_assist',dict(start=start)))
 for v,start,first,rel in itertools.product(('default','alternative'),(('Base','Steering'),('Base','Gyro','Steering'),('Base','Gyro','Cursor Gyro')),('L1','R1'),('first','second')):
  p=fresh(v,start);second='R1' if first=='L1' else 'L1';a,b=(first,second) if rel=='first' else (second,first)
  p.hold(first).wait(30).hold(second).wait(30).let_go(a).wait(30).let_go(b).wait(400)
  CASES.append(report(p,'stateful_driver_clear',dict(start=start,first=first,release_first=rel)))
 for v,owner,first in itertools.product(('default','alternative'),('Menu Keys','Cursor Gyro'),('LS','RS')):
  p=fresh(v,('Base',))
  if owner=='Menu Keys':
   p.hold('Select').wait(30).hold('Start').wait(300).let_go('Start').let_go('Select').wait(300)
  else:
   p.hold('Select').click('RS').let_go('Select').lift('RS').wait(300)
  begin_observation(p)
  second='RS' if first=='LS' else 'LS'
  p.push(first).wait(30).push(second).wait(100).lift(first).lift(second).wait(300)
  CASES.append(report(p,'two_stick_exit',dict(owner=owner,first=first,setup='Entered owner through its real menu gesture; setup feedback excluded')))
 for v,button in itertools.product(('default','alternative'),('A','B','X','Y','Up','Down','Left','Right')):
  p=fresh(v,('Base',)).hold('Select').wait(30).hold('Start').wait(300).let_go('Start').let_go('Select').wait(300)
  begin_observation(p).push('LS').wait(30).tap(button).lift('LS').wait(300)
  CASES.append(report(p,'menu_keys_button_exit',dict(button=button,setup='Entered Menu Keys through its real menu gesture; setup feedback excluded')))
 for v,direction in itertools.product(('default','alternative'),('up','down')):
  p=fresh(v,('Base',)).enter_steering(settle=False).lift('LS').wait(300)
  begin_observation(p).push('LS',direction).wait(500).lift('LS').wait(300)
  CASES.append(report(p,'steering_full_exit',dict(direction=direction,setup='Entered Steering through its real menu gesture; setup feedback excluded')))

 def entry_key(layer,control,kind,index):return (layer,*control,kind,index)
 coverage={}
 for v in ('default','alternative'):
  layout=fresh(v,('Base',)).layout
  expected=set();flag_count=0
  for title in layout.presets:
   for source,group in layout.active(title).items():
    for name,binding in group.get('inputs',{}).items():
     for i,(kind,entry) in enumerate(entries(binding.get('activators',{}))):
      flags=[command for command in actions(entry) if (found:=COMMAND.search(command)) and found.group(4)=='1']
      if flags:expected.add(entry_key(title,(source,name),kind,i));flag_count+=len(flags)
  hit={entry_key(r['layer'],r['control'],r['activator'],r['entry_index']) for c in CASES if c['variant']==v for r in c['requests']}
  coverage[v]={'flagged_commands':flag_count,'flagged_entries':len(expected),'runtime_entries_executed':len(expected&hit),'missing_entries':sorted(expected-hit),'unexpected_entries':sorted(hit-expected)}
 OUT={'scope':'Read-only exact beep-flag observation on title-converted installed 90.42; no fault injection or binding edits',
  'preflight':PREFLIGHT,'beep_entry_coverage':coverage,
  'limitations':[
   'A49 identifies the second flag as beep. The simulator logs a beep request even for an absent remove target or already-present add; this is not confirmation that Steam audibly plays every request.',
   'beep_requests_on_changed_targets counts flagged commands that mutate the modeled stack, an alternative effect-only interpretation rather than a claim about Steam audio.',
   'Simulator._run keys entry.beeps by target title rather than command identity; this observer uses each raw command flag independently. All observed request counts are compared against modeled counts.',
   'Cases start from explicitly named owner stacks where stated. New Menu Keys, Cursor Gyro and Steering exit cases use real entry gestures and exclude setup feedback.',
   'The simulator does not model audio mixing, suppression/coalescing, analog stick distances, or Steam sound-device behavior.',
  ],
  'all_exact_counts_match_simulator':all(c['beep_request_count']==len(c['sim_beeps']) for c in CASES),
  'cases':CASES}
 Path(__file__).with_name('results.json').write_text(json.dumps(OUT,indent=2)+'\n')
 print('cases',len(CASES))
 print('flagged-entry coverage',coverage)
 for label in dict.fromkeys(c['label'] for c in CASES):
  grouped={}
  for c in CASES:
   if c['label']!=label:continue
   key=(c['beep_request_count'],c['beep_requests_on_changed_targets'],len(c['sim_beeps']),tuple(c['final']))
   grouped[key]=grouped.get(key,0)+1
  print(label,grouped)
 for c in CASES:
  if c['variant']=='default' and c['label']=='two_driver_toggle' and c['overlap_ms']==30 and c['touch'] is None:
   print('TOGGLE',c['start'],c['press_first'],c['release_first'],'requests',[(x['ms'],x['op'],x['target'],x['changed']) for x in c['requests']],'final',c['final'])

if __name__=='__main__':
 main()
