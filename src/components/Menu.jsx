import { useLayoutEffect, useRef, useState } from 'react';
import { menu, tasting } from '../lib/content.js';
import { gsap, prefersReducedMotion } from '../lib/motion.js';
import { Button, Eyebrow, Lines } from './Primitives.jsx';

export default function Menu() {
  const [tab, setTab] = useState(menu[0].id);
  const listRef = useRef(null);
  const tabsRef = useRef([]);
  const first = useRef(true);
  const current = menu.find((c) => c.id === tab);

  useLayoutEffect(() => {
    if (first.current) { first.current = false; return; }
    if (prefersReducedMotion()) return;
    gsap.fromTo(
      listRef.current.children,
      { y: 24, autoAlpha: 0 },
      { y: 0, autoAlpha: 1, duration: 0.9, ease: 'expo.out', stagger: 0.05 }
    );
  }, [tab]);

  // Pfeiltasten-Navigation gemäß WAI-ARIA Tabs-Pattern
  const onKeyDown = (e, i) => {
    const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    if (!dir) return;
    e.preventDefault();
    const next = (i + dir + menu.length) % menu.length;
    setTab(menu[next].id);
    tabsRef.current[next]?.focus();
  };

  return (
    <section className="menu section" id="speisekarte" aria-labelledby="menu-title" data-theme-light>
      <div className="container">
        <div className="menu__head">
          <Eyebrow no="03">Speisekarte</Eyebrow>
          <Lines id="menu-title" className="display" text="À la carte." />
          <p className="menu__intro" data-reveal>
            Unsere Karte wechselt mit den Jahreszeiten. Alle Preise in Euro inkl. MwSt.
            Auf Allergien und Unverträglichkeiten gehen wir gerne ein.
          </p>
        </div>

        <div className="menu__layout">
          <div>
            <div className="tabs" role="tablist" aria-label="Kategorien der Speisekarte" data-reveal>
              {menu.map((c, i) => (
                <button
                  key={c.id}
                  ref={(el) => (tabsRef.current[i] = el)}
                  role="tab"
                  id={`tab-${c.id}`}
                  aria-selected={tab === c.id}
                  aria-controls={`panel-${c.id}`}
                  tabIndex={tab === c.id ? 0 : -1}
                  className={`tab ${tab === c.id ? 'is-active' : ''}`}
                  onClick={() => setTab(c.id)}
                  onKeyDown={(e) => onKeyDown(e, i)}
                >
                  <span className="tab__no">0{i + 1}</span>
                  {c.label}
                </button>
              ))}
            </div>

            <div role="tabpanel" id={`panel-${current.id}`} aria-labelledby={`tab-${current.id}`} tabIndex={0}>
              <ul className="menu__list" ref={listRef} data-reveal-group>
                {current.items.map((item) => (
                  <li className="menu__item" key={item.name}>
                    <div className="menu__row">
                      <h3 className="menu__name">{item.name}</h3>
                      <span className="menu__dots" aria-hidden="true" />
                      <p className="menu__price"><span className="visually-hidden">Preis: </span>{item.price}<span aria-hidden="true"> €</span><span className="visually-hidden"> Euro</span></p>
                    </div>
                    <p className="menu__desc">{item.desc}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <aside className="tasting" aria-label="Degustationsmenü" data-reveal data-delay="0.15">
            <p className="tasting__label">Empfehlung des Hauses</p>
            <h3 className="tasting__title">{tasting.title}</h3>
            <p className="tasting__courses">{tasting.courses}</p>
            <p className="tasting__price">{tasting.price}<span> €</span></p>
            <p className="tasting__pairing">{tasting.pairing}</p>
            <Button to="reservierung" variant="ghost">Menü reservieren</Button>
          </aside>
        </div>
      </div>
    </section>
  );
}
