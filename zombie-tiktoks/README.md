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
