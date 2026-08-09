import Image from "next/image";
import { SectionTitle } from "@/components/SectionTitle";
import { allProjectPhotos } from "@/data/home";

export function GalleryGrid() {
  return (
    <section id="galeria" className="section section-soft">
      <div className="container">
        <SectionTitle
          id="galeria-title"
          title="Todas las fotos del proyecto"
          description="Galería visual de platos y atmósfera Brasaland."
        />
        <div className="gallery-grid">
          {allProjectPhotos.map((photo) => (
            <figure key={photo.id} className="gallery-card">
              <Image
                src={photo.path}
                alt={photo.title}
                width={360}
                height={196}
                className="gallery-image"
                sizes="(max-width: 920px) 50vw, 25vw"
                loading="lazy"
              />
              <figcaption className="gallery-caption">{photo.title}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
