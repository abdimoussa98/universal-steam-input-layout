"""Verify the generated candidate's actual bindings, not its behavioral model."""
import importlib.util
import json
from pathlib import Path
import re
import unittest
from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('steering_candidate',ROOT/'findings/2026-09-29-steering-implementation/build_candidate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def mutations(e):
    return [c for c in reversed(m.commands(e)) if re.match(r'controller_action (add|remove|hold)_layer ',c)]


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builders={v:m.Builder(v) for v in ('default','alternative')}
        for b in cls.builders.values():b.finish()

    def test_complete_exports_have_valid_budgets_and_roundtrip(self):
        for b in self.builders.values():
            with self.subTest(variant=b.variant):
                self.assertEqual(audit_layout(b.data)['violations'],[])
                lookup=generate_lookup(b.data)
                readable=json.dumps(b.data)
                numeric,_=titles_to_ids(readable,lookup)
                restored,_=ids_to_titles(numeric,lookup)
                self.assertEqual(json.loads(restored),b.data)
                self.assertNotIn('{{',numeric)
                self.assertEqual(len(b.cm['actions']),1)
                self.assertEqual(len(b.new),len(set(b.new)))
                keys=list(b.cm['action_layers'])
                self.assertEqual(keys,sorted(keys,key=lambda k:int(k.split('_')[1])))

    def test_every_window_mutation_exits_itself_first(self):
        for b in self.builders.values():
            for name in b.windows:
                for source,g in b.sources(name).items():
                    for input_name,binding in g.get('inputs',{}).items():
                        for _,e in m.entries(binding):
                            actions=mutations(e)
                            if not actions:continue
                            with self.subTest(variant=b.variant,window=name,source=source,input=input_name):
                                self.assertEqual(actions[0],m.op('remove',name))
                                if input_name=='always_on_action':
                                    self.assertEqual(actions,[m.op('remove',name)])

    def test_every_window_entry_adds_last_and_never_two(self):
        windows={m.op('add',n) for n in self.builders['default'].windows}
        for b in self.builders.values():
            for g in b.cm['group']:
                for binding in g.get('inputs',{}).values():
                    for _,e in m.entries(binding):
                        actions=mutations(e)
                        adds=[a for a in actions if a in windows]
                        if adds:
                            self.assertEqual(len(adds),1)
                            self.assertEqual(actions[-1],adds[0])

    def test_window_owns_every_inherited_mutation_input(self):
        for b in self.builders.values():
            lower=['Base','Gyro',m.title()]+[m.title(o) for o in m.OWNERS]+b.banks+b.routers
            required={}
            for name in lower:
                for src,g in b.sources(name).items():
                    for n,binding in g.get('inputs',{}).items():
                        if any(mutations(e) or any(c.startswith('mode_shift ') for c in m.commands(e)) for _,e in m.entries(binding)):
                            required.setdefault(src,set()).add(n)
            for win in b.windows:
                sources=b.sources(win)
                for src,names in required.items():
                    self.assertIn(src,sources,(win,src))
                    self.assertTrue(names <= sources[src]['inputs'].keys(),(win,src,names-sources[src]['inputs'].keys()))

    def test_movement_owners_have_no_bank_or_always_on_output(self):
        for b in self.builders.values():
            for owner,side in [('W','right'),('S','left')]:
                groups=b.sources(m.title(owner))
                source='switch' if b.variant=='default' else side+'_trigger'
                name=side+'_bumper' if b.variant=='default' else 'edge'
                binding=groups[source]['inputs'][name]
                self.assertEqual(binding['activators']['Full_Press']['bindings']['binding'],m.key(owner))
                release=mutations(binding['activators']['release'])
                for bank in b.banks:self.assertIn(m.op('remove',bank),release)
                self.assertIn(m.op('remove',m.title(owner)),release)
                self.assertEqual(release[-1],m.op('add',m.title('Rearm')))
                self.assertNotIn('always_on_action',groups['switch']['inputs'])

    def test_mod2_boundaries_clear_history_and_restore_consumed(self):
        for b in self.builders.values():
            for owner in m.OWNERS:
                enter=b.context_enter(owner)
                for bank in b.banks[:2]:self.assertIn(m.op('remove',bank),enter)
                self.assertEqual(enter[-1],m.op('add',m.title('Mod2','Consumed')))
                leave=b.context_leave()
                self.assertIn(m.op('remove',m.title('Mod 2')),leave)
                self.assertEqual(leave[-1],m.op('add',m.title('Normal','Consumed')))
            for name in b.repeats:
                encoded=json.dumps(b.sources(name))
                self.assertNotIn('mouse_wheel SCROLL_',json.dumps(b.sources(name)['joystick']['inputs'].get('edge')))
                self.assertNotIn('Mod 2}}',encoded)  # Mod2 map remains inherited, never removed by repeat.

    def test_maps_preserve_keys_without_base_lifecycle(self):
        for b in self.builders.values():
            for bank in range(3):
                groups=b.sources(m.title('Mod '+str(bank)))
                for src,g in groups.items():
                    original=b.maps[bank][src]
                    for name,binding in g['inputs'].items():
                        expected=m.commands(m.output_only(original['inputs'][name])['activators']['Full_Press'])
                        actual=[c for _,e in m.entries(binding) for c in m.commands(e) if not re.match(r'controller_action (add|remove)_layer',c)]
                        self.assertEqual(actual,expected,(bank,src,name))
                        if bank==2:self.assertFalse(any(mutations(e) for kind,e in m.entries(binding) if kind=='chord'))
                for n in ('button_menu','button_escape'):
                    self.assertIn(n,groups['switch']['inputs'])

    def test_protected_menu_has_no_automatic_fn_route(self):
        for b in self.builders.values():
            for side in ('Left','Right'):
                protected,cover,automatic=b.protected_names(side)
                for name in (protected,cover):
                    groups=b.sources(name)
                    for src,g in groups.items():
                        for n,binding in g.get('inputs',{}).items():
                            for _,e in m.entries(binding):
                                for action in mutations(e):
                                    if 'Fn Layer' in action and 'add_layer' in action:self.assertEqual(n,'click')
                                    self.assertNotIn(m.op('add',automatic),action)
                    self.assertEqual(groups['joystick']['inputs']['touch'],m.full())
                owner='button_menu' if side=='Left' else 'button_escape'
                self.assertEqual(b.sources(protected)['switch']['inputs'][owner]['activators']['Full_Press']['settings']['delay_start'],'300')
                release=json.dumps(b.sources(cover)['switch']['inputs'][owner]['activators']['release'])
                self.assertNotIn('key_press',release)

    def test_release_commit_has_no_competing_stick_recovery(self):
        for b in self.builders.values():
            sources=b.sources('Transition Set 1')
            for src in ('joystick','right_joystick'):
                for n in ('edge','touch','click'):self.assertEqual(sources[src]['inputs'][n],m.full())
            release=mutations(sources['switch']['inputs']['button_escape']['activators']['release'])
            self.assertEqual(release[-2:],[m.op('add',m.title()),m.op('add',m.title('Entry Guard'))])
            self.assertNotIn('key_press',json.dumps(release))

    def test_exit_feedback_and_warning_have_no_persistent_always_on(self):
        for b in self.builders.values():
            binding=b.sources(m.title())['joystick']['inputs']['dpad_north']['activators']
            self.assertEqual(binding['Full_Press']['bindings']['binding'],m.key('W'))
            holds=binding['Long_Press']
            self.assertEqual(len(holds),2)
            self.assertEqual(holds[0]['settings']['long_press_time'],'2500')
            self.assertEqual(holds[0]['settings']['haptic_intensity'],'3')
            self.assertEqual(holds[0]['bindings']['binding'],m.EMPTY)
            self.assertEqual(holds[1]['settings']['long_press_time'],'5000')
            self.assertEqual(mutations(holds[1])[-1],m.op('remove',m.title(),1))
            ao=[]
            for name in b.new:
                if any('always_on_action' in g.get('inputs',{}) for g in b.sources(name).values()):ao.append(name)
            self.assertEqual(set(ao),set(b.windows))

    def test_rearm_inherits_exit_clock_and_acquisition_has_tie_guard(self):
        for b in self.builders.values():
            sources=b.sources(m.title('Rearm'))
            self.assertNotIn('dpad_north',sources['joystick']['inputs'])
            for owner,side in [('W','right'),('S','left')]:
                source='switch' if b.variant=='default' else side+'_trigger'
                input_name=side+'_bumper' if b.variant=='default' else 'edge'
                binding=sources[source]['inputs'][input_name]['activators']
                self.assertNotIn('delay_start',binding['Full_Press'].get('settings',{}))
                self.assertNotIn('hold_repeats',binding['Full_Press'].get('settings',{}))
                self.assertEqual(binding['chord']['settings']['interruptable'],'0')
                self.assertNotIn(m.op('add',m.title(owner)),m.commands(binding['chord']))

    def test_real_command_traces_for_context_handoff_and_release(self):
        # Executes encoded command arrays, not a substitute for Steam sampling.
        for b in self.builders.values():
            for owner in m.OWNERS:
                stack=[m.title(),m.title(owner),m.title('Mod 1'),m.title(owner,'Normal','Up','Stroke')]
                def run(e):
                    for command in reversed(m.commands(e)):
                        match=re.match(r'controller_action (add|remove)_layer {{Base::(.+?)}}',command)
                        if not match:continue
                        verb,name=match.groups()
                        active=[n for n in stack if n in b.windows]
                        if active:self.assertEqual((verb,name),('remove',active[0]))
                        if name in stack:stack.remove(name)
                        if verb=='add':stack.append(name)
                def first(name,src,input_name,kind='Full_Press'):
                    value=b.sources(name)[src]['inputs'][input_name]['activators'][kind]
                    return value[0] if isinstance(value,list) else value
                def drive(name,letter,kind):
                    side='right' if letter=='W' else 'left'
                    return first(name,'switch' if b.variant=='default' else side+'_trigger',
                                 side+'_bumper' if b.variant=='default' else 'edge',kind)
                run(first(stack[-1],'joystick','edge'))
                win=m.title(owner,'Normal','Up','Double Window')
                self.assertEqual(stack,[m.title(),m.title(owner),win])
                opposite='S' if owner=='W' else 'W'
                run(drive(win,opposite,'Full_Press'))
                self.assertEqual(stack[-2:],[m.title('Mod 2'),m.title('Mod2','Consumed')])
                run(first(m.title('Mod2','Consumed'),'joystick','edge'))
                run(first(m.title(owner),'joystick','dpad_north','chord'))
                run(first(m.title(owner,'Mod2','Up','Stroke'),'joystick','edge'))
                win=m.title(owner,'Mod2','Up','Double Window')
                run(first(win,'joystick','dpad_north'))
                self.assertIn(m.title('Mod 2'),stack)
                self.assertEqual(stack[-1],m.title('Mod2','Up','Repeat'))
                run(drive(m.title(owner),opposite,'release'))
                self.assertEqual(stack,[m.title(),m.title(owner),m.title('Normal','Consumed')])
                run(first(m.title('Normal','Consumed'),'joystick','dpad_south'))
                self.assertEqual(stack[-1],m.title('Mod 0'))
                run(drive(m.title(owner),owner,'release'))
                self.assertEqual(stack,[m.title(),m.title('Rearm')])

    def test_cloned_fn_preserves_inactive_mode_shift_references(self):
        for b in self.builders.values():
            for side in ('Left','Right'):
                original=b.presets[b.by_title[f'Menu {side}: Fn Layer']]['group_source_bindings']
                cloned=b.presets[b.by_title[f'Menu {side}: Automatic Fn']]['group_source_bindings']
                for gid,binding in original.items():
                    if not binding.endswith(' active'):self.assertEqual(cloned.get(gid),binding)
                explicit=b.sources(f'Menu {side}: Fn Layer')['switch']['inputs']['button_menu' if side=='Left' else 'button_escape']
                actions=mutations(explicit['activators']['release'])
                self.assertLess(actions.index(m.op('remove',f'Menu {side}: Protected Entry')),
                                actions.index(m.op('remove',f'Menu {side}: Fn Layer')))
