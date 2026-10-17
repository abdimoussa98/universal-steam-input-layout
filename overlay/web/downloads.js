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
const repository = 'abdimoussa98/universal-steam-input-layout';
const api = `https://api.github.com/repos/${repository}`;
const controllers = {ibex: ['Steam Controller 2', 'ibex_'], neptune: ['Steam Deck', ''], dse: ['DualSense Edge', 'dse_']};
function releaseInfo(tag) {
  const match = /^(ibex|neptune|dse)-v(\d+(?:\.\d+)+)$/.exec(tag || '');
  return match && {id: match[1], version: match[2]};
}
function newer(a, b) {
  const left = a.split('.').map(Number), right = b.split('.').map(Number);
  for (let i = 0; i < Math.max(left.length, right.length); i++) {
    if ((left[i] || 0) !== (right[i] || 0)) return (left[i] || 0) > (right[i] || 0);
  }
  return false;
}
function filenameFor(id, variant, version) {
  return `${controllers[id][1]}single-set-${variant}_hold-gyro_${version}.vdf`;
}
export function layoutUrl(entry, base) {
  if (!entry.release) return new URL(entry.filename, base);
  const {id, version} = releaseInfo(entry.release);
  return new URL(`https://raw.githubusercontent.com/${repository}/${entry.release}/versions/${id}/${version}/${entry.filename}`);
}
export async function latestPublishedLayouts(fetcher = fetch) {
  const get = async url => {
    const response = await fetcher(url, {cache: 'no-store', signal: AbortSignal.timeout(10000)});
    if (!response.ok) throw new Error('GitHub releases are unavailable.');
    return response.json();
  };
  const latest = {};
  // Releases are sorted by publication time, not version or controller. Include
  // all pages so backfilled releases cannot hide a newer version.
  for (let page = 1; ; page++) {
    if (page > 100) throw new Error('Could not finish checking releases.');
    const releases = await get(`${api}/releases?per_page=100&page=${page}`);
    if (!Array.isArray(releases)) throw new Error('Invalid release list.');
    for (const release of releases) {
      const info = releaseInfo(release.tag_name);
      if (info && !release.draft && !release.prerelease
        && (!latest[info.id] || newer(info.version, latest[info.id].version)))
        latest[info.id] = {...info, tag: release.tag_name};
    }
    if (releases.length < 100) break;
  }
  const groups = await Promise.all(Object.keys(controllers).map(async id => {
    const release = latest[id];
    if (!release) throw new Error(`No published release for ${id}.`);
    const files = await get(`${api}/contents/versions/${id}/${release.version}?ref=${release.tag}`);
    if (!Array.isArray(files)) throw new Error('Invalid release files.');
    return ['default', 'alternative'].map(variant => {
      const filename = filenameFor(id, variant, release.version);
      const file = files.find(file => file.name === filename && file.type === 'file');
      return {controller: controllers[id][0], variant, version: release.version, filename,
        release: release.tag, bytes: file?.size, git_sha1: file?.sha};
    });
  }));
  return validateCatalog({layouts: groups.flat()});
}
export async function currentLayouts(assetUrl, fetcher = fetch) {
  try {
    return {entries: await latestPublishedLayouts(fetcher), live: true};
  } catch {
    const response = await fetcher(assetUrl('./layouts/index.json'), {cache: 'no-store'});
    if (!response.ok) throw new Error('Could not check releases or load bundled layouts. Close this panel and try again.');
    return {entries: validateCatalog(await response.json()), live: false};
  }
}
export function validateCatalog(catalog) {
  const entries = catalog?.layouts;
  const names = new Set();
  if (!Array.isArray(entries) || !entries.length) throw new Error('No layouts are available.');
  for (const entry of entries) {
    const release = releaseInfo(entry.release);
    const verified = entry.release
      ? release && entry.version === release.version && entry.controller === controllers[release.id][0]
        && entry.filename === filenameFor(release.id, entry.variant, release.version) && /^[a-f0-9]{40}$/.test(entry.git_sha1)
      : /^[a-f0-9]{64}$/.test(entry.sha256);
    if (!/^[a-z0-9][a-z0-9_.-]*\.vdf$/.test(entry.filename) || names.has(entry.filename)
      || !verified || !Number.isSafeInteger(entry.bytes) || entry.bytes <= 0
      || !['default', 'alternative'].includes(entry.variant) || typeof entry.controller !== 'string'
      || !/^\d+(\.\d+)+$/.test(entry.version)) throw new Error('Invalid layout download list.');
    names.add(entry.filename);
  }
  return entries;
}
export async function loadFiles(entries, base, fetcher = fetch) {
  return Promise.all(entries.map(async entry => {
    const response = await fetcher(layoutUrl(entry, base), {signal: AbortSignal.timeout(20000)});
    if (!response.ok) throw new Error(`Could not download ${entry.filename}. Try again.`);
    const bytes = await response.arrayBuffer();
    const sha256 = await hash(bytes);
    let matches = sha256 === entry.sha256;
    if (entry.release) {
      // GitHub's contents API identifies the exact tagged Git blob. Verify its
      // header and bytes, then retain SHA-256 for local-file conflict checks.
      const blob = await new Blob([`blob ${bytes.byteLength}\0`, bytes]).arrayBuffer();
      const sha1 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-1', blob)),
        n => n.toString(16).padStart(2, '0')).join('');
      matches = sha1 === entry.git_sha1;
    }
    if (bytes.byteLength !== entry.bytes || !matches)
      throw new Error(`Download verification failed for ${entry.filename}. Reload the viewer and try again.`);
    return {entry: {...entry, sha256}, bytes};
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
    await writeFile(handle, bytes);
    saved++;
    progress(saved, unchanged);
  }
  return {saved, unchanged};
}
async function writeFile(handle, bytes) {
  const stream = await handle.createWritable();
  try { await stream.write(bytes); await stream.close(); }
  catch (error) { await stream.abort().catch(() => {}); throw error; }
}

export function installDownloads(assetUrl) {
  const dialog = document.querySelector('#downloads');
  const list = dialog.querySelector('.layout-list');
  const status = dialog.querySelector('[role=status]');
  const save = dialog.querySelector('#save-layouts');
  const close = dialog.querySelector('.close-downloads');
  const os = dialog.querySelector('#template-os');
  const paths = dialog.querySelector('.template-paths');
  const source = document.createElement('p'); source.className = 'download-source';
  list.before(source);
  const demoIdentity = document.createElement('p'); demoIdentity.className = 'demo-identity';
  list.before(demoIdentity);
  let entries, busy = false, loadGeneration = 0;
  const supported = isSecureContext && typeof window.showDirectoryPicker === 'function';
  const saveAsSupported = isSecureContext && typeof window.showSaveFilePicker === 'function';
  save.hidden = !supported;
  dialog.querySelector('.download-help').textContent = (supported
    ? 'Choose a folder to save all six files together. ' : '') + (saveAsSupported
    ? 'Select a variant below to choose its filename and save location.'
    : 'Download each file below. To choose a folder for each file, enable “Ask where to save” in your browser’s download settings. File pickers are available in Chrome or Edge over HTTPS or localhost.');
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
    const generation = ++loadGeneration;
    entries = null;
    list.replaceChildren(); source.textContent = '';
    save.disabled = true;
    status.textContent = 'Checking published releases…';
    try {
      const result = await currentLayouts(assetUrl);
      if (generation !== loadGeneration) return;
      entries = result.entries;
      source.textContent = result.live ? 'Latest published releases · checked just now on GitHub.'
        : 'Could not check GitHub. Showing bundled versions, which may be older. Reopen this panel to retry.';
      for (const controller of new Set(entries.map(entry => entry.controller))) {
        const card = document.createElement('section');
        const title = document.createElement('h3');
        title.textContent = Object.entries(controllers).find(([, [label]]) => label === controller)?.[0] || controller;
        card.append(title);
        for (const entry of entries.filter(entry => entry.controller === controller)) {
          const link = document.createElement('a');
          link.href = layoutUrl(entry, assetUrl('./layouts/'));
          link.download = entry.filename;
          link.textContent = `${entry.variant === 'default' ? 'Default' : 'Alternative'} · v${entry.version}`;
          if (entry.release || saveAsSupported) link.onclick = async event => {
            event.preventDefault();
            if (busy) return;
            busy = true; save.disabled = true; close.disabled = true;
            let choosing = saveAsSupported;
            try {
              // Open before any fetch/await can consume the click's user activation.
              const handle = saveAsSupported ? await window.showSaveFilePicker({
                id: 'steam-layout-file', startIn: 'downloads', suggestedName: entry.filename,
                types: [{description: 'Steam Input template', accept: {'application/octet-stream': ['.vdf']}}],
              }) : null;
              choosing = false;
              status.textContent = `Downloading ${entry.filename}…`;
              const [file] = await loadFiles([entry], assetUrl('./layouts/'));
              if (handle) {
                await writeFile(handle, file.bytes);
                status.textContent = `Saved ${handle.name}.`;
                return;
              }
              const url = URL.createObjectURL(new Blob([file.bytes], {type: 'application/octet-stream'}));
              const download = document.createElement('a');
              download.href = url; download.download = entry.filename;
              document.body.append(download); download.click(); download.remove();
              setTimeout(() => URL.revokeObjectURL(url), 30000);
              status.textContent = `Sent ${entry.filename} to your browser’s downloads.`;
            } catch (error) {
              status.textContent = choosing && error.name === 'AbortError'
                ? 'File selection canceled. No file saved.'
                : `Could not save the file. ${error.message || 'Choose a writable location and try again.'}`;
            }
            finally { busy = false; save.disabled = false; close.disabled = false; }
          };
          card.append(link);
        }
        list.append(card);
      }
      status.textContent = `${entries.length} loose VDF files · no archive to unpack.`;
      save.disabled = false;
    } catch (error) { if (generation === loadGeneration) status.textContent = error.message; }
  }
  window.openLayoutDownloads = () => {
    if (dialog.open) return;
    const demo = window.keybindApp && JSON.parse(window.keybindApp.diagnostic_snapshot()).demo;
    demoIdentity.textContent = demo ? `The demo runs ${demo.layout}. Newer downloads may differ from this built-in version.` : '';
    dialog.showModal();
    void load();
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
