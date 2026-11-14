/* Local-only UI/controller. It deliberately sends no runtime messages or requests. */
(() => {
  if(globalThis.__ssConversationLoaded)return;globalThis.__ssConversationLoaded=true;
  const A=SSConversationAdapter,M=SSConversationModel,E=SSConversationExport;
  const host=document.createElement('div');host.dataset.ssOwned='conversation';document.documentElement.append(host);
  const shadow=host.attachShadow({mode:'closed'}),style=document.createElement('style');
  style.textContent=`:host{all:initial}*{box-sizing:border-box}section{position:fixed;z-index:2147483647;right:18px;top:24px;width:min(410px,calc(100vw - 16px));max-height:calc(100vh - 16px);display:flex;flex-direction:column;background:#fff;color:#183d39;border:1px solid #7aaf9e;border-radius:18px;box-shadow:0 14px 48px #102d3940;font:14px/1.5 system-ui}header{padding:13px 16px;background:#e8f4ee;border-radius:18px 18px 0 0;cursor:move;touch-action:none;font-weight:700}main{padding:14px;overflow:auto;min-height:0}p{margin:7px 0}button{font:inherit;border:1px solid #c7dcd3;border-radius:10px;padding:9px 12px;background:#f1f7f4;color:#204b40;cursor:pointer;margin:3px;transition:background .15s,transform .15s}button:hover{background:#dbefe4;transform:translateY(-1px)}button:focus-visible{outline:3px solid #469477}button:disabled{opacity:.5;cursor:default}.primary{background:#216d57;color:white}.primary:hover{background:#164e3d}.danger{color:#943b3b}pre{font:13px/1.55 system-ui;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:12px;background:#f6f8fa;border-radius:10px;max-height:40vh;overflow:auto}[hidden]{display:none!important}small{color:#526e65}footer{padding:8px 12px;border-top:1px solid #dce9e2}a{color:#17624d}@media(prefers-reduced-motion:reduce){button{transition:none;transform:none!important}}`;
  style.textContent+='section{right:8px;top:8px;width:min(410px,calc(100vw - 32px))}';
  const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
  const panel=el('section'),head=el('header','ScamShield AI · Thu thập hội thoại'),main=el('main'),status=el('p','Chọn riêng khung chat để bắt đầu.'),stats=el('p'),scope=el('small','Chỉ lưu trong bộ nhớ tab · không gửi backend · chưa phân tích rủi ro'),actions=el('div'),preview=el('pre'),footer=el('footer'),downloads=el('div');
  panel.hidden=true;preview.hidden=true;downloads.hidden=true;status.setAttribute('role','status');status.setAttribute('aria-live','polite');preview.setAttribute('aria-label','Bản xem trước hội thoại');head.tabIndex=0;
  const buttons={};for(const [id,label]of [['choose','Chọn khung chat'],['start','Bắt đầu'],['pause','Tạm dừng'],['resume','Tiếp tục thu thập'],['preview','Xem trước'],['freeze','Phân tích · Xuất dữ liệu thử'],['clear','Xóa dữ liệu phiên'],['close','Đóng']]){const b=el('button',label);b.type='button';buttons[id]=b;(id==='freeze'?footer:actions).append(b);}
  buttons.freeze.className='primary';buttons.clear.className='danger';const jsonButton=el('button','Tải JSON'),txtButton=el('button','Tải TXT');downloads.append(jsonButton,txtButton);
  main.append(scope,status,stats,actions,preview,downloads);panel.append(head,main,footer);shadow.append(style,panel);
  const border=el('div');border.dataset.ssOwned='conversation-border';Object.assign(border.style,{position:'fixed',pointerEvents:'none',zIndex:'2147483646',border:'2px solid #23795c',background:'#28996e11',display:'none'});document.documentElement.append(border);
  let adapter=null,store=null,snapshot=null,state='idle',observer=null,abort=null,watch=null,debounce=null,scrollTimer=null,chooseAbort=null,url=null,reference=null,pending=new Set(),busy=false,epoch=0,scrolling=false;
  function draw(target){if(!target){border.style.display='none';return;}const r=target.getBoundingClientRect();Object.assign(border.style,{left:r.left+'px',top:r.top+'px',width:r.width+'px',height:r.height+'px',display:'block'});}
  function refresh(message){if(message)status.textContent=message;const data=store?.snapshot();stats.textContent=data?`${data.messages.length} tin · ${data.participants.length} bên · ${data.diagnostics_summary.unknown_sender_count} tin chưa rõ người gửi`:'';
    buttons.start.disabled=!adapter||!!store;buttons.pause.disabled=state!=='collecting';buttons.resume.disabled=!store||state==='collecting'||state==='changed'||store.full;buttons.freeze.disabled=!store||busy;buttons.preview.disabled=!store;buttons.clear.disabled=!store;panel.dataset.state=state;
  }
  function disconnect(){observer?.disconnect();observer=null;abort?.abort();abort=null;clearInterval(watch);clearTimeout(debounce);clearTimeout(scrollTimer);watch=debounce=scrollTimer=null;scrolling=false;}
  function halt(next,message){disconnect();state=next;draw(null);refresh(message);}
  function valid(){return adapter&&adapter.root.isConnected&&adapter.selected.isConnected&&location.href===url&&adapter.reference()===reference;}
  function guard(){if(!valid()){epoch++;pending.clear();halt('changed','Cuộc trò chuyện hoặc khung đã đổi. Dữ liệu phiên cũ được giữ; hãy chốt/xuất bản xem trước cũ hoặc chọn khung cho phiên mới.');buttons.freeze.disabled=false;return false;}return true;}
  function queueChanges(changes){for(const c of changes){const target=c.target.nodeType===1?c.target:c.target.parentElement;if(target?.closest('[data-ss-owned]'))continue;
    if(target?.closest(A.ITEM))pending.add(target.closest(A.ITEM));
    if(c.type==='attributes'&&target?.matches('[data-sender-group]'))for(const n of target.querySelectorAll(A.ITEM))pending.add(n);
    for(const n of c.addedNodes||[]){if(n.nodeType!==1||n.closest('[data-ss-owned]'))continue;if(n.matches(A.ITEM))pending.add(n);for(const child of n.querySelectorAll(A.ITEM))pending.add(child);}
    if(pending.size>1000){store.warnings.add('mutation_queue_limit');halt('paused','Nhiều cập nhật cùng lúc. Đã tạm dừng; chốt dữ liệu hiện có hoặc tiếp tục.');return;}
  }}
  function flush(scan=false){if(!store||!guard())return;queueChanges(observer?.takeRecords()||[]);
    const visible=adapter.items(),wanted=scan?visible:visible.filter(n=>pending.has(n));pending.clear();
    // Include visible neighbours to retain ordering and overlap between windows.
    if(wanted.length)store.ingest(visible.map(n=>adapter.read(n)).filter(Boolean));
    if(store.full)halt('paused','Đã chạm giới hạn phiên (1000 tin / 2 MiB dữ liệu ước tính / 4000 quan hệ thứ tự). Hãy chốt và tải file.');
    else refresh();
  }
  function attach(){disconnect();state='collecting';abort=new AbortController();observer=new MutationObserver(changes=>{if(!guard())return;queueChanges(changes);if(state!=='collecting')return;clearTimeout(debounce);debounce=setTimeout(()=>flush(),70);});observer.observe(adapter.root,{subtree:true,childList:true,attributes:true,characterData:true});
    const onScroll=()=>{if(!guard())return;scrolling=true;flush(true);if(state!=='collecting')return;refresh('Đang cuộn · chỉ ghi nhận tin đang hiển thị.');clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{flush(true);scrolling=false;if(state==='collecting')refresh('Đã dừng cuộn · lịch sử có thể vẫn chưa đầy đủ.');},700);};
    adapter.scroller.addEventListener('scroll',onScroll,{passive:true,signal:abort.signal});if(adapter.scroller!==window)window.addEventListener('scroll',onScroll,{passive:true,signal:abort.signal});
    window.addEventListener('pagehide',()=>halt('paused','Đã dừng khi rời trang.'),{once:true,signal:abort.signal});watch=setInterval(()=>{if(guard())draw(adapter.root);},300);flush(true);if(state==='collecting')refresh('Đang thu thập. Cuộn để tải các tin bạn muốn kiểm tra.');
  }
  function choose(){epoch++;disconnect();chooseAbort?.abort();chooseAbort=new AbortController();panel.hidden=false;state='choosing';refresh('Bấm vào nền khung hội thoại. Chưa thu thập nội dung. Esc để hủy.');
    const options={capture:true,signal:chooseAbort.signal};
    document.addEventListener('mousemove',e=>{if(!e.composedPath().includes(host))draw(e.target);},options);
    document.addEventListener('keydown',e=>{if(e.key==='Escape'){chooseAbort.abort();draw(null);state=store?'paused':'idle';refresh('Đã hủy chọn vùng.');}},options);
    document.addEventListener('click',e=>{if(e.composedPath().includes(host))return;e.preventDefault();e.stopImmediatePropagation();try{const next=A.resolve(e.target);adapter=next;url=location.href;reference=adapter.reference();store=null;snapshot=null;pending.clear();preview.hidden=downloads.hidden=true;chooseAbort.abort();state='ready';draw(adapter.root);refresh('Đã chọn '+(adapter.title()||'khung chat')+'. Chưa thu thập. Bấm Bắt đầu.');}catch(error){refresh(error.message);}},options);
  }
  function show(data){preview.textContent=E.toText(data);preview.hidden=false;}
  buttons.choose.onclick=()=>{if(store&&!confirm('Chọn khung mới sẽ xóa dữ liệu phiên trong bộ nhớ. Bạn đã tải file cần giữ chưa?'))return;choose();};
  buttons.start.onclick=()=>{if(!valid()){refresh('Khung đã đổi. Hãy chọn lại.');return;}store=new M.Store({description:'Chỉ tin hiển thị trong vùng đã chọn; không đọc metadata ngoài vùng.',conversation_reference:reference,title:adapter.title(),scroll_container:adapter.scroller===window?'document_viewport':adapter.scroller===adapter.root?'message_root':'nearest_scroll_ancestor',document_session_id:crypto.randomUUID()});attach();};
  buttons.pause.onclick=()=>{flush(true);halt('paused','Đã tạm dừng. Dữ liệu chỉ giữ trong bộ nhớ tab.');};
  buttons.resume.onclick=()=>{if(!guard())return;snapshot=null;downloads.hidden=true;attach();};
  buttons.preview.onclick=()=>{if(state==='collecting')flush(true);show(snapshot||store.snapshot());};
  buttons.freeze.onclick=async()=>{
    if(!store||busy)return;busy=true;const stamp=epoch;refresh('Đang hoàn tất hàng đợi…');
    try{if(state==='collecting'){const end=performance.now()+1200;while(adapter.loading()&&performance.now()<end){await new Promise(r=>setTimeout(r,80));if(stamp!==epoch)throw Error('Phiên đã đổi; hãy thử lại.');}if(adapter.loading())throw Error('Khung vẫn đang tải. Hãy chờ tải xong rồi chốt lại.');if(!guard())throw Error('Khung đã đổi. Bấm chốt lại để xuất riêng phần phiên cũ.');flush(true);}
      if(stamp!==epoch)throw Error('Phiên đã đổi. Hãy thử lại.');halt('frozen','Đã chốt bản hội thoại đã quan sát. Chưa phân tích rủi ro.');snapshot=store.snapshot('user_finalized');show(snapshot);downloads.hidden=false;
    }catch(e){refresh(e.message);}finally{busy=false;refresh();}
  };
  function clear(){epoch++;disconnect();chooseAbort?.abort();pending.clear();store=snapshot=adapter=null;state='idle';preview.textContent='';preview.hidden=downloads.hidden=true;draw(null);refresh('Đã xóa dữ liệu phiên khỏi bộ nhớ tab. File đã tải trên máy không bị xóa.');}
  buttons.clear.onclick=clear;buttons.close.onclick=()=>{chooseAbort?.abort();if(state==='collecting')flush(true);halt(store?'paused':'idle','Đã đóng và dừng thu thập.');panel.hidden=true;};
  function download(kind){E.download(snapshot,kind,shadow);}
  jsonButton.onclick=()=>download('json');txtButton.onclick=()=>download('txt');
  function clamp(){const r=panel.getBoundingClientRect();if(panel.style.left)panel.style.left=Math.max(0,Math.min(document.documentElement.clientWidth-r.width,r.left))+'px';panel.style.top=Math.max(0,Math.min(innerHeight-r.height,r.top))+'px';}
  window.addEventListener('resize',clamp);
  head.onpointerdown=e=>{if(e.button!==0)return;const r=panel.getBoundingClientRect(),dx=e.clientX-r.left,dy=e.clientY-r.top;head.setPointerCapture(e.pointerId);head.onpointermove=ev=>{panel.style.right='auto';panel.style.left=Math.max(0,Math.min(document.documentElement.clientWidth-panel.offsetWidth,ev.clientX-dx))+'px';panel.style.top=Math.max(0,Math.min(innerHeight-panel.offsetHeight,ev.clientY-dy))+'px';};head.onpointerup=head.onpointercancel=()=>{head.onpointermove=null;};};
  head.onkeydown=e=>{if(e.key==='Home'){panel.style.left='';panel.style.right='8px';panel.style.top='8px';}};
  document.addEventListener('ss-risk-mode',()=>{chooseAbort?.abort();if(state==='collecting')flush(true);halt(store?'paused':'idle','Đã dừng chế độ thu thập.');panel.hidden=true;});
  chrome.runtime.onMessage.addListener((m,sender,reply)=>{if(sender.id!==chrome.runtime.id||m.type!=='SS_CONVERSATION_CHOOSE')return;document.dispatchEvent(new Event('ss-conversation-mode'));if(store){panel.hidden=false;refresh('Phiên trước được giữ trong tab. Tiếp tục, xuất file hoặc chọn khung mới.');}else choose();reply({ok:true});});
  refresh();
})();
