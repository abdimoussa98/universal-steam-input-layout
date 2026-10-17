"""Boundary and scope coverage for the CI file-size gate."""
from pathlib import Path
import tempfile
import unittest

from check_rust_size import violations


class RustSizeTests(unittest.TestCase):
    def test_boundary_nested_modules_and_unterminated_last_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src/domain').mkdir(parents=True)
            (root / 'src/allowed.rs').write_text('// line\n' * 400)
            (root / 'src/domain/large.rs').write_text('// line\n' * 400 + '// last')
            self.assertEqual(violations(root), [(Path('src/domain/large.rs'), 401)])

    def test_checks_tests_examples_benches_and_build_but_not_generated_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ('src', 'tests', 'examples', 'benches', 'target', 'dist'):
                (root / folder).mkdir()
                (root / folder / 'large.rs').write_text('// line\n' * 401)
            (root / 'build.rs').write_text('// line\n' * 401)
            self.assertEqual({str(path) for path, _ in violations(root)}, {
                'build.rs', 'src/large.rs', 'tests/large.rs',
                'examples/large.rs', 'benches/large.rs',
            })

    def test_wrong_root_cannot_silently_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'source directory not found'):
                violations(Path(directory))
