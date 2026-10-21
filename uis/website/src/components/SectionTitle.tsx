interface SectionTitleProps {
  id: string;
  eyebrow?: string;
  title: string;
  description?: string;
}

export function SectionTitle({ id, eyebrow, title, description }: SectionTitleProps) {
  return (
    <header className="section-header" id={id}>
      {eyebrow ? <p className="section-eyebrow">{eyebrow}</p> : null}
      <h2 className="section-title">{title}</h2>
      {description ? <p className="section-text">{description}</p> : null}
    </header>
  );
}
