import Image from "next/image";
import Link from "next/link";

interface HeroProps {
  title: string;
  subtitle: string;
  imageSrc?: string;
  imageAlt?: string;
}

export function Hero({
  title,
  subtitle,
  imageSrc = "/Imagenes/Corte carne.jpg",
  imageAlt = "Corte de carne a la brasa en Brasaland",
}: HeroProps) {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-media" aria-hidden="true">
        <Image
          src={imageSrc}
          alt={imageAlt}
          fill
          priority
          sizes="100vw"
          className="hero-image"
        />
        <div className="hero-overlay" />
      </div>

      <div className="container hero-grid">
        <div className="hero-copy reveal">
          <p className="hero-brand">Brasaland</p>
          <h1 id="hero-title" className="hero-title">
            {title}
          </h1>
          <p className="hero-subtitle">{subtitle}</p>
          <div className="hero-cta-row">
            <Link className="cta" href="/carta">
              Descubrir la carta
            </Link>
            <Link className="cta cta-ghost" href="/reservas">
              Reservar mesa
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
