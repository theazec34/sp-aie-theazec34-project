import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";
import { company } from "@/data/site";

export const metadata: Metadata = { title: "Aviso legal" };

export default function AvisoLegalPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Aviso legal"
        description={`${company.legalName} — información del titular del sitio.`}
        align="center"
      />
      <section className="section">
        <div className="container narrow prose">
          <p>
            <strong>Razón Social:</strong> {company.legalName}
          </p>
          <p>
            <strong>NIF:</strong> {company.nif}
          </p>
          <p>
            <strong>Domicilio Social:</strong> {company.registeredAddressSevilla}
          </p>
          <p>
            Este sitio es una web informativa de Brasaland. El contenido gastronómico (carta y
            precios) puede actualizarse; prevalece la información confirmada en sala.
          </p>
        </div>
      </section>
    </>
  );
}
