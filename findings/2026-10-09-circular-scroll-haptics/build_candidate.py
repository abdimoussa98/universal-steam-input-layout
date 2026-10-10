"""90.40: Low right-trackpad circular-scroll haptics on the 90.38 layout.

Extends the frozen 90.38 builder directly; the separate 90.39 fallback-window
experiment is not part of this build. --install writes the working JSON pair.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

spec = importlib.util.spec_from_file_location(
    'circular_scroll_previous',
    ROOT / 'findings/2026-10-08-steering-rtp-and-menu-chords/build_candidate.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def build(variant):
    # The previous builder runs the shared fix pipeline. Make the one setting
    # change on that finished layout, in title form, preserving all bindings.
    data, report = previous.build(variant)
    readable, _ = ids_to_titles(json.dumps(data), generate_lookup(data))
    data = json.loads(readable)
    group = Layout(data).active('RTP: Circular Scroll')['right_trackpad']
    assert group['mode'] == 'scrollwheel'
    assert group['settings']['haptic_intensity'] == '0'
    group['settings']['haptic_intensity'] = '1'  # Low
    readable = json.dumps(data, indent='\t') + '\n'
    numeric, _ = titles_to_ids(readable, generate_lookup(data))
    assert '{{' not in numeric
    restored, _ = ids_to_titles(numeric, generate_lookup(data))
    assert json.loads(restored) == data
    return json.loads(numeric), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        data, report = build(variant)
        working = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        current = json.loads(working.read_text())['controller_mappings']
        cm = data['controller_mappings']
        cm['title'] = current['title'].rsplit(' :: ', 1)[0] + ' :: 90.40'
        cm['description'] = current['description']
        target = working if args.install else HERE / f'{variant}-candidate.json'
        target.write_text(json.dumps(data, indent='\t') + '\n')
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        print(target.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
