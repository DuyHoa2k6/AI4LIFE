/* User-facing result view. Backend decisions and response fields stay untouched. */
(() => {
  function render(target,result,payload,options={}){
    const UI=globalThis.ScamShieldUI;
    const analysisId=options.analysisId||crypto.randomUUID();
    target.replaceChildren();
    const box=UI.el('section',undefined,'ss-result');box.dataset.analysisId=analysisId;box.dataset.risk=result.risk_status;box.setAttribute('aria-label','Kết quả phân tích');
    box.style.cssText='display:block;max-width:100%;min-width:0;border:1px solid #dce5e0;border-radius:14px;background:#fff;color:#1e293b;font:14px/1.6 "Segoe UI",sans-serif;overflow:hidden;text-align:left;overflow-wrap:anywhere';target.append(box);
    const style=UI.el('style');style.textContent=`
      .ss-result .ss-result-header{padding:14px 16px;border-bottom:1px solid #e2e8f0;background:#fff}
      .ss-result .ss-result-title{margin:0 0 8px;font-size:15px;font-weight:700;color:#1e293b}
      .ss-result .ss-result-body{padding:16px;max-height:min(56dvh,520px,var(--ss-parent-limit,520px));overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable;scroll-behavior:smooth}
      .ss-result p{margin:0 0 12px}.ss-result h3{font:700 15px/1.5 "Segoe UI",sans-serif;margin:18px 0 10px;color:#1e293b}
      .ss-result ul,.ss-result ol{margin:6px 0 14px;padding-left:22px}.ss-result li{margin:6px 0}
      .ss-result button{font:600 13px/1.5 "Segoe UI",sans-serif;padding:8px 12px;min-height:36px;border:1px solid #b9cfc3;border-radius:8px;background:#f8faf9;color:#175d45;cursor:pointer;white-space:normal}
      .ss-result button:hover{background:#eaf4ee}.ss-result button:focus-visible,.ss-result textarea:focus-visible,.ss-result [tabindex]:focus-visible{outline:3px solid #429977;outline-offset:2px}
      .ss-result button:disabled{opacity:.55;cursor:wait}.ss-result blockquote{margin:0 0 8px;padding:10px 12px;border-left:3px solid #94a3b8;background:#f8fafc;color:#1e293b;white-space:pre-wrap}
      .ss-result .ss-evidence{padding:12px 0;border-bottom:1px solid #e2e8f0}.ss-result label{display:block;margin:10px 0 6px;font-weight:600}
      .ss-result textarea{box-sizing:border-box;display:block;width:100%;max-width:100%;min-height:85px;resize:vertical;margin:0 0 10px;padding:10px;border:1px solid #b8c8bf;border-radius:8px;font:14px/1.5 "Segoe UI",sans-serif;color:#1e293b;background:#fff}
      .ss-result .ss-followup{padding:12px;background:#eff6ff;border-radius:10px;margin:12px 0}.ss-result .ss-evidence-meta{font-size:12px;color:#64748b;margin-bottom:6px}
      .ss-result [hidden]{display:none!important}@media(prefers-reduced-motion:reduce){.ss-result .ss-result-body{scroll-behavior:auto}}
    `;box.append(style);
    const header=UI.el('header',undefined,'ss-result-header'),title=UI.el('div','Kết quả phân tích','ss-result-title');
    // Inline reset prevents the website navigation header rule from styling this header.
    header.style.cssText='display:block;height:auto;position:relative;padding:14px 16px;background:#fff;border-bottom:1px solid #e2e8f0';
    const limited=['partial','unsupported','error'].includes(result.analysis_status)&&!['high','suspicious'].includes(result.risk_status);
    const theme=UI.themeFor(result.risk_status),badge=UI.el('span',limited?'Chưa kiểm tra đầy đủ':theme.icon+' '+(UI.labels[result.risk_status]||'Chưa kiểm tra được'),'ss-risk');
    UI.applyTheme(badge,result.risk_status);Object.assign(badge.style,{display:'inline-block',padding:'7px 12px',borderRadius:'10px',fontWeight:'700',fontSize:'14px',lineHeight:'1.5'});
    if(limited)Object.assign(badge.style,{background:'#f1f5f9',color:'#475569',borderColor:'#cbd5e1'});
    header.append(title,badge);box.append(header);
    const body=UI.el('div',undefined,'ss-result-body');body.tabIndex=0;body.setAttribute('aria-label','Tóm tắt và giải thích kết quả');box.append(body);
    requestAnimationFrame(()=>{if(!box.isConnected)return;for(let p=box.parentElement;p&&p!==document.body;p=p.parentElement){if(/auto|scroll|hidden|clip/.test(getComputedStyle(p).overflowY)&&p.clientHeight){box.style.setProperty('--ss-parent-limit',Math.max(100,p.clientHeight-header.offsetHeight-60)+'px');break;}}});
    const messages=payload.messages||[{id:'m1',speaker:'unknown',text:payload.text}],byId=new Map(messages.map(m=>[m.id,m]));
    const validQuote=e=>{const m=byId.get(e.message_id);if(!m)return false;const chars=Array.from(m.text);return Number.isInteger(e.start)&&Number.isInteger(e.end)&&e.start>=0&&e.end>e.start&&e.end<=chars.length&&chars.slice(e.start,e.end).join('')===e.quote;};
    const indicators=(result.risk_indicators||[]).filter(i=>typeof i.explanation==='string'&&i.evidence?.length&&i.evidence.every(validQuote));
    const structured=['two-pass-6','local-rules-2.0','local-rules-2.1-support','facts-1.0-support','context-1.0-support','local-situation-1.0-support','phobert-structured-1.0-support'].includes(result.analysis?.decision_version);
    if(result.safety_urgency==='urgent'&&result.urgency_evidence?.length&&result.urgency_evidence.every(validQuote)){
      const urgent=UI.el('p','Ưu tiên an toàn: nội dung có dấu hiệu nguy hiểm đang xảy ra hoặc sắp xảy ra. Không cần trả lời thêm để xem hướng hỗ trợ.','ss-urgent');
      urgent.style.cssText='padding:12px;border-left:4px solid #b91c1c;background:#fff2f2;color:#7f1d1d;font-weight:600';body.append(urgent);
    }
    const checked=[];
    for(const f of result.findings||[]){
      const evidence=(f.evidence||[]).filter(e=>{const m=byId.get(e.message_id);if(!m||m.speaker!==f.speaker)return false;const chars=Array.from(m.text);return Number.isInteger(e.start)&&Number.isInteger(e.end)&&e.start>=0&&e.end>e.start&&e.end<=chars.length&&chars.slice(e.start,e.end).join('')===e.quote;});
      if(evidence.length&&evidence.length===(f.evidence||[]).length)checked.push({...f,evidence});
    }
    const requestFindings=checked.filter(f=>f.speech_role==='request'&&f.action!=='inducement');
    function actionText(f){
      const quote=f.evidence.map(e=>e.quote).join(' ');
      if(f.action==='share_auth_code'){
        const password=/mật khẩu|password/i.test(quote),explicit=/\bOTP\b|mã xác thực|mã xác nhận/i.test(quote),numbers=/dãy.{0,20}số|sáu số|6 số/i.test(quote),uncertain=/có thể|có lẽ|dường như/i.test(quote);
        const code=explicit&&!uncertain?'mã xác thực':'một dãy số có thể là mã xác thực';
        return password?'nhập hoặc cung cấp mật khẩu'+(numbers||explicit?' và '+code:''):'nhập hoặc cung cấp '+code;
      }
      return {transfer_funds:'chuyển tiền hoặc thanh toán',grant_access:'cấp quyền truy cập',install_app:'cài đặt ứng dụng',other:'thực hiện thao tác cần làm rõ bối cảnh'}[f.action]||'thực hiện thao tác trong lời nhắn';
    }
    // Never render free-form summary/description/inference/answers or retrieval prose.
    const actions=[...new Set(requestFindings.map(actionText))];
    let summary=actions.length?'Người gửi yêu cầu bạn '+actions.slice(0,3).join(', ')+'.':
      result.risk_status==='clear'?'Chưa ghi nhận dấu hiệu đáng ngờ trong nội dung đã gửi.':
      'Chưa có đủ bằng chứng hợp lệ để mô tả rõ yêu cầu và mục đích của lời nhắn.';
    if(result.risk_status==='need_context')summary+=' Cần bổ sung bối cảnh để đánh giá yêu cầu này.';
    else if(checked.some(f=>f.speech_role==='quoted_warning'||f.speech_role==='denial')&&!actions.length)summary+=' Nội dung có lời trích để cảnh báo hoặc phủ định.';
    if(structured&&typeof result.display_summary==='string')summary=result.display_summary;
    body.append(UI.el('p',summary,'ss-summary'));
    const clarificationStatus=result.case_context?.clarification_status;
    if(['question','mixed'].includes(clarificationStatus)&&typeof result.answer_to_user==='string')body.append(UI.el('p',result.answer_to_user,'ss-related-answer'));
    if(clarificationStatus==='off_topic')body.append(UI.el('p','Thông tin vừa nhập nằm ngoài phạm vi tình huống. Đánh giá trước đó được giữ nguyên.','ss-clarification-notice'));
    if(clarificationStatus==='unsupported')body.append(UI.el('p','Chưa hiểu đủ thông tin bổ sung. Hãy ghi ngắn: ai yêu cầu bạn làm gì và điều kiện để nhận quyền lợi là gì.','ss-clarification-notice'));
    const next=UI.el('div',undefined,'ss-next-action');next.append(UI.el('strong','Nên làm: '));
    const actionCodes=new Set(requestFindings.map(f=>f.action));
    next.append(document.createTextNode(structured&&typeof result.display_action==='string'?result.display_action:actionCodes.has('share_auth_code')||result.url_analysis?.length?'Mở trang hoặc ứng dụng chính thức bằng địa chỉ quen dùng để kiểm tra thông báo; không đăng nhập qua liên kết chưa xác minh.':actionCodes.has('transfer_funds')?'Liên hệ bên nhận qua số điện thoại hoặc kênh quen dùng để xác nhận mục đích trước khi chuyển tiền.':actionCodes.has('install_app')||actionCodes.has('grant_access')?'Kiểm tra nhà phát hành và mục đích cấp quyền qua kênh chính thức trước khi tiếp tục.':result.risk_status==='clear'?'Nếu cần, xác nhận lại với người gửi qua kênh quen dùng.':'Liên hệ người gửi qua kênh đã biết để làm rõ yêu cầu và bối cảnh.'));body.append(next);
    const questions=(result.follow_up_questions||[]).filter(q=>typeof q==='string'&&!/source_matches|system prompt|chain.of.thought|https?:\/\//i.test(q));
    if(!limited&&(result.risk_status==='need_context'||result.missing_information?.length||(!checked.length&&result.risk_status!=='clear'))&&!questions.length)questions.push('Người gửi là ai và họ muốn bạn thực hiện bước gì, với mục đích nào?');
    const current=()=>target.contains(box)&&(!options.isCurrent||options.isCurrent());
    if(questions.length){
      const followup=UI.el('section',undefined,'ss-followup');followup.append(UI.el('strong','Cần làm rõ'));const list=UI.el('ul');for(const q of questions.slice(0,2))list.append(UI.el('li',q));followup.append(list);
      const add=UI.el('button','Bổ sung thông tin');add.type='button';add.dataset.action='supplement';add.setAttribute('aria-expanded','false');followup.append(add);
      const form=UI.el('form'),input=UI.el('textarea'),label=UI.el('label','Thông tin bổ sung cho lần phân tích này'),send=UI.el('button',options.supplementLabel||'Phân tích với thông tin bổ sung'),status=UI.el('p');
      form.hidden=true;input.id='ss-context-'+analysisId;input.maxLength=2000;label.htmlFor=input.id;send.type='submit';status.setAttribute('role','status');form.append(label,input,send,status);followup.append(form);
      if(result.case_context){input.maxLength=1000;if(questions.some(q=>/nhận.*tiền|tiền.*tài khoản/i.test(q))){const choices=UI.el('div');for(const text of ['Tôi đã tự kiểm tra và nhận đủ tiền.','Tôi đã kiểm tra nhưng chưa nhận được tiền.','Tôi chưa kiểm tra tài khoản.']){const b=UI.el('button',text);b.type='button';b.onclick=()=>{input.value=text;input.focus();};choices.append(b);}form.insertBefore(choices,input);}}
      add.onclick=()=>{if(!current()){status.textContent='Kết quả đã cũ. Hãy phân tích lại nội dung hiện tại.';form.hidden=false;send.disabled=true;return;}form.hidden=!form.hidden;add.setAttribute('aria-expanded',String(!form.hidden));if(!form.hidden)input.focus();};
      form.onsubmit=async e=>{e.preventDefault();if(!current()){status.textContent='Kết quả đã cũ. Hãy phân tích lại nội dung hiện tại.';return;}if(!input.value.trim()){status.textContent='Nhập thông tin cần bổ sung.';return;}
        const updated=structuredClone(payload);
        if(result.case_context)updated.clarification={case_id:result.case_context.case_id,situation_id:result.case_context.situation_id,revision:result.case_context.revision,content_version:result.case_context.content_version,question_id:result.case_context.question_ids[0],answer:input.value.trim()};
        else updated.context=[updated.context||'',input.value.trim()].filter(Boolean).join('\n');
        try{UI.validate(updated);if(!options.onSupplement)throw Error('Hãy bổ sung bối cảnh ở ô nhập rồi gửi lại.');send.disabled=true;await options.onSupplement(updated,analysisId);status.textContent='Đã chuyển thông tin bổ sung cho đúng nội dung vừa phân tích.';}catch(err){status.textContent=err.message;}finally{send.disabled=false;}
      };body.append(followup);
    }
    const explainButton=UI.el('button','Xem giải thích');explainButton.type='button';explainButton.dataset.action='explain';explainButton.style.marginTop='14px';body.append(explainButton);
    const explanation=UI.el('section',undefined,'ss-explanation'),heading=UI.el('h3','Vì sao có cảnh báo này?');heading.tabIndex=-1;explanation.append(heading);
    explainButton.onclick=()=>{body.scrollTo({top:explanation.offsetTop-body.offsetTop,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});heading.focus({preventScroll:true});};
    const seen=new Set();
    const indicatorSpans=new Set();
    for(const indicator of indicators){const entry=UI.el('div',undefined,'ss-evidence');for(const e of indicator.evidence){indicatorSpans.add(e.message_id+':'+e.start+':'+e.end);entry.append(UI.el('div','Trích nội dung · '+(byId.get(e.message_id).speaker==='unknown'?'Chưa rõ người nói':byId.get(e.message_id).speaker),'ss-evidence-meta'),UI.el('blockquote',e.quote));}entry.append(UI.el('p',indicator.explanation));explanation.append(entry);}
    for(const f of checked){for(const e of f.evidence){const key=e.message_id+':'+e.start+':'+e.end+':'+f.speech_role;if(seen.has(key))continue;seen.add(key);
      if(indicatorSpans.has(e.message_id+':'+e.start+':'+e.end))continue;
      const entry=UI.el('div',undefined,'ss-evidence');entry.append(UI.el('div','Trích nội dung · '+(byId.get(e.message_id).speaker==='unknown'?'Chưa rõ người nói':byId.get(e.message_id).speaker),'ss-evidence-meta'),UI.el('blockquote',e.quote));
      const reason={share_auth_code:'cần xác minh kênh nhận để tránh lộ thông tin tài khoản',transfer_funds:'cần xác minh người nhận và mục đích để tránh chuyển nhầm hoặc mất tiền',grant_access:'quyền này có thể ảnh hưởng dữ liệu hoặc tài khoản của bạn',install_app:'cần kiểm tra nguồn cài đặt để tránh ứng dụng có quyền không mong muốn',other:'cần làm rõ mục đích trước khi thực hiện'}[f.action]||'cần đối chiếu với bối cảnh';
      let text=f.speech_role==='quoted_warning'?'Đây là lời được trích để cảnh báo, cần phân biệt với yêu cầu trực tiếp.':f.speech_role==='denial'?'Đoạn này phủ định hành vi, không tự coi là yêu cầu thực hiện.':f.action==='inducement'?'Đoạn này nêu lợi ích, sức ép hoặc điều kiện cần đối chiếu với yêu cầu trong lời nhắn.':f.speech_role==='request'?'Người gửi yêu cầu bạn '+actionText({...f,evidence:[e]})+'; '+reason+'.':'Đây là thông tin người gửi tự nêu, chưa phải danh tính hoặc sự việc đã được xác minh.';
      entry.append(UI.el('p',text));explanation.append(entry);
    }}
    if(!seen.size&&!indicators.length)explanation.append(UI.el('p',result.risk_status==='clear'?'Chưa có đoạn trích hợp lệ để giải thích thêm. Bạn có thể bổ sung lời nhắn và bối cảnh để kiểm tra tiếp.':'Chưa có đoạn trích hợp lệ để giải thích thêm. Hãy bổ sung nguyên văn lời nhắn, người gửi và thao tác được yêu cầu; chưa thể suy ra nội dung an toàn.'));
    if(result.input_sources?.length)explanation.append(UI.el('p','Một phần nội dung được đọc từ ảnh. Hãy đối chiếu đoạn trích với ảnh gốc vì chữ nhận dạng có thể sai.'));
    if(result.url_analysis?.length){const links=UI.el('section');links.append(UI.el('h3','Liên kết trong nội dung'));for(const u of result.url_analysis){links.append(UI.el('p',u.display_url));const n=u.network;if(n?.hops?.length){const chain=UI.el('ol');for(const h of n.hops)chain.append(UI.el('li',`${h.http_status} · ${h.display_url}`));links.append(chain);}if(n?.final_url)links.append(UI.el('p',`Đích phản hồi cuối: ${n.final_url} · HTTP ${n.final_http_status}`));links.append(UI.el('p',n&&n.status==='checked'?'Truy cập được không đồng nghĩa an toàn. Chưa kiểm tra nội dung hoặc danh tiếng trang.':'Chưa mở trang hoặc chưa xác định được đích cuối. Không có kết quả kiểm tra không đồng nghĩa an toàn.'));}explanation.append(links);}
    body.append(explanation);
  }
  globalThis.ScamShieldResultView=render;
})();
