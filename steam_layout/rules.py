"""The rule registry: the rule tables in resources/Layer Definition of Done.md.

Every rule the layout must follow has one row there, in one fixed shape:

    | ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |

`load()` reads every table with exactly that header and ignores the others.
An ID is `R` plus a number from 101 (R1 to R5 are buttons). It is never reused
or renumbered; a retired rule keeps its row.

"Checked by" is a `;`-separated list of:

    Budget audit: banned activators    an audit and one of its checks
    Build audit                        an audit as a whole
    `cleanup_lists` fix                a step of the fix pipeline
    `test_file.test_name`              one test, or `test_file` for the whole file
    Not checked yet                    nothing fails on this rule
    Retired, 2026-10-02: why           the rule no longer applies

A checker may end in " (part)" when it covers only some layers. "Rests on"
names Steam assumptions by ID (`A3, A12`), or is a dash.

The other direction is declared in the code: each audit and the fix pipeline
has an `ENFORCES` table, check or fix -> the rule IDs it enforces. `declared()`
collects them, and tests/test_rule_registry.py keeps the two in step.

    python3 -m steam_layout.rules      # the rules nothing checks yet, or only in part

Plan: plans/2026-10-02-rule-registry.md.
"""
from collections import namedtuple
import importlib
from pathlib import Path
import re
import sys

REGISTRY = Path(__file__).resolve().parent.parent / "resources" / "Layer Definition of Done.md"
HEADER = ("ID", "Rule", "Example", "Decided", "Checked by", "Rests on", "Exceptions")
AUDITS = ("Budget", "Window", "Flow", "Cleanup", "Build")
NOT_CHECKED = "Not checked yet"
PART = " (part)"
RULE_ID = re.compile(r"R[1-9]\d\d")
REFERENCE = re.compile(r"(?<![A-Za-z0-9])R[1-9]\d\d(?![0-9])")
ASSUMPTION_ID = re.compile(r"A[1-9]\d*")
SOURCES = (                                # (kind, audit name, module holding its ENFORCES)
    ("audit", "Budget", "audit_command_budget"),
    ("audit", "Window", "steam_layout.inheritance"),
    ("audit", "Flow", "audit_flow_inheritance"),
    ("audit", "Cleanup", "steam_layout.cleanups"),
    ("audit", "Build", "audit_build"),
    ("fix", None, "steam_layout.fixes"),
)

Rule = namedtuple("Rule", "id statement example decided checked_by rests_on exceptions section")
Checker = namedtuple("Checker", "kind name check part")   # kind: audit, fix, test, none or retired


def cells(line):
    """A table row's cells. `\\|` inside a cell is a literal pipe."""
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def checkers(text):
    """The checkers a "Checked by" cell names. Raises ValueError on a form it doesn't know."""
    if text.startswith("Retired, "):
        return (Checker("retired", None, text, False),)
    found = []
    for item in (part.strip() for part in text.split(";")):
        part = item.endswith(PART)
        item = item[:-len(PART)] if part else item
        if item == NOT_CHECKED:
            found.append(Checker("none", None, None, False))
        elif match := re.fullmatch(rf"({'|'.join(AUDITS)}) audit(?:: (.+))?", item):
            found.append(Checker("audit", match[1], match[2], part))
        elif match := re.fullmatch(r"`(\w+)` fix", item):
            found.append(Checker("fix", match[1], None, part))
        elif match := re.fullmatch(r"`(test_\w+)(?:\.(test_\w+))?`", item):
            found.append(Checker("test", match[1], match[2], part))
        else:
            raise ValueError(f"unknown checker {item!r}")
    if len(found) > 1 and any(c.kind == "none" for c in found):
        raise ValueError(f"{NOT_CHECKED!r} stands alone: {text!r}")
    return tuple(found)


def assumptions(text):
    """The assumption IDs a "Rests on" cell names; a dash means none yet."""
    if text in ("—", "-"):
        return ()
    found = tuple(item.strip() for item in text.split(","))
    if not all(ASSUMPTION_ID.fullmatch(item) for item in found):
        raise ValueError(f"bad assumption IDs {text!r}")
    return found


def load(path=REGISTRY):
    """{rule ID: Rule}, in file order."""
    found, section, in_table = {}, "", False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        if not line.lstrip().startswith("|"):
            in_table = False
            continue
        row = cells(line)
        if tuple(row) == HEADER:
            in_table = True
        elif in_table and not all(set(cell) <= set("-: ") for cell in row):
            if len(row) != len(HEADER):
                raise ValueError(f"a rule row needs {len(HEADER)} cells: {line.strip()[:80]}")
            rule_id, statement, example, decided, checked, rests, exceptions = row
            if not RULE_ID.fullmatch(rule_id):
                raise ValueError(f"bad rule ID {rule_id!r}")
            if rule_id in found:
                raise ValueError(f"{rule_id} appears twice")
            if not all((statement, example, decided, checked, rests, exceptions)):
                raise ValueError(f"{rule_id} has an empty field")
            found[rule_id] = Rule(rule_id, statement, example, decided, checkers(checked), assumptions(rests),
                                  exceptions, section)
    return found


def references(text):
    """The rule IDs a text names. R1 to R5 (buttons) and Deck check IDs like R3 never match."""
    return set(REFERENCE.findall(text))


def unchecked(rules):
    """(rules nothing fails on, rules checked only in part), as lists of IDs in file order."""
    live = [r for r in rules.values() if r.checked_by[0].kind != "retired"]
    nothing = [r.id for r in live if r.checked_by[0].kind == "none"]
    partly = [r.id for r in live if r.id not in nothing and all(c.part for c in r.checked_by)]
    return nothing, partly


def tag(ids):
    """Rule IDs as printed next to a finding: [R127, R131]."""
    return "[" + ", ".join(ids) + "]"


def declared():
    """{(kind, name, check): rule IDs} from every audit and fix that declares `ENFORCES`.

    An audit's key is one of its checks, or None for the audit as a whole; a fix's key is its name.
    """
    root = str(REGISTRY.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    found = {}
    for kind, name, module in SOURCES:
        for key, ids in getattr(importlib.import_module(module), "ENFORCES", {}).items():
            found[(kind, name or key, key if name else None)] = tuple(ids)
    return found


def main():
    """python3 -m steam_layout.rules: the rules that still need a check."""
    rules = load()
    nothing, partly = unchecked(rules)
    print(f"{len(rules)} rules in {REGISTRY.name}")
    for title, ids in (("Not checked yet", nothing), ("Checked only in part", partly)):
        print(f"\n{title} ({len(ids)})")
        for rule_id in ids:
            print(f"  {rule_id}  {rules[rule_id].statement}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
