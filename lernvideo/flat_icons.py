"""Flache Vektor-Illustrationen (im Stil moderner Erklärvideos), gezeichnet mit Pillow.

Jede Funktion liefert eine Liste von Ebenen (gleich große RGBA-Bilder). Die Ebenen werden im Video
nacheinander eingeblendet, so „baut“ sich das Symbol auf. Fahrzeuge liefern zusätzlich Räder.
Koordinaten innerhalb eines Symbols: Design-Pixel (1920x1080-Raster), skaliert mit K.
"""
import math

from PIL import Image, ImageDraw, ImageFont

DW, W = 1920, 2560
K = W / DW
SS = 3

BG = (235, 239, 242)
FLOOR = (211, 218, 224)
DARK = (31, 40, 46)
NAVY = (59, 103, 144)
ORANGE = (211, 91, 58)
MUSTARD = (240, 168, 48)
LBLUE = (169, 194, 214)
GREY = (150, 160, 168)
LGREY = (222, 228, 233)
WHITE = (255, 255, 255)
SKIN = (242, 196, 160)
STEEL = (74, 107, 135)
JPRED = (200, 40, 55)

FONT_B = "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf"


class Pen:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.s = K * SS
        self.im = Image.new("RGBA", (math.ceil(w * self.s), math.ceil(h * self.s)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, x, y):
        return (x * self.s, y * self.s)

    def rect(self, x0, y0, x1, y1, fill, r=0, outline=None, width=0):
        self.d.rounded_rectangle([*self.P(x0, y0), *self.P(x1, y1)], radius=r * self.s, fill=fill,
                                 outline=outline, width=int(width * self.s))

    def circ(self, cx, cy, r, fill=None, outline=None, width=0):
        self.d.ellipse([*self.P(cx - r, cy - r), *self.P(cx + r, cy + r)], fill=fill, outline=outline,
                       width=int(width * self.s))

    def ell(self, x0, y0, x1, y1, fill):
        self.d.ellipse([*self.P(x0, y0), *self.P(x1, y1)], fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([self.P(x, y) for x, y in pts], fill=fill)

    def line(self, pts, color, width):
        pp = [self.P(x, y) for x, y in pts]
        wpx = width * self.s
        self.d.line(pp, fill=color, width=int(wpx), joint="curve")
        for x, y in (pp[0], pp[-1]):
            self.d.ellipse([x - wpx / 2, y - wpx / 2, x + wpx / 2, y + wpx / 2], fill=color)

    def arc(self, cx, cy, r, a0, a1, color, width):
        self.d.arc([*self.P(cx - r, cy - r), *self.P(cx + r, cy + r)], a0, a1, fill=color, width=int(width * self.s))

    def pie(self, x0, y0, x1, y1, a0, a1, fill):
        self.d.pieslice([*self.P(x0, y0), *self.P(x1, y1)], a0, a1, fill=fill)

    def chord(self, x0, y0, x1, y1, a0, a1, fill):
        self.d.chord([*self.P(x0, y0), *self.P(x1, y1)], a0, a1, fill=fill)

    def text(self, cx, cy, s, size, fill):
        f = ImageFont.truetype(FONT_B, int(size * self.s))
        self.d.text(self.P(cx, cy), s, font=f, fill=fill, anchor="mm")

    def done(self):
        return self.im.resize((math.ceil(self.w * K), math.ceil(self.h * K)), Image.LANCZOS)


def layers(w, h, n):
    return [Pen(w, h) for _ in range(n)]


def wheel(r, hub=LGREY):
    p = Pen(2 * r, 2 * r)
    p.circ(r, r, r, DARK)
    p.circ(r, r, r * 0.62, hub)
    for a in range(0, 360, 60):
        ra = math.radians(a)
        p.line([(r, r), (r + r * 0.55 * math.cos(ra), r + r * 0.55 * math.sin(ra))], GREY, max(1.2, r * 0.08))
    p.circ(r, r, r * 0.18, DARK)
    return p.done()


# =========================================================================== Fahrzeuge & Figuren
def car(s):
    """Seitenansicht Auto. Rückgabe (Ebenen, Räder[(bild, dx, dy, r)]) – dx/dy relativ zur Bildmitte."""
    u = s / 100
    w, h = 180 * u, 78 * u
    a, b = layers(w, h, 2)
    a.poly([(42 * u, 34 * u), (64 * u, 10 * u), (122 * u, 10 * u), (148 * u, 34 * u)], ORANGE)
    a.rect(4 * u, 32 * u, 176 * u, 62 * u, ORANGE, r=10 * u)
    a.rect(4 * u, 50 * u, 176 * u, 62 * u, (186, 76, 48), r=6 * u)
    b.poly([(54 * u, 33 * u), (68 * u, 15 * u), (91 * u, 15 * u), (91 * u, 33 * u)], LBLUE)
    b.poly([(97 * u, 15 * u), (118 * u, 15 * u), (136 * u, 33 * u), (97 * u, 33 * u)], LBLUE)
    b.rect(164 * u, 38 * u, 176 * u, 45 * u, MUSTARD, r=2 * u)
    b.rect(4 * u, 38 * u, 12 * u, 45 * u, (240, 120, 90), r=2 * u)
    r = 15 * u
    wh = wheel(r)
    return [a.done(), b.done()], [(wh, 45 * u - w / 2, 62 * u - h / 2, r), (wh, 135 * u - w / 2, 62 * u - h / 2, r)]


def agv(s):
    """Fahrerloses Transportsystem."""
    u = s / 100
    w, h = 150 * u, 74 * u
    a, b = layers(w, h, 2)
    a.rect(2 * u, 36 * u, 148 * u, 60 * u, LBLUE, r=6 * u)
    a.rect(2 * u, 52 * u, 148 * u, 60 * u, (140, 168, 190), r=4 * u)
    a.rect(134 * u, 26 * u, 146 * u, 36 * u, DARK, r=2 * u)
    a.circ(140 * u, 31 * u, 3 * u, ORANGE)
    b.rect(36 * u, 4 * u, 104 * u, 36 * u, MUSTARD, r=3 * u)
    b.rect(36 * u, 17 * u, 104 * u, 22 * u, (214, 140, 30))
    r = 10 * u
    wh = wheel(r)
    return [a.done(), b.done()], [(wh, 28 * u - w / 2, 62 * u - h / 2, r), (wh, 122 * u - w / 2, 62 * u - h / 2, r)]


def train(s):
    """Kleiner Werkszug mit Lok, Fahrer und Wagen."""
    u = s / 100
    w, h = 170 * u, 92 * u
    a, b, c = layers(w, h, 3)
    # Wagen
    a.rect(2 * u, 48 * u, 66 * u, 76 * u, MUSTARD, r=4 * u)
    a.rect(2 * u, 66 * u, 66 * u, 76 * u, (214, 140, 30), r=3 * u)
    a.line([(66 * u, 68 * u), (80 * u, 68 * u)], DARK, 3 * u)
    # Lok
    a.rect(78 * u, 36 * u, 166 * u, 76 * u, NAVY, r=6 * u)
    a.rect(78 * u, 64 * u, 166 * u, 76 * u, (44, 80, 115), r=4 * u)
    a.rect(120 * u, 8 * u, 164 * u, 40 * u, NAVY, r=5 * u)
    a.rect(127 * u, 14 * u, 157 * u, 32 * u, LBLUE, r=3 * u)
    a.rect(90 * u, 24 * u, 100 * u, 36 * u, DARK, r=2 * u)
    # Fahrer
    b.circ(142 * u, 24 * u, 6 * u, SKIN)
    b.chord(135 * u, 13 * u, 149 * u, 27 * u, 180, 360, MUSTARD)
    # Kisten
    c.rect(8 * u, 26 * u, 32 * u, 48 * u, ORANGE, r=2 * u)
    c.rect(36 * u, 30 * u, 60 * u, 48 * u, (186, 76, 48), r=2 * u)
    c.rect(14 * u, 14 * u, 30 * u, 26 * u, MUSTARD, r=2 * u)
    r = 9 * u
    wh = wheel(r)
    whs = [(wh, x * u - w / 2, 78 * u - h / 2, r) for x in (18, 50, 96, 148)]
    return [a.done(), b.done(), c.done()], whs


def worker(s):
    u = s / 100
    a, b, c = layers(80 * u, 100 * u, 3)
    a.rect(6 * u, 56 * u, 74 * u, 100 * u, NAVY, r=18 * u)
    a.rect(22 * u, 58 * u, 30 * u, 100 * u, MUSTARD)
    a.rect(50 * u, 58 * u, 58 * u, 100 * u, MUSTARD)
    b.circ(40 * u, 38 * u, 16 * u, SKIN)
    c.chord(22 * u, 16 * u, 58 * u, 44 * u, 180, 360, MUSTARD)
    c.rect(18 * u, 28 * u, 62 * u, 33 * u, (214, 140, 30), r=2 * u)
    return [a.done(), b.done(), c.done()]


def robot(s):
    u = s / 100
    a, b, c = layers(90 * u, 100 * u, 3)
    a.rect(20 * u, 58 * u, 70 * u, 100 * u, (128, 140, 150), r=8 * u)
    a.rect(33 * u, 68 * u, 57 * u, 84 * u, LBLUE, r=3 * u)
    a.rect(6 * u, 64 * u, 18 * u, 92 * u, GREY, r=5 * u)
    a.rect(72 * u, 64 * u, 84 * u, 92 * u, GREY, r=5 * u)
    b.rect(14 * u, 14 * u, 76 * u, 54 * u, GREY, r=10 * u)
    b.line([(45 * u, 14 * u), (45 * u, 5 * u)], DARK, 3 * u)
    b.circ(45 * u, 4 * u, 4 * u, ORANGE)
    c.circ(32 * u, 34 * u, 7 * u, WHITE)
    c.circ(58 * u, 34 * u, 7 * u, WHITE)
    c.circ(32 * u, 34 * u, 3.5 * u, DARK)
    c.circ(58 * u, 34 * u, 3.5 * u, DARK)
    c.rect(34 * u, 45 * u, 56 * u, 48 * u, DARK, r=1 * u)
    return [a.done(), b.done(), c.done()]


def customer(s, shirt=ORANGE):
    u = s / 100
    a, b = layers(80 * u, 100 * u, 2)
    a.rect(6 * u, 58 * u, 74 * u, 100 * u, shirt, r=20 * u)
    b.circ(40 * u, 38 * u, 17 * u, SKIN)
    b.chord(23 * u, 18 * u, 57 * u, 46 * u, 180, 360, DARK)
    return [a.done(), b.done()]


def people(s):
    u = s / 100
    a, b, c = layers(120 * u, 100 * u, 3)
    for lay, cx, col, sc in ((a, 30, MUSTARD, 0.8), (b, 90, ORANGE, 0.8), (c, 60, NAVY, 1.0)):
        r = 15 * u * sc
        top = 100 * u - 44 * u * sc
        lay.rect(cx * u - 30 * u * sc, top, cx * u + 30 * u * sc, 100 * u, col, r=16 * u * sc)
        lay.circ(cx * u, top - 16 * u * sc, r, SKIN)
    return [a.done(), b.done(), c.done()]


def dowel(s):
    """Dübel mit Schraube."""
    u = s / 100
    a, b = layers(170 * u, 60 * u, 2)
    a.rect(52 * u, 14 * u, 168 * u, 46 * u, LBLUE, r=12 * u)
    a.poly([(150 * u, 14 * u), (168 * u, 22 * u), (168 * u, 38 * u), (150 * u, 46 * u)], (140, 168, 190))
    for x in range(64, 150, 14):
        a.rect(x * u, 14 * u, (x + 5) * u, 46 * u, (196, 214, 228))
    b.rect(2 * u, 25 * u, 110 * u, 35 * u, GREY, r=3 * u)
    for x in range(14, 106, 8):
        b.line([(x * u, 25 * u), ((x + 4) * u, 35 * u)], (120, 130, 138), 1.4 * u)
    b.rect(0, 10 * u, 12 * u, 50 * u, (110, 120, 128), r=3 * u)
    return [a.done(), b.done()]


def factory(s):
    u = s / 100
    a, b, c = layers(120 * u, 100 * u, 3)
    a.rect(8 * u, 46 * u, 112 * u, 98 * u, NAVY)
    for i in range(3):
        x = 8 + 30 * i
        a.poly([(x * u, 46 * u), (x * u, 24 * u), ((x + 30) * u, 46 * u)], NAVY)
    a.rect(84 * u, 14 * u, 98 * u, 46 * u, GREY)
    b.circ(91 * u, 9 * u, 5 * u, LGREY)
    b.circ(101 * u, 3 * u, 4 * u, LGREY)
    for x in (18, 40, 62):
        c.rect(x * u, 58 * u, (x + 14) * u, 72 * u, MUSTARD, r=1.5 * u)
    c.rect(84 * u, 70 * u, 102 * u, 98 * u, LBLUE)
    return [a.done(), b.done(), c.done()]


def flag_jp(s):
    u = s / 100
    a, b = layers(100 * u, 68 * u, 2)
    a.rect(2 * u, 2 * u, 98 * u, 66 * u, WHITE, r=4 * u, outline=LGREY, width=2 * u)
    b.circ(50 * u, 34 * u, 18 * u, JPRED)
    return [a.done(), b.done()]


# =========================================================================== Karten-Symbole (quadratisch)
def sq(s, n):
    return layers(s, s, n)


def boxes(s):
    u = s / 100
    L = sq(s, 3)
    for lay, row in zip(L, ((0, 3), (1, 2), (2, 1))):
        r, n = row
        y = 74 - r * 24
        x0 = 50 - n * 12
        for i in range(n):
            lay.rect((x0 + i * 24 + 1) * u, y * u, (x0 + i * 24 + 23) * u, (y + 22) * u, MUSTARD, r=2 * u)
    return [l.done() for l in L]


def pull(s):
    """Hol-Prinzip: Kunde zieht die Ware."""
    u = s / 100
    a, b, c = sq(s, 3)
    a.rect(4 * u, 62 * u, 36 * u, 96 * u, NAVY, r=12 * u)
    a.circ(20 * u, 50 * u, 10 * u, SKIN)
    b.rect(62 * u, 54 * u, 96 * u, 88 * u, MUSTARD, r=3 * u)
    b.rect(62 * u, 66 * u, 96 * u, 71 * u, (214, 140, 30))
    c.line([(58 * u, 40 * u), (32 * u, 40 * u)], ORANGE, 5 * u)
    c.poly([(26 * u, 40 * u), (38 * u, 31 * u), (38 * u, 49 * u)], ORANGE)
    c.line([(58 * u, 40 * u), (70 * u, 52 * u)], ORANGE, 5 * u)
    return [a.done(), b.done(), c.done()]


def stairs(s):
    u = s / 100
    a, b = sq(s, 2)
    a.poly([(6 * u, 94 * u), (6 * u, 76 * u), (28 * u, 76 * u), (28 * u, 58 * u), (50 * u, 58 * u), (50 * u, 40 * u),
            (72 * u, 40 * u), (72 * u, 22 * u), (94 * u, 22 * u), (94 * u, 94 * u)], NAVY)
    b.line([(10 * u, 62 * u), (70 * u, 10 * u)], ORANGE, 5 * u)
    b.poly([(78 * u, 3 * u), (60 * u, 8 * u), (72 * u, 20 * u)], ORANGE)
    return [a.done(), b.done()]


def checklist(s):
    u = s / 100
    a, b, c = sq(s, 3)
    a.rect(16 * u, 8 * u, 84 * u, 96 * u, NAVY, r=6 * u)
    a.rect(22 * u, 16 * u, 78 * u, 90 * u, WHITE, r=3 * u)
    a.rect(36 * u, 3 * u, 64 * u, 14 * u, DARK, r=3 * u)
    for i, lay in enumerate((b, c, b)):
        y = 32 + i * 20
        lay.line([(28 * u, y * u), (33 * u, (y + 5) * u), (41 * u, (y - 5) * u)], ORANGE, 3.6 * u)
        lay.rect(48 * u, (y - 2) * u, 72 * u, (y + 3) * u, LGREY, r=2 * u)
    return [a.done(), b.done(), c.done()]


def clipboard(s):
    u = s / 100
    a, b = sq(s, 2)
    a.rect(16 * u, 8 * u, 84 * u, 96 * u, MUSTARD, r=6 * u)
    a.rect(22 * u, 16 * u, 78 * u, 90 * u, WHITE, r=3 * u)
    a.rect(36 * u, 3 * u, 64 * u, 14 * u, DARK, r=3 * u)
    for i in range(4):
        y = 32 + i * 14
        b.rect(30 * u, y * u, (70 - (i % 2) * 14) * u, (y + 5) * u, LBLUE, r=2 * u)
    return [a.done(), b.done()]


def bin_(s):
    u = s / 100
    a, b = sq(s, 2)
    a.poly([(22 * u, 28 * u), (78 * u, 28 * u), (72 * u, 96 * u), (28 * u, 96 * u)], NAVY)
    for x in (38, 50, 62):
        a.rect((x - 2) * u, 38 * u, (x + 2) * u, 86 * u, LBLUE, r=2 * u)
    b.rect(14 * u, 16 * u, 86 * u, 26 * u, DARK, r=3 * u)
    b.rect(40 * u, 8 * u, 60 * u, 18 * u, DARK, r=3 * u)
    return [a.done(), b.done()]


def magnifier(s):
    u = s / 100
    a, b = sq(s, 2)
    a.line([(62 * u, 62 * u), (90 * u, 90 * u)], DARK, 12 * u)
    b.circ(42 * u, 42 * u, 32 * u, DARK)
    b.circ(42 * u, 42 * u, 24 * u, LBLUE)
    b.chord(22 * u, 22 * u, 62 * u, 62 * u, 200, 250, WHITE)
    return [a.done(), b.done()]


def chart(s):
    u = s / 100
    a, b, c, d = sq(s, 4)
    a.rect(6 * u, 10 * u, 94 * u, 80 * u, WHITE, r=4 * u, outline=DARK, width=4 * u)
    a.line([(30 * u, 80 * u), (22 * u, 96 * u)], DARK, 4 * u)
    a.line([(70 * u, 80 * u), (78 * u, 96 * u)], DARK, 4 * u)
    b.rect(20 * u, 50 * u, 34 * u, 70 * u, NAVY, r=2 * u)
    c.rect(43 * u, 38 * u, 57 * u, 70 * u, MUSTARD, r=2 * u)
    d.rect(66 * u, 24 * u, 80 * u, 70 * u, ORANGE, r=2 * u)
    return [a.done(), b.done(), c.done(), d.done()]


def target(s):
    u = s / 100
    a, b = sq(s, 2)
    for r, col in ((44, ORANGE), (34, WHITE), (24, ORANGE), (14, WHITE), (6, ORANGE)):
        a.circ(46 * u, 54 * u, r * u, col)
    b.line([(46 * u, 54 * u), (88 * u, 12 * u)], DARK, 4 * u)
    b.poly([(88 * u, 12 * u), (96 * u, 4 * u), (98 * u, 14 * u), (90 * u, 22 * u), (80 * u, 20 * u), (80 * u, 10 * u)], MUSTARD)
    return [a.done(), b.done()]


def loop(s):
    u = s / 100
    a, b = sq(s, 2)
    a.arc(50 * u, 52 * u, 36 * u, 40, 330, NAVY, 11 * u)
    ang = math.radians(330)
    x, y = 50 * u + 36 * u * math.cos(ang), 52 * u + 36 * u * math.sin(ang)
    b.poly([(x - 2 * u, y - 16 * u), (x + 16 * u, y + 2 * u), (x - 8 * u, y + 8 * u)], ORANGE)
    b.circ(50 * u, 52 * u, 10 * u, MUSTARD)
    return [a.done(), b.done()]


def calm(s):
    u = s / 100
    a, b = sq(s, 2)
    a.circ(50 * u, 50 * u, 44 * u, MUSTARD)
    b.arc(36 * u, 42 * u, 8 * u, 200, 340, DARK, 4 * u)
    b.arc(64 * u, 42 * u, 8 * u, 200, 340, DARK, 4 * u)
    b.arc(50 * u, 58 * u, 16 * u, 30, 150, DARK, 4.5 * u)
    return [a.done(), b.done()]


def smiley(s):
    u = s / 100
    a, b = sq(s, 2)
    a.circ(50 * u, 50 * u, 44 * u, MUSTARD)
    b.circ(36 * u, 40 * u, 5 * u, DARK)
    b.circ(64 * u, 40 * u, 5 * u, DARK)
    b.arc(50 * u, 50 * u, 24 * u, 25, 155, DARK, 5 * u)
    return [a.done(), b.done()]


def coin(s):
    u = s / 100
    a, b = sq(s, 2)
    a.circ(56 * u, 60 * u, 36 * u, (214, 140, 30))
    a.circ(44 * u, 46 * u, 38 * u, MUSTARD)
    a.circ(44 * u, 46 * u, 29 * u, (248, 196, 90))
    b.text(44 * u, 47 * u, "€", 38 * u, DARK)
    return [a.done(), b.done()]


def bank(s):
    u = s / 100
    a, b = sq(s, 2)
    a.poly([(8 * u, 34 * u), (50 * u, 8 * u), (92 * u, 34 * u)], NAVY)
    a.rect(6 * u, 84 * u, 94 * u, 96 * u, NAVY, r=2 * u)
    for x in (18, 38, 58, 78):
        b.rect(x * u, 40 * u, (x + 8) * u, 80 * u, LBLUE, r=1 * u)
    b.circ(50 * u, 25 * u, 5 * u, MUSTARD)
    return [a.done(), b.done()]


def arrows4(s):
    u = s / 100
    a, b = sq(s, 2)
    for lay, angs in ((a, (0, 180)), (b, (90, 270))):
        for ang in angs:
            r = math.radians(ang)
            ex, ey = 50 * u + 38 * u * math.cos(r), 50 * u + 38 * u * math.sin(r)
            lay.line([(50 * u, 50 * u), (ex, ey)], NAVY, 7 * u)
            px, py = -math.sin(r), math.cos(r)
            lay.poly([(ex + 10 * u * math.cos(r), ey + 10 * u * math.sin(r)), (ex + 9 * u * px, ey + 9 * u * py),
                      (ex - 9 * u * px, ey - 9 * u * py)], ORANGE)
    a.circ(50 * u, 50 * u, 9 * u, MUSTARD)
    return [a.done(), b.done()]


def warn(s):
    u = s / 100
    a, b = sq(s, 2)
    a.poly([(50 * u, 6 * u), (96 * u, 90 * u), (4 * u, 90 * u)], MUSTARD)
    b.rect(46 * u, 34 * u, 54 * u, 66 * u, DARK, r=3 * u)
    b.circ(50 * u, 77 * u, 5 * u, DARK)
    return [a.done(), b.done()]


def trophy(s):
    u = s / 100
    a, b = sq(s, 2)
    a.arc(20 * u, 34 * u, 14 * u, 90, 270, MUSTARD, 6 * u)
    a.arc(80 * u, 34 * u, 14 * u, 270, 90, MUSTARD, 6 * u)
    a.chord(18 * u, -6 * u, 82 * u, 62 * u, 0, 180, MUSTARD)
    a.rect(18 * u, 10 * u, 82 * u, 28 * u, MUSTARD)
    a.rect(44 * u, 60 * u, 56 * u, 78 * u, (214, 140, 30))
    b.rect(28 * u, 78 * u, 72 * u, 94 * u, NAVY, r=3 * u)
    b.circ(50 * u, 32 * u, 8 * u, WHITE)
    return [a.done(), b.done()]


def arrow_up(s, col=NAVY):
    u = s / 100
    (a,) = sq(s, 1)
    a.rect(38 * u, 40 * u, 62 * u, 94 * u, col, r=3 * u)
    a.poly([(50 * u, 4 * u), (90 * u, 48 * u), (10 * u, 48 * u)], col)
    return [a.done()]


def arrow_down(s, col=ORANGE):
    return [im.transpose(Image.FLIP_TOP_BOTTOM) for im in arrow_up(s, col)]


def document(s):
    u = s / 100
    a, b = sq(s, 2)
    a.poly([(16 * u, 4 * u), (66 * u, 4 * u), (84 * u, 22 * u), (84 * u, 96 * u), (16 * u, 96 * u)], LBLUE)
    a.poly([(66 * u, 4 * u), (84 * u, 22 * u), (66 * u, 22 * u)], NAVY)
    for i in range(3):
        y = 36 + i * 13
        a.rect(26 * u, y * u, (70 - i * 8) * u, (y + 5) * u, WHITE, r=2 * u)
    b.circ(70 * u, 80 * u, 16 * u, ORANGE)
    b.line([(62 * u, 80 * u), (68 * u, 86 * u), (78 * u, 74 * u)], WHITE, 4 * u)
    return [a.done(), b.done()]


def toolboard(s):
    u = s / 100
    a, b, c = sq(s, 3)
    a.rect(6 * u, 6 * u, 94 * u, 94 * u, LGREY, r=6 * u, outline=NAVY, width=3 * u)
    b.rect(18 * u, 18 * u, 30 * u, 82 * u, MUSTARD, r=3 * u)
    for y in range(26, 80, 10):
        b.line([(18 * u, y * u), (24 * u, y * u)], DARK, 1.5 * u)
    b.line([(46 * u, 24 * u), (46 * u, 82 * u)], DARK, 5 * u)
    b.rect(38 * u, 18 * u, 54 * u, 30 * u, GREY, r=2 * u)
    c.line([(72 * u, 40 * u), (72 * u, 82 * u)], ORANGE, 6 * u)
    c.rect(66 * u, 18 * u, 78 * u, 40 * u, DARK, r=3 * u)
    return [a.done(), b.done(), c.done()]


def orgchart(s):
    u = s / 100
    a, b = sq(s, 2)
    a.line([(18 * u, 40 * u), (82 * u, 40 * u)], GREY, 4 * u)
    for x in (18, 50, 82):
        a.line([(x * u, 40 * u), (x * u, 56 * u)], GREY, 4 * u)
    for x, col in ((18, MUSTARD), (50, NAVY), (82, ORANGE)):
        b.rect((x - 14) * u, 56 * u, (x + 14) * u, 84 * u, col, r=4 * u)
        b.circ(x * u, 64 * u, 5 * u, SKIN)
    a.rect(30 * u, 14 * u, 70 * u, 30 * u, LBLUE, r=4 * u)
    return [a.done(), b.done()]


def balance_base(s):
    u = s / 100
    (a,) = layers(120 * u, 120 * u, 1)
    a.rect(56 * u, 20 * u, 64 * u, 104 * u, DARK, r=3 * u)
    a.poly([(60 * u, 96 * u), (88 * u, 116 * u), (32 * u, 116 * u)], DARK)
    a.circ(60 * u, 20 * u, 7 * u, MUSTARD)
    return a.done()


def balance_beam(s):
    """Waagebalken mit Schalen; Drehpunkt in der Bildmitte."""
    u = s / 100
    (a,) = layers(120 * u, 120 * u, 1)
    a.rect(6 * u, 57 * u, 114 * u, 63 * u, DARK, r=3 * u)
    for cx, col in ((14, NAVY), (106, ORANGE)):
        a.line([(cx * u, 60 * u), ((cx - 10) * u, 92 * u)], GREY, 2 * u)
        a.line([(cx * u, 60 * u), ((cx + 10) * u, 92 * u)], GREY, 2 * u)
        a.chord((cx - 16) * u, 80 * u, (cx + 16) * u, 104 * u, 0, 180, col)
    return a.done()


def balance_icon(s):
    base = balance_base(s)
    beam = balance_beam(s)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.alpha_composite(base)
    out.alpha_composite(beam, (0, -int(s * K * 0.4)))
    return [out]


def bolt(s):
    u = s / 100
    a, b = sq(s, 2)
    a.circ(50 * u, 50 * u, 46 * u, LGREY)
    b.poly([(58 * u, 6 * u), (24 * u, 56 * u), (48 * u, 56 * u), (40 * u, 94 * u), (78 * u, 40 * u), (54 * u, 40 * u)], MUSTARD)
    return [a.done(), b.done()]


def magnet(s):
    u = s / 100
    a, b = sq(s, 2)
    a.arc(50 * u, 46 * u, 30 * u, 0, 180, ORANGE, 18 * u)
    a.rect(11 * u, 16 * u, 29 * u, 47 * u, ORANGE)
    a.rect(71 * u, 16 * u, 89 * u, 47 * u, ORANGE)
    b.rect(11 * u, 4 * u, 29 * u, 18 * u, GREY)
    b.rect(71 * u, 4 * u, 89 * u, 18 * u, GREY)
    return [a.done(), b.done()]


def nobox(s):
    u = s / 100
    a, b = sq(s, 2)
    a.rect(24 * u, 28 * u, 76 * u, 80 * u, MUSTARD, r=3 * u)
    a.rect(24 * u, 46 * u, 76 * u, 52 * u, (214, 140, 30))
    b.circ(50 * u, 54 * u, 42 * u, None, ORANGE, 7 * u)
    b.line([(22 * u, 26 * u), (78 * u, 82 * u)], ORANGE, 7 * u)
    return [a.done(), b.done()]


def flask(s):
    u = s / 100
    a, b, c = sq(s, 3)
    a.poly([(40 * u, 6 * u), (60 * u, 6 * u), (60 * u, 36 * u), (88 * u, 92 * u), (12 * u, 92 * u), (40 * u, 36 * u)], LBLUE)
    a.rect(36 * u, 2 * u, 64 * u, 10 * u, NAVY, r=2 * u)
    b.poly([(28 * u, 60 * u), (72 * u, 60 * u), (88 * u, 92 * u), (12 * u, 92 * u)], MUSTARD)
    c.circ(42 * u, 74 * u, 4 * u, WHITE)
    c.circ(58 * u, 80 * u, 3 * u, WHITE)
    c.circ(52 * u, 48 * u, 3 * u, WHITE)
    return [a.done(), b.done(), c.done()]


def bulb(s):
    u = s / 100
    a, b, c = sq(s, 3)
    a.circ(50 * u, 40 * u, 28 * u, MUSTARD)
    a.poly([(36 * u, 56 * u), (64 * u, 56 * u), (60 * u, 70 * u), (40 * u, 70 * u)], MUSTARD)
    b.rect(38 * u, 70 * u, 62 * u, 78 * u, GREY, r=2 * u)
    b.rect(40 * u, 80 * u, 60 * u, 88 * u, GREY, r=2 * u)
    b.rect(45 * u, 89 * u, 55 * u, 94 * u, DARK, r=2 * u)
    for ang in (-150, -110, -70, -30, 190):
        r = math.radians(ang)
        c.line([(50 * u + 36 * u * math.cos(r), 40 * u + 36 * u * math.sin(r)),
                (50 * u + 46 * u * math.cos(r), 40 * u + 46 * u * math.sin(r))], ORANGE, 4 * u)
    return [a.done(), b.done(), c.done()]


def dice(s):
    u = s / 100
    a, b = sq(s, 2)
    a.rect(10 * u, 10 * u, 90 * u, 90 * u, WHITE, r=14 * u, outline=DARK, width=4 * u)
    for x, y in ((30, 30), (70, 30), (50, 50), (30, 70), (70, 70)):
        b.circ(x * u, y * u, 7 * u, ORANGE if (x, y) == (50, 50) else DARK)
    return [a.done(), b.done()]


def parallel(s):
    u = s / 100
    L = sq(s, 3)
    for lay, y, col, x1 in zip(L, (22, 50, 78), (NAVY, ORANGE, MUSTARD), (78, 86, 70)):
        lay.line([(8 * u, y * u), (x1 * u, y * u)], col, 8 * u)
        lay.poly([((x1 + 14) * u, y * u), ((x1 - 2) * u, (y - 11) * u), ((x1 - 2) * u, (y + 11) * u)], col)
    return [l.done() for l in L]


def gear(s):
    u = s / 100
    a, b = sq(s, 2)
    pts = []
    for i in range(16):
        r = (44 if i % 2 == 0 else 34) * u
        for da in (-9, 9):
            ang = math.radians(i * 22.5 + da)
            pts.append((50 * u + r * math.cos(ang), 50 * u + r * math.sin(ang)))
    a.poly(pts, NAVY)
    b.circ(50 * u, 50 * u, 14 * u, LGREY)
    return [a.done(), b.done()]


def clock(s):
    u = s / 100
    a, b = sq(s, 2)
    a.circ(50 * u, 50 * u, 44 * u, DARK)
    a.circ(50 * u, 50 * u, 37 * u, WHITE)
    for i in range(12):
        r = math.radians(i * 30)
        a.line([(50 * u + 30 * u * math.cos(r), 50 * u + 30 * u * math.sin(r)),
                (50 * u + 34 * u * math.cos(r), 50 * u + 34 * u * math.sin(r))], GREY, 2 * u)
    b.line([(50 * u, 50 * u), (50 * u, 24 * u)], DARK, 5 * u)
    b.line([(50 * u, 50 * u), (68 * u, 58 * u)], ORANGE, 4 * u)
    b.circ(50 * u, 50 * u, 5 * u, MUSTARD)
    return [a.done(), b.done()]


def hourglass(s):
    u = s / 100
    a, b = sq(s, 2)
    a.poly([(26 * u, 12 * u), (74 * u, 12 * u), (52 * u, 50 * u), (74 * u, 88 * u), (26 * u, 88 * u), (48 * u, 50 * u)], LBLUE)
    a.rect(18 * u, 4 * u, 82 * u, 12 * u, DARK, r=3 * u)
    a.rect(18 * u, 88 * u, 82 * u, 96 * u, DARK, r=3 * u)
    b.poly([(36 * u, 22 * u), (64 * u, 22 * u), (50 * u, 44 * u)], MUSTARD)
    b.poly([(50 * u, 66 * u), (70 * u, 86 * u), (30 * u, 86 * u)], MUSTARD)
    return [a.done(), b.done()]


ICONS = {
    "boxes": boxes, "pull": pull, "stairs": stairs, "people": people, "checklist": checklist, "clipboard": clipboard, "bin": bin_,
    "magnifier": magnifier, "chart": chart, "target": target, "loop": loop, "calm": calm, "smiley": smiley,
    "coin": coin, "bank": bank, "arrows4": arrows4, "warn": warn, "trophy": trophy, "arrow_up": arrow_up,
    "arrow_down": arrow_down, "document": document, "toolboard": toolboard, "orgchart": orgchart,
    "balance": balance_icon, "bolt": bolt, "magnet": magnet, "nobox": nobox, "flask": flask, "bulb": bulb,
    "dice": dice, "parallel": parallel, "gear": gear, "clock": clock, "hourglass": hourglass,
    "customer": customer, "worker": worker, "robot": robot, "factory": factory, "dowel": dowel, "flag_jp": flag_jp,
}
