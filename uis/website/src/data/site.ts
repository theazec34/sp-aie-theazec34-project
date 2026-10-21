import type { GalleryPhoto, NavItem } from "@/types/site";
import menuData from "@/data/menu.json";
import type { MenuData } from "@/types/menu";

const menu = menuData as MenuData;

/** Datos operativos del local (carta + contacto). */
export const restaurant = {
  name: menu.restaurante.nombre,
  slogan: menu.restaurante.slogan,
  phone: menu.restaurante.telefono,
  email: menu.restaurante.email,
  address: "Calle de la Brasa, Nº 14, Planta Baja, 41808 Sevilla, España",
  phoneIsPlaceholder: false,
};

/** Datos societarios para textos legales. */
export const company = {
  legalName: "Brasaland Restauración S.L.",
  nif: "B-12345678",
  registeredAddressSevilla: "Calle de la Brasa, Nº 14, Planta Baja, 41808 Sevilla, España",
  registeredAddressPrivacy: "Calle de la Brasa, Nº 14, Planta Baja, 28001 Sevilla, España",
  registeredAddressCookies: "Calle de la Brasa, Nº 14, Planta Baja, 28001 Madrid, España",
  privacyEmail: "privacidad@brasaland.com",
};

/** Embed sin API key: búsqueda de la dirección del local. */
export const mapsEmbedSrc =
  "https://maps.google.com/maps?q=Calle%20de%20la%20Brasa%2014%2C%20Sevilla%2C%20Espa%C3%B1a&z=16&output=embed";

export const hours = {
  provisional: false,
  lines: [
    "Martes–Jueves: 13:00–16:00 · 20:00–23:30",
    "Viernes–Sábado: 13:00–16:30 · 20:00–00:30",
    "Domingo: 13:00–16:30 · Cerrado por la noche",
    "Lunes: cerrado",
  ],
};

export const specialty = "Carnes a la brasa · fusión sudamericana e ibérica";

export const navItems: NavItem[] = [
  { id: "inicio", label: "Inicio", href: "/" },
  { id: "carta", label: "Carta", href: "/carta" },
  { id: "reservas", label: "Reservas", href: "/reservas" },
  { id: "nosotros", label: "Nosotros", href: "/nosotros" },
  { id: "galeria", label: "Galería", href: "/galeria" },
  { id: "eventos", label: "Eventos", href: "/eventos" },
  { id: "empleo", label: "Empleo", href: "/trabaja-con-nosotros" },
  { id: "contacto", label: "Contacto", href: "/contacto" },
];

export const footerNav: NavItem[] = [
  { id: "carta", label: "Carta", href: "/carta" },
  { id: "reservas", label: "Reservas", href: "/reservas" },
  { id: "eventos", label: "Eventos", href: "/eventos" },
  { id: "empleo", label: "Trabaja con nosotros", href: "/trabaja-con-nosotros" },
  { id: "contacto", label: "Contacto", href: "/contacto" },
  { id: "nosotros", label: "Nosotros", href: "/nosotros" },
];

export const legalLinks: NavItem[] = [
  { id: "aviso", label: "Aviso legal", href: "/aviso-legal" },
  { id: "privacidad", label: "Privacidad", href: "/privacidad" },
  { id: "cookies", label: "Cookies", href: "/cookies" },
];

export const galleryPhotos: GalleryPhoto[] = [
  { id: "corte-carne", title: "Corte a la brasa", path: "/Imagenes/Corte carne.jpg" },
  { id: "entraña", title: "Entraña argentina", path: "/Imagenes/Entrana-argentina.jpg" },
  { id: "arroz-bogavante", title: "Arroz con bogavante", path: "/Imagenes/Arroz bogavante.jpg" },
  { id: "tabla-ibericos", title: "Tabla ibéricos", path: "/Imagenes/Tabla ibericos.jpg" },
  { id: "pata-cordero", title: "Cordero a la brasa", path: "/Imagenes/Pata de cordero.jpg" },
  { id: "pescado", title: "Pescado braseado", path: "/Imagenes/Pescado braseado.jpg" },
  { id: "arroz-caldoso", title: "Arroz caldoso", path: "/Imagenes/Arroz caldoso.jpg" },
  { id: "tarta", title: "Tarta de galleta", path: "/Imagenes/Tarta de galleta.jpg" },
  { id: "tiramisu", title: "Postre de la casa", path: "/Imagenes/tiramisu.jpg" },
];

export const featuredDishIds = [
  "entraña",
  "tira-asado",
  "secreto-iberico",
  "arroz-bogavante",
  "tabla-ibericos",
  "tres-leches",
] as const;

export const philosophy = {
  title: "Fuego, paciencia y mesa compartida",
  body: "En Brasaland cocinamos a la brasa cortes sudamericanos e ibéricos con el mismo respeto: brasa viva, punto exacto y producto de temporada. Venimos de la parrilla argentina y de la despensa de bellota; el resultado es una mesa generosa, hospitalaria y sin artificios.",
};

export const experiencePoints = [
  {
    id: "brasa",
    title: "Brasa de verdad",
    description: "Carbón y paciencia: el fuego marca el ritmo del servicio, no al revés.",
  },
  {
    id: "fusion",
    title: "Dos orillas, una mesa",
    description: "Chimichurri, ibéricos, arroces y postres que dialogan sin perder identidad.",
  },
  {
    id: "sala",
    title: "Hospitalidad",
    description: "Sala cercana, ritmo de restaurante y ganas de que te quedes un poco más.",
  },
];

export const jobRoles = [
  {
    id: "sala",
    title: "Sala y barra",
    blurb: "Hospitalidad, ritmo y conocimiento de carta.",
    image: "/Imagenes/empleo-sala.jpg",
  },
  {
    id: "cocina",
    title: "Cocina / parrilla",
    blurb: "Brasa, mise en place y respeto al producto.",
    image: "/Imagenes/empleo-cocina-brasas.jpg",
  },
  {
    id: "ops",
    title: "Operaciones",
    blurb: "Turnos, proveedores y excelencia del servicio.",
    image: "/Imagenes/empleo-sala.jpg",
  },
];

export const eventOfferings = [
  {
    id: "privados",
    title: "Mesas privadas y celebraciones",
    description: "Cumpleaños, cenas de equipo y sobremesas largas con menú acordado.",
    image: "/Imagenes/eventos-actuacion.jpg",
  },
  {
    id: "grupos",
    title: "Grupos",
    description: "Menús cerrados a la brasa para grupos; coordinamos tiempos y alérgenos.",
    image: "/Imagenes/Corte carne.jpg",
  },
  {
    id: "flamenco",
    title: "Noches con alma",
    description: "Flamenco y actuaciones en vivo que acompañan la brasa y la sobremesa.",
    image: "/Imagenes/eventos-flamenco.jpg",
  },
];
