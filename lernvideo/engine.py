"""Animations-Engine für die Lernclips (handgemachter Look, 1440p, 60 fps).

Koordinaten im Drehbuch sind immer in 1920x1080 angegeben und werden intern hochskaliert.
Benötigt: Pillow, numpy, fontTools, ffmpeg, pico2wave, Schriften Comic Neue + Inter + Noto Color Emoji.
"""
import math
import os
import random
import re
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --------------------------------------------------------------------------- Grundeinstellungen
DW, DH = 1920, 1080          # Design-Koordinaten
W, H = 2560, 1440            # Ausgabe
K = W / DW
FPS = 60
SR = 22050
SS = 2                       # Supersampling für glatte Linien

HAND_FONT = "/usr/share/fonts/opentype/comic-neue/ComicNeue-"
FALLBACK_FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

INK = (30, 30, 42)
MUTED = (88, 90, 105)
WHITE = (255, 255, 255)
BLUE = (45, 107, 255)
YELLOW = (255, 210, 50)
GREEN = (24, 178, 110)
RED = (232, 60, 60)
LIGHT_Y = (255, 244, 200)
LIGHT_G = (218, 246, 230)
LIGHT_R = (255, 226, 226)
LIGHT_B = (224, 235, 255)

rng = random.Random(11)


def k(v):
    return int(round(v * K))


# --------------------------------------------------------------------------- Schrift
_fonts, _cmap = {}, None


def font(px, bold=True, fallback=False):
    key = (px, bold, fallback)
    if key not in _fonts:
        path = FALLBACK_FONT if fallback else HAND_FONT + ("Bold" if bold else "Regular") + ".otf"
        _fonts[key] = ImageFont.truetype(path, px)
    return _fonts[key]


def has_glyph(ch):
    global _cmap
    if _cmap is None:
        from fontTools.ttLib import TTFont
        _cmap = TTFont(HAND_FONT + "Bold.otf").getBestCmap()
    return ch == " " or ord(ch) in _cmap


def runs(line):
    out = []
    for ch in line:
        fb = not has_glyph(ch)
        if out and out[-1][1] == fb:
            out[-1][0] += ch
        else:
            out.append([ch, fb])
    return out


_meas = ImageDraw.Draw(Image.new("RGBA", (1, 1)))


def textlen(line, px, bold):
    return sum(_meas.textlength(t, font=font(px, bold, fb)) for t, fb in runs(line))


def wrap(s, px, bold, maxw):
    if maxw is None:
        return s.split("\n")
    lines = []
    for para in s.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if textlen(t, px, bold) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_img(s, size, color=INK, bold=True, maxw=None, align="center", spacing=1.2):
    px = k(size)
    f = font(px, bold)
    lines = wrap(s, px, bold, k(maxw) if maxw else None)
    lw = [textlen(l, px, bold) for l in lines]
    asc, desc = f.getmetrics()
    lh = int(px * spacing)
    w = int(max(lw)) + 12
    h = lh * (len(lines) - 1) + asc + desc + 12
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (l, ww) in enumerate(zip(lines, lw)):
        x = {"center": (w - ww) / 2, "left": 6, "right": w - ww - 6}[align]
        for t, fb in runs(l):
            ff = font(px, bold, fb)
            dy = (asc - ff.getmetrics()[0]) if fb else 0
            d.text((x, 6 + i * lh + dy), t, font=ff, fill=color)
            x += d.textlength(t, font=ff)
    return im


# --------------------------------------------------------------------------- Bildbausteine
_emoji_cache = {}


def emoji_img(ch, size):
    key = (ch, size)
    if key not in _emoji_cache:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((20, 20), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox())
        s = k(size) / max(im.size)
        _emoji_cache[key] = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    return _emoji_cache[key]


def paste(base, im, x, y):
    x, y = int(round(x)), int(round(y))
    if x >= base.width or y >= base.height or x + im.width <= 0 or y + im.height <= 0:
        return
    if x < 0 or y < 0 or x + im.width > base.width or y + im.height > base.height:
        im = im.crop((max(0, -x), max(0, -y), min(im.width, base.width - x), min(im.height, base.height - y)))
        x, y = max(0, x), max(0, y)
    base.alpha_composite(im, (x, y))


def wobble_poly(w, h, r, amp):
    """Abgerundetes Rechteck mit leichtem Zittern (Pixel-Koordinaten)."""
    r = min(r, h / 2, w / 2)
    pts = []
    for cx, cy, a0 in [(w - r, r, -90), (w - r, h - r, 0), (r, h - r, 90), (r, r, 180)]:
        for j in range(10):
            a = math.radians(a0 + j * 10)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    dense = []
    for i in range(len(pts)):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % len(pts)]
        n = max(1, int(math.hypot(bx - ax, by - ay) / (20 * SS)))
        for j in range(n):
            dense.append((ax + (bx - ax) * j / n, ay + (by - ay) * j / n))
    p1, p2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
    out = []
    for i, (x, y) in enumerate(dense):
        t = i / len(dense) * 2 * math.pi
        j = amp * (0.6 * math.sin(3 * t + p1) + 0.4 * math.sin(7 * t + p2))
        out.append((x + 0.6 * j, y + j))
    return out


def panel(wd, hd, fill=WHITE, radius=26, ow=3.2, outline=INK, shadow=True):
    """Gezeichnete Fläche. Rückgabe: (Bild, Rand m) – Inhalt beginnt bei (m, m)."""
    w, h = k(wd), k(hd)
    m = k(18)
    big = Image.new("RGBA", ((w + 2 * m) * SS, (h + 2 * m) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    poly = [(x + m * SS, y + m * SS) for x, y in wobble_poly(w * SS, h * SS, k(radius) * SS, 2.2 * K * SS)]
    d.polygon(poly, fill=fill)
    lw = max(2, int(k(ow) * SS))
    d.line(poly + [poly[0]], fill=outline, width=lw, joint="curve")
    off = [(x + rng.uniform(-1.5, 1.5) * SS, y + rng.uniform(-1.5, 1.5) * SS) for x, y in poly]
    d.line(off + [off[0]], fill=outline, width=max(1, lw - 2 * SS), joint="curve")
    shape = big.resize((w + 2 * m, h + 2 * m), Image.LANCZOS)
    if not shadow:
        return shape, m
    a = shape.getchannel("A").point(lambda v: int(v * 0.16))
    sh = Image.new("RGBA", shape.size, INK + (0,))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(k(7)))
    out = Image.new("RGBA", shape.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (k(3), k(7)) if k(7) < m else (0, 0))
    out.alpha_composite(shape)
    return out, m


def hand_line(d, pts, color, width):
    d.line(pts, fill=color, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def card_img(wd, hd, emo, title, sub, accent=BLUE, tsize=38, ssize=29, esize=80, fill=WHITE):
    im, m = panel(wd, hd, fill=fill)
    e = emoji_img(emo, esize)
    ex, ey = m + k(28), m + k(30)
    paste(im, e, ex, ey)
    tx = ex + e.width + k(20)
    t = text_img(title, tsize, INK, True, maxw=wd - (tx - m) / K - 24, align="left", spacing=1.08)
    ty = ey + (e.height - t.height) / 2 if t.height < e.height else ey - k(4)
    paste(im, t, tx, ty)
    # gezeichnete Unterstreichung in Akzentfarbe
    big = Image.new("RGBA", (im.width * SS, im.height * SS), (0, 0, 0, 0))
    uy = (ty + t.height - k(2)) * SS
    ulen = min(t.width - k(10), im.width - tx - m - k(20)) * SS
    pts = [(tx * SS + k(4) * SS + j * ulen / 14, uy + math.sin(j * 0.8 + rng.uniform(0, 3)) * k(2) * SS)
           for j in range(15)]
    hand_line(ImageDraw.Draw(big), pts, accent + (235,), k(5) * SS)
    im.alpha_composite(big.resize(im.size, Image.LANCZOS))
    s = text_img(sub, ssize, (66, 68, 84), False, maxw=wd - 52, align="left", spacing=1.18)
    paste(im, s, m + k(24), max(ty + t.height + k(10), ey + e.height + k(8)))
    return im


def chip_img(label, emo=None, size=40, fill=WHITE, color=INK, padx=30, pady=14, shadow=True):
    t = text_img(label, size, color)
    e = emoji_img(emo, int(size * 1.15)) if emo else None
    ew = (e.width + k(12)) if e else 0
    wd = (k(padx) * 2 + ew + t.width) / K
    hd = (k(pady) * 2 + max(t.height, e.height if e else 0)) / K
    im, m = panel(wd, hd, fill=fill, radius=hd / 2, shadow=shadow)
    x = m + k(padx)
    if e:
        paste(im, e, x, m + (k(hd) - e.height) / 2)
    paste(im, t, x + ew, m + (k(hd) - t.height) / 2)
    return im


def node_img(emo, label, wd=340, hd=118, fill=WHITE):
    im, m = panel(wd, hd, fill=fill)
    e = emoji_img(emo, 62)
    t = text_img(label, 38)
    x = m + (k(wd) - e.width - k(14) - t.width) / 2
    paste(im, e, x, m + (k(hd) - e.height) / 2)
    paste(im, t, x + e.width + k(14), m + (k(hd) - t.height) / 2)
    return im


def row_img(emo, label, wd=800, hd=84, fill=WHITE, tsize=32):
    im, m = panel(wd, hd, fill=fill, radius=20)
    e = emoji_img(emo, 46)
    paste(im, e, m + k(22), m + (k(hd) - e.height) / 2)
    t = text_img(label, tsize, INK, True, maxw=wd - 110, align="left")
    paste(im, t, m + k(22) + e.width + k(18), m + (k(hd) - t.height) / 2)
    return im


def marker_img(wd, hd, color=YELLOW):
    w, h = k(wd), k(hd)
    big = Image.new("RGBA", ((w + 40) * SS, (h + 40) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    top = [((20 + j * w / 24) * SS, (20 + rng.uniform(-0.06, 0.08) * h) * SS) for j in range(25)]
    bot = [((20 + j * w / 24) * SS, (20 + h + rng.uniform(-0.08, 0.06) * h) * SS) for j in range(24, -1, -1)]
    d.polygon(top + bot, fill=color + (205,))
    im = big.resize((w + 40, h + 40), Image.LANCZOS)
    return im.rotate(rng.uniform(-1.6, 0.6), expand=True, resample=Image.BICUBIC)


_logo = None


def logo_img(hd):
    global _logo
    if _logo is None:
        _logo = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "toyota_logo.png")).convert("RGBA")
    h = k(hd)
    return _logo.resize((round(_logo.width * h / _logo.height), h), Image.LANCZOS)


# --------------------------------------------------------------------------- Sprites
def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.9):
    x = min(1.0, max(0.0, x))
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class Sprite:
    """Bild-Element. x/y = Mittelpunkt in Design-Koordinaten."""

    def __init__(self, img, x, y, anim="pop", f=0.0, d=0.0, idle=False, tilt=True, focus=False, pen=False):
        self.rot = rng.uniform(-1.5, 1.5) if tilt else 0.0
        self.base = img.rotate(self.rot, expand=True, resample=Image.BICUBIC) if self.rot else img
        self.x, self.y = k(x), k(y)
        self.anim, self.f, self.d = anim, f, d
        self.idle, self.focus, self.pen = idle, focus, pen
        self.phase = rng.uniform(0, 6.3)
        self.t = 0.0
        self._rot_cache = {}
        self._dim = None
        self.sfx = {"pop": "pop", "drop": "pop", "rise": "soft", "slide": "soft", "write": "pencil",
                    "wipe": "marker", "fade": None}.get(anim)

    @property
    def dur(self):
        return {"pop": 0.45, "drop": 0.6, "rise": 0.45, "slide": 0.5, "write": min(1.3, 0.45 + self.base.width / k(900)),
                "wipe": 0.5, "fade": 0.4}[self.anim]

    def _rot(self, img, ang):
        if abs(ang) < 0.05:
            return img
        return img.rotate(ang, expand=True, resample=Image.BICUBIC)

    def _alpha(self, img, a):
        if a >= 0.999:
            return img
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        return img

    def draw(self, frame, now, dim=0.0, exit_p=0.0, pen_img=None):
        p = (now - self.t) / self.dur
        img = self.base
        dx = dy = 0.0
        sx = sy = 1.0
        ang = 0.0
        alpha = 1.0
        crop = None
        if p < 1:
            if self.anim == "pop":
                s = max(0.02, ease_back(p))
                q = math.sin(math.pi * min(1, p * 1.2)) * 0.10
                sx, sy = s * (1 + q), s * (1 - q)
                alpha = min(1, p * 5)
                ang = (1 - ease_out(p)) * -8
            elif self.anim == "drop":
                dy = -(1 - ease_back(p, 1.4)) * k(70)
                ang = (1 - ease_out(p)) * 7
                alpha = min(1, p * 4)
                s = 0.92 + 0.08 * ease_back(p)
                sx = sy = s
            elif self.anim == "rise":
                dy = (1 - ease_out(p)) * k(36)
                alpha = ease_out(p)
            elif self.anim == "slide":
                dx = -(1 - ease_out(p)) * k(80)
                alpha = ease_out(p)
            elif self.anim == "fade":
                alpha = ease_io(p)
            elif self.anim in ("write", "wipe"):
                crop = ease_io(p) if self.anim == "write" else ease_out(p)
        if self.idle and p >= 0:
            tt = now - self.t
            dy += math.sin(tt * 2.2 + self.phase) * k(4)
            ang += round(math.sin(tt * 1.6 + self.phase) * 2.5 * 2) / 2
        if exit_p > 0:
            e = ease_io(exit_p)
            sx *= 1 - 0.15 * e
            sy *= 1 - 0.15 * e
            dy += e * k(24)
            alpha *= 1 - e
        if dim > 0:
            alpha *= 1 - 0.55 * dim
            s = 1 - 0.03 * dim
            sx *= s
            sy *= s
        if alpha <= 0.01:
            return
        if crop is not None:
            w = max(1, int(img.width * crop))
            soft = k(40)
            img = img.copy()
            mask = Image.new("L", img.size, 0)
            md = ImageDraw.Draw(mask)
            md.rectangle([0, 0, max(0, w - soft), img.height], fill=255)
            for i in range(soft):
                xx = w - soft + i
                if 0 <= xx < img.width:
                    md.line([(xx, 0), (xx, img.height)], fill=int(255 * (1 - i / soft)))
            a = img.getchannel("A")
            img.putalpha(Image.composite(a, Image.new("L", img.size, 0), mask))
            if self.pen and pen_img is not None and crop < 1:
                ox, oy = self.x - self.base.width / 2, self.y - self.base.height / 2
                paste(frame, img, ox, oy)
                px_ = ox + w - soft * 0.4
                py_ = oy + img.height * (0.55 + 0.15 * math.sin(now * 25))
                paste(frame, pen_img, px_, py_ - pen_img.height)
                return
        if ang:
            key = round(ang * 2) / 2
            if sx == sy == 1 and alpha == 1 and dx == 0 and self.idle:
                if key not in self._rot_cache:
                    self._rot_cache[key] = self._rot(img, key)
                img = self._rot_cache[key]
            else:
                img = self._rot(img, ang)
        if sx != 1 or sy != 1:
            img = img.resize((max(1, int(img.width * sx)), max(1, int(img.height * sy))), Image.BILINEAR)
        img = self._alpha(img, alpha)
        paste(frame, img, self.x + dx - img.width / 2, self.y + dy - img.height / 2)


class Stroke:
    """Handgezeichnete Linie(n), die nach und nach gezeichnet werden. pts in Design-Koordinaten."""

    def __init__(self, paths, color=RED, width=6, f=0.0, d=0.0, dur=0.7, pen=True):
        self.paths = [[(k(x) * SS, k(y) * SS) for x, y in p] for p in paths]
        allp = [pt for p in self.paths for pt in p]
        pad = k(width) * SS + 8
        self.x0 = min(x for x, _ in allp) - pad
        self.y0 = min(y for _, y in allp) - pad
        self.w = int(max(x for x, _ in allp) + pad - self.x0)
        self.h = int(max(y for _, y in allp) + pad - self.y0)
        self.paths = [[(x - self.x0, y - self.y0) for x, y in p] for p in self.paths]
        self.lens = [sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1)) for p in self.paths]
        self.total = sum(self.lens)
        self.color, self.width = color, k(width) * SS
        self.f, self.d, self.dur, self.pen = f, d, dur, pen
        self.anim, self.sfx, self.focus, self.t = "stroke", "pencil", False, 0.0
        self._full = None

    def _render(self, p):
        big = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        remaining = self.total * p
        tip = None
        for path, L in zip(self.paths, self.lens):
            if remaining <= 0:
                break
            pts = [path[0]]
            acc = 0
            for i in range(len(path) - 1):
                seg = math.dist(path[i], path[i + 1])
                if acc + seg <= remaining:
                    pts.append(path[i + 1])
                    acc += seg
                else:
                    r = (remaining - acc) / seg
                    pts.append((path[i][0] + (path[i + 1][0] - path[i][0]) * r,
                                path[i][1] + (path[i + 1][1] - path[i][1]) * r))
                    acc = remaining
                    break
            if len(pts) >= 2:
                hand_line(d, pts, self.color, self.width)
            tip = pts[-1]
            remaining -= L
        img = big.resize((max(1, self.w // SS), max(1, self.h // SS)), Image.LANCZOS)
        return img, tip

    def draw(self, frame, now, dim=0.0, exit_p=0.0, pen_img=None):
        p = min(1.0, (now - self.t) / self.dur)
        if p >= 1:
            if self._full is None:
                self._full = self._render(1)[0]
            img, tip = self._full, None
        else:
            img, tip = self._render(ease_io(p))
        if exit_p > 0:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * (1 - ease_io(exit_p)))))
        ox, oy = self.x0 / SS, self.y0 / SS
        paste(frame, img, ox, oy)
        if self.pen and pen_img is not None and tip is not None and p < 1:
            paste(frame, pen_img, ox + tip[0] / SS - k(6), oy + tip[1] / SS - pen_img.height + k(6))


# --------------------------------------------------------------------------- Drehbuch-Helfer
def E(ch, x, y, size, anim="pop", f=0.0, d=0.0, idle=True):
    return Sprite(emoji_img(ch, size), x, y, anim, f, d, idle=idle, tilt=False)


def T(s, x, y, size=40, color=INK, bold=True, anim="rise", f=0.0, d=0.0, maxw=None, tilt=True):
    return Sprite(text_img(s, size, color, bold, maxw), x, y, anim, f, d, tilt=tilt)


def TITLE(s, y=170, size=84, emo=None, f=0.0):
    t = text_img(s, size, INK, True)
    tw = t.width / K
    out = [Sprite(marker_img(tw + 50, size * 0.62), 960, y + size * 0.14, "wipe", f=f, tilt=False),
           Sprite(t, 960, y, "write", f=f, d=0.12, tilt=False, pen=True)]
    if emo:
        out.append(E(emo, 960 + tw / 2 + 40 + size * 0.45, y, int(size * 0.9), f=f, d=0.9))
    return out


def CARD(x, y, w, h, emo, title, sub, accent=BLUE, f=0.0, d=0.0, focus=True, **kw):
    return Sprite(card_img(w, h, emo, title, sub, accent, **kw), x, y, "drop", f, d, focus=focus)


def CHIP(label, x, y, emo=None, size=40, fill=WHITE, color=INK, f=0.0, d=0.0, anim="pop", **kw):
    return Sprite(chip_img(label, emo, size, fill, color, **kw), x, y, anim, f, d)


def CHIPROW(items, y, size=36, gap=26, f0=0.0, step=0.12):
    ims = [chip_img(l, e, size) for l, e in items]
    total = sum(i.width for i in ims) / K + gap * (len(ims) - 1)
    x = (DW - total) / 2
    out = []
    for n, im in enumerate(ims):
        out.append(Sprite(im, x + im.width / K / 2, y, "pop", f0 + n * step))
        x += im.width / K + gap
    return out


def NODE(emo, label, x, y, w=340, h=118, f=0.0, d=0.0, fill=WHITE):
    return Sprite(node_img(emo, label, w, h, fill), x, y, "pop", f, d)


def ROW(emo, label, x, y, w=800, h=84, fill=WHITE, tsize=32, f=0.0, d=0.0, anim="slide"):
    return Sprite(row_img(emo, label, w, h, fill, tsize), x, y, anim, f, d)


def LOGO(x, y, h, f=0.0, d=0.0):
    return Sprite(logo_img(h), x, y, "pop", f, d, tilt=False)


def NOTE(s, x, y, color=RED, size=36, rot=None, f=0.0, d=0.0):
    sp = Sprite(text_img(s, size, color, True), x, y, "write", f, d, tilt=False, pen=True)
    r = rot if rot is not None else rng.uniform(-6, -2)
    sp.base = sp.base.rotate(r, expand=True, resample=Image.BICUBIC)
    return sp


def ARROW(x1, y1, x2, y2, color=INK, width=6, bend=None, f=0.0, d=0.0, dur=0.55, pen=False):
    bend = rng.uniform(-14, 14) if bend is None else bend
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    L = math.hypot(x2 - x1, y2 - y1) or 1
    nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    cx, cy = mx + nx * bend, my + ny * bend
    pts = []
    for i in range(21):
        t = i / 20
        pts.append(((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2,
                    (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2))
    ang = math.atan2(y2 - pts[-3][1], x2 - pts[-3][0])
    hl = 26
    h1 = [(x2 - hl * math.cos(ang - 0.5), y2 - hl * math.sin(ang - 0.5)), (x2, y2)]
    h2 = [(x2, y2), (x2 - hl * math.cos(ang + 0.5), y2 - hl * math.sin(ang + 0.5))]
    return Stroke([pts, h1, h2], color, width, f, d, dur, pen)


def UNDERLINE(x1, x2, y, color=RED, width=6, f=0.0, d=0.0):
    pts = [(x1 + (x2 - x1) * i / 16, y + math.sin(i * 0.7 + rng.uniform(0, 1)) * 3 + i * 0.25) for i in range(17)]
    return Stroke([pts], color, width, f, d, 0.5)


def CIRCLE(cx, cy, rx, ry, color=RED, width=6, f=0.0, d=0.0):
    a0 = rng.uniform(-2.6, -2.0)
    pts = []
    n = 48
    for i in range(n + 1):
        t = i / n
        a = a0 + t * (2 * math.pi + 0.45)
        s = 1 + 0.06 * t + rng.uniform(-0.01, 0.01)
        pts.append((cx + rx * s * math.cos(a), cy + ry * s * math.sin(a)))
    return Stroke([pts], color, width, f, d, 0.8)


def CHECK(x, y, size=40, color=GREEN, width=8, f=0.0, d=0.0):
    return Stroke([[(x - size * 0.5, y), (x - size * 0.1, y + size * 0.4), (x + size * 0.6, y - size * 0.55)]],
                  color, width, f, d, 0.4)


def CROSS(x, y, size=60, color=RED, width=9, f=0.0, d=0.0):
    s = size / 2
    return Stroke([[(x - s, y - s), (x + s, y + s * 0.9)], [(x + s * 0.9, y - s), (x - s * 0.9, y + s)]],
                  color, width, f, d, 0.45)


def EMPH(x, y, r=40, color=RED, width=5, f=0.0, d=0.0):
    """Drei kleine Striche – „Achtung, wichtig“."""
    paths = []
    for a in (-150, -110, -70):
        ra = math.radians(a)
        paths.append([(x + r * math.cos(ra), y + r * math.sin(ra)),
                      (x + (r + 26) * math.cos(ra), y + (r + 26) * math.sin(ra))])
    return Stroke(paths, color, width, f, d, 0.4, pen=False)


def LINE(pts, color=INK, width=4, f=0.0, d=0.0, dur=0.6):
    return Stroke([pts], color, width, f, d, dur, pen=False)


def B(sub, add=(), clear=False, pause=0.45):
    return dict(sub=sub, add=list(add), clear=clear, pause=pause)


def SC(label, beats, focus=False):
    return dict(label=label, beats=beats, focus=focus)


# --------------------------------------------------------------------------- Ton
SAY = [("Lean Production", "Lien Prodacktschen"), ("Lean", "Lien"), ("KVP", "Ka Fau Pe"), ("Toyota", "Toyota")]


def to_say(s):
    for a, b in SAY:
        s = re.sub(r"\b" + re.escape(a) + r"\b", b, s)
    return s


def tts(s, path):
    subprocess.run(["pico2wave", "-l", "de-DE", "-w", path, to_say(s)], check=True)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
        sr = w.getframerate()
    nz = np.where(np.abs(a) > 300)[0]
    if len(nz):
        a = a[max(0, nz[0] - 400): nz[-1] + 1600]
    if sr != SR:
        a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a)
    return a * (19000 / max(1.0, np.abs(a).max()))


def sfx(kind, seed):
    r = np.random.default_rng(seed)
    if kind == "pop":
        n = int(SR * 0.09)
        t = np.arange(n) / SR
        f0 = r.uniform(520, 760)
        freq = f0 * (1.6 - 6 * t)
        return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 48) * 3200
    if kind == "soft":
        n = int(SR * 0.07)
        t = np.arange(n) / SR
        return np.sin(2 * np.pi * r.uniform(380, 480) * t) * np.exp(-t * 60) * 1500
    if kind in ("pencil", "marker"):
        dur = 0.6 if kind == "pencil" else 0.4
        n = int(SR * dur)
        noise = r.normal(size=n)
        noise = noise - np.convolve(noise, np.ones(6) / 6, mode="same")   # hohe Frequenzen
        t = np.arange(n) / SR
        mod = 0.55 + 0.45 * np.sin(2 * np.pi * r.uniform(9, 14) * t) ** 2
        env = np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.1)
        return noise * mod * env * (650 if kind == "pencil" else 420)
    if kind == "whoosh":
        n = int(SR * 0.45)
        noise = np.convolve(r.normal(size=n), np.ones(18) / 18, mode="same")
        env = np.sin(np.linspace(0, np.pi, n)) ** 2
        return noise * env * 4200
    return np.zeros(1)


# --------------------------------------------------------------------------- Zeitplan & Rendering
LEAD, TRANS, EXIT = 0.35, 0.5, 0.4


def timeline(scenes, tmp, voice_override=None):
    t = 0.5
    voice, effects, subs = [], [], []
    seed = 1
    for si, sc in enumerate(scenes):
        if si > 0:
            effects.append((t - TRANS, sfx("whoosh", seed)))
        sc["start"] = t
        t += LEAD
        for bi, b in enumerate(sc["beats"]):
            if b["clear"]:
                b["exit_t"] = t
                t += EXIT
            if voice_override is not None:
                a = voice_override[(si, bi)]
            else:
                a = tts(b["sub"], os.path.join(tmp, f"{si}_{bi}.wav"))
            dur = len(a) / SR
            b["t0"], b["dur"] = t, dur
            voice.append((t, a))
            subs.append((t, t + dur, b["sub"]))
            for sp in b["add"]:
                sp.t = t + sp.d + sp.f * dur
                if sp.sfx:
                    seed += 1
                    effects.append((sp.t, sfx(sp.sfx, seed)))
            t += dur + b["pause"]
        t += 0.6
        sc["end"] = t
        t += TRANS
    total = t + 0.4
    audio = np.zeros(int(total * SR) + SR)
    for st, a in voice + effects:
        i = int(st * SR)
        audio[i:i + len(a)] += a[: len(audio) - i]
    voice_only = np.zeros_like(audio)
    for st, a in voice:
        i = int(st * SR)
        voice_only[i:i + len(a)] += a[: len(audio) - i]
    fx_only = audio - voice_only
    return total, audio, fx_only, subs


_pen = None


def pen_img():
    global _pen
    if _pen is None:
        _pen = emoji_img("✏", 64)
    return _pen


def draw_scene(sc, now, frame):
    sprites = []      # (sprite, exit_p)
    for b in sc["beats"]:
        if b["clear"] and now >= b["exit_t"]:
            ep = (now - b["exit_t"]) / EXIT
            sprites = [(s, ep) for s, _ in sprites] if ep < 1 else []
        sprites += [(s, 0.0) for s in b["add"] if now >= s.t]
    focus_sprites = [s for s, _ in sprites if s.focus] if sc["focus"] else []
    undim = now > sc["end"] - 1.2
    for s, ep in sprites:
        dim = 0.0
        if focus_sprites and s.focus and not undim:
            later = [o.t for o in focus_sprites if o.t > s.t]
            if later:
                dim = ease_io((now - min(later)) / 0.35)
        elif focus_sprites and s.focus and undim:
            later = [o.t for o in focus_sprites if o.t > s.t]
            if later:
                dim = 1 - ease_io((now - (sc["end"] - 1.2)) / 0.4)
        s.draw(frame, now, dim, ep, pen_img())
    return frame


_chrome = {}


def chrome(frame, label, alpha=1.0):
    if label not in _chrome:
        _chrome[label] = text_img(label, 30, MUTED, True)
    t = _chrome[label]
    if alpha < 1:
        t = t.copy()
        t.putalpha(t.getchannel("A").point(lambda v: int(v * alpha)))
    paste(frame, t, k(44), k(28))


def blank():
    return Image.new("RGBA", (W, H), (255, 255, 255, 255))


def scene_frame(sc, now):
    fr = blank()
    chrome(fr, sc["label"], min(1, max(0, (now - sc["start"]) / 0.4)))
    return draw_scene(sc, now, fr)


def whip(a, b, p):
    """Wisch-Schwenk von Bild a zu Bild b mit Bewegungsunschärfe."""
    e = ease_io(p)
    speed = math.sin(math.pi * p)
    out = blank()
    for img, off in ((a, -e * W), (b, (1 - e) * W)):
        if -W < off < W:
            if speed > 0.15:
                f = max(2, int(14 * speed))
                img = img.resize((W // f, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
            paste(out, img, off, 0)
    return out


def render(scenes, total, outfile, wav):
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-tune", "animation", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
         "-movflags", "+faststart", outfile], stdin=subprocess.PIPE)
    trans_cache = {}
    for fi in range(int(total * FPS)):
        now = fi / FPS
        frame = None
        for i in range(1, len(scenes)):
            a, b = scenes[i - 1], scenes[i]
            if a["end"] <= now < b["start"]:
                if i not in trans_cache:
                    trans_cache[i] = (scene_frame(a, a["end"] - 1e-3), scene_frame(b, b["start"]))
                frame = whip(*trans_cache[i], (now - a["end"]) / TRANS)
                break
        if frame is None:
            sc = scenes[0]
            for s in scenes:
                if now >= s["start"]:
                    sc = s
            frame = scene_frame(sc, now)
            if now < 0.35:
                frame = Image.blend(blank(), frame, ease_io(now / 0.35))
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()


def write_wav(path, audio):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.clip(audio, -32000, 32000).astype(np.int16).tobytes())
