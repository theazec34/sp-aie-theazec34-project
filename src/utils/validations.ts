import {
  EncargoProveedor,
  EncargoProveedorEstado,
  ErrorDetail,
  PedidoDomicilio,
  PedidoDomicilioEstado,
  PedidoDomicilioPlataforma,
  PlatoCarta,
  PlatoCartaCategoria,
  ReservaMesa,
  ReservaMesaEstado,
} from "../types/models";

const ENCARGO_ESTADOS: EncargoProveedorEstado[] = ["borrador", "enviado", "recibido", "facturado"];
const PLATO_CATEGORIAS: PlatoCartaCategoria[] = ["entrada", "principal", "postre", "bebida"];
const RESERVA_ESTADOS: ReservaMesaEstado[] = ["pendiente", "confirmada", "cancelada", "completada"];
const PEDIDO_PLATAFORMAS: PedidoDomicilioPlataforma[] = ["uber", "just_eat", "web_propia"];
const PEDIDO_ESTADOS: PedidoDomicilioEstado[] = [
  "recibido",
  "en_preparacion",
  "en_reparto",
  "entregado",
  "cancelado",
];

export function validateRequiredFields<T>(
  obj: T,
  requiredFields: Array<keyof T>
): ErrorDetail[] {
  const errors: ErrorDetail[] = [];

  for (const field of requiredFields) {
    const value = (obj as any)[field];
    if (value === null || value === undefined || value === "") {
      errors.push({
        field: String(field),
        message: `El campo ${String(field)} es obligatorio`,
      });
    }
  }
  return errors;
}

export type ValidationResult = { valid: boolean; errors: ErrorDetail[] };

export function validateConsistency(obj: any): ValidationResult {
  const errors: ErrorDetail[] = [];

  if (obj.startDate && obj.endDate) {
    if (new Date(obj.startDate) > new Date(obj.endDate)) {
      errors.push({ field: "startDate", message: "startDate no puede ser posterior a endDate" });
    }
  }

  const numericFieldsToCheck = ["votes", "stock", "price"];
  for (const field of numericFieldsToCheck) {
    if (field in obj && typeof obj[field] === "number" && obj[field] < 0) {
      errors.push({ field, message: `${field} no puede ser negativo` });
    }
  }

  return { valid: errors.length === 0, errors };
}

function isIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime());
}

function isIsoDateTime(value: string): boolean {
  return !Number.isNaN(Date.parse(value));
}

function isNonEmptyTrimmed(value: unknown): boolean {
  return typeof value === "string" && value.trim().length > 0;
}

export function validateEncargoProveedor(encargo: Partial<EncargoProveedor>): ValidationResult {
  const errors: ErrorDetail[] = [];
  const fechaPrevistaEntrega = encargo.fechaPrevistaEntrega ?? "";

  if (!isNonEmptyTrimmed(encargo.id)) errors.push({ field: "id", message: "id es obligatorio" });
  if (!isNonEmptyTrimmed(encargo.idProveedor)) {
    errors.push({ field: "idProveedor", message: "idProveedor es obligatorio" });
  }

  if (!isNonEmptyTrimmed(fechaPrevistaEntrega) || !isIsoDate(fechaPrevistaEntrega)) {
    errors.push({ field: "fechaPrevistaEntrega", message: "fechaPrevistaEntrega debe ser ISO YYYY-MM-DD" });
  }

  if (!ENCARGO_ESTADOS.includes(encargo.estado as EncargoProveedorEstado)) {
    errors.push({ field: "estado", message: "estado no permitido" });
  }

  if (typeof encargo.importeTotal !== "number" || !Number.isFinite(encargo.importeTotal) || encargo.importeTotal < 0) {
    errors.push({ field: "importeTotal", message: "importeTotal debe ser numero finito y >= 0" });
  }

  if (
    typeof encargo.numeroLineas !== "number" ||
    !Number.isInteger(encargo.numeroLineas) ||
    encargo.numeroLineas < 1
  ) {
    errors.push({ field: "numeroLineas", message: "numeroLineas debe ser entero >= 1" });
  }

  return { valid: errors.length === 0, errors };
}

export function validatePlatoCarta(plato: Partial<PlatoCarta>): ValidationResult {
  const errors: ErrorDetail[] = [];

  if (!isNonEmptyTrimmed(plato.id)) errors.push({ field: "id", message: "id es obligatorio" });
  if (!isNonEmptyTrimmed(plato.nombre)) errors.push({ field: "nombre", message: "nombre es obligatorio" });

  if (!PLATO_CATEGORIAS.includes(plato.categoria as PlatoCartaCategoria)) {
    errors.push({ field: "categoria", message: "categoria no permitida" });
  }

  if (typeof plato.precio !== "number" || !Number.isFinite(plato.precio) || plato.precio <= 0 || plato.precio > 500) {
    errors.push({ field: "precio", message: "precio debe ser > 0 y <= 500" });
  }

  if (!Array.isArray(plato.alergenos)) {
    errors.push({ field: "alergenos", message: "alergenos debe ser un array" });
  } else if (plato.alergenos.some((a) => typeof a !== "string" || a.trim() === "")) {
    errors.push({ field: "alergenos", message: "cada alergeno debe ser string no vacio" });
  }

  if (typeof plato.activoEnCarta !== "boolean") {
    errors.push({ field: "activoEnCarta", message: "activoEnCarta debe ser boolean" });
  }

  return { valid: errors.length === 0, errors };
}

export function validateReservaMesa(reserva: Partial<ReservaMesa>): ValidationResult {
  const errors: ErrorDetail[] = [];
  const fechaHora = reserva.fechaHora ?? "";

  if (!isNonEmptyTrimmed(reserva.id)) errors.push({ field: "id", message: "id es obligatorio" });
  if (!isNonEmptyTrimmed(reserva.nombreCliente)) {
    errors.push({ field: "nombreCliente", message: "nombreCliente es obligatorio" });
  }
  if (!isNonEmptyTrimmed(reserva.idMesa)) errors.push({ field: "idMesa", message: "idMesa es obligatorio" });

  if (
    typeof reserva.numeroComensales !== "number" ||
    !Number.isInteger(reserva.numeroComensales) ||
    reserva.numeroComensales < 1 ||
    reserva.numeroComensales > 40
  ) {
    errors.push({ field: "numeroComensales", message: "numeroComensales debe ser entero entre 1 y 40" });
  }

  if (!isNonEmptyTrimmed(fechaHora) || !isIsoDateTime(fechaHora)) {
    errors.push({ field: "fechaHora", message: "fechaHora debe ser ISO 8601 valido" });
  }

  if (!RESERVA_ESTADOS.includes(reserva.estado as ReservaMesaEstado)) {
    errors.push({ field: "estado", message: "estado no permitido" });
  }

  return { valid: errors.length === 0, errors };
}

export function validatePedidoDomicilio(pedido: Partial<PedidoDomicilio>): ValidationResult {
  const errors: ErrorDetail[] = [];
  const direccionEntrega = pedido.direccionEntrega ?? "";
  const fechaPedido = pedido.fechaPedido ?? "";

  if (!isNonEmptyTrimmed(pedido.id)) errors.push({ field: "id", message: "id es obligatorio" });

  if (!isNonEmptyTrimmed(direccionEntrega) || direccionEntrega.trim().length < 5) {
    errors.push({ field: "direccionEntrega", message: "direccionEntrega debe tener al menos 5 caracteres" });
  }

  if (typeof pedido.importeTotal !== "number" || !Number.isFinite(pedido.importeTotal) || pedido.importeTotal < 0) {
    errors.push({ field: "importeTotal", message: "importeTotal debe ser numero finito y >= 0" });
  }

  if (!PEDIDO_PLATAFORMAS.includes(pedido.plataforma as PedidoDomicilioPlataforma)) {
    errors.push({ field: "plataforma", message: "plataforma no permitida" });
  }

  if (!PEDIDO_ESTADOS.includes(pedido.estado as PedidoDomicilioEstado)) {
    errors.push({ field: "estado", message: "estado no permitido" });
  }

  if (!isNonEmptyTrimmed(fechaPedido) || !isIsoDateTime(fechaPedido)) {
    errors.push({ field: "fechaPedido", message: "fechaPedido debe ser ISO 8601 valido" });
  }

  return { valid: errors.length === 0, errors };
}
