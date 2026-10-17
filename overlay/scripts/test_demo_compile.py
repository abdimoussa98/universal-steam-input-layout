"""Unknown behavior and release identity are build errors, not missing labels."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steam_layout.demo_compile import compile_layout
from tools.compile_demo import catalog, OUTPUT


class DemoCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'versions/ibex/1.2/ibex_single-set-default_hold-gyro_1.2.json').read_bytes())

    def compile(self, data):
        return compile_layout(json.dumps(data).encode(), controller='ibex', variant='default', version='1.2', tag='ibex-v1.2')

    def test_reproducible_catalog_and_source_digests(self):
        self.assertEqual(catalog(), OUTPUT.read_text())
        layouts = json.loads(OUTPUT.read_text())
        self.assertEqual(len(layouts), 6)
        self.assertEqual(len({(l['controller'], l['variant']) for l in layouts}), 6)
        self.assertTrue(all(len(l['sha256']) == 64 for l in layouts))

    def test_unknown_command_and_settings_fail_closed(self):
        data = json.loads(json.dumps(self.data))
        group = next(g for g in data['controller_mappings']['group'] if g.get('inputs'))
        entry = next(iter(next(iter(group['inputs'].values()))['activators'].values()))
        entry = entry[0] if isinstance(entry, list) else entry
        entry['bindings']['binding'] = 'do_something_new SOME_KEY'
        with self.assertRaisesRegex(ValueError, 'Unknown demo command'):
            self.compile(data)
        data = json.loads(json.dumps(self.data))
        data['controller_mappings']['group'][0].setdefault('settings', {})['unreviewed_response'] = '1'
        with self.assertRaisesRegex(ValueError, 'Unreviewed group_setting'):
            self.compile(data)

    def test_disabled_sources_explicit_blocks_and_dormant_modes_are_preserved(self):
        result = self.compile(self.data)
        self.assertEqual(len(result['groups']), len(self.data['controller_mappings']['group']))
        self.assertTrue(any(g['mode'] == 'disabled' for g in result['groups']))
        self.assertTrue(any(c['op'] == 'empty' for g in result['groups'] for entries in g['inputs'].values() for e in entries for c in e['commands']))
        self.assertTrue(any(item['status'] == 'approximation' for item in result['coverage']))


if __name__ == '__main__':
    unittest.main()
