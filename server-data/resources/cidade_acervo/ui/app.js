'use strict';
const $=s=>document.querySelector(s);
const inGame=typeof GetParentResourceName==='function',PAGE_SIZE=8;
const TAGS=['OK','PEÇA INCORRETA','DEFEITO NA TEXTURA'];
const zones={head:'Cabeça e pescoço',torso:'Tronco',leftArm:'Braço esquerdo',rightArm:'Braço direito',leftLeg:'Perna esquerda',rightLeg:'Perna direita'};
let items=[],sex='male',chosen={},appearance={},options={},browserAppearance={},tags={},busy=false,page=1,category='all',search='',zone='all',tagItem=null,tagDraft=[];
let rotation=0,pendingAngle=null,rotationTimer,rotating=false,rotationEpoch=0,rotationDrag=null;
const blank=()=>({hair:0,hairColor:0,beard:255,beardColor:0,tattoos:{}});
const code=i=>`${i.category.toUpperCase()} ${String(i.index).padStart(3,'0')}`;
const isAppearance=()=>['hair','beard','tattoo'].includes(category);
async function call(name,body={}){
 if(!inGame){
  if(name==='refresh'){
   const [clothes,looks,reviews]=await Promise.all([fetch('/api/wardrobe',{cache:'no-store'}),fetch('/api/appearance',{cache:'no-store'}),fetch('/api/tags',{cache:'no-store'})]);
   if(!clothes.ok||!looks.ok||!reviews.ok)throw Error('Não foi possível carregar o acervo.');
   return {ok:true,items:await clothes.json(),browserAppearance:await looks.json(),tags:(await reviews.json()).items};
  }
  if(name==='rotate')return {ok:true,rotation:body.angle};
  if(name==='tags'){
   const response=await fetch('/api/tags',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),result=await response.json();
   return response.ok?{ok:true,tags:{...tags,[body.id]:result.tags}}:{ok:false,error:result.error};
  }
  return {ok:false,error:'A prévia no personagem está disponível dentro do FiveM.'};
 }
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),12000);
 try{
  const response=await fetch(`https://${GetParentResourceName()}/${name}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
  if(!response.ok)throw Error('Não foi possível executar esta ação.');
  return await response.json();
 }finally{clearTimeout(timeout);}
}
function status(text){$('#status').textContent=text;}
function accept(result){
 if(result.sex)sex=result.sex;
 if(result.chosen)chosen=result.chosen;
 if(result.appearance)appearance=result.appearance;
 if(result.options)options=result.options;
 if(result.items)items=result.items;
 if(result.tags)tags=result.tags;
 if(result.browserAppearance)browserAppearance=result.browserAppearance;
 if(result.view)$('#view').value=result.view;
 if(result.rotation!==undefined&&!rotationDrag)showRotation(result.rotation);
}
function rows(){
 let list;
 if(category==='hair')list=(inGame?(options.hair||[]):(browserAppearance.hair||[]).filter(i=>i.sex===sex)).map(i=>({...i,kind:'hair',title:i.title||`Cabelo ${i.index}`,detail:i.collection||'Modelo nativo',value:i.index}));
 else if(category==='beard')list=[{kind:'beard',value:255,title:'Sem barba',detail:'Rosto limpo'},...Array.from({length:options.beardCount||0},(_,index)=>({kind:'beard',value:index,title:`Barba ${String(index).padStart(2,'0')}`,detail:'Confira o estilo no rosto'}))];
 else if(category==='tattoo')list=(inGame?(options.tattoos||[]):(browserAppearance.tattoos||[]).filter(i=>i.sex===sex)).filter(i=>zone==='all'||i.zone===zone).map(i=>({...i,kind:'tattoo',value:i.id,title:i.title||i.overlay,detail:i.collection}));
 else list=items.filter(i=>(i.exclusive===true||(tags[i.id]||[]).includes('OK'))&&i.sex===sex&&(category==='all'||category==='exclusive'&&i.exclusive===true||i.category===category)).sort((a,b)=>Number(b.exclusive===true)-Number(a.exclusive===true));
 const query=search.trim().toLocaleLowerCase('pt-BR');
 return list.filter(i=>!query||[i.title,i.detail,i.collectionLabel,i.overlay,i.kind?'':code(i)].join(' ').toLocaleLowerCase('pt-BR').includes(query));
}
function controls(){
 document.querySelectorAll('.piece,[data-sex],#category,#search,#zone,#view,#rotation-angle,.color-dot,.tag-button,#tag-options input,#tag-save,#tag-cancel').forEach(b=>b.disabled=busy||(!inGame&&(b.className.includes('piece')||b.className.includes('color-dot')||b=== $('#view'))));
 $('#apply').disabled=busy||!inGame;$('#reset').disabled=busy||!inGame;
 const pages=Math.max(1,Math.ceil(rows().length/PAGE_SIZE));
 $('#prev').disabled=busy||page===1;$('#next').disabled=busy||page>=pages;$('#refresh').disabled=busy;
}
async function action(name,body,done){
 if(busy)return;busy=true;controls();
 try{const result=await call(name,body);if(result.ok){accept(result);done?.(result);}else{status(result.error||'Aguarde e tente novamente.');if(tagItem)$('#tag-status').textContent=result.error||'Não foi possível salvar.';}}
 catch(error){const text=error.name==='AbortError'?'A ação demorou demais. Feche e abra o tablet novamente.':error.message;status(text);if(tagItem)$('#tag-status').textContent=text;}
 finally{busy=false;render();}
}
function selected(i){if(!inGame)return false;return i.kind==='tattoo'?!!appearance.tattoos?.[i.id]:i.kind?appearance[i.kind]===i.value:chosen[i.category]===i.id;}
function renderColors(){
 const show=(category==='hair'||category==='beard')&&(options.colors||[]).length>0;
 $('#appearance-tools').hidden=!isAppearance();$('#zone-label').hidden=category!=='tattoo';$('#color-label').hidden=!show;$('#colors').replaceChildren();
 if(show){
  const color=appearance[category==='hair'?'hairColor':'beardColor']||0;
  for(const c of options.colors){
   const dot=document.createElement('button');dot.type='button';dot.className='color-dot';dot.dataset.color=String(c.index);
   dot.style.backgroundColor=`rgb(${c.r},${c.g},${c.b})`;dot.title=`Tom ${c.index} · RGB ${c.r}, ${c.g}, ${c.b}`;
   dot.setAttribute('aria-label',dot.title);dot.setAttribute('aria-pressed',String(c.index===color));
   dot.onclick=()=>action('appearance',{kind:category==='hair'?'hairColor':'beardColor',value:c.index},()=>status('Tom aplicado no personagem.'));
   $('#colors').append(dot);
  }
 }
}
function openTags(item){
 tagItem=item;tagDraft=[...(tags[item.id]||[])];$('#tag-title').textContent=`${code(item)} · ${item.collectionLabel}`;$('#tag-status').textContent='';
 $('#tag-editor').hidden=false;renderTagOptions();$('#tag-cancel').focus();
}
function renderTagOptions(focusTag){
 $('#tag-options').replaceChildren();
 for(const tag of TAGS){const label=document.createElement('label'),check=document.createElement('input'),text=document.createElement('span');check.type='checkbox';check.checked=tagDraft.includes(tag);text.textContent=tag;
  check.onchange=()=>{if(check.checked){tagDraft=tag==='OK'?['OK']:[...tagDraft.filter(t=>t!=='OK'&&t!==tag),tag];}else tagDraft=tagDraft.filter(t=>t!==tag);renderTagOptions(tag);};
  label.append(check,text);$('#tag-options').append(label);if(tag===focusTag)check.focus();
 }
}
function closeTags(){tagItem=null;$('#tag-editor').hidden=true;}
function render(){
 const list=rows(),pages=Math.max(1,Math.ceil(list.length/PAGE_SIZE));page=Math.max(1,Math.min(page,pages));
 const active=Object.keys(chosen).length,approvedCount=items.filter(i=>(tags[i.id]||[]).includes('OK')).length,exclusiveCount=items.filter(i=>i.exclusive===true&&i.sex===sex).length;
 $('#count').textContent=isAppearance()?`${list.length} opções · aparência nativa`:`${list.length} ${sex==='male'?'masculinas':'femininas'} · ${approvedCount} peças OK${exclusiveCount?` · ${exclusiveCount} exclusivas`:''} · ${active} vestidas`;
 $('#empty').hidden=list.length>0;$('#pieces').hidden=!list.length;$('#pieces').replaceChildren();
 $('#pieces').classList.toggle('compact',category==='tattoo'||category==='beard');
 $('#empty-title').textContent=isAppearance()?'Nenhuma opção aqui.':'Nenhuma peça aqui.';
 $('#empty-note').textContent=isAppearance()?'As opções disponíveis são verificadas no personagem dentro do FiveM.':'Aplique a tag OK em peças desta categoria no acervo. A lista é sincronizada automaticamente.';
 for(const i of list.slice((page-1)*PAGE_SIZE,page*PAGE_SIZE)){
  const card=document.createElement('div');card.className='piece-card';
  const button=document.createElement('button');button.className=`piece${i.kind==='tattoo'||i.kind==='beard'?' appearance-piece':''}`;button.dataset.id=i.id||`${i.kind}:${i.value}`;
  button.setAttribute('aria-label',`${i.title}, ${i.kind?i.detail:code(i)}. ${selected(i)?'Remover':'Experimentar'}`);button.setAttribute('aria-pressed',String(selected(i)));
  if(i.kind==='tattoo'||i.kind==='beard'){
   const tag=document.createElement('span');tag.className='region';tag.textContent=i.kind==='tattoo'?zones[i.zone]:'Rosto';button.append(tag);
  }else if(i.image){
   const image=document.createElement('img');image.src=i.image;image.alt=i.title;image.width=512;image.height=640;image.loading='eager';
   image.onerror=()=>{image.classList.add('image-error');image.alt='Prévia indisponível. Confira no personagem.';};button.append(image);
  }else{const hint=document.createElement('div');hint.className='no-image';hint.textContent=i.value===0?'Sem cabelo':'Confira no personagem';button.append(hint);}
  if(i.exclusive===true){const badge=document.createElement('span');badge.className='exclusive-badge';badge.textContent='EXCLUSIVA';button.append(badge);}
  const title=document.createElement('strong');title.textContent=i.kind||i.exclusive===true?i.title:code(i);
  const subtitle=document.createElement('small');subtitle.textContent=i.kind?i.detail:`${i.title} · ${i.collectionLabel}`;button.append(title,subtitle);
  button.onclick=()=>{
   if(i.kind){const value=selected(i)&&i.kind==='hair'?0:selected(i)&&i.kind==='beard'?255:i.value;action('appearance',{kind:i.kind,value},()=>status('Aparência atualizada. As roupas foram preservadas.'));}
   else action('select',{id:i.id},result=>status(result.removed?'Peça removida. As outras escolhas foram mantidas.':`${i.title} aplicada. Combine com outras categorias.`));
  };
  card.append(button);
  if(!i.kind){
   const review=document.createElement('button');review.className='tag-button';review.type='button';review.dataset.id=i.id;
   review.textContent=(tags[i.id]||[]).length?tags[i.id].join(' · '):'+ Tags';review.setAttribute('aria-label',`Tags de ${code(i)}, ${i.collectionLabel}`);
   review.classList.toggle('has-tags',(tags[i.id]||[]).length>0);review.onclick=()=>openTags(i);card.append(review);
  }
  $('#pieces').append(card);
 }
 document.querySelectorAll('[data-sex]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sex===sex)));
 $('#page-info').textContent=`${page} / ${pages}`;$('.pager').hidden=list.length<=PAGE_SIZE;renderColors();controls();
}
function changeFilter(){page=1;render();$('#pieces').scrollTop=0;}
$('#category').onchange=()=>{category=$('#category').value;changeFilter();if(inGame)action('view',{view:category==='hair'||category==='beard'?'head':'full'});};
$('#search').oninput=()=>{search=$('#search').value;changeFilter();};
$('#zone').onchange=()=>{zone=$('#zone').value;changeFilter();if(inGame)action('view',{view:zone==='head'?'head':zone.includes('Leg')?'legs':zone==='all'?'full':'torso'});};
$('#view').onchange=()=>action('view',{view:$('#view').value});
function clearFilters(){category='all';search='';zone='all';page=1;$('#category').value='all';$('#search').value='';$('#zone').value='all';}
function stopRotation(){endRotationDrag();rotationEpoch++;pendingAngle=null;clearTimeout(rotationTimer);}
async function rotate(){
 if(rotating)return;rotating=true;const epoch=rotationEpoch;
 try{while(pendingAngle!==null&&epoch===rotationEpoch){const angle=pendingAngle;pendingAngle=null;const result=await call('rotate',{angle});if(epoch!==rotationEpoch)break;if(!result.ok){status('Aguarde para girar o personagem.');break;}}}
 catch(error){status(error.message);}finally{rotating=false;if(pendingAngle!==null)rotate();}
}
function showRotation(angle){
 rotation=Math.max(0,Math.min(360,Math.round(angle)));
 const thumb=$('#rotation-angle'),percent=`${rotation/360*100}%`;
 thumb.setAttribute('aria-valuenow',String(rotation));thumb.setAttribute('aria-valuetext',`${rotation} graus`);
 thumb.style.left=percent;$('#rotation-fill').style.width=percent;$('#rotation-value').textContent=`${rotation}°`;
}
function queueRotation(angle,flush=false){
 showRotation(angle);pendingAngle=rotation;clearTimeout(rotationTimer);
 if(flush)rotate();else rotationTimer=setTimeout(rotate,35);
}
function endRotationDrag(){
 const thumb=$('#rotation-angle'),drag=rotationDrag;rotationDrag=null;
 thumb.classList.remove('dragging');
 if(drag&&thumb.hasPointerCapture(drag.id))thumb.releasePointerCapture(drag.id);
}
$('#rotation-angle').onpointerdown=event=>{
 if(busy||event.button!==0||rotationDrag)return;
 event.preventDefault();
 rotationDrag={id:event.pointerId,x:event.clientX,angle:rotation,width:Math.max(1,$('#rotation-rail').getBoundingClientRect().width)};
 $('#rotation-angle').setPointerCapture(event.pointerId);$('#rotation-angle').classList.add('dragging');
};
$('#rotation-angle').onpointermove=event=>{
 if(!rotationDrag||event.pointerId!==rotationDrag.id)return;
 queueRotation(rotationDrag.angle+(event.clientX-rotationDrag.x)/rotationDrag.width*360);
};
$('#rotation-angle').onpointerup=event=>{
 if(!rotationDrag||event.pointerId!==rotationDrag.id)return;
 queueRotation(rotationDrag.angle+(event.clientX-rotationDrag.x)/rotationDrag.width*360,true);endRotationDrag();
};
$('#rotation-angle').onpointercancel=()=>{endRotationDrag();clearTimeout(rotationTimer);if(pendingAngle!==null)rotate();};
$('#rotation-angle').onlostpointercapture=()=>{if(rotationDrag){endRotationDrag();clearTimeout(rotationTimer);if(pendingAngle!==null)rotate();}};
$('#rotation-angle').onkeydown=event=>{
 const steps={ArrowRight:5,ArrowUp:5,ArrowLeft:-5,ArrowDown:-5,PageUp:30,PageDown:-30};
 if(!(event.key in steps)&&!['Home','End'].includes(event.key))return;
 event.preventDefault();queueRotation(event.key==='Home'?0:event.key==='End'?360:rotation+steps[event.key],true);
};
showRotation(0);
document.querySelectorAll('[data-sex]').forEach(button=>button.onclick=()=>{
 if(button.dataset.sex===sex)return;stopRotation();closeTags();
 if(!inGame){sex=button.dataset.sex;chosen={};appearance=blank();page=1;render();return;}
 status('Carregando personagem…');action('sex',{sex:button.dataset.sex},()=>{page=1;status('Personagem de roupa íntima. Combine peças de categorias diferentes.');});
});
$('#tag-cancel').onclick=()=>{if(!busy)closeTags();};
$('#tag-save').onclick=()=>{if(tagItem)action('tags',{id:tagItem.id,tags:tagDraft},()=>{closeTags();status('Tags salvas no acervo.');});};
$('#prev').onclick=()=>{page--;render();$('#pieces').scrollTop=0;};$('#next').onclick=()=>{page++;render();$('#pieces').scrollTop=0;};
$('#refresh').onclick=()=>action('refresh',{},()=>status('Peças OK, exclusivas e tags atualizadas.'));
$('#reset').onclick=()=>{stopRotation();action('reset',{},()=>status('Prévia restaurada: roupa íntima, sem acessórios, cabelo, barba ou tatuagens.'));};
$('#apply').onclick=()=>{stopRotation();action('apply',{},()=>{$('#wardrobe').hidden=true;});};
async function close(){if(!inGame)return;stopRotation();closeTags();try{await call('close');$('#wardrobe').hidden=true;}catch(error){status(error.message);}}
$('#close').onclick=close;document.addEventListener('keydown',event=>{
 if(tagItem&&event.key==='Tab'){
  const controls=[...document.querySelectorAll('#tag-editor input:not(:disabled),#tag-editor button:not(:disabled)')];
  if(!controls.length){event.preventDefault();return;}
  const first=controls[0],last=controls[controls.length-1];
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
 }
 if(event.key==='Escape'){if(tagItem){if(!busy)closeTags();}else close();}
});
window.addEventListener('message',event=>{const payload=event.data;if(!payload||typeof payload!=='object')return;
 if(payload.type==='open'){stopRotation();closeTags();chosen={};appearance=blank();options={};items=[];tags={};accept(payload);clearFilters();$('#wardrobe').hidden=false;status('Peças OK e variações exclusivas. As tags são sincronizadas com o acervo.');render();}
 if(payload.type==='items'){accept(payload);render();}
 if(payload.type==='close'){stopRotation();closeTags();$('#wardrobe').hidden=true;}
 if(payload.type==='status')status(payload.text);
});
if(!inGame){document.body.classList.add('browser-preview');$('#wardrobe').hidden=false;appearance=blank();call('refresh').then(result=>{accept(result);render();status('Prévia da interface. Experimente no personagem dentro do FiveM.');}).catch(error=>{render();status(error.message);});}
