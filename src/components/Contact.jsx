import { contact } from '../lib/content.js';
import { Eyebrow, Lines } from './Primitives.jsx';

const MAP = 'https://www.openstreetmap.org/export/embed.html?bbox=13.3935%2C52.5262%2C13.4065%2C52.5322&layer=mapnik&marker=52.5292%2C13.4000';

export default function Contact() {
  return (
    <section className="contact section" id="kontakt" aria-labelledby="contact-title">
      <div className="container">
        <Eyebrow no="06">Standort & Kontakt</Eyebrow>
        <Lines id="contact-title" className="display" text={'Mitten in Mitte,\nund doch ganz für sich.'} />

        <div className="contact__grid">
          <div className="contact__info" data-reveal-group>
            <div className="contact__block">
              <h3>Adresse</h3>
              <address>
                {contact.street}<br />{contact.city}
              </address>
              <a className="link" href="https://www.openstreetmap.org/?mlat=52.5292&mlon=13.4000#map=17/52.5292/13.4000" target="_blank" rel="noopener noreferrer">
                Route planen<span className="visually-hidden"> (öffnet in neuem Tab)</span>
              </a>
            </div>
            <div className="contact__block">
              <h3>Öffnungszeiten</h3>
              <dl className="hours">
                {contact.hours.map(([d, t]) => (
                  <div key={d}><dt>{d}</dt><dd>{t}</dd></div>
                ))}
              </dl>
            </div>
            <div className="contact__block">
              <h3>Kontakt</h3>
              <p><a className="link" href={contact.phoneHref}>{contact.phone}</a></p>
              <p><a className="link" href={`mailto:${contact.email}`}>{contact.email}</a></p>
            </div>
            <div className="contact__block">
              <h3>Folgen</h3>
              <ul className="socials" role="list">
                {contact.socials.map((s) => (
                  <li key={s.label}>
                    <a className="link" href={s.href} target="_blank" rel="noopener noreferrer">
                      {s.label}<span className="visually-hidden"> (öffnet in neuem Tab)</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="contact__map" data-reveal data-delay="0.1">
            <iframe
              title="Karte: NOIR, Linienstraße 113, Berlin"
              src={MAP}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
            />
            <div className="contact__pin" aria-hidden="true">
              <span>NOIR</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
