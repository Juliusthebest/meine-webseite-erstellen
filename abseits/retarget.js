import * as THREE from 'three';
// Retarget a clip from source rig to target rig via world-space rotation deltas (both rigs in T-pose bind).
export function retarget(srcScene, srcClip, tgtScene, mapName, fps = 30) {
  const sb = {}, tb = {}, tList = [];
  srcScene.traverse(n => { if (n.isBone) sb[n.name] = n; });
  tgtScene.traverse(n => { if (n.isBone) { tb[n.name] = n; tList.push(n); } });
  srcScene.updateMatrixWorld(true); tgtScene.updateMatrixWorld(true);
  const wq = o => o.getWorldQuaternion(new THREE.Quaternion());
  const s0 = {}, t0 = {}, map = {};
  for (const b of tList) { const sn = mapName(b.name); if (sb[sn]) { map[b.name] = sb[sn]; s0[b.name] = wq(sb[sn]); } t0[b.name] = wq(b); }
  const tgtRootWQ = b => wq(b.parent);
  const mixer = new THREE.AnimationMixer(srcScene); const act = mixer.clipAction(srcClip); act.play();
  const n = Math.max(2, Math.round(srcClip.duration * fps) + 1), times = [], vals = {}, hipPos = [];
  tList.forEach(b => vals[b.name] = []);
  const th = tList.find(b => /Hips$/.test(b.name)), sh = sb[mapName(th.name)];
  const sh0 = sh.getWorldPosition(new THREE.Vector3()), th0 = th.getWorldPosition(new THREE.Vector3());
  const ratio = th0.y / sh0.y;
  const tParent0 = {}; tList.forEach(b => tParent0[b.name] = wq(b.parent));
  for (let i = 0; i < n; i++) {
    const t = Math.min(srcClip.duration, i / fps); times.push(t);
    mixer.setTime(t); srcScene.updateMatrixWorld(true);
    const tw = {};
    for (const b of tList) {
      let w;
      if (map[b.name]) { w = wq(map[b.name]).multiply(s0[b.name].clone().invert()).multiply(t0[b.name]); }
      else { const pw = tw[b.parent.name] || tParent0[b.name]; w = pw.clone().multiply(b.quaternion); }
      tw[b.name] = w;
      const pw = tw[b.parent.name] || tParent0[b.name];
      const local = pw.clone().invert().multiply(w);
      vals[b.name].push(local.x, local.y, local.z, local.w);
    }
    const p = sh.getWorldPosition(new THREE.Vector3()).sub(sh0).multiplyScalar(ratio);
    const lp = th.position.clone().add(p); // target hips parent assumed unrotated, unit scale
    hipPos.push(lp.x * 0, lp.y, lp.z * 0);
  }
  const tracks = tList.filter(b => map[b.name]).map(b => new THREE.QuaternionKeyframeTrack(b.name + '.quaternion', times, vals[b.name]));
  tracks.push(new THREE.VectorKeyframeTrack(th.name + '.position', times, hipPos));
  return new THREE.AnimationClip(srcClip.name, srcClip.duration, tracks);
}
