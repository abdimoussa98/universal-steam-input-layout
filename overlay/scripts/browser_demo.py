"""Packaged-browser acceptance tests of executable layout outputs and mouse UI."""
import argparse
import math
from pathlib import Path
import shutil
from demo_browser_client import Browser
import browser_viewer
import browser_responsive
import browser_bindings


def run(browser):
    browser_bindings.slider(browser)
    browser_viewer.lifecycle(browser)
    state = browser.snapshot()
    assert state['demo']['layout'] == 'ibex 1.2 · default', state
    assert state['demo']['timers'] == []
    browser.click('button_diamond/button_a')
    browser.wait(lambda: 'f' in browser.snapshot()['demo']['output']['text'], 'A must type its released-layout F binding')
    assert browser.snapshot()['demo']['output']['down'] == []
    browser.click('reset')
    # Stateful cursor entry uses the diagram's buttons and the layout's releases.
    browser.click('switch/button_menu', button=2)
    browser.click('right_joystick/click')
    browser.click('switch/button_menu', button=2)
    browser.wait(lambda: browser.snapshot()['demo']['mode'] == 'Cursor Gyro', 'cursor entry')
    assert browser.snapshot()['demo']['gyro']['status'] == 'Off'
    browser.click('right_joystick/touch', button=2)
    browser.wait(lambda: browser.snapshot()['demo']['gyro']['active'], 'gyro activation selector')
    browser.click('fine-motion')
    browser.click('sound')
    browser.wait(lambda: browser.snapshot()['sound'], 'sound enabled by user gesture')
    gyro = [('gyro', 0., 0.), ('gyro', .02, 0.), ('gyro', .04, 0.), ('gyro', .4, 0.)]
    events = [(30, 'gyro', 'mousedown', 0, 0)]
    events += [(30, t, 'mousemove', x, y) for t, x, y in gyro[1:]]
    events += [(30, 'gyro', 'mouseup', .4, 0)]
    result = browser.sequence(events)
    assert result['demo']['gyro']['motion']['ticks'] > 0, result
    assert result['demo']['output']['pointer'] != [0, 0], result
    browser.wait(lambda: browser.js('return demoAudio.events.some(e=>e.frequency===720)'), 'audible threshold feedback')
    browser.click('sound')
    browser.wait(lambda: not browser.snapshot()['sound'], 'sound muted')
    audio_count = browser.js('return demoAudio.events.length')
    browser.sequence(events)
    assert browser.js('return demoAudio.events.length') == audio_count, 'Muted motion scheduled sound'
    pointer = browser.snapshot()['demo']['output']['pointer']
    browser.click('recenter')
    assert browser.snapshot()['demo']['output']['pointer'] == pointer, 'Recenter emitted output'
    print('PASS: mouse buttons, stateful Cursor Gyro, activation, cuboid motion and threshold output', flush=True)
    for scale, frame_delay in ((1, 0), (10, 0), (1, 200)):
        browser.click('reset')
        browser.click(f'speed:{scale}')
        events = [(30, 'right_trackpad', 'mousedown', 0, 0), (60*scale, 'right_trackpad', 'mouseup', 0, 0),
                  (50*scale, 'right_trackpad', 'mousedown', 0, -.9)]
        events += [(30*scale, 'right_trackpad', 'mousemove', .9*math.cos(a), .9*math.sin(a))
                   for a in [(-90+i*30)*math.pi/180 for i in range(1, 10)]]
        events += [(30*scale, 'right_trackpad', 'mouseup', 0, .9)]
        result = browser.sequence(events, frame_delay_ms=frame_delay)
        assert result['demo']['output']['wheel'] > 0, result
        assert f'Scroll {result["demo"]["output"]["wheel"]:+}' in result['output_preview'][1], result
        browser_viewer.geometry(result)
        assert not any('RTP:' in layer for layer in result['demo']['stack']), result
        assert result['demo']['output']['down'] == [], result
        assert result['demo']['error'] is None, result
        edges = [e for e in result['demo']['output']['events'] if e['detail'] == 'right_trackpad/touch' and e['kind'] in ('press', 'release')]
        assert abs(edges[1]['at'] - edges[0]['at'] - 60) <= 1, edges
        assert abs(edges[2]['at'] - edges[1]['at'] - 50) <= 1, edges
    print('PASS: mouse double-touch scroll at 1x and 10x, exact input timing and 200 ms slow-frame regression', flush=True)
    browser.click('pause')
    frozen = browser.snapshot()['demo']['now']
    browser.click('button_diamond/button_b')
    assert browser.snapshot()['demo']['now'] == frozen
    browser.click('pause')
    browser.click('reset')
    for index in range(6):
        browser.click('layout')
        browser.click(f'layout:{index}')
        expected = ['ibex 1.2', 'neptune 90.78', 'dse 1.2'][index // 2] + (' · alternative' if index % 2 else ' · default')
        browser.wait(lambda: browser.snapshot()['demo']['layout'] == expected, 'selected layout rendered')
        assert browser.snapshot()['demo']['error'] is None
        browser_viewer.selected_layout(browser, index)
        browser_bindings.inherited(browser, index)
    assert browser.snapshot()['demo']['layout'].startswith('dse')
    assert 'center_trackpad' in browser.snapshot()['targets']
    print('PASS: pause, reset and six layout selections', flush=True)
    print('PASS: all six layouts show and emit Mod 0 G/T/Z/X at 1x/10x, preserve labels through covers, and restore base labels', flush=True)
    browser_viewer.explorer(browser)
    if browser.args.webhid:
        hardware(browser)
    browser_viewer.narrow(browser)
    browser_responsive.responsive(browser)
    browser_responsive.gyro_meter(browser)
    browser_responsive.playback(browser)
    browser.click('downloads')
    browser.wait(lambda: browser.js("return document.querySelector('#downloads').open"), 'downloads dialog')
    assert browser.js("return document.querySelector('.demo-identity').textContent.includes('The demo runs')")
    browser.js("document.querySelector('.close-downloads').click()")


def hardware(browser):
    browser.click('layout'); browser.click('layout:0')
    browser.wait(lambda: browser.snapshot()['demo']['layout'] == 'ibex 1.2 · default', 'HID layout selected')
    browser.click('speed:1')
    browser.click('connect')
    browser.wait(lambda: browser.snapshot()['browser_connection']['connected'], 'WebHID connection')
    browser.click('source')
    browser.click('source:webhid:steam-controller-usb')
    browser.wait(lambda: browser.snapshot()['source'] == 'webhid:steam-controller-usb', 'source selection rendered')
    # Two reports within one JS task must both reach the layout engine.
    browser.js('fakeHid.device.frame(1); fakeHid.device.frame(0)')
    browser.wait(lambda: browser.snapshot()['demo']['output']['text'] == 'f', 'queued HID press/release')
    assert browser.snapshot()['demo']['output']['down'] == []
    browser.js('fakeHid.device.frame(0x4000);fakeHid.device.frame(0x4020);fakeHid.device.frame(0x4000);fakeHid.device.frame(0);fakeHid.device.frame(0x100000)')
    browser.wait(lambda: browser.snapshot()['demo']['mode'] == 'Cursor Gyro', 'HID stateful gesture')
    browser.js('fakeHid.device.frame(0x100000,{31:1000,43:16384})')
    browser.wait(lambda: browser.snapshot()['demo']['gyro']['motion']['ticks'] > 0, 'HID gyro motion')
    browser.click('connect')
    browser.wait(lambda: not browser.snapshot()['browser_connection']['connected'], 'HID disconnect')
    browser.wait(lambda: browser.snapshot()['demo']['output']['down'] == [], 'disconnect output cleanup')
    print('PASS: queued WebHID button edges, real layer transitions, decoded gyro and disconnect', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path('overlay/dist'))
    parser.add_argument('--driver', default=shutil.which('chromedriver'))
    parser.add_argument('--browser-binary')
    parser.add_argument('--webhid', action='store_true')
    parser.add_argument('--webdriver-delay-ms', type=int, default=0)
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    if not args.driver:
        parser.error('ChromeDriver required')
    browser = Browser(args)
    try:
        browser.start()
        run(browser)
        if args.screenshot:
            browser.screenshot(args.screenshot)
    except Exception:
        if browser.session:
            print('Browser diagnostic:', browser.snapshot().get('demo'))
            print('Sequence timing:', browser.js('return window.demoSequenceTiming'))
            if args.screenshot:
                browser.screenshot(args.screenshot)
        raise
    finally:
        browser.close()


if __name__ == '__main__':
    main()
