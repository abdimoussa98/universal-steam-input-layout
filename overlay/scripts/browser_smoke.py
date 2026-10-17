#!/usr/bin/env python3
"""Exercise the actual static WASM bundle with ChromeDriver; no npm required.

Uses a temporary browser profile. Synthetic Gamepad snapshots verify browser
normalization, not hardware visibility through Steam Input.
"""
import argparse
import base64
import functools
import http.server
import json
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path('overlay/dist'))
    parser.add_argument('--driver', default=shutil.which('chromedriver'))
    parser.add_argument('--browser-binary')
    parser.add_argument('--screenshot', type=Path)
    parser.add_argument('--companion-fixture', type=Path, help='Path to the compiled fake-input companion example')
    parser.add_argument('--webhid', action='store_true', help='Test direct WebHID permissions/input with a synthetic USB boundary')
    parser.add_argument('--stale-cache', action='store_true', help='Preload obsolete JS/WASM into the browser cache before opening the viewer')
    parser.add_argument('--live-helper', type=Path, help='Optional hardware check: use the real helper instead of synthetic input tests')
    parser.add_argument('--hosted-companion', action='store_true', help='Test HTTPS viewer to HTTP loopback helper with real browser CORS')
    args = parser.parse_args()
    if not args.driver:
        parser.error('Install ChromeDriver or pass --driver PATH')
    if args.hosted_companion and not (args.companion_fixture or args.live_helper):
        parser.error('--hosted-companion requires --companion-fixture or --live-helper')
    if args.live_helper and (args.companion_fixture or not args.hosted_companion):
        parser.error('--live-helper requires --hosted-companion and excludes --companion-fixture')
    bundle = args.bundle.resolve()
    assert (bundle / 'pkg/keybind_overlay_bg.wasm').is_file(), 'Build the web bundle first'
    priming_cache = args.stale_cache
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/cache-prime':
                body, mime = b'<!doctype html><title>Cache priming</title>', 'text/html'
            elif priming_cache and path.endswith(('.js', '.wasm')):
                body, mime = (b'\0asmobsolete', 'application/wasm') if path.endswith('.wasm') else (
                    b'throw new Error("Cached code from the previous release");', 'text/javascript')
            else:
                return super().do_GET()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Cache-Control', 'max-age=14400')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(bundle.parent)))
    tls_directory = tempfile.TemporaryDirectory(prefix='keybind-tls-') if args.hosted_companion else None
    if tls_directory:
        cert = str(Path(tls_directory.name) / 'cert.pem')
        keyfile = str(Path(tls_directory.name) / 'key.pem')
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', keyfile, '-out', cert, '-days', '1', '-subj', '/CN=localhost'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, keyfile)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    site = f'{"https://localhost" if tls_directory else "http://127.0.0.1"}:{server.server_port}/{bundle.name}/'
    threading.Thread(target=server.serve_forever, daemon=True).start()
    driver_port = free_port()
    driver = subprocess.Popen([args.driver, f'--port={driver_port}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    endpoint = f'http://127.0.0.1:{driver_port}'
    session = None
    companion = None
    def request(method, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(endpoint + path, data=body, method=method, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.load(response).get('value')
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()) from error
        if isinstance(result, dict) and 'error' in result and 'message' in result:
            raise RuntimeError(result)
        return result
    def wait_for(check, message, timeout=20):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            try:
                result = check()
                if result:
                    return result
            except Exception as error:
                last = error
            time.sleep(0.05)
        raise AssertionError(f'{message}; last error: {last}')
    def js(script, *values):
        return request('POST', f'/session/{session}/execute/sync', {'script': script, 'args': list(values)})
    def snapshot():
        return js('return window.keybindApp ? JSON.parse(window.keybindApp.diagnostic_snapshot()) : null')
    def key(code, repeat=False):
        js("const c=document.querySelector('canvas');c.focus();for(const t of ['keydown','keyup'])c.dispatchEvent(new KeyboardEvent(t,{key:arguments[0],code:arguments[0],repeat:arguments[1],bubbles:true}));", code, repeat)
    def click(x, y):
        request('POST', f'/session/{session}/actions', {'actions': [{'type': 'pointer', 'id': 'mouse', 'parameters': {'pointerType': 'mouse'}, 'actions': [
            {'type': 'pointerMove', 'duration': 0, 'x': x, 'y': y}, {'type': 'pointerDown', 'button': 0}, {'type': 'pointerUp', 'button': 0}]}]})
    def click_target(name):
        point = wait_for(lambda: (snapshot() or {}).get('ui_targets', {}).get(name), f'Missing UI target: {name}')
        click(round(point[0]), round(point[1]))
    def navigate():
        request('POST', f'/session/{session}/url', {'url': site})
        wait_for(snapshot, 'WASM startup failed')
    try:
        wait_for(lambda: request('GET', '/status'), 'ChromeDriver did not start')
        chrome = {'args': ['--headless=new', '--no-sandbox', '--enable-unsafe-swiftshader', '--window-size=1060,920']}
        if args.browser_binary:
            chrome['binary'] = args.browser_binary
        created = request('POST', '/session', {'capabilities': {'alwaysMatch': {'browserName': 'chrome', 'goog:chromeOptions': chrome, 'acceptInsecureCerts': bool(tls_directory)}}})
        session = created['sessionId']
        if args.webhid:
            fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/webhid.js'
            request('POST', f'/session/{session}/goog/cdp/execute', {
                'cmd': 'Page.addScriptToEvaluateOnNewDocument', 'params': {'source': fixture.read_text()}})
        if args.stale_cache:
            request('POST', f'/session/{session}/url', {'url': site.rsplit('/', 2)[0] + '/cache-prime'})
            paths = ['start.js', 'steam-hid.js', 'pkg/keybind_overlay.js', 'pkg/keybind_overlay_bg.wasm']
            result = request('POST', f'/session/{session}/execute/async', {
                'script': 'const done=arguments[2]; Promise.all(arguments[1].map(p=>fetch(new URL(p,arguments[0])).then(r=>r.arrayBuffer()))).then(()=>done("cached"),e=>done(String(e)));',
                'args': [site, paths]})
            assert result == 'cached', result
            priming_cache = False
        navigate()
        if args.stale_cache:
            print('PASS: current WASM viewer starts despite obsolete JS/WASM cached for four hours')
        if args.live_helper:
            companion = subprocess.Popen([str(args.live_helper.resolve()), '--viewer-url', site],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            line = companion.stdout.readline()
            assert line.startswith('Browser companion: '), line
            request('POST', f'/session/{session}/url', {'url': line.strip().removeprefix('Browser companion: ')})
            wait_for(lambda: snapshot() and snapshot()['remote'] and snapshot()['state']['status']=='live',
                     'Physical controller did not reach the hosted page')
            assert js('return window.isSecureContext')
            print('PASS: physical controller in HTTPS browser:', snapshot()['input_status'])
            key('F2')
            wait_for(lambda: snapshot()['state']['mode']=='steering', 'Physical helper did not acknowledge browser mode')
            companion.terminate()
            companion.wait(timeout=10)
            wait_for(lambda: snapshot()['state']['status']=='unavailable', 'Stopping physical helper left stale live input')
            print('PASS: physical helper mode commands and disconnect recovery')
            return
        js("Object.defineProperty(navigator,'getGamepads',{value:()=>[],configurable:true})")
        empty_status = 'Connect a controller to begin' if snapshot()['browser_connection']['available'] else 'No controllers exposed by this browser'
        wait_for(lambda: snapshot().get('input_status') == empty_status, 'Missing controllers not explained')
        assert snapshot()['controller_help'], 'Missing-controller troubleshooting not available'
        assert snapshot()['labels'] == ['F', 'V', 'C', 'R']
        assert js("return document.querySelector('#status')===null"), 'Startup status did not clear'
        key('F2')
        wait_for(lambda: snapshot()['state']['mode'] == 'steering', 'F2 did not select Steering')
        # egui determines repeat from held keys, not the DOM repeat flag. Model
        # a real held key across frames before testing its repeated keydown.
        js("document.querySelector('canvas').dispatchEvent(new KeyboardEvent('keydown',{key:'F3',code:'F3',bubbles:true}))")
        wait_for(lambda: snapshot()['state']['mode']=='menu', 'Initial held F3 did not switch')
        key('F2')
        wait_for(lambda: snapshot()['state']['mode']=='steering', 'F2 while holding F3 did not switch')
        js("document.querySelector('canvas').dispatchEvent(new KeyboardEvent('keydown',{key:'F3',code:'F3',repeat:true,bubbles:true}))")
        time.sleep(0.1)
        assert snapshot()['state']['mode'] == 'steering', 'Repeated key switched mode'
        js("document.querySelector('canvas').dispatchEvent(new KeyboardEvent('keyup',{key:'F3',code:'F3',bubbles:true}))")
        key('F3')
        wait_for(lambda: snapshot()['labels'] == ['Enter', 'Escape', 'Backspace', 'Tab'], 'F3 did not select Menu')
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            args.screenshot.with_name('menu.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
        key('F4')
        assert snapshot()['state']['mode'] == 'menu', 'F4 should be unassigned'
        # Actual pointer interaction with the shared mode button.
        click_target('mode:0')
        wait_for(lambda: snapshot()['state']['mode'] == 'base', 'Base mode button did not work')
        assert snapshot()['control_labels'][12:14]==['Mod 0 :: Scroll down', 'Mod 1 :: Scroll up']
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            request('POST', f'/session/{session}/window/rect', {'width': 1060, 'height': 1100})
            time.sleep(0.2)
            args.screenshot.write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
            request('POST', f'/session/{session}/window/rect', {'width': 640, 'height': 820})
            time.sleep(0.2)
            args.screenshot.with_name('narrow.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
            for name in ('settings', 'mode:0', 'mode:1', 'mode:2', 'connect'):
                x, y = snapshot()['ui_targets'][name]
                assert 0 <= x < 640 and y >= 0, f'{name} outside narrow viewport'
            request('POST', f'/session/{session}/window/rect', {'width': 1060, 'height': 1100})
            time.sleep(0.2)
        # Objects use native prototypes so the adapter exercises web-sys casts.
        js("""
          window.mockButtons=Array(17).fill(0);window.mockButtons[4]=1;window.mockMapping='standard';window.mockConnected=true;
          const pad=Object.create(Gamepad.prototype);
          for (const [key,value] of Object.entries({index:1,id:'Smoke controller'}))Object.defineProperty(pad,key,{value});
          Object.defineProperty(pad,'connected',{get:()=>window.mockConnected});
          Object.defineProperty(pad,'mapping',{get:()=>window.mockMapping});
          window.mockAxes=[0,0,0,0];Object.defineProperty(pad,'axes',{get:()=>window.mockAxes});
          Object.defineProperty(pad,'buttons',{get:()=>window.mockButtons.map(value=>{
            const b=Object.create(GamepadButton.prototype);Object.defineProperty(b,'pressed',{value:value>0});Object.defineProperty(b,'value',{value});return b;
          })});
          Object.defineProperty(navigator,'getGamepads',{value:()=>[null,pad],configurable:true});
        """)
        wait_for(lambda: len(snapshot()['devices']) == 1, 'Sparse Gamepad array not normalized')
        assert snapshot()['controller_help'] is None, 'Missing-controller help survived detection'
        click_target('settings')
        time.sleep(0.15)
        # A screenshot is useful if the shared control geometry changes.
        if args.screenshot:
            args.screenshot.with_name('settings.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
        click_target('controller')
        time.sleep(0.15)
        click_target('device:'+snapshot()['devices'][0]['id'])
        wait_for(lambda: snapshot()['state']['status'] == 'live', 'Controller selection did not seed held buttons')
        assert snapshot()['labels'] == ['G','X','Z','T']
        click_target('settings')  # Keep the floating settings window off the main controls.
        js('window.mockButtons[4]=1;window.mockButtons[5]=1')
        wait_for(lambda: snapshot()['labels'] == ['M','P','O','U'], 'Both modifiers did not resolve')
        js('window.mockButtons[4]=0;window.mockButtons[5]=1')
        wait_for(lambda: snapshot()['labels'] == ['H','N','B','Y'], 'Releasing L1 lost R1')
        js("window.mockMapping=''")
        wait_for(lambda: snapshot()['state']['status'] == 'unsupported_mapping', 'Unknown mapping was accepted')
        assert snapshot()['state']['held'] == [False,False]
        js("window.mockMapping='standard';window.mockConnected=false")
        wait_for(lambda: snapshot()['state']['status'] == 'disconnected', 'Disconnect not shown')
        js('window.mockConnected=true;window.mockButtons[4]=1;window.mockButtons[5]=0')
        wait_for(lambda: snapshot()['labels'] == ['G','X','Z','T'], 'Reconnect did not replace held state')
        js("window.mockHidden=true;Object.defineProperty(document,'hidden',{get:()=>window.mockHidden,configurable:true})")
        wait_for(lambda: snapshot()['state']['status'] == 'paused', 'Hidden page did not pause')
        js('window.mockButtons.fill(0);window.mockHidden=false')
        wait_for(lambda: snapshot()['state']['status'] == 'live' and snapshot()['labels']==['F','V','C','R'], 'Resume did not use a fresh snapshot')
        js("window.savedGamepads=navigator.getGamepads;Object.defineProperty(navigator,'getGamepads',{value:()=>{throw new Error('blocked for test')},configurable:true})")
        wait_for(lambda: snapshot()['state']['status'] == 'unavailable', 'Blocked Gamepad API was not reported')
        js("Object.defineProperty(navigator,'getGamepads',{value:window.savedGamepads,configurable:true})")
        wait_for(lambda: snapshot()['state']['status'] == 'live' and not snapshot()['error'], 'Input error did not clear on recovery')
        def sticks_do_not_overlap():
            targets = snapshot()['ui_targets']
            for side in range(2):
                shell = targets[f'stick:{side}:shell']
                origin = targets[f'stick:{side}:center']
                limit = targets[f'stick:{side}:range']
                lower = targets[f'stick:{side}:label_min']
                upper = targets[f'stick:{side}:label_max']
                scale = (limit[0]-origin[0])/10
                # Text stays inside the original circle and above the entire
                # movement field (including the marker stroke at full travel).
                for x in (lower[0], upper[0]):
                    for y in (lower[1], upper[1]):
                        assert ((x-shell[0])**2+(y-shell[1])**2)**0.5 < 46*scale
                assert upper[1] < origin[1]-16*scale
                assert abs(origin[0]-shell[0]) < 0.01
                assert abs(origin[1]-shell[1]-21*scale) < 0.01

        # Check the positions actually used by the painter, not just raw input.
        # Small and partial deflections must not snap to the rim or disappear.
        for axes in ([0, 0, 0, 0], [0.02, -0.04, -0.1, 0.2], [0.25, -0.5, -0.75, 1], [1, 0, 0, -1]):
            js('window.mockAxes=arguments[0]', axes)
            def markers_match():
                targets = snapshot()['ui_targets']
                for side in range(2):
                    center = targets.get(f'stick:{side}:center')
                    marker = targets.get(f'stick:{side}:marker')
                    limit = targets.get(f'stick:{side}:range')
                    if not center or not marker or not limit:
                        return False
                    radius = limit[0] - center[0]
                    if any(abs((marker[axis]-center[axis])/radius - axes[side*2+axis]) > 0.005 for axis in range(2)):
                        return False
                return True
            wait_for(markers_match, f'Stick drawing lost analog travel: {axes}')
            sticks_do_not_overlap()
            if args.screenshot and axes[0]==0.25:
                args.screenshot.with_name('analog-travel.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
        js('window.mockAxes.fill(0)')
        wait_for(lambda: snapshot()['state']['input']['stick_positions']==[[0,0],[0,0]], 'Stick centers did not reset')
        print('PASS: both rendered stick markers track center, small movements, partial travel and full deflection')
        # Each added physical control is normalized independently, including analog travel.
        for browser_index, control_index in [(8,4),(9,5),(12,6),(15,7),(13,8),(14,9),(10,10),(11,11),(6,14),(7,15)]:
            js('window.mockButtons.fill(0);window.mockButtons[arguments[0]]=arguments[1]', browser_index, 0.72 if browser_index==6 else 1)
            wait_for(lambda: snapshot()['state']['input']['buttons'][control_index], f'Control {control_index} not normalized')
            if browser_index==6:
                assert snapshot()['state']['input']['triggers'][0]==720
            js('window.mockButtons.fill(0)')
            wait_for(lambda: not any(snapshot()['state']['input']['buttons']), 'Button release was lost')
        # Reset any menu tap window before entering a fresh bumper gesture.
        time.sleep(0.2)
        js('window.mockButtons[4]=1')
        wait_for(lambda: snapshot()['state']['gestures']['lanes'][0]['phase']=='hold', 'Browser hold timer did not advance')
        js('window.mockButtons.fill(0)')
        wait_for(lambda: snapshot()['state']['gestures']['lanes'][0]['phase']=='idle', 'Hold release left a timer running')
        assert len(snapshot()['control_labels'])==16
        # Fn outputs are full-pull trigger clicks, not the soft-pull edge.
        for mode_index, mode in enumerate(('base', 'steering', 'menu')):
            click_target(f'mode:{mode_index}')
            wait_for(lambda: snapshot()['state']['mode']==mode
                     and snapshot()['state']['gestures']['initialized']
                     and not any(snapshot()['state']['input']['buttons']), 'Fn test mode did not settle')
            for button_index, lane_index in ((8, 2), (9, 3)):
                js('window.mockButtons[arguments[0]]=1', button_index)
                wait_for(lambda: snapshot()['state']['gestures']['lanes'][lane_index]['phase']=='hold', 'Fn hold did not activate')
                assert snapshot()['control_labels'][14:16]==['Full: F12', 'Full: F11'], 'Fn trigger labels missing'
                sticks_do_not_overlap()
                if args.screenshot and mode=='base' and button_index==8:
                    args.screenshot.with_name('fn-triggers.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
                js('window.mockButtons.fill(0)')
                wait_for(lambda: snapshot()['state']['gestures']['lanes'][lane_index]['phase']=='idle', 'Fn hold did not release')
        print('PASS: Fn full-pull trigger labels for Select/Start in all three modes')
        # Directional Steering labels follow axes across the browser/WASM boundary.
        click_target('mode:1')
        wait_for(lambda: snapshot()['state']['mode']=='steering', 'Steering shortcut failed')
        js('window.mockButtons[5]=1;window.mockAxes=[0,-0.8,0.3,0]')
        wait_for(lambda: snapshot()['control_labels'][10]=='Mouse back', 'Up Steering click label missing')
        sticks_do_not_overlap()
        if args.screenshot:
            args.screenshot.with_name('steering-sticks.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
        assert snapshot()['state']['input']['stick_positions']==[[0,-800],[300,0]]
        assert snapshot()['state']['input']['pads']==[None,None], 'Browser invented touch positions'
        js('window.mockAxes[1]=0.8')
        wait_for(lambda: snapshot()['control_labels'][11]=='Mouse middle', 'Down Steering click label missing')
        sticks_do_not_overlap()
        js('window.mockButtons.fill(0);window.mockAxes.fill(0)')
        click_target('mode:0')
        wait_for(lambda: snapshot()['state']['mode']=='base', 'Base shortcut failed')
        click_target('settings')
        js("Storage.prototype.setItem=function(){throw new Error('storage denied for test')}")
        click_target('apply')
        wait_for(lambda: snapshot()['error'] and 'storage denied' in snapshot()['error'], 'Storage failure was not surfaced')
        assert snapshot()['labels'] == ['F','V','C','R'], 'Storage failure discarded the working state'
        # Reload gives this temporary browser profile its real Storage methods again.
        navigate()
        print('PASS: packaged WASM startup, relative assets, mode controls, sparse Gamepad input, all 16 controls, trigger pressure, live hold timing, unknown mapping, reconnect, hidden/resume, blocked API recovery, denied storage')
        # Persisted settings and invalid profile recovery exercise browser storage.
        js("localStorage.setItem('keybind.preferences.v1', JSON.stringify({schema_version:1,hotkeys:[5,6,7],opacity:0.9,scale:1}));localStorage.setItem('keybind.profile.v1','{}');")
        navigate()
        assert snapshot()['error'], 'Invalid stored profile should report an error'
        assert snapshot()['labels'] == ['F','V','C','R'], 'Bundled fallback should remain usable'
        key('F7')
        wait_for(lambda: snapshot()['state']['mode'] == 'menu', 'Rebound browser shortcut failed')
        print('PASS: invalid profile recovery, persisted/rebound shortcuts')
        if args.companion_fixture:
            command = [str(args.companion_fixture.resolve()), str(bundle)]
            if args.hosted_companion:
                command.append(site)
            companion = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            line = companion.stdout.readline()
            assert line.startswith('Browser companion: '), line
            url = line.strip().removeprefix('Browser companion: ')
            if args.hosted_companion:
                assert url.startswith(site + '#companion=') and '&port=' in url
            request('POST', f'/session/{session}/url', {'url': url})
            wait_for(lambda: snapshot() and snapshot()['remote'] and snapshot()['state']['status']=='live', 'Companion handshake failed')
            if args.hosted_companion:
                assert js('return window.isSecureContext'), 'Hosted viewer is not a secure context'
                assert js('return location.protocol') == 'https:'
            assert snapshot()['labels']==['G','X','Z','T'], 'Companion did not own held input'
            assert snapshot()['settings']['hotkeys']==[5,6,7]
            assert snapshot()['preferences']['hotkeys']==[5,6,7], 'Browser settings did not display host shortcuts'
            js("window.localReads=0;Object.defineProperty(navigator,'getGamepads',{value:()=>{window.localReads++;throw new Error('must not use local input')},configurable:true})")
            click_target('mode:2')
            wait_for(lambda: snapshot()['state']['mode']=='menu', 'Browser mode command was not acknowledged')
            key('F6')
            wait_for(lambda: snapshot()['state']['mode']=='steering', 'Focused companion shortcut was not acknowledged')
            companion.stdin.write(json.dumps({'mode':'base','held':[False,True],'hotkeys':[8,9,10]})+'\n');companion.stdin.flush()
            wait_for(lambda: snapshot()['labels']==['H','N','B','Y'] and snapshot()['preferences']['hotkeys']==[8,9,10], 'Host state/settings did not synchronize')
            def host_input(at_ms, buttons=(), triggers=(0,0)):
                pressed=[i in buttons for i in range(16)]
                companion.stdin.write(json.dumps({'input':{'buttons':pressed,'triggers':triggers},'at_ms':at_ms})+'\n');companion.stdin.flush()
                wait_for(lambda: snapshot()['state']['gestures']['clock_ms']==at_ms, 'Authoritative host time did not arrive')
            host_input(1000)
            host_input(1010, (12,))
            assert snapshot()['state']['gestures']['lanes'][0]['phase']=='pressed'
            host_input(1100)
            assert snapshot()['state']['gestures']['lanes'][0]['phase']=='window'
            host_input(1150)
            assert any(e['label']=='Expected Scroll down' for e in snapshot()['state']['gestures']['history'])
            host_input(1200, (12,14), (720,0))
            assert snapshot()['state']['gestures']['lanes'][0]['phase']=='second'
            host_input(1350, (12,14), (720,0))
            assert snapshot()['state']['gestures']['lanes'][0]['phase']=='cover'
            assert snapshot()['state']['input']['triggers'][0]==720
            # A pad can interrupt timing without erasing bindings inherited through cover.
            held=[i==12 for i in range(16)]
            companion.stdin.write(json.dumps({'input':{'buttons':held,'pad_active':True},'at_ms':1400})+'\n');companion.stdin.flush()
            wait_for(lambda: snapshot()['state']['gestures']['lanes'][0]['phase']=='interrupted', 'Expected interrupted timing')
            assert snapshot()['control_labels'][0]=='F', 'Cover inheritance disappeared when timing became uncertain'
            host_input(1500)
            positions={'stick_positions':[[650,-700],[-250,450]],'touches':[True,False],
                       'pads':[{'touching':True,'position':[-600,500]},{'touching':True,'position':[700,-500]}], 'pad_active':True}
            companion.stdin.write(json.dumps({'input':positions,'at_ms':1600})+'\n');companion.stdin.flush()
            wait_for(lambda: snapshot()['state']['input']['pads']==positions['pads'], 'Trackpad contacts lost in companion transport')
            assert snapshot()['state']['input']['stick_positions']==positions['stick_positions']

            assert js('return window.localReads')==0, 'Companion and local controller input were mixed'
            if args.screenshot:
                args.screenshot.with_name('companion.png').write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
            companion.stdin.write('quit\n');companion.stdin.flush();companion.wait(timeout=10)
            wait_for(lambda: snapshot()['state']['status']=='unavailable', 'Closing companion left live input')
            assert snapshot()['state']['held']==[False,False]
            print('PASS: real companion handshake, native input/timing authority, acknowledged browser commands, host settings synchronization, local input exclusion, disconnect recovery')

        if args.webhid:
            js('localStorage.clear()')
            navigate()
            assert snapshot()['browser_connection']['available']
            js("Object.defineProperty(navigator,'getGamepads',{value:()=>[],configurable:true});fakeHid.cancel=true")
            click_target('connect')
            wait_for(lambda: 'No controller selected' in snapshot()['browser_connection']['message'], 'Picker cancellation not explained')
            assert js('return fakeHid.requests[0].activated'), 'Picker did not run with user activation'
            assert js('return fakeHid.requests[0].options.filters.length') == 0, 'Picker is still hiding controllers by device ID'
            assert snapshot()['state']['status'] != 'live'
            js('fakeHid.cancel=false;fakeHid.deny=true')
            click_target('connect')
            wait_for(lambda: 'blocked' in snapshot()['browser_connection']['message'], 'Permission denial not explained')
            js('fakeHid.deny=false')
            js('fakeHid.device.productId=0x1399')
            click_target('connect')
            wait_for(lambda: '28de:1399' in snapshot()['browser_connection']['message'], 'Unsupported selection did not identify the device')
            assert not js('return fakeHid.device.opened'), 'Unsupported device was opened'
            js('fakeHid.device.productId=0x1302')
            click_target('connect')
            wait_for(lambda: snapshot()['state']['status']=='live', 'Direct HID input did not become live')
            assert not snapshot()['remote'], 'HID should not use companion transport'
            assert snapshot()['state']['device']=='webhid:steam-controller-usb'
            js('fakeHid.device.frame(0x80000)')
            wait_for(lambda: snapshot()['state']['held']==[True,False], 'Direct L1 did not reach Rust')
            # A release and press delivered in one JS task must not collapse to
            # the final snapshot: the shared gesture engine must see both edges.
            js('fakeHid.device.frame(0);fakeHid.device.frame(0x80000)')
            wait_for(lambda: snapshot()['state']['gestures']['lanes'][0]['phase'] in ('second','cover'), 'Fast tap and hold lost between poll frames')
            js('fakeHid.device.frame(0)')
            wait_for(lambda: snapshot()['state']['held']==[False,False], 'Direct release was stale')
            js('fakeHid.device.frame(0x0330ee6f,{5:16384,7:32767,9:-32768,11:32767,13:32767,15:-32768,19:-16384,21:16384,25:16384,27:-16384})')
            wait_for(lambda: snapshot()['state']['input']['triggers']==[500,1000], 'Direct triggers not decoded')
            value=snapshot()['state']['input']
            assert value['stick_positions']==[[-1000,-1000],[1000,1000]]
            assert value['touches']==[True,True]
            assert value['pads']==[{'touching':True,'position':[-500,-500]},{'touching':True,'position':[500,500]}]
            js("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
            wait_for(lambda: snapshot()['state']['status']=='paused', 'Hidden HID page not paused')
            assert snapshot()['state']['held']==[False,False]
            js("fakeHid.device.frame(0);Object.defineProperty(document,'hidden',{value:false,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
            wait_for(lambda: snapshot()['state']['status']=='live', 'HID did not resume from fresh input')
            assert snapshot()['state']['held']==[False,False]
            js('fakeHid.device.frame(0x80000);fakeHid.remove()')
            wait_for(lambda: snapshot()['state']['status']=='disconnected', 'USB removal did not clear input')
            assert snapshot()['state']['held']==[False,False]
            js('fakeHid.device.report=new Uint8Array(45);fakeHid.reconnect()')
            wait_for(lambda: snapshot()['state']['status']=='live', 'USB reconnection failed')
            # The browser can stop delivering input without a disconnect event.
            js('fakeHid.device.frame(0x80000);clearInterval(fakeHid.device.timer)')
            wait_for(lambda: snapshot()['state']['status']=='unavailable', 'Stalled HID input remained live')
            assert snapshot()['state']['held']==[False,False]
            js('fakeHid.device.frame(0)')
            wait_for(lambda: snapshot()['state']['status']=='live', 'Fresh HID report did not recover')
            click_target('disconnect')
            wait_for(lambda: snapshot()['state']['status']=='disconnected', 'Disconnect action left input live')
            assert not js('return fakeHid.device.opened')
            print('PASS: direct WebHID picker activation, cancel/deny, controls, fast taps, positions, pause, reconnect, stale input and disconnect')
            # A wireless receiver stays attached while its controller turns off.
            # The occupied slot need not be the first HID interface returned.
            for product_id in [0x1304, 0x1305]:
                js('fakeHid.receiver(arguments[0])', product_id)
                click_target('connect')
                wait_for(lambda: 'Receiver connected' in snapshot()['browser_connection']['message'], 'Receiver did not open')
                assert snapshot()['browser_connection']['connected'], 'Waiting receiver must remain disconnectable'
                assert snapshot()['state']['status'] != 'live', 'An empty receiver is not a live controller'
                js('fakeHid.device.radio(true)')
                wait_for(lambda: snapshot()['state']['status']=='live', 'Occupied receiver slot was not found')
                assert 'wireless' in snapshot()['browser_connection']['message']
                js('fakeHid.device.frame(0x80000,{5:16384,7:32767})')
                wait_for(lambda: snapshot()['state']['held']==[True,False], 'Wireless buttons did not reach Rust')
                assert snapshot()['state']['input']['triggers']==[500,1000]
                js('fakeHid.device.radio(false)')
                wait_for(lambda: snapshot()['state']['status']!='live', 'Radio disconnect left stale input')
                assert snapshot()['state']['held']==[False,False]
                assert snapshot()['state']['input']['triggers']==[0,0]
                assert snapshot()['browser_connection']['connected'], 'Controller power-off closed receiver access'
                js('fakeHid.slots[0].radio(true);fakeHid.slots[0].frame(0x200)')
                time.sleep(0.1)
                assert snapshot()['state']['status']!='live', 'Another controller took over the selected slot'
                js('fakeHid.device.frame(0);fakeHid.device.radio(true)')
                wait_for(lambda: snapshot()['state']['status']=='live', 'Radio reconnect did not resume')
                assert snapshot()['state']['held']==[False,False]
                js('fakeHid.device.frame(0x80000);fakeHid.remove()')
                wait_for(lambda: snapshot()['state']['status']=='disconnected', 'Receiver removal left stale input')
                assert snapshot()['state']['held']==[False,False]
                js('fakeHid.device.report=new Uint8Array(45);fakeHid.reconnect()')
                wait_for(lambda: snapshot()['state']['status']=='live', 'Receiver USB reconnect failed')
                assert snapshot()['state']['held']==[False,False], 'USB reconnect switched controller slots'
                click_target('disconnect')
                wait_for(lambda: snapshot()['state']['status']=='disconnected', 'Receiver disconnect action failed')
                assert js('return fakeHid.devices.every(d=>!d.opened)'), 'Receiver interfaces leaked after disconnect'
            print('PASS: both wireless receivers, inactive slots, wireless controls, radio power-off/on, slot isolation and receiver USB reconnect')

    except Exception:
        if session:
            print('Browser diagnostic:', snapshot())
            print('Startup text:', js("return document.querySelector('#status')?.textContent"))
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                args.screenshot.write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
        raise
    finally:
        if companion and companion.poll() is None:
            companion.terminate()
            companion.wait(timeout=10)
        if session:
            try:
                request('DELETE', f'/session/{session}')
            except Exception:
                pass
        driver.terminate()
        driver.wait(timeout=10)
        server.shutdown()
        server.server_close()
        if tls_directory:
            tls_directory.cleanup()


if __name__ == '__main__':
    main()
