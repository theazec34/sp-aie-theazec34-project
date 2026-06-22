import Image from "next/image";
import { DishItem } from "@/types/site";

interface DishCardProps {
  item: DishItem;
}

export function DishCard({ item }: DishCardProps) {
  return (
    <article className="card dish-card">
      {item.imagePath ? (
        <Image
          className="dish-image"
          src={item.imagePath}
          alt={item.name}
          width={420}
          height={260}
        />
      ) : (
        <div className="dish-image dish-image-fallback" aria-hidden="true" />
      )}
      <div className="dish-body">
        {item.badge ? <p className="dish-badge">{item.badge}</p> : null}
        <h3 className="card-title">{item.name}</h3>
        <p className="card-text">{item.description}</p>
        {item.category ? <p className="dish-meta">Categoria: {item.category}</p> : null}
        {item.weight ? <p className="dish-meta">Porcion: {item.weight}</p> : null}
        {item.extras ? <p className="dish-meta">Extras: {item.extras}</p> : null}
        {item.allergens && item.allergens.length > 0 ? (
          <p className="dish-meta">Alergenos: {item.allergens.join(", ")}</p>
        ) : null}
        <p className="dish-price">{item.priceEur.toFixed(2)} EUR</p>
      </div>
    </article>
  );
}
