export interface MenuAllergen {
  nombre: string;
  emoji: string;
}

export interface MenuDish {
  id: string;
  nombre: string;
  descripcion: string;
  precio: number;
  peso: string;
  badge: string | null;
  alergenos: string[];
  extras: string;
}

export interface MenuCategory {
  id: string;
  nombre: string;
  icono: string;
  descripcion: string;
  platos: MenuDish[];
}

export interface MenuData {
  restaurante: {
    nombre: string;
    slogan: string;
    telefono: string;
    email: string;
    direccion: string;
  };
  alergenos_clave: Record<string, MenuAllergen>;
  categorias: MenuCategory[];
}
