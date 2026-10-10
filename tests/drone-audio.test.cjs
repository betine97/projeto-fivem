const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const handlers = {};
let timer, audio, now = 1000;
class FakeAudio {
  constructor() { audio = this; this.paused = true; this.plays = 0; }
  play() { this.paused = false; this.plays++; return Promise.resolve(); }
  pause() { this.paused = true; }
}
vm.runInNewContext(fs.readFileSync('server-data/resources/fpv_drone_runtime/html/audio.js', 'utf8'), {
  Audio: FakeAudio, Date: { now: () => now }, console,
  window: { addEventListener: (name, callback) => { handlers[name] = callback; } },
  setInterval: callback => { timer = callback; }
});
const update = volume => handlers.message({ data: { type: 'droneAudio', volume } });
async function main() {
  assert.equal(audio.loop, true);
  update(0.5);
  assert.equal(audio.paused, false);
  assert.equal(audio.volume, 0.5);
  await new Promise(setImmediate);
  update(0.4);
  assert.equal(audio.plays, 1, 'Updates must not restart a playing loop');
  update(0);
  assert.equal(audio.paused, true, 'Stationary state must pause immediately');
  assert.equal(audio.volume, 0);
  update(0.6);
  assert.equal(audio.paused, false, 'Moving again must resume');
  await new Promise(setImmediate);
  now += 1501; timer();
  assert.equal(audio.paused, true, 'Lost heartbeat must silence the loop');
  update(NaN);
  assert.equal(audio.volume, 0);
  update(9);
  assert.equal(audio.volume, 1);
  await new Promise(setImmediate);
  handlers.pagehide();
  assert.equal(audio.paused, true, 'Unloading must silence');
  console.log('OK: audio movement/stop/resume, heartbeat, bounds and cleanup');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
