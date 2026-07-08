# Propuesta de arquitectura backend — Brasaland

**Autor:** Equipo Brasaland Digital  
**Destinatario:** Project Manager / Felipe Guerrero  
**Fecha:** Julio 2026  
**Estado:** Borrador para revisión antes del próximo sprint  

---

## 1. Contexto y objetivo del documento

Brasaland es un restaurante de cocina brasileña con operación en sala, reservas de mesa y pedidos a domicilio integrados con agregadores (`uber`, `just_eat`, `web_propia`). El reto funcional central es **automatizar reservas y pedidos de forma segura**, evitando solapes de mesa y reduciendo la dependencia de llamadas telefónicas.

En el monorepo ya existen:

- **Frontend público** (`uis/website`): carta, formulario de reservas/pedidos.
- **Backoffice interno** (`uis/backoffice`): panel de operaciones (encargos, reservas, domicilio, catálogo).
- **Dominio TypeScript** (`src/`, `Brasaland.md`): cuatro entidades con reglas de validación y reportes de agregación ya definidos.

El backend que vamos a levantar será un **servicio API independiente** (FastAPI) que ambos frontends consumirán por HTTP. Este documento recoge el razonamiento arquitectónico antes de configurar el entorno y los primeros endpoints.

---

## 2. Características del proyecto que condicionan la arquitectura

| Característica | Implicación arquitectónica |
| -------------- | -------------------------- |
| Cuatro entidades de negocio bien delimitadas (`EncargoProveedor`, `PlatoCarta`, `ReservaMesa`, `PedidoDomicilio`) | Candidato natural a **módulos por dominio** (bounded contexts), no a capas técnicas globales. |
| Reglas de validación estrictas y literales (estados, categorías, rangos ISO, importes) | La lógica de negocio debe vivir en una **capa de dominio/aplicación testeable**, no en los routers. |
| Reportes de agregación obligatorios por estado, categoría y plataforma | Los casos de uso de lectura/analítica deben ser explícitos y reutilizables desde backoffice y futuros agentes. |
| Dos departamentos prioritarios: logística y marketing/carta | La estructura de carpetas puede reflejar esos **contextos de negocio** sin forzar microservicios. |
| Dos clientes separados (website + backoffice) | API versionada, contratos estables (OpenAPI) y **autenticación diferenciada** por tipo de cliente. |
| Regla crítica de reservas: evitar solape de mesa | Requiere **servicio de dominio** con invariantes (disponibilidad, transiciones de estado), no solo CRUD. |
| Integración con plataformas externas de delivery | Punto de extensión en infraestructura (adaptadores), sin contaminar el núcleo de negocio. |
| Monorepo con convención `apps/` para aplicaciones | El backend debe residir en `apps/brasaland-api/` como aplicación autónoma documentada. |

---

## 3. Patrón arquitectónico propuesto

### Patrón: **Monolito modular con Clean Architecture y organización DDD por dominios**

Propongo un **monolito modular** estructurado en capas (Clean Architecture) y agrupado por **contextos acotados** (Domain-Driven Design), no microservicios ni una estructura plana por tipo de archivo (`routers/`, `models/`, `schemas/` globales).

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation (FastAPI routers, Pydantic schemas, HTTP)     │
├─────────────────────────────────────────────────────────────┤
│  Application (casos de uso: crear reserva, reporte encargos)│
├─────────────────────────────────────────────────────────────┤
│  Domain (entidades, reglas, interfaces de repositorio)      │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure (SQLAlchemy, DB, clientes externos, email)    │
└─────────────────────────────────────────────────────────────┘
         ▲ dependencias apuntan hacia adentro (hacia Domain)
```

### Por qué encaja con Brasaland

1. **Escala de equipo y proyecto adecuada.** Somos un equipo pequeño arrancando un sprint; un monolito modular evita la complejidad operativa de microservicios (despliegues, trazas distribuidas, contratos entre servicios) sin renunciar a límites claros entre dominios.

2. **Alineación directa con el modelo de negocio.** Las cuatro entidades de `Brasaland.md` ya son bounded contexts naturales. Agrupar código por dominio (`logistica`, `carta`, `reservas`, `domicilio`) permite que dos desarrolladores trabajen en paralelo con menos conflictos de merge que si todos comparten un único `models.py`.

3. **Reglas de negocio complejas y centralizadas.** La validación de reservas (comensales 1–40, ISO con zona, estados permitidos) y la **prevención de solapes de mesa** no pertenecen a FastAPI ni a SQLAlchemy. En Clean Architecture viven en Domain/Application y se prueban con unit tests sin levantar servidor HTTP.

4. **Frontends separados, contrato único.** Website y backoffice comparten la misma API REST versionada (`/api/v1/...`). La capa Presentation traduce HTTP ↔ casos de uso; los frontends solo conocen schemas Pydantic expuestos en OpenAPI, no modelos de base de datos.

5. **Extensibilidad hacia agentes de IA y pipelines.** El monorepo ya contempla `agents/` y `workflows/`. Un backend con casos de uso bien definidos permite que un agente invoque la misma lógica que el backoffice, en lugar de duplicar reglas en prompts o scripts sueltos.

6. **Convención FastAPI recomendada para proyectos medianos.** La comunidad y plantillas recientes (estructura por feature/dominio, routers con prefijo, dependency injection) favorecen este enfoque frente al layout "todos los routers en una carpeta" cuando hay más de dos o tres áreas funcionales.

### Qué descartamos y por qué

| Alternativa | Motivo de descarte |
| ----------- | ------------------- |
| **Estructura por tipo de archivo** (`routers/`, `models/`, `schemas/` globales) | Funciona en prototipos, pero con cuatro dominios y dos frontends genera acoplamiento, archivos gigantes y confusión sobre dónde va cada regla. |
| **Microservicios** (un servicio por entidad) | Sobredimensionado para el alcance actual; duplica despliegue, observabilidad y consistencia transaccional (p. ej. confirmar reserva + actualizar ocupación). |
| **Arquitectura hexagonal pura sin módulos de dominio** | Válida, pero sin la agrupación por bounded context el equipo pierde el mapa mental de "esto es logística vs. esto es carta". |

---

## 4. Estructura de carpetas y módulos

El backend vivirá en **`apps/brasaland-api/`**, coherente con la convención del monorepo (`apps/` = una aplicación por carpeta).

### Árbol propuesto

```text
apps/brasaland-api/
├── README.md                      # Cómo arrancar, variables de entorno, endpoints
├── pyproject.toml                 # Dependencias (FastAPI, SQLAlchemy, pydantic-settings…)
├── alembic/                       # Migraciones de base de datos
├── tests/
│   ├── unit/                      # Tests de dominio y casos de uso (sin HTTP)
│   ├── integration/               # Tests con DB / API
│   └── conftest.py
└── src/
    └── brasaland_api/
        ├── main.py                # Factory de FastAPI, montaje de routers, CORS
        ├── core/                  # Transversal a toda la app
        │   ├── config.py          # Settings (pydantic-settings, .env)
        │   ├── database.py        # Session, engine
        │   ├── dependencies.py    # Inyección de dependencias compartida
        │   ├── exceptions.py      # HTTPException mappers, errores de dominio
        │   └── middleware.py      # CORS, logging, correlation-id
        ├── shared/                # Kernel compartido (mínimo)
        │   ├── schemas.py         # Respuestas comunes (paginación, ErrorResponse)
        │   └── datetime_utils.py  # Validación ISO 8601 reutilizable
        └── domains/
            ├── logistica/         # EncargoProveedor
            │   ├── domain/
            │   │   ├── entities.py
            │   │   ├── value_objects.py   # EstadoEncargo, Importe
            │   │   └── ports.py           # EncargoRepository (Protocol)
            │   ├── application/
            │   │   ├── services.py        # CrearEncargo, TransicionEstado
            │   │   └── reportes.py        # Conteo/suma/promedio por estado
            │   ├── infrastructure/
            │   │   ├── models.py          # SQLAlchemy ORM
            │   │   └── repositories.py
            │   └── presentation/
            │       ├── router.py
            │       └── schemas.py         # Pydantic request/response
            ├── carta/               # PlatoCarta
            │   └── … (misma estructura de 4 capas)
            ├── reservas/            # ReservaMesa + reglas de solape
            │   └── …
            └── domicilio/           # PedidoDomicilio + plataformas
                └── …
```

### Criterio de separación por dominio o responsabilidad

| Carpeta / módulo | Responsabilidad | Criterio de pertenencia |
| ---------------- | --------------- | ----------------------- |
| `core/` | Configuración, seguridad, DB, middleware | Código usado por **todos** los dominios; no contiene reglas de Brasaland. |
| `shared/` | Utilidades y schemas HTTP genéricos | Solo lo **verdaderamente transversal**; si algo es específico de reservas, va en `domains/reservas/`. |
| `domains/logistica/` | Ciclo de vida de encargos a proveedores | Todo lo que mencione `EncargoProveedor`, estados `borrador→facturado`, reportes de importe. |
| `domains/carta/` | Gestión del menú digital | `PlatoCarta`, categorías, alérgenos, precios, platos activos. |
| `domains/reservas/` | Reservas de mesa y ocupación | `ReservaMesa`, disponibilidad de mesa, solapes temporales. |
| `domains/domicilio/` | Pedidos a domicilio | `PedidoDomicilio`, plataformas, estados de reparto. |

**Regla de dependencias entre dominios:** un dominio **no importa** implementaciones internas de otro. Si en el futuro un pedido web propia necesita consultar platos activos, se expone un **puerto/interfaz explícita** en `carta` consumida por `domicilio`, o se orquesta en un caso de uso de aplicación en capa superior — nunca un `from domains.carta.infrastructure.models import ...` desde otro dominio.

**Correspondencia con departamentos de negocio:**

- **Logística** → `domains/logistica/`
- **Marketing / carta** → `domains/carta/` (+ endpoints públicos de lectura para website)
- **Operación sala** → `domains/reservas/`
- **Operación domicilio / agregadores** → `domains/domicilio/`

---

## 5. Organización de endpoints y routers FastAPI

### Principios

1. **Un router por dominio**, registrado en `main.py` con prefijo de versión común.
2. **Routers delgados:** validar entrada (Pydantic), llamar al caso de uso, mapear salida o error HTTP.
3. **Versionado explícito:** prefijo `/api/v1` para permitir evolución sin romper frontends.
4. **OpenAPI como contrato** entre backend, `uis/website`, `uis/backoffice` y futuros consumidores.

### Montaje en la aplicación

```python
# Conceptual — no es código de implementación
app = FastAPI(title="Brasaland API", version="1.0.0")

app.include_router(logistica_router,  prefix="/api/v1/logistica",  tags=["Logística"])
app.include_router(carta_router,      prefix="/api/v1/carta",      tags=["Carta"])
app.include_router(reservas_router,   prefix="/api/v1/reservas",   tags=["Reservas"])
app.include_router(domicilio_router,  prefix="/api/v1/domicilio",  tags=["Domicilio"])
```

### Mapa de endpoints por dominio

#### Logística — `EncargoProveedor`

| Método | Ruta | Consumidor principal | Descripción |
| ------ | ---- | -------------------- | ----------- |
| `GET` | `/api/v1/logistica/encargos` | Backoffice | Listado con filtros por estado y proveedor |
| `POST` | `/api/v1/logistica/encargos` | Backoffice | Alta de encargo (estado inicial `borrador`) |
| `GET` | `/api/v1/logistica/encargos/{id}` | Backoffice | Detalle |
| `PATCH` | `/api/v1/logistica/encargos/{id}/estado` | Backoffice | Transición controlada (`borrador→enviado→recibido→facturado`) |
| `GET` | `/api/v1/logistica/reportes/por-estado` | Backoffice | Conteo, suma y promedio de `importeTotal` por estado |

#### Carta — `PlatoCarta`

| Método | Ruta | Consumidor principal | Descripción |
| ------ | ---- | -------------------- | ----------- |
| `GET` | `/api/v1/carta/platos` | Website, Backoffice | Listado; website solo platos `activoEnCarta=true` |
| `GET` | `/api/v1/carta/platos/{id}` | Website, Backoffice | Detalle con alérgenos |
| `POST` | `/api/v1/carta/platos` | Backoffice | Alta de plato |
| `PUT` | `/api/v1/carta/platos/{id}` | Backoffice | Actualización (precio, categoría, alérgenos) |
| `GET` | `/api/v1/carta/reportes/por-categoria` | Backoffice | Conteo activos; suma, promedio, min y max de precio |

#### Reservas — `ReservaMesa`

| Método | Ruta | Consumidor principal | Descripción |
| ------ | ---- | -------------------- | ----------- |
| `GET` | `/api/v1/reservas` | Backoffice | Listado con filtros por estado y fecha |
| `POST` | `/api/v1/reservas` | Website, Backoffice | Crear reserva; **validar solape de mesa** |
| `GET` | `/api/v1/reservas/disponibilidad` | Website | Consulta de mesas libres por franja (`fechaHora`, comensales) |
| `PATCH` | `/api/v1/reservas/{id}/estado` | Backoffice | Confirmar, cancelar, completar |
| `GET` | `/api/v1/reservas/reportes/por-estado` | Backoffice | Conteo por estado; suma de comensales en `confirmada` |

#### Domicilio — `PedidoDomicilio`

| Método | Ruta | Consumidor principal | Descripción |
| ------ | ---- | -------------------- | ----------- |
| `GET` | `/api/v1/domicilio/pedidos` | Backoffice | Listado con filtros por plataforma y estado |
| `POST` | `/api/v1/domicilio/pedidos` | Website, Backoffice | Registrar pedido (`web_propia`; agregadores vía webhook futuro) |
| `PATCH` | `/api/v1/domicilio/pedidos/{id}/estado` | Backoffice | Flujo `recibido→…→entregado` o `cancelado` |
| `GET` | `/api/v1/domicilio/reportes/por-plataforma` | Backoffice | Conteo por plataforma; suma importes excluyendo `cancelado` |

### Autenticación y permisos por tipo de cliente

| Ámbito | Website (`uis/website`) | Backoffice (`uis/backoffice`) |
| ------ | ----------------------- | ------------------------------ |
| Lectura de carta activa | Público o API key de solo lectura | Autenticado |
| Crear reserva / pedido web | Público con rate limiting | Autenticado |
| CRUD completo, reportes, transiciones de estado | No permitido | Rol operaciones / admin |

La configuración CORS en `core/middleware.py` debe listar explícitamente los orígenes de desarrollo y producción de ambos frontends.

### Convenciones de nombres en routers

- Archivo: `domains/<dominio>/presentation/router.py`
- Instancia: `<dominio>_router = APIRouter()`
- Tags OpenAPI: nombre del dominio en español para legibilidad del PM y del equipo
- Schemas: sufijos `Create`, `Update`, `Response`, `Report` (p. ej. `ReservaCreate`, `ReservaResponse`)

---

## 6. Decisiones técnicas iniciales

| Decisión | Elección propuesta | Justificación |
| -------- | ------------------ | ------------- |
| Framework | **FastAPI** | Tipado, validación Pydantic alineada con reglas de `Brasaland.md`, OpenAPI automático para frontends separados. |
| Persistencia | **PostgreSQL + SQLAlchemy 2.x + Alembic** | Relaciones reserva–mesa, transacciones para evitar solapes, migraciones versionadas. |
| Validación de entrada | **Pydantic v2** en Presentation; reglas de negocio en Domain | Pydantic cubre formato ISO y rangos; invariantes (solape, transiciones) en servicios de aplicación. |
| Inyección de dependencias | **`Depends()` de FastAPI** + factories en `core/dependencies.py` | Patrón idiomático; facilita tests con repos en memoria. |
| Contrato con frontends | **OpenAPI 3 + tipos generados opcionales** | El equipo TS puede generar clientes desde el schema; alinea con `src/types/models.ts` como referencia de nombres. |
| Configuración | **`pydantic-settings`** + `.env` | Coherente con despliegue en contenedor y distintos entornos. |
| Tests | **pytest**; unit en dominio, integration con TestClient | Las reglas de Felipe ("sin atajos en cálculos") exigen tests de reportes y validaciones. |
| Ubicación en monorepo | **`apps/brasaland-api/`** | Separación clara de `uis/*`; un README por aplicación. |

### Alineación con el dominio TypeScript existente

Los nombres de campos, literales de estado y reglas de `Brasaland.md` / `src/types/models.ts` deben ser **la fuente de verdad compartida**. Recomendación: mantener `Brasaland.md` como documento de contrato y verificar en CI que los enums Pydantic coinciden (test de contrato o checklist en PR).

---

## 7. Riesgos y puntos de atención

### Riesgo 1 — Lógica de negocio en los routers ("fat controllers")

**Qué puede salir mal:** Si cada endpoint implementa validaciones, transiciones de estado y cálculos de reportes inline, tendremos reglas duplicadas e inconsistentes entre endpoints (p. ej. un `POST /reservas` que sí comprueba solape y un `PATCH` que no).

**Señales de alerta:** Archivos `router.py` de más de ~150 líneas, imports de SQLAlchemy en presentation, tests que solo existen como e2e HTTP.

**Mitigación:** Obligar el flujo `router → service/use_case → repository`. Code review checklist: "¿Hay `if estado == ...` en el router?" → mover a `application/services.py`.

---

### Riesgo 2 — Estructura por capas técnicas globales en lugar de por dominio

**Qué puede salir mal:** Organizar como `app/routers/`, `app/models/`, `app/schemas/` mezclando las cuatro entidades provoca que dos personas editen los mismos archivos, que las reglas de reservas queden lejos de su router y que nadie sepa "dueño" de cada módulo.

**Señales de alerta:** `models.py` con 800 líneas, imports circulares entre schemas, dificultad para extraer un dominio a microservicio más adelante.

**Mitigación:** Adoptar desde el día uno la estructura `domains/<nombre>/` con las cuatro subcapas. Documentar en el README del backend el mapa dominio ↔ carpeta.

---

### Riesgo 3 — Divergencia de reglas entre backend, frontends y `Brasaland.md`

**Qué puede salir mal:** El website valida `numeroComensales <= 40` en el formulario pero el backend acepta 50; los reportes del backoffice no excluyen pedidos `cancelado` en las sumas como exige el brief.

**Mitigación:** Tests unitarios de validación por entidad tomando casos de `Brasaland.md`; endpoint de health + versión de contrato; revisión cruzada TS/Python en PRs que toquen tipos.

---

### Riesgo 4 — Acoplamiento entre dominios por imports directos

**Qué puede salir mal:** `domicilio` importa modelos ORM de `carta` para leer precios; un cambio en carta rompe domicilio silenciosamente.

**Mitigación:** Interfaces (`Protocol`) en domain ports; comunicación solo vía casos de uso o API interna documentada; considerar `import-linter` en CI cuando haya más de dos dominios interdependientes.

---

## 8. Próximos pasos sugeridos (fuera de este documento)

1. Crear esqueleto `apps/brasaland-api/` con `main.py`, healthcheck y un dominio piloto (`carta` — lectura pública de platos).
2. Definir `.env.example` y documentar arranque local con Docker Compose (API + PostgreSQL).
3. Configurar CORS para orígenes de `uis/website` y `uis/backoffice` en desarrollo.
4. Primer endpoint real: `GET /api/v1/carta/platos` consumido desde el website.
5. Añadir tests de contrato para enums y rangos de `Brasaland.md`.

---

## 9. Resumen ejecutivo

| Pregunta | Respuesta |
| -------- | --------- |
| ¿Qué patrón? | Monolito modular + Clean Architecture + DDD por dominios |
| ¿Por qué? | Cuatro entidades claras, reglas estrictas, dos frontends, equipo paralelo, sin sobrecarga de microservicios |
| ¿Dónde vive? | `apps/brasaland-api/src/brasaland_api/domains/{logistica,carta,reservas,domicilio}/` |
| ¿Cómo se exponen APIs? | Routers FastAPI por dominio bajo `/api/v1/<dominio>/...`, routers delgados, OpenAPI como contrato |
| ¿Principal riesgo? | Fat controllers y estructura por tipo de archivo; ambos erosionan reglas de negocio y escalabilidad del equipo |

Este documento es la base para acordar estructura antes del sprint de configuración de entorno y primeros endpoints. No incluye implementación; el siguiente paso es validarlo con el PM y Felipe y, una vez aprobado, generar el esqueleto del proyecto.
