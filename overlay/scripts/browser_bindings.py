"""Visible inherited labels and the draggable slow-motion control."""


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
    button = 'button_diamond/button_a'
    browser.click('reset'); browser.click('speed:10')
    browser.sequence([(0, owner, 'mousedown', 0, 0),
                      (2100, owner, 'mousemove', 0, 0)])
    held = browser.js('return demoSequenceFrames')[1]
    assert any(t.endswith('Temp Cursor Gyro') for t in held['demo']['stack']), held['demo']['stack']
    assert held['binding_labels'][button] == 'G', held['binding_labels']
    assert held['demo']['output']['text'] == '', 'Rendering a binding must not execute it'
    # Latch the owner so a second mouse press can exercise the displayed binding.
    browser.click(owner, button=2)
    browser.click(button)
    browser.wait(lambda: browser.snapshot()['demo']['output']['text'] == 'g', 'displayed inherited G output')
    browser.wait(lambda: browser.snapshot()['binding_labels'][button] == 'G', 'cover keeps inherited G visible')
    browser.click(owner, button=2)
    browser.wait(lambda: browser.snapshot()['binding_labels'][button] == 'F', 'release restores base F label')
    browser.click('reset'); browser.click('speed:1')

