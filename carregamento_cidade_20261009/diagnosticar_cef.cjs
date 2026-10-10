// Read-only inspection of FiveM's local CEF debugger. Never sends input or spawn commands.
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const targets = await (await fetch('http://localhost:13172/json/list')).json();
  const result = [];
  for (const target of targets.filter(t => t.type === 'page')) {
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    const pending = new Map(), contexts = new Map();
    let sequence = 0;
    ws.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.method === 'Runtime.executionContextCreated') contexts.set(message.params.context.id, message.params.context);
      if (message.method === 'Runtime.executionContextDestroyed') contexts.delete(message.params.executionContextId);
      if (pending.has(message.id)) {
        const {resolve, reject, timer} = pending.get(message.id);
        pending.delete(message.id); clearTimeout(timer);
        message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
      }
    });
    await new Promise((resolve,reject) => { ws.addEventListener('open', resolve, {once:true}); ws.addEventListener('error', reject, {once:true}); });
    const send = (method, params = {}) => new Promise((resolve,reject) => {
      const id = ++sequence;
      const timer = setTimeout(() => {pending.delete(id); reject(new Error('CDP timeout'));},5000);
      pending.set(id,{resolve,reject,timer}); ws.send(JSON.stringify({id,method,params}));
    });
    try {
      await send('Runtime.enable');
      const tree = await send('Page.getFrameTree');
      result.push({target:target.url,tree});
      for (const context of contexts.values()) {
        const expression = `JSON.stringify({url:location.href,resource:typeof GetParentResourceName==='function'?GetParentResourceName():null,focus:document.hasFocus(),active:document.activeElement?.tagName,pointer:getComputedStyle(document.body).pointerEvents,frames:Array.from(document.querySelectorAll('iframe')).map(x=>({name:x.name,src:x.src,style:x.getAttribute('style'),display:getComputedStyle(x).display,zIndex:getComputedStyle(x).zIndex,pointer:getComputedStyle(x).pointerEvents})),loading:document.querySelector('#advance')?{disabled:document.querySelector('#advance').disabled,detail:document.querySelector('#status-detail')?.textContent,audioPaused:document.querySelector('#music')?.paused,advanceTarget:document.elementFromPoint(innerWidth-200,innerHeight-130)?.id,playTarget:document.elementFromPoint(165,innerHeight-102)?.id}:null})`;
        const evaluated = await send('Runtime.evaluate',{contextId:context.id,expression,returnByValue:true});
        result.push({context,inspection:evaluated.result?.value,exception:evaluated.exceptionDetails?.text});
        const styles = await send('Runtime.evaluate',{contextId:context.id,returnByValue:true,expression:"JSON.stringify({url:location.href,htmlClass:document.documentElement.className,bodyClass:document.body.className,meta:document.querySelector('meta[name=color-scheme]')?.content,html:{background:getComputedStyle(document.documentElement).backgroundColor,colorScheme:getComputedStyle(document.documentElement).colorScheme,visibility:getComputedStyle(document.documentElement).visibility,opacity:getComputedStyle(document.documentElement).opacity},body:{background:getComputedStyle(document.body).backgroundColor,colorScheme:getComputedStyle(document.body).colorScheme,visibility:getComputedStyle(document.body).visibility,opacity:getComputedStyle(document.body).opacity}})"});
        result.push({styles:styles.result?.value});
        if (evaluated.result?.value && JSON.parse(evaluated.result.value).loading) {
          const status = await send('Runtime.evaluate',{contextId:context.id,expression:"fetch('https://cidade_loading/loadingStatus',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json()).then(s=>JSON.stringify(s))",returnByValue:true,awaitPromise:true});
          result.push({loadingStatus:status.result?.value,exception:status.exceptionDetails?.text});
        }
      }
    } finally { ws.close(); }
  }
  fs.mkdirSync(path.join(__dirname,'verificacao'),{recursive:true});
  fs.writeFileSync(path.join(__dirname,'verificacao/cef-diagnostico.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result.filter(item=>item.inspection||item.styles||item.loadingStatus),null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
