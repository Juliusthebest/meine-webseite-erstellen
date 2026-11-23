# NOIR – Modern Dining

Premium-Restaurant-Webseite für das fiktive Restaurant **NOIR** in Berlin-Mitte.
Gebaut mit **React 19, Vite, GSAP (ScrollTrigger) und Lenis** (weiches Scrollen).

## Starten

```bash
npm install
npm run dev       # Entwicklungsserver: http://localhost:5173
npm run build     # Produktions-Build nach ./dist
npm run preview   # Build lokal ansehen
```

Der Ordner `dist/` kann direkt auf Netlify, Vercel oder GitHub Pages gehostet werden (relative Pfade).

## Aufbau

| Sektion | Datei |
| --- | --- |
| Preloader (Zähler + Vorhang) | `src/components/Preloader.jsx` |
| Navigation (verändert sich beim Scrollen, mobiles Vollbild-Menü) | `src/components/Nav.jsx` |
| Hero mit Parallax & Intro-Animation | `src/components/Hero.jsx` |
| 01 Das Haus (asymmetrisch) | `src/components/About.jsx` |
| 02 Unsere Küche (4 Signature-Gerichte) | `src/components/Kitchen.jsx` |
| Laufband | `src/components/Marquee.jsx` |
| 03 Speisekarte (Tabs, Degustation) | `src/components/Menu.jsx` |
| 04 Galerie (Editorial-Grid) | `src/components/Gallery.jsx` |
| 05 Reservierung (Validierung, Bestätigung) | `src/components/Reservation.jsx` |
| 06 Standort & Kontakt (Karte) | `src/components/Contact.jsx` |
| Footer, Impressum/Datenschutz | `src/components/Footer.jsx`, `Legal.jsx` |

- **Inhalte** (Texte, Preise, Bilder, Öffnungszeiten): `src/lib/content.js`
- **Animationen**: `src/lib/motion.js` – deklarativ über Attribute (`data-reveal`, `data-lines`, `data-img`, `data-parallax`, `data-reveal-group`)
- **Design-System** (Farben, Typografie, Abstände): `src/styles.css`

## Barrierearmut & Performance

- `prefers-reduced-motion`: kein Smooth-Scroll, keine Scroll-Animationen, Preloader nur kurz eingeblendet.
- Skip-Link, semantische Landmarks, ARIA-Tabs mit Pfeiltasten, Formular mit Fehlermeldungen und Fokusführung, Escape schließt Menü/Dialog.
- Selbst gehostete Schriften (Cormorant Garamond + Manrope), Lazy Loading für Bilder und Karte, Bild-Fallbacks.
- SEO: Meta-/Open-Graph-Tags und strukturierte Daten (`schema.org/Restaurant`).

## Hinweise

- Bilder werden von Unsplash geladen. Für den Live-Betrieb eigene Fotos in `public/` ablegen und in `content.js` eintragen.
- Das Reservierungsformular simuliert den Versand – hier ein echtes System (z. B. resmio, OpenTable) anbinden.
- Impressum und Datenschutz sind Platzhalter.
