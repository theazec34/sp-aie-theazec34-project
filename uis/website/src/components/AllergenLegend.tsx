import { EU_ALLERGENS } from "@/data/allergens";

export function AllergenLegend() {
  return (
    <section className="allergen-key" aria-labelledby="allergen-legend-title">
      <h3 id="allergen-legend-title" className="menu-category-title">
        Leyenda de alérgenos (14 grupos UE)
      </h3>
      <p className="section-text">
        Cada plato indica los códigos presentes. La información no depende solo del color:
        el código y el nombre aparecen juntos.
      </p>
      <ul className="allergen-items">
        {EU_ALLERGENS.map((a) => (
          <li key={a.code} className="allergen-item">
            <span className="allergen-code" aria-hidden="true">
              {a.code}
            </span>
            <span>
              <strong>{a.code}</strong> — {a.name}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
