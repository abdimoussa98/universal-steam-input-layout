"""The required cleanups: every layer has the cleanup functions R169 to R171 ask for.

Extends the 10-04 Tap Cover builder; it stays frozen. The rules are the author's of
2026-10-04, and so are the five decisions (suggested-fixes.md):

1. A full-pull block that covers nothing stays, and gets a guard and a cleanup.
2. `RTP: Tap Cover` gets a right-stick group in mouse mode for its touch cleanup. Over a
   menu Entry Point or the right stick guard it hides their right-stick click and edge.
3. In the Steering W and S layers the bind that adds the Modifier 2 layer moves into the
   guard chord; the cleanup is the Regular Press.
4. The left edge of the two Steering stick covers is guarded by either driver.
5. The stick guards keep inheriting L1 and R1 from the Entry Point under them.

`Fixes` reads the layout after the fix pipeline, as the install leaves it, and gives every
input the Cleanup audit names one of seven shapes, by what the input holds:

    nothing (open)              touch: the stick-touch Release, the guard chord, the cleanup
                                edge: the guard chord and the cleanup; the group states its edge radius
    a Release only              the guard chord and the cleanup beside it
    an owner chord already      the cleanup beside it (the menu Entry Points)
    an empty block              the guard chord and the cleanup
    a Regular Press output      the output moves into the guard chord; the cleanup is the Regular Press
    a Regular Press and a Release (the Steering W and S layers' other driver)
                                the Regular Press becomes the guard chord; the cleanup is the Regular Press

The guard is one chord, Any, not interruptible: the buttons of the layer's other cleanup
functions, else the buttons that keep it on. The Steering stick layers take the drivers; the
stick modifiers' right edge takes their two "driver and left stick out" chords; the Entry Guard
and the Fallback Hold take the left stick being out. The two Steering stick windows type Tab
and Escape themselves, because the W and S layers' Start and Select now hold a layer command
(R140). The `cleanup_lists` fix then fills the new lists (R128, R129).
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
from tools.audit_command_budget import audit_layout                          # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402
from steam_layout import exceptions, required_cleanups as required          # noqa: E402
from steam_layout.cleanups import Cleanups, name as button                  # noqa: E402
from steam_layout.fixes import apply_all, cleanup_lists                     # noqa: E402
from steam_layout.model import EMPTY, Layout, entries                       # noqa: E402

TAP_COVER = ROOT / 'findings/2026-10-04-tap-cover-stick-touches/build_candidate.py'
spec = importlib.util.spec_from_file_location('tap_cover_stick_touches', TAP_COVER)
tc = importlib.util.module_from_spec(spec); spec.loader.exec_module(tc)
st = tc.st

TRIO = {"joystick": "LST", "right_joystick": "RST"}
PARTS = ("Entry Point", "Tap Cover", "Temporary Gyro")
MODE = {"joystick": "dpad", "right_joystick": "joystick_mouse"}             # Base's, so the directions still come through
RADIUS = {"joystick": "4915", "right_joystick": "7209"}                     # the modifiers' edge radius
LS_OUT = {"gyro_ratchet_button_mask": str(1 << 30), "gyro_ratchet_button_requireany_or_all": "0"}
STICK_KEPT = ("Steering | LS: Entry Guard", "Steering | LS: Fallback Hold")
PADS = {"LTP": 19, "RTP": 20}                                               # a thumb on the pad, as a chord mask bit
MENU = ("button_escape", "button_menu")
BLOCK = EMPTY + ", , "                                                      # an empty binding, as the layouts store it


def chord_settings(activators):
    return [{k: v for k, v in e.get("settings", {}).items() if k.startswith(("gyro_ratchet", "chord_button"))}
            for kind, e in entries(activators) if kind == "chord"]


class Fixes:
    """Gives every input the three checks name a cleanup function, in place. `log` says what changed."""

    def __init__(self, data, keep_blocks=True):
        self.data = data
        self.keep_blocks = keep_blocks                      # decision 1: a block that covers nothing stays
        self.like = "{{" if "{{Base::" in json.dumps(data["controller_mappings"]["preset"][0]) or "{{" in json.dumps(
            data["controller_mappings"]["group"]) else ""  # the reference style of the removals it writes
        self.layout = Layout(data)
        self.c = Cleanups(self.layout)
        self.cm = data["controller_mappings"]
        self.next_group = max(int(g["id"]) for g in self.cm["group"]) + 1
        self.log = []
        modifier = next(t for t in self.c.layers if t.startswith("Steering | LS Down: Modifier"))
        activators = self.layout.active(modifier)
        self.drivers = chord_settings(activators["joystick"]["inputs"]["touch"]["activators"])
        self.driver_and_stick = chord_settings(activators["button_diamond"]["inputs"]["button_a"]["activators"])

    # --- the guard and the list ---------------------------------------------------------------

    def guards(self, layer, control):
        """The guard chords' settings for one input of `layer`."""
        if layer in STICK_KEPT:
            return [LS_OUT]
        if self.c.keeper(layer)[0] == "inside":                         # the Steering stick modifiers and their covers
            return self.driver_and_stick if control == ("right_joystick", "edge") and "Modifier" in layer else self.drivers
        found = list(self.c.cleanups(layer))
        buttons = frozenset().union(*[g for _, g, _ in found]) if found else self.c.keeper(layer)[1]
        buttons = buttons - {button(control)} or buttons        # an input isn't guarded by its own button
        for t, guard, _ in found:                               # the layer's own one-chord guard, when it has one
            chords = chord_settings(self.layout.active(layer)[t.source]["inputs"][t.input]["activators"])
            if len(chords) == 1 and guard == buttons:
                return chords
        mask = cleanup_lists.chord_mask(buttons - set(PADS)) | sum(1 << PADS[pad] for pad in buttons & set(PADS))
        return [{"gyro_ratchet_button_mask": str(mask), "gyro_ratchet_button_requireany_or_all": "0"}]

    def removals(self, layer):
        """The layer's cleanup list, or itself alone: the `cleanup_lists` fix adds what R128 and R129 ask for."""
        lists = [[x for op, x in t.ops if op == "remove_layer"] for t, _, _ in self.c.cleanups(layer)]
        return max(lists, key=len) if lists else [layer]

    def cleanup(self, layer):
        return {"bindings": {"binding": [cleanup_lists.removal(self.layout, title, self.like) for title in self.removals(layer)]},
                "settings": {"hold_repeats": "1"}}

    def chords(self, layer, control, binding=BLOCK, settings=None):
        found = [{"bindings": {"binding": copy.deepcopy(binding)}, "settings": {**(settings or {}), **guard, "interruptable": "0"}}
                 for guard in self.guards(layer, control)]
        return found[0] if len(found) == 1 else found

    # --- the groups ---------------------------------------------------------------------------

    def group(self, layer, source):
        """The layer's group for a stick, made in Base's mode when it has none."""
        preset = self.layout.presets[layer]
        active = self.layout.active(layer)
        if source not in active:
            group = {"id": str(self.next_group), "mode": MODE[source], "name": "", "description": "", "inputs": {},
                     "settings": {"layer": "1"}}
            self.next_group += 1
            self.cm["group"].append(group)
            self.layout.groups[group["id"]] = group
            preset["group_source_bindings"][group["id"]] = f"{source} active"
            active[source] = group
            self.log.append(f"{layer}: a new {source} group in {MODE[source]} mode")
        return active[source]

    # --- one input ----------------------------------------------------------------------------

    def fix(self, check, layer, control, state, reason):
        source, name = control
        where = f"{layer} / {required.label(control)}"
        if check == required.BUTTON and reason == required.NOTHING and not self.keep_blocks:
            del self.layout.active(layer)[source]["inputs"][name]
            return self.log.append(f"{where}: the block is deleted (it covers nothing)")
        group = self.group(layer, source) if source in MODE else self.layout.active(layer)[source]
        slot = group.setdefault("inputs", {}).setdefault(name, {"activators": {}})
        old = slot["activators"]
        kinds = [kind for kind, _ in entries(old)]
        new = {"Full_Press": self.cleanup(layer)}
        if name == "edge" and source in MODE:
            group.setdefault("settings", {}).setdefault("edge_binding_radius", RADIUS[source])
            group["settings"].setdefault("edge_binding_invert", "0")
        if state == "open":
            new["chord"] = self.chords(layer, control)
            if name == "touch":
                new["release"] = {"bindings": {"binding": [cleanup_lists.removal(self.layout, f"{TRIO[source]}: {part}", self.like)
                                                           for part in reversed(PARTS)]},
                                  "settings": {"haptic_intensity": "0"}}
            shape = "the Release, a guard and the cleanup" if name == "touch" else "a guard and the cleanup"
        elif state == "empty":
            new["chord"] = self.chords(layer, control)
            shape = "a guard and the cleanup replace the block"
        elif "chord" in kinds and "Full_Press" not in kinds:           # an owner chord is already there
            new.update(old)
            new["Full_Press"] = self.cleanup(layer)
            shape = "the cleanup beside the owner's chord"
        elif kinds == ["release"]:
            new["chord"] = self.chords(layer, control)
            new["release"] = old["release"]
            shape = "a guard and the cleanup beside the Release"
        elif "Full_Press" in kinds and "chord" not in kinds and set(kinds) <= {"Full_Press", "release"}:
            press = old["Full_Press"]
            new["chord"] = self.chords(layer, control, press["bindings"]["binding"], press.get("settings"))
            if "release" in old:
                new["release"] = old["release"]
            shape = "the Regular Press becomes the guard chord; the cleanup is the Regular Press"
        else:
            return self.log.append(f"{where}: NOT TRIALLED, it holds {kinds}")
        slot["activators"] = new
        count = sum(1 for _ in entries(new))
        self.log.append(f"{where}: {shape} ({len(kinds)} -> {count} entries)")

    def windows(self):
        """The two Steering stick windows inherit Start and Select from the W and S layers. Those inputs get a
        cleanup, which is a layer command, so each window types the key itself (R140)."""
        driver = next(t for t in self.c.layers if t.startswith("Steering | ") and t.endswith("W Key"))
        keys = {name: copy.deepcopy(self.layout.active(driver)["switch"]["inputs"][name]) for name in MENU}
        for window in sorted(w for w in self.c.windows if w.startswith("Steering | LS")):
            inputs = self.layout.active(window)["switch"].setdefault("inputs", {})
            for name in MENU:
                if name not in inputs:
                    inputs[name] = copy.deepcopy(keys[name])
                    self.log.append(f"{window} / {required.label(('switch', name))}: types the key itself")

    def run(self, config):
        self.windows()
        variant = "alternative" if "alternative" in self.cm.get("title", "") else "default"
        decided = required.excepted(config, variant)
        rows = [row for row in required.missing(self.c)
                if (required.RULE[row[0]], row[1], "/".join(row[2])) not in decided]
        for row in rows:
            self.fix(*row)
        lists = cleanup_lists.fix(self.data, config)
        return len(rows), lists



class RequiredCleanups:
    def finish(self):
        data = super().finish()
        apply_all(data)                    # the frozen source predates every later fix; the checks read the fixed layout
        fixes = Fixes(data)
        self.required_inputs, _ = fixes.run(exceptions.load_config())
        self.required_log = fixes.log
        skipped = [line for line in fixes.log if 'NOT TRIALLED' in line]
        left = required.audit(Cleanups(Layout(data)), exceptions.load_config())
        if skipped or not left['ok']:
            raise ValueError(skipped or left['findings'])
        self.cm['title'] = self.cm['title'].replace('tap cover stick touches candidate', 'required cleanups candidate')
        self.cm['description'] = (
            'Required cleanups candidate; device verification pending. Every layer has a cleanup function on '
            'both stick touches, the stick edges and every button it retypes or blocks. See '
            'findings/2026-10-04-required-cleanups/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (RequiredCleanups, type(tc.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-required-cleanups'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'tap_cover_generator_sha256': hashlib.sha256(TAP_COVER.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {b.required_inputs} inputs, {len(b.required_log)} changes')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
