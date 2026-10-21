import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = { title: "Privacidad" };

export default function PrivacidadPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Política de privacidad"
        description="Marco orientativo hasta redactar la política firmada por el responsable."
      />
      <section className="section">
        <div className="container narrow prose">
          <p>
            [Placeholder] Responsable del tratamiento, finalidades (reservas, candidaturas,
            contacto), bases legitimadoras, plazos de conservación y derechos ARCO/RGPD
            pendientes de documento legal oficial.
          </p>
          <p>
            Los formularios de esta web no envían datos a un servidor de Brasaland hasta
            que se conecte un backend o proveedor; el usuario puede elegir enviar un correo
            desde su propio cliente.
          </p>
        </div>
      </section>
    </>
  );
}
