import fs from 'node:fs';
const output=new URL('../reports/result_view/',import.meta.url);fs.mkdirSync(output,{recursive:true});
async function screenshot(cdp,page,name){const r=await cdp.call('Page.captureScreenshot',{format:'png'},page);fs.writeFileSync(new URL(name+'.png',output),Buffer.from(r.data,'base64'));}
export function fixture(status,long=false){
 const quote=status==='high'?'Nhập mật khẩu tài khoản trường. Điền dãy sáu số vừa hiện trên điện thoại.':'Chuyển khoản cho tôi.';
 const text=status==='clear'?'Chiều nay nhóm họp lúc 15 giờ.':Array.from({length:long?28:1},(_,i)=>`😀 Lời nhắn ${i+1}: ${quote}`).join('\n');
 const findings=[];let cursor=0;
 if(status!=='clear')for(let i=0;i<(long?28:1);i++){const at=text.indexOf(quote,cursor);cursor=at+quote.length;const start=Array.from(text.slice(0,at)).length;findings.push({id:'f'+i,action:status==='high'?'share_auth_code':'transfer_funds',speaker:'unknown',speech_role:'request',description:'PRIVATE_FINDING',inference:{text:'PRIVATE_INFERENCE'},evidence:[{message_id:'m1',quote,start,end:start+Array.from(quote).length}]});}
 return {text,result:{risk_status:status,mode:'two_pass',summary:'PRIVATE_SUMMARY source document',findings,answers:{claim:{text:'PRIVATE_ANSWERS'}},recommended_actions:['PRIVATE_ACTION'],source_matches:[{source_id:'PRIVATE_SOURCE',quote:'PRIVATE_SOURCE_TEXT',url:'https://example.gov.vn/PRIVATE_SOURCE'}],retrieval:{official_sources:{status:'matched'}},analysis:{prompt:'PRIVATE_PROMPT'},follow_up_questions:status==='need_context'?['Bạn quen người gửi qua kênh nào?','Khoản tiền này dùng vào việc gì?']:[],missing_information:status==='need_context'?['Mục đích khoản tiền']:[]}};
}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<100;i++){if(await fn())return;await pause(100);}throw Error('Result view wait timeout');}

export async function websiteChecks(cdp,page,check,report){
 await cdp.call('Emulation.setDeviceMetricsOverride',{width:390,height:800,deviceScaleFactor:1,mobile:false},page);
 await cdp.call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},page);
 await cdp.eval(page,`globalThis.viewRequests=[];globalThis.beforeViewFetch=fetch;globalThis.fetch=async(url,opts)=>{if(String(url).endsWith('/api/analyze')){viewRequests.push(JSON.parse(opts.body));return {ok:true,json:async()=>structuredClone(viewFixture.result)};}return beforeViewFetch(url,opts);};`);
 for(const status of ['high','need_context','clear']){
  const data=fixture(status,status==='need_context');
  await cdp.eval(page,`globalThis.viewFixture=${JSON.stringify(data)};document.querySelector('#format').value='text';document.querySelector('#url-target').value='';document.querySelector('#url-label').value='';document.querySelector('#content').value=viewFixture.text;document.querySelector('#content').dispatchEvent(new Event('input'));document.querySelector('#preview').click();document.querySelector('#send').click();`);
  await until(()=>cdp.eval(page,`document.querySelector('#result .ss-result')?.dataset.risk===${JSON.stringify(status)}`));
  check('WEB '+status+' immediate summary and next action',await cdp.eval(page,`(()=>{const r=document.querySelector('#result');return !!r.querySelector('.ss-summary')&&!!r.querySelector('.ss-next-action')&&getComputedStyle(r.querySelector('.ss-summary')).display!=='none'&&r.querySelector('.ss-result-header').getBoundingClientRect().top<r.querySelector('.ss-summary').getBoundingClientRect().top;})()`));
  check('WEB '+status+' hides answers, RAG and internal prose',await cdp.eval(page,`!document.querySelector('#result').innerText.includes('PRIVATE_')&&!document.querySelector('#result').innerText.includes('Chi tiết tám câu hỏi')&&!document.querySelector('#result a')`));
  if(status==='high'){
   check('WEB quotes retain exact Unicode spans',await cdp.eval(page,`document.querySelector('#result blockquote').textContent===viewFixture.result.findings[0].evidence[0].quote`));
   check('WEB inferred number remains qualified as possible authentication code',await cdp.eval(page,`document.querySelector('#result .ss-summary').textContent.includes('có thể là mã xác thực')`));
  }
  if(status==='need_context'){
   const before=await cdp.eval(page,`document.querySelector('#result .ss-result-header').getBoundingClientRect().top`);
   await cdp.eval(page,`document.querySelector('#result [data-action=explain]').click()`);
   const scroll=await cdp.eval(page,`(()=>{const b=document.querySelector('#result .ss-result-body'),h=document.querySelector('#result .ss-result-header');return {top:h.getBoundingClientRect().top,scroll:b.scrollTop,overflow:b.scrollHeight>b.clientHeight};})()`);
   check('WEB long result scrolls to explanation with fixed risk header',scroll.overflow&&scroll.scroll>0&&Math.abs(before-scroll.top)<1);
   await cdp.eval(page,`globalThis.staleViewForm=document.querySelector('#result form');document.querySelector('#result [data-action=supplement]').click();document.querySelector('#result textarea').value='Đây là khoản hoàn ứng trong nhóm quen biết.';document.querySelector('#result form').dispatchEvent(new Event('submit',{cancelable:true}));`);
   await until(()=>cdp.eval(page,`JSON.parse(document.querySelector('#payload').value).context?.includes('khoản hoàn ứng')`));
   check('WEB supplement previews same input and context without early API call',await cdp.eval(page,`JSON.parse(document.querySelector('#payload').value).text===viewFixture.text&&viewRequests.length===2`));
   await cdp.eval(page,`staleViewForm.dispatchEvent(new Event('submit',{cancelable:true}))`);
   check('WEB old analysis supplement cannot submit again',await cdp.eval(page,'viewRequests.length===2'));
  }
  if(status==='clear')check('WEB short result fits content without oversized blank area',await cdp.eval(page,`(()=>{const b=document.querySelector('#result .ss-result-body');return b.clientHeight<448&&b.scrollHeight<=b.clientHeight+1;})()`));
  check('WEB '+status+' fits mobile width',await cdp.eval(page,`(()=>{const b=document.querySelector('#result .ss-result');return b.scrollWidth<=b.clientWidth+1&&b.getBoundingClientRect().width<390;})()`));
  await cdp.eval(page,`document.querySelector('#result').scrollIntoView({block:'start'})`);await screenshot(cdp,page,'web-'+status);
 }
 // No valid quote may be replaced by invented text or free-form model explanations.
 check('WEB grounded situation summary and cross-speaker quotes render without raw analysis',await cdp.eval(page,`(()=>{const h=document.createElement('div'),a='Giao máy trước nhé.',b='Tôi đã tự kiểm tra và nhận đủ tiền.';ScamShieldUI.render(h,{risk_status:'clear',summary:'PRIVATE_SUMMARY',answers:{claim:{text:'PRIVATE_ANSWERS'}},analysis:{decision_version:'two-pass-6'},display_summary:'Người bán cho biết đã kiểm tra và nhận đủ tiền.',display_action:'Đối chiếu lại nếu có thay đổi.',findings:[],risk_indicators:[{kind:'handover_after_reported_payment',evidence:[{message_id:'a',quote:a,start:0,end:Array.from(a).length},{message_id:'b',quote:b,start:0,end:Array.from(b).length}],explanation:'Đây là lời xác nhận trong nội dung, không phải xác minh ngân hàng của hệ thống.'}]},{messages:[{id:'a',speaker:'Người mua',text:a},{id:'b',speaker:'Người bán',text:b}]});return h.querySelectorAll('blockquote').length===2&&h.textContent.includes('Người bán cho biết')&&h.textContent.includes('không phải xác minh ngân hàng')&&!h.textContent.includes('PRIVATE_');})()`));
 check('WEB invalid situation indicator quote is never displayed',await cdp.eval(page,`(()=>{const h=document.createElement('div');ScamShieldUI.render(h,{risk_status:'need_context',analysis:{decision_version:'two-pass-6'},findings:[],risk_indicators:[{evidence:[{message_id:'m1',quote:'FAKE_QUOTE',start:0,end:10}],explanation:'PRIVATE_FAKE_INDICATOR'}]},{text:'Nội dung khác'});return !h.querySelector('blockquote')&&!h.textContent.includes('PRIVATE_FAKE_INDICATOR')&&!h.textContent.includes('FAKE_QUOTE');})()`));
 check('WEB invalid evidence produces missing-evidence notice',await cdp.eval(page,`(()=>{const h=document.createElement('div');ScamShieldUI.render(h,{risk_status:'need_context',findings:[{speaker:'unknown',speech_role:'request',action:'share_auth_code',evidence:[{message_id:'m1',quote:'FAKE_QUOTE',start:0,end:10}]}],answers:{},follow_up_questions:[]},{text:'Nội dung thiếu ngữ cảnh'});return !h.querySelector('blockquote')&&h.textContent.includes('Chưa có đoạn trích hợp lệ')&&!h.textContent.includes('FAKE_QUOTE');})()`));
 await cdp.eval(page,'globalThis.fetch=beforeViewFetch');
 report.resultViewScope='UI fixtures intentionally seed high/need_context/clear and private fields; no provider/model claims for these checks';
}

export async function extensionChecks(cdp,page,worker,check,tab){
 await cdp.eval(worker,`globalThis.beforeResultFetch=fetch;globalThis.resultViewInputs=[];globalThis.fetch=async(url,opts)=>{if(String(url).endsWith('/api/analyze')&&globalThis.resultViewFixture){resultViewInputs.push(JSON.parse(opts.body));return {ok:true,json:async()=>structuredClone(resultViewFixture.result)};}return beforeResultFetch(url,opts);};`);
 for(const status of ['high','need_context','clear']){
  const data=fixture(status,status==='need_context');
  await cdp.eval(worker,`globalThis.resultViewFixture=${JSON.stringify(data)}`);
  await cdp.eval(page,`document.querySelector('#region').style.cssText='position:absolute;left:20px;top:20px;width:320px;padding:12px;background:white';document.querySelector('[data-ss-item]').replaceChildren(document.createTextNode(${JSON.stringify(data.text)}));`);
  // Only visible DOM text is eligible, so long fixture content itself stays in a small scroll-free line.
  if(status==='need_context'){
   await cdp.eval(page,`document.querySelector('[data-ss-item]').style.cssText='font-size:1px;line-height:1px';`);
  }else await cdp.eval(page,`document.querySelector('[data-ss-item]').style.fontSize='14px';document.querySelector('[data-ss-item]').style.lineHeight='1.5';`);
  await until(()=>cdp.eval(page,`document.querySelector('[data-ss-owned=badge] .ss-result')?.dataset.risk===${JSON.stringify(status)}`));
  check('EXT '+status+' result summary is immediately expanded',await cdp.eval(page,`!!document.querySelector('[data-ss-owned=badge] .ss-summary')&&document.querySelector('[data-ss-owned=badge] .ss-summary').getBoundingClientRect().height>0`));
  check('EXT '+status+' hides RAG answers and internal fields',await cdp.eval(page,`!document.querySelector('[data-ss-owned=badge]').innerText.includes('PRIVATE_')&&!document.querySelector('[data-ss-owned=badge] a')`));
  check('EXT '+status+' fits narrow result frame',await cdp.eval(page,`(()=>{const b=document.querySelector('[data-ss-owned=badge] .ss-result');return b.getBoundingClientRect().width<=320&&b.scrollWidth<=b.clientWidth+1;})()`));
  await screenshot(cdp,page,'extension-'+status);
  if(status==='need_context'){
   const headerTop=await cdp.eval(page,`document.querySelector('[data-ss-owned=badge] .ss-result-header').getBoundingClientRect().top`);
   await cdp.eval(page,`document.querySelector('[data-ss-owned=badge] [data-action=explain]').click()`);
   check('EXT long explanation scrolls while header stays visible',await cdp.eval(page,`(()=>{const b=document.querySelector('[data-ss-owned=badge] .ss-result-body'),h=document.querySelector('[data-ss-owned=badge] .ss-result-header');return b.scrollHeight>b.clientHeight&&b.scrollTop>0&&Math.abs(h.getBoundingClientRect().top-${headerTop})<1;})()`));
   await cdp.eval(page,`globalThis.oldExtensionForm=document.querySelector('[data-ss-owned=badge] form');document.querySelector('[data-ss-owned=badge] [data-action=supplement]').click();document.querySelector('[data-ss-owned=badge] textarea').value='Tôi chưa biết người nhận khoản tiền.';document.querySelector('[data-ss-owned=badge] form').dispatchEvent(new Event('submit',{cancelable:true}));`);
   await until(()=>cdp.eval(worker,'resultViewInputs.some(p=>p.context?.includes("chưa biết người nhận"))'));
   check('EXT supplement stays attached to same analyzed text',await cdp.eval(worker,`(()=>{const a=resultViewInputs.at(-2),b=resultViewInputs.at(-1);return a.text===b.text&&b.context.includes('chưa biết người nhận');})()`));
   await until(()=>cdp.eval(page,`!!document.querySelector('[data-ss-owned=badge] .ss-result')`));
  }
 }
 const before=await cdp.eval(worker,'resultViewInputs.length');
 await cdp.eval(page,`oldExtensionForm.dispatchEvent(new Event('submit',{cancelable:true}))`);await pause(200);
 check('EXT old item form cannot submit after content changes',await cdp.eval(worker,'resultViewInputs.length')===before);
}
