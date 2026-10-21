import Link from "next/link";
import { footerNav, hours, legalLinks, restaurant } from "@/data/site";

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div className="footer-brand-block">
          <p className="brand footer-brand">
            Brasa<span className="brand-highlight">land</span>
          </p>
          <p className="footer-text">{restaurant.slogan}</p>
          <p className="footer-text">
            Carnes a la brasa que unen la gastronomía sudamericana con la tradición ibérica.
          </p>
        </div>

        <div>
          <h2 className="footer-heading">Explorar</h2>
          <ul className="footer-list">
            {footerNav.map((item) => (
              <li key={item.id}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="footer-heading">Contacto</h2>
          <ul className="footer-list">
            <li>{restaurant.address}</li>
            <li>
              <a href={`tel:${restaurant.phone.replace(/\s/g, "")}`}>
                {restaurant.phone}
                {restaurant.phoneIsPlaceholder ? " [provisional]" : ""}
              </a>
            </li>
            <li>
              <a href={`mailto:${restaurant.email}`}>{restaurant.email}</a>
            </li>
          </ul>
          <h2 className="footer-heading footer-heading-spaced">Horario</h2>
          <ul className="footer-list">
            {hours.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          {hours.provisional ? (
            <p className="footer-note">Horario orientativo — confirmar en el local.</p>
          ) : null}
        </div>
      </div>

      <div className="container footer-bottom">
        <nav className="footer-legal" aria-label="Información legal">
          {legalLinks.map((item) => (
            <Link key={item.id} href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
        <p className="footer-copy">
          © {year} Brasaland. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}
