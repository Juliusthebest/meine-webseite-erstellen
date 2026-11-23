import { dishes, img } from '../lib/content.js';
import { Eyebrow, Frame, Lines } from './Primitives.jsx';

export default function Kitchen() {
  return (
    <section className="kitchen section" id="kueche" aria-labelledby="kitchen-title">
      <div className="container">
        <div className="kitchen__head">
          <div>
            <Eyebrow no="02">Unsere Küche</Eyebrow>
            <Lines id="kitchen-title" className="display" text={'Feuer, Zeit\nund Zurückhaltung.'} />
          </div>
          <div className="kitchen__intro">
            <p className="lead" data-reveal>
              Unsere Philosophie passt auf eine Serviette: das beste Produkt, das richtige Feuer und der Mut,
              einem Teller nichts hinzuzufügen, was er nicht braucht.
            </p>
            <div className="chef" data-reveal data-delay="0.1">
              <Frame src={img.chef} alt="Küchenchef Elias Brandt" className="chef__img" sizes="96px" />
              <p>
                <strong>Elias Brandt</strong>
                <span>Küchenchef — zuvor in Kopenhagen & San Sebastián</span>
              </p>
            </div>
          </div>
        </div>

        <ul className="dishes" role="list">
          {dishes.map((d) => (
            <li className="dish" key={d.no}>
              <article tabIndex={0} aria-labelledby={`dish-${d.no}`}>
                <div className="dish__media">
                  <Frame src={d.src} alt={d.name} sizes="(min-width: 900px) 45vw, 100vw" />
                  <p className="dish__hover" aria-hidden="true">{d.text}</p>
                </div>
                <div className="dish__meta" data-reveal>
                  <span className="dish__no">{d.no}</span>
                  <div>
                    <h3 id={`dish-${d.no}`} className="dish__name">{d.name}</h3>
                    <p className="dish__note">{d.note}</p>
                    <p className="visually-hidden">{d.text}</p>
                  </div>
                </div>
              </article>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
