import type { Metadata } from "next";
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
        description="Buscamos personas con ritmo, respeto al producto y ganas de hospitalidad real. Cultura de equipo, turnos exigentes y cocina con carácter."
      />
      <section className="section section-soft">
        <div className="container">
          <h2 className="section-title">Perfiles que buscamos</h2>
          <div className="grid-3">
            {jobRoles.map((role) => (
              <article key={role.id} className="feature-tile">
                <h3>{role.title}</h3>
                <p>{role.blurb}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      <section className="section" aria-labelledby="job-form-title">
        <div className="container narrow">
          <h2 id="job-form-title" className="section-title">
            Envía tu candidatura
          </h2>
          <JobApplicationForm />
        </div>
      </section>
    </>
  );
}
