// Page bootstrap only. State, controller input, binding resolution and UI are Rust.
const status = document.querySelector('#status');
// Audio follows logical feedback events, including multiple events per frame.
// Reset/pause/hide cancel scheduled sounds so resuming never plays a backlog.
let audioContext;
let soundEnabled = false;
let lastSound;
const oscillators = new Set();
window.demoSoundCancel = () => {
  for (const oscillator of oscillators) oscillator.stop();
  oscillators.clear();
  lastSound = undefined;
};
document.addEventListener('visibilitychange', () => {
  if (document.hidden) window.demoSoundCancel();
});
window.demoSoundEnable = enabled => {
  soundEnabled = enabled;
  if (enabled) {
    audioContext ??= new AudioContext();
    audioContext.resume().catch(() => {});
  } else window.demoSoundCancel();
};
window.demoSoundTick = (at, scale, kind) => {
  if (!soundEnabled || document.hidden || audioContext?.state !== 'running') return;
  const time = Math.max(audioContext.currentTime, lastSound && at >= lastSound.at
    ? lastSound.time + (at - lastSound.at) * scale / 1000 : audioContext.currentTime);
  lastSound = {at, time};
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  oscillator.frequency.value = kind === 'beep' ? 1040 : kind === 'haptic' ? 240 : 720;
  gain.gain.setValueAtTime(0.025, time);
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.035);
  oscillator.connect(gain).connect(audioContext.destination);
  oscillators.add(oscillator);
  oscillator.onended = () => oscillators.delete(oscillator);
  oscillator.start(time);
  oscillator.stop(time + 0.04);
};
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
  const { installDownloads } = await import(assetUrl('./downloads.js').href);
  installDownloads(assetUrl);
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
