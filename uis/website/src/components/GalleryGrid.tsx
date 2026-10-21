import Image from "next/image";
import { galleryPhotos } from "@/data/site";

interface GalleryGridProps {
  limit?: number;
  showCaptions?: boolean;
}

export function GalleryGrid({ limit, showCaptions = true }: GalleryGridProps) {
  const photos = typeof limit === "number" ? galleryPhotos.slice(0, limit) : galleryPhotos;

  return (
    <div className="gallery-grid">
      {photos.map((photo, index) => (
        <figure key={photo.id} className="gallery-card">
          <Image
            src={photo.path}
            alt={photo.title}
            width={960}
            height={720}
            className="gallery-image"
            sizes="(max-width: 720px) 50vw, 25vw"
            loading={index < 2 ? "eager" : "lazy"}
          />
          {showCaptions ? (
            <figcaption className="gallery-caption">{photo.title}</figcaption>
          ) : null}
        </figure>
      ))}
    </div>
  );
}
