import Image from "next/image";
import { formatAllergenCodes } from "@/data/allergens";
import { DishItem } from "@/types/site";

interface DishCardProps {
  item: DishItem;
  priority?: boolean;
}

export function DishCard({ item, priority = false }: DishCardProps) {
  return (
    <article className="dish-card">
      {item.imagePath ? (
        <div className="dish-image-wrap">
          <Image
            className="dish-image"
            src={item.imagePath}
            alt={item.name}
            width={960}
            height={640}
            sizes="(max-width: 720px) 100vw, (max-width: 1100px) 50vw, 33vw"
            priority={priority}
            loading={priority ? undefined : "lazy"}
          />
        </div>
      ) : (
        <div className="dish-image-wrap dish-image-fallback" aria-hidden="true" />
      )}
      <div className="dish-body">
        <div className="dish-top">
          {item.badge ? <p className="dish-badge">{item.badge}</p> : null}
          <p className="dish-price">{item.priceEur.toFixed(2)} €</p>
        </div>
        <h3 className="dish-title">{item.name}</h3>
        <p className="dish-desc">{item.description}</p>
        {item.weight ? <p className="dish-meta">Porción: {item.weight}</p> : null}
        {item.extras ? <p className="dish-meta">{item.extras}</p> : null}
        <p className="dish-allergens">
          <span className="dish-allergens-label">Alérgenos: </span>
          {formatAllergenCodes(item.allergens ?? [])}
        </p>
      </div>
    </article>
  );
}
