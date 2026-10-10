'use strict';
const $ = id => document.getElementById(id);
const app = $('app'), preview = new URLSearchParams(location.search).get('preview') === '1';
const resource = typeof GetParentResourceName === 'function' ? GetParentResourceName() : 'cidade_admin';
const labels = {
  vehicles: ['Veículos', 'Encontre seu próximo veículo. Um clique e você já está ao volante.'],
  weapons: ['Armas', 'Escolha a arma e a munição para equipar no seu personagem.'],
  npcs: ['NPCs', 'Crie personagens específicos e gerencie os NPCs que você trouxe ao jogo.'],
  players: ['Jogadores e IDs', 'Localize, vá até um jogador ou traga-o para perto usando o ID permanente.'],
  commands: ['Comandos da cidade', 'Consulte os comandos, seus argumentos e os recursos que precisam estar ativos.'],
  cayo: ['Editor da ilha', 'Escolha elementos de Cayo Perico e objetos capturados em Los Santos, posicione e salve para todos.'],
};
let state = {tab:'vehicles',catalog:{vehicles:[],weapons:[],npcs:[],cayo:[]},commands:[],players:[],npcs:[],island:{revision:0,objects:[]},id:0,name:'ADM'};
let islandMode='catalog',paintCount=1,paintRadius=10,paintScale=1,deleteId=null,capturedObjects=[],captureMarks=[];
let imageDialog=null,imageReturnFocus=null;
let page=1, ammo=120, modalCommand=null, modalWeapon=null, weaponTrigger=null, busy=false, toastTimer;
let favorites=new Set();
try { const saved=JSON.parse(localStorage.getItem('cidadeAdminFavorites')||'[]');if(Array.isArray(saved))favorites=new Set(saved.filter(x=>typeof x==='string')); } catch (_) {}
const size=24;
const el=(tag,className,text)=>{const n=document.createElement(tag);if(className)n.className=className;if(text!==undefined)n.textContent=text;return n;};
const button=(text,className,fn)=>{const b=el('button',className,text);b.type='button';b.addEventListener('click',fn);return b;};
function toast(text,error=false){clearTimeout(toastTimer);$('toast').textContent=text;$('toast').classList.toggle('error',error);$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,4500);}
async function post(endpoint,data={}){
  if(preview){
    if(endpoint==='close'){app.hidden=true;return {ok:true};}
    return {ok:true,message:'Prévia visual: esta ação será executada ao abrir o painel dentro do jogo.'};
  }
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),17000);
  try {const r=await fetch(`https://${resource}/${endpoint}`,{method:'POST',headers:{'Content-Type':'application/json; charset=UTF-8'},body:JSON.stringify(data),signal:controller.signal});if(!r.ok)throw new Error();return await r.json();}
  catch(_){return {ok:false,message:'Não foi possível falar com o jogo. Feche e abra o painel novamente.'};}
  finally{clearTimeout(timer);}
}
async function act(data){
  if(busy){toast('Aguarde a ação atual terminar.');return;}
  busy=true;app.classList.add('busy');
  try {
    const r=await post('action',data);
    if(r.message)toast(r.message,!r.ok);
    if(r.ok&&r.data){if(r.data.players)state.players=r.data.players;if(r.data.npcs)state.npcs=r.data.npcs;render();}
    return r;
  }finally{busy=false;app.classList.remove('busy');}
}
function open(data){
  state={...state,...data};state.npcs=data.npcs||[];state.players=data.players||[];
  state.catalog=data.catalog||state.catalog;state.commands=data.commands||[];
  if(Array.isArray(data.captured))capturedObjects=withCaptureImages(data.captured);
  if(Array.isArray(data.captureMarks))captureMarks=data.captureMarks;
  mergeCaptures();
  $('account-name').textContent=state.name;$('account-id').textContent=`ID permanente ${state.id}`;
  for(const kind of ['vehicles','weapons','npcs','cayo'])$(`count-${kind}`).textContent=(state.catalog[kind]||[]).length;
  $('preview-badge').hidden=!preview;app.hidden=false;setTab(data.tab||'vehicles');
}
function withCaptureImages(rows){
  const images=new Map(capturedObjects.filter(row=>row.image).map(row=>[row.model,row.image]));
  return rows.map(row=>({...row,image:row.image||images.get(row.model)}));
}
function mergeCaptures(){
  const captured=new Set(capturedObjects.map(row=>row.model));
  state.catalog.cayo=[...(state.catalog.cayo||[]).filter(row=>!row.captured&&!captured.has(row.model)),...capturedObjects.map(row=>({...row,captured:true}))];
  $('count-cayo').textContent=state.catalog.cayo.length;
}
function setTab(tab){
  state.tab=labels[tab]?tab:'vehicles';page=1;$('search').value='';$('favorites-only').checked=false;
  $('title').textContent=labels[state.tab][0];$('subtitle').textContent=labels[state.tab][1];
  document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===state.tab));
  $('search').placeholder=state.tab==='commands'?'Buscar comando, descrição ou recurso…':state.tab==='players'?'Buscar ID ou nome do jogador…':'Buscar por nome ou modelo…';
  $('favorite-control').hidden=['commands','players'].includes(state.tab);
  $('category').hidden=state.tab==='players';$('category').replaceChildren(el('option','', 'Todas as categorias'));$('category').firstChild.value='';
  const source=state.tab==='commands'?state.commands:state.catalog[state.tab]||[];
  [...new Set(source.map(x=>x.category))].filter(Boolean).sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(c=>{const option=el('option','',c);option.value=c;$('category').append(option);});
  renderActions();render();
  if(state.tab==='cayo'&&!preview)islandAct({action:'list'},false);
}
async function islandAct(data,feedback=true){
  if(busy){toast('Aguarde a ação atual terminar.');return;}
  busy=true;
  try{
    const r=await post('islandAction',data);
    if(r.message&&feedback)toast(r.message,!r.ok);
    if(r.ok&&r.data?.objects){state.island=r.data;renderActions();render();}
    if(r.ok&&data.action==='begin'&&!preview)app.hidden=true;
    if(!r.ok&&r.data?.objects){state.island=r.data;renderActions();render();}
    return r;
  }finally{busy=false;}
}
function renderActions(){
  const actions=$('actions');actions.replaceChildren();
  const kind=state.tab;
  if(['vehicles','npcs'].includes(kind)){
    const input=el('input','model-input');input.id='custom-model';input.maxLength=64;input.autocomplete='off';input.placeholder=kind==='vehicles'?'Modelo específico: adder, sertao…':'Modelo específico: s_m_y_cop_01…';input.setAttribute('aria-label','Modelo específico');
    const spawn=()=>{const model=input.value.trim().toLowerCase();if(!/^[a-z0-9_]{1,64}$/.test(model)){toast('Digite um nome de modelo válido.',true);return;}act({action:kind==='vehicles'?'vehicle':'npc',model});};
    input.addEventListener('keydown',e=>{if(e.key==='Enter')spawn();});actions.append(input,button('Criar por modelo →','primary',spawn));
    if(kind==='vehicles')actions.append(button('Remover meu veículo','secondary danger',()=>act({action:'deleteVehicle'})));
  }else if(kind==='weapons'){
    actions.append(el('span','ammo-label','Selecione a arma para informar a munição.'),button('Remover minhas armas','secondary danger',()=>act({action:'disarm'})));
  }else if(kind==='players'){
    const input=el('input');input.id='target-id';input.type='number';input.min='1';input.step='1';input.placeholder='ID permanente';input.setAttribute('aria-label','ID permanente do jogador');
    actions.append(input,button('Localizar','primary',()=>idAction('localizar',input.value)),button('Ir até','secondary',()=>idAction('encontrar',input.value)),button('Trazer para perto','secondary',()=>idAction('chamar',input.value)),button('↻ Atualizar jogadores','secondary',()=>act({action:'players'})));
  }else if(kind==='cayo'){
    const tabs=el('div','island-switch');
    const switchMode=mode=>{islandMode=mode;page=1;$('category').value='';$('search').value='';$('favorites-only').checked=false;renderActions();render();};
    tabs.append(button('Catálogo de elementos',islandMode==='catalog'?'primary':'secondary',()=>switchMode('catalog')),button(`Meus itens capturados · ${capturedObjects.length}`,islandMode==='captured'?'primary':'secondary',()=>switchMode('captured')),button(`Objetos salvos · ${state.island.objects.length}`,islandMode==='saved'?'primary':'secondary',()=>switchMode('saved')));actions.append(tabs);
    if(islandMode!=='saved'){
      const count=el('input');count.type='number';count.id='paint-count';count.min='1';count.max='32';count.step='1';count.value=paintCount;count.setAttribute('aria-label','Objetos por aplicação');count.addEventListener('change',()=>{const n=Number(count.value);paintCount=Number.isInteger(n)&&n>=1&&n<=32?n:1;count.value=paintCount;});
      const radius=el('input');radius.type='number';radius.id='paint-radius';radius.min='1';radius.max='50';radius.value=paintRadius;radius.setAttribute('aria-label','Raio da aplicação em metros');radius.addEventListener('change',()=>{const n=Number(radius.value);paintRadius=Number.isFinite(n)&&n>=1&&n<=50?n:10;radius.value=paintRadius;});
      const a=el('label','ammo-label','Quantidade '),b=el('label','ammo-label','Raio (m) ');a.append(count);b.append(radius);const scale=el('input');scale.type='number';scale.id='paint-scale';scale.min='.25';scale.max='3';scale.step='.05';scale.value=paintScale;scale.setAttribute('aria-label','Escala do objeto');scale.addEventListener('change',()=>{const n=Number(scale.value);paintScale=Number.isFinite(n)?Math.min(3,Math.max(.25,n)):1;scale.value=paintScale;});const size=el('label','ammo-label','Escala (1 = original) ');size.append(scale);actions.append(a,b,size);
    }
    actions.append(button('Desfazer minha última aplicação','secondary',()=>islandAct({action:'undo'})),button('↻ Atualizar','secondary',()=>islandAct({action:'list'})));
  }else{
    actions.append(button('Jogadores e IDs','secondary',()=>setTab('players')),button('Ver edição de objetos','secondary',()=>{$('search').value='objeto';page=1;render();}));
  }
}
function idAction(name,value){const id=Number(value);if(!Number.isSafeInteger(id)||id<1){toast('Use um ID permanente positivo.',true);return;}act({action:'command',name,args:String(id)});}
function matches(row){
  const q=$('search').value.trim().toLocaleLowerCase('pt-BR');const c=$('category').value;
  if(c&&row.category!==c)return false;
  if($('favorites-only').checked&&!['commands','players'].includes(state.tab)&&!favorites.has(`${state.tab}:${row.model}`))return false;
  return !q||[row.name,row.model,row.sourceModel,row.alias,row.description,row.usage,row.resource,row.id,row.category].filter(x=>x!==undefined).join(' ').toLocaleLowerCase('pt-BR').includes(q);
}
function previewIslandImage(row){
  imageReturnFocus=document.activeElement;
  if(!imageDialog){imageDialog=el('dialog','island-image-dialog');imageDialog.setAttribute('aria-labelledby','island-image-title');document.body.append(imageDialog);imageDialog.addEventListener('close',()=>{if(imageReturnFocus?.isConnected)imageReturnFocus.focus();});imageDialog.addEventListener('click',e=>{if(e.target===imageDialog)imageDialog.close();});}
  imageDialog.replaceChildren();const title=el('h2','',row.name);title.id='island-image-title';
  const img=el('img');img.src=row.image;img.alt=row.name;
  const actions=el('div','buttons');actions.append(button('Fechar','secondary',()=>imageDialog.close()),button('Posicionar este elemento ↗','primary',()=>{imageDialog.close();islandAct({action:'begin',model:row.model,count:paintCount,radius:paintRadius,scale:paintScale});}));
  imageDialog.append(title,el('p','',row.category),img,actions);imageDialog.showModal();
}
function card(row){
  const kind=state.tab, key=`${kind}:${row.model}`,c=el('article',`card ${kind==='npcs'?'npc':kind==='weapons'?'weapon':kind==='cayo'?'cayo':''}`);
  const favorite=button(favorites.has(key)?'★':'☆',`favorite ${favorites.has(key)?'saved':''}`,()=>{if(favorites.has(key))favorites.delete(key);else favorites.add(key);try{localStorage.setItem('cidadeAdminFavorites',JSON.stringify([...favorites]));}catch(_){}render();});favorite.setAttribute('aria-label',`Favoritar ${row.name}`);favorite.setAttribute('aria-pressed',String(favorites.has(key)));
  const media=el('div','thumbnail'),img=el('img');img.src=row.image||'fallback.svg';img.alt=row.name;img.loading='lazy';img.addEventListener('error',()=>{if(!img.src.endsWith('/fallback.svg'))img.src='fallback.svg';});media.append(img);
  if(kind==='cayo'&&row.image==='fallback.svg'){img.hidden=true;media.append(el('span','island-symbol',row.category.includes('Árvores')?'♧':row.category.includes('plantas')?'❦':row.category.includes('rochas')?'◆':row.category.includes('Água')?'◉':'▤'));}
  if(kind==='cayo'&&row.image!=='fallback.svg'){media.tabIndex=0;media.setAttribute('role','button');media.setAttribute('aria-label',`Ampliar imagem de ${row.name}`);media.title='Clique para ampliar';media.addEventListener('click',()=>previewIslandImage(row));media.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();previewIslandImage(row);}});}
  const info=el('div','card-info');info.append(el('h3','',row.name));if(kind!=='cayo')info.append(el('code','',row.model));const bottom=el('div','card-bottom');bottom.append(el('span','tag',row.category),button(kind==='cayo'?'Posicionar ↗':kind==='weapons'?'Equipar ↗':'Criar ↗','primary spawn',()=>{if(kind==='cayo'){islandAct({action:'begin',model:row.model,count:paintCount,radius:paintRadius,scale:paintScale});return;}if(kind==='weapons'){weaponModal(row);return;}act({action:kind==='vehicles'?'vehicle':'npc',model:row.model});}));info.append(bottom);c.append(favorite,media,info);return c;
}
function ownedNpcs(){
  const block=el('div','owned'),head=el('div','owned-header');head.append(el('strong','',`Seus NPCs no jogo · ${state.npcs.length}/12`),button('Remover todos','secondary danger',()=>act({action:'npcClear'})));block.append(head);
  if(!state.npcs.length)block.append(el('small','', 'Os personagens que você criar aparecem aqui. Você pode trazê-los de volta para perto.'));
  const list=el('div','owned-list');state.npcs.forEach(row=>{const item=el('div','owned-row');item.append(el('code','',row.model),button('Trazer','secondary',()=>act({action:'npcBring',id:row.id})),button('×','secondary danger',()=>act({action:'npcDelete',id:row.id})));list.append(item);});block.append(list);return block;
}
function render(){
  const content=$('content');content.replaceChildren();
  const original=state.tab==='cayo'&&islandMode==='saved'?state.island.objects.map(row=>({...state.catalog.cayo.find(x=>x.model===row.model),...row})):state.tab==='cayo'&&islandMode==='captured'?capturedObjects:state.tab==='commands'?state.commands:state.tab==='players'?state.players:state.catalog[state.tab]||[];
  const rows=original.filter(matches),pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages);
  const visible=rows.slice((page-1)*size,page*size);
  if(state.tab==='npcs')content.append(ownedNpcs());
  if(state.tab==='commands'){
    const info=el('div','info-box');info.append(el('strong','', 'Objetos: controles do editor existente'),el('div','', 'editarobjetos → CAPS pega/salva • ← → giram • Page Up/Down alteram a altura • HOME restaura a origem • Backspace cancela. O editor da mansão atua nos objetos definidos naquele recurso e salva para todos. Recursos desligados aparecem na lista com o botão desativado.'));content.append(info);
    content.append(commandTable(visible));
  }else if(state.tab==='players')content.append(playerTable(visible));
  else if(state.tab==='cayo'){
    if(islandMode==='captured'&&captureMarks.length){const pending=el('details','info-box');pending.append(el('summary','',`${captureMarks.length} marcações em preparação ou análise · clique para consultar`));for(const mark of captureMarks.slice(-20))pending.append(el('div','',`#${mark.id} · ${mark.name} · ${mark.status}`));content.append(pending);}
    const info=el('div','info-box');info.append(el('strong','',islandMode!=='saved'?'Do catálogo para a sua ilha':'Colocações persistentes'),el('div','',islandMode!=='saved'?'Clique na imagem para ampliar e conferir o elemento. Posicionar abandona a prévia anterior e abre a nova no jogo. Escala 0,5 reduz pela metade; 1 mantém o tamanho original; 2 dobra o tamanho. O objeto aparece à frente, alinhado ao chão, e acompanha seus movimentos, inclusive durante o voo. ↑/↓ ajustam a altura • ←/→ giram • Enter salva • Backspace cancela • F fixa/acompanha • +/- alteram a escala • V muda para primeira pessoa. Aproxime-se de um objeto salvo e pressione Caps Lock para editá-lo novamente. Quantidade maior que 1 distribui um grupo no raio escolhido.':'Cada aplicação é salva no servidor e aparece para todos, inclusive depois de reconectar. Você pode reposicionar, marcar no mapa ou remover um objeto.'));content.append(info);
    if(islandMode==='saved')content.append(islandTable(visible));else{const grid=el('div','grid');visible.forEach(row=>grid.append(card(row)));content.append(grid);}
  }
  else{const grid=el('div','grid');visible.forEach(row=>grid.append(card(row)));content.append(grid);}
  if(!rows.length)content.append(el('div','empty',state.tab==='players'?'Nenhum jogador encontrado. Atualize a lista ou use o ID permanente acima.':'Nenhum resultado. Tente outro nome, modelo ou categoria.'));
  $('result-count').textContent=`${rows.length} ${state.tab==='commands'?'comandos':state.tab==='players'?'jogadores':'modelos'}${preview?' · prévia do catálogo':' · disponíveis nesta sessão'}`;
  if(state.tab==='commands')$('result-count').textContent=`${rows.length} comandos · ${rows.filter(x=>x.active).length} ativos`;
  $('page-label').textContent=`${page} / ${pages}`;$('previous').disabled=page<=1;$('next').disabled=page>=pages;
}
function islandTable(rows){
  const [t,body]=table(['OBJETO','POSIÇÃO','ESCALA','AÇÕES']);
  rows.forEach(row=>{
    const tr=el('tr'),name=el('td');name.append(el('strong','',row.name||row.model),el('small','',`#${row.id} · ADM ${row.author}`));
    const position=el('td','',`${row.x.toFixed(1)}, ${row.y.toFixed(1)}, ${row.z.toFixed(1)}`),scale=el('td','',row.scale.toFixed(2)),cell=el('td'),actions=el('div','buttons');
    actions.append(button('Reposicionar','primary spawn',()=>islandAct({action:'begin',model:row.model,id:row.id,count:1,radius:0})),button('Marcar','secondary',()=>islandAct({action:'locate',id:row.id})),button(deleteId===row.id?'Confirmar remoção':'Remover','secondary danger',()=>{if(deleteId===row.id){deleteId=null;islandAct({action:'delete',id:row.id});}else{deleteId=row.id;render();}}));
    cell.append(actions);tr.append(name,position,scale,cell);body.append(tr);
  });return t;
}
function table(headers,className){const t=el('table',`table ${className||''}`),head=el('thead'),tr=el('tr');headers.forEach(h=>tr.append(el('th','',h)));head.append(tr);const body=el('tbody');t.append(head,body);return [t,body];}
function playerTable(rows){
  const [t,body]=table(['ID PERMANENTE','JOGADOR','INSTÂNCIA','AÇÕES']);
  rows.forEach(row=>{const tr=el('tr');tr.append(el('td','',String(row.id)),el('td','',row.name),el('td','',String(row.bucket)));const cell=el('td'),actions=el('div','buttons');actions.append(button('Localizar','secondary',()=>idAction('localizar',row.id)),button('Ir até','secondary',()=>idAction('encontrar',row.id)),button('Trazer','primary spawn',()=>idAction('chamar',row.id)));cell.append(actions);tr.append(cell);body.append(tr);});return t;
}
function commandTable(rows){
  const [t,body]=table(['COMANDO / USO','O QUE FAZ','RECURSO','AÇÕES'],'command-table');
  rows.forEach(row=>{const tr=el('tr'),name=el('td');name.append(el('code','',row.usage||row.name),el('small','',row.category));const desc=el('td');desc.append(el('div','description',row.description),el('div','resource',row.resource));const status=el('td');status.append(el('span',`status ${row.active?'':'off'}`,row.active?'Ativo':'Desligado'));const cell=el('td'),actions=el('div','buttons');actions.append(button('Copiar','secondary',()=>copy(row.usage||row.name)));const run=button('Executar','primary spawn',()=>commandModal(row));run.disabled=!row.active||row.allowed===false||['painel','paineladm','npcs'].includes(row.name);actions.append(run);cell.append(actions);tr.append(name,desc,status,cell);body.append(tr);});return t;
}
async function copy(text){
  try{await navigator.clipboard.writeText(text);toast('Comando copiado. Substitua os argumentos indicados antes de usar.');}
  catch(_){const field=el('textarea');field.value=text;document.body.append(field);field.select();const ok=document.execCommand('copy');field.remove();toast(ok?'Comando copiado.':text,!ok);}
}
function commandModal(row){
  modalCommand=row;$('modal-title').textContent=row.name;$('modal-description').textContent=row.description;$('modal-usage').textContent=row.usage||row.name;
  const usage=(row.usage||row.name).slice(row.name.length).trim();$('command-args').value='';$('command-args').placeholder=usage||'Sem argumentos';$('args-label').hidden=!usage;$('modal').hidden=false;setTimeout(()=>$('command-args').focus(),0);
}
function dismissModal(){modalCommand=null;$('modal').hidden=true;}
function weaponModal(row){
  if(busy)return;
  modalWeapon=row;weaponTrigger=document.activeElement;$('weapon-title').textContent=row.name;$('weapon-model').textContent=row.model;
  $('weapon-ammo').value=ammo;$('weapon-modal').hidden=false;$('weapon-ammo').focus();$('weapon-ammo').select();
}
function dismissWeaponModal(){modalWeapon=null;$('weapon-modal').hidden=true;if(weaponTrigger?.isConnected)weaponTrigger.focus();weaponTrigger=null;}
$('weapon-form').addEventListener('submit',async e=>{
  e.preventDefault();if(!modalWeapon||busy)return;
  const value=$('weapon-ammo').value.trim(),quantity=Number(value);
  if(!value||!Number.isInteger(quantity)||quantity<0||quantity>9999){toast('Munição: informe um inteiro de 0 a 9999.',true);$('weapon-ammo').focus();return;}
  const selected=modalWeapon;ammo=quantity;const r=await act({action:'weapon',model:selected.model,ammo:quantity});
  if(r?.ok&&modalWeapon===selected)dismissWeaponModal();
});
$('weapon-cancel').addEventListener('click',dismissWeaponModal);
window.addEventListener('keydown',e=>{
  if(e.key!=='Tab'||$('weapon-modal').hidden)return;
  const controls=Array.from($('weapon-form').querySelectorAll('input,button')).filter(n=>!n.disabled);
  const index=controls.indexOf(document.activeElement);
  if((e.shiftKey&&index<=0)||(!e.shiftKey&&(index<0||index===controls.length-1))){e.preventDefault();controls[e.shiftKey?controls.length-1:0].focus();}
});
$('command-form').addEventListener('submit',async e=>{e.preventDefault();if(!modalCommand)return;const name=modalCommand.name,args=$('command-args').value.trim();if(!/^[a-zA-Z0-9_ .+\-]*$/.test(args)){toast('Use apenas argumentos de comando, sem separadores ou quebras de linha.',true);return;}const r=await act({action:'command',name,args});if(r?.ok)dismissModal();});
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>setTab(b.dataset.tab)));
for(const id of ['search','category','favorites-only'])$(id).addEventListener(id==='search'?'input':'change',()=>{page=1;render();});
$('previous').addEventListener('click',()=>{page--;render();$('content').scrollTop=0;});$('next').addEventListener('click',()=>{page++;render();$('content').scrollTop=0;});
$('close').addEventListener('click',()=>post('close'));$('modal-cancel').addEventListener('click',dismissModal);
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&!app.hidden){e.preventDefault();if(imageDialog?.open)imageDialog.close();else if(!$('weapon-modal').hidden)dismissWeaponModal();else if(!$('modal').hidden)dismissModal();else post('close');}});
window.addEventListener('message',event=>{
  const msg=event.data;if(!msg||typeof msg!=='object')return;
  if(msg.type==='open')open(msg.data);
  else if(msg.type==='close'){app.hidden=true;if(imageDialog?.open)imageDialog.close();dismissModal();dismissWeaponModal();}
  else if(msg.type==='npcs'){state.npcs=Array.isArray(msg.rows)?msg.rows:[];if(!app.hidden&&state.tab==='npcs')render();}
  else if(msg.type==='islandWorld'&&Array.isArray(msg.data?.objects)){state.island=msg.data;if(!app.hidden&&state.tab==='cayo'){renderActions();render();}}
  else if(msg.type==='capturedCatalog'&&Array.isArray(msg.objects)){
    capturedObjects=withCaptureImages(msg.objects);captureMarks=msg.marks||[];mergeCaptures();
    if(!app.hidden&&state.tab==='cayo'){const current=$('category').value;const source=state.catalog.cayo;const select=$('category');select.replaceChildren(new Option('Todas as categorias',''));[...new Set(source.map(x=>x.category))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(c=>select.add(new Option(c,c)));select.value=current;renderActions();render();}
  }
});
if(preview){document.body.classList.add('preview-scene');Promise.all([fetch('catalog.json').then(r=>r.json()),fetch('cayo.json').then(r=>r.json())]).then(([catalog,cayo])=>{catalog.cayo=cayo.objects;const active=new Set(['cidade_admin','cidade_acesso','cidade_core','cidade_roupas','cidade_acervo','teste_ilha','fpv_drone_runtime','cidade_west_texas']);open({name:'Administrador',id:1,catalog,commands:catalog.commands.map(x=>({...x,active:active.has(x.resource)})),players:[{id:1,name:'Administrador (exemplo)',bucket:0},{id:2,name:'Jogador (exemplo)',bucket:0}],npcs:[],tab:new URLSearchParams(location.search).get('tab')||'vehicles'});}).catch(()=>toast('Não foi possível carregar a prévia.',true));}
