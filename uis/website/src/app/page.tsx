import Image from "next/image";
import Link from "next/link";
import { FeaturedDishes } from "@/components/FeaturedDishes";
import { GalleryGrid } from "@/components/GalleryGrid";
import { Hero } from "@/components/Hero";
import { InfoStrip } from "@/components/InfoStrip";
import { SectionTitle } from "@/components/SectionTitle";
import { experiencePoints, hours, philosophy, restaurant } from "@/data/site";

export default function HomePage() {
  return (
    <>
      <Hero
        title="El fuego nos une. El sabor nos define."
        subtitle="Carnes a la brasa que fusionan la gastronomía sudamericana con la tradición ibérica: producto, paciencia y mesa generosa en el corazón de Sevilla."
      />
      <InfoStrip />
      <FeaturedDishes />

      <section className="section section-carbon" aria-labelledby="philosophy-title">
        <div className="container split">
          <div className="split-copy reveal">
            <SectionTitle
              id="philosophy-title"
              eyebrow="Filosofía"
              title={philosophy.title}
              description={philosophy.body}
            />
            <Link className="cta cta-ghost-light" href="/nosotros">
              Nuestra historia
            </Link>
          </div>
          <div className="split-media">
            <Image
              src="/Imagenes/Entrana-argentina.jpg"
              alt="Entraña a la brasa"
              width={960}
              height={720}
              className="split-image"
              sizes="(max-width: 900px) 100vw, 48vw"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="experience-title">
        <div className="container">
          <SectionTitle
            id="experience-title"
            eyebrow="Experiencia"
            title="Una noche en Brasaland"
            description="Brasa, sala y ritmo de restaurante: ven a comer, quédate a conversar."
          />
          <ol className="experience-rail">
            {experiencePoints.map((item, index) => (
              <li key={item.id} className="experience-item">
                <span className="experience-index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section section-soft" aria-labelledby="home-gallery-title">
        <div className="container">
          <SectionTitle
            id="home-gallery-title"
            eyebrow="Galería"
            title="Fuego, plato y atmósfera"
            description="Fotografías reales del proyecto Brasaland."
          />
          <GalleryGrid limit={6} />
          <p className="section-cta-row">
            <Link className="cta cta-ghost" href="/galeria">
              Ver galería completa
            </Link>
          </p>
        </div>
      </section>

      <section className="section" aria-labelledby="location-title">
        <div className="container split">
          <div className="split-copy">
            <SectionTitle
              id="location-title"
              eyebrow="Ubicación"
              title="Te esperamos en Sevilla"
              description={`${restaurant.address}. Escríbenos a ${restaurant.email} o solicita mesa desde reservas.`}
            />
            <ul className="plain-list">
              {hours.lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            {hours.provisional ? (
              <p className="field-hint">Horario orientativo — confirmar en el local.</p>
            ) : null}
            <p className="section-cta-row">
              <Link className="cta" href="/reservas">
                Reservar mesa
              </Link>
              <Link className="cta cta-ghost" href="/contacto">
                Contacto
              </Link>
            </p>
          </div>
          <div className="split-media">
            <Image
              src="/Imagenes/Tabla ibericos.jpg"
              alt="Tabla ibérica Brasaland"
              width={960}
              height={720}
              className="split-image"
              sizes="(max-width: 900px) 100vw, 48vw"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      <section className="section section-cta-band" aria-labelledby="home-cta-title">
        <div className="container cta-band">
          <div>
            <h2 id="home-cta-title">Reserva tu mesa</h2>
            <p>
              {restaurant.address} ·{" "}
              <a href={`mailto:${restaurant.email}`}>{restaurant.email}</a>
            </p>
          </div>
          <div className="hero-cta-row">
            <Link className="cta" href="/reservas">
              Reservar mesa
            </Link>
            <Link className="cta cta-ghost-light" href="/carta">
              Descubrir la carta
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
