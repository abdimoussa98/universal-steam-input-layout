"""Plan step 7 measurement: the Flow audit's comparison, run on chain stacks, against today's flow stacks.

It counts inputs whose inherited binding differs between stacks. When this was measured they were
called "conflict" and failed the Flow audit; since the author's correction on 2026-10-01 they are
"varies", information only (README.md, "The Flow audit on chain stacks").

**Historical.** It was run against the family-walk Flow audit, which was replaced by chains on
2026-10-01, so its "flow stacks" row can no longer be reproduced: `run` now uses chains itself. The
numbers it produced are recorded in README.md.

Not a tool. It answers one question: if audit_flow_inheritance.py took its lower stacks from
steam_layout/chains.py instead of walking the declared families, how would its findings change?

Run from the repo root:
    python3 findings/2026-10-01-backward-chain-stacks/flow_audit_on_chains.py [default|alternative]
"""
from collections import Counter
import json
import sys
import time

sys.path.insert(0, ".")
from audit_flow_inheritance import run
from steam_layout.chains import Chains
from steam_layout.flow_inheritance import inspect_target
from steam_layout.model import Layout

variant = sys.argv[1] if len(sys.argv) > 1 else "default"
path = f"neptune/single-set-{variant}_hold-gyro_latest.json"
flow = run(path)
layout = Layout(json.load(open(path)))
chains = Chains.of(layout)

covers = {t for t, row in flow["targets"].items() if row["cover"]}
before = {}
for title, row in flow["targets"].items():
    for i in row["inputs"]:
        if i["finding"]:
            before[(title, f"{i['source']}/{i['input']}")] = (i["finding"], bool(i.get("decision")))

started = time.time()
after, providers = {}, {}
for title in layout.presets:
    if title == layout.base or not chains.reached(title):
        continue
    for r in inspect_target(layout, title, list(chains.below(title))):
        if r.finding:
            key = (title, f"{r.source}/{r.name}")
            after[key] = r.finding
            providers[key] = [v.label() for v in r.variants]
seconds = time.time() - started

print(f"{variant}: Flow audit clean today: {flow['clean']}; chain comparison took {seconds:.1f} s")
print("findings on flow stacks :", dict(Counter(f for f, _ in before.values())))
print("findings on chain stacks:", dict(Counter(after.values())))
for label, keep in (("non-cover layers", lambda t: t not in covers), ("cover layers", lambda t: t in covers)):
    old = {k for k, (f, decided) in before.items() if f == "varies" and not decided and keep(k[0])}
    new = {k for k, f in after.items() if f == "varies" and keep(k[0])}
    print(f"\n{label}: undecided varying inputs {len(old)} on flow stacks, {len(new)} on chain stacks; "
          f"{len(new - old)} new, {len(old - new)} gone")
    by_layer = Counter(t for t, _ in new - old)
    for title, count in by_layer.most_common(12):
        example = next(k for k in sorted(new - old) if k[0] == title)
        print(f"   {title}: {count} new, e.g. {example[1]} from {providers[example][:4]}")
    if len(by_layer) > 12:
        print(f"   ... and {len(by_layer) - 12} more layers")
