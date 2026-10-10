// Apply only the transparency correction to the already-loaded cidade_loading DOM.
// No spawn, game commands, server restart, or focus-stack mutation.
const fs = require('node:fs');
const path = require('node:path');
(async()=>{
  const targets=await(await fetch('http://localhost:13172/json/list')).json();
  const target=targets.find(t=>t.url==='nui://game/ui/root.html');
  if(!target)throw new Error('Root CEF não encontrado');
  const ws=new WebSocket(target.webSocketDebuggerUrl),pending=new Map(),contexts=[];
  let id=0;
  ws.addEventListener('message',event=>{
    const message=JSON.parse(event.data);
    if(message.method==='Runtime.executionContextCreated')contexts.push(message.params.context.id);
    if(pending.has(message.id)){const p=pending.get(message.id);pending.delete(message.id);clearTimeout(p.timer);message.error?p.reject(new Error(JSON.stringify(message.error))):p.resolve(message.result);}
  });
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  const send=(method,params={})=>new Promise((resolve,reject)=>{const request=++id;const timer=setTimeout(()=>reject(new Error('CDP timeout')),5000);pending.set(request,{resolve,reject,timer});ws.send(JSON.stringify({id:request,method,params}));});
  const evidence=[];
  try{
    await send('Runtime.enable');
    for(const contextId of contexts){
      const check=await send('Runtime.evaluate',{contextId,expression:'location.href',returnByValue:true});
      if(!check.result?.value?.startsWith('https://cfx-nui-cidade_loading/web/'))continue;
      const result=await send('Runtime.evaluate',{contextId,returnByValue:true,expression:`(()=>{
        const meta=document.querySelector('meta[name="color-scheme"]');
        const before={meta:meta?.content,htmlClass:document.documentElement.className,bodyClass:document.body.className};
        if(!document.documentElement.classList.contains('interactive')||document.documentElement.classList.contains('active'))throw new Error('A tela de carregamento ainda está visível; não será ocultada');
        if(meta)meta.content='normal';
        document.documentElement.style.setProperty('color-scheme','normal','important');
        document.documentElement.style.setProperty('background','transparent','important');
        document.body.style.setProperty('color-scheme','normal','important');
        document.body.style.setProperty('background','transparent','important');
        console.info('[Entrada NUI] transparência da sessão corrigida',JSON.stringify(before));
        return JSON.stringify({before,after:{meta:meta?.content,scheme:getComputedStyle(document.documentElement).colorScheme,background:getComputedStyle(document.documentElement).backgroundColor}});
      })()`});
      evidence.push(result);if(result.exceptionDetails)throw new Error(result.exceptionDetails.text);
    }
  }finally{ws.close();}
  if(!evidence.length)throw new Error('Frame oculto cidade_loading não encontrado');
  fs.writeFileSync(path.join(__dirname,'verificacao/cef-transparencia-sessao.json'),JSON.stringify(evidence,null,2));
  console.log(JSON.stringify(evidence,null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
