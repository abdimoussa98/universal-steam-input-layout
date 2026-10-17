"""Reviewed Ibex pad click regions and touch gestures for the display profile."""
from .model import actions, entries
from .flow_model import chord_condition, resolve

DIRECTIONS = ('dpad_north', 'dpad_east', 'dpad_south', 'dpad_west')
UNBOUND = {'kind': 'unbound'}


def output(acts, held):
    from .overlay_profile import display_binding
    outputs, repeats = [], []
    for kind, entry in entries(acts or {}):
        condition = chord_condition(entry.get('settings', {}))
        if condition:
            if not condition.known:
                raise ValueError('Unknown pad chord')
            active = condition.satisfied(held)
            if entry.get('settings', {}).get('edge_binding_invert') == '1':
                active = not active
            if not active:
                continue
        commands = [c for c in actions(entry) if not c.startswith('controller_action ')]
        if not commands:
            continue
        if kind not in ('Soft_Press', 'Full_Press', 'chord'):
            raise ValueError('Unreviewed pad output activator: '+kind)
        settings = entry.get('settings', {})
        delay = int(settings.get('delay_start', '0'))
        if delay:
            if settings.get('hold_repeats') != '1':
                raise ValueError('Unreviewed delayed pad output')
            repeats.append(delay)
        clean = dict(entry, bindings={'binding': commands}, settings={k:v for k,v in settings.items()
                     if k not in ('activation_threshold', 'delay_start')})
        b, issues = display_binding({'Full_Press': clean}, held)
        if issues:
            raise ValueError('Unsupported pad output: '+str(issues))
        if b['kind'] == 'label':
            outputs.append(b)
    if not outputs:
        return dict(UNBOUND), None
    if any(b != outputs[0] for b in outputs):
        raise ValueError('Competing pad outputs')
    return outputs[0], max(repeats) if repeats else None


def resolved(layout, stack, source, name):
    # A repeating cleanup exposes the source below it. Empty bindings and
    # source-mode barriers remain explicit blockers.
    stack = list(stack)
    for _ in range(len(stack)+1):
        kind, owner, acts, mode = resolve(layout, stack, source, name)
        if kind != 'binding':
            return {}, mode
        cleanup = next((layout.layer_ops(e) for k,e in entries(acts)
                        if k in ('Full_Press','Soft_Press')
                        and e.get('settings',{}).get('hold_repeats')=='1'
                        and ('remove_layer',owner) in layout.layer_ops(e)
                        and all(op=='remove_layer' for op,_ in layout.layer_ops(e))), None)
        if not cleanup:
            return acts, mode
        stack = [s for s in stack if ('remove_layer',s) not in cleanup]
    raise ValueError('Pad cleanup did not resolve')


def pad_profile(layout, stack, source, held):
    stem = 'LTP' if source=='left_trackpad' else 'RTP'
    held = held | {(source,'touch')}
    click_acts, _ = resolved(layout, stack, source, 'click')
    targets = [t for _,e in entries(click_acts) for op,t in layout.layer_ops(e) if op=='add_layer']
    # Steering's first click consumes the directional tap and installs a cover.
    # That cover repeats pad-click entry on the still-held click.
    if len(targets)==1 and targets[0] in ('Steering | LS: Tap Cover','Steering | LS: Double Tap Cover'):
        click_acts = resolve(layout,stack+[targets[0]],source,'click')[2] or {}
        if not any(e.get('settings',{}).get('hold_repeats')=='1' for _,e in entries(click_acts)):
            raise ValueError('Steering cover no longer forwards a held pad click')
    click, _ = output(click_acts, held)
    result = dict(center=click, outer=[dict(UNBOUND) for _ in DIRECTIONS],
                  repeat_ms=[None]*4, regions=None, touch='Unbound', swipe=None, double_tap=None)
    targets = [t for _,e in entries(click_acts) for op,t in layout.layer_ops(e) if op=='add_layer']
    entry = stem+': Click Entry Point'
    if entry in targets:
        edge = resolve(layout, stack+[entry], source, 'edge')[2]
        branches = {}
        for kind,e in entries(edge or {}):
            if kind!='Soft_Press': continue
            adds = [t for op,t in layout.layer_ops(e) if op=='add_layer']
            if len(adds)!=1: raise ValueError('Unknown pad click branch')
            s=e['settings']; side='inner' if s.get('edge_binding_invert')=='1' else 'outer'
            branches[side] = (adds[0],int(s['activation_threshold']),int(s.get('delay_start','0')))
        inner, outer = branches['inner'], branches['outer']
        if not (0 < outer[1] < inner[1] <= 32767 and inner[2] < outer[2]):
            raise ValueError('Pad center must win the overlapping click branches')
        result['regions'] = dict(inner_threshold=inner[1],outer_threshold=outer[1],outer_delay_ms=outer[2])
        result['center'] = output(resolve(layout,stack+[inner[0]],source,'click')[2],held)[0]
        for n,direction in enumerate(DIRECTIONS):
            result['outer'][n], result['repeat_ms'][n] = output(resolve(layout,stack+[outer[0]],source,direction)[2],held)
    touch_acts, mode = resolved(layout,stack,source,'touch')
    if mode=='2dscroll':
        result['touch']='Directional swipe'
        swipes=[]
        for direction in DIRECTIONS:
            acts=resolve(layout,stack,source,direction)[2]
            b,_=output(acts,held)
            if b['kind']=='unbound':
                adds=[t for _,e in entries(acts or {}) for op,t in layout.layer_ops(e) if op=='add_layer']
                if len(adds)==1:
                    b,_=output(resolve(layout,stack+[adds[0]],source,'touch')[2],held)
            swipes.append(b)
        result['swipe']=swipes
    elif mode=='absolute_mouse':
        result['touch']='Pointer'
    touch_targets=[t for _,e in entries(touch_acts) for op,t in layout.layer_ops(e) if op=='add_layer']
    if 'RTP: Entry Point' in touch_targets:
        entry_acts=resolve(layout,stack+['RTP: Entry Point'],source,'touch')[2]
        if not any(kind=='release' and ('add_layer','RTP: Double Tap') in layout.layer_ops(e)
                   for kind,e in entries(entry_acts)):
            raise ValueError('RTP touch release no longer opens a double-tap window')
        cover=next(int(e['settings']['delay_start']) for _,e in entries(entry_acts)
                   if ('add_layer','RTP: Tap Cover') in layout.layer_ops(e))
        window=resolve(layout,stack+['RTP: Double Tap'],'switch','always_on_action')[2]
        window_ms=next(int(e['settings']['delay_start']) for _,e in entries(window)
                       if ('remove_layer','RTP: Double Tap') in layout.layer_ops(e))
        group=layout.active('RTP: Double Tap')[source]
        # Both vertical directions enter circular scroll; center/sides dismiss it.
        for direction in DIRECTIONS:
            ops=[op for _,e in entries(group['inputs'][direction]['activators']) for op in layout.layer_ops(e)]
            if (('add_layer','RTP: Circular Scroll') in ops) != (direction in DIRECTIONS[::2]):
                raise ValueError('Unrecognized double-touch direction')
        scroll=stack+['RTP: Circular Scroll']
        result['double_tap']=dict(hold_ms=cover,window_ms=window_ms,
            clockwise=output(resolve(layout,scroll,source,'scroll_clockwise')[2],held)[0],
            counterclockwise=output(resolve(layout,scroll,source,'scroll_counterclockwise')[2],held)[0])
    return result


def export_trackpads(layout, stacks, held):
    pads=[]
    for source in ('left_trackpad','right_trackpad'):
        candidates=[pad_profile(layout,s,source,held) for s in stacks]
        if any(p!=candidates[0] for p in candidates[1:]):
            raise ValueError('Pad bindings differ by press order or Base/Gyro state')
        pads.append(candidates[0])
    return pads
