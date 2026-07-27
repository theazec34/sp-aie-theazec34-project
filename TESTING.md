# TESTING.md — Brasaland Digital

Guía breve de la batería de pruebas (AUTH-088 + ampliación backoffice / frontend).

## Cómo ejecutar

### Backend (pytest)

Desde la raíz del monorepo (con `.venv` y dependencias de la API):

```bash
source .venv/bin/activate
uv pip install -r services/api/requirements.txt
cd services/api
uv run pytest
# opcional, cobertura del módulo auth:
uv run pytest --cov=app/auth --cov=app/users --cov=app/profiles --cov-report=term-missing
```

Los tests usan TinyDB en directorios temporales: **no tocan** `services/api/data/`.

### Frontend backoffice (Jest)

```bash
cd uis/backoffice
npm install
npm test
# con cobertura:
npm test -- --coverage
```

## Plan de casos (antes de implementar)

### Auth — `POST /users` (registro)
| Tipo | Caso |
|------|------|
| Happy | Registro con email/password válidos → 201 |
| Edge | Password exactamente 8 caracteres → 201 |
| Fail | Email duplicado → 409; campos vacíos / password corta → 400 |

### Auth — `POST /auth/login`
| Tipo | Caso |
|------|------|
| Happy | Credenciales correctas → `access_token` |
| Edge | Usuario inactivo → 401 |
| Fail | Password incorrecta / email inexistente → 401; form vacío → 400/422→400 |

### Auth — `GET /auth/me`
| Tipo | Caso |
|------|------|
| Happy | Bearer válido → email + role (+ profile) |
| Edge | Usuario sin perfil aún (si aplica) |
| Fail | Sin token / token malformado / token basura → 401 |

### Auth — `PUT /profiles/me` (+ GET)
| Tipo | Caso |
|------|------|
| Happy | Actualizar nombre/teléfono → 200 |
| Edge | Campos opcionales a `null` |
| Fail | Sin Bearer → 401 |

### Auth — `POST /auth/forgot-password`
| Tipo | Caso |
|------|------|
| Happy | Email registrado → 200 mensaje genérico |
| Edge | Email no registrado → **también 200** (anti-enumeración) |
| Fail | Body sin email / email inválido → 400 |

### Auth — `POST /auth/reset-password`
| Tipo | Caso |
|------|------|
| Happy | Token válido + password nueva → 200; login con nueva password |
| Edge | Password nueva en límite (8 chars) |
| Fail | Token malformado / ya usado / caducado → 400 |

### Auth — `POST /auth/change-password`
| Tipo | Caso |
|------|------|
| Happy | Actual correcta + nueva distinta → 200 |
| Edge | Nueva igual a actual → 400 |
| Fail | Actual incorrecta → 400; sin auth → 401 |

### Extras bulletproof (auth)
- Token JWT firmado con otro `SECRET_KEY` → 401 en `/auth/me`
- Reset reutilizado → 400
- Login tras change-password solo con la nueva

### Backoffice API (prioridad baja)
- **Suppliers:** listado vacío, alta válida, categoría/país inválidos
- **Incidents:** create + summary, transición de estado inválida, 404

### Jest (uis/backoffice)
- `parseApiErrorPayload` / `networkErrorMessage`
- `labelFor` / `STATUS_TRANSITIONS` (incidents)
- Token helpers (`setToken` / `clearToken` / `getToken`) con `localStorage` mock

## Casos sugeridos / detectados con ayuda de IA

- Anti-enumeración en `forgot-password` (mismo 200 exista o no el email).
- Token de reset de un solo uso (segundo `reset-password` debe fallar).
- Usuario `is_active=false` no puede hacer login.

## Resultados

Ejecutado en rama `limit_testing`:

### Backend
```text
cd services/api && uv run pytest
# → 40 passed
```

Módulos:
- `tests/test_register.py`
- `tests/test_login.py`
- `tests/test_profiles.py`
- `tests/test_password_flows.py`
- `tests/test_suppliers.py`
- `tests/test_incidents.py`

Cobertura orientativa auth (`uv run pytest --cov=app/auth --cov=app/users --cov=app/profiles`):
- **TOTAL ~82%** en esos módulos (auth router ~98%). Cumple el umbral académico ≥70% del ticket AUTH-088.

### Frontend (Jest)
```text
cd uis/backoffice && npm test -- --coverage
# → 10 passed (2 suites)
```

- `src/__tests__/auth-errors.test.ts` — token, networkErrorMessage, parseApiErrorPayload
- `src/__tests__/incidents-utils.test.ts` — labelFor, STATUS_TRANSITIONS

### Bugs / hallazgos al escribir tests
- Ningún bug bloqueante en la API de auth existente.
- Caso reforzado por la batería (sugerido con ayuda de IA): anti-enumeración en forgot-password y reset token de un solo uso.