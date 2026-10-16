"""Canonical active test paths and durable references, without importing tests.

Only ``tests/**/test_*.py`` belongs to Python discovery. Historical archives,
findings scripts, Node tests and the excluded overlay directory are separate.
The migration ledger resolves old documentation references after a split;
unmapped ambiguous basenames fail instead of choosing an arbitrary file.
"""
import ast
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_paths(root=None):
    root = Path(root) if root is not None else ROOT
    return sorted(path for path in (root / "tests").rglob("test_*.py")
                  if not any(part.startswith(".") or part == "__pycache__"
                             for part in path.relative_to(root / "tests").parts))


def test_modules(root=None):
    root = Path(root) if root is not None else ROOT
    return [".".join(path.relative_to(root).with_suffix("").parts)
            for path in test_paths(root)]


def case_map(root=None):
    root = Path(root) if root is not None else ROOT
    ledger = root / "tests" / "test-map.csv"
    if not ledger.exists():
        return {}
    with ledger.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    found = {row["old_id"]: row["new_id"] for row in rows}
    if len(found) != len(rows) or len(set(found.values())) != len(rows):
        raise ValueError("duplicate old or new test identity in migration ledger")
    return found


def resolve_tests(name, check=None, root=None):
    """Resolve a documented module or module.method, including recorded splits."""
    root = Path(root) if root is not None else ROOT
    if check is None and ".test_" in name and not name.startswith("tests."):
        name, check = name.rsplit(".", 1)
    old_module = name if name.startswith("tests.") else "tests." + name
    mapped = {new.rsplit(".", 2)[0] for old, new in case_map(root).items()
              if old.rsplit(".", 2)[0] == old_module
              and (check is None or old.rsplit(".", 1)[1] == check)}
    if mapped:
        paths = [root.joinpath(*module.split(".")).with_suffix(".py")
                 for module in sorted(mapped)]
    else:
        paths = [path for path in test_paths(root)
                 if path.stem == name or ".".join(path.relative_to(root).with_suffix("").parts) == name]
        if len(paths) > 1:
            raise ValueError(f"ambiguous test reference: {name}")
    if not paths or any(not path.is_file() for path in paths):
        raise ValueError(f"missing test reference: {name}{'.' + check if check else ''}")
    if check:
        paths = [path for path in paths if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == check for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))))]
        if not paths:
            raise ValueError(f"missing test check: {name}.{check}")
    return paths


def resolve_test(name, check=None, root=None):
    paths = resolve_tests(name, check, root)
    if len(paths) != 1:
        raise ValueError(f"test reference spans multiple files: {name}; use resolve_tests")
    return paths[0]
