import type { Metadata } from "next";
import { PageHero } from "@/components/PageHero";
import { ReservationForm } from "@/components/ReservationForm";
import { restaurant } from "@/data/site";

export const metadata: Metadata = {
  title: "Reservas",
  description: "Solicita mesa en Brasaland. La confirmación la realiza el restaurante.",
};

export default function ReservasPage() {
  return (
    <>
      <PageHero
        eyebrow="Reservas"
        title="Tu mesa junto al fuego"
        description={`Cuéntanos cuándo vienes. Teléfono ${restaurant.phone}${restaurant.phoneIsPlaceholder ? " [provisional]" : ""} · ${restaurant.email}.`}
      />
      <section className="section">
        <div className="container narrow">
          <ReservationForm />
        </div>
      </section>
    </>
  );
}
