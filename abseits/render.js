// Renders film.html to ../abseits-erklaert.mp4 (1920x1080, 25 fps) with voice-over and stadium sound.
// Usage: node render.js [workers]
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), TMP = path.join(__dirname, '.render'), FPS = 25;
const ONLY_MUX = process.argv[2] === 'mux', WORKERS = +process.argv[2] || 3, PORT = 8771;
fs.mkdirSync(TMP, { recursive: true });
const server = spawn('python3', ['-m', 'http.server', String(PORT)], { cwd: ROOT, stdio: 'ignore' });
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
async function open() {
  const b = await chromium.launch({ args: ARGS });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto(`http://localhost:${PORT}/abseits/film.html`);
  await p.waitForFunction(() => window.READY, null, { timeout: 300000 });
  return { b, p };
}
async function worker(i, a, z) {
  const { b, p } = await open();
  const out = path.join(TMP, `seg${i}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < z; f++) {
    const d = await p.evaluate(t => { renderFrame(t); return grab(0.94); }, f / FPS);
    if (!ff.stdin.write(Buffer.from(d, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - a) % 100 === 0) console.log(`worker ${i}: ${f - a}/${z - a}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
  return out;
}
function audio(film) {
  const inputs = [], filters = [], mix = [];
  film.cues.forEach((c, k) => { inputs.push('-i', path.join(__dirname, 'voice', c.id + '.wav')); const ms = Math.round(c.t * 1000); filters.push(`[${k}:a]aresample=44100,adelay=${ms}|${ms},volume=1.6[v${k}]`); mix.push(`[v${k}]`); });
  const D = film.total.toFixed(2);
  const cheer = film.cheers.map(t => `0.9*exp(-pow((t-${(t + 0.9).toFixed(2)})/1.1\\,2))`).join('+');
  filters.push(`anoisesrc=color=pink:amplitude=0.6:duration=${D}:seed=4,highpass=f=180,lowpass=f=1400,aresample=44100,volume='0.22+0.05*sin(t*0.7)+0.55*(${cheer})':eval=frame[crowd]`);
  mix.push('[crowd]');
  film.whistles.forEach((t, k) => { filters.push(`aevalsrc='0.22*sin(2*PI*3000*t+4*sin(2*PI*36*t))*min(1\\,t*30)*min(1\\,(0.75-t)*20)':s=44100:d=0.75,adelay=${Math.round(t * 1000)}|${Math.round(t * 1000)}[w${k}]`); mix.push(`[w${k}]`); });
  filters.push(`${mix.join('')}amix=inputs=${mix.length}:normalize=0:duration=longest,atrim=0:${D},loudnorm=I=-16:TP=-1.5:LRA=11[out]`);
  fs.writeFileSync(path.join(TMP, 'audio.txt'), filters.join(';\n'));
  execFileSync('ffmpeg', ['-y', '-v', 'error', ...inputs, '-filter_complex_script', path.join(TMP, 'audio.txt'), '-map', '[out]', '-ac', '2', '-ar', '44100', path.join(TMP, 'audio.wav')], { stdio: 'inherit' });
}
(async () => {
  try {
    const { b, p } = await open();
    const film = await p.evaluate(() => FILM); await b.close();
    console.log('film', film.total.toFixed(1), 's');
    audio(film); console.log('audio ok');
    const N = Math.round(film.total * FPS), per = Math.ceil(N / WORKERS);
    const segs = ONLY_MUX ? fs.readFileSync(path.join(TMP, 'list.txt'), 'utf8').split('\n').map(l => l.slice(6, -1)) : await Promise.all([...Array(WORKERS)].map((_, i) => worker(i, i * per, Math.min(N, (i + 1) * per))));
    fs.writeFileSync(path.join(TMP, 'list.txt'), segs.map(s => `file '${s}'`).join('\n'));
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(TMP, 'list.txt'), '-i', path.join(TMP, 'audio.wav'),
      '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', path.join(ROOT, 'abseits-erklaert.mp4')], { stdio: 'inherit' });
    console.log('done');
  } catch (e) { console.log('FAILED', e.message); process.exitCode = 1; }
  server.kill();
})();
