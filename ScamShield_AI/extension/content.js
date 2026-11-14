(() => {
  if(globalThis.__scamShieldLoaded)return;
  globalThis.__scamShieldLoaded=true;
  globalThis.__scamShieldBuild='0.9.0';
  const UI=ScamShieldUI,uuid=()=>crypto.randomUUID();
  const state={mode:'off',root:null,session:null,url:location.href,document:uuid(),queue:[],records:new Map(),pending:false,deferred:0,epoch:0,config:null};
  let observer=null,intersections=null,timer=null,debounce=null,hover=null,tabId=null,documentId=null,uiEvents=null;
  const host=document.createElement('div');host.dataset.ssOwned='panel';document.documentElement.append(host);
  const shadow=host.attachShadow({mode:'closed'});
  const panel=UI.el('section');panel.hidden=true;panel.setAttribute('aria-label','Điều khiển ScamShield');shadow.append(panel);
  const title=UI.el('h3','ScamShield AI'),info=UI.el('p',undefined,'ss-info'),notice=UI.el('p',undefined,'ss-notice'),stats=UI.el('small',undefined,'ss-stats');
  const buttons={};for(const [id,text]of [['start','Bật quét vùng này'],['pause','Tạm dừng'],['resume','Tiếp tục'],['choose','Đổi vùng'],['stop','Dừng quét']]){buttons[id]=UI.el('button',text);buttons[id].type='button';}
  buttons.start.className=buttons.resume.className='ss-primary';buttons.stop.className='ss-danger';
  const actions=UI.el('div',undefined,'ss-actions');actions.append(...Object.values(buttons));panel.append(title,info,notice,actions,stats);
  const view=ScamShieldPanel(UI,shadow,panel,state);view.controls.append(actions,notice);info.hidden=stats.hidden=true;
  const retry=UI.el('button','Thử lại');retry.hidden=true;view.controls.append(retry);
  const captureButton=UI.el('button','Ảnh trong vùng · xem trước'),readImageButton=UI.el('button','Đọc chữ trong ảnh này'),analyzeImageButton=UI.el('button','Phân tích bài và chữ trong ảnh');
  const imageHint=UI.el('p','Quét tự động chỉ kiểm tra văn bản và liên kết. Ảnh chỉ được đọc khi bạn bấm Đọc chữ trong ảnh này; chỉ đánh giá rủi ro từ ảnh khi bấm Phân tích bài và chữ trong ảnh.','ss-notice');
  const imagePreview=UI.el('img'),ocrPreview=UI.el('pre'),ocrStatus=UI.el('p'),imageResult=UI.el('div');
  captureButton.className='ss-capture';readImageButton.className=analyzeImageButton.className='ss-primary';ocrStatus.className='ss-ocr-status';
  imagePreview.alt='Ảnh chụp vùng sẽ được đọc chữ';imagePreview.style.cssText='max-width:100%;max-height:220px';ocrPreview.style.cssText='white-space:pre-wrap;max-height:180px;overflow:auto';
  imagePreview.hidden=readImageButton.hidden=analyzeImageButton.hidden=true;
  imageHint.textContent='Xem trước ảnh → Đọc chữ → Phân tích. Chỉ gửi ảnh khi bạn bấm Đọc chữ.';
  const imageTools=UI.el('div');imageTools.hidden=true;imageTools.append(imageHint,imagePreview,readImageButton,ocrStatus,ocrPreview,analyzeImageButton,imageResult);view.controls.append(captureButton);view.images.append(imageTools);captureButton.hidden=true;
  let imageSnapshot=null;
  function clearImage(){imageSnapshot=null;imagePreview.removeAttribute('src');imagePreview.hidden=readImageButton.hidden=analyzeImageButton.hidden=true;readImageButton.disabled=analyzeImageButton.disabled=false;ocrPreview.textContent='';ocrStatus.textContent='';imageResult.replaceChildren();}
  const border=UI.el('div');border.dataset.ssOwned='border';border.style.cssText='position:fixed;pointer-events:none;z-index:2147483646;border:3px solid #2b9970;border-radius:5px;display:none;box-sizing:border-box';document.documentElement.append(border);
  const owned=n=>n instanceof Element&&(n===host||n===border||!!n.closest('[data-ss-owned]'));
  const forbidden=e=>!!e.closest('input,textarea,select,option,button,script,style,noscript,template,iframe,canvas,video,audio,[contenteditable]:not([contenteditable="false"]),[role="textbox"],[data-ss-owned]');
  function visible(e,viewport=true){
    if(!e?.isConnected||forbidden(e))return false;
    let rect=e.getBoundingClientRect(),left=Math.max(0,rect.left),top=Math.max(0,rect.top),right=Math.min(innerWidth,rect.right),bottom=Math.min(innerHeight,rect.bottom);
    if(!rect.width||!rect.height)return false;
    for(let n=e;n;n=n.parentElement){const s=getComputedStyle(n);if(n.hidden||n.inert||s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse'||Number(s.opacity)===0||s.contentVisibility==='hidden'||n.getAttribute('aria-hidden')==='true')return false;
      if(viewport&&n!==e&&/(auto|scroll|hidden|clip)/.test(s.overflow+s.overflowX+s.overflowY)){const r=n.getBoundingClientRect();left=Math.max(left,r.left);right=Math.min(right,r.right);top=Math.max(top,r.top);bottom=Math.min(bottom,r.bottom);}}
    return !viewport||(right>left&&bottom>top);
  }
  function textOf(item){
    const walker=document.createTreeWalker(item,NodeFilter.SHOW_TEXT),parts=[];let n;
    while(n=walker.nextNode()){
      if(!n.textContent.trim()||!visible(n.parentElement))continue;
      const range=document.createRange();range.selectNodeContents(n);const rects=[...range.getClientRects()];
      if(rects.some(r=>r.bottom>0&&r.right>0&&r.top<innerHeight&&r.left<innerWidth))parts.push(n.textContent);
    }
    return parts.join('\n').trim();
  }
  function inScope(item){return state.root?.isConnected&&state.root.contains(item)&&item.isConnected&&visible(item)&&location.href===state.url;}
  function linksOf(item,text,messageId='m1'){
    const anchors=[...(item.matches('a[href]')?[item]:[]),...item.querySelectorAll('a[href]')],links=[];
    for(const a of anchors){if(links.length>=20)break;if(!state.root.contains(a)||!visible(a)||forbidden(a)||!/^https?:/i.test(a.href)||a.href.length>2048)continue;
      const label=textOf(a);if(!label||label.length>1000||!text.includes(label))continue;
      const index=text.indexOf(label),unique=index===text.lastIndexOf(label);
      links.push({id:'link-'+links.length,message_id:messageId,url:a.href,display_text:label,start:unique?Array.from(text.slice(0,index)).length:null,end:unique?Array.from(text.slice(0,index+label.length)).length:null,origin:'dom_href'});
    }return links;
  }
  function snapshotOf(item){const text=textOf(item),links=linksOf(item,text),payload={text,...(links.length?{links}:{})};return{text,payload,fingerprint:JSON.stringify(payload)};}
  function units(){const matches=[...state.root.querySelectorAll('[data-ss-item],article,[role="article"],li')].filter(e=>!forbidden(e));return matches.length?matches.filter(e=>!matches.some(other=>other!==e&&e.contains(other))):[state.root];}
  function draw(e){if(!e?.isConnected){border.style.display='none';return;}const r=e.getBoundingClientRect();Object.assign(border.style,{display:'block',left:r.left+'px',top:r.top+'px',width:r.width+'px',height:r.height+'px'});}
  function update(message){
    const names={off:'Đã dừng',choosing:'Đang chọn vùng',ready:'Đã chọn vùng — chưa gửi nội dung',scanning:'Đang quét',paused:'Đã tạm dừng',reselect:'Cần chọn lại vùng'};
    info.textContent=message||names[state.mode];stats.textContent=`Hàng chờ ${state.queue.length}/20 · Mục bị hoãn: ${state.deferred}`;
    buttons.start.hidden=state.mode!=='ready';buttons.start.disabled=!state.config;
    buttons.pause.hidden=state.mode!=='scanning';buttons.resume.hidden=state.mode!=='paused';
    const images=state.root?[...state.root.querySelectorAll('img'),...(state.root.matches('img')?[state.root]:[])].filter(e=>visible(e)):[];captureButton.hidden=!images.length;captureButton.textContent=`Ảnh trong vùng (${images.length})`;
    retry.hidden=!!state.config&&!([...state.records.values()].some(r=>r.status==='error'));notice.hidden=!!state.config&&!['ready','choosing'].includes(state.mode);view.refresh();
    panel.dataset.mode=state.mode;
  }
  function detach(){observer?.disconnect();intersections?.disconnect();clearInterval(timer);clearTimeout(debounce);observer=intersections=timer=null;}
  document.addEventListener('ss-conversation-mode',()=>{cancel('off');panel.hidden=true;});
  async function cancel(mode){
    clearImage();imageTools.hidden=true;
    if(mode==='off'){uiEvents?.abort();uiEvents=null;}
    const old=state.session;state.epoch++;state.mode=mode;state.queue=[];detach();state.pending=false;
    if(mode==='paused'||mode==='reselect')for(const r of state.records.values()){if(r.status!=='done'&&r.status!=='error'&&r.card)view.pending(r,'Đã tạm dừng · Chưa kiểm tra xong');if(r.card&&!r.card.querySelector('.ss-historical'))r.card.prepend(UI.el('small','Kết quả trước khi dừng','ss-historical'));if(r.badge)r.badge.title='Kết quả trước khi dừng quét';}
    if(old)chrome.runtime.sendMessage({type:'SS_STOP',session:old}).catch(()=>{});
    state.session=null;update();
  }
  function schedule(){if(state.mode!=='scanning')return;clearTimeout(debounce);debounce=setTimeout(scan,120);}
  function show(item,record,label,result){
    if(!item.isConnected)return;
    record.badge?.remove();const badge=UI.el('button',result?view.labels[result.risk_status]:label);
    badge.dataset.ssOwned='badge';badge.type='button';badge.style.cssText='display:block;margin:6px 0;padding:7px 11px;border:1px solid #b9cfc2;border-radius:8px;background:#f6faf8;color:#275643;font:600 12px/1.5 Segoe UI,sans-serif;cursor:pointer';
    if(result)UI.applyTheme(badge,result.risk_status);
    badge.onclick=()=>{if(!view.mini.hidden)view.mini.click();record.card?.scrollIntoView({block:'nearest',behavior:'smooth'});record.card?.querySelector('summary')?.focus();};
    if(result){
      record.connectionError=false;
      const version=record.version,epoch=state.epoch,fingerprint=record.fingerprint,resultId=uuid();record.resultId=resultId;
      const current=()=>state.mode==='scanning'&&epoch===state.epoch&&inScope(item)&&record.version===version&&record.resultId===resultId&&snapshotOf(item).fingerprint===fingerprint;
      view.result(record,result,record.payload||{text:record.text},{current,onSupplement:async payload=>{
        if(!current())throw Error('Nội dung hoặc phiên quét đã đổi. Hãy quét lại mục này.');
        if(state.queue.length>=20)throw Error('Hàng chờ đang đầy. Hãy thử lại sau.');
        UI.validate(payload);record.payload=payload;record.version++;record.status='queued';
        state.queue.unshift({item,record,version:record.version,text:record.text,payload,fingerprint,eligibleAt:performance.now()});
        show(item,record,'Đang chờ phân tích thông tin bổ sung…');update();pump();
      }});
    }else view.pending(record,label);
    item.append(badge);record.badge=badge;
  }

  function scan(){
    if(state.mode!=='scanning')return;
    if(!state.root?.isConnected||location.href!==state.url){cancel('reselect');draw(null);return;}
    draw(state.root);state.deferred=0;
    for(const item of units()){
      if(!inScope(item))continue;
      intersections?.observe(item);
      const {text,payload,fingerprint}=snapshotOf(item);if(!text)continue;
      let r=state.records.get(item);
      if(!r){r={id:uuid(),version:0,text:'',status:'new',badge:null};state.records.set(item,r);}
      if(r.fingerprint!==fingerprint){r.text=text;r.payload=payload;r.fingerprint=fingerprint;r.version++;r.status='new';r.badge?.remove();}
      if(r.status!=='new')continue;
      try{UI.validate(payload);}catch(e){r.status='error';show(item,r,e.message);continue;}
      if(state.queue.length>=20){state.deferred++;continue;}
      r.status='queued';state.queue.push({item,record:r,version:r.version,text,payload,fingerprint,eligibleAt:performance.now()});show(item,r,'Đang chờ kiểm tra…');
    }
    // Release detached elements; no DOM/text retention after their removal.
    for(const [item,r]of state.records)if(!state.root.contains(item)){r.badge?.remove();r.card?.remove();state.records.delete(item);}
    update();pump();
  }
  async function pump(){
    if(state.pending||state.mode!=='scanning')return;
    const next=state.queue.shift();if(!next){update();return;}
    const {item,record:r,text,version,payload,fingerprint}=next;
    if(!inScope(item)||r.version!==version||snapshotOf(item).fingerprint!==fingerprint){if(r.version===version)r.status='new';schedule();pump();return;}
    state.pending=true;const epoch=state.epoch,session=state.session;
    show(item,r,'Đang kiểm tra…');
    try{
      const response=await chrome.runtime.sendMessage({type:'SS_ANALYZE',session,itemId:r.id,version,payload});
      if(epoch!==state.epoch||state.mode!=='scanning')return;
      if(!inScope(item)||r.version!==version||snapshotOf(item).fingerprint!==fingerprint){if(r.version===version)r.status='new';return;}
      if(!response?.ok){r.status='error';r.connectionError=['Failed to fetch','NETWORK_ERROR','NETWORK','TIMEOUT','FETCH_ERROR','BACKEND_UNAVAILABLE','HTTP_503','HTTP_429'].includes(response?.error)||!response?.error;show(item,r,r.connectionError?'Chưa kết nối được dịch vụ phân tích':'Chưa kiểm tra được nội dung này');if(response?.error==='SESSION_MISSING'){cancel('reselect');}return;}
      if(response.session!==session||response.tabId!==tabId||response.documentId!==documentId||response.itemId!==r.id||response.version!==version)return;
      r.status='done';show(item,r,UI.labels[response.result.risk_status]||'Chưa kiểm tra được',response.result);
    }catch(e){if(epoch===state.epoch&&state.mode==='scanning'){r.status='error';r.connectionError=true;show(item,r,'Chưa kết nối được dịch vụ phân tích');}}
    finally{if(epoch===state.epoch){state.pending=false;update();schedule();pump();}}
  }
  async function start(resume=false){
    if(!state.root?.isConnected||location.href!==state.url){cancel('reselect');draw(null);return;}
    if(!state.config||(!resume&&state.mode!=='ready')||(resume&&state.mode!=='paused'))return;
    state.session=uuid();state.url=location.href;const epoch=++state.epoch;
    try{const response=await chrome.runtime.sendMessage({type:'SS_OPEN',session:state.session});if(epoch!==state.epoch)return;if(!response?.ok)throw Error('Không mở được phiên');tabId=response.tabId;documentId=response.documentId;}
    catch(e){state.mode=resume?'paused':'ready';state.config=null;notice.textContent='Chưa kết nối được dịch vụ phân tích';update();return;}
    state.mode='scanning';state.pending=false;
    for(const r of state.records.values())if(r.status==='queued'||r.status==='pending')r.status='new';
    observer=new MutationObserver(changes=>{if(changes.some(c=>!owned(c.target.nodeType===3?c.target.parentElement:c.target)&&!(c.type==='childList'&&[...c.addedNodes,...c.removedNodes].every(n=>n.nodeType===1&&owned(n)))))schedule();});
    observer.observe(state.root,{childList:true,subtree:true,characterData:true,attributes:true});
    intersections=new IntersectionObserver(schedule);intersections.observe(state.root);
    timer=setInterval(scan,500);update();scan();
  }
  async function choose(){
    bindEvents();
    await cancel('choosing');state.records.forEach(r=>r.badge?.remove());state.records.clear();view.reset();state.root=null;hover=null;state.config=null;notice.textContent='';update();
    await loadConfig();
  }
  async function loadConfig(){try{const r=await chrome.runtime.sendMessage({type:'SS_CONFIG'});if(r?.ok&&r.protocol===2){state.config=r.config;notice.textContent=state.mode==='ready'?'Chỉ gửi chữ và liên kết trong vùng sau khi bạn bật quét. '+(r.config.processing_notice||''):'';}else{state.config=null;notice.textContent='Chưa kết nối được dịch vụ phân tích';}}catch{state.config=null;notice.textContent='Chưa kết nối được dịch vụ phân tích';}update();}
  retry.onclick=async()=>{retry.disabled=true;try{await loadConfig();if(!state.config)return;for(const r of state.records.values())if(r.status==='error'){r.status='new';r.connectionError=false;}if(state.mode==='scanning')scan();else if(state.mode==='paused')start(true);}finally{retry.disabled=false;}};

  function bindEvents(){if(uiEvents)return;uiEvents=new AbortController();
  document.addEventListener('mousemove',e=>{if(state.mode!=='choosing'||owned(e.target))return;hover=e.target;draw(hover);},{capture:true,signal:uiEvents.signal});
  document.addEventListener('click',e=>{
    if(state.mode!=='choosing'||owned(e.target))return;e.preventDefault();e.stopImmediatePropagation();
    const selected=e.target;
    if(forbidden(selected)||['HTML','BODY'].includes(selected.tagName)||selected.querySelectorAll('*').length>500){update('Khối quá rộng hoặc là vùng nhập. Hãy chọn vùng nhỏ hơn.');return;}
    state.root=selected;state.url=location.href;state.mode='ready';notice.textContent=state.config?'Chỉ gửi chữ và liên kết khi bạn bật quét. '+(state.config.processing_notice||''):'Chưa kết nối được dịch vụ phân tích';draw(selected);update(`Đã chọn ${selected.tagName.toLowerCase()}${selected.id?' #'+selected.id:''}. Chưa gửi nội dung.`);
  },{capture:true,signal:uiEvents.signal});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.mode==='choosing'){cancel('off');draw(null);}},{capture:true,signal:uiEvents.signal});
  addEventListener('scroll',()=>{if(state.mode==='choosing')draw(hover);else if(state.root){draw(state.root);schedule();}},{capture:true,signal:uiEvents.signal});
  addEventListener('resize',schedule,{signal:uiEvents.signal});
  addEventListener('pagehide',()=>cancel('off'),{signal:uiEvents.signal});
  }
  buttons.start.onclick=()=>start();buttons.pause.onclick=()=>{for(const r of state.records.values())if(r.status==='queued')r.status='new';cancel('paused');};buttons.resume.onclick=()=>start(true);buttons.choose.onclick=choose;buttons.stop.onclick=view.close.onclick=()=>{cancel('off');state.records.forEach(r=>r.badge?.remove());state.records.clear();view.reset();state.root=null;draw(null);};
  const imageKey=root=>[...(root.matches('img')?[root]:[]),...root.querySelectorAll('img')].map(e=>[e.currentSrc,e.src,e.naturalWidth,e.naturalHeight].join('|')).join('\n');
  function imageCurrent(snapshot){if(!(snapshot&&snapshot===imageSnapshot&&state.root===snapshot.root&&state.session===snapshot.session&&state.epoch===snapshot.epoch&&location.href===snapshot.url&&inScope(snapshot.root)&&textOf(snapshot.root)===snapshot.dom&&JSON.stringify(linksOf(snapshot.root,snapshot.dom,'dom-1'))===JSON.stringify(snapshot.links)&&imageKey(snapshot.root)===snapshot.images&&innerWidth===snapshot.viewport.width&&innerHeight===snapshot.viewport.height))return false;const r=snapshot.root.getBoundingClientRect();return Math.abs(Math.max(0,r.left)-snapshot.rect.x)<1&&Math.abs(Math.max(0,r.top)-snapshot.rect.y)<1&&Math.abs(Math.min(innerWidth,r.right)-snapshot.rect.x-snapshot.rect.width)<1&&Math.abs(Math.min(innerHeight,r.bottom)-snapshot.rect.y-snapshot.rect.height)<1;}
  captureButton.onclick=async()=>{
    if(!state.root||!state.config||!inScope(state.root))return;
    if(!imageTools.hidden){clearImage();imageTools.hidden=true;return;}
    clearImage();imageTools.hidden=false;
    try{
      if(!state.session){state.session=uuid();const opened=await chrome.runtime.sendMessage({type:'SS_OPEN',session:state.session});if(!opened?.ok)throw Error('Không mở được phiên OCR.');tabId=opened.tabId;documentId=opened.documentId;}
      const root=state.root,r=root.getBoundingClientRect(),rect={x:Math.max(0,r.left),y:Math.max(0,r.top),width:Math.min(innerWidth,r.right)-Math.max(0,r.left),height:Math.min(innerHeight,r.bottom)-Math.max(0,r.top)};
      const snapshot={root,session:state.session,epoch:state.epoch,url:location.href,dom:textOf(root),rect,viewport:{width:innerWidth,height:innerHeight},images:imageKey(root)};imageSnapshot=snapshot;
      snapshot.links=linksOf(root,snapshot.dom,'dom-1');
      const redactions=[...root.querySelectorAll('input,textarea,select,[contenteditable]:not([contenteditable="false"]),[role="textbox"]')].map(e=>{const q=e.getBoundingClientRect();return{x:q.left,y:q.top,width:q.width,height:q.height};});
      host.style.visibility='hidden';border.style.visibility='hidden';
      let response;
      try{await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));response=await chrome.runtime.sendMessage({type:'SS_CAPTURE',session:snapshot.session,rect,viewport:{width:innerWidth,height:innerHeight},redactions});}
      finally{host.style.visibility='';border.style.visibility='';}
      if(!imageCurrent(snapshot))return;
      if(!response?.ok)throw Error(response?.error||'Không chụp được vùng.');
      snapshot.image=response.image;imagePreview.src=response.image;imagePreview.hidden=readImageButton.hidden=false;
      ocrStatus.textContent='Chưa gửi ảnh. Xem kỹ ảnh chụp: nếu có phần ngoài ý muốn, hãy chọn vùng nhỏ hơn. Chỉ khi bấm Đọc chữ ảnh này mới gửi tới backend local. Chỉ phần đang hiển thị được chụp.';
    }catch(e){ocrStatus.textContent=e.message;}
  };
  readImageButton.onclick=async()=>{
    const snapshot=imageSnapshot;if(!imageCurrent(snapshot)){clearImage();ocrStatus.textContent='Vùng đã thay đổi. Hãy chụp lại.';return;}
    readImageButton.disabled=true;ocrStatus.textContent='Đang đọc chữ tại backend local…';
    try{const response=await chrome.runtime.sendMessage({type:'SS_IMAGE_OCR',session:snapshot.session,image:snapshot.image});if(!imageCurrent(snapshot))return;if(!response?.ok)throw Error(response?.error||'OCR_ERROR');snapshot.ocr=response.ocr;if(snapshot.ocr.status==='no_text'){ocrStatus.textContent='Chưa đọc được chữ; không thể suy ra ảnh an toàn.';return;}ocrPreview.textContent=snapshot.ocr.text;ocrStatus.textContent='Đối chiếu chữ với ảnh. Khi bấm phân tích, văn bản OCR và phần chữ của vùng sẽ được gửi theo chế độ backend hiện tại.';analyzeImageButton.hidden=false;}catch(e){ocrStatus.textContent=e.message;}finally{readImageButton.disabled=false;}
  };
  async function analyzeImagePayload(snapshot,payload){
    const requestId=uuid();snapshot.analysisId=requestId;
    const current=()=>imageCurrent(snapshot)&&snapshot.analysisId===requestId;
    try{UI.validate(payload);analyzeImageButton.disabled=true;ocrStatus.textContent='Đang phân tích văn bản bài và OCR…';const response=await chrome.runtime.sendMessage({type:'SS_ANALYZE',session:snapshot.session,payload});if(!current())return;if(!response?.ok)throw Error(response?.error||'Chưa kiểm tra được');imageResult.replaceChildren();const record={status:'done'};view.result(record,response.result,payload,{current,onSupplement:async updated=>{if(!current())throw Error('Ảnh hoặc nội dung đã thay đổi. Hãy chụp lại.');await analyzeImagePayload(snapshot,updated);}});if(record.card)imageResult.append(record.card);else imageResult.textContent='Chưa thấy dấu hiệu · Trong nội dung đã kiểm tra';ocrStatus.textContent='Đã phân tích bản vừa xem. Quote OCR cần đối chiếu ảnh gốc.';}catch(e){if(current())ocrStatus.textContent=e.message;}finally{if(current())analyzeImageButton.disabled=false;}
  }
  analyzeImageButton.onclick=async()=>{
    const snapshot=imageSnapshot;if(!imageCurrent(snapshot)||!snapshot.ocr?.source_id){clearImage();ocrStatus.textContent='Vùng đã thay đổi. Hãy chụp lại.';return;}
    const mid='ocr-'+snapshot.ocr.source_id;
    const payload={messages:[...(snapshot.dom?[{id:'dom-1',speaker:'unknown',text:snapshot.dom}]:[]),{id:mid,speaker:'unknown',text:snapshot.ocr.text}],ocr_sources:[{message_id:mid,source_id:snapshot.ocr.source_id}],...(snapshot.links.length?{links:snapshot.links}:{})};
    await analyzeImagePayload(snapshot,payload);
  };
  chrome.runtime.onMessage.addListener((m,sender,reply)=>{if(sender.id!==chrome.runtime.id)return;if(m.type==='SS_CHOOSE'){document.dispatchEvent(new Event('ss-risk-mode'));choose();reply({ok:true});}});
})();
