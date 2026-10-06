"""Every input with a cleanup function stores its entries in one order: the Regular Press, the guard, the Release.

Extends the 10-06 steering-fallback-swap builder; it stays frozen. The author's decision of
2026-10-06, after the audit in findings/2026-10-06-menu-entry-point-stick-touches/README.md: on
the first load of the layout, with a thumb on a stick and a menu button held, the Fn layer's
delayed add never came. "My suspicion is that the regular press actually isn't being interrupted.
And that the release needs to go last ... the order: repeated removal of a regular press, then
the guard, then a release. That's how it should always be."

One change to the finished layout, and no bind changes: on every input that has a cleanup
function (a repeating, interruptible Regular Press that only removes layers), the activator types
are stored as Regular Press, then chord, then Release. That is the order the Steam editor lists
them in. Until now 121 inputs in each layout had another order:

- the stick touches of the four menu Entry Points had the Release between the Regular Press and
  its guard, since 90.24 put the cleanup function in front of July's Release and guard;
- the stick touches of the two Scroll layers had the Release first;
- 109 inputs had the guard first.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.cleanups import Cleanups                                             # noqa: E402
from steam_layout.model import Layout                                                  # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

SWAP = ROOT / 'findings/2026-10-06-steering-fallback-swap/build_candidate.py'
spec = importlib.util.spec_from_file_location('steering_fallback_swap_build', SWAP)
sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw)

ORDER = ('Full_Press', 'chord', 'release')      # the Regular Press, its guard, the Release
NAMES = {'Full_Press': 'Regular Press', 'chord': 'guard', 'release': 'Release'}


def cleanup_inputs(layout):
    """(layer, source, input) of every input with a cleanup function, as the Cleanup audit reads them."""
    return sorted({(t.layer, t.source, t.input) for t in Cleanups(layout).inv.transitions if t.role == 'recovery'})


def in_order(activators):
    """The same activators with the three types first, in ORDER. Any other type keeps its place after them."""
    return {**{kind: activators[kind] for kind in ORDER if kind in activators},
            **{kind: value for kind, value in activators.items() if kind not in ORDER}}


def reorder(data):
    """Store every cleanup input's entries in ORDER. Returns the log: one line per old order, with its count."""
    layout = Layout(data)
    found, seen = collections.Counter(), 0
    for layer, source, name in cleanup_inputs(layout):
        slot = layout.active(layer)[source]['inputs'][name]
        old = slot['activators']
        unknown = set(old) - set(ORDER)
        if unknown:
            raise ValueError(f'{layer} {source}/{name}: a cleanup input with {sorted(unknown)}; decide where it goes')
        seen += 1
        if list(old) != list(in_order(old)):
            found[tuple(old)] += 1
            slot['activators'] = in_order(old)
    log = [f'{seen} inputs have a cleanup function; {sum(found.values())} were stored in another order']
    log += [f'  {", ".join(NAMES[kind] for kind in kinds)}: {count} inputs' for kinds, count in found.most_common()]
    return log


class Front:
    """In front of the 90.35 classes: one change to the finished layout."""

    def finish(self):
        data = super().finish()
        self.order_log = reorder(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('fallback swap candidate', 'cleanup entry order candidate')
        cm['description'] = (
            'Cleanup entry order candidate; device verification pending. Every input with a cleanup function stores '
            'its Regular Press, then its guard, then its Release. '
            'See findings/2026-10-06-cleanup-entry-order/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Front, type(sw.Builder(variant))), {})(variant)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--vdf', action='store_true')
    args = parser.parse_args()
    manifest = {}
    for variant in ('default', 'alternative'):
        b = Builder(variant); data = b.finish()
        readable = json.dumps(data, indent='\t') + '\n'
        numeric, count = titles_to_ids(readable, generate_lookup(data))
        if '{{' in numeric:
            raise ValueError('unresolved reference')
        restored, _ = ids_to_titles(numeric, generate_lookup(data))
        if json.loads(restored) != data:
            raise ValueError('runtime reference roundtrip')
        stem = HERE / f'{variant}-cleanup-entry-order'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(b.order_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'fallback_swap_generator_sha256': hashlib.sha256(SWAP.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers')
        for line in b.order_log:
            print('   ', line)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
