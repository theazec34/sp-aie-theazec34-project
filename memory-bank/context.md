# Context (resumen ejecutivo del proyecto)

## 1. Que es este proyecto
El dominio de negocio definido oficialmente esta en `Brasaland.md`, y la motivacion del enfoque esta en `Brasaland_Eleccion.md`.

Brasaland se modela como restaurante con foco en:
- Logistica (encargos, proveedores, facturacion).
- Marketing/carta (menu, alergenos, visibilidad digital).
- Operacion de reservas y pedidos a domicilio.

## 2. Entidades oficiales a implementar (fuente de verdad)
Segun `Brasaland.md`, el dominio TypeScript debe cubrir:
- `EncargoProveedor`
- `PlatoCarta`
- `ReservaMesa`
- `PedidoDomicilio`

Cada entidad tiene reglas estrictas de validacion y reportes obligatorios por estado/categoria/plataforma.

## 3. Estado actual real del repo
### Frontend
- Web de Brasaland ya funcional en `index.html` y `application.html`.
- Carta en vista unica continua.
- Integracion de imagenes de platos desde carpeta `Imagenes`.
- Branding actualizado con `Imagenes/Icono principal.png` (favicon y logo visible).

### Backend/logica TS de hito
- Existe capa TypeScript en `src/`, pero hoy sigue orientada a dominio de elecciones (`Candidate`, `Vote`, `Election`).
- Esto no esta alineado aun con el dominio Brasaland exigido en `Brasaland.md` y `README.md`.

## 4. Stack y ejecucion
- Node.js >= 18.
- Scripts principales:
  - `npm run typecheck`
  - `npm run build`
  - `npm run demo`
  - `npm run build:web`
  - `npm run serve` (servidor local en puerto 3000)

## 5. Brecha principal a cerrar
La brecha clave es de coherencia funcional:
- La experiencia web esta bastante avanzada para Brasaland.
- El modelo y utilidades TypeScript de hito 2 todavia no migraron al dominio Brasaland.

## 6. Prioridad recomendada de trabajo
1. Migrar `src/types/models.ts` a las 4 entidades de Brasaland.
2. Reescribir `src/utils/validations.ts` con reglas exactas de `Brasaland.md`.
3. Adaptar `src/demo.ts` para reportes de encargos, carta, reservas y domicilio.
4. Revisar README para mantenerlo sincronizado con implementacion real.

## 7. Rama de trabajo
- Rama activa para continuar: `hito-4`.
