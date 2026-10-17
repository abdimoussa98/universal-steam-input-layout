// Page bootstrap only. State, controller input, binding resolution and UI are Rust.
const status = document.querySelector('#status');
// A tunnel may cache stable JS/WASM filenames despite the origin's headers.
// Keep every dependency on the version selected by the freshly loaded HTML.
const bundleVersion = new URL(import.meta.url).searchParams.get('v');
const assetUrl = path => {
  const url = new URL(path, import.meta.url);
  if (bundleVersion) url.searchParams.set('v', bundleVersion);
  return url;
};
// Opening a pairing link in an already-open viewer changes only the fragment.
// Recreate the Rust client so the new session/port takes effect.
const initiallyPaired = location.hash.startsWith('#companion=');
window.addEventListener('hashchange', () => {
  if (initiallyPaired || location.hash.startsWith('#companion=')) location.reload();
});
try {
  const { SteamHid } = await import(assetUrl('./steam-hid.js').href);
  window.SteamHid = SteamHid;
  const { default: init, WebHandle } = await import(assetUrl('./pkg/keybind_overlay.js').href);
  await init({module_or_path: assetUrl('./pkg/keybind_overlay_bg.wasm')});
  const app = new WebHandle();
  await app.start(document.querySelector('#viewer'));
  window.keybindApp = app;
  status.remove();
  window.addEventListener('pagehide', (event) => { if (!event.persisted) app.destroy(); });
} catch (error) {
  status.textContent = `Could not start the viewer.\n${error}\nUse a browser with WebAssembly and WebGL enabled, and serve this folder over HTTPS or localhost.`;
  console.error(error);
}
