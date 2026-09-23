// Minimal DOM and API smoke check for automatic browser load/save logic.
// Run with: node tests/client_smoke.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, {
    id, dataset: {}, style: {}, value: '', innerHTML: '', textContent: '',
    className: '', classList: {add() {}, remove() {}}, addEventListener() {},
  });
  return elements.get(id);
};
let clickHandler;
let stored = structuredClone(JSON.parse(fs.readFileSync(path.join(root, 'initial_vault.json'))));
let rev = 'initial';
let posts = 0;
const local = new Map();
const fakeFetch = async (url, options = {}) => {
  if (url === '/api/config') return {ok: true, json: async () => ({vault_path:'/tmp/dashboard/vault.json', debounce_ms:100})};
  if (url === '/api/vault' && options.method === 'POST') {
    const payload = JSON.parse(options.body);
    if (payload.revision !== rev) return {ok:false,status:409,json:async () => ({error:'conflict'})};
    stored = structuredClone(payload.vault);
    rev = `rev-${++posts}`;
    return {ok:true,status:200,json:async () => ({revision:rev,saved:true})};
  }
  if (url === '/api/vault') return {ok:true,json:async () => ({vault:structuredClone(stored), revision:rev})};
  throw Error(`Unexpected request: ${url}`);
};
const context = {
  console, Date, Math, JSON, URL, setTimeout, clearTimeout,
  fetch:fakeFetch, navigator:{},
  localStorage:{getItem:key=>local.get(key)||null,setItem:(key,value)=>local.set(key,value)},
  document:{getElementById:element,body:{classList:{toggle() {}}},addEventListener:(name,handler)=>{if(name==='click') clickHandler=handler}},
  window:{addEventListener() {},open() {}},
};
vm.runInNewContext(script, context, {filename:'index.html'});

(async () => {
  await new Promise(resolve => setTimeout(resolve, 30));
  assert.match(element('statsChips').innerHTML, /3 links/);
  assert.match(element('dirtyPill').textContent, /Saved on disk/);
  const first = stored.links[0];
  const before = first.favorite;
  clickHandler({target:{dataset:{star:first.id}}});
  await new Promise(resolve => setTimeout(resolve, 250));
  assert.equal(posts, 1);
  assert.equal(stored.links[0].favorite, !before);
  assert.match(element('dirtyPill').textContent, /Saved on disk/);
  console.log('Browser logic smoke test passed: sample records loaded; star edit autosaved.');
  process.exit(0);
})().catch(error => { console.error(error); process.exit(1); });
