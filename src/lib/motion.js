import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);

export const EASE = 'expo.out';
export const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let lenis = null;

/** Weiches Scrollen (nur, wenn keine reduzierte Bewegung gewünscht ist). */
export function initSmoothScroll() {
  if (prefersReducedMotion() || lenis) return lenis;
  lenis = new Lenis({ duration: 1.15, easing: (t) => 1 - Math.pow(1 - t, 4) });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((time) => lenis && lenis.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);
  return lenis;
}

export const lockScroll = (locked) => {
  document.documentElement.classList.toggle('is-locked', locked);
  if (!lenis) return;
  locked ? lenis.stop() : lenis.start();
};

/** Sanft zu einem Anker scrollen und den Fokus für Tastatur/Screenreader setzen. */
export function scrollToId(id) {
  const el = id === 'top' ? document.body : document.getElementById(id);
  if (!el) return;
  const done = () => {
    const target = id === 'top' ? document.getElementById('main') : el;
    if (target) {
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
    }
  };
  if (lenis) {
    lenis.scrollTo(id === 'top' ? 0 : el, { duration: 1.6, onComplete: done });
  } else {
    el.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
    done();
  }
  history.replaceState(null, '', id === 'top' ? '#' : `#${id}`);
}

/**
 * Alle deklarativen Scroll-Animationen registrieren:
 *  [data-reveal]        – Text gleitet sanft von unten herein
 *  [data-reveal-group]  – Kinder erscheinen zeitlich versetzt
 *  [data-lines]         – Überschriften: Wörter steigen aus einer Maske
 *  [data-img]           – Bilder: Vorhang öffnet sich, Bild zoomt langsam heraus
 *  [data-parallax]      – dezente Parallax-Verschiebung
 */
export function initScrollAnimations(root = document) {
  const mm = gsap.matchMedia();

  mm.add('(prefers-reduced-motion: no-preference)', () => {
    root.querySelectorAll('[data-lines]').forEach((el) => {
      const words = el.querySelectorAll('.w > span');
      gsap.fromTo(
        words,
        { yPercent: 110 },
        {
          yPercent: 0,
          duration: 1.3,
          ease: EASE,
          stagger: 0.06,
          scrollTrigger: { trigger: el, start: 'top 85%', once: true },
        }
      );
    });

    root.querySelectorAll('[data-reveal]').forEach((el) => {
      gsap.fromTo(
        el,
        { y: 40, autoAlpha: 0 },
        {
          y: 0,
          autoAlpha: 1,
          duration: 1.4,
          ease: EASE,
          delay: parseFloat(el.dataset.delay || 0),
          scrollTrigger: { trigger: el, start: 'top 88%', once: true },
        }
      );
    });

    root.querySelectorAll('[data-reveal-group]').forEach((group) => {
      gsap.fromTo(
        group.children,
        { y: 50, autoAlpha: 0 },
        {
          y: 0,
          autoAlpha: 1,
          duration: 1.3,
          ease: EASE,
          stagger: 0.12,
          scrollTrigger: { trigger: group, start: 'top 85%', once: true },
        }
      );
    });

    root.querySelectorAll('[data-img]').forEach((frame) => {
      const media = frame.querySelector('img');
      const tl = gsap.timeline({
        scrollTrigger: { trigger: frame, start: 'top 88%', once: true },
      });
      tl.fromTo(
        frame,
        { clipPath: 'inset(100% 0% 0% 0%)' },
        { clipPath: 'inset(0% 0% 0% 0%)', duration: 1.6, ease: 'expo.inOut' }
      ).fromTo(
        media,
        { scale: 1.35 },
        { scale: 1, duration: 2.2, ease: EASE },
        0
      );
    });

    root.querySelectorAll('[data-parallax]').forEach((el) => {
      const amount = parseFloat(el.dataset.parallax || 12);
      gsap.fromTo(
        el,
        { yPercent: -amount },
        {
          yPercent: amount,
          ease: 'none',
          scrollTrigger: {
            trigger: el.closest('[data-parallax-wrap]') || el.parentElement,
            start: 'top bottom',
            end: 'bottom top',
            scrub: true,
          },
        }
      );
    });

    // Laufband: bewegt sich gekoppelt an die Scrollrichtung
    root.querySelectorAll('[data-marquee]').forEach((el) => {
      gsap.fromTo(
        el,
        { xPercent: 0 },
        {
          xPercent: -30,
          ease: 'none',
          scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: 0.6 },
        }
      );
    });

    // Farbübergang: dunkel → creme → dunkel rund um die Speisekarte
    const light = root.querySelector('[data-theme-light]');
    if (light) {
      ScrollTrigger.create({
        trigger: light,
        start: 'top 55%',
        end: 'bottom 45%',
        onToggle: (self) => document.body.classList.toggle('theme-light', self.isActive),
      });
    }
  });

  ScrollTrigger.refresh();
  return () => mm.revert();
}

export { gsap, ScrollTrigger };
