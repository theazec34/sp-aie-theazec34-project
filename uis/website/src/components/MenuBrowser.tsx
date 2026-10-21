"use client";

import { useMemo, useState } from "react";
import { AllergenLegend } from "@/components/AllergenLegend";
import { DishCard } from "@/components/DishCard";
import { menuImageMap } from "@/data/home";
import menuData from "@/data/menu.json";
import { MenuData } from "@/types/menu";

const typedMenu = menuData as MenuData;

/** Categorías presentes en datos reales (sin inventar pescados/bebidas). */
const CATEGORY_ORDER = ["entrantes", "carnes", "arroces", "postres"] as const;

export function MenuBrowser() {
  const [active, setActive] = useState<string>("todas");
  const [query, setQuery] = useState("");

  const categories = useMemo(() => {
    const byId = Object.fromEntries(typedMenu.categorias.map((c) => [c.id, c]));
    return CATEGORY_ORDER.map((id) => byId[id]).filter(Boolean);
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return categories
      .filter((c) => active === "todas" || c.id === active)
      .map((c) => ({
        ...c,
        platos: c.platos.filter((p) => {
          if (!q) return true;
          return (
            p.nombre.toLowerCase().includes(q) ||
            p.descripcion.toLowerCase().includes(q)
          );
        }),
      }))
      .filter((c) => c.platos.length > 0);
  }, [active, categories, query]);

  const firstDishId = filtered[0]?.platos[0]?.id;

  return (
    <div className="menu-browser">
      <div className="menu-toolbar">
        <label className="menu-search">
          <span className="sr-only">Buscar plato</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar plato…"
            autoComplete="off"
          />
        </label>
        <div className="menu-tabs" role="tablist" aria-label="Categorías de la carta">
          <button
            type="button"
            role="tab"
            aria-selected={active === "todas"}
            className={active === "todas" ? "menu-tab is-active" : "menu-tab"}
            onClick={() => setActive("todas")}
          >
            Todas
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              role="tab"
              aria-selected={active === c.id}
              className={active === c.id ? "menu-tab is-active" : "menu-tab"}
              onClick={() => setActive(c.id)}
            >
              {c.nombre}
            </button>
          ))}
        </div>
      </div>

      <p className="menu-note">
        Carta basada en datos del restaurante. Categorías como pescados, guarniciones o
        bebidas se añadirán cuando existan en la fuente de datos (no se inventan aquí).
      </p>

      {filtered.map((category) => (
        <section
          key={category.id}
          className="menu-category"
          aria-labelledby={`cat-${category.id}`}
          id={category.id}
        >
          <h2 id={`cat-${category.id}`} className="menu-category-title">
            {category.nombre}
          </h2>
          <p className="menu-category-description">{category.descripcion}</p>
          <div className="grid-dishes">
            {category.platos.map((dish) => (
              <DishCard
                key={dish.id}
                priority={dish.id === firstDishId}
                item={{
                  id: dish.id,
                  name: dish.nombre,
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

      {filtered.length === 0 ? (
        <p className="form-status" role="status">
          No hay platos que coincidan con la búsqueda.
        </p>
      ) : null}

      <AllergenLegend />
    </div>
  );
}
