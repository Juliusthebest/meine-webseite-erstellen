// Abseits – einfach erklärt: deterministic 3D film renderer.
// renderFrame(T) draws the frame at time T (seconds) into #out; the render script captures it.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { retarget } from './retarget.js';
import { makePlayer, KITS, SKINS } from './player.js';

const W = 1920, H = 1080;
const FONT = '"Liberation Sans", Arial, Helvetica, sans-serif';
const YEL = '#ffd23f', GRN = '#2fd27a', RED = '#ff3b3b', CYAN = '#29c8ff';

/* ------------------------------------------------------------------ helpers */
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => clamp((t - a) / (b - a), 0, 1);
const smooth = (a, b, v) => { const t = prog(v, a, b); return t * t * (3 - 2 * t); };
const ease = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
const easeOut = t => 1 - Math.pow(1 - t, 3);
const EASES = { io: ease, out: easeOut, lin: t => t, in: t => t * t };
function track(k, t) {
  if (!Array.isArray(k[0])) return { x: k[0], y: k[1] };
  if (t <= k[0][0]) return { x: k[0][1], y: k[0][2] };
  for (let i = 0; i < k.length - 1; i++) {
    const a = k[i], b = k[i + 1];
    if (t <= b[0]) { const p = (EASES[b[3]] || ease)((t - a[0]) / (b[0] - a[0])); return { x: lerp(a[1], b[1], p), y: lerp(a[2], b[2], p) }; }
  }
  const z = k[k.length - 1]; return { x: z[1], y: z[2] };
}
const wx = x => x - 52.5, wz = y => y - 34;
const V = (x, y, h = 0) => new THREE.Vector3(wx(x), h, wz(y));
const fm = (lt, a, d) => lt < a ? lt : (lt < a + d ? a : lt - d); // freeze mapping
function pass(from, to, t, t0, t1, h = 0) {
  const p = prog(t, t0, t1), e = easeOut(p);
  return { x: lerp(from[0], to[0], e), y: lerp(from[1], to[1], e), z: h * 4 * p * (1 - p) };
}

/* ------------------------------------------------------------------ narration */
const VOICE = {
  N1: [4.68, 'Abseits. Kaum eine Regel im Fußball sorgt für so viele Diskussionen.'],
  N2: [4.06, 'Dabei ist sie gar nicht so kompliziert. Schauen wir sie uns Schritt für Schritt an.'],
  N3: [2.92, 'Die rote Mannschaft greift an. Blau verteidigt.'],
  N4: [9.16, 'Für das Abseits zählt der vorletzte Spieler der verteidigenden Mannschaft. Meistens ist der Torwart der letzte. Der vorletzte ist dann der hinterste Abwehrspieler.'],
  N5: [2.24, 'Auf seiner Höhe verläuft die Abseitslinie.'],
  N6: [4.40, 'Entscheidend ist nur ein einziger Moment: der Augenblick, in dem der Ball gespielt wird.'],
  N7: [4.82, 'Genau jetzt. Der Stürmer steht noch hinter der Linie. Also: kein Abseits.'],
  N8: [4.60, 'Dass er danach an der Abwehr vorbeiläuft, ist völlig erlaubt. Das Tor zählt.'],
  N9: [4.19, 'Jetzt die gleiche Situation. Aber diesmal steht der Stürmer zu weit vorne.'],
  N10: [6.16, 'Beim Abspiel ist er schon näher am Tor als der Ball und der vorletzte Verteidiger. Das ist Abseits.'],
  N11: [5.77, 'Der Schiedsrichterassistent hebt die Fahne. Es gibt einen indirekten Freistoß für die verteidigende Mannschaft.'],
  N12: [4.19, 'Und wenn beide genau auf gleicher Höhe sind? Dann ist es kein Abseits.'],
  N13: [8.14, 'Gemessen wird mit allen Körperteilen, mit denen man ein Tor erzielen darf. Also Kopf, Rumpf und Füße. Arme und Hände zählen nicht.'],
  N14: [4.51, 'Es gibt ein paar Ausnahmen. In der eigenen Hälfte kann man nicht im Abseits stehen.'],
  N15: [4.11, 'Auch bei Einwurf, Abstoß und Eckstoß gibt es kein Abseits.'],
  N16: [3.06, 'Wichtig: Im Abseits zu stehen, ist noch nicht verboten.'],
  N17: [6.80, 'Strafbar wird es erst, wenn der Spieler aktiv ins Spiel eingreift. Bleibt er passiv, wie hier, zählt das Tor.'],
  N18: [13.92, 'Zusammengefasst: Es zählt der Moment der Ballabgabe. Wer dann näher am Tor ist als der Ball und der vorletzte Gegenspieler, steht im Abseits. Gleiche Höhe ist kein Abseits. Und bestraft wird nur, wer aktiv ins Spiel eingreift.']
};
// split a line into subtitle chunks (sentences), timed by character share
function chunks(id) {
  const [dur, text] = VOICE[id];
  const parts = text.match(/[^.!?:]+[.!?:]+/g).map(s => s.trim());
  const merged = [];
  parts.forEach(p => { if (merged.length && (merged[merged.length - 1].length < 22 || p.length < 14) && (merged[merged.length - 1] + ' ' + p).length < 90) merged[merged.length - 1] += ' ' + p; else merged.push(p); });
  const total = merged.reduce((s, p) => s + p.length, 0);
  let acc = 0;
  return merged.map(p => { const a = acc / total * dur; acc += p.length; return { a, b: acc / total * dur, text: p }; });
}

/* ------------------------------------------------------------------ renderer + scene */
const out = document.getElementById('out');
const octx = out.getContext('2d');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(26, W / H, 0.4, 900);

function canvasTex(w, h, draw, srgb = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
function rand(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

// sky
scene.background = canvasTex(16, 512, (c, w, h) => {
  const g = c.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, '#07101f'); g.addColorStop(0.55, '#1b3150'); g.addColorStop(1, '#4b6582');
  c.fillStyle = g; c.fillRect(0, 0, w, h);
});
scene.fog = new THREE.Fog(0x2a3d55, 160, 520);

// lights (floodlit evening)
scene.add(new THREE.HemisphereLight(0xcfe3ff, 0x2a4a22, 0.9));
const sun = new THREE.DirectionalLight(0xfff3e0, 2.6);
sun.position.set(-30, 90, 60); sun.target.position.set(10, 0, 0);
sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096);
Object.assign(sun.shadow.camera, { left: -75, right: 75, top: 55, bottom: -55, near: 10, far: 250 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
scene.add(sun, sun.target);
const fill = new THREE.DirectionalLight(0xbfd6ff, 0.6); fill.position.set(60, 50, -70); scene.add(fill);

/* pitch texture */
const PPM = 36; // pixels per metre
const pitchTex = canvasTex(Math.round(115 * PPM), Math.round(78 * PPM), (c, w, h) => {
  const ox = 5 * PPM, oy = 5 * PPM, m = v => v * PPM;
  c.fillStyle = '#2f6d2c'; c.fillRect(0, 0, w, h);
  const N = 18, sw = 105 / N;
  for (let i = 0; i < N; i++) { c.fillStyle = i % 2 ? '#3b8436' : '#347a31'; c.fillRect(ox + m(i * sw), 0, m(sw) + 1, h); }
  // grain
  const r = rand(7);
  for (let i = 0; i < 260000; i++) {
    const x = r() * w, y = r() * h, l = r();
    c.fillStyle = l > .5 ? `rgba(255,255,230,${0.02 + r() * 0.04})` : `rgba(0,30,0,${0.04 + r() * 0.06})`;
    c.fillRect(x, y, 1 + r() * 2.5, 1 + r() * 1.5);
  }
  // wear in goal areas
  [[ox + m(2), oy + m(34)], [ox + m(103), oy + m(34)]].forEach(([x, y]) => {
    const g = c.createRadialGradient(x, y, 0, x, y, m(9)); g.addColorStop(0, 'rgba(110,95,60,.35)'); g.addColorStop(1, 'rgba(110,95,60,0)');
    c.fillStyle = g; c.fillRect(x - m(10), y - m(10), m(20), m(20));
  });
  c.strokeStyle = 'rgba(245,248,240,.93)'; c.lineWidth = m(0.12);
  c.save(); c.translate(ox, oy);
  const R = (x, y, ww, hh) => c.strokeRect(m(x), m(y), m(ww), m(hh));
  R(0, 0, 105, 68);
  c.beginPath(); c.moveTo(m(52.5), 0); c.lineTo(m(52.5), m(68)); c.stroke();
  c.beginPath(); c.arc(m(52.5), m(34), m(9.15), 0, Math.PI * 2); c.stroke();
  R(88.5, 13.84, 16.5, 40.32); R(99.5, 24.84, 5.5, 18.32); R(0, 13.84, 16.5, 40.32); R(0, 24.84, 5.5, 18.32);
  const a = Math.acos(5.5 / 9.15);
  c.beginPath(); c.arc(m(94), m(34), m(9.15), Math.PI - a, Math.PI + a); c.stroke();
  c.beginPath(); c.arc(m(11), m(34), m(9.15), -a, a); c.stroke();
  [[0, 0, 0, .5], [105, 0, .5, 1], [105, 68, 1, 1.5], [0, 68, 1.5, 2]].forEach(([x, y, s, e]) => { c.beginPath(); c.arc(m(x), m(y), m(1), s * Math.PI, e * Math.PI); c.stroke(); });
  c.fillStyle = 'rgba(245,248,240,.95)';
  [[52.5, 34], [94, 34], [11, 34]].forEach(([x, y]) => { c.beginPath(); c.arc(m(x), m(y), m(0.2), 0, Math.PI * 2); c.fill(); });
  c.restore();
});
const pitch = new THREE.Mesh(new THREE.PlaneGeometry(115, 78), new THREE.MeshStandardMaterial({ map: pitchTex, roughness: 0.95 }));
pitch.rotation.x = -Math.PI / 2; pitch.receiveShadow = true; scene.add(pitch);
const apron = new THREE.Mesh(new THREE.PlaneGeometry(170, 130), new THREE.MeshStandardMaterial({ color: 0x2a5a27, roughness: 1 }));
apron.rotation.x = -Math.PI / 2; apron.position.y = -0.02; apron.receiveShadow = true; scene.add(apron);

/* stands with crowd */
const crowdTex = canvasTex(2048, 1024, (c, w, h) => {
  c.fillStyle = '#121822'; c.fillRect(0, 0, w, h);
  const r = rand(11), rows = 64, rh = h / rows;
  const shirts = ['#c8102e', '#e8e8e8', '#1f4fa0', '#20252e', '#c8102e', '#f2c14e', '#3a3f4a', '#8a1020', '#d9d9d9', '#2b6cb0'];
  for (let j = 0; j < rows; j++) {
    c.fillStyle = j % 2 ? '#1a202b' : '#161c26'; c.fillRect(0, j * rh, w, rh);
    for (let x = 0; x < w; x += 7 + r() * 3) {
      if (r() < 0.12) continue;
      const y = j * rh + rh * 0.25 + r() * 2;
      c.fillStyle = shirts[Math.floor(r() * shirts.length)]; c.fillRect(x, y + 5, 6, rh * 0.55);
      c.fillStyle = ['#e2b896', '#a8735a', '#6b4532', '#f0cdb0'][Math.floor(r() * 4)]; c.fillRect(x + 1, y, 4, 5);
    }
  }
});
crowdTex.wrapS = crowdTex.wrapT = THREE.RepeatWrapping;
function stand(len, depth, rise, pos, rotY) {
  const g = new THREE.PlaneGeometry(len, Math.hypot(depth, rise));
  const t = crowdTex.clone(); t.needsUpdate = true; t.repeat.set(len / 40, 1.4);
  const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: t, roughness: 1, color: 0xb8c0cc, emissive: 0x222833, emissiveMap: t, emissiveIntensity: 0.6 }));
  const grp = new THREE.Group(); grp.add(mesh);
  mesh.rotation.x = -Math.atan2(rise, depth) + Math.PI / 2 - Math.PI / 2; // tilt
  mesh.rotation.x = -(Math.PI / 2 - Math.atan2(rise, depth));
  mesh.position.set(0, rise / 2 + 1.2, -depth / 2);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(len + 4, 0.8, 12), new THREE.MeshStandardMaterial({ color: 0x1b222c, roughness: .8 }));
  roof.position.set(0, rise + 9, -depth + 2); grp.add(roof);
  const wall = new THREE.Mesh(new THREE.BoxGeometry(len, 1.4, 0.4), new THREE.MeshStandardMaterial({ color: 0x23303f }));
  wall.position.set(0, 0.7, 0.2); grp.add(wall);
  grp.position.copy(pos); grp.rotation.y = rotY; scene.add(grp);
}
stand(140, 30, 17, new THREE.Vector3(0, 0, -34 - 9), 0);
stand(140, 30, 17, new THREE.Vector3(0, 0, 34 + 9), Math.PI);
stand(98, 28, 16, new THREE.Vector3(52.5 + 10, 0, 0), -Math.PI / 2);
stand(98, 28, 16, new THREE.Vector3(-52.5 - 10, 0, 0), Math.PI / 2);
[[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([sx, sz]) => { const p = new THREE.Vector3(sx * 70, 0, sz * 50); stand(44, 26, 15, p, Math.atan2(-p.x, -p.z)); });

/* LED boards */
const boardTex = canvasTex(4096, 128, (c, w, h) => {
  const segs = [['#0b1b33', '#ffffff', 'REGELKUNDE'], ['#ffd23f', '#111111', 'ABSEITS EINFACH ERKLÄRT'], ['#13213a', '#7fd0ff', 'FAIR PLAY'], ['#c8102e', '#ffffff', 'FUSSBALL VERSTEHEN']];
  const sw = w / segs.length;
  segs.forEach(([bg, fg, tx], i) => { c.fillStyle = bg; c.fillRect(i * sw, 0, sw, h); c.fillStyle = fg; c.font = `bold 78px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(tx, i * sw + sw / 2, h / 2 + 4); });
});
boardTex.wrapS = THREE.RepeatWrapping;
function board(len, pos, rotY) {
  const t = boardTex.clone(); t.needsUpdate = true; t.repeat.set(len / 48, 1);
  const m = new THREE.Mesh(new THREE.BoxGeometry(len, 0.95, 0.15), [0, 0, 0, 0, new THREE.MeshStandardMaterial({ map: t, emissive: 0xffffff, emissiveMap: t, emissiveIntensity: 0.55 }), 0].map(x => x || new THREE.MeshStandardMaterial({ color: 0x111111 })));
  m.position.copy(pos); m.rotation.y = rotY; m.castShadow = true; scene.add(m);
}
board(110, new THREE.Vector3(0, 0.48, -34 - 4.5), 0);
board(110, new THREE.Vector3(0, 0.48, 34 + 4.5), Math.PI);
board(60, new THREE.Vector3(52.5 + 5, 0.48, 0), -Math.PI / 2);
board(60, new THREE.Vector3(-52.5 - 5, 0.48, 0), Math.PI / 2);

/* floodlight towers */
[[-84, -70], [84, -70], [-84, 70], [84, 70]].forEach(([x, z]) => {
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.9, 48, 8), new THREE.MeshStandardMaterial({ color: 0x3a4250 }));
  pole.position.set(x, 24, z); pole.scale.y = 1.2; scene.add(pole);
  const lamp = new THREE.Mesh(new THREE.BoxGeometry(9, 5, 1), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff6dd, emissiveIntensity: 2.2 }));
  lamp.position.set(x * 0.98, 58, z * 0.98); lamp.lookAt(0, 0, 0); scene.add(lamp);
});

/* goals */
const netTex = canvasTex(256, 256, (c, w, h) => {
  c.clearRect(0, 0, w, h); c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 2;
  for (let i = 0; i <= w; i += 16) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i, h); c.stroke(); c.beginPath(); c.moveTo(0, i); c.lineTo(w, i); c.stroke(); }
});
netTex.wrapS = netTex.wrapT = THREE.RepeatWrapping;
const netGroups = [];
function goal(x, dir) {
  const g = new THREE.Group(), white = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: .4 });
  const post = (h, px, pz, rx = 0, rz = 0) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, h, 12), white); m.position.set(px, 0, pz); m.rotation.set(rx, 0, rz); m.castShadow = true; g.add(m); return m; };
  post(2.44, 0, -3.66).position.y = 1.22; post(2.44, 0, 3.66).position.y = 1.22;
  const bar = post(7.44, 0, 0, Math.PI / 2); bar.position.y = 2.44;
  const nm = (w, h, tx) => { const t = netTex.clone(); t.needsUpdate = true; t.repeat.set(w * 4, h * 4); return new THREE.MeshStandardMaterial({ map: t, transparent: true, side: THREE.DoubleSide, depthWrite: false, alphaTest: 0.05 }); };
  const net = new THREE.Group();
  const back = new THREE.Mesh(new THREE.PlaneGeometry(7.32, 2.44), nm(7.32, 2.44)); back.rotation.y = Math.PI / 2; back.position.set(dir * 2, 1.22, 0); net.add(back);
  const top = new THREE.Mesh(new THREE.PlaneGeometry(2, 7.32), nm(2, 7.32)); top.rotation.x = Math.PI / 2; top.position.set(dir * 1, 2.44, 0); net.add(top);
  [-3.66, 3.66].forEach(z => { const s = new THREE.Mesh(new THREE.PlaneGeometry(2, 2.44), nm(2, 2.44)); s.position.set(dir, 1.22, z); net.add(s); });
  g.add(net); g.position.set(x, 0, 0); scene.add(g); netGroups.push(net);
}
goal(wx(105), 1); goal(wx(0), -1);

/* corner flags */
[[0, 0], [105, 0], [0, 68], [105, 68]].forEach(([x, y]) => {
  const p = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.5), new THREE.MeshStandardMaterial({ color: 0xffffff })); p.position.copy(V(x, y, 0.75)); scene.add(p);
  const f = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.3), new THREE.MeshStandardMaterial({ color: 0xffd23f, side: THREE.DoubleSide })); f.position.copy(V(x, y, 1.35)); f.position.x += 0.2; scene.add(f);
});

/* ball */
const ballTex = canvasTex(512, 256, (c, w, h) => {
  c.fillStyle = '#f4f4f4'; c.fillRect(0, 0, w, h);
  const r = rand(3); c.fillStyle = '#1b1b1b';
  for (let i = 0; i < 12; i++) { const x = (i % 6) * w / 6 + (i > 5 ? w / 12 : 0), y = i > 5 ? h * 0.7 : h * 0.3; c.beginPath(); for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2; c.lineTo(x + Math.cos(a) * 26, y + Math.sin(a) * 30); } c.fill(); }
  c.fillRect(0, 0, w, 10); c.fillRect(0, h - 10, w, 10);
});
const ball = new THREE.Mesh(new THREE.SphereGeometry(0.11, 24, 16), new THREE.MeshStandardMaterial({ map: ballTex, roughness: .45 }));
ball.castShadow = true; scene.add(ball);

/* overlays in 3D (ground graphics) */
const stripGeo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2).translate(0, 0, 0.5);
function strip(color, op = 0.95) {
  const m = new THREE.Mesh(stripGeo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: op, depthWrite: false, toneMapped: false }));
  m.renderOrder = 5; m.visible = false; scene.add(m); return m;
}
const lineMain = strip(0xffe14d), lineGlow = strip(0xffe14d, 0.25), lineDef = strip(0x29c8ff), lineAtt = strip(0xff3b3b), zone = strip(0xff3b3b, 0.22), half = strip(0x2fd27a, 0.18);
function setStrip(m, x0, x1, g = 1, op) {
  if (g <= 0.001) { m.visible = false; return; }
  m.visible = true; m.position.set(wx(Math.min(x0, x1)) + Math.abs(x1 - x0) / 2, 0.03, wz(0));
  m.scale.set(Math.max(0.01, Math.abs(x1 - x0)), 1, 68 * g);
  if (op !== undefined) m.material.opacity = op;
}
function setLine(m, x, width, g, op) { setStrip(m, x - width / 2, x + width / 2, g, op); }
const spotTex = canvasTex(256, 256, (c, w, h) => {
  const g = c.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
  g.addColorStop(0, 'rgba(255,255,255,.75)'); g.addColorStop(0.62, 'rgba(255,255,255,.35)'); g.addColorStop(0.7, 'rgba(255,255,255,.95)'); g.addColorStop(0.76, 'rgba(255,255,255,0)');
  c.fillStyle = g; c.fillRect(0, 0, w, h);
});
const spots = [];
for (let i = 0; i < 6; i++) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: spotTex, transparent: true, depthWrite: false, toneMapped: false }));
  m.renderOrder = 6; m.visible = false; scene.add(m); spots.push(m);
}
const arrowShape = new THREE.Shape([[0, -0.6], [30, -0.6], [30, -2], [36, 0], [30, 2], [30, 0.6], [0, 0.6]].map(([x, y]) => new THREE.Vector2(x, y)));
const arrow = new THREE.Mesh(new THREE.ShapeGeometry(arrowShape).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5, depthWrite: false, toneMapped: false }));
arrow.renderOrder = 5; arrow.visible = false; scene.add(arrow);

/* ------------------------------------------------------------------ characters */
const loader = new GLTFLoader();
const [xbot, rpm] = await Promise.all([loader.loadAsync('./models/Xbot.glb'), loader.loadAsync('./models/readyplayer.me.glb')]);
const CLIPS = {};
['idle', 'walk', 'run'].forEach(n => { CLIPS[n] = retarget(xbot.scene, xbot.animations.find(a => a.name === n), rpm.scene, b => 'mixamorig' + b); });
const CYCLE = { walk: 1.45, run: 3.9 }; // metres per animation cycle

// bind-pose data for arm posing (model space)
rpm.scene.updateMatrixWorld(true);
const BIND = {};
rpm.scene.traverse(b => { if (b.isBone) { BIND[b.name] = { q: b.getWorldQuaternion(new THREE.Quaternion()), p: b.getWorldPosition(new THREE.Vector3()) }; } });
const CHILD = { RightArm: 'RightForeArm', RightForeArm: 'RightHand', LeftArm: 'LeftForeArm', LeftForeArm: 'LeftHand' };

const POOL = {};
function addPlayer(id, kitName, skin, opts = {}) {
  const m = makePlayer(rpm.scene, { ...KITS[kitName], skin, beard: opts.beard });
  const s = opts.scale || 1; m.scale.setScalar(s);
  scene.add(m); m.visible = false;
  const mixer = new THREE.AnimationMixer(m);
  const acts = {};
  for (const n in CLIPS) { const a = mixer.clipAction(CLIPS[n]); a.play(); acts[n] = a; }
  const bones = {}; m.traverse(b => { if (b.isBone) bones[b.name] = b; });
  POOL[id] = { m, mixer, acts, bones, kit: kitName, scale: s, off: opts.off || 0 };
}
const R = n => SKINS[n % SKINS.length];
['r1', 'r2', 'r3', 'r4', 'r5', 'r6'].forEach((id, i) => addPlayer(id, 'red', R(i * 2 + 1), { scale: 0.96 + (i % 3) * 0.03, off: i * 0.37, beard: i === 2 }));
['b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7'].forEach((id, i) => addPlayer(id, 'blue', R(i * 3 + 2), { scale: 0.97 + (i % 4) * 0.02, off: i * 0.53, beard: i === 4 }));
addPlayer('gk', 'keeper', R(4), { scale: 1.04, off: 0.2 });
addPlayer('ar', 'ref', R(5), { scale: 0.98, off: 0.9 });
// assistant referee flag (attached to right hand)
const flag = new THREE.Group();
{
  const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.62), new THREE.MeshStandardMaterial({ color: 0x222222 })); stick.position.y = 0.31; flag.add(stick);
  const ft = canvasTex(64, 64, (c) => { for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { c.fillStyle = (i + j) % 2 ? '#ffd400' : '#e01b1b'; c.fillRect(i * 16, j * 16, 16, 16); } });
  const cloth = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.34), new THREE.MeshStandardMaterial({ map: ft, side: THREE.DoubleSide })); cloth.position.set(0.21, 0.45, 0); flag.add(cloth);
  flag.traverse(o => { if (o.isMesh) o.castShadow = true; });
}
POOL.ar.bones.RightHand.add(flag); flag.position.set(0, 0.08, 0.03); flag.scale.setScalar(1 / 0.98);

const _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _v = new THREE.Vector3(), _v2 = new THREE.Vector3();
// point a bone along a world direction (blend w)
function aim(P, name, dirWorld, w) {
  if (w <= 0) return;
  const b = P.bones[name], ch = CHILD[name];
  P.m.updateMatrixWorld(true);
  const rootQ = P.m.getWorldQuaternion(new THREE.Quaternion());
  const dirModel = dirWorld.clone().normalize().applyQuaternion(rootQ.clone().invert());
  const restDir = BIND[ch].p.clone().sub(BIND[name].p).normalize();
  const target = new THREE.Quaternion().setFromUnitVectors(restDir, dirModel).multiply(BIND[name].q);
  const parentQ = b.parent.getWorldQuaternion(new THREE.Quaternion()).premultiply(rootQ.clone().invert());
  const local = parentQ.invert().multiply(target);
  b.quaternion.slerp(local, w);
  b.updateMatrixWorld(true);
}

function angLerp(a, b, t) { let d = ((b - a + Math.PI * 3) % (Math.PI * 2)) - Math.PI; return a + d * t; }
// cast entry: { id, k: track keys | [x,y], face?: [x,y] | 'ball', arms?: fn }
function poseCast(cast, pt, ballPos) {
  const used = new Set();
  for (const c of cast) {
    const P = POOL[c.id]; used.add(c.id); P.m.visible = true;
    const p = track(c.k, pt);
    const p1 = track(c.k, pt - 0.12), p2 = track(c.k, pt + 0.12);
    const vx = (p2.x - p1.x) / 0.24, vy = (p2.y - p1.y) / 0.24, speed = Math.hypot(vx, vy);
    // travelled distance (for stride phase)
    let dist = 0; { let q = track(c.k, 0); for (let t = 0.04; t <= pt; t += 0.04) { const n = track(c.k, t); dist += Math.hypot(n.x - q.x, n.y - q.y); q = n; } }
    P.m.position.copy(V(p.x, p.y));
    // heading: movement direction, else face ball / given target
    const tgt = c.face === undefined || c.face === 'ball' ? ballPos : { x: c.face[0], y: c.face[1] };
    const hBall = Math.atan2(wx(tgt.x) - wx(p.x), wz(tgt.y) - wz(p.y));
    const hMove = Math.atan2(vx, vy);
    P.m.rotation.y = speed > 0.05 ? angLerp(hBall, hMove, smooth(0.4, 1.6, speed)) : hBall;
    const wIdle = 1 - smooth(0.15, 1.3, speed), wRun = smooth(2.4, 4.2, speed), wWalk = Math.max(0, 1 - wIdle - wRun);
    const A = P.acts;
    A.idle.setEffectiveWeight(wIdle); A.walk.setEffectiveWeight(wWalk); A.run.setEffectiveWeight(wRun);
    A.idle.time = (pt + P.off * 3) % CLIPS.idle.duration;
    A.walk.time = ((dist / CYCLE.walk + P.off) % 1) * CLIPS.walk.duration;
    A.run.time = ((dist / CYCLE.run + P.off) % 1) * CLIPS.run.duration;
    P.mixer.update(0);
    if (c.arms) c.arms(P);
  }
  for (const id in POOL) if (!used.has(id)) POOL[id].m.visible = false;
}
function headPos(id, up = 0.32) { const P = POOL[id]; const v = new THREE.Vector3(); P.bones.Head.getWorldPosition(v); v.y += up; return v; }
function bonePos(id, name) { const v = new THREE.Vector3(); POOL[id].bones[name].getWorldPosition(v); return v; }

/* ------------------------------------------------------------------ cameras */
function tvCam(fx, fz, fov = 24, back = 0) { fov *= 0.88; return { pos: new THREE.Vector3(wx(fx) - 4, 21 + back * 0.3, 70 + back), look: new THREE.Vector3(wx(fx), 0, wz(fz)), fov }; }
function lineCam(x, h = 12, dist = 44, lookY = -6, fov = 33) { fov *= 0.72; h *= 0.85; return { pos: new THREE.Vector3(wx(x), h, dist), look: new THREE.Vector3(wx(x), 0, lookY), fov }; }
function camKeys(keys, t) { // keys: [t, fx, fz, fov]
  const p = track(keys.map(k => [k[0], k[1], k[2], k[4]]), t);
  const f = track(keys.map(k => [k[0], k[3], 0, k[4]]), t);
  return tvCam(p.x, p.y, f.x);
}
function blendCam(a, b, t) { return { pos: a.pos.clone().lerp(b.pos, t), look: a.look.clone().lerp(b.look, t), fov: lerp(a.fov, b.fov, t) }; }

/* ------------------------------------------------------------------ scenes */
// base formation (attack towards x=105)
const F = {
  r1: [56, 40], r2: [78, 22], r3: [70, 52], r4: [63, 27], r5: [60, 47], r6: [48, 34],
  b1: [83, 28], b2: [82, 42], b3: [77, 13], b4: [77, 56], b5: [68, 33], b6: [70, 45], b7: [64, 20], gk: [101, 34]
};
const castFrom = (obj, extra = {}) => Object.keys(obj).map(id => Object.assign({ id, k: obj[id] }, extra[id] || {}));

const SCENES = [
{ id: 'intro', chapter: 'Intro', d: 10.6, voice: [['N1', 0.8], ['N2', 5.9]],
  frame(lt) {
    const a = lerp(-2.25, -1.45, ease(prog(lt, 0, 10.6)));
    const r = lerp(150, 95, ease(prog(lt, 0, 10.6)));
    const cam = { pos: new THREE.Vector3(Math.cos(a) * r + 10, lerp(70, 34, ease(prog(lt, 0, 10.6))), -Math.sin(a) * r * 0.8), look: new THREE.Vector3(18, 0, 0), fov: 30 };
    return { pt: lt, cast: castFrom(F), ball: { x: 57.3, y: 40.5, z: 0 }, cam, title: true };
  } },

{ id: 'line', chapter: 'Die Abseitslinie', d: 17.5, voice: [['N3', 0.6], ['N4', 3.9], ['N5', 13.4]],
  frame(lt) {
    const cast = castFrom(F, { r2: { k: [[0, 78, 21], [6, 78.6, 22], [12, 78, 22.5]] }, b1: { k: [[0, 83, 27], [8, 83, 28]] }, b5: { k: [[0, 67, 33], [10, 68, 34]] } });
    const cam = camKeys([[0, 72, 30, 27, 'io'], [3.5, 76, 32, 25], [8, 84, 32, 24], [12.5, 82, 31, 23], [17.5, 80, 32, 25]], lt);
    const lineG = prog(lt, 13.5, 14.6);
    return {
      pt: lt, cast, ball: { x: 57.3, y: 40.5, z: 0 }, cam,
      line: { x: 83, g: lineG, zone: prog(lt, 14.4, 15.2) },
      arrow: { x: 62, y: 63, a: prog(lt, 0.6, 1.3) * (1 - prog(lt, 4.2, 4.9)) },
      spots: [lt > 7.9 && { id: 'gk', c: YEL }, lt > 10.4 && { id: 'b1', c: YEL }].filter(Boolean),
      tags: [lt > 0.8 && lt < 4.4 && { id: 'r2', text: 'Angreifer', c: '#c8102e' }, lt > 1.9 && lt < 4.4 && { id: 'b2', text: 'Verteidiger', c: '#1f4fa0' },
        lt > 8.1 && { id: 'gk', text: '1 · Letzter', c: YEL, dark: true }, lt > 10.6 && { id: 'b1', text: '2 · Vorletzter', c: YEL, dark: true },
        lt > 14.4 && { pos: V(83, 1, 1.0), text: 'ABSEITSLINIE', c: '#ffe14d', dark: true, lift: 0 }].filter(Boolean)
    };
  } },

{ id: 'onside', chapter: 'Moment der Ballabgabe', d: 17.2, voice: [['N6', 0.5], ['N7', 5.7], ['N8', 11.4]],
  frame(lt) {
    const F0 = 5.25, FD = 5.75, pt = fm(lt, F0, FD), frozen = lt >= F0 && lt < F0 + FD;
    const P = 5.2;
    const cast = [
      { id: 'r1', k: [[0, 54, 43], [P - 0.3, 59.8, 42]] },
      { id: 'r2', k: [[0, 76, 21], [P - 0.6, 78, 24], [P, 78.3, 24.3], [P + 2.2, 93.3, 26.6, 'io'], [P + 2.6, 95, 27.4]] },
      { id: 'r3', k: [[0, 66, 54], [P, 69, 53], [P + 3, 84, 49]] },
      { id: 'r4', k: [[0, 62, 27], [P + 3, 74, 30]] },
      { id: 'r5', k: [[0, 58, 49], [P + 3, 66, 47]] },
      { id: 'b1', k: [[0, 81, 27], [P, 82, 28], [P + 0.35, 82.1, 28], [P + 2.4, 90.5, 27.6]] },
      { id: 'b2', k: [[0, 80, 43], [P, 82, 44], [P + 0.4, 82.2, 44], [P + 2.6, 89, 38]] },
      { id: 'b3', k: [[0, 75, 14], [P, 76, 15], [P + 2.8, 84, 19]] },
      { id: 'b4', k: [[0, 75, 56], [P + 3, 78, 54]] },
      { id: 'b5', k: [[0, 66, 37], [P, 65, 40], [P + 3, 70, 39]] },
      { id: 'b6', k: [[0, 69, 46], [P + 3, 72, 46]] },
      { id: 'gk', k: [[0, 101, 34], [P + 2.0, 100.4, 31], [P + 2.5, 101.6, 30.2, 'out']] },
      { id: 'ar', k: [[0, 80, -1.3], [P, 82, -1.3], [P + 0.6, 82.2, -1.3], [P + 3, 90, -1.3]], face: [82, 30] }];
    let b;
    if (pt < P) { const r1 = track(cast[0].k, pt); b = { x: r1.x + 0.6, y: r1.y + 0.3, z: 0 }; }
    else if (pt < P + 2.3) b = pass([60.4, 42.3], [93.9, 26.9], pt, P, P + 2.2);
    else b = pass([93.9, 26.9], [105.8, 31.5], pt, P + 2.4, P + 2.8, 0.9);
    let cam;
    if (lt < 5.6) cam = camKeys([[0, 70, 33, 25], [5.6, 75, 33, 24]], lt);
    else if (lt < 11.0) { const k = ease(prog(lt, 5.6, 11)); cam = lineCam(80.3, lerp(13, 10, k), lerp(46, 40, k), -8, lerp(34, 31, k)); }
    else cam = camKeys([[11, 82, 31, 24], [13.6, 92, 32, 25, 'io'], [17.2, 94, 33, 26]], lt);
    const varOn = lt > 6.1 && lt < 11.0;
    return {
      pt, cast, ball: b, cam, frozen, flashAt: F0,
      line: !frozen && lt < 5.3 ? { x: 82, g: prog(lt, 1.0, 2.0), zone: prog(lt, 1.6, 2.4) } : null,
      varLines: varOn ? { def: 82, att: 78.3 + 0.25, g: prog(lt, 6.1, 6.8), ok: true } : null,
      spots: varOn ? [{ id: 'r2', c: GRN }, { id: 'b1', c: CYAN }] : [],
      tags: varOn ? [{ id: 'r2', text: 'Stürmer', c: GRN, dark: true }, { id: 'b1', text: 'Vorletzter', c: CYAN, dark: true }] : (lt < 5.3 && lt > 1.6 ? [{ id: 'r2', text: 'Stürmer', c: '#c8102e' }] : []),
      verdict: lt > 9.2 && lt < 11.0 ? { ok: true, text: 'KEIN ABSEITS', a: prog(lt, 9.2, 9.5) * (1 - prog(lt, 10.7, 11)) } : (lt > 14.2 ? { ok: true, text: 'TOR – KEIN ABSEITS', a: prog(lt, 14.2, 14.5) } : null),
      net: pt > P + 2.8 ? prog(pt, P + 2.8, P + 3.6) : 0
    };
  } },

{ id: 'offside', chapter: 'Abseits!', d: 20.2, voice: [['N9', 0.4], ['N10', 5.2], ['N11', 13.6]],
  frame(lt) {
    const F0 = 5.0, FD = 6.8, pt = fm(lt, F0, FD), frozen = lt >= F0 && lt < F0 + FD;
    const P = 4.9, WH = 14.2, tw = WH - FD; // whistle in play time
    const st = t => Math.min(t, tw + 0.6); // players stop after whistle
    const cast = [
      { id: 'r1', k: [[0, 54, 43], [P - 0.3, 59.8, 42]] },
      { id: 'r2', k: [[0, 82, 23], [3.6, 86.6, 24], [P, 87, 24.2], [P + 2.1, 91.2, 26.5], [P + 3.5, 92, 27]] },
      { id: 'r3', k: [[0, 66, 54], [P, 69, 53], [P + 3, 76, 50]] },
      { id: 'r4', k: [[0, 62, 27], [P + 3, 70, 29]] },
      { id: 'r5', k: [[0, 58, 49], [P + 3, 63, 47]] },
      { id: 'b1', k: [[0, 81, 27], [P, 82, 28], [P + 0.5, 82.1, 28], [P + 2.6, 86, 27.5]] },
      { id: 'b2', k: [[0, 80, 43], [P, 82, 44], [P + 2.6, 85, 40]] },
      { id: 'b3', k: [[0, 75, 14], [P, 76, 15], [P + 2.8, 79, 17]] },
      { id: 'b4', k: [[0, 75, 56], [P + 3, 77, 55]] },
      { id: 'b5', k: [[0, 66, 37], [P, 65, 40], [P + 3, 68, 39]] },
      { id: 'b6', k: [[0, 69, 46], [P + 3, 71, 46]] },
      { id: 'gk', k: [[0, 101, 34], [P + 2.0, 99.5, 31.5], [P + 3, 99, 31]] },
      { id: 'ar', k: [[0, 79.5, -1.3], [P, 82, -1.3], [P + 3, 82.4, -1.3]], face: [82, 34],
        arms: Pp => { const w = smooth(13.2, 13.7, lt); aim(Pp, 'RightArm', new THREE.Vector3(0.15, 1, 0.12), w); aim(Pp, 'RightForeArm', new THREE.Vector3(0.1, 1, 0.1), w); } }];
    cast.forEach(c => { const k = c.k; c.k = Array.isArray(k[0]) ? k : k; });
    const ptS = st(pt);
    let b = pt < P ? (() => { const r1 = track(cast[0].k, pt); return { x: r1.x + 0.6, y: r1.y + 0.3, z: 0 }; })() : pass([60.4, 42.3], [91.6, 26.8], Math.min(pt, P + 2.6), P, P + 2.2);
    if (pt > P + 2.2) { const r2 = track(cast[1].k, ptS); b = { x: r2.x + 0.5, y: r2.y + 0.25, z: 0 }; }
    let cam;
    if (lt < 5.3) cam = camKeys([[0, 72, 33, 25], [5.3, 76, 33, 24]], lt);
    else if (lt < 11.8) { const k = ease(prog(lt, 5.3, 11.8)); cam = lineCam(84.6, lerp(13, 10, k), lerp(46, 40, k), -8, lerp(34, 30, k)); }
    else if (lt < 13.0) cam = camKeys([[11.8, 84, 30, 24], [13, 86, 29, 24]], lt);
    else if (lt < 16.4) { const k = ease(prog(lt, 13, 16.4)); cam = { pos: V(lerp(88.5, 87.5, k), -1.3 + lerp(10, 8.5, k), lerp(2.6, 2.3, k)), look: V(82.3, -1.3, 1.25), fov: 30 }; }
    else cam = camKeys([[16.4, 86, 30, 26], [20.2, 85, 31, 27]], lt);
    const varOn = lt > 5.8 && lt < 11.8;
    return {
      pt: ptS, cast, ball: b, cam, frozen, flashAt: F0, whistleAt: WH,
      line: !frozen && lt < 5.0 ? { x: 82, g: prog(lt, 1.0, 2.0), zone: prog(lt, 1.6, 2.4) } : null,
      varLines: varOn ? { def: 82, att: 87.35, g: prog(lt, 5.8, 6.5), ok: false } : null,
      spots: varOn ? [{ id: 'r2', c: RED }, { id: 'b1', c: CYAN }] : (lt > 13.1 && lt < 16.4 ? [] : []),
      tags: varOn ? [{ id: 'r2', text: 'Stürmer', c: RED }, { id: 'b1', text: 'Vorletzter', c: CYAN, dark: true }]
        : (lt > 1.4 && lt < 5.0 ? [{ id: 'r2', text: 'Stürmer', c: '#c8102e' }] : (lt > 13.6 && lt < 16.4 ? [{ id: 'ar', text: 'Schiedsrichter-Assistent', c: '#151b24', lift: 0.75 }] : [])),
      verdict: lt > 10.1 && lt < 11.8 ? { ok: false, text: 'ABSEITS', a: prog(lt, 10.1, 10.4) * (1 - prog(lt, 11.5, 11.8)) }
        : (lt > 16.6 ? { ok: false, text: 'INDIREKTER FREISTOSS FÜR BLAU', a: prog(lt, 16.6, 16.9), color: '#1f4fa0' } : null)
    };
  } },

{ id: 'level', chapter: 'Gleiche Höhe', d: 14.6, voice: [['N12', 0.5], ['N13', 5.2]],
  frame(lt) {
    const cast = [
      { id: 'r2', k: [80, 30.5], face: [92, 30], arms: Pp => { const w = smooth(11.2, 11.8, lt); aim(Pp, 'RightArm', new THREE.Vector3(1, 0.05, 0.15), w); aim(Pp, 'RightForeArm', new THREE.Vector3(1, 0.1, 0.05), w); } },
      { id: 'b1', k: [80, 35.5], face: [70, 33] },
      { id: 'r1', k: [64, 41], face: [80, 30] },
      { id: 'b5', k: [73, 44] }, { id: 'b3', k: [74, 22] }, { id: 'gk', k: [101, 34] }];
    const k = ease(prog(lt, 0, 14.6));
    const cam = { pos: V(80 + lerp(-0.0, 0, k), 47 - 34 + 34 + lerp(0, -2, k), lerp(2.9, 2.5, k)), look: V(80, 31, 0.95), fov: lerp(30, 27, k) };
    cam.pos = new THREE.Vector3(wx(80), lerp(7.0, 6.2, k), wz(lerp(53, 51, k)));
    cam.look = new THREE.Vector3(wx(80), 0.6, wz(32.6)); cam.fov = lerp(22, 19, k);
    const labels = [];
    if (lt > 7.3 && lt < 11.2) {
      const a = prog(lt, 7.3, 7.6);
      labels.push({ bone: ['r2', 'Head'], text: 'Kopf', c: GRN, a, dx: -170 }, { bone: ['r2', 'Spine1'], text: 'Rumpf', c: GRN, a: prog(lt, 7.9, 8.2), dx: -190 }, { bone: ['r2', 'LeftFoot'], text: 'Füße', c: GRN, a: prog(lt, 8.5, 8.8), dx: -170 });
    }
    if (lt > 11.3) labels.push({ bone: ['r2', 'RightHand'], text: 'Arm / Hand zählt nicht', c: '#8c96a6', a: prog(lt, 11.4, 11.7), dx: 120, dy: -70 });
    return {
      pt: lt, cast, ball: { x: 64.7, y: 41.4, z: 0 }, cam,
      varLines: { def: 80, att: 80, g: prog(lt, 0.8, 1.6), ok: true, same: true },
      tags: lt < 7.2 && lt > 1.0 ? [{ id: 'r2', text: 'Stürmer', c: GRN, dark: true }, { id: 'b1', text: 'Vorletzter', c: CYAN, dark: true }] : [],
      bodyLabels: labels,
      verdict: lt > 3.4 && lt < 7.2 ? { ok: true, text: 'GLEICHE HÖHE = KEIN ABSEITS', a: prog(lt, 3.4, 3.7) * (1 - prog(lt, 6.9, 7.2)) } : null
    };
  } },

{ id: 'except', chapter: 'Ausnahmen', d: 11.6, voice: [['N14', 0.5], ['N15', 6.2]],
  frame(lt) {
    if (lt < 5.7) {
      const u = lt, P = 2.0;
      const cast = [
        { id: 'r1', k: [[0, 38, 41], [P - 0.2, 40, 40.5]] },
        { id: 'r2', k: [[0, 50, 27], [P, 51, 26.5], [P + 1.8, 64, 27.5], [P + 2.6, 67, 28]] },
        { id: 'r3', k: [[0, 44, 52], [P + 3, 52, 50]] }, { id: 'r4', k: [[0, 36, 22], [P + 3, 44, 24]] },
        { id: 'b1', k: [[0, 49, 30], [P + 0.3, 49.4, 30], [P + 2.6, 58, 29]] },
        { id: 'b2', k: [[0, 50, 44], [P + 0.3, 50.2, 44], [P + 2.6, 57, 40]] },
        { id: 'b3', k: [[0, 48, 16], [P + 2.6, 53, 18]] }, { id: 'b4', k: [[0, 49, 56], [P + 2.6, 53, 54]] },
        { id: 'b5', k: [[0, 42, 36], [P + 2, 44, 37]] },
        { id: 'gk', k: [[0, 86, 34], [P + 2, 92, 33]] }];
      const b = u < P ? { x: 40.6, y: 40.8, z: 0 } : pass([40.6, 40.8], [64.6, 27.6], u, P, P + 1.8);
      if (u > P + 1.8) { const r2 = track(cast[1].k, u); b.x = r2.x + 0.6; b.y = r2.y + 0.3; }
      return {
        pt: u, cast, ball: b, cam: camKeys([[0, 47, 32, 27], [5.7, 56, 32, 26]], u), fadeIn: true,
        half: prog(u, 0.4, 1.0), line: { x: 50, g: prog(u, 0.6, 1.3) * (1 - prog(u, 3.6, 4.2)), zone: 0 },
        tags: [u > 0.8 && u < 4.2 && { id: 'r2', text: 'eigene Hälfte', c: GRN, dark: true }, u > 0.4 && { pos: V(26, 4, 0), text: 'EIGENE HÄLFTE (ROT)', c: GRN, dark: true, lift: 0 }].filter(Boolean),
        verdict: u > 3.0 ? { ok: true, text: 'KEIN ABSEITS IN DER EIGENEN HÄLFTE', a: prog(u, 3.0, 3.3) * (1 - prog(u, 5.3, 5.6)) } : null
      };
    }
    const u = lt - 5.7, T0 = 1.6;
    const thrower = { id: 'r1', k: [74, 68.8], face: [90, 46],
      arms: Pp => { const w = 1 - smooth(T0 + 0.05, T0 + 0.45, u); const back = smooth(T0 - 0.6, T0, u) * 0.6; aim(Pp, 'RightArm', new THREE.Vector3(0.1, 1, -0.15 - back), w); aim(Pp, 'LeftArm', new THREE.Vector3(-0.1, 1, -0.15 - back), w); aim(Pp, 'RightForeArm', new THREE.Vector3(0, 1, -0.3 - back), w); aim(Pp, 'LeftForeArm', new THREE.Vector3(0, 1, -0.3 - back), w); } };
    const cast = [thrower,
      { id: 'r2', k: [[0, 90, 47], [T0, 90.3, 47], [T0 + 1.3, 91.3, 46.4]] },
      { id: 'r3', k: [[0, 80, 58], [3, 82, 56]] },
      { id: 'b1', k: [[0, 85, 41], [T0 + 1, 87, 43]] }, { id: 'b2', k: [[0, 86, 31], [T0 + 1, 87, 35]] },
      { id: 'b3', k: [[0, 81, 57], [T0 + 1.2, 85, 54]] }, { id: 'b4', k: [76, 61] },
      { id: 'gk', k: [101, 36] }];
    let b;
    if (u < T0) { const P = POOL.r1; const hv = new THREE.Vector3(); P.m.visible && P.bones.RightHand.getWorldPosition(hv); b = null; }
    else b = pass([74, 68.6], [91.8, 46.6], u, T0, T0 + 1.2, 2.2);
    if (b) b.z += 2.3 * (1 - prog(u, T0, T0 + 1.2));
    return {
      pt: u, cast, ball: b, ballInHands: u < T0 ? 'r1' : null, cam: camKeys([[0, 80, 59, 24], [5.9, 84, 56, 23]], u), fadeIn: true,
      line: { x: 86, g: prog(u, 0.3, 1.0), zone: prog(u, 0.6, 1.2) },
      tags: [u > 0.3 && u < T0 + 0.3 && { id: 'r1', text: 'Einwurf', c: '#c8102e' }, u > T0 + 1.1 && { id: 'r2', text: 'kein Abseits', c: GRN, dark: true }].filter(Boolean),
      verdict: u > 2.9 ? { ok: true, text: 'EINWURF · ABSTOSS · ECKSTOSS: KEIN ABSEITS', a: prog(u, 2.9, 3.2) } : null
    };
  } },

{ id: 'passive', chapter: 'Passives Abseits', d: 12.2, voice: [['N16', 0.5], ['N17', 4.1]],
  frame(lt) {
    const P = 5.0;
    const cast = [
      { id: 'r1', k: [[0, 59, 41], [P - 0.3, 62, 40]] },
      { id: 'r2', k: [[0, 92, 59], [6, 93, 58], [12, 93.5, 57.5]], face: [96, 34] },
      { id: 'r3', k: [[0, 77, 33], [P, 80, 33], [P + 1.6, 94.2, 31.3], [P + 2.2, 96, 31.8]] },
      { id: 'r4', k: [[0, 66, 22], [P + 3, 74, 25]] },
      { id: 'b1', k: [[0, 83, 28], [P + 0.3, 83.2, 28], [P + 2.2, 91, 29]] },
      { id: 'b2', k: [[0, 84, 44], [P + 0.3, 84.2, 44], [P + 2.4, 90, 38]] },
      { id: 'b3', k: [[0, 78, 15], [P + 2.6, 84, 19]] }, { id: 'b4', k: [[0, 79, 56], [P + 2.6, 82, 53]] },
      { id: 'b5', k: [[0, 70, 38], [P + 2, 74, 37]] },
      { id: 'gk', k: [[0, 101, 34], [P + 1.4, 101, 33], [P + 2.0, 102, 31, 'out']] },
      { id: 'ar', k: [[0, 83, -1.3], [P, 84, -1.3], [P + 3, 90, -1.3]], face: [84, 30] }];
    let b;
    if (lt < P) { const r1 = track(cast[0].k, lt); b = { x: r1.x + 0.6, y: r1.y + 0.3, z: 0 }; }
    else if (lt < P + 1.8) b = pass([62.6, 40.3], [94.8, 31.5], lt, P, P + 1.6);
    else b = pass([94.8, 31.5], [105.8, 36.4], lt, P + 1.8, P + 2.15, 0.7);
    return {
      pt: lt, cast, ball: b, cam: camKeys([[0, 80, 40, 25], [5, 82, 40, 25], [7.4, 92, 38, 25], [12.2, 92, 40, 26]], lt),
      line: { x: 84, g: prog(lt, 0.8, 1.8) * (1 - prog(lt, 6.4, 7.0)), zone: prog(lt, 1.2, 2.0) * (1 - prog(lt, 6.4, 7.0)) },
      spots: lt > 1.5 ? [{ id: 'r2', c: '#9aa6b8' }] : [],
      tags: [lt > 1.5 && { id: 'r2', text: 'im Abseits – aber passiv', c: '#5d6878' }, lt > 2.4 && lt < 6.4 && { id: 'r3', text: 'kein Abseits', c: GRN, dark: true }].filter(Boolean),
      verdict: lt > 8.4 ? { ok: true, text: 'TOR ZÄHLT', a: prog(lt, 8.4, 8.7) } : null,
      net: lt > P + 2.15 ? prog(lt, P + 2.15, P + 2.9) : 0
    };
  } },

{ id: 'summary', chapter: 'Zusammenfassung', d: 16, voice: [['N18', 0.8]],
  frame(lt) {
    const k = ease(prog(lt, 0, 16));
    const cam = { pos: new THREE.Vector3(lerp(-6, 8, k), lerp(36, 32, k), 60), look: new THREE.Vector3(lerp(20, 28, k), 0, -4), fov: 34 };
    return { pt: lt, cast: castFrom(F), ball: { x: 57.3, y: 40.5, z: 0 }, cam, line: { x: 83, g: 1, zone: 1 }, summary: true };
  } }
];
let acc = 0; SCENES.forEach(s => { s.start = acc; acc += s.d; });
const TOTAL = acc;
const CUES = []; SCENES.forEach(s => s.voice.forEach(([id, t]) => CUES.push({ id, t: s.start + t })));
const WHISTLES = [SCENES[3].start + 14.2];
const CHEERS = [SCENES[2].start + 13.6, SCENES[6].start + 7.2];
const SUBS = []; CUES.forEach(c => chunks(c.id).forEach(ch => SUBS.push({ a: c.t + ch.a, b: c.t + ch.b + 0.25, text: ch.text })));

/* ------------------------------------------------------------------ 2D overlay */
function rr(c, x, y, w, h, r) { c.beginPath(); c.roundRect(x, y, w, h, r); }
function proj(v) { const p = v.clone().project(camera); return { x: (p.x + 1) / 2 * W, y: (1 - p.y) / 2 * H, vis: p.z < 1 }; }
function tag(c, x, y, text, col, dark, a = 1, leader = 46) {
  c.save(); c.globalAlpha = a;
  c.font = `bold 25px ${FONT}`;
  const tw = c.measureText(text).width, w = tw + 30, h = 40, ty = y - leader - h;
  c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 2;
  if (leader > 0) { c.beginPath(); c.moveTo(x, y); c.lineTo(x, ty + h); c.stroke(); }
  c.shadowColor = 'rgba(0,0,0,.35)'; c.shadowBlur = 10; c.shadowOffsetY = 3;
  c.fillStyle = col; c.fillRect(x - w / 2, ty, w, h); c.shadowColor = 'transparent';
  c.fillStyle = dark ? '#0d1117' : '#ffffff'; c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillText(text, x, ty + h / 2 + 1);
  c.restore();
}
function bug(c, chapter, idx, a) {
  if (a <= 0) return;
  c.save(); c.globalAlpha = a;
  c.font = `bold 20px ${FONT}`; const t1 = 'REGELKUNDE · ABSEITS';
  c.font = `bold 30px ${FONT}`; const w2 = c.measureText(chapter).width;
  const w = Math.max(320, w2 + 70);
  c.fillStyle = 'rgba(10,15,24,.82)'; c.fillRect(54, 46, w, 86);
  c.fillStyle = YEL; c.fillRect(54, 46, 8, 86);
  c.fillStyle = YEL; c.font = `bold 19px ${FONT}`; c.textBaseline = 'alphabetic'; c.textAlign = 'left';
  if (c.letterSpacing !== undefined) c.letterSpacing = '2px';
  c.fillText(t1, 82, 78);
  if (c.letterSpacing !== undefined) c.letterSpacing = '0px';
  c.fillStyle = '#fff'; c.font = `bold 30px ${FONT}`; c.fillText(chapter, 82, 116);
  c.restore();
}
function verdict(c, v) {
  if (!v || v.a <= 0) return;
  const col = v.color || (v.ok ? '#1f9d55' : '#d21f2b');
  c.save(); c.globalAlpha = Math.min(1, v.a * 1.4);
  c.font = `bold 46px ${FONT}`;
  const tw = c.measureText(v.text).width, w = tw + 150, h = 84, x = 54 - (1 - easeOut(v.a)) * 60, y = H - 270;
  c.fillStyle = col; c.beginPath(); c.moveTo(x, y); c.lineTo(x + w, y); c.lineTo(x + w - 24, y + h); c.lineTo(x, y + h); c.fill();
  c.fillStyle = 'rgba(0,0,0,.18)'; c.fillRect(x, y + h - 8, w - 22, 8);
  // icon
  c.strokeStyle = '#fff'; c.lineWidth = 8; c.lineCap = 'round'; c.lineJoin = 'round';
  c.beginPath();
  if (v.color) { c.fillStyle = '#fff'; c.fillRect(x + 36, y + 22, 6, 42); c.fillRect(x + 42, y + 22, 26, 18); }
  else if (v.ok) { c.moveTo(x + 32, y + 44); c.lineTo(x + 48, y + 60); c.lineTo(x + 74, y + 26); }
  else { c.moveTo(x + 34, y + 24); c.lineTo(x + 70, y + 60); c.moveTo(x + 70, y + 24); c.lineTo(x + 34, y + 60); }
  c.stroke();
  c.fillStyle = '#fff'; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText(v.text, x + 100, y + h / 2 + 2);
  c.restore();
}
function subtitle(c, T) {
  const s = SUBS.find(s => T >= s.a && T < s.b);
  if (!s) return;
  const a = prog(T, s.a, s.a + 0.12) * (1 - prog(T, s.b - 0.12, s.b));
  c.save(); c.globalAlpha = a;
  c.font = `38px ${FONT}`;
  // wrap into max 2 lines
  const words = s.text.split(' '), lines = [];
  let cur = '';
  words.forEach(wd => { const t = cur ? cur + ' ' + wd : wd; if (c.measureText(t).width > 1300 && cur) { lines.push(cur); cur = wd; } else cur = t; });
  lines.push(cur);
  const lh = 52, by = H - 64 - (lines.length - 1) * lh;
  lines.forEach((ln, i) => {
    const tw = c.measureText(ln).width;
    c.fillStyle = 'rgba(0,0,0,.62)'; c.fillRect(W / 2 - tw / 2 - 18, by + i * lh - 34, tw + 36, 50);
    c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'alphabetic'; c.fillText(ln, W / 2, by + i * lh + 3);
  });
  c.restore();
}
function titleCard(c, lt) {
  const a = prog(lt, 0.8, 1.8) * (1 - prog(lt, 9.4, 10.3));
  if (a <= 0) return;
  c.save();
  const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.55, `rgba(5,9,16,${0.55 * a})`); g.addColorStop(1, `rgba(5,9,16,${0.75 * a})`);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.globalAlpha = a; c.textAlign = 'left'; c.textBaseline = 'alphabetic';
  const x = 140, y = H - 330 + (1 - easeOut(a)) * 30;
  c.fillStyle = YEL; c.font = `bold 30px ${FONT}`; if (c.letterSpacing !== undefined) c.letterSpacing = '6px';
  c.fillText('REGELKUNDE', x, y - 120);
  if (c.letterSpacing !== undefined) c.letterSpacing = '0px';
  c.fillStyle = '#fff'; c.font = `bold 128px ${FONT}`; c.fillText('Die Abseitsregel', x - 6, y);
  c.fillStyle = YEL; c.fillRect(x, y + 34, 220 * easeOut(prog(lt, 1.4, 2.4)), 7);
  c.fillStyle = '#d7dee8'; c.font = `44px ${FONT}`; c.fillText('einfach erklärt', x, y + 104);
  c.restore();
}
function summaryCard(c, lt) {
  const a = prog(lt, 0.2, 1.0);
  c.save();
  const g = c.createLinearGradient(0, 0, W, 0); g.addColorStop(0, `rgba(6,10,18,${0.88 * a})`); g.addColorStop(0.62, `rgba(6,10,18,${0.7 * a})`); g.addColorStop(1, 'rgba(6,10,18,0)');
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.globalAlpha = a; c.textAlign = 'left'; c.textBaseline = 'alphabetic';
  c.fillStyle = YEL; c.font = `bold 26px ${FONT}`; if (c.letterSpacing !== undefined) c.letterSpacing = '5px';
  c.fillText('ZUSAMMENFASSUNG', 140, 210);
  if (c.letterSpacing !== undefined) c.letterSpacing = '0px';
  c.fillStyle = '#fff'; c.font = `bold 64px ${FONT}`; c.fillText('Das Wichtigste', 136, 290);
  const items = [[2.0, 'Es zählt der Moment der Ballabgabe.'], [4.6, 'Näher am Tor als Ball und vorletzter Gegner = Abseits.'], [9.7, 'Gleiche Höhe ist kein Abseits.'], [11.6, 'Bestraft wird nur aktives Eingreifen.']];
  items.forEach(([t, text], i) => {
    const p = prog(lt, t, t + 0.45); if (p <= 0) return;
    const y = 400 + i * 118;
    c.save(); c.globalAlpha = a * p; c.translate((1 - easeOut(p)) * -40, 0);
    c.fillStyle = 'rgba(255,255,255,.07)'; c.fillRect(140, y - 56, 1000, 92);
    c.fillStyle = YEL; c.fillRect(140, y - 56, 8, 92);
    c.fillStyle = YEL; c.font = `bold 46px ${FONT}`; c.fillText(String(i + 1), 176, y + 6);
    c.fillStyle = '#fff'; c.font = `36px ${FONT}`; c.fillText(text, 236, y + 2);
    c.restore();
  });
  c.restore();
}

/* ------------------------------------------------------------------ frame */
function sceneAt(T) { for (let i = SCENES.length - 1; i >= 0; i--) if (T >= SCENES[i].start) return i; return 0; }
function renderFrame(T) {
  T = clamp(T, 0, TOTAL - 1e-3);
  const idx = sceneAt(T), S = SCENES[idx], lt = T - S.start;
  const st = S.frame(lt);
  // ball
  const bp = st.ball;
  if (bp) {
    ball.visible = true; ball.position.copy(V(bp.x, bp.y, 0.11 + (bp.z || 0)));
    ball.rotation.set(bp.x * 2.1, 0, -bp.y * 2.3);
  }
  poseCast(st.cast, st.pt, bp || { x: 80, y: 50 });
  if (st.ballInHands) {
    const P = POOL[st.ballInHands]; P.m.updateMatrixWorld(true);
    const l = bonePos(st.ballInHands, 'LeftHand'), r = bonePos(st.ballInHands, 'RightHand');
    ball.visible = true; ball.position.copy(l.add(r).multiplyScalar(0.5)); ball.position.y += 0.08;
  } else if (!bp) ball.visible = false;
  // ground graphics
  const L = st.line;
  if (L && L.g > 0) { setLine(lineMain, L.x, 0.14, ease(L.g)); setLine(lineGlow, L.x, 0.7, ease(L.g)); setStrip(zone, L.x, 105, ease(L.zone || 0), 0.2 * (L.zone || 0)); }
  else { lineMain.visible = lineGlow.visible = false; zone.visible = false; }
  const VL = st.varLines;
  if (VL && VL.g > 0) {
    const g = ease(VL.g);
    setLine(lineDef, VL.def, 0.12, g);
    lineAtt.material.color.set(VL.ok ? 0x2fd27a : 0xff3b3b);
    setLine(lineAtt, VL.att + (VL.same ? 0.0 : 0), 0.12, VL.same ? 0 : g);
    if (!VL.ok) { zone.material.color.set(0xff3b3b); setStrip(zone, VL.def, VL.att, g, 0.32); } else if (!L) zone.visible = false;
  } else { lineDef.visible = false; lineAtt.visible = false; }
  if (VL && VL.same) { lineDef.material.color.set(0x2fd27a); } else lineDef.material.color.set(0x29c8ff);
  if (st.half) setStrip(half, 0, 52.5, 1, 0.2 * st.half); else half.visible = false;
  if (st.arrow && st.arrow.a > 0) { arrow.visible = true; arrow.material.opacity = 0.55 * st.arrow.a; arrow.position.copy(V(st.arrow.x, st.arrow.y, 0.04)); arrow.scale.set(lerp(0.2, 1, easeOut(st.arrow.a)), 1, 1); } else arrow.visible = false;
  spots.forEach(s => s.visible = false);
  (st.spots || []).forEach((s, i) => {
    const m = spots[i], P = POOL[s.id]; m.visible = true;
    m.position.set(P.m.position.x, 0.04, P.m.position.z); m.scale.setScalar(2.6 + 0.15 * Math.sin(T * 5)); m.material.color.set(s.c);
  });
  // net shake
  netGroups[0].position.x = st.net ? Math.sin(st.net * 18) * 0.25 * (1 - st.net) : 0;
  // camera
  camera.position.copy(st.cam.pos); camera.fov = st.cam.fov; camera.updateProjectionMatrix(); camera.lookAt(st.cam.look);
  renderer.render(scene, camera);

  // composite
  const c = octx;
  c.save();
  c.filter = st.frozen ? 'saturate(0.55) brightness(0.92) contrast(1.06)' : 'none';
  c.drawImage(renderer.domElement, 0, 0, W, H);
  c.filter = 'none';
  // vignette
  const vg = c.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${st.frozen ? 0.5 : 0.28})`);
  c.fillStyle = vg; c.fillRect(0, 0, W, H);
  c.restore();
  if (st.flashAt !== undefined && lt >= st.flashAt) { const fa = 0.55 * (1 - prog(lt, st.flashAt, st.flashAt + 0.3)); if (fa > 0) { c.fillStyle = `rgba(255,255,255,${fa})`; c.fillRect(0, 0, W, H); } }
  if (st.frozen) {
    c.save(); c.globalAlpha = prog(lt, st.flashAt, st.flashAt + 0.3);
    c.fillStyle = 'rgba(10,15,24,.82)'; c.fillRect(W - 54 - 470, 46, 470, 64);
    c.fillStyle = YEL; c.fillRect(W - 54 - 470, 46, 8, 64);
    c.fillStyle = '#fff'; c.fillRect(W - 54 - 440, 64, 9, 28); c.fillRect(W - 54 - 424, 64, 9, 28);
    c.font = `bold 26px ${FONT}`; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('STANDBILD · BALLABGABE', W - 54 - 396, 79);
    c.restore();
  }
  // tags
  (st.tags || []).forEach(t => {
    const p = t.pos ? proj(t.pos) : proj(headPos(t.id, t.lift !== undefined ? t.lift : 0.32));
    if (p.vis) tag(c, p.x, p.y, t.text, t.c, t.dark, 1, t.pos ? 0 : 46);
  });
  (st.bodyLabels || []).forEach(b => {
    const p = proj(bonePos(b.bone[0], b.bone[1]));
    c.save(); c.globalAlpha = b.a;
    c.fillStyle = b.c; c.beginPath(); c.arc(p.x, p.y, 9, 0, Math.PI * 2); c.fill();
    c.strokeStyle = '#fff'; c.lineWidth = 3; c.stroke();
    const lx = p.x + (b.dx || -160), ly = p.y + (b.dy || 0);
    c.strokeStyle = 'rgba(255,255,255,.9)'; c.lineWidth = 2; c.beginPath(); c.moveTo(p.x, p.y); c.lineTo(lx, ly); c.stroke();
    c.font = `bold 28px ${FONT}`; const tw = c.measureText(b.text).width;
    const bx = b.dx > 0 ? lx : lx - tw - 28;
    c.fillStyle = b.c; c.fillRect(bx, ly - 22, tw + 28, 44);
    c.fillStyle = b.c === GRN ? '#0d1117' : '#fff'; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText(b.text, bx + 14, ly + 1);
    c.restore();
  });
  if (st.whistleAt && lt > st.whistleAt) {
    const a = prog(lt, st.whistleAt, st.whistleAt + 0.2) * (1 - prog(lt, st.whistleAt + 1.6, st.whistleAt + 2));
    if (a > 0) { c.save(); c.globalAlpha = a; c.fillStyle = 'rgba(10,15,24,.82)'; c.fillRect(W - 54 - 250, 46, 250, 64); c.fillStyle = YEL; c.fillRect(W - 54 - 250, 46, 8, 64); c.fillStyle = '#fff'; c.font = `bold 28px ${FONT}`; c.textBaseline = 'middle'; c.fillText('PFIFF', W - 54 - 216, 79); c.restore(); }
  }
  if (st.title) titleCard(c, lt);
  if (st.summary) summaryCard(c, lt);
  verdict(c, st.verdict);
  bug(c, S.chapter, idx, idx === 0 ? 0 : (idx === SCENES.length - 1 ? 1 - prog(lt, 0, 0.6) : prog(lt, 0.2, 0.7)));
  subtitle(c, T);
  // scene fades
  let fade = Math.max(1 - prog(lt, 0, 0.35), prog(lt, S.d - 0.3, S.d));
  if (idx === 0) fade = Math.max(1 - prog(lt, 0, 0.8), prog(lt, S.d - 0.3, S.d));
  if (idx === SCENES.length - 1) fade = Math.max(1 - prog(lt, 0, 0.35), prog(lt, S.d - 1.2, S.d));
  if (S.id === 'except') fade = Math.max(fade, 1 - clamp(Math.abs(lt - 5.7) / 0.28, 0, 1));
  if (fade > 0) { c.fillStyle = `rgba(0,0,0,${fade})`; c.fillRect(0, 0, W, H); }
}
window.renderFrame = T => { renderFrame(T); return true; };
window.grab = (q = 0.92) => out.toDataURL('image/jpeg', q).split(',')[1];
window.FILM = { total: TOTAL, cues: CUES, whistles: WHISTLES, cheers: CHEERS, fps: 25 };
renderFrame(0);
window.READY = true;
