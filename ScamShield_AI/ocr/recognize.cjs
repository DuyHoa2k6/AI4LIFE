// Local input path only, invoked by backend after decoding/size validation.
const path=require('node:path');
const {createWorker}=require('tesseract.js');
(async()=>{
  let worker;
  try{
    worker=await createWorker('vie+eng',1,{langPath:path.join(__dirname,'models'),gzip:true,cacheMethod:'none',logger:()=>{}});
    const {data}=await worker.recognize(process.argv[2],{}, {text:true,blocks:true});
    const lines=[];
    for(const block of data.blocks||[])for(const paragraph of block.paragraphs||[])for(const line of paragraph.lines||[]){
      if(line.text?.trim())lines.push({text:line.text.trim(),confidence:line.confidence,bbox:line.bbox});
    }
    process.stdout.write(JSON.stringify({text:data.text.trim(),confidence:data.confidence,blocks:lines}));
  }catch{process.stderr.write('LOCAL_OCR_FAILED');process.exitCode=1;}
  finally{if(worker)await worker.terminate();}
})();
