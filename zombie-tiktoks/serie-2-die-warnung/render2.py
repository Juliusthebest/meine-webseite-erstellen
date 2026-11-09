"""Rendert einen Teil der Serie „POV: Mitten in der Klausur kommt eine Warnung aufs Handy“.

Aufruf: python3 render2.py <teil 1..7> [ausgabeordner]
Umgebungsvariablen: VOICE_DIR (Piper-Stimmen), WORK_DIR (Zwischendateien), STILLS="3,10" (nur Standbilder)
"""
import math, os, random, subprocess, sys, wave, hashlib
import numpy as np
import cairo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comic import *
from scenes import SCENES, SW, SH
from story2 import PARTS

W, H, FPS, SR = 1080, 1920, 24, 44100
VOICE_DIR = os.environ.get("VOICE_DIR", "voices")

# ------------------------------------------------------------------ Stimmen
# Sprecher -> (Modell, Tonhöhe, Tempo, Zusatzfilter, Untertitelfarbe)
YEL, GRN, WHT, PNK, BLU = (1, 0.84, 0.15), (0.55, 0.95, 0.55), (1, 1, 1), (1, 0.7, 0.85), (0.6, 0.85, 1)
VOICES = {
    "DU":     ("de-pavoque-low", 1.10, 1.02, "", WHT),
    "DENK":   ("de-pavoque-low", 1.10, 0.95, ",aecho=0.8:0.6:50:0.35", WHT),
    "NOAH":   ("de-thorsten-low", 1.14, 1.05, "", GRN),
    "WOLFF":  ("de-karlsson-low", 0.90, 1.0, "", YEL),
    "LEA":    ("de-kerstin-low", 1.08, 1.08, "", GRN),
    "SOMMER": ("de-ramona-low", 0.94, 0.98, "", YEL),
    "JONAS":  ("de-karlsson-low", 1.12, 1.05, "", GRN),
    "MAMA":   ("de-eva_k-x-low", 1.0, 1.0, "", PNK),
    "PA":     ("de-karlsson-low", 0.95, 0.95, ",highpass=f=350,lowpass=f=3200,aecho=0.8:0.7:90:0.45", YEL),
    "SOLDAT": ("de-pavoque-low", 0.86, 1.05, ",highpass=f=200", BLU),
    "FREMD":  ("de-kerstin-low", 0.95, 1.05, "", GRN),
}


def tts(spk, text, work):
    model, pitch, tempo, extra, _ = VOICES[spk]
    key = hashlib.md5(f"{spk}|{text}|{VOICES[spk]}".encode()).hexdigest()[:12]
    out = os.path.join(work, f"v_{spk}_{key}.wav")
    if os.path.exists(out):
        return out
    raw = out + ".raw.wav"
    subprocess.run(["python3", "-m", "piper", "-m", os.path.join(VOICE_DIR, model + ".onnx"),
                    "--sentence-silence", "0.12", "-f", raw], input=text.encode(), check=True, capture_output=True)
    sr_in = 16000
    filt = (f"asetrate={int(sr_in * pitch)},aresample=44100,atempo={tempo / pitch:.4f}{extra},"
            "loudnorm=I=-15:TP=-1.5,aformat=sample_fmts=s16:channel_layouts=mono")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", filt, "-ar", "44100", out], check=True)
    os.remove(raw)
    return out


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


# ------------------------------------------------------------------ Soundeffekte
def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def sfx(name, dur=None):
    rng = np.random.default_rng(abs(hash(name)) % 1000)
    if name == "alarm":           # Cell-Broadcast-Warnton
        n = int(SR * (dur or 3.0)); t = np.arange(n) / SR
        f = np.where((t * 2.2) % 1 < 0.5, 853, 960)
        s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
        return s * np.minimum(1, t / 0.02)
    if name == "multialarm":
        a = sfx("alarm", dur or 3.0)
        b = np.roll(a, int(SR * 0.13)) * 0.7
        c = np.roll(a, int(SR * 0.31)) * 0.5
        return (a + b + c) * 0.6
    if name == "gong":
        n = int(SR * 2.2); t = np.arange(n) / SR
        s = np.zeros(n)
        for i, f in enumerate((659, 523, 392)):
            o = int(i * 0.45 * SR); m = n - o
            s[o:] += np.sin(2 * np.pi * f * t[:m]) * env(m, 0.005, 0.7) * 0.4
        return s
    if name == "knock":
        n = int(SR * (dur or 2.0)); out = np.zeros(n); m = int(SR * 0.15); tt = np.arange(m) / SR
        hit = (np.sin(2 * np.pi * 95 * tt) + rng.standard_normal(m) * 0.5) * env(m, 0.001, 0.035)
        p = 0.0
        while p * SR + m < n:
            out[int(p * SR):int(p * SR) + m] += hit * (0.8 + 0.3 * rng.random())
            p += 0.18 + rng.random() * 0.12
        return out
    if name == "slam":
        n = int(SR * 1.2); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * np.cumsum(70 + 80 * np.exp(-t * 30)) / SR) * env(n, 0.001, 0.25)
                + rng.standard_normal(n) * env(n, 0.001, 0.04) * 0.6)
    if name == "metal":
        n = int(SR * 2.0); t = np.arange(n) / SR
        s = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((180, 0.5), (433, 0.3), (791, 0.2), (1210, 0.12)))
        return (s * env(n, 0.001, 0.5) + rng.standard_normal(n) * env(n, 0.001, 0.03)) * 0.7
    if name == "squeak":
        n = int(SR * 1.2); t = np.arange(n) / SR
        f = 600 + 300 * np.sin(2 * np.pi * 1.3 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / t[-1]) * 0.25
    if name == "click":
        n = int(SR * 0.1)
        return rng.standard_normal(n) * env(n, 0.0005, 0.008) * 0.8
    if name == "scrape":
        n = int(SR * (dur or 1.5)); t = np.arange(n) / SR
        s = smooth(rng.standard_normal(n), 6) * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * t))
        return s * np.sin(np.pi * t / t[-1]) * 0.6
    if name == "vibrate":
        n = int(SR * (dur or 1.2)); t = np.arange(n) / SR
        return np.sin(2 * np.pi * 150 * t) * ((t % 0.5) < 0.3) * 0.35
    if name == "ring":
        n = int(SR * (dur or 3.0)); t = np.arange(n) / SR
        notes = [784, 988, 1175, 988, 784, 659]
        s = np.zeros(n)
        for i in range(int(n / (0.18 * SR))):
            o = int(i * 0.18 * SR); m = min(int(0.17 * SR), n - o)
            f = notes[i % len(notes)]
            s[o:o + m] += np.sin(2 * np.pi * f * t[:m]) * env(m, 0.003, 0.08)
        return s * 0.5
    if name == "heart":
        n = int(SR * (dur or 3.0)); out = np.zeros(n); m = int(SR * 0.25); tt = np.arange(m) / SR
        th = np.sin(2 * np.pi * 50 * tt) * env(m, 0.004, 0.06)
        for st in range(0, n - m, int(SR * 0.75)):
            out[st:st + m] += th
            if st + int(SR * 0.22) + m < n:
                out[st + int(SR * 0.22):st + int(SR * 0.22) + m] += th * 0.7
        return out * 1.2
    if name == "growl":
        n = int(SR * (dur or 1.6)); t = np.arange(n) / SR
        f = 75 + 20 * np.sin(2 * np.pi * 2.3 * t)
        saw = ((np.cumsum(f) / SR) % 1.0) * 2 - 1
        return (saw * 0.35 + smooth(rng.standard_normal(n), 10) * 0.9) * np.clip(np.sin(np.pi * t / t[-1]), 0, 1) ** 1.5 * \
               (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t))
    if name == "scream":
        n = int(SR * (dur or 1.4)); t = np.arange(n) / SR
        f = 700 + 250 * np.sin(2 * np.pi * 0.6 * t) + 40 * np.sin(2 * np.pi * 6 * t)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR)
        return (s * 0.3 + smooth(rng.standard_normal(n), 3) * 0.25) * np.clip(np.sin(np.pi * t / t[-1]), 0, 1) ** 0.5 * 0.6
    if name == "crowd":
        n = int(SR * (dur or 3.0)); out = np.zeros(n)
        for k in range(6):
            sc = sfx("scream", 1.0 + rng.random())
            o = int(rng.random() * max(1, n - len(sc)))
            out[o:o + len(sc)] += sc * (0.2 + 0.25 * rng.random())
        out += smooth(rng.standard_normal(n), 30) * 0.5
        return out
    if name == "steps":
        n = int(SR * (dur or 2.0)); out = np.zeros(n); m = int(SR * 0.12); tt = np.arange(m) / SR
        st = smooth(rng.standard_normal(m), 15) * env(m, 0.005, 0.04) + np.sin(2 * np.pi * 80 * tt) * env(m, 0.002, 0.03)
        for p in np.arange(0, dur or 2.0, 0.55):
            o = int(p * SR)
            if o + m < n:
                out[o:o + m] += st
        return out * 0.9
    if name == "run":
        n = int(SR * (dur or 2.0)); out = np.zeros(n); m = int(SR * 0.1)
        st = smooth(rng.standard_normal(m), 10) * env(m, 0.002, 0.03)
        for p in np.arange(0, dur or 2.0, 0.28):
            o = int(p * SR)
            if o + m < n:
                out[o:o + m] += st
        return out
    if name == "hit":
        n = int(SR * 1.6); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(32 + 80 * np.exp(-t * 5)) / SR) * env(n, 0.002, 0.7) * 0.95 + \
               rng.standard_normal(n) * env(n, 0.001, 0.05) * 0.4
    if name == "bass":
        n = int(SR * 3.0); t = np.arange(n) / SR
        return np.sin(2 * np.pi * 41 * t) * np.minimum(1, t / 0.4) * np.exp(-t / 1.6) * 0.8
    if name == "whoosh":
        n = int(SR * 0.6); t = np.arange(n) / SR
        return smooth(rng.standard_normal(n), 20) * np.sin(np.pi * t / t[-1]) ** 2 * 1.3
    if name == "rotor":
        n = int(SR * (dur or 5.0)); t = np.arange(n) / SR
        thump = (np.sin(2 * np.pi * 11 * t) > 0.6).astype(float)
        nz = smooth(rng.standard_normal(n), 40)
        return nz * (0.3 + 0.9 * smooth(thump, 200)) * 1.4
    if name == "wind":
        n = int(SR * (dur or 5.0)); t = np.arange(n) / SR
        return smooth(rng.standard_normal(n), 80) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * t)) * 2.0
    if name == "hum":
        n = int(SR * (dur or 5.0)); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 50 * t) * 0.05 + np.sin(2 * np.pi * 100 * t) * 0.03 + smooth(rng.standard_normal(n), 120) * 0.6)
    if name == "piano":
        notes = [(0, 440), (0.8, 523), (1.6, 587), (2.4, 523), (3.4, 392), (4.4, 440), (5.6, 349), (6.6, 440)]
        n = int(SR * (dur or 9.0)); out = np.zeros(n); t = np.arange(n) / SR
        for st, f in notes * 3:
            pass
        for rep in range(int((dur or 9.0) / 8) + 1):
            for st, f in notes:
                o = int((st + rep * 8) * SR)
                if o >= n:
                    continue
                m = min(int(2.5 * SR), n - o)
                tt = t[:m]
                out[o:o + m] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt) +
                                 0.4 * np.sin(2 * np.pi * f / 2 * tt)) * env(m, 0.005, 0.9) * 0.25
        return out
    if name == "drone":
        n = int(SR * (dur or 6.0)); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 55 * t) * 0.3 + np.sin(2 * np.pi * 58.3 * t) * 0.25) * np.minimum(1, t / 1.5)
    if name == "glass":
        n = int(SR * 1.0)
        return smooth(rng.standard_normal(n), 2) * env(n, 0.001, 0.15) * 0.6
    if name == "keys":
        n = int(SR * (dur or 1.5)); out = np.zeros(n); t = np.arange(n) / SR
        for k in range(14):
            o = int(rng.random() * (n - SR * 0.2)); m = int(SR * 0.15)
            f = 2500 + rng.random() * 2500
            out[o:o + m] += np.sin(2 * np.pi * f * t[:m]) * env(m, 0.001, 0.03) * 0.3
        return out
    if name == "engine":
        n = int(SR * (dur or 5.0)); t = np.arange(n) / SR
        return smooth(rng.standard_normal(n), 60) * (0.6 + 0.4 * np.sin(2 * np.pi * 28 * t)) * 0.9
    if name == "notify":
        n = int(SR * 0.6); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318 * t) * (t < 0.12) + np.sin(2 * np.pi * 1760 * t) * (t > 0.14)) * env(n, 0.002, 0.25) * 0.5
    raise ValueError(name)


AMBIENT = {"room": ("hum", 0.12), "outside": ("wind", 0.3), "basement": ("hum", 0.25), "heli": ("rotor", 0.5),
           "none": (None, 0), "hall": ("hum", 0.15)}


# ------------------------------------------------------------------ Fischauge
def fisheye_map():
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xs - W / 2, ys - H / 2
    R = math.hypot(W / 2, H / 2)
    r2 = (dx * dx + dy * dy) / (R * R)
    k, a = 0.55, 0.765
    f = a * (1 + k * r2)
    sx = np.clip(SW / 2 + dx * f, 0, SW - 1).astype(np.int32)
    sy = np.clip(SH / 2 + dy * f, 0, SH - 1).astype(np.int32)
    return (sy * SW + sx).ravel()


# ------------------------------------------------------------------ POV-Elemente (Ausgabe-Koordinaten)
SLEEVE = (85, 110, 62)
HAND = (238, 200, 170)


def phone_screen(ctx, x, y, w, h, content, t):
    rrect(ctx, x, y, w, h, w * 0.14, (25, 25, 30), 4)
    sx, sy, sw, sh = x + w * 0.07, y + h * 0.05, w * 0.86, h * 0.9
    ctx.save()
    rrect_path(ctx, sx, sy, sw, sh, w * 0.08); ctx.clip()
    kind = content[0] if content else "lock"
    if kind == "alert":
        ctx.set_source_rgba(0.85, 0.12, 0.12, 1); ctx.paint()
        cx = sx + sw / 2
        ctx.move_to(cx, sy + sh * 0.12); ctx.line_to(cx + sw * 0.18, sy + sh * 0.3); ctx.line_to(cx - sw * 0.18, sy + sh * 0.3)
        ctx.close_path(); ctx.set_source_rgba(1, 1, 1, 1); ctx.fill()
        text(ctx, "!", cx, sy + sh * 0.285, sw * 0.13, (0.85, 0.12, 0.12))
        text(ctx, "WARNUNG", cx, sy + sh * 0.4, sw * 0.13, (1, 1, 1))
        text(ctx, "EXTREME", cx, sy + sh * 0.5, sw * 0.15, (1, 0.9, 0.2))
        text(ctx, "GEFAHR", cx, sy + sh * 0.6, sw * 0.15, (1, 0.9, 0.2))
        for i, ln in enumerate(["Gewalttätige Erkrankte", "gemeldet. Bleiben Sie", "in geschlossenen Räumen."]):
            text(ctx, ln, cx, sy + sh * (0.7 + i * 0.06), sw * 0.065, (1, 1, 1), bold=False)
        rrect(ctx, cx - sw * 0.2, sy + sh * 0.88, sw * 0.4, sh * 0.07, 8, (1, 1, 1, 0.9), 0)
        text(ctx, "OK", cx, sy + sh * 0.93, sw * 0.07, (0.8, 0.1, 0.1))
    elif kind == "sms":
        ctx.set_source_rgba(0.95, 0.95, 0.93, 1); ctx.paint()
        ctx.set_source_rgba(0.1, 0.45, 0.3, 1); ctx.rectangle(sx, sy, sw, sh * 0.12); ctx.fill()
        text(ctx, content[1], sx + sw * 0.1, sy + sh * 0.085, sw * 0.08, (1, 1, 1), center=False)
        yy = sy + sh * 0.18
        for msg in content[2:]:
            words = msg.split()
            lines, cur = [], ""
            font(ctx, sw * 0.062, bold=False)
            for wd in words:
                tst = (cur + " " + wd).strip()
                if ctx.text_extents(tst).x_advance > sw * 0.7 and cur:
                    lines.append(cur); cur = wd
                else:
                    cur = tst
            lines.append(cur)
            bh = len(lines) * sw * 0.08 + sw * 0.06
            rrect(ctx, sx + sw * 0.06, yy, sw * 0.82, bh, 10, (1, 1, 1), 2)
            for i, ln in enumerate(lines):
                text(ctx, ln, sx + sw * 0.1, yy + sw * 0.09 + i * sw * 0.08, sw * 0.062, (0.1, 0.1, 0.1), center=False, bold=False)
            yy += bh + sw * 0.05
    elif kind == "nonet":
        ctx.set_source_rgba(0.15, 0.18, 0.25, 1); ctx.paint()
        text(ctx, "Kein Netz", sx + sw / 2, sy + sh * 0.45, sw * 0.12, (1, 1, 1))
        text(ctx, "Notrufe möglich", sx + sw / 2, sy + sh * 0.55, sw * 0.07, (0.8, 0.8, 0.8), bold=False)
    elif kind == "light":
        ctx.set_source_rgba(1, 1, 0.95, 1); ctx.paint()
    else:  # lock
        g = cairo.LinearGradient(sx, sy, sx, sy + sh)
        g.add_color_stop_rgb(0, 0.25, 0.3, 0.55); g.add_color_stop_rgb(1, 0.55, 0.35, 0.5)
        ctx.set_source(g); ctx.paint()
        text(ctx, content[1] if len(content) > 1 else "11:15", sx + sw / 2, sy + sh * 0.3, sw * 0.22, (1, 1, 1))
    ctx.restore()


def hand(ctx, x, y, s=1.0, rot=0.0, fist=False):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ell(ctx, 0, 0, 62, 72, HAND, 5)
    for k in range(4):
        ell(ctx, -42 + k * 28, -70 + abs(k - 1.5) * 8, 15, 34 if not fist else 18, HAND, 4)
    ell(ctx, 62, 10, 16, 32, HAND, 4)
    ctx.restore()


def arm_from_bottom(ctx, x0, y0, x1, y1, w=150):
    limb(ctx, [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + 40), (x1, y1)], SLEEVE, w, 6)


def draw_pov(ctx, pose, t, phone=None, bob=0.0):
    if pose == "none" or pose is None:
        return
    b = math.sin(t * 9) * 25 * bob
    if pose in ("desk", "desk_phone", "desk_up"):
        # Tisch
        poly(ctx, [(-50, 1560), (1130, 1560), (1300, 1980), (-220, 1980)], (205, 165, 110), 6)
        ctx.save(); ctx.translate(560, 1720); ctx.rotate(-0.08)
        rect(ctx, -230, -140, 460, 300, (250, 250, 248), 5)
        ctx.set_source_rgba(0.4, 0.5, 0.8, 0.5); ctx.set_line_width(2)
        for k in range(8):
            ctx.move_to(-210, -100 + k * 34); ctx.line_to(210, -100 + k * 34); ctx.stroke()
        ctx.set_source_rgba(0.2, 0.2, 0.3, 0.8); ctx.set_line_width(3)
        ctx.move_to(-190, -80)
        for k in range(30):
            ctx.line_to(-190 + k * 9, -80 + math.sin(k) * 6)
        ctx.stroke()
        ctx.restore()
        rrect(ctx, 300, 1590, 130, 50, 8, (240, 210, 60), 5)   # Radiergummi
        arm_from_bottom(ctx, -100, 2050, 260, 1800)
        hand(ctx, 290, 1760, 0.9, 0.5)
        if pose == "desk":
            arm_from_bottom(ctx, 1150, 2050, 760, 1790)
            hand(ctx, 740, 1780, 0.9, -0.4, fist=True)
            line(ctx, 700, 1760, 820, 1680, 10, (0.85, 0.65, 0.2))
            if phone:
                ctx.save(); ctx.translate(950, 1680); ctx.rotate(0.3)
                phone_screen(ctx, -60, -110, 120, 220, phone, t)
                ctx.restore()
        else:
            up = 1.0 if pose == "desk_up" else 0.0
            px, py = 760, 1430 - up * 150
            arm_from_bottom(ctx, 1150, 2050, px + 60, py + 300)
            phone_screen(ctx, px - 100 * (1 + up * 0.4), py - 30, 220 * (1 + up * 0.4), 400 * (1 + up * 0.4), phone or ("lock",), t)
            hand(ctx, px + 70 + up * 40, py + 330 + up * 120, 0.95, -0.3)
    elif pose == "phone_big":
        arm_from_bottom(ctx, -100, 2050, 380, 1500 + b)
        arm_from_bottom(ctx, 1180, 2050, 700, 1500 + b)
        phone_screen(ctx, 330, 980 + b, 420, 760, phone or ("lock",), t)
        hand(ctx, 360, 1560 + b, 1.0, 0.6)
        hand(ctx, 720, 1560 + b, 1.0, -0.6)
    elif pose == "phone_low":
        arm_from_bottom(ctx, 1180, 2050, 760, 1650 + b)
        phone_screen(ctx, 650, 1330 + b, 230, 420, phone or ("lock",), t)
        hand(ctx, 770, 1700 + b, 0.95, -0.3)
    elif pose == "reach":
        k = math.sin(t * 3) * 20
        arm_from_bottom(ctx, 1100, 2100, 640, 1350 + k, 160)
        hand(ctx, 620, 1300 + k, 1.2, -0.1)
    elif pose == "push":
        arm_from_bottom(ctx, -100, 2050, 380, 1450 + b)
        arm_from_bottom(ctx, 1180, 2050, 700, 1450 + b)
        hand(ctx, 380, 1400 + b, 1.15, 0.2)
        hand(ctx, 700, 1400 + b, 1.15, -0.2)
    elif pose == "walk":
        arm_from_bottom(ctx, -120, 2100, 150, 1820 + b)
        hand(ctx, 160, 1790 + b, 0.95, 0.4)
        arm_from_bottom(ctx, 1200, 2100, 930, 1830 - b)
        if phone:
            phone_screen(ctx, 830, 1560 - b, 160, 290, phone, t)
        hand(ctx, 920, 1800 - b, 0.95, -0.4)
    elif pose == "flash":
        arm_from_bottom(ctx, 1180, 2050, 780, 1550 + b)
        rrect(ctx, 700, 1400 + b, 160, 260, 20, (25, 25, 30), 4)
        ell(ctx, 740, 1430 + b, 14, 14, (255, 255, 230), 3)
        hand(ctx, 790, 1600 + b, 0.95, -0.3)


def top_card(ctx, kind, a, title="", msg=""):
    if a <= 0:
        return
    ctx.save()
    ctx.push_group()
    if kind == "nina":
        rrect(ctx, 40, 150, 1000, 150, 22, (195, 25, 25), 5)
        poly(ctx, [(95, 170), (125, 222), (65, 222)], (1, 1, 1), 0)
        text(ctx, "!", 95, 218, 36, (0.76, 0.1, 0.1))
        text(ctx, "NINA · WARNUNG", 150, 212, 32, (1, 1, 1), center=False)
        text(ctx, "EXTREME GEFAHR", 70, 275, 54, (1, 1, 1), center=False)
    elif kind in ("sms", "net", "sms_grey"):
        bg = (250, 248, 240) if kind != "sms_grey" else (205, 205, 205)
        font(ctx, 46)
        words, lines, cur = msg.split(), [], ""
        for wd in words:
            tst = (cur + " " + wd).strip()
            if ctx.text_extents(tst).x_advance > 880 and cur:
                lines.append(cur); cur = wd
            else:
                cur = tst
        lines.append(cur)
        h = 90 + len(lines) * 58
        rrect(ctx, 40, 150, 1000, h, 22, bg, 5)
        text(ctx, title, 80, 205, 30, (0.25, 0.25, 0.25), center=False)
        for i, ln in enumerate(lines):
            text(ctx, ln, 80, 265 + i * 58, 46, (0.08, 0.08, 0.1), center=False)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def subtitle(ctx, txt, color, a=1.0):
    font(ctx, 52)
    words, lines, cur = txt.split(), [], ""
    for wd in words:
        tst = (cur + " " + wd).strip()
        if ctx.text_extents(tst).x_advance > 900 and cur:
            lines.append(cur); cur = wd
        else:
            cur = tst
    lines.append(cur)
    y0 = 1240 - (len(lines) - 1) * 33
    for i, ln in enumerate(lines):
        text(ctx, ln, W / 2, y0 + i * 66, 52, (*color[:3], a), outline=(0.05, 0.05, 0.05, a * 0.95), ow=11)


def endcard(ctx, src_surface, opts, a, final=False):
    # weichgezeichnetes Standbild
    small = cairo.ImageSurface(cairo.FORMAT_ARGB32, W // 14, H // 14)
    c2 = cairo.Context(small); c2.scale(1 / 14, 1 / 14); c2.set_source_surface(src_surface); c2.paint()
    ctx.save(); ctx.scale(14, 14); ctx.set_source_surface(small)
    ctx.get_source().set_filter(cairo.FILTER_BILINEAR); ctx.paint_with_alpha(a); ctx.restore()
    ctx.set_source_rgba(0, 0, 0, 0.45 * a); ctx.paint()
    if final:
        text(ctx, "ENDE", W / 2, 900, 150, (1, 1, 1, a), outline=(0, 0, 0, a), ow=12)
        text(ctx, opts[0], W / 2, 1060, 50, (1, 1, 1, a), outline=(0, 0, 0, a), ow=8)
        text(ctx, opts[1], W / 2, 1140, 50, (1, 0.84, 0.15, a), outline=(0, 0, 0, a), ow=8)
        return
    text(ctx, "WAS WÜRDEST", W / 2, 640, 84, (1, 1, 1, a), outline=(0, 0, 0, a), ow=10)
    text(ctx, "DU TUN?", W / 2, 740, 84, (1, 1, 1, a), outline=(0, 0, 0, a), ow=10)
    for i, (label, col) in enumerate(((opts[0], (40, 105, 190)), (opts[1], (200, 45, 45)))):
        y = 830 + i * 260
        ctx.save()
        ctx.push_group()
        rrect(ctx, 110, y, 860, 150, 26, col, 6)
        font(ctx, 54)
        tw = ctx.text_extents(label).x_advance
        if tw > 780:
            parts = label.split(" ")
            half = len(parts) // 2
            text(ctx, " ".join(parts[:half]), W / 2, y + 68, 50, (1, 1, 1))
            text(ctx, " ".join(parts[half:]), W / 2, y + 125, 50, (1, 1, 1))
        else:
            text(ctx, label, W / 2, y + 95, 54, (1, 1, 1))
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a); ctx.restore()
    text(ctx, "ODER", W / 2, 1060, 46, (1, 0.84, 0.15, a), outline=(0, 0, 0, a), ow=8)
    text(ctx, "Schreib es in die Kommentare", W / 2, 1320, 42, (1, 1, 1, a), outline=(0, 0, 0, a), ow=8)


# ------------------------------------------------------------------ Timeline
def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def resolve(v, p):
    if callable(v):
        return v(p)
    if isinstance(v, tuple) and len(v) == 3 and v[0] == "~":
        return v[1] + (v[2] - v[1]) * ease(p)
    return v


def build(num, out_dir, work):
    part = PARTS[num - 1]
    random.seed(num)
    shots = []
    t = 0.0
    for sh in part["shots"]:
        sh = dict(sh)
        lines = []
        lt = sh.get("lead", 0.35)
        for ln in sh.get("lines", []):
            if ln[0] == "pause":
                lt += ln[1]; continue
            spk, txt = ln[0], ln[1]
            wav = tts(spk, txt, work)
            au = read_wav(wav)
            d = len(au) / SR
            lines.append(dict(spk=spk, text=txt, start=t + lt, dur=d, audio=au))
            lt += d + sh.get("gap", 0.3)
        dur = max(sh.get("dur", 0), lt + sh.get("tail", 0.4))
        sh.update(start=t, dur=dur, lines_=lines)
        shots.append(sh)
        t += dur
    end_dur = 4.5
    total = t + end_dur
    nfr = int(total * FPS)

    # Mund-Amplituden
    hop = SR // FPS
    amp = {}
    for sh in shots:
        for ln in sh["lines_"]:
            a = amp.setdefault(ln["spk"], np.zeros(nfr + 1))
            s0 = int(ln["start"] * FPS)
            for k in range(len(ln["audio"]) // hop):
                if s0 + k < nfr:
                    seg = ln["audio"][k * hop:(k + 1) * hop]
                    a[s0 + k] = max(a[s0 + k], float(np.sqrt(np.mean(seg ** 2))) * 4)
    for k in amp:
        amp[k] = np.clip(amp[k], 0, 1)

    # ---------------- Audio
    n = int(total * SR) + SR
    mixl = np.zeros(n)

    def put(sig, at, vol=1.0):
        s = int(max(0, at) * SR)
        e = min(n, s + len(sig))
        if e > s:
            mixl[s:e] += sig[:e - s] * vol

    for sh in shots:
        amb, av = AMBIENT[sh.get("amb", "room")]
        if amb:
            put(sfx(amb, sh["dur"] + 0.05), sh["start"], av)
        for ln in sh["lines_"]:
            put(ln["audio"], ln["start"], 1.0)
        for fx in sh.get("sfx", []):
            name, off = fx[0], fx[1]
            vol = fx[2] if len(fx) > 2 else 0.7
            d = fx[3] if len(fx) > 3 else None
            put(sfx(name, d), sh["start"] + off, vol)
    put(sfx("bass"), t - 0.2, 0.6)
    if part.get("final"):
        pass
    else:
        put(sfx("heart", end_dur), t + 0.2, 0.7)
    mixl = np.nan_to_num(mixl)
    mixl = np.tanh(mixl * 0.85) * 0.95
    pcm = (np.clip(mixl, -1, 1) * 32767).astype(np.int16)
    apath = os.path.join(work, f"p2_mix_{num}.wav")
    with wave.open(apath, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

    # ---------------- Video
    src = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
    sctx = cairo.Context(src)
    fmap = fisheye_map()
    outbuf = np.zeros(W * H, dtype=np.uint32)
    out = cairo.ImageSurface.create_for_data(memoryview(outbuf).cast("B"), cairo.FORMAT_ARGB32, W, H, W * 4)
    octx = cairo.Context(out)
    last = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

    stills = [float(x) for x in os.environ.get("STILLS", "").split(",") if x]
    name = f"teil_{num}_{part['slug']}.mp4"
    out_path = os.path.join(out_dir, name)
    enc = None
    if not stills:
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", apath,
                                "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest", "-movflags", "+faststart",
                                out_path], stdin=subprocess.PIPE)
    print(f"Teil {num}: {total:.1f}s, {len(shots)} Shots", flush=True)
    if os.environ.get("STILLS"):
        print(" ".join(f"{i+1}:{s['start']:.1f}" for i, s in enumerate(shots)), flush=True)

    src_np = np.ndarray((SW * SH,), dtype=np.uint32, buffer=src.get_data())
    for f in range(nfr):
        tt = f / FPS
        if tt >= t:  # Endkarte
            a = ease((tt - t) / 0.5)
            octx.set_source_surface(last); octx.paint()
            if part.get("final"):
                octx.set_source_rgba(0, 0, 0, a); octx.paint()
                endcard(octx, last, part["end"], a, final=True)
            else:
                endcard(octx, last, part["end"], a)
        else:
            sh = next(s for s in shots if s["start"] <= tt < s["start"] + s["dur"] + 1e-6)
            p = (tt - sh["start"]) / sh["dur"]
            P = {k: resolve(v, p) for k, v in sh.get("p", {}).items()}
            talk = {}
            cur_line = None
            for ln in sh["lines_"]:
                if ln["start"] <= tt <= ln["start"] + ln["dur"]:
                    talk[ln["spk"]] = float(amp[ln["spk"]][f])
                if ln["start"] - 0.05 <= tt <= ln["start"] + ln["dur"] + 0.25:
                    cur_line = ln
            cam = {k: resolve(v, p) for k, v in sh.get("cam", {}).items()}
            zoom = cam.get("zoom", 1.0)
            cx, cy = cam.get("x", 0), cam.get("y", 0)
            shake = cam.get("shake", 0.0)
            walk = cam.get("walk", 0.0)
            sx = (math.sin(tt * 37) + math.sin(tt * 23)) * shake * 12
            sy = (math.cos(tt * 31) + math.sin(tt * 17)) * shake * 12 + abs(math.sin(tt * 9)) * walk * 30
            sy += math.sin(tt * 1.7) * 6   # Atmen
            sctx.save()
            sctx.translate(SW / 2 + sx, SH / 2 + sy)
            sctx.rotate(cam.get("roll", 0.0) + math.sin(tt * 9) * walk * 0.015)
            sctx.scale(zoom, zoom)
            sctx.translate(-SW / 2 - cx, -SH / 2 - cy)
            SCENES[sh["scene"]](sctx, tt, P, talk)
            sctx.restore()
            src.flush()
            outbuf[:] = src_np[fmap]
            out.mark_dirty()
            # POV-Hände
            draw_pov(octx, sh.get("pov", "none"), tt, phone=P.get("phone"), bob=walk)
            # Dunkelheit über Hände
            if P.get("pov_dark", 0):
                octx.set_source_rgba(0.02, 0.02, 0.04, P["pov_dark"]); octx.paint()
            # Flash / Blackout
            fl = P.get("flash", 0)
            if fl:
                octx.set_source_rgba(1, 1, 1, fl); octx.paint()
            bo = P.get("black", 0)
            if bo:
                octx.set_source_rgba(0, 0, 0, bo); octx.paint()
            # Overlays
            card = sh.get("card")
            if card:
                ca = ease((p * sh["dur"] - card.get("at", 0)) / 0.25)
                if card.get("at", 0) <= p * sh["dur"]:
                    top_card(octx, card["kind"], ca, card.get("title", ""), card.get("msg", ""))
            # Hook am Anfang
            if tt < 2.8:
                ha = ease(tt / 0.25) * (1 - ease((tt - 2.4) / 0.4))
                hl = part["hook"]
                y = 470 if not card else 520
                for i, ln in enumerate(hl):
                    text(octx, ln, W / 2, y + i * 70, 58, (1, 1, 1, ha), outline=(0, 0, 0, ha), ow=10)
            if cur_line is not None:
                subtitle(octx, cur_line["text"], VOICES[cur_line["spk"]][4])
            # Teil-Tag
            rrect(octx, 40, 60, 220, 62, 31, (0.75, 0.08, 0.08, 0.92), 0)
            text(octx, f"TEIL {num}/7", 150, 103, 34, (1, 1, 1))
            octx.save(); lc = cairo.Context(last); lc.set_source_surface(out); lc.paint(); octx.restore()
        out.flush()
        if stills:
            for st in stills:
                if int(st * FPS) == f:
                    out.write_to_png(os.path.join(work, f"p2_{num}_{st:05.1f}.png"))
            if f > max(stills) * FPS:
                break
            continue
        enc.stdin.write(memoryview(outbuf).cast("B"))
    if enc:
        enc.stdin.close(); enc.wait()
        print("fertig:", out_path, flush=True)


if __name__ == "__main__":
    num = int(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "videos"
    work = os.environ.get("WORK_DIR", "work")
    os.makedirs(out, exist_ok=True); os.makedirs(work, exist_ok=True)
    build(num, out, work)
