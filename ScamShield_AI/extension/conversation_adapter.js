/* Explicit DOM contract; fixture support only. Never infer authors from left/right. */
(() => {
  if(globalThis.SSConversationAdapter)return;
  const ROOT='[data-ss-conversation][data-conversation-id]',ITEM='[data-message-id],[data-chat-message]',OWNED='[data-ss-owned]',DENY='input,textarea,select,button,[contenteditable]:not([contenteditable="false"]),[role="textbox"],script,style,template,'+OWNED;
  function visible(el,root){
    if(!el?.isConnected||el.closest(DENY)||!root.contains(el))return false;
    let r=el.getBoundingClientRect(),left=Math.max(0,r.left),top=Math.max(0,r.top),right=Math.min(innerWidth,r.right),bottom=Math.min(innerHeight,r.bottom);
    for(let a=el;a;a=a.parentElement){const s=getComputedStyle(a);if(a.hidden||a.inert||a.getAttribute('aria-hidden')==='true'||s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0)return false;
      if(a!==el&&/(auto|scroll|hidden|clip)/.test(s.overflow+s.overflowY+s.overflowX)){r=a.getBoundingClientRect();left=Math.max(left,r.left);right=Math.min(right,r.right);top=Math.max(top,r.top);bottom=Math.min(bottom,r.bottom);}}
    return right>left&&bottom>top;
  }
  function text(el,exclude=''){
    const walk=node=>{
      if(node.nodeType===3)return node.textContent;
      if(node.nodeType!==1||node.matches(DENY+(exclude?','+exclude:'')))return '';
      const s=getComputedStyle(node);if(node.hidden||node.getAttribute('aria-hidden')==='true'||s.display==='none'||s.visibility==='hidden')return '';
      if(node.tagName==='BR')return '\n';const content=[...node.childNodes].map(walk).join('');return /^(P|DIV|LI)$/.test(node.tagName)?content+'\n':content;
    };
    return walk(el).replace(/\n{3,}/g,'\n\n').trim();
  }
  function resolve(selected){
    if(selected.closest(DENY)||['BODY','HTML'].includes(selected.tagName))throw Error('Chọn riêng khung hội thoại, không chọn toàn trang hoặc ô soạn tin.');
    const roots=selected.matches(ROOT)?[selected]:[...selected.querySelectorAll(ROOT)];
    if(roots.length!==1)throw Error('Chưa nhận diện đúng một khung chat được hỗ trợ. Hãy chọn khung chat của trang thử nghiệm.');
    const root=roots[0];let scroller=window;
    for(let a=root;a&&a!==document.body;a=a.parentElement){if(/auto|scroll/.test(getComputedStyle(a).overflowY)&&a.scrollHeight>a.clientHeight){scroller=a;break;}}
    return {root,selected,scroller,reference:()=>root.getAttribute('data-conversation-id'),title:()=>root.getAttribute('data-conversation-title')||null,
      items:()=>[...root.querySelectorAll(ITEM)].filter(el=>!el.parentElement?.closest(ITEM)&&visible(el,root)),
      loading:()=>root.getAttribute('aria-busy')==='true'||!!root.querySelector('[data-chat-loading="true"]'),
      read(el){
        if(!visible(el,root))return null;
        const group=el.closest('[data-sender-group]'),author=el.hasAttribute('data-sender-id')||el.hasAttribute('data-sender-name')?el:group;
        const system=el.getAttribute('data-kind')==='system',self=author?.getAttribute('data-sender-role')==='self';
        const q=[...el.querySelectorAll('[data-chat-quote],[data-link-preview],[data-chat-forward]')].filter(x=>!x.closest(DENY));
        const bodies=[...el.querySelectorAll('[data-chat-text]')].filter(x=>!x.parentElement.closest('[data-chat-text]'));
        const attachments=[...el.querySelectorAll('img,video,audio,[data-attachment]')].filter(x=>!x.closest(DENY)&&visible(x,root)).map(x=>({type:x.tagName==='IMG'?'image':x.tagName==='VIDEO'?'video':x.tagName==='AUDIO'?'audio':x.getAttribute('data-attachment')||'file',label:x.getAttribute('alt')||x.getAttribute('data-attachment-label')||null,status:'content_not_extracted'}));
        const links=[...el.querySelectorAll('a[href]')].filter(x=>!x.closest(DENY+', [data-chat-quote],[data-link-preview],[data-chat-forward]')&&visible(x,root)).flatMap(x=>{try{const u=new URL(x.getAttribute('href'),location.href);return /^https?:$/.test(u.protocol)?[{text:text(x),href:u.href}]:[];}catch{return [];}});
        const time=el.querySelector('time'),label=time?.textContent.trim()||el.getAttribute('data-time')||null,dt=time?.getAttribute('datetime');
        const normalized=dt&&/^\d{4}-\d\d-\d\dT.*(?:Z|[+-]\d\d:\d\d)$/.test(dt)&&Number.isFinite(Date.parse(dt))?dt:null;
        return {node:el,id:el.getAttribute('data-message-id')||null,text:bodies.map(b=>text(b,'[data-chat-quote],[data-link-preview],[data-chat-forward]')).filter(Boolean).join('\n'),sender:{platform_id:author?.getAttribute('data-sender-id')||null,name:author?.getAttribute('data-sender-name')||null,group_id:group?.getAttribute('data-sender-group')||null,self,system,role:system?'system':author?'other':'unknown',basis:author?[author===group?'explicit_dom_author_group':'message_author_attributes']:system?['system_message_marker']:[]},
          system,forwarded:el.getAttribute('data-forwarded')==='true',deleted:el.getAttribute('data-deleted')==='true',edited:el.getAttribute('data-edited')==='true',attachments,links,
          quoted_content:q.map(x=>({kind:x.hasAttribute('data-link-preview')?'link_preview':x.hasAttribute('data-chat-forward')?'forwarded_content':'reply_quote',text:text(x)})),reply_id:el.getAttribute('data-reply-to')||null,time:label,normalized_time:normalized,
          warnings:[...(!bodies.length?['body_not_identified']:[]),...(!label?['time_unknown']:[])]};
      }};
  }
  globalThis.SSConversationAdapter={resolve,visible,ITEM,DENY};
})();
