/* Snapshot presentation and explicit Blob downloads; never a server upload. */
(() => {
  if(globalThis.SSConversationExport)return;
  function toText(snapshot){
    const people=new Map(snapshot.participants.map(p=>[p.participant_id,p]));const lines=['PHẠM VI: Các tin đã quan sát trong phiên.','LƯU Ý: Chưa xác định đầy đủ lịch sử. Thứ tự giữa các đoạn có thể chưa rõ.',''];
    for(const segment of snapshot.segments){lines.push('[Đoạn '+segment.segment_id+' — '+(segment.order_resolution==='uncertain'?'thứ tự chưa xác định':'thứ tự DOM đã quan sát')+']');
      for(const r of snapshot.messages.filter(m=>m.segment_id===segment.segment_id)){const p=people.get(r.sender_id),name=p?(p.display_name||(p.role==='self'?'Bạn':'Người tham gia '+p.participant_id))+' ['+p.participant_id+']':'Chưa xác định người gửi — tham chiếu '+r.unresolved_reference+(r.sender_display_name?' (nhãn hiển thị: '+r.sender_display_name+')':'');
        lines.push('['+(r.displayed_time||'Không rõ thời gian')+'] '+name+':',r.deleted?'[Tin đã thu hồi — không xuất nội dung cũ]':r.text);
        if(r.edited)lines.push('  [Đã chỉnh sửa]');if(r.reply_to)lines.push('  Trả lời tin: '+r.reply_to);
        for(const q of r.quoted_content)lines.push('  Nội dung tham chiếu ('+q.kind+'): '+q.text);
        for(const a of r.attachments)lines.push('  Đính kèm: '+a.type+(a.label?' — '+a.label:'')+', chưa đọc nội dung.');
        for(const l of r.links)lines.push('  Liên kết: '+l.text+' <'+l.href+'>');lines.push('');
      }
    }
    lines.push('TỔNG KẾT',JSON.stringify(snapshot.coverage,null,2),'Chẩn đoán: '+snapshot.diagnostics_summary.warnings.join(', '));return lines.join('\n');
  }
  function download(snapshot,kind,container){
    if(!snapshot||!['json','txt'].includes(kind))return;
    const blob=new Blob([kind==='json'?JSON.stringify(snapshot,null,2):toText(snapshot)],{type:kind==='json'?'application/json;charset=utf-8':'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download='conversation_'+snapshot.session_id+'.'+kind;container.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  globalThis.SSConversationExport={toText,download};
})();
