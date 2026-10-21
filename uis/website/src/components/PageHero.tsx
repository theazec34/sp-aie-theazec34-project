import Image from "next/image";

interface PageHeroProps {
  eyebrow?: string;
  title: string;
  description: string;
  imageSrc?: string;
  imageAlt?: string;
  align?: "left" | "center";
}

export function PageHero({
  eyebrow,
  title,
  description,
  imageSrc,
  imageAlt = "",
  align = "center",
}: PageHeroProps) {
  const alignClass = align === "center" ? "page-hero-inner is-centered" : "page-hero-inner";

  return (
    <section className={imageSrc ? "page-hero page-hero-media" : "page-hero"}>
      {imageSrc ? (
        <div className="page-hero-bg" aria-hidden="true">
          <Image
            src={imageSrc}
            alt={imageAlt}
            fill
            priority
            sizes="100vw"
            className="page-hero-bg-image"
          />
          <div className="page-hero-bg-overlay" />
        </div>
      ) : null}
      <div className={`container ${alignClass}`}>
        {eyebrow ? <p className="section-eyebrow page-hero-eyebrow">{eyebrow}</p> : null}
        <h1 className="page-hero-title">{title}</h1>
        <p className="page-hero-text">{description}</p>
      </div>
    </section>
  );
}
