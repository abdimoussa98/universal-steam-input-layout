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
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
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
        navigate()
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
        wait_for(lambda: snapshot().get('input_status') == 'No controllers exposed by this browser', 'Missing controllers not explained')
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
        key('F4')
        assert snapshot()['state']['mode'] == 'menu', 'F4 should be unassigned'
        # Actual pointer interaction with the shared mode button.
        click_target('mode:0')
        wait_for(lambda: snapshot()['state']['mode'] == 'base', 'Base mode button did not work')
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            args.screenshot.write_bytes(base64.b64decode(request('GET', f'/session/{session}/screenshot')))
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
        # Directional Steering labels follow axes across the browser/WASM boundary.
        click_target('mode:1')
        wait_for(lambda: snapshot()['state']['mode']=='steering', 'Steering shortcut failed')
        js('window.mockButtons[5]=1;window.mockAxes=[0,-0.8,0.3,0]')
        wait_for(lambda: snapshot()['control_labels'][10]=='Mouse back', 'Up Steering click label missing')
        assert snapshot()['state']['input']['stick_positions']==[[0,-800],[300,0]]
        assert snapshot()['state']['input']['pads']==[None,None], 'Browser invented touch positions'
        js('window.mockAxes[1]=0.8')
        wait_for(lambda: snapshot()['control_labels'][11]=='Mouse middle', 'Down Steering click label missing')
        js('window.mockButtons.fill(0);window.mockAxes.fill(0)')
        click_target('mode:0')
        wait_for(lambda: snapshot()['state']['mode']=='base', 'Base shortcut failed')
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
