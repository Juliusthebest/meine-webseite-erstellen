"""Rendert eine Folge der Zombie-Apokalypse-Serie als TikTok-Video (1080x1920).

Aufruf:  python3 render.py <folgen-nummer 1..7> [ausgabe-ordner]
"""
import math, os, random, subprocess, sys, wave
import numpy as np
import cairo

from episodes import CAST, EPISODES
from voices import tts

W, H, FPS, SR = 1080, 1920, 30, 44100
GROUND = 1600
CS = 1.3  # Figurengröße
FONT = "Inter"
TOTAL_EPS = len(EPISODES)


# ----------------------------------------------------------------- helpers
def rgb(c, a=1.0):
    return (c[0] / 255, c[1] / 255, c[2] / 255, a)


def mix(c1, c2, t):
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def font(ctx, size, weight="black"):
    w = cairo.FONT_WEIGHT_BOLD
    fam = FONT + (" Black" if weight == "black" else "")
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, w)
    ctx.set_font_size(size)


def read_wav(path):
    with wave.open(path) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return data


# ----------------------------------------------------------------- sound fx
def env(n, attack=0.005, decay=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def sfx_boom():
    n = int(SR * 2.2)
    t = np.arange(n) / SR
    f = 30 + 70 * np.exp(-t * 3)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.8)
    s += np.random.randn(n) * env(n, 0.001, 0.06) * 0.4
    return s * 0.9


def sfx_hit():
    n = int(SR * 0.8)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(60 + 120 * np.exp(-t * 25)) / SR) * env(n, 0.001, 0.25)
    noise = np.random.randn(n)
    noise = np.diff(noise, prepend=0)  # brighter
    s += noise * env(n, 0.001, 0.05) * 0.35
    return s * 0.8


def sfx_whoosh():
    n = int(SR * 0.7)
    t = np.arange(n) / SR
    noise = np.random.randn(n)
    k = np.ones(30) / 30
    noise = np.convolve(noise, k, mode="same")
    e = np.sin(np.pi * t / t[-1]) ** 2
    return noise * e * 1.2


def sfx_heartbeat(dur):
    n = int(SR * dur)
    out = np.zeros(n)
    beat = int(SR * 0.85)
    m = int(SR * 0.25)
    t = np.arange(m) / SR
    thump = np.sin(2 * np.pi * 52 * t) * env(m, 0.004, 0.06)
    for start in range(0, n - m, beat):
        out[start:start + m] += thump
        s2 = start + int(SR * 0.22)
        if s2 + m < n:
            out[s2:s2 + m] += thump * 0.7
    return out * 1.1


def sfx_rimshot():
    n = int(SR * 1.6)
    out = np.zeros(n)
    def drum(f, dur, amp):
        m = int(SR * dur)
        t = np.arange(m) / SR
        s = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-t * 40))) / SR) * env(m, 0.001, 0.09)
        s += np.random.randn(m) * env(m, 0.001, 0.02) * 0.5
        return s * amp
    d1 = drum(210, 0.3, 0.7); out[:len(d1)] += d1
    o2 = int(SR * 0.2); d2 = drum(150, 0.3, 0.7); out[o2:o2 + len(d2)] += d2
    o3 = int(SR * 0.42); m = n - o3
    cym = np.random.randn(m); cym = np.diff(cym, prepend=0); cym = np.diff(cym, prepend=0)
    out[o3:] += cym * env(m, 0.001, 0.35) * 0.18
    d3 = drum(170, 0.2, 0.5); out[o3:o3 + len(d3)] += d3
    return out


def sfx_growl(dur=1.6):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 70 + 15 * np.sin(2 * np.pi * 3 * t)
    saw = ((np.cumsum(f) / SR) % 1.0) * 2 - 1
    noise = np.convolve(np.random.randn(n), np.ones(12) / 12, mode="same")
    e = np.sin(np.pi * t / dur) ** 1.5
    return (saw * 0.35 + noise * 0.8) * e * (0.7 + 0.3 * np.sin(2 * np.pi * 6 * t))


def sfx_steps(dur, rate=1.4):
    n = int(SR * dur)
    out = np.zeros(n)
    m = int(SR * 0.18)
    tt = np.arange(m) / SR
    step = np.convolve(np.random.randn(m), np.ones(20) / 20, mode="same") * env(m, 0.01, 0.07)
    step += np.sin(2 * np.pi * 70 * tt) * env(m, 0.002, 0.04) * 0.5
    i = 0.0
    while True:
        s = int(i * SR)
        if s + m >= n:
            break
        out[s:s + m] += step * (0.8 + 0.4 * random.random())
        i += 1 / rate
    return out


# ----------------------------------------------------------------- character drawing
class Actor:
    def __init__(self, key, x, facing, present=True):
        self.key = key
        self.cfg = CAST[key]
        self.x = x
        self.facing = facing
        self.present = present
        self.moves = []        # (start, dur, von, nach, flucht)
        self.seed = random.random() * 10

    def add_move(self, start, dur, frm, to, flee=False):
        if not self.moves:
            self.x = frm
        self.moves.append((start, dur, frm, to, flee))

    def pos(self, t):
        """-> (x, läuft?, flieht?)"""
        x = self.x
        for (st, du, a, b, fl) in self.moves:
            if t < st:
                break
            p = (t - st) / du
            if p >= 1:
                x = b
                continue
            return a + (b - a) * (p if fl else ease(p) * 0.3 + p * 0.7), True, fl
        return x, False, False

    def fled(self, t):
        return any(fl and t > st + du for (st, du, a, b, fl) in self.moves)


def draw_person(ctx, cfg, t, amp, facing, walking, scale=1.0, silhouette=None, cure=0.0,
                mood="drama", prop=None, seed=0.0, flee=False):
    zombie = cfg.get("zombie", False) and cure < 1.0
    zf = 1.0 if (cfg.get("zombie") and silhouette is None) else 0.0
    zf *= (1 - cure)
    skin = cfg["skin"]
    if cfg.get("zombie") and cure > 0:
        skin = mix(cfg["skin"], (232, 190, 160), cure)
    shirt = cfg["shirt"]
    hair = cfg["hair"]
    pants = (45, 45, 60) if not cfg.get("zombie") else (60, 55, 50)

    def col(c, a=1.0):
        if silhouette is not None:
            return rgb(silhouette, a)
        return rgb(c, a)

    ctx.save()
    ctx.scale(scale * facing, scale)

    ph = t * (9 if flee else (4.2 if cfg.get("zombie") else 7)) + seed
    swing = math.sin(ph) * (34 if walking else 0)
    bob = (abs(math.sin(ph)) * 10 if walking else 0) + math.sin(t * 2.1 + seed) * 3
    sway = math.sin(t * 1.3 + seed) * (0.07 if zombie else 0.015)

    # shadow
    if silhouette is None:
        ctx.set_source_rgba(0, 0, 0, 0.35)
        ellipse(ctx, 0, 4, 110, 18)
        ctx.fill()

    # legs
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(44)
    for side, sw in ((-1, swing), (1, -swing)):
        ctx.set_source_rgba(*col(pants))
        ctx.move_to(side * 26, -215 - bob)
        knee_x = side * 26 + sw * 0.6
        ctx.curve_to(knee_x, -120 - bob, side * 26 + sw, -60, side * 26 + sw, -14)
        ctx.stroke()
        ctx.set_source_rgba(*col((30, 25, 25)))
        ellipse(ctx, side * 26 + sw + 14, -8, 34, 16)
        ctx.fill()
        if zombie and side == 1 and silhouette is None:
            # zerrissenes Hosenbein
            ctx.set_source_rgba(*col(skin))
            ellipse(ctx, side * 26 + sw * 0.8, -50, 14, 22)
            ctx.fill()

    ctx.translate(0, -bob)
    ctx.rotate(sway)

    # long hair (behind)
    if cfg.get("long_hair"):
        ctx.set_source_rgba(*col(hair))
        ctx.move_to(-92, -560)
        ctx.curve_to(-120, -470, -110, -400, -80, -370)
        ctx.line_to(70, -370)
        ctx.curve_to(100, -420, 105, -480, 90, -560)
        ctx.close_path()
        ctx.fill()

    # back arm
    def arm(side, front):
        sx = 58 * side
        sy = -425
        if zombie:
            reach = 1 if side > 0 else 0.92
            hx = 175 * reach
            hy = -405 + math.sin(t * 2 + side + seed) * 14 + (10 if side < 0 else 0)
            ex, ey = (sx + hx) / 2, -420
        elif flee:
            hx = 40 * side + math.sin(ph) * 60 * side
            hy = -300 - abs(math.sin(ph)) * 40
            ex, ey = sx + 10 * side, -340
        else:
            gesture = amp > 0.08 and front
            if gesture:
                hx = 120 + math.sin(t * 6) * 18
                hy = -350 + math.cos(t * 5) * 20
                ex, ey = 95, -360
            else:
                hx = sx + 20 * side + math.sin(t * 1.7 + side) * 6
                hy = -250
                ex, ey = sx + 14 * side, -330
            if prop is not None and front:
                hx, hy, ex, ey = 110, -300, 90, -360
        ctx.set_line_width(32)
        ctx.set_source_rgba(*col(mix(shirt, (0, 0, 0), 0.12) if not front else shirt))
        ctx.move_to(sx, sy)
        ctx.curve_to(ex, ey, ex, ey, hx, hy)
        ctx.stroke()
        ctx.set_source_rgba(*col(skin))
        ctx.arc(hx, hy, 19, 0, 2 * math.pi)
        ctx.fill()
        return hx, hy

    arm(-1, False)

    # torso
    ctx.set_source_rgba(*col(shirt))
    if zombie:
        ctx.move_to(-70, -440)
        ctx.curve_to(-70, -465, 70, -465, 70, -440)
        ctx.line_to(72, -215)
        for i in range(8):
            xx = 72 - (i + 1) * 18
            ctx.line_to(xx + 9, -190 if i % 2 == 0 else -222)
        ctx.line_to(-72, -210)
        ctx.close_path()
    else:
        rrect(ctx, -70, -462, 140, 260, 42)
    ctx.fill()
    if cfg.get("key") == "DOC" or cfg.get("glasses"):
        # Laborkittel-Knöpfe
        ctx.set_source_rgba(*col((150, 150, 160)))
        for yy in (-400, -340, -280):
            ctx.arc(8, yy, 6, 0, 2 * math.pi)
            ctx.fill()
    if zombie and silhouette is None:
        ctx.set_source_rgba(0.35, 0.05, 0.05, 0.55 * zf + 0.2)
        ellipse(ctx, -25, -330, 26, 18)
        ctx.fill()
        ellipse(ctx, 30, -260, 14, 20)
        ctx.fill()
        ctx.set_source_rgba(*col(skin))
        ellipse(ctx, 20, -380, 15, 11)
        ctx.fill()

    # neck
    ctx.set_source_rgba(*col(mix(skin, (0, 0, 0), 0.1)))
    ctx.rectangle(-20, -480, 40, 30)
    ctx.fill()

    # head
    ctx.save()
    tilt = (0.18 + math.sin(t * 1.1 + seed) * 0.08) if zombie else math.sin(t * 1.5 + seed) * 0.03
    ctx.translate(0, -545)
    ctx.rotate(tilt)
    ctx.set_source_rgba(*col(skin))
    ellipse(ctx, 0, 0, 82, 92)
    ctx.fill()
    # ear
    ctx.set_source_rgba(*col(mix(skin, (0, 0, 0), 0.08)))
    ellipse(ctx, -74, 8, 14, 22)
    ctx.fill()

    if silhouette is None:
        # hair (top)
        ctx.set_source_rgba(*rgb(hair))
        if cfg.get("long_hair"):
            ctx.move_to(-88, 10)
            ctx.curve_to(-100, -90, 40, -125, 92, -40)
            ctx.curve_to(60, -55, 20, -60, -10, -45)
            ctx.curve_to(-40, -30, -60, -10, -88, 10)
            ctx.fill()
        elif zombie:
            ctx.move_to(-82, -10)
            ctx.curve_to(-85, -80, 0, -110, 50, -85)
            ctx.line_to(30, -70); ctx.line_to(10, -82); ctx.line_to(-15, -66); ctx.line_to(-40, -78)
            ctx.line_to(-60, -40)
            ctx.close_path()
            ctx.fill()
        else:
            ctx.move_to(-84, -5)
            ctx.curve_to(-92, -95, 60, -125, 86, -35)
            ctx.curve_to(70, -60, 30, -70, 0, -62)
            ctx.curve_to(-30, -55, -60, -45, -84, -5)
            ctx.fill()

        # eyes
        blink = ((t + seed) % 3.7) < 0.13 and not zombie
        for i, ex in enumerate((-8, 42)):
            ey = -12
            if zombie:
                ctx.set_source_rgba(0.15, 0.2, 0.1, 0.5 * zf)
                ellipse(ctx, ex, ey + 8, 22, 22)
                ctx.fill()
                ctx.set_source_rgba(*rgb(mix((240, 235, 140), (255, 255, 255), cure)))
                ellipse(ctx, ex, ey, 17 if i == 0 else 13, 19 if i == 0 else 12)
                ctx.fill()
                ctx.set_source_rgba(*rgb(mix((190, 20, 20), (30, 30, 40), cure)))
                ctx.arc(ex + 4, ey + 2, 5 if cure < 0.5 else 8, 0, 2 * math.pi)
                ctx.fill()
            else:
                scared = mood == "drama"
                ctx.set_source_rgba(1, 1, 1, 1)
                ellipse(ctx, ex, ey, 16, 2 if blink else (21 if scared else 18))
                ctx.fill()
                if not blink:
                    ctx.set_source_rgba(0.12, 0.1, 0.1, 1)
                    ctx.arc(ex + 6, ey + 2, 8, 0, 2 * math.pi)
                    ctx.fill()
                    ctx.set_source_rgba(1, 1, 1, 0.9)
                    ctx.arc(ex + 8, ey - 2, 3, 0, 2 * math.pi)
                    ctx.fill()
            # brows
            ctx.set_line_width(7)
            ctx.set_source_rgba(*rgb(mix(hair, (0, 0, 0), 0.3)))
            if zombie:
                ctx.move_to(ex - 16, ey - 28 + (6 if i == 0 else -4))
                ctx.line_to(ex + 16, ey - 26)
            elif mood == "drama":
                inner = 1 if i == 0 else -1  # inner end goes up -> worried
                ctx.move_to(ex - 16, ey - 30 + (0 if inner > 0 else -10))
                ctx.line_to(ex + 16, ey - 30 + (-10 if inner > 0 else 0))
            elif mood == "laugh":
                ctx.move_to(ex - 16, ey - 34)
                ctx.curve_to(ex - 5, ey - 44, ex + 5, ey - 44, ex + 16, ey - 34)
            else:
                ctx.move_to(ex - 16, ey - 32)
                ctx.line_to(ex + 16, ey - 34)
            ctx.stroke()

        if cfg.get("glasses"):
            ctx.set_line_width(5)
            ctx.set_source_rgba(0.1, 0.1, 0.12, 1)
            for ex in (-8, 42):
                ctx.arc(ex, -12, 24, 0, 2 * math.pi)
                ctx.stroke()
            ctx.move_to(16, -14); ctx.line_to(18, -14); ctx.stroke()
        if cfg.get("beard"):
            ctx.set_source_rgba(*rgb(hair))
            ctx.move_to(-60, 20)
            ctx.curve_to(-50, 110, 70, 110, 78, 20)
            ctx.curve_to(50, 40, -20, 40, -60, 20)
            ctx.fill()

        # nose
        ctx.set_source_rgba(*rgb(mix(skin, (0, 0, 0), 0.15)))
        ellipse(ctx, 30, 14, 9, 7)
        ctx.fill()

        # mouth
        mx, my = 22, 45
        if amp > 0.04:
            ctx.set_source_rgba(0.35, 0.05, 0.08, 1)
            ellipse(ctx, mx, my, 22 + amp * 6, 5 + amp * 24)
            ctx.fill()
            if zombie:
                ctx.set_source_rgba(0.85, 0.8, 0.55, 1)
                for k in range(3):
                    ctx.rectangle(mx - 14 + k * 11, my - 5 - amp * 20, 7, 9)
                    ctx.fill()
        elif mood == "laugh":
            ctx.set_source_rgba(0.35, 0.05, 0.08, 1)
            ctx.move_to(mx - 26, my - 6)
            ctx.curve_to(mx - 20, my + 30, mx + 20, my + 30, mx + 26, my - 6)
            ctx.close_path()
            ctx.fill()
        elif mood == "shock":
            ctx.set_source_rgba(0.35, 0.05, 0.08, 1)
            ellipse(ctx, mx, my + 4, 12, 16)
            ctx.fill()
        else:
            ctx.set_line_width(6)
            ctx.set_source_rgba(0.35, 0.1, 0.1, 1)
            ctx.move_to(mx - 20, my + (6 if mood == "drama" or zombie else 0))
            ctx.curve_to(mx - 8, my + (-4 if mood == "drama" or zombie else 10),
                         mx + 8, my + (-4 if mood == "drama" or zombie else 10),
                         mx + 20, my + (6 if mood == "drama" or zombie else 0))
            ctx.stroke()

        if zombie:
            # Narbe mit Stichen
            ctx.set_source_rgba(0.3, 0.1, 0.1, 0.8 * zf + 0.2)
            ctx.set_line_width(4)
            ctx.move_to(-50, -55); ctx.line_to(10, -40); ctx.stroke()
            for k in range(4):
                xx = -45 + k * 16
                yy = -54 + k * 4
                ctx.move_to(xx, yy - 8); ctx.line_to(xx + 3, yy + 8); ctx.stroke()
    ctx.restore()

    # front arm + prop
    hx, hy = arm(1, True)
    if prop and silhouette is None:
        ctx.save()
        ctx.translate(hx, hy)
        if prop == "choco":
            ctx.rotate(-0.3)
            ctx.set_source_rgba(0.45, 0.25, 0.1, 1); rrect(ctx, -18, -60, 36, 90, 6); ctx.fill()
            ctx.set_source_rgba(0.9, 0.75, 0.2, 1); rrect(ctx, -19, -10, 38, 42, 4); ctx.fill()
        elif prop == "syringe":
            ctx.rotate(-0.9)
            ctx.set_source_rgba(0.85, 0.9, 0.95, 0.9); rrect(ctx, -10, -80, 20, 70, 4); ctx.fill()
            ctx.set_source_rgba(0.3, 1.0, 0.4, 0.9); rrect(ctx, -7, -70, 14, 50, 3); ctx.fill()
            ctx.set_source_rgba(0.6, 0.6, 0.6, 1); ctx.set_line_width(3)
            ctx.move_to(0, -80); ctx.line_to(0, -115); ctx.stroke()
        elif prop == "mop":
            ctx.rotate(0.25)
            ctx.set_source_rgba(0.55, 0.35, 0.2, 1); ctx.set_line_width(10)
            ctx.move_to(0, -170); ctx.line_to(0, 230); ctx.stroke()
            ctx.set_source_rgba(0.85, 0.85, 0.8, 1)
            for k in range(-4, 5):
                ctx.set_line_width(8)
                ctx.move_to(0, 230); ctx.line_to(k * 12, 300); ctx.stroke()
        ctx.restore()

    ctx.restore()


# ----------------------------------------------------------------- backgrounds
def skyline(ctx, rng, base_y, color, hmin, hmax, wmin, wmax, windows=True, lit=0.12):
    x = -40
    while x < W + 40:
        bw = rng.uniform(wmin, wmax)
        bh = rng.uniform(hmin, hmax)
        ctx.set_source_rgba(*color)
        ctx.move_to(x, base_y)
        ctx.line_to(x, base_y - bh)
        # kaputte Dachkante
        steps = 4
        for i in range(1, steps + 1):
            ctx.line_to(x + bw * i / steps, base_y - bh + rng.uniform(-18, 30) * (i % 2))
        ctx.line_to(x + bw, base_y)
        ctx.close_path()
        ctx.fill()
        if windows:
            for wy in np.arange(base_y - bh + 30, base_y - 20, 34):
                for wx in np.arange(x + 12, x + bw - 18, 26):
                    if rng.random() < lit:
                        ctx.set_source_rgba(1, 0.75, 0.35, rng.uniform(0.4, 0.9))
                        ctx.rectangle(wx, wy, 12, 16)
                        ctx.fill()
        x += bw + rng.uniform(-10, 20)


def bg_street(ctx, rng):
    g = cairo.LinearGradient(0, 0, 0, 1250)
    g.add_color_stop_rgb(0, 0.10, 0.02, 0.05)
    g.add_color_stop_rgb(0.55, 0.45, 0.07, 0.05)
    g.add_color_stop_rgb(1, 0.95, 0.42, 0.12)
    ctx.set_source(g); ctx.rectangle(0, 0, W, 1260); ctx.fill()
    # Blutmond
    rg = cairo.RadialGradient(760, 520, 30, 760, 520, 330)
    rg.add_color_stop_rgba(0, 1, 0.55, 0.4, 0.55); rg.add_color_stop_rgba(1, 1, 0.3, 0.2, 0)
    ctx.set_source(rg); ctx.arc(760, 520, 330, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(1, 0.75, 0.6, 0.95); ctx.arc(760, 520, 120, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(0.85, 0.5, 0.4, 0.5)
    for (dx, dy, r) in ((-30, -20, 22), (40, 30, 16), (10, 60, 12)):
        ctx.arc(760 + dx, 520 + dy, r, 0, 2 * math.pi); ctx.fill()
    # Rauchsäulen
    for sx in (180, 920):
        for i in range(14):
            ctx.set_source_rgba(0.12, 0.08, 0.08, 0.10)
            ctx.arc(sx + math.sin(i * 0.7) * 40 + i * 12, 1150 - i * 70, 60 + i * 9, 0, 2 * math.pi)
            ctx.fill()
    skyline(ctx, rng, 1260, (0.22, 0.07, 0.08, 1), 250, 520, 90, 170, lit=0.06)
    skyline(ctx, rng, 1270, (0.10, 0.03, 0.05, 1), 140, 330, 110, 200, lit=0.10)
    # Straße
    g = cairo.LinearGradient(0, 1260, 0, H)
    g.add_color_stop_rgb(0, 0.16, 0.10, 0.10); g.add_color_stop_rgb(1, 0.05, 0.04, 0.05)
    ctx.set_source(g); ctx.rectangle(0, 1260, W, H - 1260); ctx.fill()
    ctx.set_source_rgba(0.25, 0.18, 0.16, 1); ctx.rectangle(0, 1260, W, 40); ctx.fill()
    ctx.set_source_rgba(0.9, 0.8, 0.3, 0.55)
    for x in range(-40, W, 220):
        ctx.move_to(x, 1640); ctx.line_to(x + 120, 1640); ctx.line_to(x + 135, 1665); ctx.line_to(x + 10, 1665)
        ctx.close_path(); ctx.fill()
    # Risse
    ctx.set_source_rgba(0, 0, 0, 0.5); ctx.set_line_width(3)
    for _ in range(10):
        x0, y0 = rng.uniform(0, W), rng.uniform(1320, 1850)
        ctx.move_to(x0, y0)
        for _ in range(4):
            x0 += rng.uniform(-40, 40); y0 += rng.uniform(-10, 25); ctx.line_to(x0, y0)
        ctx.stroke()
    # Autowrack links hinten
    ctx.set_source_rgba(0.08, 0.05, 0.06, 1)
    rrect(ctx, -60, 1180, 330, 100, 20); ctx.fill()
    rrect(ctx, 0, 1120, 200, 80, 30); ctx.fill()
    ctx.set_source_rgba(0.02, 0.02, 0.02, 1)
    ctx.arc(30, 1285, 34, 0, 2 * math.pi); ctx.fill(); ctx.arc(210, 1285, 34, 0, 2 * math.pi); ctx.fill()
    # Absperrung/Schild
    ctx.set_source_rgba(0.1, 0.06, 0.06, 1); ctx.rectangle(990, 1000, 10, 290); ctx.fill()
    ctx.set_source_rgba(0.85, 0.75, 0.2, 1)
    ctx.move_to(995, 950); ctx.line_to(1060, 1030); ctx.line_to(930, 1030); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(0.1, 0.05, 0.05, 1); font(ctx, 54); ctx.move_to(984, 1020); ctx.show_text("!")


def bg_bunker(ctx, rng):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.10, 0.12, 0.11); g.add_color_stop_rgb(0.7, 0.20, 0.22, 0.19)
    g.add_color_stop_rgb(1, 0.08, 0.08, 0.08)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    # Betonplatten
    ctx.set_source_rgba(0, 0, 0, 0.35); ctx.set_line_width(4)
    for y in range(300, 1300, 250):
        ctx.move_to(0, y); ctx.line_to(W, y); ctx.stroke()
    for y in range(300, 1300, 250):
        off = 0 if (y // 250) % 2 else 180
        for x in range(off, W, 360):
            ctx.move_to(x, y); ctx.line_to(x, y + 250); ctx.stroke()
    # Rohre
    ctx.set_source_rgba(0.25, 0.27, 0.24, 1); ctx.rectangle(0, 170, W, 34); ctx.fill()
    ctx.set_source_rgba(0.18, 0.2, 0.18, 1); ctx.rectangle(0, 225, W, 20); ctx.fill()
    # Regal mit Dosen links
    ctx.set_source_rgba(0.3, 0.22, 0.14, 1)
    for y in (780, 950, 1120):
        ctx.rectangle(30, y, 260, 16); ctx.fill()
    ctx.rectangle(30, 700, 14, 600); ctx.fill(); ctx.rectangle(276, 700, 14, 600); ctx.fill()
    for y in (780, 950):
        for k in range(rng.randint(1, 3)):
            ctx.set_source_rgba(*rgb(rng.choice([(150, 40, 40), (60, 120, 60), (180, 160, 60)])))
            rrect(ctx, 60 + k * 70, y - 70, 50, 70, 6); ctx.fill()
    # Bunkertür rechts
    ctx.set_source_rgba(0.28, 0.30, 0.28, 1); rrect(ctx, 760, 760, 300, 540, 30); ctx.fill()
    ctx.set_source_rgba(0.18, 0.2, 0.18, 1); rrect(ctx, 785, 785, 250, 490, 22); ctx.fill()
    ctx.set_source_rgba(0.55, 0.15, 0.12, 1); ctx.set_line_width(14)
    ctx.arc(910, 1030, 70, 0, 2 * math.pi); ctx.stroke()
    for a in range(4):
        ctx.move_to(910, 1030); ctx.line_to(910 + 70 * math.cos(a * math.pi / 2 + 0.4), 1030 + 70 * math.sin(a * math.pi / 2 + 0.4)); ctx.stroke()
    ctx.set_source_rgba(0.85, 0.75, 0.2, 0.8); font(ctx, 40)
    ctx.move_to(800, 840); ctx.show_text("SCHUTZRAUM 7")
    # Boden
    ctx.set_source_rgba(0.12, 0.12, 0.11, 1); ctx.rectangle(0, 1300, W, H - 1300); ctx.fill()
    ctx.set_source_rgba(0, 0, 0, 0.3)
    for y in range(1300, H, 90):
        ctx.rectangle(0, y, W, 4); ctx.fill()


def bg_lab(ctx, rng):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.04, 0.07, 0.12); g.add_color_stop_rgb(0.65, 0.09, 0.15, 0.22)
    g.add_color_stop_rgb(1, 0.03, 0.04, 0.06)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    # Fliesen
    ctx.set_source_rgba(1, 1, 1, 0.04); ctx.set_line_width(2)
    for x in range(0, W, 90):
        ctx.move_to(x, 0); ctx.line_to(x, 1300); ctx.stroke()
    for y in range(0, 1300, 90):
        ctx.move_to(0, y); ctx.line_to(W, y); ctx.stroke()
    # Warnschild
    ctx.set_source_rgba(0.95, 0.8, 0.1, 1)
    ctx.move_to(540, 690); ctx.line_to(640, 860); ctx.line_to(440, 860); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(0.05, 0.05, 0.05, 1); ctx.set_line_width(8)
    ctx.arc(540, 810, 26, 0, 2 * math.pi); ctx.stroke()
    for a in range(3):
        aa = a * 2 * math.pi / 3 - math.pi / 2
        ctx.arc(540 + 30 * math.cos(aa), 810 + 30 * math.sin(aa), 16, 0, 2 * math.pi); ctx.stroke()
    # Labortisch hinten
    ctx.set_source_rgba(0.2, 0.24, 0.28, 1); ctx.rectangle(0, 1180, W, 30); ctx.fill()
    ctx.set_source_rgba(0.12, 0.15, 0.18, 1); ctx.rectangle(0, 1210, W, 90); ctx.fill()
    for i, x in enumerate(range(60, W, 150)):
        c = [(0.3, 1, 0.4), (0.3, 0.7, 1), (1, 0.3, 0.5)][i % 3]
        ctx.set_source_rgba(0.8, 0.9, 1, 0.35)
        ctx.move_to(x, 1060); ctx.line_to(x + 24, 1060); ctx.line_to(x + 24, 1110); ctx.line_to(x + 55, 1180)
        ctx.line_to(x - 31, 1180); ctx.line_to(x, 1110); ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(c[0], c[1], c[2], 0.85)
        ctx.move_to(x - 18, 1150); ctx.line_to(x + 42, 1150); ctx.line_to(x + 55, 1180); ctx.line_to(x - 31, 1180)
        ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(0.07, 0.08, 0.1, 1); ctx.rectangle(0, 1300, W, H - 1300); ctx.fill()


def bg_house(ctx, rng):
    ctx.set_source_rgb(0.30, 0.20, 0.17); ctx.rectangle(0, 0, W, H); ctx.fill()
    ctx.set_source_rgba(0.38, 0.27, 0.22, 1)
    for x in range(0, W, 70):
        ctx.rectangle(x, 0, 30, 1300); ctx.fill()
    # Fensterrahmen (Inhalt wird pro Frame gemalt)
    ctx.set_source_rgba(0.95, 0.92, 0.85, 1); rrect(ctx, 590, 560, 430, 470, 10); ctx.fill()
    # Bild an der Wand
    ctx.set_source_rgba(0.55, 0.38, 0.15, 1); ctx.rectangle(110, 640, 260, 200); ctx.fill()
    ctx.set_source_rgba(0.6, 0.75, 0.85, 1); ctx.rectangle(128, 658, 224, 164); ctx.fill()
    ctx.set_source_rgba(0.3, 0.55, 0.3, 1)
    ctx.move_to(128, 822); ctx.line_to(200, 720); ctx.line_to(260, 790); ctx.line_to(300, 740); ctx.line_to(352, 822)
    ctx.close_path(); ctx.fill()
    font(ctx, 30); ctx.set_source_rgba(0.95, 0.9, 0.8, 1); ctx.move_to(150, 900); ctx.show_text("Home Sweet Home")
    # Sofa
    ctx.set_source_rgba(0.45, 0.15, 0.18, 1)
    rrect(ctx, 20, 1100, 420, 210, 40); ctx.fill()
    ctx.set_source_rgba(0.55, 0.2, 0.22, 1)
    rrect(ctx, 50, 1180, 360, 80, 25); ctx.fill()
    # Fußboden (glänzend gewischt)
    g = cairo.LinearGradient(0, 1300, 0, H)
    g.add_color_stop_rgb(0, 0.55, 0.4, 0.28); g.add_color_stop_rgb(1, 0.32, 0.22, 0.15)
    ctx.set_source(g); ctx.rectangle(0, 1300, W, H - 1300); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.12)
    for y in range(1340, H, 70):
        ctx.rectangle(0, y, W, 3); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.18)
    ellipse(ctx, 650, 1600, 260, 30); ctx.fill()


BGS = {"street": bg_street, "bunker": bg_bunker, "lab": bg_lab, "house": bg_house}


def make_bg(place, seed):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    BGS[place](ctx, random.Random(seed))
    return surf


def make_vignette():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = cairo.RadialGradient(W / 2, H * 0.55, 300, W / 2, H * 0.55, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    ctx.set_source(g); ctx.paint()
    return surf


def dynamic_bg(ctx, place, t, fx):
    if place == "street":
        # Feuer am Autowrack
        for i in range(6):
            fl = 0.5 + 0.5 * math.sin(t * 13 + i * 2.1)
            ctx.set_source_rgba(1, 0.45 + 0.3 * fl, 0.1, 0.55)
            x = 40 + i * 30
            ctx.move_to(x - 25, 1130)
            ctx.curve_to(x - 20, 1060 - fl * 40, x + 10, 1050 - fl * 70, x + 5, 990 - fl * 60)
            ctx.curve_to(x + 25, 1060, x + 30, 1090, x + 25, 1130)
            ctx.close_path(); ctx.fill()
        g = cairo.RadialGradient(130, 1100, 10, 130, 1100, 320)
        g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0.25 + 0.08 * math.sin(t * 17))
        g.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
        ctx.set_source(g); ctx.arc(130, 1100, 320, 0, 2 * math.pi); ctx.fill()
    elif place == "bunker":
        ang = math.sin(t * 1.4) * 0.18
        px, py = 540, 250
        lx, ly = px + math.sin(ang) * 260, py + math.cos(ang) * 260
        ctx.set_source_rgba(0.05, 0.05, 0.05, 1); ctx.set_line_width(4)
        ctx.move_to(px, py); ctx.line_to(lx, ly); ctx.stroke()
        flick = 0.85 + 0.15 * (math.sin(t * 37) > 0.97)
        g = cairo.RadialGradient(lx, ly, 10, lx, ly + 700, 900)
        g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.30 * flick)
        g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
        ctx.set_source(g)
        ctx.move_to(lx - 30, ly)
        ctx.line_to(lx - 30 - 600 + ang * 900, 1650); ctx.line_to(lx + 30 + 600 + ang * 900, 1650)
        ctx.line_to(lx + 30, ly); ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(0.15, 0.15, 0.12, 1)
        ctx.move_to(lx - 40, ly + 30); ctx.line_to(lx - 20, ly - 5); ctx.line_to(lx + 20, ly - 5); ctx.line_to(lx + 40, ly + 30)
        ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(1, 0.95, 0.7, flick); ctx.arc(lx, ly + 32, 13, 0, 2 * math.pi); ctx.fill()
    elif place == "lab":
        # Monitor mit EKG
        ctx.set_source_rgba(0.1, 0.1, 0.12, 1); rrect(ctx, 650, 380, 360, 230, 14); ctx.fill()
        ctx.set_source_rgba(0.02, 0.08, 0.05, 1); ctx.rectangle(668, 398, 324, 194); ctx.fill()
        ctx.set_source_rgba(0.3, 1, 0.45, 0.95); ctx.set_line_width(4)
        for i in range(160):
            x = 670 + i * 2
            ph = (i / 160 * 2 + t * 0.9) % 1.0
            y = 495
            if 0.45 < ph < 0.48: y -= 60
            elif 0.48 < ph < 0.51: y += 40
            elif 0.40 < ph < 0.45: y -= 8
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.stroke()
        font(ctx, 26); ctx.move_to(680, 430); ctx.show_text("VIRUS-SCAN: Z-47")
        # Blasen in den Kolben
        for i, x in enumerate(range(60, W, 150)):
            for b in range(3):
                yy = 1170 - ((t * 40 + b * 25 + i * 13) % 60)
                ctx.set_source_rgba(1, 1, 1, 0.5)
                ctx.arc(x + 12 + math.sin(t * 3 + b) * 6, yy, 4, 0, 2 * math.pi); ctx.fill()
    elif place == "house":
        g = cairo.LinearGradient(0, 580, 0, 1010)
        g.add_color_stop_rgb(0, 0.3, 0.05, 0.08); g.add_color_stop_rgb(1, 0.9, 0.35, 0.15)
        ctx.set_source(g); ctx.rectangle(610, 580, 390, 430); ctx.fill()
        ctx.set_source_rgba(0.12, 0.04, 0.05, 1)
        for k, (bx, bh) in enumerate(((610, 120), (680, 200), (760, 90), (830, 170), (920, 130))):
            ctx.rectangle(bx, 1010 - bh, 75, bh); ctx.fill()
        # Zombie-Silhouetten draußen
        for k in range(2):
            zx = 1050 - ((t * 25 + k * 210) % 520)
            ctx.save(); ctx.translate(zx, 1010)
            ctx.rectangle(610 - zx, -1010 + 580, 390, 430); ctx.clip()
            draw_person(ctx, CAST["ZOMBIE"], t + k, 0, -1, True, 0.18, silhouette=(30, 10, 12), seed=k)
            ctx.restore()
        ctx.set_source_rgba(0.95, 0.92, 0.85, 1); ctx.set_line_width(14)
        ctx.move_to(805, 580); ctx.line_to(805, 1010); ctx.stroke()
        ctx.move_to(610, 795); ctx.line_to(1000, 795); ctx.stroke()
        # Vorhänge
        ctx.set_source_rgba(0.55, 0.45, 0.2, 1)
        for x0, d in ((560, 1), (1050, -1)):
            ctx.move_to(x0, 530); ctx.line_to(x0 + d * 90, 530)
            ctx.curve_to(x0 + d * 60, 800, x0 + d * 110, 950, x0 + d * 60, 1080)
            ctx.line_to(x0, 1080); ctx.close_path(); ctx.fill()


# ----------------------------------------------------------------- text
def text_outline(ctx, txt, x, y, fill, stroke=(0, 0, 0, 1), lw=12):
    ctx.move_to(x, y)
    ctx.text_path(txt)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*stroke); ctx.set_line_width(lw); ctx.stroke_preserve()
    ctx.set_source_rgba(*fill); ctx.fill()


def wrap(ctx, words, maxw):
    lines, cur = [], []
    for i, w in enumerate(words):
        test = " ".join(x for _, x in cur + [(i, w)])
        if cur and ctx.text_extents(test).x_advance > maxw:
            lines.append(cur); cur = [(i, w)]
        else:
            cur.append((i, w))
    if cur:
        lines.append(cur)
    return lines


def draw_subtitle(ctx, line, t):
    words = line["text"].split()
    p = (t - line["start"]) / max(line["dur"], 0.01)
    # Wort-Timing proportional zur Länge
    weights = np.array([len(w) + 2 for w in words], dtype=float)
    cum = np.cumsum(weights) / weights.sum()
    cur = int(np.searchsorted(cum, p))
    narrator = line["speaker"] == "ERZ"
    size = 64 if not narrator else 58
    font(ctx, size)
    lines = wrap(ctx, words, 920)
    lh = size * 1.22
    y0 = 610 - (len(lines) - 1) * lh / 2
    appear = ease((t - line["start"]) / 0.15)
    ctx.save()
    ctx.translate(W / 2, y0)
    sc = 0.85 + 0.15 * appear
    ctx.scale(sc, sc)
    ctx.translate(-W / 2, -y0)
    if narrator:
        h = len(lines) * lh + 50
        ctx.set_source_rgba(0, 0, 0, 0.6 * appear)
        rrect(ctx, 50, y0 - size - 25, W - 100, h, 24); ctx.fill()
    else:
        cfg = CAST[line["speaker"]]
        font(ctx, 38)
        name = cfg["name"].upper()
        tw = ctx.text_extents(name).x_advance
        ctx.set_source_rgba(*rgb(cfg["shirt"], appear))
        bx = W / 2 - tw / 2 - 26
        rrect(ctx, bx, y0 - size - 72, tw + 52, 58, 29); ctx.fill()
        lum = sum(cfg["shirt"]) / 3
        ctx.set_source_rgba(*((0.05, 0.05, 0.05, appear) if lum > 160 else (1, 1, 1, appear)))
        ctx.move_to(W / 2 - tw / 2, y0 - size - 30); ctx.show_text(name)
        font(ctx, size)
    for li, ln in enumerate(lines):
        txt = " ".join(w for _, w in ln)
        x = W / 2 - ctx.text_extents(txt).x_advance / 2
        y = y0 + li * lh
        for idx, w in ln:
            if narrator:
                fill = (1, 1, 1, appear) if idx <= cur else (1, 1, 1, 0.35 * appear)
            else:
                fill = (1, 0.86, 0.1, appear) if idx == cur else (1, 1, 1, appear)
            text_outline(ctx, w, x, y, fill, (0, 0, 0, appear), 14)
            x += ctx.text_extents(w + " ").x_advance
    ctx.restore()


# ----------------------------------------------------------------- episode build
def build(ep_index, out_dir, work_dir):
    ep = EPISODES[ep_index]
    num = ep_index + 1
    random.seed(num * 77)
    np.random.seed(num)

    # Stimmen erzeugen + Zeitplan
    t = 2.0  # Intro (Titel + Hook)
    lines = []
    seen_z = set()
    for i, (spk, text, action) in enumerate(ep["lines"]):
        wav = tts(spk, text, work_dir)
        audio = read_wav(wav)
        dur = len(audio) / SR
        if action == "punch":
            t += 0.6  # dramatische Pause vor der Pointe
        if CAST[spk].get("zombie") and spk not in seen_z:
            seen_z.add(spk)
            t += 1.3  # Zombie läuft erst ins Bild
        lines.append(dict(speaker=spk, text=text, action=action, start=t, dur=dur, audio=audio))
        t += dur + (0.45 if action != "sting" else 0.6)
    punch_end = lines[-1]["start"] + lines[-1]["dur"]
    total = punch_end + 3.2

    # Amplituden-Hüllkurve pro Sprecher für Mundbewegung
    nfr = int(total * FPS) + 1
    amp = {}
    for ln in lines:
        a = amp.setdefault(ln["speaker"], np.zeros(nfr))
        hop = SR // FPS
        s0 = int(ln["start"] * FPS)
        for k in range(len(ln["audio"]) // hop):
            seg = ln["audio"][k * hop:(k + 1) * hop]
            if s0 + k < nfr:
                a[s0 + k] = max(a[s0 + k], float(np.sqrt(np.mean(seg ** 2))))
    for k, a in amp.items():
        m = a.max() or 1
        a /= m
        a[:] = np.convolve(a, np.ones(2) / 2, mode="same")
        amp[k] = np.clip(a * 1.4, 0, 1)

    # Darsteller
    humans = [c for c in ep["cast"]]
    actors = {}
    xs = [215, 520] if len(humans) == 2 else [400]
    for i, k in enumerate(humans):
        actors[k] = Actor(k, xs[i], 1 if i == 0 else -1)
    props = {"OPA": "choco", "DOC": "syringe", "MAMA": "mop"}

    zombie_keys = []
    for ln in lines:
        if CAST[ln["speaker"]].get("zombie") and ln["speaker"] not in actors:
            z = Actor(ln["speaker"], 1500, -1, present=False)
            actors[ln["speaker"]] = z
            zombie_keys.append(ln["speaker"])
    # Auftritte / Abgänge
    horde_start = None
    cure_at = None
    entered = set()
    for ln in lines:
        spk = ln["speaker"]
        if CAST[spk].get("zombie") and spk not in entered:
            entered.add(spk)
            z = actors[spk]
            z.present = True
            z.add_move(ln["start"] - 1.7, 1.9, 1500, 910)
            ln["enter"] = True
        if ln["action"] == "horde":
            horde_start = ln["start"]
        if ln["action"] == "exit_zombie":
            for zk in zombie_keys:
                actors[zk].add_move(ln["start"] + ln["dur"] - 0.2, 1.3, 910, 1700, True)
            ln["exit_at"] = ln["start"] + ln["dur"] - 0.2
        if "Spritze" in ln["text"]:
            cure_at = ln["start"] + ln["dur"]
    if horde_start is not None:
        horde_start = max(0, horde_start - 0.5)

    def zombie_on(t):
        for z in zombie_keys:
            x, _, _ = actors[z].pos(t)
            if x < W and not actors[z].fled(t):
                return True
        return False

    # ------------------------------------------------ AUDIO
    n = int(total * SR) + SR
    mixl = np.zeros(n)
    def put(sig, at, vol=1.0):
        s = int(at * SR)
        e = min(n, s + len(sig))
        if e > s:
            mixl[s:e] += sig[:e - s] * vol

    put(sfx_boom(), 0.0, 0.7)
    for ln in lines:
        put(ln["audio"], ln["start"], 1.0)
        a = ln["action"]
        if a == "sting":
            put(sfx_boom(), ln["start"] - 0.1, 0.55)
        elif a == "heart":
            put(sfx_heartbeat(ln["dur"] + 0.4), ln["start"], 0.75)
        elif a == "flash":
            put(sfx_whoosh(), ln["start"] - 0.45, 0.45); put(sfx_hit(), ln["start"], 0.7)
        elif a == "shake":
            put(sfx_hit(), ln["start"], 0.8)
        elif a == "zoom":
            put(sfx_whoosh(), ln["start"] - 0.3, 0.25)
        elif a == "horde":
            for k in range(5):
                put(sfx_growl(2.0), ln["start"] + k * 0.7, 0.18)
        elif a == "exit_zombie":
            put(sfx_steps(1.6, 6), ln["start"] + ln["dur"] - 0.2, 0.5)
        if ln.get("enter"):
            put(sfx_growl(1.8), ln["start"] - 1.6, 0.35)
            put(sfx_steps(1.8, 1.6), ln["start"] - 1.6, 0.5)
            put(sfx_hit(), ln["start"] - 0.1, 0.5)
    put(sfx_rimshot(), punch_end + 0.35, 0.9)

    # Ambient (Wind + Drone) über ffmpeg
    amb = os.path.join(work_dir, f"amb_{num}.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.5:duration={total + 1}:sample_rate={SR}",
                    "-f", "lavfi", "-i", f"sine=frequency=55:duration={total + 1}:sample_rate={SR}",
                    "-f", "lavfi", "-i", f"sine=frequency=82.4:duration={total + 1}:sample_rate={SR}",
                    "-filter_complex",
                    "[0]lowpass=f=400,volume=0.25[a];[1]volume=0.10,tremolo=f=0.2:d=0.6[b];"
                    "[2]volume=0.05,tremolo=f=0.13:d=0.7[c];[a][b][c]amix=inputs=3:normalize=0,"
                    "afade=t=out:st=" + str(punch_end + 0.2) + ":d=1.5",
                    "-ac", "1", amb], check=True)
    ambient = read_wav(amb)
    put(ambient, 0.0, 0.8)
    # Ducking: Ambient leiser während der Pointe ist schon via fade
    mixl = np.tanh(mixl * 0.9) * 0.92
    mixl[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    pcm = (np.clip(mixl, -1, 1) * 32767).astype(np.int16)
    audio_path = os.path.join(work_dir, f"mix_{num}.wav")
    with wave.open(audio_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    # ------------------------------------------------ VIDEO
    bg = make_bg(ep["place"], num)
    vig = make_vignette()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    out_path = os.path.join(out_dir, f"zombie_teil_{num}_{ep['title'].lower().replace(' ', '_')}.mp4"
                            .replace("ü", "ue").replace("ö", "oe").replace("ä", "ae"))
    stills = [float(x) for x in os.environ.get("STILLS", "").split(",") if x]
    enc = None if stills else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error",
                            "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", audio_path,
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                            "-shortest", "-movflags", "+faststart", out_path], stdin=subprocess.PIPE)

    particles = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1), random.uniform(2, 6))
                 for _ in range(70)]
    horde = [(random.uniform(-100, W + 100), random.uniform(0.22, 0.42), random.random() * 10) for _ in range(16)]
    horde.sort(key=lambda h: h[1])

    def line_at(t):
        cur = None
        for ln in lines:
            if ln["start"] - 0.05 <= t <= ln["start"] + ln["dur"] + 0.35:
                cur = ln
        return cur

    print(f"Teil {num}: {total:.1f}s", flush=True)
    for f in range(int(total * FPS)):
        t = f / FPS
        ln = line_at(t)
        # Kamera
        zoom, fx_, fy_ = 1.0, W / 2, 1000
        for l2 in lines:
            if l2["action"] in ("zoom", "punch") and l2["start"] - 0.1 <= t:
                spk = l2["speaker"]
                endt = l2["start"] + l2["dur"] + (3.5 if l2["action"] == "punch" else 0.6)
                if t <= endt:
                    p = ease((t - l2["start"]) / (0.35 if l2["action"] == "punch" else l2["dur"] + 0.5))
                    out = 1 - ease((t - (endt - 0.4)) / 0.4) if l2["action"] != "punch" else 1
                    target = 1.22 if l2["action"] == "punch" else 1.12
                    zoom = 1 + (target - 1) * p * out
                    if spk in actors:
                        ax = actors[spk].pos(t)[0]
                        fx_ = ax
                    fy_ = 900
        shake_x = shake_y = 0.0
        for l2 in lines:
            if l2["action"] in ("shake", "flash") or l2.get("enter"):
                st = l2["start"] - (0.1 if l2.get("enter") else 0)
                if 0 <= t - st < 0.6:
                    k = (1 - (t - st) / 0.6) * (26 if l2["action"] == "shake" else 14)
                    shake_x += math.sin(t * 90) * k
                    shake_y += math.cos(t * 77) * k

        ctx.save()
        ctx.translate(W / 2 + shake_x, 1000 + shake_y)
        ctx.scale(zoom, zoom)
        ctx.translate(-(W / 2 + (fx_ - W / 2) * (zoom - 1) / zoom * 1.6), -1000)
        ctx.set_source_surface(bg, 0, 0); ctx.paint()
        dynamic_bg(ctx, ep["place"], t, None)

        # Horde im Hintergrund
        if horde_start is not None and t > horde_start:
            a_in = ease((t - horde_start) / 1.5)
            for (hx0, hs, hseed) in horde:
                hx = (hx0 - (t - horde_start) * 22 * hs) % (W + 200) - 100
                ctx.save()
                ctx.translate(hx, 1265 + (hs - 0.22) * 260 - (1 - a_in) * 60)
                c = int(25 + hs * 60)
                draw_person(ctx, CAST["ZOMBIE"], t, 0, -1, True, hs * a_in,
                            silhouette=(c, int(c * 0.6), int(c * 0.6)), seed=hseed)
                ctx.restore()

        # Darsteller zeichnen (Menschen + Zombies)
        zon = zombie_on(t)
        punch_done = t > punch_end + 0.3
        order = sorted(actors.values(), key=lambda a: a.pos(t)[0])
        for a in order:
            if not a.present:
                continue
            x, walking, fleeing = a.pos(t)
            if x > W + 300:
                continue
            facing = a.facing
            is_z = CAST[a.key].get("zombie")
            mood = "drama"
            if not is_z:
                if zon and a.x < 800:
                    facing = 1
                if punch_done:
                    mood = "laugh" if lines[-1]["speaker"] != a.key else "neutral"
                elif ln is not None and ln["action"] == "punch" and ln["speaker"] != a.key:
                    mood = "shock"
            cure = 0.0
            if is_z and cure_at is not None:
                cure = ease((t - cure_at) / 1.2)
            if is_z and (fleeing or a.fled(t)):
                facing = 1
            av = amp.get(a.key)
            am = float(av[f]) if av is not None and f < len(av) else 0.0
            if ln is None or ln["speaker"] != a.key:
                am = 0.0 if am < 0.5 else am
            ctx.save()
            ctx.translate(x, GROUND + (30 if is_z else 0))
            draw_person(ctx, CAST[a.key], t, am, facing, walking, CS,
                        cure=cure, mood=mood, prop=props.get(a.key), seed=a.seed, flee=fleeing)
            ctx.restore()
            # "Schreck"-Zeichen über Zuhörern bei der Pointe
            if not is_z and ln is not None and ln["action"] == "punch" and ln["speaker"] != a.key and not punch_done:
                font(ctx, 110)
                text_outline(ctx, "?!", x - 40, GROUND - 640 * CS - 30, (1, 0.9, 0.2, 1), (0, 0, 0, 1), 12)
            if punch_done and not is_z and lines[-1]["speaker"] != a.key:
                font(ctx, 70)
                bounce = abs(math.sin(t * 9)) * 20
                text_outline(ctx, "HAHA", x - 85, GROUND - 650 * CS - 40 - bounce, (1, 1, 1, 1), (0, 0, 0, 1), 10)

        # Nebel
        for i in range(5):
            fx = ((t * (18 + i * 7) + i * 300) % (W + 800)) - 400
            g = cairo.RadialGradient(fx, 1500 + i * 40, 20, fx, 1500 + i * 40, 420)
            g.add_color_stop_rgba(0, 0.8, 0.75, 0.75, 0.10)
            g.add_color_stop_rgba(1, 0.8, 0.75, 0.75, 0)
            ctx.set_source(g); ctx.rectangle(fx - 420, 1080, 840, 840); ctx.fill()
        ctx.restore()

        # Partikel (Asche / Staub)
        for i, (px, py, sp, sz) in enumerate(particles):
            if ep["place"] == "street":
                yy = (py - t * 60 * sp) % H
                xx = (px + math.sin(t + i) * 30) % W
                ctx.set_source_rgba(1, 0.55 + 0.3 * sp, 0.2, 0.55 * sp)
            else:
                yy = (py + t * 25 * sp) % H
                xx = (px + math.sin(t * 0.5 + i) * 20) % W
                ctx.set_source_rgba(0.9, 0.9, 0.85, 0.25 * sp)
            ctx.arc(xx, yy, sz * 0.7, 0, 2 * math.pi); ctx.fill()

        ctx.set_source_surface(vig, 0, 0); ctx.paint()

        # Herzschlag: roter Puls
        if ln is not None and ln["action"] == "heart":
            beat = ((t - ln["start"]) % 0.85) / 0.85
            pulse = math.exp(-beat * 8) * 0.35
            g = cairo.RadialGradient(W / 2, H / 2, 400, W / 2, H / 2, 1200)
            g.add_color_stop_rgba(0, 0.6, 0, 0, 0)
            g.add_color_stop_rgba(1, 0.7, 0, 0, pulse + 0.15)
            ctx.set_source(g); ctx.paint()

        # Blitz
        for l2 in lines:
            if l2["action"] == "flash" and 0 <= t - l2["start"] < 0.45:
                ctx.set_source_rgba(1, 1, 1, 0.8 * (1 - (t - l2["start"]) / 0.45))
                ctx.paint()
        if cure_at is not None and 0 <= t - cure_at < 1.0:
            ctx.set_source_rgba(0.3, 1, 0.4, 0.45 * (1 - (t - cure_at)))
            ctx.paint()

        # Oben: Serien-Banner
        font(ctx, 40)
        banner = f"ZOMBIE-APOKALYPSE  ·  TEIL {num}/{TOTAL_EPS}"
        tw = ctx.text_extents(banner).x_advance
        ctx.set_source_rgba(0.75, 0.05, 0.05, 0.92)
        rrect(ctx, W / 2 - tw / 2 - 30, 168, tw + 60, 66, 14); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 1); ctx.move_to(W / 2 - tw / 2, 215); ctx.show_text(banner)
        font(ctx, 58)
        title = ep["title"].upper()
        tw = ctx.text_extents(title).x_advance
        text_outline(ctx, title, W / 2 - tw / 2, 310, (1, 1, 1, 1), (0, 0, 0, 1), 12)

        # Hook (erste Sekunden) groß
        if t < 2.0:
            a = ease(t / 0.3) * (1 - ease((t - 1.65) / 0.3))
            font(ctx, 66)
            hl = wrap(ctx, ep["hook"].split(), 900)
            for i, l3 in enumerate(hl):
                txt = " ".join(w for _, w in l3)
                tw = ctx.text_extents(txt).x_advance
                text_outline(ctx, txt, W / 2 - tw / 2, 560 + i * 80, (1, 0.86, 0.1, a), (0, 0, 0, a), 14)

        # Untertitel
        if ln is not None:
            draw_subtitle(ctx, ln, t)

        # Outro
        if t > punch_end + 0.5:
            a = ease((t - punch_end - 0.5) / 0.4)
            ctx.set_source_rgba(0, 0, 0, 0.45 * a); ctx.rectangle(0, 1560, W, 260); ctx.fill()
            font(ctx, 56)
            if num < TOTAL_EPS:
                txt = f"Teil {num + 1} kommt… Folgen!"
            else:
                txt = "ENDE. Welcher Teil war der beste?"
            tw = ctx.text_extents(txt).x_advance
            text_outline(ctx, txt, W / 2 - tw / 2, 1665, (1, 1, 1, a), (0, 0, 0, a), 10)
            font(ctx, 40)
            txt2 = "#zombie #apokalypse #drama #comedy"
            tw = ctx.text_extents(txt2).x_advance
            ctx.set_source_rgba(1, 0.86, 0.1, a); ctx.move_to(W / 2 - tw / 2, 1745); ctx.show_text(txt2)

        # Ein-/Ausblenden
        if t < 0.4:
            ctx.set_source_rgba(0, 0, 0, 1 - t / 0.4); ctx.paint()
        if t > total - 0.4:
            ctx.set_source_rgba(0, 0, 0, (t - (total - 0.4)) / 0.4); ctx.paint()

        surf.flush()
        if stills:
            for st in stills:
                if int(st * FPS) == f:
                    surf.write_to_png(os.path.join(work_dir, f"still_{num}_{st:.1f}.png"))
            if f > max(stills) * FPS:
                break
            continue
        enc.stdin.write(bytes(surf.get_data()))

    if enc is None:
        return None
    enc.stdin.close()
    enc.wait()
    print(f"fertig: {out_path} ({total:.1f}s)")
    return out_path


if __name__ == "__main__":
    idx = int(sys.argv[1]) - 1
    out = sys.argv[2] if len(sys.argv) > 2 else "out"
    work = os.environ.get("WORK_DIR", "work")
    os.makedirs(out, exist_ok=True); os.makedirs(work, exist_ok=True)
    build(idx, out, work)
