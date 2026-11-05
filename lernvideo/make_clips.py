"""Erzeugt kurze Lernvideo-Clips (MP4) zu Aufgabe 1.1-1.4 (Lean Production, Landesabitur 2009).

Aufruf: python3 make_clips.py   -> legt die Clips im Ordner clips/ ab (benötigt Pillow + ffmpeg)
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = (16, 24, 40)
CARD = (27, 38, 61)
TEXT = (236, 240, 246)
MUTED = (150, 165, 190)
ACCENT = (255, 176, 59)
ACCENT2 = (88, 196, 220)

f_title = ImageFont.truetype(FONT_B, 44)
f_big = ImageFont.truetype(FONT_B, 64)
f_sub = ImageFont.truetype(FONT, 30)
f_bullet_b = ImageFont.truetype(FONT_B, 30)
f_bullet = ImageFont.truetype(FONT, 25)
f_chip = ImageFont.truetype(FONT_B, 22)
f_small = ImageFont.truetype(FONT, 20)


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def blend(c, a):
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))


# --------------------------------------------------------------------------- Inhalte
# Jede Folie: dict(kind="title"|"bullets", ...). Bullets: (Überschrift, Erklärung)
CLIPS = [
    ("00_intro", "Einführung", [
        dict(kind="title", chip="Lernvideo", title="Lean Production",
             sub="Aufgabe 1.1 – 1.4  |  Interview mit Klaus Fischer (fischer Dübel)", dur=5),
        dict(kind="bullets", chip="Worum geht's?", title="Lean Production = „schlanke Produktion“",
             items=[("Ursprung: Toyota", "Toyota-Produktionssystem – Vorbild weltweit"),
                    ("Kernidee", "Alles weglassen, was dem Kunden keinen Nutzen bringt (Verschwendung)"),
                    ("Ziel", "Höhere Qualität, kürzere Durchlaufzeiten, geringere Kosten"),
                    ("Fischer-Interview", "„Menschen statt Roboter“ – Lean in der Praxis")]),
    ]),
    ("01_aufgabe_1-1", "Aufgabe 1.1", [
        dict(kind="title", chip="Aufgabe 1.1  (10 BE)", title="5 Elemente der Lean Production",
             sub="Nennen + Auswirkungen auf den Produktionsprozess erläutern", dur=4),
        dict(kind="bullets", chip="Aufgabe 1.1", title="Elemente & Auswirkungen (1/2)",
             items=[("1. Just-in-Time / Kanban (Pull-Prinzip)",
                     "Produktion erst bei Bedarf → kaum Lager, weniger Kapitalbindung, kurze Durchlaufzeiten"),
                    ("2. Kaizen – Kontinuierlicher Verbesserungsprozess",
                     "Ständige kleine Verbesserungen durch alle Mitarbeiter → Prozesse werden immer effizienter"),
                    ("3. Gruppen- / Teamarbeit",
                     "Teams planen und kontrollieren selbst, Springer möglich → flexibel, motiviert")]),
        dict(kind="bullets", chip="Aufgabe 1.1", title="Elemente & Auswirkungen (2/2)",
             items=[("4. Null-Fehler-Prinzip (Jidoka, Qualität an der Quelle)",
                     "Fehler werden sofort behoben, nicht weitergegeben → weniger Ausschuss und Nacharbeit"),
                    ("5. Vermeidung von Verschwendung (Muda)",
                     "Kein Überproduzieren, Warten, Suchen, unnötige Wege → Kosten sinken"),
                    ("Weitere: 5S, flache Hierarchien, Standardisierung",
                     "Ordentlicher Arbeitsplatz, schnelle Entscheidungen, stabile Abläufe")]),
    ]),
    ("02_aufgabe_1-2_teil1", "Aufgabe 1.2 – Teil 1", [
        dict(kind="title", chip="Aufgabe 1.2  (15 BE)", title="Lean Production bei Fischer",
             sub="Schwerpunkte und betriebliche Erfahrungen aus dem Interview", dur=4),
        dict(kind="bullets", chip="Aufgabe 1.2", title="Schwerpunkte im Interview (1/2)",
             items=[("Kundenorientierung (Z. 5–7)", "Jeder Prozess wird vom Kunden aus betrachtet: „Was hat der Kunde davon?“"),
                    ("Kampf gegen Verschwendung (Z. 7–9)", "Wissen, Zeit und Platz werden nicht mehr verschwendet"),
                    ("Menschen statt Roboter (Z. 13–17)", "Menschen sind flexibler; Springer ersetzen Ausfälle sofort"),
                    ("Mehr Ruhe statt Stress (Z. 26–28)", "Effiziente Abläufe → flexible Reaktion auf Aufträge, +14 % bewältigt")]),
        dict(kind="bullets", chip="Aufgabe 1.2", title="Schwerpunkte im Interview (2/2)",
             items=[("Arbeitsplatzorganisation (Z. 32–37)", "Suchzeiten vermeiden – gut organisierter Platz = schneller + bessere Qualität"),
                    ("Visualisierung (Z. 37–39)", "Kennzahlen für alle sichtbar machen statt im Computer verstecken"),
                    ("Mitarbeiter einbeziehen (Z. 2–3, 40)", "Nur Ziele vorgeben – Mitarbeiter finden den Weg selbst"),
                    ("Fehlerkultur (Z. 41–42)", "Fehler sind erlaubt – aber nie zweimal derselbe (lernen = Kaizen)")]),
    ]),
    ("03_aufgabe_1-2_teil2", "Aufgabe 1.2 – Teil 2", [
        dict(kind="title", chip="Aufgabe 1.2", title="Bedarfsgerechter Materialfluss",
             sub="Beispiel: fahrerlose Transportsysteme → kleiner Zug mit Werkslogistiker (Z. 18–23)", dur=5),
        dict(kind="bullets", chip="Diskussion", title="Bedeutung des Materialflusses",
             items=[("Kosten", "+ weniger Lager-, Such- und Stillstandskosten  |  – Personalkosten, teure Umstellung"),
                    ("Flexibilität", "+ Transport nach Bedarf statt starrem Fahrplan  |  – abhängig von Mitarbeitern"),
                    ("Kapitalbindung", "+ kleine Bestände → weniger gebundenes Kapital, mehr Liquidität"),
                    ("Kundenzufriedenheit", "+ kurze Lieferzeiten, hohe Termintreue, auch Kleinstaufträge möglich")]),
        dict(kind="bullets", chip="Fazit 1.2", title="Fazit",
             items=[("Chance", "Materialfluss nach dem Pull-Prinzip senkt Kosten und erhöht die Flexibilität"),
                    ("Risiko", "Ohne Puffer führen Lieferstörungen schnell zum Produktionsstillstand"),
                    ("Bewertung", "Bei Fischer überwiegen die Vorteile – höhere Kosten des Zugs lohnen sich")]),
    ]),
    ("04_aufgabe_1-3", "Aufgabe 1.3", [
        dict(kind="title", chip="Aufgabe 1.3  (10 BE)", title="Kosten- vs. Kundenorientierung",
             sub="Früher: Auftrag folgt der Produktion  →  Heute: Produktion folgt dem Auftrag", dur=5),
        dict(kind="bullets", chip="Aufgabe 1.3", title="Zwei Sichtweisen",
             items=[("Kostenorientierung (klassisch)", "Große Losgrößen, hohe Auslastung, wenig Umrüsten → niedrige Stückkosten"),
                    ("   aber:", "Hohe Lagerbestände, lange Lieferzeiten, Kunde muss sich anpassen"),
                    ("Kundenorientierung (Lean)", "Kleine Lose, 2–3× täglich Umrüsten (Z. 14–15), Varianten nach Wunsch"),
                    ("   aber:", "Höhere Rüst- und Personalkosten, komplexere Planung")]),
        dict(kind="bullets", chip="Diskussion", title="Spannungsfeld auflösen",
             items=[("Rüstzeiten verkürzen (SMED)", "Umrüsten wird billig → kleine Lose lohnen sich"),
                    ("Mehrwert für Kunden", "Höhere Preise, Kundenbindung, neue Aufträge"),
                    ("Kein Fertigwarenlager", "Pull-Prinzip spart Lager- und Kapitalkosten"),
                    ("Fazit", "Kurzfristig Zielkonflikt – langfristig senkt Kundenorientierung auch die Kosten")]),
    ]),
    ("05_aufgabe_1-4", "Aufgabe 1.4", [
        dict(kind="title", chip="Aufgabe 1.4  (5 BE)", title="Lean in Forschung & Entwicklung?",
             sub="Lässt sich der Lean-Gedanke auf die Produktentwicklung übertragen?", dur=4),
        dict(kind="bullets", chip="Möglichkeiten", title="Was übertragbar ist",
             items=[("Simultaneous Engineering", "Entwicklungsschritte parallel statt nacheinander → kürzere Entwicklungszeit"),
                    ("Interdisziplinäre Teams", "F&E, Produktion, Vertrieb arbeiten von Anfang an zusammen"),
                    ("Kunde früh einbeziehen", "Nur entwickeln, was der Kunde wirklich braucht"),
                    ("Verschwendung vermeiden", "Keine Doppelarbeit, Wartezeiten, unnötige Schleifen; KVP")]),
        dict(kind="bullets", chip="Grenzen & Fazit", title="Grenzen",
             items=[("Kreativität braucht Freiraum", "Forschung lässt sich kaum standardisieren oder takten"),
                    ("Ungewisse Ergebnisse", "„Umwege“ und Fehlversuche gehören zur Innovation dazu"),
                    ("Fazit", "Teilweise übertragbar: Organisation lean – aber Raum für Kreativität lassen")]),
    ]),
]


# --------------------------------------------------------------------------- Rendering
def bullet_times(n):
    start, step = 0.8, 4.5
    return [start + i * step for i in range(n)], start + n * step + 2.5


def draw_frame(slide, t, slide_dur, clip_label, progress):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fade_out = ease((slide_dur - t) / 0.5)

    # Deko
    d.rectangle([0, 0, 10, H], fill=ACCENT)
    d.text((40, H - 40), "Lean Production – Landesabitur WiLe LK 2009, Vorschlag A", font=f_small, fill=MUTED)
    tw = d.textlength(clip_label, font=f_small)
    d.text((W - 40 - tw, H - 40), clip_label, font=f_small, fill=MUTED)
    d.rectangle([0, H - 6, int(W * progress), H], fill=ACCENT2)

    a0 = ease(t / 0.6) * fade_out
    chip = slide["chip"]
    cw = d.textlength(chip, font=f_chip) + 32

    if slide["kind"] == "title":
        y_off = int((1 - ease(t / 0.8)) * 30)
        cx = (W - cw) / 2
        d.rounded_rectangle([cx, 210 + y_off, cx + cw, 250 + y_off], 18, fill=blend(ACCENT, a0))
        d.text((cx + 16, 217 + y_off), chip, font=f_chip, fill=blend((20, 20, 30), a0))
        tl = wrap(d, slide["title"], f_big, W - 200)
        y = 290 + y_off
        for line in tl:
            lw = d.textlength(line, font=f_big)
            d.text(((W - lw) / 2, y), line, font=f_big, fill=blend(TEXT, a0))
            y += 78
        a1 = ease((t - 0.6) / 0.7) * fade_out
        for line in wrap(d, slide["sub"], f_sub, W - 240):
            lw = d.textlength(line, font=f_sub)
            d.text(((W - lw) / 2, y + 20), line, font=f_sub, fill=blend(MUTED, a1))
            y += 42
        return img

    # Bullet-Folie
    d.rounded_rectangle([60, 40, 60 + cw, 80], 18, fill=blend(ACCENT, a0))
    d.text((76, 47), chip, font=f_chip, fill=blend((20, 20, 30), a0))
    d.text((60, 100), slide["title"], font=f_title, fill=blend(TEXT, a0))
    d.line([60, 165, 60 + int(260 * ease(t / 0.8)), 165], fill=ACCENT, width=4)

    times, _ = bullet_times(len(slide["items"]))
    n = len(slide["items"])
    box_h = min(118, (H - 230 - 20 * (n - 1)) // n)
    y = 190
    for (head, body), ts in zip(slide["items"], times):
        a = ease((t - ts) / 0.6) * fade_out
        if a <= 0:
            y += box_h + 16
            continue
        x_off = int((1 - ease((t - ts) / 0.6)) * 40)
        highlight = ts <= t < ts + 4.5
        d.rounded_rectangle([60 + x_off, y, W - 60 + x_off, y + box_h], 14, fill=blend(CARD, a))
        bar_col = ACCENT if highlight else ACCENT2
        d.rounded_rectangle([60 + x_off, y, 68 + x_off, y + box_h], 4, fill=blend(bar_col, a))
        d.text((90 + x_off, y + 14), head.strip(), font=f_bullet_b, fill=blend(ACCENT if head.strip().endswith(":") else TEXT, a))
        by = y + 54
        for line in wrap(d, body, f_bullet, W - 200)[:2]:
            d.text((90 + x_off, by), line, font=f_bullet, fill=blend(MUTED, a))
            by += 30
        y += box_h + 16
    return img


def render_clip(name, label, slides):
    os.makedirs(OUT, exist_ok=True)
    durs = []
    for s in slides:
        durs.append(s["dur"] if s["kind"] == "title" else bullet_times(len(s["items"]))[1])
    total = sum(durs)
    path = os.path.join(OUT, name + ".mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium",
         "-c:a", "aac", "-movflags", "+faststart", path],
        stdin=subprocess.PIPE)
    elapsed = 0.0
    for s, dur in zip(slides, durs):
        for f in range(int(dur * FPS)):
            t = f / FPS
            img = draw_frame(s, t, dur, label, (elapsed + t) / total)
            proc.stdin.write(img.tobytes())
        elapsed += dur
    proc.stdin.close()
    proc.wait()
    print(f"{path}  ({total:.0f} s)")


if __name__ == "__main__":
    for name, label, slides in CLIPS:
        render_clip(name, label, slides)
