interface PageHeroProps {
  eyebrow?: string;
  title: string;
  description: string;
}

export function PageHero({ eyebrow, title, description }: PageHeroProps) {
  return (
    <section className="page-hero">
      <div className="container page-hero-inner">
        {eyebrow ? <p className="section-eyebrow">{eyebrow}</p> : null}
        <h1 className="page-hero-title">{title}</h1>
        <p className="page-hero-text">{description}</p>
      </div>
    </section>
  );
}
