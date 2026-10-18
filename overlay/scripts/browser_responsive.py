"""Regression checks for viewport fit, visible output and the gyro threshold meter."""
import browser_viewer


def viewport(browser, width, height):
    browser.cdp('Emulation.setDeviceMetricsOverride', {
        'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': False})
    browser.point('controller')


def visible(state, names, width, height):
    for name in names:
        x, y, w, h = state['targets'][name]
        assert x-w/2 >= 0 and x+w/2 <= width, (name, state['targets'][name], width)
        assert y-h/2 >= 0 and y+h/2 <= height, (name, state['targets'][name], height)


def responsive(browser):
    browser.click('reset')
    browser.click('source'); browser.click('source:mouse')
    for width, height in ((1366, 768), (700, 900), (390, 844), (320, 740)):
        viewport(browser, width, height)
        for index in range(6):
            browser.click('layout'); browser.click(f'layout:{index}')
            browser.point('controller')
            state = browser.snapshot()
            browser_viewer.geometry(state)
            visible(state, ('controller', 'gyro', 'output-preview', 'layout', 'source',
                            'connect', 'pad-click', 'pause', 'reset'), width, height)
            controls = [k for k in state['targets'] if k.startswith(('switch/', 'button_diamond/', 'dpad/'))]
            visible(state, controls, width, height)
            before = {k: state['targets'][k] for k in ('controller', 'gyro', 'output-preview')}
            browser.click('button_diamond/button_a')
            browser.wait(lambda: browser.snapshot()['output_preview'][0].startswith('Typed: f ·'), 'visible typed output')
            assert before == {k: browser.snapshot()['targets'][k] for k in before}
            browser.click('reset')
            browser.wait(lambda: browser.snapshot()['output_preview'][0] == 'Last input: —', 'output reset')
        browser.click('layout'); browser.click('layout:0')
    phone_detail(browser)
    viewport(browser, 1300, 957)
    print('PASS: laptop and 320/390/700px views fit all six gamepads, gyro and live output; phone pad captions wrap', flush=True)


def phone_detail(browser):
    viewport(browser, 390, 844)
    browser_viewer.reveal(browser, 'trackpad-detail')
    browser.click('trackpad-detail')
    browser.wait(lambda: 'explorer:right_trackpad' in browser.snapshot()['targets'], 'expanded pads')
    browser.point('explorer:right_trackpad')
    targets = browser.snapshot()['targets']
    left, right = (targets[f'explorer:{side}_trackpad'] for side in ('left', 'right'))
    assert right[1]-right[3]/2 > left[1]+left[3]/2, (left, right)
    for side in ('left', 'right'):
        x, _, w, h = targets[f'caption:{side}_trackpad']
        assert x-w/2 >= 0 and x+w/2 <= 390 and h <= 48, targets
    browser.click('trackpad-detail')


def gyro_meter(browser):
    browser.click('reset'); browser.click('layout'); browser.click('layout:0')
    for scale in (1, 10):
        browser.click('reset'); browser.click(f'speed:{scale}')
        browser.wait(lambda: not browser.snapshot()['gyro_meter']['visible'], 'idle meter hidden')
        assert 'gyro-threshold' not in browser.snapshot()['targets']
        browser.click('switch/button_menu', button=2)
        browser.click('right_joystick/click')
        browser.click('switch/button_menu', button=2)
        browser.click('right_joystick/touch', button=2)
        browser.wait(lambda: browser.snapshot()['gyro_meter']['visible'], 'active cursor meter')
        assert browser.snapshot()['gyro_meter']['progress'] == 0
        if not browser.snapshot()['fine_motion']:
            browser.click('fine-motion')
        result = browser.sequence([(30, 'gyro', 'mousedown', 0, 0),
            (30*scale, 'gyro', 'mousemove', .02, 0),
            (30*scale, 'gyro', 'mousemove', .04, 0),
            (30*scale, 'gyro', 'mousemove', .4, 0),
            (0, 'gyro', 'mouseup', .4, 0)])
        frames = browser.js('return demoSequenceFrames')
        assert 0 < frames[1]['gyro_meter']['progress'] < 1, frames[1]['gyro_meter']
        assert frames[2]['gyro_meter']['progress'] > frames[1]['gyro_meter']['progress']
        assert frames[3]['gyro_meter']['pulse'], frames[3]['gyro_meter']
        assert frames[3]['gyro_meter']['caption'] == 'Movement emitted'
        assert result['demo']['output']['pointer'] != [0, 0]
        assert result['output_preview'][1] != 'Pointer +0, +0 · Scroll +0'
        browser.click('fine-motion')
    browser.click('reset'); browser.click('speed:1')
    print('PASS: gyro meter hidden when off, empty at rest, builds and pulses at 1x/10x with real output', flush=True)


def playback(browser):
    browser.click('reset'); browser.click('speed:10')
    browser.click('switch/left_bumper', button=2)
    browser.click('pause')
    before = browser.snapshot()['demo']['now']
    browser.click('playback-options'); browser.click('step')
    browser.wait(lambda: browser.snapshot()['demo']['now'] > before, 'next event advanced paused clock')
    assert browser.snapshot()['paused']
    browser.click('reset'); browser.click('speed:1')
    browser.click('button_diamond/button_a'); browser.click('pause')
    browser.click('playback-options'); browser.click('replay')
    browser.wait(lambda: browser.snapshot()['replaying'], 'replay started from menu')
    browser.wait(lambda: not browser.snapshot()['replaying'], 'replay completed')
    assert browser.snapshot()['demo']['output']['text'] == 'f'
    browser.click('reset')
    print('PASS: compact playback menu advances pending events and replays recorded output', flush=True)
