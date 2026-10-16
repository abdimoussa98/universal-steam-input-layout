"""The controller registry (steam_layout/controllers.py): directories, Steam names and file names.

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.controllers import *

class VersionTests(unittest.TestCase):
    def test_versions_order_by_number(self):
        self.assertGreater(controllers.version_key("90.10"), controllers.version_key("90.9"))
        self.assertGreater(controllers.version_key("1.10"), controllers.version_key("1.2"))
        self.assertEqual(controllers.next_version("90.74"), "90.75")
        self.assertEqual(controllers.next_version("1.9"), "1.10")
        for bad in ("", "90", "v90.74", "90.74-trial", "latest"):
            with self.subTest(bad):
                with self.assertRaises(ValueError):
                    controllers.version_key(bad)

    def test_the_title_ends_in_the_version(self):
        self.assertEqual(controllers.title_version("single-set-default :: always-gyro :: 90.74"), "90.74")



if __name__ == "__main__":
    unittest.main()
