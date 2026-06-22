import { DishCard } from "@/components/DishCard";
import menuData from "@/data/menu.json";
import { menuImageMap } from "@/data/home";
import { MenuData } from "@/types/menu";

const typedMenuData = menuData as MenuData;

const excludedDishIds = new Set<string>([
  "entraña",
  "picanha",
  "arroz-sudamericano",
  "paella-mixta",
  "croquetas",
  "patacon",
  "empanadas",
  "pulpo",
  "tres-leches",
  "alfajores",
]);

const dishNameOverrides: Record<string, string> = {
  "secreto-iberico": "Pata de cordero",
  ribeye: "Salmonete criollo",
  churros: "Tarta de galleta",
  "flan-iberico": "Tiramisu",
};

export function MenuSection() {
  return (
    <section id="carta" className="section">
      <div className="container">
        <h2 className="section-title">Carta completa Brasaland</h2>
        <p className="section-text">
          Datos conectados a menu.json para reflejar categorias, platos, precios y alergenos del proyecto.
        </p>
        <div className="menu-summary">
          <p>
            <strong>{typedMenuData.restaurante.nombre}</strong> · {typedMenuData.restaurante.slogan}
          </p>
          <p>
            {typedMenuData.restaurante.telefono} · {typedMenuData.restaurante.email}
          </p>
        </div>

        {typedMenuData.categorias.map((category) => (
          <section key={category.id} className="menu-category" aria-labelledby={`cat-${category.id}`}>
            <h3 id={`cat-${category.id}`} className="menu-category-title">
              {category.icono} {category.nombre}
            </h3>
            <p className="menu-category-description">{category.descripcion}</p>
            <div className="grid-3">
              {category.platos
                .filter((dish) => !excludedDishIds.has(dish.id))
                .map((dish) => (
                <DishCard
                  key={dish.id}
                  item={{
                    id: dish.id,
                    name: dishNameOverrides[dish.id] ?? dish.nombre,
                    description: dish.descripcion,
                    priceEur: dish.precio,
                    imagePath: menuImageMap[dish.id],
                    badge: dish.badge,
                    weight: dish.peso,
                    extras: dish.extras,
                    allergens: dish.alergenos,
                    category: category.nombre,
                  }}
                />
                ))}
            </div>
          </section>
        ))}

        <div className="allergen-key" aria-label="Clave de alergenos">
          <h3 className="menu-category-title">Clave de alergenos</h3>
          <div className="allergen-items">
            {Object.entries(typedMenuData.alergenos_clave).map(([id, allergen]) => (
              <p key={id} className="allergen-item">
                {allergen.emoji} {id}: {allergen.nombre}
              </p>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
