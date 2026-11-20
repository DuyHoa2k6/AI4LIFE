(() => {
  function bytesToBase64(buf){const bytes=buf instanceof Uint8Array?buf:new Uint8Array(buf);let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+32768));return btoa(binary);}
  let stream=null,video=null,timer=null,busy=false,session=null,tabId=null,grab=null,running=false;
  async function stop(){
    running=false;
    if(timer){clearInterval(timer);timer=null;}
    if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
    if(video){video.srcObject=null;video=null;}
    busy=false;
  }
  async function tick(){
    if(busy||!running||!video||!video.videoWidth)return;
    busy=true;
    try{
      if(!grab)grab=document.createElement('canvas');
      const s=Math.min(1,960/video.videoWidth);
      grab.width=Math.round(video.videoWidth*s);grab.height=Math.round(video.videoHeight*s);
      grab.getContext('2d').drawImage(video,0,0,grab.width,grab.height);
      const img=grab.getContext('2d').getImageData(0,0,grab.width,grab.height).data;
      let sum=0,n=0,step=Math.max(1,Math.floor((img.length/4)/900));
      for(let i=0;i<img.length;i+=4*step){sum+=img[i]+img[i+1]+img[i+2];n++;}
      if(!n||(sum/(n*3))<10){
        await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_RESULT',tabId,result:{verdict:'cannot_assess',smoothed_score:null,reasons:[{text:'Chưa thấy khuôn mặt'}],frames_received:0},error:null,source:'tabCapture'});
        return;
      }
      const blob=await new Promise((ok,fail)=>grab.toBlob(b=>b?ok(b):fail(Error('Chưa thấy khuôn mặt')),'image/jpeg',0.85));
      if(!blob||blob.size<800){
        await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_RESULT',tabId,result:{verdict:'cannot_assess',smoothed_score:null,reasons:[{text:'Chưa thấy khuôn mặt'}],frames_received:0},error:null,source:'tabCapture'});
        return;
      }
      const bytes=await blob.arrayBuffer();
      const response=await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_FRAME',session,base64:bytesToBase64(bytes),mime:'image/jpeg'});
      const err=response?.ok||response?.skipped?null:(response?.error||'Lỗi gửi khung hình.');
      await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_RESULT',tabId,result:response?.result||null,error:err&&/không hợp lệ/i.test(err)?'Chưa thấy khuôn mặt':err,source:'tabCapture'});
    }catch(e){
      try{await chrome.runtime.sendMessage({type:'SS_DEEPFAKE_LIVE_RESULT',tabId,error:e.message,source:'tabCapture'});}catch{}
    }finally{busy=false;}
  }
  async function start(m){
    await stop();
    session=m.session;tabId=m.tabId;running=true;
    stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{mandatory:{chromeMediaSource:'tab',chromeMediaSourceId:m.streamId}}});
    video=document.createElement('video');video.muted=true;video.playsInline=true;video.srcObject=stream;
    await video.play();
    stream.getVideoTracks()[0].addEventListener('ended',()=>stop());
    timer=setInterval(tick,1000);tick();
  }
  chrome.runtime.onMessage.addListener((m,sender,reply)=>{
    if(sender.id!==chrome.runtime.id||!m||typeof m.type!=='string')return;
    if(m.type==='SS_DEEPFAKE_OFFSCREEN_START'){
      start(m).then(()=>reply({ok:true})).catch(e=>reply({ok:false,error:e.message}));
      return true;
    }
    if(m.type==='SS_DEEPFAKE_OFFSCREEN_STOP'){
      stop().then(()=>reply({ok:true}));return true;
    }
  });
})();
