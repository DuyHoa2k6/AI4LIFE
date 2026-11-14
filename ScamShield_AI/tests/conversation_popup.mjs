import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../extension/popup.js',import.meta.url),'utf8');let n=0;
for(const [build,allowed] of [[null,true],['0.8.0',false],['0.9.0',true]]){
 const calls=[],controls={choose:{},message:{},conversation:{addEventListener(type,fn){this.click=fn;}}};
 const ctx=vm.createContext({document:{getElementById:id=>controls[id]},window:{close(){}},chrome:{tabs:{query:async()=>[{id:7,url:'https://example.invalid'}],sendMessage:async(id,m)=>calls.push(m.type)},scripting:{executeScript:async o=>{if(o.func)return[{result:{loaded:build!==null,build}}];calls.push(o.files);}}}});
 vm.runInContext(source,ctx);await controls.conversation.click();assert.equal(calls.includes('SS_CONVERSATION_CHOOSE'),allowed);
 if(allowed)assert.deepEqual(Array.from(calls.find(Array.isArray)),['conversation_model.js','conversation_adapter.js','conversation_export.js','conversation_capture.js']);
 else assert.match(controls.message.textContent,/Ctrl \+ Shift \+ R/);
 assert.equal(calls.some(x=>Array.isArray(x)&&x.includes('content.js')),false);n++;
}
for(const name of ['conversation_model.js','conversation_adapter.js','conversation_export.js','conversation_capture.js']){
 const text=fs.readFileSync(new URL('../extension/'+name,import.meta.url),'utf8');assert.ok(!/\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|runtime\.sendMessage|chrome\.storage|localStorage|sessionStorage/.test(text));n++;
}
console.log(`${n} conversation popup/isolation checks passed`);
