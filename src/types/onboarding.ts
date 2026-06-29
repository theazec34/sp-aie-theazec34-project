// src/types/onboarding.ts
// Tipos extendidos para el Agente de Onboarding Brasaland

import { ReservaMesa, PlatoCarta } from "./models";

// ============================================================================
// ONBOARDING DE EMPLEADOS
// ============================================================================

export type TallaUniforme = "XS" | "S" | "M" | "L" | "XL" | "XXL";
export type EmpleadoEstado = "no_iniciado" | "activo" | "terminado";

export interface EmpleadoOnboarding {
  // Identificación
  id: string;  // Formato: EMP_001, EMP_002, etc.
  nombre_completo: string;
  correo: string;
  
  // Onboarding (6 pasos según contexto)
  local_asignado: string | null;  // "Ciudad, NombreLocal"
  talla_uniforme: TallaUniforme | null;
  cuenta_bancaria: string | null;
  manual_confirmado: boolean;
  manual_fecha: string | null;  // ISO date
  recorrido_confirmado: boolean;
  recorrido_supervisor: string | null;
  
  // Estado del proceso
  estado: EmpleadoEstado;
  paso_actual: number;  // 1-6 (0 si no_iniciado)
  
  // Temporales
  fecha_inicio: string;  // ISO datetime
  fecha_ultima_interaccion: string;  // ISO datetime
  fecha_cierre: string | null;  // ISO datetime
  
  // Métricas
  recordatorios_enviados: number;
  intentos_fallidos: number;
}

// ============================================================================
// GESTIÓN DE MESAS Y RESERVAS
// ============================================================================

export type MesaEstado = "libre" | "ocupada" | "reservada";

export interface MesaRestaurante {
  id: string;  // Formato: M01, M02, etc.
  local_id: string;  // Referencia a local (ej: "MED_ELP")
  capacidad: number;  // 2, 4, 6, 8 personas
  estado: MesaEstado;
  hora_ocupacion: string | null;  // ISO datetime
  tiempo_promedio_min: number;  // minutos estimados
  estimacion_liberacion: string | null;  // ISO datetime
  
  // Información de reserva (si aplica)
  reserva_id?: string;
  reserva_hora?: string;
  cliente_nombre?: string;
}

export interface ReservaCliente extends ReservaMesa {
  // Extendemos ReservaMesa existente
  local_id: string;
  contacto_telefono?: string;
  notas?: string;
}

// ============================================================================
// LOCALES BRASALAND
// ============================================================================

export interface LocalBrasaland {
  id: string;  // Formato: MED_ELP, MIA_SB
  nombre: string;
  ciudad: string;
  pais: "Colombia" | "USA";
  direccion: string;
  telefono: string;
  gerente: string;
  
  // Configuración
  total_mesas: number;
  capacidad_maxima: number;
  config_mesas: {
    capacidad_2: number;
    capacidad_4: number;
    capacidad_6: number;
    capacidad_8: number;
  };
  
  // Horarios
  horarios: {
    lunes_jueves: string;
    viernes_sabado: string;
    domingo: string;
  };
  
  // Personal
  personal: {
    gerente: number;
    subgerente: number;
    chef_principal: number;
    chefs: number;
    meseros: number;
    cocina: number;
    limpieza: number;
  };
}

// ============================================================================
// ESTADÍSTICAS Y REPORTES
// ============================================================================

export interface EstadisticasOnboarding {
  total_empleados: number;
  empleados_activos: number;
  empleados_terminados: number;
  empleados_no_iniciados: number;
  
  pasos_promedio_completados: number;
  tiempo_promedio_completado_min: number | null;
  tasa_completacion: number;
  
  distribucion_por_local: Record<string, number>;
  distribucion_por_talla: Record<TallaUniforme, number>;
}

export interface ReporteMatutino {
  fecha: string;
  total_empleados_activos: number;
  nuevos_ultimas_24h: number;
  completados_ultimas_24h: number;
  
  empleados_inactivos_48h: Array<{
    id: string;
    nombre: string;
    local: string;
    ultima_interaccion: string;
    paso_actual: number;
  }>;
  
  problemas_detectados: Array<{
    tipo: "cuenta_invalida" | "local_inexistente" | "fecha_invalida";
    empleado_id: string;
    descripcion: string;
  }>;
  
  recomendaciones: string[];
}

// ============================================================================
// EVENTOS DE AUDITORÍA
// ============================================================================

export type TipoEvento =
  | "SISTEMA_INICIO"
  | "EMPLEADO_CREADO"
  | "EMPLEADO_ACTUALIZADO"
  | "EMPLEADO_TERMINADO"
  | "RESERVA_CREADA"
  | "RESERVA_CANCELADA"
  | "MESA_OCUPADA"
  | "MESA_LIBERADA"
  | "ERROR_VALIDACION"
  | "REPORTE_GENERADO"
  | "BACKUP_COMPLETADO";

export interface EventoAuditoria {
  timestamp: string;
  tipo: TipoEvento;
  usuario?: string;  // "system", "ashley", "empleado_id", "cliente"
  detalles: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// RESPUESTAS DEL AGENTE
// ============================================================================

export interface RespuestaAgente {
  success: boolean;
  mensaje: string;
  data?: any;
  errores?: Array<{ campo: string; mensaje: string }>;
  sugerencias?: string[];
  
  // Para flujos de conversación
  siguiente_paso?: number;
  preguntas_pendientes?: string[];
  estado_actual?: string;
}

// ============================================================================
// BÚSQUEDA QMD
// ============================================================================

export interface QueryQMD {
  texto: string;
  filtros?: {
    local?: string;
    estado?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
    campo_vacio?: string;
  };
  limite?: number;
  umbral_similitud?: number;
}

export interface ResultadoQMD<T> {
  resultados: T[];
  total: number;
  tiempo_ms: number;
  query: QueryQMD;
  sugerencias?: string[];
}

// ============================================================================
// VALIDACIONES ESPECÍFICAS ONBOARDING
// ============================================================================

export interface ValidacionOnboarding {
  campo: keyof EmpleadoOnboarding;
  requerido: boolean;
  validacion: (valor: any) => { valido: boolean; mensaje?: string };
  formato_ejemplo: string;
}