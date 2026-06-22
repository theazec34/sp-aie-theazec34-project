import Image from "next/image";
import { allProjectPhotos } from "@/data/home";

export function GalleryGrid() {
  return (
    <section id="galeria" className="section section-soft">
      <div className="container">
        <h2 className="section-title">Todas las fotos del proyecto</h2>
        <div className="gallery-grid">
          {allProjectPhotos.map((photo) => (
            <figure key={photo.id} className="gallery-card">
              <Image src={photo.path} alt={photo.title} width={360} height={220} className="gallery-image" />
              <figcaption className="gallery-caption">{photo.title}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
