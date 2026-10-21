/** Map dish id → photo in /public/Imagenes (reused on carta + home). */
export const menuImageMap: Record<string, string> = {
  "tira-asado": "/Imagenes/Corte carne.jpg",
  "entraña": "/Imagenes/entrana-chimichurri.jpg",
  picanha: "/Imagenes/Corte carne.jpg",
  "secreto-iberico": "/Imagenes/Pata de cordero.jpg",
  ribeye: "/Imagenes/Corte carne.jpg",
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

/** @deprecated use galleryPhotos from site.ts */
export { galleryPhotos as allProjectPhotos, navItems } from "@/data/site";
