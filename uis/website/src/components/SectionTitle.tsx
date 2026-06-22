interface SectionTitleProps {
  id: string;
  title: string;
  description: string;
}

export function SectionTitle({ id, title, description }: SectionTitleProps) {
  return (
    <header id={id}>
      <h2 className="section-title">{title}</h2>
      <p className="section-text">{description}</p>
    </header>
  );
}
