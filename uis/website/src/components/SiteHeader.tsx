"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { navItems } from "@/data/site";

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const panelId = useId();

  // Close the drawer when the route changes by keying open state to path via click handlers.
  const closeMenu = () => setOpen(false);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <Link href="/" className="brand" aria-label="Brasaland — inicio" onClick={closeMenu}>
          <Image
            className="brand-mark"
            src="/Imagenes/Icono principal.png"
            alt=""
            width={192}
            height={181}
            sizes="40px"
            style={{ width: 40, height: "auto" }}
            priority
          />
          <span>
            Brasa<span className="brand-highlight">land</span>
          </span>
        </Link>

        <nav className="nav-desktop" aria-label="Navegación principal">
          {navItems.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className={pathname === item.href ? "nav-link is-active" : "nav-link"}
            >
              {item.label}
            </Link>
          ))}
          <Link href="/reservas" className="cta cta-compact">
            Reservar
          </Link>
        </nav>

        <button
          type="button"
          className="nav-toggle"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((v) => !v)}
        >
          <span className="sr-only">{open ? "Cerrar menú" : "Abrir menú"}</span>
          <span aria-hidden="true">{open ? "✕" : "☰"}</span>
        </button>
      </div>

      <div
        id={panelId}
        className={open ? "nav-mobile is-open" : "nav-mobile"}
        hidden={!open}
      >
        <nav className="nav-mobile-links" aria-label="Menú móvil">
          {navItems.map((item) => (
            <Link key={item.id} href={item.href} className="nav-link" onClick={closeMenu}>
              {item.label}
            </Link>
          ))}
          <Link href="/reservas" className="cta" onClick={closeMenu}>
            Reservar mesa
          </Link>
        </nav>
      </div>
    </header>
  );
}
