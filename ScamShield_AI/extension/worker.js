/* Privileged network boundary. Page content cannot choose the API URL. */
const API='http://127.0.0.1:8000';
const sessions=new Map();
function trusted(sender){return sender.id===chrome.runtime.id&&sender.tab?.id!==undefined&&sender.frameId===0&&typeof sender.documentId==='string';}
function matches(s,sender,m){return s&&s.documentId===sender.documentId&&s.session===m.session&&s.url===sender.url;}
function stop(tabId){const old=sessions.get(tabId);old?.controller?.abort();old?.ocrController?.abort();sessions.delete(tabId);}
chrome.tabs.onRemoved.addListener(stop);
chrome.tabs.onUpdated.addListener((tabId,change)=>{if(change.url||change.status==='loading')stop(tabId);});
chrome.runtime.onMessage.addListener((m,sender,reply)=>{
  if(!trusted(sender)||!m||typeof m.type!=='string')return false;
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
