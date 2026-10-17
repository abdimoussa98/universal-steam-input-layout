"""Small real-Chrome test driver shared by browser demo scenarios."""
import base64
import functools
import http.server
import json
from pathlib import Path
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.error


class Browser:
    def __init__(self, args):
        self.args = args
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        bundle = args.bundle.resolve()
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(bundle.parent)))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        self.driver = subprocess.Popen([args.driver, f'--port={port}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.endpoint = f'http://127.0.0.1:{port}'
        self.session = None
        self.url = f'http://127.0.0.1:{self.server.server_port}/{bundle.name}/'

    def request(self, method, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(self.endpoint + path, data=body, method=method, headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                value = json.load(response).get('value')
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()) from error
        if isinstance(value, dict) and 'error' in value:
            raise RuntimeError(value)
        if self.args.webdriver_delay_ms:
            time.sleep(self.args.webdriver_delay_ms / 1000)
        return value

    def start(self):
        self.wait(lambda: self.request('GET', '/status'), 'driver startup')
        options = {'args': ['--headless=new', '--no-sandbox', '--enable-unsafe-swiftshader', '--window-size=1300,1100']}
        if self.args.browser_binary:
            options['binary'] = self.args.browser_binary
        result = self.request('POST', '/session', {'capabilities': {'alwaysMatch': {'browserName': 'chrome', 'goog:chromeOptions': options}}})
        self.session = result['sessionId']
        print('Browser:', result['capabilities']['browserVersion'], result['capabilities']['platformName'], flush=True)
        audio = (Path(__file__).resolve().parents[1] / 'tests/fixtures/demo-audio.js').read_text()
        self.cdp('Page.addScriptToEvaluateOnNewDocument', {'source': audio})
        clock = (Path(__file__).resolve().parents[1] / 'tests/fixtures/demo-clock.js').read_text()
        self.cdp('Page.addScriptToEvaluateOnNewDocument', {'source': clock})
        if self.args.webhid:
            source = (Path(__file__).resolve().parents[1] / 'tests/fixtures/webhid.js').read_text()
            self.cdp('Page.addScriptToEvaluateOnNewDocument', {'source': source})
        self.request('POST', f'/session/{self.session}/url', {'url': self.url})
        self.wait(lambda: self.snapshot().get('demo'), 'WASM startup')

    def js(self, script, *args):
        return self.request('POST', f'/session/{self.session}/execute/sync', {'script': script, 'args': list(args)})

    def cdp(self, command, params):
        return self.request('POST', f'/session/{self.session}/goog/cdp/execute', {'cmd': command, 'params': params})

    def snapshot(self):
        return self.js('return window.keybindApp ? JSON.parse(keybindApp.diagnostic_snapshot()) : {}') or {}

    def wait(self, predicate, message, timeout=20):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            try:
                value = predicate()
                if value:
                    return value
            except Exception as error:
                last = error
            time.sleep(0.04)
        raise AssertionError(f'{message}: {last}')

    def point(self, target):
        # Egui sizes a popup across render passes. Wait for its actual geometry,
        # rather than aiming at a provisional rectangle or adding a fixed sleep.
        point = self.request('POST', f'/session/{self.session}/execute/async', {'script': '''
          const target=arguments[0], done=arguments[arguments.length-1];
          let previous;
          function rendered(){
            const rect=JSON.parse(keybindApp.diagnostic_snapshot()).targets[target];
            if(!rect){done(null);return;}
            if(JSON.stringify(rect)===JSON.stringify(previous)){done(rect.slice(0,2));return;}
            previous=rect;requestAnimationFrame(rendered);
          }
          requestAnimationFrame(rendered);
        ''', 'args': [target]})
        if point is None:
            raise AssertionError(f'Missing visible target: {target}')
        return point

    def actions(self, actions):
        self.request('POST', f'/session/{self.session}/actions', {'actions': [{'type': 'pointer', 'id': 'mouse', 'parameters': {'pointerType': 'mouse'}, 'actions': actions}]})

    def click(self, target, button=0):
        x, y = self.point(target)
        self.actions([{'type': 'pointerMove', 'x': round(x), 'y': round(y), 'duration': 0},
                      {'type': 'pointerDown', 'button': button}, {'type': 'pause', 'duration': 50},
                      {'type': 'pointerUp', 'button': button}])

    def sequence(self, events, frame_delay_ms=0):
        """Dispatch DOM mouse events with controlled time and real rendered frames.

        It uses normal UI hit testing; there is no test-only engine mutation API.
        Each tuple is (delay_ms, target, type, dx_fraction, dy_fraction).
        """
        self.js('''
          window.demoSequenceDone=false; window.demoSequenceError=null;
          window.demoSequenceTiming=[];
          const events=arguments[0], canvas=document.querySelector('canvas');
          const rendered=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
          const snapshot=()=>JSON.parse(keybindApp.diagnostic_snapshot());
          demoClock.begin(arguments[1]);
          (async()=>{
            try {
            await rendered();
            const initial=snapshot(), start=demoClock.realNow();
            let elapsed=0;
            for(const [delay,target,type,dx,dy] of events){
              demoClock.advance(delay); elapsed+=delay;
              const s=snapshot();
              const [x,y,w,h]=s.targets[target];
              const options={bubbles:true,clientX:x+dx*w/2,clientY:y+dy*h/2,button:0,buttons:type==='mouseup'?0:1,
                pointerType:'mouse',pointerId:1,isPrimary:true};
              canvas.dispatchEvent(type==='mousemove' ? new MouseEvent(type,options) :
                new PointerEvent(type.replace('mouse','pointer'),options));
              await rendered();
              const logical=snapshot().demo.now-initial.demo.now;
              const expected=elapsed/initial.scale;
              demoSequenceTiming.push({type,expected_ms:expected,logical_ms:logical,real_ms:demoClock.realNow()-start});
              if(Math.abs(logical-expected)>1) throw new Error(`Gesture clock mismatch: ${logical} != ${expected}`);
            }
            window.demoSequenceSnapshot=snapshot();
            } catch(error) { window.demoSequenceError=String(error); }
            finally { demoClock.end(); window.demoSequenceDone=true; }
          })();
        ''', events, frame_delay_ms)
        self.wait(lambda: self.js('return window.demoSequenceDone'), 'pointer sequence')
        error = self.js('return window.demoSequenceError')
        assert not error, f'{error}; timing: {self.js("return window.demoSequenceTiming")}'
        return self.js('return window.demoSequenceSnapshot')

    def screenshot(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(self.request('GET', f'/session/{self.session}/screenshot')))

    def close(self):
        if self.session:
            try:
                self.request('DELETE', f'/session/{self.session}')
            except Exception:
                pass
        self.driver.terminate()
        self.driver.wait(timeout=10)
        self.server.shutdown()
        self.server.server_close()
