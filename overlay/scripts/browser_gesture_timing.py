"""Observe rendered gestures in the browser, independent of driver latency."""

START_TRACE = r"""
if (window.viewerGestureTrace) cancelAnimationFrame(window.viewerGestureTrace.frame);
const mouseOnly = arguments[0];
const trace = window.viewerGestureTrace = {samples: [], frame: null};
trace.capture = () => {
    const value = JSON.parse(window.keybindApp.diagnostic_snapshot());
    const state = value.rendered_state;
    if (state && (mouseOnly ? value.mouse_preview : state.status === 'live')) {
        trace.samples.push({
            at_ms: performance.now(),
            clock_ms: value.timeline.clock_ms,
            scale: state.timing_scale,
            lanes: state.gestures.lanes,
            timeline: value.timeline,
            control_labels: value.rendered_control_labels,
        });
        if (trace.samples.length > 4096) trace.samples.shift();
    }
};
function sample() {
    trace.capture();
    trace.frame = requestAnimationFrame(sample);
}
sample();
"""

STOP_TRACE = r"""
const trace = window.viewerGestureTrace;
// A driver read can see the completed render before our next animation-frame
// callback. Include that final frame when stopping instead of losing it.
trace.capture();
cancelAnimationFrame(trace.frame);
delete window.viewerGestureTrace;
return trace.samples;
"""


class GestureTrace:
    def __init__(self, js):
        self.js = js

    def start(self, mouse_only=True):
        self.js(START_TRACE, mouse_only)

    def stop(self):
        return self.js(STOP_TRACE)


def check_stage(samples, lane, phase, duration, scale, completed=None):
    """Check a captured stage and its clock; never sample a moving phase via HTTP."""
    active = [value for value in samples if value['lanes'][lane]['phase'] == phase]
    observed = list(dict.fromkeys(value['lanes'][lane]['phase'] for value in samples))
    assert len(active) >= 2, f'Browser did not render enough {phase} frames; observed {observed}'
    first, last = active[0], active[-1]
    for value in active:
        state, timeline = value['lanes'][lane], value['timeline']
        assert value['scale'] == scale, f'{phase} used the wrong timing scale'
        assert state['deadline_ms'] - state['started_ms'] == duration, \
            f'{phase} used the wrong logical duration'
        assert timeline['active'] and timeline['text'], f'{phase} timeline was blank'
        assert timeline['phase'] == phase, f'{phase} timeline and input disagree'
        assert 0 <= timeline['progress'] <= 1, f'{phase} progress is out of range'
        expected = max(0, state['deadline_ms'] - value['clock_ms']) * scale
        assert abs(timeline['remaining_ms'] - expected) <= scale, \
            f'{phase} countdown and rendered clock disagree: {timeline["remaining_ms"]} != {expected}'
    assert last['timeline']['progress'] > first['timeline']['progress'], \
        f'{phase} timeline did not advance'
    assert last['timeline']['remaining_ms'] < first['timeline']['remaining_ms'], \
        f'{phase} countdown did not advance'

    end = last
    if completed:
        finished = [value for value in samples if value['lanes'][lane]['phase'] == completed]
        assert finished, f'{phase} never reached {completed}'
        # A completed hold no longer needs repainting. Later rAF reads may
        # repeatedly observe that same frame while WebDriver is still waiting.
        end = finished[0]
        assert all(value['lanes'][lane]['started_ms'] == first['lanes'][lane]['deadline_ms']
                   for value in finished), \
            f'{phase} completed at the wrong logical deadline'
        assert end['timeline']['active'] and end['timeline']['progress'] == 1, \
            f'{completed} timeline is incomplete'
    # Both clocks are captured on the browser's animation frames. Time spent
    # waiting for WebDriver responses cannot change which frames we inspect.
    wall_ms = end['at_ms'] - first['at_ms']
    logical_ms = end['clock_ms'] - first['clock_ms']
    assert logical_ms > 0 and wall_ms > 0, f'{phase} clock did not advance'
    assert abs(wall_ms - logical_ms * scale) <= 150, \
        f'{phase} clock ran at the wrong speed: wall={wall_ms:.0f}ms, logical={logical_ms}ms, scale={scale}'
