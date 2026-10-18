"""Acceptance checks for the restored illustrated viewer and lifecycle rail."""

def geometry(state):
    targets = state['targets']
    controller, gyro, timeline = (targets[k] for k in ('controller', 'gyro', 'timeline'))
    assert timeline[1] + timeline[3] / 2 < controller[1] - controller[3] / 2, targets
    assert gyro[1] - gyro[3] / 2 > controller[1] + controller[3] / 2, targets
    assert gyro[2:4] in ([160, 100], [100, 76]), gyro
    assert controller[2] > gyro[2] * 2.5, targets


def lifecycle(browser):
    geometry(browser.snapshot())
    assert browser.snapshot()['timeline']['text'] == ''
    for scale in (1, 10):
        browser.click('reset')
        browser.click(f'speed:{scale}')
        control = 'switch/left_bumper'
        browser.sequence([(30, control, 'mousedown', 0, 0),
                          (100*scale, control, 'mousemove', 0, 0),
                          (0, control, 'mouseup', 0, 0),
                          (50*scale, control, 'mousemove', 0, 0),
                          (20*scale, control, 'mousedown', 0, 0),
                          (160*scale, control, 'mousemove', 0, 0),
                          (0, control, 'mouseup', 0, 0)])
        frames = browser.js('return demoSequenceFrames')
        assert [s['timeline'].get('phase') for s in frames] == [
            'InitialHold', 'InitialHold', 'ReleaseWindow', 'ReleaseWindow',
            'SecondHold', 'Covered', None], [s['timeline'] for s in frames]
        assert abs(frames[1]['timeline']['progress'] - .5) < .01
        assert abs(frames[1]['timeline']['remaining_ms'] - 100*scale) <= scale
        assert frames[-1]['timeline']['text'] == ''
        initial = frames[0]['targets']
        for state in frames:
            geometry(state)
            for target in (control, 'controller', 'gyro', 'right_trackpad'):
                assert state['targets'][target] == initial[target], (target, state['targets'][target], initial[target])
    browser.click('reset')
    browser.click('speed:1')
    print('PASS: original gamepad geometry, compact gyro below, full lifecycle rail at 1x/10x and stable mouse targets', flush=True)


def selected_layout(browser, index):
    geometry(browser.snapshot())
    browser.click('speed:10')
    control = 'left_trigger/edge' if index % 2 else 'switch/left_bumper'
    result = browser.sequence([(30, control, 'mousedown', 0, 0),
                               (600, control, 'mouseup', 0, 0),
                               (600, control, 'mousemove', 0, 0)])
    assert result['demo']['output']['wheel'] > 0, result
    assert result['timeline']['phase'] == 'ReleaseWindow', result
    assert result['demo']['error'] is None
    targets = result['targets']
    for name in ('button_back_left', 'button_back_right', 'button_back_left_upper', 'button_back_right_upper'):
        assert f'switch/{name}' in targets, (index, name)
    if index >= 4:
        assert 'center_trackpad' in targets and 'switch/button_capture' in targets
    else:
        assert 'left_trackpad' in targets and 'right_trackpad' in targets
    browser.click('reset')


def explorer(browser):
    browser.click('layout'); browser.click('layout:0')
    browser.click('reset'); browser.click('speed:10'); browser.click('pad-click')
    reveal(browser, 'trackpad-detail')
    browser.click('trackpad-detail')
    scroll(browser, 650)
    browser.wait(lambda: browser.snapshot()['targets']['explorer:right_trackpad'][1] < 800, 'explorer scrolled into view')
    target = 'explorer:right_trackpad'
    result = browser.sequence([(30, target, 'mousedown', .735, 0), (100, target, 'mousemove', .735, 0)])
    assert 'mouse_button MIDDLE' in result['demo']['output']['down'], result
    browser.sequence([(0, target, 'mouseup', .735, 0)])
    browser.click('reset'); browser.click('pad-touch')
    scroll(browser, -2000)
    browser.wait(lambda: browser.snapshot()['targets']['controller'][1] > 400, 'viewer returned to top')
    reveal(browser, 'trackpad-detail')
    browser.click('trackpad-detail')
    scroll(browser, -2000)
    browser.wait(lambda: browser.snapshot()['targets']['controller'][1] > 400, 'viewer returned after closing detail')
    browser.click('speed:1')
    print('PASS: restored trackpad explorer uses the same inner/outer bindings and cleanup', flush=True)


def scroll(browser, delta):
    browser.actions([{'type':'pointerMove', 'x':900, 'y':700, 'duration':0}])
    browser.cdp('Input.dispatchMouseEvent', {'type':'mouseWheel', 'x':900, 'y':700, 'deltaX':0, 'deltaY':delta})


def reveal(browser, target):
    width, height = browser.js('return [innerWidth, innerHeight]')
    y = browser.point(target)[1]
    if y > height - 40 or y < browser.snapshot()['targets']['timeline'][1] + 40:
        x, bottom = width/2, height-50
        browser.cdp('Input.dispatchMouseEvent', {'type':'mouseMoved', 'x':x, 'y':bottom})
        browser.cdp('Input.dispatchMouseEvent', {'type':'mouseWheel', 'x':x, 'y':bottom,
            'deltaX':0, 'deltaY':y-height*.6})
        browser.wait(lambda: 0 < browser.point(target)[1] < height-30, 'target scrolled into view')


def narrow(browser):
    browser.request('POST', f'/session/{browser.session}/window/rect', {'width':700,'height':1100})
    browser.wait(lambda: browser.snapshot()['targets']['controller'][2] < 780, 'narrow diagram rendered')
    browser.point('gyro')
    geometry(browser.snapshot())
    for target in ('source', 'connect', 'layout', 'pad-click'):
        x, y, w, h = browser.snapshot()['targets'][target]
        assert x-w/2 >= 0 and x+w/2 <= 700, (target, x, w)
    browser.click('button_diamond/button_a')
    browser.wait(lambda: 'f' in browser.snapshot()['demo']['output']['text'], 'narrow gamepad remains clickable')
    browser.request('POST', f'/session/{browser.session}/window/rect', {'width':1300,'height':1100})
    browser.wait(lambda: browser.snapshot()['targets']['controller'][2] == 780, 'desktop restored')
    print('PASS: narrow viewer keeps the gamepad, timeline, gyro and header controls usable', flush=True)
