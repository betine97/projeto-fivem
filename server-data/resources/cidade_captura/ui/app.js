'use strict';
const $=id=>document.getElementById(id);let busy=false,selected=false,lastMove=0,timer;
async function post(action,data={}){try{const r=await fetch(`https://${GetParentResourceName()}/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});return await r.json();}catch{return {ok:false,message:'Não foi possível conversar com o jogo.'};}}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(timer);timer=setTimeout(()=>$('toast').hidden=true,6500);}
function clear(){selected=false;$('selection').hidden=true;$('name').value='';}
window.addEventListener('message',event=>{const m=event.data;if(!m)return;
 if(m.type==='open'){$('app').hidden=false;clear();$('toast').hidden=true;}
 if(m.type==='close'){$('app').hidden=true;clear();}
 if(m.type==='clear')clear();
 if(m.type==='hover'&&!selected)$('hint').textContent=m.object?'Objeto localizado. Clique para dar um nome e adicionar ao catálogo.':m.hit?'Este trecho pode ser uma peça agrupada do mapa. Clique para marcar para análise.':'Aponte para um objeto a até 250 metros.';
 if(m.type==='selection'){const r=m.data;if(!r.ok){toast(r.message);return;}selected=true;const d=r.data;$('selection').hidden=false;$('title').textContent=d.name;$('name').value=d.name;$('details').textContent=d.details;$('category').value=d.category||'Objetos de Los Santos';$('save').textContent=d.kind==='surface'?'Marcar trecho para análise':'Adicionar ao catálogo da ilha';}
});
window.addEventListener('mousemove',e=>{if($('app').hidden||selected||Date.now()-lastMove<60)return;lastMove=Date.now();post('cursor',{x:e.clientX/innerWidth,y:e.clientY/innerHeight});});
window.addEventListener('click',async e=>{if($('app').hidden||selected||busy||e.target.closest('button,input,select,section'))return;busy=true;const r=await post('pick');busy=false;if(!r.ok)toast(r.message);});
$('close').addEventListener('click',()=>post('close'));
$('again').addEventListener('click',()=>post('again'));
$('save').addEventListener('click',async()=>{if(busy)return;busy=true;$('save').disabled=true;const r=await post('save',{name:$('name').value,category:$('category').value});busy=false;$('save').disabled=false;if(r.message)toast(r.message);});
window.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();post('close');}});
