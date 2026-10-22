import type { Metadata, Viewport } from "next";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

/**
 * Sin next/font/google: en Docker/Codespaces sin salida a fonts.googleapis.com
 * cada ruta reintentaba descargar DM Sans / Fraunces y ralentizaba formularios.
 * Stacks locales en globals.css (--font-body / --font-display).
 */

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: {
    default: "Brasaland — Carnes a la brasa en Sevilla",
    template: "%s · Brasaland",
  },
  description:
    "Restaurante Brasaland: fuego sudamericano y alma ibérica. Carta, reservas, eventos y candidaturas.",
  icons: { icon: "/favicon.png" },
  openGraph: {
    title: "Brasaland — El fuego nos une",
    description: "Carnes a la brasa, arroces y hospitalidad en Sevilla.",
    locale: "es_ES",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" data-scroll-behavior="smooth">
      <body>
        <SiteHeader />
        <main className="site-main">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
