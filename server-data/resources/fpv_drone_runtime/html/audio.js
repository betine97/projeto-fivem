/* No focus or controls: the game's Lua resource supplies movement and volume. */
const flightAudio = new Audio('flight-loop.wav');
flightAudio.loop = true;
flightAudio.preload = 'auto';
flightAudio.volume = 0;
let lastUpdate = 0;
let starting = false;
let reportedError = false;
function silence() {
  flightAudio.volume = 0;
  flightAudio.pause();
}
window.addEventListener('message', (event) => {
  if (!event.data || event.data.type !== 'droneAudio') return;
  lastUpdate = Date.now();
  const value = event.data.volume;
  const volume = Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
  if (volume === 0) { silence(); return; }
  flightAudio.volume = volume;
  if (flightAudio.paused && !starting) {
    starting = true;
    flightAudio.play().catch((error) => {
      if (error.name !== 'AbortError' && !reportedError) {
        console.error('[Drone] Falha ao reproduzir flight-loop.wav:', error.message);
        reportedError = true;
      }
    }).finally(() => { starting = false; });
  }
});
// Never keep looping if Lua stops sending state or the resource disconnects.
setInterval(() => { if (Date.now() - lastUpdate > 1500) silence(); }, 200);
window.addEventListener('pagehide', silence);
