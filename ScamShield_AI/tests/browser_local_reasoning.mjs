import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),origin='http://127.0.0.1:18769';
const profile=path.join(root,'.browser-profile-local-v2-'+Date.now()),out=path.join(root,'reports/local_v2_20261112/browser');
fs.mkdirSync(profile);fs.mkdirSync(out,{recursive:true});
const report={scope:'Real Chrome and real local API; no model provider. Injected error/stale-response scenarios are labeled.',checks:[]};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function wait(fn){for(let i=0;i<300;i++){const value=await fn();if(value)return value;await pause(100);}throw Error('Browser wait timed out');}
function check(name,value){report.checks.push({name,passed:!!value});if(!value)throw Error(name);}
class CDP{
 constructor(ws){this.ws=ws;this.seq=0;this.pending=new Map();ws.onmessage=e=>{const d=JSON.parse(e.data),p=this.pending.get(d.id);if(p){this.pending.delete(d.id);d.error?p.reject(Error(d.error.message)):p.resolve(d.result);}};}
 call(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++this.seq;this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params,sessionId}));});}
 async eval(page,expression){const d=await this.call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},page);if(d.exceptionDetails)throw Error(d.exceptionDetails.exception?.description||d.exceptionDetails.text);return d.result.value;}
}
const server=spawn('python',['-m','uvicorn','backend.main:app','--app-dir',root,'--host','127.0.0.1','--port','18769','--no-access-log'],{cwd:root,env:{...process.env,SCAMSHIELD_MODE:'mock'},windowsHide:true,stdio:'ignore'});
let chrome,ws;
try{
 await wait(async()=>{try{return(await fetch(origin+'/health')).ok;}catch{return false;}});
 const port=24000+Math.floor(Math.random()*1000);
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--remote-debugging-port='+port,'--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
 const version=await wait(async()=>{try{return await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();}catch{return false;}});report.browser=version.Browser;
 ws=new WebSocket(version.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});const cdp=new CDP(ws);
 const {targetId}=await cdp.call('Target.createTarget',{url:origin+'/local'});const {sessionId:page}=await cdp.call('Target.attachToTarget',{targetId,flatten:true});
 await wait(()=>cdp.eval(page,'!!document.querySelector("#text")'));
 const run=async(text,risk)=>{await cdp.eval(page,`document.querySelector('#text').value=${JSON.stringify(text)};document.querySelector('#text').dispatchEvent(new Event('input'));document.querySelector('#form').dispatchEvent(new Event('submit',{cancelable:true}));`);await wait(()=>cdp.eval(page,`!document.querySelector('#result').hidden&&document.querySelector('#result').dataset.risk===${JSON.stringify(risk)}&&!document.querySelector('#send').disabled`));};
 for(const [text,risk] of [['Cảnh báo: có người bị ép tham gia lừa đảo.','clear'],['Sang bên này anh lo hết.','need_context'],['Gửi ảnh CCCD qua chat.','suspicious'],['Gửi mã OTP cho tôi.','high']]){
  await run(text,risk);check('renders '+risk,await cdp.eval(page,`document.querySelector('#result').dataset.risk===${JSON.stringify(risk)}`));
 }
 const danger='Tôi đang bị ép làm việc.';await run(danger,'high');
 check('current coercion shows urgent help before optional questions',await cdp.eval(page,`!document.querySelector('#urgency').hidden&&document.querySelector('#actions').children.length>0&&document.querySelector('#urgency').getBoundingClientRect().top<document.querySelector('#questions').getBoundingClientRect().top`));
 check('user-facing view hides answer and rule/source internals',await cdp.eval(page,`!document.querySelector('#result').innerText.includes('answers_18')&&!document.querySelector('#result').innerText.includes('R-URGENT')&&!document.querySelector('#result a')`));
 await cdp.call('Page.captureScreenshot',{format:'png'},page).then(r=>fs.writeFileSync(path.join(out,'urgent.png'),Buffer.from(r.data,'base64')));
 await run('Gửi mã OTP <img src=x onerror="globalThis.injected=1"> cho tôi','high');
 check('verified quote HTML rendered as text',await cdp.eval(page,`!document.querySelector('#result img')&&!globalThis.injected&&document.querySelector('#evidence').innerText.includes('<img')`));
 await cdp.eval(page,`globalThis.savedFetch=fetch;globalThis.fetch=async()=>{throw Error('offline')}`);
 await cdp.eval(page,`document.querySelector('#text').value='Nội dung mới';document.querySelector('#text').dispatchEvent(new Event('input'));document.querySelector('#form').dispatchEvent(new Event('submit',{cancelable:true}));`);
 await wait(()=>cdp.eval(page,'!document.querySelector("#send").disabled'));
 check('offline error does not leave a green result and retains safety guidance',await cdp.eval(page,`document.querySelector('#result').hidden&&document.querySelector('#status').textContent.includes('nguy hiểm')`));
 await cdp.eval(page,`(async()=>{globalThis.fetch=savedFetch;globalThis.urgentData=await savedFetch('/api/analyze-local',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:[{id:'m1',speaker_id:'user',text:${JSON.stringify(danger)}}]})}).then(r=>r.json());globalThis.fetch=async()=>({ok:false,json:async()=>urgentData});})()`);
 await run(danger,'high');check('injected 503 with grounded urgent payload retains help',await cdp.eval(page,`!document.querySelector('#urgency').hidden&&document.querySelector('#status').textContent.includes('chưa hoàn tất')`));
 await cdp.eval(page,`globalThis.fetch=async(...args)=>{const result=await savedFetch(...args);if(JSON.parse(args[1].body).messages[0].text==='Gửi mã OTP cho tôi.')await new Promise(r=>globalThis.releaseOld=r);return result;}`);
 await cdp.eval(page,`document.querySelector('#text').value='Gửi mã OTP cho tôi.';document.querySelector('#text').dispatchEvent(new Event('input'));document.querySelector('#form').dispatchEvent(new Event('submit',{cancelable:true}));`);
 await wait(()=>cdp.eval(page,'!!globalThis.releaseOld'));
 await run('Cảnh báo: đừng gửi OTP.','clear');await cdp.eval(page,'releaseOld()');await pause(200);
 check('old result ignored after input changes',await cdp.eval(page,`document.querySelector('#result').dataset.risk==='clear'`));
}finally{
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
 try{ws?.close();}catch{}chrome?.kill();server.kill();
 process.stdout.write(JSON.stringify(report)+'\nTest profile: '+profile+'\n');
}
