import { useEffect, useRef } from 'react';
import { contact } from '../lib/content.js';
import { lockScroll } from '../lib/motion.js';

const CONTENT = {
  impressum: {
    title: 'Impressum',
    body: (
      <>
        <p><strong>NOIR Modern Dining GmbH</strong><br />{contact.street}<br />{contact.city}</p>
        <p>Vertreten durch: Elias Brandt (Geschäftsführer)<br />Registergericht: Amtsgericht Charlottenburg, HRB 000000 B<br />USt-IdNr.: DE 000 000 000</p>
        <p>Telefon: {contact.phone}<br />E-Mail: {contact.email}</p>
        <p className="fine">Hinweis: NOIR ist ein fiktives Restaurant. Alle Angaben dienen als Platzhalter.</p>
      </>
    ),
  },
  datenschutz: {
    title: 'Datenschutz',
    body: (
      <>
        <p>Wir verarbeiten personenbezogene Daten, die Sie uns im Rahmen einer Reservierung übermitteln (Name, E-Mail, Datum, Uhrzeit, Personenanzahl), ausschließlich zur Abwicklung Ihrer Reservierung gemäß Art. 6 Abs. 1 lit. b DSGVO.</p>
        <p>Die Kartendarstellung wird von OpenStreetMap bereitgestellt; beim Laden der Karte wird Ihre IP-Adresse an die OpenStreetMap Foundation übertragen.</p>
        <p>Sie haben jederzeit das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der Verarbeitung Ihrer Daten. Kontakt: {contact.email}</p>
        <p className="fine">Platzhaltertext – vor Veröffentlichung rechtlich prüfen lassen.</p>
      </>
    ),
  },
};

export default function Legal({ open, onClose }) {
  const ref = useRef(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) { d.showModal(); lockScroll(true); }
    if (!open && d.open) { d.close(); }
  }, [open]);

  const c = open ? CONTENT[open] : null;

  return (
    <dialog
      ref={ref}
      className="legal"
      aria-labelledby="legal-title"
      onClose={() => { lockScroll(false); onClose(); }}
      onClick={(e) => e.target === ref.current && onClose()}
    >
      {c && (
        <div className="legal__inner">
          <button className="legal__close" type="button" onClick={onClose} aria-label="Dialog schließen">×</button>
          <h2 id="legal-title">{c.title}</h2>
          {c.body}
        </div>
      )}
    </dialog>
  );
}
