export default function Marquee({ words }) {
  const row = words.map((w, i) => (
    <span key={i} className={i % 2 ? 'marquee__outline' : ''}>
      {w}<i aria-hidden="true">✦</i>
    </span>
  ));
  return (
    <div className="marquee" aria-hidden="true">
      <div className="marquee__track" data-marquee>
        {row}{row}
      </div>
    </div>
  );
}
