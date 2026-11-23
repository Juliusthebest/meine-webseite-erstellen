import { useEffect, useRef, useState } from 'react';
import { nav } from '../lib/content.js';
import { scrollToId, lockScroll, gsap, prefersReducedMotion } from '../lib/motion.js';

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState('');
  const overlay = useRef(null);
  const toggleRef = useRef(null);

  // Navigation verändert sich beim Scrollen: Hintergrund + Ein-/Ausblenden je nach Richtung
  useEffect(() => {
    let last = window.scrollY;
    const onScroll = () => {
      const y = window.scrollY;
      setScrolled(y > 60);
      setHidden(y > last && y > window.innerHeight * 0.8);
      last = y;
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Aktiven Bereich markieren
  useEffect(() => {
    const ids = ['konzept', 'kueche', 'speisekarte', 'galerie', 'reservierung', 'kontakt'];
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-45% 0px -50% 0px' }
    );
    ids.forEach((id) => {
      const el = document.getElementById(id);
      el && io.observe(el);
    });
    return () => io.disconnect();
  }, []);

  // Mobiles Vollbild-Menü
  useEffect(() => {
    const el = overlay.current;
    lockScroll(open);
    if (!el) return;
    const reduce = prefersReducedMotion();
    if (open) {
      gsap.set(el, { visibility: 'visible' });
      gsap.fromTo(el, { clipPath: 'inset(0% 0% 100% 0%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: reduce ? 0 : 0.9, ease: 'expo.inOut' });
      gsap.fromTo(el.querySelectorAll('.overlay__link > span'), { yPercent: 110 }, { yPercent: 0, duration: reduce ? 0 : 1, ease: 'expo.out', stagger: 0.06, delay: reduce ? 0 : 0.35 });
      el.querySelector('a')?.focus();
    } else {
      gsap.to(el, { clipPath: 'inset(0% 0% 100% 0%)', duration: reduce ? 0 : 0.7, ease: 'expo.inOut', onComplete: () => gsap.set(el, { visibility: 'hidden' }) });
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        toggleRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  const go = (id) => (e) => {
    e.preventDefault();
    setOpen(false);
    setTimeout(() => scrollToId(id), open ? 350 : 0);
  };

  return (
    <>
      <header className={`nav ${scrolled ? 'is-scrolled' : ''} ${hidden && !open ? 'is-hidden' : ''} ${open ? 'is-open' : ''}`}>
        <div className="nav__inner">
          <a href="#top" className="nav__logo" onClick={go('top')} aria-label="NOIR – zum Seitenanfang">
            NOIR<span className="nav__logo-dot" aria-hidden="true">.</span>
          </a>
          <nav aria-label="Hauptnavigation" className="nav__links">
            <ul>
              {nav.map((item) => (
                <li key={item.id}>
                  <a
                    href={`#${item.id}`}
                    onClick={go(item.id)}
                    className={active === item.id || (item.id === 'konzept' && active === 'kueche') ? 'is-active' : ''}
                    aria-current={active === item.id ? 'true' : undefined}
                  >
                    <span className="nav__label"><span data-text={item.label}>{item.label}</span></span>
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <a href="#reservierung" onClick={go('reservierung')} className="nav__cta">
            Reservieren
          </a>
          <button
            ref={toggleRef}
            className="nav__toggle"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? 'Menü schließen' : 'Menü öffnen'}
            onClick={() => setOpen((o) => !o)}
          >
            <span /><span />
          </button>
        </div>
      </header>

      <div id="mobile-menu" className="overlay" ref={overlay} aria-hidden={!open} inert={!open ? true : undefined}>
        <nav aria-label="Mobile Navigation">
          <ul>
            {[...nav, { id: 'reservierung', label: 'Reservieren' }].map((item, i) => (
              <li key={item.id}>
                <a className="overlay__link" href={`#${item.id}`} onClick={go(item.id)}>
                  <span><em>0{i + 1}</em>{item.label}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <p className="overlay__foot">Linienstraße 113 · Berlin-Mitte</p>
      </div>
    </>
  );
}
