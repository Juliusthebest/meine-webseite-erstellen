"""Kurze Lernclips zu Lean Production (Fischer-Interview) im Erklärvideo-Stil.

Nutzt die Bausteine aus erklaervideo/make_video.py.
Aufruf: python3 make_clips.py            -> clips/*.mp4, clips/ohne_ton/*.mp4, SPRECHERTEXT.md
        python3 make_clips.py --preview DIR  -> Standbilder je Szene
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "erklaervideo"))
import make_video as m  # noqa: E402

m.HAND = True  # handgemachter Look: Handschrift, wackelige Linien, weißer Hintergrund
m.SAY.append(("KVP", "Ka Fau Pe"))
from make_video import (B, S, BLUE, GREEN, RED, YELLOW, INK, MUTED, WHITE, LIGHT_B, LIGHT_G,  # noqa: E402
                        LIGHT_R, LIGHT_Y, arrow, card, chip, chip_row, emoji, list_row, node, text, title,
                        title_hl)

CLIPS = []
_LOGO = None


def toyota(height):
    """Toyota-Logo (assets/toyota_logo.png) in gewünschter Höhe."""
    global _LOGO
    from PIL import Image
    if _LOGO is None:
        _LOGO = Image.open(os.path.join(HERE, "assets", "toyota_logo.png")).convert("RGBA")
    return _LOGO.resize((int(_LOGO.width * height / _LOGO.height), height), Image.LANCZOS)


def clip(name, label, scenes):
    CLIPS.append(dict(name=name, label=label, scenes=scenes))


def sc(label, beats):
    return dict(label=label, beats=beats)


def title_emo(s, emo, y=170, size=84):
    w = text(s, size, INK, "ExtraBold").width
    return [*title_hl(s, y, size), S(emoji(emo, int(size * 0.9)), 960 + w / 2 + 40 + size * 0.45, y, f=0.3)]


def grid4(items, accent_list=None, w=800, h=250):
    """2x2-Karten: items = [(emoji, titel, text, sprechtext)] -> Beats."""
    pos = [(530, 450), (1390, 450), (530, 760), (1390, 760)]
    acc = accent_list or [BLUE, GREEN, YELLOW, RED]
    return [B(say, [S(card(w, h, e, t, s, accent=a), x, y)])
            for (e, t, s, say), (x, y), a in zip(items, pos, acc)]


# --------------------------------------------------------------------------- 00 Einführung
clip("00_einfuehrung", "Einführung", [
    sc("Einführung", [
        B("Heute schauen wir uns an, wie Lean Production in einem echten Unternehmen funktioniert.", [
            *title_hl("Lean Production in der Praxis", 300, 96),
            S(emoji("🏭", 190), 760, 600, f=0.4), S(emoji("⚙", 120), 960, 560, f=0.55),
            S(emoji("🙋", 170), 1160, 600, f=0.7)]),
        B("Die Idee kommt vom japanischen Autobauer Toyota.", [
            S(toyota(150), 560, 860), S(emoji("🇯🇵", 100), 790, 860, f=0.3),
            S(chip("Toyota-Produktionssystem", None, 42, fill=LIGHT_B), 1240, 860, f=0.5)]),
        B("Und die Grundidee ist ganz einfach: Alles weglassen, was dem Kunden keinen Nutzen bringt.", [
            S(chip("Kein Kundennutzen  =  Verschwendung", "💡", 52, fill=LIGHT_Y, padx=46, pady=26), 960, 520)],
          clear=True),
    ]),
    sc("Das Beispiel", [
        B("Unser Beispiel ist der Dübelhersteller Klaus Fischer.", [
            S(emoji("🔩", 200), 960, 330), S(text("Dübelhersteller Fischer", 72, INK, "ExtraBold"), 960, 520, "rise", f=0.3)]),
        B("Sein Motto lautet: Menschen statt Roboter.", [
            S(emoji("👷", 170), 700, 760), S(emoji("✅", 70), 790, 690, f=0.2),
            S(text("statt", 56, MUTED, "ExtraBold"), 960, 760, f=0.35),
            S(emoji("🤖", 170), 1220, 760, f=0.5), S(emoji("❌", 70), 1310, 690, f=0.7)]),
    ]),
    sc("Überblick", [
        B("In den nächsten Clips klären wir vier Fragen.", [*title_hl("Das erwartet dich", 200, 84)]),
        B("Welche Elemente gehören zu Lean? Wie setzt Fischer das um? Kosten oder Kunde? Und klappt Lean auch in der Forschung?", [
            S(list_row("🧩", "Die 5 Elemente der Lean Production", 1100, 96, tsize=40), 960, 380, "rise", f=0.0),
            S(list_row("🔩", "Lean in der Praxis bei Fischer", 1100, 96, tsize=40), 960, 500, "rise", f=0.25),
            S(list_row("⚖", "Kostenorientierung vs. Kundenorientierung", 1100, 96, tsize=40), 960, 620, "rise", f=0.45),
            S(list_row("🔬", "Lean in Forschung & Entwicklung", 1100, 96, tsize=40), 960, 740, "rise", f=0.7)]),
    ]),
])

# --------------------------------------------------------------------------- 01 Fünf Elemente
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
pos5 = [(330, 480), (960, 480), (1590, 480), (645, 800), (1275, 800)]
acc5 = [BLUE, GREEN, YELLOW, RED, BLUE]
clip("01_fuenf_elemente", "5 Elemente", [
    sc("5 Elemente", [
        B("Welche Elemente gehören zur Lean Production? Das große Vorbild ist Toyota. Hier sind die fünf wichtigsten Elemente, und was sie bewirken.", [
            *title_hl("Die 5 Elemente der Lean Production", 160, 76),
            S(text("Vorbild:", 40, MUTED), 800, 268, "rise", f=0.25), S(toyota(62), 935, 268, f=0.3),
            S(text("Toyota", 40, INK), 1065, 268, "rise", f=0.35)]),
    ] + [B(say, [S(card(580, 280, e, t, s, accent=a, tsize=36, ssize=28, esize=78), x, y)])
         for (e, t, s, say), (x, y), a in zip(five, pos5, acc5)]),
    sc("Auf einen Blick", [
        B("Dazu kommen noch weitere Bausteine, zum Beispiel Ordnung und Sauberkeit am Arbeitsplatz, flache Hierarchien und einheitliche Standards.", [
            *title_hl("Noch mehr Bausteine", 200, 84),
            *chip_row([("Ordnung am Arbeitsplatz", "🧹"), ("flache Hierarchien", "🪜"), ("einheitliche Standards", "📋")], 420, 40)]),
        B("Insgesamt bewirken die Elemente: bessere Qualität, kürzere Durchlaufzeiten und niedrigere Kosten.", [
            S(emoji("🎯", 100), 470, 700),
            S(text("Qualität ↑     Zeit ↓     Kosten ↓", 64, BLUE, "ExtraBold"), 1010, 700, "rise", f=0.2)]),
    ]),
])

# --------------------------------------------------------------------------- 02 Fischer: Schwerpunkte
clip("02_lean_bei_fischer", "Lean bei Fischer", [
    sc("Lean bei Fischer", [
        B("Wie setzt Fischer Lean Production im Alltag um? Hier sind die Schwerpunkte aus dem Interview.", [
            *title_emo("Lean bei Fischer", "🔩", 170, 84)]),
    ] + grid4([
        ("🙋", "Kunde im Mittelpunkt", "Jeder Prozess wird vom Kunden aus gedacht: Was hat der Kunde davon?",
         "Erstens: Der Kunde steht im Mittelpunkt. Bei jedem Prozess fragt Fischer: Was hat der Kunde davon?"),
        ("🗑", "Kampf gegen Verschwendung", "Wissen, Zeit und Platz werden nicht mehr verschwendet",
         "Zweitens: der Kampf gegen Verschwendung, und zwar von Wissen, Zeit und Platz."),
        ("👷", "Menschen statt Roboter", "Menschen sind flexibler – fällt jemand aus, hilft ein Springer",
         "Drittens: Menschen statt Roboter. Menschen sind flexibler. Fällt jemand aus, springt sofort ein Kollege ein. Ein kaputter Roboter legt dagegen alles lahm."),
        ("😌", "Ruhe statt Stress", "effiziente Abläufe → 14 % mehr Aufträge ganz gelassen geschafft",
         "Viertens: Es wird ruhiger statt stressiger. Trotz vierzehn Prozent mehr Aufträgen."),
    ])),
    sc("Lean bei Fischer", [
        B("Und es geht noch weiter.", [*title_emo("Lean bei Fischer", "🔩", 170, 84)]),
    ] + grid4([
        ("🔍", "Kein Suchen mehr", "gut organisierter Arbeitsplatz = schneller & bessere Qualität",
         "Fünftens: kein Suchen mehr. Ein gut organisierter Arbeitsplatz macht schneller und verbessert die Qualität."),
        ("📊", "Alles sichtbar machen", "Kennzahlen hängen für alle sichtbar aus",
         "Sechstens: Kennzahlen werden für alle sichtbar gemacht, statt im Computer zu verschwinden."),
        ("🎯", "Ziele statt Vorgaben", "nur das Ziel wird vorgegeben – den Weg finden die Mitarbeiter",
         "Siebtens: Fischer gibt nur Ziele vor. Den Weg dahin finden die Mitarbeiter selbst."),
        ("🔁", "Aus Fehlern lernen", "Fehler sind erlaubt – aber nie zweimal derselbe",
         "Und achtens: Fehler sind erlaubt, aber derselbe Fehler darf nicht zweimal passieren."),
    ])),
])

# --------------------------------------------------------------------------- 03 Materialfluss
clip("03_materialfluss", "Materialfluss", [
    sc("Materialfluss", [
        B("Ein besonders gutes Beispiel ist der Materialfluss im Werk.", [*title_hl("Bedarfsgerechter Materialfluss", 170, 80)]),
        B("Früher fuhren fahrerlose Transportsysteme nach einem starren Fahrplan, egal ob gerade Material gebraucht wurde.", [
            S(node("🤖", "Fahrerloses System", 520, 130), 520, 470), S(emoji("❌", 80), 790, 400, f=0.3),
            S(text("starrer Fahrplan", 36, RED, "Bold"), 520, 590, "rise", f=0.4),
            S(emoji("⏰", 80), 520, 700, f=0.55)]),
        B("Fischer hat sie durch einen kleinen Zug ersetzt. Ein Werkslogistiker fährt ihn und liefert genau dann, wenn Material gebraucht wird.", [
            S(arrow(260, GREEN), 960, 470, "wipe"),
            S(node("🚂", "Zug + Logistiker", 520, 130), 1400, 470, f=0.2), S(emoji("✅", 80), 1670, 400, f=0.45),
            S(text("liefert nach Bedarf", 36, GREEN, "Bold"), 1400, 590, "rise", f=0.5),
            S(emoji("👷", 80), 1400, 700, f=0.6)]),
    ]),
    sc("Was bringt das?", [
        B("Was bedeutet das für Kosten, Flexibilität, Kapitalbindung und Kundenzufriedenheit?", [
            *title_hl("Was bringt das?", 170, 84)]),
    ] + grid4([
        ("💶", "Kosten", "+ weniger Lager-, Such- & Stillstandskosten\n– Personalkosten, teure Umstellung",
         "Zu den Kosten: Lager-, Such- und Stillstandskosten sinken. Dafür gibt es Personalkosten, und die Umstellung war teuer."),
        ("🤸", "Flexibilität", "+ Lieferung nach Bedarf statt Fahrplan\n– abhängig von den Mitarbeitern",
         "Zur Flexibilität: Geliefert wird nach Bedarf statt nach Fahrplan. Dafür ist man von den Mitarbeitern abhängig."),
        ("🏦", "Kapitalbindung", "+ kleine Bestände → weniger gebundenes Kapital, mehr Liquidität",
         "Zur Kapitalbindung: Kleine Bestände binden weniger Kapital. Das Unternehmen bleibt liquide."),
        ("😊", "Kundenzufriedenheit", "+ kurze Lieferzeiten, hohe Termintreue, auch kleine Aufträge",
         "Und zur Kundenzufriedenheit: kurze Lieferzeiten, pünktliche Lieferung, und auch kleine Aufträge sind möglich."),
    ], h=270)),
    sc("Fazit", [
        B("Unterm Strich:", [*title_hl("Fazit", 200, 96)]),
        B("Der Materialfluss nach Bedarf senkt Kosten und macht flexibel.", [
            S(list_row("✅", "Chance: Kosten sinken, Flexibilität steigt", 1300, 110, fill=LIGHT_G, tsize=44), 960, 420, "rise")]),
        B("Aber ohne Lagerpuffer kann eine Lieferstörung schnell die Produktion stoppen.", [
            S(list_row("⚠", "Risiko: ohne Puffer droht Stillstand", 1300, 110, fill=LIGHT_R, tsize=44), 960, 570, "rise")]),
        B("Bei Fischer überwiegen klar die Vorteile.", [
            S(list_row("🏆", "Bei Fischer überwiegen die Vorteile", 1300, 110, fill=LIGHT_Y, tsize=44), 960, 720, "rise")]),
    ]),
])

# --------------------------------------------------------------------------- 04 Kosten vs Kunde
left = [("✅", "große Lose → niedrige Stückkosten"), ("✅", "hohe Auslastung der Maschinen"),
        ("⚠", "hohe Lagerbestände"), ("⚠", "lange Lieferzeiten")]
right = [("✅", "Varianten nach Kundenwunsch"), ("✅", "kurze Lieferzeiten"),
         ("⚠", "2–3× täglich umrüsten"), ("⚠", "höhere Rüst- & Personalkosten")]
clip("04_kosten_vs_kunde", "Kosten vs. Kunde", [
    sc("Perspektivwechsel", [
        B("Bei Fischer gibt es einen echten Perspektivwechsel.", [*title_emo("Kosten oder Kunde?", "⚖", 170, 84)]),
        B("Früher musste sich der Auftrag nach der Produktion richten.", [
            S(chip("FRÜHER", None, 40, fill=RED, color=WHITE), 330, 450),
            S(node("🏭", "Produktion"), 820, 450, f=0.1), S(arrow(200), 1110, 450, "wipe", f=0.3),
            S(node("📝", "Auftrag"), 1400, 450, f=0.4)]),
        B("Heute ist es umgekehrt: Die Produktion richtet sich nach dem Auftrag des Kunden.", [
            S(chip("HEUTE", None, 40, fill=GREEN, color=WHITE), 330, 720),
            S(node("📝", "Auftrag"), 820, 720, f=0.1), S(arrow(200, GREEN), 1110, 720, "wipe", f=0.3),
            S(node("🏭", "Produktion"), 1400, 720, f=0.4)]),
    ]),
    sc("Zwei Sichtweisen", [
        B("Schauen wir uns beide Sichtweisen an.", [
            title("Zwei Sichtweisen", 160, 80),
            S(chip("Kostenorientierung", "💶", 42, fill=LIGHT_B), 530, 300, f=0.3),
            S(chip("Kundenorientierung", "🙋", 42, fill=LIGHT_G), 1390, 300, f=0.5)]),
        B("Kostenorientiert produziert man große Lose bei hoher Auslastung. Das ist günstig pro Stück, aber es entstehen große Lager und lange Lieferzeiten.",
          [S(list_row(e, l), 530, 420 + i * 105, "rise", f=i * 0.2) for i, (e, l) in enumerate(left)]),
        B("Kundenorientiert gibt es Varianten nach Wunsch und kurze Lieferzeiten. Dafür muss man oft umrüsten, und das kostet.",
          [S(list_row(e, l), 1390, 420 + i * 105, "rise", f=i * 0.2) for i, (e, l) in enumerate(right)]),
    ]),
    sc("Lösung", [
        B("Wie löst man diesen Konflikt?", [*title_hl("Wie passt das zusammen?", 170, 80)]),
        B("Erstens: Rüstzeiten verkürzen, dann lohnen sich auch kleine Mengen.", [
            S(card(560, 280, "⚡", "Rüstzeiten verkürzen", "Umrüsten wird schnell & billig → kleine Lose lohnen sich", accent=YELLOW, tsize=36, ssize=28, esize=78), 330, 480)]),
        B("Zweitens: Zufriedene Kunden bleiben treu und zahlen auch höhere Preise.", [
            S(card(560, 280, "🤝", "Kundenbindung", "zufriedene Kunden bleiben und zahlen höhere Preise", accent=GREEN, tsize=36, ssize=28, esize=78), 960, 480)]),
        B("Drittens: Ohne Fertigwarenlager spart man Lager- und Kapitalkosten.", [
            S(card(560, 280, "📦", "Kein Fertigwarenlager", "spart Lager- und Kapitalkosten", accent=BLUE, tsize=36, ssize=28, esize=78), 1590, 480)]),
        B("Fazit: Kurzfristig gibt es einen Zielkonflikt. Langfristig senkt die Kundenorientierung aber auch die Kosten.", [
            S(chip("Kurzfristig Konflikt – langfristig sinken auch die Kosten", "💡", 44, fill=LIGHT_Y, padx=40, pady=24), 960, 820, "rise")]),
    ]),
])

# --------------------------------------------------------------------------- 05 F&E
clip("05_lean_in_der_forschung", "Lean in der Forschung", [
    sc("Lean in der Forschung", [
        B("Zum Schluss eine spannende Frage: Funktioniert Lean auch in der Forschung und Entwicklung?", [
            *title_hl("Lean in der Forschung?", 280, 96),
            S(emoji("🔬", 160), 700, 560, f=0.35), S(emoji("🧪", 160), 960, 560, f=0.5),
            S(emoji("💡", 160), 1220, 560, f=0.65)]),
    ]),
    sc("Was übertragbar ist", [
        B("Vieles lässt sich übertragen.", [*title_emo("Das klappt", "✅", 170, 84)]),
    ] + grid4([
        ("🔀", "Parallele Entwicklung", "Schritte laufen gleichzeitig statt nacheinander → neue Produkte schneller fertig",
         "Zum Beispiel parallele Entwicklung: Die Schritte laufen gleichzeitig statt nacheinander. So ist das neue Produkt schneller fertig."),
        ("👥", "Gemischte Teams", "Entwicklung, Produktion & Vertrieb arbeiten von Anfang an zusammen",
         "Gemischte Teams: Entwicklung, Produktion und Vertrieb arbeiten von Anfang an zusammen."),
        ("🙋", "Kunde früh dabei", "nur entwickeln, was der Kunde wirklich braucht",
         "Den Kunden früh einbeziehen, damit nur entwickelt wird, was er wirklich braucht."),
        ("🗑", "Verschwendung vermeiden", "keine Doppelarbeit, keine Wartezeiten, ständig verbessern",
         "Und auch hier Verschwendung vermeiden: keine Doppelarbeit und keine Wartezeiten."),
    ])),
    sc("Grenzen", [
        B("Es gibt aber auch Grenzen.", [*title_emo("Die Grenzen", "⚠", 170, 84)]),
        B("Kreativität braucht Freiraum und lässt sich nicht einfach takten oder standardisieren.", [
            S(card(800, 270, "🎨", "Kreativität braucht Freiraum", "Ideen lassen sich nicht takten oder standardisieren", accent=RED), 530, 470)]),
        B("Außerdem sind Ergebnisse in der Forschung unsicher. Umwege und Fehlversuche gehören dazu.", [
            S(card(800, 270, "🎲", "Ergebnisse sind unsicher", "Umwege & Fehlversuche gehören zur Innovation dazu", accent=RED), 1390, 470)]),
        B("Mein Fazit: Lean ist in der Entwicklung teilweise übertragbar. Die Organisation kann schlank sein, aber es muss Raum für Kreativität bleiben.", [
            S(chip("Teilweise übertragbar: schlank organisieren – Kreativität frei lassen", "🏁", 40, fill=LIGHT_Y, padx=40, pady=24), 960, 800, "rise")]),
    ]),
])


# --------------------------------------------------------------------------- Ausgabe
def fmt(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def main(preview_dir=None):
    out_dir = os.path.join(HERE, "clips")
    silent_dir = os.path.join(out_dir, "ohne_ton")
    os.makedirs(silent_dir, exist_ok=True)
    md = ["# Sprechertext – Lernclips Lean Production", "",
          "Für die Clips **ohne Ton** (Ordner `clips/ohne_ton`). Die Zeit vor jedem Satz zeigt, wann er im Clip beginnt –",
          "dann erscheinen auch die passenden Bilder. Kleine Abweichungen beim Tempo sind kein Problem.", ""]
    for c in CLIPS:
        m.SCENES[:] = c["scenes"]
        with tempfile.TemporaryDirectory() as tmp:
            total, audio, subs = m.build_timeline(tmp)
            md += [f"## {c['label']}  (`{c['name']}.mp4`, ca. {fmt(total)} min)", ""]
            for s in c["scenes"]:
                for b in s["beats"]:
                    md.append(f"**{fmt(b['t0'])}**  {b['sub']}  ")
            md.append("")
            if preview_dir:
                base = m.make_bg()
                for i, s in enumerate(c["scenes"]):
                    b = base.copy()
                    m.chrome(b, s["label"], 0.5)
                    m.draw_scene(s, s["end"] - 0.01, b).convert("RGB").save(
                        os.path.join(preview_dir, f"{c['name']}_{i}.png"))
                continue
            wav = os.path.join(tmp, "a.wav")
            import wave
            with wave.open(wav, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(m.SR)
                w.writeframes(audio.tobytes())
            path = os.path.join(out_dir, c["name"] + ".mp4")
            print(f"{c['name']}: {total:.0f} s")
            m.render(total, path, wav)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:v", "copy", "-an",
                            os.path.join(silent_dir, c["name"] + ".mp4")], check=True)
    if not preview_dir:
        with open(os.path.join(HERE, "SPRECHERTEXT.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        main(sys.argv[2])
    else:
        main()
