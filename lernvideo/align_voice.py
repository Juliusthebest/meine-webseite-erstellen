"""Eigene Sprachaufnahmen aufbereiten und den Sätzen im Drehbuch zuordnen.

1. Aufbereitung (ffmpeg): Übersteuerung glätten, Brummen/Rauschen reduzieren, Stimme klarer,
   Lautstärke angleichen (EBU R128, -16 LUFS).
2. Zuordnung: Die Aufnahme wird per DTW (Dynamic Time Warping auf MFCC-Merkmalen) mit derselben
   Satzfolge in Computerstimme verglichen. So ergibt sich, wo jeder Satz beginnt; die Grenze wird
   anschließend auf die nächste Atempause in der Aufnahme geschoben.

Die Aufnahmen liegen in aufnahmen/ (00.m4a … 05.m4a, nicht im Git).
"""
import os
import subprocess
import tempfile
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REC_DIR = os.path.join(HERE, "aufnahmen")
FEAT_SR = 16000
HOP = 160  # 10 ms

CLEAN = ("adeclip,highpass=f=75,afftdn=nf=-30:tn=1,"
         "equalizer=f=200:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.4:g=2.5,deesser=i=0.35,"
         "acompressor=threshold=-21dB:ratio=2.8:attack=6:release=90:makeup=2,"
         "loudnorm=I=-16:LRA=7:TP=-1.5")


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return a, w.getframerate()


def clean(src, dst, sr):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-af", CLEAN, "-ar", str(sr), dst],
                   check=True)


def frames_db(a, sr, hop_s=0.01):
    hop = int(sr * hop_s)
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1))
    return 20 * np.log10(rms + 1e-9)


def gaps(a, sr, min_len=0.12):
    db = frames_db(a, sr)
    floor, peak = np.percentile(db, 10), np.percentile(db, 95)
    sil = db < floor + 0.28 * (peak - floor)
    out, i = [], 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]:
                j += 1
            if (j - i) * 0.01 >= min_len:
                out.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return out, sil


def feats(a, sr):
    import librosa
    if sr != FEAT_SR:
        a = librosa.resample(a, orig_sr=sr, target_sr=FEAT_SR)
    m = librosa.feature.mfcc(y=a, sr=FEAT_SR, n_mfcc=21, n_fft=512, hop_length=HOP, n_mels=40)[1:]
    d = librosa.feature.delta(m)
    f = np.vstack([m, d])
    return (f - f.mean(axis=1, keepdims=True)) / (f.std(axis=1, keepdims=True) + 1e-6)


def align(user, usr_sr, sentences, tts_fn):
    """Gibt Startzeiten (s) der Sätze in der Aufnahme zurück, plus Diagnose."""
    import librosa
    ref, starts, durs = [], [], []
    t = 0.0
    for s in sentences:
        a = tts_fn(s)
        starts.append(t)
        durs.append(len(a) / FEAT_SR)
        ref.append(a)
        ref.append(np.zeros(int(0.25 * FEAT_SR), np.float32))
        t += len(a) / FEAT_SR + 0.25
    ref = np.concatenate(ref)
    # Stille am Rand der Aufnahme abschneiden
    g, sil = gaps(user, usr_sr)
    speech = np.where(~sil)[0]
    t0, t1 = speech[0] * 0.01, (speech[-1] + 1) * 0.01
    u = user[int(t0 * usr_sr): int(t1 * usr_sr)]
    X, Y = feats(ref, FEAT_SR), feats(u, usr_sr)
    _, wp = librosa.sequence.dtw(X=X, Y=Y, metric="cosine", global_constraints=True, band_rad=0.3)
    wp = wp[::-1]
    mapped = []
    for st in starts:
        r = int(st * FEAT_SR / HOP)
        js = wp[wp[:, 0] == min(r, wp[-1, 0]), 1]
        mapped.append(t0 + float(np.median(js)) * HOP / FEAT_SR)
    mapped[0] = t0
    # auf Atempausen schieben
    snapped, info = [], []
    for k, m in enumerate(mapped):
        if k == 0:
            snapped.append(max(0.0, t0 - 0.06))
            info.append("Anfang")
            continue
        cand = [(abs((a + b) / 2 - m), a, b) for a, b in g if abs((a + b) / 2 - m) < 0.9 and t0 < a < t1]
        if cand:
            _, a, b = min(cand)
            snapped.append(max(a, b - 0.06))
            info.append(f"Pause {b - a:.2f}s")
        else:
            # keine Pause: am leisesten Punkt in der Nähe schneiden
            db = frames_db(user, usr_sr)
            lo, hi = int((m - 0.4) / 0.01), int((m + 0.4) / 0.01)
            j = lo + int(np.argmin(db[lo:hi]))
            snapped.append(j * 0.01)
            info.append("leise Stelle")
    return snapped, t1, mapped, durs, info


def segments(user, sr, starts, end):
    """Schneidet die Sätze aus; Stille am Rand wird bis auf kurze Reste entfernt."""
    out = []
    bounds = starts + [end + 0.1]
    for k in range(len(starts)):
        a = user[int(bounds[k] * sr): int(bounds[k + 1] * sr)]
        db = frames_db(a, sr)
        floor, peak = np.percentile(db, 5), np.percentile(db, 95)
        on = np.where(db > floor + 0.25 * (peak - floor))[0]
        if len(on):
            s, e = max(0, on[0] * 0.01 - 0.05), min(len(a) / sr, (on[-1] + 1) * 0.01 + 0.12)
            a = a[int(s * sr): int(e * sr)]
        fade = int(0.012 * sr)
        if len(a) > 2 * fade:
            a = a.copy()
            a[:fade] *= np.linspace(0, 1, fade)
            a[-fade:] *= np.linspace(1, 0, fade)
        out.append(a)
    return out


def tts16(s):
    """Computerstimme (16 kHz) als Vergleich für die Zuordnung."""
    from flat_engine import to_say
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "t.wav")
        subprocess.run(["pico2wave", "-l", "de-DE", "-w", p, to_say(s)], check=True)
        a, _ = read_wav(p)
    db = frames_db(a, FEAT_SR)
    on = np.where(db > db.max() - 45)[0]
    return a[on[0] * HOP: (on[-1] + 1) * HOP] if len(on) else a


def prepare(clip_idx, scenes, out_sr, tts_fn=tts16, verbose=True):
    """Liefert {(szene, satz): audio} in out_sr (Werte im int16-Maßstab) für eine Clip-Nummer."""
    src = None
    for ext in ("m4a", "mp3", "wav", "mov", "ogg"):
        p = os.path.join(REC_DIR, f"{clip_idx:02d}.{ext}")
        if os.path.exists(p):
            src = p
    if src is None:
        return None
    keys = [(si, bi) for si, s in enumerate(scenes) for bi, _ in enumerate(s["beats"])]
    sentences = [scenes[si]["beats"][bi]["sub"] for si, bi in keys]
    with tempfile.TemporaryDirectory() as tmp:
        cw = os.path.join(tmp, "clean.wav")
        clean(src, cw, out_sr)
        user, sr = read_wav(cw)
    starts, end, mapped, durs, info = align(user, sr, sentences, tts_fn)
    segs = segments(user, sr, starts, end)
    if verbose:
        print(f"\nClip {clip_idx:02d}: {len(sentences)} Sätze, Aufnahme {len(user) / sr:.1f}s")
        for k, s in enumerate(sentences):
            nxt = starts[k + 1] if k + 1 < len(starts) else end
            print(f"  {starts[k]:6.2f}s  {nxt - starts[k]:5.2f}s (Computer {durs[k]:4.1f}s)  {info[k]:12s} {s[:60]}")
    return {key: seg * 32768 * 0.97 for key, seg in zip(keys, segs)}
