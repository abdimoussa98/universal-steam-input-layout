import test from 'node:test';
import assert from 'node:assert/strict';
import { SteamHid } from '../web/steam-hid.js';

class Device extends EventTarget {
  vendorId = 0x28de;
  productId = 0x1302;
  productName = 'Steam Controller';
  collections = [{ usagePage: 0xff00, inputReports: [{reportId: 0x47}] }];
  opened = false;
  writes = [];
  async open() { this.opened = true; }
  async close() { this.opened = false; }
  async sendFeatureReport(id, bytes) { this.writes.push([id, Array.from(bytes)]); }
  input(id, bytes) {
    const event = new Event('inputreport');
    event.reportId = id;
    event.data = new DataView(Uint8Array.from(bytes).buffer);
    this.dispatchEvent(event);
  }
}
class Hid extends EventTarget {
  selected = [];
  granted = [];
  async requestDevice(options) { this.options = options; return this.selected; }
  async getDevices() { return this.granted; }
}
function setup() {
  const hid = new Hid();
  const device = new Device();
  hid.selected = [device];
  const states = [], reports = [];
  const client = new SteamHid((id, bytes) => reports.push([id, Array.from(bytes)]),
    (state, message) => states.push([state, message]), {hid, secure: true});
  return {hid, device, states, reports, client};
}

test('picker opens only the selected supported input interface; disconnect stops reports', async () => {
  const {hid, device, states, reports, client} = setup();
  try {
    const keyboard = new Device(); keyboard.collections = [{usagePage: 1, inputReports: [{reportId: 1}]}];
    hid.selected = [keyboard, device];
    await client.connect();
    assert.deepEqual(hid.options, {filters: [0x1302, 0x1304, 0x1305].map(productId => ({vendorId: 0x28de, productId}))});
    assert.equal(keyboard.opened, false);
    assert.equal(device.opened, true);
    assert.equal(states.at(-1)[0], 'connected');
    device.input(0x47, [1, 2, 3]);
    assert.deepEqual(reports, [[0x47, [1, 2, 3]]]);
    await client.disconnect();
    device.input(0x47, [4]);
    assert.equal(reports.length, 1);
    assert.equal(device.opened, false);
    assert.equal(states.at(-1)[0], 'disconnected');
  } finally { await client.destroy(); }
});

test('cancel, denied permission and unsupported browsers have actionable status', async () => {
  const {hid, states, client} = setup();
  try {
    hid.selected = [];
    await client.connect();
    assert.equal(states.at(-1)[0], 'idle');
    assert.match(states.at(-1)[1], /selected|picker/i);
    hid.requestDevice = async () => { throw new DOMException('Blocked', 'NotAllowedError'); };
    await client.connect();
    assert.equal(states.at(-1)[0], 'error');
    assert.match(states.at(-1)[1], /permission|allow|settings/i);
    const unsupported = new SteamHid(() => {}, () => {}, {hid: null, secure: true});
    assert.equal(unsupported.available, false);
    assert.match(unsupported.supportMessage, /WebHID/);
    await unsupported.destroy();
    const insecure = new SteamHid(() => {}, () => {}, {hid, secure: false});
    assert.equal(insecure.available, false);
    assert.match(insecure.supportMessage, /HTTPS/);
    await insecure.destroy();
  } finally { await client.destroy(); }
});

test('USB disconnect clears connection and reconnect uses an already granted device', async () => {
  const {hid, device, states, client} = setup();
  try {
    await client.connect();
    const event = new Event('disconnect'); event.device = device;
    hid.dispatchEvent(event);
    assert.equal(states.at(-1)[0], 'disconnected');
    device.opened = false;
    hid.granted = [device];
    const reconnect = new Event('connect'); reconnect.device = device;
    hid.dispatchEvent(reconnect);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(device.opened, true);
    assert.equal(states.at(-1)[0], 'connected');
  } finally { await client.destroy(); }
});

test('destroy during permission/open cannot leave a controller or callback active', async () => {
  const {hid, device, states, reports, client} = setup();
  let grant;
  hid.requestDevice = () => new Promise(resolve => { grant = resolve; });
  const pending = client.connect();
  await client.destroy();
  const count = states.length;
  grant([device]);
  await pending;
  assert.equal(device.opened, false);
  device.input(0x47, [1]);
  assert.equal(states.length, count);
  assert.deepEqual(reports, []);
});

test('a failed open is recoverable without pretending a controller is live', async () => {
  const {device, states, client} = setup();
  try {
    device.open = async () => { throw new DOMException('Device in use', 'NetworkError'); };
    await client.connect();
    assert.equal(states.at(-1)[0], 'error');
    assert.equal(device.opened, false);
    device.open = async () => { device.opened = true; };
    await client.connect();
    assert.equal(states.at(-1)[0], 'connected');
  } finally { await client.destroy(); }
});

test('destroy while a device is opening closes it before accepting input', async () => {
  const {device, states, reports, client} = setup();
  let opened;
  device.open = () => new Promise(resolve => { opened = () => { device.opened = true; resolve(); }; });
  const pending = client.connect();
  await new Promise(resolve => setImmediate(resolve));
  await client.destroy();
  const count = states.length;
  opened();
  await pending;
  device.input(0x47, [1]);
  assert.equal(device.opened, false);
  assert.equal(states.length, count);
  assert.deepEqual(reports, []);
});

test('failed device initialization closes USB and reports an error', async () => {
  const {device, states, client} = setup();
  try {
    device.sendFeatureReport = async () => { throw new DOMException('Write failed', 'NetworkError'); };
    await client.connect();
    assert.equal(device.opened, false);
    assert.equal(states.at(-1)[0], 'error');
    assert(!states.some(([state]) => state === 'connected'));
  } finally { await client.destroy(); }
});

const settled = () => new Promise(resolve => setImmediate(resolve));
function receiver(productId = 0x1304) {
  const result = setup();
  const slots = Array.from({length: 4}, () => Object.assign(new Device(), {productId}));
  const keyboard = Object.assign(new Device(), {productId, collections: [{inputReports: [{reportId: 1}]}]});
  result.hid.selected = [keyboard, ...slots];
  return {...result, slots, keyboard};
}

for (const productId of [0x1304, 0x1305]) {
  test(`receiver ${productId.toString(16)} finds a populated slot without opening the keyboard`, async () => {
    const {client, slots, keyboard, states, reports} = receiver(productId);
    try {
      await client.connect();
      assert(slots.every(slot => slot.opened));
      assert.equal(keyboard.opened, false);
      assert.equal(states.at(-1)[0], 'waiting');
      assert(slots.every(slot => !slot.writes.length), 'Do not write to unoccupied receiver slots');
      slots[0].input(0x47, [1]); // A malformed frame must not win selection.
      const frame = Array(45).fill(0); frame[3] = 8; // L1
      slots[2].input(0x47, frame);
      await settled();
      assert.equal(states.at(-1)[0], 'connected');
      assert.match(states.at(-1)[1], /wireless/i);
      assert.deepEqual(reports, [[0x47, frame]]);
      assert.deepEqual(slots[2].writes[0], [1, [0x87, 3, 9, 0, 0, ...Array(58).fill(0)]]);
      slots[1].input(0x47, Array(45).fill(0));
      assert.equal(reports.length, 1, 'Another slot must not mix controller input');
      assert.equal(slots[1].writes.length, 0);
      await client.disconnect();
      assert(slots.every(slot => !slot.opened));
      slots[2].input(0x47, frame);
      assert.equal(reports.length, 1);
    } finally { await client.destroy(); }
  });
}

test('radio power-off clears input immediately and the same slot resumes after power-on', async () => {
  const {client, slots, states, reports} = receiver();
  try {
    await client.connect();
    slots[2].input(0x79, [2]);
    await settled();
    slots[2].input(0x42, Array(45).fill(0));
    assert.equal(reports.length, 1);
    slots[0].input(0x46, [1]); // Unused slot cannot disconnect the selected one.
    assert.equal(states.at(-1)[0], 'connected');
    slots[2].input(0x46, [1]);
    assert.equal(states.at(-1)[0], 'waiting');
    assert(slots[2].opened, 'Keep receiver listening while controller is off');
    slots[0].input(0x79, [2]);
    slots[0].input(0x47, Array(45).fill(0));
    await settled();
    assert.equal(reports.length, 1, 'Never silently switch to a different slot');
    slots[2].input(0x79, [2]);
    await settled();
    slots[2].input(0x47, Array(45).fill(0));
    assert.equal(states.at(-1)[0], 'connected');
    assert.equal(reports.length, 2);
    assert.equal(slots[2].writes.length, 2, 'Reinitialize after radio reconnect');
  } finally { await client.destroy(); }
});

test('receiver unplug/replug reopens authorized interfaces and preserves the chosen slot', async () => {
  const {client, slots, hid, states, reports} = receiver();
  try {
    await client.connect();
    slots[2].input(0x47, Array(45).fill(0)); await settled();
    for (const slot of slots) {
      const event = new Event('disconnect'); event.device = slot; hid.dispatchEvent(event);
    }
    await settled();
    assert.equal(states.at(-1)[0], 'disconnected');
    assert(slots.every(slot => !slot.opened));
    for (const slot of [...slots].reverse()) {
      const event = new Event('connect'); event.device = slot; hid.dispatchEvent(event);
    }
    await settled();
    assert(slots.every(slot => slot.opened));
    slots[0].input(0x47, Array(45).fill(0));
    slots[2].input(0x47, Array(45).fill(0)); await settled();
    assert.equal(states.at(-1)[0], 'connected');
    assert.equal(reports.length, 2);
  } finally { await client.destroy(); }
});

test('power-off during receiver initialization does not restore stale input', async () => {
  const {client, slots, states, reports} = receiver();
  try {
    await client.connect();
    let complete;
    slots[1].sendFeatureReport = () => new Promise(resolve => { complete = resolve; });
    slots[1].input(0x47, Array(45).fill(0));
    slots[1].input(0x79, [1]);
    complete(); await settled();
    assert.equal(states.at(-1)[0], 'waiting');
    assert.equal(reports.length, 0);
  } finally { await client.destroy(); }
});

test('receiver open failure closes all slots, including a delayed open', async () => {
  const {client, slots, states} = receiver();
  let complete;
  slots[1].open = () => new Promise(resolve => { complete = () => { slots[1].opened = true; resolve(); }; });
  slots[2].open = async () => { throw new Error('Access denied'); };
  try {
    const pending = client.connect();
    await settled();
    complete(); await pending; await settled();
    assert.equal(states.at(-1)[0], 'error');
    assert(slots.every(slot => !slot.opened));
  } finally { await client.destroy(); }
});
