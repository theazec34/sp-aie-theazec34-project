import {
  EncargoProveedor,
  PedidoDomicilio,
  PlatoCarta,
  ReservaMesa,
} from "./types/models";
import {
  validateEncargoProveedor,
  validatePedidoDomicilio,
  validatePlatoCarta,
  validateReservaMesa,
} from "./utils/validations";
import { reportCountsByCategory, reportSummaryByCategory } from "./utils/transformations";

const encargos: EncargoProveedor[] = [
  {
    id: "enc-1",
    idProveedor: "prov-carnes",
    fechaPrevistaEntrega: "2026-06-24",
    estado: "enviado",
    importeTotal: 820.5,
    numeroLineas: 7,
  },
  {
    id: "enc-2",
    idProveedor: "prov-bebidas",
    fechaPrevistaEntrega: "2026-06-25",
    estado: "facturado",
    importeTotal: 390,
    numeroLineas: 4,
  },
  {
    id: "enc-3",
    idProveedor: "prov-verduras",
    fechaPrevistaEntrega: "2026-06-23",
    estado: "recibido",
    importeTotal: 210,
    numeroLineas: 3,
  },
];

const platos: PlatoCarta[] = [
  { id: "pla-1", nombre: "Entranha Fina", categoria: "principal", precio: 32.5, alergenos: ["Su"], activoEnCarta: true },
  { id: "pla-2", nombre: "Tabla Ibericos", categoria: "entrada", precio: 24.9, alergenos: ["Su", "G"], activoEnCarta: true },
  { id: "pla-3", nombre: "Tiramisu", categoria: "postre", precio: 7.2, alergenos: ["G", "L", "H"], activoEnCarta: true },
  { id: "pla-4", nombre: "Limonada", categoria: "bebida", precio: 4.5, alergenos: [], activoEnCarta: false },
];

const reservas: ReservaMesa[] = [
  { id: "res-1", nombreCliente: "Ana", numeroComensales: 2, fechaHora: "2026-06-22T20:30:00Z", idMesa: "M-07", estado: "confirmada" },
  { id: "res-2", nombreCliente: "Luis", numeroComensales: 4, fechaHora: "2026-06-22T21:00:00Z", idMesa: "M-10", estado: "pendiente" },
  { id: "res-3", nombreCliente: "Marta", numeroComensales: 3, fechaHora: "2026-06-22T22:00:00Z", idMesa: "M-05", estado: "confirmada" },
  { id: "res-4", nombreCliente: "Jorge", numeroComensales: 2, fechaHora: "2026-06-22T19:30:00Z", idMesa: "M-02", estado: "cancelada" },
];

const pedidos: PedidoDomicilio[] = [
  {
    id: "ped-1",
    direccionEntrega: "Calle Feria 18, Sevilla",
    importeTotal: 38,
    plataforma: "uber",
    estado: "entregado",
    fechaPedido: "2026-06-22T13:10:00Z",
  },
  {
    id: "ped-2",
    direccionEntrega: "Av. Triana 45, Sevilla",
    importeTotal: 22.5,
    plataforma: "just_eat",
    estado: "cancelado",
    fechaPedido: "2026-06-22T13:30:00Z",
  },
  {
    id: "ped-3",
    direccionEntrega: "Calle Betis 10, Sevilla",
    importeTotal: 41.2,
    plataforma: "web_propia",
    estado: "en_reparto",
    fechaPedido: "2026-06-22T13:55:00Z",
  },
  {
    id: "ped-4",
    direccionEntrega: "Plaza Nueva 3, Sevilla",
    importeTotal: 17,
    plataforma: "uber",
    estado: "entregado",
    fechaPedido: "2026-06-22T14:05:00Z",
  },
];

console.log("=== DEMO BRASALAND (HITO 2) ===\n");

console.log("1) Validaciones de entidades:");
console.log("Encargos validos:", encargos.every((e) => validateEncargoProveedor(e).valid));
console.log("Platos validos:", platos.every((p) => validatePlatoCarta(p).valid));
console.log("Reservas validas:", reservas.every((r) => validateReservaMesa(r).valid));
console.log("Pedidos validos:", pedidos.every((p) => validatePedidoDomicilio(p).valid));
console.log();

console.log("2) Reporte EncargoProveedor");
const encargosByEstado = reportCountsByCategory(encargos, (e) => e.estado);
const encargosResumen = reportSummaryByCategory(encargos, (e) => e.estado, (e) => e.importeTotal);
console.log("Conteo por estado:", encargosByEstado);
console.log("Suma/promedio por estado:", encargosResumen);
console.log();

console.log("3) Reporte PlatoCarta (solo activos)");
const platosActivos = platos.filter((p) => p.activoEnCarta);
const platosByCategoria = reportCountsByCategory(platosActivos, (p) => p.categoria);
const platosResumen = reportSummaryByCategory(platosActivos, (p) => p.categoria, (p) => p.precio);
console.log("Conteo activos por categoria:", platosByCategoria);
console.log("Suma/promedio/min/max por categoria:", platosResumen);
console.log();

console.log("4) Reporte ReservaMesa");
const reservasByEstado = reportCountsByCategory(reservas, (r) => r.estado);
const totalComensalesConfirmadas = reservas
  .filter((r) => r.estado === "confirmada")
  .reduce((acc, r) => acc + r.numeroComensales, 0);
console.log("Conteo por estado:", reservasByEstado);
console.log("Suma comensales confirmadas:", totalComensalesConfirmadas);
console.log();

console.log("5) Reporte PedidoDomicilio");
const pedidosByPlataforma = reportCountsByCategory(pedidos, (p) => p.plataforma);
const pedidosNoCancelados = pedidos.filter((p) => p.estado !== "cancelado");
const pedidosResumen = reportSummaryByCategory(
  pedidosNoCancelados,
  (p) => p.plataforma,
  (p) => p.importeTotal
);
console.log("Conteo por plataforma:", pedidosByPlataforma);
console.log("Suma por plataforma (sin cancelados):", Object.fromEntries(Object.entries(pedidosResumen).map(([k, v]) => [k, v.sum])));

console.log("\n=== FIN DEMO ===");
