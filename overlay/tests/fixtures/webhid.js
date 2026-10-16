// Synthetic USB boundary for the real browser/WASM test. Production decoding
// and gesture processing are not replaced.
(() => {
  class Device extends EventTarget {
    vendorId = 0x28de;
    productId = 0x1302;
    productName = 'Steam Controller';
    collections = [{usagePage: 0xff00, inputReports: [{reportId: 0x47}]}];
    opened = false;
    report = new Uint8Array(45);
    constructor(productId = 0x1302) {
      super();
      this.productId = productId;
      this.powered = productId === 0x1302;
    }
    async open() { this.opened = true; this.timer = setInterval(() => this.emit(), 8); }
    async close() { this.opened = false; clearInterval(this.timer); }
    async sendFeatureReport() {}
    emit() {
      if (!this.opened || !this.powered) return;
      const event = new Event('inputreport');
      event.reportId = 0x47;
      event.data = new DataView(this.report.buffer);
      this.dispatchEvent(event);
    }
    frame(buttons = 0, values = {}) {
      this.report = new Uint8Array(45);
      const view = new DataView(this.report.buffer);
      view.setUint32(1, buttons, true);
      for (const [offset, value] of Object.entries(values)) view.setInt16(Number(offset), value, true);
      this.emit();
    }
    radio(on) {
      this.powered = on;
      const event = new Event('inputreport');
      event.reportId = 0x79;
      event.data = new DataView(Uint8Array.of(on ? 2 : 1).buffer);
      if (this.opened) this.dispatchEvent(event);
      this.emit();
    }
  }
  class Hid extends EventTarget {
    cancel = false;
    deny = false;
    requests = [];
    device = new Device();
    get devices() { return this.slots || [this.device]; }
    receiver(productId = 0x1304) {
      this.slots = Array.from({length: 4}, () => new Device(productId));
      this.device = this.slots[2];
    }
    async requestDevice(options) {
      this.requests.push({options, activated: navigator.userActivation.isActive});
      if (this.deny) throw new DOMException('Permission denied', 'NotAllowedError');
      return this.cancel ? [] : this.devices.filter(d => options.filters.some(f => f.vendorId === d.vendorId && f.productId === d.productId));
    }
    async getDevices() { return this.devices; }
    remove() {
      for (const device of this.devices) {
        device.close();
        const event = new Event('disconnect'); event.device = device;
        this.dispatchEvent(event);
      }
    }
    reconnect() {
      for (const device of this.devices) {
        const event = new Event('connect'); event.device = device;
        this.dispatchEvent(event);
      }
    }
  }
  window.fakeHid = new Hid();
  Object.defineProperty(navigator, 'hid', {value: window.fakeHid, configurable: true});
})();
