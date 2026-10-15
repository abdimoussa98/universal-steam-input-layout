#!/usr/bin/env python3
"""Convert: make a controller's two layouts from an Ibex release by that controller's rules (R177).

Ibex, the Steam Controller 2, is the base layout. Neptune's (the Steam Deck's) and the DualSense Edge's layouts are
made from an Ibex snapshot by the rules in steam_layout/convert.py (Layer Definition of Done section 12) and never
edited by hand. This writes `<controller>/<stem>_latest.json` for both variants; export the VDFs and save the
snapshot after (docs/publishing.md).

    python3 -m tools.convert neptune                  # from the newest Ibex snapshot
    python3 -m tools.convert dse --ibex 1.0           # from versions/ibex/1.0/
    python3 -m tools.convert dse --version 1.1        # the version to write (default below)
    python3 -m tools.convert neptune --check          # exit 1 if the working layouts are not that conversion

The version: the controller's latest release when the conversion is the same as that release, so a controller that
did not change keeps its version; otherwise the next one after its latest release (a tag). Before its first tag:
the next after the last version built directly (Neptune: 90.75), or the controller's first version (1.0).

Exit codes: 0 = written, or up to date with --check; 1 = --check found a difference; 2 = invalid input.
"""
import argparse
import json
import sys

from steam_layout import controllers, convert
from tools import release


def ibex_versions():
    """The Ibex versions with a snapshot of both variants, oldest first."""
    folder = controllers.BASE.versions
    found = [path.name for path in folder.iterdir() if path.is_dir() and controllers.VERSION.match(path.name)
             and all(controllers.BASE.snapshot(v, path.name).exists() for v in controllers.VARIANTS)] \
        if folder.is_dir() else []
    return sorted(found, key=controllers.version_key)


def latest_release(controller):
    released = [version for _, name, version in release.tags() if name == controller.name]
    return max(released, key=controllers.version_key) if released else None


def default_version(controller, made):
    """The version to write: see the module's text. `made(version)` converts with that version in the titles."""
    latest = latest_release(controller)
    if latest:
        unchanged = all(controller.snapshot(variant, latest).exists() and made(latest)[variant] ==
                        json.loads(controller.snapshot(variant, latest).read_text(encoding="utf-8"))
                        for variant in controllers.VARIANTS)
        return latest if unchanged else controllers.next_version(latest)
    if controller.built_until:
        return controllers.next_version(controller.built_until)
    return controller.first_version


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("controller", help="neptune or dse")
    parser.add_argument("--ibex", help="the Ibex version to convert (default: the newest snapshot)")
    parser.add_argument("--version", help="the version to write (default: see above)")
    parser.add_argument("--check", action="store_true", help="compare with the working layouts; write nothing")
    args = parser.parse_args()
    try:
        controller = controllers.get(args.controller)
        if controller.base:
            raise ValueError("Ibex is the base layout: a builder writes it (docs/building.md)")
        versions = ibex_versions()
        base = args.ibex or (versions[-1] if versions else None)
        if base is None or base not in versions:
            raise ValueError(f"no Ibex snapshot {base or ''} of both variants under versions/ibex/")
        sources = {variant: json.loads(controllers.BASE.snapshot(variant, base).read_text(encoding="utf-8"))
                   for variant in controllers.VARIANTS}
        cache = {}

        def made(version):
            if version not in cache:
                cache[version] = {variant: convert.convert(sources[variant], controller.name, variant, version)
                                  for variant in controllers.VARIANTS}
            return {variant: data for variant, (data, _) in cache[version].items()}

        if args.check:
            working = {variant: controller.working_json(variant) for variant in controllers.VARIANTS}
            if not all(path.exists() for path in working.values()):
                raise ValueError(f"{controller.name}/ has no working layouts")
            version = args.version or release.working_version(controller)
            current = {variant: json.loads(path.read_text(encoding="utf-8")) for variant, path in working.items()}
            stale = [variant for variant in controllers.VARIANTS if made(version)[variant] != current[variant]]
            for variant in stale:
                print(f"  {working[variant].relative_to(controllers.ROOT)} is not the conversion of ibex {base}")
            print(f"Conversion check {controller.name} {version} from ibex {base}:",
                  "up to date" if not stale else f"{len(stale)} layout(s) differ")
            return 1 if stale else 0
        version = args.version or default_version(controller, made)
        controllers.version_key(version)
        made(version)
        controller.directory.mkdir(exist_ok=True)
        for variant in controllers.VARIANTS:
            data, report = cache[version][variant]
            path = controller.working_json(variant)
            path.write_text(convert.dumps(data), encoding="utf-8")
            print(f"{path.relative_to(controllers.ROOT)}: {data['controller_mappings']['title']}, from ibex {base}")
            for line in report:
                print(f"  {line}")
    except (OSError, ValueError, KeyError, release.Problem) as error:
        print(f"Convert error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
