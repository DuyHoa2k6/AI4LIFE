import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../extension/popup.js',import.meta.url),'utf8');
for(const [state,allowed] of [[{loaded:true},false],[{loaded:true,build:'0.8.0'},false],[{loaded:true,build:'0.9.0'},true],[{loaded:false},true]]){
 const controls={choose:{},message:{}},calls=[];
 const context=vm.createContext({document:{getElementById:id=>controls[id]},window:{close:()=>{}},chrome:{tabs:{query:async()=>[{id:1,url:'https://example.invalid'}],sendMessage:async()=>calls.push('choose')},scripting:{executeScript:async opts=>{if(opts.func)return[{result:state}];calls.push('inject');}}}});
 vm.runInContext(source,context);await controls.choose.onclick();
 assert.equal(calls.includes('inject'),allowed);
 assert.equal(calls.includes('choose'),allowed);
 if(!allowed)assert.match(controls.message.textContent,/Ctrl \+ Shift \+ R/);
 assert.equal(controls.choose.disabled,false);
}
console.log('4 popup version checks passed');
