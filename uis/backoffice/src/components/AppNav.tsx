"use client";

import Link from "next/link";
import { logoutAndRedirect } from "../lib/api";

type Props = {
  active?: "dashboard" | "proveedores" | "profile";
};

export default function AppNav({ active }: Props) {
  return (
    <aside className="bo-sidebar" aria-label="Menu interno backoffice">
      <p className="bo-brand">Brasaland OPS</p>
      <nav>
        <Link
          href="/"
          className={`bo-nav-link${active === "dashboard" ? " bo-nav-link-active" : ""}`}
        >
          Dashboard
        </Link>
        <Link
          href="/proveedores"
          className={`bo-nav-link${active === "proveedores" ? " bo-nav-link-active" : ""}`}
        >
          Proveedores
        </Link>
        <Link
          href="/account/profile"
          className={`bo-nav-link${active === "profile" ? " bo-nav-link-active" : ""}`}
        >
          Mi perfil
        </Link>
        <button type="button" className="bo-nav-link bo-logout" onClick={logoutAndRedirect}>
          Cerrar sesión
        </button>
      </nav>
    </aside>
  );
}
