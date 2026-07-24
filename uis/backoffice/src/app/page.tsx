"use client";

import Link from "next/link";
import AppNav from "../components/AppNav";
import RequireAuth from "../components/RequireAuth";

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
    id: "perfil",
    title: "Mi cuenta",
    description: "Consulta y edita tu perfil (nombre y contacto) con sesión JWT.",
    href: "/account/profile",
  },
];

export default function BackofficeHome() {
  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="dashboard" />

        <section className="bo-content">
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
        </section>
      </main>
    </RequireAuth>
  );
}
