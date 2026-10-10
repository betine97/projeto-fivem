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
};
let state = {tab:'vehicles',catalog:{vehicles:[],weapons:[],npcs:[]},commands:[],players:[],npcs:[],id:0,name:'ADM'};
let page=1, ammo=120, modalCommand=null, busy=false, toastTimer;
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
  $('account-name').textContent=state.name;$('account-id').textContent=`ID permanente ${state.id}`;
  for(const kind of ['vehicles','weapons','npcs'])$(`count-${kind}`).textContent=state.catalog[kind].length;
  $('preview-badge').hidden=!preview;app.hidden=false;setTab(data.tab||'vehicles');
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
    const label=el('label','ammo-label','Munição por arma');const input=el('input');input.type='number';input.min='0';input.max='9999';input.step='1';input.value=ammo;input.id='ammo';input.setAttribute('aria-label','Munição');input.addEventListener('input',()=>ammo=Number(input.value));label.append(input);actions.append(label,button('Remover minhas armas','secondary danger',()=>act({action:'disarm'})));
  }else if(kind==='players'){
    const input=el('input');input.id='target-id';input.type='number';input.min='1';input.step='1';input.placeholder='ID permanente';input.setAttribute('aria-label','ID permanente do jogador');
    actions.append(input,button('Localizar','primary',()=>idAction('localizar',input.value)),button('Ir até','secondary',()=>idAction('encontrar',input.value)),button('Trazer para perto','secondary',()=>idAction('chamar',input.value)),button('↻ Atualizar jogadores','secondary',()=>act({action:'players'})));
  }else{
    actions.append(button('Jogadores e IDs','secondary',()=>setTab('players')),button('Ver edição de objetos','secondary',()=>{$('search').value='objeto';page=1;render();}));
  }
}
function idAction(name,value){const id=Number(value);if(!Number.isSafeInteger(id)||id<1){toast('Use um ID permanente positivo.',true);return;}act({action:'command',name,args:String(id)});}
function matches(row){
  const q=$('search').value.trim().toLocaleLowerCase('pt-BR');const c=$('category').value;
  if(c&&row.category!==c)return false;
  if($('favorites-only').checked&&!['commands','players'].includes(state.tab)&&!favorites.has(`${state.tab}:${row.model}`))return false;
  return !q||[row.name,row.model,row.alias,row.description,row.usage,row.resource,row.id,row.category].filter(x=>x!==undefined).join(' ').toLocaleLowerCase('pt-BR').includes(q);
}
function card(row){
  const kind=state.tab, key=`${kind}:${row.model}`,c=el('article',`card ${kind==='npcs'?'npc':kind==='weapons'?'weapon':''}`);
  const favorite=button(favorites.has(key)?'★':'☆',`favorite ${favorites.has(key)?'saved':''}`,()=>{if(favorites.has(key))favorites.delete(key);else favorites.add(key);try{localStorage.setItem('cidadeAdminFavorites',JSON.stringify([...favorites]));}catch(_){}render();});favorite.setAttribute('aria-label',`Favoritar ${row.name}`);favorite.setAttribute('aria-pressed',String(favorites.has(key)));
  const media=el('div','thumbnail'),img=el('img');img.src=row.image||'fallback.svg';img.alt=row.name;img.loading='lazy';img.addEventListener('error',()=>{if(!img.src.endsWith('/fallback.svg'))img.src='fallback.svg';});media.append(img);
  const info=el('div','card-info');info.append(el('h3','',row.name),el('code','',row.model));const bottom=el('div','card-bottom');bottom.append(el('span','tag',row.category),button(kind==='weapons'?'Equipar ↗':'Criar ↗','primary spawn',()=>{if(kind==='weapons'&&(!Number.isInteger(ammo)||ammo<0||ammo>9999)){toast('Munição: inteiro de 0 a 9999.',true);return;}act({action:kind==='vehicles'?'vehicle':kind==='weapons'?'weapon':'npc',model:row.model,ammo:kind==='weapons'?ammo:undefined});}));info.append(bottom);c.append(favorite,media,info);return c;
}
function ownedNpcs(){
  const block=el('div','owned'),head=el('div','owned-header');head.append(el('strong','',`Seus NPCs no jogo · ${state.npcs.length}/12`),button('Remover todos','secondary danger',()=>act({action:'npcClear'})));block.append(head);
  if(!state.npcs.length)block.append(el('small','', 'Os personagens que você criar aparecem aqui. Você pode trazê-los de volta para perto.'));
  const list=el('div','owned-list');state.npcs.forEach(row=>{const item=el('div','owned-row');item.append(el('code','',row.model),button('Trazer','secondary',()=>act({action:'npcBring',id:row.id})),button('×','secondary danger',()=>act({action:'npcDelete',id:row.id})));list.append(item);});block.append(list);return block;
}
function render(){
  const content=$('content');content.replaceChildren();
  const original=state.tab==='commands'?state.commands:state.tab==='players'?state.players:state.catalog[state.tab]||[];
  const rows=original.filter(matches),pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages);
  const visible=rows.slice((page-1)*size,page*size);
  if(state.tab==='npcs')content.append(ownedNpcs());
  if(state.tab==='commands'){
    const info=el('div','info-box');info.append(el('strong','', 'Objetos: controles do editor existente'),el('div','', 'editarobjetos → CAPS pega/salva • ← → giram • Page Up/Down alteram a altura • HOME restaura a origem • Backspace cancela. O editor da mansão atua nos objetos definidos naquele recurso e salva para todos. Recursos desligados aparecem na lista com o botão desativado.'));content.append(info);
    content.append(commandTable(visible));
  }else if(state.tab==='players')content.append(playerTable(visible));
  else{const grid=el('div','grid');visible.forEach(row=>grid.append(card(row)));content.append(grid);}
  if(!rows.length)content.append(el('div','empty',state.tab==='players'?'Nenhum jogador encontrado. Atualize a lista ou use o ID permanente acima.':'Nenhum resultado. Tente outro nome, modelo ou categoria.'));
  $('result-count').textContent=`${rows.length} ${state.tab==='commands'?'comandos':state.tab==='players'?'jogadores':'modelos'}${preview?' · prévia do catálogo':' · disponíveis nesta sessão'}`;
  if(state.tab==='commands')$('result-count').textContent=`${rows.length} comandos · ${rows.filter(x=>x.active).length} ativos`;
  $('page-label').textContent=`${page} / ${pages}`;$('previous').disabled=page<=1;$('next').disabled=page>=pages;
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
$('command-form').addEventListener('submit',async e=>{e.preventDefault();if(!modalCommand)return;const name=modalCommand.name,args=$('command-args').value.trim();if(!/^[a-zA-Z0-9_ .+\-]*$/.test(args)){toast('Use apenas argumentos de comando, sem separadores ou quebras de linha.',true);return;}const r=await act({action:'command',name,args});if(r?.ok)dismissModal();});
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>setTab(b.dataset.tab)));
for(const id of ['search','category','favorites-only'])$(id).addEventListener(id==='search'?'input':'change',()=>{page=1;render();});
$('previous').addEventListener('click',()=>{page--;render();$('content').scrollTop=0;});$('next').addEventListener('click',()=>{page++;render();$('content').scrollTop=0;});
$('close').addEventListener('click',()=>post('close'));$('modal-cancel').addEventListener('click',dismissModal);
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&!app.hidden){e.preventDefault();if(!$('modal').hidden)dismissModal();else post('close');}});
window.addEventListener('message',event=>{
  const msg=event.data;if(!msg||typeof msg!=='object')return;
  if(msg.type==='open')open(msg.data);
  else if(msg.type==='close'){app.hidden=true;dismissModal();}
  else if(msg.type==='npcs'){state.npcs=Array.isArray(msg.rows)?msg.rows:[];if(!app.hidden&&state.tab==='npcs')render();}
});
if(preview){document.body.classList.add('preview-scene');fetch('catalog.json').then(r=>r.json()).then(catalog=>{const active=new Set(['cidade_admin','cidade_acesso','cidade_core','cidade_roupas','cidade_acervo','teste_ilha','fpv_drone_runtime','cidade_west_texas']);open({name:'Administrador',id:1,catalog,commands:catalog.commands.map(x=>({...x,active:active.has(x.resource)})),players:[{id:1,name:'Administrador (exemplo)',bucket:0},{id:2,name:'Jogador (exemplo)',bucket:0}],npcs:[]});}).catch(()=>toast('Não foi possível carregar a prévia.',true));}
