"""Regression checks for CI delays without weakening slow-motion assertions."""
from copy import deepcopy
import json
import subprocess
import unittest

from browser_gesture_timing import START_TRACE, STOP_TRACE, check_stage


def hold_trace():
    result = []
    # The driver only retrieves the trace long after the 2-second hold ends.
    for clock, phase in ((100, 'pressed'), (150, 'pressed'), (300, 'hold'), (800, 'hold')):
        active = phase == 'pressed'
        result.append({
            'at_ms': clock * 10 + 5000,
            'clock_ms': clock,
            'scale': 10,
            'lanes': [{'phase': phase, 'started_ms': 100 if active else 300,
                       'deadline_ms': 300 if active else None}],
            'timeline': {'active': True, 'text': 'Mod 0 :: Scroll down', 'phase': phase,
                         'progress': (clock - 100) / 200 if active else 1,
                         'remaining_ms': (300 - clock) * 10 if active else None},
        })
    return result


class GestureTimingTests(unittest.TestCase):
    def test_recorder_uses_rendered_clock_and_captures_completion_before_next_animation(self):
        # The input poll has already advanced to hold while the UI still paints
        # pressed. Then the UI completes before the recorder's next rAF callback.
        # Run the actual injected JS, without a browser or wall-clock sleeps.
        script = r'''
          const {start, stop} = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
          const value = {state: {status: 'live', gestures: {clock_ms: 999}},
            rendered_state: {status: 'live', timing_scale: 10,
              gestures: {clock_ms: 95, lanes: [{phase: 'pressed'}]}},
            timeline: {clock_ms: 100}, rendered_control_labels: ['rendered']};
          global.window = {keybindApp: {diagnostic_snapshot: () => JSON.stringify(value)}};
          global.requestAnimationFrame = () => 1;
          global.cancelAnimationFrame = () => {};
          new Function(start)(false);
          value.rendered_state.gestures.lanes[0].phase = 'hold';
          value.timeline.clock_ms = 300;
          const samples = new Function(stop)();
          const assert = require('node:assert/strict');
          assert.deepEqual(samples.map(s => s.clock_ms), [100, 300]);
          assert.deepEqual(samples.map(s => s.lanes[0].phase), ['pressed', 'hold']);
          assert.deepEqual(samples[0].control_labels, ['rendered']);
          assert.equal(window.viewerGestureTrace, undefined);
        '''
        subprocess.run(['node', '-e', script], check=True, text=True,
                       input=json.dumps({'start': START_TRACE, 'stop': STOP_TRACE}))

    def test_late_driver_response_does_not_require_transient_phase_to_still_be_active(self):
        check_stage(hold_trace(), 0, 'pressed', 200, 10, completed='hold')

    def test_unscaled_clock_still_fails_despite_correct_declared_scale_and_logical_deadline(self):
        samples = hold_trace()
        for sample in samples:
            sample['at_ms'] = sample['clock_ms'] + 5000
        with self.assertRaisesRegex(AssertionError, 'wrong speed'):
            check_stage(samples, 0, 'pressed', 200, 10, completed='hold')

    def test_stalled_progress_and_countdown_are_not_hidden_by_eventual_completion(self):
        for field in ('progress', 'remaining_ms'):
            with self.subTest(field=field):
                samples = hold_trace()
                samples[1]['timeline'][field] = samples[0]['timeline'][field]
                with self.assertRaises(AssertionError):
                    check_stage(samples, 0, 'pressed', 200, 10, completed='hold')

    def test_missing_start_or_completion_is_not_treated_as_success(self):
        for samples in (hold_trace()[2:], hold_trace()[:2]):
            with self.assertRaises(AssertionError):
                check_stage(samples, 0, 'pressed', 200, 10, completed='hold')

    def test_completed_phase_must_start_at_the_original_deadline(self):
        samples = hold_trace()
        samples[-1]['lanes'][0]['started_ms'] = 120
        with self.assertRaisesRegex(AssertionError, 'wrong logical deadline'):
            check_stage(samples, 0, 'pressed', 200, 10, completed='hold')

    def test_release_window_can_be_observed_before_a_second_press_ends_it(self):
        samples = deepcopy(hold_trace()[:2])
        for sample in samples:
            sample['lanes'][0].update(phase='window', deadline_ms=250)
            sample['timeline'].update(phase='window', progress=(sample['clock_ms'] - 100) / 150,
                                      remaining_ms=(250 - sample['clock_ms']) * 10)
        check_stage(samples, 0, 'window', 150, 10)
