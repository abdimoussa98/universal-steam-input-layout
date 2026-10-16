import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

function observer() {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', textContent: '', className: '', listeners: {},
      addEventListener(name, fn) { this.listeners[name] = fn; },
      focus() { this.listeners.focus?.(); }, click() {},
    });
    return elements.get(id);
  }
  const document = { getElementById: element, hidden: false, listeners: {},
    addEventListener(name, fn) { this.listeners[name] = fn; },
    createElement: () => element('download-anchor') };
  const window = { addEventListener() {} };
  let exported;
  const context = vm.createContext({ document, window, performance: {now: () => 100},
    Date, navigator: {userAgent: 'test'}, Blob: class { constructor(parts) {exported=JSON.parse(parts[0]);} },
    URL: {createObjectURL: () => 'blob:test', revokeObjectURL() {}}, setTimeout(fn) {fn();} });
  const html = readFileSync(new URL('../../findings/2026-09-29-steering-native-probes/observer.html', import.meta.url), 'utf8');
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  return {element, download() {element('download').onclick(); return exported;},
    emit(type, fields={}) {element('capture').listeners[type]({preventDefault(){}, ...fields});} };
}

test('records key edges, repeats, wheel deltas and held state without conflating them', () => {
  const o=observer(); o.element('start').onclick();
  o.emit('keydown',{code:'KeyW',key:'w',repeat:false,timeStamp:12});
  o.emit('keydown',{code:'KeyW',key:'w',repeat:true,timeStamp:13});
  o.emit('wheel',{deltaX:0,deltaY:-1,deltaMode:1,timeStamp:14});
  o.emit('keyup',{code:'KeyW',key:'w',repeat:false,timeStamp:15});
  const data=o.download();
  assert.deepEqual(data.heldAtDownload,[]);
  assert.equal(data.wheelCount,1); assert.equal(data.wheelY,-1);
  assert.equal(data.events.filter(e=>e.type==='keydown').length,2);
  assert.equal(data.events.find(e=>e.type==='wheel').deltaMode,1);
});

test('intentional pointer stop preserves validity; focus loss while recording invalidates it', () => {
  const o=observer(); o.element('start').onclick();
  o.element('stop').listeners.pointerdown(); o.emit('blur');
  assert.equal(o.download().continuityValid,true);
  o.element('start').onclick(); o.emit('blur');
  assert.equal(o.download().continuityValid,false);
  o.element('start').onclick();
  assert.equal(o.download().continuityValid,true);
});
