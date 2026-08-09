"use client";

import Link from "next/link";
import AuthenticatedShell from "../components/AuthenticatedShell";

const moduleCards = [
  {
    id: "incidents-new",
    title: "Registrar incidencia",
    description:
      "Formulario en tiempo real para sedes, central y reportes de cliente.",
    href: "/incidents/nueva",
  },
  {
    id: "incidents",
    title: "Panel de incidencias",
    description: "Listado con filtros por estado, origen y sede; cambio de ciclo de vida.",
    href: "/incidents",
  },
  {
    id: "incidents-summary",
    title: "Resumen de incidencias",
    description: "Métricas agregadas para operaciones y dirección.",
    href: "/incidents/resumen",
  },
  {
    id: "proveedores",
    title: "Directorio de proveedores",
    description:
      "Fuente única de compras: tarifas, país, categorías y estado active/suspended.",
    href: "/proveedores",
  },
  {
    id: "inventory-products",
    title: "Stock de ingredientes",
    description:
      "Inventario en tiempo real con current_stock calculado y alertas de stock bajo.",
    href: "/inventory/products",
  },
  {
    id: "inventory-inbound",
    title: "Entrada de ingredientes",
    description: "Registrar entregas de proveedor (IngredientEntry) por local 1–14.",
    href: "/inventory/orders/inbound",
  },
  {
    id: "inventory-outbound",
    title: "Salida / merma",
    description:
      "Consumo o merma (IngredientExit) con stock visible antes de enviar.",
    href: "/inventory/orders/outbound",
  },
  {
    id: "inventory-orders",
    title: "Historial de inventario",
    description: "Órdenes de entrada y salida con ingrediente y user_uuid del autor.",
    href: "/inventory/orders",
  },
  {
    id: "perfil",
    title: "Mi cuenta",
    description: "Consulta y edita tu perfil (nombre y contacto) con sesión JWT.",
    href: "/account/profile",
  },
];

export default function BackofficeHome() {
  return (
    <AuthenticatedShell active="dashboard">
      <header id="overview" className="bo-topbar">
        <div>
          <p className="bo-kicker">Backoffice interno</p>
          <h1>Brasaland Digital OPS</h1>
        </div>
        <span className="bo-status">Sesión autenticada</span>
      </header>

      <section id="modulos" className="bo-grid">
        {moduleCards.map((moduleCard) => (
          <article key={moduleCard.id} className="bo-panel">
            <h3>{moduleCard.title}</h3>
            <p>{moduleCard.description}</p>
            {"href" in moduleCard && moduleCard.href ? (
              <p style={{ marginTop: 12 }}>
                <Link
                  className="bo-nav-link"
                  href={moduleCard.href}
                  style={{
                    display: "inline-block",
                    background: "#ecfeff",
                    color: "#0e7490",
                  }}
                >
                  Abrir módulo
                </Link>
              </p>
            ) : null}
          </article>
        ))}
      </section>
    </AuthenticatedShell>
  );
}
