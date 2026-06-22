export type EncargoProveedorEstado = "borrador" | "enviado" | "recibido" | "facturado";
export type PlatoCartaCategoria = "entrada" | "principal" | "postre" | "bebida";
export type ReservaMesaEstado = "pendiente" | "confirmada" | "cancelada" | "completada";
export type PedidoDomicilioPlataforma = "uber" | "just_eat" | "web_propia";
export type PedidoDomicilioEstado =
	| "recibido"
	| "en_preparacion"
	| "en_reparto"
	| "entregado"
	| "cancelado";

export interface ErrorDetail {
	field: string;
	message: string;
}

export interface EncargoProveedor {
	id: string;
	idProveedor: string;
	fechaPrevistaEntrega: string;
	estado: EncargoProveedorEstado;
	importeTotal: number;
	numeroLineas: number;
}

export interface PlatoCarta {
	id: string;
	nombre: string;
	categoria: PlatoCartaCategoria;
	precio: number;
	alergenos: string[];
	activoEnCarta: boolean;
}

export interface ReservaMesa {
	id: string;
	nombreCliente: string;
	numeroComensales: number;
	fechaHora: string;
	idMesa: string;
	estado: ReservaMesaEstado;
}

export interface PedidoDomicilio {
	id: string;
	direccionEntrega: string;
	importeTotal: number;
	plataforma: PedidoDomicilioPlataforma;
	estado: PedidoDomicilioEstado;
	fechaPedido: string;
}
