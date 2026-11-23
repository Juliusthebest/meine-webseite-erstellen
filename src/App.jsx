import { useCallback, useEffect, useState } from 'react';
import Preloader from './components/Preloader.jsx';
import Nav from './components/Nav.jsx';
import Hero from './components/Hero.jsx';
import About from './components/About.jsx';
import Kitchen from './components/Kitchen.jsx';
import Marquee from './components/Marquee.jsx';
import Menu from './components/Menu.jsx';
import Gallery from './components/Gallery.jsx';
import Reservation from './components/Reservation.jsx';
import Contact from './components/Contact.jsx';
import Footer from './components/Footer.jsx';
import Legal from './components/Legal.jsx';
import { initScrollAnimations, initSmoothScroll, lockScroll, scrollToId } from './lib/motion.js';

export default function App() {
  const [loading, setLoading] = useState(true);
  const [legal, setLegal] = useState(null);

  useEffect(() => {
    history.scrollRestoration = 'manual';
    window.scrollTo(0, 0);
    initSmoothScroll();
    lockScroll(true);
  }, []);

  const done = useCallback(() => {
    setLoading(false);
    lockScroll(false);
  }, []);

  useEffect(() => {
    if (loading) return;
    const cleanup = initScrollAnimations();
    const hash = location.hash.slice(1);
    if (hash) setTimeout(() => scrollToId(hash), 300);
    return cleanup;
  }, [loading]);

  return (
    <>
      <a className="skip" href="#main">Zum Inhalt springen</a>
      {loading && <Preloader onDone={done} />}
      <Nav />
      <main id="main">
        <Hero ready={!loading} />
        <About />
        <Kitchen />
        <Marquee words={['Saisonal', 'Regional', 'Handwerklich', 'Feuer', 'Zeit']} />
        <Menu />
        <Gallery />
        <Reservation />
        <Contact />
      </main>
      <Footer onLegal={setLegal} />
      <Legal open={legal} onClose={() => setLegal(null)} />
      <div className="grain" aria-hidden="true" />
    </>
  );
}
