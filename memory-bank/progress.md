# Progress Log (hasta hoy)

## 1) Arranque y visibilidad
- Se verificó cómo servir el proyecto en local.
- Se levantó servidor en `http://localhost:3000`.

## 2) Corrección de incongruencias iniciales
- Se detectaron enlaces en `application.html` apuntando a anclas inexistentes.
- Se actualizaron enlaces a secciones reales de `index.html`:
	- `#carta`
	- `#como-funciona`
	- `#testimonios`
- Se ajustaron textos de footer/contacto para consistencia con Brasaland.

## 3) Integración de imágenes y favicon
- Se añadió favicon en páginas principales.
- Se incorporaron imágenes de platos en la carta.
- Se preparó mapeo de imágenes por `id` de plato y render con `img` real.

## 4) Menú y experiencia de carta
- Se pasó de vista por pestañas a menú único grande en scroll continuo.
- Se mantuvo soporte de navegación interna desde enlaces de footer.
- Se implementó filtrado/render en base a imágenes disponibles.

## 5) Identidad visual del logo
- Se reemplazó uso de `favicon.jpg` por `Icono principal.png`.
- El icono principal se usa ahora:
	- como favicon (`rel=icon`),
	- junto al nombre Brasaland en header y footer.
- Se incrementó tamaño del icono para mejorar presencia visual.

## 6) Organización de trabajo
- Se creó rama de trabajo `hito-4` para continuar desarrollo.
- Se creó carpeta `memory-bank/` con documentación viva del proyecto.

## Estado actual
- Funcional: sí.
- Navegación: coherente y operativa.
- Branding: más consistente que el estado inicial.
- Carta: renderizada en vista única con assets visuales.

## Próximos pasos recomendados
- Unificar fuente de datos del menú (preferentemente solo `menu.json`).
- Ajustar/validar definitivamente relación plato-imagen con criterio de negocio.
- Limpiar CSS residual no utilizado tras los cambios de estructura.
- QA responsive final (móvil/tablet/escritorio) y revisión de accesibilidad.
