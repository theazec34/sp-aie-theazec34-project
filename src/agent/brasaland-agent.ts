// src/agent/brasaland-agent.ts - VERSIÓN CORREGIDA
// Agente principal Brasaland - Onboarding + Gestión de Mesas

import { 
  EmpleadoOnboarding, 
  RespuestaAgente,
  MesaRestaurante,
  ReservaCliente,
  TallaUniforme
} from "../types/onboarding";
import {
  guardarEmpleado,
  actualizarEmpleado,
  leerEmpleado,
  listarEmpleadosPorEstado,
  guardarEstadoMesas,
  leerEstadoMesas,
  registrarEvento,
  recuperarEstadoPostReinicio,
  validarIntegridadMemoria
} from "../utils/memory-persistence";
import {
  validarPasoOnboarding,
  obtenerPreguntaPaso,
  obtenerResumenProgreso,
  extraerFechaManual,
  extraerNombreSupervisor,
  generarIDEmpleado,
  esEmpleadoInactivo,
  validarEmpleadoCompleto
} from "../utils/onboarding-validations";
import { validateReservaMesa } from "../utils/validations";

// ============================================================================
// CLASE PRINCIPAL DEL AGENTE
// ============================================================================

export class BrasalandAgent {
  private empleadosActivos: Map<string, EmpleadoOnboarding> = new Map();
  private estadoMesas: Map<string, any> = new Map();
  
  constructor() {
    console.log("🤖 Inicializando Brasaland Agent...");
  }
  
  // ==========================================================================
  // INICIALIZACIÓN Y RECUPERACIÓN
  // ==========================================================================
  
  async inicializar(): Promise<RespuestaAgente> {
    try {
      // 1. Recuperar estado post-reinicio
      const estadoRecuperado = await recuperarEstadoPostReinicio();
      
      // 2. Cargar empleados activos en memoria
      for (const empleado of estadoRecuperado.empleadosActivos) {
        this.empleadosActivos.set(empleado.id, empleado);
      }
      
      // 3. Cargar estado de mesas
      for (const [localId, estado] of Object.entries(estadoRecuperado.mesasPorLocal)) {
        this.estadoMesas.set(localId, estado);
      }
      
      // 4. Validar integridad
      const integridad = await validarIntegridadMemoria();
      
      return {
        success: true,
        mensaje: `✅ Brasaland Agent inicializado. Recuperados: ${estadoRecuperado.empleadosActivos.length} empleados activos, ${Object.keys(estadoRecuperado.mesasPorLocal).length} locales con mesas.`,
        data: {
          empleadosRecuperados: estadoRecuperado.empleadosActivos.length,
          totalEmpleados: estadoRecuperado.totalEmpleados,
          localesConMesas: Object.keys(estadoRecuperado.mesasPorLocal).length,
          integridad: integridad,
        },
      };
      
    } catch (error) {
      console.error("❌ Error inicializando agente:", error);
      return {
        success: false,
        mensaje: "Error inicializando Brasaland Agent",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  // ==========================================================================
  // ONBOARDING DE EMPLEADOS
  // ==========================================================================
  
  async iniciarOnboarding(correo: string, nombre?: string): Promise<RespuestaAgente> {
    try {
      // Verificar si ya existe empleado con este correo
      const empleados = await listarEmpleadosPorEstado();
      const existe = empleados.find(e => e.correo.toLowerCase() === correo.toLowerCase());
      
      if (existe) {
        // Empleado ya existe, continuar desde donde estaba
        this.empleadosActivos.set(existe.id, existe);
        
        return {
          success: true,
          mensaje: `¡Bienvenido de nuevo, ${existe.nombre_completo}! Continuemos con tu onboarding.`,
          data: {
            empleado_id: existe.id,
            paso_actual: existe.paso_actual,
            estado: existe.estado,
          },
          siguiente_paso: existe.paso_actual,
          preguntas_pendientes: [obtenerPreguntaPaso(existe.paso_actual)],
          estado_actual: obtenerResumenProgreso(existe.paso_actual),
        };
      }
      
      // Crear nuevo empleado
      const nuevoEmpleado: EmpleadoOnboarding = {
        id: generarIDEmpleado(),
        nombre_completo: nombre || "Por definir",
        correo: correo.toLowerCase(),
        local_asignado: null,
        talla_uniforme: null,
        cuenta_bancaria: null,
        manual_confirmado: false,
        manual_fecha: null,
        recorrido_confirmado: false,
        recorrido_supervisor: null,
        estado: "no_iniciado",
        paso_actual: 0,
        fecha_inicio: new Date().toISOString(),
        fecha_ultima_interaccion: new Date().toISOString(),
        fecha_cierre: null,
        recordatorios_enviados: 0,
        intentos_fallidos: 0,
      };
      
      // Guardar en memoria persistente
      await guardarEmpleado(nuevoEmpleado);
      
      // Actualizar memoria en RAM
      this.empleadosActivos.set(nuevoEmpleado.id, nuevoEmpleado);
      
      return {
        success: true,
        mensaje: `¡Bienvenido a Brasaland! Comencemos con tu proceso de incorporación.`,
        data: {
          empleado_id: nuevoEmpleado.id,
          paso_actual: 0,
          estado: "no_iniciado",
        },
        siguiente_paso: 1,
        preguntas_pendientes: [obtenerPreguntaPaso(1)],
        estado_actual: "Paso 1 de 6",
      };
      
    } catch (error) {
      console.error("❌ Error iniciando onboarding:", error);
      return {
        success: false,
        mensaje: "Error iniciando proceso de onboarding",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  async procesarRespuestaEmpleado(
    empleadoId: string, 
    respuesta: string
  ): Promise<RespuestaAgente> {
    try {
      // Obtener empleado
      const empleado = this.empleadosActivos.get(empleadoId) || await leerEmpleado(empleadoId);
      if (!empleado) {
        return {
          success: false,
          mensaje: "Empleado no encontrado. Por favor, inicia el proceso de nuevo.",
          errores: [{ campo: "empleado_id", mensaje: "ID no válido" }],
        };
      }
      
      // Determinar paso actual
      let pasoActual = empleado.paso_actual;
      if (empleado.estado === "no_iniciado") {
        pasoActual = 1;
        empleado.estado = "activo";
      }
      
      // Validar respuesta según paso
      const validacion = validarPasoOnboarding(pasoActual, respuesta);
      
      if (!validacion.valido) {
        // Incrementar intentos fallidos
        empleado.intentos_fallidos += 1;
        empleado.fecha_ultima_interaccion = new Date().toISOString();
        
        // Si muchos intentos fallidos, sugerir ayuda
        if (empleado.intentos_fallidos >= 3) {
          return {
            success: false,
            mensaje: validacion.mensaje || "Respuesta no válida",
            errores: [{ campo: validacion.campo || "respuesta", mensaje: validacion.mensaje || "No válido" }],
            sugerencias: [
              "¿Necesitas ayuda con este paso?",
              "Puedo contactar a RRHH si tienes dificultades.",
            ],
          };
        }
        
        return {
          success: false,
          mensaje: validacion.mensaje || "Respuesta no válida",
          errores: [{ campo: validacion.campo || "respuesta", mensaje: validacion.mensaje || "No válido" }],
          sugerencias: [`Formato esperado para paso ${pasoActual}: ver instrucciones anteriores`],
        };
      }
      
      // Procesar respuesta válida
      switch (pasoActual) {
        case 1:
          empleado.nombre_completo = respuesta.trim();
          break;
          
        case 2:
          empleado.local_asignado = respuesta.trim();
          break;
          
        case 3:
          empleado.cuenta_bancaria = respuesta.trim();
          break;
          
        case 4:
          empleado.talla_uniforme = respuesta.trim() as TallaUniforme;
          break;
          
        case 5:
          empleado.manual_confirmado = true;
          const fechaManual = extraerFechaManual(respuesta);
          if (fechaManual) {
            empleado.manual_fecha = fechaManual;
          }
          break;
          
        case 6:
          empleado.recorrido_confirmado = true;
          const supervisor = extraerNombreSupervisor(respuesta);
          if (supervisor) {
            empleado.recorrido_supervisor = supervisor;
          }
          break;
      }
      
      // Actualizar estado
      empleado.paso_actual = pasoActual;
      empleado.fecha_ultima_interaccion = new Date().toISOString();
      empleado.intentos_fallidos = 0; // Resetear intentos fallidos
      
      // Verificar si completó todos los pasos
      if (pasoActual === 6) {
        empleado.estado = "terminado";
        empleado.fecha_cierre = new Date().toISOString();
        
        // Validar empleado completo
        const validacionCompleta = validarEmpleadoCompleto(empleado);
        
        if (validacionCompleta.valido) {
          // Notificar a Ashley (simulado)
          await this.notificarOnboardingCompletado(empleado);
        } else {
          // Hay errores en datos completos
          return {
            success: false,
            mensaje: "Proceso casi completo, pero hay inconsistencias en los datos:",
            errores: validacionCompleta.errores,
            sugerencias: validacionCompleta.sugerencias,
            data: { empleado_id: empleado.id, paso_actual: pasoActual },
          };
        }
      }
      
      // Persistir cambios
      await actualizarEmpleado(empleado);
      this.empleadosActivos.set(empleadoId, empleado);
      
      // Preparar respuesta
      const siguientePaso = pasoActual === 6 ? null : pasoActual + 1;
      const mensajeFinal = pasoActual === 6 
        ? `🎉 ¡Felicidades ${empleado.nombre_completo}! Has completado tu onboarding en Brasaland. RRHH ha sido notificado.`
        : `✅ Paso ${pasoActual} completado correctamente.`;
      
      return {
        success: true,
        mensaje: mensajeFinal,
        data: {
          empleado_id: empleado.id,
          paso_actual: pasoActual,
          siguiente_paso: siguientePaso,
          estado: empleado.estado,
          progreso: obtenerResumenProgreso(pasoActual),
        },
        siguiente_paso: siguientePaso,
        preguntas_pendientes: siguientePaso ? [obtenerPreguntaPaso(siguientePaso)] : [],
        estado_actual: obtenerResumenProgreso(pasoActual),
      };
      
    } catch (error) {
      console.error("❌ Error procesando respuesta:", error);
      return {
        success: false,
        mensaje: "Error procesando tu respuesta",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  private async notificarOnboardingCompletado(empleado: EmpleadoOnboarding): Promise<void> {
    // Simulación de notificación a Ashley
    const mensaje = `🚀 Nuevo empleado completó onboarding:
    • Nombre: ${empleado.nombre_completo}
    • Correo: ${empleado.correo}
    • Local: ${empleado.local_asignado}
    • Fecha completado: ${new Date().toLocaleDateString()}
    
    ¡Listo para incorporarse!`;
    
    await registrarEvento({
      timestamp: new Date().toISOString(),
      tipo: "EMPLEADO_TERMINADO",
      usuario: "system",
      detalles: `Onboarding completado para ${empleado.nombre_completo}`,
      metadata: {
        empleado_id: empleado.id,
        local: empleado.local_asignado,
        fecha_completado: empleado.fecha_cierre,
      },
    });
    
    console.log("📧 Notificación a Ashley:", mensaje);
    // En implementación real: enviar a Telegram @ashley_brasaland
  }
  
  // ==========================================================================
  // GESTIÓN DE MESAS Y RESERVAS
  // ==========================================================================
  
  async consultarMesasLibres(localId: string, capacidad?: number): Promise<RespuestaAgente> {
    try {
      const estadoMesas = this.estadoMesas.get(localId) || await leerEstadoMesas(localId);
      
      if (!estadoMesas) {
        return {
          success: false,
          mensaje: `Local ${localId} no encontrado o sin información de mesas`,
          errores: [{ campo: "local_id", mensaje: "Local no válido" }],
        };
      }
      
      let mesasFiltradas = estadoMesas.detalle_mesas;
      if (capacidad) {
        mesasFiltradas = mesasFiltradas.filter((m: MesaRestaurante) => m.capacidad >= capacidad && m.estado === "libre");
      } else {
        mesasFiltradas = mesasFiltradas.filter((m: MesaRestaurante) => m.estado === "libre");
      }
      
      const mesasConEstimacion = mesasFiltradas.map((mesa: MesaRestaurante) => ({
        id: mesa.id,
        capacidad: mesa.capacidad,
        estado: mesa.estado,
        estimacion_liberacion: mesa.estimacion_liberacion,
        // Calcular tiempo estimado de espera si está ocupada pero con estimación
        tiempo_espera_min: mesa.estado === "ocupada" && mesa.estimacion_liberacion
          ? Math.max(0, Math.round((new Date(mesa.estimacion_liberacion).getTime() - Date.now()) / (1000 * 60)))
          : 0,
      }));
      
      return {
        success: true,
        mensaje: `📊 Estado mesas en ${estadoMesas.nombre}: ${estadoMesas.mesas_libres} libres de ${estadoMesas.total_mesas} totales`,
        data: {
          local: estadoMesas.nombre,
          total_mesas: estadoMesas.total_mesas,
          mesas_libres: estadoMesas.mesas_libres,
          mesas_ocupadas: estadoMesas.mesas_ocupadas,
          mesas_reservadas: estadoMesas.mesas_reservadas,
          mesas_disponibles: mesasConEstimacion,
          ultima_actualizacion: estadoMesas.ultima_actualizacion,
        },
        sugerencias: capacidad 
          ? [`Para ${capacidad} personas, recomiendo mesas de capacidad ${capacidad} o superior.`]
          : ["¿Para cuántas personas necesitas mesa?"],      };
      
    } catch (error) {
      console.error("❌ Error consultando mesas:", error);
      return {
        success: false,
        mensaje: "Error consultando disponibilidad de mesas",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  async crearReserva(reserva: Partial<ReservaCliente>): Promise<RespuestaAgente> {
    try {
      // Validar reserva básica
      const validacion = validateReservaMesa(reserva);
      if (!validacion.valid) {
        return {
          success: false,
          mensaje: "Datos de reserva no válidos",
          errores: validacion.errors.map(e => ({ campo: e.field, mensaje: e.message })),
        };
      }
      
      // Verificar disponibilidad de mesa
      const localId = reserva.local_id!;
      const mesaId = reserva.idMesa!;
      
      const estadoMesas = this.estadoMesas.get(localId) || await leerEstadoMesas(localId);
      if (!estadoMesas) {
        return {
          success: false,
          mensaje: `Local ${localId} no encontrado`,
          errores: [{ campo: "local_id", mensaje: "Local no válido" }],
        };
      }
      
      const mesa = estadoMesas.detalle_mesas.find((m: MesaRestaurante) => m.id === mesaId);
      if (!mesa) {
        return {
          success: false,
          mensaje: `Mesa ${mesaId} no encontrada en este local`,
          errores: [{ campo: "idMesa", mensaje: "Mesa no existe" }],
        };
      }
      
      if (mesa.estado !== "libre") {
        const estado = mesa.estado === "ocupada" ? "ocupada" : "reservada";
        const estimacion = mesa.estimacion_liberacion 
          ? ` (se libera aproximadamente a las ${new Date(mesa.estimacion_liberacion).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`
          : "";
        
        return {
          success: false,
          mensaje: `La mesa ${mesaId} está ${estado}${estimacion}`,
          errores: [{ campo: "idMesa", mensaje: `Mesa ${estado}` }],
          sugerencias: [
            "¿Quieres consultar otras mesas disponibles?",
            "¿Prefieres reservar para más tarde?",
          ],
        };
      }
      
      // Verificar capacidad
      if (reserva.numeroComensales && reserva.numeroComensales > mesa.capacidad) {
        return {
          success: false,
          mensaje: `La mesa ${mesaId} tiene capacidad para ${mesa.capacidad} personas, pero solicitas ${reserva.numeroComensales}`,
          errores: [{ campo: "numeroComensales", mensaje: `Excede capacidad de mesa (max ${mesa.capacidad})` }],
          sugerencias: [
            `Te recomiendo una mesa de capacidad ${Math.ceil(reserva.numeroComensales / 2) * 2} o superior.`,
            "¿Quieres que busque mesas con mayor capacidad?",
          ],
        };
      }
      
      // Crear reserva
      const reservaCompleta: ReservaCliente = {
        id: `RES_${Date.now().toString().slice(-6)}`,
        nombreCliente: reserva.nombreCliente!,
        numeroComensales: reserva.numeroComensales!,
        fechaHora: reserva.fechaHora!,
        idMesa: mesaId,
        estado: "confirmada",
        local_id: localId,
        contacto_telefono: reserva.contacto_telefono,
        notas: reserva.notas,
      };
      
      // Actualizar estado de mesa
      mesa.estado = "reservada";
      mesa.reserva_id = reservaCompleta.id;
      mesa.reserva_hora = reservaCompleta.fechaHora;
      mesa.cliente_nombre = reservaCompleta.nombreCliente;
      
      // Recalcular contadores
      estadoMesas.mesas_libres -= 1;
      estadoMesas.mesas_reservadas += 1;
      estadoMesas.ultima_actualizacion = new Date().toISOString();
      
      // Persistir cambios
      await guardarEstadoMesas(localId, estadoMesas);
      this.estadoMesas.set(localId, estadoMesas);
      
      // Registrar evento
      await registrarEvento({
        timestamp: new Date().toISOString(),
        tipo: "RESERVA_CREADA",
        usuario: "cliente",
        detalles: `Reserva creada para ${reservaCompleta.nombreCliente} en mesa ${mesaId}`,
        metadata: {
          reserva_id: reservaCompleta.id,
          local_id: localId,
          mesa_id: mesaId,
          comensales: reservaCompleta.numeroComensales,
          fecha_hora: reservaCompleta.fechaHora,
        },
      });
      
      return {
        success: true,
        mensaje: `✅ Reserva confirmada para ${reservaCompleta.nombreCliente}`,
        data: {
          reserva_id: reservaCompleta.id,
          local: estadoMesas.nombre,
          mesa: mesaId,
          capacidad: mesa.capacidad,
          fecha_hora: new Date(reservaCompleta.fechaHora).toLocaleString(),
          comensales: reservaCompleta.numeroComensales,
          estado: "confirmada",
        },
        sugerencias: [
          "Llega 10 minutos antes de tu reserva.",
          "Para cancelaciones, contáctanos con al menos 2 horas de anticipación.",
        ],
      };
      
    } catch (error) {
      console.error("❌ Error creando reserva:", error);
      return {
        success: false,
        mensaje: "Error creando reserva",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  // ==========================================================================
  // REPORTES Y MONITOREO
  // ==========================================================================
  
  async generarReporteMatutino(): Promise<RespuestaAgente> {
    try {
      const empleadosActivos = await listarEmpleadosPorEstado("activo");
      const empleadosInactivos48h = empleadosActivos.filter(e => esEmpleadoInactivo(e, 48));
      
      const nuevosUltimas24h = empleadosActivos.filter(e => {
        const fechaInicio = new Date(e.fecha_inicio);
        const ahora = new Date();
        const horas = (ahora.getTime() - fechaInicio.getTime()) / (1000 * 60 * 60);
        return horas <= 24;
      });
      
      const empleadosTerminados = await listarEmpleadosPorEstado("terminado");
      const terminadosUltimas24h = empleadosTerminados.filter(e => {
        if (!e.fecha_cierre) return false;
        const fechaCierre = new Date(e.fecha_cierre);
        const ahora = new Date();
        const horas = (ahora.getTime() - fechaCierre.getTime()) / (1000 * 60 * 60);
        return horas <= 24;
      });
      
      // Calcular progreso promedio
      const progresoPromedio = empleadosActivos.length > 0
        ? empleadosActivos.reduce((sum, e) => sum + e.paso_actual, 0) / empleadosActivos.length
        : 0;
      
      const reporte = {
        fecha: new Date().toISOString().split("T")[0],
        total_empleados_activos: empleadosActivos.length,
        nuevos_ultimas_24h: nuevosUltimas24h.length,
        completados_ultimas_24h: terminadosUltimas24h.length,
        empleados_inactivos_48h: empleadosInactivos48h.map(e => ({
          id: e.id,
          nombre: e.nombre_completo,
          local: e.local_asignado || "No asignado",
          ultima_interaccion: e.fecha_ultima_interaccion,
          paso_actual: e.paso_actual,
        })),
        progreso_promedio: parseFloat(progresoPromedio.toFixed(1)),
        problemas_detectados: [] as any[],
        recomendaciones: [] as string[],
      };
      
      // Generar recomendaciones
      if (empleadosInactivos48h.length > 0) {
        reporte.recomendaciones.push(
          `Contactar a ${empleadosInactivos48h.length} empleados inactivos >48h`
        );
      }
      
      if (progresoPromedio < 2 && empleadosActivos.length > 3) {
        reporte.recomendaciones.push(
          "Progreso promedio bajo. Considerar recordatorios masivos."
        );
      }
      
      return {
        success: true,
        mensaje: `📈 Reporte Matutino Brasaland - ${reporte.fecha}`,
        data: reporte,
        sugerencias: reporte.recomendaciones,
      };
      
    } catch (error) {
      console.error("❌ Error generando reporte:", error);
      return {
        success: false,
        mensaje: "Error generando reporte matutino",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  async obtenerEstadisticas(): Promise<RespuestaAgente> {
    try {
      const empleados = await listarEmpleadosPorEstado();
      
      const estadisticas = {
        total_empleados: empleados.length,
        por_estado: {
          activos: empleados.filter(e => e.estado === "activo").length,
          terminados: empleados.filter(e => e.estado === "terminado").length,
          no_iniciados: empleados.filter(e => e.estado === "no_iniciado").length,
        },
        por_local: {} as Record<string, number>,
        por_talla: {} as Record<string, number>,
        tiempos_promedio: {
          completado_min: null as number | null,
          por_paso_min: [] as number[],
        },
      };
      
      // Calcular distribuciones
      empleados.forEach(e => {
        if (e.local_asignado) {
          estadisticas.por_local[e.local_asignado] = (estadisticas.por_local[e.local_asignado] || 0) + 1;
        }
        if (e.talla_uniforme) {
          estadisticas.por_talla[e.talla_uniforme] = (estadisticas.por_talla[e.talla_uniforme] || 0) + 1;
        }
      });
      
      // Calcular tiempos (empleados terminados)
      const terminados = empleados.filter(e => e.estado === "terminado" && e.fecha_inicio && e.fecha_cierre);
      if (terminados.length > 0) {
        const tiempos = terminados.map(e => {
          const inicio = new Date(e.fecha_inicio);
          const cierre = new Date(e.fecha_cierre!);
          return (cierre.getTime() - inicio.getTime()) / (1000 * 60); // minutos
        });
        
        estadisticas.tiempos_promedio.completado_min = 
          tiempos.reduce((sum, t) => sum + t, 0) / tiempos.length;
      }
      
      return {
        success: true,
        mensaje: `📊 Estadísticas Brasaland - Total empleados: ${estadisticas.total_empleados}`,
        data: estadisticas,
      };
      
    } catch (error) {
      console.error("❌ Error obteniendo estadísticas:", error);
      return {
        success: false,
        mensaje: "Error obteniendo estadísticas",
        errores: [{ campo: "sistema", mensaje: String(error) }],
      };
    }
  }
  
  // ==========================================================================
  // UTILIDADES DEL AGENTE
  // ==========================================================================
  
  async obtenerEmpleado(empleadoId: string): Promise<EmpleadoOnboarding | null> {
    return this.empleadosActivos.get(empleadoId) || await leerEmpleado(empleadoId);
  }
  
  async obtenerEstadoMesas(localId: string): Promise<any> {
    return this.estadoMesas.get(localId) || await leerEstadoMesas(localId);
  }
  
  getTotalEmpleadosActivos(): number {
    return this.empleadosActivos.size;
  }
  
  async limpiarCache(): Promise<void> {
    this.empleadosActivos.clear();
    this.estadoMesas.clear();
    
    // Recargar desde persistencia
    const estado = await recuperarEstadoPostReinicio();
    estado.empleadosActivos.forEach(e => this.empleadosActivos.set(e.id, e));
    Object.entries(estado.mesasPorLocal).forEach(([localId, estadoLocal]) => {
      this.estadoMesas.set(localId, estadoLocal);
    });
  }
}