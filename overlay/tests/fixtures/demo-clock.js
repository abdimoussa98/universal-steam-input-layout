// Browser-test clock only: the packaged app and its input API are unchanged.
// Eframe and the adapters read performance.now(). Rendering and WebDriver may
// take arbitrarily long without turning a simulated short touch into a hold.
(() => {
  const realNow = performance.now.bind(performance);
  const raf = window.requestAnimationFrame.bind(window);
  let frozen = null, offset = 0, frameDelay = 0, delayedFrame;
  const now = () => frozen ?? realNow() - offset;
  Object.defineProperty(performance, 'now', {value: now, configurable: true});
  window.requestAnimationFrame = callback => raf(timestamp => {
    if (frameDelay && timestamp !== delayedFrame) {
      delayedFrame = timestamp;
      const start = realNow();
      while (realNow() - start < frameDelay) { /* Simulate one slow paint per frame. */ }
    }
    callback(timestamp);
  });
  window.demoClock = {
    realNow,
    begin(delay = 0) {
      if (frozen !== null) throw new Error('Browser clock is already controlled');
      frozen = now();
      frameDelay = delay;
    },
    advance(ms) {
      if (frozen === null || !Number.isFinite(ms) || ms < 0) throw new Error('Invalid clock advance');
      frozen += ms;
    },
    end() {
      // Preserve monotonicity when returning to the real clock: elapsed test
      // execution time must not expire a pending layout gesture on return.
      if (frozen !== null) offset = realNow() - frozen;
      frozen = null;
      frameDelay = 0;
    },
  };
})();
