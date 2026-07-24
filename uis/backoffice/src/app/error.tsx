"use client";

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="bo-kicker">Brasaland OPS</p>
        <h1>Algo ha fallado</h1>
        <p className="bo-soft">
          No hemos podido mostrar esta página. Puedes reintentar o volver al
          inicio.
        </p>
        <p className="bo-alert bo-alert-error" role="alert">
          {error?.message
            ? "Ha ocurrido un error inesperado en la interfaz."
            : "Error inesperado."}
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
          <button type="button" className="bo-btn bo-btn-primary" onClick={reset}>
            Reintentar
          </button>
          <Link className="bo-btn" href="/">
            Ir al inicio
          </Link>
        </div>
      </section>
    </main>
  );
}
