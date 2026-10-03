"""Prototype of the hidden-exit check (brainstorm, 2026-10-02; not an audit yet).

A lower layer's exit is a Release that removes it. A pair is a lower layer and a
layer the backward chains can put on top of it that covers one of its exits:
binds the same input (or blocks it with a different source mode) and doesn't
remove the lower layer there.

Rule (author, 2026-10-02): a pair is a finding only when it covers an exit on
what keeps the lower layer alive, its keeper (steam_layout/cleanups.py), and the
top layer doesn't remove the lower layer there. For a button or thumb keeper
those are the exits on those buttons; for any other keeper, every exit counts.
Example: the menu Tap Cover covers the stick guard's stick-recentre Release, but
its Start and Select Releases remove the guard, and Start or Select is what keeps
the guard alive, so that pair is information, not a finding.
The stack is taken after the whole binding that added the upper layer has run,
and a finding is reported against the layer that actually answers the input. Chords are ignored, as in the chains.

Touchpad exception (author, 2026-10-02): a pair is set aside, not a finding,
when either layer is a touchpad layer (every binding that adds it is on a
trackpad) or the covered exit is a trackpad input. Tracked in todos.md.

    python3 findings/2026-10-02-hidden-exit/prototype.py neptune/single-set-default_hold-gyro_latest.json
"""
import json, sys, collections
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
from steam_layout.model import Layout, entries
from steam_layout.cleanups import BUTTONS, Cleanups
from steam_layout.flow_model import resolve
from steam_layout.stacks import apply_ops

def settled(layout, full, upper, why):
    """The stack once the binding that added `upper` has run to the end: an
    array can add more layers on top of it (L1 Modifier 0's R1 chord adds
    R1 Modifier 1, then R1 Tap Cover and Modifier 2)."""
    for _, t in reversed(why.steps):
        if ('add_layer', upper) in t.ops:
            rest = t.ops[t.ops.index(('add_layer', upper)) + 1:]
            return apply_ops(full, rest, layout.base)
    return full


def keeper_exits(c, lower, exits):
    """The exits on what keeps `lower` alive: its keeper buttons, or every exit."""
    kind, keep = c.keeper(lower)
    on_keeper = [e for e in exits if BUTTONS.get(e) in keep] if kind in ('button', 'thumb') else []
    return on_keeper or list(exits)


info_only = []   # (lower, upper, info): covers only exits that aren't on the keeper


def run(path):
    layout = Layout(json.load(open(path)))
    c = Cleanups(layout)
    info_only.clear()
    out = collections.defaultdict(dict)   # lower -> upper -> info
    for lower in c.layers:
        exits = sorted({(t.source, t.input) for t in c.inv.by_layer(lower)
                        if t.role == 'release' and ('remove_layer', lower) in t.ops})
        if not exits:
            continue
        for upper, (stack, why) in c.chains.above(lower).items():
            full = settled(layout, tuple(stack) + (upper,), upper, why)
            if lower not in full:
                continue              # the same binding removes it again
            for source, inp in exits:
                kind, layer, acts, _ = resolve(layout, full, source, inp)
                if kind == 'binding' and layer == lower:
                    continue
                info = out[lower].setdefault(layer, dict(hidden=[], carried=[], exits=exits, stack=full,
                                                         why=why.describe()))
                if acts and any(('remove_layer', lower) in set(layout.layer_ops(e)) for _, e in entries(acts)):
                    if (source, inp) not in info['carried']:
                        info['carried'].append((source, inp))
                elif (source, inp) not in info['hidden']:
                    info['hidden'].append((source, inp))
        keeping = keeper_exits(c, lower, exits)
        for layer, v in list(out[lower].items()):
            v['keeper_exits'] = keeping
            v['side'] = [h for h in v['hidden'] if h not in keeping]
            v['hidden'] = [h for h in v['hidden'] if h in keeping]
            if not v['hidden']:
                if v['side']:
                    info_only.append((lower, layer, v))
                del out[lower][layer]
        if not out[lower]:
            del out[lower]
    return layout, c, out

PADS = {'left_trackpad', 'right_trackpad'}


def touchpad_layers(c):
    """Layers that only trackpad bindings add."""
    return {t for t in c.layers if c._adding.get(t) and all(a.source in PADS for a in c._adding[t])}


def touchpad_exception():
    """True while the exceptions register sets the touchpad pairs aside (rule R136)."""
    from steam_layout import exceptions
    return any(e['scope'].get('kind') == 'touchpad' for e in exceptions.of(exceptions.load(), 'R136'))


def is_touchpad(pads, lower, upper, info):
    if not touchpad_exception():
        return False
    return lower in pads or upper in pads or any(source in PADS for source, _ in info['hidden'])


if __name__ == '__main__':
    layout, c, out = run(sys.argv[1])
    pads = touchpad_layers(c)
    excepted = {(lo, up): i for lo, ups in out.items() for up, i in ups.items() if is_touchpad(pads, lo, up, i)}
    print(f'Touchpad exception: {len(excepted)} pairs set aside (touchpad layers: {", ".join(sorted(pads))})')
    print(f'Findings: {sum(len(v) for v in out.values()) - len(excepted)} pairs')
    side = [(lo, up, i) for lo, up, i in info_only if not is_touchpad(pads, lo, up, dict(i, hidden=i['side']))]
    print(f'Information (covers an exit that is not on the keeper; the keeper exit still works): {len(side)} pairs')
    for lo, up, i in side:
        print(f'   {up} over {lo}: covers {["/".join(h) for h in i["side"]]}, keeper exits {["/".join(k) for k in i["keeper_exits"]]}'
              + (f' carried by it' if set(i['keeper_exits']) <= set(i['carried']) else ' untouched'))
    for lo in sorted(out):
        ups = {up: i for up, i in out[lo].items() if (lo, up) not in excepted}
        if not ups:
            continue
        kind, keep = c.keeper(lo)
        print(f'== {lo}   keeper=({kind}, {"+".join(sorted(keep))})   cleanup function: {"yes" if any(True for _ in c.cleanups(lo)) else "NO"}')
        for up, i in sorted(ups.items()):
            print(f'   {"window" if up in c.windows else "layer "} {up}: covers {["/".join(h) for h in i["hidden"]]}'
                  + (f', carries {["/".join(x) for x in i["carried"]]}' if i['carried'] else ''))
    print()
    print('All pairs, touchpad ones included:')
    n = sum(len(v) for v in out.values())
    allh = [(lo, up) for lo, ups in out.items() for up, i in ups.items() if len(i['hidden']) + len(i['carried']) == len(i['exits']) and not i['carried']]
    print(f'{n} (lower, upper) pairs with a hidden exit, on {len(out)} lower layers; {len(allh)} pairs hide every exit')
    for lo in sorted(out):
        kind, keep = c.keeper(lo)
        print(f'== {lo}   keeper=({kind}, {"+".join(sorted(keep))})   exits={["/".join(e) for e in next(iter(out[lo].values()))["exits"]]}')
        for up, i in sorted(out[lo].items()):
            tag = 'ALL' if (up and (lo, up) in allh) else 'some'
            print(f'   [{tag}] {up}: hides {["/".join(h) for h in i["hidden"]]}' + (f', carries {["/".join(x) for x in i["carried"]]}' if i['carried'] else ''))

def classify(path):
    layout, c, out = run(path)
    groups = collections.Counter(); ex = collections.defaultdict(list)
    for lo, ups in out.items():
        recovers = any(True for _ in c.cleanups(lo))
        for up, i in ups.items():
            mode = 'mode-block' if any(resolve(layout, i['stack'], s, n)[0] == 'mode' for s, n in i['hidden']) else 'binds it'
            key = ('window' if up in c.windows else 'layer', 'has cleanup' if recovers else 'NO cleanup', mode)
            groups[key] += 1; ex[key].append(f'{up} over {lo}: {["/".join(h) for h in i["hidden"]]}')
    return groups, ex
