async function workTab(){
  try{
    const r=await chrome.runtime.sendMessage({type:'SS_PANEL',action:'tab'});
    if(r?.ok&&r.tab?.id)return r.tab;
  }catch{}
  try{
    if(chrome.windows?.getAll){
      const wins=await chrome.windows.getAll({populate:true,windowTypes:['normal']});
      for(const w of wins){const t=(w.tabs||[]).find(x=>x.active);if(t)return t;}
    }
  }catch{}
  const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
  if(tab)return tab;
  throw Error('Mở trang HTTP/HTTPS trước.');
}
document.getElementById('conversation')?.addEventListener('click',async()=>{
  const button=document.getElementById('conversation');button.disabled=true;button.classList?.add?.('busy');
  try{
    const tab=await workTab();
    if(!tab?.id||!/^https?:/.test(tab.url||''))throw Error('Mở trang HTTP/HTTPS trước.');
    const [loaded]=await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},func:()=>({loaded:!!globalThis.__scamShieldLoaded,build:globalThis.__scamShieldBuild})});
    if(loaded?.result?.loaded&&loaded.result.build!=='0.9.0')throw Error('Tab đang giữ phiên bản cũ. Hãy tải lại trang (Ctrl + Shift + R), rồi mở extension lại.');
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['conversation_model.js','conversation_adapter.js','conversation_export.js','conversation_capture.js']});
    await chrome.tabs.sendMessage(tab.id,{type:'SS_CONVERSATION_CHOOSE'},{frameId:0});window.close();
  }catch(e){document.getElementById('message').textContent='Không mở được chế độ thu thập. '+e.message;}
  finally{button.disabled=false;button.classList?.remove?.('busy');}
});
document.getElementById('choose').onclick=async()=>{
  const button=document.getElementById('choose');button.disabled=true;button.classList?.add?.('busy');
  try{
    const tab=await workTab();
    if(!tab?.id||!/^https?:/.test(tab.url||''))throw Error('Mở trang HTTP/HTTPS trước khi chọn vùng.');
    const [loaded]=await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},func:()=>({loaded:!!globalThis.__scamShieldLoaded,build:globalThis.__scamShieldBuild})});
    if(loaded?.result?.loaded&&loaded.result.build!=='0.9.0')throw Error('Tab đang giữ phiên bản cũ. Hãy tải lại trang (Ctrl + Shift + R), rồi mở extension lại.');
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['shared.js','result_view.js','panel_view.js','content.js']});
    await chrome.tabs.sendMessage(tab.id,{type:'SS_CHOOSE'},{frameId:0});
    window.close();
  }catch(e){document.getElementById('message').textContent='Không thể mở bộ chọn vùng trên tab này. '+e.message;}
  finally{button.disabled=false;button.classList?.remove?.('busy');}
};


(() => {
  const fileInput=document.getElementById('df-file');
  const checkBtn=document.getElementById('df-check');
  const liveBtn=document.getElementById('df-live');
  const fname=document.getElementById('df-fname');
  const box=document.getElementById('df-result');
  const msg=document.getElementById('message');
  if(!fileInput||!checkBtn||!liveBtn||!fname||!box)return;

  const THEMES={
    likely_real:{label:'Có vẻ thật',color:'#166534',background:'#f0fdf4',border:'#86efac'},
    likely_fake:{label:'Có dấu hiệu giả',color:'#991b1b',background:'#fef2f2',border:'#fca5a5'},
    uncertain:{label:'Chưa chắc chắn',color:'#9a3412',background:'#fff7ed',border:'#fdba74'},
    cannot_assess:{label:'Không đánh giá được',color:'#1e40af',background:'#eff6ff',border:'#93c5fd'}
  };
  function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  function setMsg(t){if(msg)msg.textContent=t||'';}
  function withTimeout(promise,ms,message){
    let t;const timeout=new Promise((_,rej)=>{t=setTimeout(()=>rej(Error(message)),ms);});
    return Promise.race([promise,timeout]).finally(()=>clearTimeout(t));
  }
  function renderResult(r,name){
    box.replaceChildren();box.hidden=false;
    const t=THEMES[r.verdict]||{label:'Chưa kiểm tra được',color:'#475569',background:'#f8fafc',border:'#cbd5e1'};
    const head=el('div',undefined,'ss-df-head');
    head.append(el('div','Kết quả deepfake','ss-df-title'));
    const badge=el('span',t.label,'ss-df-badge');
    Object.assign(badge.style,{color:t.color,background:t.background,border:'1px solid '+t.border,borderLeft:'4px solid '+t.color});
    head.append(badge);box.append(head);
    const body=el('div',undefined,'ss-df-body');
    const score=r.score==null?'–':Math.round(Math.max(0,Math.min(1,r.score))*100)+'%';
    body.append(el('p','Mức nghi giả mạo: '+score,'ss-df-score'));
    if(r.reason)body.append(el('p',r.reason,'ss-df-reason'));
    const list=el('ul');
    for(const item of (r.reasons||[]).slice(0,8)){
      const li=el('li',typeof item==='string'?item:(item.text||''));
      if(item&&item.abnormal&&!item.info)li.className='bad';
      else if(item&&item.info)li.className='info';
      list.append(li);
    }
    if(list.childElementCount)body.append(list);
    if(r.advice)body.append(el('p',r.advice,'hint'));
    if(name)body.append(el('p',name,'hint'));
    box.append(body);
  }

  let chosen=null;
  fileInput.addEventListener('change',()=>{
    chosen=fileInput.files&&fileInput.files[0];
    checkBtn.disabled=!chosen;
    checkBtn.classList?.remove?.('busy');
    box.hidden=true;box.replaceChildren();
    if(!chosen){fname.textContent='';return;}
    if(chosen.size>100*1024*1024){fname.textContent='Tệp vượt 100 MB.';chosen=null;checkBtn.disabled=true;return;}
    fname.textContent=chosen.name+' · '+(chosen.size/1048576).toFixed(2)+' MB';
  });

  checkBtn.addEventListener('click',async()=>{
    if(!chosen)return;
    checkBtn.disabled=true;checkBtn.classList?.add?.('busy');setMsg('');
    fname.textContent='Đang phân tích, video có thể mất 1–2 phút';
    try{
      const fd=new FormData();fd.append('file',chosen,chosen.name);
      const response=await withTimeout(
        fetch('http://127.0.0.1:8000/api/deepfake/check',{method:'POST',body:fd}),
        150000,
        'Hết thời gian chờ. Hãy kiểm tra CHAY_TAT_CA.cmd đang chạy (cổng 8000 và 8011), rồi thử lại.'
      );
      let data;try{data=await response.json();}catch{data=null;}
      if(!response.ok){
        if(data&&data.code==='DEEPFAKE_OFFLINE')throw Error('Chưa kết nối được mô-đun deepfake. Hãy chạy CHAY_TAT_CA.cmd rồi thử lại.');
        throw Error((data&&(data.message||data.code))||('HTTP '+response.status));
      }
      renderResult(data,chosen.name);
      fname.textContent='Đã phân tích '+chosen.name+'.';
    }catch(e){setMsg('Không kiểm tra được tệp. '+e.message);}
    finally{checkBtn.classList?.remove?.('busy');checkBtn.disabled=!chosen;}
  });

  liveBtn.addEventListener('click',async()=>{
    liveBtn.disabled=true;liveBtn.classList?.add?.('busy');setMsg('');
    try{
      // Never use the active tab: the call often lives in a separate Messenger popup window.
      const response=await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_BEGIN'});
      if(!response?.ok)throw Error(response?.error||'Không bắt đầu được.');
      if(response.stopped)setMsg('Đã dừng quét deepfake cuộc gọi.');
      else window.close();
    }catch(e){setMsg('Không quét được cuộc gọi. '+e.message);}
    finally{liveBtn.disabled=false;liveBtn.classList?.remove?.('busy');}
  });
})();

document.getElementById('win-min')?.addEventListener('click',()=>chrome.runtime.sendMessage({type:'SS_PANEL',action:'minimize'}));
document.getElementById('win-max')?.addEventListener('click',()=>chrome.runtime.sendMessage({type:'SS_PANEL',action:'maximize'}));
