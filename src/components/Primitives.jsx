import { Fragment, useState } from 'react';
import { scrollToId } from '../lib/motion.js';

/** Überschrift, deren Wörter einzeln aus einer Maske aufsteigen. */
export function Lines({ as: Tag = 'h2', text, className = '', ...rest }) {
  const parts = text.split(/(\n)/);
  return (
    <Tag className={`lines ${className}`} data-lines {...rest}>
      {parts.map((part, i) =>
        part === '\n' ? (
          <br key={i} />
        ) : (
          part
            .split(' ')
            .filter(Boolean)
            .map((word, j) => (
              <Fragment key={`${i}-${j}`}>
                <span className="w"><span>{word}</span></span>{' '}
              </Fragment>
            ))
        )
      )}
    </Tag>
  );
}

/** Bildrahmen mit Reveal-Animation, Lazy Loading und elegantem Fallback. */
export function Frame({ src, alt, className = '', parallax, eager = false, sizes = '100vw' }) {
  const [broken, setBroken] = useState(false);
  return (
    <figure className={`frame ${broken ? 'is-broken' : ''} ${className}`} data-img data-parallax-wrap>
      {!broken && (
        <img
          src={src}
          alt={alt}
          sizes={sizes}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
          onError={() => setBroken(true)}
          {...(parallax ? { 'data-parallax': parallax } : {})}
        />
      )}
      {broken && <span className="visually-hidden">{alt}</span>}
    </figure>
  );
}

/** Kleines Sektions-Label, z. B. „01 — Das Haus". */
export function Eyebrow({ no, children }) {
  return (
    <p className="eyebrow" data-reveal>
      <span className="eyebrow__no">{no}</span>
      <span className="eyebrow__rule" aria-hidden="true" />
      <span>{children}</span>
    </p>
  );
}

/** Button mit Füll-Animation; navigiert weich zu einem Anker. */
export function Button({ to, children, variant = 'solid', type, onClick, ...rest }) {
  const handle = (e) => {
    if (to) {
      e.preventDefault();
      scrollToId(to);
    }
    onClick?.(e);
  };
  const Tag = to ? 'a' : 'button';
  return (
    <Tag
      className={`btn btn--${variant}`}
      href={to ? `#${to}` : undefined}
      type={Tag === 'button' ? type || 'button' : undefined}
      onClick={handle}
      {...rest}
    >
      <span className="btn__label" data-text={typeof children === 'string' ? children : undefined}>
        <span>{children}</span>
      </span>
      <span className="btn__arrow" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="1.4" /></svg>
      </span>
    </Tag>
  );
}
