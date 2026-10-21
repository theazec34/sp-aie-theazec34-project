import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";
import { company } from "@/data/site";

export const metadata: Metadata = { title: "Privacidad" };

export default function PrivacidadPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Política de privacidad"
        description="Cómo tratamos tus datos en Brasaland."
        align="center"
      />
      <section className="section">
        <div className="container narrow prose">
          <p>
            <strong>Responsable del Tratamiento:</strong> {company.legalName}
          </p>
          <p>
            <strong>NIF:</strong> {company.nif}
          </p>
          <p>
            <strong>Domicilio Social:</strong> {company.registeredAddressPrivacy}
          </p>
          <p>
            <strong>Email de Contacto:</strong>{" "}
            <a href={`mailto:${company.privacyEmail}`}>{company.privacyEmail}</a>
          </p>
          <p>
            En Brasaland, tratamos la información que nos facilitas con el único fin de gestionar
            tus reservas de mesa, responder a tus consultas o enviarte comunicaciones comerciales
            si lo has autorizado previamente.
          </p>
          <p>
            Tus datos personales se conservarán únicamente durante el tiempo necesario para cumplir
            con estas finalidades o mientras exista una obligación legal. No compartiremos tus datos
            con terceros, salvo por imperativo legal.
          </p>
          <p>
            Puedes ejercer tus derechos de acceso, rectificación, supresión y oposición enviando un
            correo electrónico a {company.privacyEmail} acompañado de una copia de tu documento de
            identidad.
          </p>
        </div>
      </section>
    </>
  );
}
