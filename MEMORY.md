# BRASALAND ONBOARDING AGENT - MEMORY STRUCTURE

## Configuración de Memoria Persistente
**Fecha creación**: 2026-06-29
**Agente**: Gojo (Brasaland Edition)
**Versión**: 1.0.0

---

## 1. REGLAS DE NEGOCIO PERMANENTES

### 1.1 Proceso de Onboarding (6 pasos)
1. **Nombre completo** (texto libre, documento identidad)
2. **Local asignado** (ciudad + nombre local, ej: "Medellín, El Poblado")
3. **Número cuenta bancaria** (cualquier formato Colombia/USA)
4. **Talla uniforme** (XS / S / M / L / XL / XXL)
5. **Manual Manipulación Alimentos** (confirmación + fecha)
6. **Recorrido cocina** (confirmación + nombre supervisor)

### 1.2 Estados del Empleado
- `no_iniciado`: Recién contactado, no ha respondido nada
- `activo`: En proceso, ha respondido al menos 1 pregunta
- `terminado`: Completó las 6 preguntas, proceso finalizado

### 1.3 Reglas Temporales
- **Umbral inactividad**: 48 horas sin interacción → alerta a Ashley
- **Reporte matutino**: Diario a las 08:00 (hora Miami)
- **Persistencia**: Escritura inmediata tras cada cambio de estado

---

## 2. LOCALES BRASALAND (14 LOCALES)

### Colombia
1. **Bogotá, Chapinero**
   - Dirección: Carrera 7 #45-23
   - Mesas totales: 30
   - Capacidad máxima: 120 personas

2. **Medellín, El Poblado**
   - Dirección: Calle 10 #43-28
   - Mesas totales: 25
   - Capacidad máxima: 100 personas

3. **Cali, Granada**
   - Dirección: Avenida 4N #10-45
   - Mesas totales: 20
   - Capacidad máxima: 80 personas

4. **Barranquilla, Norte**
   - Dirección: Carrera 52 #84-120
   - Mesas totales: 22
   - Capacidad máxima: 88 personas

5. **Cartagena, Bocagrande**
   - Dirección: Avenida San Martín #8-45
   - Mesas totales: 18
   - Capacidad máxima: 72 personas

6. **Pereira, Centro**
   - Dirección: Calle 19 #7-32
   - Mesas totales: 15
   - Capacidad máxima: 60 personas

7. **Bucaramanga, Cabecera**
   - Dirección: Calle 35 #25-67
   - Mesas totales: 16
   - Capacidad máxima: 64 personas

### Florida, USA
8. **Miami, South Beach**
   - Dirección: Ocean Drive #123
   - Mesas totales: 35
   - Capacidad máxima: 140 personas

9. **Miami, Brickell**
   - Dirección: Brickell Ave #456
   - Mesas totales: 28
   - Capacidad máxima: 112 personas

10. **Orlando, International Drive**
    - Dirección: I-Drive #789
    - Mesas totales: 32
    - Capacidad máxima: 128 personas

11. **Tampa, Downtown**
    - Dirección: Kennedy Blvd #101
    - Mesas totales: 24
    - Capacidad máxima: 96 personas

12. **Jacksonville, Riverside**
    - Dirección: Park Street #202
    - Mesas totales: 20
    - Capacidad máxima: 80 personas

13. **Fort Lauderdale, Las Olas**
    - Dirección: Las Olas Blvd #303
    - Mesas totales: 26
    - Capacidad máxima: 104 personas

14. **Naples, Fifth Avenue**
    - Dirección: 5th Ave South #404
    - Mesas totales: 22
    - Capacidad máxima: 88 personas

---

## 3. ESQUEMA DE DATOS EMPLEADO (TypeScript)

```typescript
interface EmpleadoOnboarding {
  // Identificación
  id: string;  // Formato: EMP_001, EMP_002, etc.
  nombre_completo: string;
  correo: string;
  
  // Onboarding (6 pasos)
  local_asignado: string | null;  // "Ciudad, NombreLocal"
  talla_uniforme: "XS" | "S" | "M" | "L" | "XL" | "XXL" | null;
  cuenta_bancaria: string | null;
  manual_confirmado: boolean;
  manual_fecha: string | null;  // ISO date
  recorrido_confirmado: boolean;
  recorrido_supervisor: string | null;
  
  // Estado del proceso
  estado: "no_iniciado" | "activo" | "terminado";
  paso_actual: number;  // 1-6 (0 si no_iniciado)
  
  // Temporales
  fecha_inicio: string;  // ISO datetime
  fecha_ultima_interaccion: string;  // ISO datetime
  fecha_cierre: string | null;  // ISO datetime
  
  // Métricas
  recordatorios_enviados: number;
  intentos_fallidos: number;
}

interface MesaRestaurante {
  id: string;  // Formato: M01, M02, etc.
  local_id: string;  // Referencia a local
  capacidad: number;  // 2, 4, 6, 8 personas
  estado: "libre" | "ocupada" | "reservada";
  hora_ocupacion: string | null;  // ISO datetime
  tiempo_promedio_min: number;  // minutos estimados
  estimacion_liberacion: string | null;  // ISO datetime
}

interface ReservaCliente {
  id: string;  // Formato: RES_001
  nombre_cliente: string;
  local_id: string;
  numero_comensales: number;
  fecha_hora: string;  // ISO datetime
  mesa_id: string;
  estado: "pendiente" | "confirmada" | "cancelada" | "completada";
}
```

---

## 4. CONFIGURACIÓN QMD (QUERY MEMORY DATABASE)

### Parámetros de búsqueda
- **Método**: QMD con similitud semántica
- **Umbral similitud**: 0.7
- **Resultados máximos**: 20
- **Reranking**: Activado
- **Campos indexados**: Todos campos texto de empleados

### Consultas predefinidas
1. `empleados inactivos >48h`: Filtro temporal + estado="activo"
2. `empleados de [ciudad]`: Filtro geográfico en local_asignado
3. `empleados sin [campo]`: Búsqueda campos null/empty
4. `mesas libres [local]`: Estado="libre" + local_id

---

## 5. TEMPLATE EMAIL BIENVENIDA

```plaintext
Asunto: Welcome to Brasaland — next steps to complete your onboarding

Hi [nombre],

We're glad to have you joining the Brasaland team. Before your first day, we need to complete a few steps to get you set up.

Please message our onboarding bot on Telegram to continue the process. You'll find it at [@brasaland_onboarding_bot].

Once you make contact, the bot will guide you through everything you need to do.

See you soon,
Brasaland People Team
```

**Nota**: Versión español disponible para locales colombianos si se implementa soporte bilingüe.

---

## 6. INSTRUCCIONES REPORTE MATUTINO

### Frecuencia: Diario 08:00 (hora Miami)
### Destinatario: Ashley Turner (@ashley_brasaland)

**Contenido mínimo:**
1. Total empleados en onboarding (activos)
2. Nuevos empleados últimos 24h
3. Empleados completados últimos 24h
4. Empleados inactivos >48h (con detalles)
5. Progreso promedio (pasos completados)
6. Problemas detectados (cuentas inválidas, etc.)
7. Recomendaciones acción

---

## 7. INTEGRACIÓN CON CARTA EXISTENTE

### Tipos reutilizados del repo TypeScript
```typescript
// De src/types/models.ts
type PlatoCartaCategoria = "entrada" | "principal" | "postre" | "bebida";
interface PlatoCarta {
  id: string;
  nombre: string;
  categoria: PlatoCartaCategoria;
  precio: number;
  alergenos: string[];
  activoEnCarta: boolean;
}

// Para reservas de clientes (extensión)
interface ReservaMesa {
  id: string;
  nombreCliente: string;
  numeroComensales: number;
  fechaHora: string;
  idMesa: string;
  estado: "pendiente" | "confirmada" | "cancelada" | "completada";
}
```

### Validaciones reutilizadas
- `validateReservaMesa()`: Para reservas de clientes
- `validatePlatoCarta()`: Para consultas de carta
- `reportSummaryByCategory()`: Para estadísticas

---

## 8. PROCEDIMIENTOS DE EMERGENCIA

### Recuperación post-reinicio
1. **Al iniciar**: Buscar empleados "activos" en `/memory/empleados/`
2. **Verificar integridad**: Chequear que todos archivos .md sean legibles
3. **Reconstruir índice QMD**: Si hay inconsistencias
4. **Generar reporte**: Mostrar estado recuperación

### Pérdida de datos
1. **Backup automático**: Cada cambio importante
2. **Log auditoría**: `/memory/auditoria.md` con timestamps
3. **Recuperación manual**: Desde último backup conocido

---

**Última actualización**: 2026-06-29T18:45:00Z  
**Próxima revisión**: 2026-07-06  
**Responsable**: Gojo (Brasaland Agent)