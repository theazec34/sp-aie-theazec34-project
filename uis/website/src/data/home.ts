import { GalleryPhoto, NavItem } from "@/types/site";

export const navItems: NavItem[] = [
  { id: "inicio", label: "Inicio", href: "#inicio" },
  { id: "carta", label: "Carta", href: "#carta" },
  { id: "galeria", label: "Fotos", href: "#galeria" },
  { id: "aplicar", label: "Formulario", href: "#aplicar" },
];

export const allProjectPhotos: GalleryPhoto[] = [
  { id: "arroz-bogavante", title: "Arroz bogavante", path: "/Imagenes/Arroz bogavante.jpg" },
  { id: "arroz-caldoso", title: "Arroz caldoso", path: "/Imagenes/Arroz caldoso.jpg" },
  { id: "corte-carne", title: "Corte de carne", path: "/Imagenes/Corte carne.jpg" },
  { id: "entranha", title: "Entrana argentina", path: "/Imagenes/Entraña argentina.jpg" },
  { id: "icono-principal", title: "Icono principal", path: "/Imagenes/Icono principal.png" },
  { id: "pata-cordero", title: "Pata de cordero", path: "/Imagenes/Pata de cordero.jpg" },
  { id: "pescado-braseado", title: "Pescado braseado", path: "/Imagenes/Pescado braseado.jpg" },
  { id: "tabla-ibericos", title: "Tabla ibericos", path: "/Imagenes/Tabla ibericos.jpg" },
  { id: "tarta-galleta", title: "Tarta de galleta", path: "/Imagenes/Tarta de galleta.jpg" },
  { id: "tiramisu", title: "Tiramisu", path: "/Imagenes/tiramisu.jpg" },
];

export const menuImageMap: Record<string, string> = {
  "tira-asado": "/Imagenes/Corte carne.jpg",
  "entraña": "/Imagenes/Entraña argentina.jpg",
  "picanha": "/Imagenes/Corte carne.jpg",
  "secreto-iberico": "/Imagenes/Pata de cordero.jpg",
  ribeye: "/Imagenes/Pescado braseado.jpg",
  "arroz-bogavante": "/Imagenes/Arroz bogavante.jpg",
  "arroz-negro": "/Imagenes/Arroz caldoso.jpg",
  "arroz-sudamericano": "/Imagenes/Arroz caldoso.jpg",
  "paella-mixta": "/Imagenes/Arroz caldoso.jpg",
  "tabla-ibericos": "/Imagenes/Tabla ibericos.jpg",
  croquetas: "/Imagenes/Tabla ibericos.jpg",
  patacon: "/Imagenes/Corte carne.jpg",
  empanadas: "/Imagenes/Corte carne.jpg",
  pulpo: "/Imagenes/Pescado braseado.jpg",
  "tres-leches": "/Imagenes/Tarta de galleta.jpg",
  churros: "/Imagenes/Tarta de galleta.jpg",
  alfajores: "/Imagenes/tiramisu.jpg",
  "flan-iberico": "/Imagenes/tiramisu.jpg",
};
