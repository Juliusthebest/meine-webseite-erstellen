import { img } from '../lib/content.js';
import { Eyebrow, Frame, Lines } from './Primitives.jsx';

export default function About() {
  return (
    <section className="about section" id="konzept" aria-labelledby="about-title">
      <div className="container">
        <Eyebrow no="01">Das Haus</Eyebrow>
        <Lines id="about-title" className="display about__title" text={'Ein Ort, an dem\ndie Zeit leiser wird.'} />

        <div className="about__grid">
          <div className="about__media-main">
            <Frame src={img.interior} alt="Der Gastraum von NOIR mit dunklem Holz und warmem Kerzenlicht" parallax="8" sizes="(min-width: 900px) 55vw, 100vw" />
            <p className="caption" data-reveal>Der Gastraum — 42 Plätze, ein Chef’s Table.</p>
          </div>

          <div className="about__text">
            <p className="lead" data-reveal>
              NOIR ist die Antwort auf eine einfache Frage: Was bleibt, wenn man alles Überflüssige weglässt?
            </p>
            <p data-reveal data-delay="0.1">
              Gedämpftes Licht, dunkles Eichenholz und eine offene Küche, in der das Feuer den Takt vorgibt.
              Hier kochen wir mit dem, was die Höfe rund um Berlin in dieser Woche hergeben — präzise,
              ehrlich und ohne Effekthascherei. Jeder Abend ist ein ruhiges Gespräch zwischen Küche und Gast.
            </p>
            <dl className="stats" data-reveal-group>
              <div><dt>Partnerhöfe</dt><dd>23</dd></div>
              <div><dt>Weine im Keller</dt><dd>480</dd></div>
              <div><dt>Gänge im Menü</dt><dd>07</dd></div>
            </dl>
          </div>

          <div className="about__media-side">
            <Frame src={img.table} alt="Ein eingedeckter Tisch mit Leinen, Gläsern und einer Kerze" parallax="10" sizes="(min-width: 900px) 30vw, 70vw" />
          </div>
        </div>
      </div>
    </section>
  );
}
