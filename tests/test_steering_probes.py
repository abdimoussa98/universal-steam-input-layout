"""Static safety invariants for isolated probes; no claim about native scheduling."""
import importlib.util
import json
from pathlib import Path
import unittest
from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup, titles_to_ids

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('steering_probes', ROOT/'findings/2026-09-29-steering-native-probes/build_probes.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def group(cm, title, source):
    names = {v['title']: k for section in ('actions', 'action_layers') for k,v in cm[section].items()}
    preset = next(p for p in cm['preset'] if p['name'] == names[title])
    gid = next(gid for gid,state in preset['group_source_bindings'].items() if state == source+' active')
    return next(g for g in cm['group'] if g['id'] == gid)


class ProbeTests(unittest.TestCase):
    def test_all_exports_resolve_and_fit_budget(self):
        for variant in ('default','alternative'):
            for kind in ('owner','entry','clock'):
                with self.subTest(variant=variant,kind=kind):
                    data=probe.build(variant,kind,clock=kind=='clock')
                    self.assertEqual(audit_layout(data)['violations'],[])
                    numeric,_=titles_to_ids(json.dumps(data),generate_lookup(data))
                    self.assertNotIn('{{',numeric)
                    cm=data['controller_mappings']
                    self.assertEqual(len(cm['actions']),1)
                    self.assertNotIn('always_on_action',numeric)
                    self.assertEqual(len({g['id'] for g in cm['group']}),len(cm['group']))
                    self.assertEqual([p['id'] for p in cm['preset']],list(map(str,range(len(cm['preset'])))))

    def test_owner_suppresses_vertical_and_opposing_movement(self):
        for variant in ('default','alternative'):
            cm=probe.build(variant)['controller_mappings']
            for title,side,key in [('W Owner','left','S'),('S Owner','right','W')]:
                stick=group(cm,title,'joystick')
                for direction in ('dpad_north','dpad_south'):
                    self.assertEqual(stick['inputs'][direction],probe.full(probe.EMPTY))
                self.assertIn('key_press A',json.dumps(stick['inputs']['dpad_west']))
                control=group(cm,title,'switch' if variant=='default' else side+'_trigger')
                binding=control['inputs'][side+'_bumper' if variant=='default' else 'edge']
                self.assertEqual(binding,probe.full(probe.EMPTY))

    def test_entry_and_release_command_order(self):
        cm=probe.build()['controller_mappings']
        enter=group(cm,'Base','switch')['inputs']['button_escape']['activators']['Full_Press']['bindings']['binding']
        self.assertEqual(enter[::-1],[probe.action('add','Steering'),probe.action('add','Entry Guard')])
        for title,button in [('W Owner','right_bumper'),('S Owner','left_bumper')]:
            release=group(cm,title,'switch')['inputs'][button]['activators']['release']['bindings']['binding']
            self.assertEqual(release[::-1],[probe.action('remove',title),probe.action('add','Rearm')])

    def test_rearm_keeps_movement_but_guards_recovery(self):
        cm=probe.build()['controller_mappings']
        stick=group(cm,'Rearm','joystick')
        for name in ('dpad_north','dpad_south','dpad_east','dpad_west'):
            activators=stick['inputs'][name]['activators']
            self.assertEqual(len(activators['Full_Press']),2)
            self.assertEqual(activators['Full_Press'][0]['settings']['interruptable'],'0')
            self.assertNotIn('interruptable',activators['Full_Press'][1]['settings'])
            self.assertEqual(activators['chord']['settings']['gyro_ratchet_button_mask'],'12')

    def test_no_inherited_production_hooks_in_stick(self):
        cm=probe.build()['controller_mappings']
        for title in ('Base',)+probe.LAYERS:
            stick=group(cm,title,'joystick')
            self.assertNotIn('touch',stick['inputs'])
            self.assertNotIn('click',stick['inputs'])
            self.assertNotIn('WASD Modifier',json.dumps(stick))

    def test_clock_markers_and_disturbance(self):
        cm=probe.build(clock=True)['controller_mappings']
        entries=group(cm,'Steering','joystick')['inputs']['dpad_north']['activators']['Full_Press']
        self.assertEqual(entries[1]['settings']['delay_start'],'2500')
        self.assertEqual(entries[2]['settings']['delay_start'],'5000')
        self.assertEqual(entries[2]['bindings']['binding'][::-1],[probe.key('F10'),probe.action('remove','Steering')])
        disturbance=group(cm,'Steering','button_diamond')['inputs']['button_b']
        self.assertIn(probe.action('remove','Clock Disturbance'),json.dumps(disturbance))
