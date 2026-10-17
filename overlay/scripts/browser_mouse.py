"""Real pointer checks for the viewer's local controller rehearsal.

The browser smoke harness supplies WebDriver callbacks. These checks read the
rendered diagnostics, but never write simulated input into the application.
"""

from browser_gesture_timing import GestureTrace, check_stage


CONTROLS = (
    'a', 'b', 'x', 'y', 'select', 'start', 'up', 'right',
    'down', 'left', 'l3', 'r3', 'l1', 'r1', 'l2', 'r2',
)
OWNERS = {'l1': 0, 'r1': 1, 'select': 2, 'start': 3}


class MouseChecks:
    def __init__(self, *, snapshot, wait_for, click_target, hold_target,
                 release_pointer, actions, focus_change, js):
        self.snapshot = snapshot
        self.wait = wait_for
        self.click = click_target
        self.hold = hold_target
        self.release = release_pointer
        self.actions = actions
        self.focus_change = focus_change
        self.trace = GestureTrace(js)

    def phase(self, key):
        return self.snapshot()['state']['gestures']['lanes'][OWNERS[key]]['phase']

    def wait_phase(self, key, phase):
        self.wait(lambda: self.phase(key) == phase, f'Mouse {key}: missing {phase}')

    def idle(self):
        self.wait(lambda: not self.snapshot()['mouse_preview'], 'Mouse preview did not finish')
        value = self.snapshot()
        assert not any(value['state']['input']['buttons']), 'Mouse button remained held'
        assert value['state']['input']['triggers'] == [0, 0], 'Mouse trigger remained held'
        self.blank()

    def blank(self):
        self.wait(lambda: not self.snapshot()['timeline']['active'], 'Idle timeline stayed active')
        assert self.snapshot()['timeline']['text'] == '', 'Idle timeline must contain no text'

    def scale(self, slow):
        self.click('timing-scale:slow' if slow else 'timing-normal')
        expected = 10 if slow else 1
        self.wait(lambda: self.snapshot()['state']['timing_scale'] == expected,
                  f'Mouse timing scale did not become {expected}')

    def pin(self, key):
        x, y = self.snapshot()['ui_targets'][f'control:{key}']
        self.actions([
            {'type': 'pointerMove', 'duration': 0, 'x': round(x), 'y': round(y)},
            {'type': 'pointerDown', 'button': 2},
            {'type': 'pointerUp', 'button': 2},
        ])

    def all_buttons(self):
        self.blank()
        value = self.snapshot()
        targets = value['ui_targets']
        assert targets['timeline'][1] < min(targets[f'control:{key}'][1] for key in CONTROLS), \
            'Timeline must sit above the controller'
        for index, key in enumerate(CONTROLS):
            self.hold(f'control:{key}')
            self.wait(lambda: self.snapshot()['mouse_preview']
                      and self.snapshot()['state']['input']['buttons'][index],
                      f'Mouse cannot press {key}')
            value = self.snapshot()
            assert value['state']['input']['buttons'] == [n == index for n in range(16)], \
                f'Mouse {key} pressed another control'
            assert value['state']['held'] == [key == 'l1', key == 'r1']
            assert value['state']['input']['triggers'] == [
                1000 if key == 'l2' else 0, 1000 if key == 'r2' else 0,
            ], f'Mouse {key} has incorrect trigger travel'
            if key not in OWNERS:
                self.blank()
            self.release()
            self.idle()
        print('PASS: all 16 viewer buttons and triggers respond to real mouse press/release; idle timeline is blank and above the controller')

    def combinations(self):
        self.pin('l1')
        self.wait(lambda: self.snapshot()['state']['held'] == [True, False], 'Right-click did not pin L1')
        self.hold('control:a')
        self.wait(lambda: self.snapshot()['state']['input']['buttons'][0], 'Pinned L1 blocked a primary press')
        assert self.snapshot()['state']['held'] == [True, False], 'Primary press released pinned L1'
        assert self.snapshot()['labels'] == ['G', 'X', 'Z', 'T'], 'Pinned modifier bindings did not appear'
        self.release()
        self.wait(lambda: not self.snapshot()['state']['input']['buttons'][0], 'Primary release left A held')
        assert self.snapshot()['state']['held'] == [True, False], 'Primary release unpinned L1'
        self.pin('r1')
        self.wait(lambda: self.snapshot()['state']['held'] == [True, True], 'Right-click did not add pinned R1')
        assert self.snapshot()['labels'] == ['M', 'P', 'O', 'U'], 'Combined mouse modifier bindings did not appear'
        self.pin('l1')
        self.wait(lambda: self.snapshot()['state']['held'] == [False, True], 'Right-click did not unpin L1')
        self.pin('r1')
        self.idle()

        self.pin('l1')
        self.wait(lambda: self.snapshot()['state']['held'] == [True, False], 'Pinned focus-loss setup failed')
        self.focus_change()
        self.idle()
        print('PASS: right-click pinned modifiers combine with mouse buttons and each other, unpin cleanly and clear on focus loss')

    def hold_timing(self):
        self.hold('control:l1')
        self.wait_phase('l1', 'hold')
        assert self.snapshot()['timeline']['active'], 'Normal hold has no timeline'
        self.release()
        self.idle()

        self.scale(True)
        self.trace.start()
        self.hold('control:l1')
        self.wait_phase('l1', 'hold')
        check_stage(self.trace.stop(), 0, 'pressed', 200, 10, completed='hold')
        self.release()
        self.idle()

    def tap_then_hold(self):
        # Deliver tap + second hold in one real pointer action sequence. Driver
        # round trips must not consume the 1.5-second second-press window.
        x, y = self.snapshot()['ui_targets']['control:select']
        self.trace.start()
        self.actions([
            {'type': 'pointerMove', 'duration': 0, 'x': round(x), 'y': round(y)},
            {'type': 'pointerDown', 'button': 0},
            {'type': 'pointerUp', 'button': 0},
            {'type': 'pause', 'duration': 600},
            {'type': 'pointerDown', 'button': 0},
        ])
        self.wait_phase('select', 'cover')
        samples = self.trace.stop()
        check_stage(samples, 2, 'window', 150, 10)
        check_stage(samples, 2, 'second', 150, 10, completed='cover')
        self.release()
        self.idle()
        print('PASS: mouse normal and 10x hold, immediate tap, stretched release window, second hold and timeline progress/countdown')

    def cancellation(self):
        self.hold('control:a')
        self.wait(lambda: self.snapshot()['state']['input']['buttons'][0], 'Drag press missing')
        self.actions([{'type': 'pointerMove', 'duration': 0, 'x': 10, 'y': 10}])
        self.release()
        self.idle()

        # After an idle pause egui can show a tooltip as the pointer arrives.
        # The tooltip must not intercept the next controller press.
        self.actions([{'type': 'pause', 'duration': 1200}])
        self.hold('control:l1')
        self.wait(lambda: self.snapshot()['state']['held'][0], 'Focus-loss setup failed')
        self.focus_change()
        self.idle()
        # WebDriver still remembers its physical button state after focus loss.
        self.release()
        self.idle()

        self.pin('select')
        self.wait(lambda: self.snapshot()['state']['input']['buttons'][4], 'Mode-reset setup failed')
        self.click('mode:1')
        self.wait(lambda: self.snapshot()['state']['mode'] == 'steering', 'Mode change failed')
        self.idle()
        self.click('mode:0')
        self.wait(lambda: self.snapshot()['state']['mode'] == 'base', 'Base mode reset failed')

        self.pin('start')
        self.wait(lambda: self.snapshot()['state']['input']['buttons'][5], 'Speed-reset setup failed')
        self.scale(False)
        self.idle()
        self.scale(True)
        self.pin('l1')
        self.wait(lambda: self.snapshot()['state']['held'][0], 'Pinned speed-reset setup failed')
        self.scale(False)
        self.idle()
        # A fresh press after all reset paths must still start an ordinary gesture.
        self.hold('control:l1')
        self.wait_phase('l1', 'hold')
        self.release()
        self.idle()
        print('PASS: mouse release outside controls, real focus loss, mode/speed changes and fresh-press recovery')

    def connected_source(self):
        before = self.snapshot()['source_state']
        assert before['status'] == 'live', 'Connected-source mouse check needs a live fixture'
        assert not any(before['input']['buttons']), 'Connected-source fixture must start released'
        self.hold('control:a')
        self.wait(lambda: self.snapshot()['mouse_preview']
                  and self.snapshot()['state']['input']['buttons'][0],
                  'Live controller prevented mouse preview')
        value = self.snapshot()
        for field in ('input', 'mode', 'device', 'status'):
            assert value['source_state'][field] == before[field], \
                f'Mouse preview changed connected controller {field}'
        self.release()
        self.wait(lambda: not self.snapshot()['mouse_preview'], 'Mouse preview did not restore live source')
        value = self.snapshot()
        assert value['state']['input'] == before['input'], 'Mouse release changed physical input'
        assert value['state']['device'] == before['device'], 'Mouse release did not restore physical controller'
        self.hold('control:l1')
        self.wait_phase('l1', 'hold')
        assert not any(self.snapshot()['source_state']['input']['buttons']), \
            'Mouse timed gesture leaked to the physical source'
        self.release()
        self.wait(lambda: not self.snapshot()['mouse_preview'], 'Timed mouse preview did not restore live source')
        print('PASS: mouse previews and timed gestures coexist with a live input source without modifying its state')


def run_mouse_checks(**callbacks):
    checks = MouseChecks(**callbacks)
    checks.all_buttons()
    checks.combinations()
    checks.hold_timing()
    checks.tap_then_hold()
    checks.cancellation()


def run_mouse_source_checks(**callbacks):
    MouseChecks(**callbacks).connected_source()
