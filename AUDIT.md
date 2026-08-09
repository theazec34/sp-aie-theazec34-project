# AUDIT — Performance (Brasaland website + backoffice)

Fecha baseline: 2026-08-09  
Herramienta: Lighthouse CLI 12.8 (Chrome headless)  
Modo de medición: builds de producción (`next build` + `next start`) — métricas más realistas que `next dev`.  
Skills de agente usadas: `core-web-vitals`, `performance`, `web-perf` (instaladas en `.agents/skills/`).

Evidencia: `audit/before/*.report.html`, `*.report.json`, `*.png`.

---

## 1. Scores iniciales (Lighthouse)

### Website — `/` (uis/website)

| Modo | Performance | Accessibility | Best Practices | SEO | LCP | CLS |
|------|-------------|---------------|----------------|-----|-----|-----|
| Mobile | **97** | 100 | 96 | 100 | 2.6 s | 0 |
| Desktop | **83** | 100 | 96 | 100 | **3.0 s** | 0 |

### Backoffice — `/login` (uis/backoffice)

| Modo | Performance | Accessibility | Best Practices | SEO | LCP | CLS |
|------|-------------|---------------|----------------|-----|-----|-----|
| Mobile | **88** | 95 | 96 | 100 | 2.5 s | **0.199** |
| Desktop | **85** | 95 | 96 | 100 | **2.7 s** | 0.04 |

Objetivos de referencia del hito: Performance ≥ 90, LCP < 2.5 s, CLS < 0.1.

---

## 2. Problemas y causa raíz

### Website

1. **LCP alto (desktop 3.0 s / mobile 2.6 s)**  
   - *Causa:* imágenes de carta/galería en `public/Imagenes/` (~2 MB PNG cada una, ~19 MB total). Lighthouse: “Properly size images” (~202–282 KiB).  
   - *Causa secundaria:* el logo en header usa `priority` pero no es el LCP; el primer plato no está priorizado.

2. **Imágenes mal dimensionadas para el viewport**  
   - *Causa:* `DishCard`/`GalleryGrid` no pasan `sizes`; CSS fuerza `height: 190/210px` distinto del aspect ratio de `width`/`height` en `next/image` → riesgo de CLS y srcset incorrecto.

3. **JS no crítico en la ruta crítica (~50 KiB unused)**  
   - *Causa:* `ApplicationForm` (`"use client"`) se importa estáticamente en `page.tsx` aunque está below-the-fold.

4. **Metadata SEO limitada (secundario)**  
   - *Causa:* solo `title`/`description` básicos; sin Open Graph / canonical explícito.

### Backoffice

1. **CLS mobile 0.199 (por encima de 0.1)**  
   - *Causa:* tarjeta de login sin altura mínima reservada + carga de dos familias tipográficas con varios pesos (IBM Plex 400–700 + Space Grotesk 500/700) → desplazamiento al aplicar fuentes/contenido.

2. **LCP ~2.5–2.7 s**  
   - *Causa:* render-blocking / JS de cliente en página 100% `"use client"`; oportunidad “Eliminate render-blocking resources” (~110–120 ms) y unused JS (~27 KiB).

3. **Shell autenticado duplicado**  
   - *Causa:* cada página repite `RequireAuth` + `AppNav` + `bo-shell` (mantenibilidad; impacto menor en CWV).

---

## 3. Análisis de refactor (duplicación)

### Caso A — Heading de sección (website)
- **Dónde:** patrón `h2.section-title` + `p.section-text` en `MenuSection`, `GalleryGrid`, `ApplicationForm`. Existe `SectionTitle.tsx` sin uso.
- **Por qué:** misma estructura visual repetida → candidato a componente compartido.
- **Propuesta:** usar `SectionTitle` en las tres secciones.

### Caso B — Carga async + error/retry (backoffice)
- **Dónde:** `inventory/products`, `inventory/orders`, `incidents`, `incidents/resumen`, `proveedores` — mismo patrón `loading`/`error`/`load`/`useEffect`/`friendlyCatch`/`Reintentar`.
- **Por qué:** lógica idéntica de ciclo de vida de datos.
- **Propuesta:** Custom Hook `useAsyncResource<T>(loader)` + uso en al menos 2 páginas de inventario.

### Caso C (bonus) — Shell autenticado
- **Dónde:** ~12 páginas con `RequireAuth` + `AppNav`.
- **Propuesta:** `AuthenticatedShell` con prop `active`.

---

## 4. Prioridad de correcciones (skills CWV)

Orden según `core-web-vitals` / `performance`:

1. LCP website — tamaño/priority/`sizes` de imágenes  
2. CLS backoffice login — reserva de layout + menos pesos de fuente  
3. Reducir JS unused — `dynamic()` del formulario  
4. Refactors compartidos (hook + SectionTitle)  
5. Metadata / SEO secundario
