# Zombie-Apokalypse – 7 TikToks

Sieben animierte Kurzclips im Hochformat (1080×1920, 30 fps). Jeder Clip ist ein kleines Drama mit Pointe und hat deutsche Stimmen.

| Teil | Titel | Pointe |
|---|---|---|
| 1 | Der Biss | Ben wurde gebissen … von Mias kleinem Bruder, wegen des Gameboys |
| 2 | Der letzte Riegel | Der Zombie verschmäht den letzten Schokoriegel: Haselnuss-Allergie |
| 3 | Das Klopfen | Der Zombie will nur das WLAN-Passwort |
| 4 | Der Ex | Zombie-Kevin „war vorher auch schon so“ |
| 5 | Das Heilmittel | Der geheilte Zombie hört „Montag“ und will zurückgebissen werden |
| 6 | Mama | Sogar die Zombies haben Angst vor Mama und dem frisch gewischten Boden |
| 7 | Das Opfer | Bens Heldenrede dauert so lange, dass die anderen längst weg sind |

Die fertigen Videos liegen in `videos/`.

## Selbst neu erzeugen

Voraussetzungen: `ffmpeg`, Python 3 mit `numpy`, `pycairo` und `piper-tts` sowie die deutschen Piper-Stimmen
(`de-thorsten-low`, `de-kerstin-low`, `de-ramona-low`, `de-karlsson-low`, `de-pavoque-low`) in einem Ordner.

```bash
export VOICE_DIR=/pfad/zu/den/stimmen
python3 render.py 1 videos   # rendert Teil 1; 1–7 möglich
```

Texte, Figuren und Effekte lassen sich in `episodes.py` ändern.

---

# Serie 2: POV – Mitten in der Klausur kommt eine Warnung aufs Handy

Ordner `serie-2-die-warnung/`: 7 zusammenhängende Teile im Comic-Stil aus der Ich-Perspektive:
- Fischauge-Kamera, eigene Hände und Handy im Bild
- NINA-Warnung, SMS-Karten und Untertitel
- Endkarte „Was würdest du tun?“

Teil 1–6 enden offen, Teil 7 hat ein Ende.

| Teil | Titel | Cliffhanger / Entscheidung |
|---|---|---|
| 1 | Die Warnung | Noah hämmert blutend an die Tür → aufmachen oder zulassen? |
| 2 | Der Kratzer | Noah wurde gebissen → einsperren oder mit ihm abhauen? |
| 3 | Der Flur | Ein Infizierter packt Noah an der Kellertür → zurückziehen oder durch die Tür? |
| 4 | Der Keller | Licht aus, jemand schreit → Handylicht an oder still sitzen? |
| 5 | Die Dunkelheit | Jonas war infiziert, nicht Noah. Mamas Auto ist leer → warten oder suchen? |
| 6 | Mamas Auto | Mama in der Turnhalle, ihr Arm ist verbunden → zu ihr rennen oder Abstand halten? |
| 7 | Das Ende | Rettungshubschrauber, Noah schließt das Tor für die anderen → ENDE |

Videos: `serie-2-die-warnung/videos/`. Neu rendern mit:

```bash
cd serie-2-die-warnung
VOICE_DIR=/pfad/zu/den/stimmen python3 render2.py 1 videos   # 1–7
```

Drehbuch: `story2.py`. Schauplätze: `scenes.py`. Figuren: `comic.py`.
Das Produktionspaket für KI-Video-Tools liegt in `PRODUKTIONSPAKET.md`. Die zusätzliche Stimme `de-eva_k-x-low` wird für Mama verwendet.
