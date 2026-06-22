interface HeroProps {
  title: string;
  subtitle: string;
}

export function Hero({ title, subtitle }: HeroProps) {
  return (
    <section id="inicio" className="hero">
      <div className="container hero-grid">
        <div>
          <p className="hero-kicker">Brasaland · Sevilla</p>
          <h1 className="hero-title">{title}</h1>
          <p className="hero-subtitle">{subtitle}</p>
          <a className="cta" href="#carta">
            Ver carta completa
          </a>
        </div>
        <aside className="hero-card" aria-label="Resumen operativo">
          <h2 className="card-title">Experiencia Brasaland completa en Next.js</h2>
          <p className="card-text">
            Sabores de brasa, carta visual y reservas en una experiencia digital alineada con la identidad real del restaurante.
          </p>
        </aside>
      </div>
    </section>
  );
}
