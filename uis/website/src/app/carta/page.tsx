import type { Metadata } from "next";
import { MenuBrowser } from "@/components/MenuBrowser";
import { PageHero } from "@/components/PageHero";
import { restaurant } from "@/data/site";

export const metadata: Metadata = {
  title: "Carta",
  description: `Carta completa de ${restaurant.name}: entrantes, carnes a la brasa, arroces y postres con alérgenos.`,
};

export default function CartaPage() {
  return (
    <>
      <PageHero
        eyebrow="Carta"
        title="Sabores a la brasa"
        description={`${restaurant.slogan}. Precios en euros. Consulta alérgenos en cada plato y en la leyenda de los 14 grupos.`}
        imageSrc="/Imagenes/Entrana-argentina.jpg"
        imageAlt="Carnes a la brasa Brasaland"
        align="center"
      />
      <section className="section">
        <div className="container">
          <MenuBrowser />
        </div>
      </section>
    </>
  );
}
