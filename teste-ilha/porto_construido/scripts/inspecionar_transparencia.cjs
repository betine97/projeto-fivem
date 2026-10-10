const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/erons/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../..'),out=path.join(__dirname,'../dados');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try {
  const page=await browser.newPage({viewport:{width:320,height:180}});
  const css=fs.readFileSync(path.join(root,'server-data/resources/cidade_admin/ui/style.css'),'utf8');
  await page.setContent(`<style>${css}</style><div id="app" hidden></div>`);
  await page.screenshot({path:path.join(out,'nui_original.png'),omitBackground:true});
  const states=[];
  states.push(await page.evaluate(()=>({name:'original',scheme:getComputedStyle(document.documentElement).colorScheme,html:getComputedStyle(document.documentElement).backgroundColor,body:getComputedStyle(document.body).backgroundColor})));
  await page.addStyleTag({content:'html,body{background:transparent!important}'});
  await page.screenshot({path:path.join(out,'nui_root_transparente.png'),omitBackground:true});
  await page.addStyleTag({content:':root{color-scheme:normal}#app{color-scheme:dark}'});
  await page.screenshot({path:path.join(out,'nui_corrigida.png'),omitBackground:true});
  states.push(await page.evaluate(()=>({name:'corrected',scheme:getComputedStyle(document.documentElement).colorScheme,html:getComputedStyle(document.documentElement).backgroundColor,body:getComputedStyle(document.body).backgroundColor})));
  await page.setContent('<style>html,body{margin:0;background:#ee00ee}iframe{border:0;width:320px;height:180px}</style><iframe></iframe>');
  const frame=page.frames()[1];await frame.setContent(`<style>${css}</style><div id="app" hidden></div>`);
  await page.screenshot({path:path.join(out,'nui_frame_original.png')});
  await frame.addStyleTag({content:':root{color-scheme:normal}#app{color-scheme:dark}'});
  await page.screenshot({path:path.join(out,'nui_frame_corrigida.png')});
  console.log(JSON.stringify(states));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
