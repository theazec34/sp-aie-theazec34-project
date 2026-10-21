import type { Metadata } from "next";
import Link from "next/link";
import { PageHero } from "@/components/PageHero";
import { hours, mapsEmbedSrc, restaurant } from "@/data/site";

export const metadata: Metadata = {
  title: "Contacto",
  description: "Dirección, teléfono, mapa y horarios de Brasaland en Sevilla.",
};

export default function ContactoPage() {
  return (
    <>
      <PageHero
        eyebrow="Contacto"
        title="Estamos en Sevilla"
        description="Escríbenos o llámanos para reservas, eventos y consultas de alérgenos."
        imageSrc="/Imagenes/banner-contacto.jpg"
        imageAlt="Brasaland Sevilla"
        align="center"
      />

      <section className="section">
        <div className="container">
          <div className="contact-highlights">
            <article className="contact-stat">
              <p className="info-label">Dirección</p>
              <p className="contact-stat-value">{restaurant.address}</p>
            </article>
            <article className="contact-stat">
              <p className="info-label">Teléfono</p>
              <p className="contact-stat-value">
                <a href={`tel:${restaurant.phone.replace(/\s/g, "")}`}>{restaurant.phone}</a>
              </p>
            </article>
            <article className="contact-stat">
              <p className="info-label">Correo</p>
              <p className="contact-stat-value">
                <a href={`mailto:${restaurant.email}`}>{restaurant.email}</a>
              </p>
            </article>
          </div>

          <div className="map-block">
            <h2 className="section-title">Cómo llegar</h2>
            <p className="section-text section-text-center">
              Calle de la Brasa, 14 — Sevilla. Abre el mapa para rutas en coche o a pie.
            </p>
            <div className="map-frame">
              <iframe
                title="Mapa de Brasaland en Google Maps"
                src={mapsEmbedSrc}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                allowFullScreen
              />
            </div>
            <p className="section-cta-row section-cta-center">
              <a
                className="cta cta-ghost"
                href="https://www.google.com/maps/search/?api=1&query=Calle+de+la+Brasa+14+Sevilla"
                target="_blank"
                rel="noopener noreferrer"
              >
                Abrir en Google Maps
              </a>
            </p>
          </div>

          <div className="contact-hours">
            <h2 className="section-title">Horario</h2>
            <ul className="plain-list hours-list">
              {hours.lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>

          <p className="section-cta-row section-cta-center">
            <Link className="cta" href="/reservas">
              Reservar mesa
            </Link>
          </p>
        </div>
      </section>
    </>
  );
}
