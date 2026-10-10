const $ = id => document.getElementById(id);
let csrf = '', filter = 'all', users = [], sequence = 0, renameId = null, timer;
const busy = new Set();
const labels = {pending:'Aguardando', approved:'Autorizado', blocked:'Bloqueado'};
function loginView(){ $('dashboard').hidden = true; $('login').hidden = false; csrf = ''; }
function dashboardView(){ $('login').hidden = true; $('dashboard').hidden = false; }
async function api(path, body){
 const response = await fetch(path, {headers: body ? {'Content-Type':'application/json','X-CSRF-Token':csrf} : {}, method:body?'POST':'GET', body:body?JSON.stringify(body):undefined});
 const data = await response.json();
 if(!response.ok){ if(response.status===401 && path!=='/api/login') loginView(); throw new Error(data.error || 'Não foi possível concluir.'); }
 return data;
}
function notify(message){ $('toast').textContent = message; $('toast').hidden = false; clearTimeout(timer); timer = setTimeout(()=> $('toast').hidden=true,3500); }
function error(message){ $('error').textContent = message; $('error').hidden = !message; }
function element(tag, text, className){ const e=document.createElement(tag); if(text!==undefined)e.textContent=text; if(className)e.className=className; return e; }
function action(user,text,status,cls){const button=element('button',text,'row-action '+cls);button.disabled=busy.has(user.id);button.addEventListener('click',()=>change(user.id,{status}));return button;}
function render(data){
 users=data.users; $('rows').replaceChildren();
 for(const user of users){
  const row=element('tr'); row.append(element('td','#'+String(user.id).padStart(3,'0'),'id'));
  const name=element('td'), cell=element('div',undefined,'player-cell'), avatar=element('div',user.name.slice(0,2).toUpperCase(),'avatar'), title=element('div',user.name,'player-name');
  if(user.online)title.append(element('small','● Online agora'));
  cell.append(avatar,title);name.append(cell);row.append(name);
  const status=element('td');status.append(element('span',labels[user.status],'pill '+user.status));row.append(status);
  const actions=element('td');
  if(user.status!=='approved')actions.append(action(user,'Autorizar','approved','allow'));
  if(user.status!=='blocked')actions.append(action(user,'Bloquear','blocked','block'));
  const rename=element('button','Renomear','row-action');rename.addEventListener('click',()=>{renameId=user.id;$('new-name').value=user.name;$('rename-error').textContent='';$('rename').showModal();});actions.append(rename);row.append(actions);$('rows').append(row);
 }
 for(const key of ['total','pending','approved','blocked'])$(key).textContent=data.counts[key];
 $('nav-count').textContent=data.counts.total;
 $('empty').hidden=users.length>0;
 $('result-count').textContent=users.length+' '+(users.length===1?'jogador':'jogadores');
 if(data.counts.total && !users.length){ $('empty').querySelector('h2').textContent='Nenhum jogador encontrado.'; $('empty').querySelector('p').textContent='Tente outro nome, ID ou filtro.'; }
 else if(!data.counts.total){ $('empty').querySelector('h2').textContent='O próximo convite começa aqui.'; $('empty').querySelector('p').textContent='Quando alguém tentar conectar, o nome e o ID aparecerão aqui. Autorize a entrada e peça para conectar novamente.'; }
}
async function refresh(){
 if(!csrf)return;
 const current=++sequence;
 try{
  const [data,status]=await Promise.all([api('/api/users?'+new URLSearchParams({q:$('search').value,status:filter})),api('/api/status')]);
  if(current!==sequence)return; render(data);error('');
  $('server-pill').className='pill '+(status.connected?'approved':'pending');$('server-pill').textContent=status.connected?'Conectado ao painel':'Aguardando conexão';
  $('server-help').textContent=status.connected?'Controle de acesso ativo. Novos jogadores precisam da sua aprovação.':'Reinicie a base para carregar o controle de acesso. Mantenha este painel em execução antes de iniciar o servidor.';
  const address=status.addresses.vpn||status.addresses.lan;
  $('vpn-command').textContent=address?'connect '+address:'Endereço ainda não configurado';
  $('copy').disabled=!address;
  $('lan-command').textContent=status.addresses.lan?'connect '+status.addresses.lan:'Endereço ainda não configurado';
  $('city-link').hidden=!status.addresses.city;
  if(status.addresses.city)$('city-command').textContent='connect '+status.addresses.city;
 }catch(e){if(current===sequence)error(e.message);}
}
async function change(id, body){
 if(busy.has(id))return;busy.add(id);
 try{await api('/api/users/'+id,body);notify(body.status==='approved'?'Entrada autorizada. O jogador já pode conectar.':body.status==='blocked'?'Acesso bloqueado.':'Nome atualizado.');await refresh();return true;}
 catch(e){error(e.message);return false;}
 finally{busy.delete(id);}
}
$('login-form').addEventListener('submit',async e=>{e.preventDefault();try{const session=await api('/api/login',{password:$('password').value});csrf=session.csrf;$('password').value='';dashboardView();await refresh();}catch(e){$('login-error').textContent=e.message;}});
$('refresh').addEventListener('click',refresh);
let searchTimer;$('search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(refresh,180);});
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{filter=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('selected',b===button));refresh();}));
$('cancel-rename').addEventListener('click',()=> $('rename').close());
$('rename-form').addEventListener('submit',async e=>{e.preventDefault();if(!$('new-name').value.trim())return;const ok=await change(renameId,{name:$('new-name').value});if(ok)$('rename').close();else $('rename-error').textContent='Não foi possível salvar. Tente novamente.';});
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('vpn-command').textContent);notify('Comando copiado. Envie para seus amigos usando o endereço do servidor.');}catch(e){notify('Copie o comando exibido acima.');}});
$('logout').addEventListener('click',async()=>{try{await api('/api/logout',{});loginView();}catch(e){error(e.message);}});
api('/api/session').then(session=>{csrf=session.csrf;dashboardView();refresh();}).catch(loginView);
setInterval(()=>{if(!document.hidden)refresh();},5000);
