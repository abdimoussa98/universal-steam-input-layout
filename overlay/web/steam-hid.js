// Browser permissions and raw HID transport only. Rust decodes reports and owns
// controller state, bindings and gesture timing. No input is sent to a server.
const FILTERS = [{vendorId: 0x28de, productId: 0x1302}];
const INPUT_REPORTS = new Set([0x42, 0x45, 0x47]);
function hasInput(collections) {
  return collections.some(c => (c.inputReports || []).some(r => INPUT_REPORTS.has(r.reportId))
    || hasInput(c.children || []));
}
function supported(device) {
  return device.vendorId === 0x28de && device.productId === 0x1302
    && hasInput(device.collections || []);
}

export class SteamHid {
  constructor(onInput, onState, {hid = globalThis.navigator?.hid, secure = globalThis.isSecureContext} = {}) {
    this.hid = hid;
    this.available = !!secure && !!hid;
    this.supportMessage = !secure ? 'Open this viewer over HTTPS to connect a controller.'
      : !hid ? 'Direct USB connection needs WebHID. Use a desktop browser with WebHID enabled, such as Chrome or Edge.'
      : 'Connect your Steam Controller 2 by USB, then choose it in the browser picker. No helper or Steam required.';
    this.onInput = onInput;
    this.onState = onState;
    this.generation = 0;
    this.device = null;
    this.wantedDevice = null;
    this.busy = false;
    this.stopped = false;
    this.timer = null;
    this.read = event => {
      if (!this.stopped && event.target === this.device) {
        this.onInput?.(event.reportId, new Uint8Array(event.data.buffer, event.data.byteOffset, event.data.byteLength));
      }
    };
    this.removed = event => {
      if (event.device === this.device || event.device === this.wantedDevice) {
        ++this.generation;
        this.busy = false;
        this.release();
        this.emit('disconnected', 'Controller unplugged. Reconnect it to resume.');
      }
    };
    this.added = event => {
      if (!this.stopped && !this.device && !this.busy && event.device === this.wantedDevice) {
        this.busy = true;
        const generation = ++this.generation;
        this.open(event.device, generation).catch(error => this.failed(error, generation));
      }
    };
    hid?.addEventListener('disconnect', this.removed);
    hid?.addEventListener('connect', this.added);
  }
  emit(state, message) {
    if (!this.stopped) this.onState?.(state, message);
  }
  async connect() {
    if (this.stopped || this.busy) return;
    if (!this.available) { this.emit('error', this.supportMessage); return; }
    this.busy = true;
    const generation = ++this.generation;
    this.emit('requesting', 'Choose your Steam Controller in the browser picker.');
    try {
      // Invoke directly from the button action, before awaiting any other work.
      const devices = await this.hid.requestDevice({filters: FILTERS});
      if (this.stopped || generation !== this.generation) return;
      if (!devices.length) {
        this.busy = false;
        this.emit('idle', 'No controller selected. If no picker appeared, allow HID device requests in your browser’s site settings, then try again.');
        return;
      }
      // Composite USB devices can return keyboard/mouse interfaces as well.
      const device = devices.find(supported);
      if (!device) throw new Error('The selected device has no supported Steam Controller input interface. Use the Steam Controller 2 USB connection.');
      this.wantedDevice = device;
      await this.open(device, generation);
    } catch (error) { await this.failed(error, generation); }
  }
  async open(device, generation) {
    await device.open();
    if (this.stopped || generation !== this.generation) { await device.close(); return; }
    this.device = device;
    device.addEventListener('inputreport', this.read);
    // Match SDL's transient Triton setting: stop desktop mouse emulation while
    // connected. The controller's watchdog restores it when these writes stop.
    const data = new Uint8Array(63);
    data.set([0x87, 3, 9, 0, 0]); // SET_SETTINGS_VALUES, LIZARD_MODE = OFF.
    await device.sendFeatureReport(1, data);
    if (this.stopped || generation !== this.generation) { await device.close(); return; }
    this.timer = setInterval(() => {
      if (this.writing || this.device !== device) return;
      this.writing = true;
      device.sendFeatureReport(1, data)
        .catch(error => this.failed(error, generation))
        .finally(() => { this.writing = false; });
    }, 3000);
    this.busy = false;
    this.emit('connected', 'Steam Controller connected directly to this browser.');
  }
  async failed(error, generation) {
    if (this.stopped || generation !== this.generation) return;
    this.busy = false;
    await this.release();
    if (this.stopped || generation !== this.generation) return;
    const message = error?.name === 'NotAllowedError' || error?.name === 'SecurityError'
      ? 'Controller access was blocked. Allow HID device requests in this site’s browser settings and try again.'
      : `Could not connect to the controller: ${error?.message || error}. Reconnect USB and try Connect controller again.`;
    this.emit('error', message);
  }
  release() {
    clearInterval(this.timer);
    this.timer = null;
    const device = this.device;
    this.device = null;
    if (device) {
      device.removeEventListener('inputreport', this.read);
      return device.close().catch(() => {});
    }
    return Promise.resolve();
  }
  async disconnect() {
    const generation = ++this.generation;
    this.busy = true;
    this.wantedDevice = null;
    this.emit('disconnecting', 'Closing the controller connection…');
    await this.release();
    if (generation !== this.generation) return;
    this.busy = false;
    this.emit('disconnected', 'Controller disconnected. Click Connect controller to choose it again.');
  }
  destroy() {
    this.stopped = true;
    this.onInput = null;
    this.onState = null;
    this.hid?.removeEventListener('disconnect', this.removed);
    this.hid?.removeEventListener('connect', this.added);
    return this.disconnect();
  }
}
