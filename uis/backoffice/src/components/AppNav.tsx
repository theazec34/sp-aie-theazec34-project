"use client";

import Link from "next/link";
import { logoutAndRedirect } from "../lib/api";

type Props = {
  active?:
    | "dashboard"
    | "web-reservations"
    | "careers"
    | "rfp"
    | "knowledge"
    | "agent"
    | "reporting"
    | "telemetry"
    | "incidents-new"
    | "incidents"
    | "incidents-summary"
    | "proveedores"
    | "inventory-products"
    | "inventory-inbound"
    | "inventory-outbound"
    | "inventory-orders"
    | "profile";
};

/** Same order as the dashboard module cards on `/`. */
const NAV_ITEMS: Array<{
  href: string;
  label: string;
  active: NonNullable<Props["active"]>;
}> = [
  { href: "/", label: "Panel", active: "dashboard" },
  { href: "/web-reservations", label: "Reservas web", active: "web-reservations" },
  { href: "/careers", label: "Candidaturas", active: "careers" },
  { href: "/rfp", label: "Recepción RFP", active: "rfp" },
  { href: "/knowledge", label: "Base de conocimiento", active: "knowledge" },
  { href: "/agent", label: "Agente soporte", active: "agent" },
  { href: "/reporting", label: "Costo y merma", active: "reporting" },
  { href: "/telemetry", label: "Telemetría", active: "telemetry" },
  { href: "/incidents/nueva", label: "Registrar incidencia", active: "incidents-new" },
  { href: "/incidents", label: "Panel de incidencias", active: "incidents" },
  { href: "/incidents/resumen", label: "Resumen incidencias", active: "incidents-summary" },
  { href: "/proveedores", label: "Proveedores", active: "proveedores" },
  { href: "/inventory/products", label: "Existencias", active: "inventory-products" },
  { href: "/inventory/orders/inbound", label: "Entrada inventario", active: "inventory-inbound" },
  { href: "/inventory/orders/outbound", label: "Salida inventario", active: "inventory-outbound" },
  { href: "/inventory/orders", label: "Historial inventario", active: "inventory-orders" },
  { href: "/account/profile", label: "Mi cuenta", active: "profile" },
];

export default function AppNav({ active }: Props) {
  return (
    <aside className="bo-sidebar" aria-label="Menú interno del backoffice">
      <p className="bo-brand">Brasaland Operaciones</p>
      <nav>
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`bo-nav-link${active === item.active ? " bo-nav-link-active" : ""}`}
          >
            {item.label}
          </Link>
        ))}
        <button type="button" className="bo-nav-link bo-logout" onClick={logoutAndRedirect}>
          Cerrar sesión
        </button>
      </nav>
    </aside>
  );
}
