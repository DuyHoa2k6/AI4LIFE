import {spawn} from 'node:child_process';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),origin='http://127.0.0.1:18771',out=process.env.SCAMSHIELD_REPORT_DIR?path.resolve(process.env.SCAMSHIELD_REPORT_DIR):path.join(root,'reports/local_switch_20261112/browser');
const profile=path.join(root,'.browser-profile-local-switch-'+Date.now()),ext=path.join(profile,'extension');fs.mkdirSync(profile);fs.mkdirSync(out,{recursive:true});fs.cpSync(path.join(root,'extension'),ext,{recursive:true});
const workerFile=path.join(ext,'worker.js');fs.writeFileSync(workerFile,fs.readFileSync(workerFile,'utf8').replace('http://127.0.0.1:8000',origin));
const report={scope:'Actual local_rules through main website and real unpacked extension; model endpoint deliberately unusable, no synthetic model provider.',checks:[]};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));async function wait(fn){for(let i=0;i<300;i++){const value=await fn();if(value)return value;await sleep(100);}throw Error('Wait timed out');}
function check(name,value){report.checks.push({name,passed:!!value});if(!value)throw Error(name);}
class CDP{constructor(ws){this.ws=ws;this.seq=0;this.pending=new Map();ws.onmessage=e=>{const d=JSON.parse(e.data),p=this.pending.get(d.id);if(p){this.pending.delete(d.id);d.error?p.reject(Error(d.error.message)):p.resolve(d.result);}};}call(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++this.seq;this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params,sessionId}));});}async eval(page,expression){const r=await this.call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true},page);if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;}}
const server=spawn('python',['-m','uvicorn','backend.main:app','--app-dir',root,'--host','127.0.0.1','--port','18771','--no-access-log'],{cwd:root,env:{...process.env,SCAMSHIELD_MODE:'local_rules',SCAMSHIELD_URL_NETWORK_ENABLED:'0',SCAMSHIELD_PROVIDER_URL:'http://127.0.0.1:9/unusable-model',SCAMSHIELD_API_KEY:''},windowsHide:true,stdio:'ignore'});
let chrome,ws;
try{
 await wait(async()=>{try{return(await fetch(origin+'/health')).ok;}catch{return false;}});
 const port=25000+Math.floor(Math.random()*1000);chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-background-networking','--no-first-run','--no-default-browser-check','--enable-unsafe-extension-debugging','--remote-debugging-port='+port,'--user-data-dir='+path.join(profile,'chrome'),'about:blank'],{windowsHide:true,stdio:'ignore'});
 const version=await wait(async()=>{try{return await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();}catch{return false;}});report.browser=version.Browser;
 ws=new WebSocket(version.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});const cdp=new CDP(ws);
 const {targetId}=await cdp.call('Target.createTarget',{url:origin});const {sessionId:page}=await cdp.call('Target.attachToTarget',{targetId,flatten:true});
 await wait(()=>cdp.eval(page,'!!document.querySelector("#send")&&!document.querySelector("#send").disabled'));
 check('main website notice is local, no model',await cdp.eval(page,`document.querySelector('#processing').textContent.includes('không gửi tới Gemini')`));
 async function run(text,risk){await cdp.eval(page,`document.querySelector('#content').value=${JSON.stringify(text)};document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();document.querySelector('#send').click();`);await wait(()=>cdp.eval(page,`document.querySelector('#result .ss-result')?.dataset.risk===${JSON.stringify(risk)}`));}
 for(const [text,risk] of [['Gửi mã OTP cho tôi.','high'],['Cảnh báo: đừng gửi OTP.','clear'],['Đọc sáu số vừa hiện để nhận tiền.','need_context'],['Gửi ảnh CCCD qua chat.','suspicious']]){
  await run(text,risk);check('main website local '+risk,await cdp.eval(page,`!!document.querySelector('#result .ss-summary')`));
 }
 await run('Đăng nhập tại https://youtubee.com/','suspicious');
 check('main website displays grounded URL support',await cdp.eval(page,`document.querySelector('#result .ss-explanation').textContent.includes('tên miền cần xác minh')&&document.querySelector('#result .ss-summary').textContent.includes('liên kết')`));
 await cdp.eval(page,`globalThis.__webRequests=[];globalThis.__savedFetch=fetch;globalThis.fetch=(url,opts)=>{if(String(url).endsWith('/api/analyze'))__webRequests.push(JSON.parse(opts.body));return __savedFetch(url,opts);};`);
 await run('Chưa thấy tiền về, nhưng cứ giao máy trước.','suspicious');
 await cdp.eval(page,`document.querySelector('#result [data-action="supplement"]').click();document.querySelector('#result .ss-followup textarea').value='Tôi đã tự kiểm tra và nhận đủ tiền.';document.querySelector('#result .ss-followup form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));`);
 await wait(()=>cdp.eval(page,`JSON.parse(document.querySelector('#payload').value).clarification?.answer==='Tôi đã tự kiểm tra và nhận đủ tiền.'`));
 check('web review hides binding IDs and has one editable answer',await cdp.eval(page,`!document.querySelector('#payload').value.includes('case_id')&&!document.querySelector('#payload').value.includes('content_version')`));
 await cdp.eval(page,`document.querySelector('#send').click();`);
 await wait(()=>cdp.eval(page,`document.querySelector('#result .ss-result')?.dataset.risk==='clear'`));
 check('web clarification updates correct situation without model',await cdp.eval(page,`__webRequests.at(-1).clarification?.revision===1&&document.querySelector('#result .ss-summary').textContent.includes('thông tin bạn bổ sung')`));
 const danger='Hiện tại tôi bị giữ lại và không được rời đi.';await run(danger,'high');
 check('main website displays grounded urgency',await cdp.eval(page,`document.querySelector('#result .ss-urgent')?.textContent.includes('Ưu tiên an toàn')`));
 check('main website hides internal answers and rulebook',await cdp.eval(page,`!document.querySelector('#result').innerText.includes('answers_18')&&!document.querySelector('#result').innerText.includes('R-URGENT')`));
 await cdp.call('Page.captureScreenshot',{format:'png'},page).then(r=>fs.writeFileSync(path.join(out,'web.png'),Buffer.from(r.data,'base64')));
 const loaded=await cdp.call('Extensions.loadUnpacked',{path:ext});const popup=await cdp.call('Target.createTarget',{url:`chrome-extension://${loaded.id}/popup.html`});const {sessionId:ps}=await cdp.call('Target.attachToTarget',{targetId:popup.targetId,flatten:true});await sleep(200);await cdp.eval(ps,`chrome.runtime.sendMessage({type:'SS_WAKE'}).catch(()=>null)`);
 const target=await wait(async()=>(await cdp.call('Target.getTargets')).targetInfos.find(t=>t.type==='service_worker'&&t.url.startsWith('chrome-extension://'+loaded.id+'/')));const {sessionId:worker}=await cdp.call('Target.attachToTarget',{targetId:target.targetId,flatten:true});
 await cdp.call('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false},page);
 await cdp.eval(page,`document.body.innerHTML='<section id="region" style="position:absolute;left:20px;top:20px;width:720px;min-height:200px;padding:20px;background:white"><article data-ss-item><p id="danger"></p></article></section><p id="outside" style="position:absolute;top:400px">OUTSIDE_PRIVATE</p>';document.querySelector('#danger').textContent=${JSON.stringify(danger)};`);
 const tab=await cdp.eval(worker,`chrome.tabs.query({}).then(t=>t.find(x=>x.url?.startsWith(${JSON.stringify(origin)})).id)`);
 await cdp.eval(worker,`(async()=>{await chrome.tabs.update(${tab},{active:true});globalThis.requests=[];globalThis.saved=fetch;globalThis.fetch=(url,opts)=>{if(String(url).endsWith('/api/analyze'))requests.push(JSON.parse(opts.body));return saved(url,opts);};await chrome.scripting.executeScript({target:{tabId:${tab}},files:['shared.js','result_view.js','panel_view.js','content.js']});await chrome.tabs.sendMessage(${tab},{type:'SS_CHOOSE'});})()`);
 const rect=await cdp.eval(page,`(()=>{const r=document.querySelector('#region').getBoundingClientRect();return {x:r.x+8,y:r.y+8};})()`);
 await cdp.call('Input.dispatchMouseEvent',{type:'mouseMoved',...rect},page);await cdp.call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...rect},page);await cdp.call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...rect},page);
 async function shadowButton(text){const id=await wait(async()=>{const doc=await cdp.call('DOM.getDocument',{depth:-1,pierce:true},page);let found;function walk(n){if(n.nodeName==='BUTTON'&&n.children?.some(c=>c.nodeValue===text))found=n.nodeId;for(const child of [...(n.children||[]),...(n.shadowRoots||[])])walk(child);}walk(doc.root);return found;});const {object}=await cdp.call('DOM.resolveNode',{nodeId:id},page);await cdp.call('Runtime.callFunctionOn',{objectId:object.objectId,functionDeclaration:'function(){this.click();}',userGesture:true},page);}
 check('extension selection sends zero analysis requests',await cdp.eval(worker,'requests.length===0'));
 await shadowButton('Bật quét vùng này');
 await wait(()=>cdp.eval(page,`Array.from(document.querySelectorAll('[data-ss-owned=badge]')).some(x=>x.textContent.includes('Rủi ro cao'))`));
 check('extension receives local backend risk',await cdp.eval(worker,'requests.length>0&&requests.every(r=>!JSON.stringify(r).includes("OUTSIDE_PRIVATE"))'));
 await wait(()=>cdp.eval(page,'!!document.querySelector(".ss-urgent")'));
 check('extension displays grounded urgent explanation',await cdp.eval(page,`document.querySelector('.ss-urgent').textContent.includes('Ưu tiên an toàn')&&document.querySelector('.ss-explanation').textContent.includes('Hiện tại')`));
 await cdp.call('Page.captureScreenshot',{format:'png'},page).then(r=>fs.writeFileSync(path.join(out,'extension.png'),Buffer.from(r.data,'base64')));
 await cdp.eval(page,`document.querySelector('#danger').innerHTML='Đăng nhập tại <a href="https://youtubee.com/">https://youtubee.com/</a>';`);
 await wait(()=>cdp.eval(page,`Array.from(document.querySelectorAll('[data-ss-owned=badge]')).some(x=>x.textContent.includes('Có dấu hiệu đáng ngờ'))`));
 check('extension updates warning using URL support',await cdp.eval(worker,`requests.some(r=>JSON.stringify(r).includes('youtubee.com'))`));
 await cdp.eval(page,`document.querySelector('#danger').textContent='Chưa thấy tiền về, nhưng cứ giao máy trước.';`);
 await wait(()=>cdp.eval(page,`document.querySelector('[data-ss-owned=badge] .ss-summary')?.textContent.includes('giao tài sản')`));
 await cdp.eval(page,`document.querySelector('[data-ss-owned=badge] [data-action="supplement"]').click();document.querySelector('[data-ss-owned=badge] .ss-followup textarea').value='Tôi đã tự kiểm tra và nhận đủ tiền.';document.querySelector('[data-ss-owned=badge] .ss-followup form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));`);
 await wait(()=>cdp.eval(page,`document.querySelector('[data-ss-owned=badge] .ss-result')?.dataset.risk==='clear'`));
 check('extension clarification keeps binding and updates result',await cdp.eval(worker,`typeof requests.at(-1).clarification?.case_id==='string'&&requests.at(-1).clarification.revision===1`));
}finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));try{ws?.close();}catch{}chrome?.kill();server.kill();process.stdout.write(JSON.stringify(report)+'\nTest profile: '+profile+'\n');}
