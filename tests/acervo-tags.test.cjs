const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
// Run the actual synchronization and tag editor handlers with an isolated API.
const source=fs.readFileSync('catalogo_roupas_web/dist/app.js','utf8');
const syncCode=source.slice(source.indexOf('async function loadTags()'),source.indexOf("function setView("));
const nodes=new Map();
function node(id){
 if(!nodes.has(id))nodes.set(id,{children:[],textContent:'',disabled:false,append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},querySelectorAll(selector){const checks=this.children.map(i=>i.children[0]);return selector.includes(':checked')?checks.filter(i=>i.checked):checks;}});
 return nodes.get(id);
}
let remote={first:['OK']},reads=0,updates=0,poll,focus,visibility,hold;
const el=(tag,cls,text)=>({tag,children:[],textContent:text,append(...items){this.children.push(...items);}});
const context=vm.createContext({console,JSON,Object,Error,Promise,
 $:node,el,update(){updates++;},toast(){},
 setInterval(callback,ms){assert.equal(ms,3000);poll=callback;},
 window:{addEventListener(name,callback){if(name==='focus')focus=callback;}},
 document:{hidden:false,addEventListener(name,callback){if(name==='visibilitychange')visibility=callback;}},
 async fetch(url,params){assert.equal(url,'/api/tags');if(params.method==='POST'){const body=JSON.parse(params.body);remote={...remote,[body.id]:body.tags};return {ok:true,json:async()=>({ok:true,tags:body.tags})};}reads++;if(hold)await hold;return {ok:true,json:async()=>({items:remote})};}
});
vm.runInContext("let tags={},tagLoad=null,detailTagsDirty=false,tagSaving=false,data={},selected={id:'first'};const TAG_LABELS=['OK','PEÇA INCORRETA','DEFEITO NA TEXTURA'];",context);
vm.runInContext(syncCode,context);
(async()=>{
 await poll();assert.equal(updates,1);assert.match(node('#tags-sync-status').textContent,/1 peças OK/);
 await poll();assert.equal(updates,1); // No card rebuild when tags are unchanged.
 vm.runInContext('renderDetailTags()',context);
 const draft=node('#detail-tags').children[1].children[0];draft.checked=true;draft.onchange();
 remote={first:['OK'],second:['PEÇA INCORRETA']};await focus();assert.equal(updates,2);
 assert.equal(node('#detail-tags').children[1].children[0],draft);assert.equal(draft.checked,true); // Poll preserves unsaved edits.
 await node('#save-tags').onclick();assert.deepEqual(remote.first,['PEÇA INCORRETA']);assert.match(node('#tags-sync-status').textContent,/0 peças OK/);
 remote={first:['OK'],second:['OK']};await visibility();assert.equal(node('#detail-tags').children[0].children[0].checked,true);
 const before=reads;context.document.hidden=true;await poll();assert.equal(reads,before);context.document.hidden=false;
 let release;hold=new Promise(resolve=>{release=resolve;});const a=poll(),b=focus();assert.equal(reads,before+1);release();await Promise.all([a,b]);hold=null;
 console.log('PASS: automatic tag polling, focus/visibility, filters update only on change, shared save, draft preservation and no overlapping reads');
})().catch(error=>{console.error(error);process.exitCode=1;});
