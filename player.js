const canvas = document.getElementById('screen');
const ctx = canvas.getContext('2d');
const overlay = document.getElementById('overlay');
const start = document.getElementById('start');
const restart = document.getElementById('restart');
const status = document.getElementById('status');
const errorBox = document.getElementById('error');
const card = document.getElementById('player-card');
let running = false, generation = 0, starting = false, keyQueue = Promise.resolve();
const held = new Set();
async function request(url, body) {
  const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body || {})});
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'Could not reach the game');
  return data;
}
async function play() {
  if (starting) return;
  starting = true; running = false; generation++; held.clear();
  await keyQueue;
  start.disabled = true; restart.disabled = true; start.textContent = 'Starting…';
  errorBox.hidden = true; status.textContent = 'STARTING YOUR GAME';
  try {
    await request('/api/start'); overlay.hidden = true; running = true;
    status.textContent = 'GAME IS RUNNING'; void poll(generation);
  } catch (e) {
    overlay.hidden = false; errorBox.textContent = e.message; errorBox.hidden = false; status.textContent = 'COULD NOT START';
  } finally {
    starting = false; start.disabled = false; restart.disabled = false; start.textContent = '▶  Start game';
  }
}
async function poll(id) {
  while (running && id === generation) {
    try {
      const r = await fetch('/api/frame', {cache: 'no-store'});
      if (!r.ok) { const o = await r.json(); throw new Error(o.error); }
      const buf = new Uint8Array(await r.arrayBuffer());
      if (id !== generation) return;
      const w = (buf[1] << 8) | buf[2], h = (buf[3] << 8) | buf[4];
      if (!w || !h || buf.length !== 16 + w * h * 3) throw new Error('Invalid game frame');
      if (canvas.width !== w || canvas.height !== h) {canvas.width = w; canvas.height = h;}
      const image = ctx.createImageData(w, h);
      for (let i = 0, j = 16; i < w * h; i++, j += 3) {
        image.data[i*4] = buf[j]; image.data[i*4+1] = buf[j+1]; image.data[i*4+2] = buf[j+2]; image.data[i*4+3] = 255;
      }
      ctx.putImageData(image, 0, 0);
    } catch (e) {
      if (id !== generation) return;
      running = false; overlay.hidden = false; errorBox.textContent = 'Connection lost. Press Start game to try again.';
      errorBox.hidden = false; status.textContent = 'GAME DISCONNECTED'; console.error(e); break;
    }
    await new Promise(resolve => setTimeout(resolve, 45));
  }
}
function key(k, down) {
  if (!running) return;
  if (down) { if (held.has(k)) return; held.add(k); }
  else { if (!held.has(k)) return; held.delete(k); }
  // Serialize input so a quick tap cannot arrive at the emulator as release-before-press.
  keyQueue = keyQueue.then(() => request('/api/key', {key: k, down})).catch(console.error);
}
document.querySelectorAll('[data-key]').forEach(button => {
  const k = Number(button.dataset.key);
  button.addEventListener('pointerdown', e => {e.preventDefault(); button.setPointerCapture(e.pointerId); key(k, true);});
  for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(event, () => key(k, false));
});
const keys = {ArrowUp:0, ArrowDown:1, ArrowLeft:2, ArrowRight:3, Enter:18, Space:18, Digit5:18, Numpad5:18, KeyQ:9, KeyW:8};
document.addEventListener('keydown', e => {if (e.code in keys && running) {e.preventDefault(); key(keys[e.code], true);}});
document.addEventListener('keyup', e => {if (e.code in keys && running) {e.preventDefault(); key(keys[e.code], false);}});
window.addEventListener('blur', () => {for (const k of [...held]) key(k, false);});
start.addEventListener('click', play); restart.addEventListener('click', play);
document.getElementById('fullscreen').addEventListener('click', async () => {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await card.requestFullscreen(); }
  catch { status.textContent = 'FULL SCREEN NOT AVAILABLE'; }
});
