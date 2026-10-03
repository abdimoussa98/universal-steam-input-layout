#!/usr/bin/env python3
"""Cover check and inheritance report, on backward chains (the "Flow audit" of the build audit).

For every layer a chain of adding bindings reaches (steam_layout/chains.py), reports the stacks that can
be under it, each with the bindings that built it, and what each input inherits on those stacks. Inputs
whose inherited binding differs between stacks are listed ("varies", "review"). An ordinary layer inherits
by default, and the one blocking rule, for layers with an Always On action, is checked by the Window audit
(audit_inheritance.py).

What fails:
- an entry to review: a "varies" or "review" input on a layer that changed since the baseline, or that a
  changed layer feeds, until it is fixed or accepted in the exceptions register (author, 2026-10-02). The
  baseline is a working layout's newest snapshot, or --baseline. On an unchanged layer they stay information
- a cover finding (steam_layout/covers.py): a cover that outlives its owners, sits below its owner, or
  inherits an input through a layer between it and its owner
- a coverage gap: a layer no chain reaches (a layer only added by hold_layer is out of scope and listed),
  a requested layer that isn't reached, or a lookup the chains can't model (a mode shift that changes
  layers, an unknown chord button)

The chains start from the contexts in the rules (Base, and Base with Gyro) and keep each chain to its own
layers, so a cover is judged with its own family. No families are declared: a new layer is picked up from
the layout. Until 2026-10-01 this audit walked families declared in the rules; that walk is deprecated and
lives in archived/depth-search-and-family-walk/.

Read-only. Exit codes: 0 = clean, 1 = cover findings or coverage gaps, 2 = invalid input.

    python3 audit_flow_inheritance.py neptune/single-set-default_hold-gyro_latest.json
    python3 audit_flow_inheritance.py <layout> --layer 'Menu Left: Fn Layer'
    python3 audit_flow_inheritance.py <layout> --inventory --layer 'L1: Modifier 0'
    python3 audit_flow_inheritance.py <layout> --json
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

from steam_layout import changes
from steam_layout.chains import NOT_FOLLOWED, SETTLE
from steam_layout.covers import RULES, check_cover, family_view, load_rules
from steam_layout.flow_inheritance import inspect_target
from steam_layout.model import TARGET, Layout, map_title
from steam_layout.rules import tag

FINDINGS = ("varies", "review", "replaced", "satisfied")
REVIEW = FINDINGS[:2]           # the entries a changed layer has to fix or accept
ENFORCES = {"cover check": ("R144",), "coverage": ("R145",), "needs review": ("R139",)}   # check -> rules


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decisions(config, variant, mapping):
    """{(layer, "source/input"): {"status", "why"}} from the flow rules' decisions."""
    result = {}
    for d in config.get("decisions", []):
        if d.get("status") not in ("allow", "todo") or not d.get("why"):
            raise ValueError(f"decision needs status allow/todo and a why: {d}")
        inputs = d["inputs"].get(variant, d["inputs"].get("default", [])) if isinstance(d["inputs"], dict) else d["inputs"]
        for layer in d["layers"]:
            for name in inputs:
                result[(map_title(layer, mapping), name)] = {"status": d["status"], "why": d["why"]}
    return result


def is_cover(title, config, mapping):
    covers = config.get("covers", {})
    titles = {map_title(t, mapping) for t in covers.get("titles", [])}
    if title in {map_title(t, mapping) for t in covers.get("not_covers", [])}:
        return False
    return title in titles or any(title.endswith(s) for s in covers.get("suffixes", []))


def needs_review(reached, changed, covers_accepted):
    """The inherited inputs that differ between stacks on a layer that changed, or that a changed layer feeds.

    Each one fails until it is fixed or accepted in the exceptions register (author, 2026-10-02). Accepting isn't
    blocking: inheritance stays the default. A cover's inputs are judged by the cover check instead, when the
    register says so.
    """
    rows = []
    for title, target in reached.items():
        if target["cover"] and covers_accepted:
            continue
        for i in target["inputs"]:
            if i["finding"] not in REVIEW or i.get("decision"):
                continue
            touched = ({title} | {p for v in i["variants"] for p in v["providers"]}) & changed
            if touched:
                rows.append({"layer": title, "input": f"{i['source']}/{i['input']}", "finding": i["finding"],
                             "changed": sorted(touched)})
    return rows


def run(layout_path, config_path=None, layers=None, baseline=None):
    data = json.loads(Path(layout_path).read_text(encoding="utf-8"))
    config = load_rules(config_path)
    layout = Layout(data)
    variant = "alternative" if "alternative" in layout.cm.get("title", "") else "default"
    mapping = config.get("variants", {}).get(variant, {})
    started = time.perf_counter()
    view = family_view(layout, config)
    decided = decisions(config, variant, mapping)
    used = set()
    contexts = [[layout.base]] + [list(c) for c in view.contexts]
    report = {"layout": {"path": str(layout_path), "title": layout.cm.get("title"), "variant": variant,
                         "sha256": sha(layout_path)},
              "rules": {"path": str(config_path or RULES), "version": config.get("version"),
                        "sha256": sha(config_path or RULES)},
              "targets": {}, "uncovered": []}
    reached = {}
    for title in layout.presets:
        if title == layout.base or not view.reached(title) or (layers and title not in layers):
            continue
        lowers = view.lineage(title)
        paths = {lower: why.describe() for lower, why in lowers.items()}
        entry = reached[title] = {"cover": is_cover(title, config, mapping), "inputs": [],
                                  "lower_stacks": [{"stack": list(lower), "path": paths[lower]} for lower in lowers]}
        for r in inspect_target(layout, title, list(lowers)):
            if r.finding or r.unsupported:
                row = _input_json(r, paths)
                key = (title, f"{r.source}/{r.name}")
                if key in decided:
                    row["decision"] = decided[key]
                    used.add(key)
                entry["inputs"].append(row)
    report["targets"] = reached
    report["stale_decisions"] = [f"{layer} {name}" for layer, name in sorted(set(decided) - used) if not layers]
    transitions = [t for t in view.inventory.transitions if t.layer in reached]
    report["unsupported"] = [t.describe() + ": " + t.reason for t in transitions if t.role == "mode-shift"] + \
        [t.describe() + ": " + t.condition.label for t in transitions if t.condition and not t.condition.known]
    allow = {}
    for a in config.get("covers", {}).get("allow", []):
        for check in a.get("checks", [a.get("check")]):
            allow.setdefault(map_title(a["cover"], mapping), {})[check] = a["reason"]
    report["covers"] = [check_cover(layout, view, title, allow.get(title))
                        for title, t in sorted(reached.items()) if t["cover"]]
    report["uncovered"] = sorted(set(layers or []) - set(reached))
    # A whole-layout audit also needs a chain to reach every layer. A context layer counts as covered.
    in_context = {t for c in contexts for t in c}
    outside = set() if layers else set(layout.presets) - set(reached) - in_context
    # Layers added only by legacy hold_layer are out of scope, listed, not gaps.
    legacy = {t for t in outside if view.inventory.legacy_only(t)}
    report["legacy_only"] = sorted(legacy)
    report["unreached"] = sorted(outside - legacy)
    report["view"] = {"contexts": contexts, "stacks": len(view.stacks()),
                      "seconds": round(time.perf_counter() - started, 3)}
    gaps = report["uncovered"] or report["unreached"] or report["unsupported"] \
        or any(i["unsupported"] and not i.get("decision") for t in reached.values() for i in t["inputs"])
    cover_findings = any(not f["allowed"] for c in report["covers"] for f in c["findings"])
    against = changes.baseline_for(layout_path, baseline)
    changed = changes.changed_since(data, against)
    report["baseline"] = str(against) if against else None
    report["changed_layers"] = sorted(changed)
    report["needs_review"] = needs_review(reached, changed, config.get("review", {}).get("covers"))
    report["clean"] = not gaps and not cover_findings and not report["needs_review"]
    return report


def _input_json(r, paths):
    return {"source": r.source, "input": r.name, "target": r.status, "finding": r.finding,
            "unsupported": r.unsupported,
            "variants": [{"kind": v.kind, "providers": sorted(v.providers), "base": v.base,
                          "directly_below": v.lowers[0][-1] in v.providers if v.lowers[0] else False,
                          "changes_layers": v.changes_layers, "activators": v.activators,
                          "example": {"stack": list(v.lowers[0]), "path": paths[v.lowers[0]]},
                          "stacks": len(v.lowers)} for v in r.variants]}


def _commands(activators, layout=None):
    def readable(c):
        c = c.split(",")[0].replace("controller_action ", "")
        m = TARGET.search("controller_action " + c)
        if m and layout:
            c = c.replace(m.group(2), layout.resolve(m.group(2)), 1)
        return c
    out = []
    for kind, value in (activators or {}).items():
        for e in value if isinstance(value, list) else [value]:
            b = e.get("bindings", {}).get("binding", [])
            b = b if isinstance(b, list) else [b]
            cmds = " ; ".join(readable(c) for c in reversed(b))
            settings = ",".join(f"{k}={v}" for k, v in sorted(e.get("settings", {}).items()))
            out.append(f"{kind}{'(' + settings + ')' if settings else ''}: {cmds}")
    return out


def print_report(report, detail, layout=None):
    lay, rules, view = report["layout"], report["rules"], report["view"]
    print(f"Layout: {lay['title']} ({lay['variant']}), sha256 {lay['sha256'][:12]}")
    print(f"Rules: v{rules['version']}, sha256 {rules['sha256'][:12]} ({rules['path']})")
    print(f"Chains: {view['stacks']} stacks from " + " and ".join(" > ".join(c) for c in view["contexts"])
          + f", {len(report['targets'])} layers reached, {view['seconds']} s")
    for u in report["unsupported"]:
        print(f"Coverage gap {tag(ENFORCES['coverage'])}: unsupported: " + u)
    print("\nInherited bindings that differ between stacks (information), and unsupported lookups (gaps)")
    print("Target                                  Lower    Varies Review Replaced Satisfied Unsupported")
    for title, t in sorted(report["targets"].items()):
        c = Counter(i["finding"] for i in t["inputs"] if i["finding"] and not i.get("decision"))
        u = sum(1 for i in t["inputs"] if i["unsupported"] and not i.get("decision"))
        d = sum(1 for i in t["inputs"] if i.get("decision"))
        note = ("  cover: see cover check" if t["cover"] else "") + (f"  decided: {d}" if d else "")
        print(f"{title[:39]:39} {len(t['lower_stacks']):5}  " + " ".join(f"{c.get(k, 0):8}" for k in FINDINGS[:2])
              + f" {c.get('replaced', 0):8} {c.get('satisfied', 0):9} {u:11}{note}")
    if report["uncovered"]:
        print(f"\nCoverage gap {tag(ENFORCES['coverage'])}: no chain of adding bindings reaches " + ", ".join(report["uncovered"]))
    for stale in report.get("stale_decisions", []):
        print("\nStale decision (matches no finding): " + stale)
    if report.get("legacy_only"):
        print("\nOut of scope: reached only by legacy hold_layer (not followed): "
              + ", ".join(report["legacy_only"]))
    if report["unreached"]:
        print(f"\nCoverage gap {tag(ENFORCES['coverage'])}: no chain of adding bindings reaches: " + ", ".join(report["unreached"]))
    shown = [(title, t) for title, t in sorted(report["targets"].items()) if detail or not t["cover"]]
    for title, t in shown:
        rows = [i for i in t["inputs"] if detail or (not i.get("decision") and i["unsupported"])]
        if not rows:
            continue
        print(f"\n== {title}" + (" (cover: see cover check)" if t["cover"] else ""))
        if detail:
            for s in t["lower_stacks"]:
                print(f"  lower: {' > '.join(s['stack'])}\n    via " + " | ".join(s["path"]))
        for i in rows:
            label = i["finding"] or f"unsupported {tag(ENFORCES['coverage'])}"
            print(f"  {label}: {i['source']}/{i['input']} (target {i['target']})" +
                  (f" - {i['unsupported']}" if i["unsupported"] else ""))
            if i.get("decision"):
                print(f"    decided ({i['decision']['status']}): {i['decision']['why']}")
            for v in i["variants"]:
                who = ", ".join(v["providers"]) or v["kind"]
                print(f"    from {who}{' [Base]' if v['base'] else ''}{' [directly below]' if v['directly_below'] else ''}"
                      f"{' [changes layers]' if v['changes_layers'] else ''}"
                      f" on {v['stacks']} stack(s), e.g. {' > '.join(v['example']['stack'])}")
                for line in _commands(v["activators"], layout):
                    print("      " + line)
                if detail:
                    print("      via " + " | ".join(v["example"]["path"]))
    if report.get("covers"):
        print("\nCover check (owners from the chains; Layer Definition of Done section 5)")
        for c in report["covers"]:
            print(f"  {c['cover']}: owners {', '.join(c['owners']) or 'none'}"
                  + ("" if c["findings"] else " - ok"))
            for f in c["findings"]:
                print(f"    {f['check']} {tag(ENFORCES['cover check'])}: {f['detail']} ({f['stacks']} stack(s), e.g. {' > '.join(f['stack'])})"
                      + (f"\n      accepted: {f['allowed']}" if f["allowed"] else ""))
                if detail or not f["allowed"]:
                    print("      via " + " | ".join(f["path"]))
            if detail:
                for upper, controls in c["above"].items():
                    taken = ", ".join(k + ("" if removes else " (keeps the cover)") for k, removes in controls.items())
                    print(f"    above: {upper} takes {taken}")
            elif c["above"]:
                print(f"    above: {len(c['above'])} layer(s) take some of its controls (--layer shows them)")
    if report.get("needs_review"):
        print(f"\nNeeds review {tag(ENFORCES['needs review'])}: on a layer changed since {Path(report['baseline']).name}, "
              "an inherited input differs between stacks.\nFix each one, or accept it in the exceptions register "
              "(steam_layout/flow_config.json) with a reason.")
        for row in report["needs_review"]:
            print(f"  {row['layer']}: {row['input']} ({row['finding']}); changed: {', '.join(row['changed'])}")
    print("\nResult: " + ("clean" if report["clean"] else
                          "not clean (cover findings, coverage gaps or entries to review above)"))


def print_inventory(layout_path, config_path, layers):
    """Every layer-changing binding, with what the chains do with it."""
    layout = Layout(json.loads(Path(layout_path).read_text(encoding="utf-8")))
    view = family_view(layout, load_rules(config_path))
    for title in layout.presets:
        rows = view.inventory.by_layer(title)
        if not rows or (layers and title not in layers):
            continue
        print(f"  {title}" + ("" if title == layout.base or view.reached(title) else "  (not reached)"))
        for t in rows:
            adds = any(op == "add_layer" for op, _ in t.ops)
            if t.role in NOT_FOLLOWED:
                mark = "skip  "
            elif adds:
                mark = "follow"
            elif t.role in SETTLE and all(op == "remove_layer" for op, _ in t.ops):
                mark = "settle"
            else:
                mark = "skip  "
            print(f"    {mark} {t.role:12} {t.describe().split(' ', len(title.split(' ')))[-1]}  ({t.reason})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--config", type=Path, help="rules (default: steam_layout/flow_config.json)")
    parser.add_argument("--layer", action="append", help="report only this layer, in full (repeatable)")
    parser.add_argument("--baseline", type=Path, help="the layout to compare with, to find the changed layers "
                        "(default: a working layout's newest snapshot)")
    parser.add_argument("--inventory", action="store_true",
                        help="list every layer-changing binding and whether the chains follow it")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.inventory:
            print_inventory(args.layout, args.config, args.layer)
            return 0
        report = run(args.layout, args.config, args.layer, args.baseline)
    except (OSError, ValueError, KeyError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        layout = Layout(json.loads(args.layout.read_text(encoding="utf-8")))
        print_report(report, detail=bool(args.layer), layout=layout)
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
