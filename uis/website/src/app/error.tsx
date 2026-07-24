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
    <main className="section">
      <div className="container">
        <h1 className="section-title">Algo ha fallado</h1>
        <p className="section-text">
          No hemos podido mostrar esta página. Puedes reintentar o volver al
          inicio de Brasaland.
        </p>
        <p className="form-error" role="alert">
          {error?.message
            ? "Ha ocurrido un error inesperado en la interfaz."
            : "Error inesperado."}
        </p>
        <div className="form-actions">
          <button type="button" className="cta" onClick={reset}>
            Reintentar
          </button>
          <Link className="cta cta-secondary" href="/">
            Ir al inicio
          </Link>
        </div>
      </div>
    </main>
  );
}
