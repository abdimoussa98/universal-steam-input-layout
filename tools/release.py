#!/usr/bin/env python3
"""Releases: check a controller's version before it is tagged, save its snapshot, build the bundle.

A release is a version with a Git tag `<controller>-v<version>`, such as `neptune-v90.75`. Pushing
the tag publishes it (.github/workflows/release.yml): the workflow runs `check` again and attaches
the bundle, one zip of every controller's latest release VDFs, to a GitHub Release. A snapshot
without a tag is not a release (trials such as 90.53 and 90.69). Versions compare as numbers:
90.10 is higher than 90.9. Publishing: docs/publishing.md.

    python3 -m tools.release check neptune             # before tagging: the version in the working titles
    python3 -m tools.release check neptune 90.74 --tagged
    python3 -m tools.release snapshot ibex neptune dse  # copy each working layout into versions/<c>/<v>/
    python3 -m tools.release bundle neptune 90.74 out/  # out/universal-steam-input-layout.zip and RELEASE.md
    python3 -m tools.release latest                    # each controller's latest release
    python3 -m tools.release pending --published "ibex-v1.0 ..."   # for the workflow: what to publish
    python3 -m tools.release shard 1 4                 # for the workflow: one part of the test modules

`check` fails unless:
  1. every working JSON and VDF title of the controller ends with ` :: <version>`;
  2. versions/<controller>/<version>/ holds each variant's JSON and VDF, byte for byte the working files;
  3. each of those JSONs exported again (tools/convert_vdf.mjs) gives its VDF byte for byte;
  4. the version is higher than the controller's latest release and has no tag yet; with --tagged, the
     tag exists, no other tag has that version, and no tag of a higher version is on its history;
  5. CHANGELOG.md has a section `## <controller> <version>`;
  6. no released snapshot changed: for every tag, versions/<controller>/<version>/ is as at the tag;
  7. a conversion (R177) is what tools.convert makes from the Ibex release its CHANGELOG section names.

Exit codes: 0 = done or check passed, 1 = check failed, 2 = invalid input.
Plan: plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 2.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from steam_layout import controllers

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = "universal-steam-input-layout.zip"
EXPORTER = "5.12.3"                     # pfwobcke.vscode-vdf, the version the committed VDFs were exported with
TAG = re.compile(r"^(?P<controller>[a-z0-9]+)-v(?P<version>\d+(?:\.\d+)+)$")
SECTION = re.compile(r"^## (?P<controller>[a-z0-9]+) (?P<version>\d+(?:\.\d+)+)\s*$", re.M)
FROM_BASE = re.compile(r"\bFrom (?P<controller>[a-z0-9]+) (?P<version>\d+(?:\.\d+)+)\b")
ZIP_TIME = (2026, 1, 1, 0, 0, 0)        # one timestamp for every file in the zip, so a bundle is reproducible
# Whole-module seconds from the complete 2026-10-15 serial run, rounded up to at least 1.
# Includes fixtures; shared preparation can move between modules or repeat across shards.
# Refresh from fresh shard timings when available. New modules default to 10 seconds.
SLOW = {
    "tests.contracts.dse.test_convert": 1,
    "tests.contracts.ibex.test_steering_rtp_menu_chords": 23,
    "tests.contracts.neptune.test_audit_inheritance": 9,
    "tests.contracts.neptune.test_cleanups": 1,
    "tests.contracts.neptune.test_double_tap_windows": 1,
    "tests.contracts.neptune.test_fixes": 1,
    "tests.contracts.neptune.test_flow_inheritance": 2,
    "tests.contracts.neptune.test_fn_feedback_steering_clear": 1,
    "tests.contracts.neptune.test_layer_order_90_64": 1,
    "tests.contracts.neptune.test_layer_report": 9,
    "tests.contracts.neptune.test_layout_hygiene": 1,
    "tests.contracts.neptune.test_layout_rules": 1,
    "tests.contracts.neptune.test_menu_base_chords": 1,
    "tests.contracts.neptune.test_modifier_rocking": 1,
    "tests.contracts.neptune.test_neptune_cursor": 1,
    "tests.contracts.neptune.test_neptune_gyro": 1,
    "tests.contracts.neptune.test_neptune_held_inputs": 1,
    "tests.contracts.neptune.test_neptune_recovery": 1,
    "tests.contracts.neptune.test_required_cleanups": 1,
    "tests.contracts.neptune.test_shapes_90_49": 1,
    "tests.contracts.neptune.test_shapes_90_52": 1,
    "tests.contracts.neptune.test_shapes_90_55": 1,
    "tests.contracts.neptune.test_shapes_90_57": 1,
    "tests.contracts.neptune.test_shapes_90_58": 31,
    "tests.contracts.neptune.test_shapes_90_62": 1,
    "tests.contracts.neptune.test_shapes_90_68": 1,
    "tests.contracts.neptune.test_shapes_90_70": 1,
    "tests.contracts.neptune.test_shapes_90_74": 1,
    "tests.contracts.neptune.test_static_checks": 18,
    "tests.contracts.neptune.test_steering_entry_feedback": 1,
    "tests.contracts.neptune.test_steering_entry_quiet_drivers": 173,
    "tests.contracts.neptune.test_steering_rtp_menu_chords": 1,
    "tests.contracts.neptune.test_steering_touch_windows": 22,
    "tests.contracts.shared.test_controllers": 1,
    "tests.contracts.shared.test_convert": 1,
    "tests.contracts.shared.test_exceptions": 1,
    "tests.contracts.shared.test_fixes": 47,
    "tests.integration.convert.test_convert": 57,
    "tests.integration.profiles.test_overlay_profile": 1,
    "tests.integration.release.test_release": 4,
    "tests.integration.release.test_test_compat": 1,
    "tests.integration.test_audit_build": 1,
    "tests.integration.test_audit_command_budget": 1,
    "tests.integration.test_audit_inheritance": 4,
    "tests.integration.test_changes": 1,
    "tests.integration.test_cleanups": 1,
    "tests.integration.test_exceptions": 1,
    "tests.integration.test_fixes": 11,
    "tests.integration.test_layer_report": 1,
    "tests.integration.test_migration": 1,
    "tests.integration.test_native": 12,
    "tests.integration.test_required_cleanups": 1,
    "tests.integration.test_rule_registry": 1,
    "tests.integration.test_scenario_registry": 1,
    "tests.integration.test_simulator": 1,
    "tests.integration.test_steering_native_gestures": 1,
    "tests.integration.test_steering_probes": 1,
    "tests.releases.ibex.test_convert": 1,
    "tests.releases.neptune.test_base_pad_click_one_add": 14,
    "tests.releases.neptune.test_changes": 1,
    "tests.releases.neptune.test_cleanup_entry_order": 83,
    "tests.releases.neptune.test_cleanups": 172,
    "tests.releases.neptune.test_convert": 23,
    "tests.releases.neptune.test_cursor_gyro": 20,
    "tests.releases.neptune.test_fallback_window": 70,
    "tests.releases.neptune.test_fallback_window_backport": 117,
    "tests.releases.neptune.test_fallback_window_replacements": 71,
    "tests.releases.neptune.test_fixes": 1,
    "tests.releases.neptune.test_fn_feedback_steering_clear": 1,
    "tests.releases.neptune.test_gamepad": 20,
    "tests.releases.neptune.test_layer_order_90_64": 1,
    "tests.releases.neptune.test_layout_rules": 1,
    "tests.releases.neptune.test_menu_base_chords": 83,
    "tests.releases.neptune.test_menu_chain_and_window_pads": 70,
    "tests.releases.neptune.test_menu_second_press_keys": 14,
    "tests.releases.neptune.test_pad_bump_removal": 68,
    "tests.releases.neptune.test_pad_bumps_and_menu_keys": 35,
    "tests.releases.neptune.test_pad_click_exits": 14,
    "tests.releases.neptune.test_pad_click_handoff": 13,
    "tests.releases.neptune.test_pad_click_holds": 14,
    "tests.releases.neptune.test_pad_click_soft_press_only": 15,
    "tests.releases.neptune.test_pad_middle_click": 14,
    "tests.releases.neptune.test_quiet_resets_and_beeps": 70,
    "tests.releases.neptune.test_required_cleanups": 3,
    "tests.releases.neptune.test_required_cleanups_build": 53,
    "tests.releases.neptune.test_shapes_90_51": 1,
    "tests.releases.neptune.test_shapes_90_53": 1,
    "tests.releases.neptune.test_shapes_90_54": 1,
    "tests.releases.neptune.test_shapes_90_55": 1,
    "tests.releases.neptune.test_shapes_90_56": 1,
    "tests.releases.neptune.test_shapes_90_57": 1,
    "tests.releases.neptune.test_shapes_90_58": 34,
    "tests.releases.neptune.test_shapes_90_61": 1,
    "tests.releases.neptune.test_shapes_90_62": 1,
    "tests.releases.neptune.test_shapes_90_63": 1,
    "tests.releases.neptune.test_shapes_90_65": 1,
    "tests.releases.neptune.test_shapes_90_66": 1,
    "tests.releases.neptune.test_shapes_90_67": 1,
    "tests.releases.neptune.test_shapes_90_68": 1,
    "tests.releases.neptune.test_shapes_90_69": 1,
    "tests.releases.neptune.test_shapes_90_70": 1,
    "tests.releases.neptune.test_shapes_90_71": 1,
    "tests.releases.neptune.test_shapes_90_72": 1,
    "tests.releases.neptune.test_standard_delays": 30,
    "tests.releases.neptune.test_stateful_transitions": 9,
    "tests.releases.neptune.test_steering_candidate": 1,
    "tests.releases.neptune.test_steering_fallback_guard": 75,
    "tests.releases.neptune.test_steering_fallback_hold": 6,
    "tests.releases.neptune.test_steering_fallback_swap": 82,
    "tests.releases.neptune.test_steering_four_way_and_open_edges": 76,
    "tests.releases.neptune.test_steering_lean": 2,
    "tests.releases.neptune.test_steering_rtp_menu_chords": 129,
    "tests.releases.neptune.test_tap_cover_stick_touches": 20,
    "tests.releases.neptune.test_window_releases_and_tap_cover_resets": 71,
    "tests.scenarios.candidates.test_scenarios_90_39": 5,
    "tests.scenarios.dse.test_scenarios_dse_1_0": 1,
    "tests.scenarios.neptune.test_scenarios_90_10": 2,
    "tests.scenarios.neptune.test_scenarios_90_11": 1,
    "tests.scenarios.neptune.test_scenarios_90_12": 2,
    "tests.scenarios.neptune.test_scenarios_90_14": 1,
    "tests.scenarios.neptune.test_scenarios_90_15": 1,
    "tests.scenarios.neptune.test_scenarios_90_16": 1,
    "tests.scenarios.neptune.test_scenarios_90_17": 1,
    "tests.scenarios.neptune.test_scenarios_90_18": 1,
    "tests.scenarios.neptune.test_scenarios_90_19": 1,
    "tests.scenarios.neptune.test_scenarios_90_20": 1,
    "tests.scenarios.neptune.test_scenarios_90_21": 1,
    "tests.scenarios.neptune.test_scenarios_90_22": 1,
    "tests.scenarios.neptune.test_scenarios_90_23": 1,
    "tests.scenarios.neptune.test_scenarios_90_24": 1,
    "tests.scenarios.neptune.test_scenarios_90_25": 2,
    "tests.scenarios.neptune.test_scenarios_90_26": 3,
    "tests.scenarios.neptune.test_scenarios_90_27": 1,
    "tests.scenarios.neptune.test_scenarios_90_28": 1,
    "tests.scenarios.neptune.test_scenarios_90_29": 1,
    "tests.scenarios.neptune.test_scenarios_90_30": 2,
    "tests.scenarios.neptune.test_scenarios_90_33": 106,
    "tests.scenarios.neptune.test_scenarios_90_34": 1,
    "tests.scenarios.neptune.test_scenarios_90_35": 1,
    "tests.scenarios.neptune.test_scenarios_90_37": 1,
    "tests.scenarios.neptune.test_scenarios_90_38": 2,
    "tests.scenarios.neptune.test_scenarios_90_42": 1,
    "tests.scenarios.neptune.test_scenarios_90_43": 34,
    "tests.scenarios.neptune.test_scenarios_90_44": 11,
    "tests.scenarios.neptune.test_scenarios_90_46": 19,
    "tests.scenarios.neptune.test_scenarios_90_47": 7,
    "tests.scenarios.neptune.test_scenarios_90_48": 9,
    "tests.scenarios.neptune.test_scenarios_90_49": 2,
    "tests.scenarios.neptune.test_scenarios_90_51": 1,
    "tests.scenarios.neptune.test_scenarios_90_52": 5,
    "tests.scenarios.neptune.test_scenarios_90_53": 7,
    "tests.scenarios.neptune.test_scenarios_90_54": 2,
    "tests.scenarios.neptune.test_scenarios_90_55": 7,
    "tests.scenarios.neptune.test_scenarios_90_56": 3,
    "tests.scenarios.neptune.test_scenarios_90_57": 25,
    "tests.scenarios.neptune.test_scenarios_90_58": 4,
    "tests.scenarios.neptune.test_scenarios_90_61": 4,
    "tests.scenarios.neptune.test_scenarios_90_62": 2,
    "tests.scenarios.neptune.test_scenarios_90_63": 1,
    "tests.scenarios.neptune.test_scenarios_90_65": 3,
    "tests.scenarios.neptune.test_scenarios_90_66": 2,
    "tests.scenarios.neptune.test_scenarios_90_67": 3,
    "tests.scenarios.neptune.test_scenarios_90_68": 2,
    "tests.scenarios.neptune.test_scenarios_90_69": 1,
    "tests.scenarios.neptune.test_scenarios_90_6_to_90_9": 1,
    "tests.scenarios.neptune.test_scenarios_90_70": 1,
    "tests.scenarios.neptune.test_scenarios_90_71": 1,
    "tests.scenarios.neptune.test_scenarios_90_72": 2,
    "tests.scenarios.neptune.test_scenarios_90_73": 1,
    "tests.scenarios.neptune.test_scenarios_90_74": 1,
    "tests.scenarios.neptune.test_scenarios_cursor": 3,
    "tests.scenarios.neptune.test_scenarios_menu_and_modifiers": 2,
    "tests.scenarios.neptune.test_scenarios_triggers_and_recovery": 1,
    "tests.unit.test_audit_command_budget": 1,
    "tests.unit.test_audit_inheritance": 1,
    "tests.unit.test_chains": 1,
    "tests.unit.test_changes": 1,
    "tests.unit.test_cleanups": 1,
    "tests.unit.test_controllers": 1,
    "tests.unit.test_convert": 1,
    "tests.unit.test_covers": 1,
    "tests.unit.test_discovery": 1,
    "tests.unit.test_exceptions": 1,
    "tests.unit.test_fixes": 1,
    "tests.unit.test_fixture_sources": 1,
    "tests.unit.test_flow_inheritance": 2,
    "tests.unit.test_layer_report": 1,
    "tests.unit.test_required_cleanups": 1,
    "tests.unit.test_rule_registry": 1,
    "tests.unit.test_runner_evidence": 2,
    "tests.unit.test_simulator": 1,
    "tests.unit.test_stacks": 1,
    "tests.unit.test_steering_touch_windows": 1,
}


class Problem(Exception):
    """A release check that failed."""


def git(*args, cwd=None):
    result = subprocess.run(["git", *args], cwd=cwd or ROOT, capture_output=True, text=True)
    if result.returncode:
        raise Problem(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


# --- versions and tags -------------------------------------------------------------------------

def tags(cwd=None):
    """Every release tag, oldest first: [(tag, controller, version)]. Other tags are left out."""
    found = []
    for line in git("for-each-ref", "--sort=creatordate", "--format=%(refname:short)", "refs/tags", cwd=cwd).split():
        match = TAG.match(line)
        if match and match["controller"] in {c.name for c in controllers.CONTROLLERS}:
            found.append((line, match["controller"], match["version"]))
    return found


def is_ancestor(older, newer, cwd=None):
    """True if commit `older` is `newer` or on its history."""
    return subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=cwd or ROOT,
                          capture_output=True).returncode == 0


def latest_release(controller, at="HEAD", cwd=None, every=None):
    """The controller's highest released version on the history of `at`, or None."""
    every = tags(cwd) if every is None else every
    found = [version for tag, name, version in every if name == controller and is_ancestor(tag, at, cwd)]
    return max(found, key=controllers.version_key) if found else None


def working_version(controller):
    """The version both working titles of a controller end with; a problem if they disagree."""
    found = {}
    for path in controller.working():
        found[path.name] = controllers.title_version(read_title(path))
        found[path.with_suffix(".vdf").name] = controllers.title_version(read_title(path.with_suffix(".vdf")))
    if not found:
        raise Problem(f"{controller.name}/ has no working layouts")
    versions = set(found.values())
    if len(versions) != 1:
        raise Problem("the working titles disagree: " + ", ".join(f"{name} {v}" for name, v in sorted(found.items())))
    return versions.pop()


def read_title(path):
    """The `title` of a layout JSON, or of a VDF (its first `"title"` line)."""
    path = Path(path)
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))["controller_mappings"]["title"]
    match = re.search(r'^\t"title"\t+"(.*)"$', path.read_text(encoding="utf-8"), re.M)
    if not match:
        raise Problem(f"{path.name} has no title")
    return match.group(1)


# --- CHANGELOG ---------------------------------------------------------------------------------

def changelog_section(controller, version, text=None):
    """The text of `## <controller> <version>` in CHANGELOG.md, heading included, or None."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if text is None else text
    headings = list(SECTION.finditer(text))
    for index, match in enumerate(headings):
        if match["controller"] == controller and match["version"] == version:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            return text[match.start():end].strip() + "\n"
    return None


def base_release(section):
    """The Ibex release a conversion's CHANGELOG section names (`From ibex 1.0`), or None."""
    match = FROM_BASE.search(section or "")
    return match["version"] if match and match["controller"] == controllers.BASE.name else None


# --- the exporter ------------------------------------------------------------------------------

def exporter_version():
    """The version of the VDF extension tools/convert_vdf.mjs uses (the newest installed), or None."""
    root = Path.home() / ".vscode" / "extensions"
    names = sorted((path for path in root.glob("pfwobcke.vscode-vdf-*") if path.is_dir()),
                   key=lambda path: [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", path.name)])
    if not names:
        return None
    return json.loads((names[-1] / "package.json").read_text(encoding="utf-8")).get("version")


def export(json_path, vdf_path):
    """Export a layout JSON to a VDF with tools/convert_vdf.mjs."""
    result = subprocess.run(["node", str(Path(__file__).resolve().parent / "convert_vdf.mjs"), str(json_path),
                             "-o", str(vdf_path)], capture_output=True, text=True)
    if result.returncode:
        raise Problem(f"exporting {Path(json_path).name}: {(result.stderr or result.stdout).strip()}")


# --- check -------------------------------------------------------------------------------------

def check(name, version=None, tagged=False, export_vdfs=True, warn=print):
    """The problems that keep a controller's version from release; empty when it passes."""
    controller = controllers.get(name)
    problems = []

    def run(step):
        try:
            step()
        except Problem as problem:
            problems.append(str(problem))

    try:
        version = version or working_version(controller)
        controllers.version_key(version)
    except (Problem, ValueError) as problem:
        return [str(problem)]
    snapshot = controller.versions / version
    every = tags()

    def titles():                                                                           # 1
        for path in controller.working():
            for file in (path, path.with_suffix(".vdf")):
                title = read_title(file)
                if not title.endswith(f" :: {version}"):
                    problems.append(f"{file.relative_to(ROOT)}: title {title!r} does not end with ' :: {version}'")

    def snapshots():                                                                        # 2
        for variant in controllers.VARIANTS:
            for suffix in (".json", ".vdf"):
                working, saved = controller.directory / f"{controller.stem(variant)}_latest{suffix}", \
                    controller.snapshot(variant, version, suffix)
                if not saved.exists():
                    problems.append(f"{saved.relative_to(ROOT)} is missing")
                elif not working.exists():
                    problems.append(f"{working.relative_to(ROOT)} is missing")
                elif working.read_bytes() != saved.read_bytes():
                    problems.append(f"{saved.relative_to(ROOT)} differs from {working.relative_to(ROOT)}")

    def exports():                                                                          # 3
        installed = exporter_version()
        if installed is None:
            raise Problem("no VDF exporter: install pfwobcke.vscode-vdf (docs/file-formats.md)")
        if installed != EXPORTER:
            warn(f"warning: the VDF exporter is {installed}, not {EXPORTER}; the VDFs were exported with {EXPORTER}")
        with tempfile.TemporaryDirectory() as folder:
            for variant in controllers.VARIANTS:
                source = controller.snapshot(variant, version)
                if not source.exists():
                    continue                                            # step 2 already says so
                out = Path(folder) / f"{variant}.vdf"
                export(source, out)
                if out.read_bytes() != source.with_suffix(".vdf").read_bytes():
                    problems.append(f"{source.with_suffix('.vdf').relative_to(ROOT)} is not the export of its JSON")

    def order():                                                                            # 4
        own = [(tag, v) for tag, c, v in every if c == name]
        same = [tag for tag, v in own if controllers.version_key(v) == controllers.version_key(version)]
        tag = f"{name}-v{version}"
        if tagged:
            if tag not in same:
                problems.append(f"no tag {tag}")
                return
            if len(same) > 1:
                problems.append(f"more than one tag has version {version}: {', '.join(same)}")
            higher = [t for t, v in own if controllers.version_key(v) > controllers.version_key(version)
                      and is_ancestor(t, tag)]
            if higher:
                problems.append(f"{tag} is lower than {', '.join(higher)}, released before it")
        else:
            if same:
                problems.append(f"{version} is already tagged: {', '.join(same)}")
            latest = max((v for _, v in own), key=controllers.version_key, default=None)
            if latest and controllers.version_key(version) <= controllers.version_key(latest):
                problems.append(f"{version} is not higher than {name}'s latest release, {latest}")

    def changelog():                                                                        # 5
        if not (ROOT / "CHANGELOG.md").exists():
            problems.append("CHANGELOG.md is missing")
        elif changelog_section(name, version) is None:
            problems.append(f"CHANGELOG.md has no section '## {name} {version}'")

    def frozen():                                                                           # 6
        problems.extend(changed_snapshots(every))

    def conversion():                                                                       # 7
        if controller.base or (controller.built_until and
                               controllers.version_key(version) <= controllers.version_key(controller.built_until)):
            return                                                       # built directly, before the base layout
        section = changelog_section(name, version) if (ROOT / "CHANGELOG.md").exists() else None
        base = base_release(section)
        if base is None:
            problems.append(f"the CHANGELOG section of {name} {version} names no Ibex release ('From ibex <version>')")
            return
        from steam_layout import convert                                # only conversions need it
        for variant in controllers.VARIANTS:
            source = controllers.BASE.snapshot(variant, base)
            if not source.exists():
                problems.append(f"{source.relative_to(ROOT)} is missing")
                continue
            made, _ = convert.convert(json.loads(source.read_text(encoding="utf-8")), name, variant, version)
            working = controller.working_json(variant)
            if not working.exists() or json.loads(working.read_text(encoding="utf-8")) != made:
                problems.append(f"{working.relative_to(ROOT)} is not the conversion of ibex {base} (R177)")

    for step in (titles, snapshots, *((exports,) if export_vdfs else ()), order, changelog, frozen, conversion):
        run(step)
    return problems


def blob(path):
    """The Git blob ID of a file on disk."""
    data = Path(path).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def changed_snapshots(every=None, cwd=None):
    """For every release tag on the history of HEAD, what differs between its snapshot folder at the tag and on
    disk. A tag on a later commit is left out: at an older commit its snapshot is not there yet."""
    cwd, problems = Path(cwd or ROOT), []
    for tag, name, version in (tags(cwd) if every is None else every):
        if not is_ancestor(tag, "HEAD", cwd):
            continue
        folder = f"versions/{name}/{version}/"
        then = {}
        for line in git("ls-tree", "-r", tag, "--", folder, cwd=cwd).splitlines():
            meta, path = line.split("\t", 1)
            then[path] = meta.split()[2]
        now = {path.relative_to(cwd).as_posix(): blob(path)
               for path in sorted((cwd / folder).rglob("*")) if path.is_file()}
        if not then:
            problems.append(f"{tag}: {folder} is not in the tagged commit")
        elif then != now:
            changed = sorted(p for p in set(then) | set(now) if then.get(p) != now.get(p))
            problems.append(f"{tag}: the released snapshot changed: {', '.join(changed)}")
    return problems


# --- snapshot ----------------------------------------------------------------------------------

def save_snapshot(name, out=print):
    """Copy each working JSON and VDF of a controller into versions/<controller>/<version>/.

    Refreshes a snapshot that is not released yet; never changes a released one (a fix after the tag
    is a new version). Refuses a VDF whose title is not its JSON's, a sign it was not exported again."""
    controller = controllers.get(name)
    version = working_version(controller)
    released = any(c == name and controllers.version_key(v) == controllers.version_key(version)
                   for _, c, v in tags())
    for variant in controllers.VARIANTS:
        pairs = [(controller.directory / f"{controller.stem(variant)}_latest{suffix}",
                  controller.snapshot(variant, version, suffix)) for suffix in (".json", ".vdf")]
        for source, target in pairs:
            if not source.exists():
                raise Problem(f"{source.relative_to(ROOT)} is missing")
        if read_title(pairs[0][0]) != read_title(pairs[1][0]):
            raise Problem(f"{pairs[1][0].name} and {pairs[0][0].name} have different titles: export it again")
        for source, target in pairs:
            if target.exists() and target.read_bytes() == source.read_bytes():
                out(f"unchanged {target.relative_to(ROOT)}")
                continue
            if target.exists() and released:
                raise Problem(f"{target.relative_to(ROOT)} is released ({name}-v{version}); "
                              "a change after the tag is a new version")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            out(f"saved {target.relative_to(ROOT)}")
    return version


# --- bundle ------------------------------------------------------------------------------------

def bundle(name, version, out, at="HEAD"):
    """Write `out/universal-steam-input-layout.zip` and `out/RELEASE.md` for the release of `name` `version`:
    every controller's latest release VDFs on the history of `at`, with `name` at `version`."""
    controllers.get(name)
    every = tags()
    rows, files = [], []
    for controller in controllers.CONTROLLERS:
        chosen = version if controller.name == name else latest_release(controller.name, at, every=every)
        if chosen is None:
            rows.append(f"| {controller.label} | `{controller.name}/` | no release yet |")
            continue
        for variant in controllers.VARIANTS:
            vdf = controller.snapshot(variant, chosen, ".vdf")
            if not vdf.exists():
                raise Problem(f"{vdf.relative_to(ROOT)} is missing")
            files.append((f"{controller.name}/{controller.stem(variant)}_latest.vdf", vdf))
        rows.append(f"| {controller.label} | `{controller.name}/` | {chosen} |")
    section = absolute_links(changelog_section(name, version) or f"## {name} {version}\n", f"{name}-v{version}")
    notes = (section + "\n## In this bundle\n\nOne folder per controller with its two layouts, the default and "
             "the alternative. Copy a controller's two VDFs into Steam's `controller_base/templates/` folder "
             "(on the Steam Deck, `/home/deck/.steam/steam/controller_base/templates/`).\n\n"
             "| Controller | Folder | Version |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "RELEASE.md").write_text(notes, encoding="utf-8")
    with zipfile.ZipFile(out / BUNDLE, "w", zipfile.ZIP_DEFLATED) as archive:
        for arcname, path in files + [("RELEASE.md", out / "RELEASE.md")]:
            info = zipfile.ZipInfo(arcname, ZIP_TIME)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            archive.writestr(info, Path(path).read_bytes())
    return out / BUNDLE


def repository():
    """`owner/name` of the GitHub repository: the workflow's GITHUB_REPOSITORY, else the origin remote."""
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    try:
        url = git("remote", "get-url", "origin").strip()
    except Problem:
        return None
    match = re.search(r"github\.com[:/](?P<path>[^/]+/[^/]+?)(?:\.git)?$", url)
    return match["path"] if match else None


def absolute_links(text, ref, repo=None):
    """Relative Markdown links made absolute on GitHub at `ref`, so they work in a release's notes."""
    repo = repo or repository()
    if not repo:
        return text
    return re.sub(r"\]\((?!https?:|#|mailto:)([^)\s]+)\)",
                  lambda match: f"](https://github.com/{repo}/blob/{ref}/{match.group(1)})", text)


# --- the workflow's helpers --------------------------------------------------------------------

def pending(published, main="origin/main"):
    """The release tags with no GitHub Release yet, oldest first, each checked to be on `main`."""
    found = [(tag, name, version) for tag, name, version in tags() if tag not in set(published)]
    off = [tag for tag, _, _ in found if not is_ancestor(tag, main)]
    if off:
        raise Problem(f"not on {main}: {', '.join(off)}")
    return found


def test_modules():
    from tests.support.discovery import test_modules as active_modules
    return active_modules(ROOT)


def shard(index, count):
    """Part `index` (1 to `count`) of the Python test modules: the slowest first, each to the part with the least
    time so far (`SLOW`), so the parts take about as long."""
    if not 1 <= index <= count:
        raise ValueError(f"part {index} of {count}")
    loads, parts = [0] * count, [[] for _ in range(count)]
    for module in sorted(test_modules(), key=lambda m: (-SLOW.get(m, 10), m)):
        least = loads.index(min(loads))
        loads[least] += SLOW.get(module, 10)
        parts[least].append(module)
    return sorted(parts[index - 1])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("check", help="check a controller's version before or after tagging")
    one.add_argument("controller")
    one.add_argument("version", nargs="?")
    one.add_argument("--tagged", action="store_true", help="the tag exists (on GitHub, after the push)")
    one.add_argument("--no-export", action="store_true", help="skip exporting the VDFs again (check 3)")
    save = commands.add_parser("snapshot", help="copy working layouts into versions/<controller>/<version>/")
    save.add_argument("controllers", nargs="*", help="default: every controller with working layouts")
    pack = commands.add_parser("bundle", help="write the release zip and its notes")
    pack.add_argument("controller")
    pack.add_argument("version")
    pack.add_argument("out", type=Path)
    commands.add_parser("latest", help="each controller's latest release")
    wait = commands.add_parser("pending", help="the release tags with no GitHub Release yet, as JSON")
    wait.add_argument("--published", default="", help="the tags that have a GitHub Release, separated by spaces")
    wait.add_argument("--main", default="origin/main")
    part = commands.add_parser("shard", help="one part of the Python test modules")
    part.add_argument("index", type=int)
    part.add_argument("count", type=int)
    args = parser.parse_args()
    try:
        if args.command == "check":
            problems = check(args.controller, args.version, args.tagged, not args.no_export,
                             warn=lambda text: print(text, file=sys.stderr))
            version = args.version or working_version(controllers.get(args.controller))
            for problem in problems:
                print(f"  {problem}")
            print(f"Release check {args.controller} {version}:", "passed" if not problems else f"{len(problems)} problem(s)")
            return 1 if problems else 0
        if args.command == "snapshot":
            for name in args.controllers or [c.name for c in controllers.with_layouts()]:
                save_snapshot(name)
        elif args.command == "bundle":
            print(bundle(args.controller, args.version, args.out))
        elif args.command == "latest":
            every = tags()
            for controller in controllers.CONTROLLERS:
                print(controller.name, latest_release(controller.name, every=every) or "no release yet")
        elif args.command == "pending":
            found = pending(args.published.split(), args.main)
            commits = list(dict.fromkeys(git("rev-list", "-n", "1", tag).strip() for tag, _, _ in found))
            print("tags=" + json.dumps([tag for tag, _, _ in found]))
            print("commits=" + json.dumps(commits))
        elif args.command == "shard":
            print(" ".join(shard(args.index, args.count)))
    except (Problem, ValueError) as problem:
        print(f"Release error: {problem}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
