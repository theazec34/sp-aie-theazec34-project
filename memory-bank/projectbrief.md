# Project Brief - Brasaland (alineado a documentos base)

## Fuentes de verdad
- Contexto de negocio: `Brasaland.md`.
- Motivacion y enfoque del alumno: `Brasaland_Eleccion.md`.
- Alcance tecnico de hito: `README.md` y `README.es.md`.

## Empresa y foco de negocio
Brasaland es un restaurante de cocina brasilena con operacion en sala, reservas y pedidos a domicilio integrados con agregadores. Los dos departamentos prioritarios definidos son:
- Logistica: compras a proveedores, facturacion y encargos.
- Marketing/carta: menu digital, alergenos y visibilidad en plataformas.

## Entidades que el proyecto debe cubrir (segun Brasaland.md)
- `EncargoProveedor`.
- `PlatoCarta`.
- `ReservaMesa`.
- `PedidoDomicilio`.

Cada entidad tiene reglas concretas de validacion y reportes obligatorios (conteos por estado/plataforma/categoria, sumas y promedios, y en el caso de carta tambien min/max de precio).

## Reto funcional definido
Automatizar pedidos a domicilio y reservas de mesa de forma segura, evitando solapes de mesa y reduciendo dependencia de llamadas telefonicas.

## Estado real del repo respecto al brief
- Se ha avanzado bastante en la web de Brasaland (`index.html`, `application.html`, `menu.json`, carpeta `Imagenes`).
- La UX de carta ya esta integrada en una vista unica y se incorporaron assets visuales del negocio.
- Existe una brecha con el hito tecnico de TypeScript: el codigo actual de `src/` sigue orientado a ejemplo de elecciones y no implementa aun las 4 entidades de Brasaland.

## Objetivo inmediato de esta rama
Continuar sobre `hito-4` cerrando la brecha entre:
1. Contexto de negocio Brasaland.
2. Reglas de validacion/reportes exigidas.
3. Implementacion TypeScript real en `src/`.
