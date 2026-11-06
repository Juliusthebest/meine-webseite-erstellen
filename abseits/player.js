import * as THREE from 'three';
import * as SU from 'three/addons/utils/SkeletonUtils.js';
const SKIN_BASE = new THREE.Color('#d6a184');
function recolor(o, fn, keepTri) {
  const g = o.geometry.clone(), pos = g.attributes.position, cnt = pos.count, col = new Float32Array(cnt * 3), c = new THREE.Color(), v = new THREE.Vector3();
  for (let i = 0; i < cnt; i++) { v.fromBufferAttribute(pos, i); fn(v, c); col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  if (keepTri) {
    const idx = g.index.array, keep = [], a = new THREE.Vector3(), b = new THREE.Vector3(), d = new THREE.Vector3();
    for (let i = 0; i < idx.length; i += 3) { a.fromBufferAttribute(pos, idx[i]); b.fromBufferAttribute(pos, idx[i + 1]); d.fromBufferAttribute(pos, idx[i + 2]); if (keepTri(a, b, d)) keep.push(idx[i], idx[i + 1], idx[i + 2]); }
    g.setIndex(keep);
  }
  o.geometry = g;
  o.material = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.78, metalness: 0, side: THREE.DoubleSide });
}
export function makePlayer(base, kit) {
  const m = SU.clone(base);
  const skin = new THREE.Color(kit.skin || '#ffffff');
  const bodySkin = SKIN_BASE.clone().multiply(skin);
  m.traverse(o => {
    if (!o.isMesh) return;
    o.castShadow = true; o.frustumCulled = false;
    const n = o.name;
    if (n === 'Wolf3D_Headwear') { o.visible = false; return; }
    if (n === 'Wolf3D_Beard') { o.visible = !!kit.beard; return; }
    if (n === 'Wolf3D_Outfit_Top') recolor(o, (v, c) => { const ax = Math.abs(v.x); if (ax > 0.34) c.copy(bodySkin); else if (ax > 0.31) c.set(kit.collar); else c.set(kit.shirt); },
      (a, b, d) => Math.min(a.y, b.y, d.y) > 0.88);
    else if (n === 'Wolf3D_Outfit_Bottom') recolor(o, (v, c) => { if (v.y > 0.62) c.set(kit.shorts); else if (v.y > 0.47) c.copy(bodySkin); else c.set(kit.socks); });
    else if (n === 'Wolf3D_Outfit_Footwear') recolor(o, (v, c) => c.set(kit.boots));
    else if (n === 'Wolf3D_Body') { o.material = o.material.clone(); o.material.color.copy(skin); }
    else if (n === 'Wolf3D_Head') { o.material = o.material.clone(); o.material.color.copy(skin); }
  });
  return m;
}
export const KITS = {
  red: { shirt: '#c8102e', collar: '#f4f4f4', shorts: '#f4f4f4', socks: '#c8102e', boots: '#151515' },
  blue: { shirt: '#1f4fa0', collar: '#f4f4f4', shorts: '#13254a', socks: '#f4f4f4', boots: '#e9e9e9' },
  keeper: { shirt: '#b5d334', collar: '#151515', shorts: '#151515', socks: '#b5d334', boots: '#151515' },
  ref: { shirt: '#161616', collar: '#d8f23a', shorts: '#161616', socks: '#161616', boots: '#111111' }
};
export const SKINS = ['#ffffff', '#f2d6c4', '#c99a7a', '#8a5a40', '#e8c0a8', '#6e4530'];
