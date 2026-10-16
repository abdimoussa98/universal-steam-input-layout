"""Always On Double Tap windows: stick-touch exits and trackpad blocks."""
import json
from pathlib import Path
import re
import unittest

from tools.audit_inheritance import Layout, always_on_layers, bindings
from steam_layout.flow_model import resolve

ROOT = Path(__file__).resolve().parents[3]
LAYER_COMMAND = re.compile(r"controller_action (add_layer|remove_layer|hold_layer)\b")
SWIPES = {"dpad_west": "ESCAPE", "dpad_east": "RETURN", "dpad_north": "TAB", "dpad_south": "BACKSPACE"}
EMPTY = "controller_action empty_binding, , "


def load(variant):
    return json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text())


class DoubleTapWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {variant: Layout(load(variant)) for variant in ("default", "alternative")}
        cls.window_titles = {variant: tuple(always_on_layers(layout))
                             for variant, layout in cls.layouts.items()}

    def windows(self):
        for variant in ("default", "alternative"):
            layout = self.layouts[variant]
            windows = self.window_titles[variant]
            # The Always On layers are exactly the Double Tap windows, so none is skipped. In 90.31 and 90.32 the
            # fallback had a window of its own; 90.33 deleted it.
            double_taps = {title for title in layout.presets if title.endswith(": Double Tap")}
            self.assertEqual(set(windows), double_taps, variant)
            self.assertTrue(double_taps, variant)
            for title in windows:
                if title in double_taps:
                    yield variant, layout, title

    def test_stick_touch_release_removes_the_window_first_then_the_side_trio(self):
        for variant, layout, title in self.windows():
            for source, prefix in (("joystick", "LST"), ("right_joystick", "RST")):
                acts = layout.active(title)[source]["inputs"]["touch"]["activators"]
                if "release" not in acts:  # the window's own stick: second touch is the transition
                    self.assertIn(prefix, title)
                    continue
                with self.subTest(variant=variant, window=title, source=source):
                    stored = [layout.resolve(re.search(r"(\{\{.+?\}\}|\d+) 0 0", b).group(1))
                              for b in acts["release"]["bindings"]["binding"]]
                    executed = stored[::-1]
                    self.assertEqual(executed[0], title)
                    self.assertEqual(set(executed[1:]),
                                     {f"{prefix}: {n}" for n in ("Entry Point", "Tap Cover", "Temporary Gyro")})

    def test_left_pad_swipes_send_keys_without_the_layer_api(self):
        for variant, layout, title in self.windows():
            with self.subTest(variant=variant, window=title):
                group = layout.active(title)["left_trackpad"]
                inputs = group["inputs"]
                for direction, key in SWIPES.items():
                    self.assertEqual(list(bindings(inputs[direction]["activators"])), [f"key_press {key}, , "])
                # Click (Base: hold LTP: Arrow Keys) and touch (the key layers' own cleanup) are cleared.
                for name in ("click", "touch"):
                    self.assertEqual(list(bindings(inputs[name]["activators"])), [EMPTY], name)
                self.assertFalse([b for v in inputs.values() for b in bindings(v["activators"])
                                  if LAYER_COMMAND.search(b)])

    def test_rtp_double_tap_keeps_its_touch_selection_and_clears_the_fn_back_buttons(self):
        # Author, 2026-09-30: the window's dpad pad is its second-tap selection (north/south
        # scroll; anywhere else stays in mouse mode), so touch is not bound there.
        # Author, 2026-10-01: a source-mode change blocks inheritance, so Base's mouse-mode
        # touch doesn't reach the window's dpad pad; no traced_stacks decision is needed.
        from steam_layout.inheritance import check_stack
        targets = json.loads((ROOT / "steam_layout" / "traced_stacks.json").read_text())["targets"]
        self.assertNotIn("RTP: Double Tap", targets)
        for variant in ("default", "alternative"):
            layout = self.layouts[variant]
            groups = layout.active("RTP: Double Tap")
            with self.subTest(variant=variant):
                self.assertEqual(groups["right_trackpad"]["mode"], "dpad")
                self.assertNotIn("touch", groups["right_trackpad"]["inputs"])
                routes, blocked = check_stack(layout, "RTP: Double Tap", [layout.base])
                self.assertIn(("right_trackpad", "touch", "mode replaced"),
                              {(b["source"], b["input"], b["kind"]) for b in blocked})
                self.assertNotIn(("right_trackpad", "touch"), {(r["source"], r["input"]) for r in routes})
                for name in ("button_back_left", "button_back_right", "button_back_left_upper", "button_back_right_upper"):
                    self.assertEqual(list(bindings(groups["switch"]["inputs"][name]["activators"])), [EMPTY], name)

    def test_default_windows_keep_the_mouse_buttons_on_the_trigger_edges(self):
        # Gyro Off Ramp Up can sit under any window, and its soft pull removes it. That is a layer
        # command and no keybind, so the one possible keybind is Base's mouse button (since 90.10).
        # The Steering windows inherit it, because no ramp layer can be under them: from 90.13 to
        # 90.33 Steering blocked the right-stick edge, and since 90.35 a driver's press removes the
        # ramp layers before it adds its layer. In 90.34 neither held and they bound it themselves.
        layout = self.layouts["default"]
        for title in self.window_titles["default"]:
            for source, button in (("left_trigger", "LEFT"), ("right_trigger", "RIGHT")):
                with self.subTest(window=title, source=source):
                    if title.startswith("Steering | "):
                        self.assertNotIn("edge", layout.active(title).get(source, {}).get("inputs", {}))
                        kind, layer, edge, _ = resolve(layout, ("Base", "Steering", title), source, "edge")
                    else:
                        edge = layout.active(title)[source]["inputs"]["edge"]["activators"]
                    self.assertEqual(list(bindings(edge)), [f"mouse_button {button}, , "])
                    self.assertEqual(edge, layout.active("Base")[source]["inputs"]["edge"]["activators"])

    def test_alternative_steering_windows_keep_the_mouse_buttons_on_the_bumpers(self):
        # The windows inherit Base's mouse buttons. Before 90.13, and in 90.34, Turning Ramp Up 0
        # could be underneath and they bound them themselves. From 90.13 to 90.33 Steering blocked
        # the right-stick edge; since 90.35 a driver's press removes the ramp layers first.
        layout = self.layouts["alternative"]
        for title in ("Steering | LS Up: Double Tap", "Steering | LS Down: Double Tap"):
            for name, button in (("left_bumper", "LEFT"), ("right_bumper", "RIGHT")):
                with self.subTest(window=title, input=name):
                    self.assertNotIn(name, layout.active(title)["switch"]["inputs"])
                    kind, layer, acts, _ = resolve(layout, ("Base", "Steering", "Steering | R2: W Key", title),
                                                   "switch", name)
                    self.assertEqual(layer, "Base")
                    self.assertEqual(list(bindings(acts)), [f"mouse_button {button}, , "])

    def test_right_pad_stays_the_mouse_with_its_click_cleared_and_a_touch_release(self):
        # Author, 2026-09-30: the cursor keeps moving during a window, and the pad adds no layer.
        # RTP Double Tap keeps its own dpad selection pad. Since 90.28 the touch isn't an empty press
        # but a Release that ends the window first, as the stick touches have (author, 2026-10-04; R172).
        for variant, layout, title in self.windows():
            with self.subTest(variant=variant, window=title):
                group = layout.active(title)["right_trackpad"]
                if title == "RTP: Double Tap":
                    self.assertEqual(group["mode"], "dpad")
                    self.assertEqual(list(bindings(group["inputs"]["click"]["activators"])), [EMPTY])
                    continue
                base = layout.active("Base")["right_trackpad"]
                self.assertEqual(group["mode"], base["mode"])
                self.assertEqual(group["settings"], {"layer": "1"})  # mouse feel inherits from Base
                self.assertEqual(set(group["inputs"]), {"click", "touch"})
                self.assertEqual(list(bindings(group["inputs"]["click"]["activators"])), [EMPTY])
                touch = group["inputs"]["touch"]["activators"]
                self.assertEqual(list(touch), ["release"])
                removed = layout.layer_ops(touch["release"])
                self.assertEqual(removed[0], ("remove_layer", title))
                self.assertTrue(all(op == "remove_layer" for op, _ in removed))

if __name__ == "__main__":
    unittest.main()
