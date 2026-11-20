/* Privileged network boundary. Page content cannot choose the API URL. */
const API='http://127.0.0.1:8000';
const sessions=new Map();
function fromExtension(sender){return sender.id===chrome.runtime.id;}
function fromPopup(sender){if(!fromExtension(sender))return false;if(sender.tab===undefined)return true;try{const u=chrome.runtime.getURL('popup.html');return sender.url===u||sender.tab?.url===u;}catch{return false;}}
function trusted(sender){return fromExtension(sender)&&sender.tab?.id!==undefined&&sender.frameId===0&&typeof sender.documentId==='string';}
function trustedDeepfake(sender){return fromExtension(sender)&&sender.tab?.id!==undefined&&typeof sender.documentId==='string';}
function fromOffscreen(sender){try{return fromExtension(sender)&&sender.url===chrome.runtime.getURL('offscreen.html');}catch{return false;}}
const DF_MAX_CHECK=100*1024*1024, DF_MAX_FRAME=8*1024*1024;
let dfOffscreen=null;
let dfLive={tabId:null,session:null,running:false};
let panelWinId=null,panelTabId=null,panelMax=false;
const DF_HOST_QUERY=[
  'https://*.messenger.com/*','https://messenger.com/*','https://www.messenger.com/*',
  'https://*.facebook.com/*','https://facebook.com/*','https://www.facebook.com/*',
  'https://chat.zalo.me/*','https://*.zalo.me/*'
];
const DF_NO_CALL='Không tìm thấy cửa sổ cuộc gọi Messenger hoặc Zalo. Hãy bắt đầu cuộc gọi trên trình duyệt (cửa sổ riêng cũng được) và giữ cửa sổ đó mở, rồi bấm lại. Không cần bấm đúng tab đó.';
function isCallUrl(url){
  if(!url||!/^https?:/i.test(url))return false;
  try{
    const u=new URL(url),host=u.hostname.replace(/^www\./,'').toLowerCase(),path=u.pathname+u.search;
    const callPath=/\/groupcall|\/videocall|[?&]call_id=|[?&]has_video=true|\/call\b/i.test(path);
    const isMsg=host==='messenger.com'||host.endsWith('.messenger.com');
    const isFb=host==='facebook.com'||host.endsWith('.facebook.com');
    const isZalo=host==='chat.zalo.me'||host==='zalo.me'||host.endsWith('.zalo.me');
    return callPath&&(isMsg||isFb||isZalo);
  }catch{return false;}
}
function isCallHost(url){
  if(!url)return false;
  try{
    const host=new URL(url).hostname.replace(/^www\./,'').toLowerCase();
    return host==='messenger.com'||host.endsWith('.messenger.com')||host==='facebook.com'||host.endsWith('.facebook.com')||host==='chat.zalo.me'||host==='zalo.me'||host.endsWith('.zalo.me');
  }catch{return false;}
}
function probeCallVideos(){
  const isSelf=v=>{
    const s=((v.className||'')+' '+(v.id||'')+' '+(v.getAttribute('aria-label')||'')+' '+(v.parentElement?.className||'')+' '+(v.parentElement?.parentElement?.className||'')).toLowerCase();
    if(/self|local-video|localvideo|preview|mirror|my-video|own.?video|webcam|camera-preview/.test(s))return true;
    const t=getComputedStyle(v).transform;
    return !!(t&&t!=='none'&&/matrix\(\s*-/.test(t));
  };
  const vids=[...document.querySelectorAll('video')].filter(v=>v.readyState>=2&&v.videoWidth>=32&&v.offsetWidth>0&&v.offsetHeight>0);
  const displays=vids.map(v=>{const r=v.getBoundingClientRect();return r.width*r.height;});
  const largest=Math.max(0,...displays);
  const vw=innerWidth,vh=innerHeight,view=vw*vh;
  return vids.map((v,i)=>{
    const r=v.getBoundingClientRect(),area=r.width*r.height;
    const nearL=r.left<vw*0.18,nearR=r.right>vw*0.82,nearT=r.top<vh*0.18,nearB=r.bottom>vh*0.82;
    const small=area<view*0.18||Math.max(r.width,r.height)<280||(largest>0&&area<largest*0.4);
    const corner=small&&(nearL||nearR)&&(nearT||nearB);
    return {area:v.videoWidth*v.videoHeight,display:area,playing:!v.paused&&!v.ended,self:isSelf(v),corner};
  });
}
async function findCallTab(preferredId){
  if(preferredId){
    try{
      const t=await chrome.tabs.get(preferredId);
      if(isCallUrl(t.url))return t;
    }catch{}
  }
  let tabs=[];
  try{tabs=await chrome.tabs.query({url:DF_HOST_QUERY});}catch{tabs=[];}
  if(!tabs.length){
    const all=await chrome.tabs.query({});
    tabs=all.filter(t=>isCallHost(t.url));
  }
  const byUrl=tabs.filter(t=>isCallUrl(t.url));
  if(byUrl.length===1)return byUrl[0];
  if(byUrl.length>1){
    byUrl.sort((a,b)=>(b.lastAccessed||0)-(a.lastAccessed||0));
    return byUrl[0];
  }
  const scored=[];
  for(const tab of tabs){
    try{
      const probes=await chrome.scripting.executeScript({target:{tabId:tab.id,allFrames:true},func:probeCallVideos});
      let best=0;
      for(const row of probes||[]){
        for(const v of row.result||[]){
          if(v.playing&&!v.self&&!v.corner&&v.area>best)best=v.area;
        }
      }
      if(best>=160*160)scored.push({tab,best,lastAccessed:tab.lastAccessed||0});
    }catch{}
  }
  if(scored.length===1)return scored[0].tab;
  if(scored.length>1){
    scored.sort((a,b)=>(b.lastAccessed||0)-(a.lastAccessed||0)||b.best-a.best);
    return scored[0].tab;
  }
  throw Error(DF_NO_CALL);
}
async function stopLiveScan(){
  const tabId=dfLive.tabId;
  dfLive={tabId:null,session:null,running:false};
  await stopOffscreen();
  if(tabId){try{await chrome.tabs.sendMessage(tabId,{type:'SS_DEEPFAKE_LIVE_STOP'});}catch{}}
}
async function beginLiveScan(preferredId){
  if(dfLive.running){
    await stopLiveScan();
    return {ok:true,stopped:true};
  }
  const tab=await findCallTab(preferredId);
  if(!tab?.id||!isCallHost(tab.url)&&!isCallUrl(tab.url))throw Error(DF_NO_CALL);
  // Never inject into a random active tab (Bing, edge://extensions, ...).
  await chrome.scripting.executeScript({target:{tabId:tab.id,allFrames:true},files:['deepfake_live.js']});
  const probes=await chrome.scripting.executeScript({target:{tabId:tab.id,allFrames:true},func:probeCallVideos});
  let best=null;
  for(const row of probes||[]){
    for(const v of row.result||[]){
      const cand={frameId:row.frameId,area:v.area,display:v.display||0,playing:v.playing,self:v.self,corner:v.corner};
      const rank=x=>(x.playing&&!x.self&&!x.corner?4:x.playing&&!x.self?3:x.playing?2:!x.self?1:0)*1e12+(x.display||x.area);
      if(!best||rank(cand)>rank(best))best=cand;
    }
  }
  if(best&&(best.self||best.corner)&&best.display<1e9){
    const remote=best.playing&&!best.self&&!best.corner;
    if(!remote){/* keep best only if nothing else — already selected by rank */}
  }
  const session='df-'+Math.random().toString(36).slice(2)+Date.now().toString(36);
  const overlay=await chrome.tabs.sendMessage(tab.id,{type:'SS_DEEPFAKE_LIVE_START_OVERLAY',session},{frameId:0});
  if(!overlay?.ok)throw Error(overlay?.error||'Không mở được bảng kết quả trên cửa sổ cuộc gọi. Hãy tải lại cửa sổ cuộc gọi (F5), rồi thử lại.');
  if(best&&!best.self&&!best.corner){
    const cap=await chrome.tabs.sendMessage(tab.id,{type:'SS_DEEPFAKE_LIVE_START_CAPTURE',session,source:'video'},{frameId:best.frameId});
    if(!cap?.ok)throw Error(cap?.error||'Không bắt được hình cuộc gọi.');
  }else if(best){
    const cap=await chrome.tabs.sendMessage(tab.id,{type:'SS_DEEPFAKE_LIVE_START_CAPTURE',session,source:'video'},{frameId:best.frameId});
    if(!cap?.ok)throw Error(cap?.error||'Không bắt được hình cuộc gọi.');
  }else{
    if(!chrome.tabCapture||!chrome.tabCapture.getMediaStreamId)throw Error('Không tìm thấy video trong cửa sổ cuộc gọi.');
    const streamId=await chrome.tabCapture.getMediaStreamId({targetTabId:tab.id});
    await ensureOffscreen();
    dfOffscreen={tabId:tab.id,session};
    await dfReset(session);
    const started=await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_OFFSCREEN_START',streamId,session,tabId:tab.id});
    if(!started?.ok)throw Error(started?.error||'Không bắt được hình cửa sổ cuộc gọi.');
  }
  dfLive={tabId:tab.id,session,running:true};
  return {ok:true,stopped:false,tabId:tab.id,url:tab.url};
}

function decodePayloadBytes(m, max, emptyMsg){
  let buf=null;
  if(typeof m.base64==='string'&&m.base64.length){
    try{
      const bin=atob(m.base64);
      const out=new Uint8Array(bin.length);
      for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);
      buf=out.buffer;
    }catch{throw Error(emptyMsg);}
  }else if(m.bytes instanceof Uint8Array){
    buf=m.bytes.buffer.slice(m.bytes.byteOffset,m.bytes.byteOffset+m.bytes.byteLength);
  }else if(typeof ArrayBuffer!=='undefined'&&m.bytes instanceof ArrayBuffer){
    buf=m.bytes;
  }else if(m.bytes&&typeof m.bytes.byteLength==='number'&&m.bytes.byteLength>0){
    try{buf=new Uint8Array(m.bytes).buffer;}catch{buf=null;}
  }
  if(!buf||buf.byteLength<1||buf.byteLength>max)throw Error(emptyMsg);
  return buf;
}
async function dfPost(path, bytes, filename, mime, sessionId, timeoutMs){
  const blob=new Blob([bytes],{type:mime||'application/octet-stream'});
  const fd=new FormData();fd.append('file',blob,filename||'frame.jpg');
  const url=API+'/api/deepfake/'+path+(sessionId?('?session_id='+encodeURIComponent(sessionId)):'');
  const r=await fetch(url,{method:'POST',body:fd,signal:AbortSignal.timeout(timeoutMs||30000)});
  let data;try{data=await r.json();}catch{data=null;}
  if(!r.ok){
    const code=data&&data.code, message=data&&data.message;
    if(code==='DEEPFAKE_OFFLINE')throw Error('Chưa kết nối được mô-đun deepfake. Hãy chạy CHAY_TAT_CA.cmd rồi thử lại.');
    throw Error(message||code||('HTTP_'+r.status));
  }
  return data;
}
async function dfReset(sessionId){
  const r=await fetch(API+'/api/deepfake/frame/reset?session_id='+encodeURIComponent(sessionId),{method:'POST',signal:AbortSignal.timeout(5000)});
  if(!r.ok)throw Error('Không khởi tạo được phiên deepfake.');
}
async function ensureOffscreen(){
  if(!chrome.offscreen)throw Error('Trình duyệt chưa hỗ trợ offscreen (cần Edge/Chrome 116+).');
  const has=chrome.offscreen.hasDocument?await chrome.offscreen.hasDocument():false;
  if(has)return;
  await chrome.offscreen.createDocument({url:'offscreen.html',reasons:['USER_MEDIA'],justification:'Chụp khung hình tab cuộc gọi để kiểm tra deepfake trên máy cục bộ.'});
}
async function stopOffscreen(){
  try{await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_OFFSCREEN_STOP'});}catch{}
  try{if(chrome.offscreen&&chrome.offscreen.hasDocument&&await chrome.offscreen.hasDocument())await chrome.offscreen.closeDocument();}catch{}
  dfOffscreen=null;
}
async function handleDeepfake(m,sender){
  if(m.type==='SS_DEEPFAKE_CHECK'){
    if(!fromPopup(sender)&&!trustedDeepfake(sender)&&!fromOffscreen(sender))throw Error('UNAUTHORIZED');
    if(typeof m.name!=='string'||m.name.length>200)throw Error('Tên tệp không hợp lệ.');
    const bytes=decodePayloadBytes(m,DF_MAX_CHECK,'Tệp trống hoặc vượt 100 MB.');
    const mime=typeof m.mime==='string'&&m.mime.length<100?m.mime:'application/octet-stream';
    return {ok:true,result:await dfPost('check',bytes,m.name,mime,null,180000)};
  }
  if(m.type==='SS_DEEPFAKE_FRAME_RESET'){
    if(!fromPopup(sender)&&!trustedDeepfake(sender)&&!fromOffscreen(sender))throw Error('UNAUTHORIZED');
    if(typeof m.session!=='string'||!m.session||m.session.length>64)throw Error('INVALID_SESSION');
    await dfReset(m.session);
    return {ok:true};
  }
  if(m.type==='SS_DEEPFAKE_FRAME'){
    if(!trustedDeepfake(sender)&&!fromPopup(sender)&&!fromOffscreen(sender))throw Error('UNAUTHORIZED');
    if(typeof m.session!=='string'||!m.session||m.session.length>64)throw Error('INVALID_SESSION');
    let bytes;
    try{bytes=decodePayloadBytes(m,DF_MAX_FRAME,'Chưa gửi được khung hình. Hãy thử lại.');}
    catch{return {ok:true,skipped:true,result:{verdict:'cannot_assess',smoothed_score:null,frames_received:0,reasons:[{text:'Chưa thấy khuôn mặt'}]}};}
    if(bytes.byteLength<800)return {ok:true,skipped:true,result:{verdict:'cannot_assess',smoothed_score:null,frames_received:0,reasons:[{text:'Chưa thấy khuôn mặt'}]}};
    return {ok:true,result:await dfPost('frame',bytes,'frame.jpg',m.mime||'image/jpeg',m.session,30000)};
  }
  if(m.type==='SS_DEEPFAKE_LIVE_RESULT'){
    if(!trustedDeepfake(sender)&&!fromOffscreen(sender))throw Error('UNAUTHORIZED');
    if(sender.tab?.id){
      try{await chrome.tabs.sendMessage(sender.tab.id,{type:'SS_DEEPFAKE_OVERLAY_UPDATE',result:m.result,error:m.error,source:m.source},{frameId:0});}catch{}
    }else if(m.tabId){
      try{await chrome.tabs.sendMessage(m.tabId,{type:'SS_DEEPFAKE_OVERLAY_UPDATE',result:m.result,error:m.error,source:m.source},{frameId:0});}catch{}
    }
    return {ok:true};
  }
  if(m.type==='SS_DEEPFAKE_LIVE_BEGIN'){
    if(!fromPopup(sender)&&!trustedDeepfake(sender))throw Error('UNAUTHORIZED');
    const prefer=m.useThisTab&&sender.tab?.id&&isCallUrl(sender.tab.url||'')?sender.tab.id:null;
    return await beginLiveScan(prefer);
  }
  if(m.type==='SS_DEEPFAKE_LIVE_STOP'){
    if(!fromPopup(sender)&&!trustedDeepfake(sender)&&!fromOffscreen(sender))throw Error('UNAUTHORIZED');
    await stopLiveScan();
    return {ok:true};
  }
  if(m.type==='SS_DEEPFAKE_TABCAPTURE'){
    if(!fromPopup(sender)&&!trustedDeepfake(sender)&&!fromOffscreen(sender))throw Error('UNAUTHORIZED');
    const tabId=m.tabId||sender.tab?.id;
    if(!tabId)throw Error('Không xác định được tab cuộc gọi.');
    if(typeof m.session!=='string'||!m.session||m.session.length>64)throw Error('INVALID_SESSION');
    if(!chrome.tabCapture||!chrome.tabCapture.getMediaStreamId)throw Error('Trình duyệt không hỗ trợ tabCapture.');
    const streamId=await chrome.tabCapture.getMediaStreamId({targetTabId:tabId});
    await ensureOffscreen();
    dfOffscreen={tabId,session:m.session};
    await dfReset(m.session);
    const started=await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_OFFSCREEN_START',streamId,session:m.session,tabId});
    if(!started?.ok)throw Error(started?.error||'Không bắt được hình tab.');
    return {ok:true,source:'tabCapture'};
  }
  throw Error('INVALID_MESSAGE');
}

function matches(s,sender,m){return s&&s.documentId===sender.documentId&&s.session===m.session&&s.url===sender.url;}
function stop(tabId){const old=sessions.get(tabId);old?.controller?.abort();old?.ocrController?.abort();sessions.delete(tabId);}
chrome.tabs.onRemoved.addListener(tabId=>{stop(tabId);if(dfLive.tabId===tabId)stopLiveScan();});
chrome.tabs.onUpdated.addListener((tabId,change)=>{if(change.url||change.status==='loading')stop(tabId);if(dfLive.tabId===tabId&&change.url)stopLiveScan();});
chrome.runtime.onMessage.addListener((m,sender,reply)=>{
  if(!fromExtension(sender)||!m||typeof m.type!=='string')return false;
  if(m.type==='SS_PANEL'){
    (async()=>{
      if(m.action==='minimize'&&panelWinId){await chrome.windows.update(panelWinId,{state:'minimized'});return {ok:true};}
      if(m.action==='maximize'&&panelWinId){
        panelMax=!panelMax;
        await chrome.windows.update(panelWinId,{state:panelMax?'maximized':'normal'});
        return {ok:true};
      }
      if(m.action==='tab'){
        if(panelTabId){try{return {ok:true,tab:await chrome.tabs.get(panelTabId)};}catch{panelTabId=null;}}
        const wins=await chrome.windows.getAll({populate:true,windowTypes:['normal']});
        const t=wins.flatMap(x=>x.tabs||[]).find(x=>x.active);
        return {ok:!!t,tab:t||null};
      }
      return {ok:false};
    })().then(reply).catch(e=>reply({ok:false,error:e.message}));
    return true;
  }
  if(typeof m.type==='string'&&m.type.startsWith('SS_DEEPFAKE_')){
    if(m.type==='SS_DEEPFAKE_OFFSCREEN_START'||m.type==='SS_DEEPFAKE_OFFSCREEN_STOP')return false;
    (async()=>handleDeepfake(m,sender))().then(reply).catch(e=>reply({ok:false,error:e.message||'NETWORK_ERROR'}));
    return true;
  }
  if(!trusted(sender))return false;
  const tabId=sender.tab.id;
  (async()=>{
    if(m.type==='SS_CONFIG'){
      const r=await fetch(API+'/client-config',{signal:AbortSignal.timeout(5000),cache:'no-store'});
      if(!r.ok)throw Error('CONFIG_ERROR');return {ok:true,protocol:2,config:await r.json()};
    }
    if(m.type==='SS_OPEN'){
      if(typeof m.session!=='string'||m.session.length>100)throw Error('INVALID_SESSION');
      stop(tabId);sessions.set(tabId,{documentId:sender.documentId,session:m.session,url:sender.url,controller:null});
      return {ok:true,tabId,documentId:sender.documentId,session:m.session};
    }
    const s=sessions.get(tabId);
    if(!matches(s,sender,m))throw Error('SESSION_MISSING');
    if(m.type==='SS_STOP'){stop(tabId);return {ok:true};}
    if(m.type==='SS_CAPTURE'){
      if(!Array.isArray(m.redactions)||m.redactions.length>200)throw Error('CROP_TOO_COMPLEX');
      const rect=m.rect,viewport=m.viewport;
      if(!rect||!viewport||![rect.x,rect.y,rect.width,rect.height,viewport.width,viewport.height].every(Number.isFinite)||rect.x<0||rect.y<0||rect.width<1||rect.height<1||rect.x+rect.width>viewport.width+1||rect.y+rect.height>viewport.height+1)throw Error('INVALID_CROP');
      const active=await chrome.tabs.query({active:true,windowId:sender.tab.windowId});
      if(active[0]?.id!==tabId)throw Error('TAB_CHANGED');
      const screenshot=await chrome.tabs.captureVisibleTab(sender.tab.windowId,{format:'png'});
      const after=await chrome.tabs.query({active:true,windowId:sender.tab.windowId});
      if(after[0]?.id!==tabId||sessions.get(tabId)!==s)throw Error('STALE_SESSION');
      const bitmap=await createImageBitmap(await (await fetch(screenshot)).blob());
      try{
        const sx=bitmap.width/viewport.width,sy=bitmap.height/viewport.height;
        const width=Math.round(rect.width*sx),height=Math.round(rect.height*sy);
        if(width*height>8000000)throw Error('CROP_TOO_LARGE');
        const canvas=new OffscreenCanvas(width,height),ctx=canvas.getContext('2d');
        ctx.drawImage(bitmap,rect.x*sx,rect.y*sy,rect.width*sx,rect.height*sy,0,0,width,height);
        for(const mask of m.redactions){if(![mask.x,mask.y,mask.width,mask.height].every(Number.isFinite))throw Error('INVALID_MASK');ctx.fillStyle='white';ctx.fillRect((mask.x-rect.x)*sx,(mask.y-rect.y)*sy,mask.width*sx,mask.height*sy);}
        const blob=await canvas.convertToBlob({type:'image/png'});
        if(blob.size>4*1024*1024)throw Error('IMAGE_TOO_LARGE');
        const bytes=new Uint8Array(await blob.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
        return {ok:true,image:'data:image/png;base64,'+btoa(binary)};
      }finally{bitmap.close();}
    }
    if(m.type==='SS_IMAGE_OCR'){
      if(s.ocrController)throw Error('OCR_BUSY');
      if(typeof m.image!=='string'||!m.image.startsWith('data:image/png;base64,')||m.image.length>5600000)throw Error('INVALID_IMAGE');
      const bytes=Uint8Array.from(atob(m.image.split(',')[1]),c=>c.charCodeAt(0));
      const control=new AbortController();s.ocrController=control;
      try{const r=await fetch(API+'/api/ocr',{method:'POST',headers:{'Content-Type':'image/png'},body:bytes,signal:control.signal});const data=await r.json();if(sessions.get(tabId)!==s)throw Error('STALE_SESSION');return r.ok?{ok:true,ocr:data}:{ok:false,error:data.code||'OCR_ERROR'};}
      finally{if(s.ocrController===control)s.ocrController=null;}
    }
    if(m.type!=='SS_ANALYZE')throw Error('INVALID_MESSAGE');
    if(s.controller)throw Error('BUSY');
    let payload;
    if(m.payload){if(typeof m.payload!=='object'||Array.isArray(m.payload)||JSON.stringify(m.payload).length>65536)throw Error('INVALID_INPUT');payload=m.payload;}
    else{if(typeof m.text!=='string'||!m.text.trim()||Array.from(m.text).length>10000)throw Error('INVALID_INPUT');payload={text:m.text};}
    const control=new AbortController();s.controller=control;
    // Temporarily disabled response deadline; session stop/navigation still aborts.
    // const timer=setTimeout(()=>control.abort(),55000);
    try{
      const r=await fetch(API+'/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:control.signal});
      if(!r.ok){
        let failure;try{failure=await r.json();}catch{}
        let message='HTTP_'+r.status;
        if(['CASE_EXPIRED','STALE_ANALYSIS','SITUATION_MISMATCH','QUESTION_MISMATCH'].includes(failure?.code))message='Phiên hoặc tình huống đã thay đổi. Hãy phân tích lại nội dung hiện tại.';
        if(failure?.code==='PROVIDER_INCONSISTENT_OUTPUT')message='Kết quả còn mâu thuẫn. Chưa có kết luận; hãy thử lại.';
        if(failure?.code==='EVIDENCE_INVALID')message='Bằng chứng chưa khớp nội dung gốc. Chưa có kết luận; hãy thử lại.';
        if(failure?.code==='INVALID_INPUT'){
          const known=new Set(['text','messages','context','question','ocr_sources','links','id','message_id','url','display_text','start','end','origin','speaker','source_id']);
          const fields=(failure.diagnostic?.issues||[]).slice(0,5).map(x=>Array.isArray(x.path)?x.path.filter(p=>Number.isInteger(p)||known.has(p)).join('.'):'' ).filter(Boolean);
          message='Dữ liệu gửi không hợp lệ (422)'+(fields.length?' — '+fields.join(', '):'')+'. Tải lại extension và trang; nếu còn lỗi, kiểm tra bản gửi.';
        }
        if(failure?.code?.startsWith('PROVIDER_')&&message==='HTTP_'+r.status)message=failure.code+' — backend chưa trả được kết quả. Hãy thử lại.';
        return {ok:false,error:message};
      }
      const result=await r.json();
      if(sessions.get(tabId)!==s)throw Error('STALE_SESSION');
      return {ok:true,result,tabId,documentId:s.documentId,session:s.session,itemId:m.itemId,version:m.version};
    }finally{
      // clearTimeout(timer); // Restore together with the timer above.
      if(s.controller===control)s.controller=null;
    }
  })().then(reply).catch(e=>reply({ok:false,error:e.name==='AbortError'?'TIMEOUT':(e.message||'NETWORK_ERROR')}));
  return true;
});
chrome.commands?.onCommand?.addListener(async command=>{
  if(command!=='toggle-deepfake-scan')return;
  try{
    const [active]=await chrome.tabs.query({active:true,lastFocusedWindow:true});
    const prefer=isCallUrl(active?.url||'')?active.id:null;
    await beginLiveScan(prefer);
  }catch(e){
    const [active]=await chrome.tabs.query({active:true,lastFocusedWindow:true});
    if(active?.id){
      try{await chrome.scripting.executeScript({target:{tabId:active.id},func:(msg)=>{alert(msg);},args:[e.message||DF_NO_CALL]});}catch{}
    }
  }
});

async function openPanel(tab){
  if(tab?.id&&!String(tab.url||'').startsWith('chrome-extension:'))panelTabId=tab.id;
  if(panelWinId){
    try{await chrome.windows.update(panelWinId,{focused:true});return;}catch{panelWinId=null;}
  }
  const win=await chrome.windows.create({url:chrome.runtime.getURL('popup.html'),type:'popup',width:400,height:640,focused:true});
  panelWinId=win.id;panelMax=false;
}
chrome.action?.onClicked?.addListener(tab=>{openPanel(tab).catch(()=>{});});
if(chrome.windows?.onRemoved)chrome.windows.onRemoved.addListener(id=>{if(id===panelWinId)panelWinId=null;});
