import importlib.util
import json
from pathlib import Path
import unittest
from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup,titles_to_ids

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('native_gestures',ROOT/'findings/2026-09-29-steering-native-probes/build_native_gestures.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class NativeGestureProbeTests(unittest.TestCase):
    def test_no_always_on_and_valid_references(self):
        data=m.build()
        self.assertEqual(audit_layout(data)['violations'],[])
        numeric,_=titles_to_ids(json.dumps(data),generate_lookup(data))
        self.assertNotIn('{{',numeric)
        self.assertNotIn('always_on_action',numeric)

    def test_ordinary_long_hold_is_silent_and_only_double_repeats(self):
        cm=m.build()['controller_mappings']
        count=0
        for group in cm['group']:
            for binding in group['inputs'].values():
                activators=binding['activators']
                if 'Double_Press' not in activators:continue
                count+=1
                self.assertEqual(activators['Long_Press']['bindings']['binding'],m.p.EMPTY)
                self.assertNotIn('hold_repeats',activators['Full_Press'].get('settings',{}))
                self.assertEqual(activators['Double_Press']['settings']['hold_repeats'],'1')
        self.assertEqual(count,4)
