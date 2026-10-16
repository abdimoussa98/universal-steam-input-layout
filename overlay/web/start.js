// Page bootstrap only. State, controller input, binding resolution and UI are Rust.
const status = document.querySelector('#status');
try {
  const { default: init, WebHandle } = await import('./pkg/keybind_overlay.js');
  await init();
  const app = new WebHandle();
  await app.start(document.querySelector('#viewer'));
  window.keybindApp = app;
  status.remove();
  window.addEventListener('pagehide', (event) => { if (!event.persisted) app.destroy(); });
} catch (error) {
  status.textContent = `Could not start the viewer.\n${error}\nUse a browser with WebAssembly and WebGL enabled, and serve this folder over HTTPS or localhost.`;
  console.error(error);
}
