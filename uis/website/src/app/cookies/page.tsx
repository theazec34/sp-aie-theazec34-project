import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";
import { company } from "@/data/site";

export const metadata: Metadata = { title: "Cookies" };

export default function CookiesPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Política de cookies"
        description="Uso de cookies en el sitio web de Brasaland."
        align="center"
      />
      <section className="section">
        <div className="container narrow prose">
          <p>
            <strong>Titular del Sitio Web:</strong> {company.legalName}
          </p>
          <p>
            <strong>NIF:</strong> {company.nif}
          </p>
          <p>
            <strong>Domicilio Social:</strong> {company.registeredAddressCookies}
          </p>
          <p>
            En Brasaland utilizamos cookies propias y de terceros para garantizar el correcto
            funcionamiento del sitio web, recordar tus preferencias (como el idioma o detalles de
            reserva) y analizar el tráfico de la página para mejorar nuestros servicios.
          </p>
          <p>
            Las cookies son pequeños archivos de texto que se descargan en tu navegador al visitar
            nuestra web. Puedes configurar, bloquear o eliminar las cookies instaladas en tu equipo
            en cualquier momento a través de los ajustes de tu navegador de internet.
          </p>
          <p>
            Ten en cuenta que si deshabilitas las cookies técnicas o de funcionamiento, algunas
            secciones de la web o el sistema de reservas en línea podrían no funcionar correctamente.
          </p>
        </div>
      </section>
    </>
  );
}
