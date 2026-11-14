/* Local demo. Never render answers, model internals or untrusted HTML. */
let generation=0;
const el=id=>document.getElementById(id),labels={clear:'Chưa ghi nhận dấu hiệu đáng ngờ',need_context:'Cần xác minh thêm',suspicious:'Có dấu hiệu đáng ngờ',high:'Rủi ro cao'};
el('form').addEventListener('submit',async event=>{
 event.preventDefault();const run=++generation,text=el('text').value;
 if(!text.trim())return;
 el('send').disabled=true;el('status').textContent='Đang phân tích…';el('result').hidden=true;
 try{
  const response=await fetch('/api/analyze-local',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:[{id:'m1',speaker_id:'user',text}]})});
  const data=await response.json();if(run!==generation)return;
  if(!data.assessment)throw Error('invalid response');
  const a=data.assessment,urgent=a.safety_urgency==='urgent';
  // Safety information remains visible even when the broader parser failed.
  el('result').hidden=false;el('result').dataset.risk=a.risk_status||'unchecked';
  el('risk').textContent=labels[a.risk_status]||'Chưa kiểm tra được';
  el('urgency').hidden=!urgent;el('urgency').textContent=urgent?'Ưu tiên an toàn: nội dung có dấu hiệu nguy hiểm đang xảy ra hoặc sắp xảy ra. Không cần trả lời thêm để xem hướng hỗ trợ.':'';
  el('summary').textContent=a.summary;
  el('actions').replaceChildren(...a.recommended_actions.map(text=>{const item=document.createElement('li');item.textContent=text;return item;}));
  el('questions').replaceChildren();
  if(a.follow_up_questions.length){const heading=document.createElement('h2');heading.textContent='Nếu có thể trao đổi an toàn';el('questions').append(heading);for(const text of a.follow_up_questions){const p=document.createElement('p');p.textContent=text;el('questions').append(p);}}
  const refs=new Set([...a.evidence_refs,...a.urgency_evidence_refs]);el('evidence').replaceChildren();
  const messageIds=new Map([["m1",text]]),seen=new Set();
  for(const s of data.annotations.spans){if(!refs.has(s.span_id)||!messageIds.has(s.message_id))continue;const original=messageIds.get(s.message_id);if(Array.from(original).slice(s.start,s.end).join('')!==s.quote||seen.has(s.quote))continue;seen.add(s.quote);const block=document.createElement('blockquote');block.textContent=s.quote;el('evidence').append(block);}
  if(!seen.size)el('evidence').textContent='Chưa có đoạn trích đủ để hỗ trợ một cảnh báo cụ thể.';
  el('status').textContent=response.ok?'Đã phân tích trong phạm vi bộ quy tắc.':'Phân tích chưa hoàn tất; xem thông tin an toàn còn có căn cứ.';
 }catch{if(run===generation){el('status').textContent='Chưa kiểm tra được. Nếu đang gặp nguy hiểm và có thể làm an toàn, tìm người tin cậy hoặc hỗ trợ khẩn cấp phù hợp; tránh đối đầu.';}}
 finally{if(run===generation)el('send').disabled=false;}
});
el('text').addEventListener('input',()=>{generation++;el('send').disabled=false;el('result').hidden=true;});
