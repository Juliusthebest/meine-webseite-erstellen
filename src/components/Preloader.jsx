import { useLayoutEffect, useRef } from 'react';
import { gsap, prefersReducedMotion } from '../lib/motion.js';

/** Eleganter Ladebildschirm: Zähler, Wortmarke, dann hebt sich der Vorhang. */
export default function Preloader({ onDone }) {
  const root = useRef(null);

  useLayoutEffect(() => {
    const el = root.current;
    if (prefersReducedMotion()) {
      const t = gsap.to(el, { autoAlpha: 0, duration: 0.4, delay: 0.2, onComplete: onDone });
      return () => t.kill();
    }
    const counter = { v: 0 };
    const num = el.querySelector('.preloader__count');
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ onComplete: onDone });
      tl.from('.preloader__letter', { yPercent: 120, duration: 1.1, ease: 'expo.out', stagger: 0.07 })
        .to(counter, {
          v: 100,
          duration: 1.6,
          ease: 'power2.inOut',
          onUpdate: () => (num.textContent = String(Math.round(counter.v)).padStart(3, '0')),
        }, 0)
        .fromTo('.preloader__bar', { scaleX: 0 }, { scaleX: 1, duration: 1.6, ease: 'power2.inOut' }, 0)
        .to('.preloader__letter', { yPercent: -120, duration: 0.8, ease: 'expo.in', stagger: 0.04 }, '+=0.15')
        .to('.preloader__meta', { autoAlpha: 0, duration: 0.4 }, '<')
        .to(el, { clipPath: 'inset(0% 0% 100% 0%)', duration: 1.1, ease: 'expo.inOut' }, '-=0.25');
    }, el);
    return () => ctx.revert();
  }, [onDone]);

  return (
    <div className="preloader" ref={root} role="status" aria-live="polite">
      <span className="visually-hidden">NOIR wird geladen</span>
      <div className="preloader__mark" aria-hidden="true">
        {'NOIR'.split('').map((l, i) => (
          <span className="preloader__mask" key={i}>
            <span className="preloader__letter">{l}</span>
          </span>
        ))}
      </div>
      <div className="preloader__meta" aria-hidden="true">
        <span>Modern Dining · Berlin</span>
        <span className="preloader__track"><span className="preloader__bar" /></span>
        <span className="preloader__count">000</span>
      </div>
    </div>
  );
}
