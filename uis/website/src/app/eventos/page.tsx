import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { PageHero } from "@/components/PageHero";
import { eventOfferings, restaurant } from "@/data/site";

export const metadata: Metadata = {
  title: "Eventos",
  description: "Eventos privados, grupos y noches con flamenco en Brasaland.",
};

export default function EventosPage() {
  return (
    <>
      <PageHero
        eyebrow="Eventos"
        title="Mesas para celebrar"
        description="Grupos, celebraciones y propuestas a medida alrededor de la brasa — con ritmo, fuego y sala."
        imageSrc="/Imagenes/eventos-flamenco-hq.jpg"
        imageAlt="Actuación de flamenco en ambiente de restaurante"
        align="center"
      />

      <section className="section">
        <div className="container section-center">
          <p className="section-eyebrow">Lo que organizamos</p>
          <h2 className="section-title">Fuego, mesa y escena</h2>
          <p className="section-text section-text-center">
            Desde cenas de equipo hasta noches con actuación en vivo: diseñamos la experiencia
            contigo.
          </p>
          <div className="grid-3 media-cards">
            {eventOfferings.map((item) => (
              <article key={item.id} className="media-card">
                <div className="media-card-image">
                  <Image
                    src={item.image}
                    alt={item.title}
                    width={900}
                    height={600}
                    sizes="(max-width: 900px) 100vw, 33vw"
                    loading="lazy"
                  />
                </div>
                <div className="media-card-body">
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>
              </article>
            ))}
          </div>
          <p className="section-cta-row section-cta-center">
            <Link className="cta" href={`mailto:${restaurant.email}?subject=Evento%20Brasaland`}>
              Consultar disponibilidad
            </Link>
            <Link className="cta cta-ghost" href="/contacto">
              Contacto
            </Link>
          </p>
        </div>
      </section>

      <section className="section section-carbon">
        <div className="container split">
          <div className="split-media">
            <Image
              src="/Imagenes/eventos-actuacion-hq.jpg"
              alt="Actuación en vivo en Brasaland"
              width={960}
              height={640}
              className="split-image"
              sizes="(max-width: 900px) 100vw, 48vw"
              loading="lazy"
            />
          </div>
          <div className="split-copy">
            <p className="section-eyebrow page-hero-eyebrow">En vivo</p>
            <h2 className="section-title">Noches que se quedan</h2>
            <p className="section-text">
              Flamenco, guitarra y brasa: el local se transforma para celebraciones íntimas o
              grupos que buscan algo más que una cena.
            </p>
            <Link className="cta cta-ghost-light" href="/reservas">
              Reservar mesa
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
