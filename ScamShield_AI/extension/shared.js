/* Shared safe renderer and request validation. No HTML from analyzed content. */
(() => {
  const labels = {clear:'Chưa ghi nhận dấu hiệu đáng ngờ',need_context:'Cần xác minh thêm',suspicious:'Có dấu hiệu đáng ngờ',high:'Rủi ro cao'};
  const themes = {
    clear:{color:'#166534',background:'#f0fdf4',border:'#86efac',icon:'✓'},
    need_context:{color:'#1e40af',background:'#eff6ff',border:'#93c5fd',icon:'?'},
    suspicious:{color:'#9a3412',background:'#fff7ed',border:'#fdba74',icon:'!'},
    high:{color:'#991b1b',background:'#fef2f2',border:'#fca5a5',icon:'⚠'}
  };
  const neutral={color:'#475569',background:'#f8fafc',border:'#cbd5e1',icon:'…'};
  function themeFor(status){return Object.hasOwn(themes,status)?themes[status]:neutral;}
  function applyTheme(node,status){const t=themeFor(status);node.dataset.risk=Object.hasOwn(themes,status)?status:'unchecked';Object.assign(node.style,{color:t.color,background:t.background,border:'1px solid '+t.border,borderLeft:'4px solid '+t.color});return t;}
  const el = (tag,text,cls) => {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const length = s => Array.from(s).length;
  function validate(p){
    if(!p || typeof p!=='object' || Array.isArray(p))throw Error('Bản gửi phải là object JSON.');
    if(Object.keys(p).some(k=>!['text','messages','context','question','ocr_sources','links','clarification'].includes(k)))throw Error('Bản gửi có trường không được hỗ trợ.');
    if(p.clarification){const c=p.clarification;if(typeof c!=='object'||Array.isArray(c)||!Number.isInteger(c.revision)||c.revision<1||typeof c.answer!=='string'||!c.answer.trim()||length(c.answer)>1000||typeof c.case_id!=='string'||typeof c.situation_id!=='string'||typeof c.question_id!=='string'||!/^[a-f0-9]{64}$/.test(c.content_version))throw Error('Thông tin bổ sung không gắn đúng lần phân tích.');}
    if(('text'in p)===('messages'in p))throw Error('Chọn đúng một dạng text hoặc messages.');
    let messages;
    if('text'in p){if(typeof p.text!=='string')throw Error('text phải là chuỗi.');messages=[{id:'m1',speaker:'unknown',text:p.text}];}
    else {if(!Array.isArray(p.messages)||!p.messages.length||p.messages.length>100)throw Error('Hội thoại phải có 1–100 tin nhắn.');messages=p.messages;}
    const ids=new Set();
    for(const m of messages){if(!m || typeof m!=='object'||Object.keys(m).some(k=>!['id','speaker','text'].includes(k)))throw Error('Tin nhắn chỉ gồm id, speaker, text.');for(const k of ['id','speaker','text'])if(typeof m[k]!=='string'||!m[k].trim())throw Error('Mỗi tin cần id, speaker và text không rỗng.');if(length(m.id)>100||length(m.speaker)>100||ids.has(m.id))throw Error('ID trùng hoặc ID/speaker quá dài.');ids.add(m.id);}
    if(messages.reduce((n,m)=>n+length(m.text),0)>10000)throw Error('Nội dung vượt 10.000 ký tự.');
    if(p.ocr_sources){if(!Array.isArray(p.ocr_sources)||p.ocr_sources.length>4)throw Error('Tối đa 4 nguồn OCR.');const refs=new Set();for(const r of p.ocr_sources){if(!r||Object.keys(r).some(k=>!['message_id','source_id'].includes(k))||typeof r.message_id!=='string'||typeof r.source_id!=='string'||r.source_id.length>100||!ids.has(r.message_id)||refs.has(r.message_id))throw Error('Nguồn OCR không hợp lệ.');refs.add(r.message_id);}}
    if(p.links){if(!Array.isArray(p.links)||p.links.length>20)throw Error('Tối đa 20 liên kết mỗi mục.');const seen=new Set();for(const l of p.links){if(!l||typeof l.id!=='string'||seen.has(l.id)||!ids.has(l.message_id)||typeof l.url!=='string'||!l.url||l.url.length>2048)throw Error('Liên kết không hợp lệ.');seen.add(l.id);}}
    for(const [k,max]of [['context',2000],['question',1000]])if(k in p && (typeof p[k]!=='string'||length(p[k])>max))throw Error(`${k} phải là chuỗi, tối đa ${max} ký tự.`);
    if(new TextEncoder().encode(JSON.stringify(p)).length>65536)throw Error('Bản gửi vượt giới hạn 65.536 byte.');
    return messages;
  }
  function render(...args){return globalThis.ScamShieldResultView(...args);}
  globalThis.ScamShieldUI={el,validate,render,labels,themeFor,applyTheme};
})();
