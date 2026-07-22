"use client";

import Link from "next/link";
import RequireAuth from "../components/RequireAuth";

const moduleCards = [
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
  {
    id: "ventas",
    title: "Ventas y margenes",
    description: "Placeholder para analitica diaria, ticket promedio y comparativa por pais.",
  },
  {
    id: "desperdicio",
    title: "Control de desperdicio",
    description: "Placeholder para costos por motivo, alertas y tendencias por locacion.",
  },
];

export default function BackofficeHome() {
  return (
    <RequireAuth>
      <main className="bo-shell">
        <aside className="bo-sidebar" aria-label="Menu interno backoffice">
          <p className="bo-brand">Brasaland OPS</p>
          <nav>
            <Link href="/" className="bo-nav-link bo-nav-link-active">
              Dashboard
            </Link>
            <Link href="/proveedores" className="bo-nav-link">
              Proveedores
            </Link>
            <Link href="/account/profile" className="bo-nav-link">
              Mi perfil
            </Link>
            <Link href="/login" className="bo-nav-link">
              Login
            </Link>
          </nav>
        </aside>

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
