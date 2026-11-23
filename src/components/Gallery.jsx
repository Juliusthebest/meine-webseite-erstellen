import { gallery } from '../lib/content.js';
import { Eyebrow, Frame, Lines } from './Primitives.jsx';

export default function Gallery() {
  return (
    <section className="gallery section" id="galerie" aria-labelledby="gallery-title">
      <div className="container">
        <div className="gallery__head">
          <Eyebrow no="04">Galerie</Eyebrow>
          <Lines id="gallery-title" className="display" text={'Momente\nam Tisch.'} />
        </div>
        <ul className="gallery__grid" role="list">
          {gallery.map((g) => (
            <li key={g.cls} className={`gallery__item ${g.cls}`}>
              <Frame src={g.src} alt={g.alt} parallax="6" sizes="(min-width: 900px) 50vw, 100vw" />
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
