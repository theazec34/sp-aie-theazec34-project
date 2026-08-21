"use client";

import Link from "next/link";
import { logoutAndRedirect } from "../lib/api";

type Props = {
  active?:
    | "dashboard"
    | "proveedores"
    | "profile"
    | "password"
    | "incidents"
    | "incidents-new"
    | "incidents-summary"
    | "inventory-products"
    | "inventory-inbound"
    | "inventory-outbound"
    | "inventory-orders"
    | "telemetry";
};

export default function AppNav({ active }: Props) {
  return (
    <aside className="bo-sidebar" aria-label="Menu interno backoffice">
      <p className="bo-brand">Brasaland OPS</p>
      <nav>
        <Link
          href="/"
          className={`bo-nav-link${active === "dashboard" ? " bo-nav-link-active" : ""}`}
        >
          Dashboard
        </Link>
        <Link
          href="/proveedores"
          className={`bo-nav-link${active === "proveedores" ? " bo-nav-link-active" : ""}`}
        >
          Proveedores
        </Link>
        <Link
          href="/inventory/products"
          className={`bo-nav-link${active === "inventory-products" ? " bo-nav-link-active" : ""}`}
        >
          Stock ingredientes
        </Link>
        <Link
          href="/inventory/orders/inbound"
          className={`bo-nav-link${active === "inventory-inbound" ? " bo-nav-link-active" : ""}`}
        >
          Entrada inventario
        </Link>
        <Link
          href="/inventory/orders/outbound"
          className={`bo-nav-link${active === "inventory-outbound" ? " bo-nav-link-active" : ""}`}
        >
          Salida inventario
        </Link>
        <Link
          href="/inventory/orders"
          className={`bo-nav-link${active === "inventory-orders" ? " bo-nav-link-active" : ""}`}
        >
          Historial inventario
        </Link>
        <Link
          href="/telemetry"
          className={`bo-nav-link${active === "telemetry" ? " bo-nav-link-active" : ""}`}
        >
          Telemetría (ops)
        </Link>
        <Link
          href="/incidents/nueva"
          className={`bo-nav-link${active === "incidents-new" ? " bo-nav-link-active" : ""}`}
        >
          Registrar incidencia
        </Link>
        <Link
          href="/incidents"
          className={`bo-nav-link${active === "incidents" ? " bo-nav-link-active" : ""}`}
        >
          Panel de incidencias
        </Link>
        <Link
          href="/incidents/resumen"
          className={`bo-nav-link${active === "incidents-summary" ? " bo-nav-link-active" : ""}`}
        >
          Resumen incidencias
        </Link>
        <Link
          href="/account/profile"
          className={`bo-nav-link${active === "profile" ? " bo-nav-link-active" : ""}`}
        >
          Mi perfil
        </Link>
        <Link
          href="/account/change-password"
          className={`bo-nav-link${active === "password" ? " bo-nav-link-active" : ""}`}
        >
          Cambiar contraseña
        </Link>
        <button type="button" className="bo-nav-link bo-logout" onClick={logoutAndRedirect}>
          Cerrar sesión
        </button>
      </nav>
    </aside>
  );
}
