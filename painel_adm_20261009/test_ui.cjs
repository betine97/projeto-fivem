const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/erons/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),port=fs.readFileSync(path.join(__dirname,'preview-port.txt'),'utf8').trim(),base=`http://127.0.0.1:${port}`;
const checks=[];
function assert(value,name){if(!value)throw new Error(name);checks.push(name);}
(async()=>{
  const browser=await chromium.launch({headless:true,channel:'msedge'});
  try{
    const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(base+'/?preview=1');await page.locator('.card').first().waitFor();
    // Explicitly load the whole tested page, including thumbnails below the
    // viewport that production intentionally lazy-loads.
    await page.locator('.thumbnail img').evaluateAll(images=>images.forEach(i=>i.loading='eager'));
    await page.waitForFunction(()=>Array.from(document.querySelectorAll('.thumbnail img')).every(i=>i.complete&&i.naturalWidth>0));
    assert(await page.locator('.card').count()===24,'Vehicle thumbnails paginated');
    await page.screenshot({path:path.join(__dirname,'painel-veiculos.png')});
    await page.locator('#search').fill('sertao');assert(await page.locator('.card').count()===1,'Custom city vehicle found');
    await page.locator('.favorite').click();await page.locator('#search').fill('');await page.locator('#favorites-only').check();assert(await page.locator('.card').count()===1,'Favorites persist and filter');
    await page.locator('[data-tab=weapons]').click();await page.locator('#search').fill('weapon_carbinerifle');assert(await page.locator('.card').count()>=1,'Weapon search by native model');
    await page.locator('.spawn').first().click();await page.locator('#weapon-ammo').fill('-1');await page.locator('#weapon-form button[type=submit]').click();assert((await page.locator('#toast').innerText()).includes('Munição'),'Invalid ammunition blocked');
    await page.locator('#weapon-cancel').click();await page.locator('#search').fill('');await page.screenshot({path:path.join(__dirname,'painel-armas.png')});
    await page.locator('[data-tab=npcs]').click();await page.locator('#search').fill('cartelking');assert(await page.locator('.card').count()===1,'Custom NPC has image and model');
    await page.locator('.spawn').click();assert((await page.locator('#toast').innerText()).includes('Prévia'),'Preview does not pretend to spawn in game');
    await page.locator('#search').fill('');await page.screenshot({path:path.join(__dirname,'painel-npcs.png')});
    await page.locator('[data-tab=commands]').click();await page.locator('#search').fill('editarobjetos');assert(await page.locator('tbody tr').count()>=1,'Existing object editor listed');
    assert(await page.getByRole('button',{name:'Executar',exact:true}).first().isDisabled(),'Inactive resource execution disabled');
    await page.locator('#search').fill('');await page.screenshot({path:path.join(__dirname,'painel-comandos.png')});
    await page.locator('[data-tab=players]').click();assert((await page.locator('.table th').first().innerText()).includes('PERMANENTE'),'Player actions identify permanent IDs');
    await page.locator('#target-id').fill('2');await page.getByRole('button',{name:'Trazer para perto',exact:true}).click();assert((await page.locator('#toast').innerText()).includes('Prévia'),'Player bring action available');
    await page.setViewportSize({width:1024,height:768});assert(await page.locator('main').evaluate(n=>n.scrollWidth<=n.clientWidth),'Panel fits 1024x768');
    await page.keyboard.press('Escape');assert(await page.locator('#app').isHidden(),'Escape closes preview');
    assert(errors.length===0,'No browser script errors');
    // Exercise real NUI request payloads against a mocked game bridge.
    const game=await browser.newPage({viewport:{width:1600,height:1000}}),requests=[];
    await game.addInitScript(()=>window.GetParentResourceName=()=> 'cidade_admin');
    await game.route('https://cidade_admin/**',async route=>{
      const data=route.request().postDataJSON();requests.push({url:route.request().url(),data});
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,message:'Autorizado pelo servidor.'})});
    });
    await game.goto(base+'/');assert(await game.locator('#app').isHidden(),'NUI starts hidden without preview');
    const cat=JSON.parse(fs.readFileSync(path.join(root,'server-data/resources/cidade_admin/ui/catalog.json'),'utf8'));
    await game.evaluate(c=>window.postMessage({type:'open',data:{name:'Teste ADM',id:77,catalog:c,commands:c.commands.map(r=>({...r,active:true})),players:[{id:1,name:'Amigo',bucket:0}],npcs:[]}},'*'),cat);
    await game.locator('[data-tab=weapons]').click();await game.locator('#search').fill('weapon_pistol');await game.locator('.spawn').first().click();await game.locator('#weapon-ammo').fill('350');await game.locator('#weapon-form button[type=submit]').click();await game.locator('#weapon-modal').waitFor({state:'hidden'});
    assert(requests.at(-1).data.action==='weapon'&&requests.at(-1).data.ammo===350,'Weapon callback includes model and selected ammo');
    await game.locator('[data-tab=players]').click();await game.locator('#target-id').fill('1');await game.getByRole('button',{name:'Trazer para perto',exact:true}).click();
    assert(requests.at(-1).data.name==='chamar'&&requests.at(-1).data.args==='1','Bring action sends permanent ID command');
    await game.locator('[data-tab=commands]').click();await game.locator('#search').fill('localizar');await game.getByRole('button',{name:'Executar',exact:true}).click();await game.locator('#command-args').fill('77;restart');await game.locator('#command-form button[type=submit]').click();
    assert((await game.locator('#toast').innerText()).includes('separadores'),'Command modal rejects injection syntax');
    await game.locator('#command-args').fill('77');await game.locator('#command-form button[type=submit]').click();
    assert(requests.at(-1).data.name==='localizar'&&requests.at(-1).data.args==='77','Command modal sends valid ID');
    await game.locator('#modal').waitFor({state:'hidden'});
    const [closeRequest]=await Promise.all([game.waitForRequest(r=>r.url().endsWith('/close')),game.keyboard.press('Escape')]);
    assert(closeRequest.url().endsWith('/close'),'Escape requests game to release focus');
    fs.writeFileSync(path.join(__dirname,'ui-verification.json'),JSON.stringify({passed:true,checks,in_game_verified:false},null,2));
    console.log('UI_TESTS_PASSED',checks.length);
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
