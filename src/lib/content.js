// Zentrale Inhalte – Texte, Bilder und Speisekarte an einer Stelle pflegen.

const u = (id, w = 1600) =>
  `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${w}&q=75`;

export const img = {
  hero: u('photo-1514933651103-005eec06c04b', 1920),
  interior: u('photo-1559339352-11d035aa65de', 1400),
  table: u('photo-1550966871-3ed3cdb5ed0c', 1000),
  chef: u('photo-1577219491135-ce391730fb2c', 1000),
  reservation: u('photo-1470337458703-46ad1756a187', 1920),
};

export const nav = [
  { id: 'speisekarte', label: 'Speisekarte' },
  { id: 'konzept', label: 'Konzept' },
  { id: 'galerie', label: 'Galerie' },
  { id: 'kontakt', label: 'Kontakt' },
];

export const dishes = [
  {
    no: '01',
    name: 'Jakobsmuschel',
    note: 'Topinambur · Haselnuss · brauner Butterschaum',
    text: 'Kurz auf dem Binchotan-Grill gegart, begleitet von geröstetem Topinambur und einer Nage aus Muschelsud.',
    src: u('photo-1559847844-5315695dadae', 1100),
  },
  {
    no: '02',
    name: 'Rote Bete aus dem Salzteig',
    note: 'Ziegenfrischkäse · Holunder · Roggen',
    text: 'Vierundzwanzig Stunden gereift, im Salzteig gebacken und mit fermentiertem Holunder lackiert.',
    src: u('photo-1546069901-ba9599a7e63c', 1100),
  },
  {
    no: '03',
    name: 'Dry Aged Rind',
    note: 'Schwarzer Knoblauch · Sellerie · Jus',
    text: '42 Tage am Knochen gereift, über Buchenholz gegrillt – mit Selleriecreme und eingekochtem Rinderjus.',
    src: u('photo-1544025162-d76694265947', 1100),
  },
  {
    no: '04',
    name: 'Schokolade & Rauch',
    note: 'Valrhona 70 % · geräuchertes Meersalz · Kirsche',
    text: 'Ein dunkles Finale: Ganache, Kirschsorbet und ein Hauch von Rauch, am Tisch vollendet.',
    src: u('photo-1488477181946-6428a0291777', 1100),
  },
];

export const menu = [
  {
    id: 'vorspeisen',
    label: 'Vorspeisen',
    items: [
      { name: 'Austern Gillardeau', desc: 'Gurke, Dill-Öl, Champagner-Vinaigrette', price: '24' },
      { name: 'Tatar vom Weiderind', desc: 'Eigelbcreme, Kapernblüten, Sauerteigchip', price: '22' },
      { name: 'Jakobsmuschel', desc: 'Topinambur, Haselnuss, brauner Butterschaum', price: '26' },
      { name: 'Rote Bete aus dem Salzteig', desc: 'Ziegenfrischkäse, Holunder, Roggen', price: '18' },
      { name: 'Consommé vom Steinpilz', desc: 'Liebstöckel, Eigelb, Brotchip', price: '16' },
    ],
  },
  {
    id: 'hauptgerichte',
    label: 'Hauptgerichte',
    items: [
      { name: 'Dry Aged Rind', desc: 'Schwarzer Knoblauch, Sellerie, Rinderjus', price: '48' },
      { name: 'Steinbutt', desc: 'Lauch, Beurre blanc, Imperial-Kaviar', price: '52' },
      { name: 'Müritz-Lamm', desc: 'Aubergine, Joghurt, Za’atar', price: '44' },
      { name: 'Maishendl aus dem Holzofen', desc: 'Morcheln, Spitzkohl, Vin jaune', price: '39' },
      { name: 'Kürbis & Miso', desc: 'Kürbiskernöl, Quitte, Buchweizen', price: '32' },
    ],
  },
  {
    id: 'desserts',
    label: 'Desserts',
    items: [
      { name: 'Schokolade & Rauch', desc: 'Valrhona 70 %, Kirsche, geräuchertes Salz', price: '17' },
      { name: 'Birne & Heu', desc: 'Heumilcheis, Sauerrahm, Hafer-Crumble', price: '15' },
      { name: 'Tarte au citron', desc: 'Yuzu, Baiser, Basilikum', price: '15' },
      { name: 'Käse von Maître Antony', desc: 'Drei Sorten, Feigenbrot, Quittengelee', price: '21' },
    ],
  },
];

export const tasting = {
  title: 'Degustation',
  courses: 'Sieben Gänge',
  price: '145',
  pairing: 'Weinbegleitung 85 € · Alkoholfreie Begleitung 55 €',
};

export const gallery = [
  { src: u('photo-1517248135467-4c7edcad34c4', 1400), alt: 'Gastraum mit warmem Licht und gedeckten Tischen', cls: 'g-a' },
  { src: u('photo-1414235077428-338989a2e8c0', 1000), alt: 'Angerichteter Teller mit feinen Komponenten', cls: 'g-b' },
  { src: u('photo-1466978913421-dad2ebd01d17', 1000), alt: 'Küchenchef beim Anrichten in der offenen Küche', cls: 'g-c' },
  { src: u('photo-1504674900247-0877df9cc836', 1000), alt: 'Saisonales Gericht von oben fotografiert', cls: 'g-d' },
  { src: u('photo-1555396273-367ea4eb4db5', 1400), alt: 'Restaurant-Terrasse in der Abenddämmerung', cls: 'g-e' },
  { src: u('photo-1551024601-bec78aea704b', 1000), alt: 'Dessert mit glänzender Glasur', cls: 'g-f' },
];

export const contact = {
  street: 'Linienstraße 113',
  city: '10115 Berlin-Mitte',
  phone: '+49 30 2345 6789',
  phoneHref: 'tel:+493023456789',
  email: 'tisch@noir-dining.de',
  hours: [
    ['Mittwoch – Samstag', '18:00 – 23:30'],
    ['Sonntag (Lunch)', '12:00 – 16:00'],
    ['Montag & Dienstag', 'Ruhetag'],
  ],
  socials: [
    { label: 'Instagram', href: 'https://www.instagram.com/' },
    { label: 'Facebook', href: 'https://www.facebook.com/' },
    { label: 'TikTok', href: 'https://www.tiktok.com/' },
  ],
};
