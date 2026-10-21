import type { Metadata } from "next";
import Image from "next/image";
import { JobApplicationForm } from "@/components/JobApplicationForm";
import { PageHero } from "@/components/PageHero";
import { jobRoles } from "@/data/site";

export const metadata: Metadata = {
  title: "Trabaja con nosotros",
  description: "Candidaturas Brasaland: sala, cocina y operaciones.",
};

export default function EmpleoPage() {
  return (
    <>
      <PageHero
        eyebrow="Empleo"
        title="Gente de brasa y de sala"
        description="Buscamos personas con ritmo, respeto al producto y ganas de hospitalidad real."
        imageSrc="/Imagenes/empleo-sala-hq.jpg"
        imageAlt="Sala de restaurante con equipo de servicio"
        align="center"
      />

      <section className="section section-soft">
        <div className="container section-center">
          <p className="section-eyebrow">Equipo</p>
          <h2 className="section-title">Perfiles que buscamos</h2>
          <p className="section-text section-text-center">
            Sala, parrilla y operaciones: tres formas de hacer Brasaland cada servicio.
          </p>
          <div className="grid-3 media-cards">
            {jobRoles.map((role) => (
              <article key={role.id} className="media-card">
                <div className="media-card-image">
                  <Image
                    src={role.image}
                    alt={role.title}
                    width={900}
                    height={600}
                    sizes="(max-width: 900px) 100vw, 33vw"
                    loading="lazy"
                  />
                </div>
                <div className="media-card-body">
                  <h3>{role.title}</h3>
                  <p>{role.blurb}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container split">
          <div className="split-copy section-center-mobile">
            <p className="section-eyebrow">Cocina</p>
            <h2 className="section-title">El corazón son las brasas</h2>
            <p className="section-text">
              Turnos exigentes, producto cuidado y un equipo que entiende el fuego como oficio.
            </p>
          </div>
          <div className="split-media">
            <Image
              src="/Imagenes/empleo-cocina-hq.jpg"
              alt="Cocina con parrilla y brasas"
              width={960}
              height={640}
              className="split-image"
              sizes="(max-width: 900px) 100vw, 48vw"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      <section className="section section-soft" aria-labelledby="job-form-title">
        <div className="container narrow">
          <header className="section-center">
            <p className="section-eyebrow">Candidatura</p>
            <h2 id="job-form-title" className="section-title">
              Envía tu candidatura
            </h2>
            <p className="section-text section-text-center">
              Cuéntanos quién eres. Revisamos cada solicitud con calma.
            </p>
          </header>
          <JobApplicationForm />
        </div>
      </section>
    </>
  );
}
