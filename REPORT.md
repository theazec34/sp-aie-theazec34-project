# REPORT — Performance (Brasaland website + backoffice)

Fecha medición final: 2026-08-09  
Ciclo: **Medir → Analizar → Corregir → Medir de nuevo**  
Herramienta: Lighthouse CLI 12.8 (Chrome headless), builds de producción (`next build` + `next start`).  
Skills de agente: `core-web-vitals`, `performance`, `web-perf` (`.agents/skills/`).

Evidencia: `audit/before/` y `audit/after/` (HTML + JSON + PNG). Análisis previo: `AUDIT.md`.

---

## 1. Correcciones aplicadas

### Website (`uis/website`)

| Commit / cambio | KPI / causa | Qué se hizo |
|-----------------|-------------|-------------|
| Comprimir `public/Imagenes` PNG→JPEG | LCP / peso | ~19 MB → ~1.8 MB de fotos de carta |
| `sizes`, `priority`, aspect-ratio | LCP imagen / BP | Primer plato con `priority`; attrs alineados a 960×523 |
| `dynamic()` de `ApplicationForm` | JS unused | Formulario below-the-fold fuera del bundle inicial |
| Metadata + Open Graph | SEO / BP | `description` + `openGraph` en `layout.tsx` |
| `SectionTitle` reutilizado | Refactor | Extraído/usado en Menu, Galería y Formulario |
| Ratios + hero + icono | BP / LCP | Logo y platos con ratio real; H1 display above-the-fold; rebuild limpio (evita CSS 500) |

### Backoffice (`uis/backoffice`)

| Commit / cambio | KPI / causa | Qué se hizo |
|-----------------|-------------|-------------|
| Menos pesos tipográficos | CLS / LCP | IBM Plex 400/600 + Space Grotesk 700 |
| `min-height` + Suspense skeleton | CLS | Reserva layout del `auth-card` y fallback que incluye campo API URL |
| `useAsyncResource` + `AuthenticatedShell` | Refactor | Hook + shell compartidos en inventario / dashboard |
| Contraste AA + favicon | A11y / BP | Accent `#0e7490`, texto botón blanco, `/favicon.png` + `/favicon.ico` |

No se reestructuró la arquitectura de los frontends; solo cambios puntuales de rendimiento, a11y y extracción reutilizable.

---

## 2. Before vs after (misma URL / mismo modo)

### Website — `/`

| Modo | Perf | A11y | BP | SEO | LCP | CLS |
|------|------|------|----|-----|-----|-----|
| Mobile **antes** | 97 | 100 | 96 | 100 | 2.6 s | 0 |
| Mobile **después** | 95 | 100 | **100** | 100 | 3.0 s | 0 |
| Desktop **antes** | 83 | 100 | 96 | 100 | 3.0 s | 0 |
| Desktop **después** | **100** | 100 | **100** | 100 | **0.6 s** | 0 |

Mejora de categoría: **Best Practices** (96→100 en ambos modos) y **Performance desktop** (83→100). LCP desktop baja de 3.0 s a 0.6 s.

### Backoffice — `/login`

| Modo | Perf | A11y | BP | SEO | LCP | CLS |
|------|------|------|----|-----|-----|-----|
| Mobile **antes** | 88 | 95 | 96 | 100 | 2.5 s | **0.199** |
| Mobile **después** | **95** | **100** | **100** | 100 | 2.5 s | **0.099** |
| Desktop **antes** | 85 | 95 | 96 | 100 | 2.7 s | 0.04 |
| Desktop **después** | **100** | **100** | **100** | 100 | **0.8 s** | 0.019 |

Mejora de categoría: **Performance**, **Accessibility** y **Best Practices**. CLS mobile pasa de 0.199 a 0.099 (< 0.1).

> Nota: Lighthouse en lab tiene varianza (± unos puntos de Performance / LCP en mobile). Los números anteriores son la última corrida estable guardada en `audit/after/`. El objetivo del hito no es un 100 perfecto, sino un ciclo documentado con mejora medible.

---

## 3. Mayor impacto (por frontend)

1. **Website — compresión de imágenes + LCP above-the-fold**  
   Reducción masiva de bytes en `Imagenes/` y mantener el H1 como señal LCP en desktop explica el salto 83→100 y LCP 3.0 s → 0.6 s.

2. **Website — aspect-ratio / logo correctos**  
   El único fallo de Best Practices en baseline era el icono 44×44 vs ratio real; alinear attrs + JPEG de platos lleva BP a 100.

3. **Backoffice — CLS del login**  
   Reserva de layout + menos pesos de fuente + skeleton Suspense alineado al formulario real baja CLS bajo el umbral 0.1.

4. **Backoffice — contraste y favicon**  
   Suben Accessibility y Best Practices a 100 (botón AA + sin 404 de `/favicon.ico`).

5. **Refactors**  
   `SectionTitle`, `useAsyncResource` y `AuthenticatedShell` no mueven el score solos, pero eliminan duplicación y facilitan mantener las correcciones.

---

## 4. Evidencia de skills

- Instaladas bajo `.agents/skills/`: `core-web-vitals`, `performance`, `web-perf`.
- Priorización siguiendo CWV: LCP/CLS primero; a11y/BP/SEO después.
- Acciones tipadas por skills: `font-display: swap`, menos font weights, `sizes`/`priority`, `dynamic()` import, aspect-ratio, evitar layout shift.

---

## 5. Refactor entregado

- **Componente:** `uis/website/src/components/SectionTitle.tsx` usado en carta, galería y formulario.
- **Custom Hook:** `uis/backoffice/src/hooks/useAsyncResource.ts` en productos e historial de pedidos.
- **Shell:** `uis/backoffice/src/components/AuthenticatedShell.tsx` en dashboard e inventario.
