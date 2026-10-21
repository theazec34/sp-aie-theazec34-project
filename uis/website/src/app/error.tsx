"use client";

import Link from "next/link";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <section className="section">
      <div className="container narrow">
        <h1 className="section-title">Algo ha fallado</h1>
        <p className="section-text">
          No hemos podido mostrar esta página. Puedes reintentar o volver al inicio.
        </p>
        <p className="form-status form-status-error" role="alert">
          Ha ocurrido un error inesperado en la interfaz.
        </p>
        <div className="form-actions">
          <button type="button" className="cta" onClick={reset}>
            Reintentar
          </button>
          <Link className="cta cta-ghost" href="/">
            Ir al inicio
          </Link>
        </div>
      </div>
    </section>
  );
}
