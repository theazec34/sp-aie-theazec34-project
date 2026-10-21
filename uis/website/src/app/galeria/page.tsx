import type { Metadata } from "next";
import { GalleryGrid } from "@/components/GalleryGrid";
import { PageHero } from "@/components/PageHero";

export const metadata: Metadata = {
  title: "Galería",
  description: "Fotografías de platos y atmósfera Brasaland.",
};

export default function GaleriaPage() {
  return (
    <>
      <PageHero
        eyebrow="Galería"
        title="El fuego, en imágenes"
        description="Selección fotográfica del proyecto: brasa, platos y detalles de sala."
        imageSrc="/Imagenes/Pescado braseado.jpg"
        imageAlt="Platos Brasaland"
        align="center"
      />
      <section className="section">
        <div className="container">
          <GalleryGrid />
        </div>
      </section>
    </>
  );
}
