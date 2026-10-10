const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('../.downloads/hud-preview/node_modules/playwright');
const root = path.resolve(__dirname, '../server-data/resources/cidade_loading/web');
const output = path.join(__dirname, 'verificacao');
const cases = [];
const mime = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.json':'application/json', '.png':'image/png', '.mp3':'audio/mpeg' };
const server = http.createServer((req, res) => {
  const file = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
  if (!file.startsWith(root + path.sep) && file !== root) { res.writeHead(403); res.end(); return; }
  const resolved = file === root ? path.join(root, 'index.html') : file;
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[path.extname(resolved)] || 'application/octet-stream');
  res.setHeader('Accept-Ranges', 'bytes');
  const size = fs.statSync(resolved).size;
  const range = /bytes=(\d+)-(\d*)/.exec(req.headers.range || '');
  if (range) {
    const start = Number(range[1]); const end = range[2] ? Math.min(size - 1, Number(range[2])) : size - 1;
    res.writeHead(206, { 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': end - start + 1 });
    fs.createReadStream(resolved, {start,end}).pipe(res);
  } else { res.setHeader('Content-Length',size); fs.createReadStream(resolved).pipe(res); }
});
(async () => {
  fs.mkdirSync(output,{recursive:true});
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  const executablePath = ['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(file=>fs.existsSync(file));
  const browser = await chromium.launch({executablePath,headless:true, args:['--autoplay-policy=no-user-gesture-required']});
  try {
    const page = await browser.newPage({viewport:{width:1672,height:941}});
    const errors = []; page.on('pageerror',err => errors.push(String(err)));
    const bridge = {holding:true,ready:false,failed:false,detail:'Carregando o mundo e preparando seu personagem.'};
    const requests = [];
    // The real CEF loadscreen reports this special frame name, not cidade_loading.
    await page.addInitScript(() => { window.GetParentResourceName = () => 'loadingScreen'; });
    await page.route('https://cidade_loading/**', async route => {
      const command = new URL(route.request().url()).pathname.slice(1); requests.push(command);
      const result = command === 'loadingStatus' ? bridge : {ok:bridge.ready};
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(result)});
    });
    await page.goto(url);
    await page.waitForFunction(() => document.getElementById('music').duration > 0);
    await page.waitForFunction(() => document.getElementById('status-detail').textContent === 'Carregando o mundo e preparando seu personagem.');
    assert(requests.includes('loadingStatus'));
    cases.push('frame loadingScreen encaminha callbacks ao recurso cidade_loading');
    assert(await page.locator('#advance').isDisabled());
    await page.evaluate(() => window.dispatchEvent(new MessageEvent('message',{data:{eventName:'loadProgress',loadFraction:1}})));
    assert(await page.locator('#advance').isDisabled());
    assert.equal(await page.locator('#progress-text').textContent(),'95%');
    assert(!requests.includes('loadingAdvance'));
    cases.push('100% do motor não libera nem avança o personagem');
    await page.screenshot({path:path.join(output,'carregando.png')});

    const tracks = [];
    for (let i=0;i<3;i++) {
      if(i) await page.locator('#next').click();
      await page.waitForFunction(() => document.getElementById('music').readyState >= 2 && document.getElementById('music').duration > 0);
      const audio = await page.evaluate(() => {const a=document.getElementById('music');return {duration:a.duration,paused:a.paused,error:a.error?.code || null,src:a.currentSrc};});
      assert(!audio.error); assert(!audio.paused); tracks.push(audio);
    }
    assert.equal(new Set(tracks.map(a=>a.src)).size,3);
    await page.locator('#next').click();
    assert.match(await page.locator('#track-count').textContent(),/^01/);
    cases.push('três MP3 decodificam, tocam e a playlist volta à primeira faixa');
    await page.evaluate(() => document.getElementById('music').dispatchEvent(new Event('ended')));
    assert.match(await page.locator('#track-count').textContent(),/^02/);
    cases.push('fim de música seleciona automaticamente a próxima');
    await page.locator('#mute').click();
    assert.equal(await page.evaluate(() => document.getElementById('music').muted),true);
    await page.locator('#volume').fill('67');
    assert.equal(await page.locator('#volume-value').textContent(),'67%');
    assert.equal(await page.evaluate(() => document.getElementById('music').muted),false);
    await page.locator('#volume').fill('0'); await page.locator('#mute').click();
    assert.equal(await page.evaluate(() => {const a=document.getElementById('music');return !a.muted&&a.volume>0;}),true);
    await page.waitForFunction(() => !document.getElementById('music').paused);
    await page.locator('#play').click();
    assert.equal(await page.evaluate(() => document.getElementById('music').paused),true);
    await page.locator('#play').click();
    await page.waitForFunction(() => !document.getElementById('music').paused);
    cases.push('silêncio, volume zero/restauração, pausa e reprodução');
    await page.locator('#playlist-toggle').click();
    assert.equal(await page.locator('#playlist button').count(),3);
    await page.locator('#playlist button').nth(2).click();
    assert.match(await page.locator('#track-count').textContent(),/^03/);
    await page.locator('#playlist-toggle').click();
    cases.push('seleção direta da playlist');

    Object.assign(bridge,{failed:true,detail:'Tente carregar novamente.'});
    await page.evaluate(state => window.dispatchEvent(new MessageEvent('message',{data:{eventName:'cidadeLoadingState',state}})),bridge);
    assert(await page.locator('#retry').isVisible()); assert(await page.locator('#advance').isDisabled());
    cases.push('falha mantém a tela e oferece nova tentativa');
    for (const invalid of [{ready:0,holding:1},{ready:1,holding:0},{ready:'true',holding:true}]) {
      await page.evaluate(state => window.dispatchEvent(new MessageEvent('message',{data:{eventName:'cidadeLoadingState',state}})),invalid);
      assert(await page.locator('#advance').isDisabled());
    }
    Object.assign(bridge,{ready:1,holding:1,failed:0,entering:0,detail:'Tudo pronto. Clique abaixo para assumir seu personagem.'});
    await page.evaluate(state => window.dispatchEvent(new MessageEvent('message',{data:{eventName:'cidadeLoadingState',state}})),bridge);
    assert(await page.locator('#advance').isEnabled());
    assert.equal(await page.locator('#status-title').textContent(),'Tudo pronto.');
    assert.equal(await page.locator('#progress-text').textContent(),'100%');
    await page.waitForTimeout(300);
    await page.screenshot({path:path.join(output,'pronto.png')});
    await page.waitForTimeout(1500);
    assert(!requests.includes('loadingAdvance'));
    assert.equal(await page.evaluate(() => document.body.classList.contains('entering')),false);
    cases.push('flags numéricas 1/0 liberam pronto e esperam o clique; zero/string não liberam');

    await page.setViewportSize({width:1280,height:720});
    assert.equal(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight),true);
    await page.screenshot({path:path.join(output,'pronto-720p.png')});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),true);
    await page.screenshot({path:path.join(output,'pronto-mobile.png'),fullPage:true});
    cases.push('layout 1080p/720p e tela estreita sem cortar controles');
    await page.setViewportSize({width:1672,height:941});
    await page.locator('#advance').click();
    await page.waitForFunction(() => document.body.classList.contains('entering'));
    await page.waitForTimeout(600);
    assert.equal(requests.filter(x=>x==='loadingAdvance').length,1);
    assert.equal(await page.evaluate(() => document.getElementById('music').paused),true);
    assert.equal(errors.length,0, errors.join('\n'));
    cases.push('clique envia uma confirmação e encerra música com fade');

    // Reproduce the actual CEF stack: the original loading frame, a hidden regular
    // UI, then another transparent full-screen resource that intercepts input.
    const stack = await browser.newPage({viewport:{width:1672,height:941}});
    stack.on('pageerror',err=>errors.push(String(err)));
    await stack.addInitScript(() => {
      window.GetParentResourceName = () => new URLSearchParams(location.search).has('interactive') ? 'cidade_loading' : 'loadingScreen';
    });
    const handoffRequests = [];
    let handoffPayload;
    const readyState = {holding:true,ready:1,failed:0,entering:0,detail:'Tudo pronto.'};
    await stack.route('https://cidade_loading/**',async route => {
      const command = new URL(route.request().url()).pathname.slice(1);
      handoffRequests.push(command);
      const payload = route.request().postDataJSON();
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(command==='loadingStatus'?readyState:{ok:true})});
      if (command==='loadingHandoff') {
        handoffPayload=payload;
        await stack.evaluate(data=>document.getElementById('interactive').contentWindow.postMessage(data,'*'),{eventName:'cidadeLoadingActivate',state:readyState,...payload});
      }
      if (command==='loadingUiActive') {
        await stack.evaluate(() => {
          document.getElementById('original').remove();
          const frame=document.getElementById('interactive');frame.style.zIndex='99999';frame.contentWindow.focus();
        });
      }
    });
    await stack.setContent(`<style>html,body{margin:0;background:rgb(238,0,238)}iframe{position:absolute;inset:0;width:100%;height:100%;border:0}</style><iframe id="original" src="${url}"></iframe><iframe id="interactive" src="${url}/?interactive=1"></iframe><iframe id="other-resource" srcdoc="<body style='margin:0;background:transparent'></body>"></iframe>`);
    const original=stack.frames().find(f=>f.url()===url+'/');
    const regular=stack.frames().find(f=>f.url().includes('interactive=1'));
    await regular.waitForFunction(()=>document.querySelectorAll('#playlist button').length===3);
    await original.waitForFunction(()=>document.getElementById('music').duration>0);
    assert.equal(await regular.evaluate(()=>document.getElementById('music').paused),true);
    assert.equal(await regular.evaluate(()=>getComputedStyle(document.body).visibility),'hidden');
    assert.equal(await regular.evaluate(()=>getComputedStyle(document.documentElement).backgroundColor),'rgba(0, 0, 0, 0)');
    assert.equal(await regular.evaluate(()=>getComputedStyle(document.documentElement).colorScheme),'normal');
    assert.equal(await stack.evaluate(()=>document.elementFromPoint(160,840).id),'other-resource');
    cases.push('interface normal começa transparente e silenciosa; reproduz sobreposição que roubava cliques');
    await original.evaluate(() => document.getElementById('next').click());
    await original.waitForFunction(()=>document.getElementById('music').readyState>=2);
    await original.evaluate(() => {
      const a=document.getElementById('music');a.pause();a.currentTime=12.75;a.volume=.67;a.muted=true;
      window.postMessage({eventName:'cidadeLoadingHandoff'},'*');
    });
    await regular.waitForFunction(()=>document.documentElement.classList.contains('active'));
    await regular.waitForFunction(()=>document.getElementById('music').currentTime>=12.7);
    await stack.waitForFunction(()=>!document.getElementById('original'));
    assert.equal(handoffPayload.audio.index,1);
    const restored=await regular.evaluate(()=>{const a=document.getElementById('music');return{paused:a.paused,volume:a.volume,muted:a.muted,time:a.currentTime};});
    assert(restored.paused&&restored.muted);assert.equal(restored.volume,.67);assert(Math.abs(restored.time-12.75)<.1);
    assert.equal(await stack.evaluate(()=>document.elementFromPoint(160,840).id),'interactive');
    assert(await regular.locator('#advance').isEnabled());
    assert.equal(await stack.evaluate(()=>document.querySelectorAll('iframe').length),2);
    cases.push('transferência preserva faixa, posição, volume, silêncio e pausa; foco fica acima de outros recursos');
    await regular.locator('#play').click();
    await regular.waitForFunction(()=>!document.getElementById('music').paused);
    await regular.locator('#play').click();
    assert.equal(await regular.evaluate(()=>document.getElementById('music').paused),true);
    await regular.locator('#next').click();
    assert.match(await regular.locator('#track-count').textContent(),/^03/);
    await regular.locator('#previous').click();
    assert.match(await regular.locator('#track-count').textContent(),/^02/);
    await regular.locator('#playlist-toggle').click();
    await regular.locator('#playlist button').nth(0).click();
    assert.match(await regular.locator('#track-count').textContent(),/^01/);
    await regular.locator('#playlist-toggle').click();
    await regular.locator('#advance').click();
    await regular.waitForFunction(()=>document.body.classList.contains('entering'));
    await regular.waitForFunction(()=>document.getElementById('music').paused);
    assert.equal(handoffRequests.filter(x=>x==='loadingAdvance').length,1);
    await regular.evaluate(()=>window.postMessage({eventName:'cidadeLoadingClose'},'*'));
    await regular.waitForFunction(()=>!document.documentElement.classList.contains('active'));
    assert.equal(await regular.evaluate(()=>getComputedStyle(document.documentElement).backgroundColor),'rgba(0, 0, 0, 0)');
    assert.equal(await regular.evaluate(()=>getComputedStyle(document.body).visibility),'hidden');
    cases.push('com outras interfaces abertas, cliques pausam/trocam músicas e confirmam entrada; saída fica transparente');
    await stack.close();
    assert.equal(errors.length,0,errors.join('\n'));
    fs.writeFileSync(path.join(output,'ui.json'), JSON.stringify({passed:true,cases,tracks,errors,in_game_verified:false},null,2));
    console.log('UI_PASS',cases.length,'MP3',tracks.map(a=>Math.round(a.duration)).join(','));
  } finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
})().catch(error => { console.error(error); server.close(); process.exitCode=1; });
