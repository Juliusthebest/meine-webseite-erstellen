"""Animations-Engine im Flat-Design-Stil (ruhige, weiche Animationen, 1440p / 60 fps).

Drehbuch-Koordinaten: 1920x1080. Elemente: Sprites (Bilder), Fahrzeuge mit drehenden Rädern,
Förderband, gezeichnete Linien und Aktionen (bewegen, drehen, ausblenden) zu späteren Sätzen.
"""
import math
import os
import re
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import flat_icons as F
from flat_icons import BG, DARK, FLOOR, GREY, LBLUE, LGREY, MUSTARD, NAVY, ORANGE, STEEL, WHITE

DW, DH = 1920, 1080
W, H = 2560, 1440
K = W / DW
FPS = 60
SR = 22050
SS = 3

FONTS = {"bold": "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
         "xbold": "/usr/share/fonts/truetype/montserrat/Montserrat-ExtraBold.ttf",
         "semi": "/usr/share/fonts/truetype/montserrat/Montserrat-SemiBold.ttf",
         "med": "/usr/share/fonts/truetype/montserrat/Montserrat-Medium.ttf"}
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def k(v):
    return int(round(v * K))


# --------------------------------------------------------------------------- Text
_fonts, _cmaps = {}, {}


def font(px, weight="bold", fb=False):
    key = (px, weight, fb)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FALLBACK if fb else FONTS[weight], px)
    return _fonts[key]


def has_glyph(ch, weight):
    if weight not in _cmaps:
        from fontTools.ttLib import TTFont
        _cmaps[weight] = TTFont(FONTS[weight]).getBestCmap()
    return ch == " " or ord(ch) in _cmaps[weight]


def runs(line, weight):
    out = []
    for ch in line:
        fb = not has_glyph(ch, weight)
        if out and out[-1][1] == fb:
            out[-1][0] += ch
        else:
            out.append([ch, fb])
    return out


_meas = ImageDraw.Draw(Image.new("RGBA", (1, 1)))


def textlen(line, px, weight):
    return sum(_meas.textlength(t, font=font(px, weight, fb)) for t, fb in runs(line, weight))


def wrap(s, px, weight, maxw):
    if maxw is None:
        return s.split("\n")
    out = []
    for para in s.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if textlen(t, px, weight) <= maxw or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def text_img(s, size, color=DARK, weight="bold", maxw=None, align="center", spacing=1.25):
    px = k(size)
    lines = wrap(s, px, weight, k(maxw) if maxw else None)
    lw = [textlen(l, px, weight) for l in lines]
    asc, desc = font(px, weight).getmetrics()
    lh = int(px * spacing)
    w, h = int(max(lw)) + 8, lh * (len(lines) - 1) + asc + desc + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (l, ww) in enumerate(zip(lines, lw)):
        x = {"center": (w - ww) / 2, "left": 4, "right": w - ww - 4}[align]
        for t, fb in runs(l, weight):
            ff = font(px, weight, fb)
            dy = (asc - ff.getmetrics()[0]) if fb else 0
            d.text((x, 4 + i * lh + dy), t, font=ff, fill=color)
            x += d.textlength(t, font=ff)
    return im


# --------------------------------------------------------------------------- Bildbausteine
def paste(base, im, x, y):
    x, y = int(round(x)), int(round(y))
    if x >= base.width or y >= base.height or x + im.width <= 0 or y + im.height <= 0:
        return
    if x < 0 or y < 0 or x + im.width > base.width or y + im.height > base.height:
        im = im.crop((max(0, -x), max(0, -y), min(im.width, base.width - x), min(im.height, base.height - y)))
        x, y = max(0, x), max(0, y)
    base.alpha_composite(im, (x, y))


def card_img(wd, hd, fill=WHITE, radius=22, shadow=True):
    w, h, m = k(wd), k(hd), k(24)
    big = Image.new("RGBA", ((w + 2 * m) * SS, (h + 2 * m) * SS), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle([m * SS, m * SS, (m + w) * SS, (m + h) * SS], k(radius) * SS, fill=fill)
    shape = big.resize((w + 2 * m, h + 2 * m), Image.LANCZOS)
    if not shadow:
        return shape
    sh = Image.new("RGBA", shape.size, (40, 60, 80, 0))
    sh.putalpha(shape.getchannel("A").point(lambda v: int(v * 0.10)))
    sh = sh.filter(ImageFilter.GaussianBlur(k(10)))
    out = Image.new("RGBA", shape.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, k(6)))
    out.alpha_composite(shape)
    return out


def rect_img(wd, hd, color, radius=0):
    w, h = k(wd), k(hd)
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], k(radius) * SS, fill=color)
    return big.resize((w, h), Image.LANCZOS)


def tag_img(label, fill=DARK, color=WHITE, size=26):
    """Preisschild-Form (wie im Beispielvideo)."""
    t = text_img(label, size, color, "bold")
    pad = k(18)
    w, h = t.width + pad * 2 + k(24), t.height + k(14)
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.polygon([(0, h * SS / 2), (k(22) * SS, 0), (w * SS, 0), (w * SS, h * SS), (k(22) * SS, h * SS)], fill=fill)
    d.ellipse([k(14) * SS, (h / 2 - k(4)) * SS, k(22) * SS, (h / 2 + k(4)) * SS], fill=BG)
    im = big.resize((w, h), Image.LANCZOS)
    paste(im, t, k(24) + pad, (h - t.height) / 2)
    return im


def comp(layers):
    out = Image.new("RGBA", layers[0].size, (0, 0, 0, 0))
    for l in layers:
        out.alpha_composite(l)
    return out


# --------------------------------------------------------------------------- Easing
def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def ease_back(x, s=1.3):
    x = min(1.0, max(0.0, x))
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# --------------------------------------------------------------------------- Sprites
ENTER_DUR = {"fadeup": 0.6, "pop": 0.5, "fade": 0.5, "slide_r": 1.7, "slide_l": 1.7, "swing": 0.8,
             "grow": 0.7, "drop": 0.7, "none": 0.01, "zoom": 0.7}


class Sp:
    def __init__(self, img, x, y, enter="fadeup", f=0.0, d=0.0, sfx="tick", fkey=None):
        self.img, self.x0, self.y0 = img, x, y
        self.enter, self.f, self.d = enter, f, d
        self.sfx, self.fkey = sfx, fkey
        self.children = []          # (bild, dx, dy, r) – Räder
        self.actions = []
        self.t = 0.0
        self.exit_t = None
        self.edur = ENTER_DUR[enter]
        self._rc = {}

    def props(self, now):
        p = (now - self.t) / self.edur
        if p < 0:
            return None
        x, y, s, a, ang = self.x0, self.y0, 1.0, 1.0, 0.0
        sx = 1.0
        if p < 1:
            e = self.enter
            if e == "fadeup":
                y += (1 - ease_out(p)) * 26
                s = 0.97 + 0.03 * ease_out(p)
                a = ease_out(p)
            elif e == "pop":
                s = 0.55 + 0.45 * ease_back(p)
                a = min(1, p * 3)
            elif e == "zoom":
                s = 0.85 + 0.15 * ease_out(p)
                a = ease_out(p)
            elif e == "fade":
                a = ease_io(p)
            elif e == "slide_r":
                x += (1 - ease_out(p)) * 1500
            elif e == "slide_l":
                x -= (1 - ease_out(p)) * 1500
            elif e == "swing":
                ang = (1 - ease_back(p, 2.2)) * 28
                y -= (1 - ease_out(p)) * 30
                a = min(1, p * 3)
            elif e == "drop":
                y -= (1 - ease_back(p, 1.6)) * 60
                a = min(1, p * 3)
            elif e == "grow":
                sx = max(0.001, ease_io(p))
        for act in self.actions:
            if now < act["t"]:
                break
            q = ease_io((now - act["t"]) / act["dur"])
            kind = act["kind"]
            if kind == "move":
                x += (act["x"] - x) * q
                y += (act["y"] - y) * q - act.get("arc", 0) * math.sin(math.pi * q)
            elif kind == "alpha":
                a += (act["v"] - a) * q
            elif kind == "angle":
                ang += (act["v"] - ang) * q
            elif kind == "scale":
                s += (act["v"] - s) * q
            elif kind == "pulse":
                s *= 1 + 0.07 * math.sin(math.pi * min(1, (now - act["t"]) / act["dur"]))
        if self.exit_t is not None and now >= self.exit_t:
            e = ease_io((now - self.exit_t) / 0.4)
            if e >= 1:
                return None
            a *= 1 - e
            s *= 1 - 0.04 * e
        return x, y, s, a, ang, sx

    def _xform(self, img, s, a, ang, sx=1.0, key=None):
        if ang:
            ck = (key, round(ang * 4) / 4)
            if ck not in self._rc:
                if len(self._rc) > 400:
                    self._rc.clear()
                self._rc[ck] = img.rotate(ck[1], expand=True, resample=Image.BICUBIC)
            img = self._rc[ck]
        if s != 1 or sx != 1:
            img = img.resize((max(1, int(img.width * s * sx)), max(1, int(img.height * s))), Image.BILINEAR)
        if a < 0.999:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        return img

    def draw(self, frame, now, dim=0.0):
        pr = self.props(now)
        if pr is None:
            return
        x, y, s, a, ang, sx = pr
        a *= 1 - 0.5 * dim
        if a <= 0.01:
            return
        img = self._xform(self.img, s, a, ang, sx, "body")
        if self.enter == "grow":
            paste(frame, img, k(x) - self.img.width / 2, k(y) - img.height / 2)
        else:
            paste(frame, img, k(x) - img.width / 2, k(y) - img.height / 2)
        for i, (wimg, dx, dy, r) in enumerate(self.children):
            spin = -math.degrees((x - self.x0) / r) if r else 0
            wi = self._xform(wimg, s, a, spin, 1.0, ("wheel", i))
            paste(frame, wi, k(x + dx * s) - wi.width / 2, k(y + dy * s) - wi.height / 2)


class Stroke:
    """Saubere Linie, die gezeichnet wird (Pfeile, Haken, Kreuze)."""

    def __init__(self, paths, color=ORANGE, width=8, f=0.0, d=0.0, dur=0.6):
        self.paths = [[(k(x) * SS, k(y) * SS) for x, y in p] for p in paths]
        allp = [q for p in self.paths for q in p]
        pad = k(width) * SS + 6
        self.ox, self.oy = min(q[0] for q in allp) - pad, min(q[1] for q in allp) - pad
        self.w = int(max(q[0] for q in allp) + pad - self.ox)
        self.h = int(max(q[1] for q in allp) + pad - self.oy)
        self.paths = [[(x - self.ox, y - self.oy) for x, y in p] for p in self.paths]
        self.lens = [sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1)) for p in self.paths]
        self.total = sum(self.lens)
        self.color, self.width = color, k(width) * SS
        self.f, self.d, self.dur = f, d, dur
        self.sfx, self.fkey, self.t, self.exit_t, self.actions = None, None, 0.0, None, []
        self._full = None

    def _render(self, p):
        big = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(big)
        rem = self.total * p
        for path, L in zip(self.paths, self.lens):
            if rem <= 0:
                break
            pts, acc = [path[0]], 0
            for i in range(len(path) - 1):
                seg = math.dist(path[i], path[i + 1])
                if acc + seg <= rem:
                    pts.append(path[i + 1])
                    acc += seg
                else:
                    r = (rem - acc) / seg
                    pts.append((path[i][0] + (path[i + 1][0] - path[i][0]) * r, path[i][1] + (path[i + 1][1] - path[i][1]) * r))
                    break
            if len(pts) > 1:
                dr.line(pts, fill=self.color, width=self.width, joint="curve")
                for px, py in (pts[0], pts[-1]):
                    dr.ellipse([px - self.width / 2, py - self.width / 2, px + self.width / 2, py + self.width / 2], fill=self.color)
            rem -= L
        return big.resize((max(1, self.w // SS), max(1, self.h // SS)), Image.LANCZOS)

    def draw(self, frame, now, dim=0.0):
        p = (now - self.t) / self.dur
        if p < 0:
            return
        if p >= 1:
            if self._full is None:
                self._full = self._render(1)
            img = self._full
        else:
            img = self._render(ease_io(p))
        a = 1 - 0.5 * dim
        for act in self.actions:
            if now >= act["t"] and act["kind"] == "alpha":
                a *= 1 + (act["v"] - 1) * ease_io((now - act["t"]) / act["dur"])
        if self.exit_t is not None and now >= self.exit_t:
            a *= 1 - ease_io((now - self.exit_t) / 0.4)
        if a < 0.999:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        paste(frame, img, self.ox / SS, self.oy / SS)


class Conveyor:
    """Förderband: dunkle Linie mit laufenden Rollen."""

    def __init__(self, y, f=0.0, d=0.0, speed=110):
        self.y, self.f, self.d, self.speed = y, f, d, speed
        self.sfx, self.fkey, self.t, self.exit_t, self.actions = None, None, 0.0, None, []
        self.stop_t = 1e9

    def draw(self, frame, now, dim=0.0):
        p = (now - self.t) / 0.8
        if p < 0:
            return
        a = 1.0
        if self.exit_t is not None and now >= self.exit_t:
            a = 1 - ease_io((now - self.exit_t) / 0.4)
        if a <= 0:
            return
        layer = Image.new("RGBA", (W, k(30)), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        wpx = int(W * ease_io(p))
        d.rectangle([0, k(4), wpx, k(16)], fill=DARK)
        run_t = min(now, self.stop_t) - self.t
        off = (run_t * self.speed) % 60
        x = -60 + off
        while x < DW + 60:
            if k(x) < wpx:
                d.ellipse([k(x) - k(4), k(6), k(x) + k(4), k(14)], fill=GREY)
            x += 60
        if a < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        paste(frame, layer, 0, k(self.y) - k(10))


# --------------------------------------------------------------------------- Drehbuch-Helfer
_fk = [0]


def new_fkey():
    _fk[0] += 1
    return _fk[0]


def TXT(s, x, y, size=40, color=DARK, weight="bold", maxw=None, enter="fadeup", f=0.0, d=0.0, align="center", fkey=None, sfx=None):
    return Sp(text_img(s, size, color, weight, maxw, align), x, y, enter, f, d, sfx, fkey)


def TITLE(s, sub=None, y=120, size=60, f=0.0):
    out = [TXT(s, 960, y, size, DARK, "xbold", enter="fade", f=f, sfx=None)]
    if sub:
        out.append(TXT(sub, 960, y + size * 0.95, size * 0.44, STEEL, "semi", enter="fade", f=f, d=0.35))
    return out


def ICON(name, x, y, s, f=0.0, d=0.0, stagger=0.09, enter="pop", fkey=None, **kw):
    lays = F.ICONS[name](s, **kw) if kw else F.ICONS[name](s)
    out = []
    for i, l in enumerate(lays):
        out.append(Sp(l, x, y, enter if i == 0 else "pop", f, d + i * stagger, "tick" if i == 0 else None, fkey))
    return out


def ICON_IMG(name, s):
    return comp(F.ICONS[name](s))


def VEHICLE(kind, x, y, s, enter="slide_r", f=0.0, d=0.0):
    lays, wheels = {"car": F.car, "agv": F.agv, "train": F.train}[kind](s)
    sp = Sp(comp(lays), x, y, enter, f, d, "whoosh")
    sp.children = [(img, dx / K, dy / K, r / K) for img, dx, dy, r in wheels]
    return sp


def CARD(x, y, w, h, icon, title, sub=None, f=0.0, d=0.0, isize=None, tsize=30, ssize=21, fkey="auto"):
    """Weiße Karte: Symbol oben, Titel, Untertitel – bauen sich nacheinander auf."""
    fk = new_fkey() if fkey == "auto" else fkey
    isize = isize or min(w * 0.42, h * 0.36)
    out = [Sp(card_img(w, h), x, y, "fadeup", f, d, "tick", fk)]
    icon_y = y - h / 2 + 30 + isize / 2 + 10
    if icon:
        out += ICON(icon, x, icon_y, isize, f, d + 0.18, fkey=fk)
    ty = icon_y + isize / 2 + 26
    t = text_img(title, tsize, DARK, "bold", maxw=w - 40)
    out.append(Sp(t, x, ty + t.height / K / 2, "fadeup", f, d + 0.32, None, fk))
    if sub:
        s = text_img(sub, ssize, STEEL, "semi", maxw=w - 44, spacing=1.3)
        out.append(Sp(s, x, ty + t.height / K + 10 + s.height / K / 2, "fadeup", f, d + 0.42, None, fk))
    return out


def node_img(icon, label, w=300, h=230):
    im = card_img(w, h)
    m = k(24)
    ic = ICON_IMG(icon, 110)
    paste(im, ic, m + (k(w) - ic.width) / 2, m + k(26))
    t = text_img(label, 30, DARK, "bold")
    paste(im, t, m + (k(w) - t.width) / 2, m + k(26) + ic.height + k(14))
    return im


def NODE(icon, label, x, y, f=0.0, d=0.0, enter="fadeup"):
    return Sp(node_img(icon, label), x, y, enter, f, d, "tick")


def LISTCARD(x, y, w, h, icon, title, rows, f=0.0, d=0.0, step=0.18):
    """Karte mit Überschrift und Zeilen (+ / –), Zeilen erscheinen nacheinander."""
    fk = new_fkey()
    out = [Sp(card_img(w, h), x, y, "fadeup", f, d, "tick", fk)]
    top = y - h / 2 + 40
    out += ICON(icon, x - w / 2 + 70, top + 30, 70, f, d + 0.15, fkey=fk)
    t = text_img(title, 34, DARK, "bold", maxw=w - 160, align="left")
    out.append(Sp(t, x - w / 2 + 120 + t.width / K / 2, top + 30, "fadeup", f, d + 0.25, None, fk))
    for i, (sign, label) in enumerate(rows):
        yy = top + 125 + i * 84
        col = NAVY if sign == "+" else ORANGE
        badge = Image.new("RGBA", (k(44), k(44)), (0, 0, 0, 0))
        bd = ImageDraw.Draw(badge)
        bd.ellipse([0, 0, k(44) - 1, k(44) - 1], fill=col)
        bt = text_img(sign if sign == "+" else "–", 28, WHITE, "bold")
        paste(badge, bt, (badge.width - bt.width) / 2, (badge.height - bt.height) / 2 - k(2))
        out.append(Sp(badge, x - w / 2 + 62, yy, "pop", f, d + 0.4 + i * step, "tick", fk))
        lt = text_img(label, 28, DARK, "semi", maxw=w - 150, align="left")
        out.append(Sp(lt, x - w / 2 + 100 + lt.width / K / 2, yy, "fadeup", f, d + 0.45 + i * step, None, fk))
    return out


def BANNER(text, x, y, w=1500, h=120, f=0.0, d=0.0, accent=MUSTARD, size=36):
    out = [Sp(card_img(w, h), x, y, "fadeup", f, d, "tick")]
    out.append(Sp(rect_img(14, h - 30, accent, 7), x - w / 2 + 34, y, "grow", f, d + 0.2, None))
    out.append(TXT(text, x + 10, y, size, DARK, "bold", maxw=w - 120, f=f, d=d + 0.3))
    return out


def FLOOR_BAND(y=860, f=0.0, d=0.0):
    return Sp(rect_img(DW, DH - y + 4, FLOOR), 960, (y + DH) / 2 + 2, "fade", f, d, None)


def TAG(label, x, y, fill=DARK, color=WHITE, rot=-6, f=0.0, d=0.0, size=26):
    img = tag_img(label, fill, color, size).rotate(rot, expand=True, resample=Image.BICUBIC)
    return Sp(img, x, y, "swing", f, d, "tick")


def ARROW(x1, y1, x2, y2, color=GREY, width=7, f=0.0, d=0.0, dur=0.6, bend=0):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    L = math.hypot(x2 - x1, y2 - y1) or 1
    cx, cy = mx - (y2 - y1) / L * bend, my + (x2 - x1) / L * bend
    pts = [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2)
           for t in [i / 24 for i in range(25)]]
    ang = math.atan2(y2 - pts[-3][1], x2 - pts[-3][0])
    hl = 22
    return Stroke([pts, [(x2 - hl * math.cos(ang - 0.55), y2 - hl * math.sin(ang - 0.55)), (x2, y2),
                         (x2 - hl * math.cos(ang + 0.55), y2 - hl * math.sin(ang + 0.55))]], color, width, f, d, dur)


def CHECK(x, y, size=60, color=NAVY, width=10, f=0.0, d=0.0):
    return Stroke([[(x - size * 0.45, y), (x - size * 0.1, y + size * 0.35), (x + size * 0.5, y - size * 0.45)]], color, width, f, d, 0.45)


def CROSS(x, y, size=120, color=ORANGE, width=12, f=0.0, d=0.0):
    s = size / 2
    return Stroke([[(x - s, y - s), (x + s, y + s)], [(x + s, y - s), (x - s, y + s)]], color, width, f, d, 0.5)


# Aktionen (wirken zu einem späteren Satz auf ein bestehendes Element)
def MOVE(sp, x, y, f=0.0, d=0.0, dur=0.9, arc=0):
    return dict(target=sp, kind="move", x=x, y=y, f=f, d=d, dur=dur, arc=arc)


def ALPHA(sp, v, f=0.0, d=0.0, dur=0.5):
    return dict(target=sp, kind="alpha", v=v, f=f, d=d, dur=dur)


def ANGLE(sp, v, f=0.0, d=0.0, dur=0.8):
    return dict(target=sp, kind="angle", v=v, f=f, d=d, dur=dur)


def PULSE(sp, f=0.0, d=0.0, dur=0.6):
    return dict(target=sp, kind="pulse", f=f, d=d, dur=dur)


def STOP(conv, f=0.0, d=0.0):
    return dict(target=conv, kind="stop", f=f, d=d, dur=0.01)


def B(sub, add=(), clear=False, pause=0.45):
    flat = []
    for a in add:
        if isinstance(a, (list, tuple)):
            flat += list(a)
        else:
            flat.append(a)
    return dict(sub=sub, add=flat, clear=clear, pause=pause)


def SC(beats, focus=False):
    return dict(beats=beats, focus=focus)


# --------------------------------------------------------------------------- Ton
SAY = [("Lean Production", "Lien Prodacktschen"), ("Lean", "Lien"), ("KVP", "Ka Fau Pe")]


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
    if kind == "tick":
        n = int(SR * 0.06)
        t = np.arange(n) / SR
        return np.sin(2 * np.pi * r.uniform(700, 900) * t) * np.exp(-t * 70) * 1100
    if kind == "whoosh":
        n = int(SR * 1.2)
        noise = np.convolve(r.normal(size=n), np.ones(30) / 30, mode="same")
        env = np.exp(-((np.arange(n) / n - 0.3) ** 2) / 0.03)
        return noise * env * 3800
    return np.zeros(1)


# --------------------------------------------------------------------------- Zeitplan & Rendering
LEAD, XFADE, EXIT = 0.35, 0.45, 0.45


def timeline(scenes, tmp, voices=None):
    t = 0.4
    voice, fx, subs = [], [], []
    seed = 3
    for si, sc in enumerate(scenes):
        sc["start"] = t
        sc["items"] = []
        t += LEAD
        for bi, b in enumerate(sc["beats"]):
            if b["clear"]:
                for it in sc["items"]:
                    if it.exit_t is None:
                        it.exit_t = t
                t += EXIT
            a = voices[(si, bi)] if voices else tts(b["sub"], os.path.join(tmp, f"{si}_{bi}.wav"))
            dur = len(a) / SR
            b["t0"], b["dur"] = t, dur
            voice.append((t, a))
            subs.append((t, t + dur, b["sub"]))
            for it in b["add"]:
                if isinstance(it, dict):
                    it["t"] = t + it["d"] + it["f"] * dur
                    if it["kind"] == "stop":
                        it["target"].stop_t = it["t"]
                    else:
                        it["target"].actions.append(it)
                        it["target"].actions.sort(key=lambda a: a["t"])
                else:
                    it.t = t + it.d + it.f * dur
                    sc["items"].append(it)
                    if it.sfx:
                        seed += 1
                        fx.append((it.t, sfx(it.sfx, seed)))
            t += dur + b["pause"]
        t += 0.7
        sc["end"] = t
        t += XFADE
    total = t + 0.3
    n = int(total * SR) + SR
    audio, vo = np.zeros(n), np.zeros(n)
    for st, a in voice:
        i = int(st * SR)
        vo[i:i + len(a)] += a[: n - i]
    for st, a in fx:
        i = int(st * SR)
        audio[i:i + len(a)] += a[: n - i]
    return total, audio + vo, audio, subs


def draw_scene(sc, now):
    frame = Image.new("RGBA", (W, H), BG + (255,))
    items = [it for it in sc["items"] if now >= it.t]
    fkeys = {}
    if sc["focus"]:
        for it in sc["items"]:
            if it.fkey is not None:
                fkeys[it.fkey] = min(fkeys.get(it.fkey, 1e9), it.t)
    undim_t = sc["end"] - 1.4
    for it in items:
        dim = 0.0
        if it.fkey is not None and it.fkey in fkeys:
            my = fkeys[it.fkey]
            later = [v for v in fkeys.values() if my < v <= now]
            if later:
                dim = ease_io((now - min(later)) / 0.4)
                if now > undim_t:
                    dim *= 1 - ease_io((now - undim_t) / 0.5)
        it.draw(frame, now, dim)
    return frame


def render(scenes, total, outfile, wav):
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "animation",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", outfile],
        stdin=subprocess.PIPE)
    cache = {}
    bgimg = Image.new("RGBA", (W, H), BG + (255,))
    for fi in range(int(total * FPS)):
        now = fi / FPS
        frame = None
        for i in range(1, len(scenes)):
            a, b = scenes[i - 1], scenes[i]
            if a["end"] <= now < b["start"]:
                if i not in cache:
                    cache = {i: (draw_scene(a, a["end"] - 1e-3), draw_scene(b, b["start"]))}
                frame = Image.blend(cache[i][0], cache[i][1], ease_io((now - a["end"]) / XFADE))
                break
        if frame is None:
            sc = scenes[0]
            for s in scenes:
                if now >= s["start"]:
                    sc = s
            frame = draw_scene(sc, now)
            if now < 0.3:
                frame = Image.blend(bgimg, frame, ease_io(now / 0.3))
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()


def write_wav(path, audio):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.clip(audio, -32000, 32000).astype(np.int16).tobytes())
