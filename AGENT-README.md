# Brasaland Agent - Agente de Onboarding con Memoria Persistente

## 🎯 **¿Qué es Brasaland Agent?**

Un agente inteligente que gestiona **onboarding de empleados** y **reservas de mesas** para la cadena de restaurantes Brasaland (14 locales en Colombia y Florida).

## 🧠 **Características principales**

### **1. Onboarding de Empleados (6 pasos)**
- **Paso 1**: Nombre completo (documento identidad)
- **Paso 2**: Local asignado (ciudad + nombre)
- **Paso 3**: Número cuenta bancaria (Colombia/USA)
- **Paso 4**: Talla uniforme (XS/S/M/L/XL/XXL)
- **Paso 5**: Confirmación Manual Manipulación Alimentos + fecha
- **Paso 6**: Confirmación recorrido cocina + nombre supervisor

### **2. Gestión de Mesas en Tiempo Real**
- Consulta de mesas libres por local y capacidad
- Reservas automatizadas con validación
- Estimación de tiempo de liberación de mesas ocupadas
- Integración con sistema TypeScript existente del repo

### **3. Memoria Persistente (Sin Amnesia)**
- Estado sobrevive reinicios del agente
- Persistencia en disco con estructura `/memory/`
- Sistema QMD para búsqueda semántica
- Recuperación post-reinicio garantizada

### **4. Reportes para Ashley Turner (RRHH)**
- Reportes matutinos automáticos
- Detección empleados inactivos >48h
- Estadísticas de progreso onboarding
- Notificaciones automáticas cuando onboarding completado

## 🏗️ **Arquitectura**

### **Estructura de Memoria**
```
MEMORY.md (carga automática)
├── Reglas de negocio permanentes
├── Esquema de datos empleado
├── Configuración de 14 locales
├── Instrucciones reportes matutinos

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
├── auditoria.md (log eventos sistema)
└── estadisticas.md (métricas iniciales)
```

### **Tipos de Datos**
```typescript
interface EmpleadoOnboarding {
  id: string;
  nombre_completo: string;
  correo: string;
  local_asignado: string | null;
  talla_uniforme: "XS" | "S" | "M" | "L" | "XL" | "XXL" | null;
  cuenta_bancaria: string | null;
  manual_confirmado: boolean;
  manual_fecha: string | null;
  recorrido_confirmado: boolean;
  recorrido_supervisor: string | null;
  estado: "no_iniciado" | "activo" | "terminado";
  paso_actual: number;
  fecha_inicio: string;
  fecha_ultima_interaccion: string;
  fecha_cierre: string | null;
}
```

## 🚀 **Cómo usar**

### **Comandos disponibles**
```bash
npm install                    # Instalar dependencias
npm run typecheck              # Validar TypeScript
npm run agent:test             # Ejecutar demo simple
npm run agent:start            # Iniciar agente completo
npm run agent:memory-check     # Verificar integridad memoria
```

### **Ejemplo de uso**
```typescript
import { BrasalandAgent } from "./src/agent/brasaland-agent";

const agente = new BrasalandAgent();
await agente.inicializar();

// Onboarding
const resultado = await agente.iniciarOnboarding("correo@example.com", "Nombre");
const respuesta = await agente.procesarRespuestaEmpleado("EMP_001", "Medellín, El Poblado");

// Gestión mesas
const mesas = await agente.consultarMesasLibres("MED_ELP", 4);
const reserva = await agente.crearReserva({
  nombreCliente: "Juan Pérez",
  numeroComensales: 4,
  fechaHora: new Date().toISOString(),
  idMesa: "M11",
  local_id: "MED_ELP"
});

// Reportes
const reporte = await agente.generarReporteMatutino();
const stats = await agente.obtenerEstadisticas();
```

## 📊 **Reportes Matutinos**

**Para Ashley Turner (@ashley_brasaland):**
- Total empleados en onboarding (activos)
- Nuevos empleados últimos 24h
- Empleados completados últimos 24h
- Empleados inactivos >48h (con detalles)
- Progreso promedio (pasos completados)
- Problemas detectados (cuentas inválidas, etc.)
- Recomendaciones acción

## 🔧 **Integración con código existente**

### **Reutilización de tipos**
```typescript
// Del repositorio original Brasaland (Hito 2)
import { PlatoCarta, ReservaMesa } from "./types/models";
import { validateReservaMesa } from "./utils/validations";
import { reportSummaryByCategory } from "./utils/transformations";
```

### **Validaciones compartidas**
- `validateReservaMesa()` usado para reservas de clientes
- Tipos `PlatoCarta` para consultas de carta
- Funciones de reporte para estadísticas

## 🤖 **Personalidad del Agente**

**Gojo (Brasaland Edition):**
- Adaptable culturalmente
- Estratégicamente internacional
- Conectador de mundos
- Pragmático en negocios
- Curioso culturalmente
- Directo pero culturalmente consciente
- Enfocado en resultados medibles

## 📋 **Validaciones Implementadas**

### **Onboarding**
- Local asignado debe ser uno de los 14 locales válidos
- Talla uniforme debe ser XS/S/M/L/XL/XXL
- Manual confirmado con fecha válida (no futura)
- Supervisor nombre mínimo 3 caracteres
- Cuenta bancaria mínimo 5 caracteres (cualquier formato)

### **Reservas**
- Capacidad mesa compatible con número comensales
- Mesa disponible (no ocupada/reservada)
- Fecha/hora ISO válida
- Validación con `validateReservaMesa()` del repo original

## 💾 **Persistencia contra Amnesia**

**Cada transición de estado genera escritura en disco inmediata**
- Empleado responde pregunta → actualiza `/memory/empleados/[id].md`
- Cambio estado mesa → actualiza `/memory/mesas/[local].json`
- Evento importante → registra en `/memory/auditoria.md`

**Recuperación post-reinicio**
1. Al iniciar, agente busca empleados "activos"
2. Verifica que todos archivos .md sean legibles
3. Reconstruye índice QMD si necesario
4. Muestra cuántos empleados recuperó exitosamente

## 🧪 **Demo Simple**
```bash
npm run agent:test
```

La demo muestra:
1. Inicialización y recuperación post-reinicio
2. Onboarding completo de empleado
3. Consulta de mesas disponibles
4. Creación de reserva
5. Reporte matutino generado
6. Estadísticas del sistema
7. Validación de persistencia (simulación reinicio)

## 📁 **Estructura del Proyecto**

```
src/
├── agent/
│   └── brasaland-agent.ts          # Agente principal
├── types/
│   ├── models.ts                   # Tipos originales repo
│   └── onboarding.ts               # Tipos extendidos agente
├── utils/
│   ├── collections.ts              # Funciones originales repo
│   ├── search.ts                   # Funciones originales repo
│   ├── transformations.ts          # Funciones originales repo
│   ├── validations.ts              # Validaciones originales repo
│   ├── memory-persistence.ts       # Persistencia contra amnesia
│   └── onboarding-validations.ts   # Validaciones específicas onboarding
├── demo-agent-simple.ts            # Demo simplificada
├── demo.ts                         # Demo original repo
└── demo-browser.ts                 # Demo browser original repo

memory/                             # Memoria persistente
├── empleados/
├── locales/
├── mesas/
├── auditoria.md
├── estadisticas.md
└── index.json

MEMORY.md                           # Reglas de negocio permanentes
MEMORY-DECISION.md                  # Análisis estrategia memoria
```

## 🚨 **Restricciones y Consideraciones**

### **Restricciones**
- Agente inicia cada sesión con ventana de contexto limitada
- Persistencia debe ser real (escritura en disco en cada transición)
- Recuperación debe demostrarse tras reinicio
- No usar memoria del historial del chat (amnesia)

### **Configuración QMD**
- Método: QMD con similitud semántica
- Búsqueda por: palabras clave + similitud semántica
- Reranking: activado
- Umbral similitud: 0.7
- Resultados máximos: 20
- Campos indexados: todos campos empleado + fechas + estados

## 🏆 **Estado del Proyecto**

✅ **COMPLETADO:**
1. Workspace Brasaland configurado y activado
2. Rama `brasaland_agent` creada y commiteada
3. Agente principal implementado
4. Memoria persistente con QMD configurado
5. Demo funcional implementada
6. Integración con código TypeScript existente

🔧 **PRÓXIMOS PASOS (si necesario):**
1. Integración con Telegram API para Ashley Turner
2. Sistema de emails automáticos de bienvenida
3. Panel web para monitoreo de estado
4. Tests unitarios completos
5. Integración con APIs de delivery (Uber, Just Eat)

## 📞 **Contacto**

**Alfredo** - Propietario del proyecto
**Gojo (Brasaland Edition)** - Implementación del agente

---

**Commit:** `brasaland_agent` con implementación completa
**Fecha:** 2026-06-29
**Estado:** Ready for production