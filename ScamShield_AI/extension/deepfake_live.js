/* Overlay + capture khung hinh cuoc goi. Khong dung __scamShieldLoaded cua quet vung. */
(() => {
  if(globalThis.__scamShieldDeepfakeLive)return;
  globalThis.__scamShieldDeepfakeLive=true;

  const THEMES={
    likely_real:{label:'Có vẻ thật',color:'#166534',background:'#f0fdf4',border:'#86efac'},
    likely_fake:{label:'Có dấu hiệu giả',color:'#991b1b',background:'#fef2f2',border:'#fca5a5'},
    uncertain:{label:'Chưa chắc chắn',color:'#9a3412',background:'#fff7ed',border:'#fdba74'},
    cannot_assess:{label:'Không đánh giá được',color:'#1e40af',background:'#eff6ff',border:'#93c5fd'}
  };
  let overlay=null,session=null,timer=null,busy=false,grab=null,running=false,drag=null,launch=null,collapsed=true,minimized=false,maximized=false;


  function bytesToBase64(buf){
    const bytes=buf instanceof Uint8Array?buf:new Uint8Array(buf);
    let binary='';
    for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+32768));
    return btoa(binary);
  }
  function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  function $(sel){return overlay&&overlay.querySelector(sel);}
  function isCallPage(){
    const u=location.href;
    return /\/groupcall|\/videocall|[?&]call_id=|[?&]has_video=true|\/call\b/i.test(u);
  }

  function isSelf(v){
    const s=((v.className||'')+' '+(v.id||'')+' '+(v.getAttribute('aria-label')||'')+' '+(v.parentElement?.className||'')+' '+(v.parentElement?.parentElement?.className||'')).toLowerCase();
    if(/self|local-video|localvideo|preview|mirror|my-video|own.?video|webcam|camera-preview/.test(s))return true;
    const t=getComputedStyle(v).transform;
    return !!(t&&t!=='none'&&/matrix\(\s*-/.test(t));
  }
  function isCornerSelf(v,largestDisplay){
    const r=v.getBoundingClientRect(),vw=innerWidth,vh=innerHeight,area=r.width*r.height,view=vw*vh;
    if(largestDisplay&&area<largestDisplay*0.4)return true;
    const nearL=r.left<vw*0.18,nearR=r.right>vw*0.82,nearT=r.top<vh*0.18,nearB=r.bottom>vh*0.82;
    const small=area<view*0.18||Math.max(r.width,r.height)<280;
    return small&&(nearL||nearR)&&(nearT||nearB);
  }
  function pickVideo(){
    const all=[...document.querySelectorAll('video')].filter(v=>v.readyState>=2&&v.videoWidth>=32&&v.offsetWidth>0);
    if(!all.length)return null;
    const largest=Math.max(0,...all.map(v=>{const r=v.getBoundingClientRect();return r.width*r.height;}));
    const remote=all.filter(v=>!isSelf(v)&&!isCornerSelf(v,largest));
    const pool=(remote.length?remote:all.filter(v=>!isCornerSelf(v,largest)));
    const list=(pool.length?pool:all).slice().sort((a,b)=>{
      const da=a.getBoundingClientRect(),db=b.getBoundingClientRect();
      return (db.width*db.height)-(da.width*da.height);
    });
    const playing=list.filter(v=>!v.paused&&!v.ended);
    return playing[0]||list[0]||null;
  }
  function isBlankCanvas(canvas){
    const w=canvas.width,h=canvas.height;
    if(!w||!h)return true;
    const ctx=canvas.getContext('2d'),data=ctx.getImageData(0,0,w,h).data;
    let sum=0,n=0,step=Math.max(1,Math.floor((data.length/4)/900));
    for(let i=0;i<data.length;i+=4*step){sum+=data[i]+data[i+1]+data[i+2];n++;}
    return !n||(sum/(n*3))<10;
  }

  function setLaunchLabel(){
    if(!launch)return;
    launch.textContent=running?'Dừng quét':'Quét deepfake';
  }
  function ensureLaunchButton(){
    if(window.top!==window)return;
    if(!isCallPage()&&!pickVideo())return;
    if(launch&&document.contains(launch)){setLaunchLabel();return;}
    launch=el('button',running?'Dừng quét':'Quét deepfake');
    launch.id='ss-df-launch';launch.type='button';
    launch.style.cssText='position:fixed;bottom:16px;right:16px;z-index:2147483645;padding:10px 14px;border:0;border-radius:22px;background:#185d4e;color:#fff;font:600 13px "Segoe UI",sans-serif;box-shadow:0 6px 18px #163f3340;cursor:pointer';
    launch.addEventListener('click',()=>{
      launch.disabled=true;
      chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_BEGIN',useThisTab:true},r=>{
        launch.disabled=false;
        if(!r?.ok)alert(r?.error||'Không quét được cuộc gọi. Hãy chạy CHAY_TAT_CA.cmd rồi thử lại.');
        else setLaunchLabel();
      });
    });
    (document.documentElement||document.body).append(launch);
  }

  function btnStyle(){return 'font:600 12px \"Segoe UI\",sans-serif;padding:4px 8px;border:1px solid #177257;border-radius:8px;background:#185d4e;color:#fff;cursor:pointer';}
  function applyChrome(){
    if(!overlay)return;
    const extra=$('#ss-df-extra'), handle=$('#ss-df-resize'), detail=$('#ss-df-detail');
    if(minimized){
      if(extra)extra.style.display='none';
      if(handle)handle.style.display='none';
      overlay.style.width='auto';overlay.style.height='auto';overlay.style.maxHeight='none';
    }else{
      if(extra)extra.style.display=collapsed?'none':'block';
      if(handle)handle.style.display='block';
      if(maximized){
        overlay.style.width=Math.min(480,window.innerWidth-24)+'px';
        overlay.style.height=Math.min(560,window.innerHeight-24)+'px';
        overlay.style.maxHeight='none';
        if(extra)extra.style.display='block';
      }else{
        overlay.style.maxHeight='70vh';
        if(!overlay.style.width)overlay.style.width='300px';
        overlay.style.height='auto';
      }
    }
    if(detail)detail.textContent=(!collapsed||maximized)&&!minimized?'Ẩn bớt':'Chi tiết';
  }
  function ensureOverlay(){
    if(overlay&&document.contains(overlay))return overlay;
    overlay=el('div');overlay.id='ss-df-overlay';
    overlay.setAttribute('role','dialog');overlay.setAttribute('aria-label','Kết quả deepfake cuộc gọi');
    overlay.style.cssText='position:fixed;top:16px;right:16px;z-index:2147483646;width:300px;max-width:calc(100vw - 24px);max-height:70vh;overflow:hidden;display:flex;flex-direction:column;background:#fff;color:#24463d;border:1px solid #dce5e0;border-radius:14px;box-shadow:0 8px 28px #163f3328;font:14px/1.5 \"Segoe UI\",sans-serif;text-align:left';
    const head=el('div');head.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:6px;padding:8px 10px;background:#f4faf7;border-bottom:1px solid #dce5e0;cursor:move;user-select:none;flex-shrink:0';
    const title=el('strong','ScamShield · Deepfake');title.style.cssText='font-size:13px;color:#163f33;flex:1';
    const tools=el('div');tools.style.cssText='display:flex;gap:4px;align-items:center';
    const detail=el('button','Chi tiết');detail.type='button';detail.id='ss-df-detail';detail.style.cssText=btnStyle();
    const minBtn=el('button','–');minBtn.type='button';minBtn.id='ss-df-min';minBtn.title='Thu nhỏ';minBtn.setAttribute('aria-label','Thu nhỏ');minBtn.style.cssText=btnStyle();
    const maxBtn=el('button','□');maxBtn.type='button';maxBtn.id='ss-df-max';maxBtn.title='Phóng to';maxBtn.setAttribute('aria-label','Phóng to');maxBtn.style.cssText=btnStyle();
    const stop=el('button','Dừng');stop.type='button';stop.id='ss-df-stop';
    stop.style.cssText=btnStyle();
    tools.append(detail,minBtn,maxBtn,stop);
    head.append(title,tools);
    const alert=el('div');alert.id='ss-df-alert';alert.hidden=true;
    alert.style.cssText='display:none;padding:8px 12px;background:#991b1b;color:#fff;font:700 12px/1.4 \"Segoe UI\",sans-serif';
    alert.textContent='CẢNH BÁO: khuôn mặt có dấu hiệu giả mạo liên tục. Đừng chuyển tiền; hãy gọi lại số quen.';
    const body=el('div');body.id='ss-df-body';body.style.cssText='padding:10px 12px;overflow:auto;flex:1';
    const row=el('div');row.id='ss-df-summary';row.style.cssText='display:flex;align-items:center;gap:10px;cursor:pointer';
    const badge=el('div','Đang bắt đầu…');badge.id='ss-df-badge';
    badge.style.cssText='display:inline-block;padding:6px 10px;border-radius:10px;font-weight:700;font-size:13px;background:#f8fafc;color:#475569;border:1px solid #cbd5e1';
    const score=el('div','–');score.id='ss-df-score';score.style.cssText='font-size:22px;font-weight:700;color:#163f33;margin:0';
    row.append(badge,score);
    const extra=el('div');extra.id='ss-df-extra';extra.style.display='none';
    const status=el('p','');status.id='ss-df-status';status.style.cssText='margin:8px 0;font-size:12px;color:#5d736b';
    const reasons=el('ul');reasons.id='ss-df-reasons';reasons.style.cssText='margin:0;padding:0;list-style:none';
    extra.append(status,reasons);
    body.append(row,extra);
    const handle=el('div');handle.id='ss-df-resize';
    handle.style.cssText='position:absolute;right:2px;bottom:2px;width:14px;height:14px;cursor:nwse-resize;background:linear-gradient(135deg,transparent 50%,#177257 50%);border-radius:2px';
    overlay.append(head,alert,body,handle);
    (document.documentElement||document.body).append(overlay);
    stop.addEventListener('click',e=>{e.stopPropagation();stopLive(true);});
    detail.addEventListener('click',e=>{e.stopPropagation();if(minimized)minimized=false;collapsed=!collapsed;if(!collapsed)maximized=false;applyChrome();});
    minBtn.addEventListener('click',e=>{e.stopPropagation();minimized=!minimized;if(minimized){maximized=false;collapsed=true;}applyChrome();});
    maxBtn.addEventListener('click',e=>{e.stopPropagation();maximized=!maximized;minimized=false;if(maximized)collapsed=false;applyChrome();});
    row.addEventListener('click',()=>{if(minimized){minimized=false;collapsed=false;}else collapsed=!collapsed;applyChrome();});
    head.addEventListener('mousedown',e=>{
      if(e.button!==0||e.target.closest('button'))return;
      const r=overlay.getBoundingClientRect();
      drag={dx:e.clientX-r.left,dy:e.clientY-r.top};
      e.preventDefault();
    });
    handle.addEventListener('mousedown',e=>{
      e.preventDefault();e.stopPropagation();
      const r=overlay.getBoundingClientRect();
      drag={resize:true,x:e.clientX,y:e.clientY,w:r.width,h:r.height};
      minimized=false;maximized=false;
    });
    document.addEventListener('mousemove',e=>{
      if(!drag||!overlay)return;
      if(drag.resize){
        overlay.style.width=Math.max(220,drag.w+e.clientX-drag.x)+'px';
        overlay.style.height=Math.max(72,drag.h+e.clientY-drag.y)+'px';
        overlay.style.maxHeight='none';
        return;
      }
      overlay.style.left=Math.max(8,e.clientX-drag.dx)+'px';
      overlay.style.top=Math.max(8,e.clientY-drag.dy)+'px';
      overlay.style.right='auto';
    },true);
    document.addEventListener('mouseup',()=>{drag=null;},true);
    applyChrome();
    return overlay;
  }

  function updateOverlay(payload){
    ensureOverlay();
    const alert=$('#ss-df-alert');
    const status=$('#ss-df-status');
    if(payload.error){
      status.textContent=payload.error;
      status.style.display='block';
      return;
    }
    const r=payload.result||{};
    const t=THEMES[r.verdict]||{label:r.verdict?'Kết quả':'Đang quét…',color:'#475569',background:'#f8fafc',border:'#cbd5e1'};
    const badge=$('#ss-df-badge');
    badge.textContent=t.label;
    Object.assign(badge.style,{color:t.color,background:t.background,border:'1px solid '+t.border,borderLeft:'4px solid '+t.color});
    const sc=r.smoothed_score;
    $('#ss-df-score').textContent=sc==null?'–':Math.round(Math.max(0,Math.min(1,sc))*100)+'%';
    status.textContent='';
    status.style.display='none';
    if(r.alert){alert.style.display='block';alert.hidden=false;overlay.style.boxShadow='0 8px 28px #991b1b55';}
    else {alert.style.display='none';alert.hidden=true;overlay.style.boxShadow='0 8px 28px #163f3328';}
    const list=$('#ss-df-reasons');list.replaceChildren();
    for(const item of (r.reasons||[])){
      const text=typeof item==='string'?item:(item&&item.text)||'';
      if(!text||/CHỈ THAM KHẢO/i.test(text))continue;
      const li=el('li',text);
      li.style.cssText='padding:5px 0;border-bottom:1px solid #eef3f0;font-size:12px;line-height:1.4;color:#24463d';
      if(item&&item.abnormal&&!item.info)li.style.color='#991b1b';
      else if(item&&item.info)li.style.color='#64748b';
      list.append(li);
    }
  }

  async function tick(){
    if(busy||!running)return;
    const video=pickVideo();
    if(!video||!video.videoWidth){
      if(overlay){const s=$('#ss-df-status');if(s){s.textContent='Chưa thấy khuôn mặt';s.style.display='block';}}
      return;
    }
    busy=true;
    try{
      if(!grab)grab=document.createElement('canvas');
      const s=Math.min(1,960/video.videoWidth);
      grab.width=Math.round(video.videoWidth*s);grab.height=Math.round(video.videoHeight*s);
      grab.getContext('2d').drawImage(video,0,0,grab.width,grab.height);
      if(isBlankCanvas(grab)){
        if(overlay){const s=$('#ss-df-status');if(s){s.textContent='Chưa thấy khuôn mặt';s.style.display='block';}}
        return;
      }
      const blob=await new Promise((ok,fail)=>grab.toBlob(b=>b?ok(b):fail(Error('Chưa thấy khuôn mặt')),'image/jpeg',0.85));
      if(!blob||blob.size<800){
        if(overlay){const s=$('#ss-df-status');if(s){s.textContent='Chưa thấy khuôn mặt';s.style.display='block';}}
        return;
      }
      const bytes=await blob.arrayBuffer();
      const response=await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_FRAME',session,base64:bytesToBase64(bytes),mime:'image/jpeg'});
      if(!running)return;
      if(response?.skipped){updateOverlay({result:response.result,error:null});if(overlay){const s=$('#ss-df-status');if(s){s.textContent='Chưa thấy khuôn mặt';s.style.display='block';}}}
      else if(!response?.ok)updateOverlay({error:response?.error||'Lỗi gửi khung hình. Kiểm tra CHAY_TAT_CA.cmd.'});
      else {
        updateOverlay({result:response.result});
        chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_RESULT',result:response.result,source:'video'}).catch(()=>{});
      }
    }catch(e){
      const m=e.message||'Lỗi quét.';
      if(running)updateOverlay({error:/không hợp lệ/i.test(m)?'Chưa thấy khuôn mặt':m});
    }finally{busy=false;}
  }

  async function startCapture(sid){
    stopCapture();
    session=sid;running=true;setLaunchLabel();
    const reset=await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_FRAME_RESET',session});
    if(!reset?.ok)throw Error(reset?.error||'Không khởi tạo được phiên.');
    timer=setInterval(tick,1000);tick();
  }
  function stopCapture(){
    running=false;busy=false;
    if(timer){clearInterval(timer);timer=null;}
    setLaunchLabel();
  }
  function stopLive(notifyWorker){
    stopCapture();
    if(overlay){
      const s=$('#ss-df-status');if(s)s.textContent='Đã dừng.';
      const b=$('#ss-df-stop');if(b)b.disabled=true;
    }
    if(notifyWorker)chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_STOP'}).catch(()=>{});
  }

  chrome.runtime.onMessage.addListener((m,sender,reply)=>{
    if(sender.id!==chrome.runtime.id||!m||typeof m.type!=='string')return;
    if(m.type==='SS_DEEPFAKE_LIVE_START_OVERLAY'){
      try{ensureOverlay();session=m.session;running=true;setLaunchLabel();const s=$('#ss-df-status');if(s){s.textContent='';s.style.display='none';}const b=$('#ss-df-stop');if(b)b.disabled=false;reply({ok:true});}
      catch(e){reply({ok:false,error:e.message});}
      return true;
    }
    if(m.type==='SS_DEEPFAKE_LIVE_START_CAPTURE'){
      (async()=>{await startCapture(m.session);reply({ok:true});})().catch(e=>reply({ok:false,error:e.message}));
      return true;
    }
    if(m.type==='SS_DEEPFAKE_OVERLAY_UPDATE'){
      if(window.top===window)updateOverlay(m);
      reply({ok:true});return;
    }
    if(m.type==='SS_DEEPFAKE_LIVE_STOP'){
      stopLive(false);reply({ok:true});return;
    }
  });

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ensureLaunchButton,{once:true});
  else ensureLaunchButton();
  setInterval(ensureLaunchButton,2000);
})();
