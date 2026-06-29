// src/utils/onboarding-validations.ts
// Validaciones específicas para el proceso de onboarding Brasaland

import { EmpleadoOnboarding, TallaUniforme, ValidacionOnboarding } from "../types/onboarding";

// ============================================================================
// LISTA DE LOCALES VÁLIDOS (14 LOCALES)
// ============================================================================

export const LOCALES_VALIDOS = [
  // Colombia
  "Bogotá, Chapinero",
  "Medellín, El Poblado", 
  "Cali, Granada",
  "Barranquilla, Norte",
  "Cartagena, Bocagrande",
  "Pereira, Centro",
  "Bucaramanga, Cabecera",
  // Florida, USA
  "Miami, South Beach",
  "Miami, Brickell",
  "Orlando, International Drive",
  "Tampa, Downtown",
  "Jacksonville, Riverside",
  "Fort Lauderdale, Las Olas",
  "Naples, Fifth Avenue",
];

// ============================================================================
// TALLAS DE UNIFORME VÁLIDAS
// ============================================================================

export const TALLAS_VALIDAS: TallaUniforme[] = ["XS", "S", "M", "L", "XL", "XXL"];

// ============================================================================
// VALIDACIONES POR CAMPO
// ============================================================================

export const VALIDACIONES_ONBOARDING: ValidacionOnboarding[] = [
  {
    campo: "nombre_completo",
    requerido: true,
    validacion: (valor: any) => {
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      const trimmed = valor.trim();
      if (trimmed.length < 3) return { valido: false, mensaje: "Mínimo 3 caracteres" };
      if (!trimmed.includes(" ")) return { valido: false, mensaje: "Debe incluir nombre y apellido" };
      return { valido: true };
    },
    formato_ejemplo: "Juan Pérez García",
  },
  {
    campo: "local_asignado",
    requerido: true,
    validacion: (valor: any) => {
      if (valor === null || valor === undefined) {
        return { valido: false, mensaje: "Local es obligatorio" };
      }
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      if (!LOCALES_VALIDOS.includes(valor.trim())) {
        return { 
          valido: false, 
          mensaje: `Local no válido. Opciones: ${LOCALES_VALIDOS.slice(0, 3).join(", ")}...` 
        };
      }
      return { valido: true };
    },
    formato_ejemplo: "Medellín, El Poblado",
  },
  {
    campo: "cuenta_bancaria",
    requerido: true,
    validacion: (valor: any) => {
      if (valor === null || valor === undefined) {
        return { valido: false, mensaje: "Cuenta bancaria es obligatoria" };
      }
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      const trimmed = valor.trim();
      if (trimmed.length < 5) return { valido: false, mensaje: "Mínimo 5 caracteres" };
      
      // Cualquier formato aceptado (Colombia o USA)
      return { valido: true };
    },
    formato_ejemplo: "ES12 3456 7890 1234 5678 o 1234567890",
  },
  {
    campo: "talla_uniforme",
    requerido: true,
    validacion: (valor: any) => {
      if (valor === null || valor === undefined) {
        return { valido: false, mensaje: "Talla es obligatoria" };
      }
      if (!TALLAS_VALIDAS.includes(valor)) {
        return { 
          valido: false, 
          mensaje: `Talla no válida. Opciones: ${TALLAS_VALIDAS.join(", ")}` 
        };
      }
      return { valido: true };
    },
    formato_ejemplo: "M",
  },
  {
    campo: "manual_confirmado",
    requerido: true,
    validacion: (valor: any) => {
      if (typeof valor !== "boolean") {
        return { valido: false, mensaje: "Debe confirmar si ha leído el manual" };
      }
      if (valor === false) {
        return { valido: false, mensaje: "Debe confirmar que ha leído el manual" };
      }
      return { valido: true };
    },
    formato_ejemplo: "true",
  },
  {
    campo: "manual_fecha",
    requerido: true,
    validacion: (valor: any) => {
      if (valor === null || valor === undefined) {
        return { valido: false, mensaje: "Fecha de lectura del manual es obligatoria" };
      }
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      
      // Validar formato fecha (YYYY-MM-DD)
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(valor)) {
        return { valido: false, mensaje: "Formato fecha inválido. Use YYYY-MM-DD" };
      }
      
      // Validar que sea fecha válida
      const date = new Date(`${valor}T00:00:00Z`);
      if (isNaN(date.getTime())) {
        return { valido: false, mensaje: "Fecha no válida" };
      }
      
      // Validar que no sea fecha futura
      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);
      if (date > hoy) {
        return { valido: false, mensaje: "Fecha no puede ser futura" };
      }
      
      return { valido: true };
    },
    formato_ejemplo: "2026-06-28",
  },
  {
    campo: "recorrido_confirmado",
    requerido: true,
    validacion: (valor: any) => {
      if (typeof valor !== "boolean") {
        return { valido: false, mensaje: "Debe confirmar si realizó el recorrido" };
      }
      if (valor === false) {
        return { valido: false, mensaje: "Debe confirmar que realizó el recorrido" };
      }
      return { valido: true };
    },
    formato_ejemplo: "true",
  },
  {
    campo: "recorrido_supervisor",
    requerido: true,
    validacion: (valor: any) => {
      if (valor === null || valor === undefined) {
        return { valido: false, mensaje: "Nombre del supervisor es obligatorio" };
      }
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      const trimmed = valor.trim();
      if (trimmed.length < 3) return { valido: false, mensaje: "Mínimo 3 caracteres" };
      return { valido: true };
    },
    formato_ejemplo: "Carlos Rodríguez",
  },
];

// ============================================================================
// FUNCIONES DE VALIDACIÓN COMPLETAS
// ============================================================================

export interface ResultadoValidacion {
  valido: boolean;
  errores: Array<{ campo: string; mensaje: string }>;
  camposFaltantes: string[];
  sugerencias: string[];
}

export function validarEmpleadoCompleto(empleado: Partial<EmpleadoOnboarding>): ResultadoValidacion {
  const errores: Array<{ campo: string; mensaje: string }> = [];
  const camposFaltantes: string[] = [];
  const sugerencias: string[] = [];

  // Validar cada campo según las reglas
  for (const validacion of VALIDACIONES_ONBOARDING) {
    const valor = empleado[validacion.campo as keyof EmpleadoOnboarding];
    
    if (validacion.requerido && (valor === null || valor === undefined || valor === "")) {
      camposFaltantes.push(validacion.campo);
      continue;
    }
    
    if (valor !== null && valor !== undefined && valor !== "") {
      const resultado = validacion.validacion(valor);
      if (!resultado.valido) {
        errores.push({
          campo: validacion.campo,
          mensaje: resultado.mensaje || `Valor inválido para ${validacion.campo}`,
        });
        
        // Añadir sugerencia con formato ejemplo
        sugerencias.push(`Para ${validacion.campo}: ${validacion.formato_ejemplo}`);
      }
    }
  }

  // Validaciones adicionales de lógica de negocio
  if (empleado.manual_confirmado && !empleado.manual_fecha) {
    errores.push({
      campo: "manual_fecha",
      mensaje: "Si confirmó el manual, debe proporcionar la fecha",
    });
  }

  if (empleado.recorrido_confirmado && !empleado.recorrido_supervisor) {
    errores.push({
      campo: "recorrido_supervisor",
      mensaje: "Si confirmó el recorrido, debe proporcionar el nombre del supervisor",
    });
  }

  // Validar que paso_actual esté entre 0 y 6
  if (empleado.paso_actual !== undefined) {
    if (empleado.paso_actual < 0 || empleado.paso_actual > 6) {
      errores.push({
        campo: "paso_actual",
        mensaje: "Paso actual debe estar entre 0 y 6",
      });
    }
  }

  return {
    valido: errores.length === 0 && camposFaltantes.length === 0,
    errores,
    camposFaltantes,
    sugerencias,
  };
}

export function validarPasoOnboarding(
  paso: number, 
  valor: any
): { valido: boolean; mensaje?: string; campo?: string } {
  
  switch (paso) {
    case 1: // Nombre completo
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      const nombreTrim = valor.trim();
      if (nombreTrim.length < 3) return { valido: false, mensaje: "Mínimo 3 caracteres" };
      if (!nombreTrim.includes(" ")) return { valido: false, mensaje: "Debe incluir nombre y apellido" };
      return { valido: true, campo: "nombre_completo" };
      
    case 2: // Local asignado
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      const localTrim = valor.trim();
      if (!LOCALES_VALIDOS.includes(localTrim)) {
        return { 
          valido: false, 
          mensaje: `Local no válido. Ejemplos: ${LOCALES_VALIDOS.slice(0, 2).join(", ")}` 
        };
      }
      return { valido: true, campo: "local_asignado" };
      
    case 3: // Cuenta bancaria
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe ser texto" };
      const cuentaTrim = valor.trim();
      if (cuentaTrim.length < 5) return { valido: false, mensaje: "Mínimo 5 caracteres" };
      return { valido: true, campo: "cuenta_bancaria" };
      
    case 4: // Talla uniforme
      if (!TALLAS_VALIDAS.includes(valor)) {
        return { 
          valido: false, 
          mensaje: `Talla no válida. Opciones: ${TALLAS_VALIDAS.join(", ")}` 
        };
      }
      return { valido: true, campo: "talla_uniforme" };
      
    case 5: // Confirmación manual + fecha
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe confirmar con texto" };
      const confirmacion = valor.toLowerCase();
      
      // Buscar patrón como "Leído el 2026-06-28" o "Sí, leído el 28/06"
      const fechaMatch = valor.match(/(\d{4}[-/]\d{2}[-/]\d{2})|(\d{2}[-/]\d{2}[-/]\d{4})/);
      const tieneConfirmacion = confirmacion.includes("sí") || confirmacion.includes("si") || 
                               confirmacion.includes("confirmo") || confirmacion.includes("leí");
      
      if (!tieneConfirmacion) {
        return { 
          valido: false, 
          mensaje: "Debe confirmar explícitamente que ha leído el manual (ej: 'Sí, leído el 2026-06-28')" 
        };
      }
      
      if (!fechaMatch) {
        return { 
          valido: false, 
          mensaje: "Debe incluir fecha de lectura (ej: 'Leído el 2026-06-28')" 
        };
      }
      
      // Extraer fecha del texto
      let fechaExtraida = fechaMatch[0];
      // Normalizar formato a YYYY-MM-DD si es DD/MM/YYYY
      if (fechaExtraida.includes("/")) {
        const parts = fechaExtraida.split("/");
        if (parts.length === 3) {
          if (parts[0].length === 2 && parts[2].length === 4) {
            fechaExtraida = `${parts[2]}-${parts[1]}-${parts[0]}`;
          } else if (parts[2].length === 2 && parts[0].length === 4) {
            fechaExtraida = `${parts[0]}-${parts[1]}-${parts[2]}`;
          }
        }
      }
      
      // Validar fecha
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(fechaExtraida)) {
        return { valido: false, mensaje: "Formato fecha inválido. Use YYYY-MM-DD" };
      }
      
      return { 
        valido: true, 
        campo: "manual_confirmado",
        mensaje: `Fecha detectada: ${fechaExtraida}. ¿Es correcta?` 
      };
      
    case 6: // Confirmación recorrido + supervisor
      if (typeof valor !== "string") return { valido: false, mensaje: "Debe confirmar con texto" };
      const recorridoConfirmacion = valor.toLowerCase();
      
      // Buscar nombre de supervisor (asumimos que después de "con" o "supervisor:")
      const nombreMatch = valor.match(/(?:con|supervisor:|supervisado por)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)/i);
      const tieneRecorrido = recorridoConfirmacion.includes("sí") || recorridoConfirmacion.includes("si") || 
                            recorridoConfirmacion.includes("realicé") || recorridoConfirmacion.includes("complete");
      
      if (!tieneRecorrido) {
        return { 
          valido: false, 
          mensaje: "Debe confirmar explícitamente que realizó el recorrido" 
        };
      }
      
      if (!nombreMatch) {
        return { 
          valido: false, 
          mensaje: "Debe incluir nombre del supervisor (ej: 'Sí, con Carlos Rodríguez')" 
        };
      }
      
      return { 
        valido: true, 
        campo: "recorrido_confirmado",
        mensaje: `Supervisor detectado: ${nombreMatch[1]}. ¿Es correcto?` 
      };
      
    default:
      return { valido: false, mensaje: "Paso no válido" };
  }
}

// ============================================================================
// HELPERS PARA PROCESAMIENTO DE RESPUESTAS
// ============================================================================

export function extraerFechaManual(texto: string): string | null {
  const fechaMatch = texto.match(/\d{4}[-/]\d{2}[-/]\d{2}/);
  if (fechaMatch) {
    let fecha = fechaMatch[0];
    // Normalizar a YYYY-MM-DD
    if (fecha.includes("/")) {
      const parts = fecha.split("/");
      if (parts.length === 3) {
        if (parts[0].length === 4) {
          fecha = `${parts[0]}-${parts[1]}-${parts[2]}`;
        } else if (parts[2].length === 4) {
          fecha = `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
      }
    }
    return fecha;
  }
  return null;
}

export function extraerNombreSupervisor(texto: string): string | null {
  const nombreMatch = texto.match(/(?:con|supervisor:|supervisado por)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)/i);
  return nombreMatch ? nombreMatch[1] : null;
}

export function generarIDEmpleado(): string {
  const timestamp = Date.now().toString().slice(-6);
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, "0");
  return `EMP_${timestamp}${random}`;
}

// ============================================================================
// VALIDACIÓN DE INACTIVIDAD
// ============================================================================

export function esEmpleadoInactivo(empleado: EmpleadoOnboarding, horasUmbral: number = 48): boolean {
  if (empleado.estado !== "activo") return false;
  
  const ultimaInteraccion = new Date(empleado.fecha_ultima_interaccion);
  const ahora = new Date();
  const horasPasadas = (ahora.getTime() - ultimaInteraccion.getTime()) / (1000 * 60 * 60);
  
  return horasPasadas > horasUmbral;
}

// ============================================================================
// GENERACIÓN DE PREGUNTAS POR PASO
// ============================================================================

export function obtenerPreguntaPaso(paso: number): string {
  switch (paso) {
    case 1:
      return "¿Cuál es tu nombre completo tal como aparece en tu documento de identidad?";
    case 2:
      return "¿A qué local has sido asignado/a? (ciudad y nombre del local, ej: 'Medellín, El Poblado')";
    case 3:
      return "¿Cuál es tu número de cuenta bancaria para el pago de nómina? (cualquier formato Colombia/USA)";
    case 4:
      return "¿Cuál es tu talla de uniforme? (XS / S / M / L / XL / XXL)";
    case 5:
      return "Confirma que has leído el Manual de Manipulación de Alimentos e indica la fecha en que lo completaste. (ej: 'Sí, leído el 2026-06-28')";
    case 6:
      return "Confirma que has realizado el recorrido de cocina con tu supervisor e indica su nombre. (ej: 'Sí, con Carlos Rodríguez')";
    default:
      return "Proceso completado. ¡Bienvenido/a a Brasaland!";
  }
}

export function obtenerResumenProgreso(pasoActual: number): string {
  const porcentaje = Math.round((pasoActual / 6) * 100);
  return `Progreso: ${pasoActual}/6 pasos completados (${porcentaje}%)`;
}