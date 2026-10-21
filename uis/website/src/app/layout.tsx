import type { Metadata, Viewport } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

const fontBody = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  display: "swap",
});

const fontDisplay = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  display: "swap",
});

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
    <html lang="es" className={`${fontBody.variable} ${fontDisplay.variable}`}>
      <body>
        <SiteHeader />
        <main className="site-main">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
