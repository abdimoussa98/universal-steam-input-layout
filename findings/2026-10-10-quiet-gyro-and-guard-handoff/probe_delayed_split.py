import copy,json,itertools
from tests.scenario import Pad
from steam_layout.model import Layout,actions
from tests.scenarios.neptune.test_scenarios_90_43 import GUARD,home
from tests.scenarios.neptune.test_scenarios_90_44 import enter_with_drivers
for variant in ('default','alternative'):
 d=json.load(open(f'findings/2026-10-10-quiet-cursor-and-steering-touch/{variant}-candidate.json'));l=Layout(d)
 controls=(('switch','left_bumper'),('switch','right_bumper')) if variant=='default' else (('left_trigger','edge'),('right_trigger','edge'))
 for owner in ('Steering',GUARD):
  for src,name in controls:
   e=l.active(owner)[src]['inputs'][name]['activators']['chord'];e['bindings']['binding']=[c for c in actions(e) if ('add_layer' in c)==(owner=='Steering')]
 for direction in ('dpad_north','dpad_south'):
  l.active('Steering')['joystick']['inputs'][direction]['activators']['Soft_Press']['settings']['delay_start']='100'
 failures=[]
 for exposed,reverse,gyro,direction,drivers,carried in itertools.product((True,False),(False,True),(False,True),('up','down'),(('L1',),('R1',),('L1','R1'),('R1','L1')),(False,True)):
  p=Pad(variant,start=home(gyro),data=d,exposed_fires=exposed,reverse_ties=reverse)
  p.push('LS',direction)
  if carried:enter_with_drivers(p,drivers).wait(250)
  else:
   p.enter_steering(settle=False).wait(100).mark().hold(*drivers).wait(250)
  if not p.has('Steering'):
   failures.append((exposed,reverse,gyro,direction,drivers,carried))
 print(variant,'failures',len(failures),'of 128',failures[:8])
