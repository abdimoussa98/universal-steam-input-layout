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
    async open() { this.opened = true; this.timer = setInterval(() => this.emit(), 8); }
    async close() { this.opened = false; clearInterval(this.timer); }
    async sendFeatureReport() {}
    emit() {
      if (!this.opened) return;
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
  }
  class Hid extends EventTarget {
    cancel = false;
    deny = false;
    requests = [];
    device = new Device();
    async requestDevice(options) {
      this.requests.push({options, activated: navigator.userActivation.isActive});
      if (this.deny) throw new DOMException('Permission denied', 'NotAllowedError');
      return this.cancel ? [] : [this.device];
    }
    async getDevices() { return [this.device]; }
    remove() {
      this.device.close();
      const event = new Event('disconnect'); event.device = this.device;
      this.dispatchEvent(event);
    }
    reconnect() {
      const event = new Event('connect'); event.device = this.device;
      this.dispatchEvent(event);
    }
  }
  window.fakeHid = new Hid();
  Object.defineProperty(navigator, 'hid', {value: window.fakeHid, configurable: true});
})();
