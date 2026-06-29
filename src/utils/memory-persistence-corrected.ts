// src/utils/memory-persistence-corrected.ts
// Versión corregida de utilidades de persistencia

import { EmpleadoOnboarding, EventoAuditoria, LocalBrasaland, MesaRestaurante, TallaUniforme } from "../types/onboarding";
import * as fs from "fs/promises";
import * as path from "path";

// ============================================================================
// CONFIGURACIÓN DE PATHS
// ============================================================================

const MEMORY_ROOT = path.join(process.cwd(), "memory");
const PATHS = {
  empleados: path.join(MEMORY_ROOT, "empleados"),
  locales: path.join(MEMORY_ROOT, "locales"),
  mesas: path.join(MEMORY_ROOT, "mesas"),
  auditoria: path.join(MEMORY_ROOT, "auditoria.md"),
  estadisticas: path.join(MEMORY_ROOT, "estadisticas.md"),
  indexEmpleados: path.join(MEMORY_ROOT, "empleados", "index.json"),
};

// ============================================================================
// INTERFACES DE ÍNDICE
// ============================================================================

interface IndexEmpleados {
  version: string;
  fecha_creacion: string;
  total_empleados: number;
  empleados_activos: number;
  empleados_terminados: number;
  empleados_no_iniciados: number;
  ultima_actualizacion: string;
  lista_empleados: Array<{
    id: string;
    nombre: string;
    estado: string;
    local: string | null;
    ultima_interaccion: string;
  }>;
}

interface EstadoMesasLocal {
  local_id: string;
  nombre: string;
  total_mesas: number;
  mesas_libres: number;
  mesas_ocupadas: number;
  mesas_reservadas: number;
  ultima_actualizacion: string;
  detalle_mesas: MesaRestaurante[];
}

// ============================================================================
// HELPERS DE ARCHIVOS
// ============================================================================

async function ensureDirectory(dirPath: string): Promise<void> {
  try {
    await fs.access(dirPath);
  } catch {
    await fs.mkdir(dirPath, { recursive: true });
  }
}

async function readJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    const content = await fs.readFile(filePath, "utf-8");
    return JSON.parse(content) as T;
  } catch (error) {
    console.warn(`No se pudo leer archivo JSON ${filePath}:`, error);
    return null;
  }
}

async function writeJsonFile<T>(filePath: string, data: T): Promise<void> {
  const content = JSON.stringify(data, null, 2);
  await fs.writeFile(filePath, content, "utf-8");
}

async function appendToFile(filePath: string, content: string): Promise<void> {
  await fs.appendFile(filePath, content + "\n", "utf-8");
}

// ============================================================================
// PERSISTENCIA DE EMPLEADOS
// ============================================================================

export async function guardarEmpleado(empleado: EmpleadoOnboarding): Promise<void> {
  await ensureDirectory(PATHS.empleados);
  
  // 1. Guardar archivo individual del empleado
  const empleadoPath = path.join(PATHS.empleados, `${empleado.id}.md`);
  const contenido = `---
id: ${empleado.id}
nombre_completo: "${empleado.nombre_completo}"
correo: "${empleado.correo}"
local_asignado: ${empleado.local_asignado ? `"${empleado.local_asignado}"` : "null"}
talla_uniforme: ${empleado.talla_uniforme ? `"${empleado.talla_uniforme}"` : "null"}
cuenta_bancaria: ${empleado.cuenta_bancaria ? `"${empleado.cuenta_bancaria}"` : "null"}
manual_confirmado: ${empleado.manual_confirmado}
manual_fecha: ${empleado.manual_fecha ? `"${empleado.manual_fecha}"` : "null"}
recorrido_confirmado: ${empleado.recorrido_confirmado}
recorrido_supervisor: ${empleado.recorrido_supervisor ? `"${empleado.recorrido_supervisor}"` : "null"}
estado: "${empleado.estado}"
paso_actual: ${empleado.paso_actual}
fecha_inicio: "${empleado.fecha_inicio}"
fecha_ultima_interaccion: "${empleado.fecha_ultima_interaccion}"
fecha_cierre: ${empleado.fecha_cierre ? `"${empleado.fecha_cierre}"` : "null"}
recordatorios_enviados: ${empleado.recordatorios_enviados}
intentos_fallidos: ${empleado.intentos_fallidos}
---
# Historial de eventos (append-only)
${new Date().toISOString()} | CREACIÓN | Inicio proceso onboarding
`;

  await fs.writeFile(empleadoPath, contenido, "utf-8");
  
  // 2. Actualizar índice
  await actualizarIndiceEmpleados(empleado);
  
  // 3. Registrar evento en auditoría
  await registrarEvento({
    timestamp: new Date().toISOString(),
    tipo: "EMPLEADO_CREADO",
    usuario: "system",
    detalles: `Empleado ${empleado.nombre_completo} creado con ID ${empleado.id}`,
    metadata: { empleado_id: empleado.id, estado: empleado.estado },
  });
  
  console.log(`✅ Empleado ${empleado.id} persistido en memoria`);
}

export async function actualizarEmpleado(empleado: EmpleadoOnboarding): Promise<void> {
  const empleadoPath = path.join(PATHS.empleados, `${empleado.id}.md`);
  
  try {
    // Leer contenido existente
    const contenido = await fs.readFile(empleadoPath, "utf-8");
    
    // Extraer YAML frontmatter
    const lines = contenido.split("\n");
    const yamlStart = lines.indexOf("---");
    const yamlEnd = lines.indexOf("---", yamlStart + 1);
    
    if (yamlStart === -1 || yamlEnd === -1) {
      throw new Error("Formato de archivo de empleado inválido");
    }
    
    // Reconstruir con datos actualizados
    const nuevoYaml = `---
id: ${empleado.id}
nombre_completo: "${empleado.nombre_completo}"
correo: "${empleado.correo}"
local_asignado: ${empleado.local_asignado ? `"${empleado.local_asignado}"` : "null"}
talla_uniforme: ${empleado.talla_uniforme ? `"${empleado.talla_uniforme}"` : "null"}
cuenta_bancaria: ${empleado.cuenta_bancaria ? `"${empleado.cuenta_bancaria}"` : "null"}
manual_confirmado: ${empleado.manual_confirmado}
manual_fecha: ${empleado.manual_fecha ? `"${empleado.manual_fecha}"` : "null"}
recorrido_confirmado: ${empleado.recorrido_confirmado}
recorrido_supervisor: ${empleado.recorrido_supervisor ? `"${empleado.recorrido_supervisor}"` : "null"}
estado: "${empleado.estado}"
paso_actual: ${empleado.paso_actual}
fecha_inicio: "${empleado.fecha_inicio}"
fecha_ultima_interaccion: "${empleado.fecha_ultima_interaccion}"
fecha_cierre: ${empleado.fecha_cierre ? `"${empleado.fecha_cierre}"` : "null"}
recordatorios_enviados: ${empleado.recordatorios_enviados}
intentos_fallidos: ${empleado.intentos_fallidos}
---`;
    
    const historial = lines.slice(yamlEnd + 1).join("\n");
    const nuevoContenido = nuevoYaml + "\n" + historial;
    
    await fs.writeFile(empleadoPath, nuevoContenido, "utf-8");
    
    // Actualizar índice
    await actualizarIndiceEmpleados(empleado);
    
    // Registrar evento
    await registrarEvento({
      timestamp: new Date().toISOString(),
      tipo: "EMPLEADO_ACTUALIZADO",
      usuario: "system",
      detalles: `Empleado ${empleado.nombre_completo} actualizado (paso ${empleado.paso_actual})`,
      metadata: { empleado_id: empleado.id, paso_actual: empleado.paso_actual },
    });
    
    console.log(`✅ Empleado ${empleado.id} actualizado en memoria`);
  } catch (error) {
    console.error(`❌ Error actualizando empleado ${empleado.id}:`, error);
    throw error;
  }
}

async function actualizarIndiceEmpleados(empleado: EmpleadoOnboarding): Promise<void> {
  const index = await readJsonFile<IndexEmpleados>(PATHS.indexEmpleados) || {
    version: "1.0.0",
    fecha_creacion: new Date().toISOString(),
    total_empleados: 0,
    empleados_activos: 0,
    empleados_terminados: 0,
    empleados_no_iniciados: 0,
    ultima_actualizacion: new Date().toISOString(),
    lista_empleados: [],
  };
  
  // Buscar si el empleado ya está en el índice
  const empleadoIndex = index.lista_empleados.findIndex(e => e.id === empleado.id);
  
  if (empleadoIndex === -1) {
    // Nuevo empleado
    index.lista_empleados.push({
      id: empleado.id,
      nombre: empleado.nombre_completo,
      estado: empleado.estado,
      local: empleado.local_asignado,
      ultima_interaccion: empleado.fecha_ultima_interaccion,
    });
    index.total_empleados++;
  } else {
    // Actualizar existente
    index.lista_empleados[empleadoIndex] = {
      id: empleado.id,
      nombre: empleado.nombre_completo,
      estado: empleado.estado,
      local: empleado.local_asignado,
      ultima_interaccion: empleado.fecha_ultima_interaccion,
    };
  }
  
  // Recalcular contadores
  index.empleados_activos = index.lista_empleados.filter(e => e.estado === "activo").length;
  index.empleados_terminados = index.lista_empleados.filter(e => e.estado === "terminado").length;
  index.empleados_no_iniciados = index.lista_empleados.filter(e => e.estado === "no_iniciado").length;
  index.ultima_actualizacion = new Date().toISOString();
  
  await writeJsonFile(PATHS.indexEmpleados, index);
}

// ============================================================================
// LECTURA DE EMPLEADOS
// ============================================================================

export async function leerEmpleado(id: string): Promise<EmpleadoOnboarding | null> {
  try {
    const empleadoPath = path.join(PATHS.empleados, `${id}.md`);
    const contenido = await fs.readFile(empleadoPath, "utf-8");
    
    // Parsear YAML frontmatter
    const lines = contenido.split("\n");
    const yamlStart = lines.indexOf("---");
    const yamlEnd = lines.indexOf("---", yamlStart + 1);
    
    if (yamlStart === -1 || yamlEnd === -1) {
      throw new Error("Formato de archivo inválido");
    }
    
    const yamlLines = lines.slice(yamlStart + 1, yamlEnd);
    const empleado: Partial<EmpleadoOnboarding> = { id };
    
    for (const line of yamlLines) {
      const match = line.match(/^(\w+):\s*(.+)$/);
      if (match) {
        const [, key, value] = match;
        
        switch (key) {
          case "nombre_completo":
          case "correo":
          case "local_asignado":
          case "cuenta_bancaria":
          case "manual_fecha":
          case "recorrido_supervisor":
          case "fecha_inicio":
          case "fecha_ultima_interaccion":
          case "fecha_cierre":
            empleado[key] = value === "null" ? null : value.replace(/^"|"$/g, "");
            break;
            
          case "talla_uniforme":
            empleado[key] = value === "null" ? null : value.replace(/^"|"$/g, "") as TallaUniforme;
            break;
            
          case "manual_confirmado":
          case "recorrido_confirmado":
            empleado[key] = value === "true";
            break;
            
          case "estado":
            empleado[key] = value.replace(/^"|"$/g, "") as any;
            break;
            
          case "paso_actual":
          case "recordatorios_enviados":
          case "intentos_fallidos":
            empleado[key] = parseInt(value, 10);
            break;
        }
      }
    }
    
    return empleado as EmpleadoOnboarding;
  } catch (error) {
    console.warn(`No se pudo leer empleado ${id}:`, error);
    return null;
  }
}

export async function listarEmpleadosPorEstado(estado?: string): Promise<EmpleadoOnboarding[]> {
  const index = await readJsonFile<IndexEmpleados>(PATHS.indexEmpleados);
  if (!index) return [];
  
  const empleados: EmpleadoOnboarding[] = [];
  
  for (const empIndex of index.lista_empleados) {
    if (!estado || empIndex.estado === estado) {
      const empleado = await leerEmpleado(empIndex.id);
      if (empleado) empleados.push(empleado);
    }
  }
  
  return empleados;
}

// ============================================================================
// GESTIÓN DE MESAS
// ============================================================================

export async function guardarEstadoMesas(
  localId: string, 
  estado: EstadoMesasLocal
): Promise<void> {
  await ensureDirectory(PATHS.mesas);
  
  const filePath = path.join(PATHS.mesas, `${localId}_mesas.json`);
  await writeJsonFile(filePath, estado);
  
  await registrarEvento({
    timestamp: new Date().toISOString(),
    tipo: "MESA_OCUPADA",
    usuario: "system",
    detalles: `Estado mesas actualizado para local ${localId}`,
    metadata: { 
      local_id: localId, 
      mesas_libres: estado.mesas_libres,
      mesas_ocupadas: estado.mesas_ocupadas,
    },
  });
}

export async function leerEstadoMesas(localId: string): Promise<EstadoMesasLocal | null> {
  const filePath = path.join(PATHS.mesas, `${localId}_mesas.json`);
  return await readJsonFile<EstadoMesasLocal>(filePath);
}

// ============================================================================
// AUDITORÍA
// ============================================================================

export async function registrarEvento(evento: EventoAuditoria): Promise<void> {
  const linea = `${evento.timestamp} | ${evento.tipo} | ${evento.detalles}`;
  await appendToFile(PATHS.auditoria, linea);
}

// ============================================================================
// RECUPERACIÓN POST-REINICIO
// ============================================================================

export async function recuperarEstadoPostReinicio(): Promise<{
  empleadosActivos: EmpleadoOnboarding[];
  totalEmpleados: number;
  mesasPorLocal: Record<string, EstadoMesasLocal>;
}> {
  console.log("🔄 Recuperando estado post-reinicio...");
  
  // 1. Leer índice de empleados
  const index = await readJsonFile<IndexEmpleados>(PATHS.indexEmpleados);
  const empleadosActivos: EmpleadoOnboarding[] = [];
  
  if (index) {
    console.log(`📊 Índice encontrado: ${index.total_empleados} empleados totales`);
    
    // Recuperar empleados activos
    for (const empIndex of index.lista_empleados.filter(e => e.estado === "activo")) {
      const empleado = await leerEmpleado(empIndex.id);
      if (empleado) empleadosActivos.push(empleado);
    }
  }
  
  // 2. Leer estado de mesas por local
  const mesasPorLocal: Record<string, EstadoMesasLocal> = {};
  
  try {
    const files = await fs.readdir(PATHS.mesas);
    for (const file of files.filter(f => f.endsWith("_mesas.json"))) {
      const localId = file.replace("_mesas.json", "");
      const estado = await leerEstadoMesas(localId);
      if (estado) mesasPorLocal[localId] = estado;
    }
  } catch (error) {
    console.warn("No se pudieron leer archivos de mesas:", error);
  }
  
  // 3. Registrar evento de recuperación
  await registrarEvento({
    timestamp: new Date().toISOString(),
    tipo: "SISTEMA_INICIO",
    usuario: "system",
    detalles: `Recuperación post-reinicio: ${empleadosActivos.length} empleados activos, ${Object.keys(mesasPorLocal).length} locales con mesas`,
    metadata: {
      empleados_activos: empleadosActivos.length,
      locales_con_mesas: Object.keys(mesasPorLocal).length,
    },
  });
  
  console.log(`✅ Recuperación completada: ${empleadosActivos.length} empleados activos`);
  
  return {
    empleadosActivos,
    totalEmpleados: index?.total_empleados || 0,
    mesasPorLocal,
  };
}

// ============================================================================
// VALIDACIÓN DE INTEGRIDAD
// ============================================================================

export async function validarIntegridadMemoria(): Promise<{
  valido: boolean;
  errores: string[];
  estadisticas: {
    total_empleados: number;
    archivos_empleados: number;
    archivos_mesas: number;
    auditoria_lineas: number;
  };
}> {
  const errores: string[] = [];
  const estadisticas = {
    total_empleados: 0,
    archivos_empleados: 0,
    archivos_mesas: 0,
    auditoria_lineas: 0,
  };
  
  try {
    // Verificar índice de empleados
    const index = await readJsonFile<IndexEmpleados>(PATHS.indexEmpleados);
    if (!index) {
      errores.push("Índice de empleados no encontrado");
    } else {
      estadisticas.total_empleados = index.total_empleados;
      
      // Verificar que cada empleado en el índice tenga archivo
      for (const emp of index.lista_empleados) {
        try {
          const empleadoPath = path.join(PATHS.empleados, `${emp.id}.md`);
          await fs.access(empleadoPath);
          estadisticas.archivos_empleados++;
        } catch {
          errores.push(`Archivo no encontrado para empleado ${emp.id}`);
        }
      }
    }
    
    // Contar archivos de mesas
    try {
      const mesaFiles = await fs.readdir(PATHS.mesas);
      estadisticas.archivos_mesas = mesaFiles.filter(f => f.endsWith(".json")).length;
    } catch {
      // No es error si no hay archivos de mesas aún
    }
    
    // Contar líneas de auditoría
    try {
      const auditoriaContent = await fs.readFile(PATHS.auditoria, "utf-8");
      estadisticas.auditoria_lineas = auditoriaContent.split("\n").filter(line => line.trim()).length;
    } catch {
      errores.push("Archivo de auditoría no encontrado");
    }
    
  } catch (error) {
    errores.push(`Error general validando integridad: ${error}`);
  }
  
  return {
    valido: errores.length === 0,
    errores,
    estadisticas,
  };
}