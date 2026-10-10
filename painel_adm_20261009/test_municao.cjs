const fs = require('fs'), path = require('path'), http = require('http');
const { chromium } = require('C:/Users/erons/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const ui = path.resolve(__dirname, '../server-data/resources/cidade_admin/ui');
const checks = [];
function check(value, name) { if (!value) throw new Error(name); checks.push(name); }

(async () => {
  const server = http.createServer((req, res) => {
    const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(ui, '.' + (name === '/' ? '/index.html' : name));
    if (!file.startsWith(ui + path.sep)) { res.writeHead(403).end(); return; }
    fs.readFile(file, (error, data) => {
      if (error) { res.writeHead(404).end(); return; }
      const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml' };
      res.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
      res.end(data);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true, channel: 'msedge' });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const requests = [], errors = [];
    let accepted = true, delay = 0;
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') console.error(message.text()); });
    await page.addInitScript(() => window.GetParentResourceName = () => 'cidade_admin');
    await page.route('https://cidade_admin/**', async route => {
      requests.push({ url: route.request().url(), data: route.request().postDataJSON() });
      if (delay) await new Promise(resolve => setTimeout(resolve, delay));
      await route.fulfill({ status: 200, headers: { 'Access-Control-Allow-Origin': '*' }, contentType: 'application/json', body: JSON.stringify({ ok: accepted, message: accepted ? 'Arma entregue.' : 'Entrega recusada pelo servidor.' }) });
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    const catalog = JSON.parse(fs.readFileSync(path.join(ui, 'catalog.json'), 'utf8'));
    const weapons = ['weapon_pistol', 'weapon_carbinerifle'].map(model => catalog.weapons.find(row => row.model === model));
    check(weapons.every(Boolean), 'Test weapons exist in installed catalog');
    await page.evaluate(weapons => window.postMessage({ type: 'open', data: { tab: 'weapons', name: 'Teste ADM', id: 1, catalog: { vehicles: [], weapons, npcs: [] } } }, '*'), weapons);
    const modal = page.locator('#weapon-modal'), input = page.locator('#weapon-ammo'), submit = page.locator('#weapon-form button[type=submit]');
    const select = () => page.locator('.spawn').first().click();
    await select();
    check(await modal.isVisible() && requests.length === 0, 'Selecting weapon asks for ammo before sending request');
    check(await page.locator('#weapon-model').innerText() === 'weapon_pistol', 'Dialog identifies selected weapon');
    await page.keyboard.press('Shift+Tab');
    check(await submit.evaluate(node => node === document.activeElement), 'Keyboard focus stays inside ammo dialog');
    await page.keyboard.press('Tab');
    check(await input.evaluate(node => node === document.activeElement), 'Keyboard focus wraps to ammo field');
    await page.locator('#weapon-cancel').click();
    check(await modal.isHidden() && requests.length === 0, 'Cancel sends no weapon request');
    await select(); await page.keyboard.press('Escape');
    check(await modal.isHidden() && await page.locator('#app').isVisible() && requests.length === 0, 'Escape cancels dialog without closing panel');
    await select();
    for (const value of ['', '-1', '1.5', '10000']) {
      await input.fill(value); await submit.click();
      check(await modal.isVisible() && requests.length === 0, 'Invalid ammo blocked: ' + (value || 'empty'));
    }
    await input.fill('350');
    await page.screenshot({ path: path.join(__dirname, 'painel-municao.png') });
    await submit.click();
    try { await modal.waitFor({ state: 'hidden', timeout: 5000 }); }
    catch (error) { console.error(JSON.stringify({ requests, errors, toast: await page.locator('#toast').textContent() })); throw error; }
    check(requests.at(-1).data.action === 'weapon' && requests.at(-1).data.model === 'weapon_pistol' && requests.at(-1).data.ammo === 350, 'Confirmed weapon request contains selected model and integer ammo');
    await page.locator('.spawn').nth(1).click();
    check(await input.inputValue() === '350', 'Last quantity is offered for next selection');
    await input.fill('0'); await submit.click(); await modal.waitFor({ state: 'hidden' });
    check(requests.at(-1).data.model === 'weapon_carbinerifle' && requests.at(-1).data.ammo === 0, 'Different selected weapon can be delivered with zero ammo');
    accepted = false;
    await select(); await input.fill('9999'); await submit.click();
    await page.waitForFunction(() => !document.getElementById('app').classList.contains('busy'));
    check(await modal.isVisible() && requests.at(-1).data.ammo === 9999, 'Server rejection keeps dialog open for retry');
    accepted = true; delay = 250;
    const before = requests.length;
    await page.locator('#weapon-form').evaluate(form => { form.requestSubmit(); form.requestSubmit(); });
    await modal.waitFor({ state: 'hidden' });
    check(requests.length === before + 1, 'Repeated confirmation does not duplicate grant');
    await select();
    await page.evaluate(() => window.postMessage({ type: 'close' }, '*'));
    await page.locator('#app').waitFor({ state: 'hidden' });
    check(await modal.isHidden(), 'Game close message clears ammo dialog');
    check(errors.length === 0, 'No browser JavaScript errors');
    fs.writeFileSync(path.join(__dirname, 'ammo-verification.json'), JSON.stringify({ passed: true, checks, in_game_verified: false }, null, 2));
    console.log('AMMO_UI_TESTS_PASSED', checks.length);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
