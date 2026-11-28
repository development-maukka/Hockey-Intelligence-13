const {test}=require('node:test');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
function launch(options={}){
 const dom=new JSDOM(fs.readFileSync(path.join(root,'site/index.html'),'utf8'),{url:'https://example.org/Hockey-Intelligence-13/',runScripts:'outside-only'}),w=dom.window;
 const local={...(options.local||{})},session={...(options.session||{})};
 for(const [property,store] of [['localStorage',local],['sessionStorage',session]])Object.defineProperty(w,property,{value:{getItem(k){if(options.blocked)throw Error('blocked');return store[k]??null},setItem(k,v){if(options.blocked)throw Error('blocked');store[k]=String(v)},removeItem(k){delete store[k]}}});
 Object.defineProperty(w.navigator,'language',{value:options.lang||'en'});Object.defineProperty(w.navigator,'userAgent',{value:options.ua||'Mozilla/5.0 Chrome/143 Safari/537.36'});Object.defineProperty(w.navigator,'standalone',{value:!!options.iosStandalone});
 const queries={};w.matchMedia=q=>queries[q]||=( {matches:!!options.standalone&&q.includes('standalone'),addEventListener(_,fn){this.change=fn}} );
 w.HTMLElement.prototype.scrollIntoView=()=>{};w.scrollTo=()=>{};w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};
 // Keep the unrelated dashboard network request pending during installation UI tests.
 w.fetch=options.resolveFetch?async()=>({ok:true,json:async()=>({updated:new Date().toISOString(),games:[],standings:[],brief:{}})}):()=>new Promise(()=>{});
 w.eval(fs.readFileSync(path.join(root,'site/install.js'),'utf8'));w.eval(fs.readFileSync(path.join(root,'site/app.js'),'utf8'));
 const settings=()=>{w.document.querySelector('#settings').click();return w.document.querySelector('[data-install-settings]')};
 const installEvent=(outcome='dismissed',fail=false)=>{let calls=0;const e=new w.Event('beforeinstallprompt',{cancelable:true});e.prompt=()=>{calls++;return fail?Promise.reject(Error('failed')):Promise.resolve()};e.userChoice=Promise.resolve({outcome});w.dispatchEvent(e);return {e,calls:()=>calls}};
 return {w,dom,local,session,queries,settings,installEvent,banner:()=>w.document.querySelector('#install-banner'),flush:()=>new Promise(r=>setImmediate(r))};
}
function second(o={}){return launch({...o,local:{'hockey-install-visits':'1',...(o.local||{})}})}
test('first visit: only settings; refresh stays first visit',()=>{
 let a=launch();assert(a.banner().hidden);assert(a.settings());let b=launch({local:a.local,session:a.session});assert(b.banner().hidden);assert.equal(b.local['hockey-install-visits'],'1');a.dom.window.close();b.dom.window.close();
});
test('second session shows suggestion and later visits keep it until dismissal',()=>{
 const a=second();assert(!a.banner().hidden);assert.equal(a.local['hockey-install-visits'],'2');const b=launch({local:a.local});assert(!b.banner().hidden);a.dom.window.close();b.dom.window.close();
});
test('closing suggestion persists while settings installation remains available',()=>{
 const a=second();a.banner().querySelector('button:last-child').click();assert(a.banner().hidden);const b=launch({local:a.local});assert(b.banner().hidden);assert(!b.settings().hidden);a.dom.window.close();b.dom.window.close();
});
test('native prompt waits for click and can only be used once',async()=>{
 const a=second(),p=a.installEvent();assert(p.e.defaultPrevented);assert.equal(p.calls(),0);a.banner().querySelector('[data-install-action]').click();await a.flush();assert.equal(p.calls(),1);assert(a.banner().hidden);assert.equal(a.local['hockey-install-dismissed'],'1');a.settings().querySelector('button').click();assert(a.w.document.querySelector('#install-dialog').open);assert.equal(p.calls(),1);a.dom.window.close();
});
test('accepted prompt hides both installation controls',async()=>{
 const a=second(),field=a.settings(),p=a.installEvent('accepted');field.querySelector('button').click();await a.flush();assert.equal(p.calls(),1);assert(field.hidden);assert(a.banner().hidden);a.dom.window.close();
});
test('appinstalled works without an in-page native prompt',()=>{
 const a=second(),field=a.settings();a.w.dispatchEvent(new a.w.Event('appinstalled'));assert(field.hidden);assert(a.banner().hidden);a.dom.window.close();
});
test('installed standalone launch and iOS standalone hide controls',()=>{
 for(const o of [{standalone:true},{iosStandalone:true}]){const a=second(o);assert(a.banner().hidden);assert(a.settings().hidden);a.dom.window.close()}
});
test('display-mode transition updates already open settings',()=>{
 const a=second(),f=a.settings(),q=a.queries['(display-mode: standalone)'];q.matches=true;q.change();assert(f.hidden);assert(a.banner().hidden);q.matches=false;q.change();assert(!f.hidden);a.dom.window.close();
});
test('Firefox Android has Firefox instructions',()=>{
 const a=second({ua:'Mozilla/5.0 (Android 16; Mobile; rv:145.0) Gecko/145.0 Firefox/145.0'});a.banner().querySelector('[data-install-action]').click();assert.match(a.w.document.querySelector('#install-dialog').textContent,/Firefox/);a.dom.window.close();
});
test('iOS, Safari Mac, Android and desktop have suitable instructions',()=>{
 for(const [ua,word] of [['iPhone Version/26 Safari','Add to Home Screen'],['Macintosh Version/26 Safari','Add to Dock'],['Android Chrome/143 Safari','⋮'],['Windows Chrome/143 Safari','address bar']]){const a=second({ua});a.settings().querySelector('button').click();assert.match(a.w.document.querySelector('#install-dialog').textContent,new RegExp(word));a.dom.window.close()}
});
test('FI DE EN, language override and other-language fallback',()=>{
 for(const [lang,pref,label] of [['fi',null,'Asenna sovellus'],['de',null,'App installieren'],['en',null,'Install app'],['fr',null,'Install app'],['en','fi','Asenna sovellus']]){const a=second({lang,local:pref?{'hockey-language':pref}:{}});assert.equal(a.settings().querySelector('button').textContent,label);a.dom.window.close()}
});
test('blocked storage: no repeated banner; manual settings and dashboard remain usable',()=>{
 const a=second({blocked:true});assert(a.banner().hidden);a.settings().querySelector('button').click();assert(a.w.document.querySelector('#install-dialog').open);assert(a.w.document.querySelector('#main'));a.dom.window.close();
});
test('failed native prompt offers instructions and clears busy state',async()=>{
 const a=second(),p=a.installEvent('dismissed',true);a.settings().querySelector('button').click();await a.flush();assert.equal(p.calls(),1);assert(a.w.document.querySelector('#install-dialog').open);assert(!a.w.document.querySelector('[data-install-settings] button').disabled);a.dom.window.close();
});
test('dismissal synchronizes with other tabs',()=>{
 const a=second();a.w.dispatchEvent(new a.w.StorageEvent('storage',{key:'hockey-install-dismissed',newValue:'1'}));assert(a.banner().hidden);assert(!a.settings().hidden);a.dom.window.close();
});

test('dashboard still loads data and opens settings with installation enabled',async()=>{
 const a=second({resolveFetch:true});await a.flush();a.w.go('games');assert.equal(a.w.document.querySelector('#main h2').textContent,'Games');assert(a.settings());assert(!a.banner().hidden);a.dom.window.close();
});

test('published HTML uses current version for both application scripts',()=>{
 const html=fs.readFileSync(path.join(root,'site/index.html'),'utf8');const version=html.match(/Development Maukka · v([0-9.]+)/)[1];assert(html.includes('app.js?v='+version+'"'));assert(html.includes('install.js?v='+version+'"'));
});
