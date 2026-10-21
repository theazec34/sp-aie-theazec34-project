import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = { title: "Cookies" };

export default function CookiesPage() {
  return (
    <>
      <PageHero
        eyebrow="Legal"
        title="Política de cookies"
        description="Información provisional sobre el uso de cookies."
      />
      <section className="section">
        <div className="container narrow prose">
          <p>
            [Placeholder] Listado de cookies técnicas y, en su caso, analíticas, con
            plazos y proveedor. Hasta disponer del inventario real, esta página no afirma
            el uso de cookies de terceros.
          </p>
        </div>
      </section>
    </>
  );
}
