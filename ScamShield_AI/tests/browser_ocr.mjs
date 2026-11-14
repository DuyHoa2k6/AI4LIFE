import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),ORIGIN='http://127.0.0.1:18766';
const profile=path.join(ROOT,'.browser-profile-ocr-'+Date.now()),report={scope:'real Chrome web and unpacked extension, real local OCR, mock analysis; isolated copy grants all_urls for screenshot fixture only, not production toolbar activeTab grant verification',checks:[]};
fs.mkdirSync(profile);const output=path.join(ROOT,'reports/ocr/browser');fs.mkdirSync(output,{recursive:true});
const extension=path.join(profile,'extension');fs.cpSync(path.join(ROOT,'extension'),extension,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(extension,'manifest.json'),'utf8'));manifest.host_permissions.push('<all_urls>');fs.writeFileSync(path.join(extension,'manifest.json'),JSON.stringify(manifest));
const workerFile=path.join(extension,'worker.js');fs.writeFileSync(workerFile,fs.readFileSync(workerFile,'utf8').replace('http://127.0.0.1:8000',ORIGIN));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function check(name,value){report.checks.push({name,passed:!!value});if(!value)throw Error(name);}
async function wait(fn){const end=Date.now()+20000;while(Date.now()<end){const r=await fn();if(r)return r;await sleep(100);}throw Error('Wait timed out');}
class CDP{
 constructor(ws){this.ws=ws;this.seq=0;this.pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data),p=this.pending.get(m.id);if(p){this.pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}};}
 call(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++this.seq;this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params,sessionId}));});}
 async eval(sessionId,expression){const r=await this.call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true},sessionId);if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;}
}
const server=spawn('python',['-m','uvicorn','backend.main:app','--app-dir',ROOT,'--host','127.0.0.1','--port','18766','--no-access-log'],{cwd:ROOT,env:{...process.env,SCAMSHIELD_MODE:'mock'},windowsHide:true,stdio:'ignore'});
let chrome,cdp;
try{
 await wait(async()=>{try{return(await fetch(ORIGIN+'/health')).ok;}catch{return false;}});
 const port=21000+Math.floor(Math.random()*1000);
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--enable-unsafe-extension-debugging','--remote-debugging-port='+port,'--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
 const version=await wait(async()=>{try{return await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();}catch{return false;}});report.browser=version.Browser;
 const ws=new WebSocket(version.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});cdp=new CDP(ws);
 const {targetId}=await cdp.call('Target.createTarget',{url:ORIGIN});const {sessionId:page}=await cdp.call('Target.attachToTarget',{targetId,flatten:true});
 await wait(()=>cdp.eval(page,'!!document.querySelector("#ocr-file")&&!document.querySelector("#send").disabled'));
 await cdp.eval(page,`globalThis.counts={ocr:0,analyze:0};globalThis.saved=fetch;globalThis.fetch=(url,opts)=>{if(String(url).endsWith('/api/ocr'))counts.ocr++;if(String(url).endsWith('/api/analyze'))counts.analyze++;return saved(url,opts);};document.querySelector('#ocr-file').closest('details').open=true;`);
 async function select(cid){const {root}=await cdp.call('DOM.getDocument',{},page);const {nodeId}=await cdp.call('DOM.querySelector',{nodeId:root.nodeId,selector:'#ocr-file'},page);await cdp.call('DOM.setFileInputFiles',{nodeId,files:[path.join(ROOT,'fixtures/ocr_checks',cid+'.png')]},page);}
 await select('O1');check('selecting image sends zero requests',await cdp.eval(page,'counts.ocr===0&&counts.analyze===0'));
 await cdp.eval(page,`document.querySelector('#ocr-read').click()`);await wait(()=>cdp.eval(page,'document.querySelector("#ocr-text").textContent.includes("500")'));
 check('real Vietnamese OCR displayed, analysis not sent',await cdp.eval(page,'counts.ocr===1&&counts.analyze===0'));
 await cdp.eval(page,`document.querySelector('#preview').click()`);
 check('preview includes OCR source and unchanged OCR message',await cdp.eval(page,`(()=>{const p=JSON.parse(document.querySelector('#payload').value);return p.ocr_sources.length===1&&p.messages[0].text===document.querySelector('#ocr-text').textContent&&counts.analyze===0;})()`));
 await cdp.eval(page,`document.querySelector('#send').click()`);await wait(()=>cdp.eval(page,'document.querySelector("#status").textContent.includes("Đã phân tích")'));
 check('OCR provenance and warning rendered after API',await cdp.eval(page,'document.querySelector("#result").textContent.includes("\u0111\u1ecdc t\u1eeb \u1ea3nh")&&counts.analyze===1'));
 await select('O4');await cdp.eval(page,`document.querySelector('#ocr-read').click()`);await wait(()=>cdp.eval(page,'document.querySelector("#ocr-status").textContent.includes("Chưa đọc được chữ")'));
 check('blank image does not analyze or claim safe',await cdp.eval(page,'counts.analyze===1&&document.querySelector("#review").hidden'));
 await cdp.call('Page.captureScreenshot',{format:'png'},page).then(r=>fs.writeFileSync(path.join(output,'web.png'),Buffer.from(r.data,'base64')));
 const loaded=await cdp.call('Extensions.loadUnpacked',{path:extension});
 const popup=await cdp.call('Target.createTarget',{url:`chrome-extension://${loaded.id}/popup.html`});
 const {sessionId:popupSession}=await cdp.call('Target.attachToTarget',{targetId:popup.targetId,flatten:true});
 await sleep(400);await cdp.eval(popupSession,`chrome.runtime.sendMessage({type:'SS_WAKE'}).catch(()=>null)`);
 const workerTarget=await wait(async()=>(await cdp.call('Target.getTargets')).targetInfos.find(t=>t.type==='service_worker'&&t.url.startsWith('chrome-extension://'+loaded.id+'/')));
 const {sessionId:worker}=await cdp.call('Target.attachToTarget',{targetId:workerTarget.targetId,flatten:true});
 await cdp.call('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false},page);
 const image='data:image/png;base64,'+fs.readFileSync(path.join(ROOT,'fixtures/ocr_checks/O1.png')).toString('base64');
 await cdp.eval(page,`document.body.innerHTML='<article id="ocr-region" style="position:absolute;left:20px;top:20px;width:950px;height:330px;background:white;padding:20px;box-sizing:border-box"><p>Ảnh tin nhắn cần kiểm tra</p><img id="fixture-image" style="width:840px;height:auto"><input style="font-size:30px" value="OCR_INPUT_SECRET"></article><p style="position:absolute;top:430px">OUTSIDE_PRIVATE_WORD</p>';document.querySelector('#fixture-image').src=${JSON.stringify(image)};`);
 await wait(()=>cdp.eval(page,'document.querySelector("#fixture-image").naturalWidth>0'));
 report.tabs=await cdp.eval(worker,'chrome.tabs.query({}).then(t=>t.map(x=>({id:x.id,url:x.url})))');
 const tab=await cdp.eval(worker,`(async()=>{for(const t of await chrome.tabs.query({})){try{const r=await chrome.scripting.executeScript({target:{tabId:t.id},func:()=>location.origin});if(r[0]?.result===${JSON.stringify(ORIGIN)})return t.id;}catch{}}throw Error('Fixture tab not accessible');})()`);
 await cdp.eval(worker,`chrome.tabs.update(${tab},{active:true})`);
 await cdp.eval(worker,`(async()=>{globalThis.ocrUploads=0;globalThis.analyzes=0;globalThis.ocrResults=[];globalThis.analysisPayloads=[];globalThis.realFetch=fetch;globalThis.fetch=async(url,opts)=>{if(String(url).endsWith('/api/ocr'))ocrUploads++;if(String(url).endsWith('/api/analyze')){analyzes++;analysisPayloads.push(JSON.parse(opts.body));}const r=await realFetch(url,opts);if(String(url).endsWith('/api/ocr')&&r.ok)ocrResults.push(await r.clone().json());return r;};await chrome.scripting.executeScript({target:{tabId:${tab}},files:['shared.js','result_view.js','panel_view.js','content.js']});await chrome.tabs.sendMessage(${tab},{type:'SS_CHOOSE'});})()`);
 await sleep(300);
 for(const type of ['mouseMoved','mousePressed','mouseReleased'])await cdp.call('Input.dispatchMouseEvent',{type,x:25,y:25,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})},page);
 async function shadowButton(text){const doc=await cdp.call('DOM.getDocument',{depth:-1,pierce:true},page);let found;function walk(n){if(n.nodeName==='BUTTON'&&n.children?.some(c=>c.nodeValue===text))found=n.nodeId;for(const child of [...(n.children||[]),...(n.shadowRoots||[])])walk(child);}walk(doc.root);if(!found)throw Error('Missing button '+text);const {object}=await cdp.call('DOM.resolveNode',{nodeId:found},page);await cdp.call('Runtime.callFunctionOn',{objectId:object.objectId,functionDeclaration:'function(){if(this.hidden)throw Error("Button hidden");this.click();}',userGesture:true},page);}
 await shadowButton('Bật quét vùng này');
 await wait(()=>cdp.eval(worker,'analyzes===1'));
 await wait(()=>cdp.eval(page,'document.querySelector("[data-ss-owned=badge]")?.textContent.includes("Mức cảnh báo")||!!document.querySelector("[data-ss-owned=badge] .ss-result")'));
 await sleep(650);
 check('automatic region scan never uploads or analyzes image content',await cdp.eval(worker,'ocrUploads===0&&analyzes===1&&analysisPayloads.every(p=>!p.ocr_sources&&!JSON.stringify(p).includes("500"))'));
 await shadowButton('Tạm dừng');await sleep(150);
 await cdp.eval(worker,'analyzes=0;analysisPayloads=[]');
 await shadowButton('Ảnh trong vùng · xem trước');await sleep(500);
 check('extension capture preview sends zero OCR/analyze requests',await cdp.eval(worker,'ocrUploads===0&&analyzes===0'));
 await shadowButton('Đọc chữ trong ảnh này');await wait(()=>cdp.eval(worker,'ocrResults.length===1'));
 check('extension cropped screenshot OCR is real',await cdp.eval(worker,'ocrResults[0].status==="ready"&&ocrResults[0].text.includes("500")'));
 check('outside text and input value absent from screenshot OCR',await cdp.eval(worker,'!ocrResults[0].text.includes("OUTSIDE_PRIVATE_WORD")&&!ocrResults[0].text.includes("OCR_INPUT_SECRET")'));
 check('extension OCR alone does not analyze',await cdp.eval(worker,'ocrUploads===1&&analyzes===0'));
 await sleep(100);await shadowButton('Phân tích bài và chữ trong ảnh');await wait(()=>cdp.eval(worker,'analyzes===1'));
 check('extension sends DOM and OCR provenance only after confirmation',await cdp.eval(worker,'analysisPayloads[0].ocr_sources.length===1&&analysisPayloads[0].messages.length===2&&!JSON.stringify(analysisPayloads[0]).includes("OCR_INPUT_SECRET")&&!JSON.stringify(analysisPayloads[0]).includes("OUTSIDE_PRIVATE_WORD")'));
 await sleep(300);await cdp.call('Page.captureScreenshot',{format:'png'},page).then(r=>fs.writeFileSync(path.join(output,'extension.png'),Buffer.from(r.data,'base64')));
}catch(e){report.error=e.stack;process.exitCode=1;}
finally{fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(cdp){await cdp.call('Browser.close').catch(()=>{});cdp.ws.close();}chrome?.kill();server.kill();report.profile=profile;console.log('Test profile: '+profile);}
