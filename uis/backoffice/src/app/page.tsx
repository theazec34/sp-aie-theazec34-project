const moduleCards = [
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
  {
    id: "catalogo",
    title: "Catalogo de menu",
    description: "Placeholder para estado de items, costos y validaciones de negocio.",
  },
];

export default function BackofficeHome() {
  return (
    <main className="bo-shell">
      <aside className="bo-sidebar" aria-label="Menu interno backoffice">
        <p className="bo-brand">Brasaland OPS</p>
        <nav>
          <a href="#overview" className="bo-nav-link bo-nav-link-active">
            Dashboard
          </a>
          <a href="#hito2" className="bo-nav-link">
            Hito 2 Scope
          </a>
          <a href="#modulos" className="bo-nav-link">
            Modulos
          </a>
        </nav>
      </aside>

      <section className="bo-content">
        <header id="overview" className="bo-topbar">
          <div>
            <p className="bo-kicker">Backoffice interno</p>
            <h1>Dashboard base vacio</h1>
          </div>
          <span className="bo-status">Estado: estructura inicial</span>
        </header>

        <section id="hito2" className="bo-panel bo-panel-muted">
          <h2>Contexto Hito 2</h2>
          <p>
            Base preparada para integrar utilidades TypeScript de operaciones: colecciones, busqueda, metricas,
            scoring y validaciones.
          </p>
        </section>

        <section id="modulos" className="bo-grid">
          {moduleCards.map((moduleCard) => (
            <article key={moduleCard.id} className="bo-panel">
              <h3>{moduleCard.title}</h3>
              <p>{moduleCard.description}</p>
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}
