"""Releases (tools/release.py): the checks before a tag, the snapshot copy, the bundle and the workflow's helpers.

Most tests run in a scratch Git repository with tiny layouts, so that each check can be shown to fail.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

from steam_layout import controllers
from tools import release

ROOT = Path(__file__).resolve().parents[3]
GIT = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
       "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}


class Repo:
    """A scratch repository with the registry's directories, in which tools/release.py runs."""

    def __init__(self, folder):
        self.root = Path(folder)
        self.clock = 1_800_000_000
        self.git("init", "-q", "-b", "main")

    def git(self, *args):
        self.clock += 60                                    # every commit and tag a minute after the last
        stamp = f"@{self.clock} +0000"
        env = {**os.environ, **GIT, "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
        return subprocess.run(["git", *args], cwd=self.root, env=env, check=True, capture_output=True,
                              text=True).stdout

    def layout(self, name, version, vdf_version=None):
        """Write both working layouts of a controller at `version` (the VDFs at `vdf_version`)."""
        controller = controllers.get(name)
        controller_dir = self.root / name
        controller_dir.mkdir(exist_ok=True)
        for variant in controllers.VARIANTS:
            title = f"single-set-{variant} :: always-gyro :: {version}"
            data = {"controller_mappings": {"title": title, "controller_type": controller.controller_type}}
            controller_dir.joinpath(f"{controller.stem(variant)}_latest.json").write_text(json.dumps(data, indent=2))
            vdf_title = f"single-set-{variant} :: always-gyro :: {vdf_version or version}"
            controller_dir.joinpath(f"{controller.stem(variant)}_latest.vdf").write_text(
                f'"controller_mappings"\n{{\n\t"title"\t\t"{vdf_title}"\n}}\n')

    def snapshot(self, name):
        with mock.patch.object(release, "ROOT", self.root), mock.patch.object(controllers, "ROOT", self.root):
            return release.save_snapshot(name, out=lambda text: None)

    def changelog(self, *sections):
        text = "# Changelog\n\n" + "".join(f"## {s}\n\nFrom ibex 1.0.\n\n" for s in sections)
        (self.root / "CHANGELOG.md").write_text(text)

    def release(self, name, version, *more):
        """Working layouts, snapshot and CHANGELOG at `version`, committed and tagged."""
        self.layout(name, version)
        self.snapshot(name)
        self.changelog(*more, f"{name} {version}")
        self.commit(f"{name} {version}")
        self.git("tag", f"{name}-v{version}")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)


class ScratchCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        self.repo = Repo(folder)
        for patch in (mock.patch.object(release, "ROOT", self.repo.root),
                      mock.patch.object(controllers, "ROOT", self.repo.root)):
            patch.start()
            self.addCleanup(patch.stop)

    def problems(self, name, version=None, tagged=False):
        return release.check(name, version, tagged, export_vdfs=False, warn=lambda text: None)


class CheckTests(ScratchCase):
    def ready(self, version="1.1"):
        """Ibex 1.0 released; `version` in the working files, snapshotted and in the CHANGELOG, not tagged."""
        self.repo.release("ibex", "1.0")
        self.repo.layout("ibex", version)
        self.repo.snapshot("ibex")
        self.repo.changelog("ibex 1.0", f"ibex {version}")
        self.repo.commit(version)

    def test_a_version_ready_for_its_tag_passes(self):
        self.ready()
        self.assertEqual(self.problems("ibex"), [])
        self.assertEqual(self.problems("ibex", "1.1"), [])

    def test_a_stale_title_fails(self):                                                       # check 1
        self.ready()
        self.repo.layout("ibex", "1.1", vdf_version="1.0")
        problems = self.problems("ibex", "1.1")
        self.assertTrue(any("does not end with ' :: 1.1'" in p for p in problems), problems)

    def test_the_working_titles_must_agree(self):
        self.ready()
        self.repo.layout("ibex", "1.2", vdf_version="1.1")
        self.assertIn("the working titles disagree", " ".join(self.problems("ibex")))

    def test_a_missing_or_different_snapshot_fails(self):                                     # check 2
        self.ready()
        self.repo.layout("ibex", "1.2")
        problems = self.problems("ibex", "1.2")
        self.assertTrue(any("1.2/ibex_single-set-default_hold-gyro_1.2.json is missing" in p for p in problems))
        self.repo.snapshot("ibex")
        working = controllers.IBEX.working_json("default")
        working.write_text(working.read_text().replace("always-gyro", "always-gyro "))
        self.assertTrue(any("differs from" in p for p in self.problems("ibex", "1.2")))

    @unittest.skipUnless(release.exporter_version() and shutil.which("node"), "needs the VDF exporter")
    def test_a_vdf_that_is_not_the_export_of_its_json_fails(self):                           # check 3
        self.ready()
        for variant in controllers.VARIANTS:
            source = controllers.IBEX.snapshot(variant, "1.1")
            release.export(source, source.with_suffix(".vdf"))
            shutil.copyfile(source.with_suffix(".vdf"), controllers.IBEX.working_vdf(variant))
        self.assertEqual(release.check("ibex", "1.1", warn=lambda text: None), [])
        for path in (controllers.IBEX.working_vdf("default"), controllers.IBEX.snapshot("default", "1.1", ".vdf")):
            path.write_text(path.read_text() + "\n")
        self.assertEqual(release.check("ibex", "1.1", warn=lambda text: None),
                         ["versions/ibex/1.1/ibex_single-set-default_hold-gyro_1.1.vdf is not the export of its JSON"])

    def test_a_version_must_be_higher_than_the_latest_release_and_untagged(self):              # check 4
        self.ready("1.1")
        self.repo.git("tag", "ibex-v1.1")
        self.assertIn("1.1 is already tagged: ibex-v1.1", self.problems("ibex"))
        self.repo.git("tag", "-d", "ibex-v1.1")
        self.repo.git("tag", "ibex-v1.10")
        self.assertIn("1.1 is not higher than ibex's latest release, 1.10", self.problems("ibex"))

    def test_after_the_tag(self):                                                              # check 4, --tagged
        self.ready("1.1")
        self.assertIn("no tag ibex-v1.1", self.problems("ibex", tagged=True))
        self.repo.git("tag", "ibex-v1.1")
        self.assertEqual(self.problems("ibex", tagged=True), [])
        self.repo.git("tag", "ibex-v1.01")
        self.assertIn("more than one tag has version 1.1: ibex-v1.01, ibex-v1.1",
                      self.problems("ibex", tagged=True))

    def test_a_lower_version_after_a_higher_release_fails_after_the_tag(self):
        self.repo.release("ibex", "1.2")
        self.repo.layout("ibex", "1.1")
        self.repo.snapshot("ibex")
        self.repo.changelog("ibex 1.2", "ibex 1.1")
        self.repo.commit("1.1")
        self.repo.git("tag", "ibex-v1.1")
        self.assertIn("ibex-v1.1 is lower than ibex-v1.2, released before it", self.problems("ibex", tagged=True))

    def test_a_missing_changelog_section_fails(self):                                         # check 5
        self.ready()
        self.repo.changelog("ibex 1.0")
        self.assertIn("CHANGELOG.md has no section '## ibex 1.1'", self.problems("ibex"))
        (self.repo.root / "CHANGELOG.md").unlink()
        self.assertIn("CHANGELOG.md is missing", self.problems("ibex"))

    def test_a_changed_released_snapshot_fails(self):                                         # check 6
        self.ready()
        released = controllers.IBEX.snapshot("default", "1.0")
        released.write_text(released.read_text() + " ")
        problems = self.problems("ibex")
        self.assertIn("ibex-v1.0: the released snapshot changed: versions/ibex/1.0/"
                      "ibex_single-set-default_hold-gyro_1.0.json", problems)
        released.write_text(released.read_text()[:-1])
        extra = released.with_name("extra.json")
        extra.write_text("{}")
        self.assertIn("ibex-v1.0: the released snapshot changed: versions/ibex/1.0/extra.json", self.problems("ibex"))

    def test_a_conversion_names_its_ibex_release(self):                                       # check 7, R177
        self.ready()
        self.repo.layout("dse", "1.0")
        self.repo.snapshot("dse")
        (self.repo.root / "CHANGELOG.md").write_text("# Changelog\n\n## dse 1.0\n\nNo base named.\n")
        self.assertIn("the CHANGELOG section of dse 1.0 names no Ibex release ('From ibex <version>')",
                      self.problems("dse"))

    def test_neptune_up_to_90_74_predates_the_base(self):
        self.repo.layout("neptune", "90.74")
        self.repo.snapshot("neptune")
        (self.repo.root / "CHANGELOG.md").write_text("# Changelog\n\n## neptune 90.74\n\nBuilt directly.\n")
        self.repo.commit("90.74")
        self.assertEqual(self.problems("neptune"), [])


    def test_a_tag_on_a_later_commit_is_not_checked_at_an_older_one(self):                 # check 6, on GitHub
        self.repo.release("ibex", "1.0")
        older = self.repo.git("rev-parse", "HEAD").strip()
        self.repo.release("ibex", "1.1", "ibex 1.0")
        self.repo.git("checkout", "-q", older)
        self.assertEqual(release.changed_snapshots(), [])
        self.assertEqual(self.problems("ibex", "1.0", tagged=True), [])


class SnapshotTests(ScratchCase):
    def test_a_snapshot_is_refreshed_until_its_tag_and_never_after(self):
        self.repo.layout("ibex", "1.0")
        self.assertEqual(self.repo.snapshot("ibex"), "1.0")
        saved = controllers.IBEX.snapshot("alternative", "1.0", ".vdf")
        self.assertEqual(saved.read_bytes(), controllers.IBEX.working_vdf("alternative").read_bytes())
        working = controllers.IBEX.working_json("default")
        working.write_text(working.read_text() + "\n")
        self.repo.snapshot("ibex")                                    # not released: refreshed
        self.assertEqual(controllers.IBEX.snapshot("default", "1.0").read_text(), working.read_text())
        self.repo.changelog("ibex 1.0")
        self.repo.commit("1.0")
        self.repo.git("tag", "ibex-v1.0")
        working.write_text(working.read_text() + "\n")
        with self.assertRaisesRegex(release.Problem, "is released"):
            self.repo.snapshot("ibex")

    def test_a_vdf_with_another_title_is_refused(self):
        self.repo.layout("ibex", "1.1", vdf_version="1.0")
        with self.assertRaisesRegex(release.Problem, "the working titles disagree"):
            self.repo.snapshot("ibex")


class BundleTests(ScratchCase):
    def test_the_bundle_holds_every_controllers_latest_release(self):
        self.repo.release("ibex", "1.0")
        self.repo.release("neptune", "90.74", "ibex 1.0")
        self.repo.release("neptune", "90.75", "ibex 1.0", "neptune 90.74")
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out)
        with mock.patch.object(release, "repository", lambda: "owner/repo"):
            path = release.bundle("ibex", "1.0", out)
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(sorted(archive.namelist()), [
                "RELEASE.md", "ibex/ibex_single-set-alternative_hold-gyro_latest.vdf",
                "ibex/ibex_single-set-default_hold-gyro_latest.vdf",
                "neptune/single-set-alternative_hold-gyro_latest.vdf",
                "neptune/single-set-default_hold-gyro_latest.vdf"])
            self.assertIn(":: 90.75", archive.read("neptune/single-set-default_hold-gyro_latest.vdf").decode())
            notes = archive.read("RELEASE.md").decode()
        self.assertTrue(notes.startswith("## ibex 1.0\n"))
        for row in ("| Steam Controller 2 | `ibex/` | 1.0 |", "| Steam Deck | `neptune/` | 90.75 |",
                    "| DualSense Edge | `dse/` | no release yet |"):
            self.assertIn(row, notes)
        self.assertEqual((out / "RELEASE.md").read_text(), notes)
        again = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, again)
        with mock.patch.object(release, "repository", lambda: "owner/repo"):
            self.assertEqual(release.bundle("ibex", "1.0", again).read_bytes(), path.read_bytes())   # reproducible

    def test_links_in_the_notes_point_at_the_tag(self):
        text = "See [record](findings/x/README.md), [top](#top) and [site](https://example.com)."
        self.assertEqual(release.absolute_links(text, "neptune-v90.74", "owner/repo"),
                         "See [record](https://github.com/owner/repo/blob/neptune-v90.74/findings/x/README.md), "
                         "[top](#top) and [site](https://example.com).")


class WorkflowHelperTests(ScratchCase):
    def test_pending_is_every_unpublished_tag_oldest_first_and_on_main(self):
        self.repo.release("ibex", "1.0")
        self.repo.release("neptune", "90.74", "ibex 1.0")
        self.repo.git("branch", "-f", "fake-main", "HEAD")
        self.assertEqual([t for t, _, _ in release.pending([], "fake-main")], ["ibex-v1.0", "neptune-v90.74"])
        self.assertEqual([t for t, _, _ in release.pending(["ibex-v1.0"], "fake-main")], ["neptune-v90.74"])
        self.repo.git("checkout", "-q", "-b", "side")
        self.repo.release("dse", "1.0", "ibex 1.0")
        with self.assertRaisesRegex(release.Problem, "not on fake-main: dse-v1.0"):
            release.pending(["ibex-v1.0", "neptune-v90.74"], "fake-main")

    def test_other_tags_are_not_releases(self):
        self.repo.release("ibex", "1.0")
        for tag in ("v1.0", "ibex-1.0", "deck-v90.75", "ibex-v1.0-trial"):
            self.repo.git("tag", tag)
        self.assertEqual(release.tags(), [("ibex-v1.0", "ibex", "1.0")])


class RepositoryTests(unittest.TestCase):
    def test_the_shards_split_the_test_modules(self):
        parts = [release.shard(index, 4) for index in range(1, 5)]
        every = [module for part in parts for module in part]
        self.assertEqual(sorted(every), release.test_modules())
        self.assertEqual(len(every), len(set(every)))
        self.assertIn("tests.integration.release.test_release", every)
        self.assertEqual(sum("tests.integration.test_scenario_registry" in part for part in parts), 1)
        seconds = [sum(release.SLOW.get(m, 10) for m in part) for part in parts]
        self.assertLess(max(seconds) - min(seconds), 120)                 # the slowest module goes first
        self.assertTrue(set(release.SLOW) <= set(every), "a slow module was renamed")

    def test_released_snapshots_are_unchanged(self):                                          # R151, check 6
        self.assertEqual(release.changed_snapshots(), [])

    def test_the_changelog_heads_each_release(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        sections = release.SECTION.findall(text)
        self.assertTrue(sections)
        self.assertEqual(len(sections), len(set(sections)))
        for name, version in sections:
            with self.subTest(f"{name} {version}"):
                controllers.get(name)
                controllers.version_key(version)
        for tag, name, version in release.tags():
            with self.subTest(tag):
                self.assertIsNotNone(release.changelog_section(name, version))


if __name__ == "__main__":
    unittest.main()
