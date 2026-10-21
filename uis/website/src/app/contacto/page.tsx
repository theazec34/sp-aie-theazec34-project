import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/PageHero";
import { hours, restaurant } from "@/data/site";

export const metadata: Metadata = {
  title: "Contacto",
  description: "Dirección, teléfono y correo de Brasaland.",
};

export default function ContactoPage() {
  return (
    <>
      <PageHero
        eyebrow="Contacto"
        title="Estamos en Sevilla"
        description="Escríbenos o llámanos para reservas, eventos y consultas de alérgenos."
      />
      <section className="section">
        <div className="container contact-grid">
          <div className="feature-tile">
            <h2>Dirección</h2>
            <p>{restaurant.address}</p>
            <p className="field-hint">
              [Mapa embebido pendiente — añadir cuando haya ficha Google Maps definitiva]
            </p>
          </div>
          <div className="feature-tile">
            <h2>Teléfono y correo</h2>
            <p>
              <a href={`tel:${restaurant.phone.replace(/\s/g, "")}`}>
                {restaurant.phone}
                {restaurant.phoneIsPlaceholder ? " [provisional]" : ""}
              </a>
            </p>
            <p>
              <a href={`mailto:${restaurant.email}`}>{restaurant.email}</a>
            </p>
          </div>
          <div className="feature-tile">
            <h2>Horario</h2>
            <ul className="plain-list">
              {hours.lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            {hours.provisional ? (
              <p className="field-hint">Horario orientativo — confirmar en el local.</p>
            ) : null}
          </div>
        </div>
        <p className="section-cta-row">
          <Link className="cta" href="/reservas">
            Reservar mesa
          </Link>
        </p>
      </section>
    </>
  );
}
