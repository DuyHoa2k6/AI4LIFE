import vm from 'node:vm';import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
let listener,active=4,captures=0;const calls=[],masks=[],checks=[];
const context=vm.createContext({AbortController,AbortSignal,Uint8Array,Blob,Map,JSON,Number,Array,String,Math,btoa,atob,setTimeout,clearTimeout,
 chrome:{runtime:{id:'test',onMessage:{addListener:fn=>listener=fn}},tabs:{onRemoved:{addListener:()=>{}},onUpdated:{addListener:()=>{}},query:async()=>[{id:active}],captureVisibleTab:async()=>{captures++;return 'data:image/png;base64,YQ==';}}},
 createImageBitmap:async()=>({width:1000,height:800,close(){}}),
 OffscreenCanvas:class{getContext(){return{drawImage(){},fillRect(...r){masks.push(r);},set fillStyle(v){}};}async convertToBlob(){return new Blob(['cropped']);}},
 fetch:async(url,opts)=>{if(String(url).startsWith('data:'))return {blob:async()=>new Blob(['screenshot'])};calls.push({url,opts});return{ok:true,json:async()=>String(url).endsWith('/api/ocr')?{status:'ready',text:'Synthetic OCR',source_id:'test'}:{risk_status:'clear'}};}});
vm.runInContext(fs.readFileSync(path.join(root,'extension/worker.js'),'utf8'),context);
const sender={id:'test',tab:{id:4,windowId:1},frameId:0,documentId:'doc',url:'https://fixture.example/'};
const send=m=>new Promise(resolve=>{if(!listener(m,sender,resolve))resolve(null);});
const check=(name,value)=>{assert.ok(value,name);checks.push({name,passed:true});};
await send({type:'SS_OPEN',session:'a'});
let r=await send({type:'SS_CAPTURE',session:'a',rect:{x:-1,y:0,width:10,height:10},viewport:{width:1000,height:800},redactions:[]});check('reject crop outside viewport before capture',!r.ok&&captures===0);
const capture={type:'SS_CAPTURE',session:'a',rect:{x:20,y:30,width:200,height:100},viewport:{width:1000,height:800},redactions:[{x:30,y:40,width:20,height:10}]};
r=await send(capture);check('preview crop produces no HTTP requests',r.ok&&calls.length===0);check('input mask applied before preview',masks.length===1&&masks[0][0]===10);
const cropped=r.image;r=await send({type:'SS_IMAGE_OCR',session:'wrong',image:cropped});check('wrong session cannot upload image',!r.ok&&calls.length===0);
await send({type:'SS_IMAGE_OCR',session:'a',image:cropped});check('only cropped bytes go to fixed OCR origin',calls.length===1&&calls[0].url==='http://127.0.0.1:8000/api/ocr'&&Buffer.from(calls[0].opts.body).toString()==='cropped');
active=9;r=await send(capture);check('changed active tab rejected',!r.ok&&captures===1);active=4;
await send({type:'SS_STOP',session:'a'});r=await send({type:'SS_IMAGE_OCR',session:'a',image:cropped});check('stopped session cannot OCR',!r.ok&&calls.length===1);
const directory=path.join(root,'reports/ocr');fs.mkdirSync(directory,{recursive:true});fs.writeFileSync(path.join(directory,'worker.json'),JSON.stringify({scope:'isolated worker with mocked Chrome/canvas APIs, not actual screenshot permission test',checks},null,2));console.log(checks.length+' OCR worker checks passed');
