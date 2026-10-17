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

const repository = 'abdimoussa98/universal-steam-input-layout';
const blobSha = createHash('sha1').update(`blob ${bytes.byteLength}\0`).update(new Uint8Array(bytes)).digest('hex');
function github({version='1.10', offline=false, corrupt=false, paged=false}={}) {
  const calls=[];
  const fetcher=async(url, options)=>{
    url=String(url); calls.push([url,options]);
    if(url.includes('/releases?')) {
      if(offline) return new Response('',{status:403});
      const releases=['ibex','neptune','dse'].flatMap(id=>[
        {tag_name:`${id}-v${version}`}, {tag_name:`${id}-v1.9`},
        {tag_name:`${id}-v99.0`,draft:true}, {tag_name:`${id}-v98.0`,prerelease:true},
      ]);
      return Response.json(paged && url.endsWith('page=1') ? Array(100).fill({tag_name:'unrelated'}) : releases);
    }
    if(url.includes('/contents/versions/')) {
      const [,id,v]=url.match(/versions\/(\w+)\/([\d.]+)/);
      return Response.json(['default','alternative'].map(variant=>({type:'file',
        name:`${id==='neptune'?'':id+'_'}single-set-${variant}_hold-gyro_${v}.vdf`,size:bytes.byteLength,sha:blobSha})));
    }
    if(url.startsWith('https://raw.githubusercontent.com/')) return new Response(corrupt?'wrong bytes':bytes);
    if(url.endsWith('/layouts/index.json')) return Response.json({layouts:[entry]});
    throw new Error(`Unexpected URL: ${url}`);
  };
  return {fetcher,calls};
}
const assetUrl=path=>new URL(path,'https://viewer.test/subdirectory/');
const {latestPublishedLayouts,currentLayouts,layoutUrl}=await import('../web/downloads.js');
test('live downloads choose numeric latest published release per controller, including later pages', async()=>{
  const remote=github({paged:true});
  const entries=await latestPublishedLayouts(remote.fetcher);
  assert.equal(entries.length,6);
  assert(entries.every(e=>e.version==='1.10'));
  assert(remote.calls.some(([url])=>url.endsWith('page=2')));
  assert(remote.calls.every(([,options])=>options.cache==='no-store'));
  const selected=entries[0];
  assert.equal(layoutUrl(selected,assetUrl('./layouts/')).href,
    `https://raw.githubusercontent.com/${repository}/ibex-v1.10/versions/ibex/1.10/${selected.filename}`);
  const files=await loadFiles(entries,assetUrl('./layouts/'),remote.fetcher);
  assert(files.every(f=>f.entry.sha256===entry.sha256));
  assert.deepEqual(await saveFiles(directory(),files),{saved:6,unchanged:0});
  await assert.rejects(loadFiles(entries,assetUrl('./layouts/'),github({corrupt:true}).fetcher),/verification/);
});
test('opening downloads rechecks releases without rebuilding and explicitly identifies bundled fallback',async()=>{
  const old=await currentLayouts(assetUrl,github({version:'1.10'}).fetcher);
  const next=await currentLayouts(assetUrl,github({version:'1.11'}).fetcher);
  assert(old.live && next.live);
  assert(old.entries.every(e=>e.version==='1.10'));
  assert(next.entries.every(e=>e.version==='1.11'));
  const fallback=await currentLayouts(assetUrl,github({offline:true}).fetcher);
  assert.equal(fallback.live,false); assert.deepEqual(fallback.entries,[entry]);
});
test('release metadata cannot redirect downloads or claim another file',async()=>{
  const [released]=await latestPublishedLayouts(github().fetcher);
  for(const change of [{release:'../../main'},{version:'1.11'},{filename:'unrelated.vdf'},{git_sha1:'bad'}])
    assert.throws(()=>validateCatalog({layouts:[{...released,...change}]}));
});
