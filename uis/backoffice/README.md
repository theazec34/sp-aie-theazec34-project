# Backoffice UI

Espacio reservado para el panel interno de operacion Brasaland.

## Estado actual
- App Next.js independiente de `uis/website`.
- Layout propio de backoffice (sidebar + topbar + paneles vacios).
- Estructura inicial lista para conectar logica del hito 2.

## Estructura base
- `src/app/layout.tsx`: layout visual del backoffice.
- `src/app/page.tsx`: dashboard vacio con modulos placeholder.
- `src/app/globals.css`: estilo interno (no corporativo de website).

## Comandos
- `npm run dev`
- `npm run lint`
- `npm run build`

Objetivos previstos:
- Gestion de reservas y ocupacion de mesas.
- Control de encargos a proveedores.
- Seguimiento de pedidos a domicilio.

La web publica principal vive en ../website.
