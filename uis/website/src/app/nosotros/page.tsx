import type { Metadata } from "next";
import Image from "next/image";
import { PageHero } from "@/components/PageHero";
import { experiencePoints, philosophy } from "@/data/site";

export const metadata: Metadata = {
  title: "Nosotros",
  description: "Historia y filosofía de Brasaland: brasa sudamericana y tradición ibérica.",
};

export default function NosotrosPage() {
  return (
    <>
      <PageHero
        eyebrow="Nosotros"
        title="De la parrilla al alma ibérica"
        description={philosophy.body}
      />
      <section className="section">
        <div className="container split">
          <div className="split-media">
            <Image
              src="/Imagenes/Tabla ibericos.jpg"
              alt="Tabla de ibéricos Brasaland"
              width={960}
              height={720}
              className="split-image"
              sizes="(max-width: 900px) 100vw, 48vw"
            />
          </div>
          <div className="split-copy">
            <h2 className="section-title">{philosophy.title}</h2>
            <p className="section-text">
              Cocinar a la brasa es un oficio de atención: el corte, el fuego y el tiempo.
              En Brasaland ese oficio se encuentra con jamones, arroces y postres que
              recuerdan dos orillas de la misma mesa.
            </p>
            <ul className="plain-list">
              {experiencePoints.map((p) => (
                <li key={p.id}>
                  <strong>{p.title}.</strong> {p.description}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}
