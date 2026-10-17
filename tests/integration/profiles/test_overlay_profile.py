"""Independent expectations for the deliberately narrow display exporter."""
import copy
import hashlib
import json
import unittest
from steam_layout.overlay_profile import export_profile, display_binding
from steam_layout.model import Layout, entries
from tests.support.sources import ROOT, load_json

SOURCE = ROOT / 'versions/ibex/1.0/ibex_single-set-default_hold-gyro_1.0.json'

class OverlayProfileTests(unittest.TestCase):
    """Frozen Ibex 1.0 default; shared read-only export, independent mutants and determinism rerun."""
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_bytes()
        cls.source = load_json(SOURCE)
        cls.profile, cls.report = export_profile(cls.raw, controller='ibex', version='1.0')

    def test_dashboard_controls_and_timings_come_from_the_layout(self):
        profile = self.profile
        self.assertEqual(profile['schema_version'], 2)
        dashboard = profile['dashboard']
        base = next(p for p in dashboard['pages'] if p['mode']=='base' and p['context']=='none' and p['phase']=='reference')
        self.assertEqual(len(base['bindings']), 16)
        for control, label in {'up':'1','right':'2','down':'3','left':'4','l3':'Q','r3':'E','l2':'Mouse left','r2':'Mouse right'}.items():
            self.assertEqual(base['bindings'][control], {'kind':'label','text':label})
        recipe = next(r for r in dashboard['recipes'] if r['mode']=='base' and r['control']=='l1')
        self.assertEqual([recipe[k] for k in ['hold_ms','output_ms','window_ms','cover_ms']], [200,50,150,150])
        self.assertEqual(recipe['tap_label'], 'Scroll down')
        self.assertEqual(recipe['repeat_ms'], 50)
        self.assertTrue(recipe['touch_completes'])
        self.assertTrue(recipe['touch_cancels_window'])
        self.assertFalse(any(r['mode']=='steering' and r['control']=='l1' for r in dashboard['recipes']))
        cover = next(p for p in dashboard['pages'] if p['mode']=='base' and p['phase']=='l1:cover')
        self.assertEqual(cover['bindings']['r1'], {'kind':'label','text':'Scroll up'})
        self.assertEqual(cover['bindings']['a'], {'kind':'label','text':'F'})
        def binding(mode, phase, control):
            return next(p for p in dashboard['pages'] if p['mode']==mode and p['phase']==phase and p['context']=='none')['bindings'][control]
        self.assertEqual(binding('steering','reference','l1'), {'kind':'label','text':'S'})
        self.assertEqual(binding('base','l1:pressed','r1'), {'kind':'label','text':'Mod 2 :: Base / Gyro'})
        self.assertEqual(binding('base','select:pressed','l3'), {'kind':'label','text':'Switch mode'})
        self.assertEqual(binding('base','l1:hold','a'), {'kind':'label','text':'G'})
        self.assertEqual(binding('base','l1:consumed','a'), {'kind':'label','text':'G'})
        self.assertEqual(binding('base','r1:hold','r3'), {'kind':'label','text':'Mouse forward'})
        # Changing the source must change the generated timing, not a UI constant.
        data=copy.deepcopy(self.source)
        for g in data['controller_mappings']['group']:
            for value in g.get('inputs',{}).values():
                for kind, item in entries(value.get('activators',{})):
                    if item.get('settings',{}).get('delay_start')=='200': item['settings']['delay_start']='180'
        updated,_=export_profile(json.dumps(data).encode(),controller='ibex',version='1.0')
        self.assertEqual(next(r for r in updated['dashboard']['recipes'] if r['mode']=='base' and r['control']=='l1')['hold_ms'],180)

    def test_mod2_release_transition_and_cover_are_distinct(self):
        d = self.profile['dashboard']
        self.assertEqual(d['combined_release_label'], 'Base / Gyro')
        for mode, phase, expected in [('base','reference','Mod 2 :: Base / Gyro'),
                                      ('base','combined:cover','Mod 2'),
                                      ('steering','reference','Mod 2')]:
            page = next(p for p in d['pages'] if p['mode']==mode and p['phase']==phase and p['context']=='both')
            for control in ('l1','r1'):
                self.assertEqual(page['bindings'][control], {'kind':'label','text':expected})

    def test_trackpad_clicks_swipes_and_double_touch(self):
        for mode in ('base','steering','menu'):
            page = next(p for p in self.profile['dashboard']['pages'] if p['mode']==mode and p['context']=='none' and p['phase']=='reference')
            left,right = page['trackpads']
            self.assertEqual(left['center'], {'kind':'label','text':'CAPSLOCK'})
            self.assertEqual([b['text'] for b in left['outer']], ['UP_ARROW','RIGHT_ARROW','DOWN_ARROW','LEFT_ARROW'])
            self.assertEqual([b['text'] for b in left['swipe']], ['Tab','Enter','Backspace','Escape'])
            self.assertIsNone(left['double_tap'])
            self.assertEqual(right['center'], {'kind':'label','text':'Mouse middle'})
            self.assertEqual([b['text'] for b in right['outer']], ['Scroll up','Mouse forward','Scroll down','Mouse back'])
            self.assertEqual(right['repeat_ms'], [150,None,150,None])
            self.assertEqual(right['regions'], dict(inner_threshold=24996,outer_threshold=23000,outer_delay_ms=5))
            self.assertEqual(right['double_tap'], dict(hold_ms=150,window_ms=150,
                clockwise={'kind':'label','text':'Scroll down'},counterclockwise={'kind':'label','text':'Scroll up'}))
        for page in self.profile['dashboard']['pages']:
            if page['mode']=='steering' and page['phase'] in ('ls:up:pressed','ls:down:pressed','ls:up:second','ls:down:second'):
                self.assertIsNotNone(page['trackpads'][1]['regions'])
            if page['phase'] in ('select:pressed','select:hold','start:hold','l1:window','r1:window'):
                for pad in page['trackpads']:
                    self.assertIsNone(pad['regions'], page['phase'])
                    self.assertEqual(pad['center'], {'kind':'unbound'}, page['phase'])
                    self.assertIsNone(pad['double_tap'], page['phase'])

    def test_pad_export_tracks_source_outputs_and_overlap_thresholds(self):
        data=copy.deepcopy(self.source)
        layout=Layout(data)
        group=layout.active('LTP: Middle Click')['left_trackpad']
        group['inputs']['click']['activators']['Soft_Press'][0]['bindings']['binding']='key_press F8, , '
        edge=layout.active('LTP: Click Entry Point')['left_trackpad']['inputs']['edge']['activators']['Soft_Press']
        edge[0]['settings']['activation_threshold']='26000'
        changed,_=export_profile(json.dumps(data).encode(),controller='ibex',version='1.0')
        pad=changed['dashboard']['pages'][0]['trackpads'][0]
        self.assertEqual(pad['center'], {'kind':'label','text':'F8'})
        self.assertEqual(pad['regions']['inner_threshold'],26000)
        edge[1]['settings']['delay_start']='0'
        with self.assertRaisesRegex(ValueError,'center must win'):
            export_profile(json.dumps(data).encode(),controller='ibex',version='1.0')

    def test_steering_position_pages_follow_source_inheritance(self):
        profile = self.profile
        d = profile['dashboard']
        self.assertEqual(d['steering']['deadzone'], 405)
        self.assertEqual(d['steering']['hold_ms'], 200)
        for context in ('left', 'right'):
            for direction, l3, r3 in [('up','Mouse back','Mouse forward'), ('down','CAPSLOCK','Mouse middle')]:
                page = next(p for p in d['pages'] if p['mode']=='steering' and p['context']==context and p['phase']==f'ls:{direction}:pressed')
                self.assertEqual(page['bindings']['l3'], {'kind':'label','text':l3})
                self.assertEqual(page['bindings']['r3'], {'kind':'label','text':r3})
                cover = next(p for p in d['pages'] if p['mode']=='steering' and p['context']==context and p['phase']==f'ls:{direction}:hold')
                self.assertEqual(cover['bindings']['l3'], {'kind':'label','text':l3})

    def test_menu_entry_uses_timed_gesture_reference_without_ambiguous_tap_hold(self):
        profile = self.profile
        page = next(p for p in profile['dashboard']['pages']
                    if p['mode']=='base' and p['phase']=='select:pressed')
        self.assertEqual(page['bindings']['select'], {'kind':'label','text':'Timed gesture'})

    def test_fn_triggers_show_full_pull_in_each_mode_and_menu_hold(self):
        for mode in ('base', 'steering', 'menu'):
            for owner in ('select', 'start'):
                page = next(p for p in self.profile['dashboard']['pages']
                            if p['mode']==mode and p['phase']==owner+':hold')
                self.assertEqual(page['bindings']['l2'], {'kind':'label','text':'Full: F12'})
                self.assertEqual(page['bindings']['r2'], {'kind':'label','text':'Full: F11'})

    def test_bumper_labels_keep_the_modifier_distinct_from_delayed_gyro(self):
        pages = self.profile['dashboard']['pages']
        for control, modifier, scroll in [('l1', 'Mod 0', 'Scroll down'), ('r1', 'Mod 1', 'Scroll up')]:
            recipe = next(r for r in self.profile['dashboard']['recipes'] if r['mode']=='base' and r['control']==control)
            self.assertEqual(recipe['modifier_label'], modifier)
            self.assertEqual(recipe['hold_label'], 'Cursor gyro')
            for phase, expected in [('reference', modifier+' :: '+scroll), ('pressed', modifier),
                                    ('hold', modifier), ('consumed', modifier), ('second', scroll), ('cover', scroll)]:
                page = next(p for p in pages if p['mode']=='base' and p['context']=='none'
                            and p['phase']==('reference' if phase=='reference' else control+':'+phase))
                self.assertEqual(page['bindings'][control], {'kind':'label','text':expected})

    def test_trigger_stages_follow_source_and_report_unsupported_full_pull(self):
        data = copy.deepcopy(self.source)
        trigger = Layout(data).active('Menu Left: Fn Layer')['left_trigger']['inputs']
        trigger['click']['activators'] = {'Full_Press': {'bindings': {'binding':'key_press F10'}}}
        trigger['edge']['activators'] = {'Full_Press': {'bindings': {'binding':'key_press F9'}}}
        def export():
            profile, report = export_profile(json.dumps(data).encode(), controller='ibex', version='1.0')
            page = next(p for p in profile['dashboard']['pages']
                        if p['mode']=='base' and p['phase']=='select:hold')
            return page['bindings']['l2'], report
        self.assertEqual(export()[0], {'kind':'label','text':'Soft: F9 / Full: F10'})
        trigger['click']['activators']['Full_Press']['bindings']['binding'] = 'unknown_command test'
        binding, report = export()
        self.assertEqual(binding['kind'], 'unavailable')
        self.assertTrue(any(i.get('stage')=='full' and i['control']=='l2' for i in report['issues']))
        trigger['click']['activators']['Full_Press']['bindings']['binding'] = 'controller_action empty_binding'
        self.assertEqual(export()[0], {'kind':'label','text':'F9'})

    def test_real_layout_labels_and_identity(self):
        raw = self.raw
        profile, report = self.profile, self.report
        expected = {
            'base': [['F','V','C','R'], ['G','X','Z','T'], ['H','N','B','Y'], ['M','P','O','U']],
            'steering': [['F','V','C','R'], ['F','V','C','R'], ['F','V','C','R'], ['M','P','O','U']],
            'menu': [['Enter','Escape','Backspace','Tab']]*4,
        }
        for row in profile['contexts']:
            i = ['none','left','right','both'].index(row['context'])
            self.assertEqual([b.get('text') for b in row['bindings']], expected[row['mode']][i])
        self.assertEqual(profile['source_digest'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(export_profile(raw, controller='ibex', version='1.0'), (profile,report))
        self.assertTrue(report['assumptions'])

    def test_unsupported_outputs_are_reported_not_silently_dropped(self):
        for activators in [
            {'Long_Press': {'bindings': {'binding':'key_press K'}}},
            {'Full_Press': {'bindings': {'binding':['key_press K','mystery_command foo']}}},
            {'Full_Press': {'bindings': {'binding':'key_press K'}, 'settings': {'delay_start':'0.5'}}},
        ]:
            result, issues = display_binding(activators, set())
            self.assertEqual(result['kind'], 'unavailable')
            self.assertTrue(issues)

    def test_inactive_chord_and_explicit_unbound(self):
        activators={'chord': {'bindings': {'binding':'key_press K'}, 'settings': {'chord_button':'1'}}}
        self.assertEqual(display_binding(activators,set())[0]['kind'],'unbound')
        activators={'Full_Press': {'bindings': {'binding':'controller_action empty_binding'}}}
        self.assertEqual(display_binding(activators,set())[0]['kind'],'unbound')

    def test_input_not_mutated_and_missing_layer_fails(self):
        data=copy.deepcopy(self.source); original=copy.deepcopy(data)
        export_profile(json.dumps(data).encode(),controller='ibex',version='1.0')
        self.assertEqual(data,original)
        data['controller_mappings']['action_layers'].clear()
        with self.assertRaises(ValueError):
            export_profile(json.dumps(data).encode(),controller='ibex',version='1.0')

    def test_inverted_chord_uses_the_layouts_actual_setting(self):
        activators={'chord': {'bindings': {'binding':'key_press K'}, 'settings': {'chord_button':'1', 'edge_binding_invert':'1'}}}
        self.assertEqual(display_binding(activators,set())[0], {'kind':'label','text':'K'})
        self.assertEqual(display_binding(activators,{('switch','left_bumper')})[0]['kind'], 'unbound')

    def test_competing_regular_and_chord_outputs_need_a_policy(self):
        activators={
            'Full_Press': {'bindings': {'binding':'key_press J'}},
            'chord': {'bindings': {'binding':'key_press K'}, 'settings': {'chord_button':'1'}},
        }
        result, issues=display_binding(activators,{('switch','left_bumper')})
        self.assertEqual(result['kind'], 'unavailable')
        self.assertTrue(issues)
