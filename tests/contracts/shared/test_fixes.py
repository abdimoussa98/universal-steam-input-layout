"""The post-install fix pipeline (steam_layout.fixes).

Fixture responsibility: contracts/shared. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.fixes import *

class PipelineTests(unittest.TestCase):

    def test_working_layouts_are_a_fixed_point(self):
        # Every fix has already been applied: running the pipeline again changes nothing. Every controller's layouts:
        # a conversion ends with the pipeline too (R177).
        for path in controllers.working_layouts():
            data = json.loads(path.read_text())
            before = copy.deepcopy(data)
            with self.subTest(path.name):
                apply_all(data)
                self.assertEqual(data, before)



if __name__ == "__main__":
    unittest.main()
