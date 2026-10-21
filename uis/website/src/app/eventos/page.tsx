import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/PageHero";
import { eventOfferings, restaurant } from "@/data/site";

export const metadata: Metadata = {
  title: "Eventos",
  description: "Eventos privados y grupos en Brasaland.",
};

export default function EventosPage() {
  return (
    <>
      <PageHero
        eyebrow="Eventos"
        title="Mesas para celebrar"
        description="Grupos, celebraciones y propuestas a medida alrededor de la brasa."
      />
      <section className="section">
        <div className="container">
          <div className="grid-3">
            {eventOfferings.map((item) => (
              <article key={item.id} className="feature-tile">
                <h2>{item.title}</h2>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
          <p className="section-cta-row">
            <Link className="cta" href={`mailto:${restaurant.email}?subject=Evento%20Brasaland`}>
              Consultar disponibilidad
            </Link>
            <Link className="cta cta-ghost" href="/contacto">
              Contacto
            </Link>
          </p>
        </div>
      </section>
    </>
  );
}
