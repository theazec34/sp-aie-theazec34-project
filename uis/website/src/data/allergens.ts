/** 14 alérgenos reglamentarios UE — leyenda textual (no solo color/icono). */
export interface AllergenDef {
  code: string;
  name: string;
  shortLabel: string;
}

export const EU_ALLERGENS: AllergenDef[] = [
  { code: "G", name: "Cereales con gluten", shortLabel: "Gluten" },
  { code: "Cr", name: "Crustáceos", shortLabel: "Crustáceos" },
  { code: "H", name: "Huevos", shortLabel: "Huevo" },
  { code: "P", name: "Pescado", shortLabel: "Pescado" },
  { code: "Ca", name: "Cacahuetes", shortLabel: "Cacahuetes" },
  { code: "So", name: "Soja", shortLabel: "Soja" },
  { code: "L", name: "Leche y lácteos (incluida lactosa)", shortLabel: "Lácteos" },
  { code: "F", name: "Frutos de cáscara", shortLabel: "Frutos secos" },
  { code: "Ap", name: "Apio", shortLabel: "Apio" },
  { code: "M", name: "Mostaza", shortLabel: "Mostaza" },
  { code: "Se", name: "Granos de sésamo", shortLabel: "Sésamo" },
  { code: "Su", name: "Dióxido de azufre y sulfitos", shortLabel: "Sulfitos" },
  { code: "Al", name: "Altramuces", shortLabel: "Altramuces" },
  { code: "Mo", name: "Moluscos", shortLabel: "Moluscos" },
];

const byCode = Object.fromEntries(EU_ALLERGENS.map((a) => [a.code, a]));

export function allergenLabel(code: string): string {
  return byCode[code]?.shortLabel ?? code;
}

export function formatAllergenCodes(codes: string[]): string {
  if (!codes.length) return "Sin alérgenos declarados en carta";
  return codes.map((c) => `${c} (${allergenLabel(c)})`).join(" · ");
}
