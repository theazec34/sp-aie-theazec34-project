# Auditoría de gestión de errores — Brasaland Digital

**Rama:** `error-handling-audit`  
**Alcance:** monorepo completo (backoffice Next.js, API FastAPI, `uis/web`, `uis/website`, scripts)  
**Modo:** informe previo a correcciones (sin cambios funcionales ajenos a errores)

## Resumen

La plataforma ya tenía buenas piezas (panel de incidencias, handlers 400/500, mensajes de red en login).  
La auditoría localizó huecos de consistencia: errores crudos en UI, falta de CTA “Reintentar”, decode UTF-8 sin captura, logging insuficiente en 500, scripts con I/O sin `try/except`, y el formulario del website que simulaba éxito sin red.

## Hallazgos priorizados

### CRÍTICO
| ID | Archivo | Categoría | Problema |
|----|---------|-----------|----------|
| C1 | `services/api/seed_auth.py` | Filtración sensible | Password de demo en código (se mantiene a petición del alumno para clase; limpia futura). |
| C2 | `services/api/app/auth/email.py` | Filtración sensible | Enlace de reset (JWT) impreso en consola. |

### ALTO
| ID | Archivo | Categoría | Problema |
|----|---------|-----------|----------|
| A1 | `services/api/app/errors.py` | Catch amplio / silent | Handler 500 no registra la excepción internamente. |
| A2 | `services/api/app/main.py` | try ausente | `.decode("utf-8")` sin `UnicodeDecodeError` → 500 opaco. |
| A3 | `uis/website/.../ApplicationForm.tsx` | Fallo silencioso / UX | “Enviado correctamente” sin backend. |

### MEDIO
| ID | Archivo | Categoría | Problema |
|----|---------|-----------|----------|
| M1 | `uis/backoffice/.../proveedores/page.tsx` | Error crudo / sin CTA | `JSON.stringify` y sin Reintentar junto al alert. |
| M2 | `uis/backoffice/.../account/profile` | Sin CTA | Error de carga sin reintentar. |
| M3 | `uis/backoffice/.../change-password` | Error crudo | “Failed to fetch” sin `networkErrorMessage`. |
| M4 | `uis/backoffice/.../register` | Parseo | No lee `errors[]` del handler custom. |
| M5 | `uis/web/app.js` | Error crudo | `detail` objeto → `[object Object]`. |
| M6 | Backoffice / website | Boundaries | Sin `error.tsx`. |
| M7 | `scripts/analyze.py` | I/O | Sin captura de encoding/IO. |

### Ya correcto (referencia)
- `/incidents` y `/incidents/resumen`: loading / error / Reintentar.
- `app/errors.py`: 400 estructurado y 500 genérico al cliente.
- `scripts/seed_incidents.py`: exit code 1 si falta CSV.

## Plan de commits
1. Este informe  
2. Backend  
3. Scripts  
4. Backoffice  
5. `uis/web` + website  
6. Logs sensibles + `progress.md`

## Nota de alcance
No se introducen features nuevas ni refactors ajenos a la gestión de errores.
