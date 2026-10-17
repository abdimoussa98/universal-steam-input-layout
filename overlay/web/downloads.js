// Loose Steam templates and browser-owned save dialogs. No paths leave the device.
export function detectOS(nav = navigator) {
  const platform = nav.userAgentData?.platform || nav.platform || nav.userAgent || '';
  if (/android|iphone|ipad/i.test(nav.userAgent || '')) return 'other';
  if (/win/i.test(platform)) return 'windows';
  if (/mac/i.test(platform)) return 'macos';
  if (/linux|steam/i.test(platform)) return 'linux';
  return 'other';
}
export const templatePaths = {
  windows: [['Steam', String.raw`C:\Program Files (x86)\Steam\controller_base\templates`]],
  macos: [['Steam', '~/Library/Application Support/Steam/Steam.AppBundle/Steam/Contents/MacOS/controller_base/templates']],
  linux: [['Steam / SteamOS', '~/.steam/steam/controller_base/templates'],
    ['Alternate Steam install', '~/.local/share/Steam/controller_base/templates'],
    ['Steam Deck', '/home/deck/.steam/steam/controller_base/templates'],
    ['Flatpak Steam', '~/.var/app/com.valvesoftware.Steam/.local/share/Steam/controller_base/templates']],
  other: [['Inside your Steam installation', 'controller_base/templates']],
};
const hash = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
  n => n.toString(16).padStart(2, '0')).join('');
export function validateCatalog(catalog) {
  const entries = catalog?.layouts;
  const names = new Set();
  if (!Array.isArray(entries) || !entries.length) throw new Error('No layouts are available.');
  for (const entry of entries) {
    if (!/^[a-z0-9][a-z0-9_.-]*\.vdf$/.test(entry.filename) || names.has(entry.filename)
      || !/^[a-f0-9]{64}$/.test(entry.sha256) || !Number.isSafeInteger(entry.bytes) || entry.bytes <= 0
      || !['default', 'alternative'].includes(entry.variant) || typeof entry.controller !== 'string'
      || !/^\d+(\.\d+)+$/.test(entry.version)) throw new Error('Invalid layout download list.');
    names.add(entry.filename);
  }
  return entries;
}
export async function loadFiles(entries, base, fetcher = fetch) {
  return Promise.all(entries.map(async entry => {
    const response = await fetcher(new URL(entry.filename, base));
    if (!response.ok) throw new Error(`Could not download ${entry.filename}. Try again.`);
    const bytes = await response.arrayBuffer();
    if (bytes.byteLength !== entry.bytes || await hash(bytes) !== entry.sha256)
      throw new Error(`Download verification failed for ${entry.filename}. Reload the viewer and try again.`);
    return {entry, bytes};
  }));
}
export async function saveFiles(directory, files, progress = () => {}) {
  // Check every existing filename before writing anything. Preserve edited templates.
  const pending = [];
  let unchanged = 0;
  for (const file of files) {
    let existing;
    try { existing = await directory.getFileHandle(file.entry.filename); }
    catch (error) { if (error.name !== 'NotFoundError') throw error; }
    if (existing) {
      const bytes = await (await existing.getFile()).arrayBuffer();
      if (await hash(bytes) !== file.entry.sha256)
        throw new Error(`${file.entry.filename} already exists with different contents. Choose another folder or rename the existing file.`);
      unchanged++;
    } else pending.push(file);
  }
  let saved = 0;
  for (const {entry, bytes} of pending) {
    const handle = await directory.getFileHandle(entry.filename, {create: true});
    const stream = await handle.createWritable();
    try { await stream.write(bytes); await stream.close(); }
    catch (error) { await stream.abort().catch(() => {}); throw error; }
    saved++;
    progress(saved, unchanged);
  }
  return {saved, unchanged};
}

export function installDownloads(assetUrl) {
  const dialog = document.querySelector('#downloads');
  const list = dialog.querySelector('.layout-list');
  const status = dialog.querySelector('[role=status]');
  const save = dialog.querySelector('#save-layouts');
  const close = dialog.querySelector('.close-downloads');
  const os = dialog.querySelector('#template-os');
  const paths = dialog.querySelector('.template-paths');
  let entries, busy = false;
  const supported = isSecureContext && typeof window.showDirectoryPicker === 'function';
  save.hidden = !supported;
  dialog.querySelector('.download-help').textContent = supported
    ? 'Choose a folder to save all six files together, or download a single variant below.'
    : 'Download each file below. To choose a folder for each file, enable “Ask where to save” in your browser’s download settings. Folder selection for all files is available in Chrome or Edge over HTTPS.';
  os.value = detectOS();
  function renderPaths() {
    paths.replaceChildren();
    for (const [label, path] of templatePaths[os.value]) {
      const row = document.createElement('div');
      const title = document.createElement('span'); title.textContent = label;
      const code = document.createElement('code'); code.textContent = path;
      const copy = document.createElement('button'); copy.type = 'button'; copy.textContent = 'Copy';
      copy.setAttribute('aria-label', `Copy ${label} template path`);
      copy.onclick = async () => {
        try { await navigator.clipboard.writeText(path); status.textContent = 'Template path copied.'; }
        catch { status.textContent = 'Select the path text and copy it manually.'; }
      };
      row.append(title, code, copy); paths.append(row);
    }
  }
  os.onchange = renderPaths; renderPaths();
  close.onclick = () => dialog.close();
  dialog.addEventListener('cancel', event => { if (busy) event.preventDefault(); });
  // Typing in this dialog must not activate the viewer's F-key/mode shortcuts.
  for (const type of ['keydown', 'keyup']) dialog.addEventListener(type, event => event.stopPropagation());
  dialog.addEventListener('close', () => document.querySelector('#viewer').focus());
  async function load() {
    save.disabled = true;
    status.textContent = 'Loading the latest layouts…';
    try {
      const response = await fetch(assetUrl('./layouts/index.json'));
      if (!response.ok) throw new Error('Could not load the layouts. Close this panel and try again.');
      entries = validateCatalog(await response.json());
      list.replaceChildren();
      for (const controller of new Set(entries.map(entry => entry.controller))) {
        const card = document.createElement('section');
        const title = document.createElement('h3'); title.textContent = controller; card.append(title);
        for (const entry of entries.filter(entry => entry.controller === controller)) {
          const link = document.createElement('a');
          link.href = assetUrl(`./layouts/${entry.filename}`);
          link.download = entry.filename;
          link.textContent = `${entry.variant === 'default' ? 'Default' : 'Alternative'} · v${entry.version}`;
          card.append(link);
        }
        list.append(card);
      }
      status.textContent = `${entries.length} loose VDF files · latest releases included with this viewer.`;
      save.disabled = false;
    } catch (error) { status.textContent = error.message; }
  }
  window.openLayoutDownloads = () => {
    if (!dialog.open) dialog.showModal();
    if (!entries) void load();
  };
  save.onclick = async () => {
    if (busy || !entries) return;
    busy = true; save.disabled = true; close.disabled = true;
    let saved = 0, choosing = true;
    try {
      // Must happen directly in the click handler, before fetching any files.
      const directory = await window.showDirectoryPicker({id: 'steam-layout-templates', mode: 'readwrite', startIn: 'downloads'});
      choosing = false;
      status.textContent = 'Preparing layouts…';
      const files = await loadFiles(entries, assetUrl('./layouts/'));
      const result = await saveFiles(directory, files, count => {
        saved = count; status.textContent = `Saved ${count} files…`;
      });
      status.textContent = `Saved ${result.saved} files to ${directory.name}.${result.unchanged ? ` ${result.unchanged} identical files already present.` : ''}`;
    } catch (error) {
      status.textContent = error.name === 'AbortError' && choosing ? 'Folder selection canceled. No files saved.'
        : `${saved ? `${saved} files saved before stopping. ` : 'No files saved. '}${error.message || 'Could not save files. Choose a writable folder and try again.'}`;
    } finally { busy = false; save.disabled = false; close.disabled = false; }
  };
}
