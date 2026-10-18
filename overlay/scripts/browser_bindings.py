"""Visible inherited labels and the draggable slow-motion control."""

FACE_CONTROLS = tuple('button_diamond/button_' + c for c in ('a', 'y', 'x', 'b'))


def face_labels(state):
    return [state['binding_labels'][control] for control in FACE_CONTROLS]


def slider(browser):
    browser.click('reset')
    start, end = browser.point('speed:1'), browser.point('speed:7')
    browser.actions([
        {'type': 'pointerMove', 'x': round(start[0]), 'y': round(start[1]), 'duration': 0},
        {'type': 'pointerDown', 'button': 0},
        {'type': 'pointerMove', 'x': round(end[0]), 'y': round(end[1]), 'duration': 150},
        {'type': 'pointerUp', 'button': 0},
    ])
    browser.wait(lambda: browser.snapshot()['scale'] == 7, 'slider drags to an intermediate speed')
    control = 'switch/left_bumper'
    browser.sequence([(0, control, 'mousedown', 0, 0),
                      (700, control, 'mousemove', 0, 0),
                      (0, control, 'mouseup', 0, 0)])
    frames = browser.js('return demoSequenceFrames')
    assert abs(frames[1]['timeline']['progress'] - .5) < .01, frames[1]['timeline']
    assert abs(frames[1]['timeline']['remaining_ms'] - 700) <= 7
    browser.click('reset'); browser.click('speed:1')
    browser.wait(lambda: browser.snapshot()['scale'] == 1, 'slider returns to normal speed')
    print('PASS: draggable 1–10× slider supports intermediate speeds on the shared lifecycle clock', flush=True)


def inherited(browser, index):
    owner = 'left_trigger/edge' if index % 2 else 'switch/left_bumper'
    for scale in (1, 10):
        browser.click('reset'); browser.click(f'speed:{scale}')
        browser.sequence([(0, owner, 'mousedown', 0, 0),
                          (210*scale, owner, 'mousemove', 0, 0)])
        initial, held = browser.js('return demoSequenceFrames')
        assert any(t.endswith('Temp Cursor Gyro') for t in held['demo']['stack']), held['demo']['stack']
        for state in (initial, held):
            assert face_labels(state) == list('GTZX'), state['binding_labels']
            assert state['demo']['output']['text'] == '', 'Rendering a binding must not execute it'
        # Latch the owner so a second mouse press can exercise the displayed binding.
        browser.click(owner, button=2)
        for offset, control in enumerate(FACE_CONTROLS):
            browser.click(control)
            browser.wait(lambda: browser.snapshot()['demo']['output']['text'] == 'gtzx'[:offset+1],
                         'displayed inherited face-button output')
            browser.wait(lambda: face_labels(browser.snapshot()) == list('GTZX'), 'cover keeps all inherited labels visible')
        browser.click(owner, button=2)
        browser.wait(lambda: face_labels(browser.snapshot()) == list('FRCV'), 'release restores all base labels')
    browser.click('reset'); browser.click('speed:1')

