import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {detectOS, templatePaths, validateCatalog, loadFiles, saveFiles} from '../web/downloads.js';
const bytes = new TextEncoder().encode('a loose vdf template').buffer;
const entry = {controller:'Steam Deck', variant:'default', version:'90.75', filename:'deck_90.75.vdf',
  bytes:bytes.byteLength, sha256:createHash('sha256').update(new Uint8Array(bytes)).digest('hex')};
const files = [{entry, bytes}];
function directory(existing = new Map()) {
  const writes = [];
  return {writes, async getFileHandle(name, options) {
    if (!options?.create && !existing.has(name)) throw new DOMException('Missing', 'NotFoundError');
    return {getFile:async()=>new Blob([existing.get(name)]), createWritable:async()=>({
      write:async data=>writes.push([name, data]), close:async()=>{}, abort:async()=>{},
    })};
  }};
}
test('OS hints prefer current platform and include SteamOS, Flatpak and the macOS app bundle', () => {
  for (const [platform, expected] of [['Win32','windows'],['MacIntel','macos'],['Linux x86_64','linux'],['','other']])
    assert.equal(detectOS({platform}),expected);
  assert.equal(detectOS({platform:'Linux',userAgent:'Android'}),'other');
  assert.equal(detectOS({platform:'MacIntel',userAgentData:{platform:'Windows'}}),'windows');
  assert(templatePaths.macos[0][1].includes('Steam.AppBundle/Steam/Contents/MacOS'));
  assert(templatePaths.linux.some(([,path])=>path.startsWith('/home/deck/')));
  assert(templatePaths.linux.some(([,path])=>path.includes('com.valvesoftware.Steam')));
});
test('catalog rejects traversal, duplicates and invalid metadata', () => {
  assert.deepEqual(validateCatalog({layouts:[entry]}),[entry]);
  for (const filename of ['../escape.vdf','folder/file.vdf','file\\name.vdf','https://host/a.vdf','x.json'])
    assert.throws(()=>validateCatalog({layouts:[{...entry,filename}]}));
  assert.throws(()=>validateCatalog({layouts:[entry,entry]}));
  assert.throws(()=>validateCatalog({layouts:[]}));
});
test('downloads verify exact release bytes and preserve subdirectory hosting', async () => {
  let url;
  const result=await loadFiles([entry],new URL('https://example.com/viewer/layouts/'),async value=>{
    url=value.href; return new Response(bytes);
  });
  assert.equal(url,'https://example.com/viewer/layouts/deck_90.75.vdf');
  assert.deepEqual(result,files);
  await assert.rejects(loadFiles([entry],new URL('https://example.com/'),async()=>new Response('broken')),/verification/);
  await assert.rejects(loadFiles([entry],new URL('https://example.com/'),async()=>new Response('',{status:404})),/Could not download/);
});
test('folder save creates loose files, skips identical versions and preserves edited files', async () => {
  const empty=directory();
  assert.deepEqual(await saveFiles(empty,files),{saved:1,unchanged:0});
  assert.deepEqual(empty.writes,[[entry.filename,bytes]]);
  const same=directory(new Map([[entry.filename,bytes]]));
  assert.deepEqual(await saveFiles(same,files),{saved:0,unchanged:1});
  assert.equal(same.writes.length,0);
  const edited=directory(new Map([[entry.filename,'custom layout']]));
  await assert.rejects(saveFiles(edited,[{entry:{...entry,filename:'new.vdf'},bytes},...files]),/different contents/);
  assert.equal(edited.writes.length,0,'Check collisions before writing any file');
});
test('failed writes abort and report only completed files', async () => {
  let aborted=false;
  const folder={getFileHandle:async(name,options)=>{
    if(!options) throw new DOMException('Missing','NotFoundError');
    return {createWritable:async()=>({write:async()=>{throw new Error('Disk full');},close:async()=>{},abort:async()=>{aborted=true;}})};
  }};
  let completed=0;
  await assert.rejects(saveFiles(folder,files,count=>{completed=count;}),/Disk full/);
  assert(aborted); assert.equal(completed,0);
});
