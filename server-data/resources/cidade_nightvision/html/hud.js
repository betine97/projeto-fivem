const mask = document.getElementById('mask');
const canvas = document.getElementById('hud');
const ctx = canvas.getContext('2d');
const ink = '#a0df78';
const state = { heading: 0, pitch: 0, roll: 0, active: false, visible: false };
let lastMessage = 0;
let width = 0, height = 0;
const clamp = (v, low, high) => Math.max(low, Math.min(high, v));
const wrap = v => (v % 360 + 360) % 360;
function resize() {
  width = window.innerWidth; height = window.innerHeight;
  const scale = Math.min(window.devicePixelRatio || 1, 2);
  for (const c of [canvas, mask]) {
    c.width = Math.round(width * scale); c.height = Math.round(height * scale);
    c.getContext('2d').setTransform(scale, 0, 0, scale, 0, 0);
  }
  const m = mask.getContext('2d');
  m.globalCompositeOperation = 'source-over';
  m.fillStyle = '#000'; m.fillRect(0, 0, width, height);
  m.globalCompositeOperation = 'destination-out';
  for (const x of [0.32, 0.68]) {
    m.save(); m.translate(width * x, height * 0.5); m.scale(width * 0.48, height * 0.58);
    const gradient = m.createRadialGradient(0, 0, 0, 0, 0, 1);
    gradient.addColorStop(0, 'rgba(0,0,0,1)'); gradient.addColorStop(0.72, 'rgba(0,0,0,1)');
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    m.fillStyle = gradient; m.fillRect(-1, -1, 2, 2); m.restore();
  }
  m.globalCompositeOperation = 'source-over';
}
function line(x1, y1, x2, y2) { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); }
function triangle(x, y, direction) {
  ctx.beginPath(); ctx.moveTo(x, y);
  if (direction === 'down') { ctx.lineTo(x - 4, y - 7); ctx.lineTo(x + 4, y - 7); }
  else { ctx.lineTo(x + direction * 7, y - 4); ctx.lineTo(x + direction * 7, y + 4); }
  ctx.closePath(); ctx.fill();
}
function compass() {
  const center = width / 2, y = height * 0.035, size = Math.min(width * 0.32, 620);
  const pixelsPerDegree = size / 120;
  const cardinal = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
  ctx.save(); ctx.beginPath(); ctx.rect(center - size / 2, 0, size, y + 52); ctx.clip();
  for (let degree = Math.floor((state.heading - 60) / 5) * 5; degree <= state.heading + 60; degree += 5) {
    const x = center + (degree - state.heading) * pixelsPerDegree;
    const angle = wrap(degree), major = angle % 45 === 0;
    line(x, y, x, y + (major ? 12 : angle % 15 === 0 ? 8 : 4));
    if (major) ctx.fillText(cardinal[angle / 45], x, y + 29);
  }
  ctx.restore(); triangle(center, y - 3, 'down');
  ctx.fillText(`${String(Math.round(state.heading) % 360).padStart(3, '0')}°`, center, y + 49);
}
function scale(x, value, limit, label, right) {
  const top = height * 0.13, span = height * 0.25;
  for (let n = -limit; n <= limit; n += limit / 9) {
    const y = top + (limit - n) / (2 * limit) * span;
    const major = Math.abs(n / (limit / 3) - Math.round(n / (limit / 3))) < 0.01;
    line(x, y, x + (right ? 1 : -1) * (major ? 11 : 5), y);
    if (major) { ctx.textAlign = right ? 'left' : 'right'; ctx.fillText(`${Math.round(n)}°`, x + (right ? 17 : -17), y + 4); }
  }
  ctx.textAlign = 'center';
  const marker = top + (limit - clamp(value, -limit, limit)) / (2 * limit) * span;
  triangle(x + (right ? -7 : 7), marker, right ? -1 : 1);
  ctx.fillText(label, x, top + span + 26);
  ctx.fillText(`${value >= 0 ? '+' : ''}${value.toFixed(1)}°`, x, top + span + 44);
}
window.addEventListener('message', event => {
  const d = event.data;
  if (!d || d.type !== 'nightvision') return;
  lastMessage = performance.now();
  state.active = d.active === true; state.visible = d.visible !== false;
  if (Number.isFinite(d.heading)) state.heading = wrap(d.heading);
  if (Number.isFinite(d.pitch)) state.pitch = clamp(d.pitch, -90, 90);
  if (Number.isFinite(d.roll)) state.roll = clamp(d.roll, -90, 90);
});
function frame() {
  const visible = state.active && state.visible && performance.now() - lastMessage < 1000;
  document.body.style.display = visible ? 'block' : 'none';
  if (visible) {
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = ink; ctx.fillStyle = ink; ctx.lineWidth = 1;
    ctx.font = `${clamp(height / 70, 11, 16)}px monospace`; ctx.textAlign = 'center';
    compass(); scale(width * 0.065, state.pitch, 90, 'ELEV', false);
    scale(width * 0.935, state.roll, 45, 'INCL', true);
  }
  requestAnimationFrame(frame);
}
window.addEventListener('resize', resize); resize(); requestAnimationFrame(frame);
