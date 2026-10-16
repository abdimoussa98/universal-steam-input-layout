// Browser permissions and raw HID transport only. Rust decodes reports and owns
// controller state, bindings and gesture timing. No input is sent to a server.
// SDL 3.4.18 usb_ids.h: Triton USB, Proteus receiver, Nereid receiver.
const PRODUCTS = [0x1302, 0x1304, 0x1305];
const FILTERS = PRODUCTS.map(productId => ({vendorId: 0x28de, productId}));
const INPUT_REPORTS = new Set([0x42, 0x45, 0x47]);
const WIRELESS_STATUS = new Set([0x46, 0x79]);
const isReceiver = device => device.productId !== 0x1302;
function hasInput(collections) {
  return collections.some(c => (c.inputReports || []).some(r => INPUT_REPORTS.has(r.reportId))
    || hasInput(c.children || []));
}
function supported(device) {
  return device.vendorId === 0x28de && PRODUCTS.includes(device.productId)
    && hasInput(device.collections || []);
}

export class SteamHid {
  constructor(onInput, onState, {hid = globalThis.navigator?.hid, secure = globalThis.isSecureContext} = {}) {
    this.hid = hid;
    this.available = !!secure && !!hid;
    this.supportMessage = !secure ? 'Open this viewer over HTTPS to connect a controller.'
      : !hid ? 'Direct USB connection needs WebHID. Use a desktop browser with WebHID enabled, such as Chrome or Edge.'
      : 'Connect your Steam Controller 2 by USB cable or wireless receiver, then choose it in the browser picker. No helper or Steam required.';
    this.onInput = onInput;
    this.onState = onState;
    this.generation = 0;
    this.epoch = 0;
    this.device = null;
    this.wantedDevices = new Set();
    this.devices = new Set();
    this.opening = new Map();
    this.initialized = false;
    this.activation = null;
    this.pendingReport = null;
    this.busy = false;
    this.stopped = false;
    this.timer = null;
    this.read = event => this.report(event);
    this.removed = event => {
      if (this.wantedDevices.has(event.device)) {
        ++this.generation;
        this.busy = false;
        // Preserve the selected receiver slot across USB reconnects.
        this.release(true);
        this.emit('disconnected', 'Controller or receiver unplugged. Reconnect it to resume.');
      }
    };
    this.added = event => {
      if (!this.stopped && !this.busy && this.wantedDevices.has(event.device)) {
        const generation = this.generation;
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
      // A receiver has up to four controller interfaces. Listen to them all,
      // excluding keyboard/mouse/management interfaces, and follow the first
      // active controller. Do not assume the first returned slot is occupied.
      const inputs = devices.filter(supported);
      if (!inputs.length) throw new Error('The selected device has no supported Steam Controller 2 input interface. Use its USB cable or wireless receiver.');
      this.device = null;
      this.wantedDevices = new Set(isReceiver(inputs[0]) ? inputs : inputs.slice(0, 1));
      await Promise.all([...this.wantedDevices].map(device => this.open(device, generation)));
      if (generation === this.generation) this.busy = false;
    } catch (error) { await this.failed(error, generation); }
  }
  async open(device, generation) {
    if (this.devices.has(device) || this.opening.get(device) === generation) return;
    this.opening.set(device, generation);
    try {
      await device.open();
      if (this.stopped || generation !== this.generation) { await device.close(); return; }
      this.devices.add(device);
      device.addEventListener('inputreport', this.read);
      if (isReceiver(device)) {
        if (!this.initialized && !this.activation) this.waiting();
      } else {
        await this.activate(device);
      }
    } finally {
      if (this.opening.get(device) === generation) this.opening.delete(device);
    }
  }
  waiting() {
    this.emit('waiting', this.device
      ? 'Receiver connected. Turn on the selected controller to resume. To choose another, disconnect and connect again.'
      : 'Receiver connected. Turn on your paired controller. The first active controller will be shown.');
  }
  report(event) {
    const device = event.target;
    if (this.stopped || !this.devices.has(device) || (this.device && device !== this.device)) return;
    const bytes = new Uint8Array(event.data.buffer, event.data.byteOffset, event.data.byteLength);
    if (isReceiver(device)) {
      // SDL's TritonWirelessStatus_t: one byte, 1 = off, 2 = connected.
      if (WIRELESS_STATUS.has(event.reportId)) {
        if (bytes[0] === 1 && device === this.device) {
          this.suspend();
          this.waiting();
        } else if (bytes[0] === 2) {
          this.activate(device);
        }
        return;
      }
      if (!INPUT_REPORTS.has(event.reportId)) return;
      // Unrelated/truncated data must not claim an empty receiver slot.
      if (!this.device && bytes.length < 45) return;
    }
    if (!this.initialized) {
      this.pendingReport = [event.reportId, bytes.slice()];
      this.activate(device);
    } else {
      this.onInput?.(event.reportId, bytes);
    }
  }
  activate(device) {
    if (this.initialized || this.activation || (this.device && device !== this.device)) return this.activation;
    this.device = device;
    const generation = this.generation;
    const epoch = ++this.epoch;
    const current = () => !this.stopped && generation === this.generation && epoch === this.epoch;
    // Match SDL's transient Triton setting: stop desktop mouse emulation while
    // connected. The controller's watchdog restores it when these writes stop.
    const data = new Uint8Array(63);
    data.set([0x87, 3, 9, 0, 0]); // SET_SETTINGS_VALUES, LIZARD_MODE = OFF.
    const activation = (async () => {
      try {
        await device.sendFeatureReport(1, data);
        if (!current()) return;
        this.initialized = true;
        let writing = false;
        this.timer = setInterval(() => {
          if (writing || !current()) return;
          writing = true;
          device.sendFeatureReport(1, data)
            .catch(error => { if (current()) return this.failed(error, generation); })
            .finally(() => { writing = false; });
        }, 3000);
        this.emit('connected', isReceiver(device)
          ? 'Steam Controller connected through its wireless receiver.'
          : 'Steam Controller connected directly to this browser.');
        const pending = this.pendingReport;
        this.pendingReport = null;
        if (pending) this.onInput?.(...pending);
      } catch (error) {
        if (current()) await this.failed(error, generation);
      }
    })();
    this.activation = activation;
    activation.finally(() => { if (this.activation === activation) this.activation = null; });
    return activation;
  }
  async failed(error, generation) {
    if (this.stopped || generation !== this.generation) return;
    const failedGeneration = ++this.generation;
    this.busy = false;
    this.wantedDevices.clear();
    await this.release();
    if (this.stopped || failedGeneration !== this.generation) return;
    const message = error?.name === 'NotAllowedError' || error?.name === 'SecurityError'
      ? 'Controller access was blocked. Allow HID device requests in this site’s browser settings and try again.'
      : `Could not connect to the controller: ${error?.message || error}. Reconnect the controller or receiver and try Connect controller again.`;
    this.emit('error', message);
  }
  suspend() {
    ++this.epoch;
    clearInterval(this.timer);
    this.timer = null;
    this.initialized = false;
    this.activation = null;
    this.pendingReport = null;
  }
  release(keepSelection = false) {
    this.suspend();
    if (!keepSelection) this.device = null;
    const devices = [...this.devices];
    this.devices.clear();
    return Promise.all(devices.map(device => {
      device.removeEventListener('inputreport', this.read);
      return device.close().catch(() => {});
    }));
  }
  async disconnect() {
    const generation = ++this.generation;
    this.busy = true;
    this.wantedDevices.clear();
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
