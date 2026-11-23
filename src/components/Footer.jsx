import { contact, nav } from '../lib/content.js';
import { scrollToId } from '../lib/motion.js';

export default function Footer({ onLegal }) {
  const go = (id) => (e) => { e.preventDefault(); scrollToId(id); };
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__top">
          <p className="footer__claim" data-reveal>A different taste<br /><em>of dining.</em></p>
          <a href="#top" className="footer__up" onClick={go('top')}>
            Nach oben <span aria-hidden="true">↑</span>
          </a>
        </div>

        <div className="footer__cols">
          <nav aria-label="Footer-Navigation">
            <h2 className="footer__h">Navigation</h2>
            <ul role="list">
              {[...nav, { id: 'reservierung', label: 'Reservierung' }].map((n) => (
                <li key={n.id}><a className="link" href={`#${n.id}`} onClick={go(n.id)}>{n.label}</a></li>
              ))}
            </ul>
          </nav>
          <div>
            <h2 className="footer__h">Besuch</h2>
            <address>{contact.street}<br />{contact.city}</address>
          </div>
          <div>
            <h2 className="footer__h">Kontakt</h2>
            <p><a className="link" href={contact.phoneHref}>{contact.phone}</a></p>
            <p><a className="link" href={`mailto:${contact.email}`}>{contact.email}</a></p>
          </div>
          <div>
            <h2 className="footer__h">Social</h2>
            <ul role="list">
              {contact.socials.map((s) => (
                <li key={s.label}><a className="link" href={s.href} target="_blank" rel="noopener noreferrer">{s.label}</a></li>
              ))}
            </ul>
          </div>
        </div>

        <p className="footer__wordmark" aria-hidden="true">NOIR</p>

        <div className="footer__bottom">
          <p>© {new Date().getFullYear()} NOIR Modern Dining GmbH</p>
          <ul role="list">
            <li><button className="link" type="button" onClick={() => onLegal('impressum')}>Impressum</button></li>
            <li><button className="link" type="button" onClick={() => onLegal('datenschutz')}>Datenschutz</button></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
