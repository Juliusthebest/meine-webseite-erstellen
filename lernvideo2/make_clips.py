"""Lernvideo 2: „Lean Production bei der GN-Glasfaser GmbH“ – Kern & Umsetzung, Kosteneinsparung,
Gehaltsforderung. Gleicher Flat-Design-Stil wie lernvideo/ (nutzt dessen Engine und Symbole).

Aufruf:
  python3 make_clips.py                 -> clips/*.mp4, clips/ohne_ton/*.mp4, Gesamtvideo, SPRECHERTEXT.md
  python3 make_clips.py --preview DIR   -> Standbilder je Satz
  python3 make_clips.py --only 02       -> nur Clips, deren Name so beginnt
Eigene Aufnahmen: aufnahmen/00.m4a … 03.m4a (werden automatisch verwendet, wenn vorhanden).
"""
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lernvideo"))

import align_voice  # noqa: E402
import flat_engine  # noqa: E402
import flat_icons as F  # noqa: E402
from flat_engine import (ALPHA, ANGLE, ARROW, B, BANNER, CARD, CHECK, CROSS, DARK, GREY, ICON, LISTCARD, MUSTARD,  # noqa: E402
                         NAVY, ORANGE, PULSE, SC, STEEL, TAG, TITLE, TXT, WHITE, Sp, card_img, comp, draw_scene,
                         ease_out, k, paste, rect_img, render, text_img, timeline, write_wav)

flat_engine.SR = 48000
flat_engine.SAY += [("GN-Glasfaser", "Ge En Glasfaser"), ("GN", "Ge En")]
align_voice.REC_DIR = os.path.join(HERE, "aufnahmen")
_logo = Image.open(os.path.join(HERE, "..", "lernvideo", "assets", "toyota_logo.png")).convert("RGBA")


def LOGO(x, y, h, f=0.0, d=0.0):
    hh = k(h)
    return Sp(_logo.resize((round(_logo.width * hh / _logo.height), hh), Image.LANCZOS), x, y, "zoom", f, d, "tick")


def de(v, dec=2):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


class Count(Sp):
    """Zahl, die hochzählt (z. B. Gesamtsumme)."""

    def __init__(self, lo, hi, x, y, size=54, color=DARK, f=0.0, d=0.0, dur=1.4):
        self.lo, self.hi, self.size, self.color, self.cdur = lo, hi, size, color, dur
        super().__init__(text_img(self.label(1.0), size, color, "xbold"), x, y, "fadeup", f, d, "tick")
        self._final = self.img

    def label(self, p):
        if self.lo == self.hi:
            return de(self.lo * p) + " €"
        return de(self.lo * p) + " € bis " + de(self.hi * p) + " €"

    def draw(self, frame, now, dim=0.0):
        pr = self.props(now)
        if pr is None:
            return
        x, y, s, a, _, _ = pr
        p = (now - self.t) / self.cdur
        img = self._final if p >= 1 else text_img(self.label(ease_out(p)), self.size, self.color, "xbold")
        img = self._xform(img, s, a * (1 - 0.5 * dim), 0)
        paste(frame, img, k(x) - img.width / 2, k(y) - img.height / 2)


def mini(x, y, icon, label, f=0.0, w=420, size=32, cross=False):
    out = [Sp(card_img(w, 120), x, y, "fadeup", f, 0, "tick")]
    out += ICON(icon, x - w / 2 + 70, y, 70, f, 0.15)
    out.append(TXT(label, x + 40, y, size, DARK, "bold", f=f, d=0.25, maxw=w - 140))
    if cross:
        out.append(CROSS(x - w / 2 + 70, y, 70, ORANGE, 9, f=f, d=0.5))
    return out


CLIPS = []


def clip(name, label, scenes):
    CLIPS.append(dict(name=name, label=label, scenes=scenes))


# ============================================================================ 00 Einführung
clip("00_einfuehrung", "Einführung", [
    SC([
        B("In diesem Video geht es um die GN-Glasfaser GmbH aus Gelnhausen.", [
            ICON("factory", 760, 470, 260), ICON("fiber", 1150, 470, 230, f=0.3),
            TXT("GN-Glasfaser GmbH", 960, 720, 72, DARK, "xbold", f=0.35),
            TXT("aus Gelnhausen im Main-Kinzig-Kreis", 960, 800, 36, STEEL, "semi", f=0.5)]),
        B("Das Unternehmen stellt Glasfaserprodukte für die Telekommunikationsbranche her und hat gute Absatzchancen in Europa.", [
            TAG("Telekommunikation", 600, 300, NAVY, WHITE, rot=-5, f=0.25, size=30),
            TAG("gute Absatzchancen in Europa", 1330, 300, MUSTARD, DARK, rot=4, f=0.6, size=30)]),
        B("Die Geschäftsführung möchte die Produktion effizienter gestalten und Personal und Anlagen bestmöglich einsetzen. Deshalb beschäftigt sie sich mit Lean Production.", [
            TITLE("Lean Production", "schlanker und effizienter produzieren", y=240, size=84),
            ICON("machine", 640, 640, 220, f=0.25), ICON("people", 960, 640, 230, f=0.4), ICON("gear", 1280, 640, 200, f=0.55)],
          clear=True),
    ]),
    SC([
        B("Im Folgenden klären wir drei Fragen.", [TITLE("Das erwartet dich", y=150, size=70)]),
        B("Was ist der Kern von Lean Production und wie setzt man es um? Wie viel Geld spart das Unternehmen dadurch? Und ist die Forderung nach fünfzehn Prozent mehr Gehalt berechtigt?", [
            CARD(480, 600, 440, 440, "stairs", "Kern & Umsetzung", "Was steckt hinter Lean Production?", f=0.0, tsize=34, ssize=25),
            CARD(960, 600, 440, 440, "coin", "Kosteneinsparung", "Rechnung für 2022 und 2023", f=0.35, tsize=34, ssize=25),
            CARD(1440, 600, 440, 440, "megaphone", "Gehaltsforderung", "+15 % – berechtigt oder nicht?", f=0.7, tsize=34, ssize=25)]),
    ]),
])

# ============================================================================ 01 Kern & Umsetzung
clip("01_kern_und_umsetzung", "Kern & Umsetzung", [
    SC([
        B("Was ist eigentlich der Kern von Lean Production?", [
            TITLE("Der Kern von Lean Production", y=120, size=66),
            TXT("Vorbild:", 822, 210, 36, STEEL, "semi", f=0.4), LOGO(942, 210, 60, f=0.45),
            TXT("Toyota", 1055, 210, 36, DARK, "bold", f=0.5)]),
        B("Lean heißt schlank. Gemeint ist eine Produktion ohne Verschwendung.", [
            TXT("Lean = schlank", 960, 350, 64, DARK, "xbold"),
            TXT("Produktion ohne Verschwendung", 960, 430, 40, ORANGE, "bold", f=0.45)]),
        B("Alles, was keinen Wert für den Kunden schafft, wird konsequent weggelassen, zum Beispiel unnötige Lagerbestände, Überproduktion, Wartezeiten und Fehler.", [
            mini(520, 580, "boxes", "Lagerbestände", f=0.2, cross=True), mini(1000, 580, "factory", "Überproduktion", f=0.35, cross=True),
            mini(520, 730, "hourglass", "Wartezeiten", f=0.5, cross=True), mini(1000, 730, "warn", "Fehler", f=0.65, cross=True),
            ICON("customer", 1500, 630, 200, f=0.1), TXT("schafft keinen Wert", 1500, 775, 30, STEEL, "bold", f=0.15)]),
        B("Im Mittelpunkt stehen der Kunde und die Wertschöpfung. Das Ziel: mit weniger Personal, Material, Fläche und Zeit eine höhere Qualität erreichen und flexibel auf Kundenwünsche reagieren.", [
            BANNER("Weniger Ressourcen einsetzen – höhere Qualität und mehr Flexibilität", 960, 920, w=1600, size=34)]),
    ]),
    SC([
        B("Für die betriebliche Umsetzung gibt es mehrere Möglichkeiten. Drei davon schauen wir uns genauer an.", [
            TITLE("Drei Möglichkeiten der Umsetzung", y=120, size=66)]),
        B("Erstens: bedarfsgerechte Fertigung, auch Just-in-Time genannt. Material wird genau dann geliefert und produziert, wenn es gebraucht wird. So sinken die Lagerbestände und die Kapitalbindung.", [
            CARD(450, 560, 480, 560, "pull", "Bedarfsgerechte Fertigung", "Just-in-Time: Lieferung und Produktion genau bei Bedarf – weniger Lager, weniger Kapitalbindung",
                 isize=150, tsize=32, ssize=24)]),
        B("Zweitens: der kontinuierliche Verbesserungsprozess, kurz KVP. Alle Mitarbeiter bringen Verbesserungsvorschläge ein, zum Beispiel in Qualitätszirkeln. So werden die Abläufe Schritt für Schritt besser.", [
            CARD(960, 560, 480, 560, "stairs", "Ständige Verbesserung (KVP)", "Mitarbeiter bringen Ideen ein, z. B. in Qualitätszirkeln – Abläufe werden Schritt für Schritt besser",
                 isize=150, tsize=32, ssize=24)]),
        B("Drittens: Gruppenarbeit mit flachen Hierarchien. Teams planen und kontrollieren ihre Arbeit selbst und übernehmen mehr Verantwortung. Das macht die Produktion flexibler und spart Kontrollaufwand.", [
            CARD(1470, 560, 480, 560, "people", "Gruppenarbeit", "Teams planen und kontrollieren selbst – flexibler, weniger Kontrollaufwand",
                 isize=150, tsize=32, ssize=24)]),
        B("Weitere Möglichkeiten sind das Null-Fehler-Prinzip und die Konzentration auf die eigenen Stärken durch Outsourcing.", [
            mini(700, 940, "checklist", "Null-Fehler-Prinzip", f=0.1, w=520), mini(1220, 940, "outsource", "Outsourcing", f=0.5, w=520)]),
    ], focus=True),
])

# ============================================================================ 02 Kosteneinsparung
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def month_box(label, fill, color):
    im = card_img(118, 110, fill=fill, radius=16)
    t = text_img(label, 30, color, "bold")
    paste(im, t, (im.width - t.width) / 2, (im.height - t.height) / 2)
    return im


MX = [960 + (i - 5.5) * 136 for i in range(12)]
grey_months = [Sp(month_box(m, (255, 255, 255), DARK), x, 500, "fadeup", 0, 0.05 * i, "tick" if i == 0 else None)
               for i, (m, x) in enumerate(zip(MONTHS, MX))]
hot_months = [Sp(month_box(m, ORANGE, WHITE), x, 500, "pop", 0.05, 0.12 * j, "tick")
              for j, (m, x) in enumerate(zip(MONTHS[8:], MX[8:]))]

COLX = (1290, 1600)
ROWS = [  # Symbol, Posten, Rechenweg, 2022, 2023, Sprechtext
    ("boxes", "Materialkosten", "12 % von 15.000.000 €", 600_000, 1_800_000,
     "Materialkosten: Zwölf Prozent von fünfzehn Millionen Euro sind 1,8 Millionen Euro im Jahr. Für vier Monate sind das 600.000 Euro."),
    ("nobox", "Lagerkosten", "24.000 € pro Quartal fallen weg", 32_000, 96_000,
     "Lagerkosten: 24.000 Euro pro Quartal fallen weg. Das sind 96.000 Euro im Jahr und 32.000 Euro für vier Monate."),
    ("factory", "Überproduktion", "17.500 € pro Monat", 70_000, 210_000,
     "Überproduktion: 17.500 Euro pro Monat. Das sind 70.000 Euro für vier Monate und 210.000 Euro im ganzen Jahr."),
    ("people", "Personalkosten", "Achtung: 2,75 Mio. € = Wert NACH Senkung → 2,75 Mio. € ÷ 0,9 − 2,75 Mio. €", 101_851.85, 305_555.56,
     "Achtung bei den Personalkosten: Die 2,75 Millionen Euro sind schon der Wert nach der Senkung um zehn Prozent. Vorher waren es also 2,75 Millionen geteilt durch 0,9, rund 3,06 Millionen Euro. Die Einsparung beträgt rund 305.556 Euro im Jahr und rund 101.852 Euro für vier Monate."),
    ("outsource", "Gemeinkosten", "Outsourcing: 125.000 € pro Jahr", 41_666.67, 125_000,
     "Gemeinkosten: Durch Outsourcing spart das Unternehmen 125.000 Euro im Jahr, für vier Monate rund 41.667 Euro."),
    ("warn", "Fehlerkosten", "25–30 % von 50.000 € pro Monat", (50_000, 60_000), (150_000, 180_000),
     "Und die Fehlerkosten: 50.000 Euro pro Monat sinken um 25 bis 30 Prozent. Das sind 12.500 bis 15.000 Euro pro Monat, also 50.000 bis 60.000 Euro für 2022 und 150.000 bis 180.000 Euro für 2023."),
]


def money(v):
    return f"{de(v[0], 0)} – {de(v[1], 0)} €" if isinstance(v, tuple) else f"{de(v)} €"


def row(i, icon, name, how, v22, v23):
    y = 300 + i * 100
    im = card_img(1640, 88, radius=16)
    m = k(24)
    ic = comp(F.ICONS[icon](56))
    paste(im, ic, m + k(26), m + (k(88) - ic.height) / 2)
    t = text_img(name, 28, DARK, "bold", align="left")
    paste(im, t, m + k(100), m + k(8))
    h = text_img(how, 21, ORANGE if how.startswith("Achtung") else STEEL, "semi", align="left")
    paste(im, h, m + k(100), m + k(8) + t.height - k(4))
    fk = flat_engine.new_fkey()
    out = [Sp(im, 960, y, "fadeup", 0, 0, "tick", fk)]
    big = isinstance(v22, tuple)
    out.append(TXT(money(v22), COLX[0], y, 25 if big else 29, NAVY, "bold", f=0.45, fkey=fk))
    out.append(TXT(money(v23), COLX[1], y, 25 if big else 29, NAVY, "bold", f=0.7, fkey=fk))
    return out


pers_row = None
row_beats = []
for i, (ic, name, how, v22, v23, say) in enumerate(ROWS):
    items = row(i, ic, name, how, v22, v23)
    row_beats.append(B(say, items))

clip("02_kosteneinsparung", "Kosteneinsparung", [
    SC([
        B("Jetzt wird gerechnet: Wie viel spart die GN-Glasfaser GmbH durch Lean Production in den Jahren 2022 und 2023?", [
            TITLE("Die Kosteneinsparung", "für die Jahre 2022 und 2023", y=150, size=72)]),
        B("Wichtig ist der Zeitpunkt: Die Umstellung ist erst am ersten September 2022 abgeschlossen.", [
            TXT("2022", 960, 380, 44, DARK, "xbold"), *grey_months,
            TAG("Umstellung fertig: 01.09.2022", 1390, 650, MUSTARD, DARK, rot=-3, f=0.55, size=28)]),
        B("Für 2022 zählen deshalb nur vier Monate, von September bis Dezember. Ab 2023 wirken die Einsparungen das ganze Jahr.", [
            *[ALPHA(s, 0.35, f=0.0) for s in grey_months[:8]], *hot_months,
            TXT("4 Monate", 1508, 400, 36, ORANGE, "xbold", f=0.45),
            TXT("2023: alle 12 Monate", 960, 820, 40, NAVY, "bold", f=0.75)]),
    ]),
    SC([
        B("Gehen wir die einzelnen Posten durch.", [
            TITLE("Die einzelnen Posten", y=110, size=60),
            TXT("Posten", 400, 225, 26, STEEL, "bold"), TXT("2022 (Sep–Dez)", COLX[0], 225, 26, STEEL, "bold", f=0.15),
            TXT("2023", COLX[1], 225, 26, STEEL, "bold", f=0.3)]),
    ] + row_beats, focus=True),
    SC([
        B("Zusammengerechnet ergibt sich:", [TITLE("Die gesamte Einsparung", y=130, size=68)]),
        B("Für 2022 spart das Unternehmen zwischen rund 895.500 und 905.500 Euro.", [
            Sp(card_img(1500, 210), 960, 400, "fadeup", 0, 0, "tick"),
            TXT("2022", 960, 345, 34, STEEL, "bold", d=0.2),
            Count(895_518.52, 905_518.52, 960, 420, 58, ORANGE, d=0.35)]),
        B("Für 2023 sind es zwischen rund 2,69 und 2,72 Millionen Euro, weil die Maßnahmen dann das ganze Jahr wirken.", [
            Sp(card_img(1500, 210), 960, 660, "fadeup", 0, 0, "tick"),
            TXT("2023", 960, 605, 34, STEEL, "bold", d=0.2),
            Count(2_686_555.56, 2_716_555.56, 960, 680, 58, NAVY, d=0.35)]),
        B("Die Spanne kommt von den Fehlerkosten, die um 25 bis 30 Prozent sinken.", [
            BANNER("Spanne: Fehlerkosten sinken um 25 bis 30 %", 960, 900, w=1300, size=34)]),
    ]),
])

# ============================================================================ 03 Gehaltsforderung
base = Sp(F.balance_base(240), 960, 650, "fadeup", 0.3, 0, "tick")
beam = Sp(F.balance_beam(240), 960, 554, "fadeup", 0.3, 0.1, None)
clip("03_gehaltsforderung", "Gehaltsforderung", [
    SC([
        B("Der Betriebsrat fordert bei der Umstellung auf Lean Production fünfzehn Prozent mehr Gehalt für alle Mitarbeiterinnen und Mitarbeiter.", [
            TITLE("Die Forderung des Betriebsrats", y=150, size=68),
            ICON("megaphone", 760, 560, 260, f=0.2), ICON("people", 1130, 560, 260, f=0.3),
            TAG("+15 % Gehalt", 960, 820, ORANGE, WHITE, rot=-4, f=0.55, size=44)]),
        B("Ist das berechtigt? Schauen wir uns beide Seiten an.", [], pause=0.3),
    ]),
    SC([
        B("Was spricht dafür, was dagegen?", [TITLE("Dafür und dagegen", y=120, size=66), base, beam]),
        B("Dafür spricht: Lean Production verlangt viel von den Mitarbeitern. Sie übernehmen mehr Verantwortung, arbeiten flexibler und bringen eigene Verbesserungsvorschläge ein. Außerdem steigt der Leistungsdruck. Ohne motivierte Mitarbeiter funktioniert Lean nicht.", [
            LISTCARD(420, 600, 580, 520, "people", "Dafür",
                     [("+", "mehr Verantwortung"), ("+", "mehr Flexibilität und Qualifikation"),
                      ("+", "höherer Leistungsdruck"), ("+", "Lean braucht motivierte Mitarbeiter")], step=0.22),
            ANGLE(beam, 9, f=0.2)]),
        B("Dagegen spricht: Fünfzehn Prozent sind sehr viel. Bei Personalkosten von 2,75 Millionen Euro wären das 412.500 Euro mehr pro Jahr, rund fünfzehn Prozent der gesamten Einsparung von 2023. Außerdem muss das Unternehmen gerade fünfzehn Millionen Euro in eine neue Maschine investieren, und Lean soll ja gerade Kosten senken.", [
            LISTCARD(1500, 600, 580, 520, "coin", "Dagegen",
                     [("-", "+412.500 € Personalkosten pro Jahr"), ("-", "frisst ca. 15 % der Einsparung auf"),
                      ("-", "15 Mio. € für die neue Maschine"), ("-", "Lean soll Kosten senken")], step=0.22),
            ANGLE(beam, -9, f=0.2)]),
    ]),
    SC([
        B("Mein Fazit: Eine pauschale Erhöhung um fünfzehn Prozent ist zu hoch.", [
            TITLE("Mein Fazit", y=120, size=66),
            BANNER("Pauschal +15 % ist zu hoch", 960, 260, w=900, size=40, accent=ORANGE)]),
        B("Fairer wäre eine Beteiligung am Erfolg: zum Beispiel Prämien, die sich nach den tatsächlich erreichten Einsparungen richten,", [
            CARD(450, 620, 460, 440, "trophy", "Erfolgsbeteiligung", "Prämie aus den tatsächlich erreichten Einsparungen", isize=140, tsize=33, ssize=24)]),
        B("Prämien für gute Verbesserungsvorschläge", [
            CARD(960, 620, 460, 440, "bulb", "Prämien für Ideen", "für Verbesserungsvorschläge im KVP", isize=140, tsize=33, ssize=24)], pause=0.2),
        B("und bezahlte Weiterbildungen für die neuen Aufgaben.", [
            CARD(1470, 620, 460, 440, "cap", "Weiterbildung", "Qualifizierung für die neuen Aufgaben", isize=140, tsize=33, ssize=24)]),
        B("So werden die Mitarbeiter fair beteiligt und die Einsparungen bleiben trotzdem erhalten.", [
            CHECK(960, 900, 70, NAVY, 11)]),
    ], focus=True),
])


# ============================================================================ Ausgabe
def fmt(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def idx(c):
    return [x["name"] for x in CLIPS].index(c["name"])


def build(c):
    out_dir = os.path.join(HERE, "clips")
    os.makedirs(os.path.join(out_dir, "ohne_ton"), exist_ok=True)
    voices = align_voice.prepare(idx(c), c["scenes"], flat_engine.SR)
    with tempfile.TemporaryDirectory() as tmp:
        total, audio, fx, subs = timeline(c["scenes"], tmp, voices)
        wav, wav_fx = os.path.join(tmp, "a.wav"), os.path.join(tmp, "fx.wav")
        write_wav(wav, audio)
        write_wav(wav_fx, fx)
        path = os.path.join(out_dir, c["name"] + ".mp4")
        render(c["scenes"], total, path, wav)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-i", wav_fx, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                        os.path.join(out_dir, "ohne_ton", c["name"] + ".mp4")], check=True)
    print(f"fertig: {c['name']} ({total:.0f} s)", flush=True)
    return c["name"], c["label"], total, [(b["t0"], b["sub"]) for s in c["scenes"] for b in s["beats"]]


def timing(c):
    voices = align_voice.prepare(idx(c), c["scenes"], flat_engine.SR, verbose=False)
    with tempfile.TemporaryDirectory() as tmp:
        total, _, _, _ = timeline(c["scenes"], tmp, voices)
    return c["name"], c["label"], total, [(b["t0"], b["sub"]) for s in c["scenes"] for b in s["beats"]]


def preview(c, outdir):
    with tempfile.TemporaryDirectory() as tmp:
        timeline(c["scenes"], tmp)
    for i, s in enumerate(c["scenes"]):
        for j, b in enumerate(s["beats"]):
            t = b["t0"] + b["dur"] + b["pause"] - 0.05
            draw_scene(s, t).convert("RGB").resize((1280, 720)).save(os.path.join(outdir, f"{c['name']}_{i}_{j}.png"))


def main():
    args = sys.argv[1:]
    only = args[args.index("--only") + 1] if "--only" in args else ""
    todo = [c for c in CLIPS if c["name"].startswith(only)]
    if "--preview" in args:
        d = args[args.index("--preview") + 1]
        os.makedirs(d, exist_ok=True)
        with Pool(4) as p:
            p.starmap(preview, [(c, d) for c in todo])
        return
    with Pool(3) as p:
        done = {r[0]: r for r in p.map(build, todo)}
        rest = [c for c in CLIPS if c["name"] not in done]
        done.update({r[0]: r for r in p.map(timing, rest)})
    md = ["# Sprechertext – Lernvideo GN-Glasfaser GmbH", "",
          "Für die Clips **ohne Ton** (Ordner `clips/ohne_ton`). Die Zeit vor jedem Satz zeigt, wann er im Clip beginnt –",
          "dann erscheinen auch die passenden Bilder. Kleine Abweichungen beim Tempo sind kein Problem.", ""]
    for c in CLIPS:
        name, label, total, beats = done[c["name"]]
        md += [f"## {label}  (`{name}.mp4`, ca. {fmt(total)} min)", ""]
        md += [f"**{fmt(t)}**  {s}  " for t, s in beats] + [""]
    with open(os.path.join(HERE, "SPRECHERTEXT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    lst = os.path.join(HERE, "clips", "liste.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{c['name']}.mp4'\n" for c in CLIPS)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", os.path.join(HERE, "GN_Glasfaser_Gesamtvideo.mp4")], check=True)
    os.remove(lst)


if __name__ == "__main__":
    main()
