"""Lernclips „Lean Production in der Praxis“ – Drehbuch im Flat-Design-Stil.

Aufruf:
  python3 make_clips.py                 -> clips/*.mp4 (mit Stimme), clips/ohne_ton/*.mp4, SPRECHERTEXT.md
  python3 make_clips.py --preview DIR   -> Standbilder je Szene
  python3 make_clips.py --only 01       -> nur Clips, deren Name so beginnt
"""
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

from PIL import Image

import flat_icons as F
from flat_engine import (ALPHA, ANGLE, ARROW, B, BANNER, CARD, CHECK, CROSS, DARK, FLOOR_BAND, ICON, LISTCARD, MOVE,
                         MUSTARD, NAVY, NODE, ORANGE, PULSE, SC, STEEL, STOP, TAG, TITLE, TXT, VEHICLE, WHITE, Conveyor,
                         Sp, card_img, comp, draw_scene, k, paste, render, text_img, timeline, write_wav)

HERE = os.path.dirname(os.path.abspath(__file__))
_logo = Image.open(os.path.join(HERE, "assets", "toyota_logo.png")).convert("RGBA")


def LOGO(x, y, h, f=0.0, d=0.0, enter="zoom"):
    hh = k(h)
    return Sp(_logo.resize((round(_logo.width * hh / _logo.height), hh), Image.LANCZOS), x, y, enter, f, d, "tick")


def every(sprites, fn, *a, **kw):
    return [fn(s, *a, **kw) for s in sprites]


def mini(x, y, icon, label, f=0.0):
    """Kleine Ergebniskarte: Symbol links, Text rechts."""
    out = [Sp(card_img(380, 130), x, y, "fadeup", f, 0, "tick")]
    out += ICON(icon, x - 120, y, 70, f, 0.15)
    out.append(TXT(label, x + 40, y, 36, DARK, "bold", f=f, d=0.25))
    return out


CLIPS = []


def clip(name, label, scenes):
    CLIPS.append(dict(name=name, label=label, scenes=scenes))


X4 = [300, 740, 1180, 1620]
X5 = [260, 610, 960, 1310, 1660]

# ============================================================================ 00 Einführung
conv = Conveyor(790, f=0.15)
dowels = [Sp(comp(F.dowel(180)), x, 725, "slide_l", 0, 0.8 + i * 0.55, "whoosh") for i, x in enumerate((330, 750, 1170, 1590))]
car = VEHICLE("car", 960, 734, 320)
robot = ICON("robot", 1280, 680, 360, f=0.3)
clip("00_einfuehrung", "Einführung", [
    SC([
        B("Heute schauen wir uns an, wie Lean Production in einem echten Unternehmen funktioniert.", [
            TITLE("Lean Production in der Praxis", "Am Beispiel des Dübelherstellers Fischer", y=230, size=80),
            conv, *dowels, STOP(conv, d=0.8 + 3 * 0.55 + 1.6)]),
        B("Die Idee kommt vom japanischen Autobauer Toyota.", [
            FLOOR_BAND(), car, LOGO(960, 300, 170, f=0.35), ICON("flag_jp", 1270, 300, 130, f=0.5),
            TXT("Toyota-Produktionssystem", 960, 460, 42, STEEL, "bold", f=0.6)], clear=True),
        B("Und die Grundidee ist ganz einfach: Alles weglassen, was dem Kunden keinen Nutzen bringt.", [
            TXT("Die Grundidee", 960, 170, 64, DARK, "xbold"),
            CARD(700, 580, 440, 420, "smiley", "Kundennutzen", "behalten", f=0.1, tsize=38, ssize=30, isize=170),
            CHECK(860, 420, 70, f=0.35),
            CARD(1220, 580, 440, 420, "bin", "Verschwendung", "weglassen", f=0.5, tsize=38, ssize=30, isize=170),
            CROSS(1380, 420, 60, f=0.8)], clear=True),
    ]),
    SC([
        B("Unser Beispiel ist der Dübelhersteller Klaus Fischer.", [
            ICON("dowel", 960, 400, 360), TXT("Dübelhersteller Fischer", 960, 650, 70, DARK, "xbold", f=0.3),
            TXT("unser Beispiel aus der Praxis", 960, 735, 36, STEEL, "semi", f=0.45)]),
        B("Sein Motto lautet: Menschen statt Roboter.", [
            FLOOR_BAND(), TXT("Menschen statt Roboter", 960, 190, 64, DARK, "xbold"),
            ICON("worker", 640, 680, 360), robot, TXT("statt", 960, 680, 48, STEEL, "bold", f=0.25),
            CHECK(830, 470, 90, f=0.4), *every(robot, ALPHA, 0.35, f=0.75), CROSS(1280, 680, 200, f=0.75)], clear=True),
    ]),
    SC([
        B("In den nächsten Clips klären wir vier Fragen.", [TITLE("Das erwartet dich", y=150, size=70)]),
        B("Welche Elemente gehören zu Lean? Wie setzt Fischer das um? Kosten oder Kunde? Und klappt Lean auch in der Forschung?", [
            CARD(330, 600, 380, 420, "boxes", "5 Elemente", "der Lean Production", f=0.0, tsize=33, ssize=24),
            CARD(750, 600, 380, 420, "dowel", "Lean bei Fischer", "Erfahrungen aus der Praxis", f=0.25, isize=110, tsize=33, ssize=24),
            CARD(1170, 600, 380, 420, "balance", "Kosten vs. Kunde", "zwei Sichtweisen", f=0.45, tsize=33, ssize=24),
            CARD(1590, 600, 380, 420, "flask", "Forschung", "Lean in der Entwicklung", f=0.7, tsize=33, ssize=24)]),
    ]),
])

# ============================================================================ 01 Fünf Elemente
five = [("pull", "Bedarfsgerechte Fertigung", "Hol-Prinzip: erst bei Bedarf produzieren",
         "Erstens: bedarfsgerechte Fertigung nach dem Hol-Prinzip. Produziert und geliefert wird erst, wenn wirklich Bedarf da ist. So gibt es kaum Lager und weniger gebundenes Kapital."),
        ("stairs", "Ständige Verbesserung (KVP)", "viele kleine Schritte, Abläufe immer besser",
         "Zweitens: der kontinuierliche Verbesserungsprozess, kurz KVP. Alle verbessern ständig in kleinen Schritten."),
        ("people", "Gruppenarbeit", "Gruppen planen und kontrollieren selbst",
         "Drittens: Gruppenarbeit. Gruppen planen und kontrollieren ihre Arbeit selbst. Das macht flexibel und motiviert."),
        ("checklist", "Null-Fehler-Prinzip", "Fehler sofort an der Quelle beheben",
         "Viertens: das Null-Fehler-Prinzip. Fehler werden sofort an der Quelle behoben, statt weitergegeben. Das spart Ausschuss und Nacharbeit."),
        ("bin", "Verschwendung vermeiden", "kein Warten, Suchen oder Überproduzieren",
         "Und fünftens: Verschwendung vermeiden. Kein Warten, kein Suchen, keine Überproduktion. Das senkt die Kosten.")]
clip("01_fuenf_elemente", "5 Elemente", [
    SC([
        B("Welche Elemente gehören zur Lean Production? Das große Vorbild ist Toyota. Hier sind die fünf wichtigsten Elemente, und was sie bewirken.", [
            TITLE("Die 5 Elemente der Lean Production", y=120, size=62),
            TXT("Vorbild:", 822, 218, 36, STEEL, "semi", f=0.3), LOGO(942, 218, 60, f=0.35),
            TXT("Toyota", 1055, 218, 36, DARK, "bold", f=0.4)]),
    ] + [B(say, [CARD(x, 620, 320, 470, ic, t, s, tsize=29, ssize=22, isize=125)]) for (ic, t, s, say), x in zip(five, X5)],
       focus=True),
    SC([
        B("Dazu kommen noch weitere Bausteine, zum Beispiel Ordnung und Sauberkeit am Arbeitsplatz, flache Hierarchien und einheitliche Standards.", [
            TITLE("Noch mehr Bausteine", y=120, size=66),
            CARD(470, 440, 420, 380, "toolboard", "Ordnung am Arbeitsplatz", None, f=0.25, isize=130),
            CARD(960, 440, 420, 380, "orgchart", "Flache Hierarchien", None, f=0.45, isize=130),
            CARD(1450, 440, 420, 380, "clipboard", "Einheitliche Standards", None, f=0.65, isize=130)]),
        B("Insgesamt bewirken die Elemente: bessere Qualität, kürzere Durchlaufzeiten und niedrigere Kosten.", [
            mini(520, 830, "arrow_up", "Qualität", f=0.1), mini(960, 830, "arrow_down", "Zeit", f=0.4),
            mini(1400, 830, "arrow_down", "Kosten", f=0.7)]),
    ]),
])

# ============================================================================ 02 Lean bei Fischer
def fischer_scene(intro, items, extra=()):
    beats = [B(intro, [TITLE("Lean bei Fischer", y=120, size=66), ICON("dowel", 1375, 120, 80, f=0.3)])]
    for (ic, t, s, say), x in zip(items, X4):
        beats.append(B(say, [CARD(x, 600, 400, 470, ic, t, s, isize=150, tsize=32, ssize=24)]))
    beats[-1]["add"] += list(extra)
    return SC(beats, focus=True)


clip("02_lean_bei_fischer", "Lean bei Fischer", [
    fischer_scene("Wie setzt Fischer Lean Production im Alltag um? Hier sind die Schwerpunkte aus dem Interview.", [
        ("customer", "Kunde im Mittelpunkt", "Jeder Prozess wird vom Kunden aus gedacht: Was hat der Kunde davon?",
         "Erstens: Der Kunde steht im Mittelpunkt. Bei jedem Prozess fragt Fischer: Was hat der Kunde davon?"),
        ("bin", "Kampf gegen Verschwendung", "Wissen, Zeit und Platz werden nicht verschwendet",
         "Zweitens: der Kampf gegen Verschwendung, und zwar von Wissen, Zeit und Platz."),
        ("worker", "Menschen statt Roboter", "Menschen sind flexibler – bei Ausfall hilft ein Springer",
         "Drittens: Menschen statt Roboter. Menschen sind flexibler. Fällt jemand aus, springt sofort ein Kollege ein. Ein kaputter Roboter legt dagegen alles lahm."),
        ("calm", "Ruhe statt Stress", "effiziente Abläufe machen den Betrieb gelassener",
         "Viertens: Es wird ruhiger statt stressiger. Trotz vierzehn Prozent mehr Aufträgen."),
    ], extra=[TAG("+14 % Aufträge", 1700, 380, MUSTARD, DARK, rot=-7, f=0.55, size=30)]),
    fischer_scene("Und es geht noch weiter.", [
        ("magnifier", "Kein Suchen mehr", "gut organisierter Arbeitsplatz: schneller und bessere Qualität",
         "Fünftens: kein Suchen mehr. Ein gut organisierter Arbeitsplatz macht schneller und verbessert die Qualität."),
        ("chart", "Alles sichtbar machen", "Kennzahlen hängen für alle sichtbar aus",
         "Sechstens: Kennzahlen werden für alle sichtbar gemacht, statt im Computer zu verschwinden."),
        ("target", "Ziele statt Vorgaben", "nur das Ziel ist vorgegeben – den Weg finden die Mitarbeiter",
         "Siebtens: Fischer gibt nur Ziele vor. Den Weg dahin finden die Mitarbeiter selbst."),
        ("loop", "Aus Fehlern lernen", "Fehler sind erlaubt – aber nie zweimal derselbe",
         "Und achtens: Fehler sind erlaubt, aber derselbe Fehler darf nicht zweimal passieren."),
    ]),
])

# ============================================================================ 03 Materialfluss
agv = VEHICLE("agv", 520, 749, 300, enter="slide_l")
clock_ic = ICON("clock", 520, 440, 140, f=0.35)
fazit3 = CARD(1470, 560, 460, 420, "trophy", "Ergebnis", "bei Fischer überwiegen die Vorteile", tsize=36, ssize=26)
clip("03_materialfluss", "Materialfluss", [
    SC([
        B("Ein besonders gutes Beispiel ist der Materialfluss im Werk.", [
            TITLE("Bedarfsgerechter Materialfluss", "Wie kommt das Material an den Arbeitsplatz?", y=130, size=64), FLOOR_BAND(f=0.3)]),
        B("Früher fuhren fahrerlose Transportsysteme nach einem starren Fahrplan, egal ob gerade Material gebraucht wurde.", [
            agv, clock_ic, TXT("starrer Fahrplan", 520, 560, 40, ORANGE, "bold", f=0.45),
            ALPHA(agv, 0.35, f=0.85), *every(clock_ic, ALPHA, 0.35, f=0.85), CROSS(520, 749, 180, f=0.85)]),
        B("Fischer hat sie durch einen kleinen Zug ersetzt. Ein Werkslogistiker fährt ihn und liefert genau dann, wenn Material gebraucht wird.", [
            VEHICLE("train", 1380, 708, 330), TXT("liefert nach Bedarf", 1380, 470, 40, NAVY, "bold", f=0.55),
            CHECK(1380, 390, 80, f=0.65)]),
    ]),
    SC([
        B("Was bedeutet das für Kosten, Flexibilität, Kapitalbindung und Kundenzufriedenheit?", [
            TITLE("Was bringt das?", y=120, size=66)]),
        B("Zu den Kosten: Lager-, Such- und Stillstandskosten sinken. Dafür gibt es Personalkosten, und die Umstellung war teuer.", [
            CARD(X4[0], 600, 400, 470, "coin", "Kosten", "+ weniger Lager-, Such- und Stillstandskosten\n– Personal, teure Umstellung", isize=150, tsize=32, ssize=24)]),
        B("Zur Flexibilität: Geliefert wird nach Bedarf statt nach Fahrplan. Dafür ist man von den Mitarbeitern abhängig.", [
            CARD(X4[1], 600, 400, 470, "arrows4", "Flexibilität", "+ Lieferung nach Bedarf\n– abhängig von Mitarbeitern", isize=150, tsize=32, ssize=24)]),
        B("Zur Kapitalbindung: Kleine Bestände binden weniger Kapital. Das Unternehmen bleibt liquide.", [
            CARD(X4[2], 600, 400, 470, "bank", "Kapitalbindung", "+ kleine Bestände, weniger gebundenes Kapital", isize=150, tsize=32, ssize=24)]),
        B("Und zur Kundenzufriedenheit: kurze Lieferzeiten, pünktliche Lieferung, und auch kleine Aufträge sind möglich.", [
            CARD(X4[3], 600, 400, 470, "smiley", "Kunden", "+ kurze Lieferzeiten, termintreu, auch kleine Aufträge", isize=150, tsize=32, ssize=24)]),
    ], focus=True),
    SC([
        B("Unterm Strich:", [TITLE("Fazit", y=130, size=72)]),
        B("Der Materialfluss nach Bedarf senkt Kosten und macht flexibel.", [
            CARD(450, 560, 460, 420, "arrow_up", "Chance", "Kosten sinken, Flexibilität steigt", tsize=36, ssize=26)]),
        B("Aber ohne Lagerpuffer kann eine Lieferstörung schnell die Produktion stoppen.", [
            CARD(960, 560, 460, 420, "warn", "Risiko", "ohne Lagerpuffer droht Stillstand", tsize=36, ssize=26)]),
        B("Bei Fischer überwiegen klar die Vorteile.", [
            fazit3, *every(fazit3, PULSE, f=0.6), TAG("Vorteile!", 1640, 345, MUSTARD, DARK, rot=-8, f=0.55)]),
    ], focus=True),
])

# ============================================================================ 04 Kosten vs. Kunde
node_p = NODE("factory", "Produktion", 620, 620, f=0.1)
node_a = NODE("document", "Auftrag", 1300, 620, f=0.45)
tag_f = TAG("FRÜHER", 960, 330, ORANGE, WHITE, rot=-4)
base = Sp(F.balance_base(260), 960, 650, "fadeup", 0.3, 0, "tick")
beam = Sp(F.balance_beam(260), 960, 546, "fadeup", 0.3, 0.1, None)
clip("04_kosten_vs_kunde", "Kosten vs. Kunde", [
    SC([
        B("Bei Fischer gibt es einen echten Perspektivwechsel.", [
            TITLE("Kosten oder Kunde?", "Ein Perspektivwechsel", y=130, size=68)]),
        B("Früher musste sich der Auftrag nach der Produktion richten.", [
            tag_f, node_p, ARROW(800, 620, 1110, 620, f=0.3), node_a]),
        B("Heute ist es umgekehrt: Die Produktion richtet sich nach dem Auftrag des Kunden.", [
            ALPHA(tag_f, 0.0, dur=0.3), TAG("HEUTE", 960, 330, NAVY, WHITE, rot=-4, f=0.12),
            MOVE(node_p, 1300, 620, f=0.2, dur=1.1, arc=-120), MOVE(node_a, 620, 620, f=0.2, dur=1.1, arc=120),
            ICON("customer", 300, 620, 160, f=0.6), TXT("Kunde", 300, 735, 28, DARK, "bold", f=0.65),
            ARROW(390, 620, 455, 620, f=0.7, dur=0.3)]),
    ]),
    SC([
        B("Schauen wir uns beide Sichtweisen an.", [TITLE("Zwei Sichtweisen", y=120, size=66), base, beam]),
        B("Kostenorientiert produziert man große Lose bei hoher Auslastung. Das ist günstig pro Stück, aber es entstehen große Lager und lange Lieferzeiten.", [
            LISTCARD(420, 600, 560, 500, "coin", "Kostenorientierung",
                     [("+", "große Lose, niedrige Stückkosten"), ("+", "hohe Auslastung"), ("-", "hohe Lagerbestände"), ("-", "lange Lieferzeiten")]),
            ANGLE(beam, 9, f=0.15)]),
        B("Kundenorientiert gibt es Varianten nach Wunsch und kurze Lieferzeiten. Dafür muss man oft umrüsten, und das kostet.", [
            LISTCARD(1500, 600, 560, 500, "customer", "Kundenorientierung",
                     [("+", "Varianten nach Wunsch"), ("+", "kurze Lieferzeiten"), ("-", "2–3× täglich umrüsten"), ("-", "höhere Rüst- und Personalkosten")]),
            ANGLE(beam, -9, f=0.15), ANGLE(beam, 0, f=0.85)]),
    ]),
    SC([
        B("Wie löst man diesen Konflikt?", [TITLE("Wie passt das zusammen?", y=120, size=66)]),
        B("Erstens: Rüstzeiten verkürzen, dann lohnen sich auch kleine Mengen.", [
            CARD(450, 490, 440, 420, "bolt", "Rüstzeiten verkürzen", "dann lohnen sich auch kleine Mengen", isize=140, tsize=33, ssize=24)]),
        B("Zweitens: Zufriedene Kunden bleiben treu und zahlen auch höhere Preise.", [
            CARD(960, 490, 440, 420, "magnet", "Kundenbindung", "Kunden bleiben treu und zahlen mehr", isize=140, tsize=33, ssize=24)]),
        B("Drittens: Ohne Fertigwarenlager spart man Lager- und Kapitalkosten.", [
            CARD(1470, 490, 440, 420, "nobox", "Kein Fertigwarenlager", "spart Lager- und Kapitalkosten", isize=140, tsize=33, ssize=24)]),
        B("Fazit: Kurzfristig gibt es einen Zielkonflikt. Langfristig senkt die Kundenorientierung aber auch die Kosten.", [
            BANNER("Kurzfristig ein Zielkonflikt – langfristig sinken auch die Kosten", 960, 880)]),
    ], focus=True),
])

# ============================================================================ 05 Forschung
clip("05_lean_in_der_forschung", "Lean in der Forschung", [
    SC([
        B("Zum Schluss eine spannende Frage: Funktioniert Lean auch in der Forschung und Entwicklung?", [
            TITLE("Lean in der Forschung?", "Forschung & Entwicklung", y=250, size=82),
            ICON("flask", 680, 620, 190, f=0.35), ICON("bulb", 960, 620, 190, f=0.5), ICON("gear", 1240, 620, 190, f=0.65)]),
    ]),
    SC([
        B("Vieles lässt sich übertragen.", [TITLE("Das klappt", y=120, size=66), CHECK(1165, 115, 54, f=0.4)]),
        B("Zum Beispiel parallele Entwicklung: Die Schritte laufen gleichzeitig statt nacheinander. So ist das neue Produkt schneller fertig.", [
            CARD(X4[0], 600, 400, 470, "parallel", "Parallele Entwicklung", "Schritte laufen gleichzeitig – schneller fertig", isize=150, tsize=32, ssize=24)]),
        B("Gemischte Teams: Entwicklung, Produktion und Vertrieb arbeiten von Anfang an zusammen.", [
            CARD(X4[1], 600, 400, 470, "people", "Gemischte Teams", "Entwicklung, Produktion und Vertrieb gemeinsam", isize=150, tsize=32, ssize=24)]),
        B("Den Kunden früh einbeziehen, damit nur entwickelt wird, was er wirklich braucht.", [
            CARD(X4[2], 600, 400, 470, "customer", "Kunde früh dabei", "nur entwickeln, was wirklich gebraucht wird", isize=150, tsize=32, ssize=24)]),
        B("Und auch hier Verschwendung vermeiden: keine Doppelarbeit und keine Wartezeiten.", [
            CARD(X4[3], 600, 400, 470, "bin", "Keine Verschwendung", "keine Doppelarbeit, keine Wartezeiten", isize=150, tsize=32, ssize=24)]),
    ], focus=True),
    SC([
        B("Es gibt aber auch Grenzen.", [TITLE("Die Grenzen", y=120, size=66)]),
        B("Kreativität braucht Freiraum und lässt sich nicht einfach takten oder standardisieren.", [
            CARD(640, 470, 560, 420, "bulb", "Kreativität braucht Freiraum", "lässt sich nicht takten oder standardisieren", isize=150, tsize=32, ssize=24)]),
        B("Außerdem sind Ergebnisse in der Forschung unsicher. Umwege und Fehlversuche gehören dazu.", [
            CARD(1280, 470, 560, 420, "dice", "Ergebnisse sind unsicher", "Umwege und Fehlversuche gehören dazu", isize=150, tsize=32, ssize=24)]),
        B("Mein Fazit: Lean ist in der Entwicklung teilweise übertragbar. Die Organisation kann schlank sein, aber es muss Raum für Kreativität bleiben.", [
            BANNER("Teilweise übertragbar: schlank organisieren – Raum für Kreativität lassen", 960, 860)]),
    ]),
])


# ============================================================================ Ausgabe
def fmt(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def build(c):
    out_dir = os.path.join(HERE, "clips")
    os.makedirs(os.path.join(out_dir, "ohne_ton"), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        total, audio, fx, subs = timeline(c["scenes"], tmp)
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
        results = p.map(build, todo)
    if only:
        return
    md = ["# Sprechertext – Lernclips Lean Production", "",
          "Für die Clips **ohne Ton** (Ordner `clips/ohne_ton`). Die Zeit vor jedem Satz zeigt, wann er im Clip beginnt –",
          "dann erscheinen auch die passenden Bilder. Kleine Abweichungen beim Tempo sind kein Problem.", ""]
    for name, label, total, beats in results:
        md += [f"## {label}  (`{name}.mp4`, ca. {fmt(total)} min)", ""]
        md += [f"**{fmt(t)}**  {s}  " for t, s in beats] + [""]
    with open(os.path.join(HERE, "SPRECHERTEXT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
