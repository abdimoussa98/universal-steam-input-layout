"""Generate complete, unverified steering candidates beside the working layouts.

The layered implementation is conservative about Always On isolation. Native
scheduling, output handoff and physical feedback still require Deck acceptance.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids
from audit_command_budget import audit_layout

EMPTY = 'controller_action empty_binding, , '
DIRECTIONS = {'Up': 'dpad_north', 'Down': 'dpad_south'}
CONTEXTS = ('Normal', 'Mod2')
OWNERS = ('W', 'S')
CENTER_RADIUS = '6553'
HOLD_MS = 250
DOUBLE_MS = 150
REPEAT_MS = 50
PREFIX = 'Steering'


def title(*parts):
    return ': '.join((PREFIX,) + parts) if parts else PREFIX


def op(verb, name, beep=0):
    return f'controller_action {verb}_layer {{{{Base::{name}}}}} {beep} 0, , '


def seq(*commands):
    return list(reversed(commands))  # Callers specify execution order.


def entry(binding, **settings):
    e = {'bindings': {'binding': binding}}
    if settings:
        e['settings'] = {k: str(v) for k, v in settings.items()}
    return e


def inp(**activators):
    return {'activators': activators, 'disabled_activators': {}}


def full(binding=EMPTY, **settings):
    return inp(Full_Press=entry(binding, **settings))


def key(k):
    return f'key_press {k}, , '


def wheel(direction):
    return f'mouse_wheel SCROLL_{direction.upper()}, , '


def entries(binding):
    for kind, items in binding.get('activators', {}).items():
        for item in items if isinstance(items, list) else [items]:
            yield kind, item


def commands(e):
    b = e['bindings']['binding']
    return b if isinstance(b, list) else [b]


def output_only(binding):
    """Extract actual key/mouse payload; deliberately discard Base lifecycle."""
    result = []
    settings = {}
    for _, e in entries(binding):
        for command in commands(e):
            if command.startswith(('key_press ', 'mouse_button ', 'mouse_wheel ')) and command not in result:
                result.append(command)
                settings = {k: v for k, v in e.get('settings', {}).items()
                            if k in ('hold_repeats', 'repeat_rate', 'haptic_intensity')}
    return full(result if len(result) > 1 else result[0] if result else EMPTY,
                interruptable=0, **settings)


class Builder:
    def __init__(self, variant):
        self.variant = variant
        self.source = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        # Preserve the original build input after lean steering is installed in
        # Neptune. Rebuilding either candidate must not ingest its own layers.
        frozen = ROOT / 'findings/2026-09-30-steering-lean/pre-steering/neptune' / self.source.name
        if frozen.exists():
            self.source = frozen
        raw = self.source.read_text()
        original = json.loads(raw)
        readable, _ = ids_to_titles(raw, generate_lookup(original))
        self.data = json.loads(readable)
        self.cm = self.data['controller_mappings']
        self.base_count = len(self.cm['action_layers'])
        self.gid = max(int(g['id']) for g in self.cm['group']) + 1
        self.pid = max(int(k.split('_')[1]) for k in self.cm['action_layers']) + 1
        self.new = []
        self.changed = []
        self.mask = '12' if variant == 'default' else '50331651'
        self.by_title = {v['title']: k for section in ('actions', 'action_layers')
                         for k, v in self.cm[section].items()}
        self.presets = {p['name']: p for p in self.cm['preset']}
        self.groups = {g['id']: g for g in self.cm['group']}
        self.base_groups = copy.deepcopy(self.sources('Base'))
        self.maps = {}
        role = ('L1', 'R1') if variant == 'default' else ('L2', 'R2')
        for bank, name in [(0, role[0]+': Modifier 0'), (1, role[1]+': Modifier 1'),
                           (2, role[0]+'!'+role[1]+': Modifier 2')]:
            self.maps[bank] = self.sources(name)
        self.stroke = [title(o,c,d,'Stroke') for o in OWNERS for c in CONTEXTS for d in DIRECTIONS]
        self.windows = [title(o,c,d,'Double Window') for o in OWNERS for c in CONTEXTS for d in DIRECTIONS]
        self.repeats = [title(c,d,'Repeat') for c in CONTEXTS for d in DIRECTIONS]
        self.banks = [title('Mod '+str(i)) for i in range(3)]
        self.routers = []  # Owner stick chords route Mod2 without separate layers.
        self.consumed = [title(c,'Consumed') for c in CONTEXTS]
        self.gestures = self.stroke+self.windows+self.repeats+self.consumed
        self.branch = self.gestures+self.banks+self.routers+[title(o) for o in OWNERS]+[title('Rearm'),title('Entry Guard')]
        self.family = self.branch+[title()]

    def sources(self, name):
        p = self.presets[self.by_title[name]]
        return {binding[:-7]: self.groups[gid] for gid,binding in p.get('group_source_bindings',{}).items()
                if binding.endswith(' active')}

    def layer(self, name):
        assert name not in self.by_title, name
        preset = f'Preset_{self.pid}'; self.pid += 1
        self.cm['action_layers'][preset] = {'title': name, 'legacy_set': '1', 'set_layer': '1',
                                          'parent_set_name': 'Preset_1000001'}
        p = {'id': str(len(self.cm['preset'])), 'name': preset, 'group_source_bindings': {}}
        self.cm['preset'].append(p); self.presets[preset] = p
        self.by_title[name] = preset; self.new.append(name)

    def group(self, name, source, inputs, settings=None, mode=None):
        p = self.presets[self.by_title[name]]
        # Replace this layer's source, not another layer sharing the group.
        for gid,binding in list(p['group_source_bindings'].items()):
            if binding == source+' active':
                del p['group_source_bindings'][gid]
        prior = self.base_groups.get(source, {})
        mode = mode or prior.get('mode', {'switch':'switches','button_diamond':'four_buttons'}.get(source,'dpad'))
        gid = str(self.gid); self.gid += 1
        s = copy.deepcopy(settings if settings is not None else {})
        if name != 'Base': s['layer'] = '1'
        g = {'id':gid,'mode':mode,'name':'','description':'','inputs':copy.deepcopy(inputs),'settings':s}
        self.cm['group'].append(g); self.groups[gid] = g
        p['group_source_bindings'][gid] = source+' active'
        return g

    def patch(self, name, source):
        old = self.sources(name)[source]
        g = self.group(name, source, old.get('inputs',{}), old.get('settings',{}), old['mode'])
        self.changed.append((name,source))
        return g

    def clear(self, names):
        return [op('remove', n) for n in dict.fromkeys(names)]

    def exit_branch(self, first=None):
        return self.clear(([first] if first else [])+self.branch)+[op('add',title('Rearm'))]

    def exit_all(self, first=None, beep=False):
        cmds = self.clear(([first] if first else [])+self.branch)
        return cmds+[op('remove', title(), int(beep))]

    def context_enter(self, owner, first=None):
        return self.clear(([first] if first else [])+self.gestures+self.banks+self.routers)+[
            op('add', title('Mod 2')),op('add',title('Mod2','Consumed'))]

    def context_leave(self, first=None):
        return self.clear(([first] if first else [])+self.gestures+self.banks+self.routers)+[op('add',title('Normal','Consumed'))]

    def menu_switches(self, first=None):
        return {button: full(seq(*self.exit_all(first),op('add',f'Menu {side}: Entry Point')))
                for side,button in [('Left','button_menu'),('Right','button_escape')]}

    def drives(self, name, bindings, switches=None):
        switches = copy.deepcopy(switches or {})
        for letter, side in [('W','right'),('S','left')]:
            b = bindings.get(letter,full())
            if self.variant == 'default': switches[side+'_bumper'] = b
            else: self.group(name,side+'_trigger',{'edge':b},
                             {'deadzone_inner_radius':'0','adaptive_threshold':'0'},'trigger')
        self.group(name,'switch',switches)

    def owner_bindings(self, owner, window=None):
        opposite = 'S' if owner=='W' else 'W'
        return {
            owner: inp(Full_Press=entry(key(owner),interruptable=0),
                       release=entry(seq(*self.exit_branch(window)))),
            opposite: inp(Full_Press=entry(seq(*self.context_enter(owner,window))),
                          release=entry(seq(*self.context_leave(window))))}

    def ls_settings(self, center=True):
        s = copy.deepcopy(self.base_groups['joystick']['settings'])
        s.update(edge_binding_radius=CENTER_RADIUS,edge_binding_invert='1' if center else '0')
        return s

    def ls_base(self, vertical=False):
        source = self.base_groups['joystick']['inputs']
        inputs = {n: output_only(source[n]) for n in ('dpad_east','dpad_west')}
        inputs.update({n: output_only(source[n]) if vertical else full() for n in DIRECTIONS.values()})
        # Block Base touch layer mutations and click aliases through transitions.
        inputs.update(edge=full())
        return inputs

    def selectors(self, owner, context):
        inputs = self.ls_base()
        for direction,input_name in DIRECTIONS.items():
            actions = []
            if context == 'Normal': actions.append(op('add',title('Mod '+('1' if direction=='Up' else '0'))))
            actions.append(op('add',title(owner,context,direction,'Stroke')))
            inputs[input_name] = full(seq(*actions),delay_start=5,interruptable=0)
        return inputs

    def opposite_mask(self, owner):
        return (8 if owner=='W' else 4) if self.variant=='default' else (33554434 if owner=='W' else 16777217)

    def owner_selectors(self, owner):
        inputs=self.selectors(owner,'Normal')
        mod2=self.selectors(owner,'Mod2')
        for input_name in DIRECTIONS.values():
            regular=inputs[input_name]['activators']['Full_Press']
            regular['settings']['interruptable']='1'
            chord=mod2[input_name]['activators']['Full_Press']
            chord['settings'].update(gyro_ratchet_button_mask=str(self.opposite_mask(owner)),
                                      gyro_ratchet_button_requireany_or_all='0')
            inputs[input_name]['activators']['chord']=chord
        return inputs

    def owner_recovery(self, owner):
        owner_mask = (4 if owner=='W' else 8) if self.variant=='default' else (16777217 if owner=='W' else 33554434)
        return inp(Full_Press=entry(seq(*self.exit_branch()),hold_repeats=1),
                   chord=entry(EMPTY,gyro_ratchet_button_mask=owner_mask,
                               gyro_ratchet_button_requireany_or_all=0,interruptable=0))

    def map_groups(self, name, bank=None, consume=False):
        sources = self.base_groups if bank is None else self.maps[bank]
        for source in ('button_diamond','dpad','switch','joystick','right_joystick'):
            g = sources.get(source)
            if not g: continue
            inputs = {}
            for n,b in g['inputs'].items():
                if source in ('joystick','right_joystick') and n != 'click': continue
                if source == 'switch' and not (n.startswith('button_back_') or n in ('button_menu','button_escape')): continue
                out = output_only(b)
                if bank is not None:
                    output=out['activators']['Full_Press']
                    output.setdefault('settings',{}).update(gyro_ratchet_button_mask=self.mask,
                        gyro_ratchet_button_requireany_or_all='0')
                    chords=[output]
                    if consume and commands(output)!=[EMPTY]:
                        chords.append(entry(op('add',title('Normal','Consumed')),
                            gyro_ratchet_button_mask=self.mask,
                            gyro_ratchet_button_requireany_or_all=0,interruptable=0))
                    out=inp(chord=chords if len(chords)>1 else chords[0],
                            Full_Press=entry(seq(*self.exit_branch()),hold_repeats=1))
                inputs[n] = out
            if inputs: self.group(name,source,inputs,{},g['mode'])

    def build_core(self):
        for n in self.family: self.layer(n)
        # Fallback owns movement and entry; other ordinary Base sources inherit.
        inputs = self.ls_base(vertical=True)
        inputs['touch']=full()
        inputs['dpad_north'] = inp(Full_Press=entry(key('W'),interruptable=0),Long_Press=[
            entry(EMPTY,long_press_time=2500,hold_repeats=1,repeat_rate=250,haptic_intensity=3,interruptable=0),
            entry(seq(*self.exit_all(beep=True)),long_press_time=5000,haptic_intensity=3,interruptable=0)])
        self.group(title(),'joystick',inputs,self.ls_settings())
        acquire = self.acquisition()
        self.drives(title(),acquire,self.menu_switches())
        guard = self.ls_base(vertical=True)
        guard['edge'] = full(op('remove',title('Entry Guard')),hold_repeats=1,repeat_rate=50)
        self.group(title('Entry Guard'),'joystick',guard,self.ls_settings())
        for o in OWNERS:
            owner_inputs=self.owner_selectors(o)
            owner_inputs['touch']=self.owner_recovery(o)
            self.group(title(o),'joystick',owner_inputs,self.ls_settings())
            self.drives(title(o),self.owner_bindings(o),self.menu_switches())
        for i in range(3): self.map_groups(title('Mod '+str(i)),i,consume=i!=2)
        # Rearm leaves fallback W/timers inherited. A fresh press with no
        # opposite held can acquire; already-held inputs have no repeat/delay
        # that could acquire automatically. Both-held presses remain quarantined.
        guard_e = entry(EMPTY,gyro_ratchet_button_mask=self.mask,
                        gyro_ratchet_button_requireany_or_all=0,interruptable=0)
        recovery = entry(op('remove',title('Rearm')),hold_repeats=1,repeat_rate=50)
        self.group(title('Rearm'),'joystick',{'edge':inp(Full_Press=recovery,chord=guard_e)},self.ls_settings())
        self.drives(title('Rearm'),self.acquisition(),self.menu_switches())

    def acquisition(self):
        result={}
        for owner in OWNERS:
            # Verified bit identities: RB bit 2 / LB bit 3; right trigger
            # full+soft bits 0+24, left trigger full+soft bits 1+25.
            opposite_mask = self.opposite_mask(owner)
            result[owner]=inp(
                Full_Press=entry(seq(op('remove',title('Entry Guard')),op('remove',title('Rearm')),
                                    op('add',title(owner)),op('add',title('Normal','Consumed')))),
                chord=entry(seq(op('remove',title('Entry Guard')),op('add',title('Rearm'))),
                            gyro_ratchet_button_mask=opposite_mask,
                            gyro_ratchet_button_requireany_or_all=0,interruptable=0))
        return result

    def build_consumed(self):
        for c in CONTEXTS:
            n=title(c,'Consumed');inputs=self.ls_base()
            for d,input_name in DIRECTIONS.items():
                if c=='Normal':
                    bank=title('Mod '+('1' if d=='Up' else '0'))
                    other=title('Mod '+('0' if d=='Up' else '1'))
                    inputs[input_name]=inp(Full_Press=entry(seq(op('remove',other),op('add',bank)),delay_start=5,interruptable=0),release=entry(op('remove',bank)))
            targets=self.stroke+self.repeats+[n]+(self.banks[:2] if c=='Normal' else [])
            inputs['edge']=full(seq(*self.clear(targets)),hold_repeats=1,repeat_rate=50)
            self.group(n,'joystick',inputs,self.ls_settings())

    def start_window(self,o,c,d):
        return self.clear(self.stroke+self.consumed+(self.banks[:2] if c=='Normal' else []))+[op('add',title(o,c,d,'Double Window'))]

    def build_strokes(self):
        for o in OWNERS:
            for c in CONTEXTS:
                for d,input_name in DIRECTIONS.items():
                    n=title(o,c,d,'Stroke');inputs=self.ls_base()
                    inputs[input_name]=inp(Full_Press=[
                        entry(op('add',title(c,'Consumed')),delay_start=HOLD_MS,interruptable=0),
                        entry(op('remove',title(c,'Consumed')),hold_repeats=1,repeat_rate=350,interruptable=0)],
                        release=entry(op('remove',title('Mod '+('1' if d=='Up' else '0'))) if c=='Normal' else EMPTY))
                    # Direct reversal or lateral departure consumes before center.
                    for other in ('dpad_north','dpad_south','dpad_east','dpad_west'):
                        if other == input_name: continue
                        out=commands(inputs[other]['activators']['Full_Press'])
                        inputs[other]=full(seq(*out,op('add',title(c,'Consumed'))),interruptable=0)
                    inputs['edge']=full(seq(*self.start_window(o,c,d)))
                    self.group(n,'joystick',inputs,self.ls_settings())

    def freeze_sources(self, name, bank=None):
        """Own every active source/input that can expose a lower mutation.

        Pending activators remain a device check; source replacement is static
        isolation, not proof Steam cancels scheduled callbacks.
        """
        universe={}
        for layer_name in list(self.by_title):
            for src,g in self.sources(layer_name).items():
                universe.setdefault(src,set()).update(g.get('inputs',{}))
        for src,names in universe.items():
            if src=='gyro': continue  # Preserve sparse gyro inheritance, no inputs.
            template=self.base_groups.get(src)
            if not template: continue
            payload=self.maps[bank].get(src,template) if bank is not None else template
            inputs={n:output_only(payload.get('inputs',{}).get(n,template.get('inputs',{}).get(n,full()))) for n in names}
            self.group(name,src,inputs,template.get('settings',{}),template['mode'])

    def build_windows(self):
        for o in OWNERS:
            for c in CONTEXTS:
                for d,input_name in DIRECTIONS.items():
                    n=title(o,c,d,'Double Window')
                    self.freeze_sources(n,2 if c=='Mod2' else None)
                    switches=self.sources(n)['switch']['inputs']
                    if c=='Normal': switches.update(self.menu_switches(n))
                    switches['always_on_action']=inp(Full_Press=[
                        entry(op('remove',n),delay_start=DOUBLE_MS,interruptable=0),
                        entry(wheel(d),delay_start=50,interruptable=0)])
                    self.drives(n,self.owner_bindings(o,n),switches)
                    inputs=self.ls_base()
                    inputs['touch']=full()
                    inputs['click']=output_only((self.maps[2] if c=='Mod2' else self.base_groups)['joystick']['inputs'].get('click',full()))
                    # Window requires recognized center from previous stroke.
                    for newdir,newinput in DIRECTIONS.items():
                        if newdir==d:
                            actions=[op('remove',n),op('add',title(c,d,'Repeat'))]
                        else:
                            actions=[op('remove',n)]
                            if c=='Normal': actions.append(op('add',title('Mod '+('1' if newdir=='Up' else '0'))))
                            actions.append(op('add',title(o,c,newdir,'Stroke')))
                        inputs[newinput]=full(seq(*actions))
                    # Sideways input cancels double history, no pending wheel.
                    for lateral in ('dpad_east','dpad_west'):
                        payload=commands(inputs[lateral]['activators']['Full_Press'])
                        inputs[lateral]=full(seq(op('remove',n),*payload,op('add',title(c,'Consumed'))),interruptable=0)
                    self.group(n,'joystick',inputs,self.ls_settings())

    def build_repeats(self):
        for c in CONTEXTS:
            for d,input_name in DIRECTIONS.items():
                n=title(c,d,'Repeat');inputs=self.ls_base()
                inputs[input_name]=inp(Full_Press=entry(wheel(d),hold_repeats=1,repeat_rate=REPEAT_MS,delay_start=5,interruptable=0),
                    release=entry(seq(op('remove',n),op('add',title(c,'Consumed')))))
                inputs['edge']=full(seq(op('remove',n),op('add',title(c,'Consumed'))),hold_repeats=1)
                self.group(n,'joystick',inputs,self.ls_settings())

    def clone(self, existing, new):
        original_bindings=copy.deepcopy(self.presets[self.by_title[existing]]['group_source_bindings'])
        self.layer(new)
        for source,g in self.sources(existing).items():
            self.group(new,source,g.get('inputs',{}),g.get('settings',{}),g['mode'])
        # Mode-shift targets need their preset references as well as their
        # global group IDs. Keep unchanged inactive targets shared.
        for gid,binding in original_bindings.items():
            if not binding.endswith(' active'):
                self.presets[self.by_title[new]]['group_source_bindings'][gid]=binding

    def protected_names(self, side):
        return f'Menu {side}: Protected Entry',f'Menu {side}: Silent Cover',f'Menu {side}: Automatic Fn'

    def transfer(self,side):
        protected,cover,automatic=self.protected_names(side)
        return seq(op('remove',automatic),op('remove',f'Menu {side}: Entry Point'),op('add',protected))

    def build_menu(self):
        # Separate automatic and deliberate Fn provenance; explicit Fn is never
        # removed merely because a stick subsequently deflects.
        for side in ('Left','Right'):
            normal=f'Menu {side}: Entry Point';fn=f'Menu {side}: Fn Layer'
            protected,cover,automatic=self.protected_names(side)
            self.clone(fn,automatic)
            for g in self.sources(automatic).values():
                for binding in g.get('inputs',{}).values():
                    for _,e in entries(binding):
                        e['bindings']['binding']=[cmd.replace('{{Base::'+fn+'}}','{{Base::'+automatic+'}}') for cmd in commands(e)]
            self.clone(normal,protected)
            self.clone(normal,cover)
            owner='button_menu' if side=='Left' else 'button_escape'
            other='button_escape' if side=='Left' else 'button_menu'
            legacy='15' if side=='Left' else '14'
            explicit=self.patch(fn,'switch')['inputs'][owner]
            release=explicit['activators']['release']
            release['bindings']['binding']=seq(op('remove',cover),op('remove',protected),*reversed(commands(release)))
            for source in list(self.sources(normal)):
                g=self.patch(normal,source)
                for b in g.get('inputs',{}).values():
                    for _,e in entries(b):
                        old=op('add',fn)
                        e['bindings']['binding']=[cmd.replace('{{Base::'+fn+'}}','{{Base::'+automatic+'}}') for cmd in commands(e)]
            for target in (normal,automatic):
                for source,radius in [('joystick','4915'),('right_joystick','7209')]:
                    g=self.patch(target,source)
                    g['settings'].update(edge_binding_radius=radius,edge_binding_invert='0')
                    g['inputs']['edge']=inp(chord=entry(self.transfer(side),chord_button=legacy,hold_repeats=1,interruptable=0))
            for target in (protected,cover):
                sw=self.patch(target,'switch')['inputs']
                cleanup=self.clear([cover,protected,automatic,normal])
                release=cleanup+([key('ESCAPE' if side=='Left' else 'TAB')] if target==protected else [])
                sw[owner]=inp(release=entry(seq(*release)),Full_Press=entry(op('add',cover) if target==protected else EMPTY,
                            delay_start=300 if target==protected else 0,interruptable=0))
                # Other-menu activity does not invoke automatic Fn.
                sw[other]=full()
                sw['left_stick_click']=full();sw['right_stick_click']=full()
                for source in ('joystick','right_joystick'):
                    g=self.patch(target,source)
                    g['inputs']['touch']=full();g['inputs']['edge']=full()
                    dest='Transition Set 1' if side=='Right' and source=='joystick' else fn
                    g['inputs']['click']=inp(chord=entry(op('add',dest),chord_button=legacy,interruptable=0))
            # The requested chord selects steering in one click, without an
            # initial click needed merely to enter Fn.
            if side=='Right':
                self.patch(normal,'joystick')['inputs']['click']=inp(chord=entry(op('add','Transition Set 1'),chord_button=14,interruptable=0))
            base=self.patch('Base','switch')
            base['inputs'][owner]=inp(Full_Press=entry(op('add',normal),hold_repeats=1),
                chord=entry(op('add',protected),gyro_ratchet_button_mask=3221225472,
                            gyro_ratchet_button_requireany_or_all=0,interruptable=0))
        # Mutually exclude touch/edge recovery while awaiting release commit.
        # Existing click blocks stay; Left Menu offers an explicit abort.
        transient=[n for n in self.by_title if n!='Base' and n!='Gyro' and not n.startswith('Steering')]
        commit=self.clear(transient)+[op('add',title()),op('add',title('Entry Guard'))]
        sw=self.patch('Transition Set 1','switch')['inputs']
        sw['button_escape']=inp(release=entry(seq(*commit)))
        sw['button_menu']=full(seq(*self.clear(transient)))
        sw['left_stick_click']=full();sw['right_stick_click']=full()
        for source in ('joystick','right_joystick'):
            g=self.patch('Transition Set 1',source)
            for input_name in ('touch','edge','click'):g['inputs'][input_name]=full()
            if source=='joystick':
                for input_name in ('dpad_north','dpad_south','dpad_east','dpad_west'):
                    g['inputs'][input_name]=output_only(self.base_groups['joystick']['inputs'][input_name])
        # Track every menu/commit mutation in the generated manifest.

    def finish(self):
        self.build_core();self.build_consumed();self.build_strokes();self.build_repeats();self.build_menu();self.build_windows()
        self.cm['title'] += ' | steering candidate'
        self.cm['description'] = ('UNVERIFIED steering candidate. Right Menu + LS click, then release Right Menu, enters steering. R1/R2 owns W; L1/L2 owns S. Up selects Mod 1, Down Mod 0, opposite selects Mod 2. Dominant release returns to WASD. Fallback W warns at 2.5s and exits at 5s. Protected menu and independent Mod 2 scrolling are wired. Device acceptance pending; see findings/2026-09-29-steering-implementation/README.md.')
        report=audit_layout(self.data)
        if report['violations']: raise ValueError(report['violations'])
        return self.data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vdf',action='store_true');args=parser.parse_args()
    manifest={}
    for variant in ('default','alternative'):
        b=Builder(variant);data=b.finish()
        readable=json.dumps(data,indent='\t')+'\n'
        numeric,count=titles_to_ids(readable,generate_lookup(data))
        if '{{' in numeric: raise ValueError('unresolved runtime reference')
        stem=HERE/f'{variant}-steering-candidate'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:subprocess.run(['node',str(ROOT/'convert_vdf.mjs'),str(stem.with_suffix('.json'))],check=True)
        binding_rows=[]
        for layer in b.new:
            for source,g in b.sources(layer).items():
                for input_name,binding in g.get('inputs',{}).items():
                    binding_rows.append({'layer':layer,'source':source,'group':g['id'],'input':input_name,
                        'source_settings':g.get('settings',{}),'activators':[{'type':kind,'settings':e.get('settings',{}),
                            'execution_order':list(reversed(commands(e)))} for kind,e in entries(binding)]})
        (HERE/f'{variant}-bindings.json').write_text(json.dumps(binding_rows,indent=2)+'\n')
        manifest[variant]={'source_sha256':hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'candidate_sha256':hashlib.sha256(numeric.encode()).hexdigest(),'new_layers':b.new,
            'new_layer_count':len(b.new),'total_layer_count':len(b.cm['action_layers']),
            'modified_sources':b.changed,'resolved_references':count,'device_status':'UNTESTED',
            'clock_mode':'native-long-press (device verification pending)',
            'timing_ms':{'hold':HOLD_MS,'double':DOUBLE_MS,'repeat':REPEAT_MS,'warning':2500,'exit':5000}}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
