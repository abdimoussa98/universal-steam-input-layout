"""Native Regular/Long/Double direction comparison; not a shipping gesture route."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from convert_runtime_ids import generate_lookup,titles_to_ids
from audit_command_budget import audit_layout
spec=importlib.util.spec_from_file_location('probe_base',HERE/'build_probes.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


def build():
    cm=copy.deepcopy(p.reference.build()['controller_mappings'])
    cm.update(title='Steering native gesture comparison',
              description='Diagnostic: Right Menu enters Normal; R1 holds Mod2 context; A consumes only Normal. Left Menu resets. D-pad Right F1-F4 reports context.')
    cm['action_layers']={};cm['preset']=[];cm['group']=[]
    names=('Base','Native Normal','Native Mod2','Native Consumed')
    def add(n):return p.action('add',n)
    def remove(n):return p.action('remove',n)
    reset=p.sequence(*(remove(n) for n in reversed(names[1:])))
    for i,name in enumerate(names):
        preset=f'Preset_{1000001+i}'
        if i:cm['action_layers'][preset]={'title':name,'legacy_set':'1','set_layer':'1','parent_set_name':'Preset_1000001'}
        refs={}
        def group(source,mode,inputs,settings=None):
            gid=str(len(cm['group']));s=dict(settings or {})
            if i:s['layer']='1'
            cm['group'].append(p.reference.group(gid,mode,inputs,s));refs[gid]=source+' active'
        switches={'button_menu':p.full(reset),'button_escape':p.full(add('Native Normal') if name=='Base' else p.EMPTY)}
        if name!='Base':
            switches['right_bumper']=p.inp(Full_Press=p.entry(p.sequence(remove('Native Consumed'),remove('Native Normal'),add('Native Mod2'))),
                release=p.entry(p.sequence(remove('Native Mod2'),add('Native Normal'),add('Native Consumed'))))
        group('switch','switches',switches)
        group('dpad','dpad',{'dpad_east':p.full(p.key('F'+str(i+1)))},{'requires_click':'0','layout':'0'})
        if name!='Base':
            ls={}
            for direction,input_name in [('UP','dpad_north'),('DOWN','dpad_south')]:
                wheel='mouse_wheel SCROLL_'+direction+', , '
                ls[input_name]=p.full(p.EMPTY) if name=='Native Consumed' else p.inp(
                    Full_Press=p.entry(wheel),
                    Long_Press=p.entry(p.EMPTY,long_press_time=250,interruptable=0),
                    Double_Press=p.entry(wheel,double_tap_time=150,hold_repeats=1,repeat_rate=50,interruptable=0))
            if name=='Native Consumed':ls['edge']=p.full(remove(name),hold_repeats=1,repeat_rate=50)
            group('joystick','dpad',ls,{'requires_click':'0','deadzone':'13276','edge_binding_radius':'6553','edge_binding_invert':'1'})
            output=p.key('M' if name=='Native Mod2' else 'H')
            if name=='Native Normal':output=p.sequence(output,add('Native Consumed'))
            group('button_diamond','four_buttons',{'button_a':p.full(output,interruptable=0)})
        cm['preset'].append({'id':str(i),'name':preset,'group_source_bindings':refs})
    return {'controller_mappings':cm}


def main():
    data=build();assert not audit_layout(data)['violations']
    readable=json.dumps(data,indent='\t')+'\n'
    numeric,_=titles_to_ids(readable,generate_lookup(data));assert '{{' not in numeric
    for suffix,content in [('readable.json',readable),('json',numeric)]:
        (HERE/('native-gestures.'+suffix)).write_text(content)
    subprocess.run(['node',str(ROOT/'convert_vdf.mjs'),str(HERE/'native-gestures.json')],check=True)


if __name__=='__main__':main()
