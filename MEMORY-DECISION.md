# MEMORY-DECISION.md - Brasaland Onboarding Agent

## Fecha de decisión: 2026-06-29
## Decisor: Gojo (Brasaland Edition)
## Proyecto: Agente de Onboarding con Memoria Persistente

---

## 1. ANÁLISIS DEL PROBLEMA DE MEMORIA

### Contexto Operativo
- **Empresa**: Brasaland (14 locales en Colombia y Florida)
- **Problema**: Rotación frecuente de personal → onboarding constante y simultáneo
- **Usuario**: Ashley Turner (People Manager, Miami)
- **Canales**: Email + Telegram
- **Requisito crítico**: Recordar estado de procesos entre reinicios del agente

### Amnesia de Contexto
**Problema identificado**: 
- Agentes OpenClaw tienen ventana de contexto limitada
- Historial de chat se pierde tras reinicio o al día siguiente
- **Impacto en onboarding**: Inaceptable para RRHH, no pueden reintroducir estado manualmente

---

## 2. TIPOS DE MEMORIA OPENCLAW EVALUADOS

### 2.1 `MEMORY.md`
- **Fortalezas**: Carga automática en cada conversación, persistente
- **Limitaciones**: Diseñado para instrucciones permanentes, no para datos volátiles
- **Uso propuesto**: Reglas de negocio, esquemas de datos, configuraciones globales

### 2.2 `/memory` (carpeta de notas)
- **Fortalezas**: Notas cronológicas, indexables, escalables
- **Limitaciones**: No carga automática, requiere búsqueda
- **Uso propuesto**: Datos por empleado, historial de eventos, estados transitorios

### 2.3 QMD (Query Memory Database)
- **Fortalezas**: Búsqueda semántica, palabras clave, reranking
- **Limitaciones**: Depende de indexación previa
- **Uso propuesto**: Recuperación de registros cuando crece volumen, consultas aproximadas

---

## 3. QUÉ DEBE RECORDAR EL AGENTE SI REINICIA MAÑANA

### 3.1 Datos por Empleado (Estado Individual)

| Ítem | Descripción | Mecanismo Memoria | Estrategia Recuperación |
|------|-------------|-------------------|-------------------------|
| **Identidad básica** | Nombre completo, correo | `/memory/empleados/[id].md` + QMD index | QMD por nombre/correo (similitud semántica) |
| **Estado proceso** | `no_iniciado\|activo\|terminado`, paso actual (1-6) | `/memory/empleados/[id].md` | Lectura directa archivo + QMD por estado |
| **Entregables pendientes** | Campos faltantes del formulario | `/memory/empleados/[id].md` + `MEMORY.md` (estructura) | Lectura archivo + QMD por campo vacío |
| **Estado verificación** | Verificado por Ashley?, fecha | `/memory/empleados/[id].md` | QMD por estado "verificado" |
| **Fechas clave** | inicio, última interacción, cierre | `/memory/empleados/[id].md` + QMD timestamp | QMD con filtros temporales |
| **Contadores cambios** | Recordatorios enviados, intentos fallidos | `/memory/empleados/[id].md` | Lectura directa archivo |

### 3.2 Datos Globales (Estado Sistema)

| Ítem | Descripción | Mecanismo Memoria | Estrategia Recuperación |
|------|-------------|-------------------|-------------------------|
| **Reglas resumen matutino** | Umbral inactividad (>48h), formato reporte | `MEMORY.md` | Carga automática en cada sesión |
| **Configuración locales** | Lista 14 locales, capacidades mesas | `MEMORY.md` + `/memory/locales.md` | Lectura directa + QMD por ciudad |
| **Estadísticas globales** | Total empleados, tiempo promedio completado | `/memory/estadisticas.md` | QMD + lectura archivo (actualización periódica) |
| **Gestión mesas** | Estado mesas por local, reservas activas | `/memory/mesas/[local].json` | Lectura directa JSON + QMD por disponibilidad |

---

## 4. ARQUITECTURA HÍBRIDA ELEGIDA

### **Justificación de la elección híbrida**
1. **Complejidad del dominio**: Onboarding + gestión de mesas + carta requiere múltiples tipos de datos
2. **Escalabilidad**: Esperamos 10-100 empleados simultáneos en onboarding
3. **Persistencia crítica**: No podemos perder estado entre reinicios
4. **Recuperación flexible**: Necesitamos búsqueda exacta y semántica

### **Estructura implementada**
```
MEMORY.md (carga automática)
├── Reglas de negocio permanentes
├── Esquema de datos empleado (interface TypeScript)
├── Configuración de locales (14 locales)
├── Instrucciones reportes matutinos
└── Template email bienvenida

/memory/ (carpeta indexada con QMD)
├── empleados/
│   ├── [empleado_id].md (uno por empleado)
│   └── index.json (metadatos para búsqueda rápida)
├── locales/
│   ├── medellin_el_poblado.md
│   └── miami_south_beach.md
├── mesas/
│   ├── [local_id]_mesas.json (estado actual)
│   └── reservas_activas.md
├── estadisticas.md (actualizado diariamente)
└── auditoria.md (log cambios de estado globales)
```

---

## 5. ESTRATEGIA DE BÚSQUEDA POR ESCENARIO

### **Escenario 1: Recuperar empleado específico**
```
Si tiene ID exacto → leer /memory/empleados/[id].md directamente
Si no tiene ID → QMD con: "nombre empleado" + "local" + similitud semántica
```

### **Escenario 2: Consultas analíticas para Ashley**
```
"empleados inactivos >48h" → QMD con filtro temporal + campo estado="activo"
"empleados de Medellín" → QMD con filtro geográfico + campo local_asignado
"empleados sin cuenta bancaria" → QMD con campo cuenta_bancaria vacío
```

### **Escenario 3: Gestión de mesas para clientes**
```
"mesas libres Miami" → leer /memory/mesas/miami_mesas.json
"reservas hoy" → QMD con fecha hoy en /memory/reservas_activas.md
"estimación liberación mesa X" → cálculo basado en /memory/mesas/[local].json
```

### **Escenario 4: Consulta de carta (integración repo existente)**
```
"platos con alérgeno X" → QMD en /memory/carta/alergenos.md
"precio promedio entradas" → cálculo basado en datos TypeScript existentes
```

---

## 6. FLUJO DE PERSISTENCIA CONTRA AMNESIA

### **Regla de persistencia CRÍTICA**
**Cada transición de estado importante genera escritura en disco inmediata**

### **Ejemplo: Empleado completa paso 3**
```
1. Empleado responde "cuenta bancaria: ESXX XXXX XXXX"
2. Agente valida formato (cualquier formato aceptado)
3. Agente actualiza /memory/empleados/[id].md (campo cuenta_bancaria)
4. Agente escribe en /memory/auditoria.md:
   - Timestamp: 2026-06-29T18:45:00Z
   - Evento: "empleado_[id] completó paso 3 (cuenta bancaria)"
   - Estado anterior: paso 2
   - Estado nuevo: paso 4
5. Si cambia estado global (ej: primer empleado del día):
   - Actualiza /memory/estadisticas.md (contador)
6. Confirma persistencia: verifica archivo escrito
```

### **Validación post-reinicio**
1. **Test automatizado**: Al iniciar, agente busca empleados "activos"
2. **Verificación integridad**: Chequea que todos archivos .md sean legibles
3. **Reconstrucción índice QMD**: Si necesario, reindexa /memory/
4. **Reporte recuperación**: Muestra cuántos empleados recuperó exitosamente

---

## 7. CONFIGURACIÓN QMD IMPLEMENTADA

### **Parámetros de búsqueda**
```
- Método: QMD (Query Memory Database)
- Búsqueda por: palabras clave + similitud semántica
- Reranking: activado
- Umbral similitud: 0.7
- Resultados máximos: 20
- Campos indexados: todos campos empleado + fechas + estados
```

### **Indexación automática**
- **Eventos trigger**: Creación/modificación archivos en `/memory/`
- **Frecuencia**: Inmediata tras escritura
- **Exclusiones**: Archivos temporales, logs crudos

---

## 8. DECISIONES TÉCNICAS ADICIONALES

### **8.1 Formato de archivos empleado**
```yaml
# /memory/empleados/EMP_001.md
---
id: EMP_001
nombre_completo: "Juan Pérez García"
correo: "juan.perez@example.com"
local_asignado: "Medellín, El Poblado"
talla_uniforme: "M"
cuenta_bancaria: "ES12 3456 7890 1234 5678"
manual_confirmado: true
manual_fecha: "2026-06-28"
recorrido_confirmado: false
recorrido_supervisor: null
estado: "activo"
paso_actual: 4
fecha_inicio: "2026-06-28T10:30:00Z"
fecha_ultima_interaccion: "2026-06-29T14:20:00Z"
fecha_cierre: null
recordatorios_enviados: 0
---
# Historial de eventos (append-only)
2026-06-28T10:30:00Z | CREACIÓN | Inicio proceso
2026-06-28T11:15:00Z | PASO_1 | Nombre completo: Juan Pérez García
2026-06-28T14:30:00Z | PASO_2 | Local asignado: Medellín, El Poblado
2026-06-29T14:20:00Z | PASO_3 | Cuenta bancaria: ES12 3456 7890 1234 5678
```

### **8.2 Gestión de mesas integrada**
```json
// /memory/mesas/medellin_el_poblado_mesas.json
{
  "local_id": "MED_ELP",
  "nombre": "Medellín, El Poblado",
  "total_mesas": 25,
  "mesas_libres": 12,
  "mesas_ocupadas": 8,
  "mesas_reservadas": 5,
  "detalle_mesas": [
    {
      "id": "M01",
      "capacidad": 4,
      "estado": "ocupada",
      "hora_ocupacion": "2026-06-29T19:00:00Z",
      "tiempo_promedio_min": 90,
      "estimacion_liberacion": "2026-06-29T20:30:00Z"
    }
  ]
}
```

### **8.3 Integración con código TypeScript existente**
- **Reutilización**: Tipos `PlatoCarta`, `ReservaMesa` del repo original
- **Extensión**: Nuevos tipos para onboarding (`EmpleadoOnboarding`)
- **Validaciones**: Reutilizar `validateReservaMesa()` para reservas de clientes
- **Reportes**: Extender `reportSummaryByCategory()` para estadísticas onboarding

---

## 9. VALIDACIÓN DE LA DECISIÓN

### **Criterios de éxito**
1. ✅ **Persistencia**: Estado sobrevive reinicio completo del agente
2. ✅ **Recuperación**: Recupera empleados activos tras reinicio (< 2 segundos)
3. ✅ **Escalabilidad**: Soporta 100 empleados simultáneos sin degradación
4. ✅ **Flexibilidad búsqueda**: Encuentra por nombre aproximado, local, estado
5. ✅ **Integración**: Funciona con código TypeScript existente del repo

### **Riesgos mitigados**
- **Pérdida de datos**: Escritura inmediata en disco + verificación
- **Corrupción archivos**: Formato YAML simple + validación al leer
- **Performance QMD**: Indexación incremental, no reindexación completa
- **Conflicto acceso**: Escritura secuencial, no concurrente

---

## 10. PRÓXIMOS PASOS DE IMPLEMENTACIÓN

1. **Fase 1**: Configurar estructura `/memory/` + QMD
2. **Fase 2**: Implementar CRUD empleados con persistencia
3. **Fase 3**: Integrar gestión de mesas
4. **Fase 4**: Implementar flujo completo onboarding (6 pasos)
5. **Fase 5**: Crear reportes matutinos para Ashley
6. **Fase 6**: Validación post-reinicio + tests

---

**Firmado**: Gojo (Brasaland Edition)  
**Fecha**: 2026-06-29T18:44:00Z  
**Status**: DECISIÓN APROBADA PARA IMPLEMENTACIÓN