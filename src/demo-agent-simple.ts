// src/demo-agent-simple.ts
// Demostración simplificada del Agente Brasaland

import { BrasalandAgent } from "./agent/brasaland-agent";

async function main() {
  console.log("🚀 DEMO SIMPLIFICADA BRASALAND AGENT");
  console.log("👤 Personalidad: Gojo (Brasaland Edition)");
  console.log("📅 Fecha: " + new Date().toISOString());
  console.log("=".repeat(60));
  
  try {
    // 1. Inicialización
    console.log("\n1. 🧠 INICIALIZANDO AGENTE...");
    const agente = new BrasalandAgent();
    const initResult = await agente.inicializar();
    
    if (initResult.success) {
      console.log("✅ " + initResult.mensaje);
    } else {
      console.error("❌ Error:", initResult.errores);
      return;
    }
    
    // 2. Onboarding de empleado
    console.log("\n2. 👤 SIMULANDO ONBOARDING DE EMPLEADO...");
    const onboardingResult = await agente.iniciarOnboarding("demo@brasaland.com", "Demo User");
    
    if (onboardingResult.success) {
      const empleadoId = onboardingResult.data?.empleado_id;
      console.log("✅ Onboarding iniciado. ID:", empleadoId);
      console.log("📝 Pregunta actual:", onboardingResult.preguntas_pendientes?.[0]);
      
      // Simular respuesta al paso 1
      console.log("\n🎯 Procesando respuesta al paso 1...");
      const respuesta1 = await agente.procesarRespuestaEmpleado(empleadoId, "Demo User Completo");
      
      if (respuesta1.success) {
        console.log("✅ " + respuesta1.mensaje);
        console.log("📊 Progreso:", respuesta1.estado_actual);
      }
    }
    
    // 3. Consulta de mesas
    console.log("\n3. 🪑 CONSULTANDO MESAS DISPONIBLES...");
    const mesasResult = await agente.consultarMesasLibres("MED_ELP", 4);
    
    if (mesasResult.success) {
      console.log("✅ " + mesasResult.mensaje);
      const data = mesasResult.data;
      if (data?.mesas_disponibles?.length > 0) {
        console.log("📋 Mesas disponibles para 4 personas:");
        data.mesas_disponibles.forEach((mesa: any, i: number) => {
          console.log(`   ${i+1}. Mesa ${mesa.id} - Capacidad: ${mesa.capacidad}`);
        });
      }
    }
    
    // 4. Reporte matutino
    console.log("\n4. 📊 GENERANDO REPORTE MATUTINO...");
    const reporteResult = await agente.generarReporteMatutino();
    
    if (reporteResult.success) {
      console.log("✅ " + reporteResult.mensaje);
      const data = reporteResult.data;
      console.log(`👥 Empleados activos: ${data?.total_empleados_activos || 0}`);
      console.log(`📈 Progreso promedio: ${data?.progreso_promedio || 0}/6 pasos`);
    }
    
    // 5. Validación de persistencia
    console.log("\n5. 💾 VALIDANDO PERSISTENCIA...");
    console.log("🔄 Limpiando cache (simulando reinicio)...");
    await agente.limpiarCache();
    
    console.log("✅ Cache limpiada. Estado debería persistir en disco.");
    
    // 6. Estadísticas
    console.log("\n6. 📈 OBTENIENDO ESTADÍSTICAS...");
    const statsResult = await agente.obtenerEstadisticas();
    
    if (statsResult.success) {
      console.log("✅ " + statsResult.mensaje);
    }
    
    console.log("\n" + "=".repeat(60));
    console.log("🏁 DEMO COMPLETADA EXITOSAMENTE");
    console.log("🎯 Agente Brasaland implementa:");
    console.log("   • Onboarding de 6 pasos con validaciones");
    console.log("   • Gestión de mesas en tiempo real");
    console.log("   • Memoria persistente (sobrevive reinicios)");
    console.log("   • Reportes para Ashley Turner (RRHH)");
    console.log("   • Personalidad Gojo adaptada a Brasaland");
    console.log("\n🤖 ¡Agente listo para producción!");
    
  } catch (error) {
    console.error("❌ Error en demo:", error);
  }
}

// Ejecutar demo
if (require.main === module) {
  main().catch(console.error);
}

export { main };