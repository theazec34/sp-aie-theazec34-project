# Technical Context

## Stack y ejecución
- Sitio estático HTML/CSS/JS (sin framework frontend).
- Node.js >= 18.
- Servido local con `http-server` via script:
	- `npm run serve` -> `npx --yes http-server . -p 3000 -a 0.0.0.0`

## Archivos clave
- `index.html`: landing principal + carta + JS de render dinámico.
- `application.html`: formulario de aplicación/reserva y navegación secundaria.
- `validation.js`: validación del formulario en cliente.
- `menu.json`: fuente de datos estructurada para categorías/platos/alérgenos.
- `Imagenes/`: assets visuales de platos + iconos.

## Decisiones técnicas implementadas
- Favicon migrado a `Imagenes/Icono principal.png`.
- Logo visible del header/footer usa también `Imagenes/Icono principal.png` con tamaño ampliado.
- Render de carta preparado para:
	- cargar desde `menu.json` si está disponible,
	- fallback a datos inline si falla carga.
- Menú visual simplificado a una sola vista continua (sin tabs activos en UI).
- Soporte de navegación móvil mediante menú overlay.

## Gestión de imágenes
- Carpeta actual `Imagenes/` contiene:
	- Arroz bogavante.png
	- Arroz caldoso.jpg
	- Corte carne.png
	- Entraña argentina.png
	- Icono principal.png
	- Pata de cordero.png
	- Pescado braseado.png
	- Tabla ibericos.png
	- Tarta de galleta.png
	- tiramisu.jpg
	- favicon.jpg
- En el estado actual se utiliza un mapeo de IDs de plato -> imagen(es) dentro de `index.html`.

## Rama y estado git
- Rama de trabajo activa: `hito-4`.
- Carpeta `memory-bank/` creada para documentar contexto y avance.

## Riesgos/temas pendientes
- Hay doble fuente de verdad de menú (inline + JSON). Recomendable consolidar a una sola.
- Puede quedar CSS heredado no usado; conviene limpiar en una pasada final.
- Revisar que precios/nombres de platos añadidos manualmente estén aprobados por negocio.
