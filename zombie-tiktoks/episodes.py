# Die 7 Folgen: "TAG 47 – Zombie-Apokalypse"
# Jede Zeile: (sprecher, text, aktion)
# Sprecher: MIA, BEN, OPA, ZOMBIE, KEVIN, DOC, MAMA, ERZ (Erzähler)
# Aktionen: enter_zombie, shake, flash, zoom, heart, sting, punch, horde, exit_zombie

CAST = {
    "MIA":    dict(name="Mia",      skin=(244, 205, 170), shirt=(200, 60, 60),  hair=(120, 60, 30),  long_hair=True,  zombie=False),
    "BEN":    dict(name="Ben",      skin=(225, 180, 140), shirt=(50, 90, 160),  hair=(40, 30, 25),   long_hair=False, zombie=False),
    "OPA":    dict(name="Opa Horst",skin=(235, 195, 165), shirt=(110, 90, 60),  hair=(220, 220, 220),long_hair=False, zombie=False, beard=True),
    "DOC":    dict(name="Dr. Weber",skin=(240, 200, 170), shirt=(235, 235, 235),hair=(90, 90, 90),   long_hair=False, zombie=False, glasses=True),
    "MAMA":   dict(name="Mama",     skin=(240, 200, 165), shirt=(170, 70, 140), hair=(150, 80, 40),  long_hair=True,  zombie=False),
    "ZOMBIE": dict(name="Zombie",   skin=(120, 160, 100), shirt=(90, 80, 70),   hair=(50, 60, 40),   long_hair=False, zombie=True),
    "KEVIN":  dict(name="Zombie-Kevin", skin=(130, 170, 110), shirt=(230, 140, 40), hair=(200, 170, 60), long_hair=False, zombie=True),
    "ERZ":    dict(name="", narrator=True),
}

EPISODES = [
    dict(
        title="Der Biss", place="street", cast=["MIA", "BEN"],
        hook="Er hat ihr etwas verschwiegen…",
        lines=[
            ("ERZ", "Tag 47 der Zombie-Apokalypse.", "sting"),
            ("MIA", "Ben… warum versteckst du deinen Arm?", "heart"),
            ("BEN", "Mia… ich muss dir etwas sagen.", "zoom"),
            ("BEN", "Ich wurde gebissen.", "flash"),
            ("MIA", "Nein! Nein, nein, nein! Wer war das?!", "shake"),
            ("BEN", "Es war… dein kleiner Bruder.", "zoom"),
            ("MIA", "Lukas?! Ist er etwa infiziert?", "heart"),
            ("BEN", "Nein. Ich hab ihm seinen Gameboy weggenommen.", "punch"),
        ]),
    dict(
        title="Der letzte Riegel", place="bunker", cast=["BEN", "OPA"],
        hook="Nur einer kann ihn haben.",
        lines=[
            ("ERZ", "Bunker. Die Vorräte sind fast leer.", "sting"),
            ("OPA", "Das ist er. Der letzte Schokoriegel der Menschheit.", "zoom"),
            ("BEN", "Opa, gib ihn mir. Ich bin jung, ich muss überleben!", "heart"),
            ("OPA", "Ich habe zwei Weltkriegsfilme überlebt, Junge!", "shake"),
            ("ZOMBIE", "Uuuuaaargh…", "enter_zombie"),
            ("BEN", "Ein Zombie! Wirf ihm den Riegel hin, schnell!", "flash"),
            ("ZOMBIE", "Uargh… Haselnuss? Ich bin allergisch.", "punch"),
        ]),
    dict(
        title="Das Klopfen", place="bunker", cast=["MIA", "BEN"],
        hook="Um drei Uhr nachts klopft es…",
        lines=[
            ("ERZ", "Drei Uhr nachts. Es klopft an der Bunkertür.", "sting"),
            ("MIA", "Ben… hast du das gehört?", "heart"),
            ("BEN", "Keine Bewegung. Die können uns riechen.", "zoom"),
            ("ZOMBIE", "Hallo? Ist da jemand?", "enter_zombie"),
            ("MIA", "Er… er kann sprechen?!", "shake"),
            ("BEN", "Was willst du von uns, Monster?!", "flash"),
            ("ZOMBIE", "Euer WLAN-Passwort. Mein Akku ist bei zwei Prozent.", "punch"),
        ]),
    dict(
        title="Der Ex", place="street", cast=["MIA", "BEN"],
        hook="Sie erkennt einen der Zombies…",
        lines=[
            ("ERZ", "Eine Horde nähert sich der Tankstelle.", "horde"),
            ("BEN", "Mia, wir müssen weg! Jetzt!", "shake"),
            ("MIA", "Warte… der da vorne… das ist Kevin. Mein Ex.", "zoom"),
            ("KEVIN", "Miiiaaa… du hast nie zurückgeschrieben…", "enter_zombie"),
            ("BEN", "Soll ich ihn erledigen?", "heart"),
            ("MIA", "Nein. Lass ihn. Er hat sich gar nicht verändert.", "flash"),
            ("BEN", "Wie meinst du das?", "zoom"),
            ("MIA", "Der war vorher auch schon so.", "punch"),
        ]),
    dict(
        title="Das Heilmittel", place="lab", cast=["DOC", "BEN"],
        hook="Sie haben ein Heilmittel gefunden.",
        lines=[
            ("ERZ", "Geheimlabor. Versuch Nummer dreihundertzwölf.", "sting"),
            ("DOC", "Es ist so weit. Das Heilmittel gegen das Zombie-Virus.", "zoom"),
            ("BEN", "Doktor, wenn das klappt, retten wir die Menschheit!", "heart"),
            ("ZOMBIE", "Graaargh!", "enter_zombie"),
            ("DOC", "Jetzt! Die Spritze!", "flash"),
            ("ZOMBIE", "Wo… wo bin ich? Welcher Tag ist heute?", "zoom"),
            ("BEN", "Montag. Du bist wieder ein Mensch!", "heart"),
            ("ZOMBIE", "Montag?! Muss ich wieder arbeiten? Beißt mich bitte sofort zurück.", "punch"),
        ]),
    dict(
        title="Mama", place="house", cast=["BEN", "MAMA"],
        hook="Er findet endlich seine Mutter…",
        lines=[
            ("ERZ", "Ben hat drei Wochen nach seiner Mutter gesucht.", "sting"),
            ("BEN", "Mama? Mama, bist du da?!", "heart"),
            ("MAMA", "Benjamin.", "zoom"),
            ("BEN", "Mama! Du lebst! Ich dachte, ich hätte dich verloren!", "shake"),
            ("MAMA", "Drei Wochen hast du dich nicht gemeldet. Drei Wochen!", "flash"),
            ("ZOMBIE", "Uuuargh…", "enter_zombie"),
            ("MAMA", "Schuhe aus! Ich hab gerade gewischt!", "exit_zombie"),
            ("BEN", "Jetzt weiß ich, warum die Zombies diese Straße meiden.", "punch"),
        ]),
    dict(
        title="Das Opfer", place="street", cast=["BEN", "MIA"],
        flee=("MIA", 3),  # Mia rennt nach dieser Zeile weg
        hook="Das große Finale. Einer bleibt zurück.",
        lines=[
            ("ERZ", "Das Finale. Die Horde hat sie eingekreist.", "horde"),
            ("BEN", "Mia. Lauf. Ich halte sie auf.", "zoom"),
            ("MIA", "Nein, Ben! Ich lasse dich nicht allein!", "heart"),
            ("BEN", "Sag allen… dass ich ein Held war. Dass ich keine Angst hatte.", "flash"),
            ("BEN", "Kommt nur her, ihr Monster! Ich bin bereit!", "shake"),
            ("ERZ", "Zehn Minuten später.", "sting"),
            ("ZOMBIE", "Bist du jetzt fertig mit deiner Rede? Die anderen sind längst weg.", "punch"),
        ]),
]
