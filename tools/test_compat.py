"""Run the test gate at a tagged commit, including tags before test reorganization.

The workflow loads this file from its own commit before executing it against
the tagged tree. Modern trees use tests.runner and its full evidence protocol.
Legacy trees keep their own unittest/sharder behavior and produce explicitly
legacy completion records. Those records cannot satisfy a modern manifest.
Legacy validation assumes a clean checkout of the tagged commit; it checks
commit/run/module completion, not working-tree bytes or tag-reference freshness.
The workflow supplies that clean checkout and keeps its pinned adapter outside
the tagged tree. Artifact paths always resolve from the caller's directory.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def output(root, *command):
    return subprocess.check_output(command, cwd=root, text=True).strip()


def modules(root, index, count):
    return output(root, sys.executable, "-m", "tools.release", "shard", str(index), str(count)).split()


def legacy_record(root, index, count, run_id, selected):
    return {"schema": "legacy-unittest-1", "head": output(root, "git", "rev-parse", "HEAD"),
            "run_id": run_id, "index": index, "count": count, "modules": selected,
            "successful": True}


def validate_legacy(records, root, run_id, count=4):
    expected = {index: legacy_record(root, index, count, run_id, modules(root, index, count))
                for index in range(1, count + 1)}
    if len(records) != count or {item.get("index") for item in records} != set(expected):
        raise ValueError("Incomplete or duplicate legacy shard set")
    for item in records:
        if item != expected[item["index"]]:
            raise ValueError("Legacy evidence differs from its tagged commit, run or assigned modules")
    flattened = [name for item in records for name in item["modules"]]
    if len(flattened) != len(set(flattened)):
        raise ValueError("Duplicate legacy test module assignment")
    every = output(root, sys.executable, "-c",
                   "from tools.release import test_modules; print(' '.join(test_modules()))").split()
    if sorted(flattened) != sorted(every):
        raise ValueError("Legacy shards do not cover the tagged commit's complete test selection")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "finalize", "node"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--shard", nargs=2, type=int)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.evidence is not None:
        args.evidence = args.evidence.resolve()
    args.files = [path.resolve() for path in args.files]
    modern = (root / "tests/runner.py").is_file()
    try:
        if args.command == "node":
            folder = root / "tests/node" if modern else root / "tests"
            paths = [folder / name for name in ("test_convert_vdf.mjs", "test_steering_observer.mjs")]
            if not all(path.is_file() for path in paths):
                raise ValueError("Both Node test files are required")
            return subprocess.call(["node", "--test", *(str(path) for path in paths)], cwd=root)
        if not args.run_id:
            parser.error("--run-id is required")
        if args.command == "run":
            if not args.shard or not args.evidence:
                parser.error("run requires --shard INDEX COUNT and --evidence")
            index, count = args.shard
            if not 1 <= index <= count:
                parser.error("invalid shard")
            if modern:
                return subprocess.call([sys.executable, "-m", "tests.runner", "--shard", str(index), str(count),
                                        "--evidence", str(args.evidence), "--run-id", args.run_id], cwd=root)
            import os
            selected = modules(root, index, count)
            if not selected:
                raise ValueError("Empty legacy test shard")
            env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(root), str(root / "tests"))))
            code = subprocess.call([sys.executable, "-m", "unittest", *selected], cwd=root, env=env)
            if code:
                return code
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(legacy_record(root, index, count, args.run_id, selected)) + "\n")
            return 0
        if modern:
            return subprocess.call([sys.executable, "-m", "tests.runner", "--finalize",
                                    *(str(path) for path in args.files), "--run-id", args.run_id], cwd=root)
        records = [json.loads(path.read_text()) for path in args.files]
        validate_legacy(records, root, args.run_id)
        print("Validated four legacy unittest shards at the tagged commit; modern scenario evidence is not claimed.")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Tagged test gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
