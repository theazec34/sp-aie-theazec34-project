const moduleCards = [
  {
    id: "proveedores",
    title: "Directorio de proveedores",
    description: "Fuente única de compras: tarifas, país, categorías y estado active/suspended.",
    href: "/proveedores",
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
  {
    id: "locaciones",
    title: "Performance de locaciones",
    description: "Placeholder para score compuesto y ranking de sedes activas.",
  },
];

export default function BackofficeHome() {
  return (
    <main className="bo-shell">
      <aside className="bo-sidebar" aria-label="Menu interno backoffice">
        <p className="bo-brand">Brasaland OPS</p>
        <nav>
          <a href="/" className="bo-nav-link bo-nav-link-active">
            Dashboard
          </a>
          <a href="/proveedores" className="bo-nav-link">
            Proveedores
          </a>
        </nav>
      </aside>

      <section className="bo-content">
        <header id="overview" className="bo-topbar">
          <div>
            <p className="bo-kicker">Backoffice interno</p>
            <h1>Brasaland Digital OPS</h1>
          </div>
          <span className="bo-status">Directorio de proveedores listo</span>
        </header>

        <section id="modulos" className="bo-grid">
          {moduleCards.map((moduleCard) => (
            <article key={moduleCard.id} className="bo-panel">
              <h3>{moduleCard.title}</h3>
              <p>{moduleCard.description}</p>
              {"href" in moduleCard && moduleCard.href ? (
                <p style={{ marginTop: 12 }}>
                  <a className="bo-nav-link" href={moduleCard.href} style={{ display: "inline-block", background: "#ecfeff", color: "#0e7490" }}>
                    Abrir módulo
                  </a>
                </p>
              ) : null}
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}
