const overlay=document.getElementById('overlay');
const start=document.getElementById('start');
const frame=document.getElementById('browser');
const address=document.getElementById('address');
const status=document.getElementById('status');
const back=document.getElementById('back');
const forward=document.getElementById('forward');
const historyStack=[];
let historyIndex=-1;

function normalizeInput(raw){
  const value=raw.trim();
  if(!value)return null;
  const candidate=/^https?:\/\//i.test(value)?value:(value.includes(' ')||!value.includes('.'))
    ?`https://www.bing.com/search?q=${encodeURIComponent(value)}`:`https://${value}`;
  try{
    const url=new URL(candidate);
    return (url.protocol==='https:'||url.protocol==='http:')?url.href:null;
  }catch{return null;}
}
function updateButtons(){
  back.disabled=historyIndex<0;
  forward.disabled=historyIndex>=historyStack.length-1;
}
function navigate(raw,push=true){
  const url=normalizeInput(raw);
  if(!url){status.textContent='Endereço inválido';return;}
  if(push){historyStack.splice(historyIndex+1);historyStack.push(url);historyIndex=historyStack.length-1;}
  address.value=url;
  start.hidden=true;
  frame.hidden=false;
  frame.src=url;
  status.textContent='Carregando…';
  updateButtons();
}
function showHome(){
  frame.removeAttribute('src');frame.hidden=true;start.hidden=false;address.value='';
  status.textContent='Pronto para navegar';
}
async function closeTablet(){
  overlay.classList.add('hidden');overlay.setAttribute('aria-hidden','true');
  showHome();historyStack.length=0;historyIndex=-1;updateButtons();
  if(typeof GetParentResourceName==='function'){
    try{await fetch(`https://${GetParentResourceName()}/close`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});}catch{}
  }
}
document.getElementById('address-form').addEventListener('submit',event=>{event.preventDefault();navigate(address.value);});
document.getElementById('close').addEventListener('click',closeTablet);
document.getElementById('home').addEventListener('click',showHome);
document.getElementById('reload').addEventListener('click',()=>{if(!frame.hidden)frame.src=frame.src;});
back.addEventListener('click',()=>{if(historyIndex>0)navigate(historyStack[--historyIndex],false);});
forward.addEventListener('click',()=>{if(historyIndex<historyStack.length-1)navigate(historyStack[++historyIndex],false);});
document.querySelectorAll('[data-url]').forEach(button=>button.addEventListener('click',()=>navigate(button.dataset.url)));
frame.addEventListener('load',()=>{status.textContent='Página solicitada — alguns sites podem bloquear exibição no jogo';});
window.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();closeTablet();}});
window.addEventListener('message',event=>{
  if(event.data?.action==='open'){
    overlay.classList.remove('hidden');overlay.setAttribute('aria-hidden','false');
    showHome();address.focus();
  }else if(event.data?.action==='close'){
    overlay.classList.add('hidden');overlay.setAttribute('aria-hidden','true');showHome();
  }
});
updateButtons();
const previewParams=new URLSearchParams(location.search);
if(previewParams.has('preview')){
  overlay.classList.remove('hidden');overlay.setAttribute('aria-hidden','false');
  if(previewParams.has('url'))navigate(previewParams.get('url'));
}
