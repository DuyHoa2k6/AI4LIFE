document.getElementById('conversation')?.addEventListener('click',async()=>{
  const button=document.getElementById('conversation');button.disabled=true;
  try{
    const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
    if(!tab?.id||!/^https?:/.test(tab.url||''))throw Error('Mở trang HTTP/HTTPS trước.');
    const [loaded]=await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},func:()=>({loaded:!!globalThis.__scamShieldLoaded,build:globalThis.__scamShieldBuild})});
    if(loaded?.result?.loaded&&loaded.result.build!=='0.9.0')throw Error('Tab đang giữ phiên bản cũ. Hãy tải lại trang (Ctrl + Shift + R), rồi mở extension lại.');
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['conversation_model.js','conversation_adapter.js','conversation_export.js','conversation_capture.js']});
    await chrome.tabs.sendMessage(tab.id,{type:'SS_CONVERSATION_CHOOSE'},{frameId:0});window.close();
  }catch(e){document.getElementById('message').textContent='Không mở được chế độ thu thập. '+e.message;}
  finally{button.disabled=false;}
});
document.getElementById('choose').onclick=async()=>{
  const button=document.getElementById('choose');button.disabled=true;
  try{
    const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
    if(!tab?.id||!/^https?:/.test(tab.url||''))throw Error('Mở trang HTTP/HTTPS trước khi chọn vùng.');
    const [loaded]=await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},func:()=>({loaded:!!globalThis.__scamShieldLoaded,build:globalThis.__scamShieldBuild})});
    if(loaded?.result?.loaded&&loaded.result.build!=='0.9.0')throw Error('Tab đang giữ phiên bản cũ. Hãy tải lại trang (Ctrl + Shift + R), rồi mở extension lại.');
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['shared.js','result_view.js','panel_view.js','content.js']});
    await chrome.tabs.sendMessage(tab.id,{type:'SS_CHOOSE'},{frameId:0});
    window.close();
  }catch(e){document.getElementById('message').textContent='Không thể mở bộ chọn vùng trên tab này. '+e.message;}
  finally{button.disabled=false;}
};
