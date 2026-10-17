// Only replace GitHub's network boundary; use the actual bundled VDF bytes.
(() => {
  const original = window.fetch.bind(window);
  const repository = 'abdimoussa98/universal-steam-input-layout';
  const api = `https://api.github.com/repos/${repository}`;
  const raw = `https://raw.githubusercontent.com/${repository}/`;
  const ids = {'Steam Controller 2':'ibex', 'Steam Deck':'neptune', 'DualSense Edge':'dse'};
  window.releaseFixture = {online:false, version:'99.2', requests:[]};
  let bundled;
  async function files() {
    if (!bundled) bundled = (async()=>{
      const catalog = await (await original(new URL('./layouts/index.json', location.href))).json();
      return Promise.all(catalog.layouts.map(async entry=>{
        const bytes = await (await original(new URL(`./layouts/${entry.filename}`, location.href))).arrayBuffer();
        const blob = await new Blob([`blob ${bytes.byteLength}\0`,bytes]).arrayBuffer();
        const sha = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-1',blob)),n=>n.toString(16).padStart(2,'0')).join('');
        return {...entry,id:ids[entry.controller],data:bytes,sha};
      }));
    })();
    return bundled;
  }
  window.fetch = async (url,options)=>{
    const path = String(url);
    if (!path.startsWith(api) && !path.startsWith(raw)) return original(url,options);
    releaseFixture.requests.push(path);
    if (!releaseFixture.online) return new Response('',{status:403});
    const version = releaseFixture.version;
    if(path.includes('/releases?')) return Response.json(Object.values(ids).map(id=>({tag_name:`${id}-v${version}`})));
    const entries = await files();
    if(path.includes('/contents/versions/')) {
      const id = path.match(/versions\/(\w+)\//)[1];
      return Response.json(entries.filter(e=>e.id===id).map(e=>({name:e.filename.replace(e.version,version),
        size:e.bytes,sha:e.sha,type:'file'})));
    }
    if(path.startsWith(raw)) {
      const name = path.split('/').pop();
      const entry = entries.find(e=>e.filename.replace(e.version,version)===name);
      return new Response(entry?.data || '',{status:entry?200:404});
    }
    throw new Error(`Unexpected release request: ${path}`);
  };
})();
