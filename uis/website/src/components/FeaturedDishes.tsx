import Link from "next/link";
import { DishCard } from "@/components/DishCard";
import { SectionTitle } from "@/components/SectionTitle";
import { menuImageMap } from "@/data/home";
import menuData from "@/data/menu.json";
import { featuredDishIds } from "@/data/site";
import { MenuData } from "@/types/menu";

const typedMenu = menuData as MenuData;

export function FeaturedDishes() {
  const dishes = featuredDishIds
    .map((id) => {
      for (const cat of typedMenu.categorias) {
        const dish = cat.platos.find((p) => p.id === id);
        if (dish) return { dish, category: cat.nombre };
      }
      return null;
    })
    .filter(Boolean) as Array<{
    dish: (typeof typedMenu.categorias)[0]["platos"][0];
    category: string;
  }>;

  return (
    <section id="carta" className="section" aria-labelledby="featured-title">
      <div className="container">
        <SectionTitle
          id="featured-title"
          eyebrow="Carta"
          title="Platos que definen Brasaland"
          description="Una selección de la brasa y la despensa. Precios en euros según la carta vigente."
        />
        <div className="grid-dishes">
          {dishes.map(({ dish, category }, index) => (
            <DishCard
              key={dish.id}
              priority={index === 0}
              item={{
                id: dish.id,
                name: dish.nombre,
                description: dish.descripcion,
                priceEur: dish.precio,
                imagePath: menuImageMap[dish.id],
                badge: dish.badge,
                weight: dish.peso,
                allergens: dish.alergenos,
                category,
              }}
            />
          ))}
        </div>
        <p className="section-cta-row">
          <Link className="cta" href="/carta">
            Ver carta completa
          </Link>
        </p>
      </div>
    </section>
  );
}
