// src/demo-agent.ts
// Demostración del Agente Brasaland - Onboarding + Gestión de Mesas

import { BrasalandAgent } from "./agent/brasaland-agent";
import { EmpleadoOnboarding } from "./types/onboarding";

// ============================================================================
// CONFIGURACIÓN DE LA DEMO
// ============================================================================

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function printSeparator(title: string): void {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`🧠 ${title}`);
  console.log(`${"=".repeat(60)}\n`);
}

// ============================================================================
// DEMO 1: INICIALIZACIÓN Y RECUPERACIÓN POST-REINICIO
// ============================================================================

async function demoInicializacion(): Promise<void> {
  printSeparator("DEMO 1: INICIALIZACIÓN DEL AGENTE");
  
  const agente = new BrasalandAgent();
  
  console.log("🤖 Creando instancia de BrasalandAgent...");
  await delay(1000);
  
  const resultado = await agente.inicializar();
  
  if (resultado.success) {
    console.log("✅ " + resultado.mensaje);
    console.log("📊 Datos recuperados:", JSON.stringify(resultado.data, null, 2));
  } else {
    console.error("❌ Error inicializando:", resultado.errores);
  }
  
  return agente;
}

// ============================================================================
// DEMO 2: PROCESO DE ONBOARDING COMPLETO
// ============================================================================

async function demoOnboardingCompleto(agente: BrasalandAgent): Promise<string> {
  printSeparator("DEMO 2: ONBOARDING COMPLETO DE EMPLEADO");
  
  console.log("👤 Simulando nuevo empleado: maria.garcia@example.com");
  await delay(500);
  
  // Paso 1: Iniciar onboarding
  const inicio = await agente.iniciarOnboarding("maria.garcia@example.com", "María García");
  
  if (!inicio.success) {
    console.error("❌ Error iniciando onboarding:", inicio.errores);
    return "";
  }
  
  const empleadoId = inicio.data?.empleado_id;
  console.log(`✅ Onboarding iniciado. ID empleado: ${empleadoId}`);
  console.log(`📝 Pregunta actual: ${inicio.preguntas_pendientes?.[0]}`);
  
  // Simular respuestas paso a paso
  const respuestas = [
    "María García López", // Paso 1: Nombre completo
    "Medellín, El Poblado", // Paso 2: Local asignado
    "ES12 3456 7890 1234 5678", // Paso 3: Cuenta bancaria
    "M", // Paso 4: Talla uniforme
    "Sí, leído el 2026-06-28", // Paso 5: Manual de alimentos
    "Sí, con Carlos Rodríguez", // Paso 6: Recorrido cocina
  ];
  
  for (let i = 0; i < respuestas.length; i++) {
    await delay(800);
    console.log(`\n🎯 Respuesta ${i + 1}: "${respuestas[i]}"`);
    
    const respuesta = await agente.procesarRespuestaEmpleado(empleadoId, respuestas[i]);
    
    if (respuesta.success) {
      console.log(`✅ ${respuesta.mensaje}`);
      if (respuesta.preguntas_pendientes?.[0]) {
        console.log(`📝 Siguiente: ${respuesta.preguntas_pendientes[0]}`);
      }
    } else {
      console.error(`❌ Error en paso ${i + 1}:`, respuesta.errores);
      if (respuesta.sugerencias) {
        console.log("💡 Sugerencias:", respuesta.sugerencias.join(", "));
      }
      break;
    }
  }
  
  return empleadoId;
}

// ============================================================================
// DEMO 3: GESTIÓN DE MESAS Y RESERVAS
// ============================================================================

async function demoGestionMesas(agente: BrasalandAgent): Promise<void> {
  printSeparator("DEMO 3: CONSULTA Y RESERVA DE MESAS");
  
  console.log("🪑 Consultando mesas disponibles en Medellín El Poblado...");
  await delay(500);
  
  // Consultar mesas libres
  const consulta = await agente.consultarMesasLibres("MED_ELP", 4);
  
  if (consulta.success) {
    console.log(`✅ ${consulta.mensaje}`);
    
    const mesasDisponibles = consulta.data?.mesas_disponibles || [];
    if (mesasDisponibles.length > 0) {
      console.log("📋 Mesas disponibles para 4 personas:");
      mesasDisponibles.forEach((mesa: any, index: number) => {
        console.log(`   ${index + 1}. Mesa ${mesa.id} - Capacidad: ${mesa.capacidad} personas`);
      });
    } else {
      console.log("⚠️ No hay mesas disponibles para 4 personas.");
    }
  } else {
    console.error("❌ Error consultando mesas:", consulta.errores);
  }
  
  // Crear reserva (simulada)
  await delay(1000);
  console.log("\n📅 Creando reserva para 4 personas...");
  
  const reserva = await agente.crearReserva({
    nombreCliente: "Juan Pérez",
    numeroComensales: 4,
    fechaHora: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // En 2 horas
    idMesa: "M11", // Mesa disponible para 4 personas
    local_id: "MED_ELP",
    contacto_telefono: "+57 300 123 4567",
    notas: "Celebración de aniversario",
  });
  
  if (reserva.success) {
    console.log(`✅ ${reserva.mensaje}`);
    console.log("📋 Detalles reserva:", JSON.stringify(reserva.data, null, 2));
    if (reserva.sugerencias) {
      console.log("💡 Recomendaciones:", reserva.sugerencias.join(" "));
    }
  } else {
    console.error("❌ Error creando reserva:", reserva.errores);
    if (reserva.sugerencias) {
      console.log("💡 Alternativas:", reserva.sugerencias.join(" "));
    }
  }
}

// ============================================================================
// DEMO 4: REPORTES Y ESTADÍSTICAS
// ============================================================================

async function demoReportes(agente: BrasalandAgent, empleadoId: string): Promise<void> {
  printSeparator("DEMO 4: REPORTES Y ESTADÍSTICAS");
  
  console.log("📊 Generando reporte matutino...");
  await delay(500);
  
  const reporte = await agente.generarReporteMatutino();
  
  if (reporte.success) {
    console.log(`✅ ${reporte.mensaje}`);
    
    const data = reporte.data;
    console.log(`👥 Empleados activos: ${data?.total_empleados_activos || 0}`);
    console.log(`🆕 Nuevos últimas 24h: ${data?.nuevos_ultimas_24h || 0}`);
    console.log(`✅ Completados últimas 24h: ${data?.completados_ultimas_24h || 0}`);
    console.log(`⏰ Progreso promedio: ${data?.progreso_promedio || 0}/6 pasos`);
    
    if (data?.empleados_inactivos_48h?.length > 0) {
      console.log("\n⚠️ Empleados inactivos >48h:");
      data.empleados_inactivos_48h.forEach((emp: any) => {
        console.log(`   • ${emp.nombre} (${emp.local}) - Última: ${emp.ultima_interaccion}`);
      });
    }
    
    if (reporte.sugerencias?.length) {
      console.log("\n💡 Recomendaciones:");
      reporte.sugerencias.forEach(s => console.log(`   • ${s}`));
    }
  }
  
  // Estadísticas generales
  await delay(1000);
  console.log("\n📈 Obteniendo estadísticas generales...");
  
  const estadisticas = await agente.obtenerEstadisticas();
  
  if (estadisticas.success) {
    console.log(`✅ ${estadisticas.mensaje}`);
    console.log("📋 Resumen:", JSON.stringify(estadisticas.data, null, 2));
  }
}

// ============================================================================
// DEMO 5: VALIDACIÓN DE PERSISTENCIA (SIMULACIÓN REINICIO)
// ============================================================================

async function demoPersistencia(agente: BrasalandAgent, empleadoId: string): Promise<void> {
  printSeparator("DEMO 5: VALIDACIÓN DE PERSISTENCIA POST-REINICIO");
  
  console.log("🔄 Simulando reinicio del agente...");
  await delay(1000);
  
  // Limpiar cache para simular reinicio
  await agente.limpiarCache();
  console.log("✅ Cache limpiada (simulando reinicio)");
  
  await delay(500);
  console.log("\n🔍 Recuperando empleado después del 'reinicio'...");
  
  const empleadoRecuperado = await agente.obtenerEmpleado(empleadoId);
  
  if (empleadoRecuperado) {
    console.log("✅ ¡Empleado recuperado exitosamente de memoria persistente!");
    console.log("📋 Datos recuperados:");
    console.log(`   • ID: ${empleadoRecuperado.id}`);
    console.log(`   • Nombre: ${empleadoRecuperado.nombre_completo}`);
    console.log(`   • Estado: ${empleadoRecuperado.estado}`);
    console.log(`   • Paso actual: ${empleadoRecuperado.paso_actual}/6`);
    console.log(`   • Local: ${empleadoRecuperado.local_asignado}`);
    console.log(`   • Fecha inicio: ${empleadoRecuperado.fecha_inicio}`);
    console.log(`   • Última interacción: ${empleadoRecuperado.fecha_ultima_interaccion}`);
    
    if (empleadoRecuperado.estado === "terminado") {
      console.log(`   • Fecha cierre: ${empleadoRecuperado.fecha_cierre}`);
    }
  } else {
    console.error("❌ No se pudo recuperar el empleado después del reinicio");
  }
}

// ============================================================================
// DEMO 6: INTEGRACIÓN CON CARTA EXISTENTE (TYPESCRIPT REPO)
// ============================================================================

async function demoIntegracionCarta(): Promise<void> {
  printSeparator("DEMO 6: INTEGRACIÓN CON CARTA BRASALAND (REPO EXISTENTE)");
  
  console.log("📋 Consultando tipos de datos de la carta existente...");
  await delay(500);
  
  // Importar tipos y funciones del repo TypeScript existente
  try {
    const { PlatoCarta, validatePlatoCarta } = require("../types/models");
    const { reportSummaryByCategory } = require("../utils/transformations");
    
    console.log("✅ Tipos importados correctamente del código base existente");
    
    // Crear datos de ejemplo de carta (simulando integración)
    const platosEjemplo: PlatoCarta[] = [
      {
        id: "pla-1",
        nombre: "Entranha Fina",
        categoria: "principal",
        precio: 32.5,
        alergenos: ["Su"],
        activoEnCarta: true,
      },
      {
        id: "pla-2",
        nombre: "Tabla Ibericos",
        categoria: "entrada",
        precio: 24.9,
        alergenos: ["Su", "G"],
        activoEnCarta: true,
      },
      {
        id: "pla-3",
        nombre: "Tiramisu",
        categoria: "postre",
        precio: 7.2,
        alergenos: ["G", "L", "H"],
        activoEnCarta: true,
      },
    ];
    
    console.log("\n🍽️  Validando platos de carta:");
    platosEjemplo.forEach(plato => {
      const validacion = validatePlatoCarta(plato);
      console.log(`   • ${plato.nombre}: ${validacion.valid ? "✅ Válido" : "❌ Inválido"}`);
    });
    
    console.log("\n📊 Generando reporte de precios por categoría:");
    const platosActivos = platosEjemplo.filter(p => p.activoEnCarta);
    const reportePrecios = reportSummaryByCategory(
      platosActivos,
      (p: PlatoCarta) => p.categoria,
      (p: PlatoCarta) => p.precio
    );
    
    Object.entries(reportePrecios).forEach(([categoria, stats]: [string, any]) => {
      console.log(`   • ${categoria}: $${stats.avg.toFixed(2)} promedio (min $${stats.min}, max $${stats.max})`);
    });
    
    console.log("\n🔗 ¡Integración con código base TypeScript exitosa!");
    
  } catch (error) {
    console.error("❌ Error en integración:", error);
    console.log("💡 Nota: Esto es una simulación. En producción se importarían los módulos reales.");
  }
}

// ============================================================================
// EJECUCIÓN PRINCIPAL
// ============================================================================

async function main(): Promise<void> {
  try {
    printSeparator("🚀 DEMO COMPLETA BRASALAND AGENT");
    console.log("👤 Personalidad: Gojo (Brasaland Edition)");
    console.log("🎯 Enfoque: Onboarding + Gestión de Mesas + Memoria Persistente");
    console.log("📅 Fecha: " + new Date().toISOString());
    
    // Demo 1: Inicialización
    const agente = await demoInicializacion();
    
    // Demo 2: Onboarding completo
    const empleadoId = await demoOnboardingCompleto(agente);
    if (!empleadoId) return;
    
    // Demo 3: Gestión de mesas
    await demoGestionMesas(agente);
    
    // Demo 4: Reportes
    await demoReportes(agente, empleadoId);
    
    // Demo 5: Persistencia
    await demoPersistencia(agente, empleadoId);
    
    // Demo 6: Integración con carta
    await demoIntegracionCarta();
    
    printSeparator("🏁 DEMO COMPLETADA");
    console.log("✅ Todas las funcionalidades han sido demostradas exitosamente.");
    console.log("🎯 Agente Brasaland está listo para:");
    console.log("   • Gestionar onboarding de empleados con memoria persistente");
    console.log("   • Consultar y reservar mesas en tiempo real");
    console.log("   • Generar reportes para Ashley Turner (RRHH)");
    console.log("   • Mantener estado entre reinicios (sin amnesia de contexto)");
    console.log("   • Integrarse con el código TypeScript existente del repo");
    console.log("\n🤖 ¡Brasaland Agent operativo y persistente!");
    
  } catch (error) {
    console.error("❌ Error en la demo:", error);
  }
}

// Ejecutar si es el módulo principal
if (require.main === module) {
  main().catch(console.error);
}

export { main };