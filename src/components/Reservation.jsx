import { useMemo, useState } from 'react';
import { img } from '../lib/content.js';
import { Button, Eyebrow, Lines } from './Primitives.jsx';

const SLOTS = ['18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30'];
const LUNCH = ['12:00', '12:30', '13:00', '13:30', '14:00'];

const iso = (d) => {
  const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return z.toISOString().slice(0, 10);
};

export default function Reservation() {
  const today = useMemo(() => iso(new Date()), []);
  const [form, setForm] = useState({ date: '', time: '', guests: 2, name: '', email: '' });
  const [errors, setErrors] = useState({});
  const [state, setState] = useState('idle'); // idle | sending | done

  const day = form.date ? new Date(`${form.date}T12:00`).getDay() : null;
  const closed = day === 1 || day === 2;
  const slots = day === 0 ? LUNCH : SLOTS;

  const set = (k) => (e) => {
    const v = e.target.value;
    setForm((f) => ({ ...f, [k]: v, ...(k === 'date' ? { time: '' } : {}) }));
    setErrors((er) => ({ ...er, [k]: undefined }));
  };

  const validate = () => {
    const er = {};
    if (!form.date) er.date = 'Bitte wählen Sie ein Datum.';
    else if (form.date < today) er.date = 'Das Datum liegt in der Vergangenheit.';
    else if (closed) er.date = 'Montags und dienstags haben wir Ruhetag.';
    if (!form.time) er.time = 'Bitte wählen Sie eine Uhrzeit.';
    if (form.name.trim().length < 2) er.name = 'Bitte geben Sie Ihren Namen an.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(form.email)) er.email = 'Bitte geben Sie eine gültige E-Mail-Adresse an.';
    return er;
  };

  const submit = (e) => {
    e.preventDefault();
    const er = validate();
    setErrors(er);
    if (Object.keys(er).length) {
      const firstKey = Object.keys(er)[0];
      document.getElementById(`res-${firstKey}`)?.focus();
      return;
    }
    setState('sending');
    // Hier würde die Anfrage an ein Reservierungssystem (z. B. OpenTable, resmio) gehen.
    setTimeout(() => setState('done'), 1200);
  };

  const fmtDate = form.date
    ? new Date(`${form.date}T12:00`).toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' })
    : '';

  const field = (k) => ({
    id: `res-${k}`,
    'aria-invalid': errors[k] ? true : undefined,
    'aria-describedby': errors[k] ? `err-${k}` : undefined,
  });
  const err = (k) => errors[k] && <p className="field__error" id={`err-${k}`} role="alert">{errors[k]}</p>;

  return (
    <section className="reservation" id="reservierung" aria-labelledby="res-title" data-parallax-wrap>
      <div className="reservation__bg" aria-hidden="true">
        <img src={img.reservation} alt="" loading="lazy" data-parallax="12" onError={(e) => (e.currentTarget.style.display = 'none')} />
      </div>
      <div className="container reservation__inner">
        <div className="reservation__copy">
          <Eyebrow no="05">Reservierung</Eyebrow>
          <Lines id="res-title" className="display" text={'Ihr Tisch\nerwartet Sie.'} />
          <p data-reveal>
            Reservierungen nehmen wir bis zu 60 Tage im Voraus entgegen. Für Gruppen ab neun Personen
            und den Chef’s Table rufen Sie uns bitte direkt an.
          </p>
          <a className="link" href="tel:+493023456789" data-reveal>+49 30 2345 6789</a>
        </div>

        <div className="reservation__card" data-reveal data-delay="0.1">
          {state === 'done' ? (
            <div className="reservation__done" role="status">
              <span className="reservation__check" aria-hidden="true">
                <svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="25" fill="none" /><path fill="none" d="M15 27l7 7 15-16" /></svg>
              </span>
              <h3>Vielen Dank, {form.name.split(' ')[0]}.</h3>
              <p>
                Ihre Anfrage für <strong>{form.guests} {Number(form.guests) === 1 ? 'Person' : 'Personen'}</strong> am{' '}
                <strong>{fmtDate}</strong> um <strong>{form.time} Uhr</strong> ist eingegangen.
                Die Bestätigung senden wir an {form.email}.
              </p>
              <button className="link" type="button" onClick={() => { setState('idle'); setForm({ date: '', time: '', guests: 2, name: '', email: '' }); }}>
                Neue Reservierung
              </button>
            </div>
          ) : (
            <form onSubmit={submit} noValidate aria-describedby="res-hint">
              <p id="res-hint" className="visually-hidden">Alle Felder sind Pflichtfelder.</p>
              <div className="form-grid">
                <div className={`field ${errors.date ? 'has-error' : ''}`}>
                  <label htmlFor="res-date">Datum</label>
                  <input type="date" min={today} value={form.date} onChange={set('date')} required {...field('date')} />
                  {err('date')}
                </div>

                <div className={`field ${errors.guests ? 'has-error' : ''}`}>
                  <span className="field__label" id="lbl-guests">Personen</span>
                  <div className="stepper" role="group" aria-labelledby="lbl-guests">
                    <button type="button" aria-label="Eine Person weniger" disabled={form.guests <= 1}
                      onClick={() => setForm((f) => ({ ...f, guests: Math.max(1, f.guests - 1) }))}>−</button>
                    <output aria-live="polite" id="res-guests">{form.guests}</output>
                    <button type="button" aria-label="Eine Person mehr" disabled={form.guests >= 8}
                      onClick={() => setForm((f) => ({ ...f, guests: Math.min(8, f.guests + 1) }))}>+</button>
                  </div>
                </div>

                <fieldset className={`field field--full ${errors.time ? 'has-error' : ''}`}>
                  <legend className="field__label">Uhrzeit {day === 0 && <em>· Sonntagslunch</em>}</legend>
                  <div className="slots" id="res-time" tabIndex={-1} aria-describedby={errors.time ? 'err-time' : undefined}>
                    {slots.map((s) => (
                      <label key={s} className={`slot ${form.time === s ? 'is-active' : ''} ${closed ? 'is-disabled' : ''}`}>
                        <input type="radio" name="time" value={s} checked={form.time === s} onChange={set('time')} disabled={closed} />
                        <span>{s}</span>
                      </label>
                    ))}
                  </div>
                  {closed && <p className="field__hint">Montag & Dienstag ist Ruhetag.</p>}
                  {err('time')}
                </fieldset>

                <div className={`field ${errors.name ? 'has-error' : ''}`}>
                  <label htmlFor="res-name">Name</label>
                  <input type="text" autoComplete="name" value={form.name} onChange={set('name')} placeholder="Vor- und Nachname" required {...field('name')} />
                  {err('name')}
                </div>

                <div className={`field ${errors.email ? 'has-error' : ''}`}>
                  <label htmlFor="res-email">E-Mail</label>
                  <input type="email" autoComplete="email" value={form.email} onChange={set('email')} placeholder="name@beispiel.de" required {...field('email')} />
                  {err('email')}
                </div>
              </div>

              <div className="reservation__submit">
                <Button type="submit" variant="light" disabled={state === 'sending'} aria-busy={state === 'sending'}>
                  {state === 'sending' ? 'Wird gesendet …' : 'Tisch anfragen'}
                </Button>
                <p className="fine">Mit dem Absenden akzeptieren Sie unsere Datenschutzhinweise.</p>
              </div>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
