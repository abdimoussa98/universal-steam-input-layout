"""WebHID gesture checks whose input timing stays inside the browser."""
from browser_gesture_timing import GestureTrace, check_stage


def run_hid_timing_checks(*, snapshot, wait_for, click_target, js):
    def phase(lane):
        return snapshot()['rendered_state']['gestures']['lanes'][lane]['phase']

    def release(lane):
        js('fakeHid.device.frame(0)')
        def ready():
            state = snapshot()['state']
            return (state['gestures']['initialized']
                    and state['gestures']['lanes'][lane]['phase'] == 'idle'
                    and not any(state['input']['buttons']))
        wait_for(ready, 'HID gesture did not return to an initialized neutral state')

    click_target('timing-scale:slow')
    wait_for(lambda: snapshot()['state']['timing_scale'] == 10, 'Timing slider did not reach 10x')
    release(2)
    trace = GestureTrace(js)
    trace.start(mouse_only=False)
    js('fakeHid.device.frame(0x4000)')
    wait_for(lambda: phase(2) == 'hold', 'Slow Select hold never completed')
    samples = trace.stop()
    check_stage(samples, 2, 'pressed', 200, 10, completed='hold')
    active = [s for s in samples if s['lanes'][2]['phase'] in ('pressed', 'hold')]
    assert all(s['control_labels'][5] == 'Enter :: Menu' for s in active), \
        'Select lifecycle lost the forward Menu transition label'
    release(2)

    trace.start(mouse_only=False)
    # Keep all timed edges in the browser. HTTP polling between release and
    # repress used to consume the 1.5-second window on slower CI workers.
    js('''fakeHid.device.frame(0x40);
          setTimeout(() => fakeHid.device.frame(0), 200);
          setTimeout(() => fakeHid.device.frame(0x40), 800);''')
    wait_for(lambda: phase(3) == 'cover', 'Slow Start second hold never completed')
    samples = trace.stop()
    check_stage(samples, 3, 'pressed', 200, 10)
    check_stage(samples, 3, 'window', 150, 10)
    check_stage(samples, 3, 'second', 150, 10, completed='cover')
    active = [s for s in samples if s['lanes'][3]['phase'] == 'pressed']
    assert all(s['control_labels'][4] == 'Backspace :: Menu' for s in active), \
        'Start lifecycle lost the reverse Menu transition label'

    click_target('timing-normal')
    wait_for(lambda: snapshot()['state']['timing_scale'] == 1, 'Normal speed reset failed')
    wait_for(lambda: phase(3) == 'unknown', 'Speed change completed an already held gesture')
    release(3)
    print('PASS: WebHID 10x hold, release window and second hold; timeline clocks, speed reset and Menu labels')
