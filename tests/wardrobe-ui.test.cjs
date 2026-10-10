const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
class Element{
 constructor(){this.children=[];this.dataset={};this.attributes={};this.className='';this.style={};this.classList={add(){},remove(){},toggle(){}};}
 append(...children){this.children.push(...children);}
 replaceChildren(){this.children=[];}
 focus(){}
 setAttribute(name,value){this.attributes[name]=value;}
 getBoundingClientRect(){return {width:240};}
 setPointerCapture(id){this.pointer=id;}
 hasPointerCapture(id){return this.pointer===id;}
 releasePointerCapture(){this.pointer=null;}
}
const elements=new Map(),node=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const sexes=['male','female'].map(sex=>{const el=new Element();el.dataset.sex=sex;return el;});
const handlers={};let chosen={},appearance={},requests=[],tags={},rotation=0;
const blank=()=>({hair:0,hairColor:0,beard:255,beardColor:0,tattoos:{}});
const rows=Array.from({length:11},(_,index)=>({id:String(index),category:index%2?'task':'jbib',index,sex:'male',title:'Peça',collectionLabel:'Teste',image:'example.webp'}));
rows.push({id:'female',category:'lowr',index:1,sex:'female',title:'Calça',collectionLabel:'Teste',image:'example.webp'});
rows.push({id:'hat',category:'p_head',index:1,sex:'male',title:'Chapéu',collectionLabel:'Teste',image:'example.webp'});
tags=Object.fromEntries(rows.map(i=>[i.id,['OK']]));
rows.push({id:'badshoe',category:'feet',index:1,sex:'male',title:'Calçado com defeito',collectionLabel:'Teste',image:'example.webp',favorite:true});
tags.badshoe=['DEFEITO NA TEXTURA'];
const options={hair:[0,1,2].map(index=>({index,title:`Cabelo ${index}`,image:'hair.webp'})),colors:[{index:0,r:0,g:0,b:0},{index:1,r:100,g:50,b:20}],beardCount:3,tattoos:[{id:'tat1',title:'Arte 1',zone:'leftArm',collection:'native'},{id:'tat2',title:'Arte 2',zone:'rightLeg',collection:'native'}]};
const context=vm.createContext({console,AbortController,setTimeout,clearTimeout,GetParentResourceName:()=> 'cidade_acervo',
 document:{querySelector:node,createElement:()=>new Element(),addEventListener(){},querySelectorAll(selector){if(selector==='[data-sex]')return sexes;if(selector==='[data-rotate]')return [];return [...node('#pieces').children,...sexes];}},
 window:{addEventListener(name,handler){handlers[name]=handler;}},
 async fetch(url,params){const route=url.split('/').at(-1),body=JSON.parse(params.body);requests.push([route,body]);let result={ok:true};
  if(route==='select'){const item=rows.find(i=>i.id===body.id),removed=chosen[item.category]===item.id;if(removed)delete chosen[item.category];else chosen[item.category]=item.id;result.removed=removed;result.chosen={...chosen};}
  if(route==='appearance'){if(body.kind==='tattoo'){if(appearance.tattoos[body.value])delete appearance.tattoos[body.value];else appearance.tattoos[body.value]=true;}else appearance[body.kind]=body.value;result.appearance=JSON.parse(JSON.stringify(appearance));}
  if(route==='reset'||route==='sex'){chosen={};appearance=blank();result={ok:true,chosen,appearance,options,view:'full'};if(route==='sex')result.sex=body.sex;}
  if(route==='view')result.view=body.view;
  if(route==='rotate'){rotation=body.angle;result.rotation=rotation;}
  if(route==='tags'){tags[body.id]=body.tags;result.tags={...tags};}
  return {ok:true,json:async()=>result};
 }
});
vm.runInContext(fs.readFileSync('server-data/resources/cidade_acervo/ui/app.js','utf8'),context);
appearance=blank();handlers.message({data:{type:'open',sex:'male',items:rows,options,appearance,tags}});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const cards=()=>node('#pieces').children;
const pieces=()=>cards().map(c=>c.children[0]);
const selected=()=>pieces().filter(b=>b.attributes['aria-pressed']==='true');
async function filter(value){node('#category').value=value;node('#category').onchange();await flush();}
(async()=>{
 assert.equal(node('#pieces').children.length,8);
 pieces()[0].onclick();await flush();assert.equal(selected().length,1);
 pieces()[1].onclick();await flush();assert.equal(selected().length,2);
 pieces()[2].onclick();await flush();assert.equal(selected().length,2);assert.equal(selected()[0].dataset.id,'1');
 pieces()[1].onclick();await flush();assert.equal(selected().length,1);assert.equal(selected()[0].dataset.id,'2');
 await filter('p_head');assert.equal(node('#pieces').children.length,1);pieces()[0].onclick();await flush();assert.equal(chosen.jbib,'2');assert.equal(chosen.p_head,'hat');
 await filter('feet');assert.equal(node('#pieces').children.length,0);assert.match(node('#empty-note').textContent,/tag OK/);
 await filter('all');
 const outfit={...chosen};cards()[0].children[1].onclick();assert.equal(node('#tag-editor').hidden,false);assert.deepEqual(chosen,outfit);
 const check=node('#tag-options').children[1].children[0];check.checked=true;check.onchange();node('#tag-save').onclick();await flush();assert.deepEqual(tags['0'],['PEÇA INCORRETA']);assert.equal(node('#tag-editor').hidden,true);assert.deepEqual(chosen,outfit);
 const thumb=node('#rotation-angle'),pointer=(x,id=1)=>({button:0,pointerId:id,clientX:x,preventDefault(){}});
 assert.equal(node('#rotation-track').onclick,undefined);assert.equal(node('#rotation-rail').onclick,undefined);
 thumb.onpointerdown(pointer(20));assert.equal(thumb.hasPointerCapture(1),true);
 thumb.onpointermove(pointer(100,2));assert.equal(node('#rotation-value').textContent,'0°'); // Ignore unrelated pointer.
 thumb.onpointermove(pointer(100));thumb.onpointermove(pointer(200));thumb.onpointerup(pointer(200));await flush();
 assert.equal(rotation,270);assert.equal(node('#rotation-value').textContent,'270°');assert.equal(thumb.attributes['aria-valuenow'],'270');assert.equal(thumb.style.left,'75%');assert.equal(thumb.hasPointerCapture(1),false);
 thumb.onpointermove(pointer(0));assert.equal(node('#rotation-value').textContent,'270°');
 thumb.onkeydown({key:'End',preventDefault(){}});await flush();assert.equal(rotation,360);
 thumb.onpointerdown(pointer(0));thumb.onpointerup(pointer(500));await flush();assert.equal(rotation,360); // Clamp.
 node('#next').onclick();assert.equal(node('#pieces').children.length,3);assert.equal(node('#page-info').textContent,'2 / 2');
 await filter('hair');assert.equal(node('#pieces').children.length,3);assert.equal(node('#view').value,'head');pieces()[2].onclick();await flush();assert.equal(appearance.hair,2);assert.equal(chosen.jbib,'2');
 assert.equal(node('#colors').children[1].style.backgroundColor,'rgb(100,50,20)');node('#colors').children[1].onclick();await flush();assert.equal(appearance.hairColor,1);
 await filter('beard');pieces()[2].onclick();await flush();assert.equal(appearance.beard,1);
 await filter('tattoo');pieces()[0].onclick();await flush();pieces()[1].onclick();await flush();assert.equal(selected().length,2);
 node('#zone').value='leftArm';node('#zone').onchange();await flush();assert.equal(node('#pieces').children.length,1);assert.equal(node('#view').value,'torso');
 pieces()[0].onclick();await flush();assert.equal(appearance.tattoos.tat1,undefined);assert.equal(appearance.tattoos.tat2,true);
 node('#reset').onclick();await flush();assert.deepEqual(chosen,{});assert.deepEqual(appearance,blank());assert.equal(node('#view').value,'full');
 await filter('all');assert.equal(selected().length,0);assert.equal(node('#apply').disabled,false);
 sexes[1].onclick();await flush();assert.equal(node('#pieces').children.length,1);assert.equal(sexes[1].attributes['aria-pressed'],'true');assert.equal(node('#page-info').textContent,'1 / 1');
 assert.match(node('#count').textContent,/1 femininas · 12 peças OK/);
 rows.push({id:'exclusive-shirt',category:'jbib',index:0,sex:'male',title:'Camiseta West Texas',collectionLabel:'Exclusivas da cidade',image:'exclusive.png',exclusive:true});
 rows.push({id:'exclusive-jeans',category:'lowr',index:0,sex:'male',title:'Jeans azul lavado',collectionLabel:'Exclusivas da cidade',image:'jeans.png',exclusive:true});
 handlers.message({data:{type:'items',items:rows,tags}});
 await filter('exclusive');assert.equal(pieces().length,0); // These variants belong to the male character.
 sexes[0].onclick();await flush();assert.equal(pieces().length,2);
 assert.equal(pieces()[0].children.find(c=>c.className==='exclusive-badge').textContent,'EXCLUSIVA');
 assert.equal(pieces()[0].children.at(-2).textContent,'Camiseta West Texas');
 pieces()[0].onclick();await flush();pieces()[1].onclick();await flush();assert.equal(selected().length,2);
 pieces()[0].onclick();await flush();assert.equal(chosen.jbib,undefined);assert.equal(chosen.lowr,'exclusive-jeans');
 assert.equal(tags['exclusive-shirt'],undefined);assert.match(node('#count').textContent,/2 exclusivas/);
 await filter('all');assert.equal(pieces()[0].dataset.id,'exclusive-shirt');assert.equal(pieces()[1].dataset.id,'exclusive-jeans');
 await filter('feet');assert.equal(pieces().length,0); // Native defects remain excluded.
 console.log('PASS: OK eligibility/removal, independent categories, appearance, reset, female filter, drag capture, no track jumps, pointer isolation, clamp and keyboard rotation');
})().catch(error=>{console.error(error);process.exitCode=1;});
