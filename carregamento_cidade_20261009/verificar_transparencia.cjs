// Pixel regression: a hidden NUI must expose the game underneath its iframe.
// Uses the real resource files; /old differs only by the original dark meta.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const zlib = require('node:zlib');
const { chromium } = require('../.downloads/hud-preview/node_modules/playwright');

const root = path.resolve(__dirname, '../server-data/resources/cidade_loading/web');
const output = path.join(__dirname, 'verificacao', 'transparencia');
const before = fs.readFileSync(path.join(__dirname, 'backup_interacao', 'index.html'), 'utf8');
const originalMeta = before.match(/<meta\s+name="color-scheme"\s+content="[^"]+"\s*\/?\s*>/i)?.[0];
assert(originalMeta && /content="dark"/.test(originalMeta), 'The original dark meta is required for the control case.');
const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.mp3': 'audio/mpeg' };
const magenta = [255, 0, 255];
const cases = [];

// Decode screenshot PNG pixels without changing, cropping or repainting images.
function pngPixels(bytes) {
  assert(bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])));
  let width, height, channels;
  const packed = [];
  for (let pos = 8; pos < bytes.length;) {
    const size = bytes.readUInt32BE(pos);
    const type = bytes.toString('ascii', pos + 4, pos + 8);
    const data = bytes.subarray(pos + 8, pos + 8 + size);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0); height = data.readUInt32BE(4);
      assert.equal(data[8], 8, 'Only eight-bit screenshot PNGs are supported.');
      channels = data[9] === 6 ? 4 : data[9] === 2 ? 3 : 0;
      assert(channels, 'Only RGB/RGBA screenshots are supported.');
      assert.equal(data[12], 0, 'Interlaced screenshots are not supported.');
    }
    if (type === 'IDAT') packed.push(data);
    pos += size + 12;
    if (type === 'IEND') break;
  }
  const scanlines = zlib.inflateSync(Buffer.concat(packed));
  const stride = width * channels;
  const pixels = Buffer.alloc(stride * height);
  const paeth = (a, b, c) => {
    const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
    return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
  };
  for (let y = 0; y < height; y++) {
    const filter = scanlines[y * (stride + 1)];
    assert(filter >= 0 && filter <= 4);
    for (let x = 0; x < stride; x++) {
      const at = y * stride + x;
      const left = x >= channels ? pixels[at - channels] : 0;
      const up = y ? pixels[at - stride] : 0;
      const upperLeft = y && x >= channels ? pixels[at - stride - channels] : 0;
      const prediction = filter === 1 ? left : filter === 2 ? up : filter === 3 ? Math.floor((left + up) / 2) : filter === 4 ? paeth(left, up, upperLeft) : 0;
      pixels[at] = (scanlines[y * (stride + 1) + x + 1] + prediction) & 255;
    }
  }
  let exposed = 0;
  for (let at = 0; at < pixels.length; at += channels) {
    if (pixels[at] === magenta[0] && pixels[at + 1] === magenta[1] && pixels[at + 2] === magenta[2]) exposed++;
  }
  const rgb = (x, y) => [...pixels.subarray((y * width + x) * channels, (y * width + x) * channels + 3)];
  return { width, height, exposed, total: width * height, corner: rgb(5,5), center: rgb(Math.floor(width / 2), Math.floor(height / 2)) };
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/host') {
    const variant = url.searchParams.get('variant') === 'old' ? 'old' : 'new';
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><meta name="color-scheme" content="normal"><style>html,body{margin:0;width:100%;height:100%;background:#ff00ff;color-scheme:normal}iframe{position:fixed;inset:0;width:100%;height:100%;border:0}</style><iframe src="/${variant}/index.html?interactive=1"></iframe>`);
    return;
  }
  const variant = url.pathname.startsWith('/old/') ? 'old' : 'new';
  const relative = url.pathname.replace(/^\/(old|new)\//, '');
  const file = path.resolve(root, relative);
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404); res.end(); return;
  }
  res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
  if (path.basename(file) === 'index.html') {
    let html = fs.readFileSync(file, 'utf8');
    if (variant === 'old') html = html.replace(/<meta\s+name="color-scheme"\s+content="[^"]+"\s*\/?\s*>/i, originalMeta);
    res.end(html); return;
  }
  const size = fs.statSync(file).size;
  const range = /bytes=(\d+)-(\d*)/.exec(req.headers.range || '');
  if (range) {
    const start = Number(range[1]), end = range[2] ? Math.min(size - 1, Number(range[2])) : size - 1;
    if (start > end || start >= size) { res.writeHead(416); res.end(); return; }
    res.writeHead(206, {'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': end - start + 1, 'Accept-Ranges': 'bytes'});
    fs.createReadStream(file, {start,end}).pipe(res);
  } else {
    res.setHeader('Content-Length',size); fs.createReadStream(file).pipe(res);
  }
});

(async () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert(/<meta\s+name="color-scheme"\s+content="normal"/.test(html), 'Save the corrected normal meta before running the regression.');
  fs.mkdirSync(output, {recursive:true});
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const executablePath = ['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(file => fs.existsSync(file));
  assert(executablePath, 'Chrome or Edge must be installed.');
  let browser;
  try {
    browser = await chromium.launch({executablePath,headless:true,args:['--autoplay-policy=no-user-gesture-required']});
    const page = await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
    const errors = [], callbacks = [];
    page.on('pageerror', err => errors.push(String(err)));
    await page.addInitScript(() => { window.GetParentResourceName = () => 'cidade_loading'; });
    const ready = {holding:1,ready:1,failed:0,entering:0,detail:'Mundo e personagem preparados.'};
    await page.route('https://cidade_loading/**', async route => {
      const command = new URL(route.request().url()).pathname.slice(1);
      callbacks.push(command);
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(command === 'loadingStatus' ? ready : {ok:true})});
    });
    const settlePaint = async frame => frame.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const frameFor = variant => page.frames().find(frame => frame.url().includes(`/${variant}/index.html`));
    const snapshot = async (name, frame) => {
      await settlePaint(frame);
      const file = path.join(output, `${name}.png`);
      const pixels = pngPixels(await page.screenshot({path:file}));
      const style = await frame.evaluate(() => ({
        meta:document.querySelector('meta[name="color-scheme"]').content,
        rootScheme:getComputedStyle(document.documentElement).colorScheme,
        rootBackground:getComputedStyle(document.documentElement).backgroundColor,
        bodyBackground:getComputedStyle(document.body).backgroundColor,
        bodyVisibility:getComputedStyle(document.body).visibility,
        active:document.documentElement.classList.contains('active')
      }));
      return {file,pixels,style};
    };

    await page.goto(`${base}/host?variant=old`);
    let frame = frameFor('old');
    await frame.waitForFunction(() => document.querySelectorAll('#playlist button').length === 3);
    const originalHidden = await snapshot('antes_oculto', frame);
    assert.equal(originalHidden.style.rootScheme, 'normal');
    assert.equal(originalHidden.style.bodyVisibility, 'hidden');
    assert.equal(originalHidden.style.rootBackground, 'rgba(0, 0, 0, 0)');
    assert.equal(originalHidden.style.bodyBackground, 'rgba(0, 0, 0, 0)');
    assert.equal(originalHidden.pixels.exposed, 0, 'The original meta must reproduce the opaque iframe canvas even with transparent computed styles.');
    cases.push('meta dark reproduz canvas opaco com HTML/body transparentes e color-scheme CSS normal');

    await page.goto(`${base}/host?variant=new`);
    frame = frameFor('new');
    await frame.waitForFunction(() => document.querySelectorAll('#playlist button').length === 3);
    const initialHidden = await snapshot('depois_oculto', frame);
    assert.equal(initialHidden.style.bodyVisibility, 'hidden');
    assert.equal(initialHidden.pixels.exposed, initialHidden.pixels.total, 'Every hidden pixel must expose the underlying game surrogate.');
    cases.push('NUI inicial oculta revela o fundo em todos os 1.296.000 pixels');

    await frame.evaluate(readyState => window.dispatchEvent(new MessageEvent('message',{data:{eventName:'cidadeLoadingActivate',progress:95,state:readyState,audio:{index:0,time:0,volume:.35,muted:true,paused:true}}})), ready);
    await frame.waitForFunction(() => document.documentElement.classList.contains('active') && !document.getElementById('advance').disabled);
    const active = await snapshot('ativa', frame);
    assert.equal(active.style.bodyVisibility, 'visible');
    assert(active.pixels.exposed < active.pixels.total * .01, 'An active loading screen must be visually present.');
    assert(callbacks.includes('loadingUiReady') && callbacks.includes('loadingUiActive'));
    cases.push('ativação Lua exibe a tela e confirma loadingUiActive; estado numérico pronto libera entrada');

    await frame.locator('#advance').click();
    await frame.waitForFunction(() => document.body.classList.contains('entering') && Number(getComputedStyle(document.body).opacity) === 0);
    assert.equal(callbacks.filter(command => command === 'loadingAdvance').length, 1);
    await frame.evaluate(() => window.dispatchEvent(new MessageEvent('message',{data:{eventName:'cidadeLoadingClose'}})));
    await frame.waitForFunction(() => !document.documentElement.classList.contains('active') && getComputedStyle(document.body).visibility === 'hidden');
    const closed = await snapshot('fechada_apos_fade', frame);
    assert.equal(closed.pixels.exposed, closed.pixels.total, 'Closing after the fade must restore every underlying game pixel.');
    cases.push('entrada após fade e cidadeLoadingClose devolve todos os pixels ao jogo');
    assert.deepEqual(errors, []);
    cases.push('nenhuma exceção JavaScript no ciclo completo');

    const result = {passed:cases.length,cases,originalHidden,initialHidden,active,closed,callbacks,errors};
    fs.writeFileSync(path.join(output,'resultado.json'), JSON.stringify(result,null,2));
    console.log(JSON.stringify({passed:cases.length,cases,output,oldPixel:originalHidden.pixels.corner,newPixel:initialHidden.pixels.corner,closedPixel:closed.pixels.corner},null,2));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error);process.exitCode=1;});
