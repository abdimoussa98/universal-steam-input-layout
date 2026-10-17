"""Conservative offline display export for the default Ibex layout family.

This is a fresh-press reference and a reviewed single-owner timing model, not
a Steam runtime simulator. Legacy face rows assume only L1/R1 held, centered
sticks and untouched pads. Dashboard pages add named controls and gesture phases;
unsupported output types and unresolved conditions fail visibly.
"""
import hashlib
import json
from .model import Layout, actions, entries
from .flow_model import chord_condition, resolve
from .overlay_trackpads import export_trackpads

FACES = ('button_a', 'button_b', 'button_x', 'button_y')
CONTEXTS = ('none', 'left', 'right', 'both')
NAMES = {'RETURN': 'Enter', 'ESCAPE': 'Escape', 'BACKSPACE': 'Backspace', 'TAB': 'Tab', 'SPACE': 'Space'}


def display_binding(activators, held):
    outputs, issues = [], []
    output_activators = set()
    for kind, entry in entries(activators or {}):
        settings = entry.get('settings', {})
        condition = chord_condition(settings)
        if condition and not condition.known:
            issues.append('Unknown chord condition')
            continue
        if kind == 'chord' and condition is None:
            issues.append('Chord without a condition')
            continue
        if condition:
            active = condition.satisfied(held)
            if settings.get('edge_binding_invert') == '1':
                active = not active
            if not active:
                continue
        commands = list(reversed(actions(entry)))
        output_commands = [c for c in commands if not c.startswith(('controller_action add_layer ', 'controller_action remove_layer ', 'controller_action empty_binding'))]
        if not output_commands:
            continue  # Layer changes/guards are accounted for in the export report.
        output_activators.add(kind)
        if kind not in ('Full_Press', 'Start_Press', 'chord'):
            issues.append('Unsupported output activator: ' + kind)
        if any(settings.get(k, '0') not in ('0', '') for k in ('delay_start', 'delay_end', 'toggle')):
            issues.append('Timed or toggled output')
        supported_settings = {'chord_button', 'gyro_ratchet_button_mask', 'gyro_ratchet_button_requireany_or_all', 'edge_binding_invert', 'interruptable', 'hold_repeats', 'repeat_rate', 'haptic_intensity', 'delay_start', 'delay_end', 'toggle'}
        if set(settings) - supported_settings:
            issues.append('Unsupported settings: ' + ', '.join(sorted(set(settings) - supported_settings)))
        for command in output_commands:
            head = command.split(',', 1)[0]
            if head.startswith('key_press ') and len(head.split()) == 2:
                key = head.split()[1]
                outputs.append(NAMES.get(key, key))
            elif head.startswith('mouse_button '):
                outputs.append('Mouse ' + head.split()[1].lower())
            elif head.startswith('mouse_wheel '):
                outputs.append(head.split()[1].replace('SCROLL_', 'Scroll ').lower().capitalize())
            else:
                issues.append('Unsupported command: ' + command)
    if len(output_activators) > 1:
        issues.append('Competing output activators need an explicit interruption policy')
    if issues:
        return {'kind': 'unavailable', 'reason': '; '.join(issues)}, issues
    if not outputs:
        return {'kind': 'unbound'}, []
    # Preserve execution order and all simultaneous key outputs.
    return {'kind': 'label', 'text': ' + '.join(dict.fromkeys(outputs))}, []


def _stacks(mode, context):
    base = ['Base'] + ({'base': [], 'gyro': ['Gyro'], 'steering': ['Steering'], 'menu': ['Menu Keys']}[mode])
    if context == 'none' or mode == 'menu':
        return [base]
    if mode == 'steering':
        left, right = 'Steering | L1: S Key', 'Steering | R1: W Key'
        both = ['Steering | L1!R1: Modifier 2', 'Steering | R1!L1: Modifier 2']
    else:
        prefix = 'Gyro | ' if mode == 'gyro' else ''
        left, right = prefix+'L1: Modifier 0', prefix+'R1: Modifier 1'
        both = [prefix+'L1!R1: Modifier 2', prefix+'R1!L1: Modifier 2']
    if context == 'left': return [base+[left]]
    if context == 'right': return [base+[right]]
    return [base+[left,right,both[0]], base+[right,left,both[1]]]


def export_profile(raw, *, controller, version):
    if controller != 'ibex':
        raise ValueError('Only the reviewed Ibex default family is supported; export other controllers after reviewing their stacks')
    try:
        layout = Layout(json.loads(raw))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Malformed layout') from exc
    report = {'assumptions': [
        'Legacy face rows: fresh presses with only L1/R1 held, pads untouched, sticks centered.',
        'Manual Base/Gyro, Steering and Menu Keys selection; does not simulate Steam layer mutations.',
        'Pure empty chord entries are guards; they contribute no key output alongside an active output chord.',
        'Legacy face rows exclude layer operations from output labels; dashboard recipes separately describe reviewed timing windows. Stale Steam stacks are not inferred.',
    ], 'issues': [], 'layer_operations': []}
    rows = []
    for mode in ('base', 'steering', 'menu'):
        for context in CONTEXTS:
            held = set()
            if context in ('left','both'): held.add(('switch','left_bumper'))
            if context in ('right','both'): held.add(('switch','right_bumper'))
            stacks = _stacks(mode, context)
            if mode == 'base': stacks += _stacks('gyro', context)
            candidates = []
            for stack in stacks:
                if any(title not in layout.presets for title in stack):
                    raise ValueError('Missing required layer in stack: ' + repr(stack))
                row = []
                for face in FACES:
                    kind, owner, activators, _ = resolve(layout, stack, 'button_diamond', face)
                    if kind in ('disabled','mode'):
                        binding, issues = {'kind':'unbound'}, []
                    elif kind == 'none':
                        binding, issues = {'kind':'unavailable','reason':'No binding definition'}, ['No binding definition']
                    else:
                        binding, issues = display_binding(activators, held)
                    for issue in issues:
                        report['issues'].append({'mode':mode,'context':context,'face':face,'owner':owner,'issue':issue})
                    for activation, entry in entries(activators or {}):
                        for command in reversed(actions(entry)):
                            if command.startswith(('controller_action add_layer ', 'controller_action remove_layer ')):
                                report['layer_operations'].append({'mode':mode,'context':context,'face':face,'owner':owner,'activation':activation,'command':command})
                    row.append(binding)
                candidates.append(row)
            bindings = []
            for i, face in enumerate(FACES):
                binding = candidates[0][i]
                if any(c[i] != binding for c in candidates[1:]):
                    reason = 'Press-order or Base/Gyro bindings differ'
                    report['issues'].append({'mode':mode,'context':context,'face':face,'issue':reason})
                    binding = {'kind':'unavailable','reason':reason}
                bindings.append(binding)
            rows.append({'mode':mode,'context':context,'bindings':bindings})
    dashboard = export_dashboard(layout, report)
    return dict(schema_version=2, dashboard=dashboard, name=f'Ibex {version} · default', controller=controller,
                variant='default', source_version=version, source_digest=hashlib.sha256(raw).hexdigest(),
                modifiers=['L1','R1'], glyphs=['A','B','X','Y'], contexts=rows), report

# Named physical controls; ordering belongs to the diagram, not the profile.
CONTROLS = dict(zip(('a','b','x','y'), [('button_diamond', n) for n in FACES]))
CONTROLS.update(select=('switch','button_menu'), start=('switch','button_escape'),
                up=('dpad','dpad_north'), right=('dpad','dpad_east'),
                down=('dpad','dpad_south'), left=('dpad','dpad_west'),
                l3=('joystick','click'), r3=('right_joystick','click'),
                l1=('switch','left_bumper'), r1=('switch','right_bumper'),
                l2=('left_trigger','edge'), r2=('right_trigger','edge'))


def export_dashboard(layout, report):
    pages, recipes = [], []
    # Base mode displays both stateful variants. Confirm both release paths
    # before advertising their shared transition, including both press orders.
    for mode, operation in [('base', 'add_layer'), ('gyro', 'remove_layer')]:
        for stack in _stacks(mode, 'both'):
            for control in ('l1', 'r1'):
                acts = resolve(layout, stack, *CONTROLS[control])[2]
                if not any(kind == 'release' and (operation, 'Gyro') in layout.layer_ops(e)
                           for kind, e in entries(acts or {})):
                    raise ValueError('Unrecognized Mod 2 stateful release transition')
    combined_release_label = 'Base / Gyro'
    combined_label = 'Mod 2 :: '+combined_release_label
    def layer_label(acts, held, source, name, stack):
        targets = []
        for _, entry in entries(acts or {}):
            condition = chord_condition(entry.get('settings', {}))
            if condition and (not condition.known or not condition.satisfied(held | {(source,name)})):
                continue
            targets += [t for op,t in layout.layer_ops(entry) if op=='add_layer']
        if any(t.startswith('Transition Set ') for t in targets):
            return 'Switch mode'
        if any('Modifier 2' in t for t in targets):
            return 'Mod 2' if any(t.startswith('Steering |') for t in targets) else combined_label
        for t in targets:
            if t in ('Steering | L1: S Key','Steering | R1: W Key'):
                child = resolve(layout, stack+[t], source, name)[2]
                b,_ = display_binding(child, held | {(source,name)})
                if b['kind']=='label': return b['text']
        for target in targets:
            if target not in ('Menu Left!Right: Entry Point','Menu Right!Left: Entry Point'):
                continue
            window = target.replace(': Entry Point', ': Double Tap')
            second_press = resolve(layout, stack+[window], source, name)[2]
            for _, entry in entries(second_press or {}):
                for op, child in layout.layer_ops(entry):
                    if op != 'add_layer': continue
                    output = resolve(layout, stack+[child], source, name)[2]
                    label, _ = display_binding(output, held | {(source,name)})
                    if label['kind']=='label': return label['text']+' :: Menu'
            raise ValueError('Unrecognized Menu transition output: '+target)
        if any(t.endswith('Fn Layer') for t in targets): return 'Function layer'
        if any(t.endswith(': Entry Point') for t in targets): return 'Timed gesture'
        return None
    def binding(stack, source, name, held, optional=False):
        kind, owner, acts, _ = resolve(layout, stack, source, name)
        if kind in ('disabled', 'mode'):
            b, issues = {'kind':'unbound'}, []
        elif kind == 'none':
            b, issues = ({'kind':'unbound'} if optional else {'kind':'unavailable','reason':'No binding definition'}), []
        else:
            b, issues = display_binding(acts, held)
            # A repeating cancellation removes its own temporary cover on
            # this fresh press, exposing the actual binding underneath.
            # Empty bindings and mode barriers remain explicit blockers.
            for _ in range(len(stack)):
                cancels_self = any(kind=='Full_Press' and e.get('settings',{}).get('hold_repeats')=='1'
                    and e.get('settings',{}).get('interruptable')=='0'
                    and list(layout.layer_ops(e))==[('remove_layer',owner)]
                    for kind,e in entries(acts or {}))
                if b['kind']!='unbound' or not cancels_self: break
                stack=[t for t in stack if t!=owner]
                kind,owner,acts,_=resolve(layout,stack,source,name)
                if kind!='binding': break
                b,issues=display_binding(acts,held)
            if b['kind']=='unbound':
                label = layer_label(acts, held, source, name, stack)
                if label: b={'kind':'label','text':label}
        return b, issues, owner

    def page(mode, context, phase, stacks, held):
        bindings = {}
        for control, (source, name) in CONTROLS.items():
            candidates = []
            for stack in stacks:
                b, issues, owner = binding(stack, source, name, held)
                if control in ('l2', 'r2'):
                    # Steam stores soft pull under edge and full pull under click.
                    # Resolve both through the same stack; an absent click is normal.
                    full, full_issues, full_owner = binding(stack, source, 'click', held, optional=True)
                    for issue in full_issues:
                        report['issues'].append(dict(mode=mode,context=context,phase=phase,
                            control=control,owner=full_owner,stage='full',issue=issue))
                    if full['kind']=='unavailable':
                        b = full
                    elif full['kind']=='label' and b['kind']!='unavailable':
                        text = 'Full: '+full['text']
                        if b['kind']=='label': text = 'Soft: '+b['text']+' / '+text
                        b = {'kind':'label','text':text}
                candidates.append(b)
                for issue in issues:
                    report['issues'].append(dict(mode=mode,context=context,phase=phase,control=control,owner=owner,issue=issue))
            b = candidates[0]
            if any(c != b for c in candidates[1:]):
                b = {'kind':'unavailable','reason':'Bindings differ by press order or Base/Gyro state'}
            if mode in ('base','steering') and context=='both' and control in ('l1','r1'):
                b = {'kind':'label','text':'Mod 2' if mode=='steering' or phase=='combined:cover' else combined_label}
            bindings[control] = b
        pages.append(dict(mode=mode,context=context,phase=phase,bindings=bindings,
                          trackpads=export_trackpads(layout,stacks,held)))
        return pages[-1]
    def activators(title, source, name):
        return resolve(layout, ['Base',title], source, name)[2] or {}
    def delayed_target(title, source, name):
        found=[]
        for _, e in entries(activators(title,source,name)):
            delay=int(e.get('settings',{}).get('delay_start','0'))
            for op,target in layout.layer_ops(e):
                if op=='add_layer' and delay: found.append((delay,target))
        if len(found)!=1: raise ValueError(f'Expected one hold transition in {title}: {found}')
        return found[0]
    for mode in ('base','steering','menu'):
        for context in CONTEXTS:
            held={CONTROLS[c] for c in ('l1','r1') if context=='both' or context=={'l1':'left','r1':'right'}[c]}
            stacks=_stacks(mode,context)
            if mode=='base': stacks+=_stacks('gyro',context)
            page(mode,context,'reference',stacks,held)
        for control,stem,second_name in [('l1','L1','Scroll Down'),('r1','R1','Scroll Up'),('select','Menu Left','Escape'),('start','Menu Right','Tab')]:
            if control in ('l1','r1') and mode!='base': continue
            prefix='Stateful | ' if mode!='base' and control in ('select','start') else ''
            parent=prefix+stem+(': Modifier 0' if control=='l1' else ': Modifier 1' if control=='r1' else ': Entry Point')
            source,name=CONTROLS[control]
            hold_ms,hold_target=delayed_target(parent,source,name)
            window=stem+': Double Tap'; second=stem+': '+second_name
            cover_ms,cover=delayed_target(second,source,name)
            timed=[]
            for _, e in entries(activators(window,'switch','always_on_action')):
                delay=int(e.get('settings',{}).get('delay_start','0'))
                if any(op=='remove_layer' and target==window for op,target in layout.layer_ops(e)):
                    window_ms=delay
                outputs=[c for c in actions(e) if c.startswith(('mouse_wheel ', 'key_press '))]
                if outputs:
                    clean={'Full_Press':{'bindings':{'binding':outputs}}}
                    timed.append((delay,display_binding(clean,set())[0]['text']))
            if len(timed)!=1: raise ValueError(f'Expected one delayed output in {window}')
            repeat=None
            for _, e in entries(activators(cover,source,name)):
                if e.get('settings',{}).get('hold_repeats')=='1' and any(not c.startswith('controller_action ') for c in actions(e)):
                    rate=e.get('settings',{}).get('repeat_rate')
                    repeat=int(rate) if rate is not None else None
            recipe=dict(mode=mode,control=control,hold_ms=hold_ms,output_ms=timed[0][0],window_ms=window_ms,
                        cover_ms=cover_ms,repeat_ms=repeat,tap_label=timed[0][1],
                        hold_label='Cursor gyro' if control in ('l1','r1') else 'Function layer',
                        both_sticks_consume=False,
                        touch_completes=all(any(kind=='release' and op=='add_layer' and t==hold_target
                            for kind,e in entries(activators(parent,stick,'touch')) for op,t in layout.layer_ops(e))
                            for stick in ('joystick','right_joystick')),
                        touch_cancels_window=all(any(kind=='release' and op=='remove_layer' and t==window
                            for kind,e in entries(activators(window,stick,'touch')) for op,t in layout.layer_ops(e))
                            for stick in ('joystick','right_joystick')),cancel_controls=[])
            if control in ('l1', 'r1'):
                # The entry modifier is the primary hold binding. The delayed
                # cursor-gyro overlay is an effect, not a replacement for it.
                recipe['modifier_label'] = parent.rsplit(': ', 1)[1].replace('Modifier ', 'Mod ')
            base_stack=_stacks(mode,'none')[0]
            phase_targets={'pressed':parent,'hold':hold_target,'window':window,'second':second,'cover':cover}
            if control in ('l1','r1'): phase_targets['consumed']=stem+': Tap Cover'
            for phase,target in phase_targets.items():
                # Release removes the entry/modifier before opening the window;
                # the second press replaces that window, and cover overlays it.
                layers = [target] if phase in ('pressed','window','second') else [second,cover] if phase=='cover' else [parent,target]
                stack=base_stack+layers
                pg=page(mode,'none',control+':'+phase,[stack],{(source,name)})
                pg['bindings'][control]={'kind':'label','text':recipe['tap_label'] if phase in ('window','second','cover') else recipe['modifier_label'] if 'modifier_label' in recipe else recipe['hold_label'] if phase=='hold' else 'Timed gesture'}
            if control in ('l1','r1'):
                target=stem+': Tap Cover'
                for c,(src,n) in CONTROLS.items():
                    if c==control:continue
                    acts=resolve(layout,base_stack+[parent],src,n)[2] or {}
                    if any(op=='add_layer' and t==target for _,e in entries(acts) for op,t in layout.layer_ops(e)):
                        recipe['cancel_controls'].append(c)
                both = {(source,name),('joystick','edge'),('right_joystick','edge')}
                recipe['both_sticks_consume'] = all(any(
                    kind=='chord' and chord_condition(e.get('settings',{})) is not None
                    and chord_condition(e['settings']).satisfied(both)
                    and ('add_layer',target) in layout.layer_ops(e)
                    for kind,e in entries(activators(parent,stick,'edge')))
                    for stick in ('joystick','right_joystick'))
            recipes.append(recipe)
    # Reference-only labels for entry commands, whose outputs live in child layers.
    for pg in pages:
        if pg['phase']!='reference':continue
        for r in recipes:
            if r['mode']==pg['mode'] and pg['context']=='none':
                text = r['modifier_label']+' :: '+r['tap_label'] if 'modifier_label' in r else r['tap_label']+' / '+r['hold_label']
                pg['bindings'][r['control']]={'kind':'label','text':text}
            elif r['mode']==pg['mode'] and 'modifier_label' in r and pg['context']=={'l1':'left','r1':'right'}.get(r['control']):
                pg['bindings'][r['control']]={'kind':'label','text':r['modifier_label']}
    # Steering direction modifiers are entered only with one bumper held.
    steering = {}
    for context in ('left', 'right'):
        held = {CONTROLS['l1' if context=='left' else 'r1'], ('joystick','edge')}
        for direction, suffix in [('up','Up: Modifier 1'), ('down','Down: Modifier 0')]:
            parent = 'Steering | LS '+suffix
            stack = _stacks('steering',context)[0]+[parent]
            source_input = 'dpad_north' if direction=='up' else 'dpad_south'
            entry = resolve(layout, _stacks('steering',context)[0], 'joystick', source_input)[2]
            if not any(('add_layer',parent) in list(layout.layer_ops(e)) for _,e in entries(entry)):
                raise ValueError('Missing Steering direction entry')
            edge = activators(parent,'joystick','edge')
            soft = next(e for kind,e in entries(edge) if kind=='Soft_Press')
            config = dict(deadzone=round(int(soft['settings']['activation_threshold'])*1000/32767),
                          hold_ms=int(soft['settings']['delay_start']), window_ms=150, cover_ms=150)
            window='Steering | LS '+('Up' if direction=='up' else 'Down')+': Double Tap'
            second='Steering | LS '+('Up: Scroll Up' if direction=='up' else 'Down: Scroll Down')
            config['window_ms'] = next(int(e['settings']['delay_start']) for _,e in entries(activators(window,'switch','always_on_action'))
                if ('remove_layer',window) in list(layout.layer_ops(e)))
            config['output_ms'] = next(int(e['settings']['delay_start']) for _,e in entries(activators(window,'switch','always_on_action')) if any(c.startswith('mouse_wheel ') for c in actions(e)))
            config['cover_ms'] = next(int(e['settings']['delay_start']) for kind,e in entries(activators(second,'joystick','edge')) if kind=='Soft_Press')
            if steering and steering != config: raise ValueError('Steering direction timings differ')
            steering=config
            for phase, layers in [('pressed',stack), ('hold',stack+['Steering | LS: Tap Cover']),
                                  ('window',_stacks('steering',context)[0]+[window]),
                                  ('second',_stacks('steering',context)[0]+[second]),
                                  ('cover',_stacks('steering',context)[0]+[second,'Steering | LS: Double Tap Cover'])]:
                page('steering',context,f'ls:{direction}:{phase}',[layers],held)
    combined_ms,combined_cover=delayed_target('L1!R1: Modifier 2','switch','right_bumper')
    page('base','both','combined:cover',
         [stack+[combined_cover] for mode in ('base','gyro') for stack in _stacks(mode,'both')],
         {CONTROLS['l1'],CONTROLS['r1']})
    report['assumptions'] += [
        'Dashboard timings are configured expectations, not observed Steam outputs.',
        'Single-owner gesture pages include inherited bindings. Bumper stick deflection follows the exported Tap Cover rule. Pads, menu-stick deflection and combined menu gestures can suspend timing inference without erasing inherited reference bindings.',
        'Trigger values show physical travel; profiles with unspecified activation thresholds do not invent a threshold.',
    ]
    return dict(pages=pages,recipes=recipes,combined_hold_ms=combined_ms,
                combined_release_label=combined_release_label,trigger_thresholds=[None,None],steering=steering)
