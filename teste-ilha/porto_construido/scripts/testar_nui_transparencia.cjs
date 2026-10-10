// Render the real closed/open ADM document over a visible scene, as NUI frames do.
const fs=require('fs'),path=require('path'),http=require('http');
const {chromium}=require('C:/Users/erons/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../..'),ui=path.join(root,'server-data/resources/cidade_admin/ui');
const out=path.join(__dirname,'../dados'),backup=path.join(__dirname,'../backups/correcao_nui_20261009/cidade_admin_style.css');
const checks=[];function check(v,n){if(!v)throw Error(n);checks.push(n)}
(async()=>{
 const server=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');
  if(url.pathname==='/scene'){
   res.setHeader('Content-Type','text/html');
   res.end(`<style>html,body{margin:0;background:#ee00ee}iframe{position:fixed;inset:0;border:0;width:100%;height:100%}</style><iframe src="/index.html${url.search}"></iframe>`);return;
  }
  let file=path.resolve(ui,'.'+decodeURIComponent(url.pathname));
  if(!file.startsWith(ui+path.sep)){res.writeHead(403);res.end();return}
  if(url.pathname==='/style.css'&&(req.headers.referer||'').includes('old=1'))file=backup;
  if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return}
  res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.png':'image/png','.svg':'image/svg+xml'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:1600,height:900}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>window.GetParentResourceName=()=> 'cidade_admin');
  const base='http://127.0.0.1:'+server.address().port;
  await page.goto(base+'/scene?old=1');
  let frame=page.frames().find(f=>f.url().includes('index.html'));
  await frame.locator('#app').waitFor({state:'hidden'});
  check(await frame.evaluate(()=>getComputedStyle(document.documentElement).colorScheme)==='dark','original dark document reproduced');
  await page.screenshot({path:path.join(out,'nui_adm_antes.png')});
  await page.goto(base+'/scene');frame=page.frames().find(f=>f.url().includes('index.html'));
  await frame.locator('#app').waitFor({state:'hidden'});
  check(await frame.evaluate(()=>getComputedStyle(document.documentElement).colorScheme)==='normal','document no longer forces a dark canvas');
  await page.screenshot({path:path.join(out,'nui_adm_depois.png')});
  const catalog=JSON.parse(fs.readFileSync(path.join(ui,'catalog.json'),'utf8'));
  await frame.evaluate(c=>window.postMessage({type:'open',data:{name:'Teste',id:1,catalog:c,commands:[],players:[],npcs:[]}},'*'),catalog);
  await frame.locator('.card').first().waitFor();
  check(await frame.locator('#app').isVisible(),'ADM opens normally');
  check(await frame.locator('#app').evaluate(e=>getComputedStyle(e).colorScheme)==='dark','ADM controls retain dark appearance');
  await page.screenshot({path:path.join(out,'nui_adm_aberto.png')});
  await frame.evaluate(()=>window.postMessage({type:'close'},'*'));
  await frame.locator('#app').waitFor({state:'hidden'});
  await page.screenshot({path:path.join(out,'nui_adm_fechado.png')});
  check(errors.length===0,'no page errors');
  fs.writeFileSync(path.join(out,'teste_nui_transparencia.json'),JSON.stringify({passed:true,checks,in_game_verified:false},null,2));
  console.log('ADM_FRAME_TESTS_PASSED',checks.length);
 }finally{await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error(e);process.exit(1)});
