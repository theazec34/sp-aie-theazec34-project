import { GalleryPhoto, NavItem } from "@/types/site";

export const navItems: NavItem[] = [
  { id: "inicio", label: "Inicio", href: "#inicio" },
  { id: "carta", label: "Carta", href: "#carta" },
  { id: "galeria", label: "Fotos", href: "#galeria" },
  { id: "aplicar", label: "Formulario", href: "#aplicar" },
];

export const allProjectPhotos: GalleryPhoto[] = [
  { id: "arroz-bogavante", title: "Arroz bogavante", path: "/Imagenes/Arroz bogavante.png" },
  { id: "arroz-caldoso", title: "Arroz caldoso", path: "/Imagenes/Arroz caldoso.jpg" },
  { id: "corte-carne", title: "Corte de carne", path: "/Imagenes/Corte carne.png" },
  { id: "entranha", title: "Entrana argentina", path: "/Imagenes/Entraña argentina.png" },
  { id: "icono-principal", title: "Icono principal", path: "/Imagenes/Icono principal.png" },
  { id: "pata-cordero", title: "Pata de cordero", path: "/Imagenes/Pata de cordero.png" },
  { id: "pescado-braseado", title: "Pescado braseado", path: "/Imagenes/Pescado braseado.png" },
  { id: "tabla-ibericos", title: "Tabla ibericos", path: "/Imagenes/Tabla ibericos.png" },
  { id: "tarta-galleta", title: "Tarta de galleta", path: "/Imagenes/Tarta de galleta.png" },
  { id: "tiramisu", title: "Tiramisu", path: "/Imagenes/tiramisu.jpg" },
];

export const menuImageMap: Record<string, string> = {
  "tira-asado": "/Imagenes/Corte carne.png",
  "entraña": "/Imagenes/Entraña argentina.png",
  "picanha": "/Imagenes/Corte carne.png",
  "secreto-iberico": "/Imagenes/Pata de cordero.png",
  ribeye: "/Imagenes/Pescado braseado.png",
  "arroz-bogavante": "/Imagenes/Arroz bogavante.png",
  "arroz-negro": "/Imagenes/Arroz caldoso.jpg",
  "arroz-sudamericano": "/Imagenes/Arroz caldoso.jpg",
  "paella-mixta": "/Imagenes/Arroz caldoso.jpg",
  "tabla-ibericos": "/Imagenes/Tabla ibericos.png",
  croquetas: "/Imagenes/Tabla ibericos.png",
  patacon: "/Imagenes/Corte carne.png",
  empanadas: "/Imagenes/Corte carne.png",
  pulpo: "/Imagenes/Pescado braseado.png",
  "tres-leches": "/Imagenes/Tarta de galleta.png",
  churros: "/Imagenes/Tarta de galleta.png",
  alfajores: "/Imagenes/tiramisu.jpg",
  "flan-iberico": "/Imagenes/tiramisu.jpg",
};
