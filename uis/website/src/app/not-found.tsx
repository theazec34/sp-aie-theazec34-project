import Link from "next/link";

export default function NotFound() {
  return (
    <section className="section">
      <div className="container narrow">
        <p className="section-eyebrow">404</p>
        <h1 className="section-title">No encontramos esta mesa</h1>
        <p className="section-text">
          La página no existe o se ha movido. Vuelve al inicio o reserva desde la carta.
        </p>
        <p className="section-cta-row">
          <Link className="cta" href="/">
            Ir al inicio
          </Link>
          <Link className="cta cta-ghost" href="/carta">
            Ver la carta
          </Link>
        </p>
      </div>
    </section>
  );
}
