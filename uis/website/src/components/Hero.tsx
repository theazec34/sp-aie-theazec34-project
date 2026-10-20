interface HeroProps {
  title: string;
  subtitle: string;
}

export function Hero({ title, subtitle }: HeroProps) {
  return (
    <section id="inicio" className="hero">
      <div className="hero-atmosphere" aria-hidden="true" />
      <div className="container hero-grid">
        <div className="hero-copy">
          <p className="hero-brand">Brasaland</p>
          <h1 className="hero-title">{title}</h1>
          <p className="hero-subtitle">{subtitle}</p>
          <div className="hero-cta-row">
            <a className="cta" href="#carta">
              Ver la carta
            </a>
            <a className="cta cta-ghost" href="#aplicar">
              Reservar mesa
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
