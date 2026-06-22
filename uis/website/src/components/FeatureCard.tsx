import { FeatureItem } from "@/types/site";

interface FeatureCardProps {
  item: FeatureItem;
}

export function FeatureCard({ item }: FeatureCardProps) {
  return (
    <article className="card">
      <h3 className="card-title">{item.title}</h3>
      <p className="card-text">{item.description}</p>
    </article>
  );
}
