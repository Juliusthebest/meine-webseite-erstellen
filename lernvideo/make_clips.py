"""Lernclips „Lean Production in der Praxis“ – Drehbuch.

Aufruf:
  python3 make_clips.py                 -> clips/*.mp4 (mit Stimme), clips/ohne_ton/*.mp4, SPRECHERTEXT.md
  python3 make_clips.py --preview DIR   -> Standbilder je Szene (Ende + mitten in der Animation)
  python3 make_clips.py --only 01       -> nur Clips, deren Name so beginnt
"""
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

from engine import (ARROW, B, BLUE, CARD, CHECK, CHIP, CHIPROW, CIRCLE, CROSS, E, EMPH, GREEN, INK, LIGHT_B,
                    LIGHT_G, LIGHT_R, LIGHT_Y, LINE, LOGO, MUTED, NODE, NOTE, RED, ROW, SC, T, TITLE, UNDERLINE,
                    WHITE, YELLOW, render, scene_frame, timeline, write_wav)

HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = []


def clip(name, label, scenes):
    CLIPS.append(dict(name=name, label=label, scenes=scenes))


GRID = [(530, 450), (1390, 450), (530, 760), (1390, 760)]
ACC = [BLUE, GREEN, YELLOW, RED]


def grid4(items, h=250):
    return [B(say, [CARD(x, y, 800, h, e, t, s, a)]) for (e, t, s, say), (x, y), a in zip(items, GRID, ACC)]


# ============================================================================ 00 Einführung
clip("00_einfuehrung", "Einführung", [
    SC("Einführung", [
        B("Heute schauen wir uns an, wie Lean Production in einem echten Unternehmen funktioniert.", [
            *TITLE("Lean Production in der Praxis", 300, 96),
            E("🏭", 760, 600, 170, f=0.45), E("⚙", 960, 560, 100, f=0.55), E("🙋", 1160, 600, 150, f=0.65)]),
        B("Die Idee kommt vom japanischen Autobauer Toyota.", [
            LOGO(560, 860, 150), E("🇯🇵", 790, 860, 95, f=0.3),
            CHIP("Toyota-Produktionssystem", 1240, 860, size=42, fill=LIGHT_B, f=0.45),
            CIRCLE(560, 860, 150, 100, RED, f=0.6)]),
        B("Und die Grundidee ist ganz einfach: Alles weglassen, was dem Kunden keinen Nutzen bringt.", [
            CHIP("Kein Kundennutzen  =  Verschwendung", 960, 560, "💡", 54, LIGHT_Y, padx=44, pady=24),
            NOTE("Grundidee!", 560, 410, RED, 42, f=0.45), ARROW(610, 445, 660, 500, RED, 6, f=0.6)], clear=True),
    ]),
    SC("Das Beispiel", [
        B("Unser Beispiel ist der Dübelhersteller Klaus Fischer.", [
            E("🔩", 960, 320, 180), *TITLE("Dübelhersteller Fischer", 520, 72, f=0.3)]),
        B("Sein Motto lautet: Menschen statt Roboter.", [
            E("👷", 700, 790, 170), CHECK(805, 705, 56, f=0.25),
            T("statt", 960, 790, 58, MUTED, f=0.35),
            E("🤖", 1220, 790, 170, f=0.5), CROSS(1220, 790, 200, RED, 11, f=0.72)]),
    ]),
    SC("Überblick", [
        B("In den nächsten Clips klären wir vier Fragen.", [*TITLE("Das erwartet dich", 200, 84)]),
        B("Welche Elemente gehören zu Lean? Wie setzt Fischer das um? Kosten oder Kunde? Und klappt Lean auch in der Forschung?", [
            *[x for i, (e, l) in enumerate([("🧩", "Die 5 Elemente der Lean Production"), ("🔩", "Lean in der Praxis bei Fischer"),
                                            ("⚖", "Kostenorientierung vs. Kundenorientierung"), ("🔬", "Lean in Forschung & Entwicklung")])
              for x in (T(f"{i + 1}.", 360, 380 + i * 120, 46, BLUE, f=[0, 0.25, 0.45, 0.7][i], anim="pop"),
                        ROW(e, l, 960, 380 + i * 120, 1100, 96, tsize=40, f=[0, 0.25, 0.45, 0.7][i]))]]),
    ]),
])

# ============================================================================ 01 Fünf Elemente
five = [("⏱", "Bedarfsgerechte Fertigung", "Hol-Prinzip: produziert wird erst bei Bedarf → kaum Lager, weniger Kapitalbindung",
         "Erstens: bedarfsgerechte Fertigung nach dem Hol-Prinzip. Produziert und geliefert wird erst, wenn wirklich Bedarf da ist. So gibt es kaum Lager und weniger gebundenes Kapital."),
        ("📈", "Ständige Verbesserung (KVP)", "kontinuierlicher Verbesserungsprozess → Abläufe werden immer besser",
         "Zweitens: der kontinuierliche Verbesserungsprozess, kurz KVP. Alle verbessern ständig in kleinen Schritten."),
        ("👥", "Gruppenarbeit", "Gruppen planen & kontrollieren selbst → flexibel und motiviert",
         "Drittens: Gruppenarbeit. Gruppen planen und kontrollieren ihre Arbeit selbst. Das macht flexibel und motiviert."),
        ("🛑", "Null-Fehler-Prinzip", "Fehler sofort an der Quelle beheben → weniger Ausschuss",
         "Viertens: das Null-Fehler-Prinzip. Fehler werden sofort an der Quelle behoben, statt weitergegeben. Das spart Ausschuss und Nacharbeit."),
        ("🗑", "Verschwendung vermeiden", "kein Warten, Suchen, Überproduzieren → geringere Kosten",
         "Und fünftens: Verschwendung vermeiden. Kein Warten, kein Suchen, keine Überproduktion. Das senkt die Kosten.")]
pos5 = [(330, 485), (960, 485), (1590, 485), (645, 805), (1275, 805)]
acc5 = [BLUE, GREEN, YELLOW, RED, BLUE]
clip("01_fuenf_elemente", "5 Elemente", [
    SC("5 Elemente", [
        B("Welche Elemente gehören zur Lean Production? Das große Vorbild ist Toyota. Hier sind die fünf wichtigsten Elemente, und was sie bewirken.", [
            *TITLE("Die 5 Elemente der Lean Production", 160, 76),
            T("Vorbild:", 800, 268, 40, MUTED, f=0.25), LOGO(935, 268, 62, f=0.3), T("Toyota", 1065, 268, 40, f=0.35)]),
    ] + [B(say, [CARD(x, y, 580, 280, e, t, s, a, tsize=36, ssize=28, esize=76)])
         for (e, t, s, say), (x, y), a in zip(five, pos5, acc5)], focus=True),
    SC("Auf einen Blick", [
        B("Dazu kommen noch weitere Bausteine, zum Beispiel Ordnung und Sauberkeit am Arbeitsplatz, flache Hierarchien und einheitliche Standards.", [
            *TITLE("Noch mehr Bausteine", 200, 84),
            *CHIPROW([("Ordnung am Arbeitsplatz", "🧹"), ("flache Hierarchien", "🪜"), ("einheitliche Standards", "📋")], 420, 40, f0=0.2, step=0.22)]),
        B("Insgesamt bewirken die Elemente: bessere Qualität, kürzere Durchlaufzeiten und niedrigere Kosten.", [
            E("🎯", 450, 710, 100),
            T("Qualität", 760, 710, 66, BLUE, f=0.12, anim="pop"), ARROW(935, 745, 935, 665, GREEN, 8, 0, f=0.22),
            T("Zeit", 1130, 710, 66, BLUE, f=0.42, anim="pop"), ARROW(1235, 665, 1235, 745, GREEN, 8, 0, f=0.52),
            T("Kosten", 1480, 710, 66, BLUE, f=0.72, anim="pop"), ARROW(1625, 665, 1625, 745, GREEN, 8, 0, f=0.82)]),
    ]),
])

# ============================================================================ 02 Lean bei Fischer
clip("02_lean_bei_fischer", "Lean bei Fischer", [
    SC("Lean bei Fischer", [
        B("Wie setzt Fischer Lean Production im Alltag um? Hier sind die Schwerpunkte aus dem Interview.", [
            *TITLE("Lean bei Fischer", 170, 84, emo="🔩")]),
    ] + grid4([
        ("🙋", "Kunde im Mittelpunkt", "Jeder Prozess wird vom Kunden aus gedacht: Was hat der Kunde davon?",
         "Erstens: Der Kunde steht im Mittelpunkt. Bei jedem Prozess fragt Fischer: Was hat der Kunde davon?"),
        ("🗑", "Kampf gegen Verschwendung", "Wissen, Zeit und Platz werden nicht mehr verschwendet",
         "Zweitens: der Kampf gegen Verschwendung, und zwar von Wissen, Zeit und Platz."),
        ("👷", "Menschen statt Roboter", "Menschen sind flexibler – fällt jemand aus, hilft ein Springer",
         "Drittens: Menschen statt Roboter. Menschen sind flexibler. Fällt jemand aus, springt sofort ein Kollege ein. Ein kaputter Roboter legt dagegen alles lahm."),
        ("😌", "Ruhe statt Stress", "effiziente Abläufe → 14 % mehr Aufträge ganz gelassen geschafft",
         "Viertens: Es wird ruhiger statt stressiger. Trotz vierzehn Prozent mehr Aufträgen."),
    ]), focus=True),
    SC("Lean bei Fischer", [
        B("Und es geht noch weiter.", [*TITLE("Lean bei Fischer", 170, 84, emo="🔩")]),
    ] + grid4([
        ("🔍", "Kein Suchen mehr", "gut organisierter Arbeitsplatz = schneller & bessere Qualität",
         "Fünftens: kein Suchen mehr. Ein gut organisierter Arbeitsplatz macht schneller und verbessert die Qualität."),
        ("📊", "Alles sichtbar machen", "Kennzahlen hängen für alle sichtbar aus",
         "Sechstens: Kennzahlen werden für alle sichtbar gemacht, statt im Computer zu verschwinden."),
        ("🎯", "Ziele statt Vorgaben", "nur das Ziel wird vorgegeben – den Weg finden die Mitarbeiter",
         "Siebtens: Fischer gibt nur Ziele vor. Den Weg dahin finden die Mitarbeiter selbst."),
        ("🔁", "Aus Fehlern lernen", "Fehler sind erlaubt – aber nie zweimal derselbe",
         "Und achtens: Fehler sind erlaubt, aber derselbe Fehler darf nicht zweimal passieren."),
    ]), focus=True),
])

# ============================================================================ 03 Materialfluss
clip("03_materialfluss", "Materialfluss", [
    SC("Materialfluss", [
        B("Ein besonders gutes Beispiel ist der Materialfluss im Werk.", [*TITLE("Bedarfsgerechter Materialfluss", 170, 80)]),
        B("Früher fuhren fahrerlose Transportsysteme nach einem starren Fahrplan, egal ob gerade Material gebraucht wurde.", [
            NODE("🤖", "Fahrerloses System", 520, 470, 520, 130), CROSS(800, 400, 64, RED, 9, f=0.3),
            T("starrer Fahrplan", 520, 595, 38, RED, f=0.4), E("⏰", 520, 710, 80, f=0.55)]),
        B("Fischer hat sie durch einen kleinen Zug ersetzt. Ein Werkslogistiker fährt ihn und liefert genau dann, wenn Material gebraucht wird.", [
            ARROW(820, 470, 1115, 470, GREEN, 8),
            NODE("🚂", "Zug + Logistiker", 1400, 470, 520, 130, f=0.2), CHECK(1680, 400, 54, f=0.45),
            T("liefert nach Bedarf", 1400, 595, 38, GREEN, f=0.5), E("👷", 1400, 710, 80, f=0.6)]),
    ]),
    SC("Was bringt das?", [
        B("Was bedeutet das für Kosten, Flexibilität, Kapitalbindung und Kundenzufriedenheit?", [
            *TITLE("Was bringt das?", 170, 84)]),
    ] + grid4([
        ("💶", "Kosten", "+ weniger Lager-, Such- & Stillstandskosten\n– Personalkosten, teure Umstellung",
         "Zu den Kosten: Lager-, Such- und Stillstandskosten sinken. Dafür gibt es Personalkosten, und die Umstellung war teuer."),
        ("🤸", "Flexibilität", "+ Lieferung nach Bedarf statt Fahrplan\n– abhängig von den Mitarbeitern",
         "Zur Flexibilität: Geliefert wird nach Bedarf statt nach Fahrplan. Dafür ist man von den Mitarbeitern abhängig."),
        ("🏦", "Kapitalbindung", "+ kleine Bestände → weniger gebundenes Kapital, mehr Liquidität",
         "Zur Kapitalbindung: Kleine Bestände binden weniger Kapital. Das Unternehmen bleibt liquide."),
        ("😊", "Kundenzufriedenheit", "+ kurze Lieferzeiten, hohe Termintreue, auch kleine Aufträge",
         "Und zur Kundenzufriedenheit: kurze Lieferzeiten, pünktliche Lieferung, und auch kleine Aufträge sind möglich."),
    ], h=270), focus=True),
    SC("Fazit", [
        B("Unterm Strich:", [*TITLE("Fazit", 200, 96)]),
        B("Der Materialfluss nach Bedarf senkt Kosten und macht flexibel.", [
            ROW("✅", "Chance: Kosten sinken, Flexibilität steigt", 960, 420, 1300, 110, LIGHT_G, 44)]),
        B("Aber ohne Lagerpuffer kann eine Lieferstörung schnell die Produktion stoppen.", [
            ROW("⚠", "Risiko: ohne Puffer droht Stillstand", 960, 570, 1300, 110, LIGHT_R, 44)]),
        B("Bei Fischer überwiegen klar die Vorteile.", [
            ROW("🏆", "Bei Fischer überwiegen die Vorteile", 960, 720, 1300, 110, LIGHT_Y, 44),
            CIRCLE(960, 722, 700, 88, RED, f=0.55)]),
    ]),
])

# ============================================================================ 04 Kosten vs. Kunde
left = [("✅", "große Lose → niedrige Stückkosten"), ("✅", "hohe Auslastung der Maschinen"),
        ("⚠", "hohe Lagerbestände"), ("⚠", "lange Lieferzeiten")]
right = [("✅", "Varianten nach Kundenwunsch"), ("✅", "kurze Lieferzeiten"),
         ("⚠", "2–3× täglich umrüsten"), ("⚠", "höhere Rüst- & Personalkosten")]
clip("04_kosten_vs_kunde", "Kosten vs. Kunde", [
    SC("Perspektivwechsel", [
        B("Bei Fischer gibt es einen echten Perspektivwechsel.", [*TITLE("Kosten oder Kunde?", 170, 84, emo="⚖")]),
        B("Früher musste sich der Auftrag nach der Produktion richten.", [
            CHIP("FRÜHER", 330, 450, size=40, fill=RED, color=WHITE),
            NODE("🏭", "Produktion", 820, 450, f=0.1), ARROW(1010, 450, 1210, 450, INK, 7, f=0.3),
            NODE("📝", "Auftrag", 1400, 450, f=0.42)]),
        B("Heute ist es umgekehrt: Die Produktion richtet sich nach dem Auftrag des Kunden.", [
            CHIP("HEUTE", 330, 720, size=40, fill=GREEN, color=WHITE),
            NODE("📝", "Auftrag", 820, 720, f=0.1), ARROW(1010, 720, 1210, 720, GREEN, 7, f=0.3),
            NODE("🏭", "Produktion", 1400, 720, f=0.42),
            ARROW(1640, 500, 1640, 680, RED, 6, -70, f=0.6), NOTE("umgedreht!", 1765, 590, RED, 36, f=0.7)]),
    ]),
    SC("Zwei Sichtweisen", [
        B("Schauen wir uns beide Sichtweisen an.", [
            *TITLE("Zwei Sichtweisen", 160, 80),
            CHIP("Kostenorientierung", 530, 300, "💶", 42, LIGHT_B, f=0.3),
            CHIP("Kundenorientierung", 1390, 300, "🙋", 42, LIGHT_G, f=0.5),
            LINE([(960, 270), (963, 600), (957, 950)], INK, 3, f=0.6)]),
        B("Kostenorientiert produziert man große Lose bei hoher Auslastung. Das ist günstig pro Stück, aber es entstehen große Lager und lange Lieferzeiten.",
          [ROW(e, l, 530, 420 + i * 105, f=i * 0.2) for i, (e, l) in enumerate(left)]),
        B("Kundenorientiert gibt es Varianten nach Wunsch und kurze Lieferzeiten. Dafür muss man oft umrüsten, und das kostet.",
          [ROW(e, l, 1390, 420 + i * 105, f=i * 0.2) for i, (e, l) in enumerate(right)]),
    ]),
    SC("Lösung", [
        B("Wie löst man diesen Konflikt?", [*TITLE("Wie passt das zusammen?", 170, 80)]),
        B("Erstens: Rüstzeiten verkürzen, dann lohnen sich auch kleine Mengen.", [
            CARD(330, 480, 560, 280, "⚡", "Rüstzeiten verkürzen", "Umrüsten wird schnell & billig → kleine Lose lohnen sich", YELLOW, tsize=36, ssize=28, esize=76)]),
        B("Zweitens: Zufriedene Kunden bleiben treu und zahlen auch höhere Preise.", [
            CARD(960, 480, 560, 280, "🤝", "Kundenbindung", "zufriedene Kunden bleiben und zahlen höhere Preise", GREEN, tsize=36, ssize=28, esize=76)]),
        B("Drittens: Ohne Fertigwarenlager spart man Lager- und Kapitalkosten.", [
            CARD(1590, 480, 560, 280, "📦", "Kein Fertigwarenlager", "spart Lager- und Kapitalkosten", BLUE, tsize=36, ssize=28, esize=76)]),
        B("Fazit: Kurzfristig gibt es einen Zielkonflikt. Langfristig senkt die Kundenorientierung aber auch die Kosten.", [
            CHIP("Kurzfristig Konflikt – langfristig sinken auch die Kosten", 960, 820, "💡", 44, LIGHT_Y, padx=40, pady=22),
            EMPH(300, 815, 40, RED, f=0.5)]),
    ], focus=True),
])

# ============================================================================ 05 Forschung
clip("05_lean_in_der_forschung", "Lean in der Forschung", [
    SC("Lean in der Forschung", [
        B("Zum Schluss eine spannende Frage: Funktioniert Lean auch in der Forschung und Entwicklung?", [
            *TITLE("Lean in der Forschung?", 280, 96),
            E("🔬", 700, 560, 150, f=0.35), E("🧪", 960, 560, 150, f=0.5), E("💡", 1220, 560, 150, f=0.65)]),
    ]),
    SC("Was übertragbar ist", [
        B("Vieles lässt sich übertragen.", [*TITLE("Das klappt", 170, 84, emo="✅")]),
    ] + grid4([
        ("🔀", "Parallele Entwicklung", "Schritte laufen gleichzeitig statt nacheinander → neue Produkte schneller fertig",
         "Zum Beispiel parallele Entwicklung: Die Schritte laufen gleichzeitig statt nacheinander. So ist das neue Produkt schneller fertig."),
        ("👥", "Gemischte Teams", "Entwicklung, Produktion & Vertrieb arbeiten von Anfang an zusammen",
         "Gemischte Teams: Entwicklung, Produktion und Vertrieb arbeiten von Anfang an zusammen."),
        ("🙋", "Kunde früh dabei", "nur entwickeln, was der Kunde wirklich braucht",
         "Den Kunden früh einbeziehen, damit nur entwickelt wird, was er wirklich braucht."),
        ("🗑", "Verschwendung vermeiden", "keine Doppelarbeit, keine Wartezeiten, ständig verbessern",
         "Und auch hier Verschwendung vermeiden: keine Doppelarbeit und keine Wartezeiten."),
    ]), focus=True),
    SC("Grenzen", [
        B("Es gibt aber auch Grenzen.", [*TITLE("Die Grenzen", 170, 84, emo="⚠")]),
        B("Kreativität braucht Freiraum und lässt sich nicht einfach takten oder standardisieren.", [
            CARD(530, 470, 800, 270, "🎨", "Kreativität braucht Freiraum", "Ideen lassen sich nicht takten oder standardisieren", RED, focus=False)]),
        B("Außerdem sind Ergebnisse in der Forschung unsicher. Umwege und Fehlversuche gehören dazu.", [
            CARD(1390, 470, 800, 270, "🎲", "Ergebnisse sind unsicher", "Umwege & Fehlversuche gehören zur Innovation dazu", RED, focus=False)]),
        B("Mein Fazit: Lean ist in der Entwicklung teilweise übertragbar. Die Organisation kann schlank sein, aber es muss Raum für Kreativität bleiben.", [
            CHIP("Teilweise übertragbar: schlank organisieren – Kreativität frei lassen", 960, 800, "🏁", 40, LIGHT_Y, padx=40, pady=22, anim="drop"),
            UNDERLINE(420, 1500, 862, RED, 6, f=0.6)]),
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
        wav = os.path.join(tmp, "a.wav")
        write_wav(wav, audio)
        wav_fx = os.path.join(tmp, "fx.wav")
        write_wav(wav_fx, fx)
        path = os.path.join(out_dir, c["name"] + ".mp4")
        render(c["scenes"], total, path, wav)
        # Version ohne Stimme (nur leise Effekte), zum Selbst-Einsprechen
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-i", wav_fx, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                        os.path.join(out_dir, "ohne_ton", c["name"] + ".mp4")], check=True)
    beats = [(b["t0"], b["sub"]) for s in c["scenes"] for b in s["beats"]]
    print(f"fertig: {c['name']} ({total:.0f} s)", flush=True)
    return c["name"], c["label"], total, beats


def preview(c, outdir):
    with tempfile.TemporaryDirectory() as tmp:
        timeline(c["scenes"], tmp)
    for i, s in enumerate(c["scenes"]):
        scene_frame(s, s["end"] - 0.01).convert("RGB").resize((1280, 720)).save(os.path.join(outdir, f"{c['name']}_{i}_end.png"))
        b = s["beats"][min(1, len(s["beats"]) - 1)]
        scene_frame(s, b["t0"] + 0.25).convert("RGB").resize((1280, 720)).save(os.path.join(outdir, f"{c['name']}_{i}_mid.png"))
    return c["name"]


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
