"""The pad window's Releases, the fallback's edge, and the Tap Cover resets come off.

Extends the 10-04 quiet-resets-and-beeps builder; it stays frozen. Three changes to the
finished layout, from what the author saw on the Deck with 90.29
(plans/2026-10-04-window-releases-and-tap-cover-resets.md):

1. **The right pad's Double Tap window carries the menu and modifier buttons' Release.**
   `RTP: Double Tap` binds Start and Select to nothing and the two modifier buttons to
   the scroll wheel. A button that was down when the window came on and is let go inside
   it had its Release covered, so its layers stayed on: the Fn layer answered the next
   press at once. Each of the four now has a Release that removes the window first and
   then every layer its pair can be holding. The fix pipeline shortens the lists to what
   can be under the window.

2. **The fallback hold leaves by up and down only.** The Release on the outer edge of
   `Steering | LS: Fallback Hold` comes off (author, 2026-10-04). The Releases on up and
   down, the pulse and the reset stay.

3. **The Tap Cover reset comes off the three Entry Points, for now.** The author thinks
   the repeated removal on the stick touches is what stopped the menu buttons while a
   thumb was on a stick. `LST: Entry Point`, `RST: Entry Point` and `RTP: Entry Point`
   have the touch of 90.24 again: the Release and the delayed Tap Cover.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout, actions, map_title                              # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

BEEPS = ROOT / 'findings/2026-10-04-quiet-resets-and-beeps/build_candidate.py'
spec = importlib.util.spec_from_file_location('quiet_resets_and_beeps_build', BEEPS)
qb = importlib.util.module_from_spec(spec); spec.loader.exec_module(qb)

WINDOW = 'RTP: Double Tap'
HOLD = 'Steering | LS: Fallback Hold'
RENAME = {'L1': 'L2', 'R1': 'R2'}       # the alternative layout's titles
# Every layer a menu button can be holding, by the default layout's titles. Not `Menu Keys`: it is a
# stateful layer, and Start and Select do nothing there. Not the windows: no window is under a window.
MENU_FAMILY = (
    'Menu Left: Entry Point', 'Menu Right: Entry Point', 'Menu Left: Fn Layer', 'Menu Right: Fn Layer',
    'Menu Left: Escape', 'Menu Right: Tab', 'Menu Left: Double Tap Cover', 'Menu Right: Double Tap Cover',
    'Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point',
    'Stateful | Menu Left: Fn Layer', 'Stateful | Menu Right: Fn Layer',
    'Menu Buttons: Left Stick Guard', 'Menu Buttons: Right Stick Guard', 'Menu Buttons: Tap Cover',
    'Menu Left!Right: Entry Point', 'Menu Right!Left: Entry Point', 'Menu Left!Right: Enter', 'Menu Right!Left: Backspace',
    'Menu Left!Right: Double Tap Cover', 'Menu Right!Left: Double Tap Cover')
# Every layer a modifier button can be holding. Not Steering's: it clears the pad's touch, so the window
# never comes on there.
MODIFIER_FAMILY = (
    'L1: Modifier 0', 'R1: Modifier 1', 'L1!R1: Modifier 2', 'R1!L1: Modifier 2',
    'Gyro | L1: Modifier 0', 'Gyro | R1: Modifier 1', 'Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2',
    'L1: Temp Cursor Gyro', 'R1: Temp Cursor Gyro', 'L1: Tap Cover', 'R1: Tap Cover', 'L1&R1: Tap Cover',
    'L1: Scroll Down', 'R1: Scroll Up', 'L1: Double Tap Cover', 'R1: Double Tap Cover')
MENU_BUTTONS = (('switch', 'button_menu'), ('switch', 'button_escape'))
SCROLL = ('mouse_wheel SCROLL_DOWN', 'mouse_wheel SCROLL_UP')


def token(title):
    return '{{Base::' + title + '}}'


def window_releases(data, variant):
    """Start, Select and the two modifier buttons get a Release in the pad's window: the window, then the family."""
    layout, log = Layout(data), []
    name = (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)
    groups = layout.active(WINDOW)
    # The modifier buttons are the two inputs the window turns into the scroll wheel: the bumpers in the
    # default layout, the triggers' soft pull in the alternative.
    modifiers = [(source, button) for source, group in groups.items() for button, slot in group.get('inputs', {}).items()
                 if any(a.startswith(SCROLL) for a in _press(slot))]
    if len(modifiers) != 2:
        raise ValueError(f'{WINDOW}: expected two inputs on the scroll wheel, found {modifiers}')
    for buttons, family, what in ((MENU_BUTTONS, MENU_FAMILY, 'the menu layers'), (modifiers, MODIFIER_FAMILY, 'the modifier layers')):
        titles = [name(title) for title in family]
        missing = [title for title in titles if title not in layout.presets]
        if missing:
            raise ValueError(f'{WINDOW}: no such layers: {missing}')
        for source, button in buttons:
            acts = groups[source]['inputs'][button]['activators']
            if list(acts) != ['Full_Press'] or not isinstance(acts['Full_Press'], dict):
                raise ValueError(f'{WINDOW} {source}/{button}: expected one press bind, found {acts}')
            commands = [f'controller_action remove_layer {token(title)} 0 0, , ' for title in [WINDOW] + titles]
            acts['release'] = {'bindings': {'binding': list(reversed(commands))}, 'settings': {'haptic_intensity': '0'}}
            log.append(f'{WINDOW} | {source}/{button}: a Release that removes the window, then {what} ({len(titles)})')
    return log


def _press(slot):
    press = slot.get('activators', {}).get('Full_Press')
    return actions(press) if isinstance(press, dict) else []


def fallback_edge(data):
    """The fallback hold's outer edge loses its Release."""
    acts = Layout(data).active(HOLD)['joystick']['inputs']['edge']['activators']
    release = acts.get('release')
    want = [f'controller_action remove_layer {token(HOLD)} 0 0, , ']
    if not isinstance(release, dict) or actions(release) != want or sorted(acts) != ['Full_Press', 'chord', 'release']:
        raise ValueError(f'{HOLD} edge: expected the pulse, the reset and a Release that removes the layer, found {acts}')
    del acts['release']
    return [f'{HOLD} | joystick/edge: the Release is removed; the pulse and the reset stay']


def cover_resets_off(data):
    """The three Entry Points' touch loses its Tap Cover reset."""
    layout, log = Layout(data), []
    for prefix, source in qb.COVER_RESETS:
        title = f'{prefix}: Entry Point'
        acts = layout.active(title)[source]['inputs']['touch']['activators']
        reset = acts.get('Full_Press')
        want = [f'controller_action remove_layer {token(prefix + ": Tap Cover")} 0 0, , ']
        if not isinstance(reset, dict) or actions(reset) != want or sorted(acts) != ['Full_Press', 'chord', 'release']:
            raise ValueError(f'{title} touch: expected the Release, the delayed Tap Cover and its reset, found {acts}')
        del acts['Full_Press']
        log.append(f'{title} | {source}/touch: the Tap Cover reset is removed')
    return log


class Releases:
    """In front of the 90.29 classes: three changes to the finished layout."""

    def finish(self):
        data = super().finish()
        self.window_log = window_releases(data, self.variant)
        self.fallback_log = fallback_edge(data)
        self.reset_off_log = cover_resets_off(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('quiet resets and beeps candidate', 'window releases and tap cover resets candidate')
        cm['description'] = (
            'Window releases and tap cover resets candidate; device verification pending. The pad window carries '
            "the menu and modifier buttons' Release, the fallback hold leaves by up and down only, and the Tap "
            'Cover resets are off. See findings/2026-10-04-window-releases-and-tap-cover-resets/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Releases, type(qb.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-window-releases-and-tap-cover-resets'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        log = b.window_log + b.fallback_log + b.reset_off_log
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'quiet_resets_generator_sha256': hashlib.sha256(BEEPS.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'window_releases': len(b.window_log), 'resets_removed': len(b.reset_off_log),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers, '
              f'{len(b.window_log)} window Releases, {len(b.reset_off_log)} resets removed')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
