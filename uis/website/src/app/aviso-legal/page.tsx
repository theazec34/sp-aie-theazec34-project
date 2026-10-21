import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = { title: "Aviso legal" };

export default function AvisoLegalPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Aviso legal"
        description="Texto legal definitivo pendiente de datos societarios reales."
      />
      <section className="section">
        <div className="container narrow prose">
          <p>
            [Placeholder] Razón social, NIF y domicilio social pendientes de facilitar por
            el titular del restaurante. Este sitio es una web informativa de Brasaland.
          </p>
          <p>
            El contenido gastronómico (carta y precios) puede actualizarse; prevalece la
            información confirmada en sala.
          </p>
        </div>
      </section>
    </>
  );
}
