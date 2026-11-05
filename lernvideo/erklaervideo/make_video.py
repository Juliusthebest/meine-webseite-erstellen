"""Erklärvideo „Lean Production – einfach erklärt“ im Stil moderner Lern-/Erklärvideos.

Heller Hintergrund, Emoji-Icons, Elemente ploppen synchron zur Sprecherstimme ins Bild.
Benötigt: Python 3 + Pillow + numpy, ffmpeg, pico2wave (Paket libttspico-utils).

Aufruf:  python3 make_video.py
Ergebnis: lean_production_erklaert.mp4 (mit Stimme), ..._ohne_ton.mp4, ...srt (Untertitel)
"""
import os
import re
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
SR = 16000  # pico2wave sample rate

FD = "/usr/share/fonts/opentype/inter/"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

BG = (250, 248, 243)
INK = (28, 28, 40)
MUTED = (105, 108, 125)
WHITE = (255, 255, 255)
BLUE = (45, 107, 255)
YELLOW = (255, 214, 64)
GREEN = (30, 190, 125)
RED = (245, 80, 80)
LIGHT_Y = (255, 243, 196)
LIGHT_G = (214, 245, 228)
LIGHT_R = (255, 222, 222)
LIGHT_B = (220, 232, 255)

_fonts = {}


def font(size, weight="Bold"):
    key = (size, weight)
    if key not in _fonts:
        name = ("InterDisplay-" if size >= 60 else "Inter-") + weight + ".otf"
        _fonts[key] = ImageFont.truetype(FD + name, size)
    return _fonts[key]


# --------------------------------------------------------------------------- Sprite-Bausteine
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def wrap(text, f, maxw):
    if maxw is None:
        return text.split("\n")
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text(s, size, color=INK, weight="Bold", maxw=None, align="center", spacing=1.18):
    f = font(size, weight)
    lines = wrap(s, f, maxw)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lw = [d.textlength(l, font=f) for l in lines]
    asc, desc = f.getmetrics()
    lh = int(size * spacing)
    w = int(max(lw)) + 8
    h = lh * (len(lines) - 1) + asc + desc + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for i, (l, ww) in enumerate(zip(lines, lw)):
        x = {"center": (w - ww) / 2, "left": 4, "right": w - ww - 4}[align]
        dr.text((x, 4 + i * lh), l, font=f, fill=color)
    return im


def panel(w, h, fill=WHITE, radius=26, outline=INK, shadow=8, ow=4):
    im = Image.new("RGBA", (w + shadow, h + shadow), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.rounded_rectangle([shadow, shadow, w + shadow - 1, h + shadow - 1], radius, fill=INK)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=fill, outline=outline, width=ow)
    return im


def paste(base, im, x, y):
    base.alpha_composite(im, (int(x), int(y)))


def chip(label, emo=None, size=40, fill=WHITE, color=INK, padx=34, pady=18, shadow=6):
    t = text(label, size, color)
    e = emoji(emo, int(size * 1.25)) if emo else None
    ew = e.width + 16 if e else 0
    w, h = padx * 2 + ew + t.width, pady * 2 + max(t.height, e.height if e else 0)
    im = panel(w, h, fill=fill, radius=h // 2, shadow=shadow)
    if e:
        paste(im, e, padx, (h - e.height) / 2)
    paste(im, t, padx + ew, (h - t.height) / 2)
    return im


def card(w, h, emo, title, sub, fill=WHITE, accent=BLUE, tsize=40, ssize=29, esize=92):
    from PIL import ImageChops
    im = panel(w, h, fill=fill)
    strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(strip).rectangle([0, 0, w, 22], fill=accent)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=255)
    strip.putalpha(ImageChops.multiply(strip.getchannel("A"), mask))
    im.alpha_composite(strip, (0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], 26, outline=INK, width=4)
    e = emoji(emo, esize)
    paste(im, e, 30, 48)
    tx = 30 + e.width + 24
    t = text(title, tsize, INK, maxw=w - tx - 24, align="left", spacing=1.1)
    paste(im, t, tx, 48 + (e.height - t.height) / 2 if t.height < e.height else 48)
    s = text(sub, ssize, MUTED, "Medium", maxw=w - 54, align="left", spacing=1.25)
    paste(im, s, 26, max(48 + t.height, 48 + e.height) + 16)
    return im


def node(emo, label, w=340, h=120, fill=WHITE):
    im = panel(w, h, fill=fill)
    e = emoji(emo, 64)
    t = text(label, 38, INK)
    x = (w - e.width - 16 - t.width) / 2
    paste(im, e, x, (h - e.height) / 2)
    paste(im, t, x + e.width + 16, (h - t.height) / 2)
    return im


def arrow(length, color=INK, thick=12, head=34, flip=False):
    im = Image.new("RGBA", (length, head + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = (head + 4) // 2
    d.rounded_rectangle([0, cy - thick // 2, length - head + 4, cy + thick // 2], thick // 2, fill=color)
    d.polygon([(length - head, cy - head // 2 - 2), (length, cy), (length - head, cy + head // 2 + 2)], fill=color)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def marker(w, h, color=YELLOW):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], h // 3, fill=color + (255,))
    return im.rotate(-1.2, expand=True, resample=Image.BICUBIC)


def list_row(emo, label, w=800, h=84, fill=WHITE, tsize=32):
    im = panel(w, h, fill=fill, radius=20, shadow=6, ow=3)
    e = emoji(emo, 46)
    paste(im, e, 22, (h - e.height) / 2)
    t = text(label, tsize, INK, "SemiBold", maxw=w - 110, align="left")
    paste(im, t, 22 + e.width + 20, (h - t.height) / 2)
    return im


def hbar(w, h=10, color=INK):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=color)
    return im


def dot(r, color=BLUE):
    im = Image.new("RGBA", (r * 2 + 8, r * 2 + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, r * 2 + 6, r * 2 + 6], fill=INK)
    ImageDraw.Draw(im).ellipse([5, 5, r * 2 + 1, r * 2 + 1], fill=color)
    return im


def S(img, x, y, anim="pop", f=0.0, d=0.0, anchor="c"):
    """Sprite: x/y = Mittelpunkt (anchor c) bzw. linke Kante (anchor l). f = Verzögerung als Anteil der Beat-Dauer."""
    if anchor == "l":
        x = x + img.width / 2
    return dict(img=img, x=x, y=y, anim=anim, f=f, d=d)


# --------------------------------------------------------------------------- Drehbuch
def title(s, y=180, size=78):
    return S(text(s, size, INK, "ExtraBold"), 960, y, "rise")


def title_hl(s, y=180, size=78):
    t = text(s, size, INK, "ExtraBold")
    return [S(marker(t.width + 50, int(size * 0.62)), 960, y + size * 0.16, "wipe"), S(t, 960, y, "rise")]


SCENES = []


def scene(label, beats):
    SCENES.append(dict(label=label, beats=beats))


def B(sub, add=(), clear=False, pause=0.45):
    return dict(sub=sub, add=list(add), clear=clear, pause=pause)


def chip_row(items, y, size=34, gap=28):
    ims = [chip(l, e, size) for l, e in items]
    total = sum(i.width for i in ims) + gap * (len(ims) - 1)
    x, out_ = (W - total) / 2, []
    for k, im in enumerate(ims):
        out_.append(S(im, x + im.width / 2, y, f=k * 0.12))
        x += im.width + gap
    return out_


# 1 Intro
big = text("Lean Production", 150, INK, "Black")
scene("Intro", [
    B("Wie schafft es ein Autohersteller, mit weniger Lager, weniger Platz und weniger Fehlern mehr zu produzieren?", [
        S(emoji("🚗", 300), 860, 470), S(emoji("❓", 200), 1150, 360, f=0.25),
        S(text("Mehr schaffen – mit weniger?", 66, INK, "ExtraBold"), 960, 780, "rise", f=0.5)]),
    B("Die Antwort heißt: Lean Production.", [
        S(marker(big.width + 70, 100), 960, 500, "wipe", d=0.3), S(big, 960, 470, "pop"),
        S(chip("einfach erklärt", "💡", 42, fill=LIGHT_B), 960, 660, f=0.5)], clear=True),
    B("In diesem Video lernst du, was dahintersteckt und wie du es in der Prüfung erklärst.", [
        *chip_row([("Begriff", "📌"), ("Herkunft", "📜"), ("Verschwendung", "🗑"), ("Prinzipien", "⚙"), ("Bewertung", "⚖")], 850)]),
])

# 2 Begriff
schlank = text("schlank", 140, BLUE, "Black")
scene("Begriff", [
    B("Lean heißt auf Deutsch: schlank.", [
        S(text("lean", 140, INK, "Black"), 560, 300), S(text("=", 140, MUTED, "Black"), 860, 300, f=0.3),
        S(marker(schlank.width + 50, 80), 1240, 330, "wipe", f=0.5), S(schlank, 1240, 300, f=0.5)]),
    B("Gemeint ist eine Produktion ohne unnötigen Ballast.", [
        S(emoji("🏭", 210), 860, 580), S(emoji("✂", 130), 1090, 520, f=0.4)]),
    B("Alles, was dem Kunden keinen Nutzen bringt, gilt als Verschwendung und wird konsequent abgebaut.", [
        S(chip("Kein Kundennutzen  =  Verschwendung  →  weg damit!", "💡", 48, fill=LIGHT_Y, padx=46, pady=26), 960, 850, "rise")]),
])

# 3 Herkunft
scene("Herkunft", [
    B("Erfunden wurde das Ganze bei Toyota in Japan, nach dem Zweiten Weltkrieg.", [
        S(hbar(1400), 960, 300, "wipe"), S(dot(20, RED), 500, 300, f=0.3),
        S(text("1950er", 44, RED, "ExtraBold"), 500, 230, "rise", f=0.3),
        S(text("Toyota, Japan", 32, INK, "SemiBold"), 500, 370, "rise", f=0.4)]),
    B("Toyota hatte wenig Geld, wenig Platz und nur kleine Stückzahlen. Massenproduktion wie bei Ford war so nicht möglich.", [
        S(card(640, 300, "🏭", "Massenproduktion (Ford)", "riesige Mengen · große Lager · wenig Varianten", accent=RED), 560, 720),
        S(text("vs.", 60, MUTED, "Black"), 960, 720, f=0.35),
        S(card(640, 300, "🚗", "Toyota nach 1945", "kleine Mengen · wenig Platz · viele Varianten", accent=GREEN), 1360, 720, f=0.45)]),
    B("Daraus entstand unter Taiichi Ohno das Toyota-Produktionssystem. Spätestens nach der Ölkrise 1973 zeigte sich, wie erfolgreich es ist.", [
        S(dot(20, YELLOW), 960, 300), S(text("1973", 44, INK, "ExtraBold"), 960, 230, "rise"),
        S(text("Toyota-Produktionssystem\nüberzeugt in der Ölkrise", 30, INK, "SemiBold"), 960, 390, "rise", f=0.1)]),
    B("Den Begriff Lean Production prägte dann um 1990 eine Studie des MIT.", [
        S(dot(20, GREEN), 1420, 300), S(text("1990", 44, GREEN, "ExtraBold"), 1420, 230, "rise"),
        S(text("MIT-Studie prägt\n„Lean Production“", 30, INK, "SemiBold"), 1420, 390, "rise", f=0.1)]),
])

# 4 Verschwendung
waste = [("📦", "Überproduktion", "mehr herstellen als bestellt",
          "Eins: Überproduktion. Es wird mehr hergestellt, als bestellt ist."),
         ("🗄", "Bestände", "volle Lager binden Kapital",
          "Zwei: zu hohe Bestände. Volle Lager binden Kapital."),
         ("🚚", "Transport", "unnötige Wege für Material",
          "Drei: Transport. Material wird unnötig hin und her gefahren."),
         ("⏳", "Wartezeiten", "Mensch oder Maschine steht still",
          "Vier: Wartezeiten. Menschen oder Maschinen stehen still."),
         ("🚶", "Bewegung", "Suchen, Laufen, Bücken",
          "Fünf: unnötige Bewegung, zum Beispiel Suchen oder Laufen."),
         ("⚙", "Überbearbeitung", "mehr Aufwand, als der Kunde zahlt",
          "Sechs: Überbearbeitung. Es wird mehr Aufwand betrieben, als der Kunde bezahlt."),
         ("❌", "Fehler", "Ausschuss & Nacharbeit",
          "Und sieben: Fehler, also Ausschuss und Nacharbeit.")]
pos = [(315, 480), (745, 480), (1175, 480), (1605, 480), (530, 790), (960, 790), (1390, 790)]
scene("Verschwendung", [
    B("Das Herzstück ist der Kampf gegen Verschwendung. Auf Japanisch heißt sie Muda. Es gibt sieben Arten.", [
        *title_hl("Die 7 Arten der Verschwendung", 170, 72), S(chip("japanisch: Muda", None, 32, fill=LIGHT_R), 960, 275, f=0.35)]),
] + [B(say, [S(card(400, 260, e, t, s, accent=RED, tsize=33, ssize=27, esize=64), x, y)], pause=0.3)
     for (e, t, s, say), (x, y) in zip(waste, pos)])

# 5 Pull statt Push
scene("Pull statt Push", [
    B("Ein zentrales Prinzip lautet: Pull statt Push.", [*title_hl("Pull statt Push", 170, 84)]),
    B("Klassisch wird auf Lager produziert und die Ware in den Markt gedrückt. Das ist Push.", [
        S(chip("PUSH", None, 40, fill=RED, color=WHITE), 230, 430),
        S(node("🏭", "Produktion"), 620, 430, f=0.05), S(arrow(150), 870, 430, "wipe", f=0.2),
        S(node("🗄", "Lager"), 1120, 430, f=0.25), S(arrow(150), 1370, 430, "wipe", f=0.4),
        S(node("🙋", "Kunde"), 1620, 430, f=0.45),
        S(text("erst produzieren – dann hoffen, dass jemand kauft", 32, MUTED, "Medium"), 1120, 540, "rise", f=0.6)]),
    B("Bei Lean zieht der Kunde die Produktion: Erst wenn bestellt wird, wird produziert. Das ist Pull.", [
        S(chip("PULL", None, 40, fill=GREEN, color=WHITE), 230, 700),
        S(node("🙋", "Kunde"), 620, 700, f=0.05), S(arrow(150, GREEN), 870, 700, "wipe", f=0.2),
        S(node("📝", "Bestellung"), 1120, 700, f=0.25), S(arrow(150, GREEN), 1370, 700, "wipe", f=0.4),
        S(node("🏭", "Produktion"), 1620, 700, f=0.45),
        S(text("erst bestellen – dann produzieren", 32, MUTED, "Medium"), 1120, 810, "rise", f=0.6)]),
    B("Den Nachschub steuern oft Kanban-Karten: Teile kommen genau dann, wenn sie gebraucht werden. Das nennt man Just in Time.", [
        S(chip("Kanban-Karten", "🗂", 40, fill=LIGHT_Y), 760, 935), S(chip("Just-in-Time", "⏱", 40, fill=LIGHT_B), 1200, 935, f=0.6)]),
])

# 6 Bausteine
scene("Prinzipien", [
    B("Dazu kommen weitere wichtige Bausteine.", [*title_hl("Weitere Bausteine", 170, 84)]),
    B("Kaizen, der kontinuierliche Verbesserungsprozess. Jeden Tag ein kleines bisschen besser werden.", [
        S(card(800, 270, "📈", "Kaizen (KVP)", "Kontinuierliche Verbesserung – jeden Tag ein bisschen besser", accent=BLUE), 530, 450)]),
    B("Das Null-Fehler-Prinzip, auf Japanisch Jidoka: Tritt ein Fehler auf, wird sofort gestoppt und die Ursache beseitigt.", [
        S(card(800, 270, "🛑", "Null-Fehler-Prinzip (Jidoka)", "Bei Fehlern sofort stoppen und die Ursache beheben", accent=RED), 1390, 450)]),
    B("Teamarbeit: Gruppen organisieren ihre Arbeit selbst und übernehmen Verantwortung.", [
        S(card(800, 270, "👥", "Teamarbeit", "Gruppen organisieren sich selbst und tragen Verantwortung", accent=GREEN), 530, 770)]),
    B("Und die 5S-Methode: ein sauberer, geordneter Arbeitsplatz, an dem niemand mehr suchen muss.", [
        S(card(800, 270, "🧹", "5S-Methode", "Sortieren, Ordnung, Sauberkeit – kein Suchen mehr", accent=YELLOW), 1390, 770)]),
])

# 7 Bewertung
pros = [("✅", "geringere Kosten & Kapitalbindung"), ("✅", "kürzere Durchlaufzeiten"),
        ("✅", "bessere Qualität"), ("✅", "zufriedenere Kunden")]
cons = [("⚠", "Lieferausfall → Produktion steht"), ("⚠", "starke Abhängigkeit der Zulieferer"),
        ("⚠", "Leistungsdruck für Mitarbeiter"), ("⚠", "Einführung braucht viel Zeit")]
scene("Bewertung", [
    B("Und was bringt das alles? Schauen wir uns Vor- und Nachteile an.", [
        title("Vor- & Nachteile", 160, 80),
        S(chip("Vorteile", "👍", 44, fill=LIGHT_G), 530, 300, f=0.3), S(chip("Nachteile", "👎", 44, fill=LIGHT_R), 1390, 300, f=0.5)]),
    B("Die Vorteile: geringere Kosten und weniger gebundenes Kapital, kürzere Durchlaufzeiten, bessere Qualität und zufriedenere Kunden.",
      [S(list_row(e, l), 530, 420 + i * 105, "rise", f=i * 0.22) for i, (e, l) in enumerate(pros)]),
    B("Die Nachteile: Ohne Lagerpuffer kann ein einziger Lieferausfall die ganze Produktion stoppen. Die Zulieferer werden stark abhängig, und auf den Mitarbeitern lastet hoher Leistungsdruck.",
      [S(list_row(e, l), 1390, 420 + i * 105, "rise", f=[0, 0.5, 0.75][i]) for i, (e, l) in enumerate(cons[:3])]),
    B("Außerdem kostet die Einführung viel Zeit, denn sie verlangt ein echtes Umdenken im ganzen Unternehmen.",
      [S(list_row(*cons[3]), 1390, 735, "rise")]),
])

# 8 Merke
merke_box = panel(1500, 640, fill=LIGHT_Y, radius=34, shadow=12, ow=5)
scene("Merke", [
    B("Merke dir für die Prüfung:", [
        S(merke_box, 960, 560, "pop"), S(chip("Merke", "📝", 50, fill=YELLOW), 960, 250, f=0.2)]),
    B("Lean Production heißt: Verschwendung vermeiden, vom Kunden her denken und ständig verbessern.", [
        S(list_row("🗑", "Verschwendung vermeiden", 1100, 92, tsize=42), 960, 400, "rise", f=0.15),
        S(list_row("🙋", "vom Kunden her denken (Pull)", 1100, 92, tsize=42), 960, 515, "rise", f=0.45),
        S(list_row("📈", "ständig verbessern (Kaizen)", 1100, 92, tsize=42), 960, 630, "rise", f=0.7)]),
    B("Das Ziel: höhere Qualität, kürzere Zeiten und niedrigere Kosten.", [
        S(emoji("🎯", 80), 520, 770),
        S(text("Qualität ↑     Zeit ↓     Kosten ↓", 56, BLUE, "ExtraBold"), 1010, 770, "rise", f=0.2)]),
])

# 9 Quiz + Outro
def _opt(letter, label, fill=WHITE):
    im = panel(420, 140, fill=fill)
    c = Image.new("RGBA", (78, 78), (0, 0, 0, 0))
    ImageDraw.Draw(c).ellipse([0, 0, 77, 77], fill=INK)
    tl = text(letter, 40, WHITE, "ExtraBold")
    paste(c, tl, (78 - tl.width) / 2, (78 - tl.height) / 2)
    paste(im, c, 30, 31)
    t = text(label, 42, INK)
    paste(im, t, 132, (140 - t.height) / 2)
    return im


done = text("Das war's!", 140, INK, "Black")
scene("Quiz", [
    B("Kurzer Check! Welche Art von Verschwendung ist ein überfülltes Ersatzteillager?", [
        S(chip("Quiz", "🤔", 44, fill=LIGHT_B), 960, 170),
        S(text("Welche Verschwendungsart ist ein überfülltes Ersatzteillager?", 60, INK, "ExtraBold", maxw=1500), 960, 340, "rise", f=0.1),
        S(_opt("A", "Transport"), 460, 620, f=0.5), S(_opt("B", "Bestände"), 960, 620, f=0.6),
        S(_opt("C", "Fehler"), 1460, 620, f=0.7)]),
    B("Denk kurz nach. Drei. Zwei. Eins.", [S(emoji("⏳", 110), 1720, 860)]),
    B("Richtig ist B: Bestände! Volle Lager binden Kapital und verstecken Probleme.", [
        S(_opt("B", "Bestände ✓", LIGHT_G), 960, 620), S(emoji("✅", 90), 1150, 545, f=0.1),
        S(text("Volle Lager binden Kapital und verstecken Probleme.", 40, INK, "SemiBold"), 960, 860, "rise", f=0.3)]),
    B("Das war's! Jetzt kennst du die Grundlagen der Lean Production. Viel Erfolg bei deiner Prüfung!", [
        S(marker(done.width + 60, 90), 960, 480, "wipe"), S(done, 960, 450),
        S(emoji("🎉", 170), 1420, 360, f=0.2),
        S(chip("Viel Erfolg bei der Prüfung!", "🍀", 48, fill=LIGHT_G), 960, 660, f=0.5)], clear=True),
])

# Aussprache-Hilfen für die deutsche Sprachausgabe
SAY = [("Lean Production", "Lien Prodacktschen"), ("Lean", "Lien"), ("Push", "Pusch"),
       ("Just in Time", "Dschast in Taim"), ("Jidoka", "Dschidoka"), ("Kaizen", "Kaisen"),
       ("MIT", "Em Ai Tie"), ("Taiichi Ohno", "Taiitschi Ohno"), ("5S", "Fünf S"),
       ("Kanban", "Kahnbahn"), ("Ford", "Fohrd")]


def to_say(s):
    for a, b in SAY:
        s = re.sub(r"\b" + re.escape(a) + r"\b", b, s)
    return s


# --------------------------------------------------------------------------- Audio
def tts(s, path):
    subprocess.run(["pico2wave", "-l", "de-DE", "-w", path, to_say(s)], check=True)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    # Stille am Rand abschneiden
    nz = np.where(np.abs(a) > 300)[0]
    if len(nz):
        a = a[max(0, nz[0] - 400): nz[-1] + 1600]
    return a


def pop_sfx():
    t = np.arange(int(SR * 0.07)) / SR
    freq = 900 - 5000 * t
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 55) * 2600


def whoosh_sfx():
    n = int(SR * 0.45)
    rng = np.random.default_rng(1)
    noise = np.convolve(rng.normal(size=n), np.ones(12) / 12, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return noise * env * 2200


# --------------------------------------------------------------------------- Timeline
TRANS = 0.7
LEAD = 0.35


def build_timeline(tmp):
    t = 0.6
    voice = []      # (start, samples)
    sfx = []        # (start, samples)
    subs = []       # (start, end, text)
    for si, sc in enumerate(SCENES):
        sc["start"] = t
        if si > 0:
            sfx.append((t - TRANS, whoosh_sfx()))
        t += LEAD
        for bi, b in enumerate(sc["beats"]):
            a = tts(b["sub"], os.path.join(tmp, f"{si}_{bi}.wav"))
            dur = len(a) / SR
            b["t0"], b["dur"] = t, dur
            voice.append((t, a))
            subs.append((t, t + dur, b["sub"]))
            for sp in b["add"]:
                sp["t"] = t + sp["d"] + sp["f"] * dur
                sfx.append((sp["t"], pop_sfx() * (0.6 if sp["anim"] != "pop" else 1.0)))
            t += dur + b["pause"]
        t += 0.5
        sc["end"] = t
        t += TRANS
    total = t + 0.6
    audio = np.zeros(int(total * SR) + SR)
    for st, a in voice:
        i = int(st * SR)
        audio[i:i + len(a)] += a * (20000 / max(1, np.abs(a).max()))
    for st, a in sfx:
        i = int(st * SR)
        audio[i:i + len(a)] += a
    audio = np.clip(audio, -32000, 32000).astype(np.int16)
    return total, audio, subs


# --------------------------------------------------------------------------- Rendering
def back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.9, 2.9
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def make_bg():
    im = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(im)
    for x in range(40, W, 48):
        for y in range(40, H, 48):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(226, 222, 212))
    return im


def chrome(frame, label, progress):
    d = ImageDraw.Draw(frame)
    lab = chip(label, None, 26, fill=INK, color=WHITE, padx=24, pady=10, shadow=0)
    paste(frame, lab, 40, 34)
    t = text("Lean Production", 26, MUTED, "SemiBold")
    paste(frame, t, W - 40 - t.width, 42)
    d.rectangle([0, H - 12, W, H], fill=(230, 226, 216))
    d.rectangle([0, H - 12, int(W * progress), H], fill=BLUE)


_chrome_cache = {}


def draw_scene(sc, t, base):
    frame = base.copy()
    visible = []
    for b in sc["beats"]:
        if t < b["t0"] and b["clear"]:
            break
        if b["clear"] and t >= b["t0"]:
            visible = []
        visible += [sp for sp in b["add"] if t >= sp["t"]]
    for sp in visible:
        k = t - sp["t"]
        img = sp["img"]
        x, y = sp["x"] - img.width / 2, sp["y"] - img.height / 2
        if sp["anim"] == "pop":
            s = back(k / 0.38)
            if s < 0.999 or k < 0.38:
                s = max(0.02, s)
                im2 = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
                a = min(1, k / 0.12)
                if a < 1:
                    im2.putalpha(im2.getchannel("A").point(lambda v: int(v * a)))
                paste(frame, im2, sp["x"] - im2.width / 2, sp["y"] - im2.height / 2)
                continue
        elif sp["anim"] == "rise":
            p = out(k / 0.4)
            if p < 1:
                im2 = img.copy()
                im2.putalpha(im2.getchannel("A").point(lambda v: int(v * p)))
                paste(frame, im2, x, y + (1 - p) * 40)
                continue
        elif sp["anim"] == "wipe":
            p = out(k / 0.45)
            if p < 1:
                cw = max(1, int(img.width * p))
                paste(frame, img.crop((0, 0, cw, img.height)), x, y)
                continue
        paste(frame, img, x, y)
    return frame


def render(total, outfile, audio_file):
    base = make_bg()
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", audio_file, "-c:v", "libx264", "-preset", "medium", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", outfile],
        stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    for fi in range(nframes):
        t = fi / FPS
        # aktuelle Szene (Wechsel in der Mitte des Übergangs)
        sc = SCENES[0]
        for s in SCENES:
            if t >= s["start"] - TRANS / 2:
                sc = s
        b = base.copy()
        chrome(b, sc["label"], t / total)
        frame = draw_scene(sc, t, b)
        # Übergang: blaue Fläche wischt durchs Bild
        for s in SCENES[1:]:
            k = (t - (s["start"] - TRANS)) / TRANS
            if 0 <= k <= 1:
                d = ImageDraw.Draw(frame)
                if k < 0.5:
                    x1 = out(k * 2) * (W + 200)
                    d.polygon([(0, 0), (x1, 0), (x1 - 200, H), (0, H)], fill=BLUE)
                else:
                    x0 = out((k - 0.5) * 2) * (W + 200)
                    d.polygon([(x0, 0), (W + 200, 0), (W + 200, H), (x0 - 200, H)], fill=BLUE)
        proc.stdin.write(frame.convert("RGB").tobytes())
        if fi % (FPS * 20) == 0:
            print(f"  {t:5.0f}/{total:.0f} s")
    proc.stdin.close()
    proc.wait()


def srt_time(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def preview(outdir):
    """Speichert je Szene ein Standbild (Ende der Szene) – zum schnellen Prüfen des Layouts."""
    import sys
    with tempfile.TemporaryDirectory() as tmp:
        total, _, _ = build_timeline(tmp)
    base = make_bg()
    for i, sc in enumerate(SCENES):
        b = base.copy()
        chrome(b, sc["label"], 0.5)
        draw_scene(sc, sc["end"] - 0.01, b).convert("RGB").save(os.path.join(outdir, f"scene_{i}.png"))
    print(f"Länge: {total:.1f} s")


def main():
    name = os.path.join(HERE, "lean_production_erklaert")
    with tempfile.TemporaryDirectory() as tmp:
        total, audio, subs = build_timeline(tmp)
        wav = os.path.join(tmp, "audio.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(audio.tobytes())
        print(f"Länge: {total:.1f} s – rendere …")
        render(total, name + ".mp4", wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", name + ".mp4", "-c:v", "copy", "-an",
                    name + "_ohne_ton.mp4"], check=True)
    with open(name + ".srt", "w", encoding="utf-8") as f:
        for i, (a, b, s) in enumerate(subs, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    print("fertig:", name + ".mp4")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        preview(sys.argv[2])
    else:
        main()
