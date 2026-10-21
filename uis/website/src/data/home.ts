/** Map dish id → photo in /public/Imagenes (reused on carta + home). */
export const menuImageMap: Record<string, string> = {
  "tira-asado": "/Imagenes/tira-asado-argentina.jpg",
  "entraña": "/Imagenes/entrana-chimichurri.jpg",
  picanha: "/Imagenes/picanha-brasilena.jpg",
  "secreto-iberico": "/Imagenes/Pata de cordero.jpg",
  ribeye: "/Imagenes/ribeye-black-angus.jpg",
  "arroz-bogavante": "/Imagenes/Arroz bogavante.jpg",
  "arroz-negro": "/Imagenes/arroz-negro-chipirones.jpg",
  "arroz-sudamericano": "/Imagenes/arroz-pollo-macho.jpg",
  "paella-mixta": "/Imagenes/paella-mixta.jpg",
  "tabla-ibericos": "/Imagenes/Tabla ibericos.jpg",
  croquetas: "/Imagenes/croquetas-jamon.jpg",
  patacon: "/Imagenes/patacon-hogao.jpg",
  empanadas: "/Imagenes/empanadas-criollas.jpg",
  pulpo: "/Imagenes/pulpo-a-la-gallega.jpg",
  "tres-leches": "/Imagenes/pastel-tres-leches.jpg",
  churros: "/Imagenes/churros-chocolate.jpg",
  alfajores: "/Imagenes/alfajores-maicena.jpg",
  "flan-iberico": "/Imagenes/flan-huevo-caramelo.jpg",
};

/** @deprecated use galleryPhotos from site.ts */
export { galleryPhotos as allProjectPhotos, navItems } from "@/data/site";
