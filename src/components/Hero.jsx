import { useLayoutEffect, useRef } from 'react';
import { img } from '../lib/content.js';
import { gsap, prefersReducedMotion, scrollToId } from '../lib/motion.js';
import { Button } from './Primitives.jsx';

export default function Hero({ ready }) {
  const root = useRef(null);

  // Parallax + leichtes Ausblenden beim Herausscrollen
  useLayoutEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      gsap.to('.hero__media', {
        yPercent: 22,
        ease: 'none',
        scrollTrigger: { trigger: root.current, start: 'top top', end: 'bottom top', scrub: true },
      });
      gsap.to('.hero__content', {
        yPercent: -30,
        autoAlpha: 0,
        ease: 'none',
        scrollTrigger: { trigger: root.current, start: 'top top', end: '70% top', scrub: true },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  // Intro-Sequenz nach dem Preloader
  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      if (prefersReducedMotion()) {
        gsap.set('.hero [data-intro]', { autoAlpha: ready ? 1 : 0 });
        return;
      }
      if (!ready) {
        gsap.set('.hero__letter', { yPercent: 110 });
        gsap.set('.hero [data-intro]', { autoAlpha: 0, y: 24 });
        gsap.set('.hero__img', { scale: 1.25 });
        return;
      }
      const tl = gsap.timeline({ defaults: { ease: 'expo.out' } });
      tl.to('.hero__img', { scale: 1, duration: 2.6 }, 0)
        .to('.hero__letter', { yPercent: 0, duration: 1.6, stagger: 0.08 }, 0.15)
        .to('.hero [data-intro]', { autoAlpha: 1, y: 0, duration: 1.4, stagger: 0.1 }, 0.7);
    }, root);
    return () => ctx.revert();
  }, [ready]);

  return (
    <section className="hero" id="top" ref={root} aria-labelledby="hero-title">
      <div className="hero__media" aria-hidden="true">
        <img className="hero__img" src={img.hero} alt="" fetchpriority="high" decoding="async" />
        <div className="hero__shade" />
      </div>

      <div className="hero__content">
        <p className="hero__kicker" data-intro>
          <span>Est. 2019</span>
          <span className="hero__kicker-rule" aria-hidden="true" />
          <span>Berlin-Mitte</span>
        </p>
        <h1 id="hero-title" className="hero__title">
          <span className="visually-hidden">NOIR – Modern Dining</span>
          <span aria-hidden="true" className="hero__word">
            {'NOIR'.split('').map((l, i) => (
              <span className="hero__mask" key={i}><span className="hero__letter">{l}</span></span>
            ))}
          </span>
        </h1>
        <p className="hero__sub" data-intro>A different taste of dining.</p>
        <div className="hero__actions" data-intro>
          <Button to="reservierung">Tisch reservieren</Button>
        </div>
      </div>

      <div className="hero__foot">
        <p data-intro className="hero__note">
          Saisonale Küche, offenes Feuer<br />und eine Weinkarte mit Haltung.
        </p>
        <a href="#konzept" className="hero__scroll" data-intro onClick={(e) => { e.preventDefault(); scrollToId('konzept'); }}>
          <span>Entdecken</span>
          <span className="hero__scroll-line" aria-hidden="true" />
        </a>
        <p data-intro className="hero__hours">Mi – Sa · ab 18 Uhr</p>
      </div>
    </section>
  );
}
