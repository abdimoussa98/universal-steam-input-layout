"""Pad touch bumps, the middle-click mouse, the Menu Keys layer and the Tap Cover resets.

Extends the 10-04 required-cleanups builder; it stays frozen. Plan and the author's
decisions (2026-10-03 and 2026-10-04): plans/2026-10-04-pad-bumps-and-menu-layer.md.

1. **A low bump on touch where a click would be the centre click.** A pad's touch adds a
   hand-over layer, `RTP: Touch Entry Point` or `LTP: Touch Entry Point`: a D-pad pad with the
   Click Entry Point's own two Soft Presses on its ring, read at the touch. The inner one
   repeats and bumps; the outer one has the 5 ms delay (author, 2026-10-04: only the outer
   bind needs it). Both remove the layer, then add the pad's Entry Point. With the same two
   binds, the bump and the click agree wherever the thumb is.
   - Right: Base stays a mouse and binds only the touch. The click's add moves to
     `RTP: Entry Point`, where it repeats, so a click that is already down when the Entry
     Point lands still fires (A6); `Steering`, whose touch is blocked, binds it itself.
   - Left: Base's pad becomes a D-pad that binds only the touch. The swipes and the click move
     to a new `LTP: Entry Point` in swipe mode. Each swipe removes it.
2. **`RTP: Middle Click` is a mouse pad**, so the cursor moves while middle mouse is held.
3. **`Menu Keys`**, the menu stateful layer. With one menu button held, the other one goes
   through the Menu chain's recipe (R119) in four new layers for each side: an Entry Point
   (tap or hold), a Double Tap window that types the key, a second-press layer that holds it,
   and its cover. The hold, 150 ms, clears the stack, `Gyro` included, and adds `Menu Keys`.
   Only the plain Entry Points add the new Entry Point, beside the Fn layer: the Fn layers are
   shared with the `Stateful` Entry Points, and the hold works from Base and `Gyro` only.
5. **The Tap Cover reset** on the touch of `LST: Entry Point`, `RST: Entry Point` and
   `RTP: Entry Point` (R120).

Part 4 of the plan, five extra presses in the hidden-exit check, is tooling
(steam_layout/cleanups.py).

The required cleanups (R169 to R171) run last, over the new layers: `Builder` puts this
class under `RequiredCleanups`.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

REQUIRED = ROOT / 'findings/2026-10-04-required-cleanups/build_candidate.py'
spec = importlib.util.spec_from_file_location('required_cleanups_build', REQUIRED)
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
tc = rc.tc
cg = tc.gp.cg
st = rc.st

GYRO = cg.GYRO
MENU_KEYS = 'Menu Keys'
# pad: (source, its Entry Point, the Soft Press that adds its Click Entry Point)
PADS = {'RTP': ('right_trackpad', 'RTP: Entry Point', 'RTP: Click Entry Point'),
        'LTP': ('left_trackpad', 'LTP: Entry Point', 'LTP: Click Entry Point')}
MIDDLE = 'RTP: Middle Click'
STEERING = 'Steering'
SWIPES = ('dpad_west', 'dpad_east', 'dpad_north', 'dpad_south')
BUMP_HAPTIC = 1                 # low (author, 2026-10-04)
# A binding that is already held when its layer lands fires on its next repeat (A6, R113).
CLICK_REPEAT_MS = cg.pc.ADD_REPEAT_MS
HOLD_MS = 150                   # both menu buttons, into Menu Keys
TAP_COVER_MS = 150              # the stick and pad Entry Points' delayed Tap Cover
# first held, then pressed: the key the pressed one types, and the Menu chain it copies
CHAINS = {('Left', 'Right'): ('RETURN', 'Enter', 'TAB', 'Tab'),
          ('Right', 'Left'): ('BACKSPACE', 'Backspace', 'ESCAPE', 'Escape')}
# Menu Keys (author, 2026-10-04)
FACE = {'button_a': 'RETURN', 'button_b': 'ESCAPE', 'button_x': 'BACKSPACE', 'button_y': 'TAB'}
ARROWS = {'dpad_north': 'UP_ARROW', 'dpad_south': 'DOWN_ARROW', 'dpad_east': 'RIGHT_ARROW', 'dpad_west': 'LEFT_ARROW'}
EITHER_STICK_OUT = (1 << 30) | (1 << 31)
# The modifier buttons, which Menu Keys closes: the bumpers, or the triggers' soft pull.
MODIFIERS = {'default': [('switch', 'left_bumper'), ('switch', 'right_bumper')],
             'alternative': [('left_trigger', 'edge'), ('right_trigger', 'edge')]}


def touch_entry_point(pad):
    return f'{pad}: Touch Entry Point'


def chain(first, second):
    """The four layers of one chorded chain: its Entry Point, window, second-press layer and cover."""
    prefix = f'Menu {first}!{second}'
    return (f'{prefix}: Entry Point', f'{prefix}: Double Tap', f'{prefix}: {CHAINS[(first, second)][1]}',
            f'{prefix}: Double Tap Cover')


def original(second):
    """The Menu chain a chorded chain copies: the pressed button's own window, second-press layer and cover."""
    key = 'Tab' if second == 'Right' else 'Escape'
    return f'Menu {second}: Double Tap', f'Menu {second}: {key}', f'Menu {second}: Double Tap Cover'


NEW = ([touch_entry_point('RTP'), touch_entry_point('LTP'), PADS['LTP'][1]]
       + [title for sides in CHAINS for title in chain(*sides)] + [MENU_KEYS])


class PadBumpsAndMenuKeys:
    def layer(self, name):
        super().layer(name)
        if name == st.COVER:
            # After Gamepad, so no runtime ID shifts, and before the whole-layout
            # clear lists are generated.
            for title in NEW:
                super().layer(title)

    def build_menu(self):
        super().build_menu()
        for title in NEW:
            self.menu_helpers.remove(title)

    def build_touch_cleanup(self):
        # The new layers bring their own stick inputs, or get them from the required cleanups.
        everything = self.new
        self.new = [n for n in everything if n not in NEW]
        try:
            super().build_touch_cleanup()
        finally:
            self.new = everything

    # --- helpers ------------------------------------------------------------------------------

    def copy_layer(self, old, new, replace):
        """`new` gets a copy of every group of `old`, with the titles and keys in `replace` swapped."""
        for source, group in self.sources(old).items():
            inputs = json.loads(self.swap(json.dumps(group.get('inputs', {})), replace))
            self.group(new, source, inputs, group.get('settings', {}), group['mode'])

    @staticmethod
    def swap(text, replace):
        for old, new in replace.items():
            text = text.replace(old, new)
        return text

    def stored(self, layer, source, name, kind):
        """The commands of one single entry, as stored."""
        return self.m.commands(self.sources(layer)[source]['inputs'][name]['activators'][kind])

    # --- part 1: the bumps --------------------------------------------------------------------

    def build_handover(self, pad):
        """The hand-over layer: the Click Entry Point's two Soft Presses on the ring, with their settings.
        The inner one repeats, the outer one has the 5 ms delay. Whichever of the two the Click Entry
        Point would fire for a thumb at that spot, this layer fires the same one."""
        m = self.m
        source, entry, click_entry = PADS[pad]
        name = touch_entry_point(pad)
        handover = m.seq(m.op('remove', name), m.op('add', entry))
        centre, outer = self.sources(click_entry)[source]['inputs']['edge']['activators']['Soft_Press']
        if centre['settings'].get('edge_binding_invert') != '1' or 'delay_start' in centre['settings'] \
                or centre['settings'].get('hold_repeats') != '1' or outer['settings'].get('delay_start') != '5' \
                or 'edge_binding_invert' in outer['settings']:
            raise ValueError(f'{click_entry}: expected the repeating centre bind and the delayed outer one, '
                             f'found {centre["settings"]} and {outer["settings"]}')
        self.group(name, source, {
            'edge': m.inp(Soft_Press=[
                m.entry(handover, **{**centre['settings'], 'haptic_intensity': BUMP_HAPTIC}),
                m.entry(handover, **{**outer['settings'], 'haptic_intensity': 0})]),
            # A thumb that lifts before the hand-over.
            'touch': m.inp(release=m.entry(m.op('remove', name), haptic_intensity=0))},
            {'requires_click': '0'}, 'dpad')

    def entry_click(self, click):
        """The click's add, for an Entry Point. The pad can already be pressed when the Entry Point lands,
        after the touch's hand-over, and an immediate add doesn't fire then (A5). A repeating one fires on
        its next repeat (A6; author, 2026-10-04). On a press after the landing it fires at once."""
        click = copy.deepcopy(click)
        click['activators']['Soft_Press'].setdefault('settings', {}).update(
            hold_repeats='1', repeat_rate=str(CLICK_REPEAT_MS))
        return click

    def build_right_pad(self):
        m = self.m
        source, entry, click_entry = PADS['RTP']
        base = self.patch('Base', source)['inputs']
        touch = base['touch']['activators']['Full_Press']
        if m.commands(touch) != [m.op('add', entry)]:
            raise ValueError(f'Base {source} touch: expected the add of {entry}, found {m.commands(touch)}')
        touch['bindings']['binding'] = m.op('add', touch_entry_point('RTP'))
        click = base.pop('click')
        if self.stored('Base', source, 'touch', 'Full_Press') and m.commands(click['activators']['Soft_Press']) != [
                m.op('add', click_entry)]:
            raise ValueError(f'Base {source} click: expected the add of {click_entry}, found {click}')
        # The layers whose pad is a mouse without a click took Base's. The Tap Cover has the Entry Point under it.
        for layer in (entry, STEERING):
            inputs = self.sources(layer)[source]['inputs']
            if 'click' in inputs:
                raise ValueError(f'{layer} {source}: a click is already bound')
            inputs['click'] = self.entry_click(click) if layer == entry else copy.deepcopy(click)
        self.build_handover('RTP')

    def build_left_pad(self):
        m = self.m
        source, entry, click_entry = PADS['LTP']
        old = self.sources('Base')[source]
        if old['mode'] != '2dscroll' or sorted(old['inputs']) != sorted(SWIPES + ('click',)):
            raise ValueError(f'Base {source}: expected the swipe pad with its click, found {old["mode"]} {list(old["inputs"])}')
        inputs = copy.deepcopy(old['inputs'])
        for direction in SWIPES:
            swipe = inputs[direction]['activators']['Full_Press']
            (add,) = m.commands(swipe)
            swipe['bindings']['binding'] = m.seq(m.op('remove', entry), add)
        # Swipe mode may give no touch Release (author). The swipes and the cleanup functions
        # end the layer without one.
        inputs['touch'] = m.inp(release=m.entry(m.op('remove', entry), haptic_intensity=0))
        inputs['click'] = self.entry_click(inputs['click'])
        self.group(entry, source, inputs, {k: v for k, v in old.get('settings', {}).items() if k != 'layer'}, old['mode'])
        self.group('Base', source, {'touch': m.full(m.op('add', touch_entry_point('LTP')), hold_repeats=1,
                                                    haptic_intensity=0, interruptable=0)},
                   {'requires_click': '0', 'haptic_intensity_override': '0'}, 'dpad')
        self.changed.append(('Base', source))
        self.build_handover('LTP')
        # The click layers' thumb lift also ends the Entry Point under them.
        for layer in (click_entry, 'LTP: Middle Click', 'LTP: Arrow Keys'):
            release = self.sources(layer)[source]['inputs']['touch']['activators']['release']
            release['bindings']['binding'] = [m.op('remove', entry)] + m.commands(release)

    # --- part 2 --------------------------------------------------------------------------------

    def build_middle_click_mouse(self):
        group = self.sources(MIDDLE)['right_trackpad']
        if group['mode'] != 'single_button' or sorted(group['inputs']) != ['click', 'touch']:
            raise ValueError(f'{MIDDLE}: expected a single button with its click and touch, found {group["mode"]}')
        group['mode'] = self.sources('Base')['right_trackpad']['mode']

    # --- part 5 --------------------------------------------------------------------------------

    def build_tap_cover_resets(self):
        m = self.m
        for prefix, source in (('LST', 'joystick'), ('RST', 'right_joystick'), ('RTP', 'right_trackpad')):
            touch = self.sources(f'{prefix}: Entry Point')[source]['inputs']['touch']['activators']
            cover = m.op('add', f'{prefix}: Tap Cover')
            if sorted(touch) != ['chord', 'release'] or m.commands(touch['chord']) != [cover] \
                    or touch['chord']['settings'].get('delay_start') != str(TAP_COVER_MS):
                raise ValueError(f'{prefix}: Entry Point touch: expected the Release and the delayed cover, found {touch}')
            touch['Full_Press'] = m.entry(m.op('remove', f'{prefix}: Tap Cover'), hold_repeats=1,
                                          repeat_rate=TAP_COVER_MS + 50, interruptable=0)

    # --- part 3: Menu Keys ---------------------------------------------------------------------

    def build_chain(self, first, second):
        m = self.m
        entry, window, held, cover = chain(first, second)
        key, _, old_key, _ = CHAINS[(first, second)]
        first_button, first_legacy, _ = st.MENU[first]
        second_button = st.MENU[second][0]
        plain, fn = st.entry_point(first), st.fn_layer(first)

        # The plain Entry Point adds the new one wherever it adds the Fn layer, to run just after it.
        fn_add = '{{Base::' + fn + '}}'
        found = 0
        for group in self.sources(plain).values():
            for binding in group.get('inputs', {}).values():
                for _, e in m.entries(binding):
                    commands = m.commands(e)
                    at = [i for i, c in enumerate(commands) if 'add_layer ' + fn_add in c]
                    if at:
                        e['bindings']['binding'] = commands[:at[0]] + [m.op('add', entry)] + commands[at[0]:]
                        found += 1
        if found != 4:
            raise ValueError(f'{plain}: expected four adds of {fn}, found {found}')

        # What the first button's Release leaves behind, as the Fn layer stores it.
        family = self.stored(fn, 'switch', first_button, 'release')

        # The Entry Point: the Menu chain's parent, for the second button. Its hold clears the stack.
        everything = self.clear([n for n in self.by_title if n not in ('Base', MENU_KEYS)])
        self.group(entry, 'switch', {second_button: m.inp(
            release=m.entry(m.seq(m.op('remove', entry), m.op('add', window)), haptic_intensity=0),
            chord=m.entry(m.seq(*everything, m.op('add', MENU_KEYS, beep=1)), chord_button=first_legacy,
                          delay_start=HOLD_MS, haptic_intensity=st.COMMIT_HAPTIC),
            Full_Press=m.entry(m.op('remove', MENU_KEYS), hold_repeats=1, repeat_rate=HOLD_MS + 50,
                               interruptable=0))})
        # Its sticks are the Fn layer's, in the same mode, so the directions still come through.
        # The edge cleanup also removes this layer; the touch gets its cleanup with the others.
        for source in st.STICKS.values():
            below = self.sources(fn)[source]
            edge = copy.deepcopy(below['inputs']['edge'])
            cleanup = edge['activators']['Full_Press']
            cleanup['bindings']['binding'] = m.commands(cleanup) + [m.op('remove', entry)]
            self.group(entry, source, {'edge': edge, 'touch': copy.deepcopy(below['inputs']['touch'])},
                       below.get('settings', {}), below['mode'])

        # The window, the second-press layer and the cover are the pressed button's own, with this key.
        # They keep the blocks that stop a layer landing on them (R136).
        olds = original(second)
        replace = {'{{Base::' + old + '}}': '{{Base::' + new + '}}' for old, new in zip(olds, (window, held, cover))}
        replace[m.key(old_key)] = m.key(key)
        for old, new in zip(olds, (window, held, cover)):
            self.copy_layer(old, new, replace)
        # The window sits on the Fn layer, whose D-pad has cleanup functions: the fix pipeline needs a
        # group to write that block into (R140).
        self.group(window, 'dpad', {}, self.base_groups['dpad'].get('settings', {}))
        # The first button is held under the window and the second-press layer, which block it. Its
        # Release there ends its own family, the window first.
        for layer, first_out in ((window, [m.op('remove', window)]), (held, [])):
            block = self.sources(layer)['switch']['inputs'][first_button]
            if m.commands(block['activators']['Full_Press']) != [m.EMPTY] or len(list(m.entries(block))) != 1:
                raise ValueError(f'{layer} {first_button}: expected an empty block, found {block}')
            block['activators']['release'] = m.entry(family + first_out, haptic_intensity=0)
        # The second-press layer and its cover keep the right stick in the Fn layer's mode. In Base's
        # mouse mode they would hide the Entry Point's right-stick click, a transition gesture (A2).
        below = self.sources(fn)['right_joystick']
        kept = self.sources(held)['right_joystick']['inputs']
        self.group(held, 'right_joystick', kept, below.get('settings', {}), below['mode'])
        self.group(cover, 'right_joystick', {'touch': copy.deepcopy(below['inputs']['touch'])},
                   below.get('settings', {}), below['mode'])
        # The Fn layer's own Release of the first button also ends the new Entry Point above it.
        release = self.sources(fn)['switch']['inputs'][first_button]['activators']['release']
        release['bindings']['binding'] = m.commands(release) + [m.op('remove', entry)]

    def build_menu_keys(self):
        m = self.m
        leave = dict(gyro_ratchet_button_mask=EITHER_STICK_OUT, gyro_ratchet_button_requireany_or_all=0,
                     interruptable=0)

        def keyed(keys):
            # A stick out plus the button leaves. The chord keeps this layer's key from being typed (A27),
            # and the press then counts as Base's, which the removal exposes (A11).
            return {name: m.inp(Full_Press=m.entry(m.key(key)),
                                chord=m.entry(m.op('remove', MENU_KEYS, beep=1), **leave))
                    for name, key in keys.items()}

        base = self.base_groups
        self.group(MENU_KEYS, 'button_diamond', keyed(FACE), base['button_diamond'].get('settings', {}))
        self.group(MENU_KEYS, 'dpad', keyed(ARROWS), base['dpad'].get('settings', {}))
        # Start and Select are blocked: no Entry Point, so no Double Tap window can land on this layer.
        # A window there would have to clear the face buttons and the D-pad on every stack (R140).
        switches = {button: m.full() for button, _, _ in st.MENU.values()}
        for source, name in MODIFIERS[self.variant]:
            if source == 'switch':
                switches[name] = m.full()
            else:
                self.group(MENU_KEYS, source, {name: m.full()}, base[source].get('settings', {}), base[source]['mode'])
        self.group(MENU_KEYS, 'switch', switches)
        # A menu button held plus a stick click: Gamepad's exit chord, the Entry Points' clear and the
        # clear transition (R158, without Entry Points).
        clear = self.sources(tc.gp.GAMEPAD)['joystick']['inputs']['click']['activators']['chord']
        if clear['settings'].get('gyro_ratchet_button_mask') != str(st.MENU_ANY):
            raise ValueError(f'{tc.gp.GAMEPAD}: expected the exit chord on either menu button, found {clear["settings"]}')
        for source, (other, radius) in cg.STICKS.items():
            click = base[source]['inputs']['click']['activators']['Full_Press']
            self.group(MENU_KEYS, source, {
                # Both sticks out: Cursor Gyro's exit, a cancellation (R135).
                'edge': m.inp(chord=m.entry(
                    m.op('remove', MENU_KEYS, beep=1), gyro_ratchet_button_mask=1 << other,
                    gyro_ratchet_button_requireany_or_all=1, hold_repeats=1, interruptable=0, haptic_intensity=0)),
                'click': m.inp(Full_Press=m.entry(click['bindings']['binding']), chord=copy.deepcopy(clear)),
                # No stick-touch helper, so no stick-touch window, lands on this layer.
                'touch': m.full()},
                {'edge_binding_radius': radius, 'edge_binding_invert': '0'})

    def build_chain_cleanups(self, data):
        """The chain layers sit on the Fn layer and block inputs it has cleanup functions on. They get
        their own (R171) here, before the fix pipeline reads them: its hidden-cleanup step (R130)
        copies a layer's cleanup and has none to copy from a layer that is only blocks."""
        layers = {title for sides in CHAINS for title in chain(*sides)[2:]}
        fixes = rc.Fixes(data)
        for row in rc.required.missing(fixes.c, only=layers):
            fixes.fix(*row)
        skipped = [line for line in fixes.log if 'NOT TRIALLED' in line]
        if skipped:
            raise ValueError(skipped)
        self.chain_log = fixes.log

    def finish(self):
        data = super().finish()
        self.build_middle_click_mouse()
        self.build_tap_cover_resets()
        self.build_right_pad()
        self.build_left_pad()
        for first, second in CHAINS:
            self.build_chain(first, second)
        self.build_menu_keys()
        self.build_chain_cleanups(data)
        return data


class Release:
    def finish(self):
        data = super().finish()
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('required cleanups candidate', 'pad bumps and menu keys candidate').replace(
            'tap cover stick touches candidate', 'pad bumps and menu keys candidate')
        cm['description'] = (
            'Pad bumps and Menu Keys candidate; device verification pending. A pad touch bumps where a click '
            'would be the centre click; both menu buttons held enter Menu Keys. '
            'See findings/2026-10-04-pad-bumps-and-menu-keys/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    # The required cleanups run last, over the new layers.
    return type('Concrete', (Release, rc.RequiredCleanups, PadBumpsAndMenuKeys, type(tc.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-bumps-and-menu-keys'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'required_cleanups_generator_sha256': hashlib.sha256(REQUIRED.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': NEW, 'new_layer_count': len(NEW),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED',
            'ranges': {'bump_centre_radius': cg.pc.CENTRE_RADIUS},
            'timing_ms': {'handover_inner_repeat': cg.pc.ADD_REPEAT_MS, 'handover_outer_delay': 5,
                          'click_add_repeat': CLICK_REPEAT_MS,
                          'menu_keys_hold': HOLD_MS, 'tap_cover_reset': TAP_COVER_MS + 50}}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers, '
              f'{b.required_inputs} inputs given a cleanup')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
