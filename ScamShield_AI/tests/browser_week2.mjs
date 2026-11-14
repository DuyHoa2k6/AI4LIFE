// Native Chrome DevTools Protocol test: Node 24 + installed Chrome, no npm packages.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const REPORT_DIR=process.env.SCAMSHIELD_REPORT_DIR?path.resolve(process.env.SCAMSHIELD_REPORT_DIR):path.join(ROOT,'reports/week2');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
if(process.env.SCAMSHIELD_BROWSER_HYBRID==='1'||process.env.SCAMSHIELD_BROWSER_TWO_PASS==='1')throw Error('External model test modes have been removed; use browser_local_provider.mjs for BE tests.');
const report={date:'2026-11-10',mode:'mock',browser:'installed Chrome headless',checks:[]};
fs.mkdirSync(REPORT_DIR,{recursive:true});
function check(id,condition,detail=''){report.checks.push({id,passed:!!condition,detail});if(!condition)throw Error(id+': '+detail);}
class CDP{
  constructor(ws){this.ws=ws;this.seq=0;this.pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=this.pending.get(m.id);if(p){this.pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}}});}
  call(method,params={},sessionId){const id=++this.seq;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending.delete(id);reject(Error('CDP timeout '+method));},15000);this.pending.set(id,{resolve:r=>{clearTimeout(timer);resolve(r);},reject:e=>{clearTimeout(timer);reject(e);}});this.ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));});}
  async eval(session,expression){const r=await this.call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true},session);if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;}
}
async function waitFor(fn,description,timeout=10000){const until=Date.now()+timeout;while(Date.now()<until){const result=await fn();if(result)return result;await sleep(100);}throw Error('Wait failed: '+description);}
const chromePath=process.env.SCAMSHIELD_CHROME||'C:/Program Files/Google/Chrome/Application/chrome.exe';
const profile=path.join(ROOT,'.browser-profile-'+Date.now());fs.mkdirSync(profile);
const debugPort=19300+Math.floor(Math.random()*1000);
const testExtension=path.join(profile,'extension');fs.cpSync(path.join(ROOT,'extension'),testExtension,{recursive:true});
const workerPath=path.join(testExtension,'worker.js');fs.writeFileSync(workerPath,fs.readFileSync(workerPath,'utf8').replace('http://127.0.0.1:8000','http://127.0.0.1:18762'));
report.test_origin='127.0.0.1:18762; worker copy changes API port only to avoid existing user server';
const testEnv={...process.env,PYTHONPATH:ROOT,SCAMSHIELD_MODE:'mock'};
const server=spawn(process.env.SCAMSHIELD_PYTHON||'python',['-m','uvicorn','backend.main:app','--app-dir',ROOT,'--host','127.0.0.1','--port','18762','--no-access-log'],{cwd:ROOT,env:testEnv,windowsHide:true,stdio:'ignore'});
let chrome,cdp;
try{
  await waitFor(async()=>{try{return (await fetch('http://127.0.0.1:18762/health')).ok;}catch{return false;}},'API readiness');
  chrome=spawn(chromePath,['--headless=new','--no-first-run','--no-default-browser-check','--remote-debugging-port='+debugPort,'--enable-unsafe-extension-debugging','--user-data-dir='+path.join(profile,'chrome'),'about:blank'],{windowsHide:true,stdio:'ignore'});
  const version=await waitFor(async()=>{try{return await(await fetch('http://127.0.0.1:'+debugPort+'/json/version')).json();}catch{return false;}},'Chrome CDP');
  report.browser_version=version.Browser;
  const ws=new WebSocket(version.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});cdp=new CDP(ws);
  const target=await cdp.call('Target.createTarget',{url:'http://127.0.0.1:18762/'});
  const {sessionId:page}=await cdp.call('Target.attachToTarget',{targetId:target.targetId,flatten:true});
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#preview")'),'web ready');
  await cdp.call('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false},page);
  // Observe browser network without storing payload outside synthetic test report.
  await cdp.call('Network.enable',{},page);
  await cdp.eval(page,`globalThis.__requests=[];globalThis.__originalFetch=fetch;globalThis.fetch=async function(url,options){if(String(url).includes('/api/analyze'))__requests.push(JSON.parse(options.body));return __originalFetch(url,options);}`);
  await cdp.eval(page,`document.querySelector('[data-example="risk"]').click();document.querySelector('#preview').click();`);
  check('WEB-01 preview does not send',await cdp.eval(page,'__requests.length===0&&!document.querySelector("#review").hidden'));
  await waitFor(()=>cdp.eval(page,'!document.querySelector("#send").disabled'),'config loaded');
  await cdp.eval(page,'document.querySelector("#send").click()');
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#result [data-risk=high]")'),'web high');
  check('WEB-01 real API rendering',await cdp.eval(page,'__requests.length===1&&!!document.querySelector("#result .ss-summary")&&!document.querySelector("#result details h4")'));
  await cdp.eval(page,`document.querySelector('#content').value='😀 Gửi OTP cho tôi.';document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#result blockquote")'),'Unicode mark');
  check('WEB Unicode codepoint highlight',await cdp.eval(page,`document.querySelector('#result blockquote').textContent==='😀 Gửi OTP cho tôi.'`));
  // Masked snapshot round trip.
  await cdp.eval(page,`document.querySelector('#content').value='Gửi OTP SECRET123 để nhận quà.';document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();const t=document.querySelector('#payload'),start=t.value.indexOf('SECRET123');t.setSelectionRange(start,start+9);document.querySelector('#mask').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'document.querySelector("#status").textContent.includes("Đã phân tích")'),'masked response');
  check('WEB masked payload only',await cdp.eval(page,'!JSON.stringify(__requests.at(-1)).includes("SECRET123")&&JSON.stringify(__requests.at(-1)).includes("[ĐÃ CHE]")'));
  // Simulated slow response races, real render code; old response deliberately ignores abort.
  await cdp.eval(page,`globalThis.__savedFetch=fetch;globalThis.__calls=0;globalThis.__staleRelease=null;globalThis.__staleCompleted=false;globalThis.fetch=async (url,opts)=>{if(!String(url).includes('/api/analyze'))return __savedFetch(url,opts);const ordinal=++__calls;const r=await __originalFetch(url,{...opts,signal:undefined});const data=await r.json();if(ordinal===1){await new Promise(resolve=>globalThis.__staleRelease=resolve);globalThis.__staleCompleted=true;}return new Response(JSON.stringify(data),{status:200});};document.querySelector('[data-example="risk"]').click();document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'typeof __staleRelease==="function"'),'old response held');
  await cdp.eval(page,`document.querySelector('[data-example="warning"]').click();document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#result [data-risk=clear]")'),'new response renders first');
  await cdp.eval(page,'__staleRelease()');
  await waitFor(()=>cdp.eval(page,'__staleCompleted'),'old response released');await sleep(100);
  check('WEB stale response ignored',await cdp.eval(page,'!!document.querySelector("#result [data-risk=clear]")'));
  await cdp.eval(page,'globalThis.fetch=__savedFetch');
  await cdp.eval(page,`document.querySelector('[data-example="context"]').click();document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#result [data-action=supplement]")'),'follow up question');
  await cdp.eval(page,`document.querySelector('#result [data-action=supplement]').click();document.querySelector('#result textarea').value='Additional context';document.querySelector('#result form').dispatchEvent(new Event('submit',{cancelable:true}));`);
  check('WEB-01 supplemental context retained',await cdp.eval(page,`JSON.parse(document.querySelector('#payload').value).text==='Lệnh rút bị treo.'&&JSON.parse(document.querySelector('#payload').value).context.includes('Additional context')`));
  await cdp.eval(page,`document.querySelector('#format').value='messages';document.querySelector('#content').value=JSON.stringify([{id:'a',speaker:'sender',text:'Ứng tiền để nhận hoa hồng.'},{id:'b',speaker:'recipient',text:'Tôi cần xác minh trước.'}]);document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#result .ss-evidence-meta")'),'ordered conversation');
  check('WEB ordered input and verified speaker',await cdp.eval(page,`__requests.at(-1).messages[0].id==='a'&&__requests.at(-1).messages[1].id==='b'&&document.querySelector('#result .ss-evidence-meta').textContent.includes('sender')`));
  await cdp.call('Page.captureScreenshot',{format:'png'},page).then(r=>fs.writeFileSync(path.join(REPORT_DIR,'web.png'),Buffer.from(r.data,'base64')));
  // Client-side validation and network-error UI are deterministic fault injections.
  const priorCount=await cdp.eval(page,'__requests.length');
  await cdp.eval(page,`document.querySelector('#format').value='text';document.querySelector('#content').value=' ';document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();`);
  check('WEB blank input rejected',await cdp.eval(page,'document.querySelector("#review").hidden&&__requests.length==='+priorCount));
  await cdp.eval(page,`document.querySelector('#content').value='x'.repeat(10001);document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();`);
  check('WEB oversized input rejected',await cdp.eval(page,'document.querySelector("#status").textContent.includes("10.000")'));
  await cdp.eval(page,`globalThis.fetch=async()=>{throw new TypeError('Failed to fetch');};document.querySelector('[data-example="risk"]').click();document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await waitFor(()=>cdp.eval(page,'document.querySelector("#result").textContent.includes("Chưa kiểm tra được")'),'web offline error');
  check('WEB offline error retry available',await cdp.eval(page,'!document.querySelector("#send").disabled'));
  await cdp.eval(page,'globalThis.fetch=__savedFetch');
  // Locate the real unpacked extension worker. No runtime shim is used.
  let workers=(await cdp.call('Target.getTargets')).targetInfos.filter(t=>t.type==='service_worker'&&t.url.startsWith('chrome-extension://')&&t.url.endsWith('/worker.js'));
  if(!workers.length){
    try{report.extension_load=await cdp.call('Extensions.loadUnpacked',{path:testExtension});}catch(e){report.extension_load_error=e.message;}
    if(report.extension_load?.id){
      const popup=await cdp.call('Target.createTarget',{url:`chrome-extension://${report.extension_load.id}/popup.html`});
      const {sessionId:popupSession}=await cdp.call('Target.attachToTarget',{targetId:popup.targetId,flatten:true});
      await sleep(400);report.popup_debug=await cdp.eval(popupSession,`({url:location.href,body:document.body?.innerText,runtime:!!chrome.runtime})`);await cdp.eval(popupSession,`chrome.runtime.sendMessage({type:'SS_WAKE'}).catch(()=>null)`);
    }
    await sleep(2500);report.targets=(await cdp.call('Target.getTargets')).targetInfos;workers=report.targets.filter(t=>t.type==='service_worker'&&t.url.startsWith('chrome-extension://')&&t.url.endsWith('/worker.js'));
  }
  check('EXT real unpacked worker loaded',workers.length>0,'Installed Chrome must support unpacked extension loading in test mode');
  const {sessionId:worker}=await cdp.call('Target.attachToTarget',{targetId:workers[0].targetId,flatten:true});
  await cdp.call('Page.navigate',{url:'http://127.0.0.1:18762/fixture'},page);
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#comments")'),'fixture');
  await cdp.eval(worker,`globalThis.__apiRequests=[];globalThis.__apiResults=[];globalThis.__workerFetch=fetch;globalThis.fetch=async function(url,opts){if(String(url).endsWith('/api/analyze'))__apiRequests.push(JSON.parse(opts.body));const r=await __workerFetch(url,opts);if(String(url).endsWith('/api/analyze')&&r.ok)__apiResults.push({input:JSON.parse(opts.body),result:await r.clone().json()});return r;};`);
  report.tabs=await cdp.eval(worker,`chrome.tabs.query({}).then(tabs=>tabs.map(t=>({id:t.id,url:t.url,pendingUrl:t.pendingUrl})))`);
  const tabId=await cdp.eval(worker,`(async()=>{const tabs=await chrome.tabs.query({});return (tabs.find(t=>t.url?.includes('/fixture'))||tabs.at(-1)).id;})()`);
  async function choose(){await cdp.eval(worker,`(async()=>{await chrome.scripting.executeScript({target:{tabId:${tabId},frameIds:[0]},files:['shared.js','result_view.js','panel_view.js','content.js']});await chrome.tabs.sendMessage(${tabId},{type:'SS_CHOOSE'},{frameId:0});})()`);await sleep(250);const r=await cdp.eval(page,`(()=>{document.querySelector('#comments').scrollIntoView({block:'start'});const r=document.querySelector('#comments').getBoundingClientRect();return{x:r.x+8,y:r.y+12};})()`);await cdp.call('Input.dispatchMouseEvent',{type:'mouseMoved',x:r.x,y:r.y},page);await cdp.call('Input.dispatchMouseEvent',{type:'mousePressed',x:r.x,y:r.y,button:'left',clickCount:1},page);await cdp.call('Input.dispatchMouseEvent',{type:'mouseReleased',x:r.x,y:r.y,button:'left',clickCount:1},page);await sleep(200);}
  async function shadowButton(text){
    const doc=await cdp.call('DOM.getDocument',{depth:-1,pierce:true},page);let found;
    function walk(n){if(n.nodeName==='BUTTON'&&n.children?.some(c=>c.nodeValue===text))found=n.nodeId;for(const x of [...(n.children||[]),...(n.shadowRoots||[])])walk(x);}
    walk(doc.root);if(!found)throw Error('No shadow button '+text);
    const {object}=await cdp.call('DOM.resolveNode',{nodeId:found},page);await cdp.call('Runtime.callFunctionOn',{objectId:object.objectId,functionDeclaration:'function(){this.click();}',userGesture:true},page);
  }
  await choose();check('EXT-01 selection sends zero requests',await cdp.eval(worker,'__apiRequests.length===0'));
  await shadowButton('Bật quét vùng này');
  await waitFor(()=>cdp.eval(worker,'__apiRequests.length>=1'),'extension sends visible units');
  await waitFor(()=>cdp.eval(page,'!!document.querySelector("#comment-risk [data-ss-owned=badge]")?.textContent.includes("Rủi ro cao")'),'extension high');
  check('EXT-02 correct item and separate result',await cdp.eval(page,'!document.querySelector("#post [data-ss-owned=badge]")&&!!document.querySelector("#comment-risk [data-ss-owned=badge]")'));
  check('PRIV-01 restricted request bodies',await cdp.eval(worker,'!JSON.stringify(__apiRequests).includes("SECRET_DO_NOT_SEND")'));
  const beforeRequests=await cdp.eval(worker,'__apiRequests.map(p=>p.text)');await cdp.eval(page,'document.querySelector("#comments").scrollTop=0');await sleep(1200);
  const newlySubmitted=await cdp.eval(worker,`__apiRequests.slice(${beforeRequests.length}).map(p=>p.text)`);
  check('EXT-03 no unchanged duplicates',newlySubmitted.every(text=>!beforeRequests.includes(text))&&new Set(newlySubmitted).size===newlySubmitted.length,'Any newly visible items may finish their first request; previously submitted text must not repeat.');
  const webPrediction=await fetch('http://127.0.0.1:18762/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:'Ứng tiền để nhận hoa hồng.'})}).then(r=>r.json());
  const extensionPrediction=await cdp.eval(worker,`__apiResults.find(x=>x.input.text==='Ứng tiền để nhận hoa hồng.').result`);
  const businessResult=value=>{const copy=structuredClone(value);if(copy.analysis)delete copy.analysis.stage_timings_ms;for(const branch of Object.values(copy.retrieval||{}))delete branch.elapsed_ms;return copy;};
  check('E2E-01 shared API behavior evidence and decision',JSON.stringify(businessResult(webPrediction))===JSON.stringify(businessResult(extensionPrediction))&&await cdp.eval(page,'document.querySelector("#comment-risk [data-ss-owned=badge]").textContent.includes("Rủi ro cao")'),'Compare all result fields except measured durations, which differ per request.');
  // Delay only one actual API response; mutate the same node while it is in flight.
  await cdp.eval(worker,`globalThis.__normalFetch=fetch;globalThis.__delayOnce=true;globalThis.fetch=async(url,opts)=>{const r=await __normalFetch(url,opts);if(String(url).endsWith('/api/analyze')&&__delayOnce){__delayOnce=false;await new Promise(r=>setTimeout(r,900));}return r;};`);
  const preEdit=await cdp.eval(worker,'__apiRequests.length');
  await cdp.eval(page,`document.querySelector('#comment-risk p').textContent='Chuyển thêm tiền để mở khóa.';`);
  await waitFor(()=>cdp.eval(worker,'__apiRequests.length>'+preEdit),'in flight edit');
  await cdp.eval(page,`document.querySelector('#comment-risk p').textContent='Cảnh giác: đừng ứng tiền để nhận hoa hồng.';`);
  await waitFor(()=>cdp.eval(page,'document.querySelector("#comment-risk [data-ss-owned=badge]")?.textContent.includes("Chưa ghi nhận")'),'latest content clear');
  check('EXT-04 old item response ignored',await cdp.eval(page,'!document.querySelector("#comment-risk [data-ss-owned=badge]").textContent.includes("Rủi ro cao")'));
  await cdp.eval(worker,'globalThis.fetch=__normalFetch');
  await cdp.eval(page,'document.querySelector("#load").click()');
  await waitFor(()=>cdp.eval(page,'document.querySelector("#added-1 [data-ss-owned=badge]")?.textContent.includes("Rủi ro cao")'),'new visible item');
  check('EXT-03 newly loaded visible item scanned',true);
  check('PRIV-01 after scroll still restricted',await cdp.eval(worker,'!JSON.stringify(__apiRequests).includes("SECRET_DO_NOT_SEND")'));
  await cdp.eval(page,'document.querySelector("#comments").scrollTop=0');await sleep(600);
  await shadowButton('Tạm dừng');const paused=await cdp.eval(worker,'__apiRequests.length');await cdp.eval(page,'document.querySelector("#comment-risk p").textContent="Gửi OTP để nhận quà."');await sleep(1000);
  check('EXT-05 pause stops requests',await cdp.eval(worker,'__apiRequests.length')===paused);
  await shadowButton('Tiếp tục');await waitFor(()=>cdp.eval(worker,'__apiRequests.length>'+paused),'resume');
  await shadowButton('Dừng quét');const stopped=await cdp.eval(worker,'__apiRequests.length');await cdp.eval(page,'document.querySelector("#comment-risk p").textContent="Chuyển thêm tiền để mở khóa."');await sleep(1000);
  check('EXT-05 stop clears session',await cdp.eval(worker,'__apiRequests.length')===stopped);
  // Fresh selection after route change must require an explicit new enable.
  await cdp.eval(page,'document.querySelector("#comments").scrollTop=0');await choose();await shadowButton('Bật quét vùng này');
  await waitFor(()=>cdp.eval(worker,'__apiRequests.length>'+stopped),'new region session');
  await cdp.eval(page,'history.pushState({},"","/fixture?changed=1")');await sleep(900);
  const afterRoute=await cdp.eval(worker,'__apiRequests.length');await cdp.eval(page,'document.querySelector("#comment-risk p").textContent="Gửi OTP để nhận quà. Changed route"');await sleep(900);
  check('EXT-06 SPA navigation stops scanning',await cdp.eval(worker,'__apiRequests.length')===afterRoute);
  await choose();await shadowButton('Bật quét vùng này');await sleep(700);await cdp.eval(page,'document.querySelector("#comments").remove()');await sleep(700);
  const afterRemove=await cdp.eval(worker,'__apiRequests.length');await sleep(700);
  check('EXT-06 removed region stops scanning',await cdp.eval(worker,'__apiRequests.length')===afterRemove);
  // Reopen fixture for no-network, 429 and timeout scenarios.
  async function reloadFixture(){await cdp.call('Page.navigate',{url:'http://127.0.0.1:18762/fixture'},page);await waitFor(()=>cdp.eval(page,'!!document.querySelector("#comments")'),'new fixture');await choose();}
  await reloadFixture();
  await cdp.eval(worker,`globalThis.__beforeErrorFetch=fetch;globalThis.fetch=async(url,opts)=>{if(String(url).endsWith('/api/analyze')){__apiRequests.push(JSON.parse(opts.body));return new Response('{}',{status:429});}return __beforeErrorFetch(url,opts);};`);
  await shadowButton('Bật quét vùng này');
  await waitFor(()=>cdp.eval(page,'document.querySelector("#comment-risk [data-ss-owned=badge]")?.textContent.includes("HTTP_429")'),'429 label');
  const count429=await cdp.eval(worker,'__apiRequests.length');await sleep(1200);
  check('EXT-07 429 no infinite retries',await cdp.eval(worker,'__apiRequests.length')===count429);
  await shadowButton('Dừng quét');await cdp.eval(worker,'globalThis.fetch=__beforeErrorFetch');
  await reloadFixture();
  await cdp.eval(worker,`globalThis.__beforeOffline=fetch;globalThis.fetch=async(url,opts)=>{if(String(url).endsWith('/api/analyze')){__apiRequests.push(JSON.parse(opts.body));throw new TypeError('Network offline');}return __beforeOffline(url,opts);};`);
  await shadowButton('Bật quét vùng này');await waitFor(()=>cdp.eval(page,'document.querySelector("#comment-risk [data-ss-owned=badge]")?.textContent.includes("Chưa kiểm tra được")'),'offline label');
  const offlineCount=await cdp.eval(worker,'__apiRequests.length');await sleep(900);
  check('EXT-07 offline no repeated request storm',await cdp.eval(worker,'__apiRequests.length')===offlineCount);
  await shadowButton('Dừng quét');await cdp.eval(worker,'globalThis.fetch=__beforeOffline');
  await reloadFixture();
  await cdp.eval(worker,`globalThis.__beforeTimeout=fetch;globalThis.fetch=async(url,opts)=>{if(String(url).endsWith('/api/analyze')){__apiRequests.push(JSON.parse(opts.body));throw new DOMException('test timeout','AbortError');}return __beforeTimeout(url,opts);};`);
  await shadowButton('Bật quét vùng này');await waitFor(()=>cdp.eval(page,'document.querySelector("#comment-risk [data-ss-owned=badge]")?.textContent.includes("TIMEOUT")'),'timeout label');
  check('EXT-07 timeout label',true,'AbortError injected in real worker fetch; API timer independently tested in week1');
  await shadowButton('Dừng quét');await cdp.eval(worker,'globalThis.fetch=__beforeTimeout');
  // A deliberately delayed response from a stopped session must not reattach a badge.
  await reloadFixture();
  await cdp.eval(worker,`globalThis.__beforeStale=fetch;globalThis.fetch=async(url,opts)=>{const r=await __beforeStale(url,opts);if(String(url).endsWith('/api/analyze'))await new Promise(r=>setTimeout(r,900));return r;};`);
  const preStale=await cdp.eval(worker,'__apiRequests.length');await shadowButton('Bật quét vùng này');
  await waitFor(()=>cdp.eval(worker,'__apiRequests.length>'+preStale),'old session pending');
  await shadowButton('Dừng quét');await choose();await sleep(1200);
  check('EXT-05 old session response ignored after region change',await cdp.eval(page,'document.querySelectorAll("[data-ss-owned=badge]").length===0'));
  await cdp.eval(worker,'globalThis.fetch=__beforeStale');
  // A visible burst exceeds queue capacity. Expanded result cards push later items
  // below the viewport, so scroll to each unfinished item as a user would.
  await shadowButton('Dừng quét');await reloadFixture();
  await cdp.call('Emulation.setDeviceMetricsOverride',{width:1280,height:7000,deviceScaleFactor:1,mobile:false},page);
  await cdp.eval(page,`const region=document.querySelector('#comments');region.replaceChildren();region.style.maxHeight='none';for(let i=0;i<35;i++){const n=document.createElement('article');n.dataset.ssItem='';n.id='burst-'+i;n.style.cssText='font-size:10px;line-height:12px;margin:0;padding:0';n.textContent='Mục '+i+': Gửi OTP để nhận quà.';region.append(n);}region.scrollIntoView({block:'start'});`);
  await cdp.eval(worker,`globalThis.__beforeBurst=fetch;globalThis.__active=0;globalThis.__maxActive=0;globalThis.fetch=async(url,opts)=>{if(!String(url).endsWith('/api/analyze'))return __beforeBurst(url,opts);__active++;__maxActive=Math.max(__maxActive,__active);try{const r=await __beforeBurst(url,opts);await new Promise(r=>setTimeout(r,100));return r;}finally{__active--;}};`);
  const burstBefore=await cdp.eval(worker,'__apiRequests.length');await shadowButton('Bật quét vùng này');await sleep(300);
  const tree=await cdp.call('DOM.getDocument',{depth:-1,pierce:true},page);let statsText='';
  function findStats(n){if(n.nodeValue?.startsWith('Hàng chờ '))statsText=n.nodeValue;for(const c of [...(n.children||[]),...(n.shadowRoots||[])])findStats(c);}findStats(tree.root);
  const queue=statsText.match(/Hàng chờ (\d+)\/20 · Mục bị hoãn: (\d+)/);
  check('EXT-07 bounded queue and deferred items',queue&&Number(queue[1])<=20&&Number(queue[2])>0,statsText);
  const burstStarted=Date.now();
  await waitFor(async()=>{if(await cdp.eval(worker,'__apiRequests.length>='+String(burstBefore+35)))return true;await cdp.eval(page,`[...document.querySelectorAll('#comments article')].find(n=>!n.querySelector('.ss-result'))?.scrollIntoView({block:'center'});`);return false;},'burst drains with scrolling',60000);await sleep(700);
  const burstAfter=await cdp.eval(worker,'__apiRequests.length');
  check('EXT-07 burst no duplicate requests and concurrency one',burstAfter-burstBefore===35&&await cdp.eval(worker,'__maxActive===1'));
  report.burst={items:35,requests:burstAfter-burstBefore,queue_capacity:20,sampled_queue:Number(queue?.[1]),sampled_deferred:Number(queue?.[2]),max_concurrent:await cdp.eval(worker,'__maxActive'),drain_observed_ms:Date.now()-burstStarted};
  await shadowButton('Dừng quét');await cdp.eval(worker,'globalThis.fetch=__beforeBurst');
  report.request_count=await cdp.eval(worker,'__apiRequests.length');report.extension_runtime='real MV3 worker and isolated-world content script';
  // Screenshot of the website is captured earlier; final checks do not depend on screenshots.
}catch(e){report.error=e.stack;process.exitCode=1;}
finally{
  delete report.targets;delete report.tabs;delete report.popup_debug;
  fs.mkdirSync(REPORT_DIR,{recursive:true});fs.writeFileSync(path.join(REPORT_DIR,'browser.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(cdp){await cdp.call('Browser.close').catch(()=>{});cdp.ws.close();}chrome?.kill();server.kill();
}


